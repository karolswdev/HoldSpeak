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
- ``daily_limit``: the Line (2026-10-29): the most calls HoldSpeak places in
  a day (0: no limit); incoming calls do not count.
- ``line``: the Line (docs/internal/betterment/line/LINE-DESIGN-2026-10-29.md):
  ``adapter`` (``line`` | ``ai-phone``; empty: the Line when baresip is
  found, else ai-phone when it is), ``where`` (``this_mac`` | ``node:<name>``)
  and ``account`` (``kind`` ``sip`` | ``telnyx``, ``user``, ``domain``,
  ``outbound``, ``password_ref``, ``codecs``). The SIP password and the
  Telnyx key are kept in the hub's keystore (``holdspeak/line/secrets.py``),
  never in this file; ``password_ref`` names the keystore slot.
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


LINE_ADAPTERS = ("", "line", "ai-phone")
LINE_ACCOUNT_KINDS = ("sip", "telnyx")
LINE_CODECS = ("opus", "PCMU", "PCMA", "L16")
DEFAULT_DAILY_LIMIT = 20


def default_line() -> dict:
    return {"adapter": "", "where": "this_mac", "account": {
        "kind": "sip", "user": "holdspeak", "domain": "", "outbound": "", "password_ref": "",
        "codecs": ["opus", "PCMU", "PCMA"]}}


def _line(value: object) -> dict:
    out = default_line()
    if not isinstance(value, dict):
        return out
    adapter = str(value.get("adapter") or "").strip().lower()
    out["adapter"] = adapter if adapter in LINE_ADAPTERS else ""
    where = str(value.get("where") or "").strip()
    if where == "this_mac" or (where.startswith("node:") and len(where) > 5):
        out["where"] = where
    account = value.get("account") if isinstance(value.get("account"), dict) else {}
    kind = str(account.get("kind") or "sip").strip().lower()
    out["account"]["kind"] = kind if kind in LINE_ACCOUNT_KINDS else "sip"
    for key in ("user", "domain", "outbound", "password_ref"):
        text = str(account.get(key) or "").strip()
        if text or key != "user":
            out["account"][key] = text
    codecs = account.get("codecs")
    if isinstance(codecs, str):
        codecs = [part.strip() for part in codecs.split(",")]
    if isinstance(codecs, (list, tuple)):
        picked = [c for c in (str(c).strip() for c in codecs) if c in LINE_CODECS]
        if picked:
            out["account"]["codecs"] = list(dict.fromkeys(picked))
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
    daily_limit: int = DEFAULT_DAILY_LIMIT
    line: dict = field(default_factory=default_line)

    def __post_init__(self) -> None:
        self.enabled = bool(self.enabled)
        self.aiphone_dir = str(self.aiphone_dir or "").strip()
        self.greeting = str(self.greeting or "").strip() or DEFAULT_GREETING
        self.allowed_numbers = _numbers(self.allowed_numbers)
        self.passphrase = str(self.passphrase or "").strip()
        self.phone_reach = _reach(self.phone_reach)
        self.phone_urgent_dnd = bool(self.phone_urgent_dnd)
        try:
            self.daily_limit = max(0, min(1000, int(self.daily_limit)))
        except (TypeError, ValueError):
            self.daily_limit = DEFAULT_DAILY_LIMIT
        self.line = _line(self.line)
