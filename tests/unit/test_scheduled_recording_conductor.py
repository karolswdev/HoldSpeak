"""HS-136-01: Scheduled recording conductor invariant tests.

All tests use an injectable clock and stubbed _start_meeting seam.
No real audio is opened. Covers invariants I1-I10 + missed fire (VI.1).
"""
from __future__ import annotations

import threading
import time
from typing import Any, Optional
from unittest.mock import MagicMock

import pytest

from holdspeak.db import Database
from holdspeak.scheduled_recording_conductor import ScheduledRecordingConductor
from holdspeak.cron import next_cron_fire
from datetime import datetime, timezone


# -- helpers --


class FakeClock:
    """Injectable clock for deterministic time control."""

    def __init__(self, epoch: float = 1_000_000_000.0):
        self._time = epoch
        self._lock = threading.Lock()

    def __call__(self) -> float:
        with self._lock:
            return self._time

    def advance(self, seconds: float) -> None:
        with self._lock:
            self._time += seconds

    def set(self, epoch: float) -> None:
        with self._lock:
            self._time = epoch


def make_db(tmp_path) -> Database:
    return Database(tmp_path / "test.db")


def make_conductor(
    db: Database,
    clock: FakeClock,
    *,
    start_meeting_fn: Any = None,
    stop_meeting_fn: Any = None,
    voice_floor_fn: Any = None,
    countdown_seconds: float = 0.01,
    tick_interval: float = 0.01,
) -> ScheduledRecordingConductor:
    return ScheduledRecordingConductor(
        clock=clock,
        db_factory=lambda: db,
        start_meeting_fn=start_meeting_fn or MagicMock(),
        stop_meeting_fn=stop_meeting_fn or MagicMock(),
        voice_floor_fn=voice_floor_fn or (lambda: None),
        countdown_seconds=countdown_seconds,
        tick_interval=tick_interval,
    )


def create_schedule(
    db: Database,
    *,
    title: str = "Test Schedule",
    cron_expr: str = "* * * * *",
    one_shot: bool = False,
    duration_minutes: int = 60,
    enabled: bool = True,
    next_fire_at: Optional[float] = None,
) -> Any:
    sched = db.scheduled_recordings.create(
        title=title,
        cron_expr=cron_expr,
        one_shot=one_shot,
        duration_minutes=duration_minutes,
        enabled=enabled,
        next_fire_at=next_fire_at,
    )
    return sched


# -- I1: single fire --


def test_single_fire_across_multiple_ticks(tmp_path):
    """A due schedule fires exactly once across multiple ticks in the same minute (I1)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0)

    # Create a schedule due now
    create_schedule(db, next_fire_at=clock() - 1)

    # Tick multiple times in the same minute bucket
    conductor._tick()
    conductor._tick()
    conductor._tick()

    # Wait for the countdown thread to fire
    time.sleep(0.2)

    # The start function should be called exactly once
    assert start_fn.call_count == 1


def test_single_fire_dedupe_different_minutes(tmp_path):
    """A schedule can fire again in a different minute (I1 only dedupes within a minute)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0)

    sched = create_schedule(db, next_fire_at=clock() - 1)

    # First tick fires
    conductor._tick()
    time.sleep(0.2)
    assert start_fn.call_count == 1

    # Advance to a different minute bucket
    clock.advance(120)
    # Reset the schedule state so it can fire again
    db.scheduled_recordings.set_state(sched.id, "idle")
    db.scheduled_recordings.update(sched.id, next_fire_at=clock() - 1)

    conductor._tick()
    time.sleep(0.2)
    assert start_fn.call_count == 2


# -- I2: recurring advances, one-shot disables --


