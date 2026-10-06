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
import re
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
    if proof and row["egress"]:
        # The egress judged at the boundary names itself on the receipt, on every settle path.
        proof = {**dict(proof), "egress": row["egress"]}
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


#: The built-in folder destination (owner ruling 2026-10-05, "strong defaults,
#: batteries included"): every desk has it with no setup. Its target names no
#: path: the file channel resolves the folder at SEND time
#: (``channel_contract.builtin_folder``), so a moved Documents folder is honoured.
BUILTIN_FOLDER_ID = "holdspeak-folder"
BUILTIN_FOLDER_NAME = "HoldSpeak folder"
BUILTIN_FOLDER_TARGET: dict[str, str] = {"builtin": "documents"}


def is_builtin(row: Mapping[str, Any]) -> bool:
    return str(row.get("id") or "") == BUILTIN_FOLDER_ID


def seed_builtin_destination(conn: Any) -> int:
    """Insert the built-in folder row when it is absent (idempotent; never changes a present row)."""
    return conn.execute(
        "INSERT OR IGNORE INTO channel_destinations (id, name, channel, account_json, target_json, target_digest,"
        " synced, state, created_at) VALUES (?, ?, 'file', '{}', ?, ?, 0, 'active', ?)",
        (BUILTIN_FOLDER_ID, BUILTIN_FOLDER_NAME, canonical_json(BUILTIN_FOLDER_TARGET),
         target_digest("file", {}, BUILTIN_FOLDER_TARGET), now_iso()),
    ).rowcount


#: Where the People overlay of the old Brief renderer starts, in each channel's
#: bytes (before #767 it was always the tail of the Brief): the Markdown heading
#: (file, GitHub, Jira, email text), its Slack form, its Confluence form, and the
#: "unavailable" line in all of them.
_BRIEF_PEOPLE_START = re.compile(
    r"\n*(?:^## People$|^\*People\*$|^PEOPLE · UNAVAILABLE$|<h2>People</h2>|<p>PEOPLE · UNAVAILABLE</p>)",
    re.MULTILINE,
)


def _without_brief_people(text: str) -> str:
    match = _BRIEF_PEOPLE_START.search(text)
    if match is None:
        return text
    head = text[:match.start()]
    return head + ("\n" if text.endswith("\n") and head and not head.endswith("\n") else "")


def _scrubbed_payload(payload: bytes) -> Optional[bytes]:
    """The payload with the old Brief People overlay cut, or None when it has none.

    A JSON payload (Slack, email, Confluence) stays valid JSON, so the Send
    list can still show its preview; a text payload (file, GitHub, Jira) is cut.
    """
    try:
        text = bytes(payload).decode("utf-8")
    except UnicodeDecodeError:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if isinstance(data, (dict, list)):
        def walk(value: Any) -> Any:
            if isinstance(value, str):
                return _without_brief_people(value)
            if isinstance(value, list):
                return [walk(item) for item in value]
            if isinstance(value, dict):
                return {key: walk(item) for key, item in value.items()}
            return value

        cleaned = walk(data)
        if cleaned == data:
            return None
        return json.dumps(cleaned, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    cleaned_text = _without_brief_people(text)
    return None if cleaned_text == text else cleaned_text.encode("utf-8")


def scrub_brief_people_text(conn: Any) -> int:
    """Cut the People text from Brief sends the old renderer froze (before #767).

    Only ``prepared`` and ``discarded`` rows: they never left the desk, yet
    their payload held names, who-owes-whom counts and the next 1:1 in plain
    text. The row stays (never DELETE); only the People lines leave its
    payload. ``payload_digest`` is kept, so a prepared row still refuses Send
    (``payload_changed`` / ``preview_changed``) and he takes a fresh preview.
    Idempotent: a scrubbed payload has no People marker and is skipped.
    """
    rows = conn.execute(
        "SELECT id, payload FROM channel_sends WHERE document_ref LIKE 'monday_brief:%'"
        " AND state IN ('prepared', 'discarded')"
    ).fetchall()
    changed = 0
    for row in rows:
        cleaned = _scrubbed_payload(row[1])
        if cleaned is None:
            continue
        conn.execute("UPDATE channel_sends SET payload=? WHERE id=?", (cleaned, row[0]))
        changed += 1
    return changed


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
