# HoldSpeak Test Framework Design

## Executive Summary

This document outlines a comprehensive testing strategy for HoldSpeak, a macOS voice-to-text application with ~4,300 lines of code across 12 modules. The framework addresses the unique challenges of testing hardware-dependent (audio), OS-level (keyboard), and ML-dependent (Whisper, LLM) code while maximizing coverage and maintainability.

---

## Testing Philosophy

### The Testing Pyramid

```
           /\
          /  \      E2E (5-10 tests)
         /    \     Full pipeline with mocked I/O
        /------\
       /        \   Integration (50-80 tests)
      /          \  Component interaction, mocked externals
     /------------\
    /              \ Unit (150-200 tests)
   /________________\ Pure functions, isolated logic
```

### Core Principles

1. **Test the seams** - Focus on boundaries between components
2. **Mock at the edges** - Hardware, OS, network, ML models
3. **Pure functions first** - Maximum coverage on deterministic code
4. **Fast by default** - Unit tests run in <5 seconds
5. **Markers for slow tests** - Opt-in for model-dependent tests

---

## Testability Analysis

### Module Classification

| Module | Pure Logic | Needs Mocking | Difficulty |
|--------|-----------|---------------|------------|
| config.py | 95% | File I/O | Easy |
| audio.py | 30% (resampling) | sounddevice | Medium |
| transcribe.py | 20% (candidates) | mlx-whisper | Medium |
| hotkey.py | 40% (mapping) | pynput | Medium |
| typer.py | 10% | pynput, pyperclip | Hard |
| meeting.py | 50% (chunks, buffer) | sounddevice | Medium |
| meeting_session.py | 60% (dataclasses) | recorder, transcriber | Medium |
| intel.py | 70% (JSON parsing) | llama-cpp | Easy |
| web_server.py | 40% (utils) | FastAPI (has TestClient) | Easy |
| tui.py | 30% | Textual (has pilot) | Medium |

### Pure Functions (No Mocks Required)

These can be tested directly with simple assertions:

```python
# audio.py
_linear_resample_mono(audio, orig_rate, target_rate)

# hotkey.py
key_from_name(name)

# transcribe.py
_model_repo_candidates(model_name)

# meeting.py
concatenate_chunks(chunks)

# intel.py
_extract_json(response)
_coerce_str_list(value)
_coerce_action_items(value)
_json_only_messages(transcript)

# web_server.py
_find_free_port()
_format_duration(seconds)
_parse_iso_datetime(iso_string)
```

### External Dependencies (Require Mocking)

| Dependency | Used By | Mock Strategy |
|------------|---------|---------------|
| sounddevice | audio.py, meeting.py | Mock InputStream, query_devices |
| pynput.keyboard | hotkey.py, typer.py | Mock Listener, Controller |
| pyperclip | typer.py, tui.py | Mock paste/copy functions |
| mlx_whisper | transcribe.py | Mock transcribe function |
| llama_cpp | intel.py | Mock Llama class |
| fastapi | web_server.py | Use TestClient (built-in) |
| textual | tui.py | Use run_test/pilot (built-in) |

---

## Directory Structure

