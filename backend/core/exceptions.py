"""
Core exception hierarchy for Shield EPC.

Source of truth: docs/ShieldEPC_Architecture_Spec_v1.md §5 (Mandatory Output Envelope)
and §6 (Zero Hallucination Policy). Every agent output that reaches the envelope
must surface errors through this hierarchy — no free-form exceptions escape the
domain layer.

Plain Python Exception hierarchy only. No Pydantic. Zero external runtime
dependencies. Stable string error codes. Immutable error metadata via
MappingProxyType. Public interfaces do not expose typing.Any.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final


__all__ = [
    # Base
    "ShieldEPCError",
    "ErrorCode",
    # Domain errors
    "InsufficientInformation",
    "GroundingMissing",
    "ConfidenceBelowThreshold",
    "HumanReviewRequired",
    "ValidationFailed",
    "EnvelopeAssemblyFailed",
    # Infrastructure errors
    "ProviderUnavailable",
    "ConfigurationError",
    "TenantIsolationViolation",
    "AuditLogFailure",
    # Routing / orchestration
    "RoutingError",
    "AgentNotFound",
    "OrchestrationError",
    # Knowledge / standards
    "StandardNotFound",
    "ClauseNotFound",
    "KnowledgeGraphUnavailable",
    # Data layer
    "TenantNotFound",
    "DocumentNotFound",
    "PersistenceError",
    # Security / auth
    "AuthenticationFailed",
    "AuthorizationFailed",
    "TokenExpired",
    # Error code registry
    "ERROR_CODE_REGISTRY",
]


class ErrorCode(str):
    """Stable string error code. Subclass for type safety in pattern matching."""

    __slots__ = ()


class ShieldEPCError(Exception):
    """
    Base exception for all Shield EPC domain errors.

    Attributes:
        code: Stable string error code for programmatic handling.
        message: Human-readable description.
        metadata: Immutable mapping of structured error context.
    """

    __slots__ = ("code", "message", "metadata")

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code: Final[ErrorCode] = code
        self.message: Final[str] = message
        self.metadata: Final[Mapping[str, object]] = MappingProxyType(
            dict(metadata) if metadata else {}
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# ---- Domain errors ---------------------------------------------------------


class InsufficientInformation(ShieldEPCError):
    """
    Raised by an agent instead of returning a best-effort guess when
    grounding is missing. §6 point 1 and point 4: no plausible-sounding
    default may fill a gap. Callers must surface this as missing_information
    in the envelope, not swallow it.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        missing_items: list[str] | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if missing_items:
            merged_meta["missing_items"] = tuple(missing_items)
        super().__init__(ErrorCode("INSUFFICIENT_INFORMATION"), message, merged_meta)


class GroundingMissing(ShieldEPCError):
    """
    Raised when retrieval returns no relevant clause/document for a
    Compliance or Risk Assessment query. Distinct from
    InsufficientInformation — this means the knowledge layer has nothing,
    not merely that the input was incomplete.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        query: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if query:
            merged_meta["query"] = query
        super().__init__(ErrorCode("GROUNDING_MISSING"), message, merged_meta)


class ConfidenceBelowThreshold(ShieldEPCError):
    """
    Raised when an agent's confidence_score falls below the tenant-configured
    threshold (architecture §8 gate table). Triggers automatic routing to
    human review queue.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        confidence_score: float,
        threshold: float,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        merged_meta["confidence_score"] = confidence_score
        merged_meta["threshold"] = threshold
        super().__init__(ErrorCode("CONFIDENCE_BELOW_THRESHOLD"), message, merged_meta)


class HumanReviewRequired(ShieldEPCError):
    """
    Raised when the gate policy (architecture §8) mandates human review
    before an output can proceed. Carries the canonical reason enum from
    the envelope schema.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        reason: str,  # One of: risk_rating_high, compliance_gap_flagged, low_confidence, statutory_requirement
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        merged_meta["human_review_reason"] = reason
        super().__init__(ErrorCode("HUMAN_REVIEW_REQUIRED"), message, merged_meta)


class ValidationFailed(ShieldEPCError):
    """
    Raised when envelope assembly (schema.py) rejects a field — e.g.
    confidence_score out of bounds, human_review_required=True without
    human_review_reason, or schema_version mismatch.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: object = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if field:
            merged_meta["field"] = field
        if value is not None:
            merged_meta["rejected_value"] = value
        super().__init__(ErrorCode("VALIDATION_FAILED"), message, merged_meta)


