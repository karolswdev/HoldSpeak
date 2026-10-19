"""Engines, against a real hub: an HTTP engine that takes tool calls gets the
desk's tools in an automation (Betterment MCP M5).

A real MeetingWebServer (``_boot``: isolated HOME and DB) and a local stub of
the owner's LAN engine (llama.cpp serving qwen, OpenAI-compatible). The stub
speaks the real wire: ``/props`` answers the recorded ``chat_template_caps``
(what the Check reads), and ``/v1/chat/completions`` streams the LAN engine's
RECORDED tool-calling replies (``tests/fixtures/ask_tool_turn_lan.json``,
``scripts/record_ask_tool_reply.py``) as SSE chunks, one reply per request. The
hub's real engine (``MeetingIntel`` and its OpenAI client) parses them; the real
MCP dispatch answers each call with this hub's records. Neither the real LAN
box nor a cloud service is called.
"""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.glass_infra import _boot

TOKEN = "desk-engines-http-tools"
RECORDED = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "ask_tool_turn_lan.json").read_text())

pytestmark = pytest.mark.timeout(180, method="thread")


class _LanStub(BaseHTTPRequestHandler):
    """The LAN engine's wire, replayed. ``server.passes`` is the reply queue;
    ``server.seen`` keeps every chat request body."""

    def _json(self, value: Any) -> None:
        body = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - http.server contract
        path = self.path.rstrip("/")
        if path.endswith("/models"):
            self._json({"object": "list", "data": [{"id": RECORDED["model"], "object": "model"}]})
        elif path.endswith("/props"):
            self._json({"chat_template_caps": RECORDED["props_chat_template_caps"]})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802 - http.server contract
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        self.server.seen.append(body)  # type: ignore[attr-defined]
        if "tools" in body and self.server.passes:  # type: ignore[attr-defined]
            reply = self.server.passes.pop(0)  # type: ignore[attr-defined]
        else:  # the item's memory note after it (no tools): one plain answer
            reply = {"choices": [{"index": 0, "finish_reason": "stop",
                                  "message": {"role": "assistant", "content": "nothing"}}],
                     "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11}}
        if not body.get("stream"):
            self._json({**reply, "object": "chat.completion", "model": RECORDED["model"]})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for chunk in _chunks(reply):
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n")

    def log_message(self, *_args: Any) -> None:
        return


def _chunks(reply: dict[str, Any]) -> list[dict[str, Any]]:
    """One recorded reply as llama.cpp streams it: the words, each tool call
    (its id and name, then its arguments), the finish, then the usage."""
    message = reply["choices"][0]["message"]
    head = {"id": "chatcmpl-stub", "object": "chat.completion.chunk", "created": 1, "model": RECORDED["model"]}

    def chunk(delta: dict[str, Any], finish: Any = None) -> dict[str, Any]:
        return {**head, "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}

    out = [chunk({"role": "assistant", "content": message.get("content") or ""})]
    for index, call in enumerate(message.get("tool_calls") or []):
        out.append(chunk({"tool_calls": [{"index": index, "id": call["id"], "type": "function",
                                          "function": {"name": call["function"]["name"], "arguments": ""}}]}))
        out.append(chunk({"tool_calls": [{"index": index,
                                          "function": {"arguments": call["function"]["arguments"]}}]}))
    out.append(chunk({}, reply["choices"][0].get("finish_reason") or "stop"))
    out.append({**head, "choices": [], "usage": reply["usage"]})
    return out


def _call(base: str, method: str, path: str, body: Any = None) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw) if raw else {}


def _ok(base: str, method: str, path: str, body: Any = None) -> Any:
    status, payload = _call(base, method, path, body)
    assert status < 300, (status, path, payload)
    return payload


@pytest.fixture()
def lan() -> Any:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _LanStub)
    server.passes = [dict(p) for p in RECORDED["passes"]]  # type: ignore[attr-defined]
    server.seen = []  # type: ignore[attr-defined]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture()
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        yield base
    finally:
        server.stop()


def _define_lan_engine(base: str, endpoint: str) -> dict[str, Any]:
    defined = _ok(base, "POST", "/api/inference/model-library/define-endpoint", {
        "draft": {
            "request_id": "lan-engine-add", "profile_id": "engine-lan-qwen", "expected_profile_revision": 0,
            "label": "LAN box", "provider_family": "openai_compatible", "model": RECORDED["model"],
            "endpoint": endpoint, "requires_key": False, "context_tokens": None,
        },
        "secret": None,
    })
    return {"profile_id": defined["provider"]["profile_id"],
            "profile_revision": int(defined["provider"]["profile_revision"])}


def _seed_mira() -> None:
    from holdspeak.db import get_database
    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    start = datetime.now() - timedelta(days=2)
    get_database().meetings.save_meeting(MeetingState(
        id="m-mira-1on1", started_at=start, ended_at=start + timedelta(minutes=30), title="1:1 with Mira",
        segments=[TranscriptSegment(text="I need your feedback on my cutover design doc by Friday.",
                                    speaker="Mira", start_time=1.0, end_time=4.0)]))


