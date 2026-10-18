"""The Brief and Needs you after a full day: the hub half, through the routes.

The test diet (2026-10-11) moves the hub facts of
tests/e2e/test_philo15_09_morning_truth_glass.py here. The same rehearsal day
(rehearsal 1a, B04/B11) through the same real producers, on the real hub
(``TestClient`` over the hub's app, tests/unit/test_philo5_the_loop.py):
the morning's brief first, then the day, then Generate again.

The service-level fences of the same rulings stay in
tests/unit/test_philo15_09_brief_truth.py (same id, the four lines, the title
and the one range). This file holds the WIRE the Chair reads:
``/api/brief/generate``, ``/api/brief/latest`` and ``/api/desk/needs-you``.

The face facts are vitest (no duplicate written here):
  * GENERATED receipt after Generate:
    web/src/desk/chair/__tests__/briefReceiptRendered202.test.tsx
    "shows the latest receipt before Generate and replaces it with the new receipt"
  * the period label in the date caption:
    web/src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx
    "puts the period and the generated date under a populated brief"
  * the RENDERED window title is the brief's title:
    web/src/desk/chair/__tests__/chairWindows.philo1311.test.tsx
    "renders `Brief · Wednesday 7 Oct 2026` in the title bar"
  * The week with no calendar is never empty (B07):
    web/src/desk/chair/__tests__/chairWindows.philo1311.test.tsx
    "a fresh desk with no calendar: one NO CALENDAR row with Connect" and
    "lists this week's decisions and the action items due by its end"
  * the Needs-you head number equals the row count, each row names its kind (B11, B12):
    web/src/desk/needs/__tests__/NeedsDrawer.test.tsx
    "the head is the number of rows, and each member row names its kind"
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

DECISION = "Use SQLite for the local meeting ledger"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    keyfile = tmp_path / "people.key"  # the path _boot names; the e2e wrote it the same way
    keyfile.write_text("{}")
    keyfile.chmod(0o600)
    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _the_rehearsal_day() -> None:
    """What the owner did in rehearsal 1a, through the real producers (the e2e's seed)."""
    from holdspeak.db import get_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.people import production_people_store
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.people_service import PeopleService
    from holdspeak.services.primitive_service import PrimitiveService

    db = get_database()
    owner = Principal(PrincipalKind.OWNER, "karol")
    start = (datetime.now() - timedelta(minutes=20)).replace(microsecond=0)
    db.meetings.save_meeting(MeetingState(
        id="m-day-one", started_at=start, ended_at=start + timedelta(seconds=35),
        title="Architect sync",
        segments=[TranscriptSegment(text="We adopt SQLite for the local meeting ledger.",
                                    speaker="Me", start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["ledger"], summary="Three decisions.", action_items=[{
            "id": "m-day-one-a1", "task": "Write the migration plan", "owner": None, "due": None,
            "status": "pending", "review_state": "accepted", "source_timestamp": None,
            "created_at": start.isoformat()}]),
        intel_status="completed"))
    PrimitiveService(db).create_decision(owner, decision_id="d-sqlite", title=DECISION, status="accepted")
    db.projects.create_project(project_id="p-ledger", name="Local meeting ledger")
    store = production_people_store()
    store.initialize()
    PeopleService(store).create_relationship(owner, {"display_name": "Priya Shah", "relationship_kind": "direct_report"})


def test_generate_after_a_full_day_makes_the_dated_brief_of_the_day(hub: Hub) -> None:
    """replaces: tests/e2e/test_philo15_09_morning_truth_glass.py::TestTheMorningTellsTheTruth::test_the_brief_the_week_and_needs_you_after_a_full_day (hub half: B04)"""
    morning = hub.client.post("/api/brief/generate")
    assert morning.status_code == 200, morning.text
    morning = morning.json()

    _the_rehearsal_day()
    again = hub.client.post("/api/brief/generate")
    assert again.status_code == 200, again.text

    latest = hub.client.get("/api/brief/latest").json()
    assert latest["id"] == morning["id"], "the same day keeps the brief's id"
    assert latest["generated_at"] > morning["generated_at"], "Generate made it again"
    texts = [i["text"] for items in latest["sections"].values() for i in items]
    for wanted in ("Meeting recorded: Architect sync",
                   f"Decision made: {DECISION}",
                   "Project added: Local meeting ledger", "Person added"):
        assert wanted in texts, (wanted, texts)
    assert latest["headline"] != "No changes"
    assert latest["title"].startswith("Brief · ") and "Monday Brief" not in latest["title"], latest["title"]
    # One range: the face's date caption reads this label (briefLoadAndDate.philo303).
    assert latest["period_label"], latest


def test_a_decision_he_made_is_not_a_needs_you_row(hub: Hub) -> None:
    """replaces: tests/e2e/test_philo15_09_morning_truth_glass.py::TestTheMorningTellsTheTruth::test_the_brief_the_week_and_needs_you_after_a_full_day (hub half: the Needs window)"""
    _the_rehearsal_day()
    needs = hub.client.get("/api/desk/needs-you")
    assert needs.status_code == 200, needs.text
    body = needs.json()
    assert DECISION not in json.dumps(body), body


# ── PHILO-15 01: a Default for AI work clears "No engine for summaries" ────
# The seeds of tests/e2e/test_philo15_01_default_clears_summaries_glass.py,
# verbatim: the LAN model as the GLOBAL default ("Set up local AI"), and,
# for the OFF case, an imported meeting with no summary request and the
# summary capability turned off by the owner.

SUMMARY = "meeting.deferred_analysis"
FALSE_ROW = "No engine for summaries"


def assign_lan_default() -> None:
    """The state "Set up local AI" leaves: one LAN model as the global default."""
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from test_phase143_inference_assignments import _profile, _result_claim

    db = get_database()
    _profile(
        db,
        "lan-qwen",
        claims=("language", "structured_output", _result_claim(SUMMARY)),
        modalities=("language", "text"),
        model="qwen3.8-27b",
        boundary="private_network",
    )
    InferenceAssignmentService(db).set_assignment(
        Principal(PrincipalKind.OWNER, "philo15-owner"),
        {
            "command_id": "philo15-01-default",
            "expected_revision": 0,
            "scope": {"kind": "global"},
            "entries": [{"profile_id": "lan-qwen", "profile_revision": 1}],
        },
    )


def seed_imported_meeting() -> None:
    """An imported transcript with no summary request: the ordinary OFF case."""
    from holdspeak.db import get_database

    db = get_database()
    now = datetime.now()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, started_at, ended_at, title, duration_seconds,"
            " intel_status, capture_status, provenance) VALUES (?,?,?,?,?,'disabled','finalized','desktop')",
            ("m-off-import", (now - timedelta(hours=2)).isoformat(),
             (now - timedelta(hours=1, minutes=30)).isoformat(), "Imported vendor call", 1800.0),
        )
        for i in range(6):
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) VALUES (?,?,?,?,?)",
                ("m-off-import", f"we agreed on the cutover plan part {i}", "Karol", float(i * 30), float((i + 1) * 30)),
            )


