"""
Verifier Agent.

Source of truth:
- ShieldEPC_Architecture_Spec_v1.md §6 (Zero Hallucination Policy)

This agent performs a verification pass over an agent result before the
response envelope is assembled. It never invents evidence. If grounding
is missing, it raises InsufficientInformation.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import Agent, InsufficientInformation


class VerifierAgent(Agent):
    """
    Phase 1 verification agent.

    Verifies that every answer has supporting grounding before the
    response reaches the EnvelopeAssembler.
    """

    name = "verifier_agent"
    version = "1.0.0"
    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Verify an agent result before envelope assembly.

        Expected request keys:
        - answer
        - source_of_reasoning

        Phase 1 intentionally performs only structural verification.
        Semantic verification against regulations and standards is added
        in a later phase.
        """

        answer = request.get("answer", "")
        sources = request.get("source_of_reasoning", [])

        if not answer:
            raise InsufficientInformation(
                "No answer available for verification."
            )

        if not sources:
            raise InsufficientInformation(
                "No supporting source_of_reasoning supplied."
            )

        verified = dict(request)
        verified["verification_status"] = "verified"
        verified["verification_agent"] = self.name
        verified["verification_agent_version"] = self.version

        return verified
