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
"""
from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_GREETING = "Hello. What can I do?"


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

    def __post_init__(self) -> None:
        self.enabled = bool(self.enabled)
        self.aiphone_dir = str(self.aiphone_dir or "").strip()
        self.greeting = str(self.greeting or "").strip() or DEFAULT_GREETING
        self.allowed_numbers = _numbers(self.allowed_numbers)
        self.passphrase = str(self.passphrase or "").strip()
