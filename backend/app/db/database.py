"""
SQLite connection management for Shield EPC operational persistence.

This is the development/local persistence layer. Per
docs/ShieldEPC_Architecture_Spec_v1.md §9, the target server architecture is
Postgres with row-level security; SQLite here is a transitional
implementation, not the final target. The audit ledger (app/audit/log.py)
is intentionally NOT part of this module or its schema -- §7 requires the
audit log to be a separate store from the operational DB.

Connections are opened per-call (sqlite3 connections are cheap, and this
avoids cross-thread sharing issues under a single uvicorn worker). Revisit
if this becomes a bottleneck.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import DB_PATH


def get_connection(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection_scope(db_path: str | Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    """
    Yields a connection; commits on success, rolls back on exception,
    always closes. Use this in repository implementations rather than
    calling get_connection() directly.
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema(db_path: str | Path = DB_PATH) -> None:
    """
    Placeholder for schema creation. Persistence Phase 2 adds the actual
    CREATE TABLE statements here (tenant, project, etc.). Intentionally
    empty in Phase 1 -- infra only, no entities defined yet.
    """
    pass
