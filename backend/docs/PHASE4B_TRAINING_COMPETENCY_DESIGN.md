Phase 4B Design Freeze — Training & Competency Agent
1. Responsibilities
The Training & Competency Agent validates and organizes caller-supplied training and competency records against a caller-supplied set of required competencies for a role or task. It determines — deterministically, not generatively — which required competencies are satisfied (present, valid, not expired) and which are not, and surfaces the gap as structured missing_information.
It does not judge whether a person is "competent" in any qualitative sense. It checks record presence and expiry against caller-supplied requirements only, exactly as Incident Investigation validates and scaffolds investigator-supplied findings rather than generating RCA conclusions.
2. Functional Scope (Phase 4B — first cut)
Accept a role/task identifier, a caller-supplied list of required competencies, and a caller-supplied list of training records.
For each required competency, check whether a matching training record exists and, if it has an expiry date, whether it is valid as of a caller-supplied assessment date.
Produce a deterministic gap list (missing or expired competencies) and a compliant list (satisfied competencies).
Compose a fixed-format draft summary, mirroring the DRAFT — PENDING ... convention used by Document Generator and Incident Investigation.
This mirrors Incident Investigation's Phase 4 boundary: deterministic validation/composition only, no LLM call, no generative inference.
3. Explicit Non-Goals
No qualitative judgment of whether completed training was adequate, sufficient, or of acceptable quality — record presence/validity only.
No integration with external LMS/training-provider APIs (deferred).
No historical trend analysis or reporting across time (deferred).
No auto-scheduling of refresher training or notifications (deferred).
No fabrication of what competencies a role requires — the required-competency list must be caller-supplied; the agent never infers or defaults it (Zero Hallucination Policy, §6 point 4).
No new EnvelopeContent fields. Unlike Incident Investigation (which added five_whys, fishbone_causes, bowtie, investigator_signoff to the envelope schema), Training & Competency introduces no analogous structured fields to schema.py. Per this design freeze's constraint, all domain detail is conveyed through the existing answer (text) and missing_information (list[str]) fields only. This is a deliberate scope boundary, not an oversight — see §5 note.
No architecture changes to orchestrator.py beyond routing-table registration (same pattern as all four existing agents).
4. Request Schema
Mirrors IncidentInvestigationRequest's pattern (pydantic model, field_validator for non-blank checks, no defaults that mask missing input):
Field
Type
Notes
role_or_task
str
Non-blank (validator, same as incident_description)
assessment_date
str
ISO8601 date; non-blank
required_competencies
list[str]
Non-empty; entries non-blank
training_records
list[TrainingRecord]
May be empty (caller may supply zero records)
TrainingRecord (nested model, same nesting style as fishbone_causes: dict[FishboneCategory, list[str]]):
Field
Type
Notes
competency_name
str
Non-blank
completed
bool
—
completion_date
str | None
ISO8601 or null
expiry_date
str | None
ISO8601 or null; null = does not expire
issuing_body
str | None
Optional
API-layer request model (backend/app/api/training_competency.py) adds tenant_id: str and user_id: str | None = None, exactly as IncidentInvestigationRequest does at the API layer.
5. Response Schema (matching ResponseEnvelope exactly)
No fields beyond the existing ResponseEnvelope / base EnvelopeContent set are used:
Field
Value for this agent
content.answer
"DRAFT — PENDING HUMAN REVIEW\n..." text summary (role/task, satisfied count, gap count)
content.confidence_score
1.0 (deterministic composition, per IE/DocGen precedent)
content.confidence_basis
States deterministic comparison of caller-supplied records against caller-supplied requirements; no generative inference performed
content.five_whys / fishbone_causes / bowtie / investigator_signoff
Not used — remain None (these are IE-specific declared fields, left unset by this agent)
source_of_reasoning
[{"type": "structured_input", "ref": "caller_supplied_training_records:training_competency"}]
missing_information
List of gap descriptions, e.g. "missing: <competency>" / "expired: <competency> (expired <date>)" — empty list only if all required competencies are satisfied
assumptions_made
[]
applicable_standards
[]
human_review_required
True (always — see §7)
human_review_reason
"compliance_gap_flagged" if missing_information non-empty, else "statutory_requirement"
Note: because no new envelope content fields are introduced, orchestrator.py's _ENVELOPE_ALLOWED_KEYS set requires no changes for this agent — every key it returns is already in that set.
6. Validation Rules
role_or_task, assessment_date: must not be blank (mirrors not_blank validator on incident_description / bowtie_top_event).
required_competencies: must be non-empty; no blank entries (mirrors five_whys_non_empty_entries).
TrainingRecord.competency_name: must not be blank.
Any validation failure raises InsufficientInformation — never defaults or guesses a value (Zero Hallucination Policy, §6 point 4), identical to both existing agents' contract.
Expiry comparison is a straight date comparison against assessment_date; no timezone or fuzzy-date inference.
7. Human Review Policy
Every response has human_review_required = True, unconditionally — matching Incident Investigation's unconditional True (competency sign-off is safety-relevant, same as RCA sign-off). human_review_reason is selected deterministically from the existing four-value HumanReviewReason enum based on whether a gap exists; no new enum value is introduced.
8. Audit Behaviour
No changes to audit/log.py or AuditEventType. The agent's invocation flows through the orchestrator's existing AGENT_INVOCATION event type exactly as Document Generator and Incident Investigation do:
Success: audit entry with outcome: "success" and verification metadata, appended before envelope assembly (ordering preserved per orchestrator's documented invariant).
InsufficientInformation: audit entry with outcome: "insufficient_information", envelope returned with confidence_score=0.0, human_review_reason="low_confidence".
Unexpected exception: audit entry with outcome: "error", exception re-raised (not swallowed) — identical to current orchestrator behaviour for all agents.
9. API Endpoint Specification
New file: backend/app/api/training_competency.py, following incident_investigation.py exactly:
POST /training-competency
Request body: API-layer pydantic model (§4) with tenant_id, user_id.
response_model=ResponseEnvelope.
Handler builds a plain dict from the validated payload (excluding tenant_id/user_id) and calls orchestrator.handle(operation_type="training_competency", request=request, tenant_id=payload.tenant_id, user_id=payload.user_id).
Router registered in backend/app/main.py alongside the existing four routers (same registration mechanism already used).
10. Orchestrator Integration
Orchestrator.__init__ gains one new constructor parameter, training_competency_agent: Agent, stored and added to self._routing:
self._routing = {
    "document_generation": document_generator_agent,
    "risk_assessment": risk_assessment_agent,
    "ptw_jsa": ptw_jsa_agent,
    "incident_investigation": incident_investigation_agent,
    "training_competency": training_competency_agent,
}
No other change to handle(), _ENVELOPE_ALLOWED_KEYS, error handling, or verification flow (VerifierAgent is domain-agnostic and requires no modification, consistent with its current usage across all four agents). backend/app/bootstrap.py wiring (not shown in provided context, but implied by from app.bootstrap import orchestrator in the API layer) needs the new agent instantiated and passed in — flagged here as a required wiring point, not a design change.
11. Unit Tests
Agent-level (TrainingCompetencyAgent.run), mirroring IncidentInvestigationAgent test shape:
All required competencies present and unexpired → missing_information == [], human_review_reason == "statutory_requirement".
One or more required competencies absent from training_records → each appears in missing_information, human_review_reason == "compliance_gap_flagged".
A record present but expiry_date before assessment_date → reported as expired in missing_information.
A record present with completed=False → treated as not satisfying the requirement.
Blank role_or_task / assessment_date → raises InsufficientInformation.
Empty required_competencies → raises InsufficientInformation.
Blank competency_name in a training record → raises InsufficientInformation.
confidence_score is always 1.0; source_of_reasoning always contains exactly one structured_input entry.
12. Integration Tests
Orchestrator routes operation_type="training_competency" to TrainingCompetencyAgent and no other agent.
Audit log receives exactly one AGENT_INVOCATION entry per call, with correct outcome for success / InsufficientInformation / error paths.
Envelope assembled by EnvelopeAssembler contains only keys within _ENVELOPE_ALLOWED_KEYS; no dropped keys are logged for this agent (since it introduces none).
VerifierAgent.run executes against this agent's result dict without modification or error.
Unknown operation_type still falls through to the existing "Unknown operation_type" branch unaffected by the new routing entry.
13. End-to-End Acceptance Tests
POST /training-competency with a fully-compliant payload → 200, envelope with human_review_required=True, human_review_reason="statutory_requirement", missing_information=[].
POST /training-competency with one expired and one missing competency → 200, missing_information contains both, human_review_reason="compliance_gap_flagged".
POST /training-competency with invalid payload (e.g. empty required_competencies) → envelope reflects insufficient_information path (confidence_score=0.0, human_review_reason="low_confidence"), not an HTTP 500.
Response in all cases validates against ResponseEnvelope with no extra/unexpected fields.
14. Phase 4B Exit Criteria
TrainingCompetencyAgent implemented and passing all unit tests in §11.
/training-competency endpoint implemented and passing all integration/E2E tests in §12–13.
Orchestrator routing entry added and covered by integration tests; no changes required to (and none made to) _ENVELOPE_ALLOWED_KEYS or schema.py.
Agent registered in bootstrap.py wiring.
8/8 planned agents implemented (Phase 4B is the final agent milestone).
ROADMAP.md and MEMORY.md updated to reflect 8/8 completion only after all tests above pass — not before, per repository convention.
