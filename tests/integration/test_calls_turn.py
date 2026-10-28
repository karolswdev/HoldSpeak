"""Calls (2026-10-28): a whole call through the hub, with a fake ai-phone.

The phone half is the fake ai-phone CLI (``tests/fixtures/fake_ai_phone.py``,
a real separate process printing ai-phone's own shapes). The turn is the
hub's real thread loop (``ThreadService.start_turn`` on ``calls.turn``, the
CALL prompt and palette, the real executor and MCP dispatch on this rig's
records). The engine:

- replays the HOME engine's REAL reply to a call's turn
  (``tests/fixtures/call_turn_home.json``, recorded by
  ``scripts/record_call_turn_reply.py`` from qwen3.8-27b over Tailscale):
  it adds the task, then says so;
- or, for the send (no recording can know the rig's send id), a SCRIPTED
  engine that does what a model does: it prepares the send, reads the send id
  from the hub's real answer, and calls ``channel.send``. Nothing in it
  answers for the hub.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.kernel.inference_stream import Delta
from tests.unit.test_desk_ask_ai import OWNER, _assign, _seed_routes, hub  # noqa: F401  (fixture)

pytestmark = pytest.mark.timeout(180, method="thread")

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
FAKE = FIXTURES / "fake_ai_phone.py"
RECORDED = json.loads((FIXTURES / "call_turn_home.json").read_text())
PASSPHRASE = "blue heron"
REMOTE = "sip:+12125550142@sip.telnyx.com"


class _RecordedHomeEngine:
    """Replays the home engine's recorded passes, one per call, as its stream did."""

    active_provider = "fixture"

    def __init__(self, model: str, passes: list[dict[str, Any]], seen: list[dict[str, Any]]) -> None:
        self.active_model = model
        self._passes = passes
        self._seen = seen

    def run_prompt_stream(self, *, messages=None, tools=None, **_kw: Any) -> Any:
        self._seen.append({"messages": [dict(m) for m in messages or []], "tools": tools})
        message = self._passes.pop(0)["choices"][0]["message"]
        if message.get("content"):
            yield Delta(kind="text", text=str(message["content"]))
        calls = message.get("tool_calls") or []
        if calls:
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {"id": c["id"], "name": c["function"]["name"], "arguments": c["function"]["arguments"]}
                for c in calls]})
        yield Delta(kind="usage", meta={"prompt_tokens": 40, "completion_tokens": 40})
        yield Delta(kind="done")


class _ScriptedSendEngine:
    """Prepares the note's send to the built-in folder, then sends it with the
    send id from the hub's own answer, then says so."""

    active_provider = "fixture"

    def __init__(self, model: str, note_ref: str, seen: list[dict[str, Any]]) -> None:
        self.active_model = model
        self._note_ref = note_ref
        self._seen = seen

    def run_prompt_stream(self, *, messages=None, tools=None, **_kw: Any) -> Any:
        self._seen.append({"messages": [dict(m) for m in messages or []], "tools": tools})
        tool_results = [m for m in messages or [] if m.get("role") == "tool"]
        if not tool_results:
            call = {"id": "call_prepare", "name": "channel.prepare",
                    "arguments": json.dumps({"document_ref": self._note_ref, "destination_id": "holdspeak-folder"})}
        elif len(tool_results) == 1:
            prepared = json.loads(str(tool_results[0].get("content") or "{}"))
            send_id = (prepared.get("send") or {}).get("id") or prepared.get("id") or prepared.get("send_id")
            call = {"id": "call_send", "name": "channel.send", "arguments": json.dumps({"send_id": send_id})}
        else:
            yield Delta(kind="text", text="Sent the runbook to your HoldSpeak folder.")
            yield Delta(kind="done")
            return
        yield Delta(kind="tool_calls", meta={"tool_calls": [call]})
        yield Delta(kind="done")


