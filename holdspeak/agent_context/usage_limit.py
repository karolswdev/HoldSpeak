"""Programs PG19: an agent's usage-limit notice, read from its own screen.

Claude Code and Codex print a line when their plan's usage window is used
up, and stop. This module reads that line (two rules, one per harness) and
the reset time it names; :mod:`screen_watch` keeps the reading on the
screen record and the flight says ``limited``. It also reads a share of
the window the harness reports before it stops ("90% of your session
limit"), for the Program's usage warning.

PG21: one real Claude Code stop is in the repository
(``tests/fixtures/usage_limit_captures.json``: the line
Claude Code printed on this Mac on 2026-10-09 and 2026-10-19, read from its
own transcript). It showed two gaps the documented wordings hid: "hit your
weekly limit" and a reset with a date ("resets Oct 24 at 2am"). No real
Codex stop was found on this Mac; its wordings are the documented ones.
:data:`DOCUMENTED` keeps one documented line per harness, the fallback the
Engines window names until a stop is read here (``limit_stops``).

Pure: callers pass the screen text and the clock.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from holdspeak.timestamps import utc_now

#: The lines of the screen's foot the notice is read from.
TAIL_LINES = 24

#: Claude Code: "Claude AI usage limit reached|1761660000" (older builds, an
#: epoch after the bar), "5-hour limit reached ∙ resets 2pm",
#: "You've hit your limit · resets 2pm (Europe/Warsaw)", "Claude usage limit
#: reached. Your limit will reset at 2pm (America/New_York)".
#: Real (2026-10-09, 2026-10-19, this Mac): "You've hit your weekly limit ·
#: resets Oct 24 at 2am (America/Denver)".
_CLAUDE = re.compile(
    r"(?:usage limit reached|limit reached\b|hit your (?:[\w-]+ )?limit)", re.IGNORECASE,
)
#: Codex: "You've hit your usage limit. Upgrade to Pro (…) or try again in
#: 2 hours 13 minutes." / "… try again at 2:05 PM." / "Rate limit reached".
_CODEX = re.compile(r"(?:hit your usage limit|usage limit (?:reached|exceeded)|rate limit reached)", re.IGNORECASE)

_EPOCH = re.compile(r"limit reached\|(\d{9,11})")
_AT = re.compile(
    r"(?:resets?|reset at|try again at|available again at)\s+(?:at\s+)?"
    r"(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)?(?:\s*\(([A-Za-z_]+/[A-Za-z_]+)\))?",
    re.IGNORECASE,
)
_MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
#: A reset with a date: "resets Oct 24 at 2am (America/Denver)".
_ON = re.compile(
    r"(?:resets?|reset at|try again at|available again at)\s+(?:on\s+)?"
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(?:at\s+)?"
    r"(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)?(?:\s*\(([A-Za-z_]+/[A-Za-z_]+)\))?",
    re.IGNORECASE,
)
_IN = re.compile(
    r"try again in\s+(?:(\d+)\s*(?:days?|d)\s*)?(?:(\d+)\s*(?:hours?|hrs?|h)\s*)?(?:(\d+)\s*(?:minutes?|mins?|m)\b)?",
    re.IGNORECASE,
)
#: "You've used 90% of your session limit", "90% of your 5-hour limit used",
#: "Approaching usage limit (85%)".
_SHARE = re.compile(r"(\d{1,3})\s*%\s*(?:of\s+(?:your\s+)?(?:[\w-]+\s+)?(?:limit|usage|window)|used)", re.IGNORECASE)
_SHARE_NEAR = re.compile(r"approaching (?:your )?usage limit\D{0,12}(\d{1,3})\s*%", re.IGNORECASE)


@dataclass(frozen=True)
class LimitReading:
    """What the screen says about the harness's usage window."""

    #: ``claude.usage_limit`` / ``codex.usage_limit`` / ``*.usage_share``.
    rule: str
    #: The line that matched (clipped), the evidence.
    line: str
    #: The reset moment (UTC), when the line names one.
    until: Optional[datetime] = None
    #: A reported share of the window, 0..1 (a warning, not a stop).
    share: Optional[float] = None

    @property
    def stopped(self) -> bool:
        return self.share is None

    def wire(self, now: Optional[datetime] = None) -> dict:
        return {
            "rule": self.rule, "line": self.line, "share": self.share,
            "until": self.until.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if self.until else None,
            "words": until_words(self.until) if self.until else "",
        }


def _tail(screen: str) -> list[str]:
    lines = [line.strip() for line in str(screen or "").splitlines() if line.strip()]
    return lines[-TAIL_LINES:]


def _local_zone(name: Optional[str], now: Optional[datetime] = None):
    """The zone a bare clock time is read in: the named zone, else the local
    zone AT ``now`` (never the real clock's: a pinned test clock crossed the
    DST change on 2026-11-01 and read "2pm" an hour off; found 2026-10-30)."""
    if name:
        try:
            from zoneinfo import ZoneInfo

            return ZoneInfo(name)
        except Exception:
            pass
    moment = now if now is not None else utc_now()
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone().tzinfo


