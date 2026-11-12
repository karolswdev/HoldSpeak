"""The brief words the same stored facts as Today, the Room and the Door."""

from tests.room_bindings import saved_binding
from datetime import datetime, timedelta, timezone

import pytest

from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.monday_brief_service import MondayBriefService
from tests.unit.test_desk_brief import hub  # noqa: F401

OWNER = Principal(PrincipalKind.OWNER, "fact-owner")


def _history_day(hub):
    from holdspeak.services.primitive_service import PrimitiveService
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    now = datetime.now().astimezone()
    morning = now.replace(hour=0, minute=0, second=0, microsecond=0)
    hub.db.meetings.save_meeting(MeetingState(
        id="overnight", title="Overnight review", started_at=morning - timedelta(minutes=10),
        ended_at=now - timedelta(seconds=1),
    ))
    PrimitiveService(hub.db).create_decision(OWNER, decision_id="history-choice", title="Use one ledger", status="accepted")
    hub.db.projects.create_project(project_id="history-project", name="The ledger")
    proposal = hub.db.proposals.create_proposal(
        meeting_id="overnight", project_id=None, kind="decision", text="Keep the local ledger", source_plugin="test",
    )
    ProposalBridgeService(hub.db).confirm_proposal(OWNER, proposal.id, binding=saved_binding(ProposalBridgeService(hub.db), 'confirm_proposal', OWNER, proposal.id))
    failed, action = hub.mcp("door.add_item", {"task": "Publish the ledger", "owner": "Me"})
    assert not failed, action
    response = hub.client.patch(f"/api/all-action-items/{action['id']}", json={"status": "done"})
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("kind,words", [
    ("desk_decision", "Decision made"), ("project", "Project added"),
    ("confirmed_decision", "Decision confirmed"), ("action", "Action done"),
    ("meeting", "Meeting recorded"),
])
def test_history_rows_have_one_gather_for_today_and_brief(hub, monkeypatch, kind, words):
    from holdspeak.services import today_service

    _history_day(hub)
    read = today_service.since_morning_read
    answers = []

    def record(*args, **kwargs):
        answer = read(*args, **kwargs)
        answers.append(answer)
        return answer

    monkeypatch.setattr(today_service, "since_morning_read", record)
    today = hub.client.get("/api/today/since-morning")
    assert today.status_code == 200, today.text
    expected = {(row["ref"], row["title"]) for row in today.json()["items"] if row["kind"] == kind}
    assert expected
    answers.clear()
    response = hub.client.post("/api/brief/generate")
    assert response.status_code == 200, response.text
    brief = response.json()
    assert len(answers) == 1, "All history wording and recording dedup must share one source answer"
    actual = {(row["source_ref"], row["text"].split(": ", 1)[1])
              for row in brief["sections"]["changed"] if row["text"].startswith(words + ": ")}
    assert expected <= actual


def test_today_does_not_call_a_running_capture_recorded(hub):
    now = datetime.now(timezone.utc)
    hub.db.meetings.save_meeting(MeetingState(id="still-recording", title="Live review", started_at=now,
                                             ended_at=now))
    with hub.db._connection() as conn:
        conn.execute("UPDATE meetings SET capture_status = 'recording' WHERE id = 'still-recording'")
    today = hub.client.get("/api/today/since-morning")
    assert today.status_code == 200, today.text
    assert "meeting:still-recording" not in {row["ref"] for row in today.json()["items"]}


def test_digest_uses_the_doors_visible_tasks_not_a_parked_meetings_tasks(hub):
    from holdspeak.runtime import composition
    from holdspeak.services.briefing_service import BriefingService

    now = datetime.now().astimezone()
    hub.db.meetings.save_meeting(MeetingState(id="parked-review", title="Parked review", started_at=now, ended_at=now))
    failed, action = hub.mcp("door.add_item", {"task": "A parked review task", "owner": "Me", "due": now.date().isoformat()})
    assert not failed, action
    with hub.db._connection() as conn:
        conn.execute("UPDATE action_items SET meeting_id = 'parked-review' WHERE id = ?", (action["id"],))
        conn.execute("UPDATE meetings SET parked = 1 WHERE id = 'parked-review'")
    door = composition.current().door_service.asking_board(OWNER)
    assert not any(row["id"] == action["id"] for lane in door.values() for row in lane)
    assert BriefingService(hub.db).digest_lines() == []


