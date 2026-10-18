"""The Agents settings (Betterment AG5, DECISIONS #23).

``working_at_once``: the most agents HoldSpeak runs at one time (default 6;
the owner runs three to eight). Only an agent that works or needs him counts:
a done, quiet or stopped agent does not. A hand past the limit waits in the
queue and starts when an agent is free (``services.agent_hand_queue``).
"""
from __future__ import annotations

from dataclasses import dataclass

DEFAULT_WORKING_AT_ONCE = 6
MIN_WORKING_AT_ONCE = 1
MAX_WORKING_AT_ONCE = 20


def _clamp(value: object) -> int:
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return DEFAULT_WORKING_AT_ONCE
    return max(MIN_WORKING_AT_ONCE, min(MAX_WORKING_AT_ONCE, number))


@dataclass
class AgentsConfig:
    working_at_once: int = DEFAULT_WORKING_AT_ONCE

    def __post_init__(self) -> None:
        self.working_at_once = _clamp(self.working_at_once)
