"""A said due ("by Wednesday", "Friday next week", "Nov 5") as a real date.

Betterment D0 (daily/RECIPE.md): a meeting says when a thing is due in
words. The words are read against the meeting's own date when the item is
stored, so "Monday" in two days is due soon and nothing stays a word
forever. The said words are kept beside the date (``due_said``). Words that
name no day stay words, with no date.
"""
from __future__ import annotations

import calendar
import re
from datetime import date, timedelta
from typing import Any, Optional

from holdspeak.timestamps import parse_stamp

_WEEKDAYS = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}

_MONTHS = {
    name.casefold(): index
    for index in range(1, 13)
    for name in (calendar.month_name[index], calendar.month_abbr[index])
}
_MONTHS["sept"] = 9

_NUMBERS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

#: Words that say WHEN in the day, not which day. They are dropped.
_DAY_PARTS = (
    "end of day", "end of the day", "close of business", "eod", "cob",
    "morning", "afternoon", "evening", "night", "noon", "midday",
)

_LEAD = re.compile(r"^(?:due|by|on|before|until|till|no later than|at the latest)\s+")


def _clean(said: str) -> str:
    text = " ".join(str(said).replace(",", " ").split()).casefold().strip(" .!?;:")
    previous = None
    while previous != text:
        previous = text
        text = _LEAD.sub("", text).strip()
    if text in _DAY_PARTS:
        return "today"  # "by end of day": the day it was said
    for part in _DAY_PARTS:
        text = re.sub(rf"(?:^|\s){re.escape(part)}$", "", text).strip()
        text = re.sub(rf"^{re.escape(part)}\s+", "", text).strip()
    return text.strip(" .")


def _week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _next_weekday(anchor: date, weekday: int) -> date:
    """The first ``weekday`` after the anchor (the same weekday means a week on)."""
    ahead = (weekday - anchor.weekday()) % 7
    return anchor + timedelta(days=ahead or 7)


def _month_day(month: int, day: int, year: Optional[int], anchor: date) -> Optional[date]:
    try:
        found = date(year or anchor.year, month, day)
    except ValueError:
        return None
    if year is None and found < anchor:
        try:
            found = date(anchor.year + 1, month, day)
        except ValueError:
            return None
    return found


def _ordinal(text: str) -> Optional[int]:
    match = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?", text)
    return int(match.group(1)) if match else None


def resolve_due(said: Any, anchor: date) -> Optional[date]:
    """The day ``said`` names, read against ``anchor`` (the meeting's date).

    Returns ``None`` when the words name no day ("soon", "after the launch").
    """
    if said is None:
        return None
    raw = str(said).strip()
    if not raw:
        return None
    # A date (or a stamp) already: it stays that day.
    if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None
    text = _clean(raw)
    if not text:
        return None
    if text in ("today", "tonight", "this evening", "now", "asap"):
        return anchor
    if text in ("tomorrow", "tmrw"):
        return anchor + timedelta(days=1)
    if text in ("this week", "end of week", "end of the week", "eow", "end of this week"):
        friday = _week_start(anchor) + timedelta(days=4)
        return friday if friday >= anchor else anchor
    if text in ("next week", "end of next week"):
        return _week_start(anchor) + timedelta(days=7 + 4)
    if text in ("end of month", "end of the month", "eom", "end of this month"):
        return date(anchor.year, anchor.month, calendar.monthrange(anchor.year, anchor.month)[1])

    words = text.split()
    # "in 3 days", "in two weeks"
    if len(words) == 3 and words[0] == "in" and words[2].rstrip("s") in ("day", "week"):
        count = _NUMBERS.get(words[1]) or (int(words[1]) if words[1].isdigit() else None)
        if count:
            return anchor + timedelta(days=count * (7 if words[2].startswith("week") else 1))
        return None

    # Weekdays: "Wednesday", "this Wednesday", "next Wednesday",
    # "Friday next week", "Wednesday this week".
    if words and words[0] == "this" and len(words) == 2 and words[1] in _WEEKDAYS:
        words = words[1:]
    if len(words) == 1 and words[0] in _WEEKDAYS:
        return _next_weekday(anchor, _WEEKDAYS[words[0]])
    if len(words) == 3 and words[0] in _WEEKDAYS and words[1:] == ["this", "week"]:
        return _week_start(anchor) + timedelta(days=_WEEKDAYS[words[0]])
    next_week = (
        (len(words) == 2 and words[0] == "next" and words[1] in _WEEKDAYS and words[1])
        or (len(words) == 3 and words[0] in _WEEKDAYS and words[1:] == ["next", "week"] and words[0])
        or (len(words) == 4 and words[0] in _WEEKDAYS and words[1:] == ["of", "next", "week"] and words[0])
    )
    if next_week:
        return _week_start(anchor) + timedelta(days=7 + _WEEKDAYS[next_week])

    # A weekday in front of a date ("Thu Nov 5") names the date.
    if len(words) > 2 and words[0] in _WEEKDAYS:
        words = words[1:]
    # "Nov 5", "November 5th 2026", "5 Nov", "5th of November"
    if words and words[0] == "the":
        words = words[1:]
    words = [w for w in words if w != "of"]
    if len(words) in (2, 3):
        year = None
        if len(words) == 3:
            if not re.fullmatch(r"\d{4}", words[2]):
                return None
            year = int(words[2])
        first, second = words[0], words[1]
        if first in _MONTHS and _ordinal(second):
            return _month_day(_MONTHS[first], _ordinal(second) or 0, year, anchor)
        if second in _MONTHS and _ordinal(first):
            return _month_day(_MONTHS[second], _ordinal(first) or 0, year, anchor)
    return None


def meeting_anchor(started_at: Any) -> Optional[date]:
    """The meeting's own local day, from its stored start stamp."""
    stamp = parse_stamp(started_at)
    return stamp.date() if stamp is not None else None


def stored_due(said: Any, anchor: Optional[date]) -> tuple[Optional[str], Optional[str]]:
    """``(due, due_said)`` for a row: the ISO day when the words name one.

    ``due`` is the ISO date when the words resolve, else the words as said.
    ``due_said`` is the words as said (``None`` when nothing was said).
    """
    if said is None or not str(said).strip():
        return None, None
    words = str(said).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}", words):
        return words, None  # a date already, not words
    day = resolve_due(words, anchor) if anchor is not None else None
    return (day.isoformat() if day is not None else words), words


def anchor_for_meeting(conn: Any, meeting_id: Any) -> Optional[date]:
    """The local day of a stored meeting's start, read through ``conn``."""
    if not meeting_id:
        return None
    try:
        row = conn.execute("SELECT started_at FROM meetings WHERE id = ?", (str(meeting_id),)).fetchone()
    except Exception:
        return None
    if row is None:
        return None
    value = row["started_at"] if hasattr(row, "keys") else row[0]
    return meeting_anchor(value)


__all__ = ["resolve_due", "stored_due", "meeting_anchor", "anchor_for_meeting"]