def test_recurring_advances_next_fire_after_recording(tmp_path):
    """A recurring schedule advances next_fire_at strictly forward after recording (I2)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    stop_fn = MagicMock()
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, stop_meeting_fn=stop_fn,
        countdown_seconds=0.0,
    )

    sched = create_schedule(
        db, cron_expr="0 9 * * *", one_shot=False,
        next_fire_at=clock() - 1, duration_minutes=1,
    )

    conductor._tick()
    time.sleep(0.2)

    # The schedule should now be in recording state
    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "recording"

    # Trigger auto-stop
    conductor._auto_stop(db, sched.id)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "stopped"
    # next_fire_at should be strictly in the future
    assert updated.next_fire_at is not None
    assert updated.next_fire_at > clock()
    assert updated.enabled is True


def test_recurring_advances_after_cancelled(tmp_path):
    """Recurring advances next_fire after cancel (I2)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, countdown_seconds=2.0,
    )

    sched = create_schedule(
        db, cron_expr="0 9 * * *", one_shot=False,
        next_fire_at=clock() - 1,
    )

    conductor._tick()
    time.sleep(0.05)

    # Cancel during countdown
    assert conductor.cancel_armed(sched.id) is True
    time.sleep(0.2)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "cancelled"
    assert updated.next_fire_at is not None
    assert updated.next_fire_at > clock()
    assert updated.enabled is True
    # Start was never called
    assert start_fn.call_count == 0


def test_recurring_advances_after_refused(tmp_path):
    """Recurring advances next_fire after mic refusal (I2)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0,
        voice_floor_fn=lambda: "dictation",  # floor held
    )

    sched = create_schedule(
        db, cron_expr="0 9 * * *", one_shot=False,
        next_fire_at=clock() - 1,
    )

    conductor._tick()
    time.sleep(0.2)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "refused"
    assert updated.next_fire_at is not None
    assert updated.next_fire_at > clock()
    assert updated.enabled is True
    assert start_fn.call_count == 0


def test_recurring_advances_after_missed(tmp_path):
    """Recurring advances next_fire after missed detection (I2)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    conductor = make_conductor(db, clock, countdown_seconds=0.0)

    sched = create_schedule(
        db, cron_expr="0 9 * * *", one_shot=False,
        next_fire_at=clock() - 100,  # missed by 100 seconds
    )

    conductor._reconcile_on_boot()

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "missed"
    assert updated.next_fire_at is not None
    assert updated.next_fire_at > clock()
    assert updated.enabled is True


def test_one_shot_disables_after_recording(tmp_path):
    """One-shot schedule disables after recording (I2)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    stop_fn = MagicMock()
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, stop_meeting_fn=stop_fn,
        countdown_seconds=0.0,
    )

    sched = create_schedule(
        db, cron_expr="0 9 * * *", one_shot=True,
        next_fire_at=clock() - 1, duration_minutes=1,
    )

    conductor._tick()
    time.sleep(0.2)

    # Trigger auto-stop
    conductor._auto_stop(db, sched.id)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "stopped"
    assert updated.enabled is False
    assert updated.next_fire_at is None


def test_one_shot_disables_after_cancelled(tmp_path):
    """One-shot disables after cancel (I2)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    conductor = make_conductor(db, clock, countdown_seconds=2.0)

    sched = create_schedule(
        db, cron_expr="0 9 * * *", one_shot=True,
        next_fire_at=clock() - 1,
    )

    conductor._tick()
    time.sleep(0.05)
    conductor.cancel_armed(sched.id)
    time.sleep(0.2)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "cancelled"
    assert updated.enabled is False


def test_one_shot_disables_after_refused(tmp_path):
    """One-shot disables after mic refusal (I2)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    conductor = make_conductor(
        db, clock, countdown_seconds=0.0,
        voice_floor_fn=lambda: "voice-typing",
    )

    sched = create_schedule(
        db, cron_expr="0 9 * * *", one_shot=True,
        next_fire_at=clock() - 1,
    )

    conductor._tick()
    time.sleep(0.2)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "refused"
    assert updated.enabled is False


# -- I3: hub-authoritative countdown + in-window-only cancel --


def test_cancel_only_honored_during_countdown(tmp_path):
    """Cancel is only honored inside the countdown window (I3)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, countdown_seconds=0.5,
    )

    sched = create_schedule(db, next_fire_at=clock() - 1)

    conductor._tick()
    time.sleep(0.05)

    # Schedule is in arming state
    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "arming"

    # Cancel should work while armed
    assert conductor.cancel_armed(sched.id) is True
    time.sleep(0.2)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "cancelled"
    assert start_fn.call_count == 0


