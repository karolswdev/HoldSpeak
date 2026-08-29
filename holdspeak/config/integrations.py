"""Integration configuration: Telegram, Rails observer, Cadence (HS-117-12).

Extracted from the monolithic ``holdspeak/config.py``.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlsplit


CALENDAR_REFRESH_SECONDS = 900


@dataclass
class CalendarSource:
    """One owner-configured ICS source (HS-146-01)."""

    id: str = ""
    label: str = ""
    url: str = ""
    enabled: bool = True

    def __post_init__(self) -> None:
        self.id = str(self.id or "").strip()
        self.label = str(self.label or "").strip()
        self.url = str(self.url or "").strip()
        self.enabled = bool(self.enabled)


@dataclass
class CalendarConfig:
    """Owner-configured ICS sources (HS-146-01, multi-source)."""

    sources: list[CalendarSource] = field(default_factory=list)

    def __post_init__(self) -> None:
        coerced: list[CalendarSource] = []
        for item in (self.sources or []):
            if isinstance(item, CalendarSource):
                coerced.append(item)
            elif isinstance(item, dict):
                coerced.append(CalendarSource(**{
                    k: v for k, v in item.items()
                    if k in ("id", "label", "url", "enabled")
                }))
        self.sources = coerced

    @property
    def subscription(self) -> str:
        """Bridge property: returns the first source's URL for callers
        that still read the old single-source field."""
        if self.sources:
            return self.sources[0].url
        return ""


def validate_calendar_subscription(value: object) -> str:
    """Normalize and validate the one calendar source at the write boundary.

    Plain text is a local path.  Anything carrying a URI scheme must be an
    ordinary HTTPS URL with a host and without embedded credentials or a
    fragment.  Fetch mechanics deliberately live in the later ingest slice.
    """
    if not isinstance(value, str):
        raise ValueError("calendar.subscription must be a string")
    source = value.strip()
    if not source:
        return ""

    parsed = urlsplit(source)
    # Windows drive-letter paths are local files even though urlsplit sees a
    # one-character scheme.  They remain useful in shared config fixtures.
    is_windows_path = (
        len(parsed.scheme) == 1
        and len(source) >= 3
        and source[1] == ":"
        and source[2] in {"/", "\\"}
    )
    if parsed.scheme and not is_windows_path:
        if parsed.scheme.lower() != "https":
            raise ValueError("calendar.subscription must be a file path or HTTPS URL")
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("calendar.subscription has an invalid HTTPS port") from exc
        if not parsed.hostname:
            raise ValueError("calendar.subscription HTTPS URL must include a host")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("calendar.subscription HTTPS URL cannot include userinfo")
        if parsed.fragment:
            raise ValueError("calendar.subscription HTTPS URL cannot include a fragment")
        if port is not None and not (0 < port <= 65535):
            raise ValueError("calendar.subscription has an invalid HTTPS port")
    return source


def _source_label(source: CalendarSource) -> str:
    """HS-146-04: resolved label for rail provenance chips.

    Fallback chain: source.label -> hostname of source.url -> "LOCAL".
    """
    if source.label:
        return source.label
    url = source.url.strip()
    if url:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        if hostname:
            return hostname
    return "LOCAL"


def calendar_subscription_revision(subscription: object) -> str:
    """Return the stable source fingerprint used by the calendar projection."""
    normalized = validate_calendar_subscription(subscription)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def calendar_source_revision(source_id: str, url: str) -> str:
    """Per-source projection fingerprint (HS-146-01).

    The source id enters the hash so two sources pointing at the same URL
    get independent projection namespaces.
    """
    normalized = validate_calendar_subscription(url)
    payload = f"{source_id}\0{normalized}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def calendar_sources_summary(sources: list[CalendarSource]) -> list[dict[str, object]]:
    """Produce one summary dict per source for Settings transports."""
    result: list[dict[str, object]] = []
    for source in sources:
        base = calendar_subscription_summary(source.url)
        base["id"] = source.id
        base["label"] = source.label
        base["enabled"] = source.enabled
        result.append(base)
    return result


def calendar_subscription_summary(subscription: object) -> dict[str, object]:
    """Produce the non-persisted source/egress fact for Settings transports."""
    try:
        source = validate_calendar_subscription(subscription)
    except ValueError:
        return {
            "kind": "invalid",
            "host": "",
            "refresh_seconds": CALENDAR_REFRESH_SECONDS,
            "egress": False,
        }
    if not source:
        return {
            "kind": "disabled",
            "host": "",
            "refresh_seconds": CALENDAR_REFRESH_SECONDS,
            "egress": False,
        }
    parsed = urlsplit(source)
    if parsed.scheme.lower() == "https":
        return {
            "kind": "https",
            "host": str(parsed.hostname or "").lower(),
            "refresh_seconds": CALENDAR_REFRESH_SECONDS,
            "egress": True,
        }
    return {
        "kind": "file",
        "host": "",
        "refresh_seconds": CALENDAR_REFRESH_SECONDS,
        "egress": False,
    }


@dataclass
class ThoughtsConfig:
    """The AI destination used by Thought Workbench refinement turns.

    ``None`` inherits the built-in this-device target. The pointer names an
    InferenceTarget; credentials remain in the target's owner-only key slot.
    """

    inference_target_id: Optional[str] = None

    def __post_init__(self) -> None:
        self.inference_target_id = (
            str(self.inference_target_id or "").strip() or None
        )


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
