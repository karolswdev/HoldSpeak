"""What the owner asks the bot, and what waits on him, as messages.

One place for the words of ``/waiting``, ``/today``, ``/quiet``, ``/status``
and ``/help``, for the notice of a thing that waits, and for a held tool
call. Every function here takes read answers and returns a
:class:`~holdspeak.services.telegram_writer.Message`: the one writer draws
it, the one transport sends it. Nothing here decides what waits: that is the
Needs you membership (``desk.needs_you``), read through :class:`Reads`.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta
from typing import Any, Mapping, Optional, Sequence

from .telegram_writer import Button, Message

#: The command menu the bot shows (``setMyCommands``).
MENU = (
    ("waiting", "What waits on you"),
    ("today", "Your day"),
    ("quiet", "No messages for a time"),
    ("status", "Your desk and this chat"),
    ("help", "What you can send"),
)
#: Cadence's commands: in the menu only when Cadence is on; always in /help.
CADENCE_MENU = (
    ("brief", "Your brief"),
    ("loops", "Your open loops"),
    ("closeout", "Close the day"),
)
COMMANDS = tuple(name for name, _words in MENU)
WAITING_MAX = 8                 # things shown by /waiting; the rest are one line
CHAT_WINDOW_SECONDS = 600       # the chat's budget: this window …
CHAT_MAX = 6                    # … holds at most this many messages that notify
DOWN_SECONDS = 600              # a desk that did not run this long says "Back at"
CALLBACK = "r1"                 # the one button-data scheme (telegram_reach.CALLBACK)

NOTHING_WAITS = "Nothing waits on you."
OPEN_DESK = "Open your desk"
QUIET_HELP = "Send /quiet 2h, /quiet (until the morning), or /quiet off."
HELD_GONE_WORDS = "This call is gone. Nothing was decided."
HELD_CHANGED_WORDS = "This call changed. Nothing was decided. Open it on your desk."
HELD_RUNS_WORDS = "It runs one time."
NOT_READ_WORDS = "Your desk could not read this now. Try again."

#: Needs you rows of these sources travel one by one as a notice with Open.
NOTICE_SOURCES = ("send", "engine")
#: Needs you rows of these sources are in the morning brief, not one by one.
BRIEF_SOURCES = ("commitment", "people_commitment", "action_item", "decision")

_QUIET = re.compile(r"^(\d{1,3})\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes)$")


class Reads:
    """The reads a command needs, from the hub's own operations. A test
    gives its own object with the same four methods."""

    def needs_you(self, principal: Any) -> dict[str, Any]:
        from holdspeak.runtime.composition import current

        root = current()
        return dict(root.operations.invoke(
            principal, "desk.needs_you", {},
            held={"door_upcoming": getattr(root.door_service, "upcoming", None)}, shape="web"))

    def today(self, principal: Any) -> dict[str, Any]:
        from holdspeak.runtime.composition import current

        return dict(current().operations.invoke(principal, "today.get", {}, shape="web"))

    def held_calls(self) -> list[Any]:
        from .thread_service import ThreadService

        return list(ThreadService.waiting_tool_calls())

    def desk_name(self) -> str:
        import platform

        return (platform.node() or "this Mac").split(".")[0]


def menu(cadence: bool = False) -> list[dict[str, str]]:
    rows = MENU + (CADENCE_MENU if cadence else ())
    return [{"command": name, "description": words} for name, words in rows]


def menu_mark(commands: Sequence[Mapping[str, str]]) -> str:
    text = "|".join(f"{row['command']}={row['description']}" for row in commands)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def command_button(name: str, words: str) -> Button:
    return Button(words, f"{CALLBACK}|cmd|{name}")


# ── what waits ───────────────────────────────────────────────────────


def waiting_rows(needs: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The members of Needs you, in its own order (membership is decided
    once, by Needs you; this takes its members and nothing else)."""
    members = {str(row.get("ref")) for row in needs.get("members") or [] if isinstance(row, dict)}
    rows = []
    for row in needs.get("items") or []:
        if not isinstance(row, dict):
            continue
        ref = str(row.get("ref") if row.get("ref") is not None else row.get("id") or "")
        if not members or ref in members:
            rows.append({**row, "ref": ref})
    return rows


