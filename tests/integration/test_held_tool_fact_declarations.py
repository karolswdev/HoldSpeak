"""Held writes disclose declared facts, never opaque references or hidden values."""
from __future__ import annotations

import json

import pytest

from holdspeak.held_arguments import NOT_YET_DESCRIBED
from holdspeak.mcp.palettes import CALL_HELD
from holdspeak.mcp.tools import TOOLS
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import thread_tools
from holdspeak.services.thread_service import ThreadService
from holdspeak.services.thread_tools import ThreadToolExecutor
from holdspeak.services.thread_turns import _ToolExecutorAggregator
from tests.unit.test_desk_ask_ai import hub  # noqa: F401

OWNER = Principal(PrincipalKind.OWNER, "fact-owner")
CALLER = Principal(PrincipalKind.AGENT, "fact-caller")


def held_capable_tools():
    """All registered write/build tools the gate can hold, including custom modes.

    CONDUCTOR steps and custom thread modes reach beyond the default palettes.
    Egress/config/authority are excluded except the explicitly held Calls set.
    Reads held by an explicit ask policy are outside this write census.
    """
    from holdspeak.held_arguments import strongest_effect
    return {tool["name"]: tool for tool in TOOLS
            if tool["name"] in thread_tools._ALL_TOOL_CLASSES and strongest_effect(tool) == "write"
            and (tool["name"] not in thread_tools.EXCLUDED_TOOLS or tool["name"] in CALL_HELD)}


def check_declarations():
    tools = held_capable_tools()
    described = {name for name, tool in tools.items() if "x-held-arguments" in tool["inputSchema"]}
    assert not (tools.keys() - described - NOT_YET_DESCRIBED), sorted(tools.keys() - described - NOT_YET_DESCRIBED)
    assert not (NOT_YET_DESCRIBED - (tools.keys() - described)), "Shrink the remaining disclosure set"
    for name in described:
        schema = tools[name]["inputSchema"]
        assert schema.get("title"), name
        fields = set()
        for fact in schema["x-held-arguments"]:
            assert fact["label"] and fact["kind"] in {"text", "secret", "token", "credential", "file bytes"}, name
            keys = fact["key"] if isinstance(fact["key"], list) else [fact["key"]]
            fields.update(key.split(".")[0] for key in keys)
            if "read" in fact:
                read = fact["read"]["tool"]
                from holdspeak.held_arguments import strongest_effect
                source = next(tool for tool in TOOLS if tool["name"] == read)
                assert strongest_effect(source) == "read", (name, read)
        assert set(schema.get("properties", {})) <= fields, name


def test_every_held_write_declares_its_facts_or_names_its_remaining_work():
    check_declarations()


def test_a_new_held_write_cannot_silently_omit_its_declaration(monkeypatch):
    monkeypatch.setitem(thread_tools._ALL_TOOL_CLASSES, "new_family.write", ("effect_proposal", False))
    monkeypatch.setattr(__import__(__name__, fromlist=["TOOLS"]), "TOOLS", [*TOOLS, {
        "name": "new_family.write", "inputSchema": {"type": "object", "properties": {}},
    }])
    with pytest.raises(AssertionError, match="new_family.write"):
        check_declarations()


def held(hub, monkeypatch, name, arguments):
    thread = hub.db.threads.create_thread(title="Read the write")
    executor = ThreadToolExecutor(hub.db, principal=CALLER, dispatch_fn=lambda *_: {"ok": True},
                                  control_mode_fn=lambda: "safe", held_egress=CALL_HELD)
    handle = executor.admit("facts-turn", thread.id, {"id": "facts-call", "name": name, "arguments": arguments})
    assert handle.state == "awaiting_decision"
    aggregator = _ToolExecutorAggregator()
    aggregator.register("facts-message", executor)
    monkeypatch.setattr(ThreadService, "_tool_executor", aggregator)
    return handle