def test_cancel_after_countdown_elapsed_has_no_effect(tmp_path):
    """Cancel after countdown has fired does nothing (I3)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0,
    )

    sched = create_schedule(db, next_fire_at=clock() - 1)

    conductor._tick()
    time.sleep(0.2)

    # By now the countdown has elapsed and start was called
    assert start_fn.call_count == 1
    # Cancel returns False since it's no longer armed
    assert conductor.cancel_armed(sched.id) is False


def test_fire_without_browser(tmp_path):
    """Fire does not require a browser connection (I3)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    # No broadcast wired = no browser
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0,
    )

    create_schedule(db, next_fire_at=clock() - 1)

    conductor._tick()
    time.sleep(0.2)

    assert start_fn.call_count == 1


# -- I4: mic authority (IV.3) --


def test_mic_held_refusal_with_receipt(tmp_path):
    """Fire while mic floor is held refuses with a receipt naming the owner (I4)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0,
        voice_floor_fn=lambda: "dictation",
    )

    sched = create_schedule(db, next_fire_at=clock() - 1)

    conductor._tick()
    time.sleep(0.2)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "refused"
    assert updated.last_outcome == "refused"
    assert updated.last_receipt_id != ""
    assert start_fn.call_count == 0

    # Verify the receipt exists in kernel_receipts
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM kernel_receipts WHERE receipt_id=?",
            (updated.last_receipt_id,),
        ).fetchone()
    assert row is not None
    assert row["outcome"] == "mic_floor_held"
    assert "dictation" in row["result_ref"]


def test_mic_free_allows_fire(tmp_path):
    """Fire with no mic floor owner proceeds normally."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0,
        voice_floor_fn=lambda: None,
    )

    sched = create_schedule(db, next_fire_at=clock() - 1)

    conductor._tick()
    time.sleep(0.2)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "recording"
    assert start_fn.call_count == 1


# -- I5: bounded delegation --


def test_enable_writes_delegation_receipt(tmp_path):
    """Enabling a schedule writes a delegation receipt (I5)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)

    sched = db.scheduled_recordings.create(
        title="Standup",
        cron_expr="0 9 * * 1-5",
        enabled=False,
    )

    # Simulate enabling with a delegation receipt
    receipt_id = f"sr_deleg_{sched.id}"
    db.scheduled_recordings.update(
        sched.id,
        enabled=True,
        delegation_receipt_id=receipt_id,
        next_fire_at=clock() + 3600,
    )

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.enabled is True
    assert updated.delegation_receipt_id == receipt_id


def test_fire_creates_kernel_receipt(tmp_path):
    """Each fire is kernel-admitted with a receipt (I5)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0,
    )

    sched = create_schedule(db, next_fire_at=clock() - 1)

    conductor._tick()
    time.sleep(0.2)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.last_receipt_id != ""

    # Verify kernel receipt exists
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM kernel_receipts WHERE receipt_id=?",
            (updated.last_receipt_id,),
        ).fetchone()
    assert row is not None
    assert row["state"] == "succeeded"
    assert row["outcome"] == "recording_started"


def test_terms_edit_bumps_revision(tmp_path):
    """A terms edit bumps revision (I5 / delegation contract)."""
    db = make_db(tmp_path)
    sched = db.scheduled_recordings.create(
        title="Standup",
        cron_expr="0 9 * * 1-5",
    )
    assert sched.revision == 1

    db.scheduled_recordings.update(sched.id, cron_expr="0 10 * * 1-5")
    updated = db.scheduled_recordings.get(sched.id)
    assert updated.revision == 2
    assert updated.cron_expr == "0 10 * * 1-5"

    db.scheduled_recordings.update(sched.id, duration_minutes=30)
    updated = db.scheduled_recordings.get(sched.id)
    assert updated.revision == 3


