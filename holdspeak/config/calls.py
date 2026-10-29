"""Calls (docs/internal/betterment/calls/CALLS-DESIGN-2026-10-28.md §6).

HoldSpeak drives the owner's own ai-phone install (a separate program, the
phone half) and owns each turn of a call.

- ``enabled``: the hub listens for calls while the ai-phone daemon runs.
- ``aiphone_dir``: the ai-phone checkout; the hub runs
  ``uv run --project <dir> ai-phone``. Empty: ``ai-phone`` on ``PATH``.
- ``greeting``: said after the passphrase.
- ``allowed_numbers``: callers that may reach the passphrase (empty: any);
  the first is his own number ("Call me").
- ``passphrase``: spoken first on every call. The settings read never shows
  it (``passphrase_set``). Without one a call has no hands.
- ``phone_reach``: Phone (2026-10-28, Settings ▸ Calls ▸ Phone ▸ Reach you):
  his own word per kind (``message``, ``call`` or ``nothing``) over the
  level's (``holdspeak/phone/phone_rules.py``); a kind not named follows the
  level.
- ``phone_urgent_dnd``: an urgent call may ring through Do Not Disturb (off
  until Apple grants the critical-alerts entitlement).
"""
from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_GREETING = "Hello. What can I do?"
PHONE_REACH_KINDS = ("core_question", "step_red", "program_done", "heartbeat_security", "aftercare", "agent_question")
PHONE_REACH_WORDS = ("message", "call", "nothing")


def _reach(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, str] = {}
    for kind, word in value.items():
        kind, word = str(kind or "").strip(), str(word or "").strip().lower()
        if kind in PHONE_REACH_KINDS and word in PHONE_REACH_WORDS:
            out[kind] = word
    return out


def _numbers(value: object) -> list[str]:
    if isinstance(value, str):
        value = [part for part in value.replace(";", ",").split(",")]
    if not isinstance(value, (list, tuple)):
        return []
    out: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and text not in out:
            out.append(text)
    return out


@dataclass
class CallsConfig:
    enabled: bool = False
    aiphone_dir: str = ""
    greeting: str = DEFAULT_GREETING
    allowed_numbers: list[str] = field(default_factory=list)
    passphrase: str = ""
    phone_reach: dict[str, str] = field(default_factory=dict)
    phone_urgent_dnd: bool = False

    def __post_init__(self) -> None:
        self.enabled = bool(self.enabled)
        self.aiphone_dir = str(self.aiphone_dir or "").strip()
        self.greeting = str(self.greeting or "").strip() or DEFAULT_GREETING
        self.allowed_numbers = _numbers(self.allowed_numbers)
        self.passphrase = str(self.passphrase or "").strip()
        self.phone_reach = _reach(self.phone_reach)
        self.phone_urgent_dnd = bool(self.phone_urgent_dnd)
