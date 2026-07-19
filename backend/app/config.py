"""
Application configuration, read from environment variables.

Kept minimal and explicit -- no config framework, just os.environ with
sensible local-dev defaults. Add entries here as new settings are
needed; do not scatter os.environ.get() calls across the codebase.
"""

from __future__ import annotations

import os
from pathlib import Path

# Where the hash-chained audit log JSONL file lives.
AUDIT_LOG_PATH: Path = Path(
    os.environ.get("AUDIT_LOG_PATH", "data/audit_log.jsonl")
)

# Path to the SQLite operational database (tenant/project data).
# Deliberately separate from AUDIT_LOG_PATH -- see app/audit/log.py and
# docs/ShieldEPC_Architecture_Spec_v1.md §7 (audit log must be a separate
# store from the operational DB).
DB_PATH: Path = Path(
    os.environ.get("DB_PATH", "data/shield_epc.db")
)
