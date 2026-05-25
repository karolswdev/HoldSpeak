"""Integration test: meeting path consumes device streams (HS-14-06).

Drives ``MeetingSession.attach_device`` plus the public
``_transcribe_chunks`` path with a fake transcriber and a fake
audio source so the per-segment ``device_id`` and speaker-label
contract can be asserted without spinning up sounddevice or
Whisper. The HTTP-side parts (``POST /api/meeting/start`` body
parsing + 404 on unknown device) are covered against
``MeetingWebServer`` via FastAPI ``TestClient``.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import numpy as np
import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from holdspeak.device_audio import DeviceDescriptor, DeviceRegistry
from holdspeak.meeting import AudioChunk
from holdspeak.meeting_session import (
    MeetingSession,
    MeetingState,
    TranscriptSegment,
)
from holdspeak.web_server import MeetingWebServer


class _FakeTranscriber:
    model_name = "fake"

    def __init__(self) -> None:
        self.calls: List[np.ndarray] = []

    def transcribe(self, audio: np.ndarray) -> str:
        self.calls.append(audio)
        # Return a stable transcript so the test can assert text content.
        return f"transcript({audio.size})"


class _FakeRemoteSource:
    """Minimal AudioSource + drain double, no networking."""

    def __init__(self) -> None:
        self.is_recording = False
        self._buffer = np.array([], dtype=np.float32)

    def start_recording(self) -> None:
        self.is_recording = True
        self._buffer = np.array([], dtype=np.float32)

    def stop_recording(self) -> np.ndarray:
        audio = self._buffer
        self._buffer = np.array([], dtype=np.float32)
        self.is_recording = False
        return audio

    def drain(self) -> np.ndarray:
        if not self.is_recording:
            return np.array([], dtype=np.float32)
        out = self._buffer
        self._buffer = np.array([], dtype=np.float32)
        return out

    def feed(self, audio: np.ndarray) -> None:
        self._buffer = np.concatenate([self._buffer, audio.astype(np.float32)])


class _StubMeetingRecorder:
    """Stand-in for the MeetingRecorder so tests don't need sounddevice.

    Records device-stream registrations the same way the real
    recorder does and supports ``get_pending_device_chunks`` /
    ``device_label`` / ``registered_device_ids`` so
    ``_transcribe_chunks`` is reachable.
    """

    def __init__(self) -> None:
        self.has_system_audio = False
        self._device_sources: dict[str, _FakeRemoteSource] = {}
        self._device_labels: dict[str, str] = {}
        self._start_time: Optional[float] = 0.0
        self.sample_rate = 16_000

    def register_device_stream(
        self, device_id: str, source: _FakeRemoteSource, *, label: str
    ) -> None:
        self._device_sources[device_id] = source
        self._device_labels[device_id] = label

    def unregister_device_stream(self, device_id: str) -> None:
        self._device_sources.pop(device_id, None)
        self._device_labels.pop(device_id, None)

    def device_label(self, device_id: str) -> Optional[str]:
        return self._device_labels.get(device_id)

    def registered_device_ids(self) -> list[str]:
        return list(self._device_sources.keys())

    def get_pending_device_chunks(self) -> dict[str, list[AudioChunk]]:
        result: dict[str, list[AudioChunk]] = {}
        for device_id, source in self._device_sources.items():
            audio = source.drain()
            if audio.size == 0:
                continue
            duration = audio.size / float(self.sample_rate)
            chunk = AudioChunk(
                audio=audio,
                timestamp=0.0,
                source=device_id,
                duration=duration,
            )
            result[device_id] = [chunk]
        return result


@pytest.mark.integration
class TestDeviceMeetingSession:
    def test_attach_device_records_descriptor_and_starts_source(self) -> None:
        session = MeetingSession(transcriber=_FakeTranscriber())
        session._state = MeetingState(id="m1", started_at=datetime.now())
        session._recorder = _StubMeetingRecorder()  # type: ignore[assignment]

        descriptor = DeviceDescriptor(
            id="aipi-1",
            label="Karol",
            connected_at=datetime.now(),
            last_seen=datetime.now(),
        )
        source = _FakeRemoteSource()

        session.attach_device(descriptor, source)  # type: ignore[arg-type]

        assert source.is_recording is True
        assert session.is_device_attached("aipi-1") is True
        assert any(d.id == "aipi-1" for d in session.state.devices)

    def test_update_device_descriptor_refreshes_health_snapshot(self) -> None:
        session = MeetingSession(transcriber=_FakeTranscriber())
        session._state = MeetingState(id="m1", started_at=datetime.now())
        session._recorder = _StubMeetingRecorder()  # type: ignore[assignment]

        descriptor = DeviceDescriptor(
            id="aipi-1",
            label="Karol",
            connected_at=datetime.now(),
            last_seen=datetime.now(),
        )
        source = _FakeRemoteSource()
        session.attach_device(descriptor, source)  # type: ignore[arg-type]

        refreshed = DeviceDescriptor(
            id="aipi-1",
            label="Karol",
            connected_at=descriptor.connected_at,
            last_seen=datetime.now(),
            battery_pct=73,
            rssi_dbm=-59,
            last_health_at=42,
        )

        assert session.update_device_descriptor(refreshed) is True
        [payload] = session.state.to_dict()["devices"]
        assert payload["battery_pct"] == 73
        assert payload["rssi_dbm"] == -59
        assert payload["last_health_at"] == 42

    def test_device_chunks_become_labeled_segments(self) -> None:
        transcriber = _FakeTranscriber()
        session = MeetingSession(transcriber=transcriber)
        session._state = MeetingState(id="m1", started_at=datetime.now())
        session._recorder = _StubMeetingRecorder()  # type: ignore[assignment]

        # Attach a device.
        descriptor = DeviceDescriptor(
            id="aipi-1",
            label="Karol",
            connected_at=datetime.now(),
            last_seen=datetime.now(),
        )
        device_source = _FakeRemoteSource()
        session.attach_device(descriptor, device_source)  # type: ignore[arg-type]

        # Feed the device with 1.5 s of audio (above the
        # MIN_CHUNK_DURATION = 1.0 floor).
        device_source.feed(np.full(int(1.5 * 16_000), 0.1, dtype=np.float32))

        # Pull device chunks the same way the transcription loop does.
        device_chunks = session._recorder.get_pending_device_chunks()  # type: ignore[union-attr]
        session._transcribe_chunks([], [], device_chunks=device_chunks)

        # Mic stream contributes a segment with no device_id; we
        # didn't drive that here, so only the device segment exists.
        segments = session.state.segments
        assert len(segments) == 1
        seg = segments[0]
        assert seg.device_id == "aipi-1"
        assert seg.speaker == "Karol"
        assert seg.text == f"transcript({int(1.5 * 16_000)})"

    def test_local_mic_segment_keeps_device_id_none(self) -> None:
        transcriber = _FakeTranscriber()
        session = MeetingSession(transcriber=transcriber, mic_label="Me")
        session._state = MeetingState(id="m1", started_at=datetime.now())
        session._recorder = _StubMeetingRecorder()  # type: ignore[assignment]

        mic_chunks = [
            AudioChunk(
                audio=np.full(int(1.2 * 16_000), 0.05, dtype=np.float32),
                timestamp=0.0,
                source="mic",
                duration=1.2,
            )
        ]
        session._transcribe_chunks(mic_chunks, [], device_chunks={})

        assert len(session.state.segments) == 1
        seg = session.state.segments[0]
        assert seg.device_id is None
        assert seg.speaker == "Me"

    def test_detach_device_stops_source_and_unregisters(self) -> None:
        session = MeetingSession(transcriber=_FakeTranscriber())
        session._state = MeetingState(id="m1", started_at=datetime.now())
        session._recorder = _StubMeetingRecorder()  # type: ignore[assignment]

        descriptor = DeviceDescriptor(
            id="aipi-1",
            label="Karol",
            connected_at=datetime.now(),
            last_seen=datetime.now(),
        )
        source = _FakeRemoteSource()
        session.attach_device(descriptor, source)  # type: ignore[arg-type]
        assert session.is_device_attached("aipi-1") is True

        session.detach_device("aipi-1")
        assert session.is_device_attached("aipi-1") is False
        assert source.is_recording is False


@pytest.mark.integration
class TestMeetingStartDevicesApi:
    def test_meeting_start_passes_devices_to_on_start(self) -> None:
        captured: dict[str, object] = {}

        def fake_on_start(*, devices: Optional[list[str]] = None) -> dict[str, object]:
            captured["devices"] = list(devices) if devices else []
            return {"id": "m1", "started_at": datetime.now().isoformat()}

        registry = DeviceRegistry()
        registry.register("aipi-1", "Karol")

        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            on_start=fake_on_start,
            get_state=lambda: {},
            device_registry=registry,
            device_psk_provider=lambda: "",
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        response = client.post("/api/meeting/start", json={"devices": ["aipi-1"]})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["success"] is True
        assert captured["devices"] == ["aipi-1"]

    def test_meeting_start_unknown_device_returns_404(self) -> None:
        from holdspeak.web_server import _UnknownDeviceError

        def fake_on_start(*, devices: Optional[list[str]] = None) -> dict[str, object]:
            assert devices is not None
            for did in devices:
                raise _UnknownDeviceError(did)
            return {"id": "m1", "started_at": datetime.now().isoformat()}

        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            on_start=fake_on_start,
            get_state=lambda: {},
            device_registry=DeviceRegistry(),
            device_psk_provider=lambda: "",
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        response = client.post("/api/meeting/start", json={"devices": ["ghost"]})
        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert body["device_id"] == "ghost"

    def test_meeting_start_legacy_no_body_works(self) -> None:
        called: list[bool] = []

        def fake_on_start() -> dict[str, object]:
            called.append(True)
            return {"id": "legacy", "started_at": datetime.now().isoformat()}

        server = MeetingWebServer(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            on_start=fake_on_start,
            get_state=lambda: {},
            device_registry=DeviceRegistry(),
            device_psk_provider=lambda: "",
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        response = client.post("/api/meeting/start")
        assert response.status_code == 200, response.text
        assert called == [True]
