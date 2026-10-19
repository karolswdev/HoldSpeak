"""Find the tasks on a note, hub half (Betterment Q9, docs/internal/betterment/asking/RECIPE.md).

One press runs the meeting's own extraction (its prompt, schema and parser,
holdspeak/intel/parsing.py) over the note, on the engine set for meeting
analysis, through the runner. The engine's reply is a REAL reply recorded
from the LAN engine (tests/fixtures/note_find_tasks_reply.json, written by
scripts/record_note_find_tasks_reply.py) on the Jun note of the asking design.
Owners are matched to People; Confirm makes the task (a Door item: Needs you
and the person's window) or the proposed decision, with the note as source.

The face half is web/src/desk/thought-workspace/__tests__/findTasks.app.test.tsx;
it replays the answers this file records (web/src/test/wire/note.find-tasks.wire.json;
HOLDSPEAK_WIRE_WRITE=1 rewrites it).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.unit.test_philo5_the_loop import hub  # noqa: F401  (fixture)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
WIRE = Path(__file__).resolve().parents[2] / "web" / "src" / "test" / "wire"
REPLY = json.loads((FIXTURES / "note_find_tasks_reply.json").read_text())
TITLE = "Jun and the cutover weekend"


class _RecordedEngine:
    """The engine the runner loads: answers with the recorded LAN reply."""

    active_provider = "recorded"
    active_model = REPLY["engine"]["model"]

    def __init__(self) -> None:
        self.prompts: list[dict[str, Any]] = []
        self.fail = False

    def run_prompt(self, **kwargs: Any) -> str:
        if self.fail:
            raise RuntimeError("the engine stopped")
        self.prompts.append(kwargs)
        return REPLY["reply_text"]


def _ok(response: Any, status: int = 200) -> Any:
    assert response.status_code == status, (response.request.url, response.status_code, response.text[:400])
    return response.json()


def wire_recorded_engine(hub, monkeypatch) -> _RecordedEngine:
    """The meeting-analysis engine answers with the recorded LAN reply."""
    from holdspeak.inference_capabilities import process_inference_capability_registry
    from holdspeak.kernel.runtime import _configure
    from tests.unit.test_phase143_inference_assignments import _profile
    from tests.unit.test_phase200_readiness import _assign

    engine = _RecordedEngine()
    broker = _configure(hub.db)
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda revision, **_kw: engine)
    schema = process_inference_capability_registry().require("meeting.deferred_analysis")
    _profile(hub.db, "lan-engine", claims=("language", f"result_schema:{schema.output_schema_sha256}"))
    _assign(hub.db, "meeting.deferred_analysis", ["lan-engine"])
    return engine


@pytest.fixture
def desk(hub, monkeypatch):  # noqa: F811
    engine = wire_recorded_engine(hub, monkeypatch)
    _ok(hub.client.post("/api/people/setup"))
    theo = _ok(hub.client.post("/api/people/relationships", json={"display_name": "Theo Park"}), 201)["relationship"]
    note = _ok(hub.client.post("/api/notes", json={"title": TITLE, "body_markdown": REPLY["note"], "tags": []}), 201)["note"]
    hub.engine, hub.theo, hub.note_id = engine, theo, note["id"]
    return hub


def test_find_the_tasks_runs_the_meetings_extraction_and_matches_owners(desk) -> None:
    assert _ok(desk.client.get(f"/api/notes/{desk.note_id}/outcomes"))["rows"] == []
    found = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/find"))

    # The meeting's prompt and schema, on the note's words.
    prompt = desk.engine.prompts[0]
    assert prompt["response_format"]["json_schema"]["name"] == "meeting_intel"
    assert "Jun is nervous about the cutover weekend" in prompt["user_prompt"]

    tasks = [(r["text"], r["owner"]) for r in found["rows"] if r["kind"] == "task"]
    assert tasks == [
        ("Pair Jun with Mira on call for the cutover weekend", "Me"),
        ("Write the on-call handbook", "Theo Park"),
    ]
    assert "person_id" not in found["rows"][0]  # the 138 law: names only in plaintext
    decisions = [r["text"] for r in found["rows"] if r["kind"] == "decision"]
    # A task the reply also named as a decision is one row: the task.
    assert decisions == ["Theo owns the on-call handbook"]
    assert all(r["state"] == "proposed" for r in found["rows"])
    # The rows stay with the note.
    assert _ok(desk.client.get(f"/api/notes/{desk.note_id}/outcomes"))["rows"] == found["rows"]


def test_confirm_makes_the_task_where_tasks_show_and_the_proposed_decision(desk) -> None:
    rows = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/find"))["rows"]
    theo_task = next(r for r in rows if r["owner"] == "Theo Park")
    my_task = next(r for r in rows if r["owner"] == "Me")
    decision = next(r for r in rows if r["kind"] == "decision")

    after = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/{theo_task['id']}/confirm"))["rows"]
    made = next(r for r in after if r["id"] == theo_task["id"])
    assert made["state"] == "confirmed" and made["made_ref"].startswith("action_item:")
    item_id = made["made_ref"].split(":", 1)[1]
    with desk.db._connection() as conn:
        item = conn.execute("SELECT * FROM action_items WHERE id=?", (item_id,)).fetchone()
    assert (item["task"], item["owner"], item["source_type"], item["source_ref"], item["review_state"]) == (
        "Write the on-call handbook", "Theo Park", "thought", f"note:{desk.note_id}", "accepted")

    # Theo's window lists it (his brief matches the owner by name).
    brief = _ok(desk.client.get(f"/api/people/relationships/{desk.theo['id']}/brief"))["brief"]
    assert "Write the on-call handbook" in [row["task"] for row in brief["open_meeting_actions"]]

    _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/{my_task['id']}/confirm"))
    needs = _ok(desk.client.get("/api/desk/needs-you?fresh=1"))
    assert "Pair Jun with Mira on call for the cutover weekend" in json.dumps(needs)

    final = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/{decision['id']}/confirm"))["rows"]
    ref = next(r for r in final if r["id"] == decision["id"])["made_ref"]
    assert ref.startswith("decision:")
    made_decision = desk.db.desk_decisions.get(ref.split(":", 1)[1])
    assert made_decision.status == "proposed"
    assert f"note:{desk.note_id}" in made_decision.context_markdown

    # Confirm again replays: one task, not two.
    again = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/{theo_task['id']}/confirm"))["rows"]
    assert next(r for r in again if r["id"] == theo_task["id"])["made_ref"] == made["made_ref"]
    with desk.db._connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM action_items WHERE task=?", ("Write the on-call handbook",)).fetchone()[0]
    assert count == 1

    # A new Find keeps the confirmed rows and adds none twice.
    refound = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/find"))["rows"]
    assert sum(1 for r in refound if r["text"] == "Write the on-call handbook") == 1
    assert all(r["state"] == "confirmed" for r in refound)


def test_no_engine_and_a_failed_engine_say_why_in_words(hub) -> None:  # noqa: F811
    note = _ok(hub.client.post("/api/notes", json={"title": TITLE, "body_markdown": REPLY["note"], "tags": []}), 201)["note"]
    refused = hub.client.post(f"/api/notes/{note['id']}/outcomes/find")
    assert refused.status_code == 409
    assert refused.json() == {"error": "no_engine",
                              "message": "No engine is set for meeting analysis. Choose one in Engines."}
    assert hub.client.post("/api/notes/note_none/outcomes/find").status_code == 404


def test_a_failed_engine_leaves_the_note_and_its_rows(desk) -> None:
    desk.engine.fail = True
    failed = desk.client.post(f"/api/notes/{desk.note_id}/outcomes/find")
    assert failed.status_code == 502
    assert failed.json()["message"] == "The engine did not answer. The note is unchanged. Try again."
    assert _ok(desk.client.get(f"/api/notes/{desk.note_id}/outcomes"))["rows"] == []


def test_the_answers_are_recorded_for_the_face(desk, tmp_path) -> None:
    from tests.unit.test_desk_speak import _record

    before = _ok(desk.client.get(f"/api/notes/{desk.note_id}/outcomes"))
    found = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/find"))
    theo_task = next(r for r in found["rows"] if r["owner"] == "Theo Park")
    mine = next(r for r in found["rows"] if r["owner"] == "Me")
    decision = next(r for r in found["rows"] if r["kind"] == "decision")
    edit_request = {"text": "Pair Jun with Mira on call", "owner_name": "Me", "due": "Friday"}
    edited = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/{mine['id']}/edit", json=edit_request))
    dismissed = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/{decision['id']}/dismiss"))
    confirmed = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/{theo_task['id']}/confirm"))
    # A refusal, as the face receives it: a note with no words yet.
    empty = _ok(desk.client.post("/api/notes", json={"title": "", "body_markdown": "", "tags": []}), 201)["note"]
    refusal = desk.client.post(f"/api/notes/{empty['id']}/outcomes/find")
    assert refusal.status_code == 422
    _record("note.find-tasks.wire", {
        "note_id": desk.note_id, "title": TITLE,
        "before": before, "found": found,
        "edit_row": mine["id"], "edit_request": edit_request, "edited": edited,
        "dismiss_row": decision["id"], "dismissed": dismissed,
        "confirm_row": theo_task["id"], "confirmed": confirmed,
        "refused": {"status": refusal.status_code, "body": refusal.json()},
    }, tmp_path, "tests/unit/test_desk_note_outcomes.py::test_the_answers_are_recorded_for_the_face", folder=WIRE)


def test_edit_and_dismiss_a_proposed_row_before_confirm(desk) -> None:
    rows = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/find"))["rows"]
    mine = next(r for r in rows if r["owner"] == "Me")
    decision = next(r for r in rows if r["kind"] == "decision")

    # Edit: the words, a new owner (matched to People again) and a date.
    edited = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/{mine['id']}/edit",
                                  json={"text": "Pair Jun with Mira on call", "owner_name": "Theo", "due": "Friday"}))["rows"]
    row = next(r for r in edited if r["id"] == mine["id"])
    assert (row["text"], row["owner"], row["person_id"], row["due"], row["state"]) == (
        "Pair Jun with Mira on call", "Theo Park", desk.theo["id"], "Friday", "proposed")

    # Dismiss: the row leaves, and a new Find never proposes it again.
    after = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/{decision['id']}/dismiss"))["rows"]
    assert decision["id"] not in [r["id"] for r in after]
    again = _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/find"))["rows"]
    assert "Theo owns the on-call handbook" not in [r["text"] for r in again]
    refused = desk.client.post(f"/api/notes/{desk.note_id}/outcomes/{decision['id']}/confirm")
    assert refused.status_code == 409 and refused.json()["error"] == "note_outcome_dismissed"

    # A confirmed row no longer changes.
    task = next(r for r in again if r["text"] == "Write the on-call handbook")
    _ok(desk.client.post(f"/api/notes/{desk.note_id}/outcomes/{task['id']}/confirm"))
    late = desk.client.post(f"/api/notes/{desk.note_id}/outcomes/{task['id']}/edit", json={"text": "x"})
    assert late.status_code == 409 and late.json()["error"] == "note_outcome_not_proposed"


def test_mcp_reaches_the_same_operations(desk) -> None:
    """MCP parity: an agent finds, reads, edits and confirms the same rows."""
    from holdspeak.mcp.tool_authority import TOOL_AUTHORITY

    for name in ("note.outcomes", "note.find_tasks", "note.outcome.edit", "note.outcome.dismiss",
                 "note.outcome.confirm"):
        assert TOOL_AUTHORITY[name] == "work", name
    is_error, found = desk.mcp("note.find_tasks", {"note_id": desk.note_id})
    assert not is_error, found
    assert [r["text"] for r in found["rows"] if r["kind"] == "task"] == [
        "Pair Jun with Mira on call for the cutover weekend", "Write the on-call handbook"]
    theo_task = next(r for r in found["rows"] if r["owner"] == "Theo Park")
    is_error, read = desk.mcp("note.outcomes", {"note_id": desk.note_id})
    assert not is_error and read["rows"] == found["rows"]
    is_error, confirmed = desk.mcp("note.outcome.confirm", {"note_id": desk.note_id, "row_id": theo_task["id"]})
    assert not is_error, confirmed
    made = next(r for r in confirmed["rows"] if r["id"] == theo_task["id"])
    assert made["state"] == "confirmed" and made["made_ref"].startswith("action_item:")
    # The HTTP read sees the MCP write: one service.
    assert _ok(desk.client.get(f"/api/notes/{desk.note_id}/outcomes"))["rows"] == confirmed["rows"]
