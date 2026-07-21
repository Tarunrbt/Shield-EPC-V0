# Shield EPC — ADR Current Register

Governed by [docs/ADR_INDEX.md](./ADR_INDEX.md) — read that file first for the status model, evidence types, promotion rules, and review policy. This file holds only the operational content: the actual table of architectural decisions and their status. Every row is an independently reviewable claim with its own evidence, tagged per the evidence types defined in ADR_INDEX.md.

## Current Register

| ID | Decision | Status | Evidence | Source |
|---|---|---|---|---|
| ADR-000 | Foundational architecture record for the Shield EPC platform — covers architectural philosophy, high-level architecture, agent roster, orchestrator design, mandatory output envelope, zero-hallucination policy, auditability, human-in-the-loop gate policy, multi-tenancy, offline-first mobile, security, and phased build order | Accepted | Spec | `docs/ShieldEPC_Architecture_Spec_v1.md` — self-identified as "**Status**: Draft for review — treat as ADR-000 (foundational architecture record)" (line 5); document itself states it should be treated as ADR-000 and frozen section-by-section as sections are validated (closing note, line 276) |

**On decomposition**: `docs/ShieldEPC_Architecture_Spec_v1.md` is currently one undivided ADR-000 covering twelve sections (§1–§12). No evidence was found that any of these sections have been split into independent, separately-tracked ADRs within this repository. A reference to "ADR-009" appears at line 72, but in context it refers to a *different* project (ShieldGate), cited as a precedent for the bounded-context pattern — not a Shield EPC ADR. Until direct evidence shows a section of ADR-000 has been split out and independently accepted/verified, it stays as one row. Do not decompose speculatively.

`ARCHITECTURE.md`'s "Frozen v1.0" header status and ADR-000's own "Draft for review" status are also inconsistent with each other and with the Promotion Rule in ADR_INDEX.md (Frozen requires Verified Stable). Flagged, not resolved, pending maintainer clarification.