def _write_config(**calls: Any) -> None:
    import holdspeak.config as config_module

    path = Path(config_module.CONFIG_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    control = calls.pop("control_mode", "yolo")
    path.write_text(json.dumps({"control_mode": control, "calls": {
        "enabled": False, "passphrase": PASSPHRASE, "greeting": "Hello Karol. What can I do?", **calls}}))


def _fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, listens: list[dict[str, Any]]) -> Path:
    from holdspeak.calls import aiphone

    script = tmp_path / "scenario.json"
    script.write_text(json.dumps({"listen": listens}))
    state = tmp_path / "fake-state.json"
    monkeypatch.setenv("FAKE_AI_PHONE_SCRIPT", str(script))
    monkeypatch.setenv("FAKE_AI_PHONE_STATE", str(state))
    monkeypatch.setenv(aiphone.COMMAND_ENV, f"{sys.executable} {FAKE}")
    monkeypatch.setenv(aiphone.HOME_ENV, str(tmp_path / "ai-phone-home"))
    return state


def _said(state: Path) -> list[str]:
    log = json.loads(state.read_text())["log"]
    out = []
    for entry in log:
        if entry[0] == "say":
            out.append(entry[1])
        elif entry[0] == "hangup" and "--say" in entry:
            out.append(entry[entry.index("--say") + 1])
    return out


def _service(hub: Any, monkeypatch: pytest.MonkeyPatch, engine: Any, frames: list[tuple[str, Any]], *, seed: bool = True) -> Any:
    """A fresh calls service on the rig hub: its broadcast, its thread loop,
    the LAN engine whose server takes tools (its recorded ``/props``)."""
    from holdspeak.calls.service import CallsService
    from holdspeak.services import ask_desk
    from holdspeak.setup_runtime import endpoint_tool_support
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes._thread_factory import thread_service_from_ctx

    monkeypatch.setenv("HOLDSPEAK_ASK_SERVER_TOOLS", "on")
    props = json.dumps({"chat_template_caps": RECORDED["props_chat_template_caps"]}).encode()
    monkeypatch.setattr(ask_desk, "_server_takes_tools", lambda endpoint, model, _pid: endpoint_tool_support(
        endpoint, model=model, lan=False, http_get=lambda _url, **_kw: (200, props)))
    if seed:
        _seed_routes(hub.db)
        hub.broker.inference_adoption_service.migrate_legacy_config(OWNER, SimpleNamespace(
            thoughts=SimpleNamespace(inference_target_id="glass-lan"),
            dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="glass-lan"))))
        _assign(hub.db, "calls.turn", ["glass-lan"], "calls-turn-lan")
    hub.broker.inference_runner._engine_factory = lambda rev, **_kw: engine(str(rev.model))
    ctx = WebContext(get_state=lambda: {}, broadcast=lambda kind, data: frames.append((kind, data)))
    service = CallsService()
    service.configure(broadcast=ctx.broadcast, db=lambda: hub.db,
                      thread_factory=lambda **overrides: thread_service_from_ctx(ctx, **overrides))
    return service


def _action_items(db: Any) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [dict(r) for r in conn.execute("SELECT id, task, owner, status FROM action_items").fetchall()]


def _note(db: Any, note_ref: str) -> Any:
    return db.notes.get(note_ref.split(":", 1)[1])


