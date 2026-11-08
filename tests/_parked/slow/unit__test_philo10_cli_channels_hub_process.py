"""Parked 2026-11-08 (owner: no pipeline restarts a real hub): the three CLI-channel cases that boot a HubProcess, moved as text from tests/unit/test_philo10_cli_channels.py. Not collected."""


"""PHILO-10-02: the GitHub and Atlassian channels, the nudge, and the steward's prepare.

Through the REAL hub on an isolated HOME (``TestClient`` over the hub's app and
``/api/mcp``) with the real producers: a published update from the Room's own
routes, destinations saved by ``channel.save_destination``, each channel's REAL
``plan`` and ``interpret``, the real kernel (``subprocess.exec`` children of the
send). Only the process edge is canned (``_philo10_cli.Canned``). The two GATES
from Codex Astra r2 on #692 come first. The mutation list (each fence red on a
deliberate in-code mutation, and the nudge fences red on main) is recorded in
the evidence.
"""
from __future__ import annotations

import json
import os
import random
import string
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_cli import EMAIL, SITE, Canned, install, save  # noqa: E402
from _philo10_send import SENTINEL, Hub, _boot, history, in_thread, prepare, room, send, sends, sent_text, until  # noqa: E402

CHANNELS = ["github", "jira", "confluence"]


@pytest.fixture


@pytest.mark.timeout(240)
def test_gate2_the_hub_answers_a_read_during_a_slow_send(tmp_path: Path) -> None:
    """One hub process serves both transports, one send each (fast diet 2026-10-12: one boot, not two)."""
    from test_philo10_send_restart import HubProcess

    home, folder = tmp_path / "home", tmp_path / "out"
    home.mkdir()
    folder.mkdir()
    hub = HubProcess(home, hold="slow")
    try:
        status, made = hub.call("POST", "/api/projects", {"name": "Payments ledger cutover"})
        pid = made["project"]["id"]
        update = hub.call("POST", f"/api/projects/{pid}/updates/draft", {})[1]["update"]["id"]
        # PHILO-15 B64: an update with no verified claim is refused; the owner's saved line is reviewed.
        assert hub.call("PUT", f"/api/updates/{update}", {"body_md": "## Progress\n\nThe ledger cutover is on track.\n"})[0] == 200
        assert hub.call("POST", f"/api/updates/{update}/publish", {})[0] == 200
        status, saved = hub.call("POST", "/api/channels/destinations",
                                 {"name": "Team folder", "channel": "file", "folder": str(folder)})
        assert status == 200, saved
        dest = saved["destination"]["id"]
        baseline = time.perf_counter()
        assert hub.call("GET", "/api/channels/destinations")[0] == 200
        baseline = time.perf_counter() - baseline
        for transport in ("http", "mcp"):
            status, prepared = hub.call("POST", "/api/channels/sends", {"document_ref": f"project_update:{update}", "destination_id": dest})
            body = {"send_id": prepared["send"]["id"]}

            def press(transport: str = transport, body: dict = body) -> Any:
                if transport == "http":
                    return hub.call("POST", "/api/channels/send", body)
                return hub.call("POST", "/api/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                     "params": {"name": "channel.send", "arguments": body}})

            thread, answer = in_thread(press)
            _started(home)
            started = time.perf_counter()
            status, _listed = hub.call("GET", "/api/channels/destinations")
            read = time.perf_counter() - started
            thread.join(30)
            assert status == 200
            assert answer and answer[0][0] == 200, (transport, answer)
            # The dispatch sleeps 1.5 s; the concurrent read must not wait for it.
            assert read < 0.5, f"{transport}: the read waited {read:.3f} s during the send (baseline {baseline:.3f} s)"
    finally:
        hub.kill()


@pytest.mark.timeout(240)
def test_a_real_kill_during_a_gh_create_ends_unknown_once_and_the_replay_never_runs_gh_again(tmp_path: Path) -> None:
    import signal
    import sqlite3

    from test_philo10_send_restart import HubProcess

    home, bin_dir, log = tmp_path / "home", tmp_path / "bin", tmp_path / "gh.log"
    home.mkdir()
    bin_dir.mkdir()
    fake = bin_dir / "gh"
    fake.write_text(_FAKE_GH)
    fake.chmod(0o755)
    env = {"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}", "FAKE_GH_LOG": str(log)}
    db = home / ".local" / "share" / "holdspeak" / "holdspeak.db"

    def rows(sql: str, *args: Any) -> list[dict[str, Any]]:
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in conn.execute(sql, args).fetchall()]
        finally:
            conn.close()

    first = HubProcess(home, extra_env=env)
    pids: list[int] = []
    try:
        pid = first.call("POST", "/api/projects", {"name": "Payments ledger cutover"})[1]["project"]["id"]
        update = first.call("POST", f"/api/projects/{pid}/updates/draft", {})[1]["update"]["id"]
        # PHILO-15 B64: an update with no verified claim is refused; the owner's saved line is reviewed.
        assert first.call("PUT", f"/api/updates/{update}", {"body_md": "## Progress\n\nThe ledger cutover is on track.\n"})[0] == 200
        assert first.call("POST", f"/api/updates/{update}/publish", {})[0] == 200
        status, saved = first.call("POST", "/api/channels/destinations", {
            "name": "Scratch issue", "channel": "github", "repo": "acme/scratch", "kind": "issue", "number": 1})
        assert status == 200, saved
        assert saved["destination"]["account"]["login"] == "octo-owner"
        status, prepared = first.call("POST", "/api/channels/sends",
                                      {"document_ref": f"project_update:{update}", "destination_id": saved["destination"]["id"]})
        body = {"send_id": prepared["send"]["id"], "command_id": "kill-during-gh"}

        def press() -> None:
            try:
                first.call("POST", "/api/channels/send", body, timeout=120)
            except OSError:
                pass

        threading.Thread(target=press, daemon=True).start()
        until(lambda: log.exists() and log.read_text().strip())
        [line] = log.read_text().strip().splitlines()
        pids.append(int(line.split()[0]))
        assert line.split()[1] == "600"  # the body file the real gh would read is 0600
        [row] = rows("SELECT * FROM channel_sends WHERE state='dispatching'")
    finally:
        first.kill()
        for gh_pid in pids:
            try:
                os.kill(gh_pid, signal.SIGKILL)
            except OSError:
                pass
    second = HubProcess(home, extra_env=env)
    try:
        [settled] = rows("SELECT * FROM channel_sends WHERE id=?", row["id"])
        assert (settled["state"], settled["reason"]) == ("unknown", "interrupted"), settled
        [operation] = rows("SELECT o.state, r.outcome FROM kernel_operations o JOIN kernel_receipts r"
                           " ON r.operation_id=o.operation_id WHERE o.operation_id=?", row["send_operation_id"])
        assert operation == {"state": "indeterminate", "outcome": "hub_restart_during_send"}, operation
        status, replayed = second.call("POST", "/api/channels/send", body)
        assert status == 200 and (replayed["outcome"], replayed["send"]["reason"]) == ("unknown", "interrupted")
        assert len(log.read_text().strip().splitlines()) == 1  # gh never ran again
        history_rows = rows("SELECT outcome FROM project_update_deliveries WHERE update_id=?", update)
        assert history_rows == [{"outcome": "unknown"}]
    finally:
        second.kill()


