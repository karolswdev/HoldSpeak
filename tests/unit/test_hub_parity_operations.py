"""The remaining adapters use the bound service contract, without granting agent authority."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak import operations
from holdspeak.config import Config
from holdspeak.db.core import Database
# The route regression also runs against a main archive before this table exists.
try:
    from holdspeak.parity_operations import PARITY_OPERATIONS
except ImportError:
    PARITY_OPERATIONS = ()
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.actuator_service import ActuatorProposalService
from holdspeak.services.delivery_service import DeliveryService
from holdspeak.services.meeting_aftercare_service import MeetingAftercareService
from holdspeak.services.project_service import ProjectService
from holdspeak.services.setup_service import SetupService
from holdspeak.services.system_service import SystemService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.desk_actuators import build_desk_actuators_router
from holdspeak.web.routes.meetings.aftercare import build_aftercare_router
from holdspeak.web.routes.mcp_http import build_mcp_http_router
from holdspeak.web.routes.missioncontrol import build_missioncontrol_router
from holdspeak.web.routes.projects import build_projects_router
from holdspeak.web.routes.setup import build_setup_router

OWNER = Principal(PrincipalKind.OWNER, "parity-owner")
AGENT = Principal(PrincipalKind.AGENT, "parity-agent")


@pytest.fixture
def edge(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    ctx = WebContext(get_state=lambda: {})
    ctx.project_service = ProjectService(db)
    ctx.setup_service = SetupService(db)
    ctx.delivery_service = DeliveryService(db).configure(map_path=tmp_path / "absent-map.json")
    ctx.meeting_aftercare_service = MeetingAftercareService(db)
    ctx.actuator_service = ActuatorProposalService(db, Config, lambda *a: None, None)
    system = SystemService(ctx)
    ctx.operations = operations.bind_available({
        "project_service": ctx.project_service, "setup_service": ctx.setup_service,
        "delivery_service": ctx.delivery_service, "meeting_aftercare_service": ctx.meeting_aftercare_service,
        "actuator_service": ctx.actuator_service, "system_service": system,
    })
    invoke = Mock(wraps=ctx.operations.invoke)
    monkeypatch.setattr(ctx.operations, "invoke", invoke)
    app = FastAPI()

    @app.middleware("http")
    async def identity(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    for build in (build_desk_actuators_router, build_aftercare_router, build_mcp_http_router,
                  build_missioncontrol_router, build_projects_router, build_setup_router):
        app.include_router(build(ctx))
    with TestClient(app, client=("127.0.0.1", 5147)) as client:
        yield client, invoke


@pytest.mark.parametrize("name,verb,path,payload,status", [
    ("desk.actuators.status", "GET", "/api/desk/actuators/status", None, 200),
    ("delivery.belt.state", "GET", "/api/missioncontrol/state", None, 200),
    ("delivery.belt.journal", "GET", "/api/missioncontrol/rails/journal?limit=3", None, 200),
    ("project.people", "GET", "/api/projects/missing/people", None, 404),
    ("setup.discover_models", "POST", "/api/setup/discover-models", {"api_key": "bad\nkey"}, 400),
    ("meeting.slack_export", "POST", "/api/meetings/missing/export/slack", {"what": "digest"}, 400),
    ("system.mcp_message", "POST", "/api/mcp", {"jsonrpc": "2.0", "id": 1, "method": "initialize"}, 200),
])
def test_each_remaining_adapter_invokes_the_bound_operation(edge, name, verb, path, payload, status):
    client, invoke = edge
    response = client.request(verb, path, **({"json": payload} if payload is not None else {}))
    assert response.status_code == status, response.text
    assert name in [call.args[1] for call in invoke.call_args_list]


@pytest.mark.parametrize("row", [row for row in PARITY_OPERATIONS if row.owner_only], ids=lambda row: row.name)
def test_private_rows_refuse_an_agent_before_arguments_or_service(row):
    target = Mock()
    registry = operations.bind({row.service: target}, (row,))
    with pytest.raises(operations.OperationOwnerRequired) as error:
        registry.invoke(AGENT, row.name, {"principal": "owner"})
    assert error.value.code == "owner_required"
    assert target.mock_calls == []


@pytest.mark.parametrize("row", [row for row in PARITY_OPERATIONS if row.tool_schema and row.owner_only], ids=lambda row: row.name)
def test_new_owner_tools_refuse_an_agent_at_mcp_dispatch(row, monkeypatch):
    from holdspeak.mcp import tools
    from holdspeak.mcp.families import declared

    target = Mock()
    registry = operations.bind({row.service: target}, (row,))
    monkeypatch.setattr(tools, "runtime_registry", lambda: registry)
    with pytest.raises(operations.OperationOwnerRequired):
        declared.dispatch(row.name, {}, AGENT)
    assert target.mock_calls == []


def test_actuator_status_is_an_agent_read_without_addresses():
    config = SimpleNamespace(meeting=SimpleNamespace(companion_webhook_url="secret-url", companion_github_repo="private/repo"))
    target = ActuatorProposalService(None, lambda: config, lambda *a: None, None)
    row = next(row for row in PARITY_OPERATIONS if row.name == "desk.actuators.status")
    result = operations.bind({"actuator_service": target}, (row,)).invoke(AGENT, row.name)
    assert result == {"webhook_configured": True, "github_configured": True}
    assert "secret-url" not in str(result) and "private/repo" not in str(result)


def test_private_room_projection_is_not_copied_to_durable_observation(tmp_path):
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
    from holdspeak.services.people_service import PeopleService
    from holdspeak.services.sqlite_observer import SQLiteObserver

    db = Database(tmp_path / "hub-private.db")
    db.projects.create_project(project_id="project-private", name="Private project")
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    person = people.create_relationship(OWNER, {"display_name": "PARITY-PRIVATE-NAME"})
    people.link_project(OWNER, person["id"], "project-private")
    service = ProjectService(db, observer=SQLiteObserver(db._connection))
    answer = service.people_preparation(OWNER, "project-private", people_service=people)
    assert answer["people"][0]["display_name"] == "PARITY-PRIVATE-NAME"
    with db._connection() as conn:
        events = [tuple(row) for row in conn.execute("SELECT args_summary, result_summary FROM pipeline_events")]
    assert events
    assert "PARITY-PRIVATE-NAME" not in str(events)


def test_an_agent_cannot_create_the_owner_update_automation(tmp_path):
    from holdspeak.services.project_update_service import ProjectUpdateService

    db = Database(tmp_path / "update.db")
    updates = ProjectUpdateService(db, project_service=ProjectService(db))
    workbench = Mock()
    updates.bind_workbench(workbench)
    with pytest.raises(operations.OperationOwnerRequired):
        updates.draft_update_command(AGENT, "project", audience="team")
    workbench.ensure_project_update.assert_not_called()


def test_belt_journal_keeps_fastapi_validation_of_its_typed_limit(edge):
    client, invoke = edge
    response = client.get("/api/missioncontrol/rails/journal?limit=words")
    assert response.status_code == 422
    assert not invoke.called


def test_pr_review_tool_refuses_an_unknown_pr_without_an_engine_or_send(tmp_path):
    from holdspeak.services.errors import ServiceError

    cache = Mock()
    cache.action_context.return_value = {"status": "unknown_pr"}
    target = DeliveryService(Database(tmp_path / "review.db")).configure(prs=cache)
    row = next(row for row in PARITY_OPERATIONS if row.name == "delivery.pr_draft_review")
    registry = operations.bind({"delivery_service": target}, (row,))
    with pytest.raises(ServiceError) as refused:
        registry.invoke(OWNER, row.name, {"source_id": "missing", "number": 1})
    assert refused.value.code == "unknown_pr"
    assert refused.value.context["status"] == 404
    cache.review_material.assert_not_called()


def test_cached_owner_attention_read_refuses_an_agent_before_reading_the_cache(tmp_path):
    cache = Mock()
    service = ProjectService(Database(tmp_path / "cached.db"))
    service.bind_needs_you_cache(cache)
    registry = operations.bind({"project_service": service}, (operations.DESK_NEEDS_YOU,))
    with pytest.raises(operations.OperationOwnerRequired):
        registry.invoke(AGENT, "desk.needs_you", {}, held={"door_upcoming": None}, shape="web")
    cache.get.assert_not_called()
