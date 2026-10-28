"""Ask my whole desk (Betterment Q7; DECISIONS #16), against the hub.

Two engines that can use tools:

- An HTTP engine whose server takes tool calls runs the hub's tool loop (the
  Thread turn, ``ThreadService``) with the ASK palette. The engine replays a
  REAL reply of the LAN engine (``tests/fixtures/ask_tool_turn_lan.json``,
  recorded by ``scripts/record_ask_tool_reply.py``): it reads the 1:1, the
  memory page and the board, then adds the task. The real thread routes, the
  real executor and the real MCP dispatch answer each call with this rig's
  records.
- An agent CLI on this Mac (the fake ``claude`` of
  ``tests/fixtures/fake_agent_cli.py``, on a real hub) gets the CONDUCTOR set
  through its run credential (MCP M1); the calls the hub serves for that run
  are the Ask's (MCP M2's record).

Each answer carries Looked at (reads, by name), Wrote (desk writes, with Undo)
and Prepared (sends); a send is only prepared, a config tool is refused.
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.kernel.inference_stream import Delta
from tests.unit.test_desk_ask_ai import OWNER, _assign, _seed_routes, hub  # noqa: F401  (fixture)

pytestmark = pytest.mark.timeout(180, method="thread")

#: The face mints `ask_<uuid without dashes>`; the held Ask's frame names this one.
HELD_INVOCATION = "ask_" + "c" * 32

RECORDED = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "ask_tool_turn_lan.json").read_text())


class _RecordedLanEngine:
    """Replays the LAN engine's recorded passes, one per call, as its stream did."""

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


def _loop_app(hub: Any, monkeypatch: pytest.MonkeyPatch, frames: list[tuple[str, Any]]) -> tuple[TestClient, list]:
    """The Ask and thread routes on the rig hub; the Answers engine is the LAN
    engine, whose server says it takes tools (its recorded ``/props``)."""
    from holdspeak.services import ask_desk
    from holdspeak.setup_runtime import endpoint_tool_support
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.primitives.ask import build_ask_router
    from holdspeak.web.routes.threads import build_threads_router

    monkeypatch.setenv("HOLDSPEAK_ASK_SERVER_TOOLS", "on")
    props = json.dumps({"chat_template_caps": RECORDED["props_chat_template_caps"]}).encode()
    monkeypatch.setattr(ask_desk, "_server_takes_tools", lambda endpoint, model, _pid: endpoint_tool_support(
        endpoint, model=model, lan=False, http_get=lambda _url, **_kw: (200, props)))
    _seed_routes(hub.db)
    hub.broker.inference_adoption_service.migrate_legacy_config(OWNER, SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="glass-lan"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="glass-lan"))))
    _assign(hub.db, "ask.answer", ["glass-lan"], "ask-tools-lan")
    seen: list[dict[str, Any]] = []
    passes = [dict(p) for p in RECORDED["passes"]]
    hub.broker.inference_runner._engine_factory = lambda rev, **_kw: _RecordedLanEngine(str(rev.model), passes, seen)
    app = FastAPI()
    ctx = WebContext(get_state=lambda: {}, broadcast=lambda kind, data: frames.append((kind, data)))
    app.include_router(build_ask_router(ctx))
    app.include_router(build_threads_router(ctx))
    return TestClient(app), seen


def _stable_message_ids(payload: dict[str, Any]) -> dict[str, Any]:
    """The thread read keys its maps by message id (``siblings``, ``used``);
    the recorded answers name each message ``tm_000…<n>`` in order of first
    appearance, the same everywhere, so their shape is the same on each run."""
    import re

    text = json.dumps(payload)
    names: dict[str, str] = {}
    for found in re.findall(r"tm_[0-9a-f]{12}", text):
        names.setdefault(found, f"tm_{len(names):012x}")
    return json.loads(re.sub(r"tm_[0-9a-f]{12}", lambda m: names[m.group(0)], text))


def _seed_mira(db: Any) -> None:
    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    start = datetime.now() - timedelta(days=2)
    db.meetings.save_meeting(MeetingState(
        id="m-mira-1on1", started_at=start, ended_at=start + timedelta(minutes=30), title="1:1 with Mira",
        segments=[TranscriptSegment(text="I need your feedback on my cutover design doc by Friday.",
                                    speaker="Mira", start_time=1.0, end_time=4.0)]))


def _action_items(db: Any) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [dict(r) for r in conn.execute("SELECT id, task, owner, due, status FROM action_items").fetchall()]


