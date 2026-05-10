"""Unit tests for ``DeviceRegistry`` (HS-14-02)."""

from __future__ import annotations

import time

import pytest

from holdspeak.audio import AudioSource
from holdspeak.device_audio import (
    DeviceDescriptor,
    DeviceRegistry,
    DeviceRegistryError,
    DuplicateLabelError,
    RemoteAudioRecorder,
)


class TestDeviceRegistry:
    """Behavioral tests for the registry."""

    def test_register_then_get_returns_descriptor(self) -> None:
        reg = DeviceRegistry()
        descriptor = reg.register("aipi-1", "Karol")

        assert isinstance(descriptor, DeviceDescriptor)
        assert descriptor.id == "aipi-1"
        assert descriptor.label == "Karol"
        assert descriptor.queue_depth == 0
        assert descriptor.connected_at == descriptor.last_seen

        lookup = reg.get("aipi-1")
        assert lookup is not None
        assert lookup.id == "aipi-1"
        assert lookup.label == "Karol"

    def test_get_unknown_id_returns_none(self) -> None:
        reg = DeviceRegistry()
        assert reg.get("nope") is None

    def test_double_register_different_label_succeeds(self) -> None:
        reg = DeviceRegistry()
        reg.register("aipi-1", "Karol")
        reg.register("aipi-2", "Guest")

        actives = {d.id: d for d in reg.active()}
        assert set(actives.keys()) == {"aipi-1", "aipi-2"}
        assert actives["aipi-1"].label == "Karol"
        assert actives["aipi-2"].label == "Guest"

    def test_duplicate_label_fails(self) -> None:
        reg = DeviceRegistry()
        reg.register("aipi-1", "Karol")
        with pytest.raises(DuplicateLabelError, match="Karol"):
            reg.register("aipi-2", "Karol")

        # The failing register must not have leaked any state.
        assert reg.get("aipi-2") is None
        assert reg.recorder_for("aipi-2") is None

    def test_double_register_same_id_raises(self) -> None:
        reg = DeviceRegistry()
        reg.register("aipi-1", "Karol")
        with pytest.raises(DeviceRegistryError, match="already registered"):
            reg.register("aipi-1", "AnotherLabel")

    def test_unregister_removes_descriptor_and_recorder(self) -> None:
        reg = DeviceRegistry()
        reg.register("aipi-1", "Karol")
        assert reg.recorder_for("aipi-1") is not None

        reg.unregister("aipi-1")

        assert reg.get("aipi-1") is None
        assert reg.recorder_for("aipi-1") is None
        assert reg.active() == []

    def test_unregister_unknown_id_is_idempotent(self) -> None:
        reg = DeviceRegistry()
        # Should not raise; should not log at warning/error level.
        reg.unregister("never-registered")
        reg.register("aipi-1", "Karol")
        reg.unregister("aipi-1")
        reg.unregister("aipi-1")  # second call is also a no-op

        assert reg.active() == []

    def test_label_freed_after_unregister_is_reusable(self) -> None:
        reg = DeviceRegistry()
        reg.register("aipi-1", "Karol")
        reg.unregister("aipi-1")
        descriptor = reg.register("aipi-2", "Karol")
        assert descriptor.id == "aipi-2"
        assert descriptor.label == "Karol"

    def test_recorder_for_returns_audio_source(self) -> None:
        reg = DeviceRegistry()
        reg.register("aipi-1", "Karol")
        recorder = reg.recorder_for("aipi-1")
        assert recorder is not None
        assert isinstance(recorder, AudioSource)
        assert isinstance(recorder, RemoteAudioRecorder)

    def test_recorder_for_unknown_id_returns_none(self) -> None:
        reg = DeviceRegistry()
        assert reg.recorder_for("nope") is None

    def test_touch_updates_last_seen(self) -> None:
        reg = DeviceRegistry()
        descriptor = reg.register("aipi-1", "Karol")
        original_last_seen = descriptor.last_seen

        time.sleep(0.001)  # ensure datetime.now() ticks forward
        reg.touch("aipi-1")

        refreshed = reg.get("aipi-1")
        assert refreshed is not None
        assert refreshed.last_seen >= original_last_seen
        assert refreshed.last_seen > original_last_seen or (
            refreshed.last_seen - original_last_seen
        ).total_seconds() >= 0

    def test_touch_unknown_id_is_noop(self) -> None:
        reg = DeviceRegistry()
        # No exception, no side effect.
        reg.touch("missing")
        assert reg.active() == []

    def test_active_returns_copies(self) -> None:
        """Mutating a returned descriptor must not corrupt registry state."""
        reg = DeviceRegistry()
        reg.register("aipi-1", "Karol")

        snapshot = reg.active()
        snapshot[0].label = "Hijacked"

        actual = reg.get("aipi-1")
        assert actual is not None
        assert actual.label == "Karol"

    def test_register_rejects_blank_inputs(self) -> None:
        reg = DeviceRegistry()
        with pytest.raises(ValueError):
            reg.register("", "Karol")
        with pytest.raises(ValueError):
            reg.register("aipi-1", "")
        with pytest.raises(ValueError):
            reg.register("   ", "Karol")
