"""The hub's side of the Line's wire (LINE design §4): text, never audio.

The node (``holdspeak line``) says ``hello`` (its lines, its version), posts
its events (``incoming``, ``heard``, ``said``, ``ended``, a command's
``result``) and long-polls ``next`` for the hub's commands (``say``,
``hangup``, ``call``). The :class:`~holdspeak.line.adapter.Line` adapter
reads the events and queues the commands. One :data:`LINE_HUB` per hub.

The waits are asyncio futures on the waiter's own loop; an event is taken
from its queue only by the waiter that wakes, so a cancelled wait never
loses one (the rule ai-phone keeps for a cancelled ``listen``).
"""
from __future__ import annotations

import asyncio
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ..logging_config import get_logger

log = get_logger("line.hub")

#: The node is live while it polls or was heard within this long.
LIVE_SECONDS = 15.0
#: … stale until this long, then offline.
OFFLINE_SECONDS = 30.0
#: The longest ``next`` wait.
NEXT_WAIT_MAX = 25.0
#: A wait woken by ``stop_all``.
STOPPED = {"kind": "_stopped"}


@dataclass
class NodeState:
    name: str
    version: str = ""
    lines: list[dict[str, Any]] = field(default_factory=list)
    active_call: Optional[dict[str, Any]] = None
    seen_at: float = 0.0
    polling: int = 0
    seq: int = 0  # the last event seq taken
    commands: list[dict[str, Any]] = field(default_factory=list)
    next_id: int = 0
    calls: set[str] = field(default_factory=set)
    ended: set[str] = field(default_factory=set)


