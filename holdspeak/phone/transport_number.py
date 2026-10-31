"""Transport 1: a call on his real number, through Calls (design §5).

``phone.call`` places the call with the Calls service (ai-phone ``call
--relay`` on his line: Telnyx or any SIP line ai-phone has); the gate is the
Calls gate as built (the passphrase first); then the voice says why the desk
called (the reason) and the Calls turn loop talks from the context. When the
call is over the transcript and his decision come back the way a Calls turn
does.

Messages on this transport would be SMS on the same line, but ai-phone's
commands (``call``, ``listen``, ``say``, ``hangup``) have no SMS: a message
with no paired app waits, and shows as a Needs you row.
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Optional

from ..logging_config import get_logger

log = get_logger("phone.transport_number")

#: The most a ``phone.call`` waits for a call on the number to end.
CALL_WAIT_SECONDS = 1800.0


def _calls() -> Any:
    from ..calls.service import CALLS

    return CALLS


def decision_of(record: Any) -> Optional[dict[str, Any]]:
    """What his answer decided: a desk decision the call's turn made, else
    his last clear yes or no (``approve`` / ``deny``) with his words."""
    from ..calls.runner import yes_or_no

    for row in getattr(record, "results", []) or []:
        if str(row.get("kind") or "") in {"desk_decision", "decision", "program_decision"}:
            return {"kind": "desk", "label": row.get("label"), "ref": row.get("ref")}
    for line in reversed(getattr(record, "transcript", []) or []):
        if line.who != "caller" or line.text.startswith("("):
            continue
        answer = yes_or_no(line.text)
        if answer:
            return {"kind": "answer", "answer": answer, "words": line.text[:300]}
    return None


def transcript_of(record: Any) -> list[dict[str, str]]:
    return [{"who": "you" if line.who == "caller" else "holdspeak", "text": line.text}
            for line in getattr(record, "transcript", []) or []]


class NumberTransport:
    """Places a call on his number through Calls and reports its end."""

    def __init__(self, calls: Optional[Callable[[], Any]] = None) -> None:
        self._calls = calls or _calls

    def number(self) -> str:
        try:
            from ..config import Config

            numbers = Config.load().calls.allowed_numbers
        except Exception:
            return ""
        return numbers[0] if numbers else ""

    def available(self) -> tuple[bool, str]:
        """``(True, "")`` when a call can go out on the number, else the reason."""
        from ..calls.service import calls_on

        if not calls_on():
            return False, "calls are off on this hub"
        if not self.number():
            return False, "your number is not set in Settings ▸ Calls"
        calls = self._calls()
        try:
            phone = calls._phone_fn()
        except Exception:
            phone = None
        if phone is None:
            return False, "ai-phone is not found on this Mac"
        return True, ""

    def sms_available(self) -> bool:
        """ai-phone has no SMS command: a message never goes out as SMS."""
        return False

    def place(self, *, reason: str, context: str, on_end: Callable[[dict[str, Any]], None],
              on_failed: Callable[[str, str], None], about: str = "") -> Optional[str]:
        """Place the call (from a worker thread). The Calls record id, or None
        when it did not connect (``on_failed(reason_word, detail)``).
        ``about``: the Program step the call is about (DIR8: its held items
        are read first)."""
        from ..calls.runner import speakable
        from ..services.errors import ServiceError

        calls = self._calls()
        why = reason.strip().rstrip(".")
        if len(why) > 1 and why[0].isupper() and why[1].islower():
            why = why[0].lower() + why[1:]  # "The step" -> "because the step"; "CI" stays
        greeting = speakable(f"This is HoldSpeak. I am calling because {why}.", 300)

        def ended(record: Any) -> None:
            duration = None
            if record.answered_at is not None and record.ended_at is not None:
                duration = round(float(record.ended_at) - float(record.answered_at), 1)
            on_end({
                "calls_turn_id": record.id, "transcript": transcript_of(record), "duration_s": duration,
                "end_reason": record.ended_by or record.outcome or "ended", "decision": decision_of(record),
                "note_ref": record.note_ref or None,
            })

        try:
            summary = calls._on_loop(calls.place(greeting=greeting, context=context, reason=reason, on_end=ended,
                                                 about=about),
                                     timeout=120.0)
        except ServiceError as exc:
            on_failed(str(exc.context.get("reason") or exc.code), exc.detail)
            return None
        except Exception as exc:
            on_failed("failed", str(exc))
            return None
        return str((summary or {}).get("id") or "") or None


def wait_for(event: threading.Event, seconds: float = CALL_WAIT_SECONDS) -> bool:
    return event.wait(seconds)


__all__ = ["CALL_WAIT_SECONDS", "NumberTransport", "decision_of", "transcript_of", "wait_for"]
