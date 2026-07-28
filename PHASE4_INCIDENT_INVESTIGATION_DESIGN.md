# Phase 4 Incident Investigation Agent Design

Status: APPROVED

## Scope (first cut)
RCA scaffolding only (5-Why, Fishbone, Bowtie structuring). Historical
pattern-match to past incidents is deferred to a later milestone — it
requires a new persistence layer (incident history store) that does
not exist yet and is out of scope here.

## Nature
Deterministic validation/composition agent, same family as
RiskAssessmentAgent, ComplianceAgent, PTWJSAAgent. No LLM call, no
generative inference. The agent does not invent RCA content — the
caller (investigator) supplies structured findings; the agent validates
and organizes them into a fixed scaffold.

## Request shape
- incident_description: str, non-empty
- five_whys: list[str], min_length=1, every entry non-blank after strip()
- fishbone_causes: dict[FishboneCategory, list[str]]
  - FishboneCategory is a fixed enum: people_factors, process,
    equipment, materials, environment
  - "people_factors" is a category of human-factors causes (e.g.
    "inadequate training"), never a field for naming an individual
- bowtie_top_event: str, non-empty
- bowtie_threats: list[str]
- bowtie_consequences: list[str]
- preventive_barriers: list[str]
- mitigative_barriers: list[str]

## Blame-safety (structural, not prompt-based)
The agent records contributing factors only. It has no schema field
capable of assigning fault, responsibility, or culpability to an
identified individual. This is enforced by the schema shape itself
(FishboneCategory enum has no "responsible_person"/"at_fault" field,
and no other field in the request or response model accepts a named
individual), not by instruction — consistent with this agent having no
generative/LLM component to instruct in the first place. Verified by a
unit test that introspects the response schema for such fields.

## Human sign-off (mandatory, structurally incomplete without it)
Response always includes:

    "investigator_signoff": {
        "signed_off": False,
        "investigator_name": None,
        "signoff_date": None,
    }

The agent can never set signed_off=True — that only happens through a
separate future sign-off workflow/endpoint, not this agent. The
rendered answer text explicitly states:
"DRAFT — PENDING HUMAN INVESTIGATOR SIGN-OFF".

## Envelope fields
- human_review_required = True
- human_review_reason = "statutory_requirement" (reusing the existing
  HumanReviewReason enum value; no new enum value added in this phase)

## Next implementation
1. backend/app/agents/incident_investigation.py
2. Unit tests (pytest, tests/test_incident_investigation.py)
3. Orchestrator routing (operation_type="incident_investigation")
4. Regression (pytest -q)
