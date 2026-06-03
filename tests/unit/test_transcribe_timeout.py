"""HS-25-05: transcription is bounded by a timeout and fails safe."""

from __future__ import annotations

import time

import numpy as np
import pytest

from holdspeak.transcribe import Transcriber, TranscriberError, TranscriberTimeoutError


class _SlowImpl:
    device = "cpu"
    compute_type = "int8"

    def __init__(self, delay: float) -> None:
        self.delay = delay
        self.calls = 0

    def transcribe(self, audio_array):
        self.calls += 1
        time.sleep(self.delay)
        return "done"


def _transcriber_with_impl(impl, timeout_seconds: float) -> Transcriber:
    # Bypass __init__'s backend resolution; we only exercise transcribe().
    t = Transcriber.__new__(Transcriber)
    t.backend = "fake"
    t.timeout_seconds = float(timeout_seconds)
    t._impl = impl
    t.model_name = "base"
    t.device = impl.device
    t.compute_type = impl.compute_type
    return t


def test_transcription_timeout_raises_and_recovers():
    impl = _SlowImpl(delay=5.0)
    t = _transcriber_with_impl(impl, timeout_seconds=0.1)

    with pytest.raises(TranscriberTimeoutError) as excinfo:
        t.transcribe(np.zeros(16000, dtype=np.float32))
    assert "abandoned" in str(excinfo.value)
    # TranscriberTimeoutError must be a TranscriberError so the runtime's
    # existing handler catches it (notify + return to idle).
    assert isinstance(excinfo.value, TranscriberError)

    # The Transcriber instance is reusable — a subsequent fast call works,
    # mirroring the runtime returning to idle for the next utterance.
    fast = _SlowImpl(delay=0.0)
    t._impl = fast
    assert t.transcribe(np.zeros(16000, dtype=np.float32)) == "done"
    assert fast.calls == 1


def test_fast_transcription_under_timeout_returns_normally():
    impl = _SlowImpl(delay=0.0)
    t = _transcriber_with_impl(impl, timeout_seconds=5.0)
    assert t.transcribe(np.zeros(16000, dtype=np.float32)) == "done"


def test_timeout_disabled_runs_inline():
    impl = _SlowImpl(delay=0.0)
    t = _transcriber_with_impl(impl, timeout_seconds=0.0)
    assert t.transcribe(np.zeros(16000, dtype=np.float32)) == "done"
    # Disabled timeout means no worker thread is involved; just a direct call.
    assert impl.calls == 1


def test_backend_error_propagates_through_timeout_path():
    class _BoomImpl(_SlowImpl):
        def transcribe(self, audio_array):
            raise TranscriberError("backend boom")

    t = _transcriber_with_impl(_BoomImpl(delay=0.0), timeout_seconds=5.0)
    with pytest.raises(TranscriberError, match="backend boom"):
        t.transcribe(np.zeros(16000, dtype=np.float32))
