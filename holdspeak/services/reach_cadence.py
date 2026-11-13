"""Cadence's commands and buttons on the one Telegram chat.

The one reach poll (``telegram_reach``) hands a slash command or a Cadence
button here. This module reads and writes Cadence's loops and answers with
plain ``Message`` structures; it sends nothing itself. The one writer and the
one transport send them. The paired chat of reach is the only chat.

(The Cadence surface had its own transport, sender, pairing and poll loop:
``holdspeak/_parked/cadence_telegram_20261113.py``.)
"""
from __future__ import annotations

from typing import Any, Optional

from .telegram_writer import Button, Message

COMMANDS = ("brief", "loops", "closeout", "status")
HELP_WORDS = "Commands: /brief /loops /closeout /status"
NOTHING_WORDS = "Nothing pressing right now."
START_WORDS = "This chat is connected to your desk. HoldSpeak sends what waits on you here."
#: Cadence's own button verbs (callback data ``<verb>:<loop id>``).
BUTTON_VERBS = ("snooze", "done", "kill", "killyes", "killno")


def loop_buttons(loop: Any) -> tuple[tuple[Button, ...], ...]:
    return ((Button("Snooze 1d", f"snooze:{loop.id}"), Button("Done", f"done:{loop.id}"),
             Button("Kill", f"kill:{loop.id}")),)


def _open_loops(db: Any) -> list[Any]:
    return [loop for loop in db.cadence.list_loops() if not loop.needs_review]


def loop_message(loop: Any) -> Message:
    return Message(head=str(loop.title), lines=(f"{loop.source_type} · {loop.stale_score:.0f}",),
                   buttons=loop_buttons(loop))


def nudge_message(loop: Any) -> Message:
    """A due loop, pushed by the Cadence tick."""
    return Message(head=str(loop.title), lines=(f"{loop.stale_score:.0f}",), buttons=loop_buttons(loop))


def brief_message(db: Any) -> Message:
    """The day's brief: its headline and first lines, with the buttons of
    the first open loop."""
    from .monday_brief_service import brief_lines, todays_brief

    brief = todays_brief(db)
    loops = _open_loops(db)
    return Message(head=str(brief.headline),
                   lines=tuple(f"{index}. {line}" for index, line in enumerate(brief_lines(brief), 1)),
                   buttons=loop_buttons(loops[0]) if loops else ())


def status_message(db: Any) -> Message:
    counts: dict[str, int] = {}
    for loop in db.cadence.list_loops(include_terminal=True):
        counts[loop.status] = counts.get(loop.status, 0) + 1
    line = ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"
    return Message(head="Cadence status", lines=(f"Loops: {line}",))


def command(db: Any, name: str) -> tuple[str, list[Message]]:
    """``(action, messages)`` for one slash command from the owner chat."""
    if name == "start":
        return "start", [Message(lines=(START_WORDS,))]
    if name in ("brief", "loops"):
        loops = _open_loops(db)
        if not loops:
            return name, [Message(lines=(NOTHING_WORDS,))]
        if name == "brief":
            return name, [brief_message(db)]
        return name, [loop_message(loop) for loop in loops[:5]]
    if name == "closeout":
        from ..cadence.closeout import build_closeout, render_closeout_text

        return name, [Message(lines=tuple(render_closeout_text(build_closeout(db)).splitlines()))]
    if name == "status":
        return name, [status_message(db)]
    return "help", [Message(lines=(HELP_WORDS,))]


def button(db: Any, data: str, pending_kill: set[str]) -> tuple[str, str, Optional[Message]]:
    """``(action, the words for the tap, a message or None)`` for one Cadence
    button. Kill is destructive: it asks one time more."""
    act, _, loop_id = data.partition(":")
    loop = db.cadence.get_loop(loop_id) if loop_id else None
    if loop is None:
        return "missing", "Loop is gone.", None
    if act == "snooze":
        from datetime import timedelta

        from holdspeak.timestamps import utc_iso, utc_now

        db.cadence.snooze(loop_id, utc_iso(utc_now() + timedelta(hours=24)))
        return act, "Snoozed 1 day.", None
    if act == "done":
        db.cadence.set_status(loop_id, "closed")
        return act, "Marked done.", None
    if act == "kill":
        pending_kill.add(loop_id)
        return "kill_confirm", "", Message(question=f"Kill {loop.title} permanently?", buttons=(
            (Button("Cancel", f"killno:{loop_id}"), Button("Yes, kill it", f"killyes:{loop_id}")),))
    if act == "killyes":
        if loop_id not in pending_kill:
            return "kill_expired", "Expired. Tap Kill again.", None
        pending_kill.discard(loop_id)
        db.cadence.set_status(loop_id, "killed")
        return act, "Killed.", None
    if act == "killno":
        pending_kill.discard(loop_id)
        return "kill_cancelled", "Kept.", None
    return "unknown", "", None