def test_a_call_does_the_job_reads_it_back_and_keeps_the_transcript_as_a_note(hub, monkeypatch, tmp_path) -> None:
    """Done when (CALLS §1): he calls, says the passphrase, asks; the turn on
    calls.turn adds the task with the desk's tools; the answer is said with the
    read back from the turn's record; "that's all" ends it; the call is a Note
    (the passphrase never in it); every change is a call_state frame."""
    _write_config()
    state = _fake(tmp_path, monkeypatch, [
        {"kind": "incoming", "remote": REMOTE},
        {"kind": "heard", "text": "Blue heron."},
        {"kind": "heard", "text": RECORDED["question"]},
        {"kind": "heard", "text": "That's all, thanks."},
    ])
    frames: list[tuple[str, Any]] = []
    seen: list[dict[str, Any]] = []
    passes = [dict(p) for p in RECORDED["passes"]]
    service = _service(hub, monkeypatch, lambda model: _RecordedHomeEngine(model, passes, seen), frames)

    assert asyncio.run(service.serve_once(wait=5)) == "call"

    said = _said(state)
    final = RECORDED["passes"][-1]["choices"][0]["message"]["content"].strip()
    [task] = _action_items(hub.db)
    assert task["task"] == "Nudge Tomás about the runbook" and task["owner"] == "Me", task
    assert said[0] == "Hello. Say your passphrase." and said[1] == "Hello Karol. What can I do?"
    assert said[2] == f"{final} Done: Added a task: {task['task']}.", said
    assert said[-1] == "Goodbye."
    # The engine got the CALL prompt and the CALL palette: the two sends held
    # for his yes, no config tool.
    first = seen[0]
    assert "on a phone call with the owner" in first["messages"][0]["content"]
    offered = {tool["function"]["name"] for tool in first["tools"]}
    assert {"door.add_item", "channel.prepare", "channel.send", "nudge.send"} <= offered
    assert not offered & {"settings.update", "inference_assignment.set", "calls.place", "agent.hand"}
    # The turn ran on calls.turn.
    with hub.db._connection() as conn:
        planned = {row[0] for row in conn.execute("SELECT capability_id FROM inference_route_plans").fetchall()}
    assert "calls.turn" in planned and "chat.turn" not in planned, planned
    # The record, the note, the frames.
    [record] = service.list()
    assert record["state"] == "ended" and record["direction"] == "in" and record["remote"] == REMOTE
    assert record["ended_by"] == "caller" and record["first_words"] == RECORDED["question"][:120]
    assert record["results"] == [{"kind": "action_item", "label": task["task"],
                                  "ref": f"action_item:{task['id']}", "effect": "wrote"}]
    note = _note(hub.db, record["note_ref"])
    assert note is not None and note.title.startswith("Call · ")
    assert RECORDED["question"] in note.body_markdown and final in note.body_markdown
    assert "heron" not in note.body_markdown.lower() and "(passphrase)" in note.body_markdown
    full = service.get(record["id"])
    assert [line["who"] for line in full["transcript"]][:3] == ["holdspeak", "caller", "holdspeak"]
    assert full["transcript"][1]["text"] == "(passphrase)"
    reasons = [data["reason"] for kind, data in frames if kind == "call_state"]
    assert reasons[0] == "incoming" and {"heard", "said", "result", "ended"} <= set(reasons), reasons


@pytest.mark.parametrize("answer, written", [("Yes, do it.", 1), ("No.", 0)])
def test_a_held_write_is_asked_aloud_and_his_spoken_answer_decides_it(hub, monkeypatch, tmp_path, answer, written) -> None:
    """On a desk set to Secure the loop holds the task: the call says what it
    wants to do and asks; his "yes" writes it, his "no" writes nothing."""
    _write_config(control_mode="safe")
    state = _fake(tmp_path, monkeypatch, [
        {"kind": "incoming", "remote": REMOTE},
        {"kind": "heard", "text": "blue heron"},
        {"kind": "heard", "text": RECORDED["question"]},
        {"kind": "heard", "text": answer},
        {"kind": "ended"},
    ])
    frames: list[tuple[str, Any]] = []
    passes = [dict(p) for p in RECORDED["passes"]]
    service = _service(hub, monkeypatch, lambda model: _RecordedHomeEngine(model, passes, []), frames)

    assert asyncio.run(service.serve_once(wait=5)) == "call"

    said = _said(state)
    assert "I want to add a task: Nudge Tomás about the runbook. Say yes or no." in said, said
    assert len(_action_items(hub.db)) == written
    holds = [data["call"]["hold"] for kind, data in frames if kind == "call_state" and data["reason"] == "hold"]
    assert holds and holds[0]["tool"] == "door.add_item", holds
    assert any(data["reason"] == "decided" for kind, data in frames if kind == "call_state")
    [record] = service.list()
    assert record["ended_by"] == "caller" and record["hold"] is None


