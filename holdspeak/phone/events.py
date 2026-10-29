"""The Phone event log: one ``seq`` for every change, replay, live fan-out.

agentring's one event log, kept (its ``relay/src/events.ts``): every change
to a message, a call or a device is one row of ``phone_events`` with a global
``seq``; a reader that was away asks for what came after the last ``seq`` it
saw (``GET /api/phone/events?after_seq=``, the device socket), so a reply is
never lost while nobody listened. Live readers subscribe here; a writer on
any thread appends, and each subscriber gets the event on its own loop.

The socket first subscribes, then replays, then drains what arrived during
the replay, skipping what the replay already sent: no event can slip in
between the replay and the live stream.
"""
from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from ..timestamps import utc_now_iso
from .store import PhoneStore

log = get_logger("phone.events")

#: One page of a replay.
REPLAY_PAGE = 500

#: A subscriber's sentinel: the device was revoked, close its socket.
REVOKED = {"type": "_revoked"}


@dataclass(eq=False)
class Subscriber:
    """One live reader: its loop, its queue, and (for a device) its id."""

    loop: asyncio.AbstractEventLoop
    queue: "asyncio.Queue[dict[str, Any]]"
    device_id: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)

    def put(self, event: Mapping[str, Any]) -> None:
        try:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, dict(event))
        except RuntimeError:  # the loop closed: the socket is gone
            pass


class PhoneEvents:
    """The log over :class:`PhoneStore` plus the live subscribers."""

    def __init__(self, store: PhoneStore, *, clock: Callable[[], str] = utc_now_iso) -> None:
        self._store = store
        self._clock = clock
        self._subscribers: set[Subscriber] = set()
        self._lock = threading.Lock()
        self._listeners: list[Callable[[dict[str, Any]], None]] = []

    def append(self, type_: str, data: Any) -> dict[str, Any]:
        """Store one event and hand it to every live reader. ``data`` is a
        mapping, or ``seq -> mapping`` when the object in it carries the
        event's own ``seq`` (agentring writes the row, then its body)."""
        ts = self._clock()
        seq, stored = self._store.append_event(type_, ts, data)
        event = {"seq": seq, "type": type_, "ts": ts, "data": stored}
        with self._lock:
            subscribers = list(self._subscribers)
            listeners = list(self._listeners)
        for subscriber in subscribers:
            subscriber.put(event)
        for listener in listeners:
            try:
                listener(event)
            except Exception as exc:  # a listener is never a gate on the write
                log.warning(f"phone event listener failed: {exc}")
        return event

    def on_event(self, listener: Callable[[dict[str, Any]], None]) -> None:
        with self._lock:
            self._listeners.append(listener)

    def page(self, after_seq: int = 0, limit: int = REPLAY_PAGE) -> dict[str, Any]:
        """A page of stored events after ``after_seq``."""
        limit = max(1, min(int(limit or REPLAY_PAGE), REPLAY_PAGE))
        rows = self._store.events_after(int(after_seq or 0), limit + 1)
        more = len(rows) > limit
        rows = rows[:limit]
        return {"events": rows, "last_seq": self._store.last_seq(), "has_more": more,
                "next_after_seq": rows[-1]["seq"] if rows else int(after_seq or 0)}

    def replay(self, after_seq: int = 0) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        after = int(after_seq or 0)
        while True:
            page = self.page(after)
            out.extend(page["events"])
            if not page["has_more"]:
                return out
            after = page["next_after_seq"]

    def last_seq(self) -> int:
        return self._store.last_seq()

    def subscribe(self, loop: asyncio.AbstractEventLoop, *, device_id: Optional[str] = None) -> Subscriber:
        subscriber = Subscriber(loop, asyncio.Queue(), device_id)
        with self._lock:
            self._subscribers.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: Subscriber) -> None:
        with self._lock:
            self._subscribers.discard(subscriber)

    def close_device(self, device_id: str) -> int:
        """A revoked device: every one of its sockets gets the close sentinel."""
        with self._lock:
            mine = [s for s in self._subscribers if s.device_id == device_id]
        for subscriber in mine:
            subscriber.put(REVOKED)
        return len(mine)

    def subscribers(self, device_id: Optional[str] = None) -> int:
        with self._lock:
            return sum(1 for s in self._subscribers if device_id is None or s.device_id == device_id)


__all__ = ["PhoneEvents", "REPLAY_PAGE", "REVOKED", "Subscriber"]
