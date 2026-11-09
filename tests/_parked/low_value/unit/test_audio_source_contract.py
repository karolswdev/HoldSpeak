# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_audio_source_contract.py to restore.

# ruff: noqa


# --- TestAudioSourceContract::test_isinstance_audio_source: P3: tests Python Protocol/isinstance/callable behaviour, not recording
# (was a method of class TestAudioSourceContract)
def test_isinstance_audio_source(self, factory: SourceFactory) -> None:
    src, _ = factory()
    assert isinstance(src, AudioSource), (
        f"{type(src).__name__} does not satisfy the AudioSource Protocol"
    )


# --- TestAudioSourceContract::test_has_start_recording_method: P3: tests Python Protocol/isinstance/callable behaviour, not recording
# (was a method of class TestAudioSourceContract)
def test_has_start_recording_method(self, factory: SourceFactory) -> None:
    src, _ = factory()
    assert callable(getattr(src, "start_recording", None))


# --- TestAudioSourceContract::test_has_stop_recording_method: P3: tests Python Protocol/isinstance/callable behaviour, not recording
# (was a method of class TestAudioSourceContract)
def test_has_stop_recording_method(self, factory: SourceFactory) -> None:
    src, _ = factory()
    assert callable(getattr(src, "stop_recording", None))


# --- TestAudioSourceProtocolSelf: P3: tests Python Protocol/isinstance/callable behaviour, not recording
class TestAudioSourceProtocolSelf:
    """Sanity checks on the Protocol declaration itself."""

    def test_protocol_is_runtime_checkable(self) -> None:
        # ``isinstance`` against a Protocol only works when
        # ``@runtime_checkable`` was applied — test the affirmative
        # case here to lock that decorator in place.
        assert isinstance(RemoteAudioRecorder(), AudioSource)

    def test_random_object_does_not_satisfy_protocol(self) -> None:
        class NotAnAudioSource:
            pass

        assert not isinstance(NotAnAudioSource(), AudioSource)
