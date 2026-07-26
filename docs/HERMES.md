# Hermes Orchestrator

## Status: Phase 1 (local CLI only) — Complete

## Purpose

Hermes is a coordination layer for the existing Gemini → Validation →
Report pipeline. It runs the existing pipeline scripts
(`gemini_preprocess.py`, `{claude,groq,deepseek}_validate.py`,
`chatgpt_report.py`) as subprocesses, in the same order and with the
same file contract as `.github/workflows/multi-agent-review.yml`.

**Hermes does not call any AI provider directly and does not duplicate
provider logic.** All actual inference happens in the existing pipeline
scripts under `ai-agents/pipeline/`. Hermes only decides what to run,
in what order, and stops on the first failure.

## Why it exists

Running the pipeline previously required either:
- Manually running each of the 3 pipeline scripts one at a time, or
- Pushing to GitHub and waiting for Actions to run

Hermes lets you run the full pipeline locally, in Termux, with one
command — useful for fast iteration before pushing.

## Architecture

Developer -> hermes_agent.py (coordinator, no AI calls itself) which runs:
Stage 1: gemini_preprocess.py -> stage1_normalized.json
Stage 2: {provider}_validate.py -> stage2_validated.json
Stage 3: chatgpt_report.py -> Verification_Report.md and .json

Each stage is run as a separate subprocess (subprocess.run), matching
how GitHub Actions runs each step.

## CLI usage

python3 ai-agents/orchestrator/hermes_agent.py --input docs/AI_AGENT_STANDARDS.md

### --skip-stage1

Skips Stage 1 (Gemini) and reuses an existing stage1_normalized.json
in the working directory. Required on Termux due to a known Gemini SDK
issue (see Known Limitations below).

python3 ai-agents/orchestrator/hermes_agent.py --skip-stage1 --input docs/AI_AGENT_STANDARDS.md

Equivalent environment variable: SKIP_STAGE1=1

## Environment variables

Same variables as the GitHub Actions workflow (.github/workflows/multi-agent-review.yml):

- GEMINI_API_KEY, GEMINI_MODEL — Stage 1 (not needed with --skip-stage1)
- VALIDATION_PROVIDER — Stage 2, must be claude, groq, or deepseek
- CLAUDE_API_KEY, CLAUDE_MODEL — Stage 2 if claude
- GROQ_API_KEY — Stage 2 if groq, and Stage 3 if REPORT_PROVIDER=groq
- DEEPSEEK_API_KEY — Stage 2 if deepseek, requires account balance
- REPORT_PROVIDER — Stage 3, must be groq or openai
- GROQ_REPORT_MODEL — Stage 3 if REPORT_PROVIDER=groq
- OPENAI_API_KEY, OPENAI_MODEL — Stage 3 if REPORT_PROVIDER=openai

Example known-working local setup (Groq for both stages, free tier):

export VALIDATION_PROVIDER=groq
export REPORT_PROVIDER=groq
export GROQ_REPORT_MODEL="openai/gpt-oss-120b"
export GROQ_API_KEY="<your key>"

## Output files

Written to the current working directory (not committed, see .gitignore):

- stage1_normalized.json — Stage 1 output (or reused input if --skip-stage1)
- stage2_validated.json — Stage 2 validation result
- Verification_Report.md — Stage 3 human-readable report
- Verification_Report.json — Stage 3 machine-readable report

## Known limitations

### Gemini (Stage 1) does not run on Termux with Python 3.14

google-genai transitively depends on google-auth then cryptography.
On Termux with Python 3.14, cryptography's Rust binding fails to load
with: ImportError: dlopen failed: cannot locate symbol "PyLong_Type"
referenced by cryptography/hazmat/bindings/_rust.abi3.so

This is an environment/ABI compatibility issue between Python 3.14 and
the cryptography package's compiled extension, not a bug in this
repo's code. The same code runs successfully in GitHub Actions
(Ubuntu, Python 3.12).

Workaround: use --skip-stage1 with a pre-existing
stage1_normalized.json (e.g. downloaded from a GitHub Actions run's
artifacts, or hand-written for testing coordination logic only, not a
substitute for a real Stage 1 run).

Possible future fixes (not yet implemented):
- Run Stage 1 in a Python 3.12/3.13 virtual environment on-device
- Replace google-genai with direct REST calls (requests/httpx) for
  Stage 1, removing the google-auth/cryptography dependency chain

### Validation failures are not bugs

If Stage 2 reports "checks_passed": false, this usually means the
validator correctly caught a real issue (e.g. Stage 1 envelope schema
mismatch), not that Hermes or the pipeline is broken. Check the note
field in stage2_validated.json for the specific reason before
assuming something needs fixing in Hermes itself.

## Roadmap

1. Phase 1 — local CLI orchestrator (this document) — Complete
2. Documentation (this file) — Complete
3. Resume/retry support (rerun only the failed stage)
4. Provider abstraction (providers.py)
5. Router abstraction (router.py)
6. Optional GitHub Actions integration (replacing the current
   per-stage if: conditionals with a single Hermes step) — only if
   this proves to have a clear benefit over the current working
   workflow.
