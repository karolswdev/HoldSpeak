"""Metal E2E tests - run against real hardware and models.

These tests require:
- Real microphone access (sounddevice)
- Real mlx-whisper model (downloads on first run)
- Real clipboard/keyboard access (pyperclip, pynput)

Run locally with: pytest tests/e2e/test_metal.py -v -m metal
Skip in CI with: pytest -m "not metal"
"""

from __future__ import annotations

import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pytest

# Skip entire module if not on macOS
pytestmark = [
    pytest.mark.metal,
    pytest.mark.skipif(
        not Path("/usr/bin/say").exists(),
        reason="Metal tests require macOS",
    ),
]


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture(scope="module")
def test_audio_file() -> Path:
    """Generate a test audio file using macOS TTS.

    Creates a WAV file with known speech content for transcription testing.
    Cached at module scope to avoid regenerating for each test.
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = Path(f.name)

    # Use macOS 'say' to generate speech audio
    # -o outputs to file, --data-format specifies WAV format
    text = "Hello world. This is a test of the transcription system."
    subprocess.run(
        [
            "say",
            "-o", str(wav_path),
            "--data-format=LEF32@16000",  # 32-bit float, 16kHz (Whisper format)
            text,
        ],
        check=True,
        capture_output=True,
    )

    yield wav_path

    # Cleanup
    wav_path.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def whisper_model():
    """Load the Whisper model once per test module.

    Uses 'tiny' model for speed. Downloads on first run (~75MB).
    """
    from holdspeak.transcribe import Transcriber

    # Use tiny model for faster tests
    transcriber = Transcriber(model_name="tiny")
    return transcriber


# ============================================================
# Microphone Tests
# ============================================================


class TestMicrophoneRecording:
    """Tests for real microphone recording."""

    def test_can_list_audio_devices(self) -> None:
        """Should be able to list available audio devices."""
        import sounddevice as sd

        devices = sd.query_devices()
        assert devices is not None
        assert len(devices) > 0, "No audio devices found"

        # Should have at least one input device
        input_devices = [d for d in devices if d["max_input_channels"] > 0]
        assert len(input_devices) > 0, "No input (microphone) devices found"

    def test_can_get_default_input_device(self) -> None:
        """Should be able to get default input device."""
        import sounddevice as sd

        try:
            default_input = sd.query_devices(kind="input")
            assert default_input is not None
            assert default_input["max_input_channels"] > 0
        except sd.PortAudioError as e:
            pytest.skip(f"No default input device: {e}")

    def test_can_record_short_audio(self) -> None:
        """Should be able to record a short audio sample."""
        from holdspeak.audio import AudioRecorder

        recorder = AudioRecorder(sample_rate=16000)

        # Record for 0.5 seconds
        recorder.start_recording()
        time.sleep(0.5)
        audio = recorder.stop_recording()

        # Verify we got audio data
        assert audio is not None
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert len(audio) > 0, "No audio data captured"

        # Should be approximately 0.5s at 16kHz = 8000 samples (with some tolerance)
        expected_samples = 8000
        assert len(audio) > expected_samples * 0.5, "Audio too short"
        assert len(audio) < expected_samples * 2, "Audio too long"

    def test_audio_level_callback(self) -> None:
        """Should receive audio level callbacks during recording."""
        from holdspeak.audio import AudioRecorder

        levels_received: list[float] = []

        def on_level(level: float) -> None:
            levels_received.append(level)

        recorder = AudioRecorder(sample_rate=16000, on_level=on_level)

        recorder.start_recording()
        time.sleep(0.3)
        recorder.stop_recording()

        # Should have received at least a few level callbacks
        assert len(levels_received) > 0, "No audio level callbacks received"

        # Levels should be in valid range [0, 1]
        for level in levels_received:
            assert 0.0 <= level <= 1.0, f"Level {level} out of range"


# ============================================================
# Transcription Tests
# ============================================================


class TestWhisperTranscription:
    """Tests for real mlx-whisper transcription."""

    def test_model_loads(self, whisper_model) -> None:
        """Whisper model should load successfully."""
        assert whisper_model is not None
        assert whisper_model._path_or_hf_repo is not None

    def test_transcribe_generated_audio(
        self, whisper_model, test_audio_file: Path
    ) -> None:
        """Should transcribe TTS-generated audio correctly."""
        import scipy.io.wavfile as wav

        # Load the test audio file
        sample_rate, audio = wav.read(test_audio_file)

        # Convert to float32 if needed
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
            if audio.max() > 1.0:
                audio = audio / 32768.0  # Normalize int16

        # Transcribe
        result = whisper_model.transcribe(audio)

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0, "Transcription was empty"

        # Check for expected words (case-insensitive, allowing for variations)
        result_lower = result.lower()
        assert "hello" in result_lower or "test" in result_lower, (
            f"Transcription doesn't contain expected words: {result}"
        )

    def test_transcribe_silence_returns_empty_or_noise(
        self, whisper_model
    ) -> None:
        """Transcribing silence should return empty or minimal text."""
        # Create 2 seconds of silence
        silence = np.zeros(32000, dtype=np.float32)

        result = whisper_model.transcribe(silence)

        # Silence should produce empty or very short result
        # (Whisper might hallucinate a bit, so we're lenient)
        assert result is not None
        # If there's text, it should be short (hallucination)
        if result.strip():
            assert len(result) < 100, f"Too much hallucinated text: {result}"

    def test_transcribe_numpy_array_directly(self, whisper_model) -> None:
        """Should accept numpy array directly."""
        # Create a simple tone (won't produce meaningful transcription)
        t = np.linspace(0, 1, 16000, dtype=np.float32)
        tone = (np.sin(2 * np.pi * 440 * t) * 0.3).astype(np.float32)

        # Should not raise
        result = whisper_model.transcribe(tone)
        assert result is not None


# ============================================================
# Text Typing Tests
# ============================================================


class TestTextTyping:
    """Tests for real text typing/clipboard operations."""

    def test_clipboard_read_write(self) -> None:
        """Should be able to read and write clipboard."""
        import pyperclip

        test_text = f"HoldSpeak test {time.time()}"

        # Save original
        try:
            original = pyperclip.paste()
        except Exception:
            original = None

        try:
            # Write to clipboard
            pyperclip.copy(test_text)

            # Read back
            result = pyperclip.paste()
            assert result == test_text, "Clipboard round-trip failed"
        finally:
            # Restore original
            if original is not None:
                pyperclip.copy(original)

    def test_text_typer_initializes(self) -> None:
        """TextTyper should initialize without errors."""
        from holdspeak.typer import TextTyper

        typer = TextTyper(use_clipboard=True)
        assert typer is not None
        assert typer.use_clipboard is True

    def test_keyboard_controller_exists(self) -> None:
        """pynput keyboard controller should be available."""
        from pynput.keyboard import Controller

        keyboard = Controller()
        assert keyboard is not None


# ============================================================
# Full Pipeline Tests
# ============================================================


class TestFullPipeline:
    """Full pipeline tests with real components."""

    def test_record_and_transcribe_live(self, whisper_model) -> None:
        """Record live audio and transcribe it.

        This test records actual microphone input. For meaningful results,
        speak during the recording window or accept that silence/background
        noise will produce minimal output.
        """
        from holdspeak.audio import AudioRecorder

        recorder = AudioRecorder(sample_rate=16000)

        # Record 1.5 seconds
        print("\n[Metal Test] Recording for 1.5 seconds...")
        recorder.start_recording()
        time.sleep(1.5)
        audio = recorder.stop_recording()
        print(f"[Metal Test] Captured {len(audio)} samples")

        # Transcribe
        result = whisper_model.transcribe(audio)
        print(f"[Metal Test] Transcription: '{result}'")

        # Just verify it completes without error
        assert result is not None

    def test_tts_to_transcription_roundtrip(
        self, whisper_model, test_audio_file: Path
    ) -> None:
        """Test TTS audio -> Whisper transcription roundtrip.

        This is the most reliable metal test since we control the input.
        """
        import scipy.io.wavfile as wav

        # Load TTS audio
        sample_rate, audio = wav.read(test_audio_file)
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
            if audio.max() > 1.0:
                audio = audio / 32768.0

        # Transcribe
        result = whisper_model.transcribe(audio)

        # The TTS said "Hello world. This is a test of the transcription system."
        # Whisper should capture at least some of those words
        result_lower = result.lower()
        keywords = ["hello", "world", "test", "transcription", "system"]
        found = [kw for kw in keywords if kw in result_lower]

        assert len(found) >= 2, (
            f"Expected at least 2 keywords from {keywords}, "
            f"found {found} in: '{result}'"
        )

    def test_pipeline_components_wire_together(self) -> None:
        """Test that all pipeline components can be instantiated together."""
        from holdspeak.audio import AudioRecorder
        from holdspeak.transcribe import Transcriber
        from holdspeak.typer import TextTyper
        from holdspeak.hotkey import HotkeyListener

        # Create all components
        recorder = AudioRecorder(sample_rate=16000)
        transcriber = Transcriber(model_name="tiny")
        typer = TextTyper(use_clipboard=True)

        # Hotkey listener with dummy callbacks
        listener = HotkeyListener(
            hotkey="alt_r",  # Valid single-key hotkey
            on_press=lambda: None,
            on_release=lambda: None,
        )

        # All should exist
        assert recorder is not None
        assert transcriber is not None
        assert typer is not None
        assert listener is not None


# ============================================================
# Performance Tests
# ============================================================


class TestPerformance:
    """Performance benchmarks for metal components."""

    def test_transcription_speed(self, whisper_model, test_audio_file: Path) -> None:
        """Transcription should complete in reasonable time."""
        import scipy.io.wavfile as wav

        sample_rate, audio = wav.read(test_audio_file)
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
            if audio.max() > 1.0:
                audio = audio / 32768.0

        audio_duration = len(audio) / sample_rate

        start = time.perf_counter()
        result = whisper_model.transcribe(audio)
        elapsed = time.perf_counter() - start

        # On Apple Silicon, tiny model should be faster than realtime
        # (transcription time < audio duration)
        rtf = elapsed / audio_duration  # Real-time factor

        print(f"\n[Metal Test] Audio: {audio_duration:.2f}s, "
              f"Transcription: {elapsed:.2f}s, RTF: {rtf:.2f}x")

        # RTF should be < 1.0 (faster than realtime) on Apple Silicon
        # Be lenient for CI/slow machines
        assert rtf < 3.0, f"Transcription too slow: {rtf:.2f}x realtime"

    def test_recording_latency(self) -> None:
        """Recording start/stop should have low latency."""
        from holdspeak.audio import AudioRecorder

        recorder = AudioRecorder(sample_rate=16000)

        # Measure start latency
        start_time = time.perf_counter()
        recorder.start_recording()
        start_latency = time.perf_counter() - start_time

        time.sleep(0.2)

        # Measure stop latency
        stop_time = time.perf_counter()
        audio = recorder.stop_recording()
        stop_latency = time.perf_counter() - stop_time

        print(f"\n[Metal Test] Start latency: {start_latency*1000:.1f}ms, "
              f"Stop latency: {stop_latency*1000:.1f}ms")

        # Start should be quick (<100ms), stop can take longer due to resampling
        assert start_latency < 0.1, f"Start too slow: {start_latency*1000:.1f}ms"
        assert stop_latency < 0.3, f"Stop too slow: {stop_latency*1000:.1f}ms"
