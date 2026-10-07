"""PHILO-14 C0b: the agent-event spool drains on a hub timer.

``event_log.SpoolTimer`` is the tick the hub's ``_agent_spool_loop`` runs
every 2 s: it drains while a launch is live, idles (one ledger stat, no live
read, no drain) when none is, shares the reads' lock and per-pass bound, and
logs a failure at most once per minute without raising.
"""
from __future__ import annotations

import fcntl
import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from holdspeak.agent_context import event_log
from holdspeak.db import Database


@pytest.fixture
def db(tmp_path) -> Database:
    database = Database(tmp_path / "hub.db")
    yield database
    database.close()


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class Live:
    def __init__(self, value: bool) -> None:
        self.value = value
        self.calls = 0

    def __call__(self) -> bool:
        self.calls += 1
        return self.value


def _spool(tmp_path: Path, count: int, key: str = "claude:s1") -> Path:
    folder = tmp_path / "agent-events"
    for n in range(count):
        row = {"event": "PostToolUse", "tool": "Bash", "head": f"echo {n}", "text": None, "detail": {}}
        assert event_log.spool_event(key, f"2026-10-07T00:00:{n % 60:02d}Z", row, spool_dir=folder)
    return folder


def _files(folder: Path) -> list[str]:
    return sorted(p.name for p in folder.iterdir() if p.name.endswith(".json") and not p.name.startswith("."))


def _heads(db: Database, key: str = "claude:s1") -> list[str]:
    with db._connection() as conn:
        return [e["head"] for e in event_log.list_events(conn, key, limit=1000)]


def _timer(db, tmp_path, live, clock, *, ledger=None, connection=None) -> event_log.SpoolTimer:
    ledger = ledger or tmp_path / "agent_launches.json"
    return event_log.SpoolTimer(
        connection or db._connection, live=live, ledger_path=lambda: ledger,
        spool_dir=tmp_path / "agent-events", clock=clock,
    )


def test_a_tick_drains_spooled_files_into_the_event_log_while_a_launch_is_live(tmp_path, db) -> None:
    folder = _spool(tmp_path, 3)
    timer = _timer(db, tmp_path, Live(True), Clock())
    assert timer.tick() == 3
    assert _heads(db) == ["echo 0", "echo 1", "echo 2"]   # the spool's order
    assert _files(folder) == []
    assert timer.tick() == 0


def test_with_no_live_launch_a_tick_neither_drains_nor_reads_live_again(tmp_path, db) -> None:
    folder = _spool(tmp_path, 2)
    live = Live(False)
    clock = Clock()
    timer = _timer(db, tmp_path, live, clock)
    for _ in range(50):
        assert timer.tick() == 0
        clock.now += event_log.SpoolTimer.INTERVAL
    assert live.calls == 1          # read once; the ledger did not change
    assert len(_files(folder)) == 2
    assert _heads(db) == []


def test_a_ledger_change_reads_live_again_and_the_drain_starts(tmp_path, db) -> None:
    folder = _spool(tmp_path, 2)
    ledger = tmp_path / "agent_launches.json"
    live = Live(False)
    timer = _timer(db, tmp_path, live, Clock(), ledger=ledger)
    assert timer.tick() == 0
    live.value = True
    ledger.write_text('{"launches_schema": 1, "launches": []}\n', encoding="utf-8")
    assert timer.tick() == 2
    assert live.calls == 2
    assert _files(folder) == []


def test_a_live_launch_is_read_again_every_30_s_so_a_dead_agent_stops_the_drain(tmp_path, db) -> None:
    live = Live(True)
    clock = Clock()
    timer = _timer(db, tmp_path, live, clock)
    timer.tick()
    assert timer.is_live and live.calls == 1
    clock.now += 10
    timer.tick()
    assert live.calls == 1
    live.value = False
    clock.now += event_log.SpoolTimer.LIVE_RECHECK
    timer.tick()
    assert live.calls == 2 and not timer.is_live
    folder = _spool(tmp_path, 1)
    clock.now += 100
    assert timer.tick() == 0 and live.calls == 2
    assert len(_files(folder)) == 1