```
tests/
├── conftest.py                 # Global fixtures, markers, plugins
├── pytest.ini                  # Pytest configuration
│
├── fixtures/                   # Test data files
│   ├── audio/
│   │   ├── silence_1s.wav      # 1s silence at 16kHz
│   │   ├── tone_440hz_1s.wav   # 1s 440Hz sine wave
│   │   └── speech_hello.wav    # Short speech sample
│   ├── configs/
│   │   ├── default.json
│   │   ├── custom_hotkey.json
│   │   └── malformed.json
│   └── responses/
│       ├── intel_valid.json
│       ├── intel_markdown.txt
│       └── segments.json
│
├── mocks/                      # Reusable mock implementations
│   ├── __init__.py
│   ├── audio.py                # MockAudioRecorder, MockInputStream
│   ├── transcriber.py          # MockTranscriber
│   ├── hotkey.py               # MockHotkeyListener, FakeKey
│   ├── typer.py                # MockTextTyper
│   └── llm.py                  # MockLlama
│
├── unit/                       # Fast, isolated tests (~200 tests)
│   ├── __init__.py
│   ├── test_config.py          # Config loading, saving, defaults, validation
│   ├── test_config_hotkey.py   # Hotkey mapping, display names
│   ├── test_audio_resample.py  # Linear resampling math
│   ├── test_transcriber_candidates.py  # Model path resolution
│   ├── test_meeting_chunks.py  # AudioChunk, concatenate_chunks
│   ├── test_meeting_buffer.py  # DualStreamBuffer operations
│   ├── test_meeting_state.py   # MeetingState dataclass
│   ├── test_transcript_segment.py  # TranscriptSegment, Bookmark
│   ├── test_intel_extract.py   # _extract_json edge cases
│   ├── test_intel_coerce.py    # _coerce_str_list, _coerce_action_items
│   ├── test_intel_messages.py  # _json_only_messages prompt building
│   ├── test_web_utils.py       # Duration, port, datetime utilities
│   └── test_hotkey_mapping.py  # key_from_name, KEY_NAME_MAP
│
├── integration/                # Component tests with mocks (~80 tests)
│   ├── __init__.py
│   ├── test_audio_recorder.py  # AudioRecorder with mocked sounddevice
│   ├── test_transcriber.py     # Transcriber with mocked mlx_whisper
│   ├── test_hotkey_listener.py # HotkeyListener with direct calls
│   ├── test_typer.py           # TextTyper with mocked clipboard/keyboard
│   ├── test_meeting_recorder.py    # MeetingRecorder with mocked streams
│   ├── test_meeting_session.py     # MeetingSession lifecycle
│   ├── test_intel.py           # MeetingIntel with mocked LLM
│   ├── test_web_server.py      # HTTP endpoints via TestClient
│   ├── test_web_websocket.py   # WebSocket broadcast testing
│   └── test_tui.py             # TUI states and interactions via pilot
│
└── e2e/                        # Full pipeline tests (~10 tests)
    ├── __init__.py
    ├── test_voice_typing_flow.py   # Hotkey → Record → Transcribe → Type
    └── test_meeting_flow.py        # Start → Record → Transcribe → Intel → Stop
```

---

## Fixture Design

### conftest.py - Global Fixtures

```python
"""Global test fixtures and configuration."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

# ============================================================
# Path Fixtures
# ============================================================

@pytest.fixture
def fixtures_dir() -> Path:
    """Root fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def audio_dir(fixtures_dir) -> Path:
    """Audio fixtures directory."""
    return fixtures_dir / "audio"


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
    """1 second of random noise at 16kHz."""
    rng = np.random.default_rng(42)  # Deterministic
    return rng.uniform(-1, 1, 16000).astype(np.float32)


@pytest.fixture
def short_audio_100ms() -> np.ndarray:
    """100ms of audio (below minimum threshold)."""
    return np.zeros(1600, dtype=np.float32)


# ============================================================
# Config Fixtures
# ============================================================

@pytest.fixture
def default_config():
    """Fresh default configuration."""
    from holdspeak.config import Config
    return Config()


@pytest.fixture
def temp_config_path(tmp_path) -> Path:
    """Temporary config file path."""
    return tmp_path / "config.json"


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
def sample_intel_response():
    """Sample LLM intel response."""
    return {
        "topics": ["Quarterly goals", "API refactor", "Follow-up meeting"],
        "action_items": [
            {"task": "Schedule follow-up", "owner": "Me", "due": "This week"},
            {"task": "Draft API refactor proposal", "owner": "Remote"},
        ],
        "summary": "Team discussed Q1 goals and agreed to prioritize API refactor.",
    }


# ============================================================
# Mock Module Fixtures
# ============================================================

@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice module for audio tests."""
    mock_sd = MagicMock()
    mock_sd.InputStream = MagicMock()
    mock_sd.query_devices = MagicMock(return_value={
        "name": "Mock Microphone",
        "default_samplerate": 48000,
        "max_input_channels": 2,
    })
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
        f5 = MagicMock(name="f5")

    mock_keyboard.Key = FakeKey
    mock_keyboard.Listener = MagicMock()
    mock_keyboard.Controller = MagicMock()

    with patch.dict("sys.modules", {
        "pynput": MagicMock(),
        "pynput.keyboard": mock_keyboard,
    }):
        yield mock_keyboard


@pytest.fixture
def mock_pyperclip():
    """Mock pyperclip with in-memory clipboard."""
    clipboard_storage = {"content": ""}

    def mock_copy(text):
        clipboard_storage["content"] = text

    def mock_paste():
        return clipboard_storage["content"]

    with patch("pyperclip.copy", side_effect=mock_copy), \
         patch("pyperclip.paste", side_effect=mock_paste):
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
                "choices": [{
                    "text": '{"topics": ["Test"], "action_items": [], "summary": "Test meeting"}'
                }]
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
    config.addinivalue_line("markers", "requires_model: requires ML model to be loaded")
    config.addinivalue_line("markers", "requires_macos: requires macOS system")
    config.addinivalue_line("markers", "integration: integration test")
    config.addinivalue_line("markers", "e2e: end-to-end test")


def pytest_collection_modifyitems(config, items):
    """Auto-skip tests based on markers and environment."""
    import sys

    skip_macos = pytest.mark.skip(reason="requires macOS")
    skip_slow = pytest.mark.skip(reason="slow test (use -m slow to run)")

    for item in items:
        # Skip macOS tests on other platforms
        if "requires_macos" in item.keywords and sys.platform != "darwin":
            item.add_marker(skip_macos)

        # Skip slow tests unless explicitly requested
        if "slow" in item.keywords and not config.getoption("-m"):
            # Only skip if not running with marker filter
            pass  # Let pytest handle via -m flag
```

