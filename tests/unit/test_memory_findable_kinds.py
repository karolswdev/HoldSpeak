"""What he does is findable in memory (inventory C, gaps 6 and 7).

Gap 6: only the transcript of a meeting was searchable; a word that exists
only in the summary or the topics found nothing.
Gap 7: sends, published updates, Prep briefs and calendar events were in no
memory kind; "what did I send Dana" had no answer.

Every row here is made by its real producer on a real hub (isolated HOME):
``save_meeting``, the Room's update routes, the channel routes with the file
channel's real dispatch, the Prep route, the calendar projection. Memory is
read through ``/api/memory/search`` and through the grounding call Ask uses.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import Hub, _boot, destination, room, send, send_body  # noqa: E402

from holdspeak.calendar_ingest import parse_calendar_bytes  # noqa: E402
from holdspeak.grounding import hydrate_refs_detailed  # noqa: E402
from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment  # noqa: E402
from holdspeak.runtime import composition  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _search(hub: Hub, query: str, **params: Any) -> list[dict[str, Any]]:
    found = hub.client.get("/api/memory/search", params={"query": query, **params})
    assert found.status_code == 200, found.text
    return found.json()["hits"]


def _refs(hub: Hub, query: str, **params: Any) -> list[str]:
    return [hit["source_ref"] for hit in _search(hub, query, **params)]


def _grounded(hub: Hub, query: str) -> Any:
    """The relevance pass Ask and desk chat run with nothing attached."""
    return hydrate_refs_detailed(hub.db, [], [], "summary", query=query, include_memory=True)


# ── gap 6: the meeting summary and topics ───────────────────────────────


def _meeting(hub: Hub) -> None:
    hub.db.meetings.save_meeting(MeetingState(
        id="m-kestrel",
        started_at=datetime(2026, 10, 1, 9, 0, 0),
        title="Ledger sync",
        segments=[TranscriptSegment(text="We looked at the kestrel dashboards.", speaker="Avery",
                                    start_time=1.0, end_time=2.0)],
        intel=IntelSnapshot(timestamp=3.0, topics=["Obsidianware licence"],
                            summary="Team agreed the zephyrine migration plan."),
    ))


def test_a_word_only_in_the_summary_finds_the_meeting(hub: Hub) -> None:
    _meeting(hub)
    assert _refs(hub, "kestrel") == ["meeting:m-kestrel"]  # the transcript, as before

    hits = _search(hub, "zephyrine")
    assert [hit["source_ref"] for hit in hits] == ["meeting:m-kestrel"]
    assert "zephyrine" in hits[0]["snippet"]

    recalled = hub.client.get("/api/memory/recall", params={"query": "zephyrine", "filter": "meetings"}).json()
    assert [row["source_ref"] for row in recalled["meetings"]] == ["meeting:m-kestrel"]


def test_a_word_only_in_the_topics_finds_the_meeting(hub: Hub) -> None:
    _meeting(hub)
    assert _refs(hub, "obsidianware") == ["meeting:m-kestrel"]


def test_a_meeting_found_by_transcript_and_summary_is_one_hit(hub: Hub) -> None:
    _meeting(hub)
    assert _refs(hub, "kestrel zephyrine", kind="meeting") == ["meeting:m-kestrel"]


def test_a_parked_meeting_summary_stays_out(hub: Hub) -> None:
    _meeting(hub)
    with hub.db._connection() as conn:
        conn.execute("UPDATE meetings SET parked=1 WHERE id='m-kestrel'")
    assert _refs(hub, "zephyrine") == []


def test_the_desk_memory_recent_read_shows_the_summary(hub: Hub) -> None:
    _meeting(hub)
    recent = hub.db.memory.recent(kinds=["meeting"])
    assert "zephyrine" in recent[0]["snippet"]


# ── gap 7: sends, published updates, Prep briefs, calendar events ───────


def test_what_did_i_send_dana_has_an_answer(hub: Hub, tmp_path: Path) -> None:
    pid, update = room(hub, name="Atlas", body="The quillon cutover is on track.")
    dest = destination(hub, tmp_path / "out", name="Dana")
    sent = send(hub, send_body(hub, "inline", update, dest, "pcmd_send_dana"))
    assert sent.status_code == 200, sent.text
    send_id = sent.json()["send"]["id"]
    assert sent.json()["send"]["state"] == "sent"

    hits = _search(hub, "what did I send Dana", kind="send")
    assert [hit["source_ref"] for hit in hits] == [f"send:{send_id}"]
    hit = hits[0]
    assert hit["title"].startswith("Atlas")           # what
    assert "To Dana" in hit["snippet"]                # to whom
    assert "sent" in hit["snippet"]                   # outcome
    assert hit["occurred_at"]                         # when
    assert hit["project_id"] == pid
    assert _refs(hub, "Dana", kind="send", project_id=pid) == [f"send:{send_id}"]

    # The frozen payload is not read: the body's word does not find the send.
    assert _refs(hub, "quillon", kind="send") == []

    # Ask's relevance pass takes the hit as context, never as an unknown ref.
    asked = _grounded(hub, "what did I send Dana")
    assert asked.unknown == []
    block = next(b for b in asked.blocks if b.kind == "send")
    assert "To: Dana" in block.text and "Outcome: sent" in block.text
    assert "quillon" not in block.text


def test_a_prepared_send_he_did_not_press_is_not_a_send(hub: Hub, tmp_path: Path) -> None:
    _pid, update = room(hub, name="Atlas")
    dest = destination(hub, tmp_path / "out", name="Dana")
    prepared = hub.client.post("/api/channels/sends", json={
        "document_ref": f"project_update:{update}", "destination_id": dest})
    assert prepared.status_code == 200, prepared.text
    assert _refs(hub, "Dana", kind="send") == []


def test_a_published_update_is_found_and_a_draft_is_not(hub: Hub) -> None:
    pid, published = room(hub, name="Atlas", body="The quillon cutover is on track.")
    assert _refs(hub, "quillon", kind="project_update") == [f"project_update:{published}"]
    assert _refs(hub, "quillon", kind="project_update", project_id=pid) == [f"project_update:{published}"]

    _other, draft = room(hub, name="Borealis", body="The quillon rehearsal slipped.", publish=False)
    assert f"project_update:{draft}" not in _refs(hub, "quillon")

    asked = _grounded(hub, "quillon cutover")
    assert asked.unknown == []
    assert any(b.kind == "project_update" and "quillon" in b.text for b in asked.blocks)


def test_a_prep_brief_is_found_until_he_discards_it(hub: Hub) -> None:
    pid = hub.client.post("/api/projects", json={"name": "Atlas"}).json()["project"]["id"]
    made = hub.client.post(f"/api/projects/{pid}/briefs/prepare",
                           json={"purpose": "vellichor architecture review", "generator": "deterministic"})
    assert made.status_code == 200, made.text
    brief_id = made.json()["brief"]["id"]

    hits = _search(hub, "vellichor", kind="prep_brief")
    assert [hit["source_ref"] for hit in hits] == [f"prep_brief:{brief_id}"]
    assert hits[0]["project_id"] == pid
    assert _grounded(hub, "vellichor").unknown == []

    assert hub.client.post(f"/api/briefs/{brief_id}/discard", json={}).status_code == 200
    assert _refs(hub, "vellichor", kind="prep_brief") == []


_ICS = b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//holdspeak//test//EN
BEGIN:VEVENT
UID:uid-thornvale
DTSTAMP:20261001T080000Z
DTSTART:20261006T100000Z
DTEND:20261006T110000Z
SUMMARY:Thornvale steering review
LOCATION:Room 4
ATTENDEE;CN=Dana:mailto:dana@example.com
END:VEVENT
END:VCALENDAR
""".replace(b"\n", b"\r\n")


