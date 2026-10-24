"""A selected Thought Note is checked once and held for its Ask turn."""
from __future__ import annotations

import asyncio
import hashlib
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.memory.retain import sweep
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.ask_service import AskService, _pinned_note
from holdspeak.services import ask_desk
from holdspeak.services.errors import ServiceError, ValidationError
from holdspeak.services.refinement_thought_service import INBOX_DIRECTORY_ID, RefinementThoughtService
from holdspeak.services.thread_service import ThreadService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.primitives.ask import build_ask_router
from tests.unit.test_thread_service import FakeAdoptionService


OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture
def selected(tmp_path):
    db = Database(tmp_path / "pinned.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    thought = RefinementThoughtService(db).create(
        OWNER, request_id="capture-pin", raw_text="OLD BODY", source={"kind": "typed"},
    )
    note_id = thought["working_note"]["id"]
    note = db.notes.get(note_id)
    snapshot = {
        "ref": f"note:{note_id}", "thought_id": thought["id"],
        "working_revision": thought["working_revision"],
        "body_sha256": hashlib.sha256(note.body_markdown.encode()).hexdigest(),
    }
    return db, thought, snapshot


def test_snapshot_checks_shape_owner_revision_and_raw_body(selected):
    db, thought, snapshot = selected
    assert _pinned_note(db, snapshot)["body"] == db.notes.get(thought["working_note"]["id"]).body_markdown
    with pytest.raises(ValidationError) as invalid:
        _pinned_note(db, {**snapshot, "working_revision": True})
    assert invalid.value.code == "source_snapshot_invalid"
    with pytest.raises(ServiceError) as owner:
        _pinned_note(db, {**snapshot, "thought_id": "other"})
    assert owner.value.code == "source_gone"
    with pytest.raises(ServiceError) as changed:
        _pinned_note(db, {**snapshot, "body_sha256": "0" * 64})
    assert changed.value.code == "source_changed"
    RefinementThoughtService(db).update_working(
        OWNER, thought["id"], expected_aggregate_revision=1,
        expected_working_revision=1, title="New title", tags=["new"],
    )
    with pytest.raises(ServiceError) as revised:
        _pinned_note(db, snapshot)
    assert revised.value.code == "source_changed"
    with pytest.raises(ServiceError) as preflight:
        asyncio.run(AskService(db).ask(OWNER, "Question", source_snapshot=snapshot))
    assert preflight.value.code == "source_changed"


def test_tombstone_refuses_before_material(selected):
    db, thought, snapshot = selected
    with db._connection() as conn:
        conn.execute("UPDATE notes SET deleted=1 WHERE id=?", (thought["working_note"]["id"],))
    with pytest.raises(ServiceError) as gone:
        _pinned_note(db, snapshot)
    assert gone.value.code == "source_gone"


def test_normal_material_and_grounding_use_one_prepared_version(selected):
    db, thought, snapshot = selected
    service = AskService(db)
    prepared = _pinned_note(db, snapshot)
    note_id = prepared["id"]
    # A writer edits after admission. No later read of this selected Note is allowed.
    RefinementThoughtService(db).update_working(
        OWNER, thought["id"], expected_aggregate_revision=1,
        expected_working_revision=1, body_markdown="NEW BODY", title="New title",
    )
    material, ids, _ = service._assemble_material(
        [{"id": note_id, "kind": "note", "title": "old"}], pinned_note=prepared,
    )
    assert "OLD BODY" in material and "NEW BODY" not in material and ids == [note_id]
    db.notes.upsert(note_id="other", title="Other source", body_markdown="OTHER BODY")
    envelope, echo = service._grounding(
        OWNER, {"refs": [snapshot["ref"], "note:other"]}, "question", pinned_note=prepared,
    )
    assert "OLD BODY" in envelope and "NEW BODY" not in envelope
    assert "OTHER BODY" in envelope
    assert {snapshot["ref"], "note:other"} <= set(echo["source_refs"])
    assert echo["matched_count"] == 2


