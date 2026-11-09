# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_meeting_chunks.py to restore.

# ruff: noqa


# --- TestAudioChunk::test_creation: P1/P3: constructs a dataclass from literals and reads the literals back
# (was a method of class TestAudioChunk)
def test_creation(self, silence_1s: np.ndarray) -> None:
    """AudioChunk can be created with required fields."""
    chunk = AudioChunk(
        audio=silence_1s,
        timestamp=10.5,
        source="mic",
        duration=1.0,
    )
    assert chunk.timestamp == 10.5
    assert chunk.source == "mic"
    assert chunk.duration == 1.0
    np.testing.assert_array_equal(chunk.audio, silence_1s)


# --- TestAudioChunk::test_source_mic: P1/P3: constructs a dataclass from literals and reads the literals back
# (was a method of class TestAudioChunk)
def test_source_mic(self, silence_1s: np.ndarray) -> None:
    """Mic source chunks."""
    chunk = AudioChunk(audio=silence_1s, timestamp=0.0, source="mic", duration=1.0)
    assert chunk.source == "mic"


# --- TestAudioChunk::test_source_system: P1/P3: constructs a dataclass from literals and reads the literals back
# (was a method of class TestAudioChunk)
def test_source_system(self, silence_1s: np.ndarray) -> None:
    """System source chunks."""
    chunk = AudioChunk(audio=silence_1s, timestamp=0.0, source="system", duration=1.0)
    assert chunk.source == "system"


# --- TestDualStreamBuffer::test_empty_buffer: P1/P3: constructs a dataclass from literals and reads the literals back
# (was a method of class TestDualStreamBuffer)
def test_empty_buffer(self) -> None:
    """New buffer starts empty."""
    buffer = DualStreamBuffer()
    mic, system = buffer.get_all_chunks()
    assert mic == []
    assert system == []


# --- TestAudioChunk::test_end_time_zero_timestamp: P5: repeats the end_time sum, the mic-side add or the concatenate test with other numbers
# (was a method of class TestAudioChunk)
def test_end_time_zero_timestamp(self, silence_1s: np.ndarray) -> None:
    """end_time with zero timestamp."""
    chunk = AudioChunk(
        audio=silence_1s,
        timestamp=0.0,
        source="mic",
        duration=1.0,
    )
    assert chunk.end_time == 1.0


# --- TestAudioChunk::test_end_time_fractional: P5: repeats the end_time sum, the mic-side add or the concatenate test with other numbers
# (was a method of class TestAudioChunk)
def test_end_time_fractional(self, silence_1s: np.ndarray) -> None:
    """end_time with fractional values."""
    chunk = AudioChunk(
        audio=silence_1s,
        timestamp=5.25,
        source="system",
        duration=0.125,
    )
    assert abs(chunk.end_time - 5.375) < 1e-9


# --- TestAudioChunk::test_end_time_zero_duration: P5: repeats the end_time sum, the mic-side add or the concatenate test with other numbers
# (was a method of class TestAudioChunk)
def test_end_time_zero_duration(self, silence_1s: np.ndarray) -> None:
    """end_time equals timestamp when duration is zero."""
    chunk = AudioChunk(
        audio=silence_1s,
        timestamp=15.0,
        source="mic",
        duration=0.0,
    )
    assert chunk.end_time == 15.0


# --- TestDualStreamBuffer::test_add_system_chunk: P5: repeats the end_time sum, the mic-side add or the concatenate test with other numbers
# (was a method of class TestDualStreamBuffer)
def test_add_system_chunk(self, silence_1s: np.ndarray) -> None:
    """Adding system chunk stores it correctly."""
    buffer = DualStreamBuffer()
    buffer.add_system_chunk(silence_1s, timestamp=0.0, duration=1.0)

    mic, system = buffer.get_all_chunks()
    assert len(mic) == 0
    assert len(system) == 1
    assert system[0].source == "system"


# --- TestDualStreamBuffer::test_accumulates_multiple_system_chunks: P5: repeats the end_time sum, the mic-side add or the concatenate test with other numbers
# (was a method of class TestDualStreamBuffer)
def test_accumulates_multiple_system_chunks(self, silence_1s: np.ndarray) -> None:
    """Multiple system chunks accumulate in order."""
    buffer = DualStreamBuffer()
    buffer.add_system_chunk(silence_1s, timestamp=0.5, duration=0.5)
    buffer.add_system_chunk(silence_1s, timestamp=1.0, duration=0.5)

    _, system = buffer.get_all_chunks()
    assert len(system) == 2


# --- TestConcatenateChunks::test_output_dtype_float32: P5: repeats the end_time sum, the mic-side add or the concatenate test with other numbers
# (was a method of class TestConcatenateChunks)
def test_output_dtype_float32(self) -> None:
    """Output is always float32."""
    audio = np.array([1.0, 2.0], dtype=np.float64)  # float64 input
    chunk = AudioChunk(audio=audio.astype(np.float32), timestamp=0.0, source="mic", duration=0.1)
    result = concatenate_chunks([chunk])
    assert result.dtype == np.float32


# --- TestConcatenateChunks::test_preserves_values: P5: repeats the end_time sum, the mic-side add or the concatenate test with other numbers
# (was a method of class TestConcatenateChunks)
def test_preserves_values(self, sine_440hz_1s: np.ndarray) -> None:
    """Concatenation preserves original audio values."""
    chunk1 = AudioChunk(audio=sine_440hz_1s[:8000], timestamp=0.0, source="mic", duration=0.5)
    chunk2 = AudioChunk(audio=sine_440hz_1s[8000:], timestamp=0.5, source="mic", duration=0.5)

    result = concatenate_chunks([chunk1, chunk2])
    np.testing.assert_array_almost_equal(result, sine_440hz_1s)
