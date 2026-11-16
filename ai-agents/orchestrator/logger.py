"""
Run Logger — Self-Improvement Layer, Level 1 (Shield EPC HSE pipeline)

Only job: record what happened during a pipeline run.
Does NOT call any AI provider. Does NOT change safety rules,
scoring, or pipeline behavior. Append-only.
"""

import json
import time
import uuid
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "audit" / "learning"
LOG_FILE = LOG_DIR / "run_history.jsonl"


def log_run(stage, status, input_file=None, output_file=None,
            provider=None, duration_seconds=None, error=None, notes=None):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        "run_id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "stage": stage,
        "provider": provider,
        "input_file": input_file,
        "output_file": output_file,
        "status": status,
        "duration_seconds": duration_seconds,
        "error": error,
        "notes": notes,
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

    return record


if __name__ == "__main__":
    log_run(stage="stage1_preprocess", provider="gemini",
             input_file="docs/AI_AGENT_STANDARDS.md",
             output_file="stage1_normalized.json",
             status="success", duration_seconds=4.2)

    log_run(stage="stage2_validation", provider="claude",
             input_file="stage1_normalized.json",
             output_file="stage2_validated.json",
             status="failed",
             error="architecture bypass mitigation missing",
             notes="matches earlier Verification_Report.json finding")

    print(f"Wrote test records to {LOG_FILE}")