def turn_summaries_off() -> None:
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    InferenceAssignmentService(get_database()).set_capability_off(
        Principal(PrincipalKind.OWNER, "philo15-owner"), capability_id=SUMMARY,
    )


def _summary_row(hub: Hub) -> dict:
    roster = hub.client.get("/api/inference/assignments")
    assert roster.status_code == 200, roster.text
    return next(r for r in roster.json()["task_overrides"] if r["id"] == SUMMARY)


def _generated_brief(hub: Hub) -> dict:
    generated = hub.client.post("/api/brief/generate")
    assert generated.status_code == 200, generated.text
    latest = hub.client.get("/api/brief/latest")
    assert latest.status_code == 200, latest.text
    return latest.json()


def test_a_global_default_clears_the_summaries_row_from_needs_you_and_the_brief(hub: Hub) -> None:
    """replaces: tests/e2e/test_philo15_01_default_clears_summaries_glass.py::TestDefaultClearsSummaries::test_needs_you_and_brief_draw_no_false_row (hub half)"""
    assign_lan_default()
    row = _summary_row(hub)
    assert row["has_override"] is False, row
    assert row["queue"]["status"] == "assigned", row
    assert row["queue"]["inherited_from"] == "global", row

    needs = hub.client.get("/api/desk/needs-you?fresh=1")
    assert needs.status_code == 200, needs.text
    body = needs.json()
    assert FALSE_ROW not in json.dumps(body), body
    assert not [b for b in body.get("blockers") or [] if b.get("key") in {"summary", "engines"}], body.get("blockers")

    assert FALSE_ROW not in json.dumps(_generated_brief(hub))