def test_selected_note_defense_covers_both_material_channels(selected):
    db, thought, _ = selected
    secret = "sk-" + "a" * 24
    updated = RefinementThoughtService(db).update_working(
        OWNER, thought["id"], expected_aggregate_revision=1,
        expected_working_revision=1, body_markdown=f"OLD BODY {secret}",
    )
    note_id = thought["working_note"]["id"]
    snapshot = {"ref": f"note:{note_id}", "thought_id": thought["id"],
                "working_revision": updated["working_revision"],
                "body_sha256": hashlib.sha256(f"OLD BODY {secret}".encode()).hexdigest()}
    pinned = _pinned_note(db, snapshot)
    service = AskService(db)
    material, _, _ = service._assemble_material(
        [{"id": note_id, "kind": "note"}], pinned_note=pinned,
    )
    grounded, _ = service._grounding(OWNER, {"refs": [snapshot["ref"]]},
                                      "question", pinned_note=pinned)
    assert secret not in material and secret not in grounded
    assert "[redacted]" in material and "[redacted]" in grounded


class _CaptureEngine:
    active_provider = "openai_compatible"

    def __init__(self):
        self.prompts = []

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        self.prompts.append(user_prompt)
        return "Pinned answer"


@pytest.mark.parametrize("mode", ["normal", "cli"])
def test_normal_and_cli_dispatch_the_admitted_note(selected, monkeypatch, mode):
    db, thought, snapshot = selected
    db.profiles.upsert(profile_id="pin-engine", name="Pin", kind="openAICompatible",
                       base_url="http://192.168.1.50:8080", model="pin-model", requires_key=False)
    broker = _configure(db)
    engine = _CaptureEngine()
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda *_a, **_k: engine)
    service = AskService(db, broker=broker)
    edited = False
    def change_after_admission(*_args):
        nonlocal edited
        if not edited:
            edited = True
            RefinementThoughtService(db).update_working(
                OWNER, thought["id"], expected_aggregate_revision=1,
                expected_working_revision=1, title="Changed", body_markdown="NEW BODY",
            )
    if mode == "normal":
        result = asyncio.run(service.ask(
            OWNER, "Question", {"refs": [snapshot["ref"]]}, source_snapshot=snapshot,
            inference_target_id="pin-engine", before_physical_dispatch=change_after_admission,
        ))
    else:
        monkeypatch.setattr(ask_desk, "tools_mode", lambda _db: ask_desk.CLI)
        # CLI's request is still an AskService call; a mutation after the
        # snapshot read cannot change the prepared bytes.
        original = service.ask
        async def dispatch(*args, **kwargs):
            kwargs["inference_target_id"] = "pin-engine"
            kwargs["before_physical_dispatch"] = change_after_admission
            return await original(*args, **kwargs)
        monkeypatch.setattr(service, "ask", dispatch)
        result = asyncio.run(service.ask_in_thread(
            OWNER, "Question", {"refs": [snapshot["ref"]]}, source_snapshot=snapshot,
        ))
    assert result["output"] == "Pinned answer"
    assert edited and len(engine.prompts) == 1
    assert "OLD BODY" in engine.prompts[0] and "NEW BODY" not in engine.prompts[0]


def test_http_passes_snapshot_and_names_source_changed(selected, monkeypatch):
    db, thought, snapshot = selected
    RefinementThoughtService(db).update_working(
        OWNER, thought["id"], expected_aggregate_revision=1,
        expected_working_revision=1, title="Changed title",
    )
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    app.include_router(build_ask_router(WebContext(get_state=lambda: {})))
    response = TestClient(app).post("/api/ask", json={"prompt": "Question",
        "grounding": {"refs": [snapshot["ref"]]}, "source_snapshot": snapshot})
    assert response.status_code == 409
    assert response.json()["reason"] == "source_changed"


def test_loop_dispatch_keeps_selected_body_after_admission(selected, monkeypatch):
    db, thought, snapshot = selected
    class CaptureAdoption(FakeAdoptionService):
        def __init__(self):
            super().__init__(output="Pinned answer")
            self.payloads = []
        def admit(self, principal, **kwargs):
            self.payloads.append(kwargs["payload"])
            admitted = super().admit(principal, **kwargs)
            RefinementThoughtService(db).update_working(
                OWNER, thought["id"], expected_aggregate_revision=1,
                expected_working_revision=1, body_markdown="NEW BODY",
            )
            return admitted
    adoption = CaptureAdoption()
    class Broker:
        inference_adoption_service = adoption
    service = AskService(db, thread_service=lambda **kw: ThreadService(
        db, broadcast=lambda *_: None, broker=Broker(), **kw))
    monkeypatch.setattr(ask_desk, "tools_mode", lambda _db: ask_desk.LOOP)
    result = asyncio.run(service.ask_in_thread(
        OWNER, "Question", {"refs": [snapshot["ref"]]}, source_snapshot=snapshot))
    assert result["output"] == "Pinned answer"
    assert len(adoption.payloads) == 1
    payload = json.dumps(adoption.payloads[0])
    assert "OLD BODY" in payload and "NEW BODY" not in payload


