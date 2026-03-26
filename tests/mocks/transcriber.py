"""Mock transcriber for testing without ML models."""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MockTranscriber:
    """Mock Transcriber for testing without mlx-whisper.

    Usage:
        transcriber = MockTranscriber(text_to_return="Hello world")
        result = transcriber.transcribe(audio_array)
        assert result == "Hello world"
        assert transcriber.transcribe_count == 1
    """

    text_to_return: str = "Hello world"
    should_fail: bool = False
    fail_message: str = "Mock transcription error"
    min_audio_length: int = 8000  # 0.5s at 16kHz

    # Call tracking
    transcribe_count: int = field(default=0, init=False)
    preload_count: int = field(default=0, init=False)
    last_audio: Optional[np.ndarray] = field(default=None, init=False)
    last_audio_length: int = field(default=0, init=False)

    def transcribe(self, audio: np.ndarray) -> str:
        """Mock transcribe - returns configured text or empty for short audio."""
        if self.should_fail:
            from holdspeak.transcribe import TranscriberError

            raise TranscriberError(self.fail_message)

        self.last_audio = audio
        self.last_audio_length = len(audio)

        if len(audio) < self.min_audio_length:
            return ""  # Too short, return empty

        self.transcribe_count += 1
        return self.text_to_return

    def preload(self) -> None:
        """Mock preload - just tracks calls."""
        self.preload_count += 1

    def reset(self) -> None:
        """Reset call counters for reuse."""
        self.transcribe_count = 0
        self.preload_count = 0
        self.last_audio = None
        self.last_audio_length = 0


@dataclass
class MockTranscriberWithHistory:
    """Mock Transcriber that returns different text for each call.

    Usage:
        transcriber = MockTranscriberWithHistory(
            responses=["First", "Second", "Third"]
        )
        assert transcriber.transcribe(audio) == "First"
        assert transcriber.transcribe(audio) == "Second"
    """

    responses: list[str] = field(default_factory=lambda: ["Hello world"])
    should_fail: bool = False
    loop: bool = True  # Whether to loop responses or return empty when exhausted

    _call_index: int = field(default=0, init=False)

    def transcribe(self, audio: np.ndarray) -> str:
        """Return next response from list."""
        if self.should_fail:
            from holdspeak.transcribe import TranscriberError

            raise TranscriberError("Mock transcription error")

        if self._call_index >= len(self.responses):
            if self.loop:
                self._call_index = 0
            else:
                return ""

        result = self.responses[self._call_index]
        self._call_index += 1
        return result

    def preload(self) -> None:
        """Mock preload."""
        pass

    def reset(self) -> None:
        """Reset to first response."""
        self._call_index = 0
