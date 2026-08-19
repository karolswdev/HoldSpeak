from __future__ import annotations

import copy
import pytest

from holdspeak.db import Database
from holdspeak.services.errors import ConflictError, ValidationError
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.services.refinement_thought_service import INBOX_DIRECTORY_ID, RefinementThoughtService
from holdspeak.services.sync_service import SyncService
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.kernel.provider_signals import retry_invocation_id

OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "thoughts.db")
    database.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    return database


def _create(db: Database):
    return RefinementThoughtService(db).create(OWNER, request_id="capture-1", raw_text="raw\nbytes", source={"kind": "typed"})


def test_create_is_idempotent_byte_exact_and_qualified_inbox(db):
    service = RefinementThoughtService(db)
    first = _create(db)
    retry = _create(db)
    assert retry["id"] == first["id"]
    assert service.get(OWNER, first["id"], include_raw=True)["raw_text"] == "raw\nbytes"
    assert db.directory_memberships.get(f"note:{first['working_note']['id']}").directory_id == INBOX_DIRECTORY_ID
    with pytest.raises(ConflictError, match="different content"):
        service.create(OWNER, request_id="capture-1", raw_text="other", source={"kind": "typed"})


def test_two_writers_generic_crud_and_direct_repo_cannot_bypass_cas(db):
    thought = _create(db)
    service = RefinementThoughtService(db)
    note_id = thought["working_note"]["id"]
    assert service.update_note(OWNER, note_id, expected_aggregate_revision=1, expected_working_revision=1, body_markdown="edited")["working_revision"] == 2
    with pytest.raises(ConflictError) as exc:
        service.update_note(OWNER, note_id, expected_aggregate_revision=1, expected_working_revision=1, body_markdown="lost")
    assert exc.value.code == "thought_revision_conflict"
    with pytest.raises(ValueError, match="expected revision"):
        db.notes.upsert(note_id=note_id, body_markdown="bypass")
    with db._connection() as conn, pytest.raises(ValueError, match="not authorized"):
        db.notes.upsert_in_transaction(conn, note_id=note_id, body_markdown="bypass")
    with pytest.raises(ConflictError) as missing:
        PrimitiveService(db).update_note(OWNER, note_id, body_markdown="bypass")
    assert missing.value.code == "thought_expected_revision_required"


def test_generic_note_mutations_racing_adoption_name_the_required_cursors(db, monkeypatch):
    """The generic ownership read may go stale; the repository lock is final."""
    service = RefinementThoughtService(db)
    primitives = PrimitiveService(db)

    def adopt_between_read_and_write(note_id: str) -> None:
        source = service.for_note(OWNER, note_id)["source_precondition"]
        service.adopt_note(OWNER, request_id=f"adopt-race-{note_id}", note_id=note_id,
            expected_source_content_sha256=source["content_sha256"],
            expected_source_last_modified=source["last_modified"])

    db.notes.upsert(note_id="update-race", body_markdown="before")
    real_upsert = db.notes.upsert
    fired_update = False
    def upsert_barrier(**kwargs):
        nonlocal fired_update
        if kwargs["note_id"] == "update-race" and not fired_update:
            fired_update = True; adopt_between_read_and_write("update-race")
        return real_upsert(**kwargs)
    monkeypatch.setattr(db.notes, "upsert", upsert_barrier)
    with pytest.raises(ConflictError) as update:
        primitives.update_note(OWNER, "update-race", body_markdown="lost")
    assert update.value.code == "thought_expected_revision_required"

    db.notes.upsert = real_upsert
    db.notes.upsert(note_id="delete-race", body_markdown="before")
    real_delete = db.notes.delete
    fired_delete = False
    def delete_barrier(note_id):
        nonlocal fired_delete
        if note_id == "delete-race" and not fired_delete:
            fired_delete = True; adopt_between_read_and_write("delete-race")
        return real_delete(note_id)
    monkeypatch.setattr(db.notes, "delete", delete_barrier)
    with pytest.raises(ConflictError) as delete:
        primitives.delete_note(OWNER, "delete-race")
    assert delete.value.code == "thought_expected_revision_required"


