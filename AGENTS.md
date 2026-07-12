# AGENTS.md — Shield EPC

This is the universal fallback instruction file, read by any AI coding agent that doesn't have a dedicated config path (and by Kiro alongside its steering files). If your tool has a dedicated config — `.cursor/rules/`, `.github/copilot-instructions.md`, `.kiro/steering/`, `.windsurf/rules/` / `.devin/rules/`, `CLAUDE.md` — use that instead; this file exists so nothing falls through the gap for tools not listed there.

**Canonical standards live in `docs/AI_AGENT_STANDARDS.md`. Read it in full before making changes to this repository.**

Summary, if you only read one paragraph: this is a safety-critical HSE platform. AI recommends, humans decide. No AI output reaches a field action, compliance verdict, or permit issuance without passing through the canonical two-human-decision-point flow in `docs/ShieldEPC_Architecture_Spec_v1.md` §8.1. Every domain agent must implement the mandatory response envelope (spec §5) — no free-form output ships. Changes to frozen architecture require a new `ARCHITECTURE_REVIEW.md` entry before they're considered done. No direct commits to `main`. When uncertain whether something is routine or architectural, ask rather than guess.

Read order: `README.md` → `ARCHITECTURE.md` → `docs/ShieldEPC_Architecture_Spec_v1.md` → `ROADMAP.md` → `ARCHITECTURE_REVIEW.md` → `docs/AI_AGENT_STANDARDS.md` for full detail.
