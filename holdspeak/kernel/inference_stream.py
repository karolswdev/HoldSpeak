"""Typed streaming primitives for inference dispatch (HS-151-03).

``Delta`` is the unit of streaming output from a provider: a frozen value
carrying kind, text, and metadata.  ``StreamCadence`` gates persistence
flushes so a streaming turn writes at most once per 500 chars OR 2 s,
and exactly once at done/abort — never the same text twice.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Protocol

import threading


# ----------------------------------------------------------- Delta

@dataclass(frozen=True)
class Delta:
    """One streaming event from the provider.

    kind:
        ``"text"``            — a content token (``text`` carries it).
        ``"reasoning"``       — a reasoning/chain-of-thought token.
        ``"tool_call_delta"`` — one tool-call streaming fragment (``meta``
                                carries ``index``, ``id`` (first chunk only),
                                ``name`` (first chunk only), and
                                ``arguments_fragment``).
        ``"tool_calls"``      — finalized tool-call list, emitted once at
                                stream end when any tool call was accumulated,
                                BEFORE ``done`` (``meta["tool_calls"]`` is
                                ``[{id, name, arguments}, ...]`` where
                                ``arguments`` is a JSON string).
        ``"usage"``           — terminal usage stats (``meta`` carries
                                ``prompt_tokens``, ``completion_tokens``, etc.).
        ``"done"``            — the stream ended normally (``text`` is empty).
        ``"error"``           — the provider raised (``text`` carries the message).
    """
    kind: str
    text: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


# ----------------------------------------------------------- StreamCadence

class StreamCadence:
    """Buffer text and decide when to flush to the persistent layer.

    Flush semantics (the spec from settled-design D3):
    - At 500 chars accumulated since the last flush, OR
    - At 2 seconds since the last flush (injectable clock), OR
    - At done/abort (``finish()``).
    - Never flush the same text twice.

    ``feed(text) -> bool`` returns True when the caller should flush.
    The pending buffer is exposed via ``pending`` so the flusher can
    read exactly what to write.  ``mark_flushed()`` resets the counters.
    """

    CHAR_THRESHOLD = 500
    TIME_THRESHOLD_S = 2.0

    def __init__(self, *, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or _default_clock
        self._buffer: list[str] = []
        self._flushed_len: int = 0  # chars already flushed
        self._last_flush_time: float = self._clock()
        self._finished: bool = False

    @property
    def pending(self) -> str:
        """The text accumulated since the last flush (the delta to persist)."""
        full = "".join(self._buffer)
        return full[self._flushed_len:]

    @property
    def total_text(self) -> str:
        """Everything fed so far (flushed + pending)."""
        return "".join(self._buffer)

    def feed(self, text: str) -> bool:
        """Append *text* and return True when a flush is due."""
        if self._finished:
            return False
        self._buffer.append(text)
        pending_chars = sum(len(s) for s in self._buffer) - self._flushed_len
        elapsed = self._clock() - self._last_flush_time
        return (
            pending_chars >= self.CHAR_THRESHOLD
            or elapsed >= self.TIME_THRESHOLD_S
        )

    def finish(self) -> bool:
        """Signal done/abort.  Returns True when there is unflushed text."""
        self._finished = True
        pending_chars = sum(len(s) for s in self._buffer) - self._flushed_len
        return pending_chars > 0

    def mark_flushed(self) -> None:
        """Called after the caller has persisted ``pending``."""
        self._flushed_len = sum(len(s) for s in self._buffer)
        self._last_flush_time = self._clock()


def _default_clock() -> float:
    import time
    return time.monotonic()


# ------------------------------------------------- frame broadcast helpers
# Canonical emit points for the three thread frames (HS-151-03).
# The thread service (HS-151-04) calls these; the realtime frame scanner
# reads them to prove the frames are wired.


def emit_thread_turn_started(
    broadcast: Callable[..., Any],
    *,
    thread_id: str,
    message_id: str,
    user_message_id: str,
    model_id: str,
    egress: str,
) -> None:
    """Broadcast ``thread_turn_started`` when the assistant row is committed."""
    broadcast("thread_turn_started", {
        "thread_id": thread_id,
        "message_id": message_id,
        "user_message_id": user_message_id,
        "model_id": model_id,
        "egress": egress,
    })


def emit_thread_delta(
    broadcast: Callable[..., Any],
    *,
    thread_id: str,
    message_id: str,
    ordinal: int,
    kind: str,
    text: str,
    seq: int,
) -> None:
    """Broadcast ``thread_delta`` for each streaming token."""
    broadcast("thread_delta", {
        "thread_id": thread_id,
        "message_id": message_id,
        "ordinal": ordinal,
        "kind": kind,
        "text": text,
        "seq": seq,
    })


def emit_thread_turn_done(
    broadcast: Callable[..., Any],
    *,
    thread_id: str,
    message_id: str,
    receipt_id: str,
    outcome: str,
    egress: str,
    stats: dict[str, Any],
) -> None:
    """Broadcast ``thread_turn_done`` when the turn receipt is written."""
    broadcast("thread_turn_done", {
        "thread_id": thread_id,
        "message_id": message_id,
        "receipt_id": receipt_id,
        "outcome": outcome,
        "egress": egress,
        "stats": stats,
    })


# --------------------------------------------------------- tool loop frames (HS-152-01)


def emit_thread_tool_pending(
    broadcast: Callable[..., Any],
    *,
    thread_id: str,
    message_id: str,
    call_id: str,
    name: str,
    args_head: str,
    tool_class: str,
    decision_required: bool,
    elicitation: dict[str, Any] | None = None,
) -> None:
    """Broadcast ``thread_tool_pending`` when a tool call awaits resolution."""
    payload: dict[str, Any] = {
        "thread_id": thread_id,
        "message_id": message_id,
        "call_id": call_id,
        "name": name,
        "args_head": args_head,
        "class": tool_class,
        "decision_required": decision_required,
    }
    if elicitation is not None:
        payload["elicitation"] = elicitation
    broadcast("thread_tool_pending", payload)


def emit_thread_tool_result(
    broadcast: Callable[..., Any],
    *,
    thread_id: str,
    message_id: str,
    call_id: str,
    name: str,
    receipt_id: str,
    outcome: str,
    kind: str,
    summary: str,
    sensitive: bool,
) -> None:
    """Broadcast ``thread_tool_result`` when a tool call has completed."""
    broadcast("thread_tool_result", {
        "thread_id": thread_id,
        "message_id": message_id,
        "call_id": call_id,
        "name": name,
        "receipt_id": receipt_id,
        "outcome": outcome,
        "kind": kind,
        "summary": summary,
        "sensitive": sensitive,
    })


def emit_thread_status_line(
    broadcast: Callable[..., Any],
    *,
    thread_id: str,
    text: str,
) -> None:
    """Broadcast ``thread_status_line`` for in-progress turn status."""
    broadcast("thread_status_line", {
        "thread_id": thread_id,
        "text": text,
    })
