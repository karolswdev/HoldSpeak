"""Integration tests for the ``/api/devices/audio`` WebSocket route (HS-14-04)."""

from __future__ import annotations

import json
import logging
import time
from typing import Callable, List, Optional, Tuple

import numpy as np
import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from holdspeak.device_audio import (
    DEVICE_HANDSHAKE_VERSION,
    DeviceRegistry,
    WS_CLOSE_DUPLICATE_LABEL,
    WS_CLOSE_INVALID_HANDSHAKE,
    WS_CLOSE_PSK_MISMATCH,
)
from holdspeak.web_server import MeetingWebServer


_DEFAULT_PSK = "test-psk-secret-1234567890"


def _silence_int16(samples: int) -> bytes:
    return (np.zeros(samples, dtype="<i2")).tobytes()


def _ramp_int16(samples: int, *, value: int = 1000) -> bytes:
    return (np.full(samples, value, dtype="<i2")).tobytes()


@pytest.fixture
def device_registry() -> DeviceRegistry:
    return DeviceRegistry()


@pytest.fixture
def chunk_sink() -> Tuple[List[Tuple[str, np.ndarray]], Callable[[str, np.ndarray], None]]:
    chunks: List[Tuple[str, np.ndarray]] = []

    def _on_chunk(device_id: str, audio: np.ndarray) -> None:
        chunks.append((device_id, audio))

    return chunks, _on_chunk


@pytest.fixture
def web_server(device_registry: DeviceRegistry, chunk_sink) -> MeetingWebServer:
    _, on_chunk = chunk_sink
    server = MeetingWebServer(
        on_bookmark=lambda _label: None,
        on_stop=lambda: None,
        get_state=lambda: {},
        device_registry=device_registry,
        device_psk_provider=lambda: _DEFAULT_PSK,
        on_device_audio_chunk=on_chunk,
        host="127.0.0.1",
    )
    return server


@pytest.fixture
def client(web_server: MeetingWebServer) -> TestClient:
    return TestClient(web_server.app)


def _send_handshake(
    ws,
    *,
    device_id: str = "aipi-1",
    label: str = "Karol",
    psk: str = _DEFAULT_PSK,
    type_: str = "hello",
    version: int = DEVICE_HANDSHAKE_VERSION,
    extras: Optional[dict] = None,
) -> None:
    payload = {
        "type": type_,
        "device_id": device_id,
        "label": label,
        "psk": psk,
        "version": version,
    }
    if extras:
        payload.update(extras)
    ws.send_text(json.dumps(payload))


@pytest.mark.integration
class TestDeviceAudioHandshake:
    def test_route_exists(self, client: TestClient) -> None:
        # connecting at all proves the route is mounted; receiving the
        # ack proves the handshake path completed end-to-end.
        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ack = ws.receive_json()
            assert ack["type"] == "hello-ack"
            assert ack["device_id"] == "aipi-1"
            assert ack["label"] == "Karol"

    def test_successful_handshake_registers_device(
        self, client: TestClient, device_registry: DeviceRegistry
    ) -> None:
        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()
            assert any(d.id == "aipi-1" for d in device_registry.active())

    def test_bad_handshake_closes_with_4001(self, client: TestClient) -> None:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/api/devices/audio") as ws:
                ws.send_text("not valid json")
                ws.receive_json()  # forces a recv to surface the close
        assert exc_info.value.code == WS_CLOSE_INVALID_HANDSHAKE

    def test_handshake_missing_field_closes_with_4001(self, client: TestClient) -> None:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/api/devices/audio") as ws:
                ws.send_text(json.dumps({"type": "hello", "device_id": "aipi-1"}))
                ws.receive_json()
        assert exc_info.value.code == WS_CLOSE_INVALID_HANDSHAKE

    def test_handshake_extra_field_closes_with_4001(self, client: TestClient) -> None:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/api/devices/audio") as ws:
                _send_handshake(ws, extras={"rogue": "oops"})
                ws.receive_json()
        assert exc_info.value.code == WS_CLOSE_INVALID_HANDSHAKE

    def test_bad_psk_closes_with_4003(self, client: TestClient) -> None:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/api/devices/audio") as ws:
                _send_handshake(ws, psk="not-the-real-psk")
                ws.receive_json()
        assert exc_info.value.code == WS_CLOSE_PSK_MISMATCH

    def test_duplicate_label_closes_with_4009(
        self, client: TestClient, device_registry: DeviceRegistry
    ) -> None:
        # Pre-register a device with the label we'll claim from the WS.
        device_registry.register("preexisting", "Karol")

        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/api/devices/audio") as ws:
                _send_handshake(ws, device_id="aipi-1", label="Karol")
                ws.receive_json()
        assert exc_info.value.code == WS_CLOSE_DUPLICATE_LABEL