def test_summaries_off_reads_off_and_asks_nothing(hub: Hub) -> None:
    """replaces: tests/e2e/test_philo15_01_default_clears_summaries_glass.py::TestSummariesOff::test_off_reads_off_and_asks_nothing (hub half)

    The Meetings headline `Summaries off` over this wire is
    web/src/pages/cores/history/__tests__/meetingsHeadlineDefault.philo1501.test.ts
    ("reads OFF over an UNSUMMARISED imported meeting")."""
    assign_lan_default()
    seed_imported_meeting()
    turn_summaries_off()
    assert _summary_row(hub)["queue"]["status"] == "off"

    needs = hub.client.get("/api/desk/needs-you?fresh=1")
    assert needs.status_code == 200, needs.text
    body = needs.json()
    assert body.get("blockers") in ([], None), body.get("blockers")
    text = json.dumps(body)
    assert FALSE_ROW not in text and "Summary failed" not in text, body
    assert not [m for m in body.get("failedMeetings") or [] if m.get("id") == "m-off-import"], body

    brief = json.dumps(_generated_brief(hub))
    assert FALSE_ROW not in brief and "Summary failed" not in brief, brief

    meetings = hub.client.get("/api/meetings?limit=20")
    assert meetings.status_code == 200, meetings.text
    imported = next(m for m in meetings.json()["meetings"] if m["id"] == "m-off-import")
    # The wire the Meetings headline reads: the planned route says OFF.
    route = imported.get("planned_route") or imported.get("current_planned_route")
    assert route and route["status"] == "unavailable" and route["reason_code"] == "summaries off", imported


# ── Betterment daily D4: Today makes Since yesterday without a press ───────


def _ensured(hub: Hub) -> dict:
    latest = hub.client.get("/api/brief/latest?ensure=1")
    assert latest.status_code == 200, latest.text
    return latest.json()


def test_today_makes_the_brief_on_first_open_and_once(hub: Hub) -> None:
    """No brief for the period: the read with ``ensure`` makes it (the owner's
    Generate, off the event loop). A second read finds it and makes nothing.
    A plain read still makes nothing (MCP, the Chair)."""
    assert hub.client.get("/api/brief/latest").json() is None
    _the_rehearsal_day()
    first = _ensured(hub)
    assert first and first["id"], first
    texts = [i["text"] for items in first["sections"].values() for i in items]
    assert "Meeting recorded: Architect sync" in texts, texts
    assert first["stale"] is False
    again = _ensured(hub)
    assert (again["id"], again["generated_at"]) == (first["id"], first["generated_at"]), "made once"


def test_today_makes_the_brief_again_for_a_new_day_or_a_newer_desk(hub: Hub) -> None:
    """A brief of an earlier day (or one older than a meeting) is made again
    on the next open; the stored brief of the day keeps its id."""
    made = hub.client.post("/api/brief/generate").json()
    yesterday = (datetime.now() - timedelta(days=1)).astimezone().isoformat()
    with hub.db._connection() as conn:
        conn.execute("UPDATE monday_briefs SET generated_at = ? WHERE id = ?", (yesterday, made["id"]))
        conn.commit()
    assert hub.client.get("/api/brief/latest").json()["stale"] is True
    fresh = _ensured(hub)
    assert fresh["generated_at"] > yesterday and fresh["stale"] is False, fresh
    # A meeting newer than the brief (stored stamps have whole seconds: the
    # brief is moved a minute back so the meeting is newer, not equal).
    earlier = (datetime.now() - timedelta(minutes=1)).astimezone().isoformat()
    with hub.db._connection() as conn:
        conn.execute("UPDATE monday_briefs SET generated_at = ? WHERE id = ?", (earlier, fresh["id"]))
        conn.commit()
    _the_rehearsal_day()
    newer = _ensured(hub)
    assert newer["generated_at"] > earlier and newer["id"] == fresh["id"], "the newer desk made it again"
    assert "Meeting recorded: Architect sync" in [i["text"] for items in newer["sections"].values() for i in items]


