"""Every write announces itself, part two: the writers with no request.

#771 made two roots announce: ``OperationRegistry.invoke`` and the HTTP
middleware. Open after it (pm/STATUS.md, 2026-10-04): "background writers
(calendar ingest, heartbeat sweep, cadence tick) and MCP tools outside the
registry send no frame; announcements carry an empty id and op 'create' on
some routes".

This file fences each of those writers on a real hub with a real ``/ws``
client. Each background writer runs on a plain thread (no HTTP request, no
registry call), so neither of the two old roots can cover for it.
"""
from __future__ import annotations

import threading
from typing import Any

import pytest

from tests.integration.test_every_write_announces import (  # noqa: F401 - fixtures
    Hub,
    _the_hub_is_the_runtime,
    hub,
    seeded,
)

pytestmark = [pytest.mark.requires_meeting]


def _on_a_thread(work: Any) -> Any:
    """Run *work* on a fresh thread: no request context, no announce scope."""
    out: list[Any] = []
    errors: list[BaseException] = []

    def run() -> None:
        try:
            out.append(work())
        except BaseException as exc:  # noqa: BLE001 - re-raised below
            errors.append(exc)

    thread = threading.Thread(target=run)
    thread.start()
    thread.join(60)
    if errors:
        raise errors[0]
    return out[0] if out else None


def _mcp(hub: Hub, name: str, arguments: dict[str, Any]) -> tuple[int, Any]:
    return hub.call("POST", "/api/mcp", {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })


def _named(frames: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    return [(change["kind"], change["id"], change["op"]) for frame in frames for change in frame["changes"]]


def test_the_heartbeat_sweep_announces_with_its_sweep_id(hub: Hub, seeded: dict[str, str]) -> None:
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.heartbeat_service import HeartbeatService

    service = HeartbeatService(get_database())
    owner = Principal(PrincipalKind.OWNER, "heartbeat-conductor")
    frames = hub.frames_from(lambda: _on_a_thread(lambda: service.run_sweep(owner)))
    assert len(frames) == 1, frames
    kind, obj_id, op = frames[0]["kind"], frames[0]["id"], frames[0]["op"]
    assert (kind, op) == ("heartbeat", "sweep")
    assert obj_id.startswith("sweep_"), obj_id


def test_a_calendar_refresh_announces_each_source_it_applied(
    hub: Hub, seeded: dict[str, str], tmp_path: Any,
) -> None:
    from datetime import datetime, timezone

    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
    from holdspeak.config import CalendarConfig, CalendarSource, Config
    from holdspeak.db import get_database

    ics = (
        b"BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:announce-event\r\n"
        b"DTSTART:20261006T160000Z\r\nDTEND:20261006T170000Z\r\n"
        b"SUMMARY:Announce event\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    )
    config = Config(calendar=CalendarConfig(sources=[
        CalendarSource(id="announce-src", label="", url="/announce.ics", enabled=True),
    ]))
    conductor = CalendarIngestConductor(
        clock=lambda: datetime(2026, 10, 5, 12, tzinfo=timezone.utc).timestamp(),
        db_factory=get_database,
        source_reader=lambda _subscription: ics,
        config_loader=lambda: config,
    )
    frames = hub.frames_from(lambda: _on_a_thread(conductor.refresh))
    assert len(frames) == 1, frames
    assert ("calendar", "announce-src", "refresh") in _named(frames), frames
    assert get_database().calendar_events.list_all(), "the refresh wrote no event"


def test_a_cadence_tick_announces(hub: Hub, seeded: dict[str, str]) -> None:
    from holdspeak.cadence.service import CadenceService
    from holdspeak.config import CadenceConfig
    from holdspeak.db import get_database

    service = CadenceService(get_database(), CadenceConfig())
    frames = hub.frames_from(lambda: _on_a_thread(service.tick))
    assert len(frames) == 1, frames
    assert (frames[0]["kind"], frames[0]["op"]) == ("cadence", "tick")


def test_an_mcp_write_outside_the_registry_announces(hub: Hub, seeded: dict[str, str]) -> None:
    """``heartbeat.run_now`` is a family tool: no registry, no service bus."""
    answer: list[tuple[int, Any]] = []
    frames = hub.frames_from(lambda: answer.append(_mcp(hub, "heartbeat.run_now", {})))
    status, body = answer[0]
    assert status == 200 and not body["result"].get("isError"), body
    assert len(frames) == 1, frames
    assert (frames[0]["kind"], frames[0]["op"]) == ("heartbeat", "sweep")
    assert frames[0]["id"].startswith("sweep_")


def test_an_mcp_read_sends_no_frame(hub: Hub, seeded: dict[str, str]) -> None:
    """A read may write a receipt of its own; it still sends nothing."""
    for name, arguments in (
        ("desk.list", {"kind": "notes"}), ("desk.needs_you", {}),
        ("project.list", {}), ("settings.get", {}), ("door.get", {}),
    ):
        answer: list[tuple[int, Any]] = []
        frames = hub.frames_from(lambda: answer.append(_mcp(hub, name, arguments)), wait_s=0.5)
        assert answer[0][0] == 200 and not answer[0][1]["result"].get("isError"), (name, answer)
        assert frames == [], (name, frames)


def test_every_mcp_write_tool_announces_at_the_root(
    hub: Hub, seeded: dict[str, str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Walk every MCP tool (main catalogue and families).

    The walk stands in for each tool body with one that writes a real row and
    answers with an id, as the registry walk in
    ``test_every_write_announces.py`` does: it proves the root, not each tool.
    A write tool sends ONE frame naming ``(kind, id, op)``; a read tool sends
    none, though it wrote a row.
    """
    from holdspeak.db import get_database
    from holdspeak.mcp import tools
    from holdspeak.mcp.tool_authority import TOOL_AUTHORITY
    from holdspeak.principals import Principal, PrincipalKind

    def body(name: str, arguments: Any, principal: Any) -> dict[str, str]:
        get_database().milestones.mark(f"walk:{name}")
        return {"id": f"walk-{name}"}

    from holdspeak.runtime import composition

    sent: list[list[tuple[str, str, str]]] = []
    root = composition.installed()
    real_send = root._send_desk_changed
    # The socket is proved by the tests above; the walk reads what the root
    # hands to it (fast: 248 tools).
    monkeypatch.setattr(
        root, "_send_desk_changed",
        lambda changes: (sent.append([(k, i, o) for k, i, o, _ in changes]), real_send(changes)),
    )
    monkeypatch.setattr(tools, "_dispatch", body)
    owner = Principal(PrincipalKind.OWNER, "the-owner")
    wrong: dict[str, Any] = {}
    for name in sorted(TOOL_AUTHORITY):
        sent.clear()
        tools.dispatch(name, {}, owner)
        kind, _, op = name.partition(".")
        want = [] if tools.is_read_tool(name) else [[(kind, f"walk-{name}", op)]]
        if sent != want:
            wrong[name] = list(sent)
    assert not wrong, f"MCP tools that announced wrongly: {wrong}"


def test_a_post_with_no_path_id_names_the_object_from_its_answer(
    hub: Hub, seeded: dict[str, str],
) -> None:
    """``POST /api/brief/generate`` was ``brief '' create``: no id, wrong op."""
    answer: list[tuple[int, Any]] = []
    frames = hub.frames_from(lambda: answer.append(hub.call("POST", "/api/brief/generate", {})))
    status, body = answer[0]
    assert status == 200, body
    assert len(frames) == 1, frames
    brief_id = body.get("id") or (body.get("brief") or {}).get("id")
    assert brief_id, body
    assert (frames[0]["kind"], frames[0]["id"], frames[0]["op"]) == ("brief", brief_id, "generate")

    answer.clear()
    frames = hub.frames_from(lambda: answer.append(hub.call("POST", "/api/scheduled-recordings", {
        "title": "Announce fence", "cron_expr": "0 9 * * 1", "tz": "UTC", "duration_minutes": 15,
    })))
    status, body = answer[0]
    assert 200 <= status < 300, body
    assert len(frames) == 1, frames
    assert frames[0]["kind"] == "scheduled_recording" and frames[0]["op"] == "create", frames
    assert frames[0]["id"] and frames[0]["id"] in str(body), (frames, body)


def test_the_route_names_unit() -> None:
    from holdspeak.web.announce import changed

    assert changed("POST", "/api/notes", {}, {"note": {"id": "n1"}}) == ("note", "n1", "create")
    assert changed("POST", "/api/brief/generate", {}, {"id": "b1"}) == ("brief", "b1", "generate")
    assert changed("POST", "/api/cadence/run-now", {}, None) == ("cadence", "", "run_now")
    assert changed("PUT", "/api/meetings/m1", {"meeting_id": "m1"}, None) == ("meeting", "m1", "update")
    assert changed("DELETE", "/api/notes/n1", {"note_id": "n1"}, None) == ("note", "n1", "delete")