### Mock Implementations

```python
# tests/mocks/audio.py
"""Mock audio components for testing."""

import numpy as np
from typing import Callable, Optional
from dataclasses import dataclass, field


@dataclass
class MockAudioRecorder:
    """Mock AudioRecorder for testing without hardware."""

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
        if self.should_fail:
            from holdspeak.audio import AudioRecorderError
            raise AudioRecorderError(self.fail_message)

        self._recording = True
        self.start_count += 1

        if self._level_callback:
            self._level_callback(self.level_to_report)

    def stop(self) -> np.ndarray:
        self._recording = False
        self.stop_count += 1
        return self.audio_to_return

    def is_recording(self) -> bool:
        return self._recording

    def set_level_callback(self, callback: Callable[[float], None]) -> None:
        self._level_callback = callback


# tests/mocks/transcriber.py
"""Mock transcriber for testing without ML models."""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MockTranscriber:
    """Mock Transcriber for testing without mlx-whisper."""

    text_to_return: str = "Hello world"
    should_fail: bool = False
    fail_message: str = "Mock transcription error"
    min_audio_length: int = 8000  # 0.5s at 16kHz

    # Call tracking
    transcribe_count: int = field(default=0, init=False)
    last_audio: Optional[np.ndarray] = field(default=None, init=False)
    preload_count: int = field(default=0, init=False)

    def transcribe(self, audio: np.ndarray) -> str:
        if self.should_fail:
            from holdspeak.transcribe import TranscriberError
            raise TranscriberError(self.fail_message)

        if len(audio) < self.min_audio_length:
            return ""  # Too short

        self.transcribe_count += 1
        self.last_audio = audio
        return self.text_to_return

    def preload(self) -> None:
        self.preload_count += 1


# tests/mocks/hotkey.py
"""Mock hotkey components for testing."""

from dataclasses import dataclass, field
from typing import Callable, Optional, Any


@dataclass
class FakeKey:
    """Fake pynput Key object."""
    name: str

    def __eq__(self, other):
        if hasattr(other, "name"):
            return self.name == other.name
        return False


@dataclass
class MockHotkeyListener:
    """Mock HotkeyListener for testing without pynput."""

    on_press: Optional[Callable[[], None]] = None
    on_release: Optional[Callable[[], None]] = None

    _running: bool = field(default=False, init=False)
    _current_key: str = field(default="alt_r", init=False)

    # Call tracking
    start_count: int = field(default=0, init=False)
    stop_count: int = field(default=0, init=False)

    def start(self) -> None:
        self._running = True
        self.start_count += 1

    def stop(self) -> None:
        self._running = False
        self.stop_count += 1

    def set_key(self, key_name: str) -> None:
        self._current_key = key_name

    def simulate_press(self) -> None:
        """Simulate hotkey press for testing."""
        if self.on_press:
            self.on_press()

    def simulate_release(self) -> None:
        """Simulate hotkey release for testing."""
        if self.on_release:
            self.on_release()


# tests/mocks/typer.py
"""Mock text typer for testing."""

from dataclasses import dataclass, field


@dataclass
class MockTextTyper:
    """Mock TextTyper for testing without system keyboard/clipboard."""

    should_fail: bool = False
    fail_message: str = "Mock typing error"

    # Capture what was typed
    typed_texts: list[str] = field(default_factory=list)
    type_count: int = field(default=0, init=False)

    def type_text(self, text: str) -> None:
        if self.should_fail:
            raise RuntimeError(self.fail_message)

        self.typed_texts.append(text)
        self.type_count += 1

    def clear(self) -> None:
        """Reset captured texts."""
        self.typed_texts.clear()
        self.type_count = 0
```

