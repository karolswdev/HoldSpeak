"""PHILO-14 C0b on a real hub: a spooled event reaches the event log with no
reader.

The hub is the real ``MeetingWebServer`` (uvicorn on a real port, its
startup tasks running). The launch is live the real way: a ledger row whose
tmux session exists. The test spools one event with the hook's own writer and
reads nothing through the hub: the row must appear within 5 s.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import pytest

pytestmark = [pytest.mark.timeout(120)]


def test_a_spooled_event_reaches_the_event_log_with_no_reader(tmp_path: Path, monkeypatch) -> None:
    if shutil.which("tmux") is None:
        pytest.skip("tmux is not installed: a launch cannot be live")

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.agent_context import event_log
    from holdspeak.db import get_database, reset_database
    from holdspeak.delivery import factory_launch
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    (home / ".holdspeak").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    ledger = home / ".holdspeak" / "agent_launches.json"
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", ledger)

    session = f"hs-c0b-{uuid.uuid4().hex[:8]}"
    subprocess.run(["tmux", "new-session", "-d", "-s", session, "sleep 120"], check=True)
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token="c0b-spool-timer",
    )
    try:
        ledger.write_text(json.dumps({
            "launches_schema": factory_launch.LAUNCHES_SCHEMA,
            "launches": [{"launch_id": "launch-c0b", "state": "launched", "session": session}],
        }), encoding="utf-8")
        server.start()
        key = "claude:c0b-session"
        row = {"event": "PostToolUse", "tool": "Bash", "head": "echo timer", "text": None, "detail": {}}
        assert event_log.spool_event(key, "2026-10-07T00:00:00Z", row)
        spool = event_log.default_spool_dir()
        assert spool == home / ".holdspeak" / "agent-events"

        deadline = time.monotonic() + 5.0
        events: list = []
        while time.monotonic() < deadline:
            with get_database()._connection() as conn:
                events = event_log.list_events(conn, key)
            if events:
                break
            time.sleep(0.2)
        assert [e["head"] for e in events] == ["echo timer"]
        assert not [p for p in spool.iterdir() if p.name.endswith(".json") and not p.name.startswith(".")]
    finally:
        server.stop()
        subprocess.run(["tmux", "kill-session", "-t", session], check=False)
        reset_database()