def test_loop_current_pin_keeps_frozen_body_older_turn_replays_live(selected):
    db, thought, snapshot = selected
    prepared = _pinned_note(db, snapshot)
    thread_id = db.threads.create_thread(title="Ask").id
    user = db.threads.append_message(thread_id, role="user")
    db.threads.append_part(user.id, kind="text", text="Question")
    db.threads.freeze_refs(thread_id, user.id, [{
        "ref_kind": "note", "ref_id": prepared["id"], "origin": "reference",
        "frozen_json": {"kind": "note", "title": prepared["title"], "text": prepared["body"],
                        "via": "", "ask_pinned": True},
    }])
    service = ThreadService(db, broadcast=lambda *_: None)
    current = service._assemble_payload(thread_id, user.id, db.threads.get(thread_id))
    assert "OLD BODY" in json.dumps(current)
    RefinementThoughtService(db).update_working(
        OWNER, thought["id"], expected_aggregate_revision=1,
        expected_working_revision=1, body_markdown="NEW BODY",
    )
    still_current = service._assemble_payload(thread_id, user.id, db.threads.get(thread_id))
    assert "OLD BODY" in json.dumps(still_current) and "NEW BODY" not in json.dumps(still_current)
    next_user = db.threads.append_message(thread_id, role="user", parent_id=user.id)
    db.threads.append_part(next_user.id, kind="text", text="Next")
    older = service._assemble_payload(thread_id, next_user.id, db.threads.get(thread_id))
    assert "NEW BODY" in json.dumps(older) and "OLD BODY" not in json.dumps(older)


def test_loop_deletion_gap_parks_unsent_user_turn(selected, monkeypatch):
    db, thought, snapshot = selected
    prepared = _pinned_note(db, snapshot)
    service = ThreadService(db, broadcast=lambda *_: None)
    thread_id = db.threads.create_thread(title="Ask").id
    def vanish(*args, **kwargs):
        with db._connection() as conn:
            conn.execute("UPDATE notes SET deleted=1 WHERE id=?", (prepared["id"],))
        return original(*args, **kwargs)
    original = service._assemble_payload
    monkeypatch.setattr(service, "_assemble_payload", vanish)
    with pytest.raises(ServiceError) as gone:
        asyncio.run(service.start_turn(OWNER, thread_id, "Question", refs=[snapshot["ref"]],
                                       pinned_note=prepared))
    assert gone.value.code == "source_gone"
    assert db.threads.list_path(thread_id) == []
    with db._connection() as conn:
        row = conn.execute("SELECT aborted_at, deleted_at FROM thread_messages WHERE thread_id=?", (thread_id,)).fetchone()
    assert row["aborted_at"] is not None and row["deleted_at"] is not None


def test_loop_deletion_during_memory_fit_still_refuses(selected, monkeypatch):
    db, _, snapshot = selected
    prepared = _pinned_note(db, snapshot)
    service = ThreadService(db, broadcast=lambda *_: None)
    thread_id = db.threads.create_thread(title="Ask").id
    def fit_then_vanish(payload, *_args, **_kwargs):
        with db._connection() as conn:
            conn.execute("UPDATE notes SET deleted=1 WHERE id=?", (prepared["id"],))
        return payload, None
    monkeypatch.setattr(service, "_with_reflect", fit_then_vanish)
    with pytest.raises(ServiceError) as gone:
        asyncio.run(service.start_turn(OWNER, thread_id, "Question", refs=[snapshot["ref"]],
                                       pinned_note=prepared))
    assert gone.value.code == "source_gone"
    assert db.threads.list_path(thread_id) == []


