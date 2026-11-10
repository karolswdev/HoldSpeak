"""Calls and Line declarations enforce authority before reaching their port."""
from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak import operations
from holdspeak.calls_operations import CALLS_OPERATIONS, LINE_OPERATIONS
from holdspeak.principals import Principal, PrincipalKind, UNAUTHENTICATED

OWNER = Principal(PrincipalKind.OWNER, "calls-owner")
AGENT = Principal(PrincipalKind.AGENT, "calls-agent")


@pytest.mark.parametrize("row", [row for row in CALLS_OPERATIONS if row.owner_only], ids=lambda row: row.name)
def test_every_owner_row_refuses_an_agent_before_its_port(row) -> None:
    class Unreached:
        def __getattr__(self, name):
            pytest.fail(f"{row.name} reached its service: {name}")

    registry = operations.bind({"calls_service": Unreached()}, (row,))
    with pytest.raises(operations.OperationOwnerRequired):
        registry.invoke(AGENT, row.name, {"actor": "owner"})


@pytest.fixture
def client(monkeypatch):
    from holdspeak.calls import service
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.calls import build_calls_router

    monkeypatch.setenv("HOLDSPEAK_CALLS", "off")
    monkeypatch.setenv("HOLDSPEAK_LINE", "on")
    monkeypatch.setattr(service, "CALLS", service.CallsService())
    who = {"principal": OWNER}
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next):
        request.state.principal = who["principal"]
        return await call_next(request)

    app.include_router(build_calls_router(WebContext(get_state=lambda: {})))
    with TestClient(app) as http:
        yield http, who


@pytest.mark.parametrize("row", [row for row in CALLS_OPERATIONS if row.owner_only], ids=lambda row: row.name)
def test_every_calls_owner_route_refuses_an_agent_even_without_edge_middleware(client, row) -> None:
    http, who = client
    who["principal"] = AGENT
    method, path = row.http
    answer = http.request(method, path.replace("{node}", "box").replace("{call_id}", "held"), json={})
    assert answer.status_code == 403, answer.text
    assert answer.json()["reason"] == "owner_required"


@pytest.mark.parametrize("verb", [row.method.split(".")[-1] for row in LINE_OPERATIONS if row.held])
def test_wire_rows_cannot_be_called_by_an_agent_or_forge_a_node_in_json(client, verb) -> None:
    http, who = client
    who["principal"] = AGENT
    answer = http.post(f"/api/calls/line/{verb}", json={"node": "this-mac"})
    assert answer.status_code == 403
    assert answer.json()["reason"] == "owner_required"
    row = next(row for row in LINE_OPERATIONS if row.name == f"calls.line.{verb}")
    assert row.tool_schema is None
    assert not any(face.startswith("mcp:") for face in row.exposure)


def test_an_agent_cannot_redeem_an_owner_code_and_the_code_stays_unspent(client, tmp_path, monkeypatch):
    from holdspeak.calls import service
    from holdspeak.delivery.node_link import NodeTokenStore
    from holdspeak.line import service as line_service
    from holdspeak.line.enrol import EnrolCodes

    monkeypatch.setattr(line_service, "CODES", EnrolCodes())
    service.CALLS.line.configure(store=NodeTokenStore(tmp_path / "nodes.json"))
    http, who = client
    code = http.post("/api/calls/line/codes", json={"node": "box"}).json()["code"]
    who["principal"] = AGENT
    refused = http.post("/api/calls/line/enrol", json={"code": code})
    assert refused.status_code == 403 and refused.json()["reason"] == "owner_required"
    who["principal"] = UNAUTHENTICATED
    enrolled = http.post("/api/calls/line/enrol", json={"code": code})
    assert enrolled.status_code == 200 and enrolled.json()["node"] == "box"
    assert enrolled.json()["token"]
    assert http.post("/api/calls/line/enrol", json={"code": code}).status_code == 401


