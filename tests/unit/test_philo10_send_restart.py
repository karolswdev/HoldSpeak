"""PHILO-10-01 R3: a send caught by a REAL hub restart (design section 4a), and a prepared send that survives it.

A hub is a PROCESS here (the Phase 7 F13 pattern; ``test_philo9_steward_restart``):
the real ``MeetingWebServer`` under uvicorn in a child process over an isolated
HOME, killed with SIGKILL while a send is inside its dispatch (held before or
after the real file write), then a NEW process booted on the same database. A
new service object in one process is not a restart.

* The new process's startup recovery ends the send ``indeterminate /
  hub_restart_during_send`` with its receipt, and in THAT transaction the row
  ends ``unknown`` (``interrupted``) with its history row; a file already on
  disk with the digest is recorded ``found_on_disk`` (still UNKNOWN).
* A replay of the same key answers that row: no second dispatch, one receipt,
  one history row.
* An AGENT's prepared send (made over ``/api/mcp`` with a Settings-issued
  credential) survives the restart with its preview, and the owner sends it on
  the new process.

Red on the round-two design (the mutation "drop the restart effect", recorded in
the evidence): the row stays ``dispatching`` and no history row is written.
"""
from __future__ import annotations

import json
import os
import signal
import sqlite3
import subprocess
import sys
import textwrap
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKEN = "philo10-01-restart-token"

_CHILD = textwrap.dedent('''
    import sys, threading, time
    from unittest.mock import MagicMock
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    hold = sys.argv[2] if len(sys.argv) > 2 else ""
    forever = threading.Event()
    if hold == "slow":  # PHILO-10-02 GATE 2: a dispatch that takes 1.5 s
        from holdspeak.services.channel_contract import FileChannel
        real = FileChannel.dispatch

        def dispatch(channel, row, *rest):
            time.sleep(1.5)
            return real(channel, row, *rest)

        FileChannel.dispatch = dispatch
    if hold in ("before", "after"):
        from holdspeak.services.channel_contract import FileChannel
        real = FileChannel.dispatch

        def dispatch(channel, row, *rest):
            if hold == "before":
                forever.wait()
            outcome = real(channel, row, *rest)
            forever.wait()
            return outcome

        FileChannel.dispatch = dispatch

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        auth_token=sys.argv[1],
    )
    print("URL " + server.start(), flush=True)
    while True:
        time.sleep(1)
''')


class HubProcess:
    def __init__(self, home: Path, hold: str = "", extra_env: dict[str, str] | None = None) -> None:
        env = dict(os.environ, HOME=str(home), **(extra_env or {}))
        env.pop("HOLDSPEAK_ALLOW_REAL_HOME", None)
        self.proc = subprocess.Popen(
            [sys.executable, "-c", _CHILD, TOKEN, hold], cwd=str(REPO_ROOT), env=env,
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

    def call(self, method: str, path: str, body: Any = None, token: str = TOKEN, timeout: float = 60) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.url + path, data=data, method=method, headers={
            "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.status, json.loads(resp.read() or b"null")
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"null")

    def kill(self) -> None:
        self.proc.send_signal(signal.SIGKILL)
        self.proc.wait(timeout=30)


def _db(home: Path) -> Path:
    return home / ".local" / "share" / "holdspeak" / "holdspeak.db"


def _rows(home: Path, sql: str, *args: Any) -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(_db(home)))
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


def _until(check: Any, timeout: float = 30.0) -> Any:
    deadline = time.time() + timeout
    while time.time() < deadline:
        value = check()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("condition never held")


def _agent_prepare(hub: HubProcess, document_ref: str, dest: str) -> dict[str, Any]:
    status, _ = hub.call("PUT", "/api/settings/remote", {"enabled": True})
    assert status == 200
    status, issued = hub.call("POST", "/api/settings/remote/credentials",
                              {"identity": "restart-agent", "palette": "PROJECT"})
    assert status == 200, issued
    status, answer = hub.call("POST", "/api/mcp", {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "channel.prepare", "arguments": {"document_ref": document_ref, "destination_id": dest}}},
        token=issued["token"])
    assert status == 200, answer
    assert answer["result"]["isError"] is False, answer
    return json.loads(answer["result"]["content"][0]["text"])


def _source(hub: HubProcess, source_kind: str) -> str:
    if source_kind == "project_update":
        status, made = hub.call("POST", "/api/projects", {"name": "Payments ledger cutover"})
        assert status == 200, made
        pid = made["project"]["id"]
        status, drafted = hub.call("POST", f"/api/projects/{pid}/updates/draft", {})
        assert status == 200, drafted
        update = drafted["update"]["id"]
        assert hub.call("POST", f"/api/updates/{update}/publish", {})[0] == 200
        return f"project_update:{update}"
    if source_kind == "desk_decision":
        status, made = hub.call("POST", "/api/decisions", {
            "title": "Keep the cutover window", "status": "accepted",
            "context_markdown": "The migration is ready for the agreed window.",
            "decision_markdown": "Run the migration during the cutover window.",
            "consequences_markdown": "The support team monitors the result.",
        })
        assert status == 201, made
        return f"desk_decision:{made['decision']['id']}"
    raise AssertionError(source_kind)