class EnvelopeAssemblyFailed(ShieldEPCError):
    """
    Raised when EnvelopeAssembler cannot build a valid ResponseEnvelope
    from agent output — typically because required fields are missing or
    the Verifier Agent's pre-check failed.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        missing_fields: list[str] | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if agent_name:
            merged_meta["agent"] = agent_name
        if missing_fields:
            merged_meta["missing_fields"] = tuple(missing_fields)
        super().__init__(ErrorCode("ENVELOPE_ASSEMBLY_FAILED"), message, merged_meta)


# ---- Infrastructure errors -------------------------------------------------


class ProviderUnavailable(ShieldEPCError):
    """
    Raised when an external LLM/provider SDK call fails due to
    connectivity, rate limits, or provider-side errors. Not for invalid
    requests — those are ValidationFailed.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        retry_after_seconds: float | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if provider:
            merged_meta["provider"] = provider
        if retry_after_seconds is not None:
            merged_meta["retry_after_seconds"] = retry_after_seconds
        super().__init__(ErrorCode("PROVIDER_UNAVAILABLE"), message, merged_meta)


class ConfigurationError(ShieldEPCError):
    """
    Raised at startup or runtime when required configuration is missing,
    invalid, or contradictory (e.g. a provider name not in the registry,
    or a required env var unset). Mirrors ai-agents/orchestrator/router.py
    RoutingError but at the platform level.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if config_key:
            merged_meta["config_key"] = config_key
        super().__init__(ErrorCode("CONFIGURATION_ERROR"), message, merged_meta)


class TenantIsolationViolation(ShieldEPCError):
    """
    Raised when a cross-tenant data access attempt is detected — the
    single most damaging failure mode for a multi-tenant HSE platform
    (architecture §9). Always logged at CRITICAL and triggers audit alert.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        source_tenant_id: str | None = None,
        target_tenant_id: str | None = None,
        operation: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if source_tenant_id:
            merged_meta["source_tenant_id"] = source_tenant_id
        if target_tenant_id:
            merged_meta["target_tenant_id"] = target_tenant_id
        if operation:
            merged_meta["operation"] = operation
        super().__init__(ErrorCode("TENANT_ISOLATION_VIOLATION"), message, merged_meta)


class AuditLogFailure(ShieldEPCError):
    """
    Raised when the append-only audit log (architecture §7) cannot accept
    an entry. This is a critical infrastructure failure — the operation
    that triggered the audit must not proceed silently.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        audit_trail_id: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if audit_trail_id:
            merged_meta["audit_trail_id"] = audit_trail_id
        super().__init__(ErrorCode("AUDIT_LOG_FAILURE"), message, merged_meta)


# ---- Routing / orchestration ----------------------------------------------


class RoutingError(ShieldEPCError):
    """
    Raised when the orchestrator cannot route a request to an agent —
    unknown intent, no matching agent, or provider selection failed.
    Mirrors ai-agents/orchestrator/router.py RoutingError at the core layer.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        intent: str | None = None,
        available_agents: list[str] | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if intent:
            merged_meta["intent"] = intent
        if available_agents:
            merged_meta["available_agents"] = tuple(available_agents)
        super().__init__(ErrorCode("ROUTING_ERROR"), message, merged_meta)


class AgentNotFound(ShieldEPCError):
    """
    Raised when a requested agent name does not match any registered
    domain agent (architecture §3 roster).
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        available_agents: list[str] | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if agent_name:
            merged_meta["agent_name"] = agent_name
        if available_agents:
            merged_meta["available_agents"] = tuple(available_agents)
        super().__init__(ErrorCode("AGENT_NOT_FOUND"), message, merged_meta)


class OrchestrationError(ShieldEPCError):
    """
    Raised when the multi-agent task graph execution fails — dependency
    cycle, agent timeout, or Verifier Agent rejection that cannot be
    resolved by retry.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        stage: str | None = None,
        agent_name: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if stage:
            merged_meta["stage"] = stage
        if agent_name:
            merged_meta["agent"] = agent_name
        super().__init__(ErrorCode("ORCHESTRATION_ERROR"), message, merged_meta)


# ---- Knowledge / standards ------------------------------------------------


class StandardNotFound(ShieldEPCError):
    """
    Raised when the Standards Knowledge Graph (architecture §6 point 3)
    has no entry for a requested standard code (e.g. ISO_45001_2018).
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        standard_code: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if standard_code:
            merged_meta["standard_code"] = standard_code
        super().__init__(ErrorCode("STANDARD_NOT_FOUND"), message, merged_meta)


class ClauseNotFound(ShieldEPCError):
    """
    Raised when a specific clause reference (e.g. ISO 45001:2018 §8.1.2)
    cannot be resolved in the versioned Knowledge Graph.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        clause_ref: str | None = None,
        standard_code: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if clause_ref:
            merged_meta["clause_ref"] = clause_ref
        if standard_code:
            merged_meta["standard_code"] = standard_code
        super().__init__(ErrorCode("CLAUSE_NOT_FOUND"), message, merged_meta)


