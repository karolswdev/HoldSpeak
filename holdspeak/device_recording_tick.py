"""HS-17-05 — periodic Recording-tick emitter for attached AIPI-Lite devices.

While a meeting is active and has attached devices, push
``Recording M:SS`` status frames every ``TICK_INTERVAL_S`` seconds so
the device's LCD shows live meeting progress. HS-14-07 originally
spec'd "Recording 00:00 updated each minute" but the periodic emitter
was never wired; live verification 2026-05-10 against AIPI-Lite
hardware confirmed only one Recording frame fired per meeting. This
module fills that gap. The current default cadence is 1 s.

Threaded (daemon) rather than asyncio-based because
:class:`DeviceStatusEmitter` is already thread-safe and the meeting
lifecycle handlers in ``web_runtime`` are synchronous. The thread
sleeps on a :class:`threading.Event` so ``stop()`` returns
immediately.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Iterable, Optional

from .logging_config import get_logger

log = get_logger("device_recording_tick")

# Sender signature: ``(device_ids, text) -> None``. Errors are
# swallowed by the underlying ``DeviceStatusEmitter.broadcast``.
TickSender = Callable[[list[str], str], None]


def _format_elapsed(elapsed_seconds: int) -> str:
    """Render ``elapsed_seconds`` as ``Recording MM:SS``.

    Capped at 99:59 for LCD width — anything beyond that is a
    cosmetic concern that does not matter to a hand-held device.
    """
    if elapsed_seconds < 0:
        elapsed_seconds = 0
    mm = min(99, elapsed_seconds // 60)
    ss = elapsed_seconds % 60
    return f"Recording {mm:02d}:{ss:02d}"


class RecordingTicker:
    """Per-meeting Recording-tick scheduler.

    One ticker instance is created per HoldSpeak process; ``start()``
    spawns a daemon thread for the active meeting; ``stop()`` signals
    it to exit. Restarting a new meeting after stop is safe.

    The thread aligns ticks to ``started_at_monotonic + N * interval``
    so cadence does not drift over the meeting's lifetime, even if
    individual ticks are delayed.
    """

    # AIPI-4-11 lands a dedicated middle LCD zone so flashes no longer
    # fight the Recording-tick for the bottom slot. Once flashes have
    # their own home, the tick can run much faster without overwriting
    # transient content. Bumped 5s → 1s on 2026-05-10 so the recording
    # timer feels live ("Recording 02:34" → "Recording 02:35" each
    # second). Cost is negligible: ~1 mA average from the extra
    # status frames on top of the always-on WiFi baseline (~80 mA).
    DEFAULT_TICK_INTERVAL_S = 1.0

    def __init__(
        self,
        *,
        status_sender: TickSender,
        tick_interval_s: float = DEFAULT_TICK_INTERVAL_S,
    ) -> None:
        self._sender = status_sender
        self._tick_interval_s = float(tick_interval_s)
        self._lock = threading.Lock()
        self._stop_event: Optional[threading.Event] = None
        self._thread: Optional[threading.Thread] = None

    def start(
        self,
        *,
        started_at_monotonic: float,
        device_ids: Iterable[str],
    ) -> None:
        """Begin firing Recording ticks for ``device_ids``.

        Resets any previous ticker. ``started_at_monotonic`` must come
        from :func:`time.monotonic` (not wall-clock time) — it is the
        reference point for both the next-tick scheduling and the
        elapsed-seconds calculation that drives the status text.

        No-ops with an empty ``device_ids``.
        """
        ids = [d for d in device_ids if d]
        if not ids:
            return
        with self._lock:
            self._stop_locked()
            stop_event = threading.Event()
            thread = threading.Thread(
                target=self._run,
                args=(started_at_monotonic, ids, stop_event),
                name="recording-tick",
                daemon=True,
            )
            self._stop_event = stop_event
            self._thread = thread
            thread.start()

    def stop(self) -> None:
        """Signal the ticker thread to exit. Idempotent."""
        with self._lock:
            self._stop_locked()

    def is_running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def _stop_locked(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        self._stop_event = None
        # We don't join — the daemon thread will exit on its next wait()
        # return; meanwhile a new start() can create a fresh thread.
        self._thread = None

    def _run(
        self,
        started_at_monotonic: float,
        device_ids: list[str],
        stop_event: threading.Event,
    ) -> None:
        # First tick fires at started_at + tick_interval (not at 0:00 —
        # that initial paint is already done by `_start_meeting`).
        next_tick_at = started_at_monotonic + self._tick_interval_s
        while not stop_event.is_set():
            wait_s = max(0.0, next_tick_at - time.monotonic())
            if stop_event.wait(wait_s):
                return
            elapsed = int(round(time.monotonic() - started_at_monotonic))
            text = _format_elapsed(elapsed)
            try:
                self._sender(device_ids, text)
            except Exception:
                # The sender is expected to swallow its own failures
                # (DeviceStatusEmitter.broadcast logs + returns 0).
                # This try/except is defense-in-depth so a bug in the
                # sender wiring doesn't kill the ticker thread silently.
                log.exception("recording_tick_send_failed")
            next_tick_at += self._tick_interval_s


__all__ = ["RecordingTicker", "TickSender"]
