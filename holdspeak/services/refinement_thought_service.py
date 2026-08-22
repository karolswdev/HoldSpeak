"""HS-141-01 custody aggregate service: every mutation appends one command."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

from ..db.core import Database
from ..db.refinement_thoughts import RefinementThoughtRepository, _now, canonical_json
from ..db.relationships import qualified_ref
from ..principals import Principal, PrincipalKind
from .errors import ConflictError, NotFound, ValidationError

INBOX_DIRECTORY_ID = "hs-seed-inbox"
_SOURCES = frozenset({"typed", "voice", "note"})

_TERMINAL_CODE_CATEGORY = {
    **{code:"owner_terminal" for code in (
        "owner_stopped","owner_stopped_after_dispatch","owner_answered","owner_accepted",
        "owner_rejected","owner_edited","owner_context_changed","thought_completed","thought_tombstoned")},
    **{code:"retryable" for code in (
        "shutdown_before_dispatch","scheduler_lost_before_dispatch","refinement_pre_admission_failed",
        "refinement_coordinator_unavailable","provider_unavailable","target_unavailable",
        "refinement_admission_changed","refinement_host_lease_expired","failed")},
    **{code:"indeterminate" for code in (
        "restart_bound_outcome_unknown","orphaned_before_dispatch_binding","kernel_operation_missing",
        "ask_result_unpublished","indeterminate","cancelled")},
    **{code:"integrity" for code in (
        "thought_missing_during_recovery","retry_plan_invalid","retry_child_missing_after_plan",
        "refinement_result_invalid","refinement_result_stale","refused","unknown_terminal_code")},
}


def _closed_terminal_code(code: str) -> str:
    return code if code in _TERMINAL_CODE_CATEGORY else "unknown_terminal_code"


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
        thought, _receipt = self.create_with_default(
            principal, request_id=request_id, raw_text=raw_text, source=source,
            initial_note=initial_note, thought_id=thought_id,
        )
        return thought

    def create_with_default(self, principal: Principal, *, request_id: str,
                            raw_text: str, source: dict[str, Any] | None = None,
                            initial_note: dict[str, Any] | None = None,
                            thought_id: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        self._require_product_owner(principal)
        if not isinstance(request_id, str) or not request_id.strip() or not isinstance(raw_text, str) or not raw_text:
            raise ValidationError("request_id and raw_text are required")
        request_id = request_id.strip()
        if source is not None and (not isinstance(source, dict)
                or set(source) - {"kind", "ref"}
                or "kind" not in source
                or not isinstance(source.get("kind"), str)
                or (source.get("ref") is not None and not isinstance(source.get("ref"), str))):
            raise ValidationError("source must be a closed kind/ref object",
                                  code="thought_create_request_invalid")
        source = dict(source or {"kind": "typed"})
        kind = source["kind"].strip().lower()
        raw_ref = source.get("ref")
        ref = raw_ref.strip() or None if isinstance(raw_ref, str) else None
        if kind not in _SOURCES:
            raise ValidationError("invalid raw source")
        if kind == "note":
            try: ref = qualified_ref(ref)
            except ValueError as exc: raise ValidationError("note source requires a qualified ref") from exc
        elif ref:
            raise ValidationError("only note source may carry ref")
        raw = raw_text.encode("utf-8", "strict")
        if initial_note is not None and (not isinstance(initial_note, dict)
                or set(initial_note) - {"id", "title", "body_markdown", "tags"}
                or ("id" in initial_note and not isinstance(initial_note["id"], str))
                or ("title" in initial_note and not isinstance(initial_note["title"], str))
                or ("body_markdown" in initial_note and not isinstance(initial_note["body_markdown"], str))
                or ("tags" in initial_note and (not isinstance(initial_note["tags"], list)
                    or any(not isinstance(tag, str) for tag in initial_note["tags"])))):
            raise ValidationError("initial_note must be a closed typed object",
                                  code="thought_create_request_invalid")
        note_input = dict(initial_note or {})
        raw_note_id = note_input.get("id")
        note_id = (raw_note_id.strip() if isinstance(raw_note_id, str) and raw_note_id
                   else f"note_thought_{hashlib.sha256(request_id.encode()).hexdigest()[:16]}")
        if not note_id: raise ValidationError("initial note id is invalid")
        title = note_input.get("title") or "First thought"
        body = note_input.get("body_markdown") or raw_text
        tags = list(note_input.get("tags") or [])
        payload_hash = RefinementThoughtRepository.payload_hash(raw, kind, ref, {"id": note_id, "title": title, "body_markdown": body, "tags": tags})
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute("SELECT * FROM refinement_thoughts WHERE create_request_id=?", (request_id,)).fetchone()
            if prior:
                record = self._record(prior)
                if record["create_payload_sha256"] != payload_hash:
                    raise ConflictError("create request was already used for different content", code="idempotency_payload_mismatch")
                from .refinement_context_service import RefinementContextService
                receipt = RefinementContextService(self._db).default_application_receipt_in_transaction(
                    conn, thought_id=record["id"], create_request_id=request_id
                )
                return self._dto_in_transaction(conn, record), receipt
            if conn.execute("SELECT 1 FROM directories WHERE id=? AND deleted=0", (INBOX_DIRECTORY_ID,)).fetchone() is None:
                raise ValidationError("Inbox is unavailable", code="inbox_unavailable")
            thought_id = str(thought_id or _id("thought")).strip()
            if not thought_id: raise ValidationError("thought id is invalid")
            if conn.execute("SELECT 1 FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone():
                raise ConflictError("thought id already exists", code="thought_id_in_use")
            if conn.execute("SELECT 1 FROM notes WHERE id=?", (note_id,)).fetchone():
                raise ConflictError("initial note id already exists", code="initial_note_id_in_use")
            now, raw_hash = _now(), hashlib.sha256(raw).hexdigest()
            attachment_hash = RefinementThoughtRepository.empty_attachment_hash(thought_id)
            resume_order = RefinementThoughtRepository.next_resume_order(conn)
            self._db.notes._upsert_in_transaction(conn, note_id=note_id, title=title, body_markdown=body, tags=tags, now=now)
            conn.execute("""INSERT INTO refinement_thoughts (id,create_request_id,create_payload_sha256,raw_utf8,raw_sha256,
                raw_source_kind,raw_source_ref,raw_captured_at,working_note_id,working_revision,lifecycle_revision,attachment_revision,
                attachment_sha256,aggregate_revision,resume_order,state,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,1,1,0,?,1,?,'working',?,?)""",
                (thought_id,request_id,payload_hash,raw,raw_hash,kind,ref,now,note_id,attachment_hash,resume_order,now,now))
            working_hash = self._insert_revision(conn, thought_id, 1, title, body, tags, now)
            record = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            life_hash = RefinementThoughtRepository.insert_lifecycle(conn, thought_id=thought_id, lifecycle_revision=1, aggregate_revision=1,
                prior_state=None, state="working", command="create", occurred_at=now)
            RefinementThoughtRepository.insert_command(conn, record, command_kind="create", prior_working_revision=0,
                prior_lifecycle_revision=0, prior_attachment_revision=0, working_sha256=working_hash, lifecycle_sha256=life_hash, accepted_at=now)
            conn.execute("""INSERT INTO directory_memberships (primitive_id,directory_id,created_at,last_modified,deleted)
                VALUES (?,?,?,?,0) ON CONFLICT(primitive_id) DO UPDATE SET directory_id=excluded.directory_id,last_modified=excluded.last_modified,deleted=0""",
                (f"note:{note_id}", INBOX_DIRECTORY_ID, now, now))
            from .refinement_context_service import RefinementContextService
            record, receipt = RefinementContextService(self._db).apply_default_at_birth_in_transaction(
                conn, thought=record, create_request_id=request_id,
                working_sha256=working_hash, occurred_at=now,
            )
            return self._dto_in_transaction(conn, record), receipt

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
        thought, _receipt = self.adopt_note_with_default(
            principal, request_id=request_id, note_id=note_id,
            expected_source_content_sha256=expected_source_content_sha256,
            expected_source_last_modified=expected_source_last_modified,
        )
        return thought

    def adopt_note_with_default(self, principal: Principal, *, request_id: str, note_id: str,
                                expected_source_content_sha256: str,
                                expected_source_last_modified: str) -> tuple[dict[str, Any], dict[str, Any]]:
        """Atomically make one existing Note the durable working thought.

        The source Note is read and snapshot under the same IMMEDIATE transaction
        that claims ownership.  It is deliberately never inserted, updated, or
        deleted by adoption.
        """
        self._require_product_owner(principal)
        values = (request_id, note_id, expected_source_content_sha256,
                  expected_source_last_modified)
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValidationError("request_id, note_id, and source precondition are required", code="note_adoption_precondition_required")
        request_id, note_id = request_id.strip(), note_id.strip()
        content_digest = expected_source_content_sha256.strip()
        modified = expected_source_last_modified.strip()
        request_digest = hashlib.sha256(canonical_json({"kind": "adopt_note", "request_id": request_id, "note_id": note_id,
            "expected_source_content_sha256": content_digest, "expected_source_last_modified": modified})).hexdigest()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute("SELECT * FROM refinement_thoughts WHERE create_request_id=?", (request_id,)).fetchone()
            if prior is not None:
                record = self._record(prior)
                if record["create_payload_sha256"] != request_digest:
                    raise ConflictError("create request was already used for different content", code="idempotency_payload_mismatch")
                from .refinement_context_service import RefinementContextService
                receipt = RefinementContextService(self._db).default_application_receipt_in_transaction(
                    conn, thought_id=record["id"], create_request_id=request_id
                )
                return self._dto_in_transaction(conn, record), receipt
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
            attachment_hash = RefinementThoughtRepository.empty_attachment_hash(thought_id)
            resume_order = RefinementThoughtRepository.next_resume_order(conn)
            conn.execute("""INSERT INTO refinement_thoughts (id,create_request_id,create_payload_sha256,raw_utf8,raw_sha256,
                raw_source_kind,raw_source_ref,raw_captured_at,working_note_id,working_revision,lifecycle_revision,attachment_revision,
                attachment_sha256,aggregate_revision,resume_order,state,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,1,1,0,?,1,?,'working',?,?)""",
                (thought_id, request_id, request_digest, raw, hashlib.sha256(raw).hexdigest(), "note", f"note:{note_id}", now, note_id, attachment_hash, resume_order, now, now))
            record = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            working_hash = self._insert_revision(conn, thought_id, 1, str(note["title"]), str(note["body_markdown"]), tags, now)
            life_hash = RefinementThoughtRepository.insert_lifecycle(conn, thought_id=thought_id, lifecycle_revision=1, aggregate_revision=1,
                prior_state=None, state="working", command="adopt_note", occurred_at=now)
            RefinementThoughtRepository.insert_command(conn, record, command_kind="adopt_note", prior_working_revision=0,
                prior_lifecycle_revision=0, prior_attachment_revision=0, working_sha256=working_hash, lifecycle_sha256=life_hash, accepted_at=now)
            conn.execute("""INSERT INTO directory_memberships (primitive_id,directory_id,created_at,last_modified,deleted)
                VALUES (?,?,?,?,0) ON CONFLICT(primitive_id) DO UPDATE SET directory_id=excluded.directory_id,last_modified=excluded.last_modified,deleted=0""",
                (f"note:{note_id}", INBOX_DIRECTORY_ID, now, now))
            from .refinement_context_service import RefinementContextService
            record, receipt = RefinementContextService(self._db).apply_default_at_birth_in_transaction(
                conn, thought=record, create_request_id=request_id,
                working_sha256=working_hash, occurred_at=now,
            )
            return self._dto_in_transaction(conn, record), receipt

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
                  invocation_id: str | None = None,
                  workspace_cursor: dict[str, Any] | None = None) -> dict[str, Any]:
        """Read/finalize only existing local proof; never creates or dispatches Ask."""
        self._require_product_owner(principal)
        if not isinstance(expected_aggregate_revision, int):
            raise ConflictError("thought reconciliation requires aggregate revision", code="thought_expected_revision_required")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if row is None: raise NotFound("thought", thought_id)
            record = self._record(row)
            self._validate_workspace_cursor_in_transaction(conn, record, workspace_cursor, relaxed=True)
            if workspace_cursor is not None:
                live_cursor_inv = conn.execute(
                    "SELECT id FROM refinement_invocations WHERE thought_id=? AND state IN ('reserved','in_flight','awaiting_projection','review_ready') ORDER BY created_at DESC,rowid DESC LIMIT 1",
                    (thought_id,),
                ).fetchone()
                if invocation_id is None or live_cursor_inv is None or str(live_cursor_inv["id"]) != invocation_id:
                    raise ConflictError("reconcile cursor must name the current invocation",
                                        code="workspace_cursor_invocation_mismatch")
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
            inv = conn.execute("SELECT * FROM refinement_invocations WHERE thought_id=?" + (" AND id=?" if invocation_id else "") + " ORDER BY created_at DESC,rowid DESC LIMIT 1", (thought_id, invocation_id) if invocation_id else (thought_id,)).fetchone()
            if inv is None:
                return self._dto_in_transaction(conn, record)
            before = (str(inv["state"]), str(inv["terminal_code"] or ""), str(inv["review_result_id"] or ""))
            self._reconcile_invocation_in_transaction(conn, dict(inv), record)
            after = conn.execute("SELECT state,terminal_code,review_result_id FROM refinement_invocations WHERE id=?", (inv["id"],)).fetchone()
            if after and before != (str(after["state"]), str(after["terminal_code"] or ""), str(after["review_result_id"] or "")):
                self._bump_continuity(conn, thought_id)
            fresh = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            return self._dto_in_transaction(conn, fresh)

    def reserve_refinement(self, principal: Principal, thought_id: str, *, request_id: str,
                           expected_aggregate_revision: int, expected_working_revision: int,
                           expected_attachment_revision: int) -> dict[str, Any]:
        invocation, _created = self.reserve_refinement_with_dispatch_claim(
            principal, thought_id, request_id=request_id,
            expected_aggregate_revision=expected_aggregate_revision,
            expected_working_revision=expected_working_revision,
            expected_attachment_revision=expected_attachment_revision,
        )
        return invocation

    def get_invocation(self, principal: Principal, invocation_id: str) -> dict[str, Any]:
        self._require_owner(principal)
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM refinement_invocations WHERE id=?", (invocation_id,)
            ).fetchone()
            if row is None:
                raise NotFound("refinement invocation", invocation_id)
            return self._invocation_dto(conn, dict(row))

    def reserve_refinement_with_dispatch_claim(
        self, principal: Principal, thought_id: str, *, request_id: str,
        expected_aggregate_revision: int, expected_working_revision: int,
        expected_attachment_revision: int, dispatch_host_id: str | None = None,
        dispatch_lease_epoch: int | None = None,
        workspace_cursor: dict[str, Any] | None = None,
        admission_claim: dict[str, Any] | None = None,
        validate_current_admission: bool = False,
        routed_admission: Callable[[Any, str, str], Mapping[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        """Persist identity and atomically grant dispatch only to its creator."""
        self._require_product_owner(principal)
        semantic = {"request_id": str(request_id), "thought_id": str(thought_id), "frozen_aggregate_revision": expected_aggregate_revision,
                    "frozen_working_revision": expected_working_revision, "frozen_attachment_revision": expected_attachment_revision, "purpose": "refinement"}
        digest = hashlib.sha256(json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute("SELECT * FROM refinement_invocations WHERE request_id=?", (request_id,)).fetchone()
            if existing:
                if str(existing["request_sha256"]) != digest: raise ConflictError("request was already used for different refinement", code="refinement_request_payload_mismatch")
                return self._invocation_dto(conn, dict(existing)), False
            thought = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if thought is None: raise NotFound("thought", thought_id)
            record = self._record(thought)
            self._validate_workspace_cursor_in_transaction(conn, record, workspace_cursor)
            if record["state"] != "working": raise ConflictError("thought is not available for refinement", code="thought_" + str(record["state"]))
            if (record["aggregate_revision"], record["working_revision"], record["attachment_revision"]) != (expected_aggregate_revision, expected_working_revision, expected_attachment_revision):
                raise self._conflict(conn, record, expected_aggregate_revision, expected_working_revision)
            note = conn.execute("SELECT deleted FROM notes WHERE id=?", (record["working_note_id"],)).fetchone()
            if note is None or note["deleted"]: raise ConflictError("working thought was deleted", code="thought_tombstoned")
            live = conn.execute("SELECT id FROM refinement_invocations WHERE thought_id=? AND state IN ('reserved','in_flight','awaiting_projection','review_ready')", (thought_id,)).fetchone()
            if live: raise ConflictError("a refinement is already live", code="refinement_already_live", context={"invocation_id": str(live["id"])})
            now, iid, ask = _now(), _id("rinv"), _id("ask")
            if dispatch_host_id:
                lease_now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
                host = conn.execute(
                    "SELECT host_kind,lease_epoch,expires_at FROM refinement_hosts WHERE host_id=?",
                    (dispatch_host_id,),
                ).fetchone()
                if host is None or int(host["lease_epoch"]) != int(dispatch_lease_epoch or 0) or str(host["expires_at"]) <= lease_now:
                    raise ConflictError("refinement execution host lease is not live", code="refinement_host_lease_expired")
            admission_json, admission_sha = self._validated_admission_claim(admission_claim, required=bool(dispatch_host_id))
            if dispatch_host_id and validate_current_admission:
                self._validate_current_admission_under_write_fence(conn, admission_claim)
            attachment_hash = str(record.get("attachment_sha256") or RefinementThoughtRepository.empty_attachment_hash(thought_id))
            conn.execute("INSERT INTO refinement_invocations(id,request_id,request_sha256,thought_id,frozen_aggregate_revision,frozen_working_revision,frozen_attachment_revision,frozen_attachment_sha256,admission_json,admission_sha256,state,dispatch_host_id,dispatch_lease_epoch,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,'reserved',?,?,?,?)", (iid,request_id,digest,thought_id,expected_aggregate_revision,expected_working_revision,expected_attachment_revision,attachment_hash,admission_json,admission_sha,dispatch_host_id,dispatch_lease_epoch,now,now))
            conn.execute("INSERT INTO refinement_invocation_attempts(invocation_id,attempt_ordinal,ask_invocation_id,state,created_at) VALUES(?,1,?,'reserved',?)", (iid,ask,now))
            if routed_admission is not None:
                admitted = dict(routed_admission(conn, iid, ask))
                conn.execute(
                    "UPDATE refinement_invocations SET route_plan_id=?,operation_plan_id=?,route_execution_id=? WHERE id=?",
                    (
                        admitted["route_plan"]["id"],
                        admitted["operation_request_plan"]["id"],
                        admitted["execution"]["id"],
                        iid,
                    ),
                )
            self._bump_continuity(conn, thought_id)
            return self._invocation_dto(conn, dict(conn.execute("SELECT * FROM refinement_invocations WHERE id=?", (iid,)).fetchone())), True

    def claim_refinement_host(self, host_id: str, host_kind: str, *, lease_seconds: float) -> int:
        if host_kind not in {"web", "mcp", "test"}:
            raise ValueError("invalid refinement host kind")
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat(timespec="microseconds").replace("+00:00", "Z")
        expires = (now_dt + timedelta(seconds=lease_seconds)).isoformat(timespec="microseconds").replace("+00:00", "Z")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute("SELECT lease_epoch FROM refinement_hosts WHERE host_id=?", (host_id,)).fetchone()
            epoch = int(prior["lease_epoch"]) + 1 if prior else 1
            conn.execute(
                "INSERT INTO refinement_hosts(host_id,host_kind,lease_epoch,heartbeat_at,expires_at) VALUES(?,?,?,?,?) "
                "ON CONFLICT(host_id) DO UPDATE SET host_kind=excluded.host_kind,lease_epoch=excluded.lease_epoch,heartbeat_at=excluded.heartbeat_at,expires_at=excluded.expires_at",
                (host_id, host_kind, epoch, now, expires),
            )
            return epoch

    def answer_and_continue_with_dispatch_claim(
        self, principal: Principal, thought_id: str, review_result_id: str, *,
        command_id: str, answer: str, expected_aggregate_revision: int,
        expected_working_revision: int, expected_attachment_revision: int,
        workspace_cursor: dict[str, Any], dispatch_host_id: str,
        dispatch_lease_epoch: int,
        admission_claim: dict[str, Any],
        validate_current_admission: bool = False,
        routed_admission: Callable[[Any, str, str, str], Mapping[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], bool]:
        """Append an answer and reserve its one child in the same transaction."""
        self._require_owner(principal)
        if not isinstance(command_id, str) or not command_id.strip():
            raise ValidationError("command_id is required", code="answer_continue_request_invalid")
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 12000:
            raise ValidationError("answer is invalid", code="refinement_answer_too_long")
        command_id = command_id.strip()
        semantic = {"command_id":command_id,"thought_id":thought_id,
                    "review_result_id":review_result_id,"answer_sha256":hashlib.sha256(answer.encode()).hexdigest(),
                    "aggregate":expected_aggregate_revision,"working":expected_working_revision,
                    "attachment":expected_attachment_revision}
        digest = hashlib.sha256(canonical_json(semantic)).hexdigest()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute("SELECT * FROM refinement_answer_continue_commands WHERE command_id=?", (command_id,)).fetchone()
            thoughtrow = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if thoughtrow is None: raise NotFound("thought", thought_id)
            record = self._record(thoughtrow)
            if prior is not None:
                if str(prior["request_sha256"]) != digest:
                    raise ConflictError("answer-and-continue command changed", code="answer_continue_payload_mismatch")
                invocation = conn.execute("SELECT * FROM refinement_invocations WHERE id=?", (prior["child_invocation_id"],)).fetchone()
                if invocation is None: raise ConflictError("answer-and-continue proof is incomplete", code="answer_continue_integrity")
                action = conn.execute("SELECT * FROM refinement_review_actions WHERE action_id=?", (prior["action_id"],)).fetchone()
                if action is None:
                    raise ConflictError("answer-and-continue proof is incomplete", code="answer_continue_integrity")
                effect = self._validated_append_effect(conn, action)
                child_request_id = "next_" + hashlib.sha256(command_id.encode()).hexdigest()[:24]
                child_semantic = {"request_id":child_request_id,"thought_id":thought_id,
                                  "frozen_aggregate_revision":int(action["post_aggregate_revision"]),
                                  "frozen_working_revision":int(action["post_working_revision"]),
                                  "frozen_attachment_revision":int(action["attachment_revision"]),
                                  "purpose":"refinement_after_answer"}
                child_digest = hashlib.sha256(canonical_json(child_semantic)).hexdigest()
                linked = (
                    str(prior["thought_id"]) == thought_id
                    and str(prior["review_result_id"]) == review_result_id
                    and str(action["action_id"]) == str(prior["action_id"])
                    and str(action["request_id"]) == command_id
                    and str(action["request_sha256"]) == digest
                    and str(action["thought_id"]) == thought_id
                    and str(action["review_result_id"]) == review_result_id
                    and str(action["action_kind"]) == "answer"
                    and int(action["post_aggregate_revision"]) == int(prior["post_aggregate_revision"])
                    and int(action["post_working_revision"]) == int(prior["post_working_revision"])
                    and int(action["post_continuity_revision"]) == int(prior["post_continuity_revision"])
                    and str(invocation["id"]) == str(prior["child_invocation_id"])
                    and str(invocation["thought_id"]) == thought_id
                    and str(invocation["request_id"]) == child_request_id
                    and str(invocation["request_sha256"]) == child_digest
                    and int(invocation["frozen_aggregate_revision"]) == int(action["post_aggregate_revision"])
                    and int(invocation["frozen_working_revision"]) == int(action["post_working_revision"])
                    and int(invocation["frozen_attachment_revision"]) == int(action["attachment_revision"])
                )
                if (not linked or canonical_json(effect).decode() != str(prior["append_effect_json"])):
                    raise ConflictError("answer-and-continue proof is invalid", code="answer_continue_integrity")
                receipt = {"id":command_id,"kind":"answer_and_continue","effect":effect,
                           "child_invocation_id":str(prior["child_invocation_id"])}
                return self._dto_in_transaction(conn, record), receipt, self._invocation_dto(conn, dict(invocation)), False
            self._validate_workspace_cursor_in_transaction(conn, record, workspace_cursor, required=True)
            if (record["state"] != "working"
                    or (int(record["aggregate_revision"]),int(record["working_revision"]),int(record["attachment_revision"]))
                    != (expected_aggregate_revision,expected_working_revision,expected_attachment_revision)):
                raise self._conflict(conn, record, expected_aggregate_revision, expected_working_revision)
            reviewrow = conn.execute(
                "SELECT rr.*,ri.state,ri.frozen_attachment_sha256,ar.payload_json "
                "FROM refinement_review_results rr JOIN refinement_invocations ri ON ri.id=rr.invocation_id "
                "JOIN ask_results ar ON ar.projection_stage_id=rr.ask_result_stage_id "
                "WHERE rr.id=? AND ri.thought_id=?", (review_result_id, thought_id)
            ).fetchone()
            if reviewrow is None or str(reviewrow["state"]) != "review_ready":
                raise ConflictError("review is no longer current", code="refinement_review_superseded")
            review = self._review_card(str(reviewrow["payload_json"]))
            if review["kind"] != "question":
                raise ValidationError("review is not a question", code="refinement_review_kind_invalid")
            if (int(reviewrow["frozen_aggregate_revision"]),int(reviewrow["frozen_working_revision"]),
                    int(reviewrow["frozen_attachment_revision"])) != (
                    expected_aggregate_revision,expected_working_revision,expected_attachment_revision):
                raise ConflictError("review was based on an older working note", code="refinement_review_superseded")
            from .refinement_context_service import RefinementContextService
            RefinementContextService(self._db).validate_frozen_in_transaction(
                conn, thought_id, expected_attachment_revision,
                str(reviewrow["frozen_attachment_sha256"]),
            )
            lease_now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
            host = conn.execute("SELECT host_kind,lease_epoch,expires_at FROM refinement_hosts WHERE host_id=?", (dispatch_host_id,)).fetchone()
            if host is None or int(host["lease_epoch"]) != int(dispatch_lease_epoch) or str(host["expires_at"]) <= lease_now:
                raise ConflictError("the next turn is unavailable", code="refinement_continuation_unavailable")
            admission_json, admission_sha = self._validated_admission_claim(admission_claim, required=True)
            if validate_current_admission:
                self._validate_current_admission_under_write_fence(conn, admission_claim)
            note = conn.execute("SELECT * FROM notes WHERE id=?", (record["working_note_id"],)).fetchone()
            if note is None or note["deleted"]: raise ConflictError("working thought was deleted", code="thought_tombstoned")
            prior_body = str(note["body_markdown"]); separator = "\n\n" if prior_body else ""
            block = "## Clarification\nQuestion: " + str(review["question"]) + "\nAnswer: " + answer
            appended = separator + block; body = prior_body + appended
            title, tags = str(note["title"]), json.loads(note["tags_json"])
            now = _now(); next_agg = expected_aggregate_revision + 1; next_work = expected_working_revision + 1
            cur = conn.execute("UPDATE refinement_thoughts SET aggregate_revision=?,working_revision=?,resume_order=?,updated_at=? "
                               "WHERE id=? AND aggregate_revision=? AND working_revision=? AND attachment_revision=? AND state='working'",
                               (next_agg,next_work,RefinementThoughtRepository.next_resume_order(conn),now,thought_id,
                                expected_aggregate_revision,expected_working_revision,expected_attachment_revision))
            if not cur.rowcount: raise self._conflict(conn, record, expected_aggregate_revision, expected_working_revision)
            self._db.notes._upsert_in_transaction(conn, note_id=record["working_note_id"], title=title,
                                                  body_markdown=body, tags=tags, now=now)
            working_hash = self._insert_revision(conn, thought_id, next_work, title, body, tags, now)
            updated = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            RefinementThoughtRepository.insert_command(conn, updated, command_kind="replace_working",
                prior_working_revision=expected_working_revision, prior_lifecycle_revision=record["lifecycle_revision"],
                prior_attachment_revision=expected_attachment_revision, working_sha256=working_hash,
                lifecycle_sha256=None, accepted_at=now)
            action_id = _id("ract")
            cur = conn.execute("UPDATE refinement_invocations SET state='superseded',terminal_code='owner_answered',updated_at=?,terminal_at=? "
                               "WHERE review_result_id=? AND state='review_ready'", (now,now,review_result_id))
            if not cur.rowcount: raise ConflictError("review is no longer current", code="refinement_review_superseded")
            child_id, ask_id = _id("rinv"), _id("ask")
            child_request_id = "next_" + hashlib.sha256(command_id.encode()).hexdigest()[:24]
            child_semantic = {"request_id":child_request_id,"thought_id":thought_id,
                              "frozen_aggregate_revision":next_agg,"frozen_working_revision":next_work,
                              "frozen_attachment_revision":expected_attachment_revision,"purpose":"refinement_after_answer"}
            child_digest = hashlib.sha256(canonical_json(child_semantic)).hexdigest()
            attachment_hash = str(updated.get("attachment_sha256") or RefinementThoughtRepository.empty_attachment_hash(thought_id))
            conn.execute("INSERT INTO refinement_invocations(id,request_id,request_sha256,thought_id,frozen_aggregate_revision,frozen_working_revision,frozen_attachment_revision,frozen_attachment_sha256,admission_json,admission_sha256,state,dispatch_host_id,dispatch_lease_epoch,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,'reserved',?,?,?,?)",
                         (child_id,child_request_id,child_digest,thought_id,next_agg,next_work,expected_attachment_revision,
                          attachment_hash,admission_json,admission_sha,dispatch_host_id,dispatch_lease_epoch,now,now))
            conn.execute("INSERT INTO refinement_invocation_attempts(invocation_id,attempt_ordinal,ask_invocation_id,state,created_at) VALUES(?,1,?,'reserved',?)",
                         (child_id,ask_id,now))
            if routed_admission is not None:
                admitted = dict(routed_admission(conn, child_id, ask_id, body))
                conn.execute(
                    "UPDATE refinement_invocations SET route_plan_id=?,operation_plan_id=?,route_execution_id=? WHERE id=?",
                    (admitted["route_plan"]["id"], admitted["operation_request_plan"]["id"],
                     admitted["execution"]["id"], child_id),
                )
            continuity = self._bump_continuity(conn, thought_id)
            post_cursor = {"hub_id":self._workspace_hub_id(conn),"thought_id":thought_id,
                           "aggregate_revision":next_agg,"continuity_revision":continuity}
            start = len(prior_body.encode("utf-8")); append_bytes = appended.encode("utf-8")
            effect = {"kind":"clarification_appended","thought_id":thought_id,"working_revision":next_work,
                      "prior_body_sha256":hashlib.sha256(prior_body.encode()).hexdigest(),
                      "body_sha256":hashlib.sha256(body.encode()).hexdigest(),"append_utf8_start":start,
                      "append_utf8_end":start+len(append_bytes),"append_sha256":hashlib.sha256(append_bytes).hexdigest(),
                      "committed_post_cursor":post_cursor}
            effect_json = canonical_json(effect).decode()
            effect_sha = hashlib.sha256(effect_json.encode()).hexdigest()
            conn.execute("INSERT INTO refinement_review_actions(action_id,request_id,request_sha256,thought_id,review_result_id,action_kind,aggregate_revision,working_revision,lifecycle_revision,attachment_revision,post_aggregate_revision,post_working_revision,post_lifecycle_revision,post_continuity_revision,committed_hub_id,append_effect_json,append_effect_sha256,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (action_id,command_id,digest,thought_id,review_result_id,"answer",expected_aggregate_revision,
                          expected_working_revision,record["lifecycle_revision"],expected_attachment_revision,
                          next_agg,next_work,record["lifecycle_revision"],continuity,post_cursor["hub_id"],effect_json,effect_sha,now))
            conn.execute("INSERT INTO refinement_answer_continue_commands(command_id,request_sha256,thought_id,review_result_id,action_id,child_invocation_id,append_effect_json,post_aggregate_revision,post_working_revision,post_continuity_revision,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                         (command_id,digest,thought_id,review_result_id,action_id,child_id,
                          effect_json,next_agg,next_work,continuity,now))
            current = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            receipt = {"id":command_id,"kind":"answer_and_continue","effect":effect,"child_invocation_id":child_id}
            invocation = self._invocation_dto(conn, dict(conn.execute("SELECT * FROM refinement_invocations WHERE id=?", (child_id,)).fetchone()))
            return self._dto_in_transaction(conn, current), receipt, invocation, True

    def _validate_workspace_cursor_in_transaction(self, conn: Any, record: dict[str, Any],
                                                  cursor: dict[str, Any] | None,
                                                  *, required: bool = False,
                                                  relaxed: bool = False) -> None:
        if cursor is None and not required: return
        keys = {"hub_id","thought_id","aggregate_revision","continuity_revision"}
        if (not isinstance(cursor, dict) or set(cursor) != keys
                or cursor.get("hub_id") != self._workspace_hub_id(conn)
                or cursor.get("thought_id") != record["id"]
                or not isinstance(cursor.get("aggregate_revision"), int)
                or not isinstance(cursor.get("continuity_revision"), int)
                or cursor["aggregate_revision"] != int(record["aggregate_revision"])
                or (cursor["continuity_revision"] != int(record.get("continuity_revision") or 0)
                    if not relaxed else not (0 <= cursor["continuity_revision"] <= int(record.get("continuity_revision") or 0)))):
            raise ConflictError("workspace changed elsewhere", code="workspace_cursor_conflict")

    @staticmethod
    def _validated_admission_claim(claim: dict[str, Any] | None, *, required: bool) -> tuple[str, str]:
        if claim is None and not required: return "{}", ""
        keys = {"target_id","target_kind","boundary","engine","model","readiness","reason"}
        if (not isinstance(claim, dict) or set(claim) != keys
                or any(not isinstance(claim.get(key), str) for key in keys)
                or claim.get("readiness") != "ready"
                or any(len(str(value).encode("utf-8")) > 500 for value in claim.values())):
            raise ConflictError("the next turn is unavailable", code="refinement_continuation_unavailable")
        raw = canonical_json(claim)
        return raw.decode("utf-8"), hashlib.sha256(raw).hexdigest()

    def _validate_current_admission_under_write_fence(self, conn: Any, claim: dict[str, Any] | None) -> None:
        """Re-observe admission while the caller holds SQLite's write fence.

        The caller has already entered BEGIN IMMEDIATE, so settings cannot race
        between this observation and persistence of the immutable claim.
        """
        from ..inference_targets import resolve_thought_placement
        if not isinstance(claim, dict):
            raise ConflictError("the next turn is unavailable", code="refinement_continuation_unavailable")
        routed = conn.execute(
            "SELECT 1 FROM inference_assignment_migrations WHERE family='thoughts-writing-route-assignments'"
        ).fetchone() is not None
        if routed:
            from ..inference_capabilities import process_inference_capability_registry
            from .inference_route_plan_service import InferenceRoutePlanService

            plans = InferenceRoutePlanService(self._db)
            capability = process_inference_capability_registry().require("thought.interview")
            route, _revisions, _preflight = plans._resolve_in_conn(
                conn,
                capability=capability,
                operation_policy_revision=plans._operation_policy(capability, None),
                invocation_id=None,
                subject_kind=None,
                subject_id=None,
                plan_id="refinement-admission-check",
            )
            primary = route["entries"][0]
            current = {
                "target_id": str(primary["profile_id"]),
                "target_kind": "assigned_profile",
                "boundary": str(primary["boundary"]),
                "engine": "",
                "model": "",
                "readiness": "ready",
                "reason": "",
            }
            if current != claim:
                raise ConflictError(
                    "Couldn't start the next turn. Your answer is still here. Add it to the Note.",
                    code="refinement_continuation_unavailable",
                    context={"readiness":"unavailable","reason":"assignment_changed"},
                )
            return
        # This fence is used only for coordinator-owned default selection.
        # Re-run that selector itself: resolving the already-claimed id would
        # miss an A→B default change and make the comparison decorative.
        target = resolve_thought_placement(self._db).target
        current = {"target_id":target.id,"target_kind":target.kind,"boundary":target.boundary,
                   "engine":target.engine,"model":target.model,"readiness":target.readiness_state,
                   "reason":target.readiness_reason}
        if current != claim or current["readiness"] != "ready":
            raise ConflictError(
                "Couldn't start the next turn. Your answer is still here. Add it to the Note.",
                code="refinement_continuation_unavailable",
                context={"readiness":current["readiness"],"reason":current["reason"]},
            )

    def heartbeat_refinement_host(self, host_id: str, lease_epoch: int, *, lease_seconds: float) -> bool:
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat(timespec="microseconds").replace("+00:00", "Z")
        expires = (now_dt + timedelta(seconds=lease_seconds)).isoformat(timespec="microseconds").replace("+00:00", "Z")
        with self._db._connection() as conn:
            cur = conn.execute(
                "UPDATE refinement_hosts SET heartbeat_at=?,expires_at=? WHERE host_id=? AND lease_epoch=?",
                (now, expires, host_id, lease_epoch),
            )
            return bool(cur.rowcount)

    def release_refinement_host(self, host_id: str, lease_epoch: int) -> None:
        now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        with self._db._connection() as conn:
            conn.execute(
                "UPDATE refinement_hosts SET expires_at=? WHERE host_id=? AND lease_epoch=?",
                (now, host_id, lease_epoch),
            )

    def pending_host_cancellations(self, host_id: str, lease_epoch: int) -> list[dict[str, str]]:
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT ri.id,ria.ask_invocation_id FROM refinement_invocations ri "
                "JOIN refinement_invocation_attempts ria ON ria.invocation_id=ri.id "
                "WHERE ri.dispatch_host_id=? AND ri.dispatch_lease_epoch=? "
                "AND ri.cancel_requested_at IS NOT NULL AND ri.cancel_observed_at IS NULL "
                "ORDER BY ria.attempt_ordinal DESC",
                (host_id, lease_epoch),
            ).fetchall()
            seen: set[str] = set()
            result = []
            for row in rows:
                invocation_id = str(row["id"])
                if invocation_id in seen: continue
                seen.add(invocation_id)
                result.append({"invocation_id":invocation_id,"ask_invocation_id":str(row["ask_invocation_id"])})
            return result

    def observe_host_cancellation(self, host_id: str, lease_epoch: int, invocation_id: str, disposition: str) -> None:
        with self._db._connection() as conn:
            inv = conn.execute("SELECT thought_id FROM refinement_invocations WHERE id=?", (invocation_id,)).fetchone()
            cur = conn.execute(
                "UPDATE refinement_invocations SET cancel_observed_at=?,cancel_disposition=? "
                "WHERE id=? AND dispatch_host_id=? AND dispatch_lease_epoch=? "
                "AND cancel_requested_at IS NOT NULL AND cancel_observed_at IS NULL",
                (_now(), disposition, invocation_id, host_id, lease_epoch),
            )
            if cur.rowcount and inv: self._bump_continuity(conn, str(inv["thought_id"]))

    def terminalize_reserved(self, principal: Principal, invocation_id: str, *, code: str) -> dict[str, Any]:
        """Coordinator-only named pre-admission terminalization; no kernel row."""
        self._require_owner(principal)
        code = _closed_terminal_code(str(code))
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            inv = conn.execute("SELECT * FROM refinement_invocations WHERE id=?", (invocation_id,)).fetchone()
            if inv is None: raise NotFound("refinement invocation", invocation_id)
            if str(inv["state"]) != "reserved": return self._invocation_dto(conn, dict(inv))
            now = _now()
            conn.execute("UPDATE refinement_invocation_attempts SET state='refused',terminal_code=?,terminal_at=? WHERE invocation_id=? AND attempt_ordinal=1 AND state='reserved'", (code, now, invocation_id))
            conn.execute("UPDATE refinement_invocations SET state='refused',terminal_code=?,updated_at=?,terminal_at=? WHERE id=? AND state='reserved'", (code, now, now, invocation_id))
            self._bump_continuity(conn, str(inv["thought_id"]))
            return self._invocation_dto(conn, dict(conn.execute("SELECT * FROM refinement_invocations WHERE id=?", (invocation_id,)).fetchone()))

    def recover_refinements_on_startup(
        self,
        *,
        recovery_host_id: str | None = None,
        recovery_lease_epoch: int | None = None,
    ) -> list[str]:
        """Reconcile abandoned app tasks without ever dispatching them again.

        Kernel recovery/projection reaping runs before this method.  A logical
        invocation with no native operation was never admitted and gets the
        exact pre-dispatch shutdown outcome.  Anything with kernel identity is
        reconciled from receipts only; a bound operation with no terminal proof
        is indeterminate after process loss.
        """
        recovered: list[str] = []
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            lease_now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
            rows = conn.execute(
                "SELECT * FROM refinement_invocations "
                "WHERE state IN ('reserved','in_flight','awaiting_projection') "
                "ORDER BY created_at,id"
            ).fetchall()
            for raw in rows:
                inv = dict(raw)
                invocation_id = str(inv["id"])
                if inv.get("dispatch_host_id"):
                    host = conn.execute(
                        "SELECT lease_epoch,expires_at FROM refinement_hosts WHERE host_id=?",
                        (inv["dispatch_host_id"],),
                    ).fetchone()
                    if host is not None and int(host["lease_epoch"]) == int(inv.get("dispatch_lease_epoch") or 0) and str(host["expires_at"]) > lease_now:
                        # Another first-class host still owns execution. Missing
                        # kernel proof is not abandonment while that lease lives.
                        continue
                attempts = conn.execute(
                    "SELECT * FROM refinement_invocation_attempts "
                    "WHERE invocation_id=? ORDER BY attempt_ordinal",
                    (invocation_id,),
                ).fetchall()
                if inv.get("route_execution_id"):
                    route_execution = conn.execute(
                        "SELECT state FROM inference_route_executions WHERE id=?",
                        (str(inv["route_execution_id"]),),
                    ).fetchone()
                    if route_execution is not None and str(route_execution["state"]) in {"active", "stopping"}:
                        # Exact material/route/controller admission survived;
                        # atomically transfer its dispatch lease before the
                        # replacement coordinator resumes this identity.
                        if recovery_host_id and recovery_lease_epoch:
                            conn.execute(
                                """UPDATE refinement_invocations
                                      SET dispatch_host_id=?,dispatch_lease_epoch=?,updated_at=?
                                    WHERE id=?""",
                                (
                                    recovery_host_id,
                                    int(recovery_lease_epoch),
                                    _now(),
                                    invocation_id,
                                ),
                            )
                        recovered.append(invocation_id)
                        continue
                bound = False
                for attempt in attempts:
                    if attempt["kernel_operation_id"]:
                        bound = True
                        break
                    native = conn.execute(
                        "SELECT 1 FROM kernel_operations WHERE native_id=?",
                        (attempt["ask_invocation_id"],),
                    ).fetchone()
                    if native is not None:
                        bound = True
                        break
                now = _now()
                if not bound:
                    conn.execute(
                        "UPDATE refinement_invocation_attempts SET "
                        "state='refused',terminal_code='shutdown_before_dispatch',terminal_at=? "
                        "WHERE invocation_id=? AND state='reserved'",
                        (now, invocation_id),
                    )
                    conn.execute(
                        "UPDATE refinement_invocations SET "
                        "state='refused',terminal_code='shutdown_before_dispatch',updated_at=?,terminal_at=? "
                        "WHERE id=?",
                        (now, now, invocation_id),
                    )
                    recovered.append(invocation_id)
                    continue
                thought = conn.execute(
                    "SELECT * FROM refinement_thoughts WHERE id=?",
                    (inv["thought_id"],),
                ).fetchone()
                if thought is None:
                    conn.execute(
                        "UPDATE refinement_invocations SET state='unknown',"
                        "terminal_code='thought_missing_during_recovery',updated_at=?,terminal_at=? "
                        "WHERE id=?",
                        (now, now, invocation_id),
                    )
                    recovered.append(invocation_id)
                    continue
                self._reconcile_invocation_in_transaction(
                    conn, inv, self._record(thought)
                )
                fresh = conn.execute(
                    "SELECT state FROM refinement_invocations WHERE id=?",
                    (invocation_id,),
                ).fetchone()
                if fresh and str(fresh["state"]) in {"reserved", "in_flight"}:
                    conn.execute(
                        "UPDATE refinement_invocation_attempts SET "
                        "state='indeterminate',terminal_code='restart_bound_outcome_unknown',terminal_at=? "
                        "WHERE invocation_id=? AND kernel_operation_id IS NOT NULL "
                        "AND state IN ('reserved','in_flight')",
                        (now, invocation_id),
                    )
                    conn.execute(
                        "UPDATE refinement_invocations SET state='indeterminate',"
                        "terminal_code='restart_bound_outcome_unknown',updated_at=?,terminal_at=? "
                        "WHERE id=?",
                        (now, now, invocation_id),
                    )
                recovered.append(invocation_id)
            recovered_thoughts = {
                str(row["thought_id"]) for invocation_id in recovered
                for row in conn.execute("SELECT thought_id FROM refinement_invocations WHERE id=?", (invocation_id,)).fetchall()
            }
            for recovered_thought_id in recovered_thoughts:
                self._bump_continuity(conn, recovered_thought_id)
        return recovered

    def settle_coordinator_failure(
        self,
        principal: Principal,
        thought_id: str,
        invocation_id: str,
        *,
        code: str,
    ) -> dict[str, Any]:
        """Reconcile kernel proof, then name a bound proof gap honestly."""
        self._require_owner(principal)
        code = _closed_terminal_code(str(code))
        thought = self.get(principal, thought_id)
        result = self.reconcile(
            principal,
            thought_id,
            expected_aggregate_revision=thought["aggregate_revision"],
            invocation_id=invocation_id,
        )
        if result["continuity"]["state"] not in {
            "reserved",
            "in_flight",
            "awaiting_projection",
        }:
            return result
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            inv = conn.execute(
                "SELECT state FROM refinement_invocations WHERE id=? AND thought_id=?",
                (invocation_id, thought_id),
            ).fetchone()
            bound = conn.execute(
                "SELECT 1 FROM refinement_invocation_attempts "
                "WHERE invocation_id=? AND kernel_operation_id IS NOT NULL LIMIT 1",
                (invocation_id,),
            ).fetchone()
            if inv and bound and str(inv["state"]) in {
                "reserved",
                "in_flight",
                "awaiting_projection",
            }:
                now = _now()
                conn.execute(
                    "UPDATE refinement_invocation_attempts SET state='indeterminate',"
                    "terminal_code=?,terminal_at=? WHERE invocation_id=? "
                    "AND state IN ('reserved','in_flight')",
                    (code, now, invocation_id),
                )
                conn.execute(
                    "UPDATE refinement_invocations SET state='indeterminate',"
                    "terminal_code=?,updated_at=?,terminal_at=? WHERE id=?",
                    (code, now, now, invocation_id),
                )
                self._bump_continuity(conn, thought_id)
                current = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
                return self._dto_in_transaction(conn, current)
        return result

    def stop_refinement(self, principal: Principal, thought_id: str, *, invocation_id: str, expected_aggregate_revision: int) -> tuple[dict[str, Any], str | None]:
        thought, target = self.stop_refinement_with_owner(
            principal, thought_id, invocation_id=invocation_id,
            expected_aggregate_revision=expected_aggregate_revision,
        )
        return thought, target.get("ask_invocation_id")

    def stop_refinement_with_owner(self, principal: Principal, thought_id: str, *, invocation_id: str,
                                   expected_aggregate_revision: int,
                                   workspace_cursor: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        self._require_owner(principal)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            thought = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            inv = conn.execute("SELECT * FROM refinement_invocations WHERE id=? AND thought_id=?", (invocation_id, thought_id)).fetchone()
            if thought is None: raise NotFound("thought", thought_id)
            record = self._record(thought)
            self._validate_workspace_cursor_in_transaction(conn, record, workspace_cursor, relaxed=True)
            if int(record["aggregate_revision"]) != expected_aggregate_revision: raise self._conflict(conn, record, expected_aggregate_revision, None)
            if inv is None: raise NotFound("refinement invocation", invocation_id)
            ask = conn.execute("SELECT ask_invocation_id FROM refinement_invocation_attempts WHERE invocation_id=? ORDER BY attempt_ordinal DESC LIMIT 1", (invocation_id,)).fetchone()
            changed = str(inv["state"]) in {"reserved","in_flight","awaiting_projection","review_ready"}
            if changed:
                now, code = _now(), "owner_stopped" if str(inv["state"]) == "reserved" else "owner_stopped_after_dispatch"
                conn.execute("UPDATE refinement_invocation_attempts SET state='cancelled',terminal_code=?,terminal_at=? WHERE invocation_id=? AND state IN ('reserved','in_flight')", (code, now, invocation_id))
                conn.execute("UPDATE refinement_invocations SET state='cancelled',terminal_code=?,cancel_requested_at=COALESCE(cancel_requested_at,?),updated_at=?,terminal_at=? WHERE id=? AND state IN ('reserved','in_flight','awaiting_projection','review_ready')", (code, now, now, now, invocation_id))
                self._bump_continuity(conn, thought_id)
            host = conn.execute(
                "SELECT lease_epoch,expires_at FROM refinement_hosts WHERE host_id=?",
                (inv["dispatch_host_id"],),
            ).fetchone() if inv["dispatch_host_id"] else None
            lease_now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
            live = bool(host and int(host["lease_epoch"]) == int(inv["dispatch_lease_epoch"] or 0) and str(host["expires_at"]) > lease_now)
            target = {
                "ask_invocation_id": str(ask["ask_invocation_id"]) if ask else None,
                "route_execution_id": str(inv["route_execution_id"] or "") or None,
                "dispatch_host_id": str(inv["dispatch_host_id"] or ""),
                "dispatch_lease_epoch": int(inv["dispatch_lease_epoch"] or 0),
                "host_live": live,
            }
            return self._dto_in_transaction(conn, record), target

    def review(self, principal: Principal, thought_id: str, review_result_id: str) -> dict[str, Any]:
        self._require_owner(principal)
        with self._db._connection() as conn:
            row = conn.execute("SELECT rr.*,ri.thought_id,ri.state,ar.payload_json FROM refinement_review_results rr JOIN refinement_invocations ri ON ri.id=rr.invocation_id JOIN ask_results ar ON ar.projection_stage_id=rr.ask_result_stage_id WHERE rr.id=? AND ri.thought_id=?", (review_result_id, thought_id)).fetchone()
            if row is None: raise NotFound("refinement review", review_result_id)
            if str(row["state"]) != "review_ready": raise ConflictError("review is no longer current", code="refinement_review_superseded")
            card = self._review_card(str(row["payload_json"]))
            provenance = self._review_provenance(str(row["payload_json"]))
            from .refinement_context_service import RefinementContextService
            used = RefinementContextService(self._db).used_context_in_transaction(
                conn, thought_id, int(row["frozen_attachment_revision"])
            )
            if used is not None: provenance["used_context"] = used
            return {"review":{"id":review_result_id, **card, **provenance,"frozen_aggregate_revision":row["frozen_aggregate_revision"],"frozen_working_revision":row["frozen_working_revision"],"frozen_attachment_revision":row["frozen_attachment_revision"]}}

    def review_action(self, principal: Principal, thought_id: str, review_result_id: str, *, request_id: str, action: str,
                      expected_aggregate_revision: int, expected_working_revision: int,
                      expected_attachment_revision: int, answer: str = "",
                      workspace_cursor: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        self._require_owner(principal)
        if action not in {"answer","accept","reject"}: raise ValidationError("invalid review action")
        if action == "answer" and len(answer) > 12000:
            raise ValidationError("answer is too long", code="refinement_answer_too_long")
        digest = hashlib.sha256(canonical_json({"request_id":request_id,"thought_id":thought_id,"review_result_id":review_result_id,"action":action,"aggregate":expected_aggregate_revision,"working":expected_working_revision,"attachment":expected_attachment_revision,"answer_sha256":hashlib.sha256(answer.encode()).hexdigest() if action == "answer" else ""})).hexdigest()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute("SELECT * FROM refinement_review_actions WHERE request_id=?", (request_id,)).fetchone()
            thoughtrow = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if thoughtrow is None: raise NotFound("thought", thought_id)
            record = self._record(thoughtrow)
            if prior is not None:
                if str(prior["request_sha256"]) != digest: raise ConflictError("review action request changed", code="refinement_review_action_payload_mismatch")
                if (int(record["aggregate_revision"]),int(record["working_revision"]),int(record["lifecycle_revision"])) == (int(prior["post_aggregate_revision"]),int(prior["post_working_revision"]),int(prior["post_lifecycle_revision"])):
                    receipt = {"id":str(prior["action_id"]),"kind":str(prior["action_kind"])}
                    if str(prior["action_kind"]) == "answer":
                        receipt["effect"] = self._validated_append_effect(conn, prior)
                    if workspace_cursor is not None:
                        if not str(prior["committed_hub_id"] or ""):
                            raise ConflictError("review action proof is incomplete", code="refinement_review_action_integrity")
                        receipt["committed_post_cursor"] = {"hub_id":str(prior["committed_hub_id"]),"thought_id":thought_id,
                            "aggregate_revision":int(prior["post_aggregate_revision"]),
                            "continuity_revision":int(prior["post_continuity_revision"])}
                    return self._dto_in_transaction(conn, record), receipt
                raise ConflictError("review action was superseded", code="refinement_review_action_superseded", context={"current":self._dto_in_transaction(conn,record)})
            self._validate_workspace_cursor_in_transaction(conn, record, workspace_cursor)
            reviewrow = conn.execute("SELECT rr.*,ri.state,ri.frozen_attachment_sha256,ar.payload_json FROM refinement_review_results rr JOIN refinement_invocations ri ON ri.id=rr.invocation_id JOIN ask_results ar ON ar.projection_stage_id=rr.ask_result_stage_id WHERE rr.id=? AND ri.thought_id=?", (review_result_id, thought_id)).fetchone()
            if reviewrow is None or str(reviewrow["state"]) != "review_ready": raise ConflictError("review is no longer current", code="refinement_review_superseded")
            review = self._review_card(str(reviewrow["payload_json"]))
            if (int(record["aggregate_revision"]),int(record["working_revision"]),int(record["attachment_revision"])) != (expected_aggregate_revision,expected_working_revision,expected_attachment_revision): raise self._conflict(conn,record,expected_aggregate_revision,expected_working_revision)
            if (int(reviewrow["frozen_aggregate_revision"]), int(reviewrow["frozen_working_revision"]), int(reviewrow["frozen_attachment_revision"])) != (expected_aggregate_revision, expected_working_revision, expected_attachment_revision):
                raise ConflictError("review was based on an older working note", code="refinement_review_superseded", context={"current": self._dto_in_transaction(conn, record)})
            if action == "answer" and review["kind"] != "question": raise ValidationError("review is not a question", code="refinement_review_kind_invalid")
            if action == "accept" and review["kind"] != "synthesis": raise ValidationError("review is not a synthesis", code="refinement_review_kind_invalid")
            if action in {"answer", "accept"}:
                from .refinement_context_service import RefinementContextService
                RefinementContextService(self._db).validate_frozen_in_transaction(
                    conn, thought_id, expected_attachment_revision,
                    str(reviewrow["frozen_attachment_sha256"]),
                )
            now = _now(); aid = _id("ract")
            cur = conn.execute("UPDATE refinement_invocations SET state='superseded',terminal_code=?,updated_at=?,terminal_at=? WHERE review_result_id=? AND state='review_ready'", ("owner_"+action+"ed",now,now,review_result_id))
            if not cur.rowcount: raise ConflictError("review is no longer current", code="refinement_review_superseded")
            updated = record
            effect: dict[str, Any] | None = None
            if action != "reject":
                note = conn.execute("SELECT * FROM notes WHERE id=?", (record["working_note_id"],)).fetchone()
                title, body, tags = str(note["title"]), str(note["body_markdown"]), json.loads(note["tags_json"])
                if action == "answer":
                    prior_body = body
                    appended = ("\n\n" if body else "") + "## Clarification\nQuestion: " + review["question"] + "\nAnswer: " + answer
                    body += appended
                else: title, body, tags = review["title"], review["body_markdown"], review["tags"]
                conn.execute("UPDATE refinement_thoughts SET aggregate_revision=?,working_revision=?,updated_at=? WHERE id=?", (expected_aggregate_revision+1,expected_working_revision+1,now,thought_id))
                self._db.notes._upsert_in_transaction(conn,note_id=record["working_note_id"],title=title,body_markdown=body,tags=tags,now=now)
                wh=self._insert_revision(conn,thought_id,expected_working_revision+1,title,body,tags,now); updated=self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?",(thought_id,)).fetchone()); RefinementThoughtRepository.insert_command(conn,updated,command_kind="replace_working",prior_working_revision=expected_working_revision,prior_lifecycle_revision=record["lifecycle_revision"],prior_attachment_revision=record["attachment_revision"],working_sha256=wh,lifecycle_sha256=None,accepted_at=now)
            post_continuity = self._bump_continuity(conn, thought_id)
            if action == "answer":
                append_bytes = appended.encode("utf-8")
                effect = {"kind":"clarification_appended","thought_id":thought_id,
                          "working_revision":int(updated["working_revision"]),
                          "prior_body_sha256":hashlib.sha256(prior_body.encode()).hexdigest(),
                          "body_sha256":hashlib.sha256(body.encode()).hexdigest(),
                          "append_utf8_start":len(prior_body.encode("utf-8")),
                          "append_utf8_end":len(prior_body.encode("utf-8"))+len(append_bytes),
                          "append_sha256":hashlib.sha256(append_bytes).hexdigest(),
                          "committed_post_cursor":{"hub_id":self._workspace_hub_id(conn),"thought_id":thought_id,
                                                   "aggregate_revision":int(updated["aggregate_revision"]),
                                                   "continuity_revision":post_continuity}}
            effect_json = canonical_json(effect).decode() if effect is not None else ""
            effect_sha = hashlib.sha256(effect_json.encode()).hexdigest() if effect_json else ""
            committed_hub = self._workspace_hub_id(conn) if action == "answer" or workspace_cursor is not None else ""
            conn.execute("INSERT INTO refinement_review_actions(action_id,request_id,request_sha256,thought_id,review_result_id,action_kind,aggregate_revision,working_revision,lifecycle_revision,attachment_revision,post_aggregate_revision,post_working_revision,post_lifecycle_revision,post_continuity_revision,committed_hub_id,append_effect_json,append_effect_sha256,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (aid,request_id,digest,thought_id,review_result_id,action,expected_aggregate_revision,expected_working_revision,record["lifecycle_revision"],expected_attachment_revision,updated["aggregate_revision"],updated["working_revision"],updated["lifecycle_revision"],post_continuity,committed_hub,effect_json,effect_sha,now))
            current = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            receipt = {"id":aid,"kind":action}
            if effect is not None:
                receipt["effect"] = effect
            if workspace_cursor is not None:
                receipt["committed_post_cursor"] = {"hub_id":committed_hub,"thought_id":thought_id,
                    "aggregate_revision":int(updated["aggregate_revision"]),"continuity_revision":post_continuity}
            return self._dto_in_transaction(conn,current), receipt

    def _validated_append_effect(self, conn: Any, action: Any) -> dict[str, Any]:
        raw = str(action["append_effect_json"] or "")
        if not raw or hashlib.sha256(raw.encode()).hexdigest() != str(action["append_effect_sha256"] or ""):
            raise ConflictError("review action proof is incomplete", code="refinement_review_action_integrity")
        try:
            effect = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise ConflictError("review action proof is invalid", code="refinement_review_action_integrity") from exc
        keys = {"kind","thought_id","working_revision","prior_body_sha256","body_sha256",
                "append_utf8_start","append_utf8_end","append_sha256","committed_post_cursor"}
        if not isinstance(effect, dict) or set(effect) != keys or effect.get("kind") != "clarification_appended" \
                or effect.get("thought_id") != str(action["thought_id"]) \
                or effect.get("working_revision") != int(action["post_working_revision"]):
            raise ConflictError("review action proof is invalid", code="refinement_review_action_integrity")
        prior = conn.execute("SELECT body_markdown FROM refinement_working_revisions WHERE thought_id=? AND revision=?",
                             (action["thought_id"], int(action["working_revision"]))).fetchone()
        post = conn.execute("SELECT body_markdown FROM refinement_working_revisions WHERE thought_id=? AND revision=?",
                            (action["thought_id"], int(action["post_working_revision"]))).fetchone()
        if prior is None or post is None:
            raise ConflictError("review action proof is incomplete", code="refinement_review_action_integrity")
        before = str(prior["body_markdown"]).encode("utf-8"); after = str(post["body_markdown"]).encode("utf-8")
        start, end = effect.get("append_utf8_start"), effect.get("append_utf8_end")
        cursor = effect.get("committed_post_cursor")
        if (not isinstance(start, int) or not isinstance(end, int) or start != len(before) or end != len(after)
                or not after.startswith(before) or hashlib.sha256(before).hexdigest() != effect.get("prior_body_sha256")
                or hashlib.sha256(after).hexdigest() != effect.get("body_sha256")
                or hashlib.sha256(after[start:end]).hexdigest() != effect.get("append_sha256")
                or not isinstance(cursor, dict) or set(cursor) != {"hub_id","thought_id","aggregate_revision","continuity_revision"}
                or not isinstance(cursor.get("hub_id"), str) or cursor.get("hub_id") != str(action["committed_hub_id"])
                or not isinstance(cursor.get("thought_id"), str) or cursor.get("thought_id") != str(action["thought_id"])
                or not isinstance(cursor.get("aggregate_revision"), int)
                or not isinstance(cursor.get("continuity_revision"), int)
                or cursor.get("aggregate_revision") != int(action["post_aggregate_revision"])
                or cursor.get("continuity_revision") != int(action["post_continuity_revision"])):
            raise ConflictError("review action proof is invalid", code="refinement_review_action_integrity")
        return effect

    def update_working(self, principal: Principal, thought_id: str, *, expected_aggregate_revision: int | None,
                       expected_working_revision: int | None, title: str | None = None,
                       body_markdown: str | None = None, tags: list[str] | None = None,
                       workspace_cursor: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require_owner(principal)
        if not isinstance(expected_aggregate_revision, int) or not isinstance(expected_working_revision, int):
            raise ConflictError("thought-owned notes require aggregate and working revisions", code="thought_expected_revision_required")
        custody_lost = False
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if row is None: raise NotFound("thought", thought_id)
            record = self._record(row)
            self._validate_workspace_cursor_in_transaction(conn, record, workspace_cursor)
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
                self._supersede_invocations(conn, thought_id, "owner_edited")
                self._bump_continuity(conn, thought_id)
                current = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
                return self._dto_in_transaction(conn, current)
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
                              expected_lifecycle_revision: int | None,
                              workspace_cursor: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
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
                    return self._dto_in_transaction(conn, record), self._completion_receipt(
                        prior, str(prior["committed_hub_id"] or "") if workspace_cursor is not None else None
                    )
                raise ConflictError("completion request was superseded by later work", code="completion_request_superseded",
                    context={"current": self._dto_in_transaction(conn, record)})
            self._validate_workspace_cursor_in_transaction(conn, record, workspace_cursor)
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
            self._supersede_invocations(conn, thought_id, "thought_completed")
            life_hash = RefinementThoughtRepository.insert_lifecycle(conn, thought_id=thought_id, lifecycle_revision=next_life,
                aggregate_revision=next_agg, prior_state="working", state="completed", command="complete", occurred_at=now)
            work = conn.execute("SELECT content_sha256 FROM refinement_working_revisions WHERE thought_id=? AND revision=?", (thought_id, record["working_revision"])).fetchone()
            RefinementThoughtRepository.insert_command(conn, updated, command_kind="complete", prior_working_revision=record["working_revision"],
                prior_lifecycle_revision=expected_lifecycle_revision, prior_attachment_revision=record["attachment_revision"],
                working_sha256=str(work["content_sha256"]), lifecycle_sha256=life_hash, accepted_at=now)
            receipt_id = _id("rcomp")
            post_continuity = self._bump_continuity(conn, thought_id)
            committed_hub = self._workspace_hub_id(conn) if workspace_cursor is not None else ""
            conn.execute("INSERT INTO refinement_completion_receipts(receipt_id,thought_id,request_id,request_sha256,aggregate_revision,lifecycle_revision,continuity_revision,committed_hub_id,working_note_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (receipt_id, thought_id, request_id, digest, next_agg, next_life, post_continuity, committed_hub, record["working_note_id"], now))
            receipt = {"receipt_id": receipt_id, "thought_id": thought_id, "aggregate_revision": next_agg,
                "lifecycle_revision": next_life, "continuity_revision": post_continuity, "committed_hub_id":committed_hub,
                "working_note_id": record["working_note_id"], "created_at": now}
            current = self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            return self._dto_in_transaction(conn, current), self._completion_receipt(
                receipt, committed_hub if workspace_cursor is not None else None
            )

    @staticmethod
    def _completion_receipt(row: Any, hub_id: str | None = None) -> dict[str, Any]:
        receipt = {"id": str(row["receipt_id"]), "kind": "thought_completed", "thought_id": str(row["thought_id"]),
            "note_ref": f"note:{row['working_note_id']}", "aggregate_revision": int(row["aggregate_revision"]),
            "lifecycle_revision": int(row["lifecycle_revision"]), "created_at": str(row["created_at"])}
        if hub_id:
            receipt["committed_post_cursor"] = {"hub_id":hub_id,"thought_id":str(row["thought_id"]),
                "aggregate_revision":int(row["aggregate_revision"]),
                "continuity_revision":int(row["continuity_revision"])}
        return receipt

    def resume(self, principal: Principal, thought_id: str, *, expected_aggregate_revision: int | None,
               expected_lifecycle_revision: int | None,
               workspace_cursor: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._transition(principal,thought_id,expected_aggregate_revision=expected_aggregate_revision,
            expected_lifecycle_revision=expected_lifecycle_revision,command="resume",state="working",
            workspace_cursor=workspace_cursor)

    def _transition(self, principal: Principal, thought_id: str, *, expected_aggregate_revision: int | None,
                    expected_lifecycle_revision: int | None, command: str, state: str,
                    workspace_cursor: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require_owner(principal)
        if not isinstance(expected_aggregate_revision,int) or not isinstance(expected_lifecycle_revision,int):
            raise ConflictError("thought transitions require aggregate and lifecycle revisions", code="thought_expected_revision_required")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row=conn.execute("SELECT * FROM refinement_thoughts WHERE id=?",(thought_id,)).fetchone()
            if row is None: raise NotFound("thought",thought_id)
            record=self._record(row)
            self._validate_workspace_cursor_in_transaction(conn, record, workspace_cursor)
            allowed=(command=="complete" and record["state"]=="working") or (command=="resume" and record["state"]=="completed")
            if not allowed or record["aggregate_revision"]!=expected_aggregate_revision or record["lifecycle_revision"]!=expected_lifecycle_revision:
                raise self._conflict(conn,record,expected_aggregate_revision,None,code="thought_revision_conflict")
            now,next_life,next_agg=_now(),expected_lifecycle_revision+1,expected_aggregate_revision+1
            cur=conn.execute("UPDATE refinement_thoughts SET state=?,lifecycle_revision=?,aggregate_revision=?,resume_order=?,completed_at=?,updated_at=? WHERE id=? AND aggregate_revision=? AND lifecycle_revision=? AND state=?",
                (state,next_life,next_agg,RefinementThoughtRepository.next_resume_order(conn),now if state=="completed" else None,now,thought_id,expected_aggregate_revision,expected_lifecycle_revision,record["state"]))
            if not cur.rowcount: raise self._conflict(conn,self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?",(thought_id,)).fetchone()),expected_aggregate_revision,None)
            updated=self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?",(thought_id,)).fetchone())
            if state == "completed": self._supersede_invocations(conn, thought_id, "thought_completed")
            life_hash=RefinementThoughtRepository.insert_lifecycle(conn,thought_id=thought_id,lifecycle_revision=next_life,aggregate_revision=next_agg,prior_state=record["state"],state=state,command=command,occurred_at=now)
            work=conn.execute("SELECT content_sha256 FROM refinement_working_revisions WHERE thought_id=? AND revision=?",(thought_id,record["working_revision"])).fetchone()
            RefinementThoughtRepository.insert_command(conn,updated,command_kind=command,prior_working_revision=record["working_revision"],prior_lifecycle_revision=expected_lifecycle_revision,prior_attachment_revision=record["attachment_revision"],working_sha256=str(work["content_sha256"]),lifecycle_sha256=life_hash,accepted_at=now)
            self._bump_continuity(conn, thought_id)
            current=self._record(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?",(thought_id,)).fetchone())
            return self._dto_in_transaction(conn,current)

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
            conn.execute("""INSERT INTO refinement_thoughts (id,create_request_id,create_payload_sha256,raw_utf8,raw_sha256,raw_source_kind,raw_source_ref,raw_captured_at,working_note_id,working_revision,lifecycle_revision,attachment_revision,attachment_sha256,aggregate_revision,resume_order,state,created_at,updated_at,completed_at,tombstoned_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (thought_id,str(value["create_request_id"]),str(value["create_payload_sha256"]),raw_utf8,str(value["raw_sha256"]),str(source["kind"]),source.get("ref"),str(value["raw_captured_at"]),note_id,int(value["working_revision"]),int(value["lifecycle_revision"]),int(value["attachment_revision"]),str(value["attachment_sha256"]),int(value["aggregate_revision"]),RefinementThoughtRepository.next_resume_order(conn),str(value["state"]),str(value.get("created_at") or now),now,now if value["state"]=="completed" else None,now if value["state"]=="tombstoned" else None))
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
            conn.execute("UPDATE refinement_thoughts SET working_revision=?,lifecycle_revision=?,attachment_revision=?,attachment_sha256=?,aggregate_revision=?,resume_order=?,state=?,updated_at=?,completed_at=?,tombstoned_at=? WHERE id=?",(int(value["working_revision"]),int(value["lifecycle_revision"]),int(value["attachment_revision"]),str(value["attachment_sha256"]),int(value["aggregate_revision"]),RefinementThoughtRepository.next_resume_order(conn),str(value["state"]),now,now if value["state"]=="completed" else None,now if value["state"]=="tombstoned" else None,thought_id))
            if value["state"]=="tombstoned": conn.execute("UPDATE directory_memberships SET deleted=1,last_modified=? WHERE primitive_id=?",(now,f"note:{local['working_note_id']}"))

    @staticmethod
    def _install_ledger_rows(conn: Any, thought_id: str, value: dict[str, Any], *, start_command: int) -> None:
        for revision in value.get("attachments") or []:
            number = int(revision["attachment_revision"])
            if conn.execute("SELECT 1 FROM refinement_attachment_revisions WHERE thought_id=? AND attachment_revision=?", (thought_id, number)).fetchone():
                continue
            conn.execute("INSERT INTO refinement_attachment_revisions(thought_id,attachment_revision,aggregate_revision,attachment_sha256,visible_count,leaf_count,created_at) VALUES(?,?,?,?,?,?,?)", (thought_id,number,int(revision["aggregate_revision"]),str(revision["attachment_sha256"]),int(revision["visible_count"]),int(revision["leaf_count"]),str(revision["created_at"])))
            for visible in revision.get("visible") or []:
                conn.execute("INSERT INTO refinement_attachment_visible(thought_id,attachment_revision,ordinal,visible_ref,visible_kind,visible_title,source_last_modified,visible_sha256) VALUES(?,?,?,?,?,?,?,?)", (thought_id,number,int(visible["ordinal"]),str(visible["visible_ref"]),str(visible["visible_kind"]),str(visible["visible_title"]),str(visible["source_last_modified"]),str(visible["visible_sha256"])))
                for leaf in visible.get("leaves") or []:
                    conn.execute("INSERT INTO refinement_attachment_leaves(thought_id,attachment_revision,visible_ordinal,leaf_ordinal,leaf_ref,leaf_title,source_last_modified,membership_last_modified,leaf_content_sha256,leaf_metadata_sha256) VALUES(?,?,?,?,?,?,?,?,?,?)", (thought_id,number,int(visible["ordinal"]),int(leaf["leaf_ordinal"]),str(leaf["leaf_ref"]),str(leaf["leaf_title"]),str(leaf["source_last_modified"]),str(leaf["membership_last_modified"]),str(leaf["leaf_content_sha256"]),str(leaf["leaf_metadata_sha256"])))
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
                conn.execute("INSERT INTO refinement_aggregate_commands (thought_id,aggregate_revision,command_kind,prior_working_revision,next_working_revision,prior_lifecycle_revision,next_lifecycle_revision,prior_attachment_revision,next_attachment_revision,canonical_version,attachment_sha256,canonical_sha256,lifecycle_sha256,accepted_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(thought_id,int(item["aggregate_revision"]),str(item["command_kind"]),int(item["prior_working_revision"]),int(item["next_working_revision"]),int(item["prior_lifecycle_revision"]),int(item["next_lifecycle_revision"]),int(item["prior_attachment_revision"]),int(item["next_attachment_revision"]),int(item.get("canonical_version") or 1),item.get("attachment_sha256"),str(item["canonical_sha256"]),item.get("lifecycle_sha256"),str(item["accepted_at"])))

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
                try:
                    admission = json.loads(str(inv["admission_json"] or "{}"))
                except ValueError:
                    admission = {}
                admission_raw = canonical_json(admission)
                if (inv["dispatch_host_id"] and (admission.get("readiness") != "ready"
                        or hashlib.sha256(admission_raw).hexdigest() != str(inv["admission_sha256"] or ""))):
                    raise ValidationError("refinement admission claim is invalid", code="refinement_admission_invalid")
                if inv["dispatch_host_id"]:
                    lease_now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
                    host = conn.execute("SELECT lease_epoch,expires_at FROM refinement_hosts WHERE host_id=?",
                                        (inv["dispatch_host_id"],)).fetchone()
                    if (host is None or int(host["lease_epoch"]) != int(inv["dispatch_lease_epoch"] or 0)
                            or str(host["expires_at"]) <= lease_now):
                        raise ValidationError("refinement execution host lease is not live",
                                              code="refinement_host_lease_expired")
                routed_child = str(ask_invocation_id).startswith("invoke_") and conn.execute(
                    "SELECT 1 FROM inference_route_attempts WHERE child_invocation_id=? "
                    "AND physical_attempt_ordinal=? AND child_operation_id=?",
                    (ask_invocation_id, attempt_ordinal, operation_id),
                ).fetchone() is not None
                if routed_child and attempt_ordinal == 1 and attempt is not None:
                    if attempt["kernel_operation_id"] is None:
                        conn.execute(
                            "UPDATE refinement_invocation_attempts SET ask_invocation_id=? "
                            "WHERE invocation_id=? AND attempt_ordinal=1",
                            (ask_invocation_id, invocation_id),
                        )
                        attempt = conn.execute(
                            "SELECT * FROM refinement_invocation_attempts WHERE invocation_id=? AND attempt_ordinal=1",
                            (invocation_id,),
                        ).fetchone()
                elif routed_child and attempt is None and attempt_ordinal > 1:
                    previous = conn.execute(
                        "SELECT * FROM refinement_invocation_attempts WHERE invocation_id=? "
                        "AND attempt_ordinal=?",
                        (invocation_id, attempt_ordinal - 1),
                    ).fetchone()
                    prior_receipt = None if previous is None else conn.execute(
                        "SELECT receipt_id,outcome,result_ref FROM kernel_receipts WHERE operation_id=?",
                        (previous["kernel_operation_id"],),
                    ).fetchone()
                    if prior_receipt is not None and str(previous["state"]) == "in_flight":
                        conn.execute(
                            "UPDATE refinement_invocation_attempts SET state=?,receipt_id=?,result_ref=?,terminal_at=? "
                            "WHERE invocation_id=? AND attempt_ordinal=?",
                            (str(prior_receipt["outcome"]), prior_receipt["receipt_id"],
                             prior_receipt["result_ref"], _now(), invocation_id,
                             attempt_ordinal - 1),
                        )
                        previous = conn.execute(
                            "SELECT * FROM refinement_invocation_attempts WHERE invocation_id=? AND attempt_ordinal=?",
                            (invocation_id, attempt_ordinal - 1),
                        ).fetchone()
                    if previous is None or str(previous["state"]) not in {
                        "failed", "refused", "cancelled", "indeterminate"
                    }:
                        raise ValidationError("routed fallback is not earned", code="refinement_attempt_invalid")
                    conn.execute(
                        "INSERT INTO refinement_invocation_attempts"
                        "(invocation_id,attempt_ordinal,ask_invocation_id,state,created_at) "
                        "VALUES(?,?,?,'reserved',?)",
                        (invocation_id, attempt_ordinal, ask_invocation_id, _now()),
                    )
                    attempt = conn.execute(
                        "SELECT * FROM refinement_invocation_attempts WHERE invocation_id=? AND attempt_ordinal=?",
                        (invocation_id, attempt_ordinal),
                    ).fetchone()
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
                if attempt is None or str(attempt["ask_invocation_id"]) != ask_invocation_id:
                    raise ValidationError("refinement attempt cannot dispatch", code="refinement_attempt_invalid")
                thought = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (inv["thought_id"],)).fetchone()
                if thought is None or str(thought["state"]) != "working" or (int(thought["aggregate_revision"]),int(thought["working_revision"]),int(thought["attachment_revision"]),str(thought["attachment_sha256"] or RefinementThoughtRepository.empty_attachment_hash(str(inv["thought_id"])))) != (int(inv["frozen_aggregate_revision"]),int(inv["frozen_working_revision"]),int(inv["frozen_attachment_revision"]),str(inv["frozen_attachment_sha256"])):
                    raise ValidationError("refinement source changed", code="refinement_result_stale")
                if str(inv["state"]) not in {"reserved","in_flight"}:
                    raise ValidationError("refinement attempt cannot dispatch", code="refinement_attempt_invalid")
                from .refinement_context_service import RefinementContextService
                RefinementContextService(self._db).validate_frozen_in_transaction(
                    conn, str(inv["thought_id"]), int(inv["frozen_attachment_revision"]),
                    str(inv["frozen_attachment_sha256"]),
                )
                now = _now()
                if attempt["kernel_operation_id"] and str(attempt["kernel_operation_id"]) != operation_id: raise ValidationError("attempt operation changed", code="refinement_correlation_mismatch")
                if (str(attempt["kernel_operation_id"] or "") == operation_id
                        and str(attempt["state"]) == "in_flight" and str(inv["state"]) == "in_flight"):
                    return
                conn.execute("UPDATE refinement_invocation_attempts SET kernel_operation_id=?,state='in_flight',bound_at=? WHERE invocation_id=? AND attempt_ordinal=?", (operation_id,now,invocation_id,attempt_ordinal))
                conn.execute("UPDATE refinement_invocations SET state='in_flight',updated_at=? WHERE id=?", (now,invocation_id))
                self._bump_continuity(conn, str(inv["thought_id"]))
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
                if not existing:
                    owner = conn.execute("SELECT thought_id FROM refinement_invocations WHERE id=?", (invocation_id,)).fetchone()
                    if owner: self._bump_continuity(conn, str(owner["thought_id"]))
        return plan

    def get_workbench(self, principal: Principal, thought_id: str, *, inference_available: bool,
                      intended_placement: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return one coherent, zero-write owner projection from one snapshot."""
        self._require_product_owner(principal)
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if row is None: raise NotFound("thought", thought_id)
            return self._workbench_in_transaction(conn, self._record(row), inference_available=inference_available,
                                                  intended_placement=intended_placement)

    def validate_workspace_cursor(self, principal: Principal, thought_id: str,
                                  cursor: dict[str, Any] | None, *, relaxed: bool = False,
                                  invocation_id: str | None = None) -> None:
        """Validate the optional additive Workbench fence without mutating."""
        self._require_product_owner(principal)
        if cursor is None: return
        keys = {"hub_id", "thought_id", "aggregate_revision", "continuity_revision"}
        if (not isinstance(cursor, dict) or set(cursor) != keys
                or not isinstance(cursor.get("hub_id"), str)
                or not isinstance(cursor.get("thought_id"), str)
                or not isinstance(cursor.get("aggregate_revision"), int)
                or not isinstance(cursor.get("continuity_revision"), int)):
            raise ValidationError("workspace cursor is invalid", code="workspace_cursor_invalid")
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if row is None: raise NotFound("thought", thought_id)
            record = self._record(row); current = int(record.get("continuity_revision") or 0)
            same = (cursor["hub_id"] == self._workspace_hub_id(conn)
                    and cursor["thought_id"] == thought_id
                    and cursor["aggregate_revision"] == int(record["aggregate_revision"]))
            if relaxed:
                same = same and 0 <= cursor["continuity_revision"] <= current
                if invocation_id is not None:
                    inv = conn.execute("SELECT state FROM refinement_invocations WHERE id=? AND thought_id=?",
                                       (invocation_id, thought_id)).fetchone()
                    same = same and bool(inv and str(inv["state"]) in {"reserved","in_flight","awaiting_projection","review_ready"})
            else:
                same = same and cursor["continuity_revision"] == current
            if not same:
                raise ConflictError("workspace changed elsewhere", code="workspace_cursor_conflict",
                                    context={"current": self._workbench_in_transaction(conn, record, inference_available=True)})

    @staticmethod
    def _workspace_hub_id(conn: Any) -> str:
        row = conn.execute("SELECT hub_id FROM refinement_workspace_identity WHERE id=1").fetchone()
        if row is None or not str(row["hub_id"] or "").startswith("hub_"):
            raise ConflictError("workspace identity is unavailable", code="workspace_identity_unavailable")
        return str(row["hub_id"])

    @staticmethod
    def _bump_continuity(conn: Any, thought_id: str) -> int:
        conn.execute("UPDATE refinement_thoughts SET continuity_revision=continuity_revision+1 WHERE id=?", (thought_id,))
        row = conn.execute("SELECT continuity_revision FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
        return int(row["continuity_revision"])

    @staticmethod
    def _terminal_status(code: str) -> dict[str, Any] | None:
        if not code: return None
        visible_code = _closed_terminal_code(code)
        category = _TERMINAL_CODE_CATEGORY[visible_code]
        return {"code": visible_code, "category": category, "retryable": category == "retryable"}

    def _strict_review_provenance(self, payload_json: str) -> dict[str, Any]:
        """Validate placement as one closed combined proof; never salvage halves."""
        unavailable = {"state": "unavailable"}
        try: payload = json.loads(payload_json)
        except (TypeError, ValueError): return unavailable
        if not isinstance(payload, dict): return unavailable
        placement, egress = payload.get("actual_placement"), payload.get("egress")
        pkeys = {"target_id","target_name","target_kind","boundary","owner","transport",
                 "data_classes","engine","model","fallback_reason"}
        required = {"target_id","target_name","target_kind","boundary","owner","transport","data_classes","engine"}
        if (not isinstance(placement, dict) or not isinstance(egress, dict)
                or set(placement) - pkeys or set(egress) - {"scope","host"} or not required <= set(placement)):
            return unavailable
        if any(not isinstance(placement[key], str) or not placement[key] or len(placement[key].encode("utf-8")) > 500
               for key in required - {"data_classes"}):
            return unavailable
        classes = placement.get("data_classes")
        if (not isinstance(classes, list) or len(classes) > 8
                or len(set(classes)) != len(classes)
                or any(not isinstance(item, str) or not item or len(item) > 120 or not item.isascii() for item in classes)):
            return unavailable
        if egress.get("scope") not in {"local","private_network","cloud","mesh"}:
            return unavailable
        if egress.get("host") is not None and (not isinstance(egress.get("host"), str)
                                                or len(egress["host"].encode("utf-8")) > 500
                                                or not egress["host"].isascii()): return unavailable
        if any(placement.get(key) is not None and not isinstance(placement.get(key), str)
               for key in ("model","fallback_reason")): return unavailable
        if any(isinstance(placement.get(key), str) and len(placement[key].encode("utf-8")) > 500
               for key in ("model","fallback_reason")): return unavailable
        if any(not str(placement[key]).isascii() for key in ("target_id","target_kind","boundary","owner","transport")):
            return unavailable
        exact = {
            ("this_device","same_device","you","in_process","local"),
            ("private_endpoint","private_network","you","https","private_network"),
            ("external_service","external_service","service_provider","https","cloud"),
            ("paired_device","paired_device","you","paired_https","local"),
            ("paired_device","paired_device_then_external_service","you","paired_https","cloud"),
            ("mesh_node","private_mesh","you","mesh_relay","mesh"),
        }
        combo = (str(placement["target_kind"]),str(placement["boundary"]),str(placement["owner"]),
                 str(placement["transport"]),str(egress["scope"]))
        host = egress.get("host")
        fallback = placement.get("fallback_reason")
        host_required = egress["scope"] in {"private_network","mesh"}
        fallback_required = placement["boundary"] == "paired_device_then_external_service"
        if (combo not in exact or (host_required and not host) or (not host_required and host is not None)
                or (fallback_required and not fallback) or (not fallback_required and fallback is not None)):
            return unavailable
        return {"state":"available", "actual_placement":placement, "egress":egress}

    def _workbench_in_transaction(self, conn: Any, record: dict[str, Any], *,
                                  inference_available: bool,
                                  intended_placement: dict[str, Any] | None = None) -> dict[str, Any]:
        thought = self._dto_in_transaction(conn, record); hub_id = self._workspace_hub_id(conn)
        cursor = {"hub_id":hub_id,"thought_id":record["id"],
                  "aggregate_revision":int(record["aggregate_revision"]),
                  "continuity_revision":int(record.get("continuity_revision") or 0)}
        inv = conn.execute("SELECT * FROM refinement_invocations WHERE thought_id=? ORDER BY created_at DESC,rowid DESC LIMIT 1",
                           (record["id"],)).fetchone()
        review = None; terminal = None; state = "idle"; state_actions: list[dict[str, Any]] = []; primary = None
        if record["state"] == "completed":
            state = "completed"; primary = {"kind":"resume"}; state_actions = [primary]
        elif inv is not None and str(inv["state"]) in {"reserved","in_flight","awaiting_projection"}:
            state = str(inv["state"]); primary = {"kind":"stop_refinement","invocation_id":str(inv["id"])}; state_actions = [primary]
        elif inv is not None and str(inv["state"]) == "review_ready":
            row = conn.execute("SELECT rr.*,ar.payload_json FROM refinement_review_results rr JOIN ask_results ar ON ar.projection_stage_id=rr.ask_result_stage_id WHERE rr.id=?",
                               (inv["review_result_id"],)).fetchone()
            if row is not None:
                card = self._review_card(str(row["payload_json"])); state = str(card["kind"])
                review = {"id":str(row["id"]), **card,
                          "placement":self._strict_review_provenance(str(row["payload_json"])),
                          "frozen_aggregate_revision":int(row["frozen_aggregate_revision"]),
                          "frozen_working_revision":int(row["frozen_working_revision"]),
                          "frozen_attachment_revision":int(row["frozen_attachment_revision"])}
                from .refinement_context_service import RefinementContextService
                used = RefinementContextService(self._db).used_context_in_transaction(
                    conn, str(record["id"]), int(row["frozen_attachment_revision"])
                )
                if used is not None: review["used_context"] = used
                if card["kind"] == "question":
                    answer = {"kind":"answer_review","review_result_id":str(row["id"])}
                    state_actions = [answer,{"kind":"reject_review","review_result_id":str(row["id"])}]
                    if inference_available:
                        primary = {"kind":"answer_and_continue","review_result_id":str(row["id"])}
                        state_actions.insert(0, primary)
                    else: primary = answer
                else:
                    primary = {"kind":"accept_review","review_result_id":str(row["id"])}
                    state_actions = [primary,{"kind":"reject_review","review_result_id":str(row["id"])}]
        elif inv is not None:
            terminal = self._terminal_status(str(inv["terminal_code"] or "unknown_terminal"))
            state = "idle" if terminal and terminal["category"] == "owner_terminal" else "named_failure"
            if state == "idle" and inference_available:
                primary = {"kind":"refine"}; state_actions = [primary]
            elif terminal and terminal["retryable"] and inference_available:
                primary = {"kind":"refine"}; state_actions = [primary]
        elif record["state"] == "working" and inference_available:
            primary = {"kind":"refine"}; state_actions = [primary]
        ambient = ["update_working","attach_context","complete"] if record["state"] == "working" else []
        if primary is None and record["state"] == "working":
            primary = {"kind":"configure_ai"} if state == "idle" and not inference_available else {"kind":"complete"}
            state_actions = [primary]
        attachments = thought.get("attachments") or []
        broken = next((item for item in attachments if item.get("state") != "current"), None)
        if broken is not None and state in {"idle", "named_failure", "question", "synthesis"}:
            state = "stale"
            repair_kind = "detach_context" if broken.get("state") == "missing" else "refresh_context"
            primary = {"kind":repair_kind,"ref":str(broken["ref"])}
            state_actions = [primary]
            if repair_kind != "detach_context":
                state_actions.append({"kind":"detach_context","ref":str(broken["ref"])})
        return {"schema_version":1,
                "process_scope":{"kind":"hub_local","hub_id":hub_id,
                                 "state":"available" if inference_available else "unavailable"},
                "workspace_cursor":cursor,"thought":thought,"workspace_state":state,
                "actions":{"primary":primary,"state":state_actions,"ambient":ambient},"review":review,
                "context_status":{"summary":" · ".join(str(item.get("title") or item.get("ref")) for item in attachments),
                                  "state":str(broken.get("state")) if broken else ("current" if attachments else "empty"),
                                  "repair_ref":str(broken["ref"]) if broken else None},
                "inference":{"availability":"ready" if inference_available else "unavailable",
                             "continuation_admission":"ready" if inference_available else "unavailable",
                             "intended_placement":intended_placement},"terminal_status":terminal}

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
        row = conn.execute("SELECT id,state,review_result_id,terminal_code FROM refinement_invocations WHERE thought_id=? ORDER BY created_at DESC,rowid DESC LIMIT 1", (thought_id,)).fetchone()
        if row is None: return {"state":"idle","code":""}
        state = str(row["state"]); return {"state": "named_failure" if state in {"failed","refused","cancelled","indeterminate","unknown","superseded"} else state, "invocation_id":str(row["id"]), "review_result_id":row["review_result_id"], "code":str(row["terminal_code"] or "")}
    @staticmethod
    def _supersede_invocations(conn: Any, thought_id: str, code: str) -> None:
        now = _now()
        conn.execute("UPDATE refinement_invocations SET state='superseded',terminal_code=?,updated_at=?,terminal_at=? WHERE thought_id=? AND state IN ('reserved','in_flight','awaiting_projection','review_ready')", (_closed_terminal_code(str(code)),now,now,thought_id))
    def _invocation_dto(self, conn: Any, inv: dict[str, Any]) -> dict[str, Any]:
        attempts = conn.execute("SELECT attempt_ordinal,ask_invocation_id,state FROM refinement_invocation_attempts WHERE invocation_id=? ORDER BY attempt_ordinal", (inv["id"],)).fetchall()
        try:
            admission = json.loads(str(inv.get("admission_json") or "{}"))
        except (TypeError, ValueError):
            admission = {}
        return {"id":inv["id"],"request_id":inv["request_id"],"thought_id":inv["thought_id"],"frozen_aggregate_revision":inv["frozen_aggregate_revision"],"frozen_working_revision":inv["frozen_working_revision"],"frozen_attachment_revision":inv["frozen_attachment_revision"],"frozen_attachment_sha256":inv["frozen_attachment_sha256"],"admission":admission,"route_plan_id":inv.get("route_plan_id"),"operation_plan_id":inv.get("operation_plan_id"),"route_execution_id":inv.get("route_execution_id"),"state":inv["state"],"attempts":[{"attempt_ordinal":x["attempt_ordinal"],"ask_invocation_id":x["ask_invocation_id"],"state":x["state"]} for x in attempts]}
    def _reconcile_invocation_in_transaction(self, conn: Any, inv: dict[str, Any], thought: dict[str, Any]) -> None:
        # Stop, Good enough, owner edit, Answer/Accept/Reject and an earlier
        # terminal reconciliation are durable suppression fences.  Late kernel
        # proof may remain auditable in native tables, but can never resurrect
        # a review invitation after one of those owner decisions.
        if str(inv["state"]) not in {"reserved", "in_flight", "awaiting_projection", "review_ready"}:
            return
        if (int(thought["aggregate_revision"]),int(thought["working_revision"]),int(thought["attachment_revision"])) != (int(inv["frozen_aggregate_revision"]),int(inv["frozen_working_revision"]),int(inv["frozen_attachment_revision"])):
            conn.execute("UPDATE refinement_invocations SET state='stale',terminal_code='refinement_result_stale',updated_at=?,terminal_at=? WHERE id=?", (_now(),_now(),inv["id"])); return
        if inv.get("route_execution_id"):
            routed = conn.execute(
                """SELECT ra.child_operation_id,ra.outcome,ra.result_ref,
                          kr.receipt_id,ks.stage_id,ar.projection_stage_id ask_stage
                     FROM inference_route_executions re
                     LEFT JOIN inference_route_attempts ra ON ra.id=re.winning_attempt_id
                     LEFT JOIN kernel_receipts kr ON kr.operation_id=ra.child_operation_id
                     LEFT JOIN kernel_projection_stages ks ON ks.operation_id=ra.child_operation_id
                     LEFT JOIN ask_results ar ON ar.operation_id=ra.child_operation_id
                    WHERE re.id=? AND re.state='terminal' AND re.terminal_outcome='succeeded'""",
                (str(inv["route_execution_id"]),),
            ).fetchone()
            if routed is not None and routed["child_operation_id"] and routed["ask_stage"]:
                conn.execute(
                    """UPDATE refinement_invocation_attempts
                          SET kernel_operation_id=?,projection_stage_id=?,ask_result_stage_id=?,
                              receipt_id=?,result_ref=?,state='succeeded',terminal_code='',
                              bound_at=COALESCE(bound_at,?),terminal_at=COALESCE(terminal_at,?)
                        WHERE invocation_id=? AND attempt_ordinal=1""",
                    (str(routed["child_operation_id"]), str(routed["stage_id"]),
                     str(routed["ask_stage"]), str(routed["receipt_id"]),
                     str(routed["result_ref"]), _now(), _now(), str(inv["id"])),
                )
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
            row = conn.execute("SELECT r.receipt_id,r.outcome,r.result_ref,s.stage_id,s.kind,s.state stage_state,s.invocation_id stage_invocation,s.operation_id stage_operation,s.result_ref stage_result_ref,a.projection_stage_id,a.invocation_id ask_invocation,a.operation_id ask_operation,a.receipt_id ask_receipt,a.payload_json,ra.id route_attempt_id,ra.child_invocation_id route_child_invocation,ra.execution_id route_execution_id,re.state route_execution_state,re.terminal_outcome route_execution_outcome,re.winning_attempt_id FROM kernel_receipts r LEFT JOIN kernel_projection_stages s ON s.operation_id=r.operation_id LEFT JOIN ask_results a ON a.operation_id=r.operation_id LEFT JOIN inference_route_attempts ra ON ra.child_operation_id=r.operation_id LEFT JOIN inference_route_executions re ON re.id=ra.execution_id WHERE r.operation_id=?", (op,)).fetchone()
            if row is None: continue
            if str(row["outcome"]) == "succeeded": known_success = True
            controller_winner = (
                row["route_attempt_id"] is None
                or (
                    str(row["route_execution_state"] or "") == "terminal"
                    and str(row["route_execution_outcome"] or "") == "succeeded"
                    and str(row["winning_attempt_id"] or "") == str(row["route_attempt_id"])
                )
            )
            expected_invocation = str(row["route_child_invocation"] or attempt["ask_invocation_id"])
            if str(row["outcome"]) == "succeeded" and controller_winner and row["projection_stage_id"] and str(row["result_ref"]) and str(row["stage_id"] or "") == str(row["projection_stage_id"]) and str(row["kind"] or "") == "ask-result" and str(row["stage_state"] or "") == "PUBLISHED" and str(row["stage_invocation"] or "") == expected_invocation and str(row["ask_invocation"] or "") == expected_invocation and str(row["stage_operation"] or "") == op and str(row["ask_operation"] or "") == op and str(row["ask_receipt"] or "") == str(row["receipt_id"]) and str(row["stage_result_ref"] or "") == str(row["result_ref"]):
                winners.append((attempt,row,hashlib.sha256(str(row["payload_json"]).encode()).hexdigest()))
            conn.execute("UPDATE refinement_invocation_attempts SET state=?,receipt_id=?,result_ref=?,terminal_at=? WHERE invocation_id=? AND attempt_ordinal=?", (str(row["outcome"]),row["receipt_id"],row["result_ref"],_now(),inv["id"],attempt["attempt_ordinal"]))
        if len(winners) > 1:
            raise ConflictError("multiple refinement result attempts matched", code="refinement_correlation_mismatch")
        if winners:
            attempt,row,digest=winners[0]; existing=conn.execute("SELECT * FROM refinement_review_results WHERE invocation_id=?",(inv["id"],)).fetchone(); rid=str(existing["id"]) if existing else _id("rresult")
            # Never persist a review-ready invitation whose native payload is
            # not the narrow card grammar.  A malformed model result is a
            # named terminal outcome, not an actionable owner decision.
            try:
                self._review_card(str(row["payload_json"]))
            except ValidationError:
                conn.execute("UPDATE refinement_invocation_attempts SET state='failed',terminal_code='refinement_result_invalid',terminal_at=? WHERE invocation_id=? AND attempt_ordinal=?", (_now(), inv["id"], attempt["attempt_ordinal"]))
                conn.execute("UPDATE refinement_invocations SET state='failed',terminal_code='refinement_result_invalid',updated_at=?,terminal_at=? WHERE id=?", (_now(), _now(), inv["id"]))
                return
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
                conn.execute("UPDATE refinement_invocations SET state=?,terminal_code=?,updated_at=?,terminal_at=? WHERE id=?", (state,_closed_terminal_code(str(last["terminal_code"] or state)),_now(),_now(),inv["id"]))
    def _dto(self,record:dict[str,Any],*,include_raw:bool=False,remote:bool=False)->dict[str,Any]:
        with self._db._connection() as conn: return self._dto_in_transaction(conn,record,include_raw=include_raw,remote=remote)
    @staticmethod
    def _review_card(payload_json: str) -> dict[str, Any]:
        """The only model-shaped datum that may become an owner review card."""
        try:
            outer = json.loads(payload_json); card = json.loads(str(outer.get("output") or ""))
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValidationError("refinement result is not a valid review", code="refinement_result_invalid") from exc
        if not isinstance(card, dict): raise ValidationError("refinement result is not a valid review", code="refinement_result_invalid")
        if card.get("kind") == "question" and set(card) <= {"kind","question","reason"} and isinstance(card.get("question"), str) and isinstance(card.get("reason", ""), str) and 0 < len(card["question"]) <= 1200 and len(str(card.get("reason") or "")) <= 1200:
            return {"kind":"question", "question":card["question"], "reason":str(card.get("reason") or "")}
        if card.get("kind") == "synthesis" and set(card) <= {"kind","title","body_markdown","tags"} and isinstance(card.get("title"),str) and isinstance(card.get("body_markdown"),str) and isinstance(card.get("tags"),list) and len(card["title"]) <= 500 and len(card["body_markdown"]) <= 12000 and len(card["tags"]) <= 24 and all(isinstance(x,str) and len(x) <= 80 for x in card["tags"]):
            return {"kind":"synthesis","title":card["title"],"body_markdown":card["body_markdown"],"tags":card["tags"]}
        raise ValidationError("refinement result is not a valid review", code="refinement_result_invalid")
    @staticmethod
    def _review_provenance(payload_json: str) -> dict[str, Any]:
        """Expose bounded execution facts, never the native Ask payload."""
        try:
            payload = json.loads(payload_json)
        except (TypeError, ValueError):
            payload = {}
        if not isinstance(payload, dict): payload = {}
        raw_placement = payload.get("actual_placement")
        placement: dict[str, Any] = {}
        if isinstance(raw_placement, dict):
            for key in ("target_id","target_name","target_kind","boundary","owner","transport","engine","model","fallback_reason"):
                value = raw_placement.get(key)
                if value is None or isinstance(value, (str, int, float, bool)):
                    placement[key] = value if not isinstance(value, str) else value[:500]
            classes = raw_placement.get("data_classes")
            if isinstance(classes, list):
                placement["data_classes"] = [str(value)[:120] for value in classes[:8]]
        raw_egress = payload.get("egress")
        egress: dict[str, str] = {}
        if isinstance(raw_egress, dict):
            for key in ("scope", "host"):
                if isinstance(raw_egress.get(key), str): egress[key] = str(raw_egress[key])[:500]
        return {"actual_placement": placement, "egress": egress}
    def _dto_in_transaction(self,conn:Any,record:dict[str,Any],*,include_raw:bool=False,remote:bool=False)->dict[str,Any]:
        note=conn.execute("SELECT * FROM notes WHERE id=?",(record["working_note_id"],)).fetchone(); member=conn.execute("SELECT * FROM directory_memberships WHERE primitive_id=?",(f"note:{record['working_note_id']}",)).fetchone()
        attachment_hash=str(record.get("attachment_sha256") or RefinementThoughtRepository.empty_attachment_hash(record["id"]))
        from .refinement_context_service import RefinementContextService
        attachments=RefinementContextService(self._db).project_in_transaction(conn,record)
        out={"id":record["id"],"raw_id":record["id"],"raw_sha256":record["raw_sha256"],"source":{"kind":record["raw_source_kind"]},"raw_captured_at":record["raw_captured_at"],"state":record["state"],"aggregate_revision":record["aggregate_revision"],"lifecycle_revision":record["lifecycle_revision"],"working_revision":record["working_revision"],"attachment_revision":record["attachment_revision"],"attachment_sha256":attachment_hash,"attachments":attachments,"working_note":self._note(note),"filing_status":"filed" if member and not member["deleted"] else "missing","continuity":({"state":"unavailable_remote","code":"continuity_unavailable_remote"} if remote else self._continuity(conn,record["id"]))}
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
