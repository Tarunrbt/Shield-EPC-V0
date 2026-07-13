"""
Base Agent contract.

Source of truth: docs/ShieldEPC_Architecture_Spec_v1.md §3 (Agent Roster
and Single-Responsibility Definitions) and §6 (Zero Hallucination Policy).

Every domain agent has exactly one responsibility and must be able to
say "insufficient_information" instead of fabricating an answer when
grounding is missing. This ABC only defines that contract shape — it does
not implement any specific agent yet. Phase 1 (ROADMAP.md) builds the
Document Generator Agent first as the initial concrete subclass.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class InsufficientInformation(Exception):
    """
    Raised by an agent instead of returning a best-effort guess when
    grounding is missing. §6 point 1 and point 4: no plausible-sounding
    default may fill a gap. Callers must surface this as
    missing_information in the envelope, not swallow it.
    """


class Agent(ABC):
    """Single-responsibility domain specialist. See §3 for the roster."""

    name: str
    version: str

    @abstractmethod
    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Executes the agent's one job against a request payload and returns
        a raw result dict — NOT an envelope. Envelope assembly happens one
        layer up (app.envelope.middleware.EnvelopeAssembler), per §4 point 4:
        assembly is the Orchestrator's job, not the agent's.

        Must raise InsufficientInformation rather than return a fabricated
        answer when required grounding isn't available.
        """
        raise NotImplementedError
