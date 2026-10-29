"""The Phone store: four tables, static SQL only (``holdspeak/db/schema.py``).

``phone_devices``, ``phone_messages``, ``phone_calls`` and ``phone_events``.
Every write is a whole-row write of a known column set or one named column
update, so each statement prepares against the schema
(``tests/unit/test_static_sql_matches_schema.py``). The rules live in
:mod:`.service` and :mod:`.calls`; this module only reads and writes.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Optional

DEVICE_COLUMNS = ("id", "name", "platform", "push_token", "push_kind", "sip_identity", "jwt_kid", "state",
                  "paired_at", "last_seen_at", "revoked_at")
MESSAGE_COLUMNS = ("id", "seq", "direction", "text", "reply_to", "created_at", "delivered_at", "read_at",
                   "origin_ref", "program_step_id")
CALL_COLUMNS = ("id", "seq", "direction", "reason", "context_digest", "urgent", "state", "created_at",
                "answered_at", "ended_at", "end_reason", "transcript_ref", "decision_json", "transport",
                "calls_turn_id")

_DEVICE_UPSERT = (
    "INSERT INTO phone_devices (id, name, platform, push_token, push_kind, sip_identity, jwt_kid, state, "
    "paired_at, last_seen_at, revoked_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE "
    "SET name=excluded.name, platform=excluded.platform, push_token=excluded.push_token, "
    "push_kind=excluded.push_kind, sip_identity=excluded.sip_identity, jwt_kid=excluded.jwt_kid, "
    "state=excluded.state, paired_at=excluded.paired_at, last_seen_at=excluded.last_seen_at, "
    "revoked_at=excluded.revoked_at"
)
_MESSAGE_UPSERT = (
    "INSERT INTO phone_messages (id, seq, direction, text, reply_to, created_at, delivered_at, read_at, "
    "origin_ref, program_step_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE "
    "SET seq=excluded.seq, direction=excluded.direction, text=excluded.text, reply_to=excluded.reply_to, "
    "created_at=excluded.created_at, delivered_at=excluded.delivered_at, read_at=excluded.read_at, "
    "origin_ref=excluded.origin_ref, program_step_id=excluded.program_step_id"
)
_CALL_UPSERT = (
    "INSERT INTO phone_calls (id, seq, direction, reason, context_digest, urgent, state, created_at, "
    "answered_at, ended_at, end_reason, transcript_ref, decision_json, transport, calls_turn_id) VALUES "
    "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET seq=excluded.seq, "
    "direction=excluded.direction, reason=excluded.reason, context_digest=excluded.context_digest, "
    "urgent=excluded.urgent, state=excluded.state, created_at=excluded.created_at, "
    "answered_at=excluded.answered_at, ended_at=excluded.ended_at, end_reason=excluded.end_reason, "
    "transcript_ref=excluded.transcript_ref, decision_json=excluded.decision_json, "
    "transport=excluded.transport, calls_turn_id=excluded.calls_turn_id"
)


def _row(row: Any, columns: tuple[str, ...]) -> dict[str, Any]:
    return {key: row[key] for key in columns}


def _call(row: Any) -> dict[str, Any]:
    out = _row(row, CALL_COLUMNS)
    out["urgent"] = bool(out["urgent"])
    try:
        out["decision"] = json.loads(out.pop("decision_json") or "null")
    except ValueError:
        out["decision"] = None
    return out


class PhoneStore:
    """Reads and writes of the four Phone tables."""

    def __init__(self, db: Any) -> None:
        self._db = db

    # ── devices ──────────────────────────────────────────────────────

    def save_device(self, device: Mapping[str, Any]) -> None:
        with self._db._connection() as conn:
            conn.execute(_DEVICE_UPSERT, [device.get(key) for key in DEVICE_COLUMNS])

    def get_device(self, device_id: str) -> Optional[dict[str, Any]]:
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM phone_devices WHERE id=?", (device_id,)).fetchone()
        return _row(row, DEVICE_COLUMNS) if row is not None else None

    def device_by_kid(self, jwt_kid: str) -> Optional[dict[str, Any]]:
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM phone_devices WHERE jwt_kid=?", (jwt_kid,)).fetchone()
        return _row(row, DEVICE_COLUMNS) if row is not None else None

    def list_devices(self) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute("SELECT * FROM phone_devices ORDER BY paired_at DESC, id").fetchall()
        return [_row(row, DEVICE_COLUMNS) for row in rows]

    def touch_device(self, device_id: str, at: str) -> None:
        with self._db._connection() as conn:
            conn.execute("UPDATE phone_devices SET last_seen_at=? WHERE id=?", (at, device_id))

    # ── messages ─────────────────────────────────────────────────────

    def save_message(self, message: Mapping[str, Any]) -> None:
        with self._db._connection() as conn:
            conn.execute(_MESSAGE_UPSERT, [message.get(key) for key in MESSAGE_COLUMNS])

    def get_message(self, message_id: str) -> Optional[dict[str, Any]]:
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM phone_messages WHERE id=?", (message_id,)).fetchone()
        return _row(row, MESSAGE_COLUMNS) if row is not None else None

    def list_messages(self, *, after_seq: int = 0, limit: int = 200) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM phone_messages WHERE seq > ? ORDER BY seq, id LIMIT ?", (int(after_seq), int(limit)),
            ).fetchall()
        return [_row(row, MESSAGE_COLUMNS) for row in rows]

    def recent_messages(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute("SELECT * FROM phone_messages ORDER BY created_at DESC, seq DESC LIMIT ?",
                                (int(limit),)).fetchall()
        return [_row(row, MESSAGE_COLUMNS) for row in rows]

    def unread_replies(self) -> list[dict[str, Any]]:
        """His messages nobody at the desk has read yet (``get_replies``)."""
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM phone_messages WHERE direction='from_phone' AND read_at IS NULL ORDER BY seq, id",
            ).fetchall()
        return [_row(row, MESSAGE_COLUMNS) for row in rows]

    def replies_to(self, message_id: str) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM phone_messages WHERE reply_to=? AND direction='from_phone' ORDER BY seq",
                (message_id,),
            ).fetchall()
        return [_row(row, MESSAGE_COLUMNS) for row in rows]

    def count_step_messages_since(self, step_id: str, since: str) -> int:
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM phone_messages WHERE program_step_id=? AND direction='to_phone' "
                "AND created_at >= ?", (step_id, since),
            ).fetchone()
        return int(row["n"] if row is not None else 0)

    # ── calls ────────────────────────────────────────────────────────

    def save_call(self, call: Mapping[str, Any]) -> None:
        values = []
        for key in CALL_COLUMNS:
            if key == "decision_json":
                decision = call.get("decision")
                values.append(json.dumps(decision) if decision is not None else None)
            elif key == "urgent":
                values.append(1 if call.get("urgent") else 0)
            else:
                values.append(call.get(key))
        with self._db._connection() as conn:
            conn.execute(_CALL_UPSERT, values)

    def get_call(self, call_id: str) -> Optional[dict[str, Any]]:
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM phone_calls WHERE id=?", (call_id,)).fetchone()
        return _call(row) if row is not None else None

    def list_calls(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute("SELECT * FROM phone_calls ORDER BY created_at DESC, seq DESC LIMIT ?",
                                (int(limit),)).fetchall()
        return [_call(row) for row in rows]

    def open_calls(self) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM phone_calls WHERE state IN ('ringing', 'answered') ORDER BY created_at",
            ).fetchall()
        return [_call(row) for row in rows]

    # ── events ───────────────────────────────────────────────────────

    def append_event(self, type_: str, ts: str, payload: Any) -> tuple[int, dict[str, Any]]:
        """One event; ``payload`` is a mapping or ``seq -> mapping`` (the
        object inside the event then carries the event's own ``seq``)."""
        with self._db._connection() as conn:
            cursor = conn.execute("INSERT INTO phone_events (type, ts, payload_json) VALUES (?, ?, '{}')",
                                  (type_, ts))
            seq = int(cursor.lastrowid or 0)
            data = dict(payload(seq) if callable(payload) else payload)
            conn.execute("UPDATE phone_events SET payload_json=? WHERE seq=?", (json.dumps(data, default=str), seq))
            return seq, data

    def events_after(self, after_seq: int, limit: int) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT seq, type, ts, payload_json FROM phone_events WHERE seq > ? ORDER BY seq LIMIT ?",
                (int(after_seq), int(limit)),
            ).fetchall()
        return [_event(row) for row in rows]

    def events_of_type(self, type_: str, since: str) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT seq, type, ts, payload_json FROM phone_events WHERE type=? AND ts >= ? ORDER BY seq",
                (type_, since),
            ).fetchall()
        return [_event(row) for row in rows]

    def last_seq(self) -> int:
        with self._db._connection() as conn:
            row = conn.execute("SELECT MAX(seq) AS s FROM phone_events").fetchone()
        return int(row["s"] or 0) if row is not None else 0


def _event(row: Any) -> dict[str, Any]:
    try:
        data = json.loads(row["payload_json"] or "{}")
    except ValueError:
        data = {}
    return {"seq": int(row["seq"]), "type": row["type"], "ts": row["ts"], "data": data}


__all__ = ["CALL_COLUMNS", "DEVICE_COLUMNS", "MESSAGE_COLUMNS", "PhoneStore"]
