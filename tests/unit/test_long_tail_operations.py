"""Shared transports preserve results and refuse owner-only effects."""
from __future__ import annotations

import base64
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak import operations
from holdspeak.db import Database
from holdspeak.mcp.families import declared
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.calendar_service import CalendarService
from holdspeak.services.errors import ServiceError
from holdspeak.services.watch_service import WatchService
from holdspeak.web.routes.calendar_snapshot import build_calendar_snapshot_router
from holdspeak.web.routes.watches import build_watches_router
from tests.watch_seed import seed_watch

OWNER = Principal(PrincipalKind.OWNER, "owner")
AGENT = Principal(PrincipalKind.AGENT, "agent")


def client(router, principal=OWNER):
    app = FastAPI()

    @app.middleware("http")
    async def authenticated(request, call_next):
        request.state.principal = principal
        return await call_next(request)

    app.include_router(router)
    return TestClient(app)


def bind_tools(monkeypatch, **services):
    registry = operations.bind_available(services)
    monkeypatch.setattr("holdspeak.mcp.tools.runtime_registry", lambda: registry)
    return registry


def test_calendar_upload_and_tool_extract_the_same_reviewable_events(monkeypatch):
    context = SimpleNamespace(_snapshot_extractor=lambda payload: json.dumps({
        "anchor_date": "2026-11-09", "anchor_confidence": "visible_header",
        "events": [{"title": "Standup", "weekday": "monday", "start_time": "09:00", "end_time": "09:30"}],
    }))
    context.operations = bind_tools(monkeypatch, calendar_service=CalendarService(context))
    png = (Path(__file__).parents[1] / "fixtures/philo13/calendar-input.png").read_bytes()
    web = client(build_calendar_snapshot_router(context)).post("/api/calendar/snapshot",
        files=[("files", ("calendar.png", png, "image/png"))])
    mcp = declared.dispatch("calendar.snapshot.extract", {"images": [{
        "content_type": "image/png", "data_base64": base64.b64encode(png).decode("ascii"),
    }]}, OWNER)
    assert web.status_code == 200
    assert web.json() == mcp
    assert mcp["events"][0]["title"] == "Standup"
    assert mcp["anchor_date"] == "2026-11-09"


