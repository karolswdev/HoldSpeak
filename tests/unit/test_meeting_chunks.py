"""Unit tests for meeting audio chunk data structures."""

from __future__ import annotations

import threading
import numpy as np
import pytest

from holdspeak.meeting import AudioChunk, DualStreamBuffer, concatenate_chunks


class TestAudioChunk:
    """Tests for AudioChunk dataclass."""

    # ============================================================
    # Basic Creation Tests
    # ============================================================

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

    def test_source_mic(self, silence_1s: np.ndarray) -> None:
        """Mic source chunks."""
        chunk = AudioChunk(audio=silence_1s, timestamp=0.0, source="mic", duration=1.0)
        assert chunk.source == "mic"

    def test_source_system(self, silence_1s: np.ndarray) -> None:
        """System source chunks."""
        chunk = AudioChunk(audio=silence_1s, timestamp=0.0, source="system", duration=1.0)
        assert chunk.source == "system"

    # ============================================================
    # end_time Property Tests
    # ============================================================

    def test_end_time_property(self, silence_1s: np.ndarray) -> None:
        """end_time is timestamp + duration."""
        chunk = AudioChunk(
            audio=silence_1s,
            timestamp=10.0,
            source="mic",
            duration=2.5,
        )
        assert chunk.end_time == 12.5

    def test_end_time_zero_timestamp(self, silence_1s: np.ndarray) -> None:
        """end_time with zero timestamp."""
        chunk = AudioChunk(
            audio=silence_1s,
            timestamp=0.0,
            source="mic",
            duration=1.0,
        )
        assert chunk.end_time == 1.0

    def test_end_time_fractional(self, silence_1s: np.ndarray) -> None:
        """end_time with fractional values."""
        chunk = AudioChunk(
            audio=silence_1s,
            timestamp=5.25,
            source="system",
            duration=0.125,
        )
        assert abs(chunk.end_time - 5.375) < 1e-9

    def test_end_time_zero_duration(self, silence_1s: np.ndarray) -> None:
        """end_time equals timestamp when duration is zero."""
        chunk = AudioChunk(
            audio=silence_1s,
            timestamp=15.0,
            source="mic",
            duration=0.0,
        )
        assert chunk.end_time == 15.0