def _calendar_today(hub: Hub, mira: str) -> None:
    """The recon's day on the calendar: the 1:1 with Mira in 90 minutes (her
    series linked to her), the platform sync after it, the 1:1 with Jun
    tomorrow. Applied by the real ingest conductor."""
    import tempfile
    from datetime import timezone

    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    events = (
        ("daily-mira-1on1", "1:1 with Mira", now + timedelta(minutes=90), 30),
        ("daily-platform-sync", "Payments platform sync", now + timedelta(hours=3), 30),
        ("daily-jun-1on1", "1:1 with Jun", now + timedelta(days=1), 30),
    )
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HoldSpeak//daily D4//EN"]
    for uid, title, start, minutes in events:
        lines += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",
                  f"DTEND:{(start + timedelta(minutes=minutes)).strftime('%Y%m%dT%H%M%SZ')}",
                  f"SUMMARY:{title}", "END:VEVENT"]
    ics = Path(tempfile.mkdtemp(prefix="daily-d4-ics-")) / "week.ics"
    ics.write_text("\r\n".join([*lines, "END:VCALENDAR", ""]), encoding="utf-8")
    put = hub.client.put("/api/settings", json={"calendar": {"sources": [
        {"id": "daily-work", "label": "Work", "url": str(ics), "enabled": True}]}})
    assert put.status_code == 200, put.text
    assert CalendarIngestConductor().refresh() is True
    linked = hub.client.post(f"/api/people/relationships/{mira}/calendar-links",
                             json={"uid": "daily-mira-1on1", "source_id": "daily-work", "label": "1:1 with Mira"})
    assert linked.status_code == 200, linked.text


def test_today_on_the_daily_week_reads_the_one_number_the_day_and_since_yesterday(hub: Hub) -> None:
    """The recon's week (D1: after the nine keeps, the LAN engine set) and its
    day on the calendar. Today's reads: the one number (4), the next 1:1 with
    Mira (her Prep), and the brief made on the first open. The face's half
    (web/src/desk/__tests__/today.app.test.tsx) renders these answers."""
    from datetime import date

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.fixtures.daily_week import seed
    from tests.unit.test_desk_speak import _record

    seeded = seed(hub, monday=date.today(), engine=True)
    _calendar_today(hub, seeded["Mira"])
    needs = hub.client.get("/api/desk/needs-you?fresh=1").json()
    assert needs["count"] == 4, needs["count"]
    door = hub.client.get("/api/door").json()
    mira = next(e for e in door["upcoming"] if e.get("title") == "1:1 with Mira")
    assert mira["person_relationship_id"] == seeded["Mira"], mira
    assert door["week"]["has_calendar"] is True and door["week"]["total"] >= 2, door["week"]
    brief = _ensured(hub)
    assert brief and brief["id"], brief
    meetings = hub.client.get("/api/meetings?limit=40").json()
    wire = json.loads(json.dumps({
        "recordedAt": datetime.now().astimezone().isoformat(),
        "gets": {
            "/api/desk/needs-you?fresh=1": needs,
            "/api/door": door,
            "/api/brief/latest?ensure=1": brief,
            "/api/meetings?limit=40": meetings,
        },
    }).replace(seeded["project"], "proj-daily-week"))
    _record("today", wire, Path(hub.db.db_path).parent,
            "tests/unit/test_desk_brief.py::test_today_on_the_daily_week_reads_the_one_number_the_day_and_since_yesterday",
            folder=Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__"
            / "fixtures" / "daily-week")


def test_today_on_an_empty_desk_reads_nothing_waiting_and_no_calendar(hub: Hub) -> None:
    """A fresh desk with its engine set (else the hub's "No engine for
    summaries" row waits: the design wants that row only once a meeting
    waits, a hub rule D4 does not change): no calendar, no meeting, nothing
    waits. The first open still makes the (empty) brief. The face's half
    (today.app.test.tsx, "an empty desk is one line") renders these answers."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.fixtures.daily_week import seed_engine
    from tests.unit.test_desk_speak import _record

    seed_engine(hub.client)
    needs = hub.client.get("/api/desk/needs-you?fresh=1").json()
    assert needs["count"] == 0 and needs["members"] == [], needs
    door = hub.client.get("/api/door").json()
    assert door["calendar_configured"] is False and door["upcoming"] == [], door
    brief = _ensured(hub)
    assert brief and brief["id"], brief
    meetings = hub.client.get("/api/meetings?limit=40").json()
    assert meetings["meetings"] == []
    _record("today-empty", {
        "recordedAt": datetime.now().astimezone().isoformat(),
        "gets": {
            "/api/desk/needs-you?fresh=1": needs,
            "/api/door": door,
            "/api/brief/latest?ensure=1": brief,
            "/api/meetings?limit=40": meetings,
        },
    }, Path(hub.db.db_path).parent,
        "tests/unit/test_desk_brief.py::test_today_on_an_empty_desk_reads_nothing_waiting_and_no_calendar",
        folder=Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__" / "fixtures" / "daily-week")
