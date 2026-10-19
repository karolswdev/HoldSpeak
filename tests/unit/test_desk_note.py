"""The note app, hub half (Betterment Q8 "One note", docs/internal/betterment/asking/RECIPE.md).

A note is one thing with one window, the sticky. Every note opens there: the
hub gives the note's thought (``POST /api/thoughts/open-note``), adopting a
plain note and resuming a finished one, so no note needs a "Develop" press to
open. Opening, asking about or finishing a note never moves it to another
drawer. Ask ▸ Add to note appends an answer to the note through the note's own
thought write, and Undo puts it back.

The face half (the window, Add to note and Undo) is
``web/src/desk/pullouts/__tests__/note.app.test.tsx``; it replays the answers
this file records (``web/src/test/wire/note.one-note.wire.json``;
``HOLDSPEAK_WIRE_WRITE=1`` rewrites it). Every answer comes from the real hub
(MeetingWebServer through TestClient, isolated HOME and database).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from holdspeak.principals import Principal, PrincipalKind
from tests.unit.test_philo5_the_loop import hub  # noqa: F401  (fixture)

OWNER = Principal(PrincipalKind.OWNER, "note-owner")

WIRE = Path(__file__).resolve().parents[2] / "web" / "src" / "test" / "wire"
TITLE = "Jun and the cutover weekend"
BODY = ("Jun is nervous about the cutover weekend. Maybe pair him with Mira on call, "
        "and write the on-call handbook first.\nTheo could own the handbook.")
# The answer Add to note appends: the recorded Ask answer the face replays
# (ask.thread.wire.json, tests/unit/test_desk_ask.py), so the face's append
# and Undo meet the very bodies this hub recorded.
ANSWER = json.loads((WIRE / "ask.thread.wire.json").read_text())["first"]["output"]


def _ok(response: Any) -> Any:
    assert response.status_code in (200, 201), (response.request.url, response.status_code, response.text[:300])
    return response.json()


def _seed(hub: Any, *, drawer: bool = True) -> str:
    from holdspeak.services.primitive_service import PrimitiveService

    note = _ok(hub.client.post("/api/notes", json={"title": TITLE, "body_markdown": BODY, "tags": []}))["note"]
    if drawer:
        hub.db.directories.upsert(directory_id="d-work", name="Work")
        PrimitiveService(hub.db).file_member(OWNER, "d-work", f"note:{note['id']}")
    return str(note["id"])


def _drawer(hub: Any, note_id: str) -> str | None:
    member = hub.db.directory_memberships.get(f"note:{note_id}")
    return None if member is None else str(member.directory_id)


def test_a_plain_note_opens_in_the_sticky_with_no_develop_press(hub) -> None:
    note_id = _seed(hub)
    before = _ok(hub.client.get(f"/api/thoughts/for-note/{note_id}"))
    assert before["ownership"] == "ordinary"

    opened = _ok(hub.client.post("/api/thoughts/open-note", json={"note_id": note_id}))["thought"]
    assert opened["state"] == "working"
    assert opened["working_note"]["id"] == note_id
    assert opened["working_note"]["title"] == TITLE
    assert opened["working_note"]["body_markdown"] == BODY
    # The note stays in the drawer he put it in (before Q8, adoption moved it to Inbox).
    assert opened["directory_id"] == "d-work"
    assert _drawer(hub, note_id) == "d-work"

    again = _ok(hub.client.post("/api/thoughts/open-note", json={"note_id": note_id}))["thought"]
    assert again["id"] == opened["id"]
    assert len(hub.db.refinement_thoughts.list()) == 1
    assert [n.id for n in hub.db.notes.list()] == [note_id]


def test_a_note_on_the_desk_stays_on_the_desk(hub) -> None:
    note_id = _seed(hub, drawer=False)
    assert _drawer(hub, note_id) is None
    _ok(hub.client.post("/api/thoughts/open-note", json={"note_id": note_id}))
    assert _drawer(hub, note_id) is None


def test_develop_no_longer_moves_the_note_into_inbox(hub) -> None:
    note_id = _seed(hub)
    status = _ok(hub.client.get(f"/api/thoughts/for-note/{note_id}"))
    pre = status["source_precondition"]
    _ok(hub.client.post("/api/thoughts/adopt", json={
        "request_id": "q8-develop", "note_id": note_id,
        "expected_source_content_sha256": pre["content_sha256"],
        "expected_source_last_modified": pre["last_modified"],
    }))
    assert _drawer(hub, note_id) == "d-work"


def test_a_finished_note_opens_writable(hub) -> None:
    from holdspeak.services.refinement_thought_service import RefinementThoughtService

    note_id = _seed(hub)
    thought = _ok(hub.client.post("/api/thoughts/open-note", json={"note_id": note_id}))["thought"]
    RefinementThoughtService(hub.db)._complete_without_receipt(
        OWNER, thought["id"], expected_aggregate_revision=thought["aggregate_revision"],
        expected_lifecycle_revision=thought["lifecycle_revision"],
    )
    assert _ok(hub.client.get(f"/api/thoughts/for-note/{note_id}"))["thought"]["state"] == "completed"

    reopened = _ok(hub.client.post("/api/thoughts/open-note", json={"note_id": note_id}))["thought"]
    assert reopened["id"] == thought["id"]
    assert reopened["state"] == "working"
    assert _drawer(hub, note_id) == "d-work"


def test_open_note_refuses_a_missing_or_deleted_note_and_a_bad_request(hub) -> None:
    assert hub.client.post("/api/thoughts/open-note", json={"note_id": "note_none"}).status_code == 404
    note_id = _seed(hub)
    assert hub.client.delete(f"/api/notes/{note_id}").status_code in (200, 204)
    assert hub.client.post("/api/thoughts/open-note", json={"note_id": note_id}).status_code == 404
    refused = hub.client.post("/api/thoughts/open-note", json={"note_id": note_id, "extra": 1})
    assert refused.status_code == 422 and refused.json()["error"] == "note_open_request_invalid"


def test_add_to_note_appends_and_undo_restores_recorded_for_the_face(hub, tmp_path) -> None:
    """The answers the face replays: the window's open and its reads, then
    Ask ▸ Add to note (open, write the appended body) and Undo (open, write
    the body back). The note stays in its drawer throughout."""
    from tests.unit.test_desk_speak import _record

    note_id = _seed(hub)
    opened = _ok(hub.client.post("/api/thoughts/open-note", json={"note_id": note_id}))
    thought = opened["thought"]
    workbench = _ok(hub.client.get(f"/api/thoughts/{thought['id']}/workbench"))

    # Add to note (web/src/desk/noteAppend.ts): open, then the thought write.
    add_open = _ok(hub.client.post("/api/thoughts/open-note", json={"note_id": note_id}))
    current = add_open["thought"]
    grown = f"{BODY}\n\n{ANSWER}"
    add_request = {
        "expected_aggregate_revision": current["aggregate_revision"],
        "expected_working_revision": current["working_revision"],
        "title": TITLE, "body_markdown": grown, "tags": [],
    }
    added = _ok(hub.client.patch(f"/api/thoughts/{thought['id']}/working", json=add_request))
    assert added["thought"]["working_note"]["body_markdown"] == grown
    assert hub.db.notes.get(note_id).body_markdown == grown

    # Undo: open, see the grown body is still there, write the body back.
    undo_open = _ok(hub.client.post("/api/thoughts/open-note", json={"note_id": note_id}))
    assert undo_open["thought"]["working_note"]["body_markdown"] == grown
    undo_request = {
        "expected_aggregate_revision": undo_open["thought"]["aggregate_revision"],
        "expected_working_revision": undo_open["thought"]["working_revision"],
        "title": TITLE, "body_markdown": BODY, "tags": [],
    }
    undone = _ok(hub.client.patch(f"/api/thoughts/{thought['id']}/working", json=undo_request))
    assert undone["thought"]["working_note"]["body_markdown"] == BODY
    assert hub.db.notes.get(note_id).body_markdown == BODY
    assert _drawer(hub, note_id) == "d-work"

    _record("note.one-note.wire", {
        "note_id": note_id,
        "title": TITLE,
        "answer": ANSWER,
        "open": opened,
        "workbench": workbench,
        "add": {"open": add_open, "request": add_request, "answer": added},
        "undo": {"open": undo_open, "request": undo_request, "answer": undone},
    }, tmp_path, "tests/unit/test_desk_note.py::test_add_to_note_appends_and_undo_restores_recorded_for_the_face",
        folder=WIRE)