def test_calendar_agent_refused_before_image_read_or_model(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("An agent reached the upload or model")

    context = SimpleNamespace(_snapshot_extractor=forbidden)
    context.operations = bind_tools(monkeypatch, calendar_service=CalendarService(context))
    from starlette.datastructures import UploadFile
    monkeypatch.setattr(UploadFile, "read", forbidden)
    response = client(build_calendar_snapshot_router(context), AGENT).post("/api/calendar/snapshot",
        files=[("files", ("calendar.png", b"refused", "image/png"))])
    assert response.status_code == 403
    with pytest.raises(operations.OperationOwnerRequired):
        declared.dispatch("calendar.snapshot.extract", {"images": []}, AGENT)


def test_watch_list_tool_and_http_keep_project_and_state_filter(tmp_path, monkeypatch):
    db = Database(tmp_path / "watches.db")
    for ident, project in (("ours", "project-a"), ("other", "project-b")):
        seed_watch(db, watch_id=ident, connector_id="gh", query_kind="pull_requests",
                   name=ident, query={"repository": "org/repo"})
        db.automations.update_watch_spec(ident, project_id=project)
    service = WatchService(db)
    service.pause_watch(OWNER, "ours")
    context = SimpleNamespace(watch_service=service, operations=bind_tools(monkeypatch, watch_service=service))
    web = client(build_watches_router(context)).get("/api/projects/project-a/watches?state=paused")
    mcp = declared.dispatch("project.watch.list", {"project_id": "project-a", "state": "paused"}, OWNER)
    assert web.status_code == 200
    assert web.json() == mcp
    assert [row["id"] for row in mcp["watches"]] == ["ours"]
    assert declared.dispatch("project.watch.list", {"project_id": "project-a", "state": "retired"}, OWNER) == {"watches": []}
    with pytest.raises(operations.OperationOwnerRequired):
        declared.dispatch("project.watch.list", {"project_id": "project-a"}, AGENT)
    db.close()


@pytest.mark.parametrize("operation", ["project.watch.update", "project.watch.baseline"])
def test_new_watch_write_tools_refuse_agents_without_state_change(tmp_path, monkeypatch, operation):
    db = Database(tmp_path / "watch-write.db")
    seed_watch(db, watch_id="watch", connector_id="gh", query_kind="pull_requests",
               name="Original", query={"repository": "org/repo"})
    def forbidden(*args, **kwargs):
        pytest.fail("An agent reached a watch source")
    service = WatchService(db, snapshot_fetcher=forbidden)
    registry = bind_tools(monkeypatch, watch_service=service)
    before = service.get_watch(OWNER, "watch")
    with pytest.raises(operations.OperationOwnerRequired):
        declared.dispatch(operation, {"watch_id": "watch"}, AGENT)
    assert service.get_watch(OWNER, "watch") == before
    row = registry.descriptor(operation)
    assert row.owner_press
    assert row.authority != "work"
    db.close()


def test_interview_tool_uses_service_projection_and_refuses_agent(tmp_path, monkeypatch):
    from holdspeak.mcp.families import interview
    from holdspeak.services.interview_service import InterviewService
    from holdspeak.services.interview_contracts import INTERVIEW_MODE_ID

    db = Database(tmp_path / "interview.db")
    thread = db.threads.create_thread(recipe_id=INTERVIEW_MODE_ID)
    monkeypatch.setattr(interview, "get_database", lambda: db)
    service = InterviewService(db)
    assert interview.dispatch("interview.get", {"thread_id": thread.id}, OWNER) == service.model_context(OWNER, thread.id)
    with pytest.raises(ServiceError, match="owner"):
        service.model_context(AGENT, thread.id)
    db.close()


def test_feedback_tool_replays_the_http_bundle_without_losing_context(tmp_path, monkeypatch):
    from holdspeak.services import ui_feedback
    from holdspeak.web.routes.system.ui_feedback import build_ui_feedback_router
    from tests.integration.test_desk_ui_feedback import _payload

    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    monkeypatch.setattr(ui_feedback, "feedback_root", lambda home=None: tmp_path / "feedback")
    service = ui_feedback.FeedbackService()
    context = SimpleNamespace(operations=bind_tools(monkeypatch, feedback_service=service))
    payload = _payload(note="Keep these words")
    web = client(build_ui_feedback_router(context)).post("/api/ui-feedback", json=payload)
    assert web.status_code == 200
    assert declared.dispatch("ui_feedback.save", {"payload": payload}, OWNER) == web.json()
    report_path = Path(web.json()["directory"]) / "report.json"
    assert json.loads(report_path.read_text())["context"] == payload["context"]
    with pytest.raises(operations.OperationOwnerRequired):
        declared.dispatch("ui_feedback.save", {"payload": payload}, AGENT)


def test_meeting_followup_is_the_same_draft_on_both_transports(tmp_path, monkeypatch):
    from holdspeak.meeting_session import MeetingState
    from holdspeak.services.meeting_aftercare_service import MeetingAftercareService
    from holdspeak.timestamps import utc_now
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.meetings.aftercare import build_aftercare_router

    db = Database(tmp_path / "aftercare.db")
    db.meetings.save_meeting(MeetingState(id="meeting", title="Planning", started_at=utc_now()))
    service = MeetingAftercareService(db)
    context = WebContext(get_state=lambda: {}, meeting_aftercare_service=service)
    context.operations = bind_tools(monkeypatch, meeting_aftercare_service=service)
    web = client(build_aftercare_router(context)).get("/api/meetings/meeting/followup-draft")
    assert web.status_code == 200
    assert declared.dispatch("meeting.followup_draft", {"meeting_id": "meeting"}, OWNER) == web.json()
    assert web.json()["is_empty"] is True
    with pytest.raises(operations.OperationOwnerRequired):
        declared.dispatch("meeting.aftercare_file_issue", {"meeting_id": "meeting", "action_item_id": "absent", "repo": "org/repo"}, AGENT)
    assert not db.actuators.list_proposals("meeting")
    db.close()


def test_ask_reads_share_the_service_and_keep_retained_runs_owner_only(tmp_path, monkeypatch):
    from holdspeak.services.ask_service import AskService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.primitives.ask import build_ask_router

    db = Database(tmp_path / "ask.db")
    service = AskService(db)
    context = WebContext(get_state=lambda: {})
    context.operations = bind_tools(monkeypatch, ask_service=service)
    web = client(build_ask_router(context)).get("/api/ask/runs?ids=unknown")
    assert web.status_code == 200
    assert web.json() == declared.dispatch("ask.runs", {"ids": "unknown"}, OWNER)
    assert declared.dispatch("ask.engine_tools", {}, OWNER) == service.engine_tools()
    with pytest.raises(operations.OperationOwnerRequired):
        declared.dispatch("ask.runs", {"ids": "unknown"}, AGENT)
    db.close()
