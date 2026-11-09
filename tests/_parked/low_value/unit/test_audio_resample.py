# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_audio_resample.py to restore.

# ruff: noqa


# --- TestLinearResampleMono::test_upsample_with_sine_wave: P5: repeats another case in this class (same length/dtype/raise check on the same path)
# (was a method of class TestLinearResampleMono)
def test_upsample_with_sine_wave(self) -> None:
    """Upsampling a sine wave preserves frequency characteristics."""
    # 440Hz at 8kHz sample rate, 0.5 seconds
    t = np.linspace(0, 0.5, 4000, dtype=np.float32)
    audio_8k = np.sin(2 * np.pi * 440 * t).astype(np.float32)

    result = _linear_resample_mono(audio_8k, 8000, 16000)
    assert len(result) == 8000  # 0.5 seconds at 16kHz


# --- TestLinearResampleMono::test_upsample_4x: P5: repeats another case in this class (same length/dtype/raise check on the same path)
# (was a method of class TestLinearResampleMono)
def test_upsample_4x(self) -> None:
    """Upsampling 4x (4kHz to 16kHz)."""
    audio_4k = np.ones(4000, dtype=np.float32)  # 1 second at 4kHz
    result = _linear_resample_mono(audio_4k, 4000, 16000)
    assert len(result) == 16000  # 1 second at 16kHz


# --- TestLinearResampleMono::test_downsample_with_sine_wave: P5: repeats another case in this class (same length/dtype/raise check on the same path)
# (was a method of class TestLinearResampleMono)
def test_downsample_with_sine_wave(self, sine_440hz_1s: np.ndarray) -> None:
    """Downsampling a sine wave preserves duration."""
    result = _linear_resample_mono(sine_440hz_1s, 16000, 8000)
    # 1 second at 8kHz = 8000 samples
    assert len(result) == 8000


# --- TestLinearResampleMono::test_empty_array_same_rate: P5: repeats another case in this class (same length/dtype/raise check on the same path)
# (was a method of class TestLinearResampleMono)
def test_empty_array_same_rate(self) -> None:
    """Empty array with same rate returns empty float32."""
    empty = np.array([], dtype=np.float32)
    result = _linear_resample_mono(empty, 16000, 16000)
    assert len(result) == 0
    assert result.dtype == np.float32


# --- TestLinearResampleMono::test_preserves_dc_component_same_rate: P5: repeats another case in this class (same length/dtype/raise check on the same path)
# (was a method of class TestLinearResampleMono)
def test_preserves_dc_component_same_rate(self) -> None:
    """Constant signal stays constant with same rate."""
    dc_signal = np.full(16000, 0.25, dtype=np.float32)
    result = _linear_resample_mono(dc_signal, 16000, 16000)
    np.testing.assert_array_almost_equal(result, dc_signal)


# --- TestLinearResampleMono::test_output_dtype_is_float32: P5: repeats another case in this class (same length/dtype/raise check on the same path)
# (was a method of class TestLinearResampleMono)
def test_output_dtype_is_float32(self, silence_1s: np.ndarray) -> None:
    """Output dtype is always float32."""
    result = _linear_resample_mono(silence_1s, 16000, 8000)
    assert result.dtype == np.float32


# --- TestLinearResampleMono::test_output_dtype_float32_same_rate: P5: repeats another case in this class (same length/dtype/raise check on the same path)
# (was a method of class TestLinearResampleMono)
def test_output_dtype_float32_same_rate(self) -> None:
    """Same rate conversion still produces float32."""
    audio_f64 = np.zeros(16000, dtype=np.float64)
    result = _linear_resample_mono(audio_f64, 16000, 16000)
    assert result.dtype == np.float32


# --- TestLinearResampleMono::test_raises_on_negative_rates: P5: repeats another case in this class (same length/dtype/raise check on the same path)
# (was a method of class TestLinearResampleMono)
def test_raises_on_negative_rates(self, silence_1s: np.ndarray) -> None:
    """Raises ValueError for negative sample rates."""
    with pytest.raises(ValueError, match="positive"):
        _linear_resample_mono(silence_1s, -16000, 8000)
    with pytest.raises(ValueError, match="positive"):
        _linear_resample_mono(silence_1s, 16000, -8000)


# --- TestLinearResampleMono::test_single_sample: P1: asserts the length is 2 or 0, so it cannot fail
# (was a method of class TestLinearResampleMono)
def test_single_sample(self) -> None:
    """Single sample input."""
    single = np.array([0.5], dtype=np.float32)
    result = _linear_resample_mono(single, 16000, 32000)
    # Duration is 1/16000 seconds, at 32000 Hz = 2 samples
    assert len(result) == 2 or len(result) == 0  # Depends on rounding
