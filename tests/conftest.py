"""Global test fixtures and configuration for HoldSpeak tests."""

from __future__ import annotations

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from holdspeak.config import Config

# ============================================================
# Path Fixtures
# ============================================================


@pytest.fixture
def fixtures_dir() -> Path:
    """Root fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def audio_dir(fixtures_dir: Path) -> Path:
    """Audio fixtures directory."""
    return fixtures_dir / "audio"


@pytest.fixture
def project_root() -> Path:
    """Project root directory."""
    return Path(__file__).parent.parent


# ============================================================
# Audio Fixtures
# ============================================================


@pytest.fixture
def silence_1s() -> np.ndarray:
    """1 second of silence at 16kHz."""
    return np.zeros(16000, dtype=np.float32)


@pytest.fixture
def sine_440hz_1s() -> np.ndarray:
    """1 second 440Hz sine wave at 16kHz."""
    t = np.linspace(0, 1, 16000, dtype=np.float32)
    return (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)


@pytest.fixture
def random_audio_1s() -> np.ndarray:
    """1 second of random noise at 16kHz (deterministic seed)."""
    rng = np.random.default_rng(42)
    return rng.uniform(-1, 1, 16000).astype(np.float32)


@pytest.fixture
def short_audio_100ms() -> np.ndarray:
    """100ms of audio at 16kHz (below typical minimum threshold)."""
    return np.zeros(1600, dtype=np.float32)


@pytest.fixture
def stereo_audio_1s() -> np.ndarray:
    """1 second of stereo audio at 16kHz."""
    t = np.linspace(0, 1, 16000, dtype=np.float32)
    left = np.sin(2 * np.pi * 440 * t) * 0.5
    right = np.sin(2 * np.pi * 880 * t) * 0.3
    return np.column_stack([left, right]).astype(np.float32)


# ============================================================
# Config Fixtures
# ============================================================


@pytest.fixture
def default_config() -> "Config":
    """Fresh default configuration."""
    from holdspeak.config import Config

    return Config()


@pytest.fixture
def temp_config_path(tmp_path: Path) -> Path:
    """Temporary config file path."""
    return tmp_path / "config.json"


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Temporary config directory."""
    config_dir = tmp_path / ".config" / "holdspeak"
    config_dir.mkdir(parents=True)
    return config_dir


# ============================================================
# Meeting Fixtures
# ============================================================


@pytest.fixture
def sample_segments():
    """Sample transcript segments for testing."""
    from holdspeak.meeting_session import TranscriptSegment

    return [
        TranscriptSegment(
            text="Let's discuss the quarterly goals.",
            speaker="Me",
            start_time=0.0,
            end_time=5.2,
        ),
        TranscriptSegment(
            text="I think we should prioritize the API refactor.",
            speaker="Remote",
            start_time=6.0,
            end_time=12.5,
        ),
        TranscriptSegment(
            text="Agreed. Let's schedule a follow-up.",
            speaker="Me",
            start_time=14.0,
            end_time=18.0,
        ),
    ]


@pytest.fixture
def sample_meeting_state():
    """Sample meeting state."""
    from holdspeak.meeting_session import MeetingState

    return MeetingState(
        id="test-meeting-123",
        started_at=datetime(2024, 1, 15, 10, 30, 0),
        mic_label="Me",
        remote_label="Remote",
    )


@pytest.fixture
def sample_intel_response() -> dict:
    """Sample LLM intel response."""
    return {
        "topics": ["Quarterly goals", "API refactor", "Follow-up meeting"],
        "action_items": [
            {"task": "Schedule follow-up", "owner": "Me", "due": "This week"},
            {"task": "Draft API refactor proposal", "owner": "Remote"},
        ],
        "summary": "Team discussed Q1 goals and agreed to prioritize API refactor.",
    }


@pytest.fixture
def sample_bookmark():
    """Sample meeting bookmark."""
    from holdspeak.meeting_session import Bookmark

    return Bookmark(
        timestamp=45.5,
        label="Important decision",
        created_at=datetime(2024, 1, 15, 10, 35, 45),
    )


# ============================================================
# Mock Module Fixtures
# ============================================================


@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice module for audio tests."""
    mock_sd = MagicMock()
    mock_sd.InputStream = MagicMock()
    mock_sd.query_devices = MagicMock(
        return_value={
            "name": "Mock Microphone",
            "default_samplerate": 48000,
            "max_input_channels": 2,
        }
    )
    mock_sd.CallbackFlags = MagicMock()

    with patch.dict("sys.modules", {"sounddevice": mock_sd}):
        yield mock_sd


@pytest.fixture
def mock_pynput_keyboard():
    """Mock pynput.keyboard module."""
    mock_keyboard = MagicMock()

    # Create fake Key enum
    class FakeKey:
        alt_r = MagicMock(name="alt_r")
        alt_l = MagicMock(name="alt_l")
        ctrl_r = MagicMock(name="ctrl_r")
        ctrl_l = MagicMock(name="ctrl_l")
        f1 = MagicMock(name="f1")
        f5 = MagicMock(name="f5")
        f12 = MagicMock(name="f12")
        caps_lock = MagicMock(name="caps_lock")

    mock_keyboard.Key = FakeKey
    mock_keyboard.Listener = MagicMock()
    mock_keyboard.Controller = MagicMock()

    with patch.dict(
        "sys.modules",
        {
            "pynput": MagicMock(),
            "pynput.keyboard": mock_keyboard,
        },
    ):
        yield mock_keyboard


@pytest.fixture
def mock_pyperclip():
    """Mock pyperclip with in-memory clipboard."""
    clipboard_storage = {"content": "original"}

    def mock_copy(text: str) -> None:
        clipboard_storage["content"] = text

    def mock_paste() -> str:
        return clipboard_storage["content"]

    with patch("pyperclip.copy", side_effect=mock_copy), patch(
        "pyperclip.paste", side_effect=mock_paste
    ):
        yield clipboard_storage


@pytest.fixture
def mock_mlx_whisper():
    """Mock mlx_whisper module."""
    mock_whisper = MagicMock()
    mock_whisper.transcribe = MagicMock(return_value={"text": "Hello world"})

    with patch.dict("sys.modules", {"mlx_whisper": mock_whisper}):
        yield mock_whisper


@pytest.fixture
def mock_llama():
    """Mock llama_cpp module."""
    mock_llama_module = MagicMock()

    class MockLlama:
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, prompt, **kwargs):
            return {
                "choices": [
                    {
                        "text": '{"topics": ["Test"], "action_items": [], "summary": "Test meeting"}'
                    }
                ]
            }

    mock_llama_module.Llama = MockLlama

    with patch.dict("sys.modules", {"llama_cpp": mock_llama_module}):
        yield mock_llama_module


# ============================================================
# Pytest Configuration
# ============================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow-running")
    config.addinivalue_line(
        "markers", "requires_model: requires ML model to be loaded"
    )
    config.addinivalue_line("markers", "requires_macos: requires macOS system")
    config.addinivalue_line(
        "markers",
        "requires_meeting: requires optional meeting/web dependencies",
    )
    config.addinivalue_line("markers", "integration: integration test")
    config.addinivalue_line("markers", "e2e: end-to-end test")


def pytest_collection_modifyitems(config, items):
    """Auto-skip tests based on markers and environment."""
    import sys

    skip_macos = pytest.mark.skip(reason="requires macOS")

    for item in items:
        # Skip macOS tests on other platforms
        if "requires_macos" in item.keywords and sys.platform != "darwin":
            item.add_marker(skip_macos)