def _automation_on(base: str, endpoint: str, monkeypatch: pytest.MonkeyPatch) -> str:
    # The rig turns the Check's tool question off; this test asks the stub.
    monkeypatch.setenv("HOLDSPEAK_ASK_SERVER_TOOLS", "on")
    bench = _ok(base, "POST", "/api/workbenches", {"name": "What I owe Mira"})["workbench"]["id"]
    _ok(base, "PUT", f"/api/workbenches/{bench}",
        {"instruction": "What do I owe Mira this week? Make the feedback a task for Friday 2026-10-23."})
    entry = _define_lan_engine(base, endpoint)
    _ok(base, "POST", "/api/inference/assignments/set", {
        "command_id": "assign-workbench-item", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "workbench.item"}, "entries": [entry],
    })
    return bench


def test_an_automation_on_the_lan_engine_reads_the_meeting_and_its_result_says_so(
    hub: str, lan: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Done when (M5): with a recorded tool-calling reply from the LAN model,
    the result's Looked at lists the meeting it read, by its title. The engine
    got the ASK tools (no send, no config, no schedule), each call was answered
    by this hub's records, and the task it wrote is under Wrote with Undo."""
    from holdspeak.db import get_database

    _seed_mira()
    endpoint = f"http://127.0.0.1:{lan.server_address[1]}/v1"
    bench = _automation_on(hub, endpoint, monkeypatch)

    _ok(hub, "POST", f"/api/workbenches/{bench}/run", {})

    results = _ok(hub, "GET", f"/api/workbenches/{bench}")["workbench"]["results"]
    assert results and results[0]["status"] == "done", results
    final = RECORDED["passes"][-1]["choices"][0]["message"]["content"].strip()
    assert results[0]["text"].strip() == final, results[0]
    used = results[0]["used"]
    assert used is not None, results[0]
    assert {"ref": "meeting:m-mira-1on1", "label": "1:1 with Mira", "kind": "meeting"} in used["looked_at"], used
    [wrote] = used["wrote"]
    assert wrote["kind"] == "action_item" and wrote["undo"] is True, wrote
    with get_database()._connection() as conn:
        [task] = [dict(r) for r in conn.execute("SELECT id, due, status FROM action_items").fetchall()]
    assert wrote["ref"] == f"action_item:{task['id']}" and task["due"] == "2026-10-23", (wrote, task)
    assert used["prepared"] == []

    tool_requests = [body for body in lan.seen if "tools" in body]
    assert len(tool_requests) == len(RECORDED["passes"]), [sorted(b) for b in lan.seen]
    offered = {tool["function"]["name"] for tool in tool_requests[0]["tools"]}
    assert {"meeting.get", "memory.page", "door.add_item", "channel.prepare"} <= offered
    assert not offered & {"channel.send", "settings.update", "inference_assignment.set",
                          "workbench.create", "workbench.update", "heartbeat.set"}, offered
    assert tool_requests[0]["stream"] is True
    # The second request carries the hub's own answer to meeting.get (its
    # record, not the recording's), after the assistant's tool calls.
    second = tool_requests[1]["messages"]
    asked = next(m for m in second if m["role"] == "assistant")
    assert [c["function"]["name"] for c in asked["tool_calls"]] == ["meeting.get", "memory.page", "desk.needs_you"]
    answered = {m["tool_call_id"]: m["content"] for m in second if m["role"] == "tool"}
    meeting_answer = answered[asked["tool_calls"][0]["id"]]
    assert "I need your feedback on my cutover design doc" in meeting_answer, meeting_answer


def test_a_lan_engine_call_outside_the_tool_set_is_refused_and_the_run_goes_on(
    hub: str, lan: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A tool the run was not given (a send, a schedule) is refused through the
    same gate an agent run meets on /api/mcp: the engine reads the refusal,
    nothing is sent or scheduled, and the run still answers."""
    _seed_mira()
    first = RECORDED["passes"][0]
    refused_pass = json.loads(json.dumps(first))
    refused_pass["choices"][0]["message"]["tool_calls"] = [
        {"type": "function", "id": "send-1", "function": {"name": "channel.send", "arguments": "{\"send_id\":\"x\"}"}},
        {"type": "function", "id": "sched-1", "function": {
            "name": "heartbeat.set", "arguments": "{\"enabled\":true}"}},
    ]
    lan.passes[:] = [refused_pass, RECORDED["passes"][-1]]
    endpoint = f"http://127.0.0.1:{lan.server_address[1]}/v1"
    bench = _automation_on(hub, endpoint, monkeypatch)

    _ok(hub, "POST", f"/api/workbenches/{bench}/run", {})

    results = _ok(hub, "GET", f"/api/workbenches/{bench}")["workbench"]["results"]
    assert results and results[0]["status"] == "done", results
    assert results[0]["used"] is None, results[0]  # a refused call touched nothing
    second = [body for body in lan.seen if "tools" in body][1]["messages"]
    answers = [m["content"] for m in second if m["role"] == "tool"]
    assert len(answers) == 2 and all("error" in a for a in answers), answers
    assert "MCP-005" in answers[0] or "palette" in answers[0], answers