---

## Sample Test Implementations

### Unit Tests - Pure Functions

```python
# tests/unit/test_intel_extract.py
"""Tests for intel JSON extraction."""

import pytest
from holdspeak.intel import _extract_json


class TestExtractJsonValid:
    """Test valid JSON extraction."""

    def test_plain_json_object(self):
        response = '{"topics": ["AI", "ML"], "summary": "Discussion"}'
        result = _extract_json(response)
        assert result["topics"] == ["AI", "ML"]
        assert result["summary"] == "Discussion"

    def test_json_in_markdown_code_block(self):
        response = '''Here is the analysis:
```json
{"topics": ["Testing"], "summary": "Test meeting"}
```
Done.'''
        result = _extract_json(response)
        assert result["topics"] == ["Testing"]

    def test_json_with_surrounding_text(self):
        response = 'The result is {"key": "value"} as shown.'
        result = _extract_json(response)
        assert result["key"] == "value"

    def test_nested_objects(self):
        response = '{"outer": {"inner": "value"}}'
        result = _extract_json(response)
        assert result["outer"]["inner"] == "value"

    def test_arrays_in_json(self):
        response = '{"items": [1, 2, 3]}'
        result = _extract_json(response)
        assert result["items"] == [1, 2, 3]


class TestExtractJsonInvalid:
    """Test handling of invalid JSON."""

    def test_empty_string(self):
        result = _extract_json("")
        assert result == {}

    def test_no_json_present(self):
        result = _extract_json("Just plain text without any JSON")
        assert result == {}

    def test_malformed_json(self):
        result = _extract_json('{"unclosed": "brace"')
        assert result == {}

    def test_json_array_not_object(self):
        # Depending on implementation, might return {} or handle arrays
        result = _extract_json('[1, 2, 3]')
        # Assert based on expected behavior
        assert isinstance(result, (dict, list))


class TestExtractJsonEdgeCases:
    """Test edge cases in JSON extraction."""

    def test_unicode_content(self):
        response = '{"message": "Hello \u4e16\u754c"}'
        result = _extract_json(response)
        assert "message" in result

    def test_escaped_quotes(self):
        response = '{"text": "He said \\"hello\\""}'
        result = _extract_json(response)
        assert result["text"] == 'He said "hello"'

    def test_whitespace_only(self):
        result = _extract_json("   \n\t  ")
        assert result == {}

    def test_multiple_json_objects(self):
        # Should extract first valid JSON
        response = '{"first": 1} {"second": 2}'
        result = _extract_json(response)
        assert "first" in result or "second" in result


# tests/unit/test_audio_resample.py
"""Tests for audio resampling."""

import pytest
import numpy as np
from holdspeak.audio import _linear_resample_mono


class TestResampleBasic:
    """Basic resampling tests."""

    def test_same_rate_returns_copy(self):
        audio = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        result = _linear_resample_mono(audio, 16000, 16000)
        np.testing.assert_array_equal(result, audio)

    def test_upsample_doubles_length(self):
        audio = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        result = _linear_resample_mono(audio, 8000, 16000)
        assert len(result) == 8  # Double the samples

    def test_downsample_halves_length(self):
        audio = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], dtype=np.float32)
        result = _linear_resample_mono(audio, 16000, 8000)
        assert len(result) == 4

    def test_empty_array(self):
        audio = np.array([], dtype=np.float32)
        result = _linear_resample_mono(audio, 16000, 8000)
        assert len(result) == 0


class TestResampleAccuracy:
    """Test resampling numerical accuracy."""

    def test_preserves_dc_component(self):
        """Constant signal should remain constant after resampling."""
        audio = np.ones(1000, dtype=np.float32) * 0.5
        result = _linear_resample_mono(audio, 48000, 16000)
        np.testing.assert_allclose(result, 0.5, rtol=1e-5)

    def test_output_dtype_is_float32(self):
        audio = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        result = _linear_resample_mono(audio, 16000, 8000)
        assert result.dtype == np.float32


# tests/unit/test_config.py
"""Tests for configuration management."""

import pytest
import json
from pathlib import Path
from holdspeak.config import Config, HotkeyConfig, ModelConfig, UIConfig


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_hotkey(self):
        config = Config()
        assert config.hotkey.key == "alt_r"

    def test_default_model(self):
        config = Config()
        assert config.model.name == "base"

    def test_default_ui_shows_meter(self):
        config = Config()
        assert config.ui.show_audio_meter is True

    def test_default_history_lines(self):
        config = Config()
        assert config.ui.history_lines == 10


class TestConfigPersistence:
    """Test config save/load operations."""

    def test_save_creates_file(self, tmp_path):
        config = Config()
        config_path = tmp_path / "config.json"
        config.save(config_path)
        assert config_path.exists()

    def test_save_creates_valid_json(self, tmp_path):
        config = Config()
        config_path = tmp_path / "config.json"
        config.save(config_path)

        # Should parse without error
        data = json.loads(config_path.read_text())
        assert "hotkey" in data

    def test_load_restores_values(self, tmp_path):
        config = Config()
        config.hotkey.key = "f5"
        config.model.name = "tiny"

        config_path = tmp_path / "config.json"
        config.save(config_path)

        loaded = Config.load(config_path)
        assert loaded.hotkey.key == "f5"
        assert loaded.model.name == "tiny"

    def test_load_missing_file_returns_defaults(self, tmp_path):
        config_path = tmp_path / "nonexistent.json"
        config = Config.load(config_path)
        assert config.hotkey.key == "alt_r"

    def test_load_malformed_json_returns_defaults(self, tmp_path):
        config_path = tmp_path / "bad.json"
        config_path.write_text("{invalid json")
        config = Config.load(config_path)
        assert config.hotkey.key == "alt_r"

    def test_load_partial_config_fills_defaults(self, tmp_path):
        config_path = tmp_path / "partial.json"
        config_path.write_text('{"hotkey": {"key": "f1"}}')
        config = Config.load(config_path)
        assert config.hotkey.key == "f1"
        assert config.model.name == "base"  # Default


class TestHotkeyConfig:
    """Test hotkey configuration."""

    @pytest.mark.parametrize("key_name", [
        "alt_r", "alt_l", "ctrl_r", "ctrl_l",
        "f1", "f2", "f5", "f12",
        "caps_lock",
    ])
    def test_valid_key_names(self, key_name):
        config = HotkeyConfig(key=key_name)
        assert config.key == key_name

    def test_display_contains_symbol_for_alt(self):
        config = HotkeyConfig(key="alt_r")
        # Should have some display representation
        assert config.display is not None
        assert len(config.display) > 0
```

