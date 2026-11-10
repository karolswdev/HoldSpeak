"""Owner and device boundaries refuse agent effects before dispatch."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import APIRouter, FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak import operations
from holdspeak.agent_operations import AGENT_OPERATIONS
from holdspeak.coder_operations import CODER_OPERATIONS
from holdspeak.delivery_operations import DELIVERY_OPERATIONS
from holdspeak.phone_operations import PHONE_OPERATIONS
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "owner-test")
AGENT = Principal(PrincipalKind.AGENT, "agent-test")
ROWS = AGENT_OPERATIONS + CODER_OPERATIONS + DELIVERY_OPERATIONS + PHONE_OPERATIONS


class Untouched:
    def __getattr__(self, name):
        def fail(*args, **kwargs):
            pytest.fail(f"Refused call reached the service: {name}")
        return fail


@pytest.mark.parametrize("row", [row for row in ROWS if row.owner_only or
    "device" in row.held or "token" in row.held or "node_token" in row.held or row.name == "phone.redeem"],
    ids=lambda row: row.name)
def test_owner_and_device_rows_refuse_agent_before_service(row):
    registry = operations.bind({row.service: Untouched()}, (row,))
    with pytest.raises(operations.OperationOwnerRequired) as exc:
        registry.invoke(AGENT, row.name, {}, held={key: {"id": "paired"} for key in row.held})
    assert exc.value.code == "owner_required"
    assert "owner_required" in row.refusals


@pytest.mark.parametrize("name", ("agent.helper.allow", "agent.launch.answer", "agent.launch.resume"))
def test_launch_authority_cannot_be_self_approved(name):
    row = next(row for row in AGENT_OPERATIONS if row.name == name)
    assert row.owner_only and row.owner_press
    assert row.authority == "authority"
    from holdspeak.services.conductor_launch import NOT_OFFERED
    assert name in NOT_OFFERED


@pytest.mark.parametrize("name", ("agent.hand", "project.repository.register"))
def test_hand_and_repository_declare_their_owner_refusal(name):
    row = next(row for row in AGENT_OPERATIONS if row.name == name)
    assert "owner_required" in row.refusals
    with pytest.raises(operations.OperationOwnerRequired):
        operations.bind({row.service: Untouched()}, (row,)).invoke(AGENT, name, {})


@pytest.mark.parametrize("principal", (OWNER, AGENT), ids=("owner", "agent"))
def test_actuator_proposal_stays_pending_in_yolo(tmp_path, principal):
    from holdspeak.config import Config
    from holdspeak.db import Database
    from holdspeak.services.actuator_service import ActuatorProposalService
    from holdspeak.web_requests import _CompanionSlackRequest

    config = Config()
    config.control_mode = "yolo"
    config.meeting.companion_webhook_url = "https://example.test/hook"
    calls = []
    lifecycle = SimpleNamespace(apply=lambda proposal, target: (calls.append(target), proposal)[1],
        serialize=lambda proposal: {"id": proposal.id, "status": proposal.status})
    db = Database(tmp_path / "hub.db")
    try:
        service = ActuatorProposalService(db, lambda: config, lambda *args: None, lifecycle)
        answer = service.propose_webhook(principal, _CompanionSlackRequest(text="Draft for the owner"))
        proposal = db.actuators.get_proposal(answer["proposal"]["id"])
        assert proposal.status == "proposed"
        assert calls == []
        with pytest.raises(operations.OperationOwnerRequired):
            service.decide_webhook(AGENT, proposal.id, SimpleNamespace(decision="approved"))
        assert db.actuators.get_proposal(proposal.id).status == "proposed"
    finally:
        db.close()


def test_relay_http_uses_declared_row_and_keeps_remote_refusal(monkeypatch):
    from holdspeak.services.coder_service import CoderService
    from holdspeak.web.routes.system.coder_relay_routes import register_relay_routes
    from holdspeak import coder_steering_relay

    principal = [OWNER]
    calls = []
    def relay(node, verb, key, **kwargs):
        calls.append((node, verb, key, kwargs))
        return {"status": "unarmed", "node": node}
    monkeypatch.setattr(coder_steering_relay, "relay", relay)
    service = object.__new__(CoderService)
    service._observer = None
    registry = operations.bind_available({"coder_service": service})
    app = FastAPI()
    @app.middleware("http")
    async def auth(request: Request, call_next):
        request.state.principal = principal[0]
        return await call_next(request)
    router = APIRouter()
    register_relay_routes(router, lambda: registry)
    app.include_router(router)
    with TestClient(app) as client:
        response = client.post("/api/coders/relay/beta/keys", json={"key": "pane:%2", "keys": ["Enter"]})
        assert response.status_code == 409
        assert response.json()["status"] == "unarmed"
        assert calls[-1] == ("beta", "keys", "pane:%2", {"method": "POST", "body": {"keys": ["Enter"]}})
        principal[0] = AGENT
        response = client.post("/api/coders/relay/beta/keys", json={"key": "pane:%2", "keys": ["Enter"]})
        assert response.status_code == 403
        assert len(calls) == 1


def test_owner_relay_text_and_screen_stay_out_of_agent_readable_events(monkeypatch):
    """An agent reads pipeline events: the owner's steering text and the peeked screen are not there."""
    from types import SimpleNamespace
    from holdspeak import coder_steering_relay
    from holdspeak.services.coder_service import CoderService
    from holdspeak.services.errors import ServiceError

    events = []
    answers = iter([{"status": "ok", "screen": "SCREEN_TEXT_DO_NOT_RECORD"}, {"status": "unarmed"}])
    monkeypatch.setattr(coder_steering_relay, "relay", lambda *a, **kw: next(answers))
    monkeypatch.setattr(coder_steering_relay, "relay_http_code", lambda result: 200 if result["status"] == "ok" else 409)
    service = object.__new__(CoderService)
    service._observer = SimpleNamespace(on_event=events.append)

    service.relay(OWNER, "steer", {"node": "beta", "key": "pane:%2", "text": "631904"})
    with pytest.raises(ServiceError):
        service.relay(OWNER, "steer", {"node": "beta", "key": "pane:%2", "text": "631904"})

    recorded = [event for event in events if event.method == "relay"]
    assert len(recorded) == 2
    for event in recorded:
        assert "631904" not in event.args_summary
        assert "steer" in event.args_summary
        assert "SCREEN_TEXT_DO_NOT_RECORD" not in (event.result_summary or "")