def test_a_tool_engine_ask_looks_at_the_1on1_and_writes_the_task_with_undo(hub, monkeypatch, tmp_path) -> None:
    """Done when (Q7): with a tool engine, "What do I owe Mira this week?"
    answers from her meeting, Looked at names it, and "make it a task for
    Friday" shows the task under Wrote with Undo. The thread keeps all three
    for the window that reopens it."""
    _seed_mira(hub.db)
    frames: list[tuple[str, Any]] = []
    client, seen = _loop_app(hub, monkeypatch, frames)

    assert client.get("/api/ask/engine").json() == {"tools": "desk"}
    answered = client.post("/api/ask", json={"prompt": RECORDED["question"], "thread": True})

    assert answered.status_code == 200, answered.text
    body = answered.json()
    assert body["tools"] == "desk"
    assert "Give Mira feedback on her cutover design doc" in body["output"]
    # The answer is the last pass's words, not what it said on the way.
    final = RECORDED["passes"][-1]["choices"][0]["message"]["content"].strip()
    assert body["output"] == final and "Let me check" not in body["output"]
    # The engine got the Ask's prompt and the ASK palette (no send, no config).
    first = seen[0]
    assert "Read memory pages first" in first["messages"][0]["content"]
    offered = {tool["function"]["name"] for tool in first["tools"]}
    assert {"meeting.get", "memory.page", "door.add_item", "channel.prepare"} <= offered
    assert not offered & {"channel.send", "settings.update", "inference_assignment.set", "agent.hand"}
    # Looked at: the 1:1, by its name.
    assert ("meeting:m-mira-1on1", "1:1 with Mira") in {(row["ref"], row["title"]) for row in body["looked_at"]}, body["looked_at"]
    # Wrote: the task, with Undo; the task is on the desk with its date.
    [task] = _action_items(hub.db)
    assert task["due"] == "2026-10-23" and task["status"] == "open", task
    [wrote] = body["used"]["wrote"]
    assert wrote == {"ref": f"action_item:{task['id']}", "label": task["task"], "kind": "action_item", "undo": True}
    assert body["used"]["prepared"] == []
    # The thread keeps it: a reopened Ask draws the same lines.
    thread = client.get(f"/api/threads/{body['thread_id']}").json()
    assert thread["used"][body["message_ids"]["answer"]] == body["used"]

    # Make it a task under an answer: the same write (door.add_item) through
    # the thread's /todo; the face shows it under Wrote with Undo.
    todo = client.post(f"/api/threads/{body['thread_id']}/todo",
                       json={"text": "Give Mira feedback on her cutover design doc"}).json()
    assert todo["status"] == "ok" and todo["result"]["id"].startswith("ai_"), todo

    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_desk_speak import _record

    assignments = InferenceAssignmentService(hub.db).assignment_summary(OWNER)
    _record("ask.tools.wire", _stable_message_ids({
        "engine": {"tools": "desk"}, "assignments": assignments, "answer": body, "thread": thread, "todo": todo,
    }), tmp_path,
            "tests/integration/test_desk_ask_tools.py::test_a_tool_engine_ask_looks_at_the_1on1_and_writes_the_task_with_undo",
            folder=Path(__file__).resolve().parents[2] / "web" / "src" / "test" / "wire")


def test_a_held_call_waits_for_his_press_and_deny_writes_nothing(hub, monkeypatch, tmp_path) -> None:
    """On a desk set to Secure, the loop holds the task for his press: the Ask
    window hears the hold (an ``ask_progress`` frame with its words) and Deny
    goes through the thread's own decide route. Nothing is written."""
    import holdspeak.config as config_module

    config_file = Path(config_module.CONFIG_FILE)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps({"control_mode": "safe"}))
    _seed_mira(hub.db)
    frames: list[tuple[str, Any]] = []
    client, _seen = _loop_app(hub, monkeypatch, frames)
    result: dict[str, Any] = {}
    asking = threading.Thread(target=lambda: result.update(response=client.post(
        "/api/ask", json={"prompt": RECORDED["question"], "thread": True, "invocation_id": HELD_INVOCATION})))
    asking.start()
    hold = None
    deadline = time.monotonic() + 60
    while hold is None and time.monotonic() < deadline:
        for kind, data in list(frames):
            if kind == "ask_progress" and data.get("state") == "hold" and data.get("holds"):
                hold = data
        time.sleep(0.05)
    assert hold is not None, frames
    assert hold["invocation_id"] == HELD_INVOCATION
    [held] = hold["holds"]
    assert held["tool"] == "door.add_item" and held["words"] == "Add a task", held

    decided = client.post(f"/api/threads/{hold['thread_id']}/decide",
                          json={"call_id": held["call_id"], "decision": "deny"})
    assert decided.status_code == 200, decided.text
    asking.join(timeout=60)
    assert result["response"].status_code == 200, result["response"].text
    body = result["response"].json()
    assert _action_items(hub.db) == []
    assert body["used"].get("wrote", []) == []
    assert ("meeting:m-mira-1on1", "1:1 with Mira") in {(row["ref"], row["title"]) for row in body["looked_at"]}

    from tests.unit.test_desk_speak import _record

    _record("ask.hold.wire", {"hold": hold, "decided": decided.json(), "answer": body}, tmp_path,
            "tests/integration/test_desk_ask_tools.py::test_a_held_call_waits_for_his_press_and_deny_writes_nothing",
            folder=Path(__file__).resolve().parents[2] / "web" / "src" / "test" / "wire")


