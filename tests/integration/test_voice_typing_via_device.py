"""Integration test for device-driven voice typing (HS-14-05).

Wires the WS route's voice-typing handlers to a
``VoiceTypingSession`` plus a fake STT and a mock typer, then
exercises the path end-to-end through a FastAPI ``TestClient``.
The actual web-runtime integration is covered indirectly — this
test isolates the wiring change from the hotkey/menubar plumbing.
"""

from __future__ import annotations

import json
import threading
from typing import List, Optional, Tuple

import numpy as np
import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from holdspeak.audio import AudioSource
from holdspeak.device_audio import (
    DEVICE_HANDSHAKE_VERSION,
    DeviceRegistry,
)
from holdspeak.voice_typing import VoiceTypingSession
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


_DEFAULT_PSK = "test-psk-secret"


class _FakeSTT:
    def __init__(self) -> None:
        self.calls: List[np.ndarray] = []

    def transcribe(self, audio: np.ndarray) -> str:
        self.calls.append(audio)
        return f"transcript({audio.size} samples)"


class _MockTyper:
    def __init__(self) -> None:
        self.typed: List[str] = []

    def type_text(self, text: str) -> None:
        self.typed.append(text)


def _ramp_int16(samples: int, *, value: int = 2000) -> bytes:
    return (np.full(samples, value, dtype="<i2")).tobytes()


def _send_handshake(
    ws,
    *,
    device_id: str,
    label: str,
    psk: str = _DEFAULT_PSK,
) -> None:
    ws.send_text(
        json.dumps(
            {
                "type": "hello",
                "device_id": device_id,
                "label": label,
                "psk": psk,
                "version": DEVICE_HANDSHAKE_VERSION,
            }
        )
    )


@pytest.fixture
def device_registry() -> DeviceRegistry:
    return DeviceRegistry()


@pytest.fixture
def voice_session() -> VoiceTypingSession:
    return VoiceTypingSession()


@pytest.fixture
def stt() -> _FakeSTT:
    return _FakeSTT()


@pytest.fixture
def typer() -> _MockTyper:
    return _MockTyper()


@pytest.fixture
def web_server(
    device_registry: DeviceRegistry,
    voice_session: VoiceTypingSession,
    stt: _FakeSTT,
    typer: _MockTyper,
) -> Tuple[MeetingWebServer, threading.Event]:
    """Build a server whose voice handlers run a synthetic transcribe+type pipeline."""

    transcribed_event = threading.Event()

    def on_voice_start(device_id: str, source: AudioSource) -> bool:
        return voice_session.begin(source, owner=f"device:{device_id}")

    def on_voice_stop(device_id: str, source: AudioSource) -> Optional[np.ndarray]:
        audio = voice_session.end(owner=f"device:{device_id}")
        if audio is None:
            return None
        text = stt.transcribe(audio)
        if text:
            typer.type_text(text)
        transcribed_event.set()
        return audio

    def on_voice_cancel(device_id: str) -> None:
        voice_session.cancel(owner=f"device:{device_id}")

    server = MeetingWebServer(
                 WebRuntimeCallbacks(
                     on_bookmark=lambda _label: None,
                     on_stop=lambda: None,
                     get_state=lambda: {},
                     device_registry=device_registry,
                     device_psk_provider=lambda: _DEFAULT_PSK,
                     on_device_voice_start=on_voice_start,
                     on_device_voice_stop=on_voice_stop,
                     on_device_voice_cancel=on_voice_cancel,
                 ),
                 host="127.0.0.1",
             )
    return server, transcribed_event


@pytest.fixture
def client(web_server) -> TestClient:
    server, _ = web_server
    return TestClient(server.app)


@pytest.mark.integration
class TestVoiceTypingViaDevice:
    def test_device_drives_full_voice_typing_pipeline(
        self,
        client: TestClient,
        web_server,
        stt: _FakeSTT,
        typer: _MockTyper,
    ) -> None:
        _, transcribed_event = web_server

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws, device_id="aipi-1", label="Karol")
            ws.receive_json()  # hello-ack

            ws.send_text(json.dumps({"type": "start"}))
            ws.send_bytes(_ramp_int16(8000, value=3000))
            ws.send_text(json.dumps({"type": "stop"}))
            ws.close()

        assert transcribed_event.wait(timeout=2.0), "transcribe handler did not run"

        assert len(stt.calls) == 1
        captured_audio = stt.calls[0]
        assert captured_audio.dtype == np.float32
        assert captured_audio.shape == (8000,)
        # The fake STT returns a deterministic transcript; the
        # mock typer should see exactly that text.
        assert typer.typed == [f"transcript({captured_audio.size} samples)"]

    def test_concurrent_device_start_receives_session_busy(
        self, client: TestClient, voice_session: VoiceTypingSession
    ) -> None:
        # Pre-seed: another device is already mid-session.
        # We simulate that state by reaching into the shared
        # VoiceTypingSession directly with a sentinel source.
        class _DummySource:
            def start_recording(self) -> None:
                pass

            def stop_recording(self) -> np.ndarray:
                return np.zeros(0, dtype=np.float32)

        assert voice_session.begin(_DummySource(), owner="device:other") is True

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws, device_id="aipi-1", label="Karol")
            ws.receive_json()  # hello-ack

            ws.send_text(json.dumps({"type": "start"}))
            error_frame = ws.receive_json()

        assert error_frame == {
            "type": "error",
            "code": "session_busy",
            "reason": "another voice-typing session is already active",
        }

        # The pre-existing session is still held by the other owner.
        assert voice_session.active_owner == "device:other"

    def test_disconnect_mid_session_cancels_cleanly(
        self,
        client: TestClient,
        voice_session: VoiceTypingSession,
        stt: _FakeSTT,
        typer: _MockTyper,
    ) -> None:
        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws, device_id="aipi-1", label="Karol")
            ws.receive_json()
            ws.send_text(json.dumps({"type": "start"}))
            ws.send_bytes(_ramp_int16(800))
            # No "stop" — peer drops.

        # Session must be released (no leaked owner) and no
        # transcribe / type happened.
        assert voice_session.is_active is False
        assert stt.calls == []
        assert typer.typed == []

    def test_legacy_path_still_works_when_no_voice_handlers(
        self,
        device_registry: DeviceRegistry,
    ) -> None:
        # When the runtime opts out of the voice handlers, the
        # original "start records, stop emits chunk" path kicks
        # back in (HS-14-04 behavior). Lock that contract in.
        chunks: List[Tuple[str, np.ndarray]] = []

        server = MeetingWebServer(
                     WebRuntimeCallbacks(
                         on_bookmark=lambda _label: None,
                         on_stop=lambda: None,
                         get_state=lambda: {},
                         device_registry=device_registry,
                         device_psk_provider=lambda: _DEFAULT_PSK,
                         on_device_audio_chunk=lambda d, a: chunks.append((d, a)),
                     ),
                     host="127.0.0.1",
                 )
        client = TestClient(server.app)

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws, device_id="aipi-1", label="Karol")
            ws.receive_json()
            ws.send_text(json.dumps({"type": "start"}))
            ws.send_bytes(_ramp_int16(800))
            ws.send_text(json.dumps({"type": "stop"}))
            ws.close()

        assert len(chunks) == 1
        device_id, audio = chunks[0]
        assert device_id == "aipi-1"
        assert audio.shape == (800,)
