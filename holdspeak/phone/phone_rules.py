"""Reach: when the desk may message or call him (design §6, by Control level).

``reach(level, kind, facts) -> Reach | Hold``, the same shape as Programs'
``program_rules.decide``. The table, row by row:

======================  =========  =================================  ==============================
kind                    Secure     Normal                             YOLO
======================  =========  =================================  ==============================
core_question           message    message; call after 10 min with    call at once when may_call,
                                   no reply when may_call             else message
step_red                message    message                            message; call when may_call
                                                                      and the Program is the night's
program_done            nothing    message                            message
heartbeat_security      message    call                               call, urgent
aftercare               nothing    message                            message
agent_question          message    message; call after 10 min when    call
                                   he is away (no desk 30 min)
======================  =========  =================================  ==============================

Always, in this order: his own word per kind (Settings ▸ Calls ▸ Phone:
Message · Call · Nothing) wins over the level's; a reply to the message
ends it (he answered); never twice in 5 minutes for the same thing; never a
call while a call is on (a message instead); quiet hours (the desk's one
quiet-hours store, Settings ▸ Rhythm) queue a message and let only an urgent
call ring; urgent rings through Do Not Disturb only when he allowed it.

The etiquette is agentring's skill (``skills/agentring/SKILL.md``): pick the
lightest channel; a call only when it is urgent or a message got no answer;
never treat silence as consent. Here it is code, not only words.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Union

LEVELS = ("secure", "normal", "yolo")
_DESK_MODES = {"safe": "secure", "secure": "secure", "neutral": "normal", "normal": "normal", "yolo": "yolo"}

KINDS = ("core_question", "step_red", "program_done", "heartbeat_security", "aftercare", "agent_question")
#: The words his Settings may set per kind.
WORDS = ("message", "call", "nothing")

#: Minutes a message waits for a reply before a call may follow it.
CALL_AFTER_MINUTES = 10
#: Minutes without the desk in front of him before he counts as away.
AWAY_MINUTES = 30
#: Never twice in this many minutes for the same thing.
REPEAT_MINUTES = 5


@dataclass(frozen=True)
class Reach:
    """Reach him on ``channel`` (``message`` or ``call``) under ``rule``."""

    channel: str
    rule: str
    urgent: bool = False

    @property
    def held(self) -> bool:
        return False


@dataclass(frozen=True)
class Hold:
    """Do not reach him now. ``queued``: a message waits (quiet hours)."""

    reason: str
    rule: str
    queued: bool = False

    @property
    def held(self) -> bool:
        return True


Outcome = Union[Reach, Hold]


def level_of(value: Any) -> str:
    return _DESK_MODES.get(str(value or "").strip().lower(), "normal")


def table(level: str, kind: str, facts: Mapping[str, Any]) -> tuple[str, str]:
    """The level's own word for ``kind``: ``(word, rule)``; word is
    ``nothing``, ``message``, ``call`` or ``call_urgent``."""
    may_call = bool(facts.get("may_call"))
    waited = float(facts.get("minutes_without_reply") or 0) >= CALL_AFTER_MINUTES and bool(facts.get("messaged"))
    if kind == "core_question":
        if level == "secure":
            return "message", "Secure: a core question is a message"
        if level == "normal":
            if may_call and waited:
                return "call", f"Normal: no reply in {CALL_AFTER_MINUTES} minutes and the program may call"
            return "message", "Normal: a core question is a message first"
        if may_call:
            return "call", "YOLO: a core question rings at once when the program may call"
        return "message", "YOLO: the program may not call, so a message"
    if kind == "step_red":
        if level == "yolo" and may_call and facts.get("night_program"):
            return "call", "YOLO: a red step of the night's program rings when it may call"
        return "message", f"{level.capitalize()}: a red step is a message"
    if kind == "program_done":
        if level == "secure":
            return "nothing", "Secure: a finished program waits on the desk"
        return "message", f"{level.capitalize()}: a finished program is a message"
    if kind == "heartbeat_security":
        if level == "secure":
            return "message", "Secure: a security or data-loss finding is a message"
        if level == "normal":
            return "call", "Normal: a security or data-loss finding rings"
        return "call_urgent", "YOLO: a security or data-loss finding rings, urgent"
    if kind == "aftercare":
        if level == "secure":
            return "nothing", "Secure: a meeting's asks wait on the desk"
        return "message", f"{level.capitalize()}: a meeting's asks are a message"
    if kind == "agent_question":
        if level == "secure":
            return "message", "Secure: an agent's question is a message"
        if level == "normal":
            if waited and facts.get("away"):
                return "call", f"Normal: no reply in {CALL_AFTER_MINUTES} minutes and he is away from the desk"
            return "message", "Normal: an agent's question is a message first"
        return "call", "YOLO: an agent's question the desk could not draft rings"
    return "nothing", "no rule for this kind"


def reach(level: Any, kind: str, facts: Optional[Mapping[str, Any]] = None) -> Outcome:
    """One reach decision for ``kind`` at ``level`` with ``facts``:

    ``may_call``, ``messaged`` (a message about it went out),
    ``minutes_without_reply``, ``replied`` (he answered it), ``away``,
    ``night_program``, ``recent_minutes`` (since the last reach about the
    same thing), ``call_active``, ``quiet`` (inside quiet hours),
    ``urgent_dnd`` (he lets urgent ring through Do Not Disturb), ``word``
    (his own word for the kind: message, call, nothing)."""
    facts = dict(facts or {})
    level = level_of(level)
    if kind not in KINDS:
        return Hold("there is no rule to reach him for this", "no rule")
    word, rule = table(level, kind, facts)
    own = str(facts.get("word") or "").strip().lower()
    if own in WORDS:
        if own == "nothing":
            word, rule = "nothing", "his own word for this kind: nothing"
        elif own == "message":
            word, rule = "message", "his own word for this kind: a message"
        elif own == "call" and word not in ("call", "call_urgent"):
            word, rule = "call", "his own word for this kind: a call"
    if word == "nothing":
        return Hold("the rule reaches him for this only on the desk", rule)
    if facts.get("replied"):
        return Hold("he answered the message", "a reply ends the reach")
    recent = facts.get("recent_minutes")
    if recent is not None and float(recent) < REPEAT_MINUTES:
        return Hold(f"he was reached about this {int(float(recent))} minutes ago",
                    f"never twice in {REPEAT_MINUTES} minutes for the same thing")
    urgent = word == "call_urgent"
    channel = "call" if word in ("call", "call_urgent") else "message"
    if channel == "call" and facts.get("call_active"):
        channel, urgent, rule = "message", False, "a call is on: a message instead"
    if facts.get("quiet"):
        if channel == "message":
            return Hold("quiet hours: the message waits for the morning", "quiet hours queue messages", queued=True)
        if not urgent:
            return Hold("quiet hours: only an urgent call rings", "quiet hours let only urgent calls ring",
                        queued=True)
    return Reach(channel, rule, urgent=urgent)


__all__ = [
    "AWAY_MINUTES", "CALL_AFTER_MINUTES", "Hold", "KINDS", "LEVELS", "REPEAT_MINUTES", "Reach", "WORDS",
    "level_of", "reach", "table",
]
