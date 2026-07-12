# Changelog

All notable changes to the Shield EPC platform architecture and codebase are recorded here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Initial repository structure: docs/, frontend/, backend/, ai-agents/, assets/
- ARCHITECTURE.md — vision, core principles, layer diagram (v1.0, frozen)
- Full architecture spec (docs/ShieldEPC_Architecture_Spec_v1.md)
- Dashboard mockup audit and first-pass fixes (docs/ShieldEPC_Dashboard_Audit_v1.md)
- ROADMAP.md — Phase 1–5 build plan with dependencies and exit criteria, expanded from Architecture Spec §12 (draft v1.0)
- ARCHITECTURE_REVIEW.md — standardized review log template (entry structure, severity/status definitions) with dashboard audit reformatted as first full entry

### Changed
- Resolved F2 (one-tap "Deploy Auditor" action): confirmed intended behavior is not direct dispatch. Added canonical 5-state flow to `docs/ShieldEPC_Architecture_Spec_v1.md` §8.1 — AI Observation → Assign for Review → Supervisor Approval (role-gated) → Auditor Assignment → Field Action, every transition audit-logged
- `ARCHITECTURE.md` human-in-the-loop principle updated to reference §8.1
- `frontend/dashboard_mockup_v1.html` hazard card rebuilt to implement the full 5-state workflow with visible status badge and inline, timestamped audit trail (JS state machine — UI simulation only, not backend-enforced)
- `ARCHITECTURE_REVIEW.md` F2 marked Resolved; all 4 dashboard audit findings now closed
- `ROADMAP.md` Phase 1 exit criteria expanded: Auth layer must structurally prevent the same user from both assigning an observation for review and approving it as supervisor (surfaced by F2 resolution — role separation is not yet simulated in the mockup and must be enforced server-side)

### Added — AI Agent Configuration Layer
- `docs/AI_AGENT_STANDARDS.md` — canonical, single-source standards for any AI coding assistant working on this repo: source-of-truth hierarchy, mandatory human-in-the-loop policy, coding standards, naming conventions, project structure, documentation expectations, git workflow, security standards, and explicit prohibition on bypassing approved architecture/review process
- `.cursor/rules/project-standards.mdc` — Cursor (current `.mdc` format, not the legacy `.cursorrules` single file)
- `.github/copilot-instructions.md` — GitHub Copilot
- `.kiro/steering/project-standards.md` — Kiro
- `.windsurf/rules/project-standards.md` + `.devin/rules/project-standards.md` (mirrored) — Windsurf/Cascade, noting the 2 June 2026 Cognition rebrand to Devin Desktop
- `AGENTS.md` — universal fallback for any tool without a dedicated config path
- `CLAUDE.md` — Claude Code (added beyond the original four tools requested — flagged as optional, safe to remove if not needed)
- All tool-specific files are thin pointers to `docs/AI_AGENT_STANDARDS.md`, not duplicated content, to prevent standards drift across config files
- Note: original requested paths `.cursor/instructions.mdc` and `.windsurf/instructions.md` were corrected to the paths these tools actually read (`.cursor/rules/*.mdc`, `.windsurf/rules/*.md`) — verified against current tool documentation

### Fixed
- `docs/AI_AGENT_STANDARDS.md` — corrected a dangling cross-reference (intro text pointed to "§7" for tool-path info; §7 is actually Git Workflow) and a mis-cited source (SCADA/integration guidance was attributed to "full spec §3," which is the Agent Roster, not Integration — corrected to `ARCHITECTURE.md`, Layer 8) and an ambiguous internal reference (Knowledge Graph versioning cited bare "§6," which reads as this doc's own §6 Documentation Expectations; corrected to "full spec §6")
- `docs/AI_AGENT_STANDARDS.md` — added missing §11 (Tool-Specific Configuration Files — Full Map), closing the gap that caused the dangling §7 reference above; added a Zero Trust service-to-service bullet to §8 Security Standards, matching the Auth layer requirement already stated in `ARCHITECTURE.md`
- `ROADMAP.md` — corrected an imprecise citation ("Architecture §6.1," implying a subsection heading that doesn't exist in the full spec) to "Architecture §6, point 1"
- Full-repo consistency pass (11 Jul 2026): every `§N` reference across all 16 tracked files checked against the actual section maps of `ARCHITECTURE.md`, `docs/ShieldEPC_Architecture_Spec_v1.md`, and `docs/AI_AGENT_STANDARDS.md`; confirmed `docs/AI_AGENT_STANDARDS.md` has zero verbatim-sentence duplication with any tool-config adapter file; confirmed the five canonical flow status labels (AI Flagged, Pending Supervisor Review, Supervisor Approved, Auditor Assigned, Field Action Complete) match exactly between the full spec's §8.1 diagram and the dashboard mockup's JS state machine
- `docs/ShieldEPC_Dashboard_Audit_v1.md` — added a superseding status note; the original F2 "not a confirmed fix" line was stale now that `ARCHITECTURE_REVIEW.md` shows it Resolved

### Added — GitHub Actions & Multi-Agent Pipeline Scaffold (11 Jul 2026)
- `.github/workflows/multi-agent-review.yml` — CI workflow implementing the Gemini → Claude → ChatGPT review pipeline described in this session's request; references `CLAUDE_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY` (confirmed present as GitHub repository secrets via user-provided screenshot); includes an explicit human-review-required gate; does not auto-merge or auto-approve anything
- `ai-agents/pipeline/gemini_preprocess.py`, `claude_validate.py`, `chatgpt_report.py` — stub scripts defining the pipeline's I/O contract; **do not yet call any provider API** — each file documents this in its own header
- `Verification_Report.md`, `Consistency_Report.md`, `Final_Audit_Report.md`, `Release_Notes.md` — audit reports for this session, all explicitly distinguishing user-confirmed claims (GitHub secrets, via screenshot) from claims verified directly in-session (documentation consistency) from claims not yet true (workflow execution, real pipeline functionality)
- `README.md` repository map updated to include the new workflow, pipeline, and report files
