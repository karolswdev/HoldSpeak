"""Every declared window act has one atomic, revision-safe Undo."""
import pytest

from holdspeak import operations
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.desk_window_service import DeskWindowService
from holdspeak.services.errors import ConflictError

OWNER = Principal(PrincipalKind.OWNER, "undo-owner")
AGENT = Principal(PrincipalKind.AGENT, "undo-agent")
RECT = {"x": "0", "y": "0", "w": "50%", "h": "50%"}


@pytest.fixture
def desk(tmp_path):
    frames = []
    service = DeskWindowService(Database(tmp_path / "desk.db"), on_changed=lambda *a: None, send_request=frames.append)
    service.open("surface-projects", object_ref="note:a", geometry=RECT, room="left")
    service.open("surface-meetings")
    port = operations.bind({"desk_window_service": service}, operations.DESK_DISPLAY_OPERATIONS)
    return service, port, frames


def state(service):
    listed = service.list()
    return {"shelf": listed["stage_shelf"], "windows": [
        {key: value for key, value in row.items() if key not in {"revision", "updated_at"}}
        for row in listed["windows"]]}


@pytest.mark.parametrize("verb,args", [
    ("open", {"window_id": "surface-programs"}),
    ("open", {"window_id": "surface-projects", "object_ref": "note:b", "room": "right"}),
    ("close", {"window_id": "surface-projects"}),
    ("move", {"window_id": "surface-projects", "x": "10", "y": "20"}),
    ("resize", {"window_id": "surface-projects", "w": "70%", "h": "80%"}),
    ("set_geometry", {"window_id": "surface-projects", "rect": None}),
    ("raise", {"window_id": "surface-projects"}),
    ("send_back", {"window_id": "surface-meetings"}),
    ("seat", {"window_id": "surface-projects", "seated": True}),
    ("zoom", {"window_id": "surface-projects", "zoomed": True, "rect": RECT}),
    ("arrange", {"rects": {"surface-projects": {**RECT, "w": "70%"}, "surface-meetings": RECT}}),
    ("stage_shelf", {"side": "right"}),
])
def test_agent_window_act_then_one_undo_restores_the_desk(desk, verb, args):
    service, port, frames = desk
    before = state(service)
    port.invoke(AGENT, f"windows.{verb}", args)
    assert state(service) != before
    assert len(frames) == 1 and frames[0]["op"] == "undo"
    port.invoke(OWNER, "windows.restore", frames[0]["args"])
    assert state(service) == before
    assert len(frames) == 1, "Undo must not offer an Undo of itself"


def test_stale_multiwindow_undo_keeps_all_newer_work(desk):
    service, port, frames = desk
    port.invoke(AGENT, "windows.arrange", {"rects": {"surface-projects": RECT, "surface-meetings": RECT}})
    service.move("surface-projects", "90", "10")
    before = state(service)
    with pytest.raises(ConflictError):
        port.invoke(OWNER, "windows.restore", frames[0]["args"])
    assert state(service) == before


def test_noop_offers_no_undo(desk):
    service, port, frames = desk
    port.invoke(AGENT, "windows.raise", {"window_id": "surface-meetings"})
    assert frames == []
