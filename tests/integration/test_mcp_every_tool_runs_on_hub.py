"""Every registered MCP tool runs on a real hub through ``POST /api/mcp``.

The sweep boots a real hub process on a throwaway HOME, lists the tools, and calls
each one once with placeholder arguments built from its input schema. A tool
passes when it answers with a result, or with an error of a KNOWN class: an
argument, validation, not-found or no-engine refusal (:func:`_refusal_is_known`).
Every other answer fails and names the tool: an unknown error, a JSON-RPC error,
an HTTP failure, no answer.

History (2026-10-03 backend inventory, finding 1): eleven tools failed on every
call in the real product while their unit tests were green, because a unit test
calls ``dispatch`` with no running event loop and the hub calls it inside one.

Also here, on the same real hub:
- the mutation proof: with dispatch broken for every tool, the sweep fails for
  every tool (Astra on #766: the first sweep passed with all 246 broken);
- the ordering proof: two concurrent ``desk.update`` calls on one Note lose no
  change (Astra on #766: 39 of 40 pairs lost a change on a worker pool).
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

TOKEN = "mcp-sweep-token"

_CHILD = r'''
import sys, time
from unittest.mock import MagicMock
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

if sys.argv[2] == "broken":  # the mutation: no tool can run at all
    from holdspeak.mcp import server as mcp_server

    def unavailable(*_args, **_kwargs):
        raise RuntimeError("MCP executor is unavailable")

    mcp_server.dispatch = unavailable
    mcp_server.dispatch_for_palette = unavailable

server = MeetingWebServer(
    WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
    auth_token=sys.argv[1],
)
print("URL " + server.start(), flush=True)
while True:
    time.sleep(1)
'''

# An error answer passes only if it is one of these classes. Placeholder
# arguments on an empty HOME can only be refused for what they are: wrong,
# unknown, or in need of an engine or a store that a fresh HOME does not have.
KNOWN_CODE = re.compile(
    r"not_found|unknown|invalid|validation|conflict|mismatch|stale|not_saved|not_absolute"
    r"|^inference_target_unavailable$"  # ask.run: no model on a fresh HOME
    r"|^inbox_unavailable$"  # thought.create: no inbox on a fresh HOME
)
KNOWN_MESSAGE = re.compile(
    r"^people_store_unavailable$"  # no People keystore on a fresh HOME
    r"|must be qualified as kind:id|^parent_operation_unknown$|not allowlisted for MCP"
    r"|is retired|live capture controller|not found: x$|^Unknown shelf state: x$"
)
# Code-less refusals of the placeholder id that leak a raw exception text. They
# are argument errors; each is named so that no other tool can hide behind them.
KNOWN_BY_TOOL = {
    "decision_record.create_from_meeting": "'x'",
    "decision_record.create_from_desk": "'x'",
    "project.open_review": "FOREIGN KEY constraint failed",
}


def _refusal_is_known(name: str, payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    code, message = payload.get("code"), payload.get("error")
    if isinstance(code, str) and KNOWN_CODE.search(code):
        return True
    if not isinstance(message, str):
        return False
    return bool(KNOWN_MESSAGE.search(message)) or KNOWN_BY_TOOL.get(name) == message


class _Hub:
    def __init__(self, home: Path, mode: str = "real") -> None:
        env = dict(os.environ, HOME=str(home), HF_HUB_OFFLINE="1")
        env.pop("HOLDSPEAK_ALLOW_REAL_HOME", None)
        self.proc = subprocess.Popen(
            [sys.executable, "-c", _CHILD, TOKEN, mode],
            cwd=str(Path(__file__).resolve().parents[2]), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        lines: list[str] = []
        for line in self.proc.stdout:  # type: ignore[union-attr]
            lines.append(line)
            if line.startswith("URL "):
                self.url = line.split(" ", 1)[1].strip().rstrip("/")
                break
        else:  # pragma: no cover - the child died before serving
            raise AssertionError("the hub process never served:\n" + "".join(lines[-40:]))
        threading.Thread(target=lambda: [None for _ in self.proc.stdout], daemon=True).start()  # type: ignore[union-attr]

    def mcp(self, method: str, params: dict[str, Any], timeout: float = 60) -> tuple[int, Any]:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        request = urllib.request.Request(self.url + "/api/mcp", data=body, method="POST", headers={
            "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.status, json.loads(resp.read() or b"null")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", "replace")

    def kill(self) -> None:
        self.proc.send_signal(signal.SIGKILL)
        self.proc.wait(timeout=30)


def _placeholder(schema: Any) -> Any:
    """One value that satisfies the schema's type, with no meaning."""
    if not isinstance(schema, dict):
        return "x"
    if schema.get("enum"):
        return schema["enum"][0]
    kind = schema.get("type")
    if isinstance(kind, list):
        kind = next((k for k in kind if k != "null"), "string")
    if kind == "integer" or kind == "number":
        return max(1, int(schema.get("minimum", 1)))
    if kind == "boolean":
        return False
    if kind == "array":
        return []
    if kind == "object":
        return _arguments(schema)
    return "x"