def _containing_ref(db, pinned_ref: str, kind: str) -> str:
    db.notes.upsert(note_id="other", title="Other", body_markdown="OTHER BODY")
    if kind in {"knowledge", "project_knowledge"}:
        db.kbs.upsert(kb_id="selected-kb", name="Selected KB",
                      member_ids=[pinned_ref, "note:other"])
        if kind == "project_knowledge":
            db.projects.create_project(project_id="selected-project", name="Selected Project")
            db.project_relationships.upsert(project_id="selected-project",
                                            resource_ref="knowledge:selected-kb")
            return "project:selected-project"
        return "knowledge:selected-kb"
    db.directories.upsert(directory_id="selected-zone", name="Selected Zone")
    db.directory_memberships.upsert(primitive_id=pinned_ref, directory_id="selected-zone")
    db.directory_memberships.upsert(primitive_id="note:other", directory_id="selected-zone")
    if kind == "knowledge_zone":
        db.kbs.upsert(kb_id="selected-kb", name="Selected KB",
                      member_ids=["zone:selected-zone"])
        return "knowledge:selected-kb"
    return "zone:selected-zone"


@pytest.mark.parametrize("container", ["knowledge", "zone", "knowledge_zone", "project_knowledge"])
def test_normal_container_does_not_reread_selected_note(selected, monkeypatch, container):
    db, thought, snapshot = selected
    containing_ref = _containing_ref(db, snapshot["ref"], container)
    db.profiles.upsert(profile_id="pin-engine", name="Pin", kind="openAICompatible",
                       base_url="http://192.168.1.50:8080", model="pin-model", requires_key=False)
    broker = _configure(db)
    if container == "project_knowledge":
        # An index-free hub uses the project's supported recency member path.
        db.memory = None
    engine = _CaptureEngine()
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda *_a, **_k: engine)
    service = AskService(db, broker=broker)
    original = service._grounding
    def edit_before_container_hydration(*args, **kwargs):
        RefinementThoughtService(db).update_working(
            OWNER, thought["id"], expected_aggregate_revision=1,
            expected_working_revision=1, body_markdown="NEW BODY",
        )
        return original(*args, **kwargs)
    monkeypatch.setattr(service, "_grounding", edit_before_container_hydration)
    result = asyncio.run(service.ask(
        OWNER, "Question", {"refs": [snapshot["ref"], containing_ref]},
        source_snapshot=snapshot, inference_target_id="pin-engine",
    ))
    assert result["output"] == "Pinned answer"
    prompt = engine.prompts[0]
    assert "OLD BODY" in prompt and "OTHER BODY" in prompt and "NEW BODY" not in prompt


@pytest.mark.parametrize("container", ["knowledge", "zone", "knowledge_zone", "project_knowledge"])
def test_loop_container_does_not_reread_selected_note(selected, monkeypatch, container):
    db, thought, snapshot = selected
    containing_ref = _containing_ref(db, snapshot["ref"], container)
    if container == "project_knowledge":
        db.memory = None
    class CaptureAdoption(FakeAdoptionService):
        def __init__(self):
            super().__init__(output="Pinned answer")
            self.payloads = []
        def admit(self, principal, **kwargs):
            self.payloads.append(kwargs["payload"])
            return super().admit(principal, **kwargs)
    adoption = CaptureAdoption()
    class Broker:
        inference_adoption_service = adoption
    service = AskService(db, thread_service=lambda **kw: ThreadService(
        db, broadcast=lambda *_: None, broker=Broker(), **kw))
    monkeypatch.setattr(ask_desk, "tools_mode", lambda _db: ask_desk.LOOP)
    original = ask_desk.run_loop
    async def edit_before_start_turn(*args, **kwargs):
        RefinementThoughtService(db).update_working(
            OWNER, thought["id"], expected_aggregate_revision=1,
            expected_working_revision=1, body_markdown="NEW BODY",
        )
        return await original(*args, **kwargs)
    monkeypatch.setattr(ask_desk, "run_loop", edit_before_start_turn)
    result = asyncio.run(service.ask_in_thread(
        OWNER, "Question", {"refs": [snapshot["ref"], containing_ref]},
        source_snapshot=snapshot,
    ))
    assert result["output"] == "Pinned answer"
    prompt = json.dumps(adoption.payloads[0])
    assert "OLD BODY" in prompt and "OTHER BODY" in prompt and "NEW BODY" not in prompt


def _change_with_unrelated_memory(db, thought, snapshot):
    RefinementThoughtService(db).update_working(
        OWNER, thought["id"], expected_aggregate_revision=1,
        expected_working_revision=1, body_markdown="NEW BODY Atlas review",
    )
    db.notes.upsert(note_id="other-memory", title="Atlas review",
                    body_markdown="UNRELATED MEMORY Atlas review is Friday")
    sweep(db)
    hits = db.memory.search("Atlas review", exclude_refs=[snapshot["ref"]]).hits
    assert any(hit.source_ref == "note:other-memory" for hit in hits)


