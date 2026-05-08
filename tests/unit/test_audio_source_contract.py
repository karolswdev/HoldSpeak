"""Shape contract test for the ``AudioSource`` Protocol (HS-14-01).

This test pins the substrate-level contract every audio source must
honour. It runs the same checks against every implementation
HoldSpeak ships, so a future source (e.g. a file-backed test
double, or a different transport in phase 15) only has to land here
to be wired into both the voice-typing and meeting paths.

The contract is intentionally minimal — start/stop, output shape,
and "stop without start raises". Behavioral specifics (resampling,
overflow policy, etc.) live in each implementation's own test
module; the goal here is structural conformance, not behavior.
"""

from __future__ import annotations

from typing import Callable, Tuple

import numpy as np
import pytest

from holdspeak.audio import AudioRecorder, AudioRecorderError, AudioSource
from holdspeak.device_audio import (
    RemoteAudioRecorder,
    RemoteAudioRecorderError,
)


SourceFactory = Callable[[], Tuple[AudioSource, type]]


def _local_recorder() -> Tuple[AudioSource, type]:
    """Return a real ``AudioRecorder``; sounddevice import is not required for shape checks."""
    return AudioRecorder(), AudioRecorderError


def _remote_recorder() -> Tuple[AudioSource, type]:
    return RemoteAudioRecorder(), RemoteAudioRecorderError


@pytest.fixture(
    params=[
        pytest.param(_local_recorder, id="AudioRecorder"),
        pytest.param(_remote_recorder, id="RemoteAudioRecorder"),
    ],
)
def factory(request: pytest.FixtureRequest) -> SourceFactory:
    return request.param


class TestAudioSourceContract:
    """Every AudioSource implementation must pass these."""

    def test_isinstance_audio_source(self, factory: SourceFactory) -> None:
        src, _ = factory()
        assert isinstance(src, AudioSource), (
            f"{type(src).__name__} does not satisfy the AudioSource Protocol"
        )

    def test_has_start_recording_method(self, factory: SourceFactory) -> None:
        src, _ = factory()
        assert callable(getattr(src, "start_recording", None))

    def test_has_stop_recording_method(self, factory: SourceFactory) -> None:
        src, _ = factory()
        assert callable(getattr(src, "stop_recording", None))

    def test_stop_without_start_raises(self, factory: SourceFactory) -> None:
        src, error_type = factory()
        with pytest.raises(error_type):
            src.stop_recording()


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
