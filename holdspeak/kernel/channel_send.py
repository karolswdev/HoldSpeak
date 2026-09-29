"""The kernel's settle for a send it ends itself (PHILO-10-01; design section 4a, seam 1).

A typed concern carved beside ``kernel/project.py`` (the kernel density guard).
The liveness reaper (``desk_broker.reap``) and the hub's startup recovery
(``steward_contract.recover_admitted_on_startup``) end a silent
``channel.send`` operation ``indeterminate``; :func:`channel_send_ended_effect`
is the effect that runs in THAT transaction, so the send row, its history row
and the kernel receipt commit together.
"""
from __future__ import annotations

from typing import Any, Mapping

#: PHILO-10-01: the Send's admitted rows (the charter's admission table).
#: The owner's rows: an AGENT is refused ``owner_principal_required`` with a
#: receipt (none is in the grant). ``channel.prepare`` completes under the
#: preparer's own identity (Q5, "You, every time": an agent prepares, only the
#: owner sends).
CHANNEL_ADMITTED: frozenset[str] = frozenset({
    "channel.save_destination", "channel.remove_destination", "channel.prepare",
    "channel.discard", "channel.send",
})
#: The one Send operation an AGENT's own call completes (its own identity, no grant).
AGENT_PREPARE_OPERATIONS: frozenset[str] = frozenset({"channel.prepare"})
#: The operation whose replay after a non-``succeeded`` end answers its settled
#: row (design section 4a, seam 3); a refusal before the boundary still raises.
SETTLED_ROW_REPLAY: frozenset[str] = frozenset({"channel.send"})
#: PHILO-10-02 (Q5): a steward run's children for the Send. It PREPARES under
#: its own identity; its send or discard reaches the codec only to be refused
#: ``owner_principal_required`` with a receipt ("You, every time").
STEWARD_SEND_CHILDREN: frozenset[str] = frozenset({"channel.prepare", "channel.send", "channel.discard"})
OWNER_PRESS: frozenset[str] = frozenset({"channel.send", "channel.discard"})

def channel_send_ended_effect(store: Any, operation: Mapping[str, Any], reason: str, *,
                              row_reason: str = "reaped", before: str = "reaped_before_dispatch") -> Any:
    """The kernel's settle for a ``channel.send`` it ends itself (design section 4a, seam 1).

    The liveness reaper and the startup recovery end a silent send
    ``indeterminate``; this effect runs in THAT transaction. A row of this
    operation that is ``dispatching`` settles ``unknown`` (reason *row_reason*)
    with its history row; for a file send whose file reads back with the
    payload digest, the proof records it ``found_on_disk`` (the outcome stays
    UNKNOWN, as the kernel's state is). No dispatching row (the boundary never
    committed): nothing moves, nothing was sent, and the receipt names it
    *before* (``reaped_before_dispatch``; the restart's ``hub_restart_before_dispatch``).
    ``None`` for every other operation.
    The file is read BEFORE the transaction (the effect itself is local SQL).
    """
    if str(operation.get("name") or "") == "nudge.send":
        return _nudge_ended_effect(str(operation.get("operation_id") or ""), row_reason)
    if str(operation.get("name") or "") != "channel.send":
        return None
    operation_id = str(operation.get("operation_id") or "")
    found: dict[str, Any] = {}
    with store._connection() as conn:
        row = conn.execute("SELECT channel, file_path, payload_digest, target_json FROM channel_sends"
                           " WHERE send_operation_id=? AND state='dispatching'", (operation_id,)).fetchone()
    if row is not None and str(row["channel"]) == "file" and row["file_path"]:
        found = _found_on_disk(str(row["file_path"]), str(row["payload_digest"]))

    def effect(conn: Any) -> Any:
        from ..db.channels import settle_in_transaction

        name = conn.execute(
            "SELECT d.name FROM channel_sends s JOIN channel_destinations d ON d.id=s.destination_id"
            " WHERE s.send_operation_id=?", (operation_id,)).fetchone()
        settled = settle_in_transaction(
            conn, send_operation_id=operation_id, state="unknown", reason=row_reason,
            proof=found or None, delivered_to=str(name["name"]) if name is not None else "")
        return None if settled is not None else before

    return effect


def _found_on_disk(path: str, digest: str) -> dict[str, Any]:
    """A reaped file send's read-back: the path, sha256 and size when the bytes match."""
    import hashlib
    import os

    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError:
        return {}
    sha = hashlib.sha256(data).hexdigest()
    if sha != digest:
        return {}
    return {"found_on_disk": {"path": os.path.abspath(path), "sha256": sha, "size": len(data)}}


def _nudge_ended_effect(operation_id: str, reason: str) -> Any:
    """PHILO-10-02 (F4): a nudge the kernel ends itself while ``sending`` is UNKNOWN, never offered again."""
    def effect(conn: Any) -> None:
        conn.execute(
            "UPDATE steward_steps SET state='unknown', receipt_json=json_object('effect_kind','github_comment',"
            "'outcome','unknown','reason',?), completed_at=datetime('now'), updated_at=datetime('now')"
            " WHERE state='sending' AND json_extract(observed_state_json,'$.send_operation_id')=?",
            (reason, operation_id))

    return effect