class KnowledgeGraphUnavailable(ShieldEPCError):
    """
    Raised when the vector DB / Knowledge Graph service is unreachable
    or returns an error. Distinct from ClauseNotFound (which means the
    service responded but the clause doesn't exist).
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(ErrorCode("KNOWLEDGE_GRAPH_UNAVAILABLE"), message, metadata)


# ---- Data layer -----------------------------------------------------------


class TenantNotFound(ShieldEPCError):
    """Raised when a tenant_id cannot be resolved in the data layer."""

    __slots__ = ()

    def __init__(
        self,
        message: str,
        tenant_id: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if tenant_id:
            merged_meta["tenant_id"] = tenant_id
        super().__init__(ErrorCode("TENANT_NOT_FOUND"), message, merged_meta)


class DocumentNotFound(ShieldEPCError):
    """
    Raised when a tenant-scoped document (SOP, JSA, permit, incident
    record) is not found in object storage or the operational DB.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        document_id: str | None = None,
        tenant_id: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if document_id:
            merged_meta["document_id"] = document_id
        if tenant_id:
            merged_meta["tenant_id"] = tenant_id
        super().__init__(ErrorCode("DOCUMENT_NOT_FOUND"), message, merged_meta)


class PersistenceError(ShieldEPCError):
    """
    Raised when a database or object storage operation fails
    unexpectedly — connection loss, constraint violation, serialization
    error. Not for "not found" cases (use TenantNotFound/DocumentNotFound).
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if operation:
            merged_meta["operation"] = operation
        super().__init__(ErrorCode("PERSISTENCE_ERROR"), message, merged_meta)


# ---- Security / auth ------------------------------------------------------


class AuthenticationFailed(ShieldEPCError):
    """
    Raised when credentials are invalid, missing, or the OIDC/OAuth2
    flow cannot be completed.
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        auth_method: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if auth_method:
            merged_meta["auth_method"] = auth_method
        super().__init__(ErrorCode("AUTHENTICATION_FAILED"), message, merged_meta)


class AuthorizationFailed(ShieldEPCError):
    """
    Raised when an authenticated principal lacks the required role or
    permission for an operation (e.g. Supervisor Approval gate in
    architecture §8.1 step 3 requires supervisor role).
    """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        required_role: str | None = None,
        principal_id: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if required_role:
            merged_meta["required_role"] = required_role
        if principal_id:
            merged_meta["principal_id"] = principal_id
        super().__init__(ErrorCode("AUTHORIZATION_FAILED"), message, merged_meta)


class TokenExpired(ShieldEPCError):
    """Raised when a JWT or session token has expired."""

    __slots__ = ()

    def __init__(
        self,
        message: str,
        token_type: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        merged_meta = dict(metadata) if metadata else {}
        if token_type:
            merged_meta["token_type"] = token_type
        super().__init__(ErrorCode("TOKEN_EXPIRED"), message, merged_meta)


# ---- Error code registry --------------------------------------------------


ERROR_CODE_REGISTRY: Final[Mapping[str, type[ShieldEPCError]]] = MappingProxyType(
    {
        "INSUFFICIENT_INFORMATION": InsufficientInformation,
        "GROUNDING_MISSING": GroundingMissing,
        "CONFIDENCE_BELOW_THRESHOLD": ConfidenceBelowThreshold,
        "HUMAN_REVIEW_REQUIRED": HumanReviewRequired,
        "VALIDATION_FAILED": ValidationFailed,
        "ENVELOPE_ASSEMBLY_FAILED": EnvelopeAssemblyFailed,
        "PROVIDER_UNAVAILABLE": ProviderUnavailable,
        "CONFIGURATION_ERROR": ConfigurationError,
        "TENANT_ISOLATION_VIOLATION": TenantIsolationViolation,
        "AUDIT_LOG_FAILURE": AuditLogFailure,
        "ROUTING_ERROR": RoutingError,
        "AGENT_NOT_FOUND": AgentNotFound,
        "ORCHESTRATION_ERROR": OrchestrationError,
        "STANDARD_NOT_FOUND": StandardNotFound,
        "CLAUSE_NOT_FOUND": ClauseNotFound,
        "KNOWLEDGE_GRAPH_UNAVAILABLE": KnowledgeGraphUnavailable,
        "TENANT_NOT_FOUND": TenantNotFound,
        "DOCUMENT_NOT_FOUND": DocumentNotFound,
        "PERSISTENCE_ERROR": PersistenceError,
        "AUTHENTICATION_FAILED": AuthenticationFailed,
        "AUTHORIZATION_FAILED": AuthorizationFailed,
        "TOKEN_EXPIRED": TokenExpired,
    }
)


def error_code_to_exception(code: str) -> type[ShieldEPCError] | None:
    """Look up exception class by stable error code string."""
    return ERROR_CODE_REGISTRY.get(code)