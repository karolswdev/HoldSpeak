"""PHILO-16 (16b): an agent reaches the owner's desk windows over MCP.

The family is thin over ``DeskWindowService``. Every tool is ``work`` (a
window is not egress, authority or config); a launched agent meets the
``window`` launch rule; ``list`` is the one read, so a Secure launch's gate
and a Secure thread hold every other tool. Each write through the one MCP
dispatcher sends ONE ``desk_changed`` frame.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.mcp import tools as mcp_tools
from holdspeak.mcp.families import desk_windows as family
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition

OWNER = Principal(PrincipalKind.OWNER, "philo16-owner")
LAUNCH = Principal(PrincipalKind.AGENT, "agent:launch:L-16b")
NAMES = {"desk_window.list", "desk_window.open", "desk_window.close", "desk_window.raise",
         "desk_window.arrange", "desk_window.seat"}
WRITES = NAMES - {"desk_window.list"}


@pytest.fixture()
def hub(tmp_path: Path) -> Any:
    frames: list[dict[str, Any]] = []
    composition.install(composition.RuntimeServices(
        db=Database(tmp_path / "w.db"),
        broadcast=lambda kind, data: frames.append(data) if kind == "desk_changed" else None))
    try:
        yield frames
    finally:
        composition.uninstall()


def test_the_family_names_six_tools_in_the_catalogue() -> None:
    assert {t["name"] for t in family.TOOLS} == NAMES
    assert NAMES <= {t["name"] for t in mcp_tools.TOOLS}


def test_arrange_schema_teaches_center_origin_tile_coordinates() -> None:
    """The model-facing contract must name the compositor's right-half origin."""
    tool = next(t for t in family.TOOLS if t["name"] == "desk_window.arrange")
    description = tool["description"]
    assert "x and y zero is the view centre" in description
    assert "left {x:-1/2, y:-1/2, w:1/2, h:1/1}" in description
    assert "right {x:0, y:-1/2, w:1/2, h:1/1}" in description
    assert "x:1/2 starts at the far edge and is off-band" in description


def test_the_tools_open_raise_seat_arrange_close_through_the_dispatcher(hub: Any) -> None:
    for wid in ("chair:brief", "chair:week"):
        mcp_tools.dispatch("desk_window.open", {"window_id": wid}, OWNER)
    listed = mcp_tools.dispatch("desk_window.list", {}, OWNER)
    assert [w["id"] for w in listed["windows"] if w["front"]] == ["chair:week"]
    assert mcp_tools.dispatch("desk_window.raise", {"window_id": "chair:brief"}, OWNER)["front"] is True
    assert mcp_tools.dispatch("desk_window.seat", {"window_id": "chair:week", "seated": True}, OWNER)["minimized"]
    tiled = mcp_tools.dispatch("desk_window.arrange", {"rects": {
        "chair:brief": {"x": "-1/2", "y": "-1/2", "w": "1/2", "h": "100%"},
        "chair:week": {"x": "0%", "y": "-1/2", "w": "1/2", "h": "100%"}}}, OWNER)
    assert {w["id"]: w["x"] for w in tiled["windows"]} == {"chair:brief": "-1/2", "chair:week": "0%"}
    assert mcp_tools.dispatch("desk_window.close", {"window_id": "chair:week"}, OWNER)["closed"] is True
    # one frame per write, none for the reads; arrange names both ids in one frame
    assert [(f["op"], [c["id"] for c in f["changes"]]) for f in hub] == [
        ("open", ["chair:brief"]), ("open", ["chair:week"]), ("raise", ["chair:brief"]),
        ("seat", ["chair:week"]), ("arrange", ["chair:brief", "chair:week"]), ("close", ["chair:week"])]
    assert {f["kind"] for f in hub} == {"windows"}


