"""
Hermes Phase 3 — manual resume state.

Tracks which stage last completed successfully so a failed run can be
resumed with --resume instead of re-running the entire pipeline. State
is written only after a stage succeeds, and cleared once the full
pipeline completes. Resume is manual only — Hermes never auto-retries
a failed stage.
"""

import json
import os

STATE_FILE = ".hermes_state.json"


def save_state(last_completed_stage, outputs):
    state = {
        "last_completed_stage": last_completed_stage,
        "status": "ok",
        "outputs": outputs,
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def clear_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