def test_pr_proposal_waits_for_owner_then_executes_once(tmp_path, monkeypatch):
    from holdspeak.db import Database
    from holdspeak.kernel import runtime
    from holdspeak.plugins.actuator_executor import ActuatorExecutor
    from holdspeak.services.delivery_service import DeliveryService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes import actuator_shared
    from holdspeak.web.routes.delivery_prs import build_delivery_prs_router
    from tests.unit.test_pr_receipts import FakeSource, FakeWorktree, make_runner, make_service

    source = FakeSource(worktrees=[FakeWorktree(path=str(tmp_path), branch="agent/hs-104-02-tool-call-gate")])
    cache, _, _ = make_service(source=source, runner=make_runner(git_head="a" * 40))
    cache.refresh()
    db = Database(tmp_path / "hub.db")
    broker = runtime._configure(db)
    monkeypatch.setattr(runtime, "_service", lambda: broker)
    sent = []
    def execute(ctx, database, proposal, *, actor):
        return ActuatorExecutor(database, connector=lambda item: sent.append(item.payload) or {"status": 201},
            allow_actuators=True, operation_broker=broker,
            executor_principal=Principal(PrincipalKind.NODE, "actuator-local")).execute(proposal.id)
    monkeypatch.setattr(actuator_shared, "execute_github_proposal", execute)
    service = DeliveryService(db).configure(prs=cache)
    app = FastAPI()
    @app.middleware("http")
    async def auth(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)
    app.include_router(build_delivery_prs_router(WebContext(get_state=lambda: {}, delivery_service=service)))
    try:
        with TestClient(app) as client:
            response = client.post("/api/delivery/prs/src_1/42/propose", json={"body": "Reviewed by the owner"})
            assert response.status_code == 202, response.text
            proposal_id = response.json()["proposal_id"]
            operation_id = response.json()["operation_id"]
            assert db.actuators.get_proposal(proposal_id).status == "proposed"
            assert sent == []
            decide = f"/api/delivery/prs/proposals/{proposal_id}/decide"
            response = client.post(decide, json={"decision": "approve"})
            assert response.status_code == 200, response.text
            assert response.json()["proposal"]["status"] == "executed"
            assert sent == [{"repo": "o/r", "number": 42, "body": "Reviewed by the owner"}]
            assert broker.store.receipt(operation_id)["state"] == "succeeded"
            assert client.post(decide, json={"decision": "approve"}).status_code == 409
            assert len(sent) == 1
    finally:
        db.close()


def test_declared_mcp_refusal_keeps_its_code(monkeypatch):
    import json
    from holdspeak.mcp import server, tools

    registry = operations.bind_available({"coder_service": Untouched()})
    monkeypatch.setattr(tools, "runtime_registry", lambda: registry)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    response = server.handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "coder.list", "arguments": {"principal": "owner"}}})
    assert response["result"]["isError"] is True
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["code"] == "authority_in_arguments"


def test_node_protocol_changes_liveness_without_a_desk_write(tmp_path):
    from holdspeak.db import Database
    from holdspeak.delivery.node_link import NODE_PROTOCOL, NodeLinkState, NodeTokenStore
    from holdspeak.runtime import composition
    from holdspeak.services.delivery_service import DeliveryService

    db = Database(tmp_path / "hub.db")
    frames = []
    composition.install(composition.RuntimeServices(db=db, broadcast=lambda *args: frames.append(args)))
    store = NodeTokenStore(tmp_path / "nodes.json")
    _, token = store.create("lab")
    link = NodeLinkState(store)
    service = DeliveryService(db).configure(link=link, legacy_env={})
    registry = operations.bind_available({"delivery_service": service})
    try:
        registry.invoke(Principal(PrincipalKind.NODE, "lab"), "delivery.node.hello",
            {"name": "lab", "node_protocol": NODE_PROTOCOL, "instance_id": "test", "capabilities": []},
            held={"node_token": token})
        nodes = registry.invoke(OWNER, "delivery.nodes", {})
        assert any(node["name"] == "lab" for node in nodes["nodes"])
        assert frames == []
    finally:
        db.close()