def test_create_refuses_existing_ordinary_initial_note_without_overwrite(db):
    db.notes.upsert(note_id="ordinary", title="Keep me", body_markdown="original")
    with pytest.raises(ConflictError) as exc:
        RefinementThoughtService(db).create(
            OWNER, request_id="adoption-is-later", raw_text="raw", source={"kind": "typed"},
            initial_note={"id": "ordinary", "title": "overwrite", "body_markdown": "bad"},
        )
    assert exc.value.code == "initial_note_id_in_use"
    assert db.notes.get("ordinary").body_markdown == "original"
    assert db.refinement_thoughts.list() == []


def test_adopt_note_snapshots_existing_note_without_overwrite_and_is_idempotent(db):
    db.notes.upsert(note_id="ordinary", title="Keep me", body_markdown="exact\nbody", tags=["kept"])
    service = RefinementThoughtService(db)
    source = service.for_note(OWNER, "ordinary")
    adopted = service.adopt_note(OWNER, request_id="adopt-1", note_id="ordinary",
        expected_source_content_sha256=source["source_precondition"]["content_sha256"],
        expected_source_last_modified=source["source_precondition"]["last_modified"])
    assert adopted["working_note"]["id"] == "ordinary"
    assert service.get(OWNER, adopted["id"], include_raw=True)["raw_text"] == "exact\nbody"
    assert db.notes.get("ordinary").to_dict()["body_markdown"] == "exact\nbody"
    assert db.directory_memberships.get("note:ordinary").directory_id == INBOX_DIRECTORY_ID
    assert db.refinement_thoughts.commands(adopted["id"])[0]["command_kind"] == "adopt_note"
    retry = service.adopt_note(OWNER, request_id="adopt-1", note_id="ordinary",
        expected_source_content_sha256=source["source_precondition"]["content_sha256"],
        expected_source_last_modified=source["source_precondition"]["last_modified"])
    assert retry["id"] == adopted["id"] and len(db.notes.list()) == 1


def test_adopt_note_refuses_stale_source_and_page_snapshot_excludes_later_adoption(db):
    service = RefinementThoughtService(db)
    first = _create(db)
    page = service.list_unfinished(OWNER, limit=1)
    db.notes.upsert(note_id="ordinary", title="Original", body_markdown="one")
    source = service.for_note(OWNER, "ordinary")
    db.notes.upsert(note_id="ordinary", title="Changed", body_markdown="two")
    with pytest.raises(ConflictError) as stale:
        service.adopt_note(OWNER, request_id="adopt-stale", note_id="ordinary",
            expected_source_content_sha256=source["source_precondition"]["content_sha256"],
            expected_source_last_modified=source["source_precondition"]["last_modified"])
    assert stale.value.code == "note_adoption_conflict"
    fresh = service.for_note(OWNER, "ordinary")
    adopted = service.adopt_note(OWNER, request_id="adopt-fresh", note_id="ordinary",
        expected_source_content_sha256=fresh["source_precondition"]["content_sha256"],
        expected_source_last_modified=fresh["source_precondition"]["last_modified"])
    # The old high-water cursor cannot leak an item committed after its first page.
    if page["next_cursor"]:
        assert adopted["id"] not in {item["id"] for item in service.list_unfinished(OWNER, limit=1, cursor=page["next_cursor"])["items"]}
    assert adopted["id"] in {item["id"] for item in service.list_unfinished(OWNER, limit=20)["items"]}


def test_paired_sync_validates_adoption_provenance(tmp_path):
    left, right = Database(tmp_path / "adopt-left.db"), Database(tmp_path / "adopt-right.db")
    for database in (left, right):
        database.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    left.notes.upsert(note_id="source", title="Source", body_markdown="kept bytes")
    service = RefinementThoughtService(left)
    source = service.for_note(OWNER, "source")
    adopted = service.adopt_note(OWNER, request_id="adopt-sync", note_id="source",
        expected_source_content_sha256=source["source_precondition"]["content_sha256"],
        expected_source_last_modified=source["source_precondition"]["last_modified"])
    packet = SyncService(left, hub_model_name=lambda: "").pull(None)
    assert SyncService(right, hub_model_name=lambda: "").push(None, packet)["received"]["refinement_thoughts"] == 1
    assert RefinementThoughtService(right).get(OWNER, adopted["id"], include_raw=True)["raw_text"] == "kept bytes"
    forged = copy.deepcopy(packet)
    forged["refinement_thoughts"][0]["value"]["source"]["ref"] = "note:other"
    third = Database(tmp_path / "adopt-third.db")
    third.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    with pytest.raises(ValidationError) as refused:
        SyncService(third, hub_model_name=lambda: "").push(None, forged)
    assert refused.value.code == "thought_adoption_provenance_invalid"


