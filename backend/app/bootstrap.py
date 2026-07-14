"""
Application-wide singleton wiring.

Constructed once when this module is first imported (Python caches
module imports, so this only runs once per process). main.py and any
api/ route module that needs the orchestrator should import from here,
not construct their own instances -- this is the single source of
truth for how Phase 1/2 components are wired together in a running
app, mirroring test_e2e.py wiring but with a persistent AuditLog path
instead of a tempfile.

NOTE: AuditLog is not multi-process safe (see app/audit/log.py
docstring). Fine for a single uvicorn worker; must be revisited before
running with --workers > 1 or behind a multi-process server.
"""

from __future__ import annotations

from app.agents.document_generator import DocumentGeneratorAgent
from app.agents.verifier import VerifierAgent
from app.audit.log import AuditLog
from app.config import AUDIT_LOG_PATH
from app.envelope.middleware import EnvelopeAssembler
from app.orchestrator import Orchestrator

audit_log = AuditLog(AUDIT_LOG_PATH)
envelope_assembler = EnvelopeAssembler(model_version="phase2-api")
verifier = VerifierAgent()
document_generator_agent = DocumentGeneratorAgent()

orchestrator = Orchestrator(
    audit_log=audit_log,
    envelope_assembler=envelope_assembler,
    verifier=verifier,
)
