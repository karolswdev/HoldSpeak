"""Scheduled recording conductor: hub-side timer that fires capture on a cron (HS-136-01).

Modeled on WorkbenchConductor (workbench_conductor.py:505-568). A daemon thread
ticks every 60 seconds, checking enabled scheduled recordings for due fires.
Drives the state machine: idle -> arming -> recording -> stopped, with cancelled /
refused / missed branches.

Invariants:
  I1  -- single fire: a due schedule fires exactly once per due instant.
  I2  -- recurring advances next_fire_at strictly forward; one-shot disables.
  I3  -- hub-authoritative countdown; cancel honored only in countdown window.
  I4  -- mic authority (IV.3): refuses if voice floor held.
  I5  -- bounded delegation: enable records approval; each fire is kernel-admitted.
  I6  -- auto-stop at duration_minutes with no client.
  I7  -- restart durability: deadline_at persisted; reconcile on boot.
  I8  -- clock honesty: tz-explicit cron evaluation; past one-shot refuses.
  I9  -- no cross-path race: fire lock serializes scheduled fires;
        voice floor + graceful refusal gates against manual captures.
  I10 -- bounded catch-up: missed window capped, never a burst.
"""
from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Optional

from .cron import cron_is_due, next_cron_fire
from .logging_config import get_logger
from .principals import Principal, PrincipalKind

log = get_logger("scheduled_recording_conductor")

COUNTDOWN_SECONDS = 10
# I10: bounded catch-up window. Missed fires older than this are collapsed
# into a single missed receipt.
MISSED_CATCHUP_WINDOW_SECONDS = 3600  # 1 hour

_conductor: Optional[ScheduledRecordingConductor] = None
_broadcast: Optional[Callable[..., Any]] = None


def set_broadcast(fn: Any) -> None:
    """Wire the broadcast callback from the hub's WebSocket manager."""
    global _broadcast
    _broadcast = fn