def test_a_send_leaves_only_on_his_spoken_yes(hub, monkeypatch, tmp_path) -> None:
    """channel.send is offered on a call and held whatever the control mode
    (yolo here): the call names what leaves and where; his yes sends the
    note into the built-in folder."""
    from holdspeak.mcp.tools import dispatch

    monkeypatch.delenv("XDG_DOCUMENTS_DIR", raising=False)
    _write_config()
    created = dispatch("desk.create", {"kind": "notes", "data": {
        "title": "Payments runbook", "body_markdown": "Restart the ledger worker first."}}, OWNER)
    note_id = str(created.get("id") or created.get("note_id") or (created.get("note") or {}).get("id"))
    state = _fake(tmp_path, monkeypatch, [
        {"kind": "incoming", "remote": REMOTE},
        {"kind": "heard", "text": "blue heron"},
        {"kind": "heard", "text": "Send the payments runbook to my HoldSpeak folder."},
        {"kind": "heard", "text": "Yes, send it."},
        {"kind": "ended"},
    ])
    frames: list[tuple[str, Any]] = []
    seen: list[dict[str, Any]] = []
    service = _service(hub, monkeypatch, lambda model: _ScriptedSendEngine(model, f"note:{note_id}", seen), frames)

    assert asyncio.run(service.serve_once(wait=5)) == "call"

    said = _said(state)
    asked = [line for line in said if line.endswith("Say yes or no.")]
    assert asked == ["I want to send Payments runbook to HoldSpeak folder. Say yes or no."], said
    with hub.db._connection() as conn:
        rows = [dict(r) for r in conn.execute("SELECT state, destination_id FROM channel_sends").fetchall()]
    assert rows == [{"state": "sent", "destination_id": "holdspeak-folder"}], rows
    sent_dir = Path(os.path.realpath(Path(os.environ["HOME"]) / "Documents")) / "HoldSpeak" / "Sent"
    assert len(list(sent_dir.iterdir())) == 1
    [record] = service.list()
    assert {"kind": "send", "effect": "sent"}.items() <= next(r for r in record["results"] if r["effect"] == "sent").items()


def test_a_send_he_refuses_never_leaves(hub, monkeypatch, tmp_path) -> None:
    from holdspeak.mcp.tools import dispatch

    _write_config()
    created = dispatch("desk.create", {"kind": "notes", "data": {"title": "Payments runbook", "body_markdown": "x"}}, OWNER)
    note_id = str(created.get("id") or created.get("note_id") or (created.get("note") or {}).get("id"))
    _fake(tmp_path, monkeypatch, [
        {"kind": "incoming", "remote": REMOTE},
        {"kind": "heard", "text": "blue heron"},
        {"kind": "heard", "text": "Send the payments runbook to my HoldSpeak folder."},
        {"kind": "heard", "text": "No, not now."},
        {"kind": "ended"},
    ])
    service = _service(hub, monkeypatch, lambda model: _ScriptedSendEngine(model, f"note:{note_id}", []), [])
    assert asyncio.run(service.serve_once(wait=5)) == "call"
    with hub.db._connection() as conn:
        rows = [dict(r) for r in conn.execute("SELECT state FROM channel_sends").fetchall()]
    assert rows == [{"state": "prepared"}], rows


