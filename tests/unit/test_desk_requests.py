"""One display protocol (2026-11-08): the desk's display requests.

``holdspeak/desk_operations.py`` declares ``desk.mark``, ``desk.press``,
``desk.say`` and ``desk.scroll``: each descriptor produces an HTTP route and an
MCP tool. A request is one ``desk_request`` frame ``{request_id, op, args}``;
the compositor answers ``POST /api/desk/requests/{id}/result`` and
``desk.request.read`` returns the answer. Press is the owner's alone.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak import operations  # first: it imports desk_operations
from holdspeak import desk_operations
from holdspeak.db import Database
from holdspeak.mcp import tools as mcp_tools
from holdspeak.mcp.families import declared
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition
from holdspeak.services import desk_window_service
from holdspeak.services.desk_window_service import DeskWindowService
from holdspeak.web import announce
from holdspeak.web.context import WebContext
from holdspeak.web.routes.desk_windows import build_desk_windows_router

OWNER = Principal(PrincipalKind.OWNER, "requests-owner")
AGENT = Principal(PrincipalKind.AGENT, "agent:requests")
REQUESTS = ("desk.mark", "desk.press", "desk.say", "desk.scroll")


@pytest.fixture()
def hub(tmp_path: Path) -> Any:
    db = Database(tmp_path / "r.db")
    frames: list[tuple[str, Any]] = []
    composition.install(composition.RuntimeServices(db=db, broadcast=lambda kind, data: frames.append((kind, data))))
    app = FastAPI()

    @app.middleware("http")
    async def owner(request: Request, call_next):  # noqa: ANN001
        request.state.principal = OWNER
        return await call_next(request)

    announce.install(app)
    app.include_router(build_desk_windows_router(WebContext(get_state=lambda: {}),
                                                 service=lambda: DeskWindowService(db)))
    client = TestClient(app)
    client.frames = frames  # type: ignore[attr-defined]
    try:
        yield client
    finally:
        composition.uninstall()


def test_each_request_produces_a_route_and_a_tool_from_its_descriptor(hub: Any) -> None:
    by_name = {d.name: d for d in operations.DESCRIPTORS}
    paths = {(method, route.path) for route in hub.app.routes for method in getattr(route, "methods", ())}
    for name in REQUESTS + ("desk.request.read",):
        descriptor = by_name[name]
        assert descriptor.http in paths, name
        assert name in declared.NAMES and name in {t["name"] for t in mcp_tools.TOOLS}
        assert next(t for t in declared.TOOLS if t["name"] == name)["inputSchema"] == descriptor.tool_schema
    # The compositor's answer is a route only: no agent answers for the desk.
    assert by_name["desk.request.result"].http in paths and "desk.request.result" not in declared.NAMES


def test_mark_sends_one_desk_request_frame_and_the_answer_comes_back(hub: Any) -> None:
    args = {"target": "needs-row", "window": "chair:needs", "thing": "needs rows", "words": "This one"}
    sent = hub.post("/api/desk/requests/mark", json=args)
    assert sent.status_code == 200, sent.text
    request_id = sent.json()["request_id"]
    assert hub.frames == [("desk_request", {"request_id": request_id, "op": "mark", "args": args})]
    assert hub.get(f"/api/desk/requests/{request_id}").json() == {
        "request_id": request_id, "op": "mark", "answered": False}
    answered = hub.post(f"/api/desk/requests/{request_id}/result", json={"done": True})
    assert answered.status_code == 200 and answered.json()["done"] is True
    assert hub.frames[1:] == [], "an answer is no desk change"
    assert mcp_tools.dispatch("desk.request.read", {"request_id": request_id}, OWNER) == {
        "request_id": request_id, "op": "mark", "answered": True, "done": True}


def test_a_refusal_keeps_its_reason_and_an_unknown_request_is_not_found(hub: Any) -> None:
    request_id = mcp_tools.dispatch("desk.scroll", {"target": "missing"}, OWNER)["request_id"]
    hub.post(f"/api/desk/requests/{request_id}/result", json={"done": False, "reason": "No rows here yet"})
    assert hub.get(f"/api/desk/requests/{request_id}").json()["reason"] == "No rows here yet"
    missing = hub.get("/api/desk/requests/req-nope")
    assert missing.status_code == 404 and missing.json()["error"] == "not_found"


def test_say_needs_words_and_mark_needs_a_target(hub: Any) -> None:
    assert hub.post("/api/desk/requests/say", json={}).json()["error"] == "words_required"
    assert hub.post("/api/desk/requests/mark", json={"words": "x"}).json()["error"] == "target_required"
    assert hub.frames == []


def test_press_is_the_owners_and_mark_is_work() -> None:
    by_name = {d.name: d for d in desk_operations.DESK_DISPLAY_OPERATIONS}
    assert by_name["desk.press"].owner_only and by_name["desk.press"].authority == "authority"
    assert {by_name[n].authority for n in ("desk.mark", "desk.say", "desk.scroll")} == {"work"}
    registry = operations.bind({"desk_window_service": DeskWindowService(None)}, desk_operations.DESK_DISPLAY_OPERATIONS)
    with pytest.raises(operations.OperationOwnerRequired):
        registry.invoke(AGENT, "desk.press", {"target": "x"})


def test_the_hub_keeps_the_last_fifty_requests(hub: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(desk_window_service, "_REQUESTS", type(desk_window_service._REQUESTS)())
    ids = [hub.post("/api/desk/requests/say", json={"words": f"line {n}"}).json()["request_id"] for n in range(52)]
    assert len(desk_window_service._REQUESTS) == desk_window_service.REQUESTS_KEPT == 50
    assert hub.get(f"/api/desk/requests/{ids[0]}").status_code == 404
    assert hub.get(f"/api/desk/requests/{ids[-1]}").status_code == 200


@pytest.mark.parametrize("spoken", [True, False])
def test_say_keeps_the_compositors_voice_outcome(hub, spoken):
    rid = hub.post("/api/desk/requests/say", json={"words": "The update is ready."}).json()["request_id"]
    answer = hub.post(f"/api/desk/requests/{rid}/result", json={"done": True, "spoken": spoken})
    assert answer.json()["spoken"] is spoken
    assert hub.get(f"/api/desk/requests/{rid}").json()["spoken"] is spoken


def test_desk_callbacks_are_http_only_and_refuse_agent_writes():
    registry = operations.bind({"desk_window_service": DeskWindowService(None)}, desk_operations.DESK_DISPLAY_OPERATIONS)
    for name in ("desk.presence", "desk.arrivals.seen", "desk.request.result", "windows.restore"):
        row = registry.descriptor(name)
        assert row.http and row.tool_schema is None
        with pytest.raises(operations.OperationOwnerRequired):
            registry.invoke(AGENT, name, {})


def test_replay_cannot_repeat_an_owner_press(hub):
    rid = hub.post("/api/desk/requests/press", json={"target": "send"}).json()["request_id"]
    answer = hub.post(f"/api/desk/requests/{rid}/replay", json={})
    assert answer.status_code == 400 and answer.json()["error"] == "request_not_replayable"
    assert len(hub.frames) == 1


@pytest.mark.parametrize("name,args", [
    ("desk.presence", {"visible": False}),
    ("desk.arrivals.seen", {"meeting_ids": []}),
])
def test_desk_callback_answers_match_their_declared_contract(hub, name, args):
    from tests.unit.test_philo5_the_loop_r2 import _declared_keys

    descriptor = next(row for row in desk_operations.DESK_DISPLAY_OPERATIONS if row.name == name)
    response = hub.post(descriptor.http[1], json=args)
    assert response.status_code == 200
    assert set(_declared_keys(descriptor.result)) <= response.json().keys()
