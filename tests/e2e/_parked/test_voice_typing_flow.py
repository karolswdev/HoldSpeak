"""End-to-end tests for the voice typing flow.

These tests simulate the complete pipeline:
  press hotkey -> record -> release -> transcribe -> type

They use mock components to avoid hardware dependencies.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

import numpy as np
import pytest

from tests.mocks.audio import MockAudioRecorder
from tests.mocks.transcriber import MockTranscriber, MockTranscriberWithHistory
from tests.mocks.hotkey import MockHotkeyListener
from tests.mocks.typer import MockTextTyper


class VoiceTypingPipeline:
    """Simplified voice typing pipeline for E2E testing.

    Wires together: hotkey -> recorder -> transcriber -> typer
    Similar to HoldSpeakController but without TUI dependencies.
    """

    MIN_AUDIO_SAMPLES = 1600  # 0.1s at 16kHz (same as main.py)

    def __init__(
        self,
        recorder: MockAudioRecorder,
        transcriber: MockTranscriber,
        typer: MockTextTyper,
        on_state_change: Optional[Callable[[str], None]] = None,
    ):
        self.recorder = recorder
        self.transcriber = transcriber
        self.typer = typer
        self.on_state_change = on_state_change

        self._state = "idle"
        self._recording_active = False
        self._lock = threading.Lock()

        # Create hotkey listener with callbacks
        self.hotkey_listener = MockHotkeyListener(
            on_press=self._on_press,
            on_release=self._on_release,
        )

        # Track errors
        self.last_error: Optional[str] = None
        self.notifications: list[str] = []

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    def _set_state(self, state: str) -> None:
        with self._lock:
            self._state = state
        if self.on_state_change:
            self.on_state_change(state)

    def _on_press(self) -> None:
        """Handle hotkey press - start recording."""
        self._set_state("recording")
        try:
            self.recorder.start()
            self._recording_active = True
        except Exception as e:
            self._set_state("idle")
            self._recording_active = False
            self.last_error = f"Recording failed: {e}"

    def _on_release(self) -> None:
        """Handle hotkey release - stop recording and transcribe."""
        # Don't proceed if recording was never started
        if not self._recording_active:
            return

        self._recording_active = False

        try:
            audio = self.recorder.stop()
        except Exception as e:
            self._set_state("idle")
            self.last_error = f"Recording error: {e}"
            return

        # Check minimum audio length
        if len(audio) < self.MIN_AUDIO_SAMPLES:
            self._set_state("idle")
            self.notifications.append("Recording too short")
            return

        self._set_state("transcribing")

        # Transcribe (synchronous in tests for simplicity)
        try:
            text = self.transcriber.transcribe(audio)
            if text:
                self.typer.type_text(text)
            else:
                self.notifications.append("No speech detected")
        except Exception as e:
            self.last_error = f"Transcription failed: {e}"
        finally:
            self._set_state("idle")

    def start(self) -> None:
        """Start the pipeline."""
        self.hotkey_listener.start()

    def stop(self) -> None:
        """Stop the pipeline."""
        self.hotkey_listener.stop()

    def simulate_voice_typing(self) -> None:
        """Convenience method to simulate a complete press-release cycle."""
        self.hotkey_listener.simulate_press_release()


# ============================================================
# E2E Tests
# ============================================================


@pytest.mark.e2e
class TestVoiceTypingFlow:
    """End-to-end tests for the voice typing pipeline."""

    @pytest.fixture
    def normal_audio(self) -> np.ndarray:
        """1 second of audio at 16kHz (above minimum threshold)."""
        return np.zeros(16000, dtype=np.float32)

    @pytest.fixture
    def short_audio(self) -> np.ndarray:
        """100ms audio - below 0.1s minimum threshold."""
        return np.zeros(1600 - 1, dtype=np.float32)  # Just under threshold

    @pytest.fixture
    def very_short_audio(self) -> np.ndarray:
        """50ms audio - well below minimum threshold."""
        return np.zeros(800, dtype=np.float32)

    def test_full_pipeline_press_record_release_transcribe_type(
        self, normal_audio: np.ndarray
    ) -> None:
        """Test complete voice typing flow: press -> record -> release -> transcribe -> type."""
        recorder = MockAudioRecorder(audio_to_return=normal_audio)
        transcriber = MockTranscriber(text_to_return="Hello world")
        typer = MockTextTyper()

        pipeline = VoiceTypingPipeline(recorder, transcriber, typer)
        pipeline.start()

        # Simulate press-release cycle
        pipeline.simulate_voice_typing()

        # Verify all components were called
        assert recorder.start_count == 1, "Recorder should be started once"
        assert recorder.stop_count == 1, "Recorder should be stopped once"
        assert transcriber.transcribe_count == 1, "Transcriber should be called once"
        assert typer.type_count == 1, "Typer should type once"
        assert typer.last_text == "Hello world", "Typed text should match transcription"
        assert pipeline.state == "idle", "Pipeline should return to idle state"

        pipeline.stop()

    def test_short_recording_not_transcribed(self, short_audio: np.ndarray) -> None:
        """Test that recordings shorter than 0.1s are not transcribed."""
        recorder = MockAudioRecorder(audio_to_return=short_audio)
        transcriber = MockTranscriber(text_to_return="Should not appear")
        typer = MockTextTyper()

        pipeline = VoiceTypingPipeline(recorder, transcriber, typer)
        pipeline.start()

        pipeline.simulate_voice_typing()

        # Recording happened but transcription should be skipped
        assert recorder.start_count == 1
        assert recorder.stop_count == 1
        assert transcriber.transcribe_count == 0, "Should not transcribe short audio"
        assert typer.type_count == 0, "Should not type when no transcription"
        assert "Recording too short" in pipeline.notifications

        pipeline.stop()

    def test_empty_transcription_not_typed(self, normal_audio: np.ndarray) -> None:
        """Test that empty transcription results are not typed."""
        recorder = MockAudioRecorder(audio_to_return=normal_audio)
        transcriber = MockTranscriber(text_to_return="")  # Empty result
        typer = MockTextTyper()

        pipeline = VoiceTypingPipeline(recorder, transcriber, typer)
        pipeline.start()

        pipeline.simulate_voice_typing()

        # Transcription was attempted but empty
        assert recorder.start_count == 1
        assert recorder.stop_count == 1
        # Note: MockTranscriber returns "" for long audio with text_to_return=""
        # but doesn't increment transcribe_count (by design in the mock)
        assert typer.type_count == 0, "Should not type empty transcription"
        assert "No speech detected" in pipeline.notifications

        pipeline.stop()

    def test_transcription_error_handling(self, normal_audio: np.ndarray) -> None:
        """Test that transcription errors are handled gracefully."""
        recorder = MockAudioRecorder(audio_to_return=normal_audio)
        transcriber = MockTranscriber(
            should_fail=True,
            fail_message="Model not loaded",
        )
        typer = MockTextTyper()

        pipeline = VoiceTypingPipeline(recorder, transcriber, typer)
        pipeline.start()

        pipeline.simulate_voice_typing()

        # Error should be captured, not raised
        assert typer.type_count == 0, "Should not type when transcription fails"
        assert pipeline.last_error is not None
        assert "Transcription failed" in pipeline.last_error
        assert pipeline.state == "idle", "Should return to idle after error"

        pipeline.stop()

    def test_recording_error_handling(self) -> None:
        """Test that recording errors are handled gracefully."""
        recorder = MockAudioRecorder(
            should_fail=True,
            fail_message="Microphone not available",
        )
        transcriber = MockTranscriber()
        typer = MockTextTyper()

        pipeline = VoiceTypingPipeline(recorder, transcriber, typer)
        pipeline.start()

        pipeline.simulate_voice_typing()

        # Error during recording start
        assert transcriber.transcribe_count == 0, "Should not transcribe if recording fails"
        assert typer.type_count == 0
        assert pipeline.last_error is not None
        assert "Recording failed" in pipeline.last_error

        pipeline.stop()

    def test_multiple_press_release_cycles(self, normal_audio: np.ndarray) -> None:
        """Test multiple consecutive voice typing sessions."""
        responses = ["First message", "Second message", "Third message"]
        recorder = MockAudioRecorder(audio_to_return=normal_audio)
        transcriber = MockTranscriberWithHistory(responses=responses)
        typer = MockTextTyper()

        pipeline = VoiceTypingPipeline(recorder, transcriber, typer)
        pipeline.start()

        # Perform 3 voice typing cycles
        for _ in range(3):
            pipeline.simulate_voice_typing()

        assert recorder.start_count == 3, "Should record 3 times"
        assert recorder.stop_count == 3, "Should stop 3 times"
        assert typer.type_count == 3, "Should type 3 times"
        assert typer.typed_texts == responses, "Should type each response in order"

        pipeline.stop()

    def test_state_transitions(self, normal_audio: np.ndarray) -> None:
        """Test that state transitions happen in correct order."""
        recorder = MockAudioRecorder(audio_to_return=normal_audio)
        transcriber = MockTranscriber(text_to_return="Test")
        typer = MockTextTyper()

        states_observed: list[str] = []

        def track_state(state: str) -> None:
            states_observed.append(state)

        pipeline = VoiceTypingPipeline(
            recorder, transcriber, typer, on_state_change=track_state
        )
        pipeline.start()

        pipeline.simulate_voice_typing()

        expected_states = ["recording", "transcribing", "idle"]
        assert states_observed == expected_states, (
            f"State transitions should be {expected_states}, got {states_observed}"
        )

        pipeline.stop()

    def test_very_short_audio_rejected(self, very_short_audio: np.ndarray) -> None:
        """Test that very short recordings (< 0.1s) are rejected."""
        recorder = MockAudioRecorder(audio_to_return=very_short_audio)
        transcriber = MockTranscriber(text_to_return="Should not appear")
        typer = MockTextTyper()

        pipeline = VoiceTypingPipeline(recorder, transcriber, typer)
        pipeline.start()

        pipeline.simulate_voice_typing()

        assert transcriber.transcribe_count == 0
        assert typer.type_count == 0
        assert "Recording too short" in pipeline.notifications

        pipeline.stop()

    def test_hotkey_listener_integration(self, normal_audio: np.ndarray) -> None:
        """Test that hotkey listener correctly triggers the pipeline."""
        recorder = MockAudioRecorder(audio_to_return=normal_audio)
        transcriber = MockTranscriber(text_to_return="Hotkey test")
        typer = MockTextTyper()

        pipeline = VoiceTypingPipeline(recorder, transcriber, typer)
        pipeline.start()

        # Verify listener is running
        assert pipeline.hotkey_listener.is_running

        # Manual press/release
        pipeline.hotkey_listener.simulate_press()
        assert pipeline.state == "recording", "Should be recording after press"
        assert recorder.is_recording()

        pipeline.hotkey_listener.simulate_release()
        assert pipeline.state == "idle", "Should be idle after release"
        assert not recorder.is_recording()

        assert typer.last_text == "Hotkey test"

        pipeline.stop()
        assert not pipeline.hotkey_listener.is_running

    def test_pipeline_tracks_call_counts(self, normal_audio: np.ndarray) -> None:
        """Test that mock components correctly track their call counts."""
        recorder = MockAudioRecorder(audio_to_return=normal_audio)
        transcriber = MockTranscriber(text_to_return="Count test")
        typer = MockTextTyper()

        pipeline = VoiceTypingPipeline(recorder, transcriber, typer)
        pipeline.start()

        # Perform 5 cycles
        for _ in range(5):
            pipeline.simulate_voice_typing()

        # Verify counts
        assert recorder.start_count == 5
        assert recorder.stop_count == 5
        assert transcriber.transcribe_count == 5
        assert typer.type_count == 5
        assert len(typer.typed_texts) == 5

        # Reset and verify
        recorder.reset()
        transcriber.reset()
        typer.reset()

        assert recorder.start_count == 0
        assert transcriber.transcribe_count == 0
        assert typer.type_count == 0

        pipeline.stop()

    def test_audio_passed_to_transcriber(self, normal_audio: np.ndarray) -> None:
        """Test that the recorded audio is correctly passed to the transcriber."""
        # Create audio with recognizable pattern
        test_audio = np.arange(16000, dtype=np.float32)
        recorder = MockAudioRecorder(audio_to_return=test_audio)
        transcriber = MockTranscriber(text_to_return="Audio test")
        typer = MockTextTyper()

        pipeline = VoiceTypingPipeline(recorder, transcriber, typer)
        pipeline.start()

        pipeline.simulate_voice_typing()

        # Verify the audio passed to transcriber matches what recorder returned
        assert transcriber.last_audio is not None
        assert len(transcriber.last_audio) == len(test_audio)
        np.testing.assert_array_equal(
            transcriber.last_audio, test_audio,
            err_msg="Audio passed to transcriber should match recorded audio"
        )

        pipeline.stop()

    def test_typed_text_matches_transcription(self, normal_audio: np.ndarray) -> None:
        """Test that the text typed exactly matches the transcription output."""
        expected_text = "The quick brown fox jumps over the lazy dog"
        recorder = MockAudioRecorder(audio_to_return=normal_audio)
        transcriber = MockTranscriber(text_to_return=expected_text)
        typer = MockTextTyper()

        pipeline = VoiceTypingPipeline(recorder, transcriber, typer)
        pipeline.start()

        pipeline.simulate_voice_typing()

        assert typer.last_text == expected_text
        assert typer.all_typed_text == expected_text

        pipeline.stop()
