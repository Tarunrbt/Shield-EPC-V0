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