def _history(home: Path, document_ref: str) -> list[dict[str, Any]]:
    if document_ref.startswith("project_update:"):
        update = document_ref.split(":", 1)[1]
        return _rows(home, "SELECT outcome, operation_id, channel FROM project_update_deliveries WHERE update_id=?", update)
    return _rows(home, "SELECT state AS outcome, send_operation_id AS operation_id, channel FROM channel_sends "
                      "WHERE document_ref=? AND state IN ('sent','unknown')", document_ref)


@pytest.mark.timeout(240)
@pytest.mark.parametrize("form", ["send_id", "inline"])
@pytest.mark.parametrize("hold", ["before", "after"], ids=["killed-before-the-write", "killed-after-the-write"])
@pytest.mark.parametrize("source_kind", ["project_update", "desk_decision"])
def test_r3_a_restart_during_dispatching_ends_unknown_once_and_the_replay_answers_it(
    tmp_path: Path, form: str, hold: str, source_kind: str,
) -> None:
    home, folder = tmp_path / "home", tmp_path / "out"
    home.mkdir()
    folder.mkdir()
    first = HubProcess(home, hold=hold)
    try:
        document_ref = _source(first, source_kind)
        status, saved = first.call("POST", "/api/channels/destinations",
                                   {"name": "Team folder", "channel": "file", "folder": str(folder)})
        assert status == 200, saved
        dest = saved["destination"]["id"]
        waiting = _agent_prepare(first, document_ref, dest)["send"]  # survives the restart, never pressed here
        if form == "send_id":
            prepared = _agent_prepare(first, document_ref, dest)["send"]
            body: dict[str, Any] = {"send_id": prepared["id"], "command_id": f"restart-{form}-{hold}"}
        else:
            status, preview = first.call("POST", "/api/channels/preview", {"document_ref": document_ref, "destination_id": dest})
            body = {"document_ref": document_ref, "destination_id": dest, "preview_digest": preview["payload_digest"],
                    "command_id": f"restart-{form}-{hold}"}
        def press() -> None:
            try:
                first.call("POST", "/api/channels/send", body, timeout=120)
            except OSError:  # the process is killed under the caller: a lost caller
                pass

        threading.Thread(target=press, daemon=True).start()
        row = _until(lambda: next(iter(_rows(home, "SELECT * FROM channel_sends WHERE state='dispatching'")), None))
        if hold == "after":
            _until(lambda: list(folder.iterdir()))
    finally:
        first.kill()
    second = HubProcess(home)
    try:
        [settled] = _rows(home, "SELECT * FROM channel_sends WHERE id=?", row["id"])
        assert (settled["state"], settled["reason"]) == ("unknown", "interrupted"), settled
        [operation] = _rows(home, "SELECT o.state, r.outcome FROM kernel_operations o JOIN kernel_receipts r"
                                  " ON r.operation_id=o.operation_id WHERE o.operation_id=?", row["send_operation_id"])
        assert operation == {"state": "indeterminate", "outcome": "hub_restart_during_send"}, operation
        assert len(_rows(home, "SELECT 1 FROM kernel_receipts WHERE operation_id=?", row["send_operation_id"])) == 1
        assert _history(home, document_ref) == [{"outcome": "unknown", "operation_id": row["send_operation_id"], "channel": "file"}]
        on_disk = sorted(folder.iterdir())
        proof = json.loads(settled["proof_json"]) if settled["proof_json"] else None
        if hold == "after":
            [written] = on_disk
            assert proof == {"found_on_disk": {"path": str(written), "sha256": settled["payload_digest"],
                                               "size": written.stat().st_size}}
        else:
            assert on_disk == [] and proof is None
        status, replayed = second.call("POST", "/api/channels/send", body)
        assert status == 200, replayed
        assert (replayed["outcome"], replayed["send"]["reason"]) == ("unknown", "interrupted")
        assert replayed["operation_id"] == row["send_operation_id"]
        assert sorted(folder.iterdir()) == on_disk  # no second dispatch
        assert len(_history(home, document_ref)) == 1
        # The agent's prepared send survived the restart with its preview; the owner sends it now.
        status, listed = second.call("GET", f"/api/channels/sends?send_id={waiting['id']}")
        [survivor] = listed["sends"]
        assert (survivor["state"], survivor["prepared_by"]["kind"]) == ("prepared", "agent")
        assert survivor["preview"] == waiting["preview"] and survivor["payload_digest"] == waiting["payload_digest"]
        status, sent = second.call("POST", "/api/channels/send", {"send_id": waiting["id"]})
        assert status == 200 and sent["outcome"] == "sent", sent
        assert Path(sent["send"]["proof"]["path"]).read_text() == survivor["preview"]["text"]
    finally:
        second.kill()