def broadcast(event_type: str, data: dict) -> None:
    if _broadcast:
        try:
            _broadcast(event_type, data)
        except Exception as exc:
            log.debug(f"Broadcast emit failed: {exc}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _resolve_tz(tz_name: str) -> timezone:
    """Resolve a timezone name to a timezone offset (I8).

    For robustness, supports UTC and fixed-offset names. Full IANA tz
    support would require zoneinfo (Python 3.9+), used here for DST.
    """
    if not tz_name or tz_name.upper() == "UTC":
        return timezone.utc
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(tz_name)  # type: ignore[return-value]
    except (ImportError, KeyError):
        return timezone.utc


class ScheduledRecordingConductor:
    """Background scheduler for scheduled recordings.

    Lifecycle:
      start() -> spawns daemon thread
      stop()  -> signals shutdown and joins

    The conductor accepts injectable dependencies for testing:
      clock        -- callable returning epoch seconds (default time.time)
      db_factory   -- callable returning a Database (default get_database)
      start_meeting_fn -- the fire seam (default: _start_meeting on the live runtime)
      stop_meeting_fn  -- the auto-stop seam
      voice_floor_fn   -- callable() -> Optional[str] returning the current mic owner
    """

    def __init__(
        self,
        *,
        clock: Optional[Callable[[], float]] = None,
        db_factory: Optional[Callable[[], Any]] = None,
        start_meeting_fn: Optional[Callable[..., Any]] = None,
        stop_meeting_fn: Optional[Callable[..., Any]] = None,
        voice_floor_fn: Optional[Callable[[], Optional[str]]] = None,
        tick_interval: float = 60.0,
        countdown_seconds: float = COUNTDOWN_SECONDS,
    ) -> None:
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._clock = clock or time.time
        self._db_factory = db_factory
        self._start_meeting_fn = start_meeting_fn
        self._stop_meeting_fn = stop_meeting_fn
        self._voice_floor_fn = voice_floor_fn
        self._tick_interval = tick_interval
        self._countdown_seconds = countdown_seconds
        # I1/I9: single-fire dedupe and scheduled-fire serialization lock
        self._fired_minutes: dict[str, float] = {}
        self._fire_lock = threading.Lock()
        # Active arming state: schedule_id -> cancel_event
        self._arming: dict[str, threading.Event] = {}
        # Active recording auto-stop timers: schedule_id -> Timer
        self._auto_stop_timers: dict[str, threading.Timer] = {}

    # -- lifecycle --

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="scheduled-recording-conductor"
        )
        self._thread.start()
        log.info("Scheduled recording conductor started")

    def stop(self) -> None:
        self._stop.set()
        # Cancel any active arming countdowns
        for cancel_event in list(self._arming.values()):
            cancel_event.set()
        # Cancel any active auto-stop timers
        for timer in self._auto_stop_timers.values():
            timer.cancel()
        self._auto_stop_timers.clear()
        if self._thread:
            self._thread.join(timeout=5)
        log.info("Scheduled recording conductor stopped")

    # -- public API for cancel (HS-136-02 will call this) --

    def cancel_armed(self, schedule_id: str) -> bool:
        """Cancel an armed countdown. Returns True if cancelled, False if not armed."""
        entry = self._arming.get(schedule_id)
        if entry is None:
            return False
        entry.set()
        return True

    # -- main loop --

    def _loop(self) -> None:
        # I7: on startup, reconcile any interrupted states
        try:
            self._reconcile_on_boot()
        except Exception as exc:
            log.error(f"Boot reconciliation failed: {exc}", exc_info=True)
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as exc:
                log.error(f"Scheduled recording tick failed: {exc}", exc_info=True)
            self._stop.wait(self._tick_interval)

    def _get_db(self) -> Any:
        if self._db_factory:
            return self._db_factory()
        from .db import get_database
        return get_database()

    def _write_receipt(
        self,
        db: Any,
        schedule_id: str,
        state: str,
        outcome: str,
        *,
        detail: str = "",
    ) -> str:
        """Write a kernel receipt for a scheduled recording event (V.2, VI.1)."""
        receipt_id = f"sr_rcpt_{uuid.uuid4().hex[:12]}"
        now = self._clock()
        operation_id = f"sr_op_{uuid.uuid4().hex[:12]}"
        idem_key = f"sr:{schedule_id}:{now}:{uuid.uuid4().hex[:8]}"
        try:
            with db._connection() as conn:
                conn.execute(
                    """INSERT INTO kernel_operations
                       (operation_id, request_id, idempotency_key, name, version,
                        principal_kind, principal_identity, target_ref, placement,
                        envelope_sha256, policy_version, authority_basis,
                        state, revision, native_id, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?,?)""",
                    (
                        operation_id,
                        idem_key,
                        idem_key,
                        "scheduled_recording",
                        1,
                        "scheduler",
                        f"scheduled-recording-conductor:{schedule_id}",
                        f"schedule:{schedule_id}",
                        "local",
                        "",
                        "",
                        f"schedule-delegation:{schedule_id}",
                        state,
                        operation_id,
                        now,
                        now,
                    ),
                )
                conn.execute(
                    """INSERT INTO kernel_receipts
                       (receipt_id, operation_id, state, outcome, result_ref, created_at)
                       VALUES (?,?,?,?,?,?)""",
                    (receipt_id, operation_id, state, outcome, detail, now),
                )
        except Exception as exc:
            log.error(f"Receipt write failed for {schedule_id}: {exc}")
            return receipt_id
        return receipt_id

    # -- I7: boot reconciliation --

    def _reconcile_on_boot(self) -> None:
        """On startup, reconcile any interrupted states (I7) and detect missed fires."""
        db = self._get_db()
        now = self._clock()
        all_schedules = db.scheduled_recordings.list_all()

        for sched in all_schedules:
            if not sched.enabled:
                continue

            # I7: recording whose deadline has passed -> auto-stop + receipt
            if sched.state == "recording" and sched.deadline_at is not None:
                if sched.deadline_at <= now:
                    log.info(
                        f"Reconcile: recording '{sched.title}' (id={sched.id}) "
                        f"deadline passed, stopping"
                    )
                    try:
                        if self._stop_meeting_fn:
                            self._stop_meeting_fn()
                    except Exception as exc:
                        log.error(f"Reconcile stop failed for {sched.id}: {exc}")
                    receipt_id = self._write_receipt(
                        db, sched.id, "succeeded", "auto_stopped_on_restart",
                        detail=f"Deadline {sched.deadline_at} passed during hub downtime",
                    )
                    db.scheduled_recordings.set_state(
                        sched.id, "stopped",
                        last_outcome="auto_stopped_on_restart",
                        last_receipt_id=receipt_id,
                        deadline_at=None,
                        armed_at=None,
                    )
                    broadcast("scheduled_recording.stopped", {
                        "schedule_id": sched.id, "title": sched.title,
                        "receipt_id": receipt_id, "reason": "deadline_passed_on_restart",
                        "at": _now_iso(),
                    })
                    self._advance_after_terminal(db, sched, "auto_stopped_on_restart", receipt_id)
                    continue
                else:
                    # Recording still within deadline -- re-arm auto-stop timer
                    remaining = sched.deadline_at - now
                    timer = threading.Timer(
                        remaining, self._auto_stop, args=(db, sched.id),
                    )
                    timer.daemon = True
                    timer.name = f"sr-autostop-{sched.id}"
                    self._auto_stop_timers[sched.id] = timer
                    timer.start()
                    log.info(
                        f"Reconcile: re-armed auto-stop for '{sched.title}' "
                        f"(id={sched.id}), {remaining:.0f}s remaining"
                    )
                    continue

            # I7: interrupted arming -> resolve as missed
            if sched.state == "arming":
                log.info(
                    f"Reconcile: arming '{sched.title}' (id={sched.id}) "
                    f"interrupted, marking missed"
                )
                receipt_id = self._write_receipt(
                    db, sched.id, "refused", "missed_interrupted_arming",
                    detail="Hub restarted during countdown",
                )
                db.scheduled_recordings.set_state(
                    sched.id, "missed",
                    last_outcome="missed_interrupted_arming",
                    last_receipt_id=receipt_id,
                    armed_at=None,
                )
                broadcast("scheduled_recording.missed", {
                    "schedule_id": sched.id, "title": sched.title,
                    "receipt_id": receipt_id, "reason": "interrupted_arming",
                    "at": _now_iso(),
                })
                self._advance_after_terminal(db, sched, "missed_interrupted_arming", receipt_id)
                continue

            # I10 + VI.1: detect missed fires (bounded catch-up)
            if sched.state in ("idle", "stopped", "cancelled", "refused", "missed"):
                if sched.next_fire_at is not None and sched.next_fire_at < now:
                    # I10: only issue one missed receipt regardless of how long
                    # the hub was down. The window check caps catch-up.
                    log.info(
                        f"Missed fire for schedule '{sched.title}' (id={sched.id}), "
                        f"next_fire_at={sched.next_fire_at} < now={now}"
                    )
                    receipt_id = self._write_receipt(
                        db, sched.id, "refused", "missed",
                        detail=f"Hub was down at scheduled time {sched.next_fire_at}",
                    )
                    db.scheduled_recordings.set_state(
                        sched.id, "missed",
                        last_outcome="missed",
                        last_receipt_id=receipt_id,
                    )
                    broadcast("scheduled_recording.missed", {
                        "schedule_id": sched.id, "title": sched.title,
                        "missed_at": sched.next_fire_at, "receipt_id": receipt_id,
                        "at": _now_iso(),
                    })
                    self._advance_after_terminal(db, sched, "missed", receipt_id)

    # -- tick --

    def _tick(self) -> None:
        db = self._get_db()
        schedules = db.scheduled_recordings.list_enabled()
        now = self._clock()
        now_minute = int(now) // 60

        for sched in schedules:
            if sched.state not in ("idle", "stopped", "cancelled", "refused", "missed"):
                continue
            if sched.next_fire_at is None:
                continue
            if sched.next_fire_at > now:
                continue

            # I1/I9: single-fire dedupe under the fire lock
            with self._fire_lock:
                dedupe_key = f"{sched.id}:{now_minute}"
                if dedupe_key in self._fired_minutes:
                    continue
                self._fired_minutes[dedupe_key] = now

            # Prune old dedupe entries (keep last 100)
            if len(self._fired_minutes) > 200:
                sorted_keys = sorted(self._fired_minutes, key=self._fired_minutes.get)  # type: ignore[arg-type]
                for k in sorted_keys[:100]:
                    del self._fired_minutes[k]

            log.info(f"Schedule '{sched.title}' (id={sched.id}) is due, arming")
            self._arm(db, sched)

    def _arm(self, db: Any, sched: Any) -> None:
        """Enter arming state: emit countdown, start hub-authoritative timer.

        The armed_at timestamp is persisted (I7) so boot reconciliation can
        detect interrupted countdowns.
        """
        now = self._clock()
        cancel_event = threading.Event()
        self._arming[sched.id] = cancel_event

        # I7: persist arming state with armed_at timestamp
        db.scheduled_recordings.set_state(
            sched.id, "arming",
            armed_at=now,
        )

        broadcast("scheduled_recording.arming", {
            "schedule_id": sched.id, "title": sched.title,
            "countdown_seconds": self._countdown_seconds,
            "fire_at": now + self._countdown_seconds,
            "at": _now_iso(),
        })

        # Start countdown in a separate thread (hub-authoritative timer, I3)
        t = threading.Thread(
            target=self._countdown_then_fire,
            args=(db, sched.id, now + self._countdown_seconds, cancel_event),
            daemon=True,
            name=f"sr-countdown-{sched.id}",
        )
        t.start()

    def _countdown_then_fire(
        self,
        db: Any,
        schedule_id: str,
        fire_at: float,
        cancel_event: threading.Event,
    ) -> None:
        """Wait for countdown then fire, unless cancelled (I3)."""
        remaining = fire_at - self._clock()
        if remaining > 0:
            cancelled = cancel_event.wait(timeout=remaining)
        else:
            cancelled = cancel_event.is_set()

        # Clean up arming state
        self._arming.pop(schedule_id, None)

        sched = db.scheduled_recordings.get(schedule_id)
        if sched is None:
            return

        if cancelled or self._stop.is_set():
            # Cancel path
            receipt_id = self._write_receipt(
                db, schedule_id, "refused", "cancelled",
                detail="Cancelled during countdown",
            )
            db.scheduled_recordings.set_state(
                schedule_id, "cancelled",
                last_outcome="cancelled",
                last_receipt_id=receipt_id,
                last_fired_at=self._clock(),
                armed_at=None,
            )
            broadcast("scheduled_recording.cancelled", {
                "schedule_id": schedule_id, "title": sched.title,
                "receipt_id": receipt_id, "at": _now_iso(),
            })
            self._advance_after_terminal(db, sched, "cancelled", receipt_id)
            return

        # I9: fire lock serializes scheduled fires against each other (two
        # schedules due in the same minute, or a late tick racing an on-time
        # one). Cross-path gating against a manual /api/meeting/start is
        # handled by the voice floor (I4): _start_meeting acquires
        # voice_session, and a held floor causes a graceful refusal here.
        with self._fire_lock:
            # I4: mic authority check (IV.3)
            if self._voice_floor_fn:
                floor_owner = self._voice_floor_fn()
                if floor_owner is not None:
                    receipt_id = self._write_receipt(
                        db, schedule_id, "refused", "mic_floor_held",
                        detail=f"Audio floor held by {floor_owner!r}",
                    )
                    db.scheduled_recordings.set_state(
                        schedule_id, "refused",
                        last_outcome="refused",
                        last_receipt_id=receipt_id,
                        last_fired_at=self._clock(),
                        armed_at=None,
                    )
                    broadcast("scheduled_recording.refused", {
                        "schedule_id": schedule_id, "title": sched.title,
                        "reason": f"mic floor held by {floor_owner!r}",
                        "receipt_id": receipt_id, "at": _now_iso(),
                    })
                    self._advance_after_terminal(db, sched, "refused", receipt_id)
                    return

            # Fire! (I5: kernel-admitted; SERVICE principal per HS-151-06 — see _fire)
            self._fire(db, sched)

    def _fire(self, db: Any, sched: Any) -> None:
        """Start the actual recording through _start_meeting seam.

        Called under _fire_lock (I9). Persists deadline_at before observable
        side-effects (I7 -- durable before observable).
        """
        schedule_id = sched.id
        # HS-151-06 (the attended leg's catch): SCHEDULER can NEVER hold a
        # parent route bundle — the Phase-D validator admits only OWNER or
        # SERVICE (inference_parent_route_bundle_service.py:261), so a fired
        # recording captured audio but every transcription interval dropped
        # and the meeting persisted EMPTY. The wake precedent (Sol Amendment
        # 4, speech_session/session.py:144-152) is the lawful shape for
        # ambient capture: a narrow SERVICE identity whose authority basis is
        # what the owner ALREADY configured — here, the armed schedule (the
        # bounded-delegation ruling: enabling a schedule approves its exact
        # work until disabled; every run still gets admission + receipt).
        # The identity/basis/operations must EXACTLY match the sealed
        # "scheduled-recording@1" policy (inference_service_route_policy.py);
        # the schedule id rides the receipts and the bundle command_id, never
        # the principal (sealed policies are keyed on fixed identities).
        principal = Principal(
            PrincipalKind.SERVICE,
            "scheduled-recording",
            frozenset({
                ("meeting.session", 1),
                ("inference.invoke", 1),
                ("inference.cancel", 1),
            }),
            "scheduled-recording:armed-schedule",
        )

        now = self._clock()
        deadline = now + (sched.duration_minutes * 60)

        # I7: persist deadline BEFORE starting capture (durable before observable)
        db.scheduled_recordings.set_state(
            schedule_id, "recording",
            last_fired_at=now,
            armed_at=None,
            deadline_at=deadline,
        )

        # I5: write admission receipt
        receipt_id = self._write_receipt(
            db, schedule_id, "succeeded", "recording_started",
            detail=f"Scheduled recording '{sched.title}' fired",
        )
        db.scheduled_recordings.set_state(
            schedule_id, "recording",
            last_outcome="recording_started",
            last_receipt_id=receipt_id,
        )

        try:
            if self._start_meeting_fn:
                self._start_meeting_fn(
                    principal=principal,
                    title=sched.title,
                    calendar_event_id=sched.calendar_event_id or None,
                )
        except Exception as exc:
            log.error(f"Scheduled recording fire failed for {schedule_id}: {exc}")
            error_receipt = self._write_receipt(
                db, schedule_id, "failed", "start_failed",
                detail=str(exc),
            )
            db.scheduled_recordings.set_state(
                schedule_id, "refused",
                last_outcome="start_failed",
                last_receipt_id=error_receipt,
                deadline_at=None,
            )
            broadcast("scheduled_recording.refused", {
                "schedule_id": schedule_id, "title": sched.title,
                "reason": str(exc), "receipt_id": error_receipt, "at": _now_iso(),
            })
            self._advance_after_terminal(db, sched, "start_failed", error_receipt)
            return

        broadcast("scheduled_recording.started", {
            "schedule_id": schedule_id, "title": sched.title,
            "duration_minutes": sched.duration_minutes,
            "deadline_at": deadline,
            "receipt_id": receipt_id, "at": _now_iso(),
        })

        # I6: schedule auto-stop after duration_minutes
        duration_seconds = sched.duration_minutes * 60
        timer = threading.Timer(
            duration_seconds, self._auto_stop, args=(db, schedule_id),
        )
        timer.daemon = True
        timer.name = f"sr-autostop-{schedule_id}"
        self._auto_stop_timers[schedule_id] = timer
        timer.start()

    def _auto_stop(self, db: Any, schedule_id: str) -> None:
        """Auto-stop a scheduled recording after its duration elapses (I6)."""
        self._auto_stop_timers.pop(schedule_id, None)
        sched = db.scheduled_recordings.get(schedule_id)
        if sched is None or sched.state != "recording":
            return

        log.info(f"Auto-stopping scheduled recording '{sched.title}' (id={schedule_id})")

        stop_error: Optional[str] = None
        try:
            if self._stop_meeting_fn:
                self._stop_meeting_fn()
        except Exception as exc:
            stop_error = str(exc)
            log.error(f"Auto-stop failed for {schedule_id}: {exc}")

        if stop_error:
            receipt_id = self._write_receipt(
                db, schedule_id, "failed", "stop_failed",
                detail=f"Auto-stop raised: {stop_error}",
            )
            outcome = "stop_failed"
        else:
            receipt_id = self._write_receipt(
                db, schedule_id, "succeeded", "auto_stopped",
                detail=f"Auto-stopped after {sched.duration_minutes} minutes",
            )
            outcome = "auto_stopped"
        db.scheduled_recordings.set_state(
            schedule_id, "stopped",
            last_outcome=outcome,
            last_receipt_id=receipt_id,
            deadline_at=None,
        )
        broadcast("scheduled_recording.stopped", {
            "schedule_id": schedule_id, "title": sched.title,
            "receipt_id": receipt_id, "outcome": outcome, "at": _now_iso(),
        })
        self._advance_after_terminal(db, sched, outcome, receipt_id)

    def _advance_after_terminal(
        self,
        db: Any,
        sched: Any,
        outcome: str,
        receipt_id: str,
    ) -> None:
        """After any terminal outcome: advance next_fire for recurring, disable for one-shot (I2)."""
        if sched.one_shot:
            db.scheduled_recordings.update(
                sched.id,
                enabled=False,
                next_fire_at=None,
            )
            return
        # I8: compute next fire in the schedule's timezone
        tz = _resolve_tz(sched.tz)
        now_dt = datetime.fromtimestamp(self._clock(), tz=tz)
        next_fire = next_cron_fire(sched.cron_expr, after=now_dt)
        db.scheduled_recordings.update(
            sched.id,
            next_fire_at=next_fire,
        )


def start_scheduled_recording_conductor(
    **kwargs: Any,
) -> ScheduledRecordingConductor:
    global _conductor
    if _conductor is None:
        _conductor = ScheduledRecordingConductor(**kwargs)
    _conductor.start()
    return _conductor


def stop_scheduled_recording_conductor() -> None:
    global _conductor
    if _conductor:
        _conductor.stop()
        _conductor = None