def _arguments(schema: Any) -> dict[str, Any]:
    """Placeholder arguments: every required property, nothing else."""
    if not isinstance(schema, dict):
        return {}
    properties = schema.get("properties") or {}
    return {name: _placeholder(properties.get(name)) for name in schema.get("required") or []}


def _tool_json(answer: Any) -> Any:
    """The JSON a tool answered with (its one text content block)."""
    return json.loads(answer["result"]["content"][0]["text"])


def _sweep(hub: _Hub) -> tuple[int, dict[str, str]]:
    """Call every tool once. Returns (tool count, {tool: why it cannot run})."""
    status, listed = hub.mcp("tools/list", {})
    assert status == 200, listed
    tools = listed["result"]["tools"]
    broken: dict[str, str] = {}
    for tool in tools:
        name = tool["name"]
        try:
            status, answer = hub.mcp("tools/call", {
                "name": name, "arguments": _arguments(tool.get("inputSchema"))})
        except Exception as exc:  # a timeout or a dropped connection
            broken[name] = f"no answer: {type(exc).__name__}: {exc}"
            continue
        text = answer if isinstance(answer, str) else json.dumps(answer)
        if status != 200 or not isinstance(answer, dict) or "result" not in answer:
            broken[name] = f"HTTP {status}: {text[:200]}"
            continue
        if not answer["result"].get("isError"):
            continue
        try:
            payload = _tool_json(answer)
        except Exception:
            payload = None
        if not _refusal_is_known(name, payload):
            broken[name] = text[:300]
    assert hub.mcp("ping", {})[0] == 200  # the hub is still alive after the sweep
    return len(tools), broken


@pytest.mark.timeout(900)
def test_every_mcp_tool_runs_on_the_real_hub(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    hub = _Hub(home)
    try:
        count, broken = _sweep(hub)
    finally:
        hub.kill()
    assert count > 200, count  # the real catalogue, not a stub
    report = "\n".join(f"  {name}: {why}" for name, why in sorted(broken.items()))
    assert not broken, f"{len(broken)} MCP tool(s) cannot run on the hub:\n{report}"


@pytest.mark.timeout(900)
def test_the_sweep_fails_for_every_tool_when_no_tool_can_run(tmp_path: Path) -> None:
    """The mutation: dispatch raises ``RuntimeError("MCP executor is unavailable")`` for every tool."""
    home = tmp_path / "home"
    home.mkdir()
    hub = _Hub(home, "broken")
    try:
        count, broken = _sweep(hub)
    finally:
        hub.kill()
    assert count > 200, count
    assert len(broken) == count, f"the sweep passed {count - len(broken)} of {count} broken tools"


@pytest.mark.timeout(900)
def test_concurrent_edits_of_one_note_lose_no_change(tmp_path: Path) -> None:
    """Forty pairs: one call changes the title, one the body, at the same time. Both changes stay."""
    home = tmp_path / "home"
    home.mkdir()
    hub = _Hub(home)

    def call(name: str, arguments: dict[str, Any]) -> Any:
        status, answer = hub.mcp("tools/call", {"name": name, "arguments": arguments})
        assert status == 200 and answer["result"]["isError"] is False, answer
        return _tool_json(answer)

    lost: list[str] = []
    try:
        note_id = call("desk.create", {"kind": "notes", "data": {"title": "T", "body_markdown": "B"}})["id"]
        for round_ in range(40):
            title, body = f"Title {round_}", f"Body {round_}"
            gate = threading.Barrier(2)

            def update(data: dict[str, Any]) -> None:
                gate.wait(10)
                call("desk.update", {"kind": "notes", "id": note_id, "data": data})

            pair = [threading.Thread(target=update, args=({"title": title},)),
                    threading.Thread(target=update, args=({"body_markdown": body},))]
            for thread in pair:
                thread.start()
            for thread in pair:
                thread.join(60)
            note = call("desk.get", {"kind": "notes", "id": note_id})
            if (note.get("title"), note.get("body_markdown")) != (title, body):
                lost.append(f"round {round_}: {note.get('title')!r} / {note.get('body_markdown')!r}")
    finally:
        hub.kill()
    assert not lost, f"{len(lost)} of 40 pairs lost a change:\n" + "\n".join(lost)