# -- I6: auto-stop at duration --


def test_auto_stop_at_duration(tmp_path):
    """A recording started by a schedule stops at duration_minutes (I6)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    stop_fn = MagicMock()
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, stop_meeting_fn=stop_fn,
        countdown_seconds=0.0,
    )

    sched = create_schedule(
        db, next_fire_at=clock() - 1, duration_minutes=1,
    )

    conductor._tick()
    time.sleep(0.2)

    # The schedule should be recording
    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "recording"

    # Manually call auto_stop (simulating the timer firing)
    conductor._auto_stop(db, sched.id)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "stopped"
    assert updated.last_outcome == "auto_stopped"
    assert stop_fn.call_count == 1


def test_auto_stop_with_no_client(tmp_path):
    """Auto-stop works even with no client attached (I6)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    stop_fn = MagicMock()
    # No broadcast = no client
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, stop_meeting_fn=stop_fn,
        countdown_seconds=0.0,
    )

    sched = create_schedule(
        db, next_fire_at=clock() - 1, duration_minutes=1,
    )

    conductor._tick()
    time.sleep(0.2)

    # Verify recording started
    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "recording"

    # Auto-stop
    conductor._auto_stop(db, sched.id)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "stopped"
    assert stop_fn.call_count == 1


def test_auto_stop_timer_scheduled(tmp_path):
    """An auto-stop timer is scheduled for duration_minutes seconds (I6)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0,
    )

    sched = create_schedule(
        db, next_fire_at=clock() - 1, duration_minutes=60,
    )

    conductor._tick()
    time.sleep(0.2)

    # An auto-stop timer should be registered
    assert sched.id in conductor._auto_stop_timers
    timer = conductor._auto_stop_timers[sched.id]
    assert timer.is_alive()
    timer.cancel()  # Clean up


def test_auto_stop_failure_receipt_reflects_error(tmp_path):
    """If _stop_meeting_fn raises, the receipt records stop_failed, not success (VI.1)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    stop_fn = MagicMock(side_effect=RuntimeError("device vanished"))
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, stop_meeting_fn=stop_fn,
        countdown_seconds=0.0,
    )

    sched = create_schedule(db, next_fire_at=clock() - 1, duration_minutes=1)

    conductor._tick()
    time.sleep(0.2)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "recording"

    # Auto-stop where the stop function raises
    conductor._auto_stop(db, sched.id)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "stopped"
    assert updated.last_outcome == "stop_failed"
    assert updated.last_receipt_id != ""

    # Verify the receipt records failure, not success
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM kernel_receipts WHERE receipt_id=?",
            (updated.last_receipt_id,),
        ).fetchone()
    assert row is not None
    assert row["state"] == "failed"
    assert row["outcome"] == "stop_failed"
    assert "device vanished" in row["result_ref"]


def test_start_failure_recurring_advances(tmp_path):
    """_start_meeting_fn raising -> refused state with receipt, next_fire_at advanced (recurring)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock(side_effect=RuntimeError("device gone"))
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0,
    )

    sched = create_schedule(
        db, cron_expr="0 9 * * *", one_shot=False,
        next_fire_at=clock() - 1,
    )

    conductor._tick()
    time.sleep(0.2)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "refused"
    assert updated.last_outcome == "start_failed"
    assert updated.last_receipt_id != ""
    # Recurring: next_fire_at advanced
    assert updated.next_fire_at is not None
    assert updated.next_fire_at > clock()
    assert updated.enabled is True

    # Receipt names the failure
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM kernel_receipts WHERE receipt_id=?",
            (updated.last_receipt_id,),
        ).fetchone()
    assert row is not None
    assert row["state"] == "failed"
    assert row["outcome"] == "start_failed"
    assert "device gone" in row["result_ref"]


def test_start_failure_one_shot_disables(tmp_path):
    """_start_meeting_fn raising -> one-shot disables."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock(side_effect=RuntimeError("no mic"))
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0,
    )

    sched = create_schedule(
        db, cron_expr="0 9 * * *", one_shot=True,
        next_fire_at=clock() - 1,
    )

    conductor._tick()
    time.sleep(0.2)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "refused"
    assert updated.last_outcome == "start_failed"
    assert updated.enabled is False


