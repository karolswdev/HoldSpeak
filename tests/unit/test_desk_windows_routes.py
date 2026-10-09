"""PHILO-16 (16b): the desk's windows over HTTP -- thin over the service.

``GET /api/desk/windows``, ``POST /api/desk/windows/{id}/{verb}``,
``POST /api/desk/windows/arrange``, ``POST /api/desk/windows/stage-shelf``:
validate, call the service, serialize. A stale revision answers 409, an
unknown window 400, a closed one 404. Through the hub's announce middleware
one write is ONE ``desk_changed`` frame (kind ``windows``) and a no-op is none.
The edge gate admits the owner only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind, PrincipalRight, required_right
from holdspeak.runtime import composition
from holdspeak.services.desk_window_service import DeskWindowService
from holdspeak.web import announce
from holdspeak.web.context import WebContext
from holdspeak.web.routes.desk_windows import build_desk_windows_router

OWNER = Principal(PrincipalKind.OWNER, "philo16-owner")


@pytest.fixture()
def hub(tmp_path: Path) -> Any:
    db = Database(tmp_path / "w.db")
    frames: list[dict[str, Any]] = []
    composition.install(composition.RuntimeServices(
        db=db, broadcast=lambda kind, data: frames.append(data) if kind == "desk_changed" else None))
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


def _post(client: Any, wid: str, verb: str, body: dict[str, Any] | None = None) -> Any:
    return client.post(f"/api/desk/windows/{quote(wid, safe='')}/{verb}", json=body or {})


def test_open_list_raise_and_front(hub: Any) -> None:
    for wid in ("chair:brief", "chair:week", "chair:needs"):
        answer = _post(hub, wid, "open")
        assert answer.status_code == 200, answer.text
    listed = hub.get("/api/desk/windows").json()
    assert [w["id"] for w in listed["windows"]] == ["chair:brief", "chair:week", "chair:needs"]
    assert [w["id"] for w in listed["windows"] if w["front"]] == ["chair:needs"]
    assert listed["stage_shelf"] == "left" and "chair:brief" in listed["registry"]["static"]
    raised = _post(hub, "chair:brief", "raise").json()
    assert raised["front"] is True and raised["depth"] == 4


def test_every_verb_reaches_the_service(hub: Any) -> None:
    _post(hub, "zone:d1", "open", {"geometry": {"x": "-1/2", "y": "-1/2", "w": "1/2", "h": "100%"}})
    _post(hub, "chair:brief", "open")
    assert _post(hub, "zone:d1", "move", {"x": "-1/2 + 10", "y": 0}).json()["x"] == "-1/2 + 10"
    assert _post(hub, "zone:d1", "resize", {"w": 300, "h": "1/2"}).json()["w"] == 300
    assert _post(hub, "zone:d1", "set_geometry", {"rect": {"x": 1, "y": 2, "w": 3, "h": 4}}).json()["h"] == 4
    assert _post(hub, "zone:d1", "send_back").json()["depth"] < 2
    assert _post(hub, "zone:d1", "seat", {"seated": True}).json()["minimized"] is True
    assert _post(hub, "zone:d1", "seat", {"seated": False}).json()["front"] is True
    zoomed = _post(hub, "zone:d1", "zoom", {"zoomed": True, "rect": {"x": "-1/2", "y": "-1/2", "w": "100%", "h": "100%"}})
    assert zoomed.json()["zoomed"] is True
    arranged = hub.post("/api/desk/windows/arrange", json={"rects": {
        "zone:d1": {"x": "-1/2", "y": "-1/2", "w": "1/2", "h": "100%"},
        "chair:brief": {"x": "0%", "y": "-1/2", "w": "1/2", "h": "100%"}}})
    assert arranged.status_code == 200 and len(arranged.json()["windows"]) == 2
    assert hub.post("/api/desk/windows/stage-shelf", json={"side": "right"}).json()["stage_shelf"] == "right"
    assert _post(hub, "zone:d1", "close").json() == {"id": "zone:d1", "closed": True}


def test_refusals_carry_their_status(hub: Any) -> None:
    _post(hub, "chair:brief", "open")
    rev = hub.get("/api/desk/windows").json()["windows"][0]["revision"]
    assert _post(hub, "chair:brief", "move", {"x": 1, "y": 1, "expected_revision": rev}).status_code == 200
    stale = _post(hub, "chair:brief", "move", {"x": 2, "y": 2, "expected_revision": rev})
    assert stale.status_code == 409 and stale.json()["error"] == "window_stale"
    assert stale.json()["revision"] == rev + 1
    assert _post(hub, "nonsense", "open").status_code == 400
    assert _post(hub, "chair:week", "raise").status_code == 404
    assert _post(hub, "chair:brief", "explode").status_code == 404
    bad = _post(hub, "chair:brief", "set_geometry", {"rect": {"x": "wide", "y": 1, "w": 1, "h": 1}})
    assert bad.status_code == 400 and bad.json()["error"] == "geometry_invalid"


def test_one_write_is_one_frame_and_a_no_op_is_none(hub: Any) -> None:
    _post(hub, "chair:brief", "open")
    _post(hub, "chair:week", "open")
    assert [(f["kind"], f["id"], f["op"]) for f in hub.frames] == [
        ("windows", "chair:brief", "open"), ("windows", "chair:week", "open")]
    hub.frames.clear()
    _post(hub, "chair:week", "raise")  # already front
    assert hub.frames == []
    hub.post("/api/desk/windows/arrange", json={"rects": {
        "chair:brief": {"x": 1, "y": 1, "w": 1, "h": 1}, "chair:week": {"x": 2, "y": 2, "w": 2, "h": 2}}})
    assert len(hub.frames) == 1
    assert [c["id"] for c in hub.frames[0]["changes"]] == ["chair:brief", "chair:week"]
    hub.frames.clear()
    _post(hub, "chair:week", "raise", {"expected_revision": 999})  # refused: no frame
    assert hub.frames == []


def test_the_edge_gate_admits_only_the_owner() -> None:
    for method, path in (("GET", "/api/desk/windows"), ("POST", "/api/desk/windows/chair:brief/raise"),
                         ("POST", "/api/desk/windows/arrange")):
        assert required_right(method, path) is PrincipalRight.OWNER