@pytest.mark.timeout(240)
def test_gate2_a_slow_cli_read_in_setup_or_recheck_never_blocks_the_hub(tmp_path: Path) -> None:
    """Codex Astra r1 finding 2: MCP channel.save_destination's identity read blocked a read 1.73 s.
    One hub process serves the four calls in turn (fast diet 2026-10-12: one boot, not four); each
    read starts once the fake gh has noted its start, so it lands inside the 1 s gh call."""
    from test_philo10_send_restart import HubProcess

    home, bin_dir = tmp_path / "home", tmp_path / "bin"
    home.mkdir()
    bin_dir.mkdir()
    fake = bin_dir / "gh"
    fake.write_text(_SLOW_GH)
    fake.chmod(0o755)
    gh_log = tmp_path / "gh.log"
    hub = HubProcess(home, extra_env={"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}", "SLOW_GH_LOG": str(gh_log)})
    try:
        for call in ("mcp-save-destination", "http-save-destination", "mcp-recheck", "http-recheck"):
            gh_log.unlink(missing_ok=True)
            destination = {"name": f"Scratch issue {call}", "channel": "github", "repo": "acme/scratch", "kind": "issue",
                           "number": 1}

            def slow(call: str = call, destination: dict = destination) -> Any:
                if call == "http-save-destination":
                    return hub.call("POST", "/api/channels/destinations", destination)
                if call == "http-recheck":
                    return hub.call("POST", "/api/connections/github/recheck", {})
                name, args = (("channel.save_destination", destination) if call == "mcp-save-destination"
                              else ("connection.recheck", {"provider_id": "github"}))
                return hub.call("POST", "/api/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                     "params": {"name": name, "arguments": args}})

            thread, answer = in_thread(slow)
            until(lambda: gh_log.exists() and gh_log.read_text().strip())  # the call is inside its 1 s gh read
            started = time.perf_counter()
            status, _listed = hub.call("GET", "/api/channels/destinations")
            read = time.perf_counter() - started
            thread.join(30)
            assert status == 200
            assert answer and answer[0][0] == 200, answer
            if call.startswith("mcp"):
                assert answer[0][1]["result"]["isError"] is False, answer
            assert read < 0.5, f"{call}: the read waited {read:.3f} s during the slow gh call"
    finally:
        hub.kill()