def _room_day(hub):
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    now = datetime.now().astimezone()
    for mid in ("filed-review", "unfiled-review"):
        hub.db.meetings.save_meeting(MeetingState(id=mid, title=mid, started_at=now, ended_at=now))
    # The same meeting belongs to two Rooms. Facts must still be said once.
    for project_id in ("room-one", "room-two"):
        hub.db.projects.create_project(project_id=project_id, name=project_id)
        hub.db.projects.associate_meeting_project(meeting_id="filed-review", project_id=project_id)
    service = ProposalBridgeService(hub.db)
    for mid, kind in (("filed-review", "decision"), ("filed-review", "action"), ("unfiled-review", "decision"),
                      ("unfiled-review", "action")):
        proposal = hub.db.proposals.create_proposal(meeting_id=mid, project_id=None, kind=kind, text=f"{mid} {kind}", source_plugin="test")
        result = service.confirm_proposal(OWNER, proposal.id, owner="Me", due=now.date().isoformat(), binding=saved_binding(service, 'confirm_proposal', OWNER, proposal.id))
        assert result.get("decision_record_id"), result
    return now


@pytest.mark.parametrize("fact", ["decisions", "commitments"])
def test_meeting_watch_uses_the_room_rows_once(hub, fact):
    from holdspeak.runtime import composition

    now = _room_day(hub)
    room = composition.current().project_service.room(OWNER, "room-one")
    assert room[fact]["state"] == "ok", room[fact]
    rows = room[fact]["items"]
    expected = {row["id"] for row in rows if row.get("kind") == ("decision" if fact == "decisions" else "action")}
    assert expected
    response = hub.client.post("/api/brief/generate")
    assert response.status_code == 200, response.text
    source = "meeting_watch:decisions" if fact == "decisions" else "meeting_watch:commitments_due"
    items = [row for row in response.json()["sections"]["this_week"] if row["source_ref"] == source]
    assert len(items) == 1
    assert items[0]["text"].split()[0] == str(len(expected)), items
    if fact == "commitments":
        assert "filed-review action" in items[0]["detail"]
        assert not any(row["text"].startswith("Commitment due") for row in response.json()["sections"]["decisions"])


def test_programs_in_the_brief_follow_todays_moved_programs(hub, tmp_path):
    from holdspeak.services.program_service import ProgramService

    import subprocess

    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    service = ProgramService(hub.db)
    # A held Program changed today and waits for the owner's next move.
    program = service.create(OWNER, title="The review", goal="Review the ledger", repository=str(repo),
                             check_command="true", template="fast-cycle", control="secure")
    expected = service.since_morning(OWNER)
    assert expected["moved"]
    today = hub.client.get("/api/today/since-morning")
    assert today.status_code == 200, today.text
    assert today.json()["programs"] == expected
    response = hub.client.post("/api/brief/generate")
    assert response.status_code == 200, response.text
    rows = [row for row in response.json()["sections"]["changed"] if row["text"] == "Programs"]
    # Even a draft that moved is visible; the previous gather only listed running/waiting Programs with a Project.
    assert len(rows) == 1, (program, expected, response.json())
    assert rows[0]["source_ref"] == "programs:today"


def test_room_failure_stays_partial_and_does_not_fall_back_to_private_sql(hub, monkeypatch):
    from holdspeak.services.project_service import ProjectService

    _room_day(hub)

    def unavailable(*args, **kwargs):
        raise RuntimeError("Room facts unavailable")

    monkeypatch.setattr(ProjectService, "briefing_facts", unavailable, raising=False)
    response = hub.client.post("/api/brief/generate")
    assert response.status_code == 200, response.text
    brief = response.json()
    assert any(row["source_ref"] == "not_read:room" for row in brief["sections"]["waiting"])
    assert not any(str(row["source_ref"]).startswith("meeting_watch:") for row in brief["sections"]["this_week"])


@pytest.mark.parametrize("source", ["history", "calendar"])
def test_an_unread_fact_owner_is_partial_without_a_second_gather(hub, monkeypatch, source):
    from holdspeak.services import today_service
    from holdspeak.services.calendar_service import CalendarService

    _history_day(hub)

    def unavailable(*args, **kwargs):
        raise RuntimeError("Source unavailable")

    if source == "history":
        monkeypatch.setattr(today_service, "since_morning_read", unavailable)
    else:
        monkeypatch.setattr(CalendarService, "lookahead", unavailable, raising=False)
    response = hub.client.post("/api/brief/generate")
    assert response.status_code == 200, response.text
    brief = response.json()
    assert any(row["source_ref"] == f"not_read:{source}" for row in brief["sections"]["waiting"])
    if source == "history":
        assert not any(row["text"].startswith(("Action done:", "Decision made:", "Project added:", "Meeting recorded:"))
                       for row in brief["sections"]["changed"])


