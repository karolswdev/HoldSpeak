"""CAD-1-04 — the scheduler: quiet hours, snooze, repeat window, daily cap, pressure."""
from __future__ import annotations

from datetime import datetime

from holdspeak.cadence.models import OpenLoop
from holdspeak.cadence.scheduler import SchedulerConfig, due_loops, in_quiet_hours


def _loop(score=10.0, **kw) -> OpenLoop:
    loop = OpenLoop(source_type="meeting_action", source_id=kw.pop("sid", "x"),
                    title=kw.pop("title", "t"), stale_score=score, **kw)
    return loop


DAYTIME = datetime(2026, 6, 28, 10, 0, 0)
NIGHT = datetime(2026, 6, 28, 23, 0, 0)
CFG = SchedulerConfig(quiet_hours_start=22, quiet_hours_end=8, max_nudges_per_day=12)


def test_quiet_hours_wraps_midnight():
    assert in_quiet_hours(NIGHT, 22, 8)
    assert in_quiet_hours(datetime(2026, 6, 28, 3, 0), 22, 8)
    assert not in_quiet_hours(DAYTIME, 22, 8)


def test_no_nudges_during_quiet_hours():
    assert due_loops([_loop()], now=NIGHT, config=CFG) == []


def test_daytime_loop_is_due():
    due = due_loops([_loop()], now=DAYTIME, config=CFG)
    assert len(due) == 1


def test_needs_review_never_due():
    assert due_loops([_loop(needs_review=True)], now=DAYTIME, config=CFG) == []


def test_snoozed_loop_suppressed_until_due():
    snoozed = _loop(status="snoozed", snoozed_until="2999-01-01T00:00:00")
    assert due_loops([snoozed], now=DAYTIME, config=CFG) == []
    past = _loop(status="snoozed", snoozed_until="2000-01-01T00:00:00")
    assert len(due_loops([past], now=DAYTIME, config=CFG)) == 1


def test_repeat_window_suppresses_recently_nudged():
    recent = _loop(last_nudged_at="2026-06-28T09:00:00")  # 1h ago, < 4h window
    assert due_loops([recent], now=DAYTIME, config=CFG) == []
    old = _loop(last_nudged_at="2026-06-28T00:00:00")  # 10h ago
    assert len(due_loops([old], now=DAYTIME, config=CFG)) == 1


def test_daily_cap_limits_and_orders_by_score():
    loops = [_loop(score=s, sid=f"s{s}") for s in (1, 9, 5, 7)]
    cfg = SchedulerConfig(max_nudges_per_day=2)
    due = due_loops(loops, now=DAYTIME, config=cfg, nudged_today=0)
    assert [l.stale_score for l in due] == [9, 7]  # top 2, highest first
    assert due_loops(loops, now=DAYTIME, config=cfg, nudged_today=2) == []  # cap reached


def test_pressure_changes_repeat_window():
    nudged = _loop(last_nudged_at="2026-06-28T07:30:00")  # 2.5h ago
    gentle = SchedulerConfig(pressure="gentle")     # 8h window -> suppressed
    aggressive = SchedulerConfig(pressure="aggressive")  # 2h window -> eligible
    assert due_loops([nudged], now=DAYTIME, config=gentle) == []
    assert len(due_loops([nudged], now=DAYTIME, config=aggressive)) == 1
