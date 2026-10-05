"""The batteries-included watcher (owner ruling 2026-10-05, "strong defaults").

One daemon thread in the hub lifespan's start/stop set (HS-200-03: what the
lifespan starts, the lifespan stops).  Every ``RESCAN_SECONDS`` it does two
light things:

1. **Find an engine started after boot.**  While no "Default for AI work"
   head exists, ``InferenceDefaultService.rescan`` scans the four loopback
   engine ports (Ollama, LM Studio, llama.cpp 8080 / 8000).  Loopback only,
   no proxy, no redirect.  The scan stops for good once a ``global`` head
   exists (made by HoldSpeak or the owner, set or cleared).
2. **Summarise the backlog.**  ``MeetingSummaryBacklog`` queues the meetings
   saved before ``meeting.deferred_analysis`` had an engine, once it gains
   one (services/meeting_backlog_service.py).

Ownership: like every conductor that writes, it runs only in the process that
owns the database (``intel_queue_conductor.owns_database``).
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Optional

from .logging_config import get_logger

log = get_logger("defaults_conductor")

#: Seconds between ticks.  One idle tick = four refused loopback connects and
#: one assignment read.
RESCAN_SECONDS = 30.0


class DefaultsConductor:
    def __init__(
        self,
        *,
        defaults_service: Any = None,
        backlog: Any = None,
        interval: float = RESCAN_SECONDS,
    ) -> None:
        self._defaults = defaults_service
        self._backlog = backlog
        self._interval = float(interval)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._scan_done = False

    def tick(self) -> dict[str, Any]:
        """One pass.  Never raises: a background default never breaks the hub."""
        out: dict[str, Any] = {}
        if self._defaults is not None and not self._scan_done:
            try:
                result = self._defaults.rescan()
                out["rescan"] = result
                if result.get("status") in {"has_default", "assigned"}:
                    self._scan_done = True  # a default exists: stop scanning
            except Exception as exc:
                log.warning("default rescan failed: %s", exc)
                out["rescan"] = {"status": "failed"}
        if self._backlog is not None:
            try:
                out["backlog"] = self._backlog.tick()
            except Exception as exc:
                log.warning("summary backlog tick failed: %s", exc)
                out["backlog"] = {"status": "failed"}
        return out

    @property
    def scanning(self) -> bool:
        return self._defaults is not None and not self._scan_done

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="defaults-conductor", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout)
        self._thread = None

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _loop(self) -> None:
        # The first tick waits one interval: boot already ran ``ensure``.
        while not self._stop.wait(self._interval):
            self.tick()


_conductor: Optional[DefaultsConductor] = None
_lock = threading.Lock()


def start_defaults_conductor(
    *,
    defaults_service: Any,
    db_factory: Optional[Callable[[], Any]] = None,
    interval: float = RESCAN_SECONDS,
) -> Optional[DefaultsConductor]:
    """Start the one process-global watcher; ``None`` when this process does not own the DB."""
    global _conductor
    from .intel_queue_conductor import owns_database, wake_intel_queue_conductor
    from .services.meeting_backlog_service import MeetingSummaryBacklog

    with _lock:
        if _conductor is not None and _conductor.is_alive():
            return _conductor
        if not owns_database():
            log.info("Defaults watcher is OFF: this process does not own the database.")
            return None
        if db_factory is None:
            from .db import get_database as db_factory
        backlog = MeetingSummaryBacklog(db_factory, wake=wake_intel_queue_conductor)
        _conductor = DefaultsConductor(
            defaults_service=defaults_service, backlog=backlog, interval=interval,
        )
        _conductor.start()
        log.info("Defaults watcher started (every %.0fs)", interval)
        return _conductor


def stop_defaults_conductor() -> None:
    global _conductor
    with _lock:
        conductor = _conductor
        _conductor = None
    if conductor is not None:
        conductor.stop()


def current_defaults_conductor() -> Optional[DefaultsConductor]:
    return _conductor
