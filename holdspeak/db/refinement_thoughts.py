"""Persistence and immutable-ledger helpers for HS-141 refinement thoughts."""
from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .base import BaseRepository


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_json(value: Any) -> bytes:
    """The exact JSON encoding used by the thought ledger and sync wire."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class RefinementThoughtRepository(BaseRepository):
    table = "refinement_thoughts"

    def get(self, thought_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM refinement_thoughts WHERE id = ?", (str(thought_id),)).fetchone()
        return self._row(row) if row else None

    def get_by_request_id(self, request_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM refinement_thoughts WHERE create_request_id = ?", (str(request_id),)).fetchone()
        return self._row(row) if row else None

    def get_by_note(self, note_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM refinement_thoughts WHERE working_note_id = ?", (str(note_id),)).fetchone()
        return self._row(row) if row else None

    def list(self, *, state: str | None = None) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM refinement_thoughts" + (" WHERE state = ?" if state else "") + " ORDER BY updated_at DESC", (state,) if state else ()).fetchall()
        return [self._row(row) for row in rows]

    def revisions(self, thought_id: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM refinement_working_revisions WHERE thought_id=? ORDER BY revision", (thought_id,)).fetchall()
        return [dict(row) | {"tags": self._tags(row["tags_json"])} for row in rows]

    def lifecycle(self, thought_id: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM refinement_lifecycle_revisions WHERE thought_id=? ORDER BY lifecycle_revision", (thought_id,)).fetchall()
        return [dict(row) for row in rows]

    def commands(self, thought_id: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM refinement_aggregate_commands WHERE thought_id=? ORDER BY aggregate_revision", (thought_id,)).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def next_resume_order(conn: Any) -> int:
        row = conn.execute("SELECT value FROM refinement_resume_sequence WHERE id=1").fetchone()
        value = int(row["value"]) + 1 if row else 1
        conn.execute("INSERT INTO refinement_resume_sequence(id,value) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET value=excluded.value", (value,))
        return value

    @staticmethod
    def reconcile_resume_orders(conn: Any) -> int:
        """Backfill pre-HS-141-02 rows once without timestamp tie ordering."""
        rows = conn.execute("SELECT id FROM refinement_thoughts WHERE resume_order=0 ORDER BY created_at,id").fetchall()
        for row in rows:
            conn.execute("UPDATE refinement_thoughts SET resume_order=? WHERE id=?", (RefinementThoughtRepository.next_resume_order(conn), row["id"]))
        return len(rows)

    @staticmethod
    def lifecycle_bytes(*, thought_id: str, lifecycle_revision: int, aggregate_revision: int,
                        prior_state: str | None, state: str, command: str, occurred_at: str) -> bytes:
        return canonical_json({"aggregate_revision": aggregate_revision, "command": command,
                               "lifecycle_revision": lifecycle_revision, "occurred_at": occurred_at,
                               "prior_state": prior_state, "state": state, "thought_id": thought_id})

    @classmethod
    def lifecycle_hash(cls, **kwargs: Any) -> str:
        return _sha(cls.lifecycle_bytes(**kwargs))

    @staticmethod
    def content_hash(title: str, body_markdown: str, tags: list[str]) -> str:
        return _sha(canonical_json({"title": title, "body_markdown": body_markdown, "tags": tags}))

    @staticmethod
    def payload_hash(raw_utf8: bytes, source_kind: str, source_ref: str | None, note: dict[str, Any]) -> str:
        return _sha(canonical_json({"raw_utf8_b64": base64.b64encode(raw_utf8).decode("ascii"), "source_kind": source_kind,
                                    "source_ref": source_ref or "", "note": {key: note.get(key) for key in ("id", "title", "body_markdown", "tags")}}))

    @staticmethod
    def aggregate_hash(record: dict[str, Any], *, working_sha256: str, lifecycle_sha256: str | None) -> str:
        return _sha(canonical_json({"thought_id": record["id"], "raw_sha256": record["raw_sha256"], "state": record["state"],
                                    "working_revision": int(record["working_revision"]), "lifecycle_revision": int(record["lifecycle_revision"]),
                                    "attachment_revision": int(record["attachment_revision"]), "aggregate_revision": int(record["aggregate_revision"]),
                                    "working_sha256": working_sha256, "lifecycle_sha256": lifecycle_sha256}))

    @staticmethod
    def insert_lifecycle(conn: Any, *, thought_id: str, lifecycle_revision: int, aggregate_revision: int,
                         prior_state: str | None, state: str, command: str, occurred_at: str) -> str:
        digest = RefinementThoughtRepository.lifecycle_hash(thought_id=thought_id, lifecycle_revision=lifecycle_revision,
            aggregate_revision=aggregate_revision, prior_state=prior_state, state=state, command=command, occurred_at=occurred_at)
        conn.execute("""INSERT INTO refinement_lifecycle_revisions
                     (thought_id,lifecycle_revision,aggregate_revision,prior_state,state,command,occurred_at,entry_sha256)
                     VALUES (?,?,?,?,?,?,?,?)""", (thought_id, lifecycle_revision, aggregate_revision, prior_state, state, command, occurred_at, digest))
        return digest

    @staticmethod
    def insert_command(conn: Any, record: dict[str, Any], *, command_kind: str,
                       prior_working_revision: int, prior_lifecycle_revision: int, prior_attachment_revision: int,
                       working_sha256: str, lifecycle_sha256: str | None, accepted_at: str) -> None:
        conn.execute("""INSERT INTO refinement_aggregate_commands
                     (thought_id,aggregate_revision,command_kind,prior_working_revision,next_working_revision,
                      prior_lifecycle_revision,next_lifecycle_revision,prior_attachment_revision,next_attachment_revision,
                      canonical_sha256,lifecycle_sha256,accepted_at)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                     (record["id"], record["aggregate_revision"], command_kind, prior_working_revision, record["working_revision"],
                      prior_lifecycle_revision, record["lifecycle_revision"], prior_attachment_revision, record["attachment_revision"],
                      RefinementThoughtRepository.aggregate_hash(record, working_sha256=working_sha256, lifecycle_sha256=lifecycle_sha256), lifecycle_sha256, accepted_at))

    @staticmethod
    def reconcile_missing_working_notes(conn: Any) -> int:
        rows = conn.execute("""SELECT id FROM refinement_thoughts WHERE state != 'tombstoned'
            AND NOT EXISTS (SELECT 1 FROM notes WHERE notes.id=refinement_thoughts.working_note_id AND notes.deleted=0)""").fetchall()
        for row in rows:
            RefinementThoughtRepository.terminalize_in_transaction(conn, str(row["id"]))
        return len(rows)

    @staticmethod
    def reconcile_legacy_ledgers(conn: Any) -> int:
        """Give pre-ledger HS-141 rows one explicit migration command, never silent history."""
        rows = conn.execute("SELECT * FROM refinement_thoughts WHERE NOT EXISTS (SELECT 1 FROM refinement_aggregate_commands c WHERE c.thought_id=refinement_thoughts.id)").fetchall()
        for row in rows:
            record = dict(row); now = str(record["updated_at"] or _now())
            work = conn.execute("SELECT content_sha256 FROM refinement_working_revisions WHERE thought_id=? AND revision=?", (record["id"], record["working_revision"])).fetchone()
            if work is None:
                continue
            conn.execute("UPDATE refinement_thoughts SET lifecycle_revision=1,aggregate_revision=1 WHERE id=?", (record["id"],))
            record["lifecycle_revision"], record["aggregate_revision"] = 1, 1
            command = "create" if record["state"] == "working" else "reconcile_legacy"
            life = RefinementThoughtRepository.insert_lifecycle(conn, thought_id=record["id"], lifecycle_revision=1, aggregate_revision=1,
                prior_state=None, state=record["state"], command=command, occurred_at=now)
            RefinementThoughtRepository.insert_command(conn, record, command_kind=command, prior_working_revision=0,
                prior_lifecycle_revision=0, prior_attachment_revision=0, working_sha256=str(work["content_sha256"]), lifecycle_sha256=life, accepted_at=now)
        return len(rows)

    @staticmethod
    def terminalize_in_transaction(conn: Any, thought_id: str, *, expected_aggregate_revision: int | None = None,
                                   expected_lifecycle_revision: int | None = None) -> bool:
        """Single terminalization command for delete, repair, and sync application."""
        row = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
        if row is None:
            return False
        record = dict(row)
        if record["state"] == "tombstoned":
            return True
        if expected_aggregate_revision is not None and int(record["aggregate_revision"]) != expected_aggregate_revision:
            return False
        if expected_lifecycle_revision is not None and int(record["lifecycle_revision"]) != expected_lifecycle_revision:
            return False
        now = _now()
        working = conn.execute("SELECT content_sha256 FROM refinement_working_revisions WHERE thought_id=? AND revision=?", (thought_id, record["working_revision"])).fetchone()
        working_hash = str(working["content_sha256"]) if working else ""
        next_lifecycle, next_aggregate = int(record["lifecycle_revision"]) + 1, int(record["aggregate_revision"]) + 1
        cur = conn.execute("""UPDATE refinement_thoughts SET state='tombstoned', lifecycle_revision=?, aggregate_revision=?, resume_order=?,
                           tombstoned_at=COALESCE(tombstoned_at, ?), updated_at=? WHERE id=? AND aggregate_revision=? AND lifecycle_revision=?""",
                           (next_lifecycle, next_aggregate, RefinementThoughtRepository.next_resume_order(conn), now, now, thought_id, record["aggregate_revision"], record["lifecycle_revision"]))
        if not cur.rowcount:
            return False
        updated = dict(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
        life_hash = RefinementThoughtRepository.insert_lifecycle(conn, thought_id=thought_id, lifecycle_revision=next_lifecycle,
            aggregate_revision=next_aggregate, prior_state=record["state"], state="tombstoned", command="tombstone", occurred_at=now)
        RefinementThoughtRepository.insert_command(conn, updated, command_kind="tombstone", prior_working_revision=record["working_revision"],
            prior_lifecycle_revision=record["lifecycle_revision"], prior_attachment_revision=record["attachment_revision"],
            working_sha256=working_hash, lifecycle_sha256=life_hash, accepted_at=now)
        note_id = str(record["working_note_id"])
        conn.execute("UPDATE notes SET deleted=1,updated_at=?,last_modified=? WHERE id=?", (now, now, note_id))
        conn.execute("UPDATE directory_memberships SET deleted=1,last_modified=? WHERE primitive_id=? AND deleted=0", (now, f"note:{note_id}"))
        return True

    def _row(self, row: Any) -> dict[str, Any]:
        result = dict(row)
        result["raw_utf8_b64"] = base64.b64encode(bytes(result.pop("raw_utf8"))).decode("ascii")
        return result

    @staticmethod
    def _tags(raw: str) -> list[str]:
        try:
            parsed = json.loads(raw)
            return [str(item) for item in parsed] if isinstance(parsed, list) else []
        except Exception:
            return []


__all__ = ["RefinementThoughtRepository", "_now", "canonical_json"]
