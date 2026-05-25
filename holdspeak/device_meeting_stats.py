"""AIPI-4-14 — meeting-stat view formatters for the device LCD.

The bridge fires ``event.double_left_click`` while a meeting is active.
HoldSpeak cycles through a short rotation of stat views and pushes the
current page to the device's middle slot. AIPI-4-11 v2's persist-
until-replaced behaviour keeps the view on screen until the next
press or new content lands.

Views are formatted to fit AIPI-4-12's wider middle widget (montserrat_8,
~150 char ceiling). Each view is independent — no shared formatting
state — so the cycle index is plain ``int % len(views)``.
"""

from __future__ import annotations

from collections import Counter
from typing import Callable, Optional

from .device_status import LCD_TEXT_MAX_CHARS, truncate_for_lcd

# Public view-id constants so callers / tests can refer to pages by
# name rather than magic indexes.
VIEW_NUMBERS = "numbers"
VIEW_SPEAKERS = "speakers"
VIEW_INTEL = "intel"

# Cycle order. The bridge fires one event per double-tap; the index
# is rotated per-device by :func:`pick_next_view`.
CYCLE_ORDER: tuple[str, ...] = (VIEW_NUMBERS, VIEW_SPEAKERS, VIEW_INTEL)


def _format_duration(seconds: float) -> str:
    """``mm:ss`` for short meetings; ``hh:mm:ss`` once past an hour."""
    if seconds is None or seconds < 0:
        return "00:00"
    total = int(seconds)
    if total >= 3600:
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    m, s = divmod(total, 60)
    return f"{m:02d}:{s:02d}"


def format_numbers_view(state) -> str:
    """Page 1 — duration + segment count + bookmark count.

    ``state`` is a ``MeetingSessionState`` (duck-typed): we read
    ``duration`` (float seconds), ``segments`` (list), and
    ``bookmarks`` (list).
    """
    duration_s = float(getattr(state, "duration", 0.0) or 0.0)
    segments = getattr(state, "segments", []) or []
    bookmarks = getattr(state, "bookmarks", []) or []
    lines = [
        "Stats:",
        f"Recording: {_format_duration(duration_s)}",
        f"Segments: {len(segments)}",
        f"Bookmarks: {len(bookmarks)}",
    ]
    return truncate_for_lcd("\n".join(lines))


def format_speakers_view(state) -> str:
    """Page 2 — top 3 speakers with their segment counts.

    Falls back to ``Speakers:\\nNone yet`` when no segments have been
    finalised.
    """
    segments = getattr(state, "segments", []) or []
    if not segments:
        return truncate_for_lcd("Speakers:\nNone yet")
    counter: Counter[str] = Counter()
    for seg in segments:
        speaker = getattr(seg, "speaker", None)
        if isinstance(seg, dict):
            speaker = seg.get("speaker") or speaker
        counter[str(speaker or "?")] += 1
    top = counter.most_common(3)
    lines = ["Speakers:"]
    for speaker, count in top:
        lines.append(f"- {speaker}: {count}")
    return truncate_for_lcd("\n".join(lines))


def format_intel_view(state) -> str:
    """Page 3 — latest intel snapshot (topics + first action item)
    or a placeholder when none has been produced yet."""
    intel = getattr(state, "intel", None)
    if intel is None:
        return truncate_for_lcd("Intel:\nNot yet ready")
    topics = getattr(intel, "topics", None) or []
    topic_strs = [str(t).strip() for t in topics[:3] if str(t).strip()]
    action_items = getattr(intel, "action_items", None) or []
    next_action: Optional[str] = None
    for item in action_items[:1]:
        if isinstance(item, dict):
            task = (item.get("task") or "").strip()
            owner = (item.get("owner") or "").strip()
        else:
            task = (getattr(item, "task", None) or "").strip()
            owner = (getattr(item, "owner", None) or "").strip()
        if task:
            next_action = f"{owner}: {task}" if owner else task
            break
    if not topic_strs and not next_action:
        return truncate_for_lcd("Intel:\nNo content yet")
    lines = ["Intel:"]
    if topic_strs:
        lines.append("Topics: " + ", ".join(topic_strs))
    if next_action:
        lines.append("Next: " + next_action)
    return truncate_for_lcd("\n".join(lines))


_FORMATTERS: dict[str, Callable[[object], str]] = {
    VIEW_NUMBERS: format_numbers_view,
    VIEW_SPEAKERS: format_speakers_view,
    VIEW_INTEL: format_intel_view,
}


def pick_next_view(current_index: int) -> tuple[int, str, Callable[[object], str]]:
    """Advance the cycle index and return ``(next_index, view_id, formatter)``.

    Wraps modulo :data:`CYCLE_ORDER` length. Callers store ``next_index``
    on their per-device state for the next event.
    """
    next_index = (current_index + 1) % len(CYCLE_ORDER)
    view_id = CYCLE_ORDER[next_index]
    return next_index, view_id, _FORMATTERS[view_id]


def render_view_for_state(view_id: str, state) -> str:
    """Render ``view_id`` against a meeting state. Used by tests and the
    runtime side-by-side."""
    formatter = _FORMATTERS.get(view_id)
    if formatter is None:
        return truncate_for_lcd(f"Unknown view: {view_id}")
    return formatter(state)


__all__ = [
    "CYCLE_ORDER",
    "LCD_TEXT_MAX_CHARS",
    "VIEW_INTEL",
    "VIEW_NUMBERS",
    "VIEW_SPEAKERS",
    "format_intel_view",
    "format_numbers_view",
    "format_speakers_view",
    "pick_next_view",
    "render_view_for_state",
]
