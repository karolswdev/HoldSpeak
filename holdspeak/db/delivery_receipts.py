"""Command receipt persistence (HS-94-06) — both halves.

Node half: :class:`NodeReceiptLedger`, a durable standalone SQLite
ledger mapping ``command_id`` → the exact receipt the node produced,
plus the per-target expected-sequence counters. Duplicates return the
SAME receipt without re-execution; the ledger's ``epoch`` (minted once
at creation) is how a hub distinguishes "this node never executed it"
from "this node lost the ledger across an unclean reset"
(PLATFORM-CONTRACT §8.2 → ``indeterminate_after_node_reset``).

Hub half: :class:`DeliveryCommandReceiptRepository` over the hub
database — the durable aggregate Receipt joining what the hub sent
(hash/head only; the full payload is never retained merely because it
crossed the node link, §8.1) with the node's stored receipt by
``command_id``.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

from .base import BaseRepository

LEDGER_SCHEMA = 1
LEDGER_MAX_ROWS = 5000
DEFAULT_LEDGER_PATH = Path.home() / ".holdspeak" / "node_command_ledger.db"

HUB_STATES = (
    "sent",
    "claimed",
    "unknown",
    "complete",
    "not_executed",
    "indeterminate_after_node_reset",
)

_LEDGER_SQL = """
CREATE TABLE IF NOT EXISTS ledger_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS command_receipts (
    command_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL DEFAULT '',
    receipt_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_command_receipts_created
ON command_receipts(created_at);
CREATE TABLE IF NOT EXISTS target_sequences (
    target_id TEXT PRIMARY KEY,
    next_sequence INTEGER NOT NULL DEFAULT 1
);
"""


class NodeReceiptLedger:
    """The node's durable deduplication ledger.

    Retention is bounded (newest :data:`LEDGER_MAX_ROWS` kept) — long
    enough to cover client reconciliation and node reconnect, small
    enough to stay boring.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else DEFAULT_LEDGER_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(_LEDGER_SQL)
            conn.execute(
                "INSERT OR IGNORE INTO ledger_meta (key, value) VALUES (?, ?)",
                ("epoch", "epoch_" + uuid.uuid4().hex[:16]),
            )
            conn.execute(
                "INSERT OR IGNORE INTO ledger_meta (key, value) VALUES (?, ?)",
                ("ledger_schema", str(LEDGER_SCHEMA)),
            )

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    @property
    def epoch(self) -> str:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM ledger_meta WHERE key = 'epoch'"
            ).fetchone()
        return str(row["value"]) if row else ""

    def get(self, command_id: str) -> Optional[dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT receipt_json FROM command_receipts WHERE command_id = ?",
                (str(command_id),),
            ).fetchone()
        if row is None:
            return None
        try:
            parsed = json.loads(row["receipt_json"])
        except ValueError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def next_sequence(self, target_id: str) -> int:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT next_sequence FROM target_sequences WHERE target_id = ?",
                (str(target_id),),
            ).fetchone()
        return int(row["next_sequence"]) if row else 1

    def commit(
        self,
        command_id: str,
        receipt: dict[str, Any],
        *,
        target_id: str = "",
        advance_sequence: bool = False,
    ) -> None:
        """Persist the dedup result — and, when the command consumed its
        sequence slot, advance the target's counter in the SAME
        transaction (§8 step 8: persist before the receipt is final)."""
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO command_receipts "
                "(command_id, target_id, receipt_json) VALUES (?, ?, ?)",
                (
                    str(command_id),
                    str(target_id),
                    json.dumps(receipt, separators=(",", ":"), sort_keys=True),
                ),
            )
            if advance_sequence and target_id:
                conn.execute(
                    "INSERT INTO target_sequences (target_id, next_sequence) "
                    "VALUES (?, 2) "
                    "ON CONFLICT(target_id) DO UPDATE SET "
                    "next_sequence = next_sequence + 1",
                    (str(target_id),),
                )
            conn.execute(
                "DELETE FROM command_receipts WHERE command_id IN ("
                "SELECT command_id FROM command_receipts "
                "ORDER BY created_at DESC, rowid DESC "
                "LIMIT -1 OFFSET ?)",
                (LEDGER_MAX_ROWS,),
            )