def test_filing_is_not_custody_but_tombstone_blocks_refile(db):
    thought = _create(db)
    note_id = thought["working_note"]["id"]
    primitive = PrimitiveService(db)
    assert primitive.unfile_member(OWNER, INBOX_DIRECTORY_ID, f"note:{note_id}")
    assert RefinementThoughtService(db).get(OWNER, thought["id"])["state"] == "working"
    assert RefinementThoughtService(db).get(OWNER, thought["id"])["filing_status"] == "missing"
    assert primitive.delete_note(OWNER, note_id, expected_aggregate_revision=1, expected_lifecycle_revision=1)
    assert db.directory_memberships.get(f"note:{note_id}") is None
    assert db.directory_memberships.get(f"note:{note_id}", include_deleted=True).deleted is True
    with pytest.raises(ConflictError) as blocked:
        primitive.file_member(OWNER, INBOX_DIRECTORY_ID, f"note:{note_id}")
    assert blocked.value.code == "thought_tombstoned"


def test_directory_delete_only_makes_live_thought_filing_repairable(db):
    thought = _create(db)
    assert PrimitiveService(db).delete_directory(OWNER, INBOX_DIRECTORY_ID)
    reloaded = RefinementThoughtService(db).get(OWNER, thought["id"])
    assert reloaded["state"] == "working"
    assert reloaded["filing_status"] == "missing"


def test_restart_terminalizes_only_missing_working_note(tmp_path):
    path = tmp_path / "restart.db"
    db = Database(path)
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    thought = _create(db)
    # Losing the organization edge is not custody loss, even across restart.
    db.directory_memberships.delete(f"note:{thought['working_note']['id']}")
    db.close()
    reopened = Database(path)
    assert reopened.refinement_thoughts.get(thought["id"])["state"] == "working"
    with reopened._connection() as conn:
        conn.execute("UPDATE notes SET deleted=1 WHERE id=?", (thought["working_note"]["id"],))
    reopened.close()
    terminal = Database(path)
    assert terminal.refinement_thoughts.get(thought["id"])["state"] == "tombstoned"


def test_missing_note_update_repair_uses_shared_terminalization_and_membership(db):
    thought = _create(db)
    note_id = thought["working_note"]["id"]
    with db._connection() as conn:
        conn.execute("UPDATE notes SET deleted=1 WHERE id=?", (note_id,))
    with pytest.raises(ConflictError) as repair:
        RefinementThoughtService(db).update_working(OWNER, thought["id"], expected_aggregate_revision=1, expected_working_revision=1, body_markdown="lost")
    assert repair.value.code == "thought_tombstoned"
    assert db.refinement_thoughts.get(thought["id"])["state"] == "tombstoned"
    assert db.directory_memberships.get(f"note:{note_id}") is None


def test_paired_sync_bundle_retries_without_second_note_or_lww_bypass(tmp_path):
    left, right = Database(tmp_path / "left.db"), Database(tmp_path / "right.db")
    for database in (left, right):
        database.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    created = RefinementThoughtService(left).create(OWNER, request_id="paired", raw_text="raw", source={"kind": "typed"})
    packet = SyncService(left, hub_model_name=lambda: "").pull(None)
    pushed = SyncService(right, hub_model_name=lambda: "").push(None, packet)
    assert pushed["received"]["refinement_thoughts"] == 1
    assert RefinementThoughtService(right).get(OWNER, created["id"], include_raw=True)["raw_text"] == "raw"
    # The exact replay is a retry, never a second note or false generic merge.
    replay = SyncService(right, hub_model_name=lambda: "").push(None, packet)
    assert replay["received"]["notes"] == 0
    assert len(right.notes.list()) == 1

    # A tombstone carries its expected revision in meta (the sync contract
    # correctly has no content-bearing tombstone value), so it cannot become a
    # timestamp-only LWW delete.
    assert RefinementThoughtService(left).tombstone_note(OWNER, created["working_note"]["id"], expected_aggregate_revision=1, expected_lifecycle_revision=1)
    tomb = SyncService(left, hub_model_name=lambda: "").pull(None)
    assert tomb["refinement_thoughts"][0]["meta"]["expected_aggregate_revision"] == 1
    assert SyncService(right, hub_model_name=lambda: "").push(None, tomb)["received"]["refinement_thoughts"] == 1
    assert right.refinement_thoughts.get(created["id"])["state"] == "tombstoned"


