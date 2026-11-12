"""Every Calls answer uses the exact tool details read before the question."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak import operations
from holdspeak.calls.aiphone import Reply
from holdspeak.calls.runner import CallRecord, CallRunner
from holdspeak.calls.service import CallsService, DeskTurns
from holdspeak.calls_operations import CALLS_OPERATIONS
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.thread_service import ThreadService
from holdspeak.services.thread_tools import ThreadToolExecutor
from holdspeak.services.thread_turns import _ToolExecutorAggregator
from holdspeak.web.context import WebContext
from holdspeak.web.routes.calls import build_calls_router

OWNER = Principal(PrincipalKind.OWNER, "owner-binding")
CALLER = Principal(PrincipalKind.AGENT, "calling-agent")


@pytest.fixture
def rig(tmp_path, monkeypatch):
    db = Database(tmp_path / "calls.db")
    thread = db.threads.create_thread(title="Held task")
    executor = ThreadToolExecutor(db, principal=CALLER, dispatch_fn=lambda *_: {"ok": True},
                                  control_mode_fn=lambda: "safe")
    handle = executor.admit("call-turn", thread.id, {"id": "held-task", "name": "door.add_item", "arguments": {
        "task": "Email Dana about the cutover", "owner": "Karol",
    }})
    aggregator = _ToolExecutorAggregator()
    aggregator.register("call-message", executor)
    monkeypatch.setattr(ThreadService, "_tool_executor", aggregator)
    turns = DeskTurns(db, lambda **_: None)
    record = CallRecord(phone_call_id="phone-binding", direction="in", thread_id=thread.id, state="live")
    async def save(_):
        pass
    runner = CallRunner(None, record, turns=turns, passphrase="", allowed_numbers=[], greeting="",
                        emit=lambda *_: None, save_note=save)
    details = ThreadService.held_tool_details(OWNER, handle.thread_id, handle.call_id)
    record.hold = {**details, "label": details["words"]}
    record.held_callers = [CALLER]
    service = CallsService()
    service._keep(record)
    service._runners[record.id] = runner
    registry = operations.bind({"calls_service": service}, CALLS_OPERATIONS)
    from holdspeak.mcp import tools
    monkeypatch.setattr(tools, "runtime_registry", lambda: registry)
    from holdspeak.calls import service as calls_module
    monkeypatch.setattr(calls_module, "CALLS", service)
    principal = [OWNER]
    app = FastAPI()
    @app.middleware("http")
    async def authenticated(request, call_next):
        request.state.principal = principal[0]
        return await call_next(request)
    app.include_router(build_calls_router(WebContext(get_state=lambda: {}, operations=registry)))
    with TestClient(app) as client:
        yield SimpleNamespace(db=db, executor=executor, handle=handle, turns=turns, record=record,
                              runner=runner, service=service, registry=registry, client=client, principal=principal)
    db.close()


def press(rig, transport, binding):
    body = {"call_id": rig.record.id, "decision": "approve"}
    if binding is not None:
        body["binding"] = binding
    if transport == "http":
        response = rig.client.post(f"/api/calls/{rig.record.id}/decide", json=body)
        return response.status_code, response.json()
    try:
        if transport == "service":
            answer = rig.service.decide(rig.record.id, "approve", **({"binding": binding} if binding is not None else {}))
        else:
            from holdspeak.mcp.tools import dispatch
            answer = dispatch("calls.decide", body, OWNER)
        return 200, answer
    except ServiceError as error:
        return error.context.get("status", 409), {"code": error.code}


@pytest.mark.parametrize("transport", ["service", "http", "mcp"])
@pytest.mark.parametrize("changed", [False, True])
def test_missing_or_stale_call_details_refuse_the_answer(rig, transport, changed):
    binding = rig.record.hold["binding"] if changed else None
    rig.handle.args["task"] = "Publish the cutover plan"
    status, body = press(rig, transport, binding)
    assert status == 409, body
    assert body.get("code", body.get("reason")) == "answer_stale", body
    assert rig.handle.state == "awaiting_decision"
    assert rig.record.results == []


@pytest.mark.parametrize("transport", ["service", "http", "mcp"])
def test_the_read_call_binding_approves_only_one_time(rig, transport):
    read = rig.client.get(f"/api/calls/{rig.record.id}").json()["hold"]
    assert read["facts"] == [{"label": "Task", "value": "Email Dana about the cutover"},
                             {"label": "Owner", "value": "Karol"}]
    assert press(rig, transport, read["binding"])[0] == 200
    assert rig.handle.state == "admitted"
    assert press(rig, transport, read["binding"])[0] == 409


def test_the_port_and_thread_decision_share_the_same_guard(rig):
    before = []
    binding = rig.record.hold["binding"]
    with pytest.raises(ServiceError) as agent:
        ThreadService.answer_tool_handle(rig.handle, "approve", principal=CALLER, binding=binding)
    assert agent.value.code == "owner_required"
    rig.handle.args["task"] = "Changed"
    with pytest.raises(ServiceError) as stale:
        ThreadService.answer_tool_handle(rig.handle, "approve", principal=OWNER, binding=binding,
                                         before_answer=lambda: before.append(True))
    assert stale.value.code == "answer_stale" and before == []
    service = ThreadService(rig.db, broadcast=lambda *_: None)
    with pytest.raises(ServiceError) as missing:
        service.decide_tool(OWNER, rig.handle.thread_id, rig.handle.call_id, "approve", always=True)
    assert missing.value.code == "answer_stale"
    assert rig.handle.state == "awaiting_decision"
    assert rig.db.threads.effective_tool_policy(rig.handle.thread_id, rig.handle.name) is None


@pytest.mark.parametrize("principal", [CALLER, OWNER, Principal(PrincipalKind.AGENT, "stranger"),
                                       Principal(PrincipalKind.BRIEFING, "page")])
def test_only_the_owner_and_caller_read_the_question_facts(rig, principal):
    rig.principal[0] = principal
    response = rig.client.get(f"/api/calls/{rig.record.id}")
    if principal in (CALLER, OWNER):
        assert response.status_code == 200
        assert response.json()["hold"]["facts"] == rig.record.hold["facts"]
    else:
        assert response.status_code == 403
        assert "Email Dana" not in response.text


def test_completed_call_keeps_the_question_read_scope(rig):
    binding = rig.record.hold["binding"]
    assert press(rig, "service", binding)[0] == 200
    rig.record.add("holdspeak", "Task: Email Dana about the cutover")
    rig.record.state = "ended"
    rig.principal[0] = Principal(PrincipalKind.AGENT, "stranger")
    response = rig.client.get(f"/api/calls/{rig.record.id}")
    assert response.status_code == 403 and "Email Dana" not in response.text
    assert rig.service.get(rig.record.id, CALLER)["hold"] is None


def test_spoken_yes_after_arguments_change_approves_nothing_and_reads_again(rig):
    class Phone:
        said = []
        heard = 0
        async def say(self, text, **_):
            self.said.append(text)
            return Reply(0, {"ok": True})
        async def listen(self, **_):
            self.heard += 1
            if self.heard == 1:
                rig.handle.args["task"] = "Publish the cutover plan"
                return Reply(0, {"ok": True, "kind": "heard", "text": "yes"})
            return Reply(0, {"ok": True, "kind": "ended"})
    phone = Phone()
    rig.runner._phone = phone
    asyncio.run(rig.runner._ask(rig.handle.call_id, rig.handle.name))
    assert rig.handle.state == "awaiting_decision"
    assert rig.record.results == []
    assert any("Email Dana" in text for text in phone.said)
    assert any("Nothing was approved" in text for text in phone.said)
    assert any("Publish the cutover plan" in text for text in phone.said)


def test_record_the_real_calls_question_and_stale_refusal(rig, tmp_path):
    from pathlib import Path
    from tests.unit.test_desk_speak import _record
    rig.record.hold, _question, _noop = rig.runner._question(rig.handle.call_id, rig.handle.name)
    read = rig.client.get(f"/api/calls/{rig.record.id}").json()
    rig.handle.args["task"] = "Publish the cutover plan"
    status, stale = press(rig, "http", read["hold"]["binding"])
    assert status == 409
    refreshed = rig.client.get(f"/api/calls/{rig.record.id}").json()
    assert refreshed["hold"]["binding"] != read["hold"]["binding"]
    assert refreshed["hold"]["facts"][0]["value"] == "Publish the cutover plan"
    assert press(rig, "http", refreshed["hold"]["binding"])[0] == 200
    _record("calls.held.binding", {"read": read, "stale": stale, "refreshed": refreshed,
        "answered": rig.service.get(rig.record.id)}, tmp_path,
        "tests/integration/test_calls_held_binding.py::test_record_the_real_calls_question_and_stale_refusal",
        folder=Path(__file__).parents[1] / "fixtures")