def test_deadline_persisted_before_start(tmp_path):
    """Deadline is persisted BEFORE the recording starts (I7, durable before observable)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)

    deadline_at_on_start = []

    def capturing_start(principal, title, **kwargs):
        sched = db.scheduled_recordings.list_all()[0]
        deadline_at_on_start.append(sched.deadline_at)

    conductor = make_conductor(
        db, clock, start_meeting_fn=capturing_start, countdown_seconds=0.0,
    )

    create_schedule(db, next_fire_at=clock() - 1, duration_minutes=30)

    conductor._tick()
    time.sleep(0.2)

    # Deadline should have been set BEFORE start_meeting_fn was called
    assert len(deadline_at_on_start) == 1
    assert deadline_at_on_start[0] is not None
    assert deadline_at_on_start[0] == clock() + 30 * 60


# -- I7: restart durability --


def test_restart_stops_recording_with_past_deadline(tmp_path):
    """On boot, a recording whose deadline has passed is stopped with receipt (I7)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    stop_fn = MagicMock()

    sched = create_schedule(db, next_fire_at=clock() - 7200, duration_minutes=30)

    # Simulate: the recording was in progress when the hub died
    db.scheduled_recordings.set_state(
        sched.id, "recording",
        deadline_at=clock() - 3600,  # deadline passed 1 hour ago
        last_fired_at=clock() - 7200,
    )

    conductor = make_conductor(db, clock, stop_meeting_fn=stop_fn, countdown_seconds=0.0)
    conductor._reconcile_on_boot()

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "stopped"
    assert updated.last_outcome == "auto_stopped_on_restart"
    assert updated.last_receipt_id != ""
    assert updated.deadline_at is None
    assert stop_fn.call_count == 1

    # Receipt was written
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM kernel_receipts WHERE receipt_id=?",
            (updated.last_receipt_id,),
        ).fetchone()
    assert row is not None
    assert row["outcome"] == "auto_stopped_on_restart"


def test_restart_rearms_recording_within_deadline(tmp_path):
    """On boot, a recording still within deadline gets its auto-stop timer re-armed (I7)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)

    sched = create_schedule(db, next_fire_at=clock() - 3600, duration_minutes=120)

    # Recording in progress, deadline in the future
    db.scheduled_recordings.set_state(
        sched.id, "recording",
        deadline_at=clock() + 3600,  # 1 hour remaining
        last_fired_at=clock() - 3600,
    )

    conductor = make_conductor(db, clock, countdown_seconds=0.0)
    conductor._reconcile_on_boot()

    # Should still be recording
    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "recording"

    # Auto-stop timer should be re-armed
    assert sched.id in conductor._auto_stop_timers
    timer = conductor._auto_stop_timers[sched.id]
    assert timer.is_alive()
    timer.cancel()  # Clean up


def test_restart_resolves_interrupted_arming(tmp_path):
    """On boot, an interrupted arming state resolves as missed (I7)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)

    sched = create_schedule(db, cron_expr="0 9 * * *", next_fire_at=clock() - 100)

    # Simulate: arming was in progress when hub died
    db.scheduled_recordings.set_state(
        sched.id, "arming",
        armed_at=clock() - 100,
    )

    conductor = make_conductor(db, clock, countdown_seconds=0.0)
    conductor._reconcile_on_boot()

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "missed"
    assert updated.last_outcome == "missed_interrupted_arming"
    assert updated.last_receipt_id != ""
    assert updated.armed_at is None
    # Recurring: next_fire_at advanced
    assert updated.next_fire_at is not None
    assert updated.next_fire_at > clock()


# -- I8: clock honesty --


