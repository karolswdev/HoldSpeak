"""Pruning the journal of dead poll records, with a signed checkpoint.

The kernel journal is one SHA-256 chain for each stream: every record names
the hash of the record before it (``JournalStore.verify``). Rows cannot leave
the middle of that chain silently.

Until 2026-11-13 the Telegram long poll timed out on every call and each call
was a full ``external.egress`` operation: about 91,000 operations and 455,000
journal rows that say only "the poll did not answer". They can leave, under
these rules:

* Only one class of operation can be pruned: an ``external.egress`` operation
  of connector ``reach-telegram`` with data class ``reach_update_cursor`` (the
  poll) that ended ``indeterminate``, ``refused`` or ``failed``. Anything else
  is refused (``journal_prune_not_a_dead_poll``): a send, an inference, a poll
  that succeeded, an operation that another table still names.
* For each run of removed records the journal keeps ONE checkpoint row
  (``kernel_journal_prunes``): the stream, the first and the last removed
  sequence, the count, the hash of the record before the run and the hash of
  the last removed record, the class and the time, signed with the database's
  own secret. ``verify`` walks across a gap only through a checkpoint whose
  numbers and hashes fit the two records that stand on its sides. A changed
  or invented checkpoint fails verification.
* The newest record of a stream is never removed, so the next append links
  to a record that exists.

An auditor reads: this many records of this class were removed from this
range at this time. Not: what each of them was. They held no content.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from collections.abc import Iterable, Mapping
from typing import Any

from .model import KernelRefused

DEAD_POLL_CLASS = "reach-telegram reach_update_cursor poll: indeterminate, refused or failed"
_DEAD_STATES = ("indeterminate", "refused", "failed")
_POLL_REFS = ("connector:reach-telegram", "data-class:reach_update_cursor")
_FIELDS = ("stream", "first_sequence", "last_sequence", "records", "class",
           "previous_sha256", "last_sha256", "pruned_at")

# The dead polls: an egress operation in a dead state whose admission names
# the Telegram connector and the poll's data class, exactly.
DEAD_POLLS_SQL = f"""SELECT o.operation_id FROM kernel_operations o
 WHERE o.name = 'external.egress' AND o.state IN ({",".join("?" * len(_DEAD_STATES))})
   AND EXISTS (
     SELECT 1 FROM kernel_journal a
      WHERE a.operation_id = o.operation_id AND a.event_type = 'operation.admitted'
        AND EXISTS (SELECT 1 FROM json_each(a.refs_json) e WHERE e.value = ?)
        AND EXISTS (SELECT 1 FROM json_each(a.refs_json) e WHERE e.value = ?))"""


def checkpoint_hash(secret: str, checkpoint: Mapping[str, Any]) -> str:
    material = json.dumps({field: checkpoint[field] for field in _FIELDS}, separators=(",", ":"), sort_keys=True)
    return "hmac-sha256:" + hmac.new(secret.encode(), material.encode(), hashlib.sha256).hexdigest()


def checkpoints(conn: Any, stream: str) -> dict[int, dict[str, Any]]:
    """The stream's checkpoints, by the first removed sequence."""
    rows = conn.execute(
        "SELECT * FROM kernel_journal_prunes WHERE stream=? ORDER BY first_sequence", (stream,)
    ).fetchall()
    return {int(row["first_sequence"]): dict(row) for row in rows}


def cross_gap(secret: str, known: Mapping[int, Mapping[str, Any]], *, previous_hash: str,
              previous_sequence: int, record: Mapping[str, Any]) -> int:
    """``record`` does not name the record before it. Walk the gap through
    its checkpoint, or refuse. Returns the count of removed records."""
    checkpoint = known.get(previous_sequence + 1)
    if checkpoint is None:
        raise KernelRefused("journal_previous_hash_mismatch")
    fits = (
        int(checkpoint["last_sequence"]) == int(record["stream_sequence"]) - 1
        and int(checkpoint["records"]) == int(checkpoint["last_sequence"]) - int(checkpoint["first_sequence"]) + 1
        and str(checkpoint["previous_sha256"]) == previous_hash
        and str(checkpoint["last_sha256"]) == str(record["previous_sha256"])
    )
    if not fits or not hmac.compare_digest(str(checkpoint["checkpoint_sha256"]), checkpoint_hash(secret, checkpoint)):
        raise KernelRefused("journal_prune_checkpoint_invalid")
    return int(checkpoint["records"])


def dead_poll_operation_ids(conn: Any) -> list[str]:
    rows = conn.execute(DEAD_POLLS_SQL, (*_DEAD_STATES, *_POLL_REFS)).fetchall()
    return [str(row[0]) for row in rows]


