# MEMORY.md — Shield EPC AI Platform

## 1. Project Overview

Shield EPC AI Platform is an enterprise AI safety platform built around a multi-agent backend architecture. The system coordinates a set of specialized AI agents through a central orchestrator to generate, verify, and manage safety and compliance documentation for EPC (Engineering, Procurement, Construction) operations — including permits, risk assessments, hazard analysis, and incident investigations.

Repository: `Tarunrbt/Shield-EPC-V0` (branch: `main`)

## 2. Current Implementation Status

- **Planned agents:** 8
- **Implemented:** 7
- **Remaining:** 1

| Agent | Status |
|---|---|
| Orchestrator | Built and Tested |
| Document Generator | Built and Tested |
| Verifier | Built and Tested |
| Compliance | Built and Tested |
| Risk Assessment | Built and Tested |
| PTW/JSA | Built and Tested |
| Incident Investigation (Phase 4A) | Built and Tested |
| Training & Competency (Phase 4B) | Not Yet Implemented |

## 3. Completed Milestones

- Core orchestrator wired to all built agents
- Document Generator, Verifier, Compliance, Risk Assessment, and PTW/JSA agents built and tested
- Incident Investigation agent completed (Phase 4A)
- Backend module structure established (`agents/`, `api/`, `audit/`, `db/`, `envelope/`, `hazards/`, `services/`)
- API routes live: `generate`, `incident_investigation`, `health`, `tenants`, `projects`
- Documentation set established under `backend/docs/`: PRD.md, ARCHITECTURE.md, DESIGN.md, PHASES.md, RULES.md
- Top-level docs in place: README.md, ROADMAP.md, ARCHITECTURE.md
- Repository documentation synchronized with current implementation

## 4. Current Architecture Summary

Backend structure (`backend/app/`):

```
backend/app/
├── agents/       # Individual AI agent implementations
├── api/          # API route definitions
├── audit/        # Audit logging / traceability
├── db/           # Database layer
├── envelope/     # Request/response envelope handling
├── hazards/      # Hazard-related domain logic
├── services/     # Shared service layer
├── orchestrator.py
└── main.py
```

The orchestrator coordinates agent calls; each built agent (Document Generator, Verifier, Compliance, Risk Assessment, PTW/JSA, Incident Investigation) is invoked through it. Detailed architectural decisions live in `backend/docs/ARCHITECTURE.md` and the top-level `ARCHITECTURE.md`.

## 5. Documentation Inventory

Top level:
- `README.md`
- `ROADMAP.md`
- `ARCHITECTURE.md`

`backend/docs/`:
- `PRD.md`
- `ARCHITECTURE.md`
- `DESIGN.md`
- `PHASES.md`
- `RULES.md`
- `MEMORY.md` (this file)

## 6. Current Active Development Phase

**Phase 4A — Incident Investigation Agent:** Complete (built and tested).

Active focus is the transition into **Phase 4B**.

## 7. Next Planned Phase

**Phase 4B — Training & Competency Agent** (not yet implemented). This is the final agent needed to reach the full planned set of 8 agents.

## 8. Pending Tasks

- Implement the Training & Competency Agent (Phase 4B)
- Integrate Training & Competency Agent into the orchestrator
- Extend API routes to expose Training & Competency functionality
- Update PHASES.md and ROADMAP.md once Phase 4B is complete (not part of this task)

## 9. Repository Conventions

- Documentation lives under `backend/docs/` for backend-specific docs; project-level docs (`README.md`, `ROADMAP.md`, `ARCHITECTURE.md`) live at the repository root.
- Existing completed documentation files (PRD.md, ARCHITECTURE.md, DESIGN.md, PHASES.md, RULES.md) are not to be rewritten or regenerated — only additive, targeted edits are made to the codebase and docs.
- Agents are organized under `backend/app/agents/`, with orchestration handled centrally by `orchestrator.py`.
- Repository state (`main` branch) is treated as the single source of truth for implementation status.

## 10. Last Updated Summary

- **Implemented agents:** 7 of 8
- **Last completed phase:** Phase 4A — Incident Investigation Agent
- **Next planned phase:** Phase 4B — Training & Competency Agent
- **Documentation status:** Synchronized with implementation; MEMORY.md completed as the current reference file
