"""The Phone wire: one contract for the hub, the desk and the Apple app.

Each model mirrors a row of the design's tables (§10) or one event of the log
(§4). The golden fixtures in ``tests/fixtures/phone/`` are round-tripped
through these models by ``tests/unit/test_phone_contract.py``; the Apple
app's ``Codable`` twins (``apple/Sources/Contracts/Phone.swift``, a later
Program step) read the same files.

The shape of the event log (a global ``seq``, a ``type`` and a ``ts`` on
every event, a ``hello`` that is never stored) and of the signed push (the
event as a JSON string beside its HMAC) is taken from agentring's
``protocol/relay.openapi.yaml`` (Apache-2.0); the names and the fields are
HoldSpeak's own.
"""
from __future__ import annotations

from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

Direction = Literal["to_phone", "from_phone"]
DeviceState = Literal["pairing", "paired", "revoked"]
CallState = Literal["held", "ringing", "answered", "missed", "declined", "ended"]
Transport = Literal["number", "app"]
Channel = Literal["message", "call"]

EVENT_TYPES = (
    "message.new", "message.delivered", "message.read", "message.wait",
    "call.held", "call.invite", "call.answered", "call.declined", "call.missed", "call.ended",
    "device.paired", "device.revoked", "reach", "hello", "ping",
)
EventType = Literal[
    "message.new", "message.delivered", "message.read", "message.wait",
    "call.held", "call.invite", "call.answered", "call.declined", "call.missed", "call.ended",
    "device.paired", "device.revoked", "reach", "hello", "ping",
]


class _Wire(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Device(_Wire):
    """A paired phone (``phone_devices``); the push token is never on the wire."""

    id: str
    name: str
    platform: str
    state: DeviceState
    has_push: bool = False
    push_kind: Optional[str] = None
    sip_identity: Optional[str] = None
    paired_at: str
    last_seen_at: Optional[str] = None
    revoked_at: Optional[str] = None


class Message(_Wire):
    """One line between the desk and his phone (``phone_messages``)."""

    id: str
    seq: int
    direction: Direction
    text: str
    reply_to: Optional[str] = None
    created_at: str
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None
    origin_ref: Optional[str] = None
    program_step_id: Optional[str] = None


class Call(_Wire):
    """One call (``phone_calls``). ``decision`` is what his answer decided."""

    id: str
    seq: int
    direction: Direction
    reason: str
    urgent: bool = False
    state: CallState
    transport: Transport
    created_at: str
    answered_at: Optional[str] = None
    ended_at: Optional[str] = None
    end_reason: Optional[str] = None
    duration_s: Optional[float] = None
    transcript_ref: Optional[str] = None
    decision: Optional[dict[str, Any]] = None


# ── the events ──────────────────────────────────────────────────────────

class MessageNew(_Wire):
    message: Message


class MessageMark(_Wire):
    msg_id: str
    at: str
    by: Optional[Literal["phone", "desk"]] = None


class CallFull(_Wire):
    call: Call
    expires_at: Optional[str] = None


class CallMark(_Wire):
    call_id: str
    at: str
    by: Optional[Literal["phone", "desk", "timeout"]] = None
    end_reason: Optional[str] = None
    duration_s: Optional[float] = None
    rings: Optional[int] = None


class DevicePaired(_Wire):
    device: Device


class DeviceRevoked(_Wire):
    device_id: str
    at: str


class Reach(_Wire):
    """The desk's own decision to reach him, with its rule (§6)."""

    kind: str
    channel: Channel
    rule: str
    level: str
    urgent: bool = False
    may_call: bool = False
    queued: bool = False
    reason: Optional[str] = None
    origin_ref: Optional[str] = None
    msg_id: Optional[str] = None
    call_id: Optional[str] = None


class Hello(_Wire):
    """The first frame on a socket; never stored (no ``seq``)."""

    hub_id: str
    last_seq: int
    server_ts: str


class Ping(_Wire):
    """A keep-alive on a quiet socket; never stored."""


_DATA: dict[str, type[_Wire]] = {
    "message.new": MessageNew, "message.delivered": MessageMark, "message.read": MessageMark,
    "message.wait": MessageMark, "call.held": CallFull, "call.invite": CallFull, "call.answered": CallMark,
    "call.declined": CallMark, "call.missed": CallMark, "call.ended": CallMark,
    "device.paired": DevicePaired, "device.revoked": DeviceRevoked, "reach": Reach, "hello": Hello,
    "ping": Ping,
}

EventData = Union[MessageNew, MessageMark, CallFull, CallMark, DevicePaired, DeviceRevoked, Reach, Hello]


class Event(_Wire):
    """One event of the log: ``{seq, type, ts, data}``; ``hello`` has no ``seq``."""

    seq: Optional[int] = None
    type: EventType
    ts: str
    data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _typed(self) -> "Event":
        model = _DATA[self.type]
        self.data = model.model_validate(self.data).model_dump(mode="json", exclude_none=True)
        if self.type not in ("hello", "ping") and self.seq is None:
            raise ValueError("a stored event has a seq")
        return self


# ── pairing, push, answers ──────────────────────────────────────────────

class PairingToken(_Wire):
    """``POST /api/phone/pair``: the QR the app scans (10 minutes)."""

    token: str
    qr_payload: str
    qr_png_base64: Optional[str] = None
    expires_at: str


class PairRequest(_Wire):
    """``POST /api/phone/devices``: the app redeems the token."""

    pair_token: str
    name: str = Field(min_length=1, max_length=64)
    platform: Literal["ios", "android", "test"]
    push_token: Optional[str] = Field(default=None, max_length=4096)
    push_kind: Optional[Literal["apns", "null"]] = None
    sip_identity: Optional[str] = Field(default=None, max_length=256)


class PairResponse(_Wire):
    device_id: str
    device_jwt: str
    push_secret: str
    hub_id: str


class PushData(_Wire):
    """What a push carries: the event as JSON text and its signature."""

    v: Literal["1"] = "1"
    hub_id: str
    event: str
    sig: str


class Line(_Wire):
    who: Literal["you", "holdspeak"]
    text: str


class CallAnswer(_Wire):
    """``phone.call``'s answer when the call is over."""

    call_id: str
    state: CallState
    transcript: list[Line] = Field(default_factory=list)
    end_reason: Optional[str] = None
    duration_s: Optional[float] = None
    decision: Optional[dict[str, Any]] = None
    words: Optional[str] = None


class Replies(_Wire):
    """``phone.get_replies``: his new replies, each once."""

    replies: list[Message] = Field(default_factory=list)
    note: Optional[str] = None


__all__ = [
    "Call", "CallAnswer", "CallFull", "CallMark", "Device", "DevicePaired", "DeviceRevoked", "EVENT_TYPES",
    "Event", "Hello", "Line", "Message", "MessageMark", "MessageNew", "PairRequest", "PairResponse",
    "PairingToken", "PushData", "Reach", "Replies",
]
