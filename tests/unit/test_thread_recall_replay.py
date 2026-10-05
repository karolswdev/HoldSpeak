"""A thread's saved recall is replayed only while its source is live.

A chat turn saves ("freezes") the recall it used in ``thread_refs``, and
every later turn of the thread sends those saved blocks to the model again.
The saved row is the receipt and stays as it was.  The text that goes to
the model is checked against the source on each turn
(``ThreadService._live_replay``):

* the source is gone (deleted, discarded) -> the block is not sent;
* memory selected the block (the desk relevance pass, or a ``project:``
  search) and memory now refuses the source (promoted, parked, a sensitive
  thread part) or the source left that project -> the block is not sent;
* the source text changed -> the live text is sent, never the saved text;
* nothing changed -> the saved bytes, the same prompt as main (fenced
  against main's recorded output, ``tests/fixtures/thread_recall_replay_main.json``).

A source the owner attached by hand follows the hand-attach rule: it is
sent while it exists (a promotion or a refile does not take it away),
redacted like every hydrated block, and it is never sent after it is
deleted.  A named Knowledge or Zone container
is rebuilt from its live members: a gone member is left out, the others
stay.

Rows main wrote (f5b65b7be, no ``via``): the desk relevance row is checked
as memory's, a container row by the hand-attach rule, and any other row is
not sent (main stamped a project's hits 'reference' like a named ref, so
neither rule can be checked).  Fenced with the rows main's producer wrote
(``tests/fixtures/thread_recall_replay_main_rows.json``).

A read tool result (``memory.search``, ``memory.observations``,
``memory.page``, and since 2026-10-05 every ``evidence_read`` or
``candidate_builder`` tool: a note read, a meeting, a People read) is
replayed on a later turn as a stub that says to read again; the stored
result stays as the receipt.

Every source is written by its real producer where one exists (the note
repository, the thread repository, project relationships).  The promotion
row is written direct, every column named, as the slice 1 and phase 200
tests write it (the interview service is its producer).  The turns run the
real hub, ThreadService and kernel broker; only the model leaf is replaced.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Optional

import pytest

from holdspeak.memory.retain import sweep

from tests.unit.test_memory_slice3_facts import _note
from tests.unit.test_memory_slice6_reflect import _turn, hub  # noqa: F401  (the fixture)

SECRET = "ZEPHYRREPLAY"
LIVE = "LIVEWORDREPLAY"
QUESTION = "What is the Atlas codename?"
FIXTURE = Path(__file__).parents[1] / "fixtures" / "thread_recall_replay_main.json"


def _promote(db: Any, ref: str) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO context_promotions(
                   promotion_id, thread_id, fact_id, source_message_id,
                   quote_sha256, quote_locator_json, target_kind, target_ref,
                   target_revision_label, target_content_sha256,
                   disclosure_state, request_sha256, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (f"cp-{ref}", "th-promote", "f1", "msg-1", "sha256:q", "{}", "note", ref,
             "2026-10-05T09:00:00Z", "sha256:c", "active", "sha256:r",
             "2026-10-05T09:00:00Z", "2026-10-05T09:00:00Z"),
        )


def _source(db: Any, mode: str, project: Optional[str]) -> tuple[str, Callable[[], None]]:
    """One source that holds ``SECRET``; returns its ref and the withdrawal."""
    if mode == "sensitive":
        thread = db.threads.create_thread(title="Planning")
        message = db.threads.append_message(thread.id, role="user")
        part = db.threads.append_part(message.id, kind="text", text=f"Atlas codename is {SECRET}.")
        if project:
            db.project_relationships.upsert(project_id=project, resource_ref=f"thread:{thread.id}")

        def withdraw() -> None:
            db.threads.append_part(message.id, kind="text", text=part.text, sensitive=True)
            db.threads.delete_part(part.id)

        return f"thread:{thread.id}", withdraw
    _note(db, "n-code", "Codename", f"Atlas codename is {SECRET}.")
    if project:
        db.project_relationships.upsert(project_id=project, resource_ref="note:n-code")

    def withdraw() -> None:
        if mode == "delete":
            db.notes.delete("n-code")
        elif mode == "edit":
            _note(db, "n-code", "Codename", f"Atlas codename is {LIVE}.")
        elif mode == "exclude":
            _promote(db, "note:n-code")
        elif mode == "refile":
            db.project_relationships.upsert(project_id="atlas", resource_ref="note:n-code", deleted=True)
            db.project_relationships.upsert(project_id="harbor", resource_ref="note:n-code")

    return "note:n-code", withdraw


def _two_turns(hub: Any, refs: Optional[list[str]], withdraw: Callable[[], None]) -> tuple[dict, dict]:
    sweep(hub.db)
    first = _turn(hub, QUESTION, refs=refs)
    assert first["outcome"] == "succeeded"
    assert SECRET in json.dumps(first["calls"][0])  # turn 1 recalled it
    frozen = "\n".join(r.frozen_json for r in hub.db.threads.get_refs(first["thread_id"]))
    assert SECRET in frozen  # and saved it
    withdraw()
    sweep(hub.db)
    second = _turn(hub, "Continue.", thread_id=first["thread_id"])
    assert second["outcome"] == "succeeded"
    # The receipt is kept: the saved rows still hold what turn 1 saw.
    assert frozen == "\n".join(r.frozen_json for r in hub.db.threads.get_refs(first["thread_id"])
                               if r.message_id == first["user_message_id"] or r.message_id is None)
    return first, second


def _sent(turn: dict) -> str:
    return json.dumps(turn["calls"][0])


# ── Memory selected it: the desk relevance pass, or a project search ─────

SELECTED = [
    ("desk", "delete"), ("desk", "edit"), ("desk", "exclude"), ("desk", "sensitive"),
    ("project", "delete"), ("project", "edit"), ("project", "exclude"),
    ("project", "refile"), ("project", "sensitive"),
]


@pytest.mark.parametrize(("scope", "mode"), SELECTED)
def test_a_withdrawn_recall_never_reaches_a_later_turn(hub, scope: str, mode: str) -> None:
    project = "atlas" if scope == "project" else None
    _ref, withdraw = _source(hub.db, mode, project)
    refs = ["project:atlas"] if project else None
    _first, second = _two_turns(hub, refs, withdraw)
    sent = _sent(second)
    assert SECRET not in sent
    if mode == "edit":
        assert LIVE in sent  # the live text, not the saved text


# ── He attached it by hand ──────────────────────────────────────────────

@pytest.mark.parametrize("mode", ["delete", "edit", "sensitive", "exclude", "refile"])
def test_a_hand_attached_source_follows_the_hand_attach_rule(hub, mode: str) -> None:
    ref, withdraw = _source(hub.db, mode, "atlas")
    _first, second = _two_turns(hub, [ref], withdraw)
    sent = _sent(second)
    if mode in ("delete", "edit", "sensitive"):
        assert SECRET not in sent  # gone or changed: never resurrected
    else:
        assert SECRET in sent  # attached on purpose: a promotion or a refile keeps it
    if mode == "edit":
        assert LIVE in sent


# ── Nothing withdrawn: the prompt is main's, byte for byte ───────────────

def _scenario(hub: Any, name: str) -> dict:
    db = hub.db
    _note(db, "n-desk", "Desk codename", "Atlas codename is DESKWORD. It uses token=hunter2SECRETVALUE.")
    _note(db, "n-atlas", "Atlas codename", "Atlas codename is ATLASWORD. It uses token=hunter2SECRETVALUE.")
    _note(db, "n-named", "Named", "Harbor launch is 2026-11-01.")
    db.project_relationships.upsert(project_id="atlas", resource_ref="note:n-atlas")
    other = db.threads.create_thread(title="Planning")
    message = db.threads.append_message(other.id, role="user")
    db.threads.append_part(message.id, kind="text", text="Atlas codename is THREADWORD.")
    sweep(db)
    refs = {"desk": None, "project": ["project:atlas", "note:n-named"]}[name]
    first = _turn(hub, QUESTION, refs=refs)
    second = _turn(hub, "Continue.", thread_id=first["thread_id"])
    adoption = hub.broker.inference_adoption_service
    out = {}
    for label, turn in (("first", first), ("second", second)):
        admitted = adoption.admitted_payload(str(db.threads.get_message(turn["assistant_message_id"]).operation_id))
        out[label] = {k: v for k, v in admitted.items() if k != "tools"}
    return out


@pytest.mark.parametrize("name", ["desk", "project"])
def test_with_nothing_withdrawn_the_later_turn_is_byte_identical_to_main(hub, name: str) -> None:
    if os.environ.get("HOLDSPEAK_RECORD_REPLAY_FIXTURE"):
        # Recorded with main's producer (f5b65b7be), never with this code.
        fixed = hub.svc.__class__
        hub.svc.__class__ = _main_thread_service()
        try:
            recorded = json.loads(FIXTURE.read_text()) if FIXTURE.exists() else {}
            recorded[name] = _scenario(hub, name)
            FIXTURE.write_text(json.dumps(recorded, indent=1, sort_keys=True) + "\n")
        finally:
            hub.svc.__class__ = fixed
        pytest.skip("recorded; run again without the variable to compare")
    got = _scenario(hub, name)
    main = json.loads(FIXTURE.read_text())[name]
    # The scenario recalls on turn 1 and replays on turn 2 (else the fence is empty).
    assert "Atlas codename is" in json.dumps(main["second"])
    # A memory-selected block is redacted, so the replay check reads the
    # source the way it was selected (memory defense on).
    assert "[redacted]" in json.dumps(main["second"]) and "hunter2SECRETVALUE" not in json.dumps(main)
    assert json.dumps(got, sort_keys=True) == json.dumps(main, sort_keys=True)


# ── Rows saved before the replay check: the f5b65b7be producer's rows ───
#
# ``tests/fixtures/thread_recall_replay_main_rows.json`` holds the
# ``thread_refs`` rows that main's own ``start_turn`` (f5b65b7be) wrote for
# three turns: the desk relevance pass, ``project:atlas`` + a named note, and
# a named Knowledge container.  ``test_record_the_main_rows`` re-records them
# (with HOLDSPEAK_RECORD_REPLAY_FIXTURE=1, on a checkout that has f5b65b7be).

MAIN_ROWS = Path(__file__).parents[1] / "fixtures" / "thread_recall_replay_main_rows.json"
CODE_BODY = f"Atlas codename is {SECRET}. It uses token=hunter2SECRETVALUE."


def _main_sources(db: Any, name: str) -> Optional[list[str]]:
    """The sources of the recorded turn, as the recorder made them."""
    _note(db, "n-code", "Codename", CODE_BODY)
    _note(db, "n-named", "Named", "Harbor launch is 2026-11-01.")
    if name == "project":
        db.project_relationships.upsert(project_id="atlas", resource_ref="note:n-code")
        return ["project:atlas", "note:n-named"]
    if name == "knowledge":
        _note(db, "n-two", "Second", "SURVIVORWORD still current.")
        db.kbs.upsert(kb_id="bundle", name="Bundle", member_ids=["note:n-code", "note:n-two"])
        return ["knowledge:bundle"]
    return None


def _thread_with_main_rows(hub: Any, name: str, origin: Optional[str] = None) -> str:
    """A thread whose turn 1 is the recorded one: the question, the answer,
    and the rows main's producer saved for it."""
    db = hub.db
    _main_sources(db, name)
    thread_id = hub.svc.create(title="Reflect")["id"]
    user = db.threads.append_message(thread_id, role="user")
    db.threads.append_part(user.id, kind="text", text=QUESTION)
    answer = db.threads.append_message(thread_id, role="assistant", parent_id=user.id)
    db.threads.append_part(answer.id, kind="text", text="OK")
    rows = json.loads(MAIN_ROWS.read_text())[name]["rows"]
    if origin is not None:  # a row written before the origin column: ''
        rows = [{**row, "origin": origin} for row in rows]
    db.threads.freeze_refs(thread_id, user.id, rows)
    return thread_id


