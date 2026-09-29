"""PHILO-10-01: the Send records (``design/send-lifecycle.md`` section 1).

``channel_destinations``: the saved destinations. A row never changes its
target: Edit parks the old row and makes a new one; Remove parks it.

``channel_sends``: one row per send, from prepare to its end. The frozen target
and the exact transport bytes (``payload``) with their digest. Every state move
is ONE conditional write (``... WHERE state=?``): prepared -> dispatching (the
dispatch boundary, committed before any effect), dispatching -> sent | failed |
unknown (the settle, in the transaction of the kernel's terminal receipt), and
prepared -> discarded. No move out of sent, failed, unknown or discarded.

:func:`settle_in_transaction` is the ONE settle write: the send's service, the
liveness reaper and the startup recovery all call it on the connection of the
kernel's terminal transaction, so the row, its history row and the receipt
commit together.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from .base import BaseRepository

SETTLED_STATES = frozenset({"sent", "failed", "unknown"})
FINAL_STATES = SETTLED_STATES | {"discarded"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def target_digest(channel: str, account: Mapping[str, Any], target: Mapping[str, Any]) -> str:
    """sha256 of channel + account + target_json (design section 1)."""
    material = canonical_json({"channel": channel, "account": dict(account), "target": dict(target)})
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def delivery_id_for(operation_id: str) -> str:
    """The history row's id, derived from the send operation (one per operation)."""
    return "pdel_" + hashlib.sha256(str(operation_id).encode()).hexdigest()[:16]


def settle_in_transaction(conn: Any, *, send_operation_id: str, state: str, reason: Optional[str],
                          proof: Optional[Mapping[str, Any]], delivered_to: str) -> Optional[dict[str, Any]]:
    """dispatching -> sent | failed | unknown, and the history row for sent and unknown.

    ONE conditional write on the caller's connection (the kernel's terminal
    transaction). ``None`` when no row of this operation is ``dispatching``
    (nothing moves). The history row goes to ``project_update_deliveries`` for
    a ``project_update:`` document (the Room reads its history from that one
    table); its ``operation_id`` is the send operation, so there is one per send.
    """
    if state not in SETTLED_STATES:
        raise ValueError(f"not a settled state: {state}")
    row = conn.execute("SELECT * FROM channel_sends WHERE send_operation_id=? AND state='dispatching'",
                       (send_operation_id,)).fetchone()
    if row is None:
        return None
    settled_at = now_iso()
    proof_json = canonical_json(dict(proof)) if proof else None
    changed = conn.execute(
        "UPDATE channel_sends SET state=?, reason=?, proof_json=?, settled_at=? "
        "WHERE id=? AND state='dispatching' AND send_operation_id=?",
        (state, reason, proof_json, settled_at, row["id"], send_operation_id),
    ).rowcount
    if changed != 1:
        return None
    document_ref = str(row["document_ref"])
    if state in {"sent", "unknown"} and document_ref.startswith("project_update:"):
        update_id = document_ref.split(":", 1)[1]
        update = conn.execute("SELECT project_id FROM project_updates WHERE id=?", (update_id,)).fetchone()
        if update is not None:
            conn.execute(
                "INSERT INTO project_update_deliveries (id, update_id, project_id, delivered_at, delivered_to,"
                " operation_id, channel, send_id, outcome, proof_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (delivery_id_for(send_operation_id), update_id, update["project_id"],
                 row["dispatch_started_at"] or settled_at, delivered_to, send_operation_id, row["channel"],
                 row["id"], state, proof_json),
            )
    return dict(conn.execute("SELECT * FROM channel_sends WHERE id=?", (row["id"],)).fetchone())


class ChannelDestinationsRepository(BaseRepository):
    """The saved destinations (no secret; park, never delete)."""

    table = "channel_destinations"  # registration anchor

    def get(self, destination_id: str) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM channel_destinations WHERE id=?", (str(destination_id),)).fetchone()
        return dict(row) if row is not None else None

    def list(self, *, include_parked: bool = False) -> list[dict[str, Any]]:
        sql = "SELECT * FROM channel_destinations"
        if not include_parked:
            sql += " WHERE state='active'"
        with self._connection() as conn:
            return [dict(r) for r in conn.execute(sql + " ORDER BY created_at, rowid")]

    @staticmethod
    def insert_in_transaction(conn: Any, *, destination_id: str, name: str, channel: str,
                              account: Mapping[str, Any], target: Mapping[str, Any], synced: bool) -> None:
        conn.execute(
            "INSERT INTO channel_destinations (id, name, channel, account_json, target_json, target_digest, synced,"
            " state, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)",
            (destination_id, name, channel, canonical_json(dict(account)), canonical_json(dict(target)),
             target_digest(channel, account, target), 1 if synced else 0, now_iso()),
        )

    @staticmethod
    def park_in_transaction(conn: Any, destination_id: str) -> bool:
        return conn.execute(
            "UPDATE channel_destinations SET state='parked', parked_at=? WHERE id=? AND state='active'",
            (now_iso(), str(destination_id)),
        ).rowcount == 1


class ChannelSendsRepository(BaseRepository):
    """The send rows (prepare to end; one conditional write per move)."""

    table = "channel_sends"  # registration anchor

    def get(self, send_id: str) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM channel_sends WHERE id=?", (str(send_id),)).fetchone()
        return dict(row) if row is not None else None

    def by_operation(self, *, send_operation_id: str = "", prepare_operation_id: str = "") -> Optional[dict[str, Any]]:
        column, value = (("send_operation_id", send_operation_id) if send_operation_id
                         else ("prepare_operation_id", prepare_operation_id))
        with self._connection() as conn:
            row = conn.execute(f"SELECT * FROM channel_sends WHERE {column}=?", (str(value),)).fetchone()
        return dict(row) if row is not None else None

    def list_for_document(self, document_ref: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM channel_sends WHERE document_ref=? ORDER BY created_at, rowid", (document_ref,))]

    def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connection() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM channel_sends ORDER BY created_at DESC, rowid DESC LIMIT ?", (int(limit),))]