### Integration Tests

```python
# tests/integration/test_web_server.py
"""Integration tests for web server."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime


@pytest.fixture
def mock_meeting_callbacks():
    """Create mock callbacks for MeetingWebServer."""
    bookmarks = []
    stopped = False

    def on_bookmark(label: str):
        bookmark = {
            "label": label,
            "timestamp": 123.45,
            "created_at": datetime.now().isoformat(),
        }
        bookmarks.append(bookmark)
        return bookmark

    def on_stop():
        nonlocal stopped
        stopped = True
        return {"status": "stopped"}

    def get_state():
        return {
            "id": "test-meeting",
            "started_at": "2024-01-15T10:30:00",
            "segments": [],
            "bookmarks": bookmarks,
        }

    return {
        "on_bookmark": on_bookmark,
        "on_stop": on_stop,
        "get_state": get_state,
        "_bookmarks": bookmarks,
        "_stopped": lambda: stopped,
    }


@pytest.fixture
def web_server(mock_meeting_callbacks):
    """Create and start test web server."""
    from holdspeak.web_server import MeetingWebServer

    server = MeetingWebServer(
        on_bookmark=mock_meeting_callbacks["on_bookmark"],
        on_stop=mock_meeting_callbacks["on_stop"],
        get_state=mock_meeting_callbacks["get_state"],
    )
    server.start()
    yield server, mock_meeting_callbacks
    server.stop()


class TestWebServerEndpoints:
    """Test HTTP endpoints."""

    def test_root_returns_html(self, web_server):
        server, _ = web_server
        client = TestClient(server._app)

        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_state_endpoint(self, web_server):
        server, _ = web_server
        client = TestClient(server._app)

        response = client.get("/api/state")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "test-meeting"
        assert "segments" in data

    def test_bookmark_endpoint_creates_bookmark(self, web_server):
        server, callbacks = web_server
        client = TestClient(server._app)

        response = client.post(
            "/api/bookmark",
            json={"label": "Important point"}
        )
        assert response.status_code == 200
        assert len(callbacks["_bookmarks"]) == 1
        assert callbacks["_bookmarks"][0]["label"] == "Important point"

    def test_stop_endpoint(self, web_server):
        server, callbacks = web_server
        client = TestClient(server._app)

        response = client.post("/api/stop")
        assert response.status_code == 200
        assert response.json()["status"] == "stopped"


class TestWebServerUtils:
    """Test utility functions."""

    def test_format_duration_seconds(self):
        from holdspeak.web_server import _format_duration
        assert _format_duration(45) == "0:45"

    def test_format_duration_minutes(self):
        from holdspeak.web_server import _format_duration
        assert _format_duration(125) == "2:05"

    def test_format_duration_hours(self):
        from holdspeak.web_server import _format_duration
        assert _format_duration(3665) == "1:01:05"

    def test_find_free_port(self):
        from holdspeak.web_server import _find_free_port
        port = _find_free_port()
        assert 1024 < port < 65535


# tests/integration/test_tui.py
"""Integration tests for TUI."""

import pytest
from holdspeak.tui import HoldSpeakApp, SettingsScreen
from holdspeak.config import Config


@pytest.mark.asyncio
class TestTuiStates:
    """Test TUI state transitions."""

    async def test_starts_in_idle_state(self):
        config = Config()
        app = HoldSpeakApp(config=config)

        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            # App should start in idle state
            # (verify based on actual implementation)

    async def test_set_state_updates_display(self):
        config = Config()
        app = HoldSpeakApp(config=config)

        async with app.run_test(size=(100, 30)) as pilot:
            app.set_state("recording")
            await pilot.pause()
            # Recording state should be reflected in UI

    async def test_audio_level_updates(self):
        config = Config()
        app = HoldSpeakApp(config=config)

        async with app.run_test(size=(100, 30)) as pilot:
            app.set_state("recording")
            app.set_audio_level(0.75)
            await pilot.pause()
            # Audio level should be displayed


@pytest.mark.asyncio
class TestTuiKeyboardShortcuts:
    """Test keyboard shortcuts."""

    async def test_q_quits_app(self):
        config = Config()
        app = HoldSpeakApp(config=config)

        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.press("q")
            # App should exit

    async def test_s_opens_settings(self):
        config = Config()
        app = HoldSpeakApp(config=config)

        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.press("s")
            await pilot.pause()

            # Settings screen should be visible
            assert isinstance(app.screen, SettingsScreen)
```