def _main_thread_service() -> Any:
    """``ThreadService`` as main had it (f5b65b7be), with main's grounding.
    Used only to (re-)record the fixtures."""
    import subprocess
    import sys
    import types

    def module(path: str, name: str, package: str) -> Any:
        source = subprocess.check_output(["git", "show", "f5b65b7be:" + path], text=True)
        mod = types.ModuleType(name)
        mod.__package__ = package
        sys.modules[name] = mod
        exec(compile(source, "f5b65b7be:" + path, "exec"), mod.__dict__)
        return mod

    ground = module("holdspeak/grounding.py", "holdspeak._main_grounding", "holdspeak")
    thread = module("holdspeak/services/thread_service.py", "holdspeak.services._main_thread", "holdspeak.services")
    thread.hydrate_refs_detailed = ground.hydrate_refs_detailed
    return thread.ThreadService


@pytest.mark.parametrize("name", ["desk", "project", "knowledge"])
def test_record_the_main_rows(hub, name: str) -> None:
    """Re-record the fixture from the real f5b65b7be producer (opt-in)."""
    if not os.environ.get("HOLDSPEAK_RECORD_REPLAY_FIXTURE"):
        pytest.skip("set HOLDSPEAK_RECORD_REPLAY_FIXTURE=1 to re-record from f5b65b7be")
    refs = _main_sources(hub.db, name)
    sweep(hub.db)
    hub.svc.__class__ = _main_thread_service()
    first = _turn(hub, QUESTION, refs=refs)
    rows = [{"ref_kind": r.ref_kind, "ref_id": r.ref_id, "origin": r.origin, "frozen_json": r.frozen_json}
            for r in hub.db.threads.get_refs(first["thread_id"])]
    recorded = json.loads(MAIN_ROWS.read_text()) if MAIN_ROWS.exists() else {}
    recorded[name] = {"source": "f5b65b7be ThreadService.start_turn", "refs": refs, "rows": rows}
    MAIN_ROWS.write_text(json.dumps(recorded, indent=1, sort_keys=True) + "\n")