def test_revoke_refuses_a_conflicting_body_and_keeps_the_node_credential(client, tmp_path):
    from holdspeak.calls import service
    from holdspeak.delivery.node_link import NodeTokenStore

    store = NodeTokenStore(tmp_path / "nodes.json")
    service.CALLS.line.configure(store=store)
    http, _ = client
    code = http.post("/api/calls/line/codes", json={"node": "box"}).json()["code"]
    token = http.post("/api/calls/line/enrol", json={"code": code}).json()["token"]
    refused = http.request("DELETE", "/api/calls/line/nodes/box", json={"node": "other"})
    assert refused.status_code == 400 and refused.json()["reason"] == "path_body_mismatch"
    assert store.identify(token) is not None


@pytest.mark.parametrize("body, expected", [({}, "node is required"),
                                          ({"node": "box", "after": "bad"}, "after and wait_s are numbers"),
                                          ({"node": "box", "wait_s": []}, None)])
def test_next_keeps_wire_validation_and_empty_poll_bytes(client, body, expected):
    http, _ = client
    answer = http.post("/api/calls/line/next", json=body)
    if expected:
        assert answer.status_code == 400
        assert answer.content == json.dumps(
            {"error": expected, "reason": "usage"}, separators=(",", ":")).encode()
    else:
        assert answer.status_code == 200 and answer.content == b'{"commands":[]}'


def test_decide_is_an_owner_tool_on_the_same_calls_service(client):
    from holdspeak.calls import service
    from holdspeak.calls.runner import CallRecord
    from holdspeak.mcp.tools import dispatch

    decisions = []
    record = CallRecord(phone_call_id="held", direction="in", remote="sip:owner@example")
    service.CALLS._keep(record)
    service.CALLS._runners[record.id] = SimpleNamespace(
        decide=lambda decision, **kw: decisions.append((decision, kw)) or True)
    assert dispatch("calls.decide", {"call_id": record.id, "decision": "approve"}, OWNER)["id"] == record.id
    assert decisions == [("approve", {"by": "tap"})]
    with pytest.raises(operations.OperationOwnerRequired):
        dispatch("calls.decide", {"call_id": record.id, "decision": "deny"}, AGENT)
    assert decisions == [("approve", {"by": "tap"})]


def test_calls_reads_the_owning_thread_port_without_looking_inside_its_executor(monkeypatch):
    from holdspeak.calls.service import DeskTurns
    from holdspeak.services.thread_service import ThreadService

    handle = object()
    monkeypatch.setattr(ThreadService, "tool_handle", lambda call_id: handle if call_id == "held" else None)
    monkeypatch.setattr(ThreadService, "_tool_executor", object())
    assert DeskTurns._handle("held") is handle
    assert DeskTurns._handle("released") is None


def test_cancelled_http_poll_releases_its_waiter_and_keeps_the_next_command(client, monkeypatch):
    import httpx

    from holdspeak.line import service as line_service
    from holdspeak.line.hub import LineHub

    hub = LineHub()
    monkeypatch.setattr(line_service, "LINE_HUB", hub)
    http, _ = client

    async def walk():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=http.app), base_url="http://test") as async_http:
            poll = asyncio.create_task(async_http.post(
                "/api/calls/line/next", json={"node": "box", "wait_s": 25}))

            async def waiting():
                while not hub.waiting("box", "next"):
                    await asyncio.sleep(0.001)

            await asyncio.wait_for(waiting(), 2)
            poll.cancel()
            with pytest.raises(asyncio.CancelledError):
                await poll
            assert not hub.waiting("box", "next")
            cmd = hub.queue("box", "say", call_id="c1", text="Hello.")
            answer = await async_http.post("/api/calls/line/next", json={"node": "box", "wait_s": 0})
            assert answer.status_code == 200
            assert answer.json() == {"commands": [{"id": cmd, "op": "say", "call_id": "c1", "text": "Hello."}]}

    asyncio.run(walk())