def test_a_drain_in_progress_is_never_doubled(tmp_path, db) -> None:
    folder = _spool(tmp_path, 3)
    timer = _timer(db, tmp_path, Live(True), Clock())
    # A read's drain holds the shared lock: the timer's pass takes nothing.
    with open(folder / ".drain.lock", "a+") as held:
        fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert timer.tick() == 0
        assert len(_files(folder)) == 3
    assert timer.tick() == 3
    assert _heads(db) == ["echo 0", "echo 1", "echo 2"]


def test_one_pass_takes_at_most_5000_files_and_keeps_the_order(tmp_path, db) -> None:
    total = event_log.DRAIN_MAX_FILES + 3
    folder = _spool(tmp_path, total)
    names = _files(folder)
    timer = _timer(db, tmp_path, Live(True), Clock())
    assert timer.tick() == event_log.DRAIN_MAX_FILES
    assert _files(folder) == names[event_log.DRAIN_MAX_FILES:]   # the oldest went first
    assert timer.tick() == 3
    # The session keeps its newest EVENT_LOG_KEEP rows, in spool order.
    with db._connection() as conn:
        heads = [r[0] for r in conn.execute("SELECT head FROM agent_session_events ORDER BY id")]
    keep = event_log.EVENT_LOG_KEEP
    assert heads == [f"echo {n}" for n in range(total - keep, total)]


def test_a_failed_drain_is_logged_once_per_minute_and_never_raised(tmp_path, db, caplog) -> None:
    folder = _spool(tmp_path, 1)
    clock = Clock()
    broken = MagicMock(side_effect=RuntimeError("disk gone"))
    timer = _timer(db, tmp_path, Live(True), clock, connection=broken)
    with caplog.at_level(logging.WARNING, logger="holdspeak.agent_context.event_log"):
        for _ in range(20):
            assert timer.tick() == 0
            clock.now += event_log.SpoolTimer.INTERVAL   # 40 s in all
        assert len([r for r in caplog.records if "spool not drained" in r.getMessage()]) == 1
        clock.now += event_log.SpoolTimer.ERROR_LOG_EVERY
        timer.tick()
        assert len([r for r in caplog.records if "spool not drained" in r.getMessage()]) == 2
    assert timer.failures == 21
    assert len(_files(folder)) == 1   # the file waits for a drain that works


def test_a_failed_live_read_fails_toward_draining(tmp_path, db) -> None:
    folder = _spool(tmp_path, 2)

    def live() -> bool:
        raise OSError("tmux gone")

    timer = _timer(db, tmp_path, live, Clock())
    assert timer.tick() == 2
    assert _files(folder) == []


def test_the_hub_starts_the_timer_with_the_app_and_stops_it_on_shutdown(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    reset_database()
    get_database(tmp_path / "holdspeak.db")
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}))
    )
    try:
        assert server._agent_spool_task is None
        with TestClient(server.app):
            task = server._agent_spool_task
            assert task is not None and not task.done()
        assert task.done()
    finally:
        reset_database()


# ── Astra r1 on #953: the production liveness path, the tail, the replay ──


class TmuxRunner:
    """tmux as ``LaunchReads.runner`` sees it: ``plan`` is a list of
    ``"alive" | "dead" | "timeout"``, one per probe; the last one repeats."""

    def __init__(self, *plan: str) -> None:
        self.plan = list(plan)
        self.calls = 0

    def __call__(self, argv):
        import subprocess
        from types import SimpleNamespace

        assert argv[:2] == ["tmux", "has-session"]
        step = self.plan[min(self.calls, len(self.plan) - 1)]
        self.calls += 1
        if step == "timeout":
            raise subprocess.TimeoutExpired(argv, 5)
        return SimpleNamespace(returncode=0 if step == "alive" else 1)