class TestDualStreamBuffer:
    """Tests for DualStreamBuffer class."""

    # ============================================================
    # Basic Operations Tests
    # ============================================================

    def test_empty_buffer(self) -> None:
        """New buffer starts empty."""
        buffer = DualStreamBuffer()
        mic, system = buffer.get_all_chunks()
        assert mic == []
        assert system == []

    def test_add_mic_chunk(self, silence_1s: np.ndarray) -> None:
        """Adding mic chunk stores it correctly."""
        buffer = DualStreamBuffer()
        buffer.add_mic_chunk(silence_1s, timestamp=0.0, duration=1.0)

        mic, system = buffer.get_all_chunks()
        assert len(mic) == 1
        assert len(system) == 0
        assert mic[0].source == "mic"
        assert mic[0].timestamp == 0.0
        assert mic[0].duration == 1.0

    def test_add_system_chunk(self, silence_1s: np.ndarray) -> None:
        """Adding system chunk stores it correctly."""
        buffer = DualStreamBuffer()
        buffer.add_system_chunk(silence_1s, timestamp=0.0, duration=1.0)

        mic, system = buffer.get_all_chunks()
        assert len(mic) == 0
        assert len(system) == 1
        assert system[0].source == "system"

    # ============================================================
    # Accumulation Tests
    # ============================================================

    def test_accumulates_multiple_mic_chunks(self, silence_1s: np.ndarray) -> None:
        """Multiple mic chunks accumulate in order."""
        buffer = DualStreamBuffer()
        buffer.add_mic_chunk(silence_1s, timestamp=0.0, duration=1.0)
        buffer.add_mic_chunk(silence_1s, timestamp=1.0, duration=1.0)
        buffer.add_mic_chunk(silence_1s, timestamp=2.0, duration=1.0)

        mic, _ = buffer.get_all_chunks()
        assert len(mic) == 3
        assert [c.timestamp for c in mic] == [0.0, 1.0, 2.0]

    def test_accumulates_multiple_system_chunks(self, silence_1s: np.ndarray) -> None:
        """Multiple system chunks accumulate in order."""
        buffer = DualStreamBuffer()
        buffer.add_system_chunk(silence_1s, timestamp=0.5, duration=0.5)
        buffer.add_system_chunk(silence_1s, timestamp=1.0, duration=0.5)

        _, system = buffer.get_all_chunks()
        assert len(system) == 2

    def test_accumulates_mixed_chunks(self, silence_1s: np.ndarray) -> None:
        """Mic and system chunks accumulate independently."""
        buffer = DualStreamBuffer()
        buffer.add_mic_chunk(silence_1s, timestamp=0.0, duration=1.0)
        buffer.add_system_chunk(silence_1s, timestamp=0.5, duration=1.0)
        buffer.add_mic_chunk(silence_1s, timestamp=1.0, duration=1.0)
        buffer.add_system_chunk(silence_1s, timestamp=1.5, duration=1.0)

        mic, system = buffer.get_all_chunks()
        assert len(mic) == 2
        assert len(system) == 2

    # ============================================================
    # get_chunks_since Tests
    # ============================================================

    def test_get_chunks_since_all(self, silence_1s: np.ndarray) -> None:
        """get_chunks_since(0) returns all chunks."""
        buffer = DualStreamBuffer()
        buffer.add_mic_chunk(silence_1s, timestamp=0.0, duration=1.0)
        buffer.add_mic_chunk(silence_1s, timestamp=1.0, duration=1.0)
        buffer.add_system_chunk(silence_1s, timestamp=0.5, duration=1.0)

        mic, system = buffer.get_chunks_since(0.0)
        assert len(mic) == 2
        assert len(system) == 1

    def test_get_chunks_since_partial(self, silence_1s: np.ndarray) -> None:
        """get_chunks_since filters by timestamp."""
        buffer = DualStreamBuffer()
        buffer.add_mic_chunk(silence_1s, timestamp=0.0, duration=1.0)
        buffer.add_mic_chunk(silence_1s, timestamp=1.0, duration=1.0)
        buffer.add_mic_chunk(silence_1s, timestamp=2.0, duration=1.0)

        mic, _ = buffer.get_chunks_since(1.5)
        assert len(mic) == 1
        assert mic[0].timestamp == 2.0

    def test_get_chunks_since_none(self, silence_1s: np.ndarray) -> None:
        """get_chunks_since returns empty if no chunks after timestamp."""
        buffer = DualStreamBuffer()
        buffer.add_mic_chunk(silence_1s, timestamp=0.0, duration=1.0)
        buffer.add_mic_chunk(silence_1s, timestamp=1.0, duration=1.0)

        mic, system = buffer.get_chunks_since(10.0)
        assert mic == []
        assert system == []

    # ============================================================
    # Clear and Trim Tests
    # ============================================================

    def test_clear(self, silence_1s: np.ndarray) -> None:
        """clear() removes all chunks."""
        buffer = DualStreamBuffer()
        buffer.add_mic_chunk(silence_1s, timestamp=0.0, duration=1.0)
        buffer.add_system_chunk(silence_1s, timestamp=0.5, duration=1.0)

        buffer.clear()
        mic, system = buffer.get_all_chunks()
        assert mic == []
        assert system == []

    def test_trim_before(self, silence_1s: np.ndarray) -> None:
        """trim_before removes chunks that end before timestamp."""
        buffer = DualStreamBuffer()
        buffer.add_mic_chunk(silence_1s, timestamp=0.0, duration=1.0)  # ends at 1.0
        buffer.add_mic_chunk(silence_1s, timestamp=1.0, duration=1.0)  # ends at 2.0
        buffer.add_mic_chunk(silence_1s, timestamp=2.0, duration=1.0)  # ends at 3.0

        buffer.trim_before(1.5)  # Remove chunks ending before 1.5 (first chunk ends at 1.0)
        mic, _ = buffer.get_all_chunks()
        assert len(mic) == 2
        assert mic[0].timestamp == 1.0
        assert mic[1].timestamp == 2.0

    def test_trim_before_keeps_overlapping(self, silence_1s: np.ndarray) -> None:
        """trim_before keeps chunks that overlap the timestamp."""
        buffer = DualStreamBuffer()
        buffer.add_mic_chunk(silence_1s, timestamp=0.0, duration=2.0)  # ends at 2.0

        buffer.trim_before(1.5)  # Chunk ends at 2.0 > 1.5, so keep it
        mic, _ = buffer.get_all_chunks()
        assert len(mic) == 1

    # ============================================================
    # Thread Safety Tests
    # ============================================================

    def test_thread_safe_add(self, silence_1s: np.ndarray) -> None:
        """Concurrent adds are thread-safe."""
        buffer = DualStreamBuffer()
        errors = []

        def add_mic_chunks() -> None:
            try:
                for i in range(100):
                    buffer.add_mic_chunk(silence_1s, timestamp=float(i), duration=0.1)
            except Exception as e:
                errors.append(e)

        def add_system_chunks() -> None:
            try:
                for i in range(100):
                    buffer.add_system_chunk(silence_1s, timestamp=float(i), duration=0.1)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=add_mic_chunks),
            threading.Thread(target=add_system_chunks),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        mic, system = buffer.get_all_chunks()
        assert len(mic) == 100
        assert len(system) == 100


