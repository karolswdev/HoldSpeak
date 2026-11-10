"""A Program shows its work through the same display port an MCP tool uses."""
import json

import pytest

from holdspeak import desk_presence, operations
from holdspeak.runtime import composition
from holdspeak.services import program_desk
from holdspeak.services.desk_window_service import DeskWindowService
from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_rig import Rig, OWNER


@pytest.fixture
def rig(tmp_path):
    rig = Rig(tmp_path)
    rig.display_frames = []
    rig.request_clock = 0.0
    rig.windows = DeskWindowService(rig.db, request_clock=lambda: rig.request_clock, on_changed=lambda *a: None, send_request=rig.display_frames.append)
    port = operations.bind({"desk_window_service": rig.windows}, operations.DESK_DISPLAY_OPERATIONS)
    try:
        previous = composition.current()
    except composition.NoRuntimeError:
        previous = None
    composition.install(composition.RuntimeServices(db=rig.db, desk_window_service=rig.windows, operations=port))
    desk_presence.clear()
    try:
        yield rig
    finally:
        desk_presence.clear()
        if previous is None:
            composition.uninstall()
        else:
            composition.install(previous)


def make(rig, rows):
    return rig.service.create(OWNER, title="Show the changes", control="yolo", steps=[{
        "title": "Show the result", "kind": "desk", "brief": json.dumps(rows)}])


def test_desk_step_waits_then_sends_in_order_and_finishes_only_on_answers(rig):
    rows = [{"op": "mark", "args": {"target": "notes-list", "window": "surface-projects"}},
            {"op": "say", "args": {"words": "The notes are ready."}},
            {"op": "scroll", "args": {"target": "notes-list", "window": "surface-projects"}}]
    made = make(rig, rows)
    assert rig.service.store.get_program(made["id"])["repo_root"] == ""
    assert made["steps"][0]["agent"] == "Desk"
    rig.service.start(OWNER, made["id"])
    step = rig.service.store.get_step(made["steps"][0]["id"])
    assert step["state"] == "waiting" and rig.display_frames == []
    needs = rig.service.needs_you_items()
    assert [row["title"] for row in needs] == [program_desk.WAIT]

    desk_presence.report(None, True)
    rig.runner.tick_program(made["id"])
    for index, row in enumerate(rows):
        assert len(rig.display_frames) == index + 1
        frame = rig.display_frames[-1]
        assert (frame["op"], frame["args"]) == (row["op"], row["args"])
        rig.runner.tick_program(made["id"])
        assert len(rig.display_frames) == index + 1, "an unanswered request is not resent"
        rig.windows.request_result(frame["request_id"], True, spoken=False)
        rig.runner.tick_program(made["id"])
    step = rig.service.store.get_step(step["id"])
    assert step["state"] == "done"
    assert [answer["op"] for answer in step["facts"]["desk"]["answers"]] == [row["op"] for row in rows]
    assert step["facts"]["desk"]["answers"][1]["spoken"] is False
    assert rig.service.needs_you_items() == []


@pytest.mark.parametrize("op", ["press", "desk.press", "open", "undo"])
def test_program_refuses_an_owner_press_and_other_non_display_work(rig, op):
    with pytest.raises(ProgramRefused, match="press is yours"):
        make(rig, [{"op": op, "args": {"target": "send"}}])
    assert rig.display_frames == []


def test_desk_refusal_keeps_the_report_and_resume_sends_a_fresh_request(rig):
    desk_presence.report(None, True)
    made = make(rig, [{"op": "mark", "args": {"target": "missing"}}])
    rig.service.start(OWNER, made["id"])
    rig.windows.request_result(rig.display_frames[-1]["request_id"], False, "No notes here yet")
    rig.runner.tick_program(made["id"])
    step = rig.service.store.get_step(made["steps"][0]["id"])
    assert step["state"] == "failed" and step["report"] == "No notes here yet"
    assert step["facts"]["desk"]["answers"][-1]["done"] is False
    refused = rig.display_frames[-1]["request_id"]
    rig.service.resume(OWNER, made["id"])
    retried = rig.display_frames[-1]["request_id"]
    assert retried != refused
    rig.windows.request_result(retried, True)
    rig.runner.tick_program(made["id"])
    step = rig.service.store.get_step(step["id"])
    assert step["state"] == "done"
    assert [answer["done"] for answer in step["facts"]["desk"]["answers"]] == [False, True]


def test_hub_restart_replays_only_the_unanswered_display_request(rig, monkeypatch):
    from holdspeak.services import desk_window_service

    desk_presence.report(None, True)
    made = make(rig, [{"op": "say", "args": {"words": "The changes are ready."}}])
    rig.service.start(OWNER, made["id"])
    first = rig.display_frames[-1]["request_id"]
    monkeypatch.setattr(desk_window_service, "_REQUESTS", type(desk_window_service._REQUESTS)())
    rig.runner.tick_program(made["id"])
    second = rig.display_frames[-1]["request_id"]
    assert first != second
    rig.windows.request_result(second, True, spoken=False)
    rig.runner.tick_program(made["id"])
    assert rig.service.store.get_step(made["steps"][0]["id"])["state"] == "done"


def test_reconnect_reuses_the_unanswered_request_id(rig):
    desk_presence.report(None, True)
    made = make(rig, [{"op": "say", "args": {"words": "The changes are ready."}}])
    rig.service.start(OWNER, made["id"])
    original = rig.display_frames[-1]
    desk_presence.clear()
    rig.runner.tick_program(made["id"])
    rig.request_clock = 20.0
    desk_presence.report(None, True)
    rig.runner.tick_program(made["id"])
    assert rig.display_frames == [original, original]
    rig.windows.request_result(original["request_id"], True, spoken=False)
    rig.runner.tick_program(made["id"])
    assert rig.service.store.get_step(made["steps"][0]["id"])["state"] == "done"