@pytest.fixture
def hub_timer(tmp_path):
    """The hub's own timer (``web_server._agent_spool_timer``) on the
    production ``LaunchReads`` (its tmux catch included), a ledger written by
    the production ``LaunchLedger``, a fake clock and a fake tmux."""
    from types import SimpleNamespace

    from holdspeak.db import get_database, reset_database
    from holdspeak.delivery.factory_launch import LaunchLedger
    from holdspeak.services.agent_hand_preview import LaunchReads
    from holdspeak.web_server import _agent_spool_timer

    reset_database()
    database = get_database(tmp_path / "holdspeak.db")
    ledger_path = tmp_path / "agent_launches.json"
    LaunchLedger(ledger_path).record({"launch_id": "launch-1", "state": "launched", "session": "hs-c0b"})

    def build(runner: TmuxRunner):
        reads = LaunchReads(ledger_path=ledger_path, runner=runner)
        timer = _agent_spool_timer(SimpleNamespace(agent_hand_reads=reads), spool_dir=tmp_path / "agent-events")
        clock = Clock()
        timer._clock = clock
        return timer, clock

    yield build, database
    reset_database()


def test_a_probe_that_times_out_is_unknown_never_none_live(tmp_path, hub_timer) -> None:
    build, database = hub_timer
    tmux = TmuxRunner("timeout", "alive")
    timer, clock = build(tmux)
    folder = _spool(tmp_path, 1)
    assert timer.tick() == 1          # unknown: drain this tick
    assert tmux.calls == 1 and timer.failures == 1
    _spool(tmp_path, 1)
    clock.now += event_log.SpoolTimer.LIVE_RECHECK
    assert timer.tick() == 1          # probed again within 30 s, and live
    assert tmux.calls == 2 and timer.is_live
    assert _files(folder) == []


def test_when_the_last_agent_dies_the_recheck_drains_once_more_then_idles(tmp_path, hub_timer) -> None:
    build, database = hub_timer
    tmux = TmuxRunner("alive", "dead")
    timer, clock = build(tmux)
    folder = _spool(tmp_path, 1)
    assert timer.tick() == 1 and timer.is_live
    _spool(tmp_path, 1)                # the agent's last event
    clock.now += event_log.SpoolTimer.LIVE_RECHECK
    assert timer.tick() == 1           # the tail drain
    assert not timer.is_live and _files(folder) == []
    _spool(tmp_path, 1)
    for _ in range(50):
        clock.now += event_log.SpoolTimer.LIVE_RECHECK
        assert timer.tick() == 0       # idle: no probe, no drain
    assert tmux.calls == 2


def test_a_committed_file_whose_unlink_failed_is_never_replayed(tmp_path, db, monkeypatch) -> None:
    folder = _spool(tmp_path, 10)
    real_unlink = event_log.os.unlink

    def failing(path, *a, **k):
        if str(path).endswith(".json"):
            raise PermissionError("unlink refused")
        return real_unlink(path, *a, **k)

    monkeypatch.setattr(event_log.os, "unlink", failing)
    assert event_log.drain_spool(db._connection, spool_dir=folder, keep=4) == 10
    assert len(_files(folder)) == 10
    monkeypatch.setattr(event_log.os, "unlink", real_unlink)
    event_log.drain_spool(db._connection, spool_dir=folder, keep=4)   # the retry
    with db._connection() as conn:
        heads = [r[0] for r in conn.execute("SELECT head FROM agent_session_events ORDER BY id")]
    assert heads == ["echo 6", "echo 7", "echo 8", "echo 9"]   # the newest kept, once each
    assert _files(folder) == []
    _spool(tmp_path, 1)
    assert event_log.drain_spool(db._connection, spool_dir=folder, keep=4) == 1