def test_the_gate_wrong_number_no_passphrase_and_two_wrong_tries(hub, monkeypatch, tmp_path) -> None:
    """A number not in the list, a desk without a passphrase, two wrong
    passphrases: each call ends before any turn, with no hands."""
    seen: list[dict[str, Any]] = []
    cases = [
        ({"allowed_numbers": ["+1 646 555 0100"]}, [{"kind": "incoming", "remote": REMOTE}],
         "This line does not take calls from your number. Goodbye."),
        ({"passphrase": ""}, [{"kind": "incoming", "remote": REMOTE}],
         "Calls are not set up. Set a passphrase in HoldSpeak first. Goodbye."),
        ({}, [{"kind": "incoming", "remote": REMOTE}, {"kind": "heard", "text": "red fox"},
              {"kind": "heard", "text": "green frog"}], "Goodbye."),
    ]
    for index, (calls, listens, last) in enumerate(cases):
        folder = tmp_path / f"case{index}"
        folder.mkdir()
        _write_config(**calls)
        state = _fake(folder, monkeypatch, listens)
        service = _service(hub, monkeypatch, lambda model: _RecordedHomeEngine(model, [], seen), [], seed=index == 0)
        assert asyncio.run(service.serve_once(wait=5)) == "call"
        assert _said(state)[-1] == last, (index, _said(state))
        [record] = service.list()
        assert record["state"] == "ended" and record["results"] == []
    assert seen == []  # no turn reached the engine


def test_the_routes_place_a_call_list_it_and_refuse_without_a_number(hub, monkeypatch, tmp_path) -> None:
    """POST /api/calls/place calls his number (the first allowed number) in
    relay mode; GET /api/calls lists it; without a number it is a 409 with a
    reason; GET /api/calls/status names the steps."""
    from holdspeak.calls import service as calls_service
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.calls import build_calls_router

    _write_config(allowed_numbers=[])
    state = _fake(tmp_path, monkeypatch, [{"kind": "heard", "text": "blue heron"}, {"kind": "ended"}])
    frames: list[tuple[str, Any]] = []
    fresh = _service(hub, monkeypatch, lambda model: _RecordedHomeEngine(model, [], []), frames)
    monkeypatch.setattr(calls_service, "CALLS", fresh)
    import holdspeak.web.routes.calls as calls_routes

    monkeypatch.setattr(calls_routes, "CALLS", fresh)
    app = FastAPI()
    app.include_router(build_calls_router(WebContext(get_state=lambda: {}, broadcast=lambda k, d: frames.append((k, d)))))
    with TestClient(app) as client:
        refused = client.post("/api/calls/place", json={})
        assert refused.status_code == 409 and refused.json()["reason"] == "no_number", refused.text
        _write_config(allowed_numbers=["+1 212 555 0142"])
        placed = client.post("/api/calls/place", json={})
        assert placed.status_code == 201, placed.text
        assert placed.json()["direction"] == "out" and placed.json()["remote"] == "+1 212 555 0142"
        for _ in range(200):
            if client.get("/api/calls").json()["calls"][0]["state"] == "ended":
                break
            import time
            time.sleep(0.05)
        [listed] = client.get("/api/calls").json()["calls"]
        assert listed["state"] == "ended", listed
        assert client.get(f"/api/calls/{listed['id']}").json()["transcript"][0]["who"] == "holdspeak"
        assert client.get("/api/calls/nope").status_code == 404
        assert client.post(f"/api/calls/{listed['id']}/decide", json={"decision": "approve"}).status_code == 409
        status = client.get("/api/calls/status").json()
    log = json.loads(state.read_text())["log"]
    assert log[0][:3] == ["call", "+1 212 555 0142", "--relay"]
    assert status["aiphone"]["state"] == "not_running" and status["passphrase_set"] is True
    assert [step["id"] for step in status["steps"]] == ["install", "daemon", "line", "engine", "passphrase", "enable"]
    assert [step["done"] for step in status["steps"]] == [True, False, False, True, True, False], status["steps"]
    assert status["engine"]["state"] == "ready" and status["engine"]["model"] == "qwen3.8-27b"
