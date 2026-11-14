"""The owner sees the declared write before deciding its exact saved content."""
from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak import operations
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind, PrincipalRight, required_right
from holdspeak.services.errors import ServiceError
from holdspeak.services.thread_service import ThreadService
from holdspeak.services.thread_tools import ThreadToolExecutor
from holdspeak.services.thread_turns import _ToolExecutorAggregator
from holdspeak.thread_operations import THREAD_OPERATIONS
from holdspeak.web.context import WebContext
from holdspeak.web.routes.threads import build_threads_router

OWNER = Principal(PrincipalKind.OWNER, "owner")
CALLER = Principal(PrincipalKind.AGENT, "caller")


def test_only_the_exact_held_read_gets_the_agent_read_edge_right():
    assert required_right("GET", "/api/threads/t/held/c") is PrincipalRight.AGENT_READ
    for method, path in [("POST", "/api/threads/t/held/c"), ("GET", "/api/threads/t"),
                         ("GET", "/api/threads/t/held/c/extra"), ("POST", "/api/threads/t/decide")]:
        assert required_right(method, path) is PrincipalRight.OWNER


def test_the_real_http_edge_admits_only_the_calling_agents_read(tmp_path, monkeypatch):
    from tests.integration.test_principal_separation import _server
    from holdspeak.principals import agent_credentials

    server, owner, db = _server(tmp_path, monkeypatch)
    clients = []
    try:
        for identity in ("held-caller", "held-stranger"):
            token = owner.post("/api/principals/agents", json={"identity": identity}).json()["credential"]
            client = TestClient(server.app)
            client.headers.pop("x-holdspeak-token", None)
            client.headers["Authorization"] = f"Bearer {token}"
            clients.append((client, agent_credentials.derive(token)))
        thread = db.threads.create_thread(title="Held task")
        executor = ThreadToolExecutor(db, dispatch_fn=lambda *_: {}, principal=clients[0][1],
                                      control_mode_fn=lambda: "safe")
        handle = executor.admit("real-edge", thread.id, {
            "id": "edge-task", "name": "door.add_item", "arguments": {"task": "Email Dana"},
        })
        aggregator = _ToolExecutorAggregator()
        aggregator.register("edge-message", executor)
        monkeypatch.setattr(ThreadService, "_tool_executor", aggregator)
        path = f"/api/threads/{thread.id}/held/{handle.call_id}"
        details = clients[0][0].get(path)
        assert details.status_code == 200
        assert details.json()["facts"] == [{"label": "Task", "value": "Email Dana"}]
        assert owner.get(path).json() == details.json()
        assert clients[1][0].get(path).status_code == 403
        assert clients[0][0].get(f"/api/threads/{thread.id}").status_code == 403
        assert clients[0][0].post(f"/api/threads/{thread.id}/decide", json={
            "call_id": handle.call_id, "decision": "approve", "binding": details.json()["binding"],
        }).status_code == 403
        assert handle.state == "awaiting_decision"
    finally:
        for identity in ("held-caller", "held-stranger"):
            agent_credentials.revoke(identity)
        db.close()


@pytest.fixture
def rig(tmp_path, monkeypatch):
    db = Database(tmp_path / "held.db")
    service = ThreadService(db, broadcast=lambda *_: None)
    thread = db.threads.create_thread(title="Cutover")
    executor = ThreadToolExecutor(db, dispatch_fn=lambda *_: {"ok": True}, principal=CALLER,
                                  control_mode_fn=lambda: "safe")
    handle = executor.admit("turn", thread.id, {"id": "held-task", "name": "door.add_item", "arguments": {
        "task": "Email Dana about the cutover", "owner": "Karol", "due": "2026-11-13",
    }})
    aggregator = _ToolExecutorAggregator()
    aggregator.register("message", executor)
    monkeypatch.setattr(ThreadService, "_tool_executor", aggregator)
    registry = operations.bind({"hub_thread_service": lambda: service}, THREAD_OPERATIONS)
    from holdspeak.mcp import tools
    monkeypatch.setattr(tools, "runtime_registry", lambda: registry)
    current = [OWNER]
    app = FastAPI()

    @app.middleware("http")
    async def authenticated(request, call_next):
        request.state.principal = current[0]
        return await call_next(request)

    app.include_router(build_threads_router(WebContext(get_state=lambda: {}, operations=registry)))
    with TestClient(app) as client:
        yield service, handle, registry, client, current
    db.close()


def read(rig, principal=OWNER):
    service, handle, *_ = rig
    return service.held_tool_details(principal, handle.thread_id, handle.call_id)


def url(rig):
    h = rig[1]
    return f"/api/threads/{h.thread_id}/held/{h.call_id}"