@pytest.mark.parametrize("form", ["prepared", "inline", "prepare"])
def test_a_held_send_names_the_document_destination_and_channel(hub, tmp_path, monkeypatch, form):
    from holdspeak.channel_operations import CHANNEL_OPERATIONS
    from holdspeak import operations
    from holdspeak.services.channel_service import ChannelService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.channels import build_channels_router
    registry = operations.bind({"channel_service": ChannelService(hub.db)}, CHANNEL_OPERATIONS)
    hub.client.app.include_router(build_channels_router(WebContext(get_state=lambda: {}, operations=registry)))
    from holdspeak.services.primitive_service import PrimitiveService
    primitives = PrimitiveService(hub.db)
    note = primitives.create_note(OWNER, title="Platform plan", body_markdown="Keep these exact words.")
    folder = tmp_path / "team"
    folder.mkdir()
    saved = hub.client.post("/api/channels/destinations", json={
        "name": "Platform team", "channel": "file", "folder": str(folder),
    })
    assert saved.status_code == 200, saved.text
    destination = saved.json()["destination"]
    args = {"document_ref": f"note:{note['id']}", "destination_id": destination["id"]}
    preview = hub.client.post("/api/channels/preview", json=args)
    assert preview.status_code == 200, preview.text
    if form == "prepared":
        prepared = hub.client.post("/api/channels/sends", json=args)
        assert prepared.status_code == 200, prepared.text
        args = {"send_id": prepared.json()["send"]["id"]}
    elif form == "inline":
        args["preview_digest"] = preview.json()["payload_digest"]
    handle = held(hub, monkeypatch, "channel.prepare" if form == "prepare" else "channel.send", args)
    response = hub.client.get(f"/api/threads/{handle.thread_id}/held/{handle.call_id}")
    assert response.status_code == 200, response.text
    details = response.json()
    assert details["facts"][:3] == [{"label": "Document", "value": "Platform plan"},
                                    {"label": "To", "value": "Platform team"},
                                    {"label": "Through", "value": "file"}]
    for opaque in (note["id"], destination["id"], args.get("send_id"), args.get("preview_digest")):
        if opaque:
            assert opaque not in response.text
    before = details["binding"]
    # Same arguments; a changed shown name must change the question revision.
    with hub.db._connection() as conn:
        conn.execute("UPDATE channel_destinations SET name = ? WHERE id = ?", ("Cutover team", destination["id"]))
    after = ThreadService.held_tool_details(OWNER, handle.thread_id, handle.call_id)
    assert after["binding"] != before
    assert after["facts"][1]["value"] == "Cutover team"
    from holdspeak.services.errors import ServiceError
    with pytest.raises(ServiceError) as stale:
        ThreadService.answer_tool_handle(handle, "approve", principal=OWNER, binding=before)
    assert stale.value.code == "answer_stale"
    assert handle.state == "awaiting_decision"
    assert list(folder.iterdir()) == []  # A disclosure never sends.


def test_unreadable_references_and_private_payloads_never_leave_the_question(hub, monkeypatch):
    handle = held(hub, monkeypatch, "desk.update", {
        "kind": "notes", "id": "opaque-missing-note", "data": {"title": "New title", "private": "private-sentinel"},
    })
    details = ThreadService.held_tool_details(OWNER, handle.thread_id, handle.call_id)
    assert {"label": "Object", "value": "hidden (secret)"} in details["facts"]
    assert "opaque-missing-note" not in json.dumps(details)
    assert "private-sentinel" not in json.dumps(details)


def test_a_declaration_cannot_use_a_write_as_its_name_lookup(hub, monkeypatch):
    from holdspeak.mcp import tools
    from holdspeak.held_arguments import held_arguments, named
    tool = next(t for t in tools.TOOLS if t["name"] == "desk.update")
    monkeypatch.setitem(tool, "inputSchema", {**tool["inputSchema"], **held_arguments("Change a note",
        named("id", "Note", "door.add_item", {"task": "id"}, "task"))})
    handle = held(hub, monkeypatch, "desk.update", {"kind": "notes", "id": "must-never-be-written", "data": {}})
    calls = []
    monkeypatch.setattr(tools, "dispatch", lambda *args: calls.append(args))
    details = ThreadService.held_tool_details(OWNER, handle.thread_id, handle.call_id)
    assert calls == []
    assert {"label": "Note", "value": "hidden (secret)"} in details["facts"]
    assert "must-never-be-written" not in json.dumps(details)
