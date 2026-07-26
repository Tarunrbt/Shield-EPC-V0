"""
Hermes Orchestrator — Phase 1 (local CLI only).

Coordinates the existing pipeline scripts (gemini_preprocess.py,
{claude,groq,deepseek}_validate.py, chatgpt_report.py) as subprocesses,
in the same order and with the same file contract as
.github/workflows/multi-agent-review.yml.

This is a coordination layer only — it does not call any AI provider
directly and does not duplicate provider logic. All actual inference
happens in the existing pipeline scripts.

Usage:
    python3 ai-agents/orchestrator/hermes_agent.py --input docs/AI_AGENT_STANDARDS.md

    # Skip Stage 1 (useful when the local environment can't run
    # google-genai, e.g. Termux + Python 3.14 cryptography ABI issues).
    # Requires an existing stage1_normalized.json in the working directory.
    python3 ai-agents/orchestrator/hermes_agent.py --skip-stage1 --input docs/AI_AGENT_STANDARDS.md

Environment variables (same as the GitHub Actions workflow):
    GEMINI_API_KEY, GEMINI_MODEL
    VALIDATION_PROVIDER (claude | groq | deepseek)
    CLAUDE_API_KEY, CLAUDE_MODEL
    GROQ_API_KEY
    DEEPSEEK_API_KEY
    REPORT_PROVIDER (groq | openai)
    GROQ_REPORT_MODEL
    OPENAI_API_KEY, OPENAI_MODEL

    SKIP_STAGE1=1  (equivalent to --skip-stage1)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent / "pipeline"

STAGE1_OUT = "stage1_normalized.json"
STAGE2_OUT = "stage2_validated.json"
REPORT_MD = "Verification_Report.md"
REPORT_JSON = "Verification_Report.json"

VALIDATOR_SCRIPTS = {
    "claude": "claude_validate.py",
    "groq": "groq_validate.py",
    "deepseek": "deepseek_validate.py",
}


def run_stage(name, cmd):
    print(f"\n[HERMES] --- {name} ---")
    print(f"[HERMES] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[HERMES] ::error:: {name} failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"[HERMES] {name} completed successfully.")


def main():
    parser = argparse.ArgumentParser(description="Hermes Orchestrator (Phase 1 — local CLI)")
    parser.add_argument("--input", required=True, help="Path to the document/artifact to review")
    parser.add_argument(
        "--skip-stage1",
        action="store_true",
        help="Skip Stage 1 (Gemini) and reuse an existing stage1_normalized.json. "
             "Useful when the local environment can't run google-genai.",
    )
    args = parser.parse_args()

    skip_stage1 = args.skip_stage1 or os.environ.get("SKIP_STAGE1") == "1"

    validation_provider = os.environ.get("VALIDATION_PROVIDER", "").strip().lower()
    if validation_provider not in VALIDATOR_SCRIPTS:
        print(
            "::error::VALIDATION_PROVIDER must be one of "
            f"{list(VALIDATOR_SCRIPTS.keys())} (got: '{validation_provider or '<unset>'}').",
            file=sys.stderr,
        )
        sys.exit(1)

    validator_script = PIPELINE_DIR / VALIDATOR_SCRIPTS[validation_provider]

    # Stage 1 - Gemini preprocessing
    if skip_stage1:
        print("\n[HERMES] --- Stage 1 - Gemini preprocessing (SKIPPED) ---")
        if not os.path.exists(STAGE1_OUT):
            print(
                f"::error::--skip-stage1 was set but {STAGE1_OUT} does not exist. "
                "Provide an existing Stage 1 output file to skip Stage 1.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"[HERMES] Reusing existing {STAGE1_OUT}.")
    else:
        run_stage(
            "Stage 1 - Gemini preprocessing",
            [
                "python3", str(PIPELINE_DIR / "gemini_preprocess.py"),
                "--input", args.input,
                "--output", STAGE1_OUT,
            ],
        )

    # Stage 2 - validation (provider selected via VALIDATION_PROVIDER)
    run_stage(
        f"Stage 2 - {validation_provider} validation",
        [
            "python3", str(validator_script),
            "--input", STAGE1_OUT,
            "--output", STAGE2_OUT,
        ],
    )

    # Stage 3 - report generation
    run_stage(
        "Stage 3 - report generation",
        [
            "python3", str(PIPELINE_DIR / "chatgpt_report.py"),
            "--input", STAGE2_OUT,
            "--output-md", REPORT_MD,
            "--output-json", REPORT_JSON,
        ],
    )

    print("\n[HERMES] Pipeline completed successfully.")
    print(f"[HERMES] Outputs: {STAGE1_OUT}, {STAGE2_OUT}, {REPORT_MD}, {REPORT_JSON}")
    print("[HERMES] Human review is required before approval or merge.")


if __name__ == "__main__":
    main()