class TestConcatenateChunks:
    """Tests for concatenate_chunks function."""

    # ============================================================
    # Basic Tests
    # ============================================================

    def test_empty_list(self) -> None:
        """Empty list returns empty array."""
        result = concatenate_chunks([])
        assert len(result) == 0
        assert result.dtype == np.float32

    def test_single_chunk(self, silence_1s: np.ndarray) -> None:
        """Single chunk returns its audio."""
        chunk = AudioChunk(audio=silence_1s, timestamp=0.0, source="mic", duration=1.0)
        result = concatenate_chunks([chunk])
        np.testing.assert_array_equal(result, silence_1s)

    def test_multiple_chunks_concatenate(self) -> None:
        """Multiple chunks are concatenated in timestamp order."""
        audio1 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        audio2 = np.array([4.0, 5.0, 6.0], dtype=np.float32)

        chunks = [
            AudioChunk(audio=audio1, timestamp=0.0, source="mic", duration=0.1),
            AudioChunk(audio=audio2, timestamp=0.1, source="mic", duration=0.1),
        ]

        result = concatenate_chunks(chunks)
        expected = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float32)
        np.testing.assert_array_equal(result, expected)

    # ============================================================
    # Sorting Tests
    # ============================================================

    def test_sorts_by_timestamp(self) -> None:
        """Chunks are sorted by timestamp before concatenation."""
        audio1 = np.array([1.0, 2.0], dtype=np.float32)
        audio2 = np.array([3.0, 4.0], dtype=np.float32)
        audio3 = np.array([5.0, 6.0], dtype=np.float32)

        # Create in reverse timestamp order
        chunks = [
            AudioChunk(audio=audio3, timestamp=2.0, source="mic", duration=0.1),
            AudioChunk(audio=audio1, timestamp=0.0, source="mic", duration=0.1),
            AudioChunk(audio=audio2, timestamp=1.0, source="mic", duration=0.1),
        ]

        result = concatenate_chunks(chunks)
        expected = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float32)
        np.testing.assert_array_equal(result, expected)

    def test_handles_same_timestamp(self) -> None:
        """Handles chunks with same timestamp (stable sort)."""
        audio1 = np.array([1.0], dtype=np.float32)
        audio2 = np.array([2.0], dtype=np.float32)

        chunks = [
            AudioChunk(audio=audio1, timestamp=0.0, source="mic", duration=0.1),
            AudioChunk(audio=audio2, timestamp=0.0, source="mic", duration=0.1),
        ]

        result = concatenate_chunks(chunks)
        # Both should be included, order depends on stable sort
        assert len(result) == 2

    # ============================================================
    # Output Type Tests
    # ============================================================

    def test_output_dtype_float32(self) -> None:
        """Output is always float32."""
        audio = np.array([1.0, 2.0], dtype=np.float64)  # float64 input
        chunk = AudioChunk(audio=audio.astype(np.float32), timestamp=0.0, source="mic", duration=0.1)
        result = concatenate_chunks([chunk])
        assert result.dtype == np.float32

    def test_preserves_values(self, sine_440hz_1s: np.ndarray) -> None:
        """Concatenation preserves original audio values."""
        chunk1 = AudioChunk(audio=sine_440hz_1s[:8000], timestamp=0.0, source="mic", duration=0.5)
        chunk2 = AudioChunk(audio=sine_440hz_1s[8000:], timestamp=0.5, source="mic", duration=0.5)

        result = concatenate_chunks([chunk1, chunk2])
        np.testing.assert_array_almost_equal(result, sine_440hz_1s)
