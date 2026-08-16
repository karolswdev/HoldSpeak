"""HS-132-05 — the streaming mic is honest.

Three properties of ``/ws/dictation/stream`` are pinned here.

**The floor is held for the whole utterance.** The browser mic claims the
audio floor on a LEASE (``voice_support.BROWSER_FLOOR_LEASE_SECONDS``) and a
dictation can easily outlive one. Nothing renewed it, so past the lease the
hotkey, the wake listener or a meeting could seize the microphone mid-word.
Every chunk that lands now heartbeats the claim; a stream many lease-lengths
long holds the floor from the first frame to the last.

**One utterance, one transcription pass.** Each 600 ms chunk used to take its
own full Whisper pass — on the very ``transcription_lock`` the hotkey needs,
with the worst possible context for hallucination — and the "partial" it
produced had no consumer anywhere in the client. The chunks are accumulated;
only the whole utterance is transcribed.

**A refusal keeps its name.** The floor being taken is a NAMED failure with
the closed-interval marker, not a silent stop or a bare error string.

The transcriber is a stub and the socket declares ``pipeline: false``, so
these tests reach no model, no journal and no LAN endpoint.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import numpy as np
import pytest

from holdspeak.config import Config
from holdspeak.voice_typing import VoiceTypingSession
from holdspeak.web.context import WebContext
from holdspeak.web.routes.system import voice as voice_routes
from holdspeak.web.routes.system import voice_support
from holdspeak.web.routes.system.voice import build_voice_router

OWNER_TOKEN = "streaming-mic-owner-token"
TEST_LEASE_SECONDS = 5.0
#: one 600 ms chunk of 16 kHz mono 16-bit PCM
CHUNK = np.zeros(9_600, dtype=np.int16).tobytes()


class _Clock:
    """A hand-cranked monotonic clock; the audio floor reads it."""

    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class _FakeInterval:
    handle = "mic_streaming_honesty"

    def __init__(self) -> None:
        class _Fence:
            def publish(self, _stage: str, publication: Any) -> tuple[bool, Any]:
                return True, publication()

            def reason(self) -> str:
                return ""

        class _Session:
            fence = _Fence()

            def provider(self) -> Any:
                return object()

        self.session = _Session()


class _FakeRegistry:
    """Admission itself is HS-131-09's ground; this keeps it out of the way."""

    def __init__(self) -> None:
        self.closed: list[str] = []

    def open(self, _principal: Any, **_kw: Any) -> _FakeInterval:
        return _FakeInterval()

    def close(self, _principal: Any, *, reason: str = "") -> str:
        self.closed.append(reason)
        return _FakeInterval.handle


class _Socket:
    """The client half of the socket, with a hook that runs BETWEEN frames."""

    def __init__(self, messages: list[dict[str, Any]], between=None) -> None:
        self.headers = {
            "authorization": f"Bearer {OWNER_TOKEN}",
            "sec-websocket-protocol": "",
        }
        self.messages = list(messages)
        self.sent: list[dict[str, Any]] = []
        self.between = between
        self.closed = False

    async def accept(self, **_kw: Any) -> None:
        return None

    async def receive(self) -> dict[str, Any]:
        if self.between is not None:
            self.between()
        if not self.messages:
            return {"type": "websocket.disconnect"}
        return self.messages.pop(0)

    async def send_json(self, payload: dict[str, Any]) -> None:
        self.sent.append(dict(payload))

    async def close(self, **_kw: Any) -> None:
        self.closed = True

    def of(self, kind: str) -> list[dict[str, Any]]:
        return [event for event in self.sent if event.get("type") == kind]


@pytest.fixture
def dictate(monkeypatch):
    """Run one scripted socket against the real route; report what happened."""
    monkeypatch.setattr(voice_routes, "browser_mic_sessions", lambda: _FakeRegistry())
    monkeypatch.setattr(
        voice_support, "BROWSER_FLOOR_LEASE_SECONDS", TEST_LEASE_SECONDS
    )
    config = Config()
    config.dictation.pipeline.enabled = False
    config.meeting.web_auth_token = OWNER_TOKEN
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: config))

    def run(
        messages: list[dict[str, Any]],
        *,
        floor: VoiceTypingSession | None = None,
        between=None,
        said: str = "ship it friday",
    ) -> tuple[_Socket, list[int]]:
        passes: list[int] = []

        def transcribe(audio: Any, **_kw: Any) -> str:
            passes.append(int(getattr(audio, "size", 0)))
            return said

        ctx = WebContext(
            get_state=lambda: {},
            on_transcribe=transcribe,
            voice_session=floor,
            web_auth_token=OWNER_TOKEN,
        )
        endpoint = _endpoint_for(build_voice_router(ctx), "/ws/dictation/stream")
        socket = _Socket(messages, between=between)
        asyncio.run(endpoint(socket))
        return socket, passes

    return run


def _endpoint_for(router: Any, path: str) -> Any:
    for route in router.routes:
        if getattr(route, "path", "") == path:
            return route.endpoint
    raise AssertionError(f"no route for {path}")


def _stream(chunks: int) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = [
        {"text": json.dumps({"type": "start", "pipeline": False})}
    ]
    frames += [{"bytes": CHUNK} for _ in range(chunks)]
    frames.append({"text": json.dumps({"type": "end"})})
    return frames


