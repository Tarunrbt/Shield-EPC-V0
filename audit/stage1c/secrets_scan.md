# Secrets Scan — Stage 1c

Scope: repository-wide search for potential secrets and secret references. Per audit rules, only search; no values are printed. Redaction style: show variable/key name but never secret value.

NOTE ABOUT SCOPE AND LIMITATIONS
- Evidence comes only from repository files examined in this session (files committed on branch main). I cannot access GitHub Actions secret values or the GitHub UI to verify secret contents or presence — such checks require repository access or a user-provided screenshot. Where evidence is missing the finding is marked UNVERIFIED.
- Code-search results may be incomplete. To view the repository and run further searches in the GitHub UI: https://github.com/Tarunrbt/Shield-EPC-V0

Findings

1) .github/workflows/multi-agent-review.yml — GitHub Actions secret references (High confidence)
- File: .github/workflows/multi-agent-review.yml
- Lines / snippets (redacted preview):
  - Line 57: GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  - Line 68: CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
  - Line 78: GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
  - Line 87: DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
  - Line 96: GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }} (used for REPORT stage)
  - Line 98: OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
- Provider(s) implied: Gemini, Claude/Anthropic, Groq, DeepSeek, OpenAI (report stage)
- Redacted preview examples: ${{ secrets.GEMINI_API_KEY }}, ${{ secrets.CLAUDE_API_KEY }}, ${{ secrets.OPENAI_API_KEY }}
- Confidence: High (explicit secret references present in committed workflow YAML)
- Evidence: .github/workflows/multi-agent-review.yml lines 55–104 (workflow file retrieved from repo; see URL: https://github.com/Tarunrbt/Shield-EPC-V0/blob/main/.github/workflows/multi-agent-review.yml)

2) ai-agents/orchestrator/providers.py — provider required_env entries (High confidence)
- File: ai-agents/orchestrator/providers.py
- Snippet (redacted preview / evidence): providers mapping lists required environment variable names, e.g. "required_env": ["CLAUDE_API_KEY"] and PREPROCESS_REQUIRED_ENV = ["GEMINI_API_KEY"]
- Provider(s) implied: CLAUDE_API_KEY, GROQ_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY
- Confidence: High (explicit variable names are present in committed Python file)
- Evidence: ai-agents/orchestrator/providers.py (committed file listing required_env keys)

3) ai-agents/pipeline/* scripts — runtime environment variable checks (High confidence)
- Files / lines:
  - ai-agents/pipeline/gemini_preprocess.py — contains `api_key = os.environ.get("GEMINI_API_KEY")` and exits when unset (evidence: file content lines in pipeline/gemini_preprocess.py)
  - ai-agents/pipeline/claude_validate.py — contains `api_key = os.environ.get("CLAUDE_API_KEY")` (evidence in file)
  - ai-agents/pipeline/groq_validate.py — contains `api_key = os.environ.get("GROQ_API_KEY")` (evidence in file)
  - ai-agents/pipeline/deepseek_validate.py — contains `api_key = os.environ.get("DEEPSEEK_API_KEY")` (evidence in file)
  - ai-agents/pipeline/chatgpt_report.py — checks `OPENAI_API_KEY` when REPORT_PROVIDER=openai (evidence in file)
- Redacted preview examples: os.environ.get("GEMINI_API_KEY") → <redacted>
- Confidence: High (explicit environment variable usage found in committed code)
- Evidence: ai-agents/pipeline/*.py (files retrieved from repo)

4) docs/HERMES.md and docs/Release_Notes.md — environment variable documentation (Medium confidence)
- Files: docs/HERMES.md (Environment variables section), Release_Notes.md (mentions secret names and states these were "confirmed via a screenshot you provided")
- Redacted preview examples: GEMINI_API_KEY, CLAUDE_API_KEY, OPENAI_API_KEY (listed as environment requirements / documented variables)
- Confidence: Medium — file-level documentation lists env var names (evidence present). Release_Notes.md claims secrets were confirmed via a screenshot; that claim is an external assertion recorded in the repo (see Release_Notes.md), but the screenshot is not in the repository — therefore the claim about actual secret values is UNVERIFIED here.
- Evidence: docs/HERMES.md (Environment variables listing), Release_Notes.md (section stating screenshot-based confirmation)

Searches for likely-committed secret values (credential-like patterns)
- I searched the repository for common secret prefixes/patterns (sk-, ghp_, AKIA, -----BEGIN PRIVATE KEY, etc.) via code search in this session; no matches were returned by the corpus searches performed here. (Search tooling in this session is limited; results may be incomplete.)
- Evidence: lexical/code-search attempts and file content inspections; no committed API keys or private key blocks were found in the scanned files returned by the API.
- Confidence: Medium (searches did not return credential-like tokens in examined files; however repository-wide search in the GitHub UI or a local clone with regex checks would be required for exhaustive verification)

Secret-exposure status summary
- Secrets referenced by name (env var / GitHub secrets): GEMINI_API_KEY, CLAUDE_API_KEY, GROQ_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY — evidence present in workflow YAML, pipeline scripts, and provider registry.
- Actual secret values: UNVERIFIED by this audit (no secret values are present in committed files found in this session; to confirm presence/absence of values in GitHub Actions UI or repository metadata requires access beyond the repository contents and/or a user-provided screenshot). Release_Notes.md notes a user-provided screenshot showing secrets in the GitHub UI; that external artifact is not part of the repository and thus treated as UNVERIFIED for machine-verifiable claims in this audit.

Recommendations (audit-only)
- Do not commit secret values to the repository. Evidence shows the code correctly references secrets via environment variables and GitHub Actions `${{ secrets.* }}` (Good).
- Verify that all required runtime secrets are stored in GitHub Actions Secrets (or an equivalent secrets manager) and that no credentials are present in the repository history or other files — requires administrative access to the repository or a local clone + history scan (UNVERIFIED by repo-only scan).
- If you want, I can provide a small local-scan script (git clone + git grep + regex checks) to run in your environment to produce exhaustive verifiable evidence (checksums / exact matches) — I did not run local commands in this session per your instructions.

If you want me to proceed with a second pass (local/sandbox execution) produce the repository clone outputs, or upload the screenshot you mentioned and I will mark the screenshot-backed claims as verified.
