# Shield EPC — Instructions for GitHub Copilot

Full standards: `docs/AI_AGENT_STANDARDS.md` — this file summarizes; that file is authoritative.

## Read before acting

`README.md` → `ARCHITECTURE.md` → `docs/ShieldEPC_Architecture_Spec_v1.md` → `ROADMAP.md` → `ARCHITECTURE_REVIEW.md`.

## Human-in-the-loop is mandatory, not a preference

No AI output — from Shield EPC's own domain agents, or from code you generate that touches them — reaches a field action, compliance verdict, or permit issuance without passing through the canonical flow in `docs/ShieldEPC_Architecture_Spec_v1.md` §8.1:

**AI Observation → Assign for Review → Supervisor Approval (role-gated) → Auditor Assignment → Field Action**, every transition audit-logged.

Any code path that could let an AI output trigger a real-world action in fewer than two independent human decision points is a defect. Flag it rather than shipping it, even if the immediate task didn't ask you to check for this.

## Response envelope is mandatory for all domain agents

Every agent (Risk Assessment, Compliance, Incident Investigation, Document Generator, PTW/JSA, Training & Competency, Verifier) must return: `confidence_score` + `confidence_basis`, `source_of_reasoning`, `missing_information`, `assumptions_made`, `applicable_standards`, `human_review_required`, `audit_trail_id`. See spec §5 for the full schema.

## Coding standards

- Backend/agents: Python, type-hinted
- Frontend: TypeScript, strict mode, no untyped `any` without justification
- No fabricated APIs or packages — verify before generating
- Retrieval-grounded generation only for Compliance/Risk Assessment logic — return `insufficient_information` rather than guessing when retrieval comes up empty

## Process rules

- No direct commits to `main`; all changes via PR, human-reviewed and human-merged
- Changes to frozen architecture require a new `ARCHITECTURE_REVIEW.md` entry before the code change is considered complete
- Documentation and `CHANGELOG.md` updates ship in the same PR as the code change, not after
- When uncertain whether a change is routine or architectural, treat it as architectural and ask

Full detail on naming conventions, project structure, and security standards: `docs/AI_AGENT_STANDARDS.md`.
