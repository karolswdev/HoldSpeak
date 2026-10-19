"""Betterment AG9: a finished agent notifies quietly, once, never while its
own window is in front; Done stays out of Needs you."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from holdspeak.db import Database

NOON = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def heartbeat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import holdspeak.delivery.factory_launch as factory_launch
    from holdspeak.services.heartbeat_service import HeartbeatService

    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", tmp_path / "agent_launches.json")
    db = Database(tmp_path / "hub.db")
    hb = HeartbeatService(db, clock=lambda: NOON, local_zone=timezone.utc)
    hb.update_settings({"notify": "edge", "quiet_hours": {"start": 22, "end": 8}})
    return hb, db, tmp_path


def _notices(tmp_path: Path) -> list[dict]:
    path = tmp_path / "agent_done_notices.json"
    return json.loads(path.read_text()) if path.exists() else []


def _done(hb, sent: list):
    return hb.notify_agent_done(launch_id="l1", agent="claude", title="Draft test scaffolding",
                                turn_id="t1", _notifier=lambda t, b, click_url=None: sent.append((t, b)) or True,
                                now=NOON)


def test_a_finished_agent_raises_one_quiet_notice(heartbeat) -> None:
    hb, _db, tmp = heartbeat
    sent: list = []
    assert _done(hb, sent)["outcome"] == "sent"
    assert sent == [("Agent finished", "Claude Code finished Draft test scaffolding")]
    assert [n["outcome"] for n in _notices(tmp)] == ["sent"]


def test_no_notice_while_notify_is_off_or_in_quiet_hours(heartbeat) -> None:
    hb, _db, tmp = heartbeat
    sent: list = []
    hb.update_settings({"notify": "off"})
    assert _done(hb, sent)["outcome"] == "off"
    hb.update_settings({"notify": "edge", "quiet_hours": {"start": 11, "end": 13}})
    assert _done(hb, sent)["outcome"] == "held_quiet_hours"
    assert sent == []


def test_no_notice_for_the_agent_whose_window_is_in_front(heartbeat) -> None:
    hb, db, _tmp = heartbeat
    from holdspeak.services.desk_window_service import DeskWindowService

    windows = DeskWindowService(db, on_changed=lambda *_a: None)
    windows.open("lane", object_ref="launch:l1")
    sent: list = []
    assert _done(hb, sent)["outcome"] == "held_in_front"
    windows.open("conductor")   # another window in front: the notice goes
    assert _done(hb, sent)["outcome"] == "sent"


def test_the_watcher_notifies_each_new_done_turn_once_and_never_on_start(monkeypatch) -> None:
    import holdspeak.web_server as ws
    from holdspeak.services import agent_flights, heartbeat_service

    flights = [{"launch_id": "l1", "turn_id": "t1", "state": "done", "new": True, "agent": "claude", "title": "A"}]
    monkeypatch.setattr(agent_flights, "agent_flights", lambda db: list(flights))
    monkeypatch.setattr("holdspeak.db.get_database", lambda: object())
    calls: list = []
    monkeypatch.setattr(heartbeat_service.HeartbeatService, "__init__", lambda self, db, observer=None: None)
    monkeypatch.setattr(heartbeat_service.HeartbeatService, "notify_agent_done",
                        lambda self, **kw: calls.append(kw) or {"outcome": "sent"})
    monkeypatch.setattr(ws, "_DONE_SEEN", None)
    assert ws._agent_done_step() == []          # the first read is the baseline
    flights.append({"launch_id": "l2", "turn_id": "t9", "state": "done", "new": True, "agent": "codex", "title": "B"})
    assert ws._agent_done_step() == ["l2"]
    assert ws._agent_done_step() == []          # once
    assert [c["launch_id"] for c in calls] == ["l2"]
