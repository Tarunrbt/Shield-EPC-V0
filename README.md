# Shield EPC

Enterprise AI-powered HSE platform for EPC, Oil & Gas, Construction, Infrastructure, Manufacturing, and Industrial projects.

**Start here**: [`ARCHITECTURE.md`](./ARCHITECTURE.md) is the single source of truth for how this system is designed and why. Read it before touching code.

## Repository Map

| Path | Contents |
|---|---|
| `ARCHITECTURE.md` | Vision, core principles, system layer diagram |
| `ROADMAP.md` | Phased build plan |
| `ARCHITECTURE_REVIEW.md` | Design review log — findings, decisions, open questions |
| `CHANGELOG.md` | Version history |
| `LICENSE` | License terms |
| `AGENTS.md` | Universal AI agent instructions (fallback for tools without a dedicated config path) |
| `CLAUDE.md` | Claude Code instructions |
| `.cursor/rules/` | Cursor project rules |
| `.github/copilot-instructions.md` | GitHub Copilot instructions |
| `.kiro/steering/` | Kiro steering files |
| `.windsurf/rules/`, `.devin/rules/` | Windsurf/Cascade rules (mirrored — see note on the Devin Desktop rebrand inside) |
| `docs/` | Supporting documentation (specs, ADRs, standards mapping, `AI_AGENT_STANDARDS.md`) |
| `frontend/` | Web portal + mobile app (offline-first) |
| `backend/` | API gateway, orchestrator, domain services |
| `ai-agents/` | Agent definitions, prompts, evaluation sets; `ai-agents/pipeline/` holds stub scripts for the Gemini→Claude→ChatGPT review pipeline (not yet real API integrations) |
| `assets/` | Design assets, diagrams, brand materials |
| `.github/workflows/multi-agent-review.yml` | CI workflow scaffold for the review pipeline — exists, unexecuted, calls stub scripts |
| `Verification_Report.md`, `Consistency_Report.md`, `Final_Audit_Report.md`, `Release_Notes.md` | Point-in-time audit reports, dated — see each file's own date before relying on it |

## AI Agent Configuration

Every AI coding tool used on this repo — regardless of which one — is governed by a single canonical document: **`docs/AI_AGENT_STANDARDS.md`**. The tool-specific files above (`.cursor/rules/`, `.github/copilot-instructions.md`, `.kiro/steering/`, `.windsurf/rules/`, `CLAUDE.md`, `AGENTS.md`) are thin pointers to that document, not duplicates — this avoids the standards drifting out of sync across five-plus separate config files. If you add a new AI tool to your workflow, add a new pointer file in that tool's format; don't re-write the standards themselves anywhere but `docs/AI_AGENT_STANDARDS.md`.

## Status

Pre-implementation. Architecture frozen at v1.0, pending Phase 1 build (see `ROADMAP.md`).