def test_a_calendar_event_is_found_by_title_and_attendee(hub: Hub) -> None:
    # The ingest's own parser makes the rows; the repository stores them.
    parsed = parse_calendar_bytes(_ICS, now=datetime(2026, 10, 3, tzinfo=timezone.utc),
                                  subscription_revision="rev-1")
    assert parsed.feed_error is None and len(parsed.events) == 1, parsed
    hub.db.calendar_events.replace_projection(
        "rev-1", parsed.events, seen_at=1.0, source_id="work", source_label="Work")
    event_id = hub.db.calendar_events.list_all()[0].id

    assert _refs(hub, "thornvale", kind="calendar_event") == [f"calendar_event:{event_id}"]
    by_attendee = _search(hub, "dana", kind="calendar_event")
    assert [hit["source_ref"] for hit in by_attendee] == [f"calendar_event:{event_id}"]

    asked = _grounded(hub, "thornvale steering")
    assert asked.unknown == []
    assert any(b.kind == "calendar_event" and "2026-10-06" in b.text for b in asked.blocks)


# ── gap 8: the Desk memory face recalls an action item ──────────────────


def _meeting_with_actions(hub: Hub) -> None:
    def action(action_id: str, task: str, status: str) -> dict[str, Any]:
        return {"id": action_id, "task": task, "owner": "Dana", "due": "2026-10-09", "status": status,
                "review_state": "accepted", "source_timestamp": None, "created_at": "2026-10-01T09:00:00"}

    hub.db.meetings.save_meeting(MeetingState(
        id="m-rollout",
        started_at=datetime(2026, 10, 1, 9, 0, 0),
        title="Rollout planning",
        segments=[TranscriptSegment(text="We planned the rollout.", speaker="Avery", start_time=1.0, end_time=2.0)],
        intel=IntelSnapshot(timestamp=3.0, topics=[], summary="", action_items=[
            action("act-open", "Draft the quillfeather rollout checklist", "pending"),
            action("act-done", "Book the quillfeather review room", "done"),
        ]),
    ))


