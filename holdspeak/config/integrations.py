"""Integration configuration: Telegram, Rails observer, Cadence (HS-117-12).

Extracted from the monolithic ``holdspeak/config.py``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CadenceConfig:
    """The Cadence Engine (CAD-1) -- OFF BY DEFAULT.

    When `enabled` is False the runtime starts no cadence thread and behaves
    identically to a build without cadence. `pressure` scales policy *timings*
    only (never what is nudged or any safety gate). `tick_interval_seconds` is how
    often the in-runtime loop projects + scores. Quiet hours are default-on.
    """

    enabled: bool = False
    pressure: str = "normal"  # gentle | normal | aggressive (timing multiplier only)
    use_llm: bool = False     # CAD-7: LLM-DRAFT next actions (fail-closed to deterministic)
    tick_interval_seconds: int = 300
    quiet_hours_start: int = 22  # local hour [0..23]
    quiet_hours_end: int = 8
    max_nudges_per_day: int = 12

    def __post_init__(self) -> None:
        if self.pressure not in ("gentle", "normal", "aggressive"):
            self.pressure = "normal"
        self.tick_interval_seconds = max(30, int(self.tick_interval_seconds))
        self.quiet_hours_start = int(self.quiet_hours_start) % 24
        self.quiet_hours_end = int(self.quiet_hours_end) % 24
        self.max_nudges_per_day = max(0, int(self.max_nudges_per_day))


@dataclass
class TelegramConfig:
    """The Cadence Telegram surface (CAD-4) -- OFF BY DEFAULT.

    `bot_token` is a CREDENTIAL -- it is never logged or written into a message/row;
    it is joined in memory only at the moment of an API call. `allowed_chat_ids` is the
    hard pairing allow-list: only these chats may read anything. `pairing_code` (if set)
    lets a chat self-pair via `/pair <code>`. With `enabled` False or no token, the
    surface is inert (no poller, no send).
    """

    enabled: bool = False
    bot_token: str = ""
    allowed_chat_ids: list[str] = field(default_factory=list)
    pairing_code: str = ""

    def __post_init__(self) -> None:
        self.bot_token = str(self.bot_token or "").strip()
        self.pairing_code = str(self.pairing_code or "").strip()
        self.allowed_chat_ids = [str(c).strip() for c in (self.allowed_chat_ids or []) if str(c).strip()]

    @property
    def is_active(self) -> bool:
        """Live only when explicitly enabled AND a token is present."""
        return bool(self.enabled and self.bot_token)


@dataclass
class RailsObserverConfig:
    """The ambient dw observer (HS-88-03) -- OFF BY DEFAULT.

    When `enabled` is False the runtime starts no observer loop and
    behaves identically to a build without it. When on, a local model
    (the RuntimeProfile named by `profile_id`, else the hub default)
    summarizes a bounded `dw events` tail into a journal note. The
    observer is READ-ONLY: it never writes to the rails; anything it
    would DO is a proposal through the actuator flow.
    """

    enabled: bool = False
    # The ONE pointer for the observer's summarizer: an InferenceTarget id
    # in the profiles table. None = hub default (HS-112-01 sentinel rule).
    profile_id: Optional[str] = None
    poll_seconds: int = 30
    tail: int = 20  # how many recent rail events to consider per tick

    def __post_init__(self) -> None:
        self.profile_id = str(self.profile_id or "").strip() or None