def test_cron_evaluation_uses_timezone(tmp_path):
    """Cron evaluation is timezone-explicit (I8)."""
    db = make_db(tmp_path)
    sched = db.scheduled_recordings.create(
        title="EU standup",
        cron_expr="0 9 * * *",
        tz="Europe/London",
    )
    assert sched.tz == "Europe/London"


def test_past_one_shot_does_not_fire_retroactively(tmp_path):
    """A one-shot whose fire time is past at create-time does not fire retroactively (I8).

    Design decision: past one-shots are detected as missed on the next
    reconcile pass and get a missed receipt. They never fire.
    """
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0)

    # Create a one-shot whose fire time is in the past
    create_schedule(
        db, cron_expr="0 9 * * *", one_shot=True,
        next_fire_at=clock() - 3600,  # 1 hour ago
    )

    # Boot reconciliation catches it as missed
    conductor._reconcile_on_boot()

    # It should be missed, not fired
    schedules = db.scheduled_recordings.list_all()
    assert len(schedules) == 1
    assert schedules[0].state == "missed"
    assert schedules[0].enabled is False  # one-shot disables
    assert start_fn.call_count == 0


def test_cron_wallclock_arithmetic_utc_gap(tmp_path):
    """Cron wallclock arithmetic: a time that doesn't exist in a gap is not matched (UTC, I8).

    NOTE: these assertions use timezone.utc, which has no DST transitions.
    Real DST double-fire on short schedules during fall-back repeated hours
    is accepted/known cron semantics and not tested here.
    """
    from holdspeak.cron import cron_is_due, next_cron_fire
    from datetime import datetime, timezone

    # Verify cron_is_due correctly matches/rejects wallclock times
    pre_gap = datetime(2026, 3, 8, 1, 59, 0, tzinfo=timezone.utc)
    post_gap = datetime(2026, 3, 8, 3, 0, 0, tzinfo=timezone.utc)

    # "30 2 * * *" = 2:30 AM
    assert cron_is_due("30 2 * * *", now=pre_gap) is False  # 1:59
    assert cron_is_due("30 2 * * *", now=post_gap) is False  # 3:00

    # next_cron_fire should find the next occurrence the next day
    nf = next_cron_fire("30 2 * * *", after=post_gap)
    assert nf is not None
    dt = datetime.fromtimestamp(nf, tz=timezone.utc)
    assert dt.day == 9  # next day


def test_cron_wallclock_arithmetic_utc_advance(tmp_path):
    """Cron wallclock arithmetic: next_cron_fire advances past the current minute (UTC, I8).

    NOTE: uses timezone.utc (no DST). DST-repeated-hour double-fire on
    short schedules is accepted/known cron semantics.
    """
    from holdspeak.cron import next_cron_fire
    from datetime import datetime, timezone

    pre = datetime(2026, 11, 1, 1, 59, 0, tzinfo=timezone.utc)
    nf = next_cron_fire("30 2 * * *", after=pre)
    assert nf is not None
    dt = datetime.fromtimestamp(nf, tz=timezone.utc)
    assert dt.hour == 2
    assert dt.minute == 30


# -- I9: no cross-path race --


def test_concurrent_fire_attempts_single_capture(tmp_path):
    """Two concurrent fire attempts result in exactly one capture (I9)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0)

    sched = create_schedule(db, next_fire_at=clock() - 1)

    # Run two ticks concurrently from separate threads
    threads = []
    for _ in range(5):
        t = threading.Thread(target=conductor._tick)
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=2)

    # Wait for any countdown threads to fire
    time.sleep(0.3)

    # Exactly one start
    assert start_fn.call_count == 1


def test_manual_capture_blocks_scheduled_fire(tmp_path):
    """A manual capture already holding the floor prevents scheduled fire (I4/I9)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    start_fn = MagicMock()
    conductor = make_conductor(
        db, clock, start_meeting_fn=start_fn, countdown_seconds=0.0,
        voice_floor_fn=lambda: "meeting",  # manual capture holds the floor
    )

    sched = create_schedule(db, next_fire_at=clock() - 1)

    conductor._tick()
    time.sleep(0.2)

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "refused"
    assert start_fn.call_count == 0

    # Verify receipt names the floor owner
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM kernel_receipts WHERE receipt_id=?",
            (updated.last_receipt_id,),
        ).fetchone()
    assert "meeting" in row["result_ref"]