def _other_tables_naming_operations(conn: Any) -> list[tuple[str, str]]:
    """Every (table, column) that can name a kernel operation, but the three
    tables the prune itself clears."""
    own = {"kernel_operations", "kernel_receipts", "kernel_journal", "kernel_journal_prunes"}
    found: list[tuple[str, str]] = []
    for (table,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        if table in own or str(table).startswith("sqlite_"):
            continue
        for column in conn.execute(f'PRAGMA table_info("{table}")').fetchall():
            if str(column[1]) in ("operation_id", "parent_operation_id"):
                found.append((str(table), str(column[1])))
    return found


def prune(conn: Any, secret: str, operation_ids: Iterable[str], *, now: float) -> dict[str, Any]:
    """Remove these dead polls inside the caller's transaction. Every id is
    checked again here; one id that is not a dead poll refuses the whole act."""
    ids = list(dict.fromkeys(str(item) for item in operation_ids))
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS _prune_ops(operation_id TEXT PRIMARY KEY)")
    conn.execute("DELETE FROM _prune_ops")
    conn.executemany("INSERT INTO _prune_ops(operation_id) VALUES(?)", [(item,) for item in ids])
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS _dead_polls(operation_id TEXT PRIMARY KEY)")
    conn.execute("DELETE FROM _dead_polls")
    conn.execute(f"INSERT INTO _dead_polls {DEAD_POLLS_SQL}", (*_DEAD_STATES, *_POLL_REFS))
    not_dead = conn.execute(
        "SELECT COUNT(*) FROM _prune_ops p WHERE NOT EXISTS (SELECT 1 FROM _dead_polls d WHERE d.operation_id = p.operation_id)"
    ).fetchone()[0]
    if not_dead:
        raise KernelRefused("journal_prune_not_a_dead_poll", str(not_dead))
    children = conn.execute(
        "SELECT COUNT(*) FROM kernel_operations c JOIN _prune_ops p ON p.operation_id = c.parent_operation_id"
    ).fetchone()[0]
    if children:
        raise KernelRefused("journal_prune_not_a_dead_poll", "an operation has children")
    for table, column in _other_tables_naming_operations(conn):
        named = conn.execute(
            f'SELECT COUNT(*) FROM "{table}" t JOIN _prune_ops p ON p.operation_id = t."{column}"'
        ).fetchone()[0]
        if named:
            raise KernelRefused("journal_prune_not_a_dead_poll", f"{table} names an operation")

    removed = 0
    streams = [str(row[0]) for row in conn.execute(
        "SELECT DISTINCT j.stream FROM kernel_journal j JOIN _prune_ops p ON p.operation_id = j.operation_id"
    ).fetchall()]
    for stream in streams:
        newest = conn.execute(
            "SELECT operation_id FROM kernel_journal WHERE stream=? ORDER BY stream_sequence DESC LIMIT 1", (stream,)
        ).fetchone()
        if newest is not None:
            # The newest record stays: the next append links to it.
            conn.execute("DELETE FROM _prune_ops WHERE operation_id=?", (str(newest[0]),))
        runs: list[dict[str, Any]] = []
        run: dict[str, Any] | None = None
        rows = conn.execute(
            """SELECT j.stream_sequence, j.previous_sha256, j.record_sha256,
                      EXISTS (SELECT 1 FROM _prune_ops p WHERE p.operation_id = j.operation_id) AS goes
                 FROM kernel_journal j WHERE j.stream=? ORDER BY j.stream_sequence""",
            (stream,),
        )
        for sequence, previous_sha, record_sha, goes in rows:
            if not goes:
                run = None
                continue
            if run is not None and int(sequence) == int(run["last_sequence"]) + 1:
                run["last_sequence"], run["last_sha256"] = int(sequence), str(record_sha)
                run["records"] += 1
                continue
            run = {"stream": stream, "first_sequence": int(sequence), "last_sequence": int(sequence),
                   "records": 1, "previous_sha256": str(previous_sha), "last_sha256": str(record_sha)}
            runs.append(run)
        # A new run can stand beside a checkpoint of an earlier prune: one
        # checkpoint for one gap.
        items = sorted([*checkpoints(conn, stream).values(), *runs], key=lambda item: int(item["first_sequence"]))
        joined: list[dict[str, Any]] = []
        for item in items:
            last = joined[-1] if joined else None
            if last is not None and int(item["first_sequence"]) == int(last["last_sequence"]) + 1:
                if str(item["previous_sha256"]) != str(last["last_sha256"]):
                    raise KernelRefused("journal_prune_checkpoint_invalid")
                last["last_sequence"], last["last_sha256"] = int(item["last_sequence"]), str(item["last_sha256"])
                last["records"] = int(last["records"]) + int(item["records"])
                last["pruned_at"] = now
                continue
            joined.append({**item, "class": DEAD_POLL_CLASS, "pruned_at": item.get("pruned_at", now)})
        conn.execute("DELETE FROM kernel_journal_prunes WHERE stream=?", (stream,))
        for item in joined:
            conn.execute(
                """INSERT INTO kernel_journal_prunes(
                       prune_id, stream, first_sequence, last_sequence, records, class,
                       previous_sha256, last_sha256, pruned_at, checkpoint_sha256)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                ("prune_" + uuid.uuid4().hex, item["stream"], item["first_sequence"], item["last_sequence"],
                 item["records"], item["class"], item["previous_sha256"], item["last_sha256"],
                 item["pruned_at"], checkpoint_hash(secret, item)),
            )
        removed += sum(int(item["records"]) for item in runs)
    counts = {
        "operations": conn.execute("SELECT COUNT(*) FROM _prune_ops").fetchone()[0],
        "journal_records": removed,
    }
    conn.execute("DELETE FROM kernel_journal WHERE operation_id IN (SELECT operation_id FROM _prune_ops)")
    counts["receipts"] = conn.execute(
        "DELETE FROM kernel_receipts WHERE operation_id IN (SELECT operation_id FROM _prune_ops)").rowcount
    conn.execute("DELETE FROM kernel_operations WHERE operation_id IN (SELECT operation_id FROM _prune_ops)")
    conn.execute("DELETE FROM _prune_ops")
    conn.execute("DELETE FROM _dead_polls")
    return counts
