"""The Line as a Calls adapter: the surface of ``AiPhone``, the same ``Reply``.

``holdspeak/calls/runner.py`` runs unchanged against either adapter (LINE
design §4, "the contract"). The result codes are ai-phone's numbers, so
``REASONS`` and the ``409`` reasons of ``POST /api/calls/place`` stay:

0 ok, 5 busy, 6 no answer, 7 rejected (a SIP 4xx/6xx), 9 the Line is not
running (node offline or baresip down), 10 listen timeout, 11 no such call,
12 another listener, 13 emergency number, 14 daily limit.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Callable, Optional

from ..calls.aiphone import (
    BUSY, DAILY_LIMIT, EMERGENCY, LISTEN_TIMEOUT, LISTENER_BUSY, NO_ANSWER, NO_CALL, NOT_RUNNING, OK, REJECTED,
    USAGE, Reply,
)
from ..logging_config import get_logger
from .guards import DEFAULT_DAILY_LIMIT, DailyCount, is_emergency
from .hub import LINE_HUB, STOPPED, LineHub

log = get_logger("line.adapter")

#: A node's ``call`` result outcome → the exit code.
OUTCOME_CODES = {"answered": OK, "busy": BUSY, "no_answer": NO_ANSWER, "rejected": REJECTED,
                 "not_running": NOT_RUNNING, "emergency": EMERGENCY, "daily_limit": DAILY_LIMIT,
                 "failed": NOT_RUNNING, "usage": USAGE}
#: How long a ``say`` (or a hang-up's words) may take.
SAY_SECONDS = 180.0
#: How often a long wait looks whether the node is still there.
CHECK_SECONDS = 2.0


def _not_running(words: str = "The Line is not running") -> Reply:
    return Reply(NOT_RUNNING, {"ok": False, "error": words, "code": NOT_RUNNING})


class Line:
    """One Line node, through the hub's wire."""

    def __init__(self, node: str, *, hub: Optional[LineHub] = None,
                 daily_limit: Callable[[], int] = lambda: DEFAULT_DAILY_LIMIT,
                 count_path: Optional[Path] = None) -> None:
        self.node = node
        self._hub = hub or LINE_HUB
        self._limit = daily_limit
        self._count_path = count_path

    @property
    def _count(self) -> DailyCount:
        from .supervisor import state_dir

        return DailyCount(self._count_path or state_dir() / "placed-hub.json")

    @property
    def hub(self) -> LineHub:
        return self._hub

    def _live(self) -> bool:
        return self._hub.node_state(self.node) in {"live", "stale"}

    async def _result(self, cmd: int, timeout: float) -> Optional[dict[str, Any]]:
        """The node's result for one command; None when the node went away."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while loop.time() < deadline:
            found = await self._hub.wait(self.node, f"result:{cmd}", min(CHECK_SECONDS, deadline - loop.time()))
            if found is STOPPED:
                return None
            if found is not None:
                return found
            if self._hub.node_state(self.node) in {"offline", "never"}:
                return None
        return None

    # ── the relay commands ────────────────────────────────────────────

    async def listen(self, *, call_id: str = "", timeout: float = 60.0) -> Reply:
        if not self._live():
            await asyncio.sleep(min(1.0, float(timeout)))
            return _not_running()
        if call_id and not self._hub.knows(self.node, call_id):
            return Reply(NO_CALL, {"ok": False, "error": f"no call {call_id}", "code": NO_CALL})
        key = f"call:{call_id}" if call_id else "listen"
        if not call_id and self._hub.waiting(self.node, key):
            return Reply(LISTENER_BUSY, {"ok": False, "error": "another listen is waiting", "code": LISTENER_BUSY})
        loop = asyncio.get_running_loop()
        deadline = loop.time() + max(1.0, float(timeout))
        while True:
            left = deadline - loop.time()
            if left <= 0:
                return Reply(LISTEN_TIMEOUT, {"ok": True, "kind": "timeout"})
            event = await self._hub.wait(self.node, key, min(CHECK_SECONDS, left))
            if event is STOPPED:
                return _not_running("The Line stopped")
            if event is None:
                if self._hub.node_state(self.node) in {"offline", "never"}:
                    return _not_running()
                continue
            kind = str(event.get("kind") or "")
            if kind == "incoming":
                return Reply(OK, {"ok": True, "kind": "incoming", "call_id": str(event.get("call_id") or ""),
                                  "line": str(event.get("line") or "main"), "remote": str(event.get("remote") or "")})
            if kind == "heard":
                heard = {"ok": True, "kind": "heard", "text": str(event.get("text") or "")}
                if isinstance(event.get("stt_ms"), (int, float)):
                    heard["stt_ms"] = float(event["stt_ms"])  # the node's own speech-in time
                return Reply(OK, heard)
            if kind == "ended":
                return Reply(OK, {"ok": True, "kind": "ended", "call_id": call_id,
                                  "outcome": str(event.get("outcome") or "completed"),
                                  "ended_by": str(event.get("ended_by") or "them"),
                                  "detail": str(event.get("detail") or "")})
            # dtmf and anything newer: not a turn; listen on.

    async def say(self, text: str, *, call_id: str = "") -> Reply:
        text = str(text or "").strip()
        if not text or len(text) > 2000:
            return Reply(USAGE, {"ok": False, "error": "say needs 1 to 2000 characters of text", "code": USAGE})
        if not self._live():
            return _not_running()
        if call_id and self._hub.ended(self.node, call_id):
            return Reply(NO_CALL, {"ok": False, "error": f"call {call_id} has ended", "code": NO_CALL})
        cmd = self._hub.queue(self.node, "say", call_id=call_id, text=text)
        result = await self._result(cmd, SAY_SECONDS)
        if result is None:
            return _not_running()
        said = str(result.get("result") or "")
        if said in {"said", "interrupted"}:
            return Reply(OK, {"ok": True, "result": said, "call_id": call_id})
        return Reply(NO_CALL, {"ok": False, "error": f"call {call_id} has ended", "code": NO_CALL})

    async def hangup(self, *, say: str = "", call_id: str = "") -> Reply:
        if not self._live():
            return _not_running()
        if call_id and self._hub.ended(self.node, call_id):
            return Reply(NO_CALL, {"ok": False, "error": f"call {call_id} has ended", "code": NO_CALL})
        cmd = self._hub.queue(self.node, "hangup", call_id=call_id, text=str(say or ""))
        result = await self._result(cmd, SAY_SECONDS)
        if result is None:
            return _not_running()
        if str(result.get("result") or "") == "no_call":
            return Reply(NO_CALL, {"ok": False, "error": "no call in progress", "code": NO_CALL})
        return Reply(OK, {"ok": True, "call_id": call_id, "outcome": "completed", "ended_by": "hangup_command"})

    async def call(self, to: str, *, ring_seconds: float = 30.0, line: str = "") -> Reply:
        target = str(to or "").strip()
        if not target:
            return Reply(USAGE, {"ok": False, "error": "call needs a number or a SIP address", "code": USAGE})
        if is_emergency(target):
            return Reply(EMERGENCY, {"ok": False, "outcome": "emergency", "code": EMERGENCY,
                                     "error": "HoldSpeak never calls an emergency number"})
        limit = int(self._limit() or 0)
        if not self._count.allow(limit):
            return Reply(DAILY_LIMIT, {"ok": False, "outcome": "daily_limit", "code": DAILY_LIMIT,
                                       "error": f"The daily limit of {limit} calls is reached"})
        if not self._live():
            return _not_running()
        ring = max(1.0, float(ring_seconds))
        cmd = self._hub.queue(self.node, "call", to=target, ring_seconds=ring, line=str(line or ""))
        result = await self._result(cmd, ring + 30.0)
        if result is None:
            return _not_running()
        outcome = str(result.get("outcome") or "failed")
        code = OUTCOME_CODES.get(outcome, REJECTED)
        if code == OK:
            self._count.add()
            return Reply(OK, {"ok": True, "call_id": str(result.get("call_id") or ""), "mode": "relay",
                              "outcome": "answered"},
                         [{"event": "created", "call_id": str(result.get("call_id") or "")}])
        return Reply(code, {"ok": False, "outcome": outcome, "detail": str(result.get("detail") or ""),
                            "error": str(result.get("error") or ""), "code": code})

    def stop_all(self) -> None:
        self._hub.stop_all()

    # ── its state (the shape of ai-phone's ``state.json``) ────────────

    def running(self) -> bool:
        return self._live()

    def state(self) -> dict[str, Any]:
        snap = self._hub.snapshot(self.node)
        if not snap:
            return {}
        lines = {str(row.get("id") or "main"): {"id": str(row.get("id") or "main"), "kind": str(row.get("kind") or "sip"),
                                                "address": str(row.get("address") or ""),
                                                "state": str(row.get("state") or "")}
                 for row in snap.get("lines") or []}
        return {"lines": lines, "active_call": snap.get("active_call"), "node": self.node,
                "version": snap.get("version") or ""}


__all__ = ["Line", "OUTCOME_CODES"]