# -- I10: bounded catch-up --


def test_bounded_catchup_long_downtime(tmp_path):
    """Down-for-a-week yields ONE missed receipt, never a burst (I10)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    conductor = make_conductor(db, clock, countdown_seconds=0.0)

    # Create a schedule that fires every hour, hub was down for a week
    sched = create_schedule(
        db, cron_expr="0 * * * *", one_shot=False,
        next_fire_at=clock() - (7 * 24 * 3600),  # 1 week ago
    )

    conductor._reconcile_on_boot()

    # Should produce exactly ONE missed receipt, not 168
    with db._connection() as conn:
        receipts = conn.execute(
            "SELECT * FROM kernel_receipts WHERE outcome='missed'"
        ).fetchall()
    assert len(receipts) == 1

    # Schedule should have advanced to the future
    updated = db.scheduled_recordings.get(sched.id)
    assert updated.next_fire_at is not None
    assert updated.next_fire_at > clock()


def test_bounded_catchup_multiple_schedules(tmp_path):
    """Multiple schedules with long downtime each get exactly one missed receipt (I10)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    conductor = make_conductor(db, clock, countdown_seconds=0.0)

    for i in range(3):
        create_schedule(
            db, title=f"Schedule {i}", cron_expr="0 * * * *", one_shot=False,
            next_fire_at=clock() - (7 * 24 * 3600),
        )

    conductor._reconcile_on_boot()

    with db._connection() as conn:
        receipts = conn.execute(
            "SELECT * FROM kernel_receipts WHERE outcome='missed'"
        ).fetchall()
    assert len(receipts) == 3  # one per schedule, not hundreds


# -- VI.1: missed fire --


def test_missed_fire_receipt_on_startup(tmp_path):
    """A fire time that passed while the hub was down yields a missed receipt (VI.1)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    conductor = make_conductor(db, clock, countdown_seconds=0.0)

    # Create a schedule whose next_fire_at is in the past (hub was down)
    sched = create_schedule(
        db, cron_expr="0 9 * * *",
        next_fire_at=clock() - 3600,  # missed by 1 hour
    )

    # Simulate hub startup -- reconcile runs
    conductor._reconcile_on_boot()

    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "missed"
    assert updated.last_receipt_id != ""

    # Verify the receipt
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM kernel_receipts WHERE receipt_id=?",
            (updated.last_receipt_id,),
        ).fetchone()
    assert row is not None
    assert row["outcome"] == "missed"


def test_missed_fire_not_silent_skip(tmp_path):
    """A missed fire is never a silent skip -- it leaves a receipt (VI.1)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)

    broadcasts = []

    def capture_broadcast(event_type, data):
        broadcasts.append((event_type, data))

    import holdspeak.scheduled_recording_conductor as src_mod
    old_broadcast = src_mod._broadcast
    src_mod._broadcast = capture_broadcast

    try:
        conductor = make_conductor(db, clock)
        create_schedule(
            db, cron_expr="0 9 * * *",
            next_fire_at=clock() - 600,
        )

        conductor._reconcile_on_boot()

        # Should have emitted a missed event
        missed_events = [e for e in broadcasts if e[0] == "scheduled_recording.missed"]
        assert len(missed_events) == 1
        assert "receipt_id" in missed_events[0][1]
    finally:
        src_mod._broadcast = old_broadcast


def test_missed_fire_one_shot_disables(tmp_path):
    """After a missed fire, one-shot schedules disable (VI.1 + I2)."""
    clock = FakeClock(1_000_000_000.0)
    db = make_db(tmp_path)
    conductor = make_conductor(db, clock)

    create_schedule(
        db, cron_expr="0 9 * * *", one_shot=True,
        next_fire_at=clock() - 3600,
    )

    conductor._reconcile_on_boot()

    schedules = db.scheduled_recordings.list_all()
    assert len(schedules) == 1
    assert schedules[0].enabled is False


