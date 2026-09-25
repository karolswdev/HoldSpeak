"""PHILO-7-02 F13 + F11: the grant survives a REAL hub restart; a waiting desk write is recovered.

A hub is a PROCESS here: the credential store is a module singleton captured
by the auth middleware, so only a new process is a real restart (the lifecycle
beat, "Probes": restart was not probeable in-process). The fence boots the real
``MeetingWebServer`` under uvicorn in a child process over an isolated HOME and
database, grants G1 to an agent identity through the real route, kills the
process (SIGKILL: no clean shutdown) while a REAL agent request is in flight
and waiting in ``awaiting_decision`` (its approval held by the fence's child
script), boots a NEW process on the same database, issues a new credential for the same
identity through the real route, and files a note under G1 over ``/api/mcp``.

Red on main: the grant route is a 404 and the agent's filing makes no
operation and no receipt.
"""
from __future__ import annotations

import json
import os
import threading
import time
import signal
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKEN = "philo7-02-restart-token"
AGENT_ID = "restart-agent"

_CHILD = textwrap.dedent('''
    import sys, threading, time
    from unittest.mock import MagicMock
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    if len(sys.argv) > 2 and sys.argv[2] == "hold":
        # The fence's hold: a desk write's approval never returns, so the REAL
        # request waits in awaiting_decision until the process is killed.
        from holdspeak.kernel.broker import Broker
        real_decide = Broker.decide
        def held(self, operation_id, *args, **kwargs):
            if (self.store.operation(operation_id) or {}).get("name") == "zone.file":
                threading.Event().wait()
            return real_decide(self, operation_id, *args, **kwargs)
        Broker.decide = held

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        auth_token=sys.argv[1],
    )
    print("URL " + server.start(), flush=True)
    while True:
        time.sleep(1)
''')


class HubProcess:
    def __init__(self, home: Path, *, hold: bool = False) -> None:
        env = dict(os.environ, HOME=str(home))
        env.pop("HOLDSPEAK_ALLOW_REAL_HOME", None)
        self.proc = subprocess.Popen(
            [sys.executable, "-c", _CHILD, TOKEN, *(["hold"] if hold else [])], cwd=str(REPO_ROOT), env=env,
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

    def call(self, method: str, path: str, body: Any = None, token: str = TOKEN) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.url + path, data=data, method=method, headers={
            "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                return resp.status, json.loads(resp.read() or b"null")
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"null")

    def tool(self, token: str, name: str, arguments: dict[str, Any]) -> tuple[bool, Any]:
        status, body = self.call("POST", "/api/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                      "params": {"name": name, "arguments": arguments}}, token=token)
        assert status == 200, body
        return body["result"]["isError"], json.loads(body["result"]["content"][0]["text"])

    def credential(self) -> str:
        assert self.call("PUT", "/api/settings/remote", {"enabled": True})[0] == 200
        status, issued = self.call("POST", "/api/settings/remote/credentials", {"identity": AGENT_ID, "palette": "DESK"})
        assert status == 200, issued
        return issued["token"]

    def kill(self) -> None:
        self.proc.send_signal(signal.SIGKILL)
        self.proc.wait(timeout=30)


def _swallow(call: Any) -> None:
    try:
        call()
    except Exception:
        pass  # the connection dies with the killed process


def _db(home: Path) -> Path:
    return home / ".local" / "share" / "holdspeak" / "holdspeak.db"


def _rows(home: Path, sql: str, *args: Any) -> list[tuple[Any, ...]]:
    import sqlite3

    conn = sqlite3.connect(str(_db(home)))
    try:
        return [tuple(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


def _waiting(home: Path) -> list[tuple[Any, ...]]:
    return _rows(home, "SELECT operation_id, name, principal_identity FROM kernel_operations WHERE state='awaiting_decision'")


@pytest.mark.timeout(300)
def test_f13_the_grant_survives_a_real_restart_and_f11_recovers_a_waiting_write(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    first = HubProcess(home, hold=True)
    try:
        status, granted = first.call("PUT", f"/api/settings/remote/delegations/{AGENT_ID}", {})
        assert status == 200, granted
        g1 = granted["grant_id"]
        token = first.credential()
        _status, zone = first.call("POST", "/api/directories", {"name": "Before the kill"})
        _status, note = first.call("POST", "/api/notes", {"title": "in flight"})
        # A REAL agent request, in flight when the hub dies: its approval is
        # held, so it waits in awaiting_decision (Astra MISSED 4).
        in_flight = threading.Thread(target=lambda: _swallow(lambda: first.tool(token, "zone.file", {
            "directory_id": zone["directory"]["id"], "primitive_id": f"note:{note['note']['id']}"})), daemon=True)
        in_flight.start()
        deadline = time.time() + 30
        while not _waiting(home) and time.time() < deadline:
            time.sleep(0.1)
        waiting_rows = _waiting(home)
        assert [(r[1], r[2]) for r in waiting_rows] == [("zone.file", AGENT_ID)], waiting_rows
        waiting = str(waiting_rows[0][0])
    finally:
        first.kill()

    second = HubProcess(home)
    try:
        # F11: the new process's startup ended the waiting desk write, with its receipt.
        assert _rows(home, "SELECT o.state, r.outcome FROM kernel_operations o JOIN kernel_receipts r "
                           "ON r.operation_id=o.operation_id WHERE o.operation_id=?", waiting) == [
            ("indeterminate", "hub_restart_during_decision")]
        # The old token died with the old process; a new credential for the same identity.
        token = second.credential()
        status, zone = second.call("POST", "/api/directories", {"name": "After restart"})
        status, note = second.call("POST", "/api/notes", {"title": "filed after restart"})
        is_error, filed = second.tool(token, "zone.file", {
            "directory_id": zone["directory"]["id"], "primitive_id": f"note:{note['note']['id']}"})
        assert is_error is False, filed
        assert filed["receipt"]["authority_basis"].split(":", 2)[1] == g1
        ledger = second.call("GET", "/api/settings/remote")[1]
        assert ledger["credentials"][0]["delegation"]["state"] == "LIVE"
        assert ledger["credentials"][0]["delegation"]["grant_id"] == g1
    finally:
        second.kill()
