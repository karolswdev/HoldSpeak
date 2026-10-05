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
sent while it exists (a promotion or a refile does not take it away), and
it is never sent after it is deleted.

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
    got = _scenario(hub, name)
    if os.environ.get("HOLDSPEAK_RECORD_REPLAY_FIXTURE"):
        recorded = json.loads(FIXTURE.read_text()) if FIXTURE.exists() else {}
        recorded[name] = got
        FIXTURE.write_text(json.dumps(recorded, indent=1, sort_keys=True) + "\n")
    main = json.loads(FIXTURE.read_text())[name]
    # The scenario recalls on turn 1 and replays on turn 2 (else the fence is empty).
    assert "Atlas codename is" in json.dumps(main["second"])
    # A memory-selected block is redacted, so the replay check reads the
    # source the way it was selected (memory defense on).
    assert "[redacted]" in json.dumps(main["second"]) and "hunter2SECRETVALUE" not in json.dumps(main)
    assert json.dumps(got, sort_keys=True) == json.dumps(main, sort_keys=True)


# ── Rows saved before the replay check (no "via" key) ───────────────────

def _strip_via(db: Any, thread_id: str) -> None:
    """Make this thread's saved rows look like rows main wrote."""
    with db._connection() as conn:
        for row_id, frozen in conn.execute(
            "SELECT id, frozen_json FROM thread_refs WHERE thread_id=? AND frozen_json!=''", (thread_id,)
        ).fetchall():
            value = json.loads(frozen)
            value.pop("via", None)
            conn.execute("UPDATE thread_refs SET frozen_json=? WHERE id=?",
                         (json.dumps(value, separators=(",", ":"), sort_keys=True), row_id))


@pytest.mark.parametrize("name", ["desk", "project"])
def test_a_row_saved_before_the_check_replays_as_main_and_never_unredacted(hub, name: str) -> None:
    db = hub.db
    _note(db, "n-code", "Codename", "Atlas codename is ATLASWORD. It uses token=hunter2SECRETVALUE.")
    if name == "project":
        db.project_relationships.upsert(project_id="atlas", resource_ref="note:n-code")
    sweep(db)
    first = _turn(hub, QUESTION, refs=["project:atlas"] if name == "project" else None)
    _strip_via(db, first["thread_id"])
    second = _turn(hub, "Continue.", thread_id=first["thread_id"])
    sent = _sent(second)
    assert "ATLASWORD. It uses [redacted]" in sent  # unchanged: the saved bytes
    assert "hunter2SECRETVALUE" not in sent
    db.notes.delete("n-code")
    third = _turn(hub, "Continue.", thread_id=first["thread_id"])
    assert "ATLASWORD" not in _sent(third)  # gone: not sent


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