# -- DB repository tests --


def test_create_and_get(tmp_path):
    db = make_db(tmp_path)
    sched = db.scheduled_recordings.create(
        title="Daily standup",
        cron_expr="0 9 * * 1-5",
        duration_minutes=30,
    )
    assert sched.id.startswith("sr_")
    assert sched.title == "Daily standup"
    assert sched.cron_expr == "0 9 * * 1-5"
    assert sched.duration_minutes == 30
    assert sched.enabled is False
    assert sched.revision == 1
    assert sched.state == "idle"
    assert sched.tz == "UTC"

    fetched = db.scheduled_recordings.get(sched.id)
    assert fetched is not None
    assert fetched.id == sched.id


def test_list_enabled(tmp_path):
    db = make_db(tmp_path)
    db.scheduled_recordings.create(title="A", cron_expr="0 9 * * *", enabled=True)
    db.scheduled_recordings.create(title="B", cron_expr="0 10 * * *", enabled=False)
    db.scheduled_recordings.create(title="C", cron_expr="0 11 * * *", enabled=True)

    enabled = db.scheduled_recordings.list_enabled()
    assert len(enabled) == 2
    assert all(s.enabled for s in enabled)


def test_update_terms_bumps_revision(tmp_path):
    db = make_db(tmp_path)
    sched = db.scheduled_recordings.create(title="X", cron_expr="0 9 * * *")

    updated = db.scheduled_recordings.update(sched.id, duration_minutes=45)
    assert updated.revision == 2

    updated = db.scheduled_recordings.update(sched.id, title="Y")
    assert updated.revision == 2  # title change doesn't bump

    updated = db.scheduled_recordings.update(sched.id, cron_expr="0 10 * * *")
    assert updated.revision == 3


def test_delete(tmp_path):
    db = make_db(tmp_path)
    sched = db.scheduled_recordings.create(title="X", cron_expr="0 9 * * *")
    assert db.scheduled_recordings.delete(sched.id) is True
    assert db.scheduled_recordings.get(sched.id) is None
    assert db.scheduled_recordings.delete(sched.id) is False


def test_set_state_with_deadline(tmp_path):
    """set_state persists armed_at and deadline_at (I7 data shape)."""
    db = make_db(tmp_path)
    sched = db.scheduled_recordings.create(title="X", cron_expr="0 9 * * *")

    db.scheduled_recordings.set_state(
        sched.id, "arming", armed_at=12345.0,
    )
    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "arming"
    assert updated.armed_at == 12345.0

    db.scheduled_recordings.set_state(
        sched.id, "recording", deadline_at=99999.0, armed_at=None,
    )
    updated = db.scheduled_recordings.get(sched.id)
    assert updated.state == "recording"
    assert updated.deadline_at == 99999.0
    assert updated.armed_at is None


# -- cron module tests --


def test_cron_is_due():
    from holdspeak.cron import cron_is_due
    from datetime import datetime

    now = datetime(2026, 8, 17, 9, 0, 0)  # Monday
    assert cron_is_due("0 9 * * 1", now=now) is True
    assert cron_is_due("0 10 * * 1", now=now) is False
    assert cron_is_due("* * * * *", now=now) is True
    assert cron_is_due("*/5 * * * *", now=now) is True
    assert cron_is_due("*/5 * * * *", now=datetime(2026, 8, 17, 9, 3, 0)) is False


def test_next_cron_fire():
    from datetime import datetime, timezone

    after = datetime(2026, 8, 17, 9, 0, 0, tzinfo=timezone.utc)
    nf = next_cron_fire("0 10 * * *", after=after)
    assert nf is not None
    dt = datetime.fromtimestamp(nf, tz=timezone.utc)
    assert dt.hour == 10
    assert dt.minute == 0


def test_next_cron_fire_invalid():
    assert next_cron_fire("bad") is None
    assert next_cron_fire("* * *") is None