def test_an_engine_without_tools_keeps_todays_ask(hub, monkeypatch) -> None:
    """The rigs' default: no server is asked; the Ask is today's grounded Ask
    and the engine line says it reads only what is in About."""
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.primitives.ask import build_ask_router

    _seed_routes(hub.db)
    _assign(hub.db, "ask.answer", ["glass-lan"], "ask-plain-lan")
    app = FastAPI()
    app.include_router(build_ask_router(WebContext(get_state=lambda: {})))
    assert TestClient(app).get("/api/ask/engine").json() == {"tools": ""}


# ── an agent CLI on this Mac (MCP M1 + M2) ──────────────────────────────────

TOKEN = "desk-engines-tools"  # the token the borrowed helpers send


@pytest.fixture()
def real_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from tests.e2e.glass_infra import _boot

    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        yield base
    finally:
        server.stop()


def test_a_cli_engine_ask_records_reads_writes_and_a_prepared_send(real_hub: str, tmp_path, monkeypatch) -> None:
    """The fake claude reads the 1:1, adds the task, prepares a send, and
    tries a send and a config change. The answer's Looked at names the 1:1,
    Wrote the task (with Undo), Prepared the send; the send and the config
    change are refused, and nothing left the desk."""
    from holdspeak.db import get_database
    from tests.fixtures.fake_agent_cli import (
        calls, install_fake_agent_clis, mcp_runs, path_with, set_claude_answer, set_tool_plan,
    )
    from tests.integration.test_desk_engines_tools import _assign as assign, _connect, _ok, _refused

    bin_dir = install_fake_agent_clis(tmp_path / "home" / "bin")
    monkeypatch.setenv("PATH", path_with(bin_dir))
    monkeypatch.setenv("HOLDSPEAK_CLI_ENGINES", "on")
    _seed_mira(get_database())
    note = _ok(real_hub, "POST", "/api/notes", {"title": "Cutover feedback", "body_markdown": "Looks good."})["note"]["id"]
    folder = tmp_path / "outbox"
    folder.mkdir()
    destination = _ok(real_hub, "POST", "/api/channels/destinations",
                      {"name": "Outbox folder", "channel": "file", "folder": str(folder)})["destination"]["id"]
    assign(real_hub, "ask.answer", _connect(real_hub, "claude"))
    settings_before = _ok(real_hub, "GET", "/api/settings")
    set_tool_plan(bin_dir, "claude", [
        {"name": "meeting.get", "arguments": {"meeting_id": "m-mira-1on1"}},
        {"name": "door.add_item", "arguments": {"task": "Give Mira feedback on the cutover design doc",
                                                "due": "2026-10-23"}},
        {"name": "channel.prepare", "arguments": {"document_ref": f"note:{note}", "destination_id": destination}},
        {"name": "channel.send", "arguments": {"send_id": "send-x"}},
        {"name": "settings.update", "arguments": {"control_mode": "safe"}},
    ], once=True)
    set_claude_answer(bin_dir, "You owe Mira feedback on her cutover design doc by Friday. I made it a task.")

    assert _ok(real_hub, "GET", "/api/ask/engine") == {"tools": "desk"}
    body = _ok(real_hub, "POST", "/api/ask", {"prompt": "What do I owe Mira this week? Make it a task.", "thread": True})

    assert body["tools"] == "desk"
    (call,) = calls(bin_dir, "claude")
    assert "Read memory pages first" in call["prompt"]
    (run,) = mcp_runs(bin_dir, "claude")
    sent, configured = run["calls"][3], run["calls"][4]
    assert _refused(sent["reply"]) and _refused(configured["reply"]), run["calls"]
    assert _ok(real_hub, "GET", "/api/settings") == settings_before
    assert list(folder.iterdir()) == []  # prepared only: nothing left the desk

    assert ("meeting:m-mira-1on1", "1:1 with Mira") in {(row["ref"], row["title"]) for row in body["looked_at"]}, body["looked_at"]
    [wrote] = body["used"]["wrote"]
    assert wrote["ref"].startswith("action_item:") and wrote["undo"] is True, wrote
    assert wrote["label"] == "Give Mira feedback on the cutover design doc"
    [prepared] = body["used"]["prepared"]
    assert prepared["ref"] == f"note:{note}" and prepared["destination"] == "Outbox folder" and prepared["send_id"]
    thread = _ok(real_hub, "GET", f"/api/threads/{body['thread_id']}")
    assert thread["used"][body["message_ids"]["answer"]] == body["used"]
