"""Every registered MCP tool runs on a real hub through ``POST /api/mcp``.

The sweep boots a real hub process on a throwaway HOME, lists the tools, and calls
each one once with placeholder arguments built from its input schema. A tool may
answer with an argument, validation or not-found error. A tool must never answer
with a transport or runtime-plumbing error (an event-loop refusal, a runtime that
was never started, a coroutine that was never awaited, an HTTP failure).

History (2026-10-03 backend inventory, finding 1): ten tools failed on every call
in the real product while their unit tests were green, because a unit test calls
``dispatch`` with no running event loop and the hub calls it inside one.
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

server = MeetingWebServer(
    WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
    auth_token=sys.argv[1],
)
print("URL " + server.start(), flush=True)
while True:
    time.sleep(1)
'''

# The answers that mean "the hub could not run this tool at all".
PLUMBING = re.compile(
    r"active event loop|event loop is|no running event loop|no current event loop"
    r"|different (event )?loop|runtime is not (started|running)|was never awaited"
    r"|coroutine object|asyncio\.run\(\) cannot",
    re.IGNORECASE,
)


class _Hub:
    def __init__(self, home: Path) -> None:
        env = dict(os.environ, HOME=str(home), HF_HUB_OFFLINE="1")
        env.pop("HOLDSPEAK_ALLOW_REAL_HOME", None)
        self.proc = subprocess.Popen(
            [sys.executable, "-c", _CHILD, TOKEN],
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


@pytest.mark.timeout(900)
def test_every_mcp_tool_runs_on_the_real_hub(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    hub = _Hub(home)
    broken: dict[str, str] = {}
    try:
        status, listed = hub.mcp("tools/list", {})
        assert status == 200, listed
        tools = listed["result"]["tools"]
        assert len(tools) > 200, len(tools)  # the real catalogue, not a stub
        for tool in tools:
            name = tool["name"]
            try:
                status, answer = hub.mcp("tools/call", {
                    "name": name, "arguments": _arguments(tool.get("inputSchema"))})
            except Exception as exc:  # a timeout or a dropped connection
                broken[name] = f"no answer: {type(exc).__name__}: {exc}"
                continue
            text = answer if isinstance(answer, str) else json.dumps(answer)
            if status != 200:
                broken[name] = f"HTTP {status}: {text[:200]}"
                continue
            found = PLUMBING.search(text)
            if found:
                start = max(0, found.start() - 80)
                broken[name] = text[start:found.end() + 40]
        # The hub is still alive after the sweep.
        assert hub.mcp("ping", {})[0] == 200
    finally:
        hub.kill()
    report = "\n".join(f"  {name}: {why}" for name, why in sorted(broken.items()))
    assert not broken, f"{len(broken)} MCP tool(s) cannot run on the hub:\n{report}"
