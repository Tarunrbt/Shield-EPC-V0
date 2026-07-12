# Shield EPC — AI Agent Configuration Standards

**Status**: Active — canonical source
**Last updated**: 11 Jul 2026
**Applies to**: Every AI coding assistant used on this repository (Cursor, GitHub Copilot, Kiro, Windsurf/Devin, Claude Code, or any other tool) — present or future.

---

## Why this file exists, and why the tool-specific files don't duplicate it

Every AI coding tool reads its config from a different path with a different format (full list with exact paths: §11 below). If the actual standards were copy-pasted into four-plus separate files, they will drift — someone updates the Cursor rules after a review finding and forgets Copilot's file exists. That's the same single-source-of-truth failure this project has already been built to avoid at the architecture level (see `ARCHITECTURE.md` — "Why this structure"). The same discipline applies here: **this file is the only place these standards are written out in full.** Every tool-specific config file is a short adapter that points here plus whatever tool-specific activation syntax that tool requires.

If you're an AI agent reading this through a tool-specific file: read this document in full before making any change to this repository. If the tool-specific file and this file ever conflict, this file wins — the tool-specific file is stale and should be corrected.

---

## 1. Source of Truth Hierarchy

Read in this order before acting on any request:

1. **`README.md`** — orientation, repo map
2. **`ARCHITECTURE.md`** — frozen vision, core principles, layer diagram (root-level, concise)
3. **`docs/ShieldEPC_Architecture_Spec_v1.md`** — full detailed spec: agent roster, response envelope schema, gate policy, canonical flows
4. **`ROADMAP.md`** — current phase, what's in scope now, exit criteria
5. **`ARCHITECTURE_REVIEW.md`** — review log; check for open findings before touching an area that was previously flagged
6. **`CHANGELOG.md`** — what has already shipped

If a request conflicts with something frozen in `ARCHITECTURE.md` or the full spec, **stop and flag the conflict rather than resolving it unilaterally.** Architecture changes go through a logged review (§6), not a silent code change.

---

## 2. Mandatory Human-in-the-Loop Policy

This is the single most important constraint on this codebase. It is not a style preference.

