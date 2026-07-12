# Shield EPC — Rules for Cascade (Windsurf)

> **Note on naming**: Windsurf was rebranded to Devin Desktop by Cognition on 2 June 2026, and the Cascade agent is being folded into Devin Local. This file (`.windsurf/rules/`) still works and is read as a fallback, but current builds prefer `.devin/rules/` — an identical copy is maintained there. Keep both in sync until you've fully migrated tooling; don't let one silently go stale.

Canonical standards: `docs/AI_AGENT_STANDARDS.md`. This file is a pointer, not the source of truth.

## Read before acting

`README.md` → `ARCHITECTURE.md` → `docs/ShieldEPC_Architecture_Spec_v1.md` → `ROADMAP.md` → `ARCHITECTURE_REVIEW.md`.

## Human-in-the-loop is mandatory

No AI output reaches a field action, compliance verdict, or permit issuance without the canonical flow (full spec §8.1): **AI Observation → Assign for Review → Supervisor Approval (role-gated) → Auditor Assignment → Field Action**, every step audit-logged. Given Cascade/Devin's autonomous, multi-step execution style, this matters more here than in tools that require step-by-step confirmation by design — do not let an autonomous run collapse this flow into a single action, even if it seems like the efficient path to complete a task.

## Response envelope (mandatory, all domain agents)

confidence_score + confidence_basis, source_of_reasoning, missing_information, assumptions_made, applicable_standards, human_review_required, audit_trail_id (full spec §5).

## Coding defaults

Python (type-hinted) for backend/agents; TypeScript (strict) for frontend. No fabricated APIs or packages. Retrieval-grounded generation only for Compliance/Risk Assessment — return `insufficient_information` rather than a best-effort guess.

## Process — applies to autonomous execution too

No direct commits to `main`. All changes via PR, human-reviewed and human-merged — this includes autonomous multi-step runs; don't merge your own work even if the task appeared complete. Changes to frozen architecture require a new `ARCHITECTURE_REVIEW.md` entry before the code change is considered done. Docs and `CHANGELOG.md` update in the same change as the code.

If a task seems to require bypassing any of the above to finish faster, stop and ask instead of proceeding autonomously through it.

Full detail: `docs/AI_AGENT_STANDARDS.md`.