def test_the_recorded_rows_are_mains_shape() -> None:
    rows = json.loads(MAIN_ROWS.read_text())
    assert [r["origin"] for r in rows["desk"]["rows"]] == ["relevance"]
    # Main stamps a project's search hit 'reference', like a named note.
    assert [(r["ref_id"], r["origin"]) for r in rows["project"]["rows"]] == [
        ("n-code", "reference"), ("n-named", "reference")]
    assert [r["ref_kind"] for r in rows["knowledge"]["rows"]] == ["knowledge"]
    assert all("via" not in r["frozen_json"] for v in rows.values() for r in v["rows"])


@pytest.mark.parametrize("origin", ["relevance", ""])
@pytest.mark.parametrize("mode", ["none", "delete", "edit", "exclude"])
def test_a_main_desk_row_is_checked_as_memorys(hub, mode: str, origin: str) -> None:
    """Main's relevance row, and the same row with the UNKNOWN origin of a
    row written before the origin column (HS-200-10 keeps that replaying
    while it is unpromoted)."""
    thread_id = _thread_with_main_rows(hub, "desk", origin=origin or "")
    if mode == "delete":
        hub.db.notes.delete("n-code")
    elif mode == "edit":
        _note(hub.db, "n-code", "Codename", f"Atlas codename is {LIVE}. It uses token=hunter2SECRETVALUE.")
    elif mode == "exclude":
        _promote(hub.db, "note:n-code")
    sent = _sent(_turn(hub, "Continue.", thread_id=thread_id))
    assert "hunter2SECRETVALUE" not in sent
    if mode == "none":
        assert f"Atlas codename is {SECRET}. It uses [redacted]" in sent  # the saved bytes
    else:
        assert SECRET not in sent
    if mode == "edit":
        assert f"Atlas codename is {LIVE}. It uses [redacted]" in sent


