"""HS-141-01 custody aggregate service: every mutation appends one command."""
from __future__ import annotations

import base64
import hashlib
import json
import uuid
from typing import Any

from ..db.core import Database
from ..db.refinement_thoughts import RefinementThoughtRepository, _now
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
        if principal is None or principal.kind not in {PrincipalKind.OWNER, PrincipalKind.NODE}:
            raise ValidationError("thought custody requires the authenticated owner", code="thought_owner_required")

    def create(self, principal: Principal, *, request_id: str, raw_text: str, source: dict[str, Any] | None = None,
               initial_note: dict[str, Any] | None = None, thought_id: str | None = None) -> dict[str, Any]:
        self._require_owner(principal)
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
            self._db.notes._upsert_in_transaction(conn, note_id=note_id, title=title, body_markdown=body, tags=tags, now=now)
            conn.execute("""INSERT INTO refinement_thoughts (id,create_request_id,create_payload_sha256,raw_utf8,raw_sha256,
                raw_source_kind,raw_source_ref,raw_captured_at,working_note_id,working_revision,lifecycle_revision,attachment_revision,
                aggregate_revision,state,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,1,1,0,1,'working',?,?)""",
                (thought_id,request_id,payload_hash,raw,raw_hash,kind,ref,now,note_id,now,now))
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

    def get(self, principal: Principal, thought_id: str, *, include_raw: bool = False) -> dict[str, Any]:
        self._require_owner(principal)
        record = self._db.refinement_thoughts.get(thought_id)
        if record is None: raise NotFound("thought", thought_id)
        return self._dto(record, include_raw=include_raw)

    def list_unfinished(self, principal: Principal) -> list[dict[str, Any]]:
        self._require_owner(principal)
        return [self._dto(row) for row in self._db.refinement_thoughts.list(state="working")]

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
                cur = conn.execute("UPDATE refinement_thoughts SET working_revision=?,aggregate_revision=?,updated_at=? WHERE id=? AND working_revision=? AND aggregate_revision=? AND state='working'",
                    (next_working,next_aggregate,now,thought_id,expected_working_revision,expected_aggregate_revision))
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

    def complete(self, principal: Principal, thought_id: str, *, expected_aggregate_revision: int | None,
                 expected_lifecycle_revision: int | None) -> dict[str, Any]:
        return self._transition(principal,thought_id,expected_aggregate_revision=expected_aggregate_revision,
            expected_lifecycle_revision=expected_lifecycle_revision,command="complete",state="completed")

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
            cur=conn.execute("UPDATE refinement_thoughts SET state=?,lifecycle_revision=?,aggregate_revision=?,completed_at=?,updated_at=? WHERE id=? AND aggregate_revision=? AND lifecycle_revision=? AND state=?",
                (state,next_life,next_agg,now if state=="completed" else None,now,thought_id,expected_aggregate_revision,expected_lifecycle_revision,record["state"]))
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
        self._require_owner(principal)
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
            conn.execute("""INSERT INTO refinement_thoughts (id,create_request_id,create_payload_sha256,raw_utf8,raw_sha256,raw_source_kind,raw_source_ref,raw_captured_at,working_note_id,working_revision,lifecycle_revision,attachment_revision,aggregate_revision,state,created_at,updated_at,completed_at,tombstoned_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (thought_id,str(value["create_request_id"]),str(value["create_payload_sha256"]),raw_utf8,str(value["raw_sha256"]),str(source["kind"]),source.get("ref"),str(value["raw_captured_at"]),note_id,int(value["working_revision"]),int(value["lifecycle_revision"]),int(value["attachment_revision"]),int(value["aggregate_revision"]),str(value["state"]),str(value.get("created_at") or now),now,now if value["state"]=="completed" else None,now if value["state"]=="tombstoned" else None))
            self._install_ledger_rows(conn, thought_id, value, start_command=1)
            if value["state"] == "tombstoned":
                conn.execute("UPDATE directory_memberships SET deleted=1 WHERE primitive_id=?", (f"note:{note_id}",))

    def apply_sync_bundle(self, principal: Principal, *, thought_id: str, value: dict[str, Any]) -> None:
        """Fast-forward a validated contiguous aggregate-command suffix."""
        self._require_owner(principal)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row=conn.execute("SELECT * FROM refinement_thoughts WHERE id=?",(thought_id,)).fetchone()
            if row is None: raise NotFound("thought",thought_id)
            local=self._record(row); start=int(local["aggregate_revision"])+1
            if start>int(value["aggregate_revision"]): return
            self._install_ledger_rows(conn,thought_id,value,start_command=start)
            working=dict(value["working_note"]); now=str(value.get("last_modified") or _now())
            conn.execute("UPDATE notes SET title=?,body_markdown=?,tags_json=?,updated_at=?,last_modified=?,deleted=? WHERE id=?",(str(working.get("title") or ""),str(working.get("body_markdown") or ""),json.dumps(working.get("tags") or [],separators=(",",":")),now,now,int(value["state"]=="tombstoned"),local["working_note_id"]))
            conn.execute("UPDATE refinement_thoughts SET working_revision=?,lifecycle_revision=?,attachment_revision=?,aggregate_revision=?,state=?,updated_at=?,completed_at=?,tombstoned_at=? WHERE id=?",(int(value["working_revision"]),int(value["lifecycle_revision"]),int(value["attachment_revision"]),int(value["aggregate_revision"]),str(value["state"]),now,now if value["state"]=="completed" else None,now if value["state"]=="tombstoned" else None,thought_id))
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

    def _dto(self,record:dict[str,Any],*,include_raw:bool=False)->dict[str,Any]:
        with self._db._connection() as conn: return self._dto_in_transaction(conn,record,include_raw=include_raw)
    def _dto_in_transaction(self,conn:Any,record:dict[str,Any],*,include_raw:bool=False)->dict[str,Any]:
        note=conn.execute("SELECT * FROM notes WHERE id=?",(record["working_note_id"],)).fetchone(); member=conn.execute("SELECT * FROM directory_memberships WHERE primitive_id=?",(f"note:{record['working_note_id']}",)).fetchone()
        out={"id":record["id"],"raw_id":record["id"],"raw_sha256":record["raw_sha256"],"source":{"kind":record["raw_source_kind"],"ref":record["raw_source_ref"]},"raw_captured_at":record["raw_captured_at"],"state":record["state"],"aggregate_revision":record["aggregate_revision"],"lifecycle_revision":record["lifecycle_revision"],"working_revision":record["working_revision"],"attachment_revision":record["attachment_revision"],"working_note":self._note(note),"filing_status":"filed" if member and not member["deleted"] else "missing"}
        if member and not member["deleted"]: out["directory_id"]=member["directory_id"]
        if include_raw: out["raw_text"]=base64.b64decode(record["raw_utf8_b64"]).decode("utf-8","strict")
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
