"""Betterment daily D8: the window in front of the owner, as his desk reports it.

The desk (each browser view) posts its front window while its page is visible
and focused (``POST /api/desk/presence``), when the front window changes and
once a minute. The heartbeat reads :func:`front_window` before it raises a
notice: a notice about the window he is looking at is not raised.

In memory only: a restart forgets it, and a report older than
:data:`FRESH_SECONDS` says nothing (the page closed, the laptop slept).
"""
from __future__ import annotations

import threading
import time
from typing import Optional

#: A report older than this is not presence (the desk reports once a minute).
FRESH_SECONDS = 150.0

_lock = threading.Lock()
_state: dict[str, object] = {"front": None, "visible": False, "at": 0.0}

#: The windows that show the Needs-you rows: a notice about a row is not
#: raised while one of them is in front.
NEEDS_WINDOWS = frozenset({"chair:needs", "pullout:intelligence:desk"})
#: The windows that show an agent's ask.
AGENT_WINDOWS = frozenset({"conductor", "lane"})


def report(front: Optional[str], visible: bool, *, now: Optional[float] = None) -> None:
    """Store the desk's front window and whether its page is in front of him."""
    with _lock:
        _state["front"] = str(front) if front else None
        _state["visible"] = bool(visible)
        _state["at"] = time.time() if now is None else now


def front_window(*, now: Optional[float] = None) -> Optional[str]:
    """The window in front of the owner now, or ``None`` (no fresh visible report)."""
    clock = time.time() if now is None else now
    with _lock:
        if not _state["visible"] or clock - float(_state["at"] or 0.0) > FRESH_SECONDS:
            return None
        front = _state["front"]
    return str(front) if front else None


def clear() -> None:
    """Forget the report (tests)."""
    report(None, False, now=0.0)
