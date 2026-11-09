"""Unit tests for audio resampling functionality."""

from __future__ import annotations

import numpy as np
import pytest

from holdspeak.audio import _linear_resample_mono


class TestLinearResampleMono:
    """Tests for _linear_resample_mono function."""

    # ============================================================
    # Basic Functionality Tests
    # ============================================================

    def test_same_rate_returns_copy(self, silence_1s: np.ndarray) -> None:
        """Same rate returns a float32 copy without modification."""
        result = _linear_resample_mono(silence_1s, 16000, 16000)
        assert result.dtype == np.float32
        np.testing.assert_array_equal(result, silence_1s)
        # Ensure it's a copy or view with same dtype behavior
        assert result.shape == silence_1s.shape

    def test_same_rate_preserves_values(self, sine_440hz_1s: np.ndarray) -> None:
        """Same rate preserves original values."""
        result = _linear_resample_mono(sine_440hz_1s, 16000, 16000)
        np.testing.assert_array_almost_equal(result, sine_440hz_1s)

    # ============================================================
    # Upsampling Tests
    # ============================================================

    def test_upsample_doubles_length(self) -> None:
        """Upsampling from 8kHz to 16kHz approximately doubles length."""
        # Create a simple 8kHz audio (1 second = 8000 samples)
        audio_8k = np.zeros(8000, dtype=np.float32)
        result = _linear_resample_mono(audio_8k, 8000, 16000)
        # Should be approximately 16000 samples (1 second at 16kHz)
        assert len(result) == 16000

    # ============================================================
    # Downsampling Tests
    # ============================================================

    def test_downsample_halves_length(self, silence_1s: np.ndarray) -> None:
        """Downsampling from 16kHz to 8kHz halves length."""
        result = _linear_resample_mono(silence_1s, 16000, 8000)
        assert len(result) == 8000

    def test_downsample_from_48khz(self) -> None:
        """Downsampling from 48kHz to 16kHz (common device fallback)."""
        audio_48k = np.zeros(48000, dtype=np.float32)  # 1 second at 48kHz
        result = _linear_resample_mono(audio_48k, 48000, 16000)
        assert len(result) == 16000  # 1 second at 16kHz

    def test_downsample_from_44100hz(self) -> None:
        """Downsampling from 44.1kHz to 16kHz."""
        audio_44k = np.zeros(44100, dtype=np.float32)  # 1 second at 44.1kHz
        result = _linear_resample_mono(audio_44k, 44100, 16000)
        assert len(result) == 16000  # 1 second at 16kHz

    # ============================================================
    # Edge Cases
    # ============================================================

    def test_empty_array_returns_empty(self) -> None:
        """Empty array input returns empty float32 array."""
        empty = np.array([], dtype=np.float32)
        result = _linear_resample_mono(empty, 16000, 8000)
        assert len(result) == 0
        assert result.dtype == np.float32

    # ============================================================
    # DC Component / Constant Signal Tests
    # ============================================================

    def test_preserves_dc_component_upsample(self) -> None:
        """Constant (DC) signal stays constant after upsampling."""
        dc_signal = np.full(8000, 0.75, dtype=np.float32)
        result = _linear_resample_mono(dc_signal, 8000, 16000)
        # All values should remain 0.75
        np.testing.assert_array_almost_equal(result, np.full(len(result), 0.75))

    def test_preserves_dc_component_downsample(self) -> None:
        """Constant (DC) signal stays constant after downsampling."""
        dc_signal = np.full(16000, -0.5, dtype=np.float32)
        result = _linear_resample_mono(dc_signal, 16000, 8000)
        np.testing.assert_array_almost_equal(result, np.full(len(result), -0.5))

    def test_zero_signal_stays_zero(self, silence_1s: np.ndarray) -> None:
        """Zero (silence) signal stays zero after resampling."""
        result = _linear_resample_mono(silence_1s, 16000, 8000)
        np.testing.assert_array_almost_equal(result, np.zeros(8000, dtype=np.float32))

    # ============================================================
    # Output Type Tests
    # ============================================================

    def test_output_dtype_float32_from_float64(self) -> None:
        """Input float64 produces float32 output."""
        audio_f64 = np.zeros(8000, dtype=np.float64)
        result = _linear_resample_mono(audio_f64, 8000, 16000)
        assert result.dtype == np.float32

    def test_output_dtype_float32_from_int16(self) -> None:
        """Input int16 produces float32 output."""
        audio_int16 = np.zeros(8000, dtype=np.int16)
        result = _linear_resample_mono(audio_int16, 8000, 16000)
        assert result.dtype == np.float32

    # ============================================================
    # Error Handling Tests
    # ============================================================

    def test_raises_on_2d_array(self) -> None:
        """Raises ValueError for 2D (stereo) input."""
        stereo = np.zeros((16000, 2), dtype=np.float32)
        with pytest.raises(ValueError, match="1D mono"):
            _linear_resample_mono(stereo, 16000, 8000)

    def test_raises_on_zero_src_rate(self, silence_1s: np.ndarray) -> None:
        """Raises ValueError for zero source rate."""
        with pytest.raises(ValueError, match="positive"):
            _linear_resample_mono(silence_1s, 0, 16000)

    def test_raises_on_zero_dst_rate(self, silence_1s: np.ndarray) -> None:
        """Raises ValueError for zero destination rate."""
        with pytest.raises(ValueError, match="positive"):
            _linear_resample_mono(silence_1s, 16000, 0)

