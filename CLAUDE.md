# CLAUDE.md — Shield EPC

**Note**: this file wasn't in your original list (`.cursor`, `.github`, `.kiro`, `.windsurf`) — adding it because Claude Code is Anthropic's own agentic coding tool and reads specifically from `CLAUDE.md`, not `AGENTS.md`. If you don't plan to use Claude Code on this repo, this file is harmless to leave in place; delete it if you'd rather keep the config surface to exactly the four tools you named.

Canonical standards: `docs/AI_AGENT_STANDARDS.md`. This file is a pointer, not a duplicate.

## Read before acting

`README.md` → `ARCHITECTURE.md` → `docs/ShieldEPC_Architecture_Spec_v1.md` → `ROADMAP.md` → `ARCHITECTURE_REVIEW.md`.

## Human-in-the-loop is mandatory, not a style preference

No AI-generated output — from Shield EPC's own domain agents, or from code changes you make to them — reaches a field action, compliance verdict, or permit issuance without the canonical flow in spec §8.1: **AI Observation → Assign for Review → Supervisor Approval (role-gated, distinct user) → Auditor Assignment → Field Action**, every transition audit-logged. Treat any shortcut around this as a defect to flag, not a convenience to implement, even if the request driving the change didn't explicitly ask you to preserve it.

## Response envelope — mandatory for every domain agent

confidence_score + confidence_basis, source_of_reasoning, missing_information, assumptions_made, applicable_standards, human_review_required, audit_trail_id. Full schema: spec §5. An agent returning free-form output without this envelope is non-compliant regardless of answer quality.

## Coding standards

- Backend/agents: Python, type-hinted
- Frontend: TypeScript, strict mode
- No fabricated APIs, packages, or config options — verify rather than generate against an assumption
- Retrieval-grounded generation only for Compliance/Risk Assessment logic; `insufficient_information` beats a guess

## Process

- No direct commits to `main` — all changes via PR, human-reviewed and human-merged
- Changes to frozen architecture require a new `ARCHITECTURE_REVIEW.md` entry first
- Docs and `CHANGELOG.md` updates ship in the same change as the code
- If a task seems to require bypassing any of the above, stop and ask rather than proceeding

Full detail on naming conventions, project structure, and security standards: `docs/AI_AGENT_STANDARDS.md`.
