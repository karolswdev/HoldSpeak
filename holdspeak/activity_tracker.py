"""Runtime activity snapshots for web + desktop presence clients."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional


RuntimeActivityState = str

VALID_ACTIVITY_STATES = frozenset(
    {
        "idle",
        "listening",
        "recording",
        "transcribing",
        "processing",
        "typing",
        "complete",
        "meeting_live",
        "saving",
        "error",
        # HS-60: the wake word's bounded armed window.
        "armed",
    }
)

_DEFAULT_LABELS = {
    "idle": "Ready",
    "listening": "Listening",
    "recording": "Recording",
    "transcribing": "Transcribing",
    "processing": "Processing",
    "typing": "Typing",
    "complete": "Complete",
    "meeting_live": "Meeting live",
    "saving": "Saving",
    "error": "Needs attention",
    "armed": "Armed",
}

_ACTIVE_WINDOW_STATES = frozenset(
    {"listening", "recording", "transcribing", "processing", "typing", "saving", "armed"}
)
_LINGER_WINDOW_STATES = frozenset({"complete", "meeting_live", "error"})


def _utc_now_iso() -> str:
    return datetime.now().isoformat()


def normalize_activity_state(value: object) -> RuntimeActivityState:
    state = str(value or "").strip().lower()
    if state in VALID_ACTIVITY_STATES:
        return state
    return "idle"


def desktop_window_policy(state: object) -> dict[str, object]:
    """Return the native presence-window visibility policy for a state.

    The desktop host is intentionally transient: idle never renders an
    always-on window; active work renders immediately; terminal states linger
    briefly and then hide/destroy.
    """
    normalized = normalize_activity_state(state)
    if normalized == "idle":
        return {"mode": "hidden", "visible": False, "linger_ms": 0}
    if normalized in _LINGER_WINDOW_STATES:
        if normalized == "complete":
            linger_ms = 2200
        elif normalized == "meeting_live":
            linger_ms = 2600
        else:
            linger_ms = 5200
        return {"mode": "linger", "visible": True, "linger_ms": linger_ms}
    if normalized in _ACTIVE_WINDOW_STATES:
        return {"mode": "active", "visible": True, "linger_ms": 0}
    return {"mode": "hidden", "visible": False, "linger_ms": 0}


@dataclass
class RuntimeActivity:
    state: RuntimeActivityState = "idle"
    source: str = "runtime"
    label: str = "Ready"
    detail: str = ""
    started_at: str = field(default_factory=_utc_now_iso)
    updated_at: str = field(default_factory=_utc_now_iso)
    last_event: str = ""
    last_error: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "state": self.state,
            "source": self.source,
            "label": self.label,
            "detail": self.detail,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "last_event": self.last_event,
            "last_error": self.last_error,
            "window": desktop_window_policy(self.state),
        }


class RuntimeActivityTracker:
    """Small state holder for the runtime's current presence snapshot."""

    def __init__(self, *, clock: Callable[[], str] = _utc_now_iso) -> None:
        self._clock = clock
        stamp = self._clock()
        self._activity = RuntimeActivity(started_at=stamp, updated_at=stamp)

    def snapshot(self) -> dict[str, object]:
        return self._activity.to_dict()

    def update(
        self,
        state: object,
        *,
        source: str = "runtime",
        label: Optional[str] = None,
        detail: str = "",
        last_event: str = "",
        last_error: Optional[str] = None,
    ) -> dict[str, object]:
        normalized = normalize_activity_state(state)
        clean_source = str(source or "runtime").strip() or "runtime"
        stamp = self._clock()
        previous = self._activity
        started_at = (
            previous.started_at
            if previous.state == normalized and previous.source == clean_source
            else stamp
        )
        if last_error is None:
            last_error = previous.last_error if normalized != "idle" else ""
        self._activity = RuntimeActivity(
            state=normalized,
            source=clean_source,
            label=str(label or _DEFAULT_LABELS[normalized]),
            detail=str(detail or ""),
            started_at=started_at,
            updated_at=stamp,
            last_event=str(last_event or ""),
            last_error=str(last_error or ""),
        )
        return self.snapshot()


__all__ = [
    "RuntimeActivity",
    "RuntimeActivityTracker",
    "VALID_ACTIVITY_STATES",
    "desktop_window_policy",
    "normalize_activity_state",
]