def test_the_service_and_http_read_carry_the_declared_write_facts(rig):
    expected = [{"label": "Task", "value": "Email Dana about the cutover"},
                {"label": "Owner", "value": "Karol"}, {"label": "Due", "value": "2026-11-13"}]
    details = read(rig)
    assert details["words"] == "Add a task"
    assert details["facts"] == expected
    assert rig[3].get(url(rig)).json() == details
    assert rig[2].invoke(CALLER, "thread.held", {
        "thread_id": rig[1].thread_id, "call_id": rig[1].call_id,
    }) == details
    from holdspeak.mcp.tools import dispatch
    assert dispatch("thread.held", {"thread_id": rig[1].thread_id, "call_id": rig[1].call_id}, CALLER) == details
    assert "arguments" not in details


@pytest.mark.parametrize("kind", ["secret", "token", "credential", "file bytes"])
def test_a_hidden_argument_never_leaves_the_read(rig, monkeypatch, kind):
    from holdspeak.mcp import tools

    tool = next(t for t in tools.TOOLS if t["name"] == "door.add_item")
    schema = dict(tool["inputSchema"])
    schema["properties"] = {**schema["properties"], "private": {"type": "string"}}
    schema["x-held-arguments"] = [*schema["x-held-arguments"], {
        "key": "private", "label": "Private", "kind": kind,
    }]
    monkeypatch.setitem(tool, "inputSchema", schema)
    rig[1].args["private"] = "never-send-this-value"
    response = rig[3].get(url(rig))
    assert response.status_code == 200
    assert "never-send-this-value" not in response.text
    assert {"label": "Private", "value": "Hidden"} in response.json()["facts"]
    binding = response.json()["binding"]
    rig[1].args["private"] = "changed-secret"
    assert read(rig)["binding"] != binding


@pytest.mark.parametrize("principal", [Principal(PrincipalKind.AGENT, "other"),
    Principal(PrincipalKind.BRIEFING, "caller"), Principal(PrincipalKind.NONE, "caller"),
    Principal(PrincipalKind.NODE, "caller")])
def test_another_agent_or_token_page_cannot_read_the_call(rig, principal):
    with pytest.raises(ServiceError) as error:
        read(rig, principal)
    assert error.value.code == "held_call_forbidden"
    rig[4][0] = principal
    response = rig[3].get(url(rig))
    assert response.status_code == 403
    assert "Email Dana" not in response.text
    with pytest.raises(ServiceError, match="another principal"):
        rig[2].invoke(principal, "thread.held", {"thread_id": rig[1].thread_id, "call_id": rig[1].call_id})


def test_the_calling_agent_can_read_but_cannot_decide(rig):
    rig[4][0] = CALLER
    assert rig[3].get(url(rig)).json() == read(rig, CALLER)
    response = rig[3].post(url(rig).split("/held/")[0] + "/decide", json={
        "call_id": rig[1].call_id, "decision": "approve", "binding": read(rig, CALLER)["binding"],
    })
    assert response.status_code == 403
    assert "requires the owner" in response.json()["error"]
    assert rig[1].state == "awaiting_decision"


@pytest.mark.parametrize("decision", ["approve", "deny"])
@pytest.mark.parametrize("stale", [True, False])
def test_missing_or_stale_details_are_refused_before_allow_always_or_deny(rig, decision, stale):
    binding = read(rig)["binding"] if stale else None
    rig[1].args["task"] = "Delete the cutover plan"
    response = rig[3].post(url(rig).split("/held/")[0] + "/decide", json={
        "call_id": rig[1].call_id, "decision": decision, "always": True, "binding": binding,
    })
    assert response.status_code == 409
    assert response.json()["code"] == "answer_stale"
    assert "Read again" in response.json()["error"]
    assert rig[1].state == "awaiting_decision"
    assert rig[0]._threads.effective_tool_policy(rig[1].thread_id, rig[1].name) is None


@pytest.mark.parametrize("decision,state", [("approve", "admitted"), ("deny", "denied")])
def test_a_current_binding_answers_once(rig, decision, state):
    body = {"call_id": rig[1].call_id, "decision": decision, "binding": read(rig)["binding"]}
    endpoint = url(rig).split("/held/")[0] + "/decide"
    assert rig[3].post(endpoint, json=body).status_code == 200
    assert rig[1].state == state
    assert rig[3].post(endpoint, json=body).status_code == 409


def test_undeclared_or_structured_values_are_not_described(rig):
    rig[1].args = {"task": {"token": "nested-secret"}, "extra": "unknown-secret"}
    details = read(rig)
    assert {"label": "Task", "value": "not described"} in details["facts"]
    assert "nested-secret" not in json.dumps(details)
    assert "unknown-secret" not in json.dumps(details)
    rig[1].name = "desk.create"
    assert read(rig)["facts"] == [{"label": "Write details", "value": "not described"}]
