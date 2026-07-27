# Shield EPC — ADR Current Register

Governed by [docs/ADR_INDEX.md](./ADR_INDEX.md) — read that file first for the status model, evidence types, promotion rules, and review policy. This file holds only the operational content: the actual table of architectural decisions and their status. Every row is an independently reviewable claim with its own evidence, tagged per the evidence types defined in ADR_INDEX.md.

## Current Register

| ID | Decision | Status | Evidence | Source |
|---|---|---|---|---|
| ADR-000 | Foundational architecture record for the Shield EPC platform — covers architectural philosophy, high-level architecture, agent roster, orchestrator design, mandatory output envelope, zero-hallucination policy, auditability, human-in-the-loop gate policy, multi-tenancy, offline-first mobile, security, and phased build order | Open | Spec | `docs/ShieldEPC_Architecture_Spec_v1.md` — self-identified as "**Status**: Draft for review — treat as ADR-000 (foundational architecture record)" (line 5); document itself states it should be treated as ADR-000 and frozen section-by-section as sections are validated (closing note, line 276) |

**On decomposition**: `docs/ShieldEPC_Architecture_Spec_v1.md` is currently one undivided ADR-000 covering twelve sections (§1–§12). No evidence was found that any of these sections have been split into independent, separately-tracked ADRs within this repository. A reference to "ADR-009" appears at line 72, but in context it refers to a *different* project (ShieldGate), cited as a precedent for the bounded-context pattern — not a Shield EPC ADR. Until direct evidence shows a section of ADR-000 has been split out and independently accepted/verified, it stays as one row. Do not decompose speculatively.

Resolved (F5, 27 Jul 2026): ADR-000 register status set to Open, aligning with the underlying spec document's self-declared "Draft for review" status (`docs/ShieldEPC_Architecture_Spec_v1.md`, line 5). ARCHITECTURE.md's status line ("Accepted (v1.0) — pending Verified Stable per ADR promotion rules") describes a separate document — ARCHITECTURE.md is a distinct summary/overview document that lists the spec as "Related," not identical (confirmed: ARCHITECTURE.md line 6, no "ADR-000" reference in its status block). The two statuses are independent and do not require alignment. Promotion path for ADR-000: Open → Accepted requires formal spec review; Accepted → Verified Stable requires source-code confirmation per Promotion Rule.


| P9-C | Open, documented gap. No dedicated test evidence found for ai-agents/orchestrator/router.py or providers.py routing/env-validation logic. backend/tests/test_orchestrator.py covers a different module (app.orchestrator.Orchestrator). Test-writing scoped to a separate future phase, not blocking current architecture review closure. |

| P9-D | Open, documented gap. Phase 2 completion claim ("both tests (happy path + error handling) pass") is unverifiable against current repo state — no test file for router.py/providers.py found in docs/HERMES.md, commit d53619a's file list, or CI workflow (.github/workflows/multi-agent-review.yml). Claim not confirmed false, only unsupported by persisted evidence. Resolution deferred to same future test-writing phase as P9-C. |
