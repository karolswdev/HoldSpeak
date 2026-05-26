"""Pydantic models mirroring HoldSpeak's device-audio WebSocket wire contract.

Source of truth: ~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md (HS-14-08) and
~/dev/HoldSpeak/holdspeak/device_audio.py.

Strict mode (`extra="forbid"`, `str_strip_whitespace=True` where the
HoldSpeak side strips) so any schema drift on either side fails loudly
during validation rather than producing silently-wrong frames.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

DEVICE_HANDSHAKE_VERSION = 1

# Application close codes from the HoldSpeak protocol §5. Mirror values
# from holdspeak/device_audio.py:WS_CLOSE_*.
WS_CLOSE_INVALID_HANDSHAKE = 4001
WS_CLOSE_PSK_MISMATCH = 4003
WS_CLOSE_DUPLICATE_LABEL = 4009


class Hello(BaseModel):
    """First-message handshake the bridge sends after opening the WS.

    Mirrors `holdspeak.device_audio.DeviceHandshake` exactly: same fields,
    same `extra="forbid"`, same `str_strip_whitespace=True`, same
    non-empty validators on the three string fields.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    type: Literal["hello"] = "hello"
    device_id: str
    label: str
    psk: str
    version: int = DEVICE_HANDSHAKE_VERSION

    @field_validator("device_id", "label", "psk")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("must not be empty")
        return value


class HelloAck(BaseModel):
    """Server's acceptance of the handshake. The label is echoed back."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    type: Literal["hello-ack"]
    device_id: str
    label: str


class Heartbeat(BaseModel):
    """Bridge → server liveness ping. No reply; refreshes `last_seen`."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["heartbeat"] = "heartbeat"


class StartFrame(BaseModel):
    """Begin a recording session. Wired in AIPI-2-03."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["start"] = "start"


class StopFrame(BaseModel):
    """End the recording session. Wired in AIPI-2-03."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["stop"] = "stop"


class EventFrame(BaseModel):
    """Device-side gesture event (e.g., bookmark on `long_press` during a meeting).

    Phase 2 doesn't emit these — no gesture maps to one in this phase
    (see `phase-2-bridge-protocol-translator/current-phase-status.md`
    decisions). Defined here so a follow-up can wire it without
    teaching the model to a future story.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["event"] = "event"
    name: str
    at: float | None = None


class QueryFrame(BaseModel):
    """Device → server read-only state query (AIPI-4-06)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["query"] = "query"
    name: Literal["last_segment", "agent_question", "agent_next"]
    at: int


class Status(BaseModel):
    """Server → device LCD pushback (HS-14-07)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["status"]
    text: str
    ttl_ms: int


class ErrorFrame(BaseModel):
    """Server → device error frame (e.g. `session_busy`).

    Connection is NOT closed when the server sends an error frame —
    the device can wait + retry on the next user action.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    type: Literal["error"]
    code: str
    reason: str


__all__ = [
    "DEVICE_HANDSHAKE_VERSION",
    "WS_CLOSE_INVALID_HANDSHAKE",
    "WS_CLOSE_PSK_MISMATCH",
    "WS_CLOSE_DUPLICATE_LABEL",
    "Hello",
    "HelloAck",
    "Heartbeat",
    "StartFrame",
    "StopFrame",
    "EventFrame",
    "QueryFrame",
    "Status",
    "ErrorFrame",
]
