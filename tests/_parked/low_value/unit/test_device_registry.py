# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_device_registry.py to restore.

# ruff: noqa


# --- TestDeviceRegistry::test_recorder_for_returns_audio_source: P6: isinstance checks on the returned recorder
# (was a method of class TestDeviceRegistry)
def test_recorder_for_returns_audio_source(self) -> None:
    reg = DeviceRegistry()
    reg.register("aipi-1", "Karol")
    recorder = reg.recorder_for("aipi-1")
    assert recorder is not None
    assert isinstance(recorder, AudioSource)
    assert isinstance(recorder, RemoteAudioRecorder)
