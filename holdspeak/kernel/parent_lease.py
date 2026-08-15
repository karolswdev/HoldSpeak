"""Process-owned heartbeat helpers for live parent dispatches."""
from __future__ import annotations

from threading import Event, Lock, Thread
from typing import Any, Callable


class ParentLeaseHeartbeats:
    """Daemon refreshers that vanish with their owning controller process."""

    def __init__(self, refresh: Callable[[str], None], *, interval: Callable[[], float]) -> None:
        self._refresh, self._interval = refresh, interval
        self._stops: dict[str, Event] = {}
        self._lock = Lock()

    def start(self, operation_id: str) -> None:
        with self._lock:
            previous = self._stops.pop(operation_id, None)
            stop = Event()
            self._stops[operation_id] = stop
        if previous is not None:
            previous.set()
        Thread(target=self._run, args=(operation_id, stop), daemon=True,
               name=f"parent-lease-{operation_id[-8:]}").start()

    def stop(self, operation_id: str) -> None:
        with self._lock:
            stop = self._stops.pop(operation_id, None)
        if stop is not None:
            stop.set()

    def stop_all(self) -> None:
        """Release every refresher when its broker is replaced or shuts down."""
        with self._lock:
            stops = tuple(self._stops.values())
            self._stops.clear()
        for stop in stops:
            stop.set()

    def _run(self, operation_id: str, stop: Event) -> None:
        while not stop.wait(self._interval()):
            self._refresh(operation_id)


__all__ = ["ParentLeaseHeartbeats"]