@pytest.mark.parametrize("mode", ["none", "refile", "exclude", "delete"])
def test_a_main_project_row_is_never_replayed(hub, mode: str) -> None:
    """Main wrote the project hit and the named note alike ('reference', no
    record of the project), so neither the project scope nor the hand-attach
    rule can be checked: neither row is sent again."""
    thread_id = _thread_with_main_rows(hub, "project")
    if mode == "refile":
        hub.db.project_relationships.upsert(project_id="atlas", resource_ref="note:n-code", deleted=True)
        hub.db.project_relationships.upsert(project_id="harbor", resource_ref="note:n-code")
    elif mode == "exclude":
        _promote(hub.db, "note:n-code")
    elif mode == "delete":
        hub.db.notes.delete("n-code")
    sent = _sent(_turn(hub, "Continue.", thread_id=thread_id))
    assert SECRET not in sent
    assert "Harbor launch" not in sent


@pytest.mark.parametrize("mode", ["none", "delete", "edit"])
def test_a_main_container_row_follows_the_hand_attach_rule(hub, mode: str) -> None:
    thread_id = _thread_with_main_rows(hub, "knowledge")
    if mode == "delete":
        hub.db.notes.delete("n-code")
    elif mode == "edit":
        _note(hub.db, "n-code", "Codename", f"Atlas codename is {LIVE}.")
    sent = _sent(_turn(hub, "Continue.", thread_id=thread_id))
    assert "SURVIVORWORD still current." in sent  # the live member stays
    if mode == "none":
        # He attached it: sent while it exists, redacted (2026-10-05: a
        # source attached by hand is redacted too; main sent the key).
        assert f"Atlas codename is {SECRET}." in sent and "hunter2SECRETVALUE" not in sent
    else:
        assert SECRET not in sent
    if mode == "edit":
        assert LIVE in sent