def _hour(hour: int, meridiem: str) -> int:
    meridiem = (meridiem or "").lower().replace(".", "")
    if meridiem == "pm" and hour < 12:
        return hour + 12
    if meridiem == "am" and hour == 12:
        return 0
    return hour


def reset_moment(line: str, now: datetime) -> Optional[datetime]:
    """The reset time a notice line names, as an aware UTC moment; the next
    such clock time after ``now`` for a bare "2pm"."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    epoch = _EPOCH.search(line)
    if epoch:
        return datetime.fromtimestamp(int(epoch.group(1)), tz=timezone.utc)
    within = _IN.search(line)
    if within and any(within.groups()):
        days, hours, minutes = (int(value or 0) for value in within.groups())
        return (now + timedelta(days=days, hours=hours, minutes=minutes)).astimezone(timezone.utc)
    on = _ON.search(line)
    if on:
        month, day = _MONTHS.index(on.group(1).lower()[:3]) + 1, int(on.group(2))
        hour, minute = _hour(int(on.group(3)), on.group(5)), int(on.group(4) or 0)
        local = now.astimezone(_local_zone(on.group(6), now))
        try:
            moment = local.replace(month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0)
            if moment < local - timedelta(days=1):  # "Jan 2" read on Dec 30 is next year's
                moment = moment.replace(year=local.year + 1)
        except ValueError:
            return None
        return moment.astimezone(timezone.utc)
    at = _AT.search(line)
    if at:
        hour, minute = _hour(int(at.group(1)), at.group(3)), int(at.group(2) or 0)
        if hour > 23 or minute > 59:
            return None
        zone = _local_zone(at.group(4), now)
        local = now.astimezone(zone)
        moment = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if moment <= local:
            moment += timedelta(days=1)
        return moment.astimezone(timezone.utc)
    return None


def until_words(moment: Optional[datetime]) -> str:
    """``14:00`` in the hub's local time (the faces' clock words)."""
    if moment is None:
        return ""
    return moment.astimezone().strftime("%H:%M")


def read_limit(agent: str, screen: str, now: Optional[datetime] = None) -> Optional[LimitReading]:
    """The usage-limit notice on ``agent``'s screen, or ``None``. The newest
    matching line wins (the foot of the screen)."""
    clock = now or datetime.now(timezone.utc)
    key = str(agent or "").lower()
    rule = _CLAUDE if key == "claude" else _CODEX if key == "codex" else None
    lines = _tail(screen)
    if rule is not None:
        for line in reversed(lines):
            if rule.search(line) and not _SHARE.search(line):
                return LimitReading(rule=f"{key}.usage_limit", line=line[:240], until=reset_moment(line, clock))
    for line in reversed(lines):
        found = _SHARE_NEAR.search(line) or (_SHARE.search(line) if re.search(r"limit|usage", line, re.I) else None)
        if found:
            share = min(100, int(found.group(1))) / 100.0
            return LimitReading(rule=f"{key or 'agent'}.usage_share", line=line[:240], share=share,
                                until=reset_moment(line, clock))
    return None


#: PG21: the harnesses whose notice is read, each with one documented line
#: (the fallback the Engines window names; not in this slice: gemini, pi).
DOCUMENTED: dict[str, str] = {
    "claude": "5-hour limit reached ∙ resets 2pm",
    "codex": "You've hit your usage limit. Upgrade to Pro or try again in 2 hours 13 minutes.",
}

_SHAPES = (
    (re.compile(r"\|\d{9,11}"), "|<epoch>"),
    (re.compile(r"\((?:[A-Za-z_]+/)+[A-Za-z_]+\)"), "(<zone>)"),
    (re.compile(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?\b", re.I), "<date>"),
    (re.compile(r"\b\d{1,2}(?::\d{2})?\s*[ap]\.?m\b\.?", re.I), "<time>"),
    (re.compile(r"\b\d{1,2}:\d{2}\b"), "<time>"),
    (re.compile(r"\b\d+(\s*(?:days?|hours?|hrs?|minutes?|mins?)\b)", re.I), r"<n>\1"),
    (re.compile(r"https?://[^\s)]+"), "<link>"),
)


def notice_shape(line: str) -> str:
    """A notice line with its times, dates, zone, waits and links replaced:
    what the harness says, not when or where (the record keeps the reset
    moment on its own)."""
    # The harness's own glyph before the line (⎿, ■, ●) is screen, not notice.
    text = re.sub(r"^[^\w'\"]+", "", str(line or "").strip())
    for pattern, word in _SHAPES:
        text = pattern.sub(word, text)
    return text[:240]


__all__ = ["DOCUMENTED", "LimitReading", "notice_shape", "read_limit", "reset_moment", "until_words"]