def test_an_mcp_no_op_write_sends_no_frame(hub: Any) -> None:
    """MAY (Astra r1): a raise of the front window changes nothing: no frame."""
    mcp_tools.dispatch("desk_window.open", {"window_id": "chair:brief"}, OWNER)
    hub.clear()
    mcp_tools.dispatch("desk_window.raise", {"window_id": "chair:brief"}, OWNER)
    mcp_tools.dispatch("desk_window.seat", {"window_id": "chair:brief", "seated": False}, OWNER)
    assert hub == []


def test_an_agent_open_is_announced_so_the_owner_sees_it(hub: Any) -> None:
    mcp_tools.dispatch("desk_window.open", {"window_id": "surface-people"}, LAUNCH)
    assert [(f["kind"], f["id"], f["op"]) for f in hub] == [("windows", "surface-people", "open")]


def test_the_s9_object_windows_use_the_registry_and_keep_their_scope(hub: Any) -> None:
    """Ask opens the real registry windows with the object's protected scope."""
    people = mcp_tools.dispatch("desk_window.open", {
        "window_id": "surface-people", "object_ref": "people:rel-mira:prep",
    }, OWNER)
    meeting = mcp_tools.dispatch("desk_window.open", {
        "window_id": "surface-meetings", "object_ref": "meeting:platform-sync?view=review",
    }, OWNER)

    assert people["app"] == "open-people"
    assert people["object_ref"] == "people:rel-mira:prep"
    assert meeting["app"] == "review-meetings"
    assert meeting["object_ref"] == "meeting:platform-sync?view=review"
    listed = mcp_tools.dispatch("desk_window.list", {}, OWNER)
    assert listed["registry"]["static"]["surface-people"] == "open-people"
    assert listed["registry"]["static"]["surface-meetings"] == "review-meetings"


def test_the_whole_window_producer_records_grouped_wrote_and_revision_safe_undo(hub: Any) -> None:
    """The real MCP dispatch plus trace projection is the S9 Wrote wire."""
    from holdspeak.services import run_trace
    from holdspeak.runtime import composition

    db = composition.current().db
    trace = run_trace.ask_trace("s9-window-wire")

    calls = [
        ("desk_window.open", {"window_id": "surface-people", "object_ref": "people:rel-mira:prep"}),
        ("desk_window.open", {"window_id": "surface-meetings", "object_ref": "meeting:platform-sync?view=review"}),
    ]
    for name, arguments in calls:
        value = mcp_tools.dispatch(name, arguments, OWNER)
        run_trace.record_value(trace, name, arguments, value, db=db)

    listed = mcp_tools.dispatch("desk_window.list", {}, OWNER)
    rects = {
        "surface-people": {"x": "-1/2", "y": "-1/2", "w": "1/2", "h": "100%"},
        "surface-meetings": {"x": "0%", "y": "-1/2", "w": "1/2", "h": "100%"},
    }
    revisions = {row["id"]: row["revision"] for row in listed["windows"]}
    arrange_args = {"rects": rects, "expected_revisions": revisions}
    arranged = mcp_tools.dispatch("desk_window.arrange", arrange_args, OWNER)
    run_trace.record_value(trace, "desk_window.arrange", arrange_args, arranged, db=db)

    with db._connection() as conn:
        rows = conn.execute(
            "SELECT tool, ref, detail_json FROM agent_run_calls WHERE run_id=? ORDER BY id",
            (trace,),
        ).fetchall()
    assert [row["tool"] for row in rows] == [
        "desk_window.open", "desk_window.open", "desk_window.arrange", "desk_window.arrange",
    ]
    assert all(json.loads(row["detail_json"])["window_undo"]["windows"] for row in rows)

    used = run_trace.use_by_trace(db, [trace])[trace]
    assert used["wrote_summary"] == "Opened 2 windows · Tiled"
    wrote = {row["ref"]: row for row in used["wrote"]}
    assert wrote["window:surface-people"]["undo"] is True
    assert wrote["window:surface-meetings"]["undo"] is False
    undo = wrote["window:surface-people"]["window_undo"]
    by_id = {row["id"]: row for row in undo["windows"]}
    assert by_id["surface-people"]["before"] is None
    assert by_id["surface-people"]["after"]["object_ref"] == "people:rel-mira:prep"
    assert by_id["surface-meetings"]["after"]["object_ref"] == "meeting:platform-sync?view=review"


