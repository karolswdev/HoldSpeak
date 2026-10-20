"""AG14 T4: the real hub hand path, queue admission, and Done projection.

The hub and WorkbenchRunner stay real.  The only leaf stand-in is the native
agent process: it keeps a private tmux pane alive while this test feeds the
same hook events a native agent emits, including its Done turn.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.glass_infra import _boot
from tests.unit.test_agent_hand import OWNER, PROJECT, _seed
from tests.unit.test_factory_launch import _make_repo

TOKEN = "ag14-t4"

pytestmark = pytest.mark.timeout(180, method="thread")


def _call(base: str, method: str, path: str, body: Any = None) -> tuple[int, Any]:
    import urllib.error
    import urllib.request

    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw) if raw else {}


def _ok(base: str, method: str, path: str, body: Any = None) -> Any:
    status, payload = _call(base, method, path, body)
    assert status < 300, (status, path, payload)
    return payload


def _wait_for(read: Any, predicate: Any, *, timeout: float = 20.0) -> Any:
    deadline = time.monotonic() + timeout
    while True:
        value = read()
        if predicate(value) or time.monotonic() >= deadline:
            assert predicate(value), value
            return value
        time.sleep(0.1)


def _native_done(state_path: Path, spool: Path, *, session_id: str, cwd: Path, story_id: str, words: str) -> None:
    """Emit the native Stop hook that closes one live turn."""
    from holdspeak.agent_context import ingest_agent_hook_event

    ingest_agent_hook_event(
        agent="claude",
        state_path=state_path,
        events_spool_dir=spool,
        payload={
            "session_id": session_id,
            "cwd": str(cwd),
            "story_ref": {"project": PROJECT, "story_id": story_id},
            "hook_event_name": "Stop",
            "last_assistant_message": words,
            "stop_hook_active": False,
        },
    )


def test_real_hub_hand_queue_done_today_and_idempotent_rerun(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two actions use the real Run → hand → queue → Done producer chain."""
    from holdspeak.config import Config
    import holdspeak.config as config_module
    from holdspeak.db import get_database
    from holdspeak import agent_context
    from holdspeak import coder_gate
    from holdspeak.delivery import factory_launch, registry as registry_module
    from holdspeak.delivery import agent_mcp
    from holdspeak import missioncontrol_bridge

    # The fake is a native leaf replay: it imports the real hook receiver and
    # emits its startup turn before it sleeps in tmux.  Give that receiver
    # enough time to register the first working flight before the same Run
    # admission evaluates item two.
    from holdspeak import coder_factory
    monkeypatch.setattr(coder_factory, "START_SETTLE_SECONDS", 2.0)

    home = tmp_path / "home"
    # macOS tmux has a short Unix-socket path limit; keep this private socket
    # root outside pytest's long temporary path while retaining isolation.
    tmux_dir = Path(tempfile.mkdtemp(prefix="hs14-"))
    home.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("TMUX_TMPDIR", str(tmux_dir))
    monkeypatch.setenv("HOLDSPEAK_OWN_AGENTS", "off")
    monkeypatch.setenv("HOLDSPEAK_TEST_NO_REAL_CLI", "1")
    private_config = home / ".config" / "holdspeak" / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", private_config)

    # Production launch paths are real, but every persistent location is in
    # this rig's HOME and the only executable on PATH is a sleeping fake.
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_claude = fake_bin / "claude"
    source_root = Path(__file__).resolve().parents[2]
    fake_claude.write_text(
        f"#!{__import__('sys').executable}\n"
        "import os, sys, time\n"
        f"sys.path.insert(0, {str(source_root)!r})\n"
        "from pathlib import Path\n"
        "from holdspeak.agent_context import ingest_agent_hook_event\n"
        "ref = os.environ.get('HOLDSPEAK_STORY_REF', '')\n"
        "project, _, story_id = ref.replace(':', '/').partition('/')\n"
        "session_id = 'ag14-' + story_id\n"
        "common = {'session_id': session_id, 'cwd': os.getcwd(), 'story_ref': {'project': project, 'story_id': story_id}}\n"
        "for event, fields in [('SessionStart', {'source': 'startup'}), ('UserPromptSubmit', {'prompt': 'the hand brief'}), ('PostToolUse', {'tool_name': 'Bash', 'tool_input': {'command': 'git status'}})]:\n"
        "    ingest_agent_hook_event(agent='claude', state_path=Path(os.environ['AG14_STATE']), events_spool_dir=Path(os.environ['AG14_SPOOL']), payload={**common, 'hook_event_name': event, **fields})\n"
        "time.sleep(600)\n",
        encoding="utf-8",
    )
    fake_claude.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}:{os.environ.get('PATH', '')}")

    map_path = home / ".holdspeak" / "delivery_workbench.json"
    map_path.parent.mkdir(parents=True)
    repo = _make_repo(tmp_path / "source")
    map_path.write_text(json.dumps({"projects": {"Railsproj": str(repo)}}), encoding="utf-8")
    monkeypatch.setattr(missioncontrol_bridge, "DEFAULT_MAP_PATH", map_path)
    monkeypatch.setattr(registry_module, "DEFAULT_REGISTRY_PATH", home / ".holdspeak" / "delivery_sources.json")
    monkeypatch.setattr(factory_launch, "DEFAULT_PROFILES_PATH", home / ".holdspeak" / "agent_profiles.json")
    launches_path = home / ".holdspeak" / "agent_launches.json"
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", launches_path)
    monkeypatch.setattr(factory_launch, "DEFAULT_PROFILES_PATH", home / ".holdspeak" / "agent_profiles.json")
    monkeypatch.setattr(agent_mcp, "mcp_config_dir", lambda: home / ".holdspeak" / "gate-spawn-settings" / "mcp")
    monkeypatch.setattr(coder_gate, "GATE_CONFIG_FILE", home / ".holdspeak" / "gate.json")
    monkeypatch.setattr(agent_context, "AGENT_CONTEXT_FILE", home / ".holdspeak" / "agent_sessions.json")
    spool = home / ".holdspeak" / "agent-events"
    monkeypatch.setenv("AG14_STATE", str(agent_context.AGENT_CONTEXT_FILE))
    monkeypatch.setenv("AG14_SPOOL", str(spool))

    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        # _boot establishes its own private config path. Set the admission
        # limit after that setup so every production reader sees the same
        # isolated value.
        monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
        config = Config.load()
        config.agents.working_at_once = 1
        config.save()
        db = get_database()
        _seed(db)
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO action_items (id, meeting_id, task, owner, status) VALUES (?, ?, ?, ?, ?)",
                ("ai_2", "m1", "Write the on-call note", "Me", "open"),
            )

        made = _ok(base, "POST", "/api/workbenches", {
            "name": "AG14 hand queue",
            "instruction": "Complete each action and report the result.",
            "sources": ["action:ai_1", "action:ai_2"],
            "output_target": "today",
            "do_kind": "hand_to_agent",
            "agent_profile": "claude-default",
            "review_by": "claude",
        })["workbench"]
        workbench_id = made["id"]

        first = _ok(base, "POST", f"/api/workbenches/{workbench_id}/run", {})["run"]
        assert len(first["agents_started"]) == 1, first
        first_launch = first["agents_started"][0]["launch_id"]
        assert len(first["agents_queued"]) == 1, first
        queued = first["agents_queued"][0]
        assert queued["queue_id"], queued

        # Let the native rider bind the first launch. Its startup hook sequence
        # is the real slot-holding event before the runner reaches item two.
        from holdspeak.delivery.factory_launch import LaunchLedger

        ledger = LaunchLedger(launches_path)
        _wait_for(lambda: ledger.get(first_launch), lambda row: bool((row or {}).get("attempt_id")))
        first_worktree = repo.parent / "hs-action-ai_1"
        first_session_id = "ag14-action-ai_1"
        _wait_for(
            lambda: __import__("holdspeak.services.agent_flights", fromlist=["agent_flights"]).agent_flights(db, ledger=ledger),
            lambda rows: bool(rows and rows[0].get("session_key") == f"claude:{first_session_id}" and rows[0].get("state") == "working"),
        )

        second = _ok(base, "POST", f"/api/workbenches/{workbench_id}/run", {})["run"]
        assert second["agents_started"] == [], second
        assert second["agents_queued"] == [], second
        assert len(second["skipped"]) == 2, second

        # A native Done hook releases the real slot. The hub's existing queue
        # heartbeat seam starts the queued item through the same hand service.
        _native_done(
            agent_context.AGENT_CONTEXT_FILE, spool, session_id=first_session_id,
            cwd=first_worktree, story_id="action-ai_1", words="Done — action one is complete.",
        )
        from holdspeak.services import automation_runs
        from holdspeak.services.agent_flights import agent_flights
        from holdspeak.web_server import _start_queued_hands

        _wait_for(lambda: agent_flights(db, ledger=ledger), lambda rows: bool(rows and rows[0].get("state") == "done"))
        _start_queued_hands()
        second_launch = _wait_for(
            lambda: [row for row in ledger.list() if row.get("origin_ref") == {"kind": "action", "id": "ai_2"}],
            lambda rows: bool(rows and rows[0].get("launch_id")),
        )[0]["launch_id"]
        second_worktree = repo.parent / "hs-action-ai_2"
        second_session_id = "ag14-action-ai_2"
        _native_done(
            agent_context.AGENT_CONTEXT_FILE, spool, session_id=second_session_id,
            cwd=second_worktree, story_id="action-ai_2", words="Done — action two is complete.",
        )
        # The native hook has written the Stop to the existing event spool;
        # drain that durable event log before the normal result read.
        from holdspeak.agent_context import event_log
        event_log.drain_spool(db._connection, spool_dir=spool)

        # Existing result reads perform the Done projection, Today read and
        # notification model sync. Two links are durable, one per source item.
        payload = _ok(base, "GET", f"/api/workbenches/{workbench_id}")["workbench"]
        results = payload["results"]
        _wait_for(lambda: _ok(base, "GET", f"/api/workbenches/{workbench_id}")["workbench"]["results"], lambda rows: len([r for r in rows if r["status"] == "done"]) == 2)
        results = _ok(base, "GET", f"/api/workbenches/{workbench_id}")["workbench"]["results"]
        assert len(results) == 2 and {row["text"] for row in results} == {
            "Done — action one is complete.", "Done — action two is complete.",
        }, results
        prepared = _ok(base, "GET", "/api/automations/prepared")
        assert prepared["prepared"]["workbench_id"] == workbench_id
        assert prepared["automation"]["id"] == workbench_id
        with db._connection() as conn:
            artifact_count = conn.execute(
                "SELECT COUNT(*) FROM artifacts WHERE plugin_id='automation_agent_hand' AND source_item_id IS NOT NULL",
            ).fetchone()[0]
            link_count = conn.execute(
                "SELECT COUNT(*) FROM artifact_sources WHERE source_type='workbench_item' AND artifact_id IN (SELECT id FROM artifacts WHERE plugin_id='automation_agent_hand')",
            ).fetchone()[0]
        assert artifact_count == link_count == 2

        rerun = _ok(base, "POST", f"/api/workbenches/{workbench_id}/run", {})["run"]
        assert rerun["agents_started"] == [] and rerun["agents_queued"] == []
        assert len(rerun["skipped"]) == 2, rerun
        assert automation_runs.sync_agent_results(db) == 0
    finally:
        server.stop()
        subprocess.run(
            ["tmux", "kill-server"], env={**os.environ, "HOME": str(home), "TMUX_TMPDIR": str(tmux_dir)},
            capture_output=True, check=False,
        )
        shutil.rmtree(tmux_dir, ignore_errors=True)