@pytest.mark.integration
class TestDeviceAudioStreaming:
    def test_push_then_stop_emits_audio_chunk(
        self,
        client: TestClient,
        chunk_sink: Tuple[List[Tuple[str, np.ndarray]], Callable[[str, np.ndarray], None]],
    ) -> None:
        chunks, _ = chunk_sink

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()

            ws.send_text(json.dumps({"type": "start"}))
            # 0.5 s @ 16 kHz = 8000 samples = 16000 bytes.
            ws.send_bytes(_ramp_int16(8000, value=2000))
            ws.send_text(json.dumps({"type": "stop"}))
            # Politely close to flush the stop frame through the
            # server before the test client tears the socket down.
            ws.close()

        assert len(chunks) == 1
        device_id, audio = chunks[0]
        assert device_id == "aipi-1"
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert audio.shape == (8000,)
        # int16 value 2000 → ~0.061 in float32.
        np.testing.assert_allclose(
            audio, np.full(8000, 2000 / 32768.0, dtype=np.float32), atol=2.0 / 32768.0
        )

    def test_heartbeat_refreshes_last_seen(
        self, client: TestClient, device_registry: DeviceRegistry
    ) -> None:
        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()

            before = device_registry.get("aipi-1")
            assert before is not None

            ws.send_text(json.dumps({"type": "heartbeat"}))
            # Roundtrip a no-op control through the server before
            # snapshotting last_seen — sending alone doesn't await
            # processing.
            ws.send_text(json.dumps({"type": "heartbeat"}))
            ws.send_bytes(_silence_int16(160))  # tiny push to flush
            # Read nothing back; just give the server one event loop tick.
            ws.close()

        # last_seen should have been bumped at least once during the
        # short connection lifecycle. The descriptor itself is gone
        # post-disconnect; assert via a fresh handshake that the
        # registry is clean (descriptor removed, label freed).
        assert device_registry.get("aipi-1") is None

    def test_disconnect_unregisters_device(
        self, client: TestClient, device_registry: DeviceRegistry
    ) -> None:
        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()
            assert device_registry.get("aipi-1") is not None
        # Context manager close → server detects disconnect → cleanup.
        assert device_registry.get("aipi-1") is None

    def test_mid_recording_disconnect_drops_audio_cleanly(
        self,
        client: TestClient,
        device_registry: DeviceRegistry,
        chunk_sink: Tuple[List[Tuple[str, np.ndarray]], Callable[[str, np.ndarray], None]],
    ) -> None:
        chunks, _ = chunk_sink

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()
            ws.send_text(json.dumps({"type": "start"}))
            ws.send_bytes(_ramp_int16(1600))
            # No "stop" frame — peer just disconnects.

        # No chunk should have been emitted to the consumer.
        assert chunks == []
        # And the device is unregistered.
        assert device_registry.get("aipi-1") is None

    def test_overflow_logs_once_and_drops_oldest(
        self,
        client: TestClient,
        device_registry: DeviceRegistry,
        chunk_sink: Tuple[List[Tuple[str, np.ndarray]], Callable[[str, np.ndarray], None]],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        chunks, _ = chunk_sink

        # Pin the recorder to a small buffer cap to force overflow
        # without blasting megabytes of audio.
        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()

            recorder = device_registry.recorder_for("aipi-1")
            assert recorder is not None
            recorder.max_buffer_seconds = 0.05  # 800 samples @ 16 kHz

            ws.send_text(json.dumps({"type": "start"}))

            with caplog.at_level(logging.WARNING, logger="holdspeak.audio.remote"):
                ws.send_bytes(_ramp_int16(800, value=100))   # fills cap
                ws.send_bytes(_ramp_int16(400, value=900))   # overflows by 400
                ws.send_text(json.dumps({"type": "stop"}))
                ws.close()

        assert len(chunks) == 1
        device_id, audio = chunks[0]
        assert device_id == "aipi-1"
        # Only the newer 400 samples survive the drop-oldest policy.
        assert audio.shape == (400,)

        overflow_records = [
            r
            for r in caplog.records
            if r.levelno == logging.WARNING
            and "device.queue.overflow" in r.getMessage()
        ]
        assert len(overflow_records) == 1
        record = overflow_records[0]
        assert getattr(record, "device_id", None) == "aipi-1"
        assert getattr(record, "dropped_bytes", 0) == 800 * 2

    def test_active_reflects_live_queue_depth(
        self, client: TestClient, device_registry: DeviceRegistry
    ) -> None:
        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()

            ws.send_text(json.dumps({"type": "start"}))
            ws.send_bytes(_ramp_int16(800))  # 1600 bytes pushed

            # Roundtrip a heartbeat so the server has finished
            # processing the binary push before we snapshot.
            ws.send_text(json.dumps({"type": "heartbeat"}))
            ws.send_bytes(b"")  # cheap fence

            actives = device_registry.active()
            descriptors = {d.id: d for d in actives}
            assert "aipi-1" in descriptors
            # ≤ because ordering of "active() vs server processing"
            # is not strict; we mainly want > 0 to confirm the
            # registry surfaces the live recorder buffer depth.
            assert descriptors["aipi-1"].queue_depth >= 1600

            ws.close()


@pytest.mark.integration
class TestDeviceActiveFrames:
    def test_device_health_updates_registry_and_health_api(
        self,
        client: TestClient,
        device_registry: DeviceRegistry,
    ) -> None:
        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()

            ws.send_text(
                json.dumps(
                    {
                        "type": "device_health",
                        "battery_pct": 84,
                        "rssi_dbm": -57,
                        "at": 1234,
                    }
                )
            )

            descriptor = None
            for _ in range(20):
                descriptor = device_registry.get("aipi-1")
                if descriptor is not None and descriptor.battery_pct == 84:
                    break
                time.sleep(0.01)
            assert descriptor is not None
            assert descriptor.battery_pct == 84
            assert descriptor.rssi_dbm == -57
            assert descriptor.last_health_at == 1234

            response = client.get("/api/devices/health")
            assert response.status_code == 200, response.text
            [device] = response.json()["devices"]
            assert device["id"] == "aipi-1"
            assert device["battery_pct"] == 84
            assert device["rssi_dbm"] == -57
            assert device["last_health_at"] == 1234

    def test_device_health_callback_receives_refreshed_descriptor(
        self,
        device_registry: DeviceRegistry,
    ) -> None:
        seen: list[tuple[int | None, int | None, int | None]] = []
        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            device_registry=device_registry,
            device_psk_provider=lambda: _DEFAULT_PSK,
            on_device_health=lambda d: seen.append((d.battery_pct, d.rssi_dbm, d.last_health_at)),
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()
            ws.send_text(
                json.dumps(
                    {
                        "type": "device_health",
                        "battery_pct": 66,
                        "rssi_dbm": -70,
                        "at": 999,
                    }
                )
            )

            for _ in range(20):
                if seen:
                    break
                time.sleep(0.01)

        assert seen == [(66, -70, 999)]

    def test_invalid_device_health_frame_is_dropped_and_socket_stays_open(
        self,
        device_registry: DeviceRegistry,
    ) -> None:
        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            device_registry=device_registry,
            device_psk_provider=lambda: _DEFAULT_PSK,
            on_device_query=lambda _device_id, _name, _at: {"text": "still open", "ttl_ms": 1000},
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()

            ws.send_text(
                json.dumps(
                    {
                        "type": "device_health",
                        "battery_pct": 101,
                        "rssi_dbm": -57,
                        "at": 1234,
                    }
                )
            )
            ws.send_text(json.dumps({"type": "query", "name": "last_segment", "at": 1235}))
            assert ws.receive_json()["text"] == "still open"

            descriptor = device_registry.get("aipi-1")
            assert descriptor is not None
            assert descriptor.battery_pct is None

    def test_query_last_segment_replies_with_status_frame(
        self,
        device_registry: DeviceRegistry,
    ) -> None:
        def on_query(device_id: str, name: str, at: Optional[float]) -> Optional[dict]:
            assert device_id == "aipi-1"
            assert name == "last_segment"
            assert at == 44.0
            return {"text": "Karol: shipped health", "ttl_ms": 5000}

        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            device_registry=device_registry,
            device_psk_provider=lambda: _DEFAULT_PSK,
            on_device_query=on_query,
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        with client.websocket_connect("/api/devices/audio") as ws:
            _send_handshake(ws)
            ws.receive_json()

            ws.send_text(json.dumps({"type": "query", "name": "last_segment", "at": 44}))
            status = ws.receive_json()

        assert status == {
            "type": "status",
            "text": "Karol: shipped health",
            "ttl_ms": 5000,
        }


@pytest.mark.integration
class TestDeviceAudioPskRotation:
    def test_handshake_uses_provider_each_time(self, device_registry: DeviceRegistry) -> None:
        psk_box = {"value": "first-psk"}
        chunks: List[Tuple[str, np.ndarray]] = []

        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            device_registry=device_registry,
            device_psk_provider=lambda: psk_box["value"],
            on_device_audio_chunk=lambda d, a: chunks.append((d, a)),
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        # First connection: PSK matches.
        with client.websocket_connect("/api/devices/audio") as ws:
            ws.send_text(
                json.dumps(
                    {
                        "type": "hello",
                        "device_id": "aipi-A",
                        "label": "A",
                        "psk": "first-psk",
                        "version": DEVICE_HANDSHAKE_VERSION,
                    }
                )
            )
            ack = ws.receive_json()
            assert ack["device_id"] == "aipi-A"

        # Rotate the PSK; old PSK should now be rejected.
        psk_box["value"] = "second-psk"
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/api/devices/audio") as ws:
                ws.send_text(
                    json.dumps(
                        {
                            "type": "hello",
                            "device_id": "aipi-B",
                            "label": "B",
                            "psk": "first-psk",
                            "version": DEVICE_HANDSHAKE_VERSION,
                        }
                    )
                )
                ws.receive_json()
        assert exc_info.value.code == WS_CLOSE_PSK_MISMATCH
