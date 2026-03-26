"""Mock audio components for testing."""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class MockAudioRecorder:
    """Mock AudioRecorder for testing without hardware.

    Usage:
        recorder = MockAudioRecorder(audio_to_return=my_audio_array)
        recorder.start()
        audio = recorder.stop()
        assert recorder.start_count == 1
    """

    audio_to_return: np.ndarray = field(
        default_factory=lambda: np.zeros(16000, dtype=np.float32)
    )
    level_to_report: float = 0.5
    should_fail: bool = False
    fail_message: str = "Mock recording error"

    _recording: bool = field(default=False, init=False)
    _level_callback: Optional[Callable[[float], None]] = field(default=None, init=False)

    # Call tracking
    start_count: int = field(default=0, init=False)
    stop_count: int = field(default=0, init=False)

    def start(self) -> None:
        """Start mock recording."""
        if self.should_fail:
            from holdspeak.audio import AudioRecorderError

            raise AudioRecorderError(self.fail_message)

        self._recording = True
        self.start_count += 1

        if self._level_callback:
            self._level_callback(self.level_to_report)

    def stop(self) -> np.ndarray:
        """Stop mock recording and return configured audio."""
        self._recording = False
        self.stop_count += 1
        return self.audio_to_return

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording

    def set_level_callback(self, callback: Callable[[float], None]) -> None:
        """Set the audio level callback."""
        self._level_callback = callback

    def reset(self) -> None:
        """Reset call counters for reuse."""
        self.start_count = 0
        self.stop_count = 0
        self._recording = False


@dataclass
class MockInputStream:
    """Mock sounddevice.InputStream for low-level testing."""

    callback: Optional[Callable] = None
    samplerate: int = 16000
    channels: int = 1
    blocksize: int = 1024

    _active: bool = field(default=False, init=False)

    def start(self) -> None:
        self._active = True

    def stop(self) -> None:
        self._active = False

    def close(self) -> None:
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    def simulate_audio(self, audio: np.ndarray) -> None:
        """Simulate audio data arriving via callback."""
        if self.callback and self._active:
            # Simulate callback flags
            class MockFlags:
                input_underflow = False
                input_overflow = False

            self.callback(audio, len(audio), None, MockFlags())