def waits_count(needs: Mapping[str, Any], held: int = 0) -> int:
    try:
        return int(needs.get("count") or 0) + held
    except (TypeError, ValueError):
        return len(waiting_rows(needs)) + held


def count_words(count: int) -> str:
    return "1 thing waits on you" if count == 1 else f"{count} things wait on you"


def _sentence(words: Any) -> str:
    text = " ".join(str(words or "").replace("_", " ").split())
    return text[:1].upper() + text[1:].lower() if text.isupper() else text


def _since(since: Any, now: datetime) -> str:
    from .telegram_reach import _waits

    words = _waits(since, now)
    return words[:1].upper() + words[1:] if words else ""


def row_rev(row: Mapping[str, Any]) -> str:
    """One mark for what a row says: a row that says another thing is new."""
    text = "|".join(str(row.get(key) or "") for key in ("title", "why", "dueAt"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def row_message(row: Mapping[str, Any], link: Optional[str], now: datetime) -> Message:
    """One waiting thing as the desk row says it: what waits, who or what
    from, since when; then the way to it."""
    from_words = " · ".join(part for part in (
        str(row.get("projectName") or row.get("group") or "").strip(),
        str(row.get("personName") or row.get("person_name") or "").strip()) if part)
    lines = [part for part in (from_words, _sentence(row.get("why")), _since(row.get("since"), now)) if part]
    return Message(head=str(row.get("title") or "A thing waits"), lines=tuple(lines), link=link,
                   link_words=OPEN_DESK, desk_words="Open it on your desk.")


def more_message(count: int, link: Optional[str]) -> Message:
    words = "and 1 more on your desk." if count == 1 else f"and {count} more on your desk."
    return Message(lines=(words,), link=link, link_words=OPEN_DESK)


def held_message(details: Mapping[str, Any], key: str) -> Message:
    """A tool call that waits: what it will write, then Deny and Allow once.
    Deny is first: Allow is never the first button."""
    facts = tuple((str(fact.get("label") or ""), str(fact.get("value") or ""))
                  for fact in details.get("facts") or [] if isinstance(fact, dict))
    return Message(head="A tool call waits for you", question=str(details.get("words") or "Tool call"),
                   facts=facts, closing=(HELD_RUNS_WORDS,),
                   buttons=((Button("Deny", f"{CALLBACK}|held|{key}|d"),
                             Button("Allow once", f"{CALLBACK}|held|{key}|a")),))


def held_settled(details_words: str, words: str) -> Message:
    return Message(head="A tool call waited for you", lines=(details_words,) if details_words else (),
                   closing=(words,))


# ── the day ──────────────────────────────────────────────────────────


def _local(stamp: Any) -> Optional[datetime]:
    try:
        at = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return at.astimezone() if at.tzinfo is not None else at


def today_lines(today: Mapping[str, Any], needs: Mapping[str, Any], now: datetime, held: int = 0) -> list[str]:
    """The day in six lines at most: the meetings ahead with their times,
    how many things wait, what is due today."""
    local = now.astimezone()
    day = dict(today.get("day") or {})
    ahead = []
    for event in day.get("upcoming") or []:
        at = _local((event or {}).get("starts_at"))
        if at is None or at.date() != local.date() or at.replace(tzinfo=None) < local.replace(tzinfo=None):
            continue
        ahead.append((at, str(event.get("title") or "Meeting")))
    ahead.sort(key=lambda pair: pair[0])
    lines = [f"{at.strftime('%H:%M')} {title}" for at, title in ahead[:3]]
    if len(ahead) > 3:
        lines.append(f"and {len(ahead) - 3} more meetings")
    if not ahead:
        lines.append("No meetings ahead today.")
    count = waits_count(needs, held)
    lines.append(count_words(count) + "." if count else NOTHING_WAITS)
    today_mark = local.strftime("%Y-%m-%d")
    due = [row for row in waiting_rows(needs)
           if str(row.get("dueAt") or "")[:10] == today_mark or str(row.get("why") or "").upper() == "DUE TODAY"]
    if due:
        lines.append("1 is due today." if len(due) == 1 else f"{len(due)} are due today.")
    return lines[:6]


def today_message(today: Mapping[str, Any], needs: Mapping[str, Any], link: Optional[str], now: datetime,
                  held: int = 0) -> Message:
    local = now.astimezone()
    return Message(head=f"Today · {local.strftime('%a, %b')} {local.day}",
                   lines=tuple(today_lines(today, needs, now, held)), link=link, link_words=OPEN_DESK,
                   buttons=((command_button("waiting", "What waits"),),))


# ── quiet, status, help ──────────────────────────────────────────────


def parse_quiet(arg: str, now: datetime, morning: datetime) -> Optional[datetime]:
    """``2h`` / ``30m`` to a time; nothing to ``morning`` (the end of quiet
    hours); ``off`` to the past (quiet ends now). None: not understood."""
    words = " ".join(str(arg or "").lower().split())
    if not words:
        return morning
    if words in ("off", "end", "stop"):
        return now - timedelta(seconds=1)
    match = _QUIET.match(words.replace(" ", ""))
    if not match:
        return None
    amount = int(match.group(1))
    if amount <= 0:
        return None
    span = timedelta(hours=amount) if match.group(2).startswith("h") else timedelta(minutes=amount)
    return now + min(span, timedelta(hours=72))


def until_words(until: datetime, now: datetime) -> str:
    local, here = until.astimezone(), now.astimezone()
    clock = local.strftime("%H:%M")
    if local.date() == here.date():
        return clock
    if local.date() == (here + timedelta(days=1)).date():
        return f"{clock} tomorrow"
    return f"{clock} on {local.strftime('%a, %b')} {local.day}"


def quiet_message(until: Optional[datetime], now: datetime) -> Message:
    if until is None or until <= now:
        return Message(head="Quiet is off", lines=("Messages come as they did before.",))
    return Message(head=f"Quiet until {until_words(until, now)}",
                   lines=("No message comes until then. What waits is kept and comes after.",
                          "Send /quiet off to end it."))


def status_message(*, desk: str, health_words: str, count: int, mode_words: str,
                   quiet_until: Optional[datetime], quiet_now: bool, last_said: Optional[str],
                   now: datetime, loops: Optional[str] = None) -> Message:
    if quiet_until is not None and quiet_until > now:
        quiet = f"Quiet until {until_words(quiet_until, now)}."
    elif quiet_now:
        quiet = "Quiet hours now."
    else:
        quiet = "Not quiet now."
    return Message(head=f"Your desk on {desk}", lines=(
        health_words,
        count_words(count) + "." if count else NOTHING_WAITS,
        f"Messages: {mode_words}.",
        quiet,
        f"Last message here: {last_said}." if last_said else "No message here since the desk started.",
    ) + ((loops,) if loops else ()), buttons=((command_button("waiting", "What waits"),),))


def help_message(cadence: bool = False) -> Message:
    lines = [f"/{name} · {words}" for name, words in MENU]
    lines += [f"/{name} · {words}" for name, words in CADENCE_MENU]
    return Message(head="What you can send", lines=tuple(lines), closing=(
        "To answer a question: press its button, or reply to its message.",
        "Only this chat can answer.",
    ))


def back_message(now: datetime, count: int) -> Message:
    clock = now.astimezone().strftime("%H:%M")
    words = "1 thing waited." if count == 1 else f"{count} things waited."
    return Message(lines=(f"Back at {clock}. {words}",), buttons=((command_button("waiting", "What waits"),),))


def notice_key(row: Mapping[str, Any]) -> str:
    return f"notice:{row.get('ref')}:{row_rev(row)}"


def failed_meeting_rows(needs: Mapping[str, Any]) -> list[dict[str, Any]]:
    """A meeting whose summary was not made, as a row that can travel."""
    rows = []
    for meeting in needs.get("failedMeetings") or []:
        if not isinstance(meeting, dict) or not meeting.get("id"):
            continue
        rows.append({"ref": f"meeting:{meeting['id']}", "source": "meeting",
                     "title": f"Summary not made: {meeting.get('title') or 'a meeting'}",
                     "why": str(meeting.get("why") or meeting.get("intel_status_detail") or ""),
                     "since": meeting.get("since") or meeting.get("ended_at")})
    return rows


def notice_rows(needs: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The waiting things that travel one by one as a notice with Open: a
    Send that waits for his press, a job that did not run, a summary that
    was not made. (A Program or agent question has its own message with
    its answer buttons; a thing that is due is in the morning brief.)"""
    rows = [row for row in waiting_rows(needs) if str(row.get("source") or row.get("kind") or "") in NOTICE_SOURCES]
    return rows + failed_meeting_rows(needs)
