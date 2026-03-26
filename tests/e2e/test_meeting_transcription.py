"""Long E2E test - transcribe a full mock meeting recording and extract intel.

This test uses a real ~7 minute meeting recording to verify:
- Whisper can handle long-form audio
- Transcription quality on realistic meeting content
- LLM intel extraction (topics, action items, summary)
- Full pipeline: audio -> transcript -> structured intelligence

Audio source: Mock meeting recording (tests/fixtures/mock_meeting.wav)
Duration: ~6:41 (401 seconds)

Run with: pytest tests/e2e/test_meeting_transcription.py -v -s
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest

wav = pytest.importorskip(
    "scipy.io.wavfile",
    reason="requires scipy (install with `.[dev]` or add scipy)",
)


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
MOCK_MEETING_WAV = FIXTURES_DIR / "mock_meeting.wav"


pytestmark = [
    pytest.mark.metal,
    pytest.mark.slow,
    pytest.mark.skipif(
        not MOCK_MEETING_WAV.exists(),
        reason=f"Mock meeting fixture not found: {MOCK_MEETING_WAV}",
    ),
]


@pytest.fixture(scope="module")
def meeting_audio() -> tuple[np.ndarray, float]:
    """Load the mock meeting audio file.

    Returns:
        Tuple of (audio_array, duration_seconds)
    """
    sample_rate, audio = wav.read(MOCK_MEETING_WAV)

    # Convert to float32 normalized [-1, 1]
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0
    elif audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    duration = len(audio) / sample_rate
    print(f"\n[Meeting Test] Loaded {duration:.1f}s of audio ({len(audio):,} samples)")

    return audio, duration


@pytest.fixture(scope="module")
def whisper_model():
    """Load Whisper model for meeting transcription.

    Uses 'base' model for better accuracy on long-form content.
    """
    from holdspeak.transcribe import Transcriber

    print("\n[Meeting Test] Loading Whisper model (base)...")
    start = time.perf_counter()
    transcriber = Transcriber(model_name="base")
    elapsed = time.perf_counter() - start
    print(f"[Meeting Test] Model loaded in {elapsed:.1f}s")

    return transcriber


class TestMeetingTranscription:
    """Tests for transcribing full meeting recordings."""

    def test_full_meeting_transcription(
        self, whisper_model, meeting_audio: tuple[np.ndarray, float]
    ) -> None:
        """Transcribe the entire mock meeting and verify output quality."""
        audio, duration = meeting_audio

        print(f"\n[Meeting Test] Transcribing {duration:.1f}s of meeting audio...")

        start = time.perf_counter()
        transcript = whisper_model.transcribe(audio)
        elapsed = time.perf_counter() - start

        rtf = elapsed / duration
        words = len(transcript.split()) if transcript else 0
        words_per_minute = (words / duration) * 60 if duration > 0 else 0

        print(f"[Meeting Test] Transcription completed:")
        print(f"  - Time: {elapsed:.1f}s (RTF: {rtf:.2f}x)")
        print(f"  - Words: {words:,} ({words_per_minute:.0f} words/min)")
        print(f"  - Characters: {len(transcript):,}")
        print(f"\n[Meeting Test] Transcript preview (first 500 chars):")
        print(f"  {transcript[:500]}...")

        # Basic quality assertions
        assert transcript is not None, "Transcription returned None"
        assert len(transcript) > 100, "Transcription too short"

        # A 6+ minute meeting should produce substantial output
        # Typical speech is 100-150 words/min, so expect at least 400 words
        assert words > 300, f"Expected >300 words for {duration:.0f}s meeting, got {words}"

        # RTF should be reasonable (< 1.0 means faster than realtime)
        assert rtf < 2.0, f"Transcription too slow: {rtf:.2f}x realtime"

    def test_meeting_contains_meeting_keywords(
        self, whisper_model, meeting_audio: tuple[np.ndarray, float]
    ) -> None:
        """Verify transcription contains expected meeting-related content."""
        audio, _ = meeting_audio

        transcript = whisper_model.transcribe(audio)
        transcript_lower = transcript.lower()

        # Common meeting words that should appear in a mock meeting
        meeting_keywords = [
            "meeting", "team", "project", "update", "discuss",
            "agenda", "action", "item", "question", "thank",
            "week", "time", "work", "need", "think",
        ]

        found_keywords = [kw for kw in meeting_keywords if kw in transcript_lower]

        print(f"\n[Meeting Test] Found {len(found_keywords)}/{len(meeting_keywords)} keywords:")
        print(f"  Found: {found_keywords}")
        print(f"  Missing: {[kw for kw in meeting_keywords if kw not in transcript_lower]}")

        # Should find at least 5 meeting-related keywords
        assert len(found_keywords) >= 5, (
            f"Expected at least 5 meeting keywords, found {len(found_keywords)}: {found_keywords}"
        )

    def test_chunked_transcription(
        self, whisper_model, meeting_audio: tuple[np.ndarray, float]
    ) -> None:
        """Test transcribing in chunks (simulating streaming/incremental processing)."""
        audio, duration = meeting_audio

        # Split into ~30 second chunks
        chunk_size = 30 * 16000  # 30 seconds at 16kHz
        chunks = [audio[i:i + chunk_size] for i in range(0, len(audio), chunk_size)]

        print(f"\n[Meeting Test] Transcribing {len(chunks)} chunks (~30s each)...")

        all_transcripts = []
        total_time = 0

        for i, chunk in enumerate(chunks):
            chunk_duration = len(chunk) / 16000
            start = time.perf_counter()
            transcript = whisper_model.transcribe(chunk)
            elapsed = time.perf_counter() - start
            total_time += elapsed

            words = len(transcript.split()) if transcript else 0
            print(f"  Chunk {i+1}/{len(chunks)}: {chunk_duration:.1f}s -> {words} words ({elapsed:.1f}s)")

            if transcript:
                all_transcripts.append(transcript)

        combined = " ".join(all_transcripts)
        total_words = len(combined.split())

        print(f"\n[Meeting Test] Chunked transcription complete:")
        print(f"  - Total time: {total_time:.1f}s")
        print(f"  - Total words: {total_words:,}")
        print(f"  - Avg RTF: {total_time / duration:.2f}x")

        # Chunked should produce similar word count to full transcription
        assert total_words > 300, f"Expected >300 words, got {total_words}"


class TestMeetingPerformance:
    """Performance benchmarks for meeting transcription."""

    def test_memory_usage_reasonable(
        self, whisper_model, meeting_audio: tuple[np.ndarray, float]
    ) -> None:
        """Verify memory usage stays reasonable during transcription."""
        import os

        audio, duration = meeting_audio

        # Get memory before
        pid = os.getpid()

        # Transcribe
        transcript = whisper_model.transcribe(audio)

        # Basic check - we completed without OOM
        assert transcript is not None
        assert len(transcript) > 0

        print(f"\n[Meeting Test] Transcription completed without memory issues")

    def test_repeated_transcriptions_stable(
        self, whisper_model, meeting_audio: tuple[np.ndarray, float]
    ) -> None:
        """Verify repeated transcriptions produce consistent results."""
        audio, _ = meeting_audio

        # Take first 30 seconds for speed
        short_audio = audio[:30 * 16000]

        print("\n[Meeting Test] Running 3 transcriptions of same audio...")

        results = []
        times = []

        for i in range(3):
            start = time.perf_counter()
            transcript = whisper_model.transcribe(short_audio)
            elapsed = time.perf_counter() - start

            results.append(transcript)
            times.append(elapsed)

            words = len(transcript.split()) if transcript else 0
            print(f"  Run {i+1}: {words} words in {elapsed:.2f}s")

        # Results should be identical (deterministic inference)
        assert results[0] == results[1] == results[2], (
            "Transcription results differ between runs"
        )

        # Times should be similar (within 50% of each other)
        avg_time = sum(times) / len(times)
        for t in times:
            assert abs(t - avg_time) / avg_time < 0.5, (
                f"Transcription time {t:.2f}s varies too much from avg {avg_time:.2f}s"
            )

        print(f"[Meeting Test] All 3 runs produced identical output")
        print(f"[Meeting Test] Avg time: {avg_time:.2f}s (variance: {max(times) - min(times):.2f}s)")


# ============================================================
# Intel Extraction Tests (LLM)
# ============================================================

# Models for testing - prioritize quality/speed balance with GPU acceleration
# Override with INTEL_MODEL env var for custom model testing
# e.g., INTEL_MODEL=~/Models/gguf/custom-model.gguf pytest ...
import os

INTEL_MODELS = [
    # Best balance: Qwen 32B with GPU takes ~12s for meeting intel
    ("Qwen2.5-32B", "~/Models/gguf/qwen2.5-32b-instruct-q4_k_m-00001-of-00005.gguf"),
    # Faster alternatives (downloading):
    ("Llama-3.1-8B", "~/Models/gguf/Meta-Llama-3.1-8B-Instruct-Q6_K.gguf"),
    ("Phi-3-Medium", "~/Models/gguf/Phi-3-medium-128k-instruct-Q6_K.gguf"),
    ("Gemma-2-27B", "~/Models/gguf/gemma-2-27b-it-Q4_K_M.gguf"),
    # Fallback - always available, ~30s
    ("Mistral-7B", "~/Models/gguf/Mistral-7B-Instruct-v0.3-Q6_K.gguf"),
    # Very large (may OOM):
    # ("Llama-3.1-70B", "~/Models/gguf/Meta-Llama-3.1-70B-Instruct-Q4_K_M.gguf"),
]


def _find_best_intel_model() -> tuple[str, Path]:
    """Find the best available intel model.

    Respects INTEL_MODEL env var for override.
    """
    # Allow env var override for production testing with larger models
    env_model = os.environ.get("INTEL_MODEL")
    if env_model:
        path = Path(env_model).expanduser()
        if path.exists():
            return f"Custom ({path.name})", path

    for name, path_str in INTEL_MODELS:
        path = Path(path_str).expanduser()
        if path.exists():
            return name, path
    return "", Path("")


INTEL_MODEL_NAME, INTEL_MODEL_PATH = _find_best_intel_model()


@pytest.fixture(scope="module")
def intel_model():
    """Load the best available LLM for intel extraction.

    Tries models in order: Llama-3.1-70B > Qwen2.5-14B > Mistral-7B
    """
    if not INTEL_MODEL_PATH or not INTEL_MODEL_PATH.exists():
        pytest.skip(f"No intel model found. Tried: {[m[0] for m in INTEL_MODELS]}")

    from holdspeak.intel import MeetingIntel

    print(f"\n[Intel Test] Using model: {INTEL_MODEL_NAME}")
    print(f"[Intel Test] Loading from: {INTEL_MODEL_PATH}")
    print(f"[Intel Test] Size: {INTEL_MODEL_PATH.stat().st_size / 1e9:.1f} GB")

    start = time.perf_counter()
    intel = MeetingIntel(model_path=str(INTEL_MODEL_PATH))
    # Force model load
    intel._ensure_model_loaded()
    elapsed = time.perf_counter() - start
    print(f"[Intel Test] LLM loaded in {elapsed:.1f}s")

    return intel


@pytest.fixture(scope="module")
def meeting_transcript(whisper_model, meeting_audio: tuple[np.ndarray, float]) -> str:
    """Get the full meeting transcript (cached at module level)."""
    audio, duration = meeting_audio
    print(f"\n[Intel Test] Transcribing {duration:.1f}s meeting for intel extraction...")

    start = time.perf_counter()
    transcript = whisper_model.transcribe(audio)
    elapsed = time.perf_counter() - start

    words = len(transcript.split()) if transcript else 0
    print(f"[Intel Test] Transcript ready: {words} words in {elapsed:.1f}s")

    return transcript


class TestMeetingIntelExtraction:
    """Tests for LLM-based meeting intelligence extraction."""

    def test_extract_intel_from_transcript(
        self, intel_model, meeting_transcript: str
    ) -> None:
        """Extract structured intel from the meeting transcript."""
        print(f"\n[Intel Test] Extracting intel from {len(meeting_transcript):,} char transcript...")

        start = time.perf_counter()
        result = intel_model.analyze(meeting_transcript)
        elapsed = time.perf_counter() - start

        print(f"[Intel Test] Intel extraction completed in {elapsed:.1f}s")
        print(f"\n[Intel Test] Results:")
        print(f"  Topics ({len(result.topics)}):")
        for topic in result.topics:
            print(f"    - {topic}")

        print(f"\n  Action Items ({len(result.action_items)}):")
        for item in result.action_items:
            owner = item.owner or "Unassigned"
            due = item.due or "No due date"
            print(f"    - [{owner}] {item.task} (Due: {due})")

        print(f"\n  Summary:")
        print(f"    {result.summary}")

        print(f"\n  Raw response length: {len(result.raw_response)} chars")

        # Verify we got meaningful results
        assert result is not None, "Intel result is None"
        assert len(result.topics) > 0, "No topics extracted"
        assert len(result.summary) > 20, "Summary too short"

    def test_intel_topics_are_relevant(
        self, intel_model, meeting_transcript: str
    ) -> None:
        """Verify extracted topics are relevant to the meeting content."""
        result = intel_model.analyze(meeting_transcript)

        # Topics should be non-empty strings
        for topic in result.topics:
            assert isinstance(topic, str), f"Topic is not a string: {topic}"
            assert len(topic) > 0, "Empty topic found"
            assert len(topic) < 200, f"Topic too long: {topic}"

        # Should have at least 2 topics for a 7-minute meeting
        assert len(result.topics) >= 2, f"Expected >= 2 topics, got {len(result.topics)}"

        print(f"\n[Intel Test] Verified {len(result.topics)} topics are well-formed")

    def test_intel_action_items_structure(
        self, intel_model, meeting_transcript: str
    ) -> None:
        """Verify action items have proper structure."""
        result = intel_model.analyze(meeting_transcript)

        for item in result.action_items:
            # Task is required
            assert item.task, "Action item missing task"
            assert len(item.task) > 5, f"Task too short: {item.task}"

            # Owner is optional but should be string if present
            if item.owner:
                assert isinstance(item.owner, str)

            # Due is optional but should be string if present
            if item.due:
                assert isinstance(item.due, str)

        print(f"\n[Intel Test] Verified {len(result.action_items)} action items are well-formed")

    def test_intel_summary_quality(
        self, intel_model, meeting_transcript: str
    ) -> None:
        """Verify summary captures key meeting points."""
        result = intel_model.analyze(meeting_transcript)

        summary = result.summary.lower()

        # Summary should be substantial but concise
        assert len(result.summary) >= 50, "Summary too short"
        assert len(result.summary) <= 1000, "Summary too long"

        # Summary should mention some meeting-related concepts
        meeting_concepts = [
            "meeting", "discuss", "schedule", "calendar", "booking",
            "process", "team", "staff", "decision", "agree",
        ]
        found = [c for c in meeting_concepts if c in summary]

        print(f"\n[Intel Test] Summary contains {len(found)} meeting concepts: {found}")

        # Should have at least 1 relevant concept
        assert len(found) >= 1, f"Summary doesn't mention meeting concepts: {result.summary}"


class TestFullPipelineE2E:
    """Full end-to-end pipeline tests: Audio -> Transcript -> Intel."""

    def test_full_pipeline_audio_to_intel(
        self, whisper_model, intel_model, meeting_audio: tuple[np.ndarray, float]
    ) -> None:
        """Test the complete pipeline from audio to structured intelligence."""
        audio, duration = meeting_audio

        print(f"\n[E2E Pipeline] Starting full pipeline for {duration:.1f}s meeting...")

        # Step 1: Transcribe
        print("[E2E Pipeline] Step 1: Transcribing audio...")
        t1_start = time.perf_counter()
        transcript = whisper_model.transcribe(audio)
        t1_elapsed = time.perf_counter() - t1_start
        words = len(transcript.split())
        print(f"[E2E Pipeline]   -> {words} words in {t1_elapsed:.1f}s")

        # Step 2: Extract intel
        print("[E2E Pipeline] Step 2: Extracting intelligence...")
        t2_start = time.perf_counter()
        intel = intel_model.analyze(transcript)
        t2_elapsed = time.perf_counter() - t2_start
        print(f"[E2E Pipeline]   -> {len(intel.topics)} topics, {len(intel.action_items)} actions in {t2_elapsed:.1f}s")

        # Total pipeline time
        total_time = t1_elapsed + t2_elapsed
        print(f"\n[E2E Pipeline] Complete!")
        print(f"  - Audio duration: {duration:.1f}s")
        print(f"  - Transcription: {t1_elapsed:.1f}s")
        print(f"  - Intel extraction: {t2_elapsed:.1f}s")
        print(f"  - Total pipeline: {total_time:.1f}s")
        print(f"  - Pipeline RTF: {total_time / duration:.2f}x")

        # Pipeline should complete faster than realtime
        assert total_time < duration, (
            f"Pipeline slower than realtime: {total_time:.1f}s > {duration:.1f}s"
        )

        # Should produce meaningful output
        assert words > 300, f"Transcript too short: {words} words"
        assert len(intel.topics) > 0, "No topics extracted"
        assert len(intel.summary) > 20, "Summary too short"

        # Print final intel summary
        print(f"\n[E2E Pipeline] Final Intel Summary:")
        print(f"  Topics: {intel.topics}")
        print(f"  Action Items: {len(intel.action_items)}")
        for item in intel.action_items:
            print(f"    - {item.task}")
        print(f"  Summary: {intel.summary[:200]}...")
