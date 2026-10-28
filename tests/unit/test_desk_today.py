"""DELIGHT slice 5 (2026-10-28): Today in the evening, the hub half.

``GET /api/today/since-morning`` lists what got done today, newest first:
a task ticked (through the real ``PATCH /api/action-items/{id}``), a note
filed (``POST /api/notes`` + ``PUT /api/directories/{id}/members/note:<id>``),
a decision recorded, a send sent and a meeting held (their rows as the
producers write them). Yesterday's work, a pending task, a note left in no
folder and a failed send stay out. The answer is recorded for the face
(web/src/desk/pullouts/views/TodayView.test.tsx, "Since this morning");
HOLDSPEAK_WIRE_WRITE=1 rewrites the file.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from test_desk_needs_you import _boot  # noqa: E402
from test_desk_speak import _record  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TODAY_FIXTURES = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures" / "today-hub"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _ok(response: Any, status: int = 200) -> dict[str, Any]:
    assert response.status_code == status, response.text
    return response.json()


def _iso(at: datetime) -> str:
    return at.astimezone(timezone.utc).isoformat()


def _seed(hub: Any) -> dict[str, str]:
    now = datetime.now().astimezone()
    morning = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # Today's times stay inside today even just after midnight.
    at = lambda minutes: max(now - timedelta(minutes=minutes), morning + timedelta(seconds=minutes))  # noqa: E731
    yesterday = morning - timedelta(hours=2)
    with hub.db._connection() as conn:
        for mid, title, start, end, intel in (
            ("m-today", "Payments weekly", at(50), at(20), "ready"),
            ("m-old", "Old standup", yesterday, yesterday + timedelta(minutes=15), "ready"),
        ):
            conn.execute(
                "INSERT INTO meetings (id, started_at, ended_at, title, intel_status) VALUES (?,?,?,?,?)",
                (mid, _iso(start), _iso(end), title, intel))
        for aid, task in (("a-tick", "Email Dana the cutover plan"), ("a-open", "Book the review room")):
            conn.execute("INSERT INTO action_items (id, meeting_id, task, status) VALUES (?,?,?, 'pending')",
                         (aid, "m-today", task))
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, status, completed_at) VALUES (?,?,?, 'done', ?)",
            ("a-old", "m-old", "Yesterday's task", _iso(yesterday)))
        for rid, text, when in (("r-today", "Freeze the ledger on Nov 12\nWhy: the audit.", at(10)),
                                ("r-old", "An old decision", yesterday)):
            conn.execute(
                "INSERT INTO decision_records (id, decision_text, source_type, source_id, created_at, updated_at, kind)"
                " VALUES (?,?, 'desk', ?, ?, ?, 'decision')", (rid, text, rid, _iso(when), _iso(when)))
        conn.execute(
            "INSERT INTO channel_destinations (id, name, channel, target_json, target_digest, created_at)"
            " VALUES ('d-1', 'Payments folder', 'folder', '{}', 'x', ?)", (_iso(yesterday),))
        for sid, state, settled in (("s-sent", "sent", at(5)), ("s-failed", "failed", at(4))):
            conn.execute(
                "INSERT INTO channel_sends (id, document_ref, destination_id, channel, target_json, target_digest,"
                " payload, payload_digest, document_json, state, created_at, settled_at)"
                " VALUES (?, 'meeting:m-today', 'd-1', 'folder', '{}', 'x', x'00', 'x', ?, ?, ?, ?)",
                (sid, '{"title": "Payments weekly summary"}', state, _iso(settled), _iso(settled)))
    # The task is ticked through the hub's own route (the Needs-you Done).
    _ok(hub.client.patch("/api/action-items/a-tick", json={"status": "done"}))
    note = _ok(hub.client.post("/api/notes", json={"title": "", "body_markdown": "# Cutover notes\nThe plan."}), 201)
    loose = _ok(hub.client.post("/api/notes", json={"title": "A loose note", "body_markdown": "x"}), 201)
    folder = _ok(hub.client.post("/api/directories", json={"name": "Payments"}), 201)
    note_id = str(note["note"]["id"])
    _ok(hub.client.put(f"/api/directories/{folder['directory']['id']}/members/note:{note_id}"))
    return {"note": note_id, "loose": str(loose["note"]["id"])}


def test_since_morning_lists_what_got_done_today(hub: Any, tmp_path: Path) -> None:
    ids = _seed(hub)
    body = _ok(hub.client.get("/api/today/since-morning"))
    rows = [(row["kind"], row["ref"], row["title"], row["word"]) for row in body["items"]]
    assert sorted(rows) == sorted([
        ("action", "action_item:a-tick", "Email Dana the cutover plan", "Done"),
        ("note", f"note:{ids['note']}", "Cutover notes", "Filed in Payments"),
        ("send", "meeting:m-today", "Payments weekly summary", "Sent"),
        ("decision", "decision_record:r-today", "Freeze the ledger on Nov 12", "Recorded"),
        ("meeting", "meeting:m-today", "Payments weekly", "Summary stored"),
    ]), rows
    stamps = [row["at"] for row in body["items"]]
    assert stamps == sorted(stamps, reverse=True), "newest first"
    morning = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    assert body["since"] == morning.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    assert all(row["at"].endswith("Z") for row in body["items"])
    _record("since-morning", {"/api/today/since-morning": body}, tmp_path,
            "tests/unit/test_desk_today.py", folder=TODAY_FIXTURES)


def test_since_morning_is_empty_on_a_new_desk(hub: Any) -> None:
    body = _ok(hub.client.get("/api/today/since-morning"))
    assert body["items"] == []