def test_new_peer_gets_exact_rev2_completed_history_and_tombstone_fence(tmp_path):
    source, peer, fenced = (Database(tmp_path / name) for name in ("source.db", "peer.db", "fenced.db"))
    for database in (source, peer, fenced):
        database.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    service = RefinementThoughtService(source)
    thought = service.create(OWNER, request_id="history", raw_text="raw", source={"kind": "typed"})
    service.update_working(OWNER, thought["id"], expected_aggregate_revision=1, expected_working_revision=1, title="rev two", body_markdown="edited")
    service.complete(OWNER, thought["id"], expected_aggregate_revision=2, expected_lifecycle_revision=1)
    live = SyncService(source, hub_model_name=lambda: "").pull(None)
    SyncService(peer, hub_model_name=lambda: "").push(None, live)
    copied = peer.refinement_thoughts.get(thought["id"])
    assert copied["state"] == "completed" and copied["working_revision"] == 2
    assert [row["revision"] for row in peer.refinement_thoughts.revisions(thought["id"])] == [1, 2]
    assert peer.notes.get(copied["working_note_id"]).body_markdown == "edited"

    # A tombstone arriving first becomes a durable high-water fence. The old
    # live bundle is refused rather than recreating the aggregate.
    assert service.tombstone_note(OWNER, thought["working_note"]["id"], expected_aggregate_revision=3, expected_lifecycle_revision=2)
    tomb = SyncService(source, hub_model_name=lambda: "").pull(None)
    assert SyncService(fenced, hub_model_name=lambda: "").push(None, tomb)["received"]["refinement_thoughts"] == 1
    with pytest.raises(ConflictError) as stale:
        SyncService(fenced, hub_model_name=lambda: "").push(None, live)
    assert stale.value.code == "thought_tombstoned"

    corrupt = copy.deepcopy(live)
    corrupt["refinement_thoughts"][0]["value"]["raw_sha256"] = "0" * 64
    bad_peer = Database(tmp_path / "bad-peer.db")
    bad_peer.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    with pytest.raises(ValidationError) as bad:
        SyncService(bad_peer, hub_model_name=lambda: "").push(None, corrupt)
    assert getattr(bad.value, "code", "") == "thought_raw_hash_mismatch"
    altered = copy.deepcopy(live)
    altered["refinement_thoughts"][0]["value"]["working_note"]["body_markdown"] = "forged"
    snapshot_peer = Database(tmp_path / "snapshot-peer.db")
    snapshot_peer.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    with pytest.raises(ValidationError) as snapshot:
        SyncService(snapshot_peer, hub_model_name=lambda: "").push(None, altered)
    assert snapshot.value.code == "thought_working_snapshot_invalid"


def test_existing_peer_fast_forwards_contiguous_revision_suffix(tmp_path):
    source, peer = Database(tmp_path / "suffix-source.db"), Database(tmp_path / "suffix-peer.db")
    for database in (source, peer):
        database.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    service = RefinementThoughtService(source)
    thought = service.create(OWNER, request_id="suffix", raw_text="raw", source={"kind": "typed"})
    SyncService(peer, hub_model_name=lambda: "").push(None, SyncService(source, hub_model_name=lambda: "").pull(None))
    service.update_working(OWNER, thought["id"], expected_aggregate_revision=1, expected_working_revision=1, body_markdown="two")
    service.update_working(OWNER, thought["id"], expected_aggregate_revision=2, expected_working_revision=2, body_markdown="three")
    SyncService(peer, hub_model_name=lambda: "").push(None, SyncService(source, hub_model_name=lambda: "").pull(None))
    copied = peer.refinement_thoughts.get(thought["id"])
    assert copied["working_revision"] == 3
    assert [x["revision"] for x in peer.refinement_thoughts.revisions(thought["id"])] == [1, 2, 3]
    assert peer.notes.get(copied["working_note_id"]).body_markdown == "three"