# ── the floor is held for the whole utterance ────────────────────────────────


def test_a_dictation_far_longer_than_the_lease_never_drops_the_floor(dictate):
    """The lease is 5 s here and the capture runs 120 s of clock. Every chunk
    heartbeats the claim, so a rival owner is refused from the first frame to
    the last — the hotkey cannot seize the mic mid-utterance."""
    clock = _Clock()
    floor = VoiceTypingSession(clock=clock)
    rival_wins: list[float] = []

    def between() -> None:
        clock.advance(3.0)  # well past the 5 s lease across two frames
        if floor.acquire("hotkey"):
            rival_wins.append(clock.now)
            floor.release("hotkey")

    socket, passes = dictate(_stream(40), floor=floor, between=between)

    assert rival_wins == [], "the floor was lost mid-capture"
    assert clock.now - 1_000.0 >= 120.0, "the capture must outlive the lease"
    assert socket.of("final") == [{"type": "final", "text": "ship it friday"}]
    assert socket.of("error") == []
    # ...and the floor is given back when the socket ends.
    assert floor.active_owner is None


def test_the_floor_is_released_to_the_hotkey_once_the_capture_ends(dictate):
    clock = _Clock()
    floor = VoiceTypingSession(clock=clock)

    dictate(_stream(3), floor=floor, between=lambda: clock.advance(1.0))

    assert floor.acquire("hotkey") is True


def test_a_floor_taken_mid_stream_stops_the_capture_by_name(dictate):
    """A floor that was genuinely lost is a NAMED refusal with the closed
    interval marker — never a silent recording into somebody else's mic."""
    clock = _Clock()
    floor = VoiceTypingSession(clock=clock)
    frames = {"count": 0}

    def between() -> None:
        frames["count"] += 1
        if frames["count"] == 3:
            # the lease lapsed unrenewed and the hotkey took the floor
            clock.advance(TEST_LEASE_SECONDS + 1.0)
            assert floor.acquire("hotkey") is True

    socket, passes = dictate(_stream(6), floor=floor, between=between)

    assert socket.of("final") == [], "nothing is transcribed off a lost floor"
    assert passes == []
    error = socket.of("error")[0]
    assert error["reason"] == "audio_floor_lost"
    assert error["failure_category"] == "audio_floor_lost"
    assert error["mic_interval"] == "closed"
    assert floor.active_owner == "hotkey", "the taker keeps what it took"


def test_the_floor_is_claimed_on_the_shared_lease_constant(dictate):
    """The claim and the heartbeat read the same number, so they cannot drift."""
    clock = _Clock()
    floor = VoiceTypingSession(clock=clock)
    seen: list[str | None] = []

    def between() -> None:
        seen.append(floor.active_owner)

    dictate(_stream(2), floor=floor, between=between)

    assert seen[0] == "browser_mic"
    assert voice_support.BROWSER_FLOOR_LEASE_SECONDS == TEST_LEASE_SECONDS


# ── one utterance, one transcription pass ────────────────────────────────────


def test_forty_chunks_take_exactly_one_transcription_pass(dictate):
    """Forty 600 ms chunks used to be forty independent Whisper passes on the
    hotkey's lock. Now the accumulated utterance is transcribed once."""
    socket, passes = dictate(_stream(40))

    assert len(passes) == 1, "one utterance, one pass"
    assert passes[0] == 40 * 9_600, "the WHOLE utterance, not the last chunk"
    assert socket.of("final") == [{"type": "final", "text": "ship it friday"}]


def test_no_partial_event_is_ever_sent(dictate):
    """The partial had no consumer in the client; it is gone from the wire."""
    socket, _passes = dictate(_stream(12))

    assert socket.of("partial") == []
    assert [event["type"] for event in socket.sent] == ["final"]


def test_a_silent_stream_still_answers_with_a_final(dictate):
    """No audio at all: one empty final, no error, no pass."""
    socket, passes = dictate(
        [
            {"text": json.dumps({"type": "start", "pipeline": False})},
            {"text": json.dumps({"type": "end"})},
        ]
    )

    assert socket.of("final") == [{"type": "final", "text": ""}]
    assert passes == []


# ── refusals keep their names ────────────────────────────────────────────────


def test_a_held_floor_refuses_by_name_before_anything_is_captured(dictate):
    clock = _Clock()
    floor = VoiceTypingSession(clock=clock)
    assert floor.acquire("meeting") is True

    socket, passes = dictate(_stream(3), floor=floor)

    error = socket.of("error")[0]
    assert error["reason"] == "audio_floor_held"
    assert error["failure_category"] == "audio_floor_held"
    assert passes == []
    assert socket.closed is True
    assert floor.active_owner == "meeting"


def test_an_unavailable_transcriber_says_which_failure_it_is(monkeypatch):
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: Config()))
    ctx = WebContext(get_state=lambda: {}, web_auth_token=OWNER_TOKEN)
    endpoint = _endpoint_for(build_voice_router(ctx), "/ws/dictation/stream")
    socket = _Socket(_stream(1))

    asyncio.run(endpoint(socket))

    error = socket.of("error")[0]
    assert error["failure_category"] == "transcription_unavailable"
    assert socket.closed is True