def test_calendar_lookahead_uses_the_calendar_owners_occurrences_and_recording_dedup(hub, monkeypatch):
    from holdspeak.calendar_ingest import parse_calendar_bytes
    from holdspeak.services.calendar_service import CalendarService

    now = datetime.now(timezone.utc).replace(microsecond=0)
    end = now + timedelta(days=1)
    # One recorded occurrence in the lookback and its next recurring occurrence.
    # Both start after now to exercise the recorded-event exclusion explicitly.
    starts = (now + timedelta(minutes=30), now + timedelta(hours=1))
    events = "".join(f"BEGIN:VEVENT\r\nUID:review\r\nDTSTART:{at:%Y%m%dT%H%M%SZ}\r\n"
                     f"DTEND:{at + timedelta(minutes=20):%Y%m%dT%H%M%SZ}\r\nSUMMARY:Review\r\nEND:VEVENT\r\n"
                     for at in starts)
    parsed = parse_calendar_bytes(("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n" + events + "END:VCALENDAR\r\n").encode(),
                                  now=now, subscription_revision="fact-owner")
    assert parsed.events, parsed
    hub.db.calendar_events.replace_projection("fact-owner", parsed.events, seen_at=now.timestamp())
    recorded, upcoming = sorted(parsed.events, key=lambda event: event.starts_at)
    hub.db.meetings.save_meeting(MeetingState(id="recorded-occurrence", title="Earlier review", started_at=now - timedelta(minutes=10),
                                             ended_at=now, calendar_event_id=recorded.id))
    hub.db.scheduled_recordings.create(title="Review", cron_expr="0 9 * * *", enabled=True,
                                       calendar_event_id=upcoming.id)
    read = CalendarService.lookahead
    answers = []

    def record(self, *args, **kwargs):
        answer = read(self, *args, **kwargs)
        answers.append(answer)
        return answer

    monkeypatch.setattr(CalendarService, "lookahead", record)
    service = MondayBriefService(hub.db)
    history = service._history((now - timedelta(hours=1)).isoformat(), now.isoformat())
    excluded = service._recorded_calendar_event_ids("", "", history=history)
    items = service._collect_calendar_events(now.isoformat().replace("+00:00", "Z"),
                                              end.isoformat().replace("+00:00", "Z"),
                                              now.isoformat().replace("+00:00", "Z"), exclude_event_ids=excluded)
    assert len(answers) == 1
    expected = [row for row in answers[0] if row["id"] not in excluded]
    assert [row["id"] for row in expected] == [upcoming.id]
    assert {item.text for item in items if item.source_ref in ("calendar:week", "calendar:armed")} == {
        "1 meeting this week", "1 armed",
    }
    assert [item.source_ref for item in items if item.text.startswith("Next:")] == [f"calendar_event:{upcoming.id}"]


def test_digest_keeps_the_doors_snoozed_task_out(hub):
    from holdspeak.runtime import composition
    from holdspeak.services.briefing_service import BriefingService

    today = datetime.now().astimezone().date()
    failed, action = hub.mcp("door.add_item", {"task": "Read the review later", "owner": "Me", "due": today.isoformat()})
    assert not failed, action
    follow = composition.current().follow_through_service
    follow.complete(OWNER, action["id"], "snooze", {"until": (today + timedelta(days=2)).isoformat()})
    door = composition.current().door_service.asking_board(OWNER)
    assert not any(row["id"] == action["id"] for lane in door.values() for row in lane)
    assert BriefingService(hub.db).digest_lines() == []


def test_program_counts_in_the_brief_match_the_seeded_today_face(tmp_path):
    from tests.unit.test_desk_today import _programs_day

    rig, client = _programs_day(tmp_path)
    today = client.get("/api/today/since-morning")
    assert today.status_code == 200, today.text
    expected = today.json()["programs"]
    assert expected["running"] and expected["waiting"] and expected["merged"]
    brief = MondayBriefService(rig.db).generate(OWNER, people_reads=False)
    rows = [row for row in brief.sections["changed"] if row.text == "Programs"]
    assert len(rows) == 1
    assert rows[0].detail == (f"{expected['running']} running, {expected['waiting']} waits on you, "
                              f"{expected['merged']} PR merged")
