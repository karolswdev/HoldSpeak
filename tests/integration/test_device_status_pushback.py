"""Integration test for server → device status push (HS-14-07)."""

from __future__ import annotations

import json
from typing import List, Optional, Tuple

import numpy as np
import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from holdspeak.audio import AudioSource
from holdspeak.device_audio import DEVICE_HANDSHAKE_VERSION, DeviceRegistry
from holdspeak.device_status import DeviceStatusEmitter
from holdspeak.voice_typing import VoiceTypingSession
from holdspeak.web_server import MeetingWebServer


_DEFAULT_PSK = "status-test-psk"


def _send_handshake(
    ws,
    *,
    device_id: str = "aipi-1",
    label: str = "Karol",
) -> None:
    ws.send_text(
        json.dumps(
            {
                "type": "hello",
                "device_id": device_id,
                "label": label,
                "psk": _DEFAULT_PSK,
                "version": DEVICE_HANDSHAKE_VERSION,
            }
        )
    )


def _drain_status_messages(ws, *, count: int, timeout: float = 1.0) -> list[dict]:
    """Receive ``count`` status frames or until disconnect."""
    received: list[dict] = []
    while len(received) < count:
        msg = ws.receive_json()
        received.append(msg)
    return received


@pytest.mark.integration
class TestDeviceStatusOutbound:
    def _build_server(
        self,
        *,
        on_voice_start=None,
        on_voice_stop=None,
        on_event=None,
    ) -> Tuple[MeetingWebServer, DeviceStatusEmitter, DeviceRegistry]:
        registry = DeviceRegistry()
        emitter = DeviceStatusEmitter(label_lookup=registry)
        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            device_registry=registry,
            device_psk_provider=lambda: _DEFAULT_PSK,
            device_status_emitter=emitter,
            on_device_voice_start=on_voice_start,
            on_device_voice_stop=on_voice_stop,
            on_device_event=on_event,
            host="127.0.0.1",
        )
        return server, emitter, registry

    def test_emit_after_handshake_reaches_device(self) -> None:
        server, emitter, _ = self._build_server()
        client = TestClient(server.app)

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ack = ws.receive_json()
            assert ack["type"] == "hello-ack"

            # Now the connection is live; emit a status message
            # via the shared emitter and verify the device sees it.
            emitter.send("aipi-1", "Listening...")
            msg = ws.receive_json()
            assert msg == {"type": "status", "text": "Listening...", "ttl_ms": 0}

    def test_label_substitution_and_ttl_round_trip(self) -> None:
        server, emitter, _ = self._build_server()
        client = TestClient(server.app)

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws, device_id="aipi-1", label="Karol")
            ws.receive_json()  # ack

            emitter.send("aipi-1", "{label} listening", ttl_ms=2500)
            msg = ws.receive_json()
            assert msg == {
                "type": "status",
                "text": "Karol listening",
                "ttl_ms": 2500,
            }

    def test_voice_typing_status_sequence(self) -> None:
        """End-to-end: a device-driven voice-typing turn emits Listening → Thinking → snippet."""
        captured_audio: List[np.ndarray] = []
        voice_session = VoiceTypingSession()

        # We'll supply a status emitter whose senders we'll monitor.
        registry = DeviceRegistry()
        emitter = DeviceStatusEmitter(label_lookup=registry)

        def on_voice_start(device_id: str, source: AudioSource) -> bool:
            ok = voice_session.begin(source, owner=f"device:{device_id}")
            if ok:
                emitter.send(device_id, "Listening...")
            return ok

        def on_voice_stop(device_id: str, source: AudioSource) -> Optional[np.ndarray]:
            audio = voice_session.end(owner=f"device:{device_id}")
            if audio is None:
                return None
            captured_audio.append(audio)
            emitter.send(device_id, "Thinking...")
            # Synthesize a transcript, send the snippet.
            emitter.send(device_id, "hello world", ttl_ms=4000)
            return audio

        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            device_registry=registry,
            device_psk_provider=lambda: _DEFAULT_PSK,
            device_status_emitter=emitter,
            on_device_voice_start=on_voice_start,
            on_device_voice_stop=on_voice_stop,
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ack = ws.receive_json()
            assert ack["type"] == "hello-ack"

            ws.send_text(json.dumps({"type": "start"}))
            listening = ws.receive_json()
            assert listening == {"type": "status", "text": "Listening...", "ttl_ms": 0}

            ws.send_bytes(np.full(800, 1000, dtype="<i2").tobytes())
            ws.send_text(json.dumps({"type": "stop"}))

            # The stop handler fires Thinking + transcript snippet
            # via the emitter; consume both.
            thinking = ws.receive_json()
            snippet = ws.receive_json()
            ws.close()

        assert thinking == {"type": "status", "text": "Thinking...", "ttl_ms": 0}
        assert snippet == {"type": "status", "text": "hello world", "ttl_ms": 4000}
        assert len(captured_audio) == 1


@pytest.mark.integration
class TestDeviceEventInbound:
    def test_event_dispatches_to_handler_with_at(self) -> None:
        events: List[Tuple[str, str, Optional[float]]] = []

        def on_event(device_id: str, name: str, at: Optional[float]) -> None:
            events.append((device_id, name, at))

        registry = DeviceRegistry()
        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            device_registry=registry,
            device_psk_provider=lambda: _DEFAULT_PSK,
            on_device_event=on_event,
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()  # ack

            ws.send_text(
                json.dumps({"type": "event", "name": "long_press", "at": 47.5})
            )
            # Send a heartbeat so we have something the dispatcher
            # acks back; the event itself produces no reply.
            ws.send_text(json.dumps({"type": "heartbeat"}))
            ws.close()

        assert events == [("aipi-1", "long_press", 47.5)]

    def test_event_without_name_is_ignored(self) -> None:
        events: List[Tuple[str, str, Optional[float]]] = []

        def on_event(device_id: str, name: str, at: Optional[float]) -> None:
            events.append((device_id, name, at))

        registry = DeviceRegistry()
        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            device_registry=registry,
            device_psk_provider=lambda: _DEFAULT_PSK,
            on_device_event=on_event,
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()
            ws.send_text(json.dumps({"type": "event"}))
            ws.send_text(json.dumps({"type": "heartbeat"}))
            ws.close()

        assert events == []

    def test_event_at_can_be_missing(self) -> None:
        events: List[Tuple[str, str, Optional[float]]] = []

        def on_event(device_id: str, name: str, at: Optional[float]) -> None:
            events.append((device_id, name, at))

        registry = DeviceRegistry()
        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            device_registry=registry,
            device_psk_provider=lambda: _DEFAULT_PSK,
            on_device_event=on_event,
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()
            ws.send_text(json.dumps({"type": "event", "name": "double_tap"}))
            ws.send_text(json.dumps({"type": "heartbeat"}))
            ws.close()

        assert events == [("aipi-1", "double_tap", None)]


@pytest.mark.integration
class TestStatusEmitterDisconnectCleanup:
    def test_disconnect_unregisters_emitter(self) -> None:
        registry = DeviceRegistry()
        emitter = DeviceStatusEmitter(label_lookup=registry)
        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            device_registry=registry,
            device_psk_provider=lambda: _DEFAULT_PSK,
            device_status_emitter=emitter,
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()
            assert emitter.is_registered("aipi-1") is True

        # Context exit → server detects disconnect → cleanup unregisters emitter.
        assert emitter.is_registered("aipi-1") is False