def _recall(hub: Hub, query: str, **params: Any) -> dict[str, Any]:
    found = hub.client.get("/api/memory/recall", params={"query": query, **params})
    assert found.status_code == 200, found.text
    return found.json()


def test_desk_memory_recalls_an_action_item(hub: Hub) -> None:
    _meeting_with_actions(hub)
    assert "action:act-open" in _refs(hub, "quillfeather")  # memory.search, as before

    recalled = _recall(hub, "quillfeather")
    # The open one is OWED, in the shape the owed row species draws.
    assert [row["action_item_id"] for row in recalled["owed"]] == ["act-open"]
    owed = recalled["owed"][0]
    assert owed["text"] == "Draft the quillfeather rollout checklist"
    assert owed["ref"] == "action:act-open"
    assert owed["owner_token"] == "OWNER · DANA" and owed["due_at"] == "2026-10-09"
    assert owed["next_action"] == "mark_done" and owed["unknowns"] == []
    # The settled one is remembered under ALSO, and never drawn twice.
    assert [row["source_ref"] for row in recalled["also"] if row["kind"] == "action"] == ["action:act-done"]
    assert recalled["remembered"] >= 2

    only_owed = _recall(hub, "quillfeather", filter="commitments")
    assert [row["action_item_id"] for row in only_owed["owed"]] == ["act-open"]


def test_desk_memory_answers_what_did_i_send_dana(hub: Hub, tmp_path: Path) -> None:
    _pid, update = room(hub, name="Atlas", body="The quillon cutover is on track.")
    dest = destination(hub, tmp_path / "out", name="Dana")
    sent = send(hub, send_body(hub, "inline", update, dest, "pcmd_send_dana"))
    assert sent.status_code == 200, sent.text

    recalled = _recall(hub, "Dana")
    assert [row["kind"] for row in recalled["also"]] == ["send"]
    assert "To Dana" in recalled["also"][0]["snippet"]


def test_the_wordless_desk_memory_read_keeps_calendar_events_out(hub: Hub) -> None:
    parsed = parse_calendar_bytes(_ICS, now=datetime(2026, 10, 3, tzinfo=timezone.utc),
                                  subscription_revision="rev-1")
    hub.db.calendar_events.replace_projection(
        "rev-1", parsed.events, seen_at=1.0, source_id="work", source_label="Work")
    recent = hub.client.get("/api/memory/recall", params={"recent": "true"})
    assert recent.status_code == 200, recent.text
    assert [row["kind"] for row in recent.json()["also"]] == []
    assert [row["kind"] for row in _recall(hub, "thornvale")["also"]] == ["calendar_event"]