### End-to-End Tests

```python
# tests/e2e/test_voice_typing_flow.py
"""End-to-end tests for voice typing flow."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from tests.mocks.audio import MockAudioRecorder
from tests.mocks.transcriber import MockTranscriber
from tests.mocks.typer import MockTextTyper
from tests.mocks.hotkey import MockHotkeyListener


class TestVoiceTypingPipeline:
    """Test complete voice typing pipeline."""

    @pytest.fixture
    def pipeline_mocks(self, sine_440hz_1s):
        """Set up all mocked components."""
        return {
            "recorder": MockAudioRecorder(audio_to_return=sine_440hz_1s),
            "transcriber": MockTranscriber(text_to_return="Hello world"),
            "typer": MockTextTyper(),
            "hotkey": MockHotkeyListener(),
        }

    def test_press_record_release_types(self, pipeline_mocks):
        """Full flow: press hotkey → record → release → transcribe → type."""
        recorder = pipeline_mocks["recorder"]
        transcriber = pipeline_mocks["transcriber"]
        typer = pipeline_mocks["typer"]
        hotkey = pipeline_mocks["hotkey"]

        # Wire up callbacks (simulating HoldSpeakController)
        def on_press():
            recorder.start()

        def on_release():
            audio = recorder.stop()
            if len(audio) > 8000:  # Minimum length
                text = transcriber.transcribe(audio)
                if text:
                    typer.type_text(text)

        hotkey.on_press = on_press
        hotkey.on_release = on_release

        # Simulate user interaction
        hotkey.simulate_press()
        assert recorder.is_recording()

        hotkey.simulate_release()
        assert not recorder.is_recording()

        # Verify pipeline completed
        assert transcriber.transcribe_count == 1
        assert typer.typed_texts == ["Hello world"]

    def test_short_recording_not_transcribed(self, pipeline_mocks):
        """Short recordings should be ignored."""
        # Use very short audio
        pipeline_mocks["recorder"].audio_to_return = np.zeros(1000, dtype=np.float32)

        recorder = pipeline_mocks["recorder"]
        transcriber = pipeline_mocks["transcriber"]
        typer = pipeline_mocks["typer"]
        hotkey = pipeline_mocks["hotkey"]

        def on_press():
            recorder.start()

        def on_release():
            audio = recorder.stop()
            if len(audio) > 8000:
                text = transcriber.transcribe(audio)
                if text:
                    typer.type_text(text)

        hotkey.on_press = on_press
        hotkey.on_release = on_release

        hotkey.simulate_press()
        hotkey.simulate_release()

        # Should not have transcribed or typed
        assert transcriber.transcribe_count == 0
        assert typer.typed_texts == []

    def test_empty_transcription_not_typed(self, pipeline_mocks, sine_440hz_1s):
        """Empty transcription results should not be typed."""
        pipeline_mocks["transcriber"].text_to_return = ""

        recorder = pipeline_mocks["recorder"]
        transcriber = pipeline_mocks["transcriber"]
        typer = pipeline_mocks["typer"]
        hotkey = pipeline_mocks["hotkey"]

        def on_press():
            recorder.start()

        def on_release():
            audio = recorder.stop()
            if len(audio) > 8000:
                text = transcriber.transcribe(audio)
                if text:
                    typer.type_text(text)

        hotkey.on_press = on_press
        hotkey.on_release = on_release

        hotkey.simulate_press()
        hotkey.simulate_release()

        assert transcriber.transcribe_count == 1
        assert typer.typed_texts == []  # Nothing typed
```