def test_lifecycle_command_cas_refuses_completed_edits_until_resume_and_dtos_carry_cursors(db):
    service = RefinementThoughtService(db)
    thought = _create(db)
    assert {"aggregate_revision", "lifecycle_revision", "working_revision", "attachment_revision"} <= thought.keys()
    completed = service.complete(OWNER, thought["id"], expected_aggregate_revision=1, expected_lifecycle_revision=1)
    assert completed["state"] == "completed" and completed["aggregate_revision"] == 2 and completed["lifecycle_revision"] == 2
    with pytest.raises(ConflictError) as blocked:
        service.update_working(OWNER, thought["id"], expected_aggregate_revision=2, expected_working_revision=1, body_markdown="must wait")
    assert blocked.value.code == "thought_completed"
    resumed = service.resume(OWNER, thought["id"], expected_aggregate_revision=2, expected_lifecycle_revision=2)
    assert resumed["state"] == "working" and resumed["aggregate_revision"] == 3 and resumed["lifecycle_revision"] == 3
    assert service.update_working(OWNER, thought["id"], expected_aggregate_revision=3, expected_working_revision=1, body_markdown="now edit")["working_revision"] == 2


def test_unfinished_page_is_bounded_private_and_cursor_signed(db):
    service = RefinementThoughtService(db)
    first = _create(db)
    second = service.create(OWNER, request_id="capture-2", raw_text="another private raw", source={"kind": "typed"})
    page = service.list_unfinished(OWNER, limit=1)
    assert len(page["items"]) == 1 and page["next_cursor"]
    item = page["items"][0]
    assert {"aggregate_revision", "lifecycle_revision", "working_revision", "attachment_revision"} <= item.keys()
    assert item["source_kind"] == "typed" and item["body_preview"] == "another private raw" and item["updated_at"]
    assert not ({"body_markdown", "raw_text", "raw_sha256", "source", "continuity"} & item.keys())
    next_page = service.list_unfinished(OWNER, limit=1, cursor=page["next_cursor"])
    assert {item["id"], next_page["items"][0]["id"]} == {first["id"], second["id"]}
    assert page["items"][0]["id"] == second["id"]  # same-second timestamps still order by monotonic resume order
    with pytest.raises(ValidationError) as invalid:
        service.list_unfinished(OWNER, limit=1, cursor=page["next_cursor"] + "forged")
    assert invalid.value.code == "thought_cursor_invalid"


def test_reservation_is_idempotent_one_live_and_attempt_hook_fences_stale_thought(db):
    service = RefinementThoughtService(db)
    thought = _create(db)
    reserved = service.reserve_refinement(OWNER, thought["id"], request_id="refine-1", expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0)
    assert reserved["attempts"] == [{"attempt_ordinal": 1, "ask_invocation_id": reserved["attempts"][0]["ask_invocation_id"], "state": "reserved"}]
    assert service.reserve_refinement(OWNER, thought["id"], request_id="refine-1", expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0)["id"] == reserved["id"]
    with pytest.raises(ConflictError) as live:
        service.reserve_refinement(OWNER, thought["id"], request_id="refine-2", expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0)
    assert live.value.code == "refinement_already_live"
    service.update_working(OWNER, thought["id"], expected_aggregate_revision=1, expected_working_revision=1, body_markdown="changed")
    with pytest.raises(ValidationError) as stale:
        service.before_physical_dispatch(reserved["id"])("op_test", reserved["attempts"][0]["ask_invocation_id"], 1)
    assert stale.value.code == "refinement_result_stale"
    assert service.reconcile(OWNER, thought["id"], expected_aggregate_revision=2, invocation_id=reserved["id"])["continuity"]["state"] == "stale"
    assert service.reserve_refinement(OWNER, thought["id"], request_id="refine-after-stale", expected_aggregate_revision=2, expected_working_revision=2, expected_attachment_revision=0)["state"] == "reserved"


