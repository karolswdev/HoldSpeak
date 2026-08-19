"""HS-141-01 custody aggregate service: every mutation appends one command."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from typing import Any

from ..db.core import Database
from ..db.refinement_thoughts import RefinementThoughtRepository, _now, canonical_json
from ..db.relationships import qualified_ref
from ..principals import Principal, PrincipalKind
from .errors import ConflictError, NotFound, ValidationError

INBOX_DIRECTORY_ID = "hs-seed-inbox"
_SOURCES = frozenset({"typed", "voice", "note"})


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class RefinementThoughtService:
    def __init__(self, db: Database) -> None:
        self._db = db

    @staticmethod
    def _require_owner(principal: Principal | None) -> None:
        if principal is None or principal.kind is not PrincipalKind.OWNER:
            raise ValidationError("thought custody requires the authenticated owner", code="thought_owner_required")

    @staticmethod
    def _require_sync_node(principal: Principal | None) -> None:
        if principal is None or principal.kind is not PrincipalKind.NODE:
            raise ValidationError("thought aggregate install requires paired sync authority", code="thought_sync_authority_required")

    @staticmethod
    def _require_product_owner(principal: Principal | None) -> None:
        if principal is None or principal.kind is not PrincipalKind.OWNER:
            raise ValidationError("thought read requires the authenticated owner", code="thought_owner_required")

    def create(self, principal: Principal, *, request_id: str, raw_text: str, source: dict[str, Any] | None = None,
               initial_note: dict[str, Any] | None = None, thought_id: str | None = None) -> dict[str, Any]:
        self._require_product_owner(principal)
        request_id = str(request_id or "").strip()
        if not request_id or not isinstance(raw_text, str) or not raw_text:
            raise ValidationError("request_id and raw_text are required")
        source, kind = dict(source or {}), str((source or {}).get("kind") or "typed").strip().lower()
        ref = str(source.get("ref") or "").strip() or None
        if kind not in _SOURCES:
            raise ValidationError("invalid raw source")
        if kind == "note":
            try: ref = qualified_ref(ref)
            except ValueError as exc: raise ValidationError("note source requires a qualified ref") from exc
        elif ref:
            raise ValidationError("only note source may carry ref")
        raw = raw_text.encode("utf-8", "strict")
        note_input = dict(initial_note or {})
        note_id = str(note_input.get("id") or f"note_thought_{hashlib.sha256(request_id.encode()).hexdigest()[:16]}").strip()
        if not note_id: raise ValidationError("initial note id is invalid")
        title, body = str(note_input.get("title") or "First thought"), str(note_input.get("body_markdown") or raw_text)
        tags = [str(tag) for tag in (note_input.get("tags") or [])]
        payload_hash = RefinementThoughtRepository.payload_hash(raw, kind, ref, {"id": note_id, "title": title, "body_markdown": body, "tags": tags})
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute("SELECT * FROM refinement_thoughts WHERE create_request_id=?", (request_id,)).fetchone()
            if prior:
                record = self._record(prior)
                if record["create_payload_sha256"] != payload_hash:
                    raise ConflictError("create request was already used for different content", code="idempotency_payload_mismatch")
                return self._dto_in_transaction(conn, record)
            if conn.execute("SELECT 1 FROM directories WHERE id=? AND deleted=0", (INBOX_DIRECTORY_ID,)).fetchone() is None:
                raise ValidationError("Inbox is unavailable", code="inbox_unavailable")
            thought_id = str(thought_id or _id("thought")).strip()
            if not thought_id: raise ValidationError("thought id is invalid")
            if conn.execute("SELECT 1 FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone():
                raise ConflictError("thought id already exists", code="thought_id_in_use")
            if conn.execute("SELECT 1 FROM notes WHERE id=?", (note_id,)).fetchone():
                raise ConflictError("initial note id already exists", code="initial_note_id_in_use")
            now, raw_hash = _now(), hashlib.sha256(raw).hexdigest()
            resume_order = RefinementThoughtRepository.next_resume_order(conn)
            self._db.notes._upsert_in_transaction(conn, note_id=note_id, title=title, body_markdown=body, tags=tags, now=now)
            conn.execute("""INSERT INTO refinement_thoughts (id,create_request_id,create_payload_sha256,raw_utf8,raw_sha256,
                raw_source_kind,raw_source_ref,raw_captured_at,working_note_id,working_revision,lifecycle_revision,attachment_revision,
                aggregate_revision,resume_order,state,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,1,1,0,1,?,'working',?,?)""",
                (thought_id,request_id,payload_hash,raw,raw_hash,kind,ref,now,note_id,resume_order,now,now))
            working_hash = self._insert_revision(conn, thought_id, 1, title, body, tags, now)
            record = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            life_hash = RefinementThoughtRepository.insert_lifecycle(conn, thought_id=thought_id, lifecycle_revision=1, aggregate_revision=1,
                prior_state=None, state="working", command="create", occurred_at=now)
            RefinementThoughtRepository.insert_command(conn, record, command_kind="create", prior_working_revision=0,
                prior_lifecycle_revision=0, prior_attachment_revision=0, working_sha256=working_hash, lifecycle_sha256=life_hash, accepted_at=now)
            conn.execute("""INSERT INTO directory_memberships (primitive_id,directory_id,created_at,last_modified,deleted)
                VALUES (?,?,?,?,0) ON CONFLICT(primitive_id) DO UPDATE SET directory_id=excluded.directory_id,last_modified=excluded.last_modified,deleted=0""",
                (f"note:{note_id}", INBOX_DIRECTORY_ID, now, now))
            return self._dto_in_transaction(conn, record)

    def for_note(self, principal: Principal, note_id: str) -> dict[str, Any]:
        """Return a narrow owner-only ownership/precondition projection for one Note."""
        self._require_product_owner(principal)
        with self._db._connection() as conn:
            note = conn.execute("SELECT * FROM notes WHERE id=?", (str(note_id),)).fetchone()
            if note is None or note["deleted"]:
                raise NotFound("note", str(note_id))
            owned = conn.execute("SELECT * FROM refinement_thoughts WHERE working_note_id=?", (str(note_id),)).fetchone()
            if owned is not None:
                return {"ownership": "thought", "thought": self._dto_in_transaction(conn, self._record(owned))}
            item = self._note(note)
            assert item is not None
            return {
                "ownership": "ordinary",
                "note": item,
                "source_precondition": {
                    "content_sha256": RefinementThoughtRepository.content_hash(item["title"], item["body_markdown"], item["tags"]),
                    "last_modified": item["last_modified"],
                },
            }

    def adopt_note(self, principal: Principal, *, request_id: str, note_id: str,
                   expected_source_content_sha256: str, expected_source_last_modified: str) -> dict[str, Any]:
        """Atomically make one existing Note the durable working thought.

        The source Note is read and snapshot under the same IMMEDIATE transaction
        that claims ownership.  It is deliberately never inserted, updated, or
        deleted by adoption.
        """
        self._require_product_owner(principal)
        request_id, note_id = str(request_id or "").strip(), str(note_id or "").strip()
        content_digest, modified = str(expected_source_content_sha256 or "").strip(), str(expected_source_last_modified or "").strip()
        if not request_id or not note_id or not content_digest or not modified:
            raise ValidationError("request_id, note_id, and source precondition are required", code="note_adoption_precondition_required")
        request_digest = hashlib.sha256(canonical_json({"kind": "adopt_note", "request_id": request_id, "note_id": note_id,
            "expected_source_content_sha256": content_digest, "expected_source_last_modified": modified})).hexdigest()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute("SELECT * FROM refinement_thoughts WHERE create_request_id=?", (request_id,)).fetchone()
            if prior is not None:
                record = self._record(prior)
                if record["create_payload_sha256"] != request_digest:
                    raise ConflictError("create request was already used for different content", code="idempotency_payload_mismatch")
                return self._dto_in_transaction(conn, record)
            if conn.execute("SELECT 1 FROM directories WHERE id=? AND deleted=0", (INBOX_DIRECTORY_ID,)).fetchone() is None:
                raise ValidationError("Inbox is unavailable", code="inbox_unavailable")
            note = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
            if note is None:
                raise NotFound("note", note_id)
            if note["deleted"]:
                raise ConflictError("note was deleted", code="note_tombstoned")
            claimed = conn.execute("SELECT * FROM refinement_thoughts WHERE working_note_id=?", (note_id,)).fetchone()
            if claimed is not None:
                raise ConflictError("note is already a thought", code="note_already_a_thought",
                                    context={"thought": self._dto_in_transaction(conn, self._record(claimed))})
            tags = json.loads(note["tags_json"])
            actual = RefinementThoughtRepository.content_hash(str(note["title"]), str(note["body_markdown"]), tags)
            if actual != content_digest or str(note["last_modified"] or "") != modified:
                current = self._note(note)
                assert current is not None
                raise ConflictError("note changed before adoption", code="note_adoption_conflict", context={"note": current,
                    "source_precondition": {"content_sha256": actual, "last_modified": current["last_modified"]}})
            raw = str(note["body_markdown"]).encode("utf-8", "strict")
            now, thought_id = _now(), _id("thought")
            resume_order = RefinementThoughtRepository.next_resume_order(conn)
            conn.execute("""INSERT INTO refinement_thoughts (id,create_request_id,create_payload_sha256,raw_utf8,raw_sha256,
                raw_source_kind,raw_source_ref,raw_captured_at,working_note_id,working_revision,lifecycle_revision,attachment_revision,
                aggregate_revision,resume_order,state,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,1,1,0,1,?,'working',?,?)""",
                (thought_id, request_id, request_digest, raw, hashlib.sha256(raw).hexdigest(), "note", f"note:{note_id}", now, note_id, resume_order, now, now))
            record = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            working_hash = self._insert_revision(conn, thought_id, 1, str(note["title"]), str(note["body_markdown"]), tags, now)
            life_hash = RefinementThoughtRepository.insert_lifecycle(conn, thought_id=thought_id, lifecycle_revision=1, aggregate_revision=1,
                prior_state=None, state="working", command="adopt_note", occurred_at=now)
            RefinementThoughtRepository.insert_command(conn, record, command_kind="adopt_note", prior_working_revision=0,
                prior_lifecycle_revision=0, prior_attachment_revision=0, working_sha256=working_hash, lifecycle_sha256=life_hash, accepted_at=now)
            conn.execute("""INSERT INTO directory_memberships (primitive_id,directory_id,created_at,last_modified,deleted)
                VALUES (?,?,?,?,0) ON CONFLICT(primitive_id) DO UPDATE SET directory_id=excluded.directory_id,last_modified=excluded.last_modified,deleted=0""",
                (f"note:{note_id}", INBOX_DIRECTORY_ID, now, now))
            return self._dto_in_transaction(conn, record)

    def get(self, principal: Principal, thought_id: str, *, include_raw: bool = False) -> dict[str, Any]:
        self._require_product_owner(principal)
        record = self._db.refinement_thoughts.get(thought_id)
        if record is None: raise NotFound("thought", thought_id)
        return self._dto(record, include_raw=include_raw, remote=principal.kind is PrincipalKind.NODE)

    def list_unfinished(self, principal: Principal, *, limit: int = 20, cursor: str | None = None) -> dict[str, Any]:
        """Return the deliberately small, keyset-paged Resume projection."""
        self._require_product_owner(principal)
        if not isinstance(limit, int) or limit < 1 or limit > 50:
            raise ValidationError("limit must be between 1 and 50", code="thought_list_limit_invalid")
        with self._db._connection() as conn:
            token = self._decode_cursor(conn, cursor) if cursor else None
            if token and token.get("state") != "unfinished":
                raise ValidationError("thought cursor state is invalid", code="thought_cursor_invalid")
            high = int(token["high"]) if token else self._high_water(conn)
            clauses = ["state='working'", "resume_order <= ?"]
            values: list[Any] = [high]
            if token:
                clauses.append("(resume_order < ? OR (resume_order = ? AND id < ?))")
                values.extend([int(token["last_resume_order"]), int(token["last_resume_order"]), str(token["last_id"])])
            values.append(limit + 1)
            rows = conn.execute("SELECT * FROM refinement_thoughts WHERE " + " AND ".join(clauses) + " ORDER BY resume_order DESC,id DESC LIMIT ?", values).fetchall()
            page, more = rows[:limit], len(rows) > limit
            items = [self._list_item_in_transaction(conn, self._record(row), remote=principal.kind is PrincipalKind.NODE) for row in page]
            next_cursor = None
            if more and page:
                last = page[-1]
                next_cursor = self._encode_cursor(conn, {"v": 2, "state": "unfinished", "high": high, "last_resume_order": int(last["resume_order"]), "last_id": str(last["id"])})
            return {"items": items, "next_cursor": next_cursor}

    def reconcile(self, principal: Principal, thought_id: str, *, expected_aggregate_revision: int | None,
                  invocation_id: str | None = None) -> dict[str, Any]:
        """Read/finalize only existing local proof; never creates or dispatches Ask."""
        self._require_product_owner(principal)
        if not isinstance(expected_aggregate_revision, int):
            raise ConflictError("thought reconciliation requires aggregate revision", code="thought_expected_revision_required")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if row is None: raise NotFound("thought", thought_id)
            record = self._record(row)
            if int(record["aggregate_revision"]) != expected_aggregate_revision:
                raise self._conflict(conn, record, expected_aggregate_revision, None)
            working = conn.execute("SELECT deleted FROM notes WHERE id=?", (record["working_note_id"],)).fetchone()
            if working is None or working["deleted"]:
                RefinementThoughtRepository.terminalize_in_transaction(conn, thought_id)
                self._supersede_invocations(conn, thought_id, "thought_tombstoned")
                fresh = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
                return self._dto_in_transaction(conn, fresh)
            if record["state"] != "working":
                self._supersede_invocations(conn, record["id"], "thought_tombstoned" if record["state"] == "tombstoned" else "thought_completed")
                return self._dto_in_transaction(conn, record)
            inv = conn.execute("SELECT * FROM refinement_invocations WHERE thought_id=?" + (" AND id=?" if invocation_id else "") + " ORDER BY created_at DESC LIMIT 1", (thought_id, invocation_id) if invocation_id else (thought_id,)).fetchone()
            if inv is None:
                return self._dto_in_transaction(conn, record)
            self._reconcile_invocation_in_transaction(conn, dict(inv), record)
            fresh = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            return self._dto_in_transaction(conn, fresh)

    def reserve_refinement(self, principal: Principal, thought_id: str, *, request_id: str,
                           expected_aggregate_revision: int, expected_working_revision: int,
                           expected_attachment_revision: int) -> dict[str, Any]:
        """Future Story-04 entry point: persist logical/base-attempt identity only."""
        self._require_product_owner(principal)
        semantic = {"request_id": str(request_id), "thought_id": str(thought_id), "frozen_aggregate_revision": expected_aggregate_revision,
                    "frozen_working_revision": expected_working_revision, "frozen_attachment_revision": expected_attachment_revision, "purpose": "refinement"}
        digest = hashlib.sha256(json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute("SELECT * FROM refinement_invocations WHERE request_id=?", (request_id,)).fetchone()
            if existing:
                if str(existing["request_sha256"]) != digest: raise ConflictError("request was already used for different refinement", code="refinement_request_payload_mismatch")
                return self._invocation_dto(conn, dict(existing))
            thought = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if thought is None: raise NotFound("thought", thought_id)
            record = self._record(thought)
            if record["state"] != "working": raise ConflictError("thought is not available for refinement", code="thought_" + str(record["state"]))
            if (record["aggregate_revision"], record["working_revision"], record["attachment_revision"]) != (expected_aggregate_revision, expected_working_revision, expected_attachment_revision):
                raise self._conflict(conn, record, expected_aggregate_revision, expected_working_revision)
            note = conn.execute("SELECT deleted FROM notes WHERE id=?", (record["working_note_id"],)).fetchone()
            if note is None or note["deleted"]: raise ConflictError("working thought was deleted", code="thought_tombstoned")
            live = conn.execute("SELECT id FROM refinement_invocations WHERE thought_id=? AND state IN ('reserved','in_flight','awaiting_projection','review_ready')", (thought_id,)).fetchone()
            if live: raise ConflictError("a refinement is already live", code="refinement_already_live", context={"invocation_id": str(live["id"])})
            now, iid, ask = _now(), _id("rinv"), _id("ask")
            conn.execute("INSERT INTO refinement_invocations(id,request_id,request_sha256,thought_id,frozen_aggregate_revision,frozen_working_revision,frozen_attachment_revision,state,created_at,updated_at) VALUES(?,?,?,?,?,?,?,'reserved',?,?)", (iid,request_id,digest,thought_id,expected_aggregate_revision,expected_working_revision,expected_attachment_revision,now,now))
            conn.execute("INSERT INTO refinement_invocation_attempts(invocation_id,attempt_ordinal,ask_invocation_id,state,created_at) VALUES(?,1,?,'reserved',?)", (iid,ask,now))
            return self._invocation_dto(conn, dict(conn.execute("SELECT * FROM refinement_invocations WHERE id=?", (iid,)).fetchone()))

    def update_working(self, principal: Principal, thought_id: str, *, expected_aggregate_revision: int | None,
                       expected_working_revision: int | None, title: str | None = None,
                       body_markdown: str | None = None, tags: list[str] | None = None) -> dict[str, Any]:
        self._require_owner(principal)
        if not isinstance(expected_aggregate_revision, int) or not isinstance(expected_working_revision, int):
            raise ConflictError("thought-owned notes require aggregate and working revisions", code="thought_expected_revision_required")
        custody_lost = False
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if row is None: raise NotFound("thought", thought_id)
            record = self._record(row)
            note = conn.execute("SELECT * FROM notes WHERE id=?", (record["working_note_id"],)).fetchone()
            if note is None or note["deleted"]:
                RefinementThoughtRepository.terminalize_in_transaction(conn, thought_id)
                custody_lost = True
            else:
                if record["state"] == "tombstoned": raise self._conflict(conn, record, expected_aggregate_revision, expected_working_revision, code="thought_tombstoned")
                if record["state"] == "completed": raise self._conflict(conn, record, expected_aggregate_revision, expected_working_revision, code="thought_completed")
                if record["aggregate_revision"] != expected_aggregate_revision or record["working_revision"] != expected_working_revision:
                    raise self._conflict(conn, record, expected_aggregate_revision, expected_working_revision)
                now, next_working, next_aggregate = _now(), expected_working_revision + 1, expected_aggregate_revision + 1
                resolved = (str(title) if title is not None else str(note["title"]), str(body_markdown) if body_markdown is not None else str(note["body_markdown"]),
                            [str(x) for x in tags] if tags is not None else json.loads(note["tags_json"]))
                cur = conn.execute("UPDATE refinement_thoughts SET working_revision=?,aggregate_revision=?,resume_order=?,updated_at=? WHERE id=? AND working_revision=? AND aggregate_revision=? AND state='working'",
                    (next_working,next_aggregate,RefinementThoughtRepository.next_resume_order(conn),now,thought_id,expected_working_revision,expected_aggregate_revision))
                if not cur.rowcount:
                    fresh = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
                    raise self._conflict(conn, fresh, expected_aggregate_revision, expected_working_revision)
                self._db.notes._upsert_in_transaction(conn,note_id=record["working_note_id"],title=resolved[0],body_markdown=resolved[1],tags=resolved[2],now=now)
                working_hash = self._insert_revision(conn, thought_id, next_working, *resolved, now)
                updated = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
                RefinementThoughtRepository.insert_command(conn,updated,command_kind="replace_working",prior_working_revision=expected_working_revision,
                    prior_lifecycle_revision=record["lifecycle_revision"],prior_attachment_revision=record["attachment_revision"],working_sha256=working_hash,lifecycle_sha256=None,accepted_at=now)
                return self._dto_in_transaction(conn, updated)
        if custody_lost:
            fresh = self._db.refinement_thoughts.get(thought_id)
            with self._db._connection() as conn:
                raise self._conflict(conn, fresh, expected_aggregate_revision, expected_working_revision, code="thought_tombstoned")
        raise AssertionError("unreachable")

    def update_note(self, principal: Principal, note_id: str, *, expected_aggregate_revision: int | None,
                    expected_working_revision: int | None, **fields: Any) -> dict[str, Any]:
        record = self._db.refinement_thoughts.get_by_note(note_id)
        if record is None: raise NotFound("thought note", note_id)
        return self.update_working(principal, record["id"], expected_aggregate_revision=expected_aggregate_revision,
            expected_working_revision=expected_working_revision, title=fields.get("title"), body_markdown=fields.get("body_markdown"), tags=fields.get("tags"))

    def _complete_without_receipt(self, principal: Principal, thought_id: str, *, expected_aggregate_revision: int | None,
                                  expected_lifecycle_revision: int | None) -> dict[str, Any]:
        """Internal fixture/migration transition; public completion uses the receipt ledger."""
        return self._transition(principal,thought_id,expected_aggregate_revision=expected_aggregate_revision,
            expected_lifecycle_revision=expected_lifecycle_revision,command="complete",state="completed")

    def complete_with_receipt(self, principal: Principal, thought_id: str, *, request_id: str,
                              expected_aggregate_revision: int | None,
                              expected_lifecycle_revision: int | None) -> tuple[dict[str, Any], dict[str, Any]]:
        """Complete exactly once and keep a durable response-loss receipt."""
        self._require_owner(principal)
        request_id = str(request_id or "").strip()
        if not request_id or not isinstance(expected_aggregate_revision, int) or not isinstance(expected_lifecycle_revision, int):
            raise ValidationError("request_id and completion revisions are required", code="completion_request_required")
        digest = hashlib.sha256(canonical_json({"thought_id": thought_id,
            "expected_aggregate_revision": expected_aggregate_revision,
            "expected_lifecycle_revision": expected_lifecycle_revision})).hexdigest()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute("SELECT * FROM refinement_completion_receipts WHERE request_id=?", (request_id,)).fetchone()
            row = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if row is None: raise NotFound("thought", thought_id)
            record = self._record(row)
            if prior is not None:
                if str(prior["request_sha256"]) != digest:
                    raise ConflictError("completion request was already used for different thought state", code="completion_request_payload_mismatch")
                if (record["state"] == "completed" and int(record["aggregate_revision"]) == int(prior["aggregate_revision"])
                        and int(record["lifecycle_revision"]) == int(prior["lifecycle_revision"])):
                    return self._dto_in_transaction(conn, record), self._completion_receipt(prior)
                raise ConflictError("completion request was superseded by later work", code="completion_request_superseded",
                    context={"current": self._dto_in_transaction(conn, record)})
            if record["state"] == "completed":
                # A remote completion has no local receipt: never manufacture
                # one from the synchronized command ledger.
                raise ConflictError("thought is already completed", code="thought_already_completed",
                    context={"current": self._dto_in_transaction(conn, record)})
            if record["state"] != "working" or record["aggregate_revision"] != expected_aggregate_revision or record["lifecycle_revision"] != expected_lifecycle_revision:
                raise self._conflict(conn, record, expected_aggregate_revision, None, code="thought_revision_conflict")
            now, next_life, next_agg = _now(), expected_lifecycle_revision + 1, expected_aggregate_revision + 1
            cur = conn.execute("UPDATE refinement_thoughts SET state='completed',lifecycle_revision=?,aggregate_revision=?,resume_order=?,completed_at=?,updated_at=? WHERE id=? AND aggregate_revision=? AND lifecycle_revision=? AND state='working'",
                (next_life, next_agg, RefinementThoughtRepository.next_resume_order(conn), now, now, thought_id, expected_aggregate_revision, expected_lifecycle_revision))
            if not cur.rowcount:
                fresh = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
                raise self._conflict(conn, fresh, expected_aggregate_revision, None, code="thought_revision_conflict")
            updated = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            life_hash = RefinementThoughtRepository.insert_lifecycle(conn, thought_id=thought_id, lifecycle_revision=next_life,
                aggregate_revision=next_agg, prior_state="working", state="completed", command="complete", occurred_at=now)
            work = conn.execute("SELECT content_sha256 FROM refinement_working_revisions WHERE thought_id=? AND revision=?", (thought_id, record["working_revision"])).fetchone()
            RefinementThoughtRepository.insert_command(conn, updated, command_kind="complete", prior_working_revision=record["working_revision"],
                prior_lifecycle_revision=expected_lifecycle_revision, prior_attachment_revision=record["attachment_revision"],
                working_sha256=str(work["content_sha256"]), lifecycle_sha256=life_hash, accepted_at=now)
            receipt_id = _id("rcomp")
            conn.execute("INSERT INTO refinement_completion_receipts(receipt_id,thought_id,request_id,request_sha256,aggregate_revision,lifecycle_revision,working_note_id,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (receipt_id, thought_id, request_id, digest, next_agg, next_life, record["working_note_id"], now))
            receipt = {"receipt_id": receipt_id, "thought_id": thought_id, "aggregate_revision": next_agg,
                "lifecycle_revision": next_life, "working_note_id": record["working_note_id"], "created_at": now}
            return self._dto_in_transaction(conn, updated), self._completion_receipt(receipt)

    @staticmethod
    def _completion_receipt(row: Any) -> dict[str, Any]:
        return {"id": str(row["receipt_id"]), "kind": "thought_completed", "thought_id": str(row["thought_id"]),
            "note_ref": f"note:{row['working_note_id']}", "aggregate_revision": int(row["aggregate_revision"]),
            "lifecycle_revision": int(row["lifecycle_revision"]), "created_at": str(row["created_at"])}

    def resume(self, principal: Principal, thought_id: str, *, expected_aggregate_revision: int | None,
               expected_lifecycle_revision: int | None) -> dict[str, Any]:
        return self._transition(principal,thought_id,expected_aggregate_revision=expected_aggregate_revision,
            expected_lifecycle_revision=expected_lifecycle_revision,command="resume",state="working")

    def _transition(self, principal: Principal, thought_id: str, *, expected_aggregate_revision: int | None,
                    expected_lifecycle_revision: int | None, command: str, state: str) -> dict[str, Any]:
        self._require_owner(principal)
        if not isinstance(expected_aggregate_revision,int) or not isinstance(expected_lifecycle_revision,int):
            raise ConflictError("thought transitions require aggregate and lifecycle revisions", code="thought_expected_revision_required")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row=conn.execute("SELECT * FROM refinement_thoughts WHERE id=?",(thought_id,)).fetchone()
            if row is None: raise NotFound("thought",thought_id)
            record=self._record(row)
            allowed=(command=="complete" and record["state"]=="working") or (command=="resume" and record["state"]=="completed")
            if not allowed or record["aggregate_revision"]!=expected_aggregate_revision or record["lifecycle_revision"]!=expected_lifecycle_revision:
                raise self._conflict(conn,record,expected_aggregate_revision,None,code="thought_revision_conflict")
            now,next_life,next_agg=_now(),expected_lifecycle_revision+1,expected_aggregate_revision+1
            cur=conn.execute("UPDATE refinement_thoughts SET state=?,lifecycle_revision=?,aggregate_revision=?,resume_order=?,completed_at=?,updated_at=? WHERE id=? AND aggregate_revision=? AND lifecycle_revision=? AND state=?",
                (state,next_life,next_agg,RefinementThoughtRepository.next_resume_order(conn),now if state=="completed" else None,now,thought_id,expected_aggregate_revision,expected_lifecycle_revision,record["state"]))
            if not cur.rowcount: raise self._conflict(conn,self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?",(thought_id,)).fetchone()),expected_aggregate_revision,None)
            updated=self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?",(thought_id,)).fetchone())
            life_hash=RefinementThoughtRepository.insert_lifecycle(conn,thought_id=thought_id,lifecycle_revision=next_life,aggregate_revision=next_agg,prior_state=record["state"],state=state,command=command,occurred_at=now)
            work=conn.execute("SELECT content_sha256 FROM refinement_working_revisions WHERE thought_id=? AND revision=?",(thought_id,record["working_revision"])).fetchone()
            RefinementThoughtRepository.insert_command(conn,updated,command_kind=command,prior_working_revision=record["working_revision"],prior_lifecycle_revision=expected_lifecycle_revision,prior_attachment_revision=record["attachment_revision"],working_sha256=str(work["content_sha256"]),lifecycle_sha256=life_hash,accepted_at=now)
            return self._dto_in_transaction(conn,updated)

    def tombstone_note(self, principal: Principal, note_id: str, *, expected_aggregate_revision: int | None,
                       expected_lifecycle_revision: int | None) -> dict[str, Any]:
        self._require_owner(principal)
        if not isinstance(expected_aggregate_revision,int) or not isinstance(expected_lifecycle_revision,int):
            raise ConflictError("thought-owned notes require aggregate and lifecycle revisions", code="thought_expected_revision_required")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row=conn.execute("SELECT * FROM refinement_thoughts WHERE working_note_id=?",(note_id,)).fetchone()
            if row is None: raise NotFound("thought note",note_id)
            record=self._record(row)
            if record["state"]=="tombstoned": return self._dto_in_transaction(conn, record)
            if not RefinementThoughtRepository.terminalize_in_transaction(conn,record["id"],expected_aggregate_revision=expected_aggregate_revision,expected_lifecycle_revision=expected_lifecycle_revision):
                raise self._conflict(conn,self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?",(record["id"],)).fetchone()),expected_aggregate_revision,None)
            updated = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (record["id"],)).fetchone())
            return self._dto_in_transaction(conn, updated)

    def install_sync_bundle(self, principal: Principal, *, value: dict[str, Any], raw_utf8: bytes) -> None:
        """Install a validated full aggregate ledger on a peer that has no row."""
        self._require_sync_node(principal)
        thought_id, working = str(value["id"]), dict(value["working_note"])
        note_id, now = str(working["id"]), str(value.get("last_modified") or _now())
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if conn.execute("SELECT 1 FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone():
                raise ConflictError("thought sync aggregate already exists", code="thought_revision_conflict")
            if conn.execute("SELECT 1 FROM notes WHERE id=?", (note_id,)).fetchone():
                raise ConflictError("sync working note id already exists", code="initial_note_id_in_use")
            source=dict(value["source"])
            conn.execute("INSERT INTO notes (id,title,body_markdown,tags_json,created_at,updated_at,last_modified,deleted) VALUES (?,?,?,?,?,?,?,?)", (note_id,str(working.get("title") or ""),str(working.get("body_markdown") or ""),json.dumps(working.get("tags") or [],separators=(",",":")),now,now,now,int(value["state"]=="tombstoned")))
            conn.execute("""INSERT INTO refinement_thoughts (id,create_request_id,create_payload_sha256,raw_utf8,raw_sha256,raw_source_kind,raw_source_ref,raw_captured_at,working_note_id,working_revision,lifecycle_revision,attachment_revision,aggregate_revision,resume_order,state,created_at,updated_at,completed_at,tombstoned_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (thought_id,str(value["create_request_id"]),str(value["create_payload_sha256"]),raw_utf8,str(value["raw_sha256"]),str(source["kind"]),source.get("ref"),str(value["raw_captured_at"]),note_id,int(value["working_revision"]),int(value["lifecycle_revision"]),int(value["attachment_revision"]),int(value["aggregate_revision"]),RefinementThoughtRepository.next_resume_order(conn),str(value["state"]),str(value.get("created_at") or now),now,now if value["state"]=="completed" else None,now if value["state"]=="tombstoned" else None))
            self._install_ledger_rows(conn, thought_id, value, start_command=1)
            if value["state"] == "tombstoned":
                conn.execute("UPDATE directory_memberships SET deleted=1 WHERE primitive_id=?", (f"note:{note_id}",))

    def apply_sync_bundle(self, principal: Principal, *, thought_id: str, value: dict[str, Any]) -> None:
        """Fast-forward a validated contiguous aggregate-command suffix."""
        self._require_sync_node(principal)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row=conn.execute("SELECT * FROM refinement_thoughts WHERE id=?",(thought_id,)).fetchone()
            if row is None: raise NotFound("thought",thought_id)
            local=self._record(row); start=int(local["aggregate_revision"])+1
            if start>int(value["aggregate_revision"]): return
            self._install_ledger_rows(conn,thought_id,value,start_command=start)
            working=dict(value["working_note"]); now=str(value.get("last_modified") or _now())
            conn.execute("UPDATE notes SET title=?,body_markdown=?,tags_json=?,updated_at=?,last_modified=?,deleted=? WHERE id=?",(str(working.get("title") or ""),str(working.get("body_markdown") or ""),json.dumps(working.get("tags") or [],separators=(",",":")),now,now,int(value["state"]=="tombstoned"),local["working_note_id"]))
            conn.execute("UPDATE refinement_thoughts SET working_revision=?,lifecycle_revision=?,attachment_revision=?,aggregate_revision=?,resume_order=?,state=?,updated_at=?,completed_at=?,tombstoned_at=? WHERE id=?",(int(value["working_revision"]),int(value["lifecycle_revision"]),int(value["attachment_revision"]),int(value["aggregate_revision"]),RefinementThoughtRepository.next_resume_order(conn),str(value["state"]),now,now if value["state"]=="completed" else None,now if value["state"]=="tombstoned" else None,thought_id))
            if value["state"]=="tombstoned": conn.execute("UPDATE directory_memberships SET deleted=1,last_modified=? WHERE primitive_id=?",(now,f"note:{local['working_note_id']}"))

    @staticmethod
    def _install_ledger_rows(conn: Any, thought_id: str, value: dict[str, Any], *, start_command: int) -> None:
        existing_work={int(x["revision"]) for x in conn.execute("SELECT revision FROM refinement_working_revisions WHERE thought_id=?",(thought_id,))}
        for item in value["revisions"]:
            if int(item["revision"]) not in existing_work:
                conn.execute("INSERT INTO refinement_working_revisions (thought_id,revision,title,body_markdown,tags_json,content_sha256,accepted_at) VALUES (?,?,?,?,?,?,?)",(thought_id,int(item["revision"]),str(item.get("title") or ""),str(item.get("body_markdown") or ""),json.dumps(item.get("tags") or [],separators=(",",":")),str(item["content_sha256"]),str(item["accepted_at"])))
        existing_life={int(x["lifecycle_revision"]) for x in conn.execute("SELECT lifecycle_revision FROM refinement_lifecycle_revisions WHERE thought_id=?",(thought_id,))}
        for item in value["lifecycle"]:
            if int(item["lifecycle_revision"]) not in existing_life:
                conn.execute("INSERT INTO refinement_lifecycle_revisions (thought_id,lifecycle_revision,aggregate_revision,prior_state,state,command,occurred_at,entry_sha256) VALUES (?,?,?,?,?,?,?,?)",(thought_id,int(item["lifecycle_revision"]),int(item["aggregate_revision"]),item.get("prior_state"),str(item["state"]),str(item["command"]),str(item["occurred_at"]),str(item["entry_sha256"])))
        for item in value["commands"]:
            if int(item["aggregate_revision"]) >= start_command:
                conn.execute("INSERT INTO refinement_aggregate_commands (thought_id,aggregate_revision,command_kind,prior_working_revision,next_working_revision,prior_lifecycle_revision,next_lifecycle_revision,prior_attachment_revision,next_attachment_revision,canonical_sha256,lifecycle_sha256,accepted_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(thought_id,int(item["aggregate_revision"]),str(item["command_kind"]),int(item["prior_working_revision"]),int(item["next_working_revision"]),int(item["prior_lifecycle_revision"]),int(item["next_lifecycle_revision"]),int(item["prior_attachment_revision"]),int(item["next_attachment_revision"]),str(item["canonical_sha256"]),item.get("lifecycle_sha256"),str(item["accepted_at"])))

    def thought_for_note(self,note_id:str)->dict[str,Any]|None: return self._db.refinement_thoughts.get_by_note(note_id)
    def assert_live_filing_allowed(self,primitive_ref:str)->None:
        if primitive_ref.startswith("note:"):
            thought=self._db.refinement_thoughts.get_by_note(primitive_ref.split(":",1)[1])
            if thought and thought["state"]=="tombstoned": raise ConflictError("tombstoned thought cannot be filed",code="thought_tombstoned")

    def before_physical_dispatch(self, invocation_id: str):
        """Return the runner hook which durably binds every physical attempt."""
        def hook(operation_id: str, ask_invocation_id: str, attempt_ordinal: int) -> None:
            with self._db._connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                inv = conn.execute("SELECT * FROM refinement_invocations WHERE id=?", (invocation_id,)).fetchone()
                attempt = conn.execute("SELECT * FROM refinement_invocation_attempts WHERE invocation_id=? AND attempt_ordinal=?", (invocation_id, attempt_ordinal)).fetchone()
                if inv is None: raise ValidationError("refinement invocation is unknown", code="refinement_invocation_unknown")
                if attempt is None and attempt_ordinal == 2:
                    base = conn.execute("SELECT * FROM refinement_invocation_attempts WHERE invocation_id=? AND attempt_ordinal=1", (invocation_id,)).fetchone()
                    # The runner admits the compatibility child immediately
                    # after closing the base receipt; reconcile may not have
                    # observed it yet. Read the native receipt here rather than
                    # accepting an arbitrary in-flight predecessor.
                    base_receipt = None if base is None else conn.execute("SELECT outcome FROM kernel_receipts WHERE operation_id=?", (base["kernel_operation_id"],)).fetchone()
                    if base is None or base_receipt is None or str(base_receipt["outcome"]) != "failed": raise ValidationError("compatibility retry is not earned", code="refinement_attempt_invalid")
                    plan = conn.execute("SELECT * FROM refinement_retry_plans WHERE invocation_id=? AND parent_attempt_ordinal=1", (invocation_id,)).fetchone()
                    if plan is None or int(plan["child_attempt_ordinal"]) != 2 or str(plan["child_ask_invocation_id"]) != ask_invocation_id: raise ValidationError("compatibility retry plan is invalid", code="refinement_attempt_invalid")
                    conn.execute("UPDATE refinement_invocation_attempts SET state='failed',terminal_at=? WHERE invocation_id=? AND attempt_ordinal=1", (_now(),invocation_id))
                    conn.execute("INSERT INTO refinement_invocation_attempts(invocation_id,attempt_ordinal,ask_invocation_id,state,created_at) VALUES(?,?,?,'reserved',?)", (invocation_id,attempt_ordinal,ask_invocation_id,_now()))
                    attempt = conn.execute("SELECT * FROM refinement_invocation_attempts WHERE invocation_id=? AND attempt_ordinal=?", (invocation_id,attempt_ordinal)).fetchone()
                if attempt is None or str(attempt["ask_invocation_id"]) != ask_invocation_id or str(inv["state"]) not in {"reserved","in_flight"}:
                    raise ValidationError("refinement attempt cannot dispatch", code="refinement_attempt_invalid")
                thought = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (inv["thought_id"],)).fetchone()
                if thought is None or str(thought["state"]) != "working" or (int(thought["aggregate_revision"]),int(thought["working_revision"]),int(thought["attachment_revision"])) != (int(inv["frozen_aggregate_revision"]),int(inv["frozen_working_revision"]),int(inv["frozen_attachment_revision"])):
                    raise ValidationError("refinement source changed", code="refinement_result_stale")
                now = _now()
                if attempt["kernel_operation_id"] and str(attempt["kernel_operation_id"]) != operation_id: raise ValidationError("attempt operation changed", code="refinement_correlation_mismatch")
                conn.execute("UPDATE refinement_invocation_attempts SET kernel_operation_id=?,state='in_flight',bound_at=? WHERE invocation_id=? AND attempt_ordinal=?", (operation_id,now,invocation_id,attempt_ordinal))
                conn.execute("UPDATE refinement_invocations SET state='in_flight',updated_at=? WHERE id=?", (now,invocation_id))
        return hook

    def before_compatibility_retry(self, invocation_id: str):
        """Runner callback: record exact retry lineage before child admission."""
        def plan(parent_operation_id: str, parent_ask_id: str, child_ask_id: str, child_ordinal: int, reason: str) -> None:
            from ..kernel.provider_signals import retry_invocation_id
            if child_ordinal != 2 or child_ask_id != retry_invocation_id(parent_ask_id, 2):
                raise ValidationError("compatibility retry identity is invalid", code="refinement_attempt_invalid")
            with self._db._connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                base = conn.execute("SELECT * FROM refinement_invocation_attempts WHERE invocation_id=? AND attempt_ordinal=1", (invocation_id,)).fetchone()
                receipt = None if base is None else conn.execute("SELECT outcome FROM kernel_receipts WHERE operation_id=?", (parent_operation_id,)).fetchone()
                if base is None or str(base["ask_invocation_id"]) != parent_ask_id or str(base["kernel_operation_id"] or "") != parent_operation_id or receipt is None or str(receipt["outcome"]) != "failed":
                    raise ValidationError("compatibility retry is not earned", code="refinement_attempt_invalid")
                existing = conn.execute("SELECT * FROM refinement_retry_plans WHERE invocation_id=? AND parent_attempt_ordinal=1", (invocation_id,)).fetchone()
                if existing and (str(existing["child_ask_invocation_id"]), int(existing["child_attempt_ordinal"]), str(existing["reason"])) != (child_ask_id, 2, reason):
                    raise ConflictError("compatibility retry plan changed", code="refinement_correlation_mismatch")
                if not existing: conn.execute("INSERT INTO refinement_retry_plans(invocation_id,parent_attempt_ordinal,child_attempt_ordinal,child_ask_invocation_id,reason,created_at) VALUES(?,?,?,?,?,?)", (invocation_id,1,2,child_ask_id,reason,_now()))
        return plan

    def _cursor_secret(self, conn: Any) -> bytes:
        row = conn.execute("SELECT value FROM kernel_meta WHERE key='refinement_cursor_secret'").fetchone()
        if row is None:
            conn.execute("INSERT OR IGNORE INTO kernel_meta(key,value) VALUES('refinement_cursor_secret',?)", (uuid.uuid4().hex + uuid.uuid4().hex,))
            row = conn.execute("SELECT value FROM kernel_meta WHERE key='refinement_cursor_secret'").fetchone()
        return str(row["value"]).encode()
    def _encode_cursor(self, conn: Any, value: dict[str, Any]) -> str:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        sig = hmac.new(self._cursor_secret(conn), raw, hashlib.sha256).hexdigest()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=") + "." + sig
    def _decode_cursor(self, conn: Any, token: str) -> dict[str, Any]:
        try:
            body, sig = str(token).split(".", 1); raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
            if not hmac.compare_digest(hmac.new(self._cursor_secret(conn), raw, hashlib.sha256).hexdigest(), sig): raise ValueError
            value = json.loads(raw); assert value.get("v") == 2 and all(value.get(x) is not None for x in ("state","high","last_resume_order","last_id"))
            return value
        except Exception as exc: raise ValidationError("thought cursor is invalid", code="thought_cursor_invalid") from exc
    @staticmethod
    def _high_water(conn: Any) -> str:
        row = conn.execute("SELECT COALESCE(MAX(resume_order),0) high FROM refinement_thoughts WHERE state='working'").fetchone(); return int(row["high"])
    def _list_item_in_transaction(self, conn: Any, record: dict[str, Any], *, remote: bool) -> dict[str, Any]:
        note = conn.execute("SELECT title,body_markdown FROM notes WHERE id=?", (record["working_note_id"],)).fetchone()
        member = conn.execute("SELECT deleted FROM directory_memberships WHERE primitive_id=?", (f"note:{record['working_note_id']}",)).fetchone()
        preview = " ".join(str(note["body_markdown"] if note else "").split())[:160]
        return {"id":record["id"],"working_note_id":record["working_note_id"],"source_kind":record["raw_source_kind"],"title":str(note["title"] if note else ""),"body_preview":preview,"updated_at":record["updated_at"],"state":record["state"],"aggregate_revision":record["aggregate_revision"],"lifecycle_revision":record["lifecycle_revision"],"working_revision":record["working_revision"],"attachment_revision":record["attachment_revision"],"continuity_state":"unavailable_remote" if remote else self._continuity(conn,record["id"])["state"],"filing_status":"filed" if member and not member["deleted"] else "missing"}
    def _continuity(self, conn: Any, thought_id: str) -> dict[str, Any]:
        row = conn.execute("SELECT id,state,review_result_id,terminal_code FROM refinement_invocations WHERE thought_id=? ORDER BY created_at DESC LIMIT 1", (thought_id,)).fetchone()
        if row is None: return {"state":"idle","code":""}
        state = str(row["state"]); return {"state": "named_failure" if state in {"failed","refused","cancelled","indeterminate","unknown","superseded"} else state, "invocation_id":str(row["id"]), "review_result_id":row["review_result_id"], "code":str(row["terminal_code"] or "")}
    @staticmethod
    def _supersede_invocations(conn: Any, thought_id: str, code: str) -> None:
        now = _now()
        conn.execute("UPDATE refinement_invocations SET state='superseded',terminal_code=?,updated_at=?,terminal_at=? WHERE thought_id=? AND state IN ('reserved','in_flight','awaiting_projection','review_ready')", (code,now,now,thought_id))
    def _invocation_dto(self, conn: Any, inv: dict[str, Any]) -> dict[str, Any]:
        attempts = conn.execute("SELECT attempt_ordinal,ask_invocation_id,state FROM refinement_invocation_attempts WHERE invocation_id=? ORDER BY attempt_ordinal", (inv["id"],)).fetchall()
        return {"id":inv["id"],"request_id":inv["request_id"],"thought_id":inv["thought_id"],"frozen_aggregate_revision":inv["frozen_aggregate_revision"],"frozen_working_revision":inv["frozen_working_revision"],"frozen_attachment_revision":inv["frozen_attachment_revision"],"state":inv["state"],"attempts":[{"attempt_ordinal":x["attempt_ordinal"],"ask_invocation_id":x["ask_invocation_id"],"state":x["state"]} for x in attempts]}
    def _reconcile_invocation_in_transaction(self, conn: Any, inv: dict[str, Any], thought: dict[str, Any]) -> None:
        if (int(thought["aggregate_revision"]),int(thought["working_revision"]),int(thought["attachment_revision"])) != (int(inv["frozen_aggregate_revision"]),int(inv["frozen_working_revision"]),int(inv["frozen_attachment_revision"])):
            conn.execute("UPDATE refinement_invocations SET state='stale',terminal_code='refinement_result_stale',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"])); return
        attempts = conn.execute("SELECT * FROM refinement_invocation_attempts WHERE invocation_id=? ORDER BY attempt_ordinal", (inv["id"],)).fetchall()
        # A crash can land after the runner durably plans the one compatibility
        # child but before that child's pre-dispatch hook has created its attempt
        # row. Reconcile names this exact plan; it never reconstructs/rebinds it.
        plans = conn.execute("SELECT * FROM refinement_retry_plans WHERE invocation_id=?", (inv["id"],)).fetchall()
        ordinals = {int(item["attempt_ordinal"]) for item in attempts}
        for plan in plans:
            child_ordinal = int(plan["child_attempt_ordinal"])
            if child_ordinal in ordinals:
                continue
            base = next((item for item in attempts if int(item["attempt_ordinal"]) == int(plan["parent_attempt_ordinal"])), None)
            from ..kernel.provider_signals import retry_invocation_id
            expected = retry_invocation_id(str(base["ask_invocation_id"]) if base else "", child_ordinal)
            if base is None or str(plan["child_ask_invocation_id"]) != expected:
                conn.execute("UPDATE refinement_invocations SET state='unknown',terminal_code='retry_plan_invalid',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"])); return
            native = conn.execute("SELECT operation_id FROM kernel_operations WHERE native_id=?", (str(plan["child_ask_invocation_id"]),)).fetchone()
            if native is not None:
                conn.execute("INSERT INTO refinement_invocation_attempts(invocation_id,attempt_ordinal,ask_invocation_id,state,terminal_code,created_at,terminal_at) VALUES(?,?,?,'orphaned_before_dispatch_binding','orphaned_before_dispatch_binding',?,?)", (inv["id"],child_ordinal,str(plan["child_ask_invocation_id"]),_now(),_now()))
                conn.execute("UPDATE refinement_invocations SET state='unknown',terminal_code='orphaned_before_dispatch_binding',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"])); return
            conn.execute("UPDATE refinement_invocations SET state='failed',terminal_code='retry_child_missing_after_plan',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"])); return
        winners: list[tuple[Any, Any, str]] = []; known_success = False
        for attempt in attempts:
            op = str(attempt["kernel_operation_id"] or "")
            if not op:
                native = conn.execute("SELECT operation_id FROM kernel_operations WHERE native_id=?", (attempt["ask_invocation_id"],)).fetchone()
                if native:
                    conn.execute("UPDATE refinement_invocation_attempts SET state='orphaned_before_dispatch_binding',terminal_code='orphaned_before_dispatch_binding',terminal_at=? WHERE invocation_id=? AND attempt_ordinal=?", (_now(),inv["id"],attempt["attempt_ordinal"]))
                    conn.execute("UPDATE refinement_invocations SET state='unknown',terminal_code='orphaned_before_dispatch_binding',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"])); return
                continue
            row = conn.execute("SELECT r.receipt_id,r.outcome,r.result_ref,s.stage_id,s.kind,s.state stage_state,s.invocation_id stage_invocation,s.operation_id stage_operation,s.result_ref stage_result_ref,a.projection_stage_id,a.invocation_id ask_invocation,a.operation_id ask_operation,a.receipt_id ask_receipt,a.payload_json FROM kernel_receipts r LEFT JOIN kernel_projection_stages s ON s.operation_id=r.operation_id LEFT JOIN ask_results a ON a.operation_id=r.operation_id WHERE r.operation_id=?", (op,)).fetchone()
            if row is None: continue
            if str(row["outcome"]) == "succeeded": known_success = True
            if str(row["outcome"]) == "succeeded" and row["projection_stage_id"] and str(row["result_ref"]) and str(row["stage_id"] or "") == str(row["projection_stage_id"]) and str(row["kind"] or "") == "ask-result" and str(row["stage_state"] or "") == "PUBLISHED" and str(row["stage_invocation"] or "") == str(attempt["ask_invocation_id"]) and str(row["ask_invocation"] or "") == str(attempt["ask_invocation_id"]) and str(row["stage_operation"] or "") == op and str(row["ask_operation"] or "") == op and str(row["ask_receipt"] or "") == str(row["receipt_id"]) and str(row["stage_result_ref"] or "") == str(row["result_ref"]):
                winners.append((attempt,row,hashlib.sha256(str(row["payload_json"]).encode()).hexdigest()))
            conn.execute("UPDATE refinement_invocation_attempts SET state=?,receipt_id=?,result_ref=?,terminal_at=? WHERE invocation_id=? AND attempt_ordinal=?", (str(row["outcome"]),row["receipt_id"],row["result_ref"],_now(),inv["id"],attempt["attempt_ordinal"]))
        if len(winners) > 1:
            raise ConflictError("multiple refinement result attempts matched", code="refinement_correlation_mismatch")
        if winners:
            attempt,row,digest=winners[0]; existing=conn.execute("SELECT * FROM refinement_review_results WHERE invocation_id=?",(inv["id"],)).fetchone(); rid=str(existing["id"]) if existing else _id("rresult")
            if not existing:
                conn.execute("INSERT INTO refinement_review_results(id,invocation_id,attempt_ordinal,ask_result_stage_id,ask_invocation_id,kernel_operation_id,receipt_id,result_ref,frozen_aggregate_revision,frozen_working_revision,frozen_attachment_revision,result_sha256,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(rid,inv["id"],attempt["attempt_ordinal"],row["projection_stage_id"],attempt["ask_invocation_id"],attempt["kernel_operation_id"],row["receipt_id"],row["result_ref"],inv["frozen_aggregate_revision"],inv["frozen_working_revision"],inv["frozen_attachment_revision"],digest,_now()))
            elif (str(existing["ask_result_stage_id"]),str(existing["ask_invocation_id"]),str(existing["kernel_operation_id"]),str(existing["receipt_id"]),str(existing["result_ref"]),str(existing["result_sha256"])) != (str(row["projection_stage_id"]),str(attempt["ask_invocation_id"]),str(attempt["kernel_operation_id"]),str(row["receipt_id"]),str(row["result_ref"]),digest):
                raise ConflictError("stored review result does not match native proof", code="refinement_correlation_mismatch")
            conn.execute("UPDATE refinement_invocation_attempts SET state='succeeded',receipt_id=?,projection_stage_id=?,ask_result_stage_id=?,result_ref=?,terminal_at=? WHERE invocation_id=? AND attempt_ordinal=?",(row["receipt_id"],row["stage_id"],row["projection_stage_id"],row["result_ref"],_now(),inv["id"],attempt["attempt_ordinal"]))
            conn.execute("UPDATE refinement_invocations SET state='review_ready',review_result_id=?,updated_at=? WHERE id=?",(rid,_now(),inv["id"]))
        elif attempts and all(not str(item["kernel_operation_id"] or "") for item in attempts):
            conn.execute("UPDATE refinement_invocations SET state='unknown',terminal_code='kernel_operation_missing',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"]))
        elif known_success:
            conn.execute("UPDATE refinement_invocations SET state='awaiting_projection',terminal_code='ask_result_unpublished',updated_at=? WHERE id=?", (_now(),inv["id"]))
        else:
            fresh_attempts = conn.execute("SELECT state,terminal_code FROM refinement_invocation_attempts WHERE invocation_id=? ORDER BY attempt_ordinal", (inv["id"],)).fetchall()
            plans = conn.execute("SELECT child_attempt_ordinal FROM refinement_retry_plans WHERE invocation_id=?", (inv["id"],)).fetchall()
            planned_children = {int(row["child_attempt_ordinal"]) for row in plans}
            present = set(range(1, len(fresh_attempts) + 1))
            terminal = {"failed", "refused", "cancelled", "indeterminate", "orphaned_before_dispatch_binding"}
            if fresh_attempts and all(str(row["state"]) in terminal for row in fresh_attempts) and planned_children <= present:
                last = fresh_attempts[-1]
                state = "unknown" if str(last["state"]) == "orphaned_before_dispatch_binding" else str(last["state"])
                conn.execute("UPDATE refinement_invocations SET state=?,terminal_code=?,updated_at=?,terminal_at=? WHERE id=?", (state,str(last["terminal_code"] or state),_now(),_now(),inv["id"]))
    def _dto(self,record:dict[str,Any],*,include_raw:bool=False,remote:bool=False)->dict[str,Any]:
        with self._db._connection() as conn: return self._dto_in_transaction(conn,record,include_raw=include_raw,remote=remote)
    def _dto_in_transaction(self,conn:Any,record:dict[str,Any],*,include_raw:bool=False,remote:bool=False)->dict[str,Any]:
        note=conn.execute("SELECT * FROM notes WHERE id=?",(record["working_note_id"],)).fetchone(); member=conn.execute("SELECT * FROM directory_memberships WHERE primitive_id=?",(f"note:{record['working_note_id']}",)).fetchone()
        out={"id":record["id"],"raw_id":record["id"],"raw_sha256":record["raw_sha256"],"source":{"kind":record["raw_source_kind"]},"raw_captured_at":record["raw_captured_at"],"state":record["state"],"aggregate_revision":record["aggregate_revision"],"lifecycle_revision":record["lifecycle_revision"],"working_revision":record["working_revision"],"attachment_revision":record["attachment_revision"],"working_note":self._note(note),"filing_status":"filed" if member and not member["deleted"] else "missing","continuity":({"state":"unavailable_remote","code":"continuity_unavailable_remote"} if remote else self._continuity(conn,record["id"]))}
        if member and not member["deleted"]: out["directory_id"]=member["directory_id"]
        if include_raw:
            out["raw_text"]=base64.b64decode(record["raw_utf8_b64"]).decode("utf-8","strict"); out["source"]["ref"]=record["raw_source_ref"]
        return out
    @staticmethod
    def _note(row:Any)->dict[str,Any]|None:
        return None if row is None else {"id":row["id"],"title":row["title"],"body_markdown":row["body_markdown"],"tags":json.loads(row["tags_json"]),"deleted":bool(row["deleted"]),"last_modified":row["last_modified"]}
    @staticmethod
    def _record(row:Any)->dict[str,Any]:
        d=dict(row); d["raw_utf8_b64"]=base64.b64encode(bytes(d.pop("raw_utf8"))).decode("ascii"); return d
    @staticmethod
    def _insert_revision(conn:Any,thought_id:str,revision:int,title:str,body:str,tags:list[str],now:str)->str:
        digest=RefinementThoughtRepository.content_hash(title,body,tags); conn.execute("INSERT INTO refinement_working_revisions (thought_id,revision,title,body_markdown,tags_json,content_sha256,accepted_at) VALUES (?,?,?,?,?,?,?)",(thought_id,revision,title,body,json.dumps(tags,separators=(",",":")),digest,now)); return digest
    def _conflict(self,conn:Any,record:dict[str,Any],expected_aggregate:int|None,expected_working:int|None,*,code:str="thought_revision_conflict")->ConflictError:
        return ConflictError("working thought changed elsewhere",code=code,context={"thought_id":record["id"],"expected_aggregate_revision":expected_aggregate,"actual_aggregate_revision":record["aggregate_revision"],"actual_lifecycle_revision":record["lifecycle_revision"],"expected_working_revision":expected_working,"actual_working_revision":record["working_revision"],"current":self._dto_in_transaction(conn,record)})
