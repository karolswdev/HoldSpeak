"""Parked 2026-11-08 (Lane W): five thread frame emitters no face read.

thread_turn_started, thread_guardrail, thread_compacted, thread_status_line
and thread_call_state were consumed only by the Thread window
(web/src/desk/pullouts/_parked/ThreadPullout.tsx, parked by Betterment Q4).
The Ask reads its own ask_* frames and taps four other thread frames in
process. The thread rows (guardrail parts, compaction cut, status_line,
call_mode) are still written; only the live broadcast is parked.
Moved from holdspeak/kernel/inference_stream.py.
"""
from __future__ import annotations

from typing import Any, Callable


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


def emit_thread_guardrail(
    broadcast: Callable[..., Any],
    *,
    thread_id: str,
    message_id: str,
    violations: list[str],
    warnings: list[str],
    guardrails: list[str],
    raw: dict[str, Any] | None = None,
) -> None:
    """Broadcast ``thread_guardrail`` when a guardrail evaluation completes (HS-153-03)."""
    payload: dict[str, Any] = {
        "thread_id": thread_id,
        "message_id": message_id,
        "violations": violations,
        "warnings": warnings,
        "guardrails": guardrails,
    }
    if raw is not None:
        payload["raw"] = raw
    broadcast("thread_guardrail", payload)


def emit_thread_compacted(
    broadcast: Callable[..., Any],
    *,
    thread_id: str,
    message_id: str,
    cut_at: str,
    count: int,
) -> None:
    """Broadcast ``thread_compacted`` when a compaction cut is committed (HS-153-05)."""
    broadcast("thread_compacted", {
        "thread_id": thread_id,
        "message_id": message_id,
        "cut_at": cut_at,
        "count": count,
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


def emit_thread_call_state(
    broadcast: Callable[..., Any],
    *,
    thread_id: str,
    state: str,
) -> None:
    """Broadcast ``thread_call_state`` on call mode transitions (HS-154-03).

    ``state`` is one of: ``off``, ``listening``, ``thinking``, ``speaking``.
    Only ``off`` / ``listening`` (the persisted ON/OFF) are emitted from the
    server; ``thinking`` / ``speaking`` are derived client-side from the
    existing turn-streaming and TTS state.
    """
    broadcast("thread_call_state", {
        "thread_id": thread_id,
        "state": state,
    })