class LineHub:
    """The wire's state: one entry per node."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._nodes: dict[str, NodeState] = {}
        self._queues: dict[tuple[str, str], deque[dict[str, Any]]] = {}
        self._waiters: dict[tuple[str, str], list[tuple[asyncio.AbstractEventLoop, asyncio.Future[Any]]]] = {}
        #: The node's config (the hello answer): set by the calls service.
        self.config_fn: Callable[[str], dict[str, Any]] = lambda node: {}

    def reset(self) -> None:
        with self._lock:
            self._nodes.clear()
            self._queues.clear()
            self._waiters.clear()

    def _node(self, name: str) -> NodeState:
        node = self._nodes.get(name)
        if node is None:
            node = self._nodes[name] = NodeState(name)
        return node

    # ── the node's side ───────────────────────────────────────────────

    def hello(self, name: str, *, lines: list[dict[str, Any]], version: str = "",
              active_call: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        with self._lock:
            node = self._node(name)
            node.version, node.lines, node.active_call = str(version or ""), list(lines or []), active_call
            node.seen_at = time.monotonic()
        return {"config": self.config_fn(name)}

    def post_events(self, name: str, events: list[dict[str, Any]]) -> int:
        """Take the node's events (each once, by ``seq``); the last seq taken."""
        wake: list[tuple[str, str]] = []
        with self._lock:
            node = self._node(name)
            node.seen_at = time.monotonic()
            for event in sorted(events or [], key=lambda e: int(e.get("seq") or 0)):
                seq = int(event.get("seq") or 0)
                if seq and seq <= node.seq:
                    continue
                node.seq = max(node.seq, seq)
                kind = str(event.get("kind") or "")
                call_id = str(event.get("call_id") or "")
                if kind == "result":
                    key = f"result:{event.get('cmd')}"
                elif kind == "incoming":
                    node.calls.add(call_id)
                    key = "listen"
                elif kind in {"heard", "ended", "dtmf"}:
                    key = f"call:{call_id}"
                    if kind == "ended":
                        node.ended.add(call_id)
                else:
                    continue  # said / interrupted ride the result; others are the node's own
                if kind == "result" and event.get("call_id") and event.get("outcome") == "answered":
                    node.calls.add(call_id)
                self._queues.setdefault((name, key), deque()).append(dict(event))
                wake.append((name, key))
            for key in wake:
                self._wake(key)
            return node.seq

    async def next(self, name: str, *, after: int = 0, wait: float = NEXT_WAIT_MAX) -> list[dict[str, Any]]:
        """The commands after ``after`` (a long poll: waits up to ``wait`` s)."""
        wait = max(0.0, min(float(wait), NEXT_WAIT_MAX))
        with self._lock:
            node = self._node(name)
            node.polling += 1
            node.seen_at = time.monotonic()
        try:
            loop = asyncio.get_running_loop()
            deadline = loop.time() + wait
            while True:
                with self._lock:
                    node.commands = [c for c in node.commands if c["id"] > after]
                    if node.commands or loop.time() >= deadline:
                        return [dict(c) for c in node.commands]
                await self._sleep_on((name, "next"), deadline - loop.time(),
                                     ready=lambda: any(c["id"] > after for c in node.commands))
        finally:
            with self._lock:
                node.polling -= 1
                node.seen_at = time.monotonic()

    # ── the adapter's side ────────────────────────────────────────────

    def queue(self, name: str, op: str, **fields: Any) -> int:
        with self._lock:
            node = self._node(name)
            node.next_id += 1
            node.commands.append({"id": node.next_id, "op": op, **fields})
            self._wake((name, "next"))
            return node.next_id

    def knows(self, name: str, call_id: str) -> bool:
        with self._lock:
            node = self._nodes.get(name)
            return bool(node and call_id in node.calls)

    def ended(self, name: str, call_id: str) -> bool:
        with self._lock:
            node = self._nodes.get(name)
            return bool(node and call_id in node.ended)

    def take(self, name: str, key: str) -> Optional[dict[str, Any]]:
        with self._lock:
            queue = self._queues.get((name, key))
            return queue.popleft() if queue else None

    async def wait(self, name: str, key: str, timeout: float) -> Optional[dict[str, Any]]:
        """The next event for ``key`` (``listen``, ``call:<id>``, ``result:<cmd>``);
        None after ``timeout``; :data:`STOPPED` after ``stop_all``."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + max(0.0, float(timeout))
        while True:
            found = self.take(name, key)
            if found is not None:
                return found
            left = deadline - loop.time()
            if left <= 0:
                return None
            if await self._sleep_on((name, key), left, ready=lambda: bool(self._queues.get((name, key)))) is STOPPED:
                return STOPPED

    async def _sleep_on(self, key: tuple[str, str], timeout: float, *, ready: Callable[[], bool]) -> Any:
        """Sleep until woken or ``timeout``; ``ready`` (read under the lock,
        after the waiter is in) says the thing came before we slept."""
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        with self._lock:
            if ready():
                return None
            self._waiters.setdefault(key, []).append((loop, fut))
        try:
            return await asyncio.wait_for(fut, max(0.0, timeout))
        except asyncio.TimeoutError:
            return None
        finally:
            with self._lock:
                rows = self._waiters.get(key) or []
                self._waiters[key] = [row for row in rows if row[1] is not fut]

    def _wake(self, key: tuple[str, str], value: Any = None) -> None:
        for loop, fut in list(self._waiters.get(key) or []):
            def settle(fut: asyncio.Future[Any] = fut) -> None:
                if not fut.done():
                    fut.set_result(value)
            try:
                loop.call_soon_threadsafe(settle)
            except RuntimeError:  # that loop is closed
                pass

    def stop_all(self) -> None:
        with self._lock:
            for key in list(self._waiters):
                self._wake(key, STOPPED)

    def waiting(self, name: str, key: str) -> bool:
        with self._lock:
            return any(not fut.done() for _loop, fut in self._waiters.get((name, key)) or [])

    # ── reads ─────────────────────────────────────────────────────────

    def node_state(self, name: str) -> str:
        """``live``, ``stale``, ``offline`` or ``never`` (no hello yet)."""
        with self._lock:
            node = self._nodes.get(name)
            if node is None or not node.seen_at:
                return "never"
            if node.polling:
                return "live"
            age = time.monotonic() - node.seen_at
        if age < LIVE_SECONDS:
            return "live"
        return "stale" if age < OFFLINE_SECONDS else "offline"

    def snapshot(self, name: str) -> dict[str, Any]:
        with self._lock:
            node = self._nodes.get(name)
            if node is None:
                return {}
            return {"node": node.name, "version": node.version, "lines": [dict(r) for r in node.lines],
                    "active_call": dict(node.active_call) if node.active_call else None}

    def nodes(self) -> list[str]:
        with self._lock:
            return sorted(self._nodes)


#: The hub's one Line wire.
LINE_HUB = LineHub()

__all__ = ["LINE_HUB", "LIVE_SECONDS", "LineHub", "NEXT_WAIT_MAX", "NodeState", "OFFLINE_SECONDS", "STOPPED"]