def test_s9_arrange_cas_keeps_a_later_owner_placement(hub: Any) -> None:
    """A stale Undo arrange cannot overwrite the owner's newer placement."""
    from holdspeak.services.errors import ServiceError

    mcp_tools.dispatch("desk_window.open", {"window_id": "surface-people"}, OWNER)
    initial = mcp_tools.dispatch("desk_window.list", {}, OWNER)["windows"][0]
    first = {"surface-people": {"x": "-1/2", "y": "-1/2", "w": "1/2", "h": "100%"}}
    mcp_tools.dispatch("desk_window.arrange", {
        "rects": first, "expected_revisions": {"surface-people": initial["revision"]},
    }, OWNER)
    moved = mcp_tools.dispatch("desk_window.list", {}, OWNER)["windows"][0]
    newer = {"surface-people": {"x": "25%", "y": "20%", "w": "50%", "h": "70%"}}
    mcp_tools.dispatch("desk_window.arrange", {
        "rects": newer, "expected_revisions": {"surface-people": moved["revision"]},
    }, OWNER)

    with pytest.raises(ServiceError) as stale:
        mcp_tools.dispatch("desk_window.arrange", {
            "rects": first, "expected_revisions": {"surface-people": moved["revision"]},
        }, OWNER)
    assert stale.value.code == "window_stale"
    current = mcp_tools.dispatch("desk_window.list", {}, OWNER)["windows"][0]
    assert current["x"] == "25%" and current["y"] == "20%"


def test_bad_arguments_are_refused_before_any_write(hub: Any) -> None:
    from holdspeak.services.errors import ServiceError

    with pytest.raises(Exception):
        mcp_tools.dispatch("desk_window.open", {"window_id": "chair:brief", "geometry": {"x": 1}}, OWNER)
    with pytest.raises(ServiceError):
        mcp_tools.dispatch("desk_window.open", {"window_id": "not-a-window"}, OWNER)
    with pytest.raises(ServiceError):
        mcp_tools.dispatch("desk_window.arrange", {"rects": {"chair:brief": {"x": "1/0", "y": 1, "w": 1, "h": 1}}}, OWNER)
    assert hub == []


def test_authority_launch_rule_and_secure_hold() -> None:
    from holdspeak.coder_gate import mcp_tool_is_read
    from holdspeak.mcp.palettes import conductor_call_allowed, resolve_palette
    from holdspeak.mcp.tool_authority import TOOL_AUTHORITY, WORK
    from holdspeak.services import conductor_launch, thread_tools

    assert {TOOL_AUTHORITY[name] for name in NAMES} == {WORK}
    assert NAMES <= resolve_palette("CONDUCTOR")
    assert all(conductor_call_allowed(name, {"window_id": "chair:brief"}) for name in NAMES)
    for name in WRITES:
        assert conductor_launch.LAUNCH_RULES[name][0] == conductor_launch.WINDOW
        assert conductor_launch.gate_call(name, {"window_id": "chair:brief"}, LAUNCH) == {"window_id": "chair:brief"}
    # Secure holds every call that is not a read: the gate's read test, by name.
    assert mcp_tool_is_read("mcp__holdspeak__desk_window_list") is True
    assert not any(mcp_tool_is_read(f"mcp__holdspeak__{name.replace('.', '_')}") for name in WRITES)
    # A thread in Secure ("safe") holds each write and admits the read.
    for name in WRITES:
        assert thread_tools.resolve_tool_decision(None, "safe", thread_tools.tool_class(name)) == "hold"
    assert thread_tools.resolve_tool_decision(None, "safe", thread_tools.tool_class("desk_window.list")) == "admit"