# ── A named container keeps its live members ────────────────────────────

def _container(db: Any, kind: str, members: list[str]) -> str:
    if kind == "knowledge":
        db.kbs.upsert(kb_id="bundle", name="Bundle", member_ids=members)
    else:
        db.directories.upsert(directory_id="bundle", name="Bundle")
        for ref in members:
            db.directory_memberships.upsert(primitive_id=ref, directory_id="bundle")
    return f"{kind}:bundle"


@pytest.mark.parametrize("kind", ["knowledge", "zone"])
@pytest.mark.parametrize("mode", ["delete", "sensitive", "edit"])
def test_a_container_drops_only_its_withdrawn_member(hub, kind: str, mode: str) -> None:
    ref, withdraw = _source(hub.db, mode, None)
    _note(hub.db, "n-two", "Second", "SURVIVORWORD still current.")
    container = _container(hub.db, kind, [ref, "note:n-two"])
    first = _turn(hub, QUESTION, refs=[container])
    assert first["outcome"] == "succeeded" and SECRET in _sent(first)
    withdraw()
    second = _turn(hub, "Continue.", thread_id=first["thread_id"])
    sent = _sent(second)
    assert SECRET not in sent
    assert "SURVIVORWORD still current." in sent
    if mode == "edit":
        assert LIVE in sent


# ── Memory read tool results ────────────────────────────────────────────

def _cloud(hub: Any, thread_id: str) -> None:
    from tests.unit.test_thread_people_fence import _seed_profile

    _seed_profile(hub.db, "replay-cloud", boundary="external_service")
    hub.svc.patch(thread_id, profile_override="replay-cloud")


@pytest.mark.parametrize("route", ["local", "cloud"])
@pytest.mark.parametrize("mode", ["delete", "sensitive", "refile", "exclude"])
def test_a_memory_search_result_is_never_replayed_on_a_later_turn(hub, mode: str, route: str) -> None:
    """Astra's #852 repro: memory.search finds the source on turn 1, the
    source is withdrawn, "Continue." in the same thread.  Turn 2 gets a stub
    that says to search again; the tool record (the receipt) stays."""
    db = hub.db
    _ref, withdraw = _source(db, mode, "atlas")
    sweep(db)
    hub.engine.tool = ("memory.search", {"query": QUESTION, "project_id": "atlas"})
    first = _turn(hub, "Proceed.")
    assert first["outcome"] == "succeeded" and SECRET in json.dumps(first["calls"][-1])
    assert SECRET not in "\n".join(r.frozen_json for r in db.threads.get_refs(first["thread_id"]))
    withdraw()
    sweep(db)
    hub.engine.tool = None
    if route == "cloud":
        _cloud(hub, first["thread_id"])
    second = _turn(hub, "Continue.", thread_id=first["thread_id"])
    assert second["outcome"] == "succeeded"
    if route == "cloud":
        assert db.threads.get_message(second["assistant_message_id"]).egress_scope == "cloud"
    sent = second["calls"][0]
    assert not [m for m in sent if SECRET in str(m.get("content", ""))]
    assert any(m["role"] == "tool" and "Call memory.search again" in m["content"] for m in sent)
    kept = [part.text for message in db.threads.list_path(first["thread_id"]) if message.role == "tool"
            for part in db.threads.get_parts(message.id)]
    assert any(SECRET in str(text) for text in kept)  # the receipt is kept