class DeliveryCommandReceiptRepository(BaseRepository):
    """Hub half of the aggregate Receipt (table
    ``delivery_command_receipts``): what was sent (hash/head only),
    to which node/target/generation, under which authority, and — once
    the node answers — the joined node receipt."""

    def record_sent(
        self, envelope: dict[str, Any], *, dispatch_epoch: Optional[str] = None
    ) -> None:
        target = dict(envelope.get("target") or {})
        operation = dict(envelope.get("operation") or {})
        authority = dict(envelope.get("authority") or {})
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO delivery_command_receipts
                    (command_id, node_id, target_id, target_generation,
                     operation_family, operation_verb, payload_sha256,
                     payload_head, expected_sequence, issued_at, expires_at,
                     dispatch_epoch, hub_state, authority_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'sent', ?)
                """,
                (
                    str(envelope.get("command_id")),
                    str(target.get("node_id") or ""),
                    str(target.get("target_id") or ""),
                    str(target.get("target_generation") or ""),
                    str(operation.get("family") or ""),
                    str(operation.get("verb") or ""),
                    str(envelope.get("payload_sha256") or ""),
                    str(envelope.get("payload_head") or ""),
                    envelope.get("expected_sequence"),
                    str(envelope.get("issued_at") or ""),
                    str(envelope.get("expires_at") or ""),
                    dispatch_epoch,
                    self._json_dumps(authority, fallback="{}"),
                ),
            )

    def set_state(self, command_id: str, state: str) -> None:
        if state not in HUB_STATES:
            raise ValueError(f"unknown hub receipt state: {state!r}")
        with self._connection() as conn:
            conn.execute(
                "UPDATE delivery_command_receipts "
                "SET hub_state = ?, updated_at = datetime('now') "
                "WHERE command_id = ?",
                (state, str(command_id)),
            )

    def attach_receipt(self, receipt: dict[str, Any]) -> None:
        """Join the node half by command_id. Idempotent: the first
        stored receipt wins (a duplicate is the SAME receipt by the
        node's dedup contract)."""
        with self._connection() as conn:
            conn.execute(
                "UPDATE delivery_command_receipts "
                "SET receipt_id = COALESCE(receipt_id, ?), "
                "    receipt_json = CASE WHEN receipt_json = '{}' THEN ? "
                "                        ELSE receipt_json END, "
                "    hub_state = 'complete', "
                "    updated_at = datetime('now') "
                "WHERE command_id = ?",
                (
                    str(receipt.get("receipt_id") or ""),
                    self._json_dumps(dict(receipt), fallback="{}"),
                    str(receipt.get("command_id")),
                ),
            )

    def get(self, command_id: str) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM delivery_command_receipts WHERE command_id = ?",
                (str(command_id),),
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["authority"] = self._json_loads_dict(data.pop("authority_json", "{}"))
        receipt = self._json_loads_dict(data.pop("receipt_json", "{}"))
        data["receipt"] = receipt or None
        return data

    def pending_for_node(self, node_id: str, *, limit: int = 16) -> list[str]:
        """Command ids sent to a node that have no joined receipt yet —
        the reconcile sweep's worklist."""
        limit = max(1, min(int(limit), 100))
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT command_id FROM delivery_command_receipts "
                "WHERE node_id = ? AND hub_state IN ('sent', 'claimed', 'unknown') "
                "ORDER BY created_at ASC LIMIT ?",
                (str(node_id), limit),
            ).fetchall()
        return [str(row["command_id"]) for row in rows]


__all__ = [
    "DEFAULT_LEDGER_PATH",
    "DeliveryCommandReceiptRepository",
    "HUB_STATES",
    "LEDGER_MAX_ROWS",
    "NodeReceiptLedger",
]