- No AI-generated output (from Shield EPC's own agents, or from your work as a coding assistant modifying agent code) reaches a field action, a compliance verdict, or a permit issuance without passing through the canonical flow in `docs/ShieldEPC_Architecture_Spec_v1.md` §8.1: **AI Observation → Assign for Review → Supervisor Approval (role-gated) → Auditor Assignment → Field Action**, every transition audit-logged.
- Any UI control, API endpoint, or agent function that could let an AI output trigger a real-world action in fewer than two independent human decision points is a defect — flag it, do not ship it, even if the request that generated it didn't ask you to check for this.
- Do not "simplify" this flow to make a feature easier to build. If a task seems to require collapsing a gate, stop and ask rather than proceeding.

---

## 3. Coding Standards

Defaults below apply until Phase 1 stack decisions are formally recorded in `docs/ShieldEPC_Architecture_Spec_v1.md`. If you're starting new code and the stack isn't yet locked, follow these defaults rather than picking your own:

- **Backend / AI agents**: Python, type-hinted (no untyped function signatures in new code). Matches the existing HSE Toolkit precedent.
- **Frontend**: TypeScript, strict mode. No `any` in new code without an inline comment explaining why it's unavoidable.
- **No fabricated APIs, packages, or config options.** If you're not certain a library function exists as you're describing it, say so and verify rather than generating plausible-looking code against it.
- **Every domain agent (Risk Assessment, Compliance, Incident Investigation, Document Generator, PTW/JSA, Training & Competency, Verifier) must implement the mandatory response envelope** (`docs/ShieldEPC_Architecture_Spec_v1.md` §5) — confidence_score with confidence_basis, source_of_reasoning, missing_information, assumptions_made, applicable_standards, human_review_required, audit_trail_id. An agent that returns free-form output without this envelope is non-compliant, regardless of how good the underlying answer is.
- **Retrieval-grounded generation only** for anything Compliance or Risk Assessment related — no filling a gap with a plausible-sounding default (§6 of the full spec). If retrieval returns nothing relevant, the correct code path returns `insufficient_information`, not a best-effort guess.

---

## 4. Naming Conventions

- **Files**: `snake_case` for Python, `kebab-case` for TypeScript/React component files, `PascalCase` for React component names.
- **Agents**: named for their single responsibility, matching the roster in the full spec exactly (`risk_assessment_agent`, `compliance_agent`, `incident_investigation_agent`, `document_generator_agent`, `ptw_jsa_agent`, `training_competency_agent`, `verifier_agent`). Don't introduce a differently-named agent without adding it to the roster table first.
- **Branches**: `phase-<n>/<short-description>` (e.g., `phase-1/response-envelope`) so branch names map to `ROADMAP.md` phases.
- **Standards/clause references in code or data**: always include the dated version (e.g., `ISO_45001_2018_8_1_2`, not `ISO_45001_8_1_2`) — matches the Knowledge Graph versioning requirement in full spec §6.

---

## 5. Project Structure

Mirrors `README.md`'s repo map — don't introduce new top-level directories without updating that map:

```
docs/         — specs, ADRs, standards mapping, this file
frontend/     — web portal + mobile app
backend/      — API gateway, orchestrator, domain services
ai-agents/    — agent definitions, prompts, evaluation sets
assets/       — design assets, diagrams, brand materials
```

Domain agent code belongs under `ai-agents/<agent_name>/`. Shared envelope/audit-log logic used by all agents belongs in a shared location under `backend/`, not duplicated per-agent — duplicating the envelope implementation across seven agents is exactly the kind of drift this file exists to prevent.

---

## 6. Documentation Expectations

- Any change that touches a frozen architectural decision (agent boundaries, gate policy, envelope schema, canonical flows) requires a new dated entry in `ARCHITECTURE_REVIEW.md` **before** the code change is considered complete — follow the entry template already established there.
- Any new capability that ships gets a `CHANGELOG.md` entry in the same PR that ships it, not after.
- If a `ROADMAP.md` exit criterion is affected by your change (met, newly blocked, or newly required), update the checkbox/criterion in the same PR.
- Don't write documentation that restates what the code does line-by-line. Document decisions and reasoning — the "why," matching the standard already set in `ARCHITECTURE_REVIEW.md`.

---

## 7. Git Workflow

- No direct commits to `main`. All changes via PR.
- PR description must state: what phase/exit-criterion this addresses (if applicable), what was tested, and whether it touches anything in the Source of Truth Hierarchy (§1) — if yes, link the corresponding `ARCHITECTURE_REVIEW.md` entry.
- Commit messages: imperative mood, scoped prefix where useful (`agents:`, `frontend:`, `docs:`) — e.g., `agents: add missing_information field to compliance_agent envelope`.
- **AI coding agents do not merge their own PRs.** A human reviews and merges. This is the same human-in-the-loop principle from §2, applied to the development process itself, not just the product's runtime behavior.

---

## 8. Security Standards

- No secrets, API keys, or tenant data in code, comments, commit messages, or files under version control. Use the secrets manager referenced in the full spec §11.
- Service-to-service calls (agent-to-agent, agent-to-orchestrator) follow zero-trust verification, not implicit internal-network trust — matches the Auth layer requirement in `ARCHITECTURE.md`.
- Tenant isolation (row-level security, `tenant_id` scoping) is not optional in any new data-layer code — if you're writing a query against tenant data, it must be tenant-scoped, no exceptions for "just a quick internal tool."
- Treat all SCADA/IoT/ERP integration data as evidence, not ground truth, in any agent logic that consumes it — sensor drift and fault conditions are real (`ARCHITECTURE.md`, Layer 8 — Integration).
- PII/health-record fields require field-level encryption, not just table-level access control, per full spec §11.

---

## 9. AI Agents Must Not Bypass Approved Architecture or Review Process

This applies to you, the coding assistant, as much as it applies to the domain agents you're helping build:

- Do not implement a feature that routes around a documented gate (§2) because it's faster or the request didn't explicitly ask for the gate to be preserved. The gate is the default; removing it requires an explicit, reviewed decision.
- Do not alter a frozen section of `ARCHITECTURE.md` or the full spec without first creating an `ARCHITECTURE_REVIEW.md` entry describing what's changing and why, and getting human confirmation. "The user's most recent message implied this" is not sufficient authorization to change a frozen architectural decision — ask directly if a request seems to require one.
- Do not silently drop a `ROADMAP.md` exit criterion because it's inconvenient to satisfy. If a criterion genuinely needs to change, that's a roadmap edit with a stated reason, not an omission.
- When uncertain whether a change is a normal implementation task or an architectural change requiring review, treat it as the latter and ask. This mirrors §6 of the full spec (Zero Hallucination Policy) applied to your own behavior as a coding agent: when uncertain, request clarification instead of guessing.

---

## 10. What "Done" Means

A task is not complete because the code runs. It's complete when:
- It matches the response envelope schema, if it's agent-facing code (§3)
- It respects the human-in-the-loop gate, if it's anywhere near a field-action path (§2)
- Relevant docs are updated in the same change (§6)
- It's tenant-scoped and secrets-clean, if it touches data (§8)

If you're not sure a change meets all four, say so explicitly rather than presenting it as finished.

---

## 11. Tool-Specific Configuration Files — Full Map

Every file below is a thin pointer to this document. If you're editing standards, edit **this file only** — then check whether any pointer file's summary needs a matching one-line update (it shouldn't need more than that).

| Tool | Path | Format notes |
|---|---|---|
| Cursor | `.cursor/rules/project-standards.mdc` | Current `.mdc` directory format, not legacy `.cursorrules` |
| GitHub Copilot | `.github/copilot-instructions.md` | Standard path Copilot reads automatically |
| Kiro | `.kiro/steering/project-standards.md` | `inclusion: always` frontmatter |
| Windsurf / Cascade | `.windsurf/rules/project-standards.md` | Legacy-adjacent; still read as of this writing |
| Devin Desktop | `.devin/rules/project-standards.md` | Mirrored copy — Windsurf was rebranded to Devin Desktop by Cognition on 2 Jun 2026; current builds prefer this path |
| Claude Code | `CLAUDE.md` | Read from repo root |
| Any other tool | `AGENTS.md` | Universal fallback, repo root |

If a new AI tool is adopted, add one new pointer file here using that tool's real activation format (verify the tool's current docs — these paths and formats do change), and add a row to this table. Do not write the standards content itself anywhere but this file.
