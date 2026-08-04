"""
Hermes Orchestrator — Phase 2 (local CLI, provider/router abstraction).

Coordinates the existing pipeline scripts as subprocesses, using
router.py to resolve which script/provider to run and providers.py as
the source of truth for provider metadata. Hermes itself still does
not call any AI provider directly — see docs/HERMES.md.

Usage:
    python3 ai-agents/orchestrator/hermes_agent.py --input docs/AI_AGENT_STANDARDS.md
    python3 ai-agents/orchestrator/hermes_agent.py --skip-stage1 --input docs/AI_AGENT_STANDARDS.md

See docs/HERMES.md for environment variables and provider details.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from router import (
    RoutingError,
    resolve_preprocess,
    resolve_validation_provider,
    resolve_report_provider,
)

from state import load_state, save_state, clear_state

STAGE1_OUT = "stage1_normalized.json"
STAGE2_OUT = "stage2_validated.json"
REPORT_MD = "Verification_Report.md"
REPORT_JSON = "Verification_Report.json"


def run_stage(name, cmd):
    print(f"\n[HERMES] --- {name} ---")
    print(f"[HERMES] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[HERMES] ::error:: {name} failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"[HERMES] {name} completed successfully.")


def require_env(stage_name, missing):
    if missing:
        print(
            f"[HERMES] ::error:: {stage_name} is missing required environment "
            f"variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Hermes Orchestrator (Phase 2 — router/providers)")
    parser.add_argument("--input", required=True, help="Path to the document/artifact to review")
    parser.add_argument(
        "--skip-stage1",
        action="store_true",
        help="Skip Stage 1 (Gemini) and reuse an existing stage1_normalized.json.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from the last successfully completed stage.",
    )
    args = parser.parse_args()

    skip_stage1 = args.skip_stage1 or os.environ.get("SKIP_STAGE1") == "1"

    resume = args.resume
    state = load_state() if resume else None

    resume_from = None
    if resume:
        if state is None:
            print(
                "[HERMES] ::error:: --resume was set but no .hermes_state.json "
                "was found. Run the full pipeline first (without --resume).",
                file=sys.stderr,
            )
            sys.exit(1)
        last = state.get("last_completed_stage")
        if last not in ("stage1", "stage2"):
            print(
                f"[HERMES] ::error:: .hermes_state.json has an unsupported "
                f"last_completed_stage: {last!r}. Delete .hermes_state.json "
                f"and run the full pipeline.",
                file=sys.stderr,
            )
            sys.exit(1)
        resume_from = last
        print(f"[HERMES] --resume: resuming after '{resume_from}' (from .hermes_state.json).")

    validation_provider = os.environ.get("VALIDATION_PROVIDER", "")
    report_provider = os.environ.get("REPORT_PROVIDER", "")

    try:
        validator_script, validator_missing = resolve_validation_provider(validation_provider)
        report_script, report_missing = resolve_report_provider(report_provider)
    except RoutingError as e:
        print(f"[HERMES] ::error:: {e}", file=sys.stderr)
        sys.exit(1)

    # Stage 1 - Gemini preprocessing
    if resume_from in ("stage1", "stage2"):
        print("\n[HERMES] --- Stage 1 - Gemini preprocessing (SKIPPED — resuming) ---")
        if not os.path.exists(STAGE1_OUT):
            print(
                f"::error::--resume requires an existing {STAGE1_OUT} but it was not found.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"[HERMES] Reusing existing {STAGE1_OUT}.")
    elif skip_stage1:
        print("\n[HERMES] --- Stage 1 - Gemini preprocessing (SKIPPED) ---")
        if not os.path.exists(STAGE1_OUT):
            print(
                f"::error::--skip-stage1 was set but {STAGE1_OUT} does not exist.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"[HERMES] Reusing existing {STAGE1_OUT}.")
        save_state("stage1", {"stage1": STAGE1_OUT})
    else:
        preprocess_script, preprocess_missing = resolve_preprocess()
        require_env("Stage 1 - Gemini preprocessing", preprocess_missing)
        run_stage(
            "Stage 1 - Gemini preprocessing",
            [
                "python3", str(preprocess_script),
                "--input", args.input,
                "--output", STAGE1_OUT,
            ],
        )
        save_state("stage1", {"stage1": STAGE1_OUT})

    # Stage 2 - validation
    if resume_from == "stage2":
        print("\n[HERMES] --- Stage 2 - validation (SKIPPED — resuming) ---")
        if not os.path.exists(STAGE2_OUT):
            print(
                f"::error::--resume requires an existing {STAGE2_OUT} but it was not found.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"[HERMES] Reusing existing {STAGE2_OUT}.")
    else:
        require_env(f"Stage 2 - {validation_provider} validation", validator_missing)
        run_stage(
            f"Stage 2 - {validation_provider} validation",
            [
                "python3", str(validator_script),
                "--input", STAGE1_OUT,
                "--output", STAGE2_OUT,
            ],
        )
        save_state("stage2", {"stage1": STAGE1_OUT, "stage2": STAGE2_OUT})

    # Stage 3 - report generation
    require_env(f"Stage 3 - {report_provider} report", report_missing)
    run_stage(
        "Stage 3 - report generation",
        [
            "python3", str(report_script),
            "--input", STAGE2_OUT,
            "--output-md", REPORT_MD,
            "--output-json", REPORT_JSON,
        ],
    )

    clear_state()
    print("\n[HERMES] Pipeline completed successfully.")
    print(f"[HERMES] Outputs: {STAGE1_OUT}, {STAGE2_OUT}, {REPORT_MD}, {REPORT_JSON}")
    print("[HERMES] Human review is required before approval or merge.")


if __name__ == "__main__":
    main()