---

## Configuration

### pyproject.toml additions

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
markers = [
    "slow: marks tests as slow-running (deselect with '-m \"not slow\"')",
    "requires_model: requires ML model to be loaded",
    "requires_macos: requires macOS system",
    "integration: integration test",
    "e2e: end-to-end test",
]
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]
addopts = [
    "--strict-markers",
    "-ra",  # Show summary of all non-passed tests
]

[tool.coverage.run]
source = ["holdspeak"]
branch = true
omit = [
    "holdspeak/__main__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "@abstractmethod",
]
fail_under = 70
show_missing = true

[tool.coverage.html]
directory = "htmlcov"
```

### Test Dependencies

Add to `pyproject.toml` dev dependencies:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
    "pytest-mock>=3.12",
    "pytest-timeout>=2.2",
    "httpx>=0.26",  # For FastAPI TestClient async
    "freezegun>=1.2",  # Time mocking
]
```

---

## CI/CD Configuration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync --dev

      - name: Run unit tests
        run: |
          uv run pytest tests/unit -v \
            --cov=holdspeak \
            --cov-report=xml \
            --cov-report=term-missing

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
          fail_ci_if_error: false

  integration-tests:
    name: Integration Tests (macOS)
    runs-on: macos-14  # Apple Silicon

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync --dev

      - name: Run integration tests
        run: |
          uv run pytest tests/integration -v \
            -m "not requires_model" \
            --timeout=60

  lint:
    name: Lint
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync --dev

      - name: Run ruff
        run: uv run ruff check holdspeak tests