@pytest.mark.parametrize("mode", ["normal", "cli"])
@pytest.mark.parametrize("source_mode", ["snapshot_only", "context_note", "grounding_ref"])
def test_normal_and_cli_keep_original_memory_decision(selected, monkeypatch, mode, source_mode):
    db, thought, snapshot = selected
    db.profiles.upsert(profile_id="pin-engine", name="Pin", kind="openAICompatible",
                       base_url="http://192.168.1.50:8080", model="pin-model", requires_key=False)
    broker = _configure(db)
    engine = _CaptureEngine()
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda *_a, **_k: engine)
    service = AskService(db, broker=broker)
    original_grounding = service._grounding
    def change_after_snapshot(*args, **kwargs):
        _change_with_unrelated_memory(db, thought, snapshot)
        return original_grounding(*args, **kwargs)
    monkeypatch.setattr(service, "_grounding", change_after_snapshot)
    grounding = {"refs": [snapshot["ref"]]} if source_mode == "grounding_ref" else None
    context = ([{"id": snapshot["ref"][5:], "kind": "note", "ref": snapshot["ref"],
                "title": "First thought"}] if source_mode == "context_note" else None)
    if mode == "normal":
        result = asyncio.run(service.ask(
            OWNER, "Atlas review", grounding, context=context, source_snapshot=snapshot,
            inference_target_id="pin-engine",
        ))
    else:
        monkeypatch.setattr(ask_desk, "tools_mode", lambda _db: ask_desk.CLI)
        original_ask = service.ask
        async def dispatch(*args, **kwargs):
            kwargs["inference_target_id"] = "pin-engine"
            return await original_ask(*args, **kwargs)
        monkeypatch.setattr(service, "ask", dispatch)
        result = asyncio.run(service.ask_in_thread(
            OWNER, "Atlas review", grounding, context=context, source_snapshot=snapshot,
        ))
    assert result["output"] == "Pinned answer"
    prompt = engine.prompts[0]
    assert "OLD BODY" in prompt
    assert ("UNRELATED MEMORY" in prompt) is (source_mode != "grounding_ref")
    assert "NEW BODY" not in prompt


@pytest.mark.parametrize("source_mode", ["snapshot_only", "context_note", "grounding_ref"])
def test_loop_keeps_original_memory_decision_and_looked_at(selected, monkeypatch, source_mode):
    db, thought, snapshot = selected
    class CaptureAdoption(FakeAdoptionService):
        def __init__(self):
            super().__init__(output="Pinned answer")
            self.payloads = []
        def admit(self, principal, **kwargs):
            self.payloads.append(kwargs["payload"])
            return super().admit(principal, **kwargs)
    adoption = CaptureAdoption()
    class Broker:
        inference_adoption_service = adoption
    service = AskService(db, thread_service=lambda **kw: ThreadService(
        db, broadcast=lambda *_: None, broker=Broker(), **kw))
    monkeypatch.setattr(ask_desk, "tools_mode", lambda _db: ask_desk.LOOP)
    original_loop = ask_desk.run_loop
    async def change_after_snapshot(*args, **kwargs):
        _change_with_unrelated_memory(db, thought, snapshot)
        assert kwargs["refs"] == ([snapshot["ref"]] if source_mode != "snapshot_only" else [])
        return await original_loop(*args, **kwargs)
    monkeypatch.setattr(ask_desk, "run_loop", change_after_snapshot)
    grounding = {"refs": [snapshot["ref"]]} if source_mode == "grounding_ref" else None
    context = ([{"id": snapshot["ref"][5:], "kind": "note", "ref": snapshot["ref"],
                "title": "First thought"}] if source_mode == "context_note" else None)
    result = asyncio.run(service.ask_in_thread(
        OWNER, "Atlas review", grounding, context=context, source_snapshot=snapshot,
    ))
    assert result["output"] == "Pinned answer"
    prompt = json.dumps(adoption.payloads[0])
    assert "OLD BODY" in prompt
    assert ("UNRELATED MEMORY" in prompt) is (source_mode == "snapshot_only")
    assert "NEW BODY" not in prompt
    assert {row["ref"] for row in result["looked_at"]} >= {snapshot["ref"]}
