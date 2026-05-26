"""Pure AI PI companion state and LCD-priority contract.

This module deliberately does not talk to ESPHome or HoldSpeak. It is the
small product-state layer HS-22-01 needs before the bridge starts polling
`/api/companion/status` or wiring new gestures.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from bridge.lcd import (
    ERROR_FLASH_MS,
    LINK_OFFLINE,
    LINK_ONLINE,
    SESSION_BUSY_FLASH_MS,
)

AGENT_STALE_AFTER_S = 120
STALE_CLEAR_FLASH_MS = 3000


class CompanionState(str, Enum):
    """Product-level states the physical companion can present."""

    DISCONNECTED = "disconnected"
    IDLE_CONNECTED = "idle_connected"
    MEETING_RECORDING = "meeting_recording"
    AGENT_WAITING = "agent_waiting"
    REPLY_CAPTURE = "reply_capture"
    TRANSCRIBING = "transcribing_rewrite_pending"
    ERROR_BUSY = "error_busy"
    STALE_CLEARED = "stale_cleared"


class LcdLifetime(str, Enum):
    """How long a zone paint is expected to remain meaningful."""

    STICKY = "sticky"
    FLASH = "flash"
    PERSIST_UNTIL_REPLACED = "persist_until_replaced"
    CLEAR = "clear"


class CompanionOwner(str, Enum):
    """Runtime component responsible for declaring or clearing a state."""

    BRIDGE = "bridge"
    FIRMWARE = "firmware"
    HOLDSPEAK = "holdspeak"


@dataclass(frozen=True)
class StateContract:
    state: CompanionState
    owner: CompanionOwner
    trigger: str
    display: str
    clear: str


@dataclass(frozen=True)
class ZonePaint:
    text: str
    lifetime: LcdLifetime
    ttl_ms: int = 0


@dataclass(frozen=True)
class LcdPlan:
    primary_state: CompanionState
    top_right: ZonePaint
    middle: ZonePaint
    bottom: ZonePaint


@dataclass(frozen=True)
class CompanionSignals:
    """Inputs used to resolve LCD priority.

    The fields mirror facts HoldSpeak, the bridge, or firmware already know
    today. Future polling/gesture stories should adapt runtime payloads into
    this shape, then paint the returned `LcdPlan`.
    """

    connected: bool = True
    meeting_recording: bool = False
    agent_waiting: bool = False
    agent_label: str = "Agent"
    agent_question: str = ""
    agent_age_s: float | None = None
    reply_capture: bool = False
    transcribing: bool = False
    transcript_flash: str = ""
    busy: bool = False
    error_text: str = ""


STATE_CONTRACTS: dict[CompanionState, StateContract] = {
    CompanionState.DISCONNECTED: StateContract(
        state=CompanionState.DISCONNECTED,
        owner=CompanionOwner.BRIDGE,
        trigger="HoldSpeak WebSocket is connecting or offline.",
        display="Top-right link icon shows offline/connecting; bottom keeps last sticky state if available.",
        clear="Handshake succeeds and the bridge republishes link/activity.",
    ),
    CompanionState.IDLE_CONNECTED: StateContract(
        state=CompanionState.IDLE_CONNECTED,
        owner=CompanionOwner.BRIDGE,
        trigger="Bridge and HoldSpeak are connected with no active meeting or agent question.",
        display="Top-right online icon; bottom `Ready`; middle empty.",
        clear="Meeting starts, agent waits, reply capture starts, or an error arrives.",
    ),
    CompanionState.MEETING_RECORDING: StateContract(
        state=CompanionState.MEETING_RECORDING,
        owner=CompanionOwner.HOLDSPEAK,
        trigger="HoldSpeak emits `Recording ...` sticky status or runtime reports an active meeting.",
        display="Bottom sticky recording timer; middle remains available for flashes or agent attention.",
        clear="Meeting stops and HoldSpeak emits a non-recording sticky status.",
    ),
    CompanionState.AGENT_WAITING: StateContract(
        state=CompanionState.AGENT_WAITING,
        owner=CompanionOwner.HOLDSPEAK,
        trigger="Captured Claude/Codex session has `awaiting_response=true` inside the freshness window.",
        display="Middle sticky agent label/question; bottom continues to show meeting or ready state.",
        clear="Agent session clears, user starts reply capture, or freshness exceeds the stale TTL.",
    ),
    CompanionState.REPLY_CAPTURE: StateContract(
        state=CompanionState.REPLY_CAPTURE,
        owner=CompanionOwner.FIRMWARE,
        trigger="User starts voice capture for an agent reply.",
        display="Bottom sticky listening state; middle sticky reply target.",
        clear="Firmware stops capture and HoldSpeak enters transcription/rewrite pending.",
    ),
    CompanionState.TRANSCRIBING: StateContract(
        state=CompanionState.TRANSCRIBING,
        owner=CompanionOwner.HOLDSPEAK,
        trigger="HoldSpeak is transcribing or running the dictation rewrite pipeline.",
        display="Bottom sticky transcribing state; middle keeps higher-priority attention if present.",
        clear="Text insertion completes, fails, or HoldSpeak returns to ready/recording.",
    ),
    CompanionState.ERROR_BUSY: StateContract(
        state=CompanionState.ERROR_BUSY,
        owner=CompanionOwner.BRIDGE,
        trigger="HoldSpeak sends `session_busy` or another device-facing error.",
        display="Middle flash with busy/error text; link and bottom baseline remain readable.",
        clear="Flash TTL expires or a newer middle-priority message replaces it.",
    ),
    CompanionState.STALE_CLEARED: StateContract(
        state=CompanionState.STALE_CLEARED,
        owner=CompanionOwner.BRIDGE,
        trigger="An agent question is older than the accepted freshness window.",
        display="Middle flash indicating stale agent context was cleared; then middle clears.",
        clear="Stale-clear flash TTL expires or a fresh agent question arrives.",
    ),
}


def build_lcd_plan(signals: CompanionSignals) -> LcdPlan:
    """Resolve an LCD plan from current companion facts.

    Priority is zone-aware:

    - top-right always represents the HoldSpeak link;
    - bottom is the persistent baseline, ordered reply > transcribing > meeting > ready;
    - middle is attention, ordered error/busy > reply target > stale clear >
      fresh agent question > transcript flash > clear.
    """

    top_right = ZonePaint(
        LINK_ONLINE if signals.connected else LINK_OFFLINE,
        LcdLifetime.STICKY,
    )
    bottom_state, bottom = _bottom_baseline(signals)
    middle_state, middle = _middle_attention(signals)

    if not signals.connected:
        primary = CompanionState.DISCONNECTED
    elif middle_state is not None:
        primary = middle_state
    else:
        primary = bottom_state

    return LcdPlan(
        primary_state=primary,
        top_right=top_right,
        middle=middle,
        bottom=bottom,
    )


def is_agent_stale(signals: CompanionSignals) -> bool:
    """True when the captured agent context is too old to answer safely."""

    return (
        signals.agent_waiting
        and signals.agent_age_s is not None
        and signals.agent_age_s > AGENT_STALE_AFTER_S
    )


def _bottom_baseline(signals: CompanionSignals) -> tuple[CompanionState, ZonePaint]:
    if signals.reply_capture:
        return (
            CompanionState.REPLY_CAPTURE,
            ZonePaint("Listening...", LcdLifetime.STICKY),
        )
    if signals.transcribing:
        return (
            CompanionState.TRANSCRIBING,
            ZonePaint("Transcribing...", LcdLifetime.STICKY),
        )
    if signals.meeting_recording:
        return (
            CompanionState.MEETING_RECORDING,
            ZonePaint("Recording", LcdLifetime.STICKY),
        )
    return (
        CompanionState.IDLE_CONNECTED,
        ZonePaint("Ready", LcdLifetime.STICKY),
    )


def _middle_attention(
    signals: CompanionSignals,
) -> tuple[CompanionState | None, ZonePaint]:
    if signals.busy:
        return (
            CompanionState.ERROR_BUSY,
            ZonePaint("Busy", LcdLifetime.FLASH, SESSION_BUSY_FLASH_MS),
        )
    if signals.error_text:
        return (
            CompanionState.ERROR_BUSY,
            ZonePaint(f"Error: {signals.error_text}", LcdLifetime.FLASH, ERROR_FLASH_MS),
        )
    if signals.reply_capture:
        label = _compact_label(signals.agent_label, fallback="Agent")
        return (
            CompanionState.REPLY_CAPTURE,
            ZonePaint(f"Replying to {label}", LcdLifetime.STICKY),
        )
    if is_agent_stale(signals):
        return (
            CompanionState.STALE_CLEARED,
            ZonePaint("Agent stale; cleared", LcdLifetime.FLASH, STALE_CLEAR_FLASH_MS),
        )
    if signals.agent_waiting:
        label = _compact_label(signals.agent_label, fallback="Agent")
        question = " ".join(signals.agent_question.split())
        text = f"{label} waiting"
        if question:
            text = f"{text}\n{question}"
        return (
            CompanionState.AGENT_WAITING,
            ZonePaint(text, LcdLifetime.STICKY),
        )
    if signals.transcript_flash:
        return (
            None,
            ZonePaint(
                " ".join(signals.transcript_flash.split()),
                LcdLifetime.PERSIST_UNTIL_REPLACED,
            ),
        )
    return None, ZonePaint("", LcdLifetime.CLEAR)


def _compact_label(label: str, *, fallback: str) -> str:
    compacted = " ".join(str(label or "").split())
    return compacted or fallback


__all__ = [
    "AGENT_STALE_AFTER_S",
    "STALE_CLEAR_FLASH_MS",
    "CompanionOwner",
    "CompanionSignals",
    "CompanionState",
    "LcdLifetime",
    "LcdPlan",
    "STATE_CONTRACTS",
    "StateContract",
    "ZonePaint",
    "build_lcd_plan",
    "is_agent_stale",
]