```

---

## Implementation Roadmap

### Phase 1: Foundation (4-6 hours)
- [ ] Create `tests/` directory structure
- [ ] Write `conftest.py` with core fixtures
- [ ] Create `tests/mocks/` with mock implementations
- [ ] Add test dependencies to `pyproject.toml`
- [ ] Verify pytest runs with `uv run pytest`

### Phase 2: Unit Tests - Pure Functions (4-6 hours)
- [ ] `test_config.py` - 20-25 tests
- [ ] `test_intel_extract.py` - 15-20 tests
- [ ] `test_intel_coerce.py` - 10-15 tests
- [ ] `test_audio_resample.py` - 10-12 tests
- [ ] `test_hotkey_mapping.py` - 8-10 tests
- [ ] `test_web_utils.py` - 8-10 tests

### Phase 3: Unit Tests - Data Classes (3-4 hours)
- [ ] `test_meeting_state.py` - 15-20 tests
- [ ] `test_meeting_chunks.py` - 12-15 tests
- [ ] `test_transcript_segment.py` - 8-10 tests

### Phase 4: Integration Tests (6-8 hours)
- [ ] `test_web_server.py` - 15-20 tests
- [ ] `test_tui.py` - 15-20 tests
- [ ] `test_meeting_session.py` - 15-20 tests
- [ ] `test_audio_recorder.py` - 10-12 tests
- [ ] `test_transcriber.py` - 8-10 tests

### Phase 5: E2E Tests (3-4 hours)
- [ ] `test_voice_typing_flow.py` - 5-8 tests
- [ ] `test_meeting_flow.py` - 5-8 tests

### Phase 6: CI Integration (2-3 hours)
- [ ] Create `.github/workflows/test.yml`
- [ ] Configure codecov integration
- [ ] Add status badges to README
- [ ] Set up branch protection rules

---

## Expected Outcomes

| Metric | Target |
|--------|--------|
| Total tests | 200-250 |
| Unit test coverage | 80%+ |
| Overall coverage | 70%+ |
| Unit test runtime | <10 seconds |
| Full test suite | <2 minutes |
| CI pipeline | <5 minutes |

---

## Notes

### Why This Approach Works

1. **Mock at boundaries** - External dependencies (hardware, ML, OS) are mocked at module boundaries, not deep inside functions
2. **Pure functions tested directly** - ~40% of code is pure logic that needs no mocks
3. **Textual/FastAPI have test tools** - Built-in testing support reduces custom mock code
4. **Incremental adoption** - Can add tests module-by-module without blocking development

### What Won't Be Tested

- Actual audio hardware capture
- Real ML model inference (except optional slow tests)
- Real keyboard/clipboard operations
- macOS-specific system interactions

These are explicitly out of scope for automated testing and should be verified through manual QA on real hardware.
