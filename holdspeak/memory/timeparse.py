"""The time phrase in a memory question (MEMORY-DESIGN.md §3.2, the Time retriever).

``parse_time_phrase("what did I send last week", now)`` gives the range
"last week" names, in the owner's zone, and the words that named it.  No
model and no new dependency: a small set of English patterns.

* **The owner's zone** is the hub's local zone, as everywhere else on the
  desk (``services/door_service.py`` ``_local_zone``; PR #778: a bare ISO
  time is the hub's local wall time).  A test passes ``zone``.
* **A week starts on Monday.**
* **A range is ``[time_from, time_to)``**: ISO-8601 with the offset in force
  at each end, so a range across a DST change is exact.
* **A bare month, weekday, quarter or date is the most recent one** that
  has started ("in September" asked in March is last September).

The patterns:

``today`` · ``yesterday`` · ``the day before yesterday`` ·
``this morning|afternoon|evening``, ``tonight``, ``yesterday morning|…``,
``last night`` · ``this|last week|month|quarter|year|weekend`` ·
``the past week``, ``the last month`` (a rolling span to now) ·
``the last|past N days|weeks|months|years`` · ``N days|weeks|months|years ago``
· ``on Tuesday``, ``last Tuesday``, ``Tuesday`` · ``in September``,
``September 2025`` · ``September 15``, ``15 September``, ``2026-09-15`` ·
``in Q3``, ``Q3 2025`` · ``in 2025`` · ``since <any of these>`` (to now).
"""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from typing import Callable, NamedTuple, Optional


class TimeRange(NamedTuple):
    """The range a phrase names: ``[time_from, time_to)``, ISO-8601 with offset."""

    time_from: str
    time_to: str
    phrase: str


_WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}
_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}
# Short names only next to a day number ("Sep 15"): "Jan" alone is a person.
_MONTH_SHORT = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
_NUMBERS = {
    "a couple of": 2, "couple of": 2, "a few": 3, "few": 3, "a": 1, "an": 1,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}


def _alternation(words) -> str:
    return "|".join(sorted((re.escape(word) for word in words), key=len, reverse=True))


_WD = _alternation(_WEEKDAYS)
_MON = _alternation(_MONTHS)
_MON_ANY = _alternation(list(_MONTHS) + list(_MONTH_SHORT))
_NUM = r"\d{1,3}|" + _alternation(_NUMBERS)
_UNIT = r"day|week|month|year"
_DAY = r"(\d{1,2})(?:st|nd|rd|th)?"
_YEAR = r"((?:19|20)\d{2})"


class _Clock:
    """``now`` in the owner's zone, and local midnights built per day (a
    midnight on the far side of a DST change carries its own offset)."""

    def __init__(self, now: datetime, zone: Optional[tzinfo]) -> None:
        if now.tzinfo is None:
            now = now.astimezone()
        self.zone = zone
        self.now = now.astimezone(zone) if zone is not None else now.astimezone()
        self.today = self.now.date()

    def at(self, day: date, hour: int = 0) -> datetime:
        naive = datetime.combine(day, time(hour))
        return naive.replace(tzinfo=self.zone) if self.zone is not None else naive.astimezone()

    def day(self, day: date) -> tuple[datetime, datetime]:
        return self.at(day), self.at(day + timedelta(days=1))

    def week_start(self, day: date) -> date:
        return day - timedelta(days=day.weekday())


def _number(word: str) -> int:
    word = " ".join(word.lower().split())
    return int(word) if word.isdigit() else _NUMBERS[word]