def test_a_memory_observations_result_is_a_stub_on_a_later_turn(hub) -> None:
    hub.engine.tool = ("memory.observations", {"scope": "desk"})
    first = _turn(hub, "Proceed.")
    assert first["outcome"] == "succeeded"
    assert any(m.get("role") == "tool" for m in first["calls"][-1])
    hub.engine.tool = None
    second = _turn(hub, "Continue.", thread_id=first["thread_id"])
    assert any(m["role"] == "tool" and "Call memory.observations again" in m["content"]
               for m in second["calls"][0])


@pytest.mark.parametrize("mode", ["delete", "edit"])
def test_a_note_read_result_is_never_replayed_on_a_later_turn(hub, mode: str) -> None:
    """The open limit of #852: a tool that returns source text other than
    the memory reads (here ``desk.get`` on a note) replayed its saved result.
    Turn 2 gets a stub that says to read again; the receipt stays."""
    db = hub.db
    _ref, withdraw = _source(db, mode, None)
    hub.engine.tool = ("desk.get", {"kind": "notes", "id": "n-code"})
    first = _turn(hub, "Proceed.")
    assert first["outcome"] == "succeeded" and SECRET in json.dumps(first["calls"][-1])
    withdraw()
    hub.engine.tool = None
    second = _turn(hub, "Continue.", thread_id=first["thread_id"])
    assert second["outcome"] == "succeeded"
    sent = second["calls"][0]
    assert not [m for m in sent if SECRET in str(m.get("content", ""))]
    assert any(m["role"] == "tool" and "Call desk.get again" in m["content"] for m in sent)
    kept = [part.text for message in db.threads.list_path(first["thread_id"]) if message.role == "tool"
            for part in db.threads.get_parts(message.id)]
    assert any(SECRET in str(text) for text in kept)  # the receipt is kept


def test_every_read_tool_replays_as_a_stub_and_every_write_as_stored() -> None:
    """Census over the classification table: a read (evidence_read,
    candidate_builder) is a stub on replay; an effect_proposal result is
    replayed as stored; an unknown name fails closed."""
    from holdspeak.services.thread_service import _replay_stub
    from holdspeak.services.thread_tools import _ALL_TOOL_CLASSES

    for name, (kind, _sensitive) in _ALL_TOOL_CLASSES.items():
        stub = _replay_stub(name)
        if kind == "effect_proposal":
            assert stub is None, name
        else:
            assert stub is not None and f"Call {name} again" in stub, name
    assert _replay_stub("no.such.tool") is not None
    assert _replay_stub(None) is None and _replay_stub("") is None


def test_a_source_the_caller_holds_out_is_not_live_for_memory() -> None:
    """``live_block`` honours the turn's exclusions for what memory picked
    (the chat turn holds out its own thread and unkept drafts)."""
    from holdspeak.db import Database
    from holdspeak.grounding import live_block
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        db = Database(Path(tmp) / "x.db")
        _note(db, "n1", "One", "Body one.")
        assert live_block(db, "note:n1", via="memory").text == "Body one."
        assert live_block(db, "note:n1", via="memory", exclude_refs={"note:n1"}) is None
        # He named it: the hand-attach rule reads it whatever memory holds out.
        assert live_block(db, "note:n1", via="", exclude_refs={"note:n1"}).text == "Body one."
