"""
Append-only, hash-chained audit log.

Source of truth: docs/ShieldEPC_Architecture_Spec_v1.md §7.

Phase 1 scaffold note: this is a JSONL file store, not the multi-tenant
operational DB — that's intentional. §7 requires the audit ledger to be a
"separate store from operational DB (so it can't be edited by
application-layer bugs or bad actors with app-DB access)". A JSONL file
satisfies "separate store" for the scaffold and keeps this module's public
interface (append/verify_chain) stable when it's later swapped for a real
dedicated ledger store — nothing above this module needs to change.

Each entry embeds the SHA-256 hash of the previous entry (§7: "hash-chain
the audit log entries ... so tampering is detectable even by an insider
with DB access"). entry #1's prev_hash is a fixed genesis value.
"""

from __future__ import annotations

import hashlib
import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

GENESIS_HASH = "0" * 64


class AuditEventType(str, Enum):
    AGENT_INVOCATION = "agent_invocation"
    HUMAN_REVIEW_ACTION = "human_review_action"
    DOCUMENT_VERSION = "document_version"


@dataclass
class AuditEntry:
    entry_id: str
    event_type: AuditEventType
    timestamp: str
    tenant_id: str
    user_id: Optional[str]
    payload: dict[str, Any]
    prev_hash: str
    entry_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.entry_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        canonical = json.dumps(
            {
                "entry_id": self.entry_id,
                "event_type": self.event_type.value,
                "timestamp": self.timestamp,
                "tenant_id": self.tenant_id,
                "user_id": self.user_id,
                "payload": self.payload,
                "prev_hash": self.prev_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_json_line(self) -> str:
        return json.dumps(
            {
                "entry_id": self.entry_id,
                "event_type": self.event_type.value,
                "timestamp": self.timestamp,
                "tenant_id": self.tenant_id,
                "user_id": self.user_id,
                "payload": self.payload,
                "prev_hash": self.prev_hash,
                "entry_hash": self.entry_hash,
            },
            sort_keys=True,
        )


class AuditLog:
    """
    Thread-safe, append-only, hash-chained audit log backed by a JSONL file.

    Not multi-process safe (no file locking) — fine for a single-process
    Phase 1 scaffold, must be revisited before this runs under multiple
    uvicorn workers.
    """

    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        if not self._path.exists():
            self._path.touch()

    def _last_hash(self) -> str:
        last_line = None
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    last_line = line
        if last_line is None:
            return GENESIS_HASH
        return json.loads(last_line)["entry_hash"]

    def append(
        self,
        event_type: AuditEventType,
        tenant_id: str,
        payload: dict[str, Any],
        user_id: Optional[str] = None,
    ) -> AuditEntry:
        with self._lock:
            entry = AuditEntry(
                entry_id=str(uuid.uuid4()),
                event_type=event_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                tenant_id=tenant_id,
                user_id=user_id,
                payload=payload,
                prev_hash=self._last_hash(),
            )
            with self._path.open("a", encoding="utf-8") as f:
                f.write(entry.to_json_line() + "\n")
            return entry

    def read_all(self) -> list[dict[str, Any]]:
        entries = []
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def verify_chain(self) -> bool:
        expected_prev = GENESIS_HASH
        for raw in self.read_all():
            recomputed = AuditEntry(
                entry_id=raw["entry_id"],
                event_type=AuditEventType(raw["event_type"]),
                timestamp=raw["timestamp"],
                tenant_id=raw["tenant_id"],
                user_id=raw["user_id"],
                payload=raw["payload"],
                prev_hash=raw["prev_hash"],
            )
            if recomputed.entry_hash != raw["entry_hash"]:
                return False
            if raw["prev_hash"] != expected_prev:
                return False
            expected_prev = raw["entry_hash"]
        return True