def test_reconcile_links_only_receipt_gated_matching_attempt(db):
    service = RefinementThoughtService(db)
    thought = _create(db)
    reserved = service.reserve_refinement(OWNER, thought["id"], request_id="refine-success", expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0)
    ask_id = reserved["attempts"][0]["ask_invocation_id"]
    service.before_physical_dispatch(reserved["id"])("op_refine", ask_id, 1)
    with db._connection() as conn:
        conn.execute("""INSERT INTO kernel_operations(operation_id,request_id,idempotency_key,name,version,principal_kind,principal_identity,target_ref,placement,envelope_sha256,policy_version,authority_basis,state,revision,native_id,parent_operation_id,correlation_id,delegator_kind,delegator_identity,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", ("op_refine","req","idem","inference.invoke",1,"owner","test-owner","invocation:"+ask_id,"node:test","sha256:x","v","test","succeeded",1,ask_id,"","","","",1.0,1.0))
        conn.execute("INSERT INTO kernel_receipts(receipt_id,operation_id,state,outcome,result_ref,created_at) VALUES(?,?,?,?,?,?)", ("rcpt_refine","op_refine","succeeded","succeeded","projection-stage:pstg_refine",1.0))
        conn.execute("INSERT INTO kernel_projection_stages(stage_id,invocation_id,operation_id,kind,projection_json,projection_sha256,result_ref,state,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)", ("pstg_refine",ask_id,"op_refine","ask-result","{}","sha256:x","projection-stage:pstg_refine","PUBLISHED",1.0,1.0))
        conn.execute("INSERT INTO ask_results(projection_stage_id,invocation_id,operation_id,receipt_id,payload_json,created_at) VALUES(?,?,?,?,?,?)", ("pstg_refine",ask_id,"op_refine","rcpt_refine",'{"output":"answer"}',1.0))
    loaded = service.reconcile(OWNER, thought["id"], expected_aggregate_revision=1, invocation_id=reserved["id"])
    assert loaded["continuity"]["state"] == "review_ready"
    assert loaded["continuity"]["review_result_id"]
    assert service.reconcile(OWNER, thought["id"], expected_aggregate_revision=1, invocation_id=reserved["id"])["continuity"]["review_result_id"] == loaded["continuity"]["review_result_id"]
    assert db.notes.get(thought["working_note"]["id"]).body_markdown == "raw\nbytes"


def test_restart_after_retry_plan_before_child_admission_is_terminal_and_releasable(db):
    service = RefinementThoughtService(db)
    thought = _create(db)
    reserved = service.reserve_refinement(OWNER, thought["id"], request_id="retry-crash", expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0)
    base_ask = reserved["attempts"][0]["ask_invocation_id"]
    service.before_physical_dispatch(reserved["id"])("op_retry_base", base_ask, 1)
    with db._connection() as conn:
        conn.execute("""INSERT INTO kernel_operations(operation_id,request_id,idempotency_key,name,version,principal_kind,principal_identity,target_ref,placement,envelope_sha256,policy_version,authority_basis,state,revision,native_id,parent_operation_id,correlation_id,delegator_kind,delegator_identity,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", ("op_retry_base","req","idem-retry","inference.invoke",1,"owner","test-owner","invocation:"+base_ask,"node:test","sha256:x","v","test","failed",1,base_ask,"","","","",1.0,1.0))
        conn.execute("INSERT INTO kernel_receipts(receipt_id,operation_id,state,outcome,result_ref,created_at) VALUES(?,?,?,?,?,?)", ("rcpt_retry_base","op_retry_base","failed","failed","",1.0))
    child_ask = retry_invocation_id(base_ask, 2)
    service.before_compatibility_retry(reserved["id"])("op_retry_base", base_ask, child_ask, 2, "dialect")
    path = db.db_path
    db.close()
    restarted = Database(path)
    recovered = RefinementThoughtService(restarted).reconcile(OWNER, thought["id"], expected_aggregate_revision=1, invocation_id=reserved["id"])
    assert recovered["continuity"]["state"] == "named_failure"
    assert recovered["continuity"]["code"] == "retry_child_missing_after_plan"
    assert RefinementThoughtService(restarted).reserve_refinement(OWNER, thought["id"], request_id="retry-after-crash", expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0)["state"] == "reserved"


def test_two_peer_same_content_completion_fast_forwards_aggregate_command_suffix(tmp_path):
    source, peer = Database(tmp_path / "complete-source.db"), Database(tmp_path / "complete-peer.db")
    for database in (source, peer):
        database.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    service = RefinementThoughtService(source)
    thought = service.create(OWNER, request_id="same-content", raw_text="raw", source={"kind": "typed"})
    SyncService(peer, hub_model_name=lambda: "").push(None, SyncService(source, hub_model_name=lambda: "").pull(None))
    service.complete(OWNER, thought["id"], expected_aggregate_revision=1, expected_lifecycle_revision=1)
    packet = SyncService(source, hub_model_name=lambda: "").pull(None)
    SyncService(peer, hub_model_name=lambda: "").push(None, packet)
    copied = peer.refinement_thoughts.get(thought["id"])
    assert copied["state"] == "completed" and copied["working_revision"] == 1
    assert copied["aggregate_revision"] == 2 and copied["lifecycle_revision"] == 2
    assert [x["command_kind"] for x in peer.refinement_thoughts.commands(thought["id"])] == ["create", "complete"]


def test_sync_rejects_noncanonical_lifecycle_entry_before_install(tmp_path):
    source, peer = Database(tmp_path / "hash-source.db"), Database(tmp_path / "hash-peer.db")
    for database in (source, peer):
        database.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    thought = RefinementThoughtService(source).create(OWNER, request_id="hash", raw_text="raw", source={"kind": "typed"})
    packet = SyncService(source, hub_model_name=lambda: "").pull(None)
    packet["refinement_thoughts"][0]["value"]["lifecycle"][0]["entry_sha256"] = "0" * 64
    with pytest.raises(ValidationError) as rejected:
        SyncService(peer, hub_model_name=lambda: "").push(None, packet)
    assert rejected.value.code == "thought_lifecycle_hash_mismatch"
    assert peer.refinement_thoughts.get(thought["id"]) is None


def test_sync_rejects_forged_command_prior_and_tombstone_fence_is_absolute(tmp_path):
    source, peer, fenced = (Database(tmp_path / name) for name in ("prior-source.db", "prior-peer.db", "prior-fenced.db"))
    for database in (source, peer, fenced):
        database.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    service = RefinementThoughtService(source)
    thought = service.create(OWNER, request_id="prior", raw_text="raw", source={"kind": "typed"})
    live = SyncService(source, hub_model_name=lambda: "").pull(None)
    forged = copy.deepcopy(live)
    forged["refinement_thoughts"][0]["value"]["commands"][0]["prior_working_revision"] = 999
    with pytest.raises(ValidationError) as refused:
        SyncService(peer, hub_model_name=lambda: "").push(None, forged)
    assert refused.value.code == "thought_revision_history_invalid" and peer.refinement_thoughts.get(thought["id"]) is None
    service.tombstone_note(OWNER, thought["working_note"]["id"], expected_aggregate_revision=1, expected_lifecycle_revision=1)
    tomb = SyncService(source, hub_model_name=lambda: "").pull(None)
    applied = SyncService(fenced, hub_model_name=lambda: "").push(None, tomb)
    assert applied["received"]["refinement_thoughts"] == 1
    assert applied["received"]["notes"] == 0 and applied["received"]["directory_memberships"] == 0
    assert fenced.notes.get(thought["working_note"]["id"], include_deleted=True) is None
    assert fenced.directory_memberships.get(f"note:{thought['working_note']['id']}", include_deleted=True) is None
    replay = SyncService(fenced, hub_model_name=lambda: "").push(None, tomb)
    assert replay["received"]["refinement_thoughts"] == 1
    assert replay["received"]["notes"] == 0 and replay["received"]["directory_memberships"] == 0
    delayed = {"directory_memberships": [{"meta": {"id": f"note:{thought['working_note']['id']}", "kind": "directory_membership", "last_modified": "2099-01-01T00:00:00Z", "deleted": False}, "value": {"directory_id": INBOX_DIRECTORY_ID}}]}
    with pytest.raises(ConflictError) as fenced_member:
        SyncService(fenced, hub_model_name=lambda: "").push(None, delayed)
    assert fenced_member.value.code == "thought_tombstoned"
    with pytest.raises(ConflictError):
        SyncService(fenced, hub_model_name=lambda: "").push(None, live)
