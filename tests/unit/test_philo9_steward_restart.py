"""PHILO-9-02 L6 + D1: the steward's recovery and a delivery's replay across a REAL hub restart.

A hub is a PROCESS here (the Phase 7 F13 pattern, ``test_philo7_grant_restart``):
the real ``MeetingWebServer`` under uvicorn in a child process over an isolated
HOME and database, killed with SIGKILL (no clean shutdown) while a REAL run is
in flight, then a NEW process booted on the same database. A new service object
in one process is not a restart (the beat, section 7).

* **L6** at each point a run can be caught -- its operation admitted with no
  run yet, its run queued, running, stopping, and one of its children claimed --
  the new process's startup ends every steward operation ``indeterminate /
  hub_restart_during_steward`` with its receipt, children first, and the run
  row ``interrupted``; nothing is replayed (the held effect never ran); a
  repeat restart is a no-op; the project's slot is free for a new run.
* **D1** a mark delivered with a ``command_id``, then a restart: the same key
  answers the original row, time, operation and receipt; no second row.

Red on main (L6): the run is interrupted by the old domain-only recovery, and
there is no operation and no receipt at all.
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

# Owner ruling 2026-10-03 (fast tests): each case boots, kills and boots a real hub process (35 s in all). It is marked slow: the fast
# run (`-m "not slow"`) leaves it out; the nightly full run and a direct run keep it.
pytestmark = pytest.mark.slow

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKEN = "philo9-02-restart-token"

_CHILD = textwrap.dedent('''
    import sys, threading, time
    from unittest.mock import MagicMock
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    hold = sys.argv[2] if len(sys.argv) > 2 else ""
    forever = threading.Event()
    if hold == "insert":
        from holdspeak.db.steward import StewardRunRepository
        StewardRunRepository.insert_run_in_transaction = lambda *a, **k: forever.wait()
    if hold == "queued":
        from holdspeak.services.steward_contract import StewardContract
        StewardContract._work = lambda *a, **k: forever.wait()
    if hold in ("running", "stopping"):
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
        ProjectEvidenceCollector.collect_all = lambda *a, **k: forever.wait()
    if hold == "child":
        from holdspeak.services.project_update_service import ProjectUpdateService
        ProjectUpdateService.draft_update = lambda *a, **k: forever.wait()

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        auth_token=sys.argv[1],
    )
    print("URL " + server.start(), flush=True)
    while True:
        time.sleep(1)
''')


class HubProcess:
    def __init__(self, home: Path, hold: str = "") -> None:
        env = dict(os.environ, HOME=str(home))
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

    def call(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.url + path, data=data, method=method, headers={
            "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                return resp.status, json.loads(resp.read() or b"null")
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"null")

    def kill(self) -> None:
        self.proc.send_signal(signal.SIGKILL)
        self.proc.wait(timeout=30)


def _db(home: Path) -> Path:
    return home / ".local" / "share" / "holdspeak" / "holdspeak.db"


def _rows(home: Path, sql: str, *args: Any) -> list[tuple[Any, ...]]:
    conn = sqlite3.connect(str(_db(home)))
    try:
        return [tuple(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


def _until(check: Any, timeout: float = 30.0) -> Any:
    deadline = time.time() + timeout
    while time.time() < deadline:
        value = check()
        if value:
            return value
        time.sleep(0.1)
    raise AssertionError("the condition never held")


def _steward_ops(home: Path) -> list[tuple[Any, ...]]:
    return _rows(home, "SELECT o.operation_id, o.name, o.state, o.parent_operation_id, r.outcome"
                       " FROM kernel_operations o LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id"
                       " WHERE o.name IN ('project.run_steward','project.steward.effect','project.stop_steward')"
                       " ORDER BY o.created_at")


def _fire(call: Any) -> None:
    threading.Thread(target=lambda: _swallow(call), daemon=True).start()


def _swallow(call: Any) -> None:
    try:
        call()
    except Exception:
        pass  # the connection dies with the killed process


@pytest.mark.timeout(300)
@pytest.mark.parametrize("hold", ["insert", "queued", "running", "stopping", "child"])
def test_l6_a_real_restart_ends_every_steward_operation_and_its_run_once(tmp_path: Path, hold: str) -> None:
    home = tmp_path / "home"
    home.mkdir()
    first = HubProcess(home, hold)
    try:
        status, made = first.call("POST", "/api/projects", {"name": "Payments ledger cutover"})
        assert status == 200, made
        pid = made["project"]["id"]
        if hold == "child":
            assert first.call("PUT", f"/api/projects/{pid}/steward/policy", {"eligible_effect_kinds": ["draft_update"]})[0] == 200
        _fire(lambda: first.call("POST", f"/api/projects/{pid}/steward/runs", {}))
        if hold == "insert":
            _until(lambda: [r for r in _steward_ops(home) if r[1] == "project.run_steward" and r[2] == "claimed"])
            assert _rows(home, "SELECT COUNT(*) FROM steward_runs") == [(0,)]
        else:
            run_state = {"queued": "queued", "running": "running", "stopping": "running", "child": "running"}[hold]
            _until(lambda: _rows(home, "SELECT id FROM steward_runs WHERE state=?", run_state))
        if hold == "stopping":
            run_id = _rows(home, "SELECT id FROM steward_runs")[0][0]
            status, stopped = first.call("POST", f"/api/steward/runs/{run_id}/stop", {})
            assert status == 200, stopped
            assert _rows(home, "SELECT state FROM steward_runs") == [("stopping",)]
        if hold == "child":
            _until(lambda: [r for r in _steward_ops(home) if r[1] == "project.steward.effect" and r[2] == "claimed"])
    finally:
        first.kill()
    before = _steward_ops(home)
    assert [r for r in before if r[1] == "project.run_steward"][0][2] == "claimed"

    second = HubProcess(home)
    try:
        after = {r[0]: r for r in _steward_ops(home)}
        run_op = next(r for r in after.values() if r[1] == "project.run_steward")
        assert (run_op[2], run_op[4]) == ("indeterminate", "hub_restart_during_steward"), after
        for row in after.values():
            if row[1] == "project.steward.effect":
                assert (row[2], row[4]) == ("indeterminate", "hub_restart_during_steward"), row
                assert row[3] == run_op[0]
            if row[1] == "project.stop_steward":
                assert (row[2], row[4]) == ("succeeded", "stop_requested")
        receipts = _rows(home, "SELECT operation_id, COUNT(*) FROM kernel_receipts GROUP BY operation_id HAVING COUNT(*) > 1")
        assert receipts == [], receipts
        runs = _rows(home, "SELECT state, operation_id FROM steward_runs")
        if hold == "insert":
            assert runs == []  # an operation with no run: closed on its own
        else:
            assert runs == [("interrupted", run_op[0])], runs
        # Children first: the effect's receipt is not later than its parent's.
        if hold == "child":
            child = next(r for r in after.values() if r[1] == "project.steward.effect")
            ordered = _rows(home, "SELECT operation_id FROM kernel_receipts WHERE operation_id IN (?, ?) ORDER BY created_at, rowid",
                            child[0], run_op[0])
            assert [r[0] for r in ordered] == [child[0], run_op[0]]
            assert _rows(home, "SELECT COUNT(*) FROM project_updates") == [(0,)]  # the held effect never replayed
        # The slot is free: a new explicit start runs to its end.
        pid = _rows(home, "SELECT id FROM projects")[0][0]
        status, started = second.call("POST", f"/api/projects/{pid}/steward/runs", {})
        assert status == 200, started
        _until(lambda: _rows(home, "SELECT state FROM steward_runs WHERE id=? AND state='completed'", started["run_id"]))
    finally:
        second.kill()
    frozen = _rows(home, "SELECT COUNT(*) FROM kernel_receipts")

    third = HubProcess(home)  # a repeat recovery is a no-op
    try:
        assert _rows(home, "SELECT COUNT(*) FROM kernel_receipts") == frozen
    finally:
        third.kill()


@pytest.mark.timeout(300)
def test_d1_a_delivery_replay_after_a_real_restart_answers_the_original(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    body = {"delivered_to": "Priya", "command_id": "confirm-restart"}
    first = HubProcess(home)
    try:
        pid = first.call("POST", "/api/projects", {"name": "Payments"})[1]["project"]["id"]
        update = first.call("POST", f"/api/projects/{pid}/updates/draft", {})[1]["update"]["id"]
        assert first.call("POST", f"/api/updates/{update}/publish", {})[0] == 200
        status, original = first.call("POST", f"/api/updates/{update}/delivered", body)
        assert status == 200, original
    finally:
        first.kill()
    second = HubProcess(home)
    try:
        status, replayed = second.call("POST", f"/api/updates/{update}/delivered", body)
        assert status == 200, replayed
        assert replayed["delivery"] == original["delivery"]
        assert replayed["operation_id"] == original["operation_id"]
        assert replayed["receipt"]["receipt_id"] == original["receipt"]["receipt_id"]
        assert _rows(home, "SELECT COUNT(*) FROM project_update_deliveries") == [(1,)]
    finally:
        second.kill()
