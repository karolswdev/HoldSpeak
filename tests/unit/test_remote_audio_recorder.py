"""Unit tests for ``RemoteAudioRecorder`` (HS-14-01)."""

from __future__ import annotations

import logging

import numpy as np
import pytest

from holdspeak.device_audio import (
    RemoteAudioRecorder,
    RemoteAudioRecorderError,
)


def _int16_le(samples: np.ndarray) -> bytes:
    """Encode a float32 [-1, 1) array as int16 LE PCM bytes."""
    clipped = np.clip(samples, -1.0, 1.0 - 1.0 / 32768.0)
    return (clipped * 32768.0).astype("<i2").tobytes()


class TestRemoteAudioRecorder:
    """Behavioral tests for the pushed-PCM audio source."""

    def test_start_then_stop_with_no_push_returns_empty(self) -> None:
        rec = RemoteAudioRecorder()
        rec.start_recording()
        out = rec.stop_recording()
        assert isinstance(out, np.ndarray)
        assert out.dtype == np.float32
        assert out.size == 0

    def test_push_then_stop_returns_concatenation(self) -> None:
        rec = RemoteAudioRecorder()
        rec.start_recording()

        first = np.linspace(-0.5, 0.5, 800, dtype=np.float32)
        second = np.linspace(0.25, -0.25, 400, dtype=np.float32)

        rec.push(_int16_le(first))
        rec.push(_int16_le(second))
        out = rec.stop_recording()

        assert out.dtype == np.float32
        assert out.shape == (1200,)
        # Round-tripping through int16 introduces small quantization,
        # so compare with a generous absolute tolerance.
        np.testing.assert_allclose(out[:800], first, atol=2.0 / 32768.0)
        np.testing.assert_allclose(out[800:], second, atol=2.0 / 32768.0)

    def test_buffer_overflow_drops_oldest_with_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        # Cap at 0.05 s @ 16 kHz = 800 samples.
        rec = RemoteAudioRecorder(max_buffer_seconds=0.05)
        rec.start_recording()

        old = np.full(800, 0.1, dtype=np.float32)  # fills the cap exactly
        new = np.full(400, 0.9, dtype=np.float32)  # overflows by 400

        with caplog.at_level(logging.WARNING, logger="holdspeak.audio.remote"):
            rec.push(_int16_le(old))
            rec.push(_int16_le(new))

        out = rec.stop_recording()
        # Oldest frame (the 800-sample 0.1 burst) was dropped; only
        # the newer 400-sample 0.9 burst should survive.
        assert out.shape == (400,)
        np.testing.assert_allclose(out, new, atol=2.0 / 32768.0)

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("remote_audio_buffer_overflow" in r.getMessage() for r in warnings)
        overflow = next(r for r in warnings if "remote_audio_buffer_overflow" in r.getMessage())
        assert getattr(overflow, "dropped_samples", 0) == 800

    def test_stop_without_start_raises(self) -> None:
        rec = RemoteAudioRecorder()
        with pytest.raises(RemoteAudioRecorderError, match="not started"):
            rec.stop_recording()

    def test_double_start_raises(self) -> None:
        rec = RemoteAudioRecorder()
        rec.start_recording()
        try:
            with pytest.raises(RemoteAudioRecorderError, match="already started"):
                rec.start_recording()
        finally:
            rec.stop_recording()

    def test_bytes_pushed_after_stop_are_ignored(self) -> None:
        rec = RemoteAudioRecorder()
        rec.start_recording()
        rec.push(_int16_le(np.full(200, 0.3, dtype=np.float32)))
        first = rec.stop_recording()
        assert first.shape == (200,)

        # Push during the "stopped" gap — should be silently dropped.
        rec.push(_int16_le(np.full(200, 0.7, dtype=np.float32)))

        rec.start_recording()
        second = rec.stop_recording()
        assert second.size == 0  # nothing carried over

    def test_bytes_pushed_before_start_are_ignored(self) -> None:
        rec = RemoteAudioRecorder()
        rec.push(_int16_le(np.full(200, 0.5, dtype=np.float32)))

        rec.start_recording()
        out = rec.stop_recording()
        assert out.size == 0

    def test_resample_path_produces_target_rate_float32(self) -> None:
        # On-wire rate 8 kHz → resample to 16 kHz on stop.
        rec = RemoteAudioRecorder(wire_sample_rate=8_000)
        rec.start_recording()

        # 1 second of audio at 8 kHz = 8000 samples.
        samples = np.full(8000, 0.25, dtype=np.float32)
        rec.push(_int16_le(samples))
        out = rec.stop_recording()

        assert out.dtype == np.float32
        # 1 second at 16 kHz target = ~16000 samples.
        assert abs(out.size - 16_000) <= 1
        # DC level should survive linear resampling.
        np.testing.assert_allclose(out, np.full(out.size, 0.25), atol=2.0 / 32768.0)

    def test_int16_decoding_preserves_extremes(self) -> None:
        rec = RemoteAudioRecorder()
        rec.start_recording()
        # int16 min/zero/max bytes (LE).
        rec.push(b"\x00\x80" + b"\x00\x00" + b"\xff\x7f")
        out = rec.stop_recording()
        assert out.shape == (3,)
        assert out[0] == pytest.approx(-1.0, abs=1e-6)
        assert out[1] == pytest.approx(0.0, abs=1e-6)
        assert out[2] == pytest.approx((32767 / 32768.0), abs=1e-6)

    def test_odd_trailing_byte_is_dropped(self) -> None:
        rec = RemoteAudioRecorder()
        rec.start_recording()
        # 4 bytes (2 valid samples) + 1 trailing byte.
        rec.push(b"\x00\x00\x00\x00\xff")
        out = rec.stop_recording()
        assert out.shape == (2,)
        assert np.all(out == 0)

    def test_empty_push_is_noop(self) -> None:
        rec = RemoteAudioRecorder()
        rec.start_recording()
        rec.push(b"")
        out = rec.stop_recording()
        assert out.size == 0

    def test_invalid_constructor_args_raise(self) -> None:
        with pytest.raises(ValueError):
            RemoteAudioRecorder(sample_rate=0)
        with pytest.raises(ValueError):
            RemoteAudioRecorder(wire_sample_rate=-1)
        with pytest.raises(ValueError):
            RemoteAudioRecorder(max_buffer_seconds=0)