def _month_shift(year: int, month: int, by: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + by
    return index // 12, index % 12 + 1


def _month_range(clock: _Clock, year: int, month: int, months: int = 1) -> tuple[datetime, datetime]:
    end_year, end_month = _month_shift(year, month, months)
    return clock.at(date(year, month, 1)), clock.at(date(end_year, end_month, 1))


def _recent_month_year(clock: _Clock, month: int, *, before_this: bool = False) -> int:
    """The year of the most recent ``month`` that has started."""
    year = clock.today.year
    if month > clock.today.month or (before_this and month == clock.today.month):
        year -= 1
    return year


def _shift_local(clock: _Clock, unit: str, count: int) -> datetime:
    """``now`` moved back ``count`` units on the local wall clock."""
    now = clock.now.replace(tzinfo=None)
    if unit == "day":
        moved = now - timedelta(days=count)
    elif unit == "week":
        moved = now - timedelta(weeks=count)
    else:
        months = count * (12 if unit == "year" else 1)
        year, month = _month_shift(now.year, now.month, -months)
        last_day = (date(*_month_shift(year, month, 1), 1) - timedelta(days=1)).day
        moved = now.replace(year=year, month=month, day=min(now.day, last_day))
    return moved.replace(tzinfo=clock.zone) if clock.zone is not None else moved.astimezone()


Range = Optional[tuple[datetime, datetime]]
Handler = Callable[[re.Match, _Clock], Range]


def _today(match: re.Match, clock: _Clock) -> Range:
    return clock.day(clock.today)


def _yesterday(match: re.Match, clock: _Clock) -> Range:
    return clock.day(clock.today - timedelta(days=1))


def _day_before_yesterday(match: re.Match, clock: _Clock) -> Range:
    return clock.day(clock.today - timedelta(days=2))


_PARTS = {"morning": (0, 12), "afternoon": (12, 18), "evening": (18, 24), "tonight": (18, 24)}


def _part_of_day(match: re.Match, clock: _Clock) -> Range:
    which = (match.groupdict().get("which") or "this").lower()
    part = match.group("part").lower()
    day = clock.today - timedelta(days=1) if which == "yesterday" else clock.today
    start, end = _PARTS[part]
    return clock.at(day, start), (clock.at(day, end) if end < 24 else clock.at(day + timedelta(days=1)))


def _last_night(match: re.Match, clock: _Clock) -> Range:
    day = clock.today - timedelta(days=1)
    return clock.at(day, 18), clock.at(clock.today, 6)


def _this_last_unit(match: re.Match, clock: _Clock) -> Range:
    which = " ".join(match.group("which").lower().split())
    unit = match.group("unit").lower()
    the = bool(match.group("the"))
    rolling = which in ("past", "this past") or (the and which == "last")
    today = clock.today
    if unit == "weekend":
        # The most recent weekend that has started (Saturday and Sunday).
        saturday = today - timedelta(days=(today.weekday() - 5) % 7)
        if which != "this" and today.weekday() >= 5:
            saturday -= timedelta(days=7)
        return clock.at(saturday), clock.at(saturday + timedelta(days=2))
    if rolling:
        span = {"week": ("week", 1), "month": ("month", 1), "quarter": ("month", 3), "year": ("year", 1)}[unit]
        return _shift_local(clock, *span), clock.now
    back = 0 if which == "this" else 1
    if unit == "week":
        start = clock.week_start(today) - timedelta(weeks=back)
        return clock.at(start), clock.at(start + timedelta(weeks=1))
    if unit == "month":
        year, month = _month_shift(today.year, today.month, -back)
        return _month_range(clock, year, month)
    if unit == "quarter":
        first = 3 * ((today.month - 1) // 3) + 1
        year, month = _month_shift(today.year, first, -3 * back)
        return _month_range(clock, year, month, 3)
    year = today.year - back
    return clock.at(date(year, 1, 1)), clock.at(date(year + 1, 1, 1))


def _last_n(match: re.Match, clock: _Clock) -> Range:
    count = _number(match.group("n"))
    if count <= 0:
        return None
    return _shift_local(clock, match.group("unit").lower(), count), clock.now


def _ago(match: re.Match, clock: _Clock) -> Range:
    count = _number(match.group("n"))
    unit = match.group("unit").lower()
    today = clock.today
    if unit == "day":
        return clock.day(today - timedelta(days=count))
    if unit == "week":
        start = clock.week_start(today) - timedelta(weeks=count)
        return clock.at(start), clock.at(start + timedelta(weeks=1))
    if unit == "month":
        year, month = _month_shift(today.year, today.month, -count)
        return _month_range(clock, year, month)
    year = today.year - count
    return clock.at(date(year, 1, 1)), clock.at(date(year + 1, 1, 1))


def _weekday(match: re.Match, clock: _Clock) -> Range:
    # The most recent one before today: "on Tuesday" asked on a Tuesday is
    # last week's Tuesday (today has its own word).
    back = (clock.today.weekday() - _WEEKDAYS[match.group("wd").lower()]) % 7 or 7
    return clock.day(clock.today - timedelta(days=back))


def _named_day(year: Optional[str], month: int, day: int, clock: _Clock) -> Range:
    try:
        if year:
            return clock.day(date(int(year), month, day))
        found = date(clock.today.year, month, day)
        if found > clock.today:
            found = date(clock.today.year - 1, month, day)
        return clock.day(found)
    except ValueError:
        return None


def _month_name(word: str) -> int:
    word = word.lower().rstrip(".")
    return _MONTHS.get(word) or _MONTH_SHORT[word]


def _month_day(match: re.Match, clock: _Clock) -> Range:
    return _named_day(match.group("y"), _month_name(match.group("mon")), int(match.group("d")), clock)


def _iso_day(match: re.Match, clock: _Clock) -> Range:
    try:
        return clock.day(date(int(match.group("y")), int(match.group("m")), int(match.group("d"))))
    except ValueError:
        return None


def _month(match: re.Match, clock: _Clock) -> Range:
    word = match.group("mon").lower()
    month = _MONTHS[word]
    which = (match.group("which") or "").lower()
    if word in ("may", "march") and which not in ("in", "during", "last", ""):
        return None  # "this may take", "of march": not a month
    if match.group("y"):
        return _month_range(clock, int(match.group("y")), month)
    if which == "this":
        return _month_range(clock, clock.today.year, month)
    return _month_range(clock, _recent_month_year(clock, month, before_this=which == "last"), month)


def _quarter(match: re.Match, clock: _Clock) -> Range:
    first = 3 * (int(match.group("q")) - 1) + 1
    year = int(match.group("y")) if match.group("y") else _recent_month_year(clock, first)
    return _month_range(clock, year, first, 3)


def _year(match: re.Match, clock: _Clock) -> Range:
    year = int(match.group("y"))
    return clock.at(date(year, 1, 1)), clock.at(date(year + 1, 1, 1))


# Every optional lead word starts on a word boundary: "login last week" is
# "last week" and the word "login", never "in last week" and "log".
_LEAD = r"(?:\b(?:in|during|over|within|for)\s+)?"
_PATTERNS: list[tuple[re.Pattern, Handler]] = [
    (re.compile(r"\bthe\s+day\s+before\s+yesterday\b", re.I), _day_before_yesterday),
    (re.compile(r"\b(?P<which>yesterday|this|earlier\s+this)\s+(?P<part>morning|afternoon|evening)\b", re.I), _part_of_day),
    (re.compile(r"\b(?P<part>tonight)\b", re.I), _part_of_day),
    (re.compile(r"\blast\s+night\b", re.I), _last_night),
    (re.compile(r"\b(?:earlier\s+|so\s+far\s+)?today\b", re.I), _today),
    (re.compile(r"\byesterday\b", re.I), _yesterday),
    (re.compile(
        _LEAD + r"\b(?:(?P<the>the)\s+)?(?P<which>this\s+past|this|last|previous|prior|past)\s+"
        r"(?P<unit>week|weekend|month|quarter|year)\b", re.I), _this_last_unit),
    (re.compile(
        _LEAD + r"\b(?:the\s+)?(?:last|past|previous|prior)\s+(?P<n>" + _NUM + r")\s+(?P<unit>"
        + _UNIT + r")s?\b", re.I), _last_n),
    (re.compile(r"\b(?P<n>" + _NUM + r")\s+(?P<unit>" + _UNIT + r")s?\s+ago\b", re.I), _ago),
    (re.compile(r"\b(?:(?:on|last|this\s+past|past)\s+)?(?P<wd>" + _WD + r")\b", re.I), _weekday),
    (re.compile(
        r"\b(?:on\s+)?(?P<mon>" + _MON_ANY + r")\.?\s+" + _DAY.replace("(", "(?P<d>", 1)
        + r"\b(?:,?\s+(?P<y>(?:19|20)\d{2})\b)?", re.I), _month_day),
    (re.compile(
        r"\b(?:on\s+)?(?:the\s+)?" + _DAY.replace("(", "(?P<d>", 1) + r"\s+(?:of\s+)?(?P<mon>"
        + _MON_ANY + r")\b\.?(?:,?\s+(?P<y>(?:19|20)\d{2})\b)?", re.I), _month_day),
    (re.compile(r"\b(?:on\s+)?(?P<y>(?:19|20)\d{2})-(?P<m>\d{2})-(?P<d>\d{2})\b", re.I), _iso_day),
    (re.compile(
        r"\b(?:(?P<which>in|during|of|last|this)\s+)(?P<mon>" + _MON + r")\b(?:\s+(?P<y>(?:19|20)\d{2})\b)?",
        re.I), _month),
    (re.compile(r"\b(?P<which>)(?P<mon>" + _MON + r")\s+(?P<y>(?:19|20)\d{2})\b", re.I), _month),
    (re.compile(_LEAD + r"\b(?:the\s+)?q(?P<q>[1-4])\b(?:\s+(?P<y>(?:19|20)\d{2})\b)?", re.I), _quarter),
    (re.compile(r"\b(?:in|during)\s+(?P<y>(?:19|20)\d{2})\b", re.I), _year),
]
# After "since" a bare month counts ("since September").
_SINCE_ONLY: list[tuple[re.Pattern, Handler]] = [
    (re.compile(r"(?P<which>)(?P<mon>" + _MON + r")\b(?:\s+(?P<y>(?:19|20)\d{2})\b)?", re.I), _month),
]
_SINCE = re.compile(r"\bsince\s+", re.I)


def _find(question: str, clock: _Clock) -> Optional[tuple[int, int, datetime, datetime]]:
    """The first phrase in the question: ``(start, end, time_from, time_to)``."""
    found: list[tuple[int, int, datetime, datetime]] = []
    for since in _SINCE.finditer(question):
        at = since.end()
        for pattern, handler in _PATTERNS + _SINCE_ONLY:
            match = pattern.match(question, at)
            if match is None:
                continue
            span = handler(match, clock)
            if span is not None and span[0] < clock.now:
                found.append((since.start(), match.end(), span[0], clock.now))
                break
    for pattern, handler in _PATTERNS:
        for match in pattern.finditer(question):
            span = handler(match, clock)
            if span is not None:
                found.append((match.start(), match.end(), span[0], span[1]))
                break
    if not found:
        return None
    return min(found, key=lambda item: (item[0], -(item[1] - item[0])))


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def parse_time_phrase(
    question: str, now: Optional[datetime] = None, zone: Optional[tzinfo] = None
) -> Optional[TimeRange]:
    """The range the question's time phrase names, or None when it names none."""
    read = read_time_phrase(question, now, zone)
    return read[0] if read is not None else None


def read_time_phrase(
    question: str, now: Optional[datetime] = None, zone: Optional[tzinfo] = None
) -> Optional[tuple[TimeRange, str]]:
    """``(range, the question without the phrase)``, or None."""
    text = str(question or "")
    clock = _Clock(now or datetime.now(timezone.utc), zone)
    found = _find(text, clock)
    if found is None:
        return None
    start, end, time_from, time_to = found
    rest = " ".join((text[:start] + " " + text[end:]).split())
    return TimeRange(_iso(time_from), _iso(time_to), text[start:end].strip()), rest


def instant(value: object, zone: Optional[tzinfo] = None) -> Optional[datetime]:
    """One stored time as an aware instant, or None.

    The stores hold three shapes (``db/projections.py``
    ``_normalize_timestamp``): a SQLite stamp ``YYYY-MM-DD HH:MM:SS`` is UTC;
    an ISO time with an offset is exact; a bare ISO time or a bare date is the
    hub's local wall time.
    """
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), timezone.utc)
    clean = str(value or "").strip()
    if not clean:
        return None
    sqlite_utc = "T" not in clean and " " in clean
    try:
        parsed = datetime.fromisoformat(clean.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return parsed
    if sqlite_utc:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.replace(tzinfo=zone) if zone is not None else parsed.astimezone()


__all__ = ["TimeRange", "instant", "parse_time_phrase", "read_time_phrase"]
