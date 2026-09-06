"""Global test fixtures and configuration for HoldSpeak tests."""

from __future__ import annotations

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime
from typing import TYPE_CHECKING

try:
    from starlette.testclient import TestClient as _StarletteTestClient
except ImportError:  # web is an optional dependency in the base test environment
    _StarletteTestClient = None


# MeetingWebServer now authenticates loopback exactly like every other bind.
# Existing route tests represent the owner browser, so make that construction
# explicit once at the harness edge instead of adding a production test bypass
# or touching hundreds of unrelated call sites.
if _StarletteTestClient is not None:
    _original_test_client_init = _StarletteTestClient.__init__

    def _owner_test_client_init(self, app, *args, **kwargs):
        _original_test_client_init(self, app, *args, **kwargs)
        token = str(getattr(getattr(app, "state", None), "owner_token", "") or "")
        if token:
            self.headers.setdefault("X-HoldSpeak-Token", token)

    _StarletteTestClient.__init__ = _owner_test_client_init


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


def pytest_addoption(parser):
    parser.addoption(
        "--run-metal",
        action="store_true",
        default=False,
        help="run opt-in tests that require a real microphone/model/keyboard",
    )


# ============================================================
# HS-200-03: the isolated-HOME guard
# ============================================================

REAL_HOME_OPT_IN = "HOLDSPEAK_ALLOW_REAL_HOME"

# `holdspeak.config.core.CONFIG_DIR` and `holdspeak.db.core.DEFAULT_DB_PATH`
# are built from `Path.home()` at IMPORT time, so an installation is detected
# by the two directories those constants live in — named here rather than
# imported, because importing holdspeak would freeze the very paths we are
# checking before the guard could refuse.
_INSTALLATION_MARKERS = (
    Path(".local") / "share" / "holdspeak",
    Path(".config") / "holdspeak",
)


def _passwd_home() -> Path | None:
    """The account's home from the password database, ignoring ``$HOME``.

    ``$HOME`` is the thing under test, so it cannot also be the reference.
    """
    import pwd
    import os as _os

    try:
        return Path(pwd.getpwuid(_os.getuid()).pw_dir)
    except Exception:  # pragma: no cover - no passwd entry (some containers)
        return None


def real_home_violation(
    home: Path | str, passwd_home: Path | str | None, *, opt_in: str = ""
) -> str:
    """The refusal text for a run pointed at a real installation, else ``""``.

    The dangerous condition is precise: ``$HOME`` is the account's own home
    AND a HoldSpeak installation lives under it. That is the owner's real
    database and config, and a product suite writing there has destroyed real
    rows before (schema v43 pollution, the 167/168 walk seeds). A bare CI
    runner is also its own passwd home but holds no installation, so it is
    lawful and is not refused.

    ``opt_in`` is the value of ``HOLDSPEAK_ALLOW_REAL_HOME``; a live attended
    walk sets it to the name of the walk it is running, which is echoed back
    in the run header so the choice is never silent.
    """
    if str(opt_in).strip():
        return ""
    if passwd_home is None:
        return ""
    try:
        resolved_home = Path(home).expanduser().resolve()
        resolved_passwd = Path(passwd_home).expanduser().resolve()
    except Exception:  # pragma: no cover - unresolvable path
        return ""
    if resolved_home != resolved_passwd:
        return ""
    present = [
        str(resolved_home / marker)
        for marker in _INSTALLATION_MARKERS
        if (resolved_home / marker).exists()
    ]
    if not present:
        return ""
    return (
        "refusing to run the product suite against a real HoldSpeak "
        f"installation: HOME={resolved_home} holds " + ", ".join(present) + ". "
        "Run with an isolated HOME instead:\n"
        "  HOME=$(mktemp -d) uv run pytest ...\n"
        f"An attended live walk sets {REAL_HOME_OPT_IN}=<walk name> to accept "
        "this deliberately."
    )


def _enforce_isolated_home(config) -> None:
    import os

    home = os.environ.get("HOME") or str(Path.home())
    opt_in = os.environ.get(REAL_HOME_OPT_IN, "")
    violation = real_home_violation(home, _passwd_home(), opt_in=opt_in)
    if violation:
        raise pytest.UsageError(violation)


def pytest_report_header(config):
    """Never silent: every run states where its HOME points."""
    import os

    home = os.environ.get("HOME") or str(Path.home())
    opt_in = os.environ.get(REAL_HOME_OPT_IN, "")
    if opt_in.strip():
        return (
            f"holdspeak: HOME isolation WAIVED by {REAL_HOME_OPT_IN}="
            f"{opt_in!r} — running against HOME={home}"
        )
    return f"holdspeak: HOME={home}"


def pytest_configure(config):
    """Register custom markers; isolate HOME per xdist worker."""
    # HS-132-12: under pytest-xdist every worker inherited ONE $HOME, so any
    # two tests touching the default Path.home() state (the holdspeak DB,
    # npm/npx locks, model dirs) could collide across workers — the whole
    # genus of "green solo, red parallel" flakes (UNIQUE constraint,
    # RecipeVerifyError, npx lock corruption). Each worker gets its own
    # subdirectory of the run's HOME instead. Serial runs are unchanged, and
    # absolute-path passthroughs (PLAYWRIGHT_BROWSERS_PATH, npm_config_cache)
    # are unaffected.
    import os

    # HS-200-03: refuse a real installation BEFORE anything imports holdspeak
    # (its path constants freeze at import) and before the xdist rewrite below
    # turns HOME into a subdirectory of whatever it was.
    _enforce_isolated_home(config)

    worker = os.environ.get("PYTEST_XDIST_WORKER")
    if worker:
        per_worker = Path(os.environ["HOME"]) / f"xdist-{worker}"
        per_worker.mkdir(parents=True, exist_ok=True)
        os.environ["HOME"] = str(per_worker)
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
    config.addinivalue_line(
        "markers", "critical: G0 critical journey (tests/critical)"
    )
    config.addinivalue_line(
        "markers",
        "requires_mlx_whisper: requires the mlx_whisper package on this machine",
    )
    config.addinivalue_line(
        "markers",
        "requires_local_dictation_route: requires this machine to resolve an "
        "on-device dictation artifact from default configuration",
    )


# ============================================================
# HS-200-03: availability probes behind the dependency markers
#
# A declared dependency that is absent must SKIP with the reason. It must
# never pass silently (the absence would then be invisible) and it must never
# fail as if the product were broken (it is the environment that is missing).
# Each probe answers "" when the dependency is present, or the reason text.
# ============================================================


def missing_local_model_reason() -> str:
    """Why the configured local meeting-intel model file cannot be loaded."""
    try:
        from holdspeak.inference_targets import local_model_file_present
        from holdspeak.intel.providers import configured_local_meeting_model_path

        path = configured_local_meeting_model_path()
    except Exception as exc:  # pragma: no cover - import-time environment fault
        return f"local model readiness could not be probed: {exc}"
    if local_model_file_present(path):
        return ""
    return f"no local model file on this machine: {path or '<unconfigured>'}"


def missing_mlx_whisper_reason() -> str:
    """Why mlx_whisper is unusable here (absent off Apple silicon)."""
    import importlib.util

    try:
        if importlib.util.find_spec("mlx_whisper") is not None:
            return ""
    except Exception as exc:  # pragma: no cover - broken namespace package
        return f"mlx_whisper is not importable: {exc}"
    return "mlx_whisper is not installed on this machine"


def missing_local_dictation_route_reason() -> str:
    """Why default configuration names no on-device dictation artifact.

    `_local_dictation_engine` resolves `auto` to MLX on Apple silicon with
    `mlx_lm` importable, and to llama.cpp everywhere else. Neither engine's
    package is a core dependency: `mlx-whisper` is `sys_platform == 'darwin'
    and platform_machine == 'arm64'` and `llama-cpp-python` lives in the
    `meeting` extra (pyproject.toml). The Unit job installs `--extra test`
    only, so on that runner the resolved engine has no package behind it, the
    speech route cannot be frozen, and admission refuses `no_assignment`.

    That is the environment, not a product defect, so the tests that assert on
    a resolved speech route declare the dependency and skip with this reason.
    """
    try:
        import importlib.util

        from holdspeak.config import Config
        from holdspeak.speech_session.plan import (
            _local_dictation_engine,
            _pipeline_terms,
            dictation_local_deployment_identity,
        )

        terms = _pipeline_terms(Config())
        engine = _local_dictation_engine(str(terms.get("runtime_backend", "") or ""))
    except Exception as exc:  # pragma: no cover - import-time environment fault
        return f"dictation route could not be probed: {exc}"
    if not engine:
        return "default configuration names no on-device dictation engine"
    if dictation_local_deployment_identity(terms) is None:
        return f"default configuration names no {engine} dictation artifact"
    package = {"mlx": "mlx_lm", "llama_cpp": "llama_cpp"}.get(engine, "")
    if package and importlib.util.find_spec(package) is None:
        return (
            f"this machine resolves the {engine} dictation engine but "
            f"{package!r} is not installed (it is an optional extra)"
        )
    return ""


_DEPENDENCY_PROBES = {
    "requires_model": missing_local_model_reason,
    "requires_mlx_whisper": missing_mlx_whisper_reason,
    "requires_local_dictation_route": missing_local_dictation_route_reason,
}


def pytest_collection_modifyitems(config, items):
    """Auto-skip tests based on markers and environment."""
    import sys

    skip_macos = pytest.mark.skip(reason="requires macOS")
    skip_metal = pytest.mark.skip(
        reason="real hardware lane; rerun with -m metal --run-metal"
    )
    # Probe each declared dependency at most once per run, and only when some
    # collected item actually declares it.
    probed: dict[str, str] = {}

    def dependency_reason(name: str) -> str:
        if name not in probed:
            probed[name] = _DEPENDENCY_PROBES[name]()
        return probed[name]

    for item in items:
        for marker_name in _DEPENDENCY_PROBES:
            if marker_name in item.keywords:
                reason = dependency_reason(marker_name)
                if reason:
                    item.add_marker(pytest.mark.skip(reason=reason))
        # Skip macOS tests on other platforms
        if "requires_macos" in item.keywords and sys.platform != "darwin":
            item.add_marker(skip_macos)
        if "metal" in item.keywords and not config.getoption("--run-metal"):
            item.add_marker(skip_metal)


@pytest.fixture(autouse=True)
def _isolate_agent_session_registry(tmp_path_factory, monkeypatch):
    """Point the coder-session registry at a per-test temp file, ALWAYS.

    The agent hooks are a real product feature that developers run on their
    own machines (HSM-17-02): a live Claude/Codex session writes
    `~/.config/holdspeak/agent_sessions.json` continuously. Without this,
    any test that touches `get_recent_agent_session` / project detection
    reads the DEVELOPER'S live coding session and flakes (found the day the
    hooks went live: the suite detected the session that was running it).
    Tests that need a registry still monkeypatch their own path on top.
    """
    import holdspeak.agent_context as agent_context

    registry = tmp_path_factory.mktemp("agent-registry") / "agent_sessions.json"
    monkeypatch.setattr(agent_context, "AGENT_CONTEXT_FILE", registry)


@pytest.fixture(autouse=True)
def _isolate_config_file(tmp_path_factory, monkeypatch):
    """HS-112-01: `Config.load()` with no explicit path is the REAL install's
    load — it runs the one-time legacy-endpoint migration, which writes to
    the profiles DB and re-saves the config. Tests must never read the
    developer's live `~/.config/holdspeak/config.json` or mint rows in the
    real DB, so the default config path is a per-test temp file. Tests that
    need a specific config still monkeypatch their own path on top."""
    import holdspeak.config as config_mod

    cfg = tmp_path_factory.mktemp("config") / "config.json"
    monkeypatch.setattr(config_mod, "CONFIG_FILE", cfg)


@pytest.fixture
def local_model_present(monkeypatch):
    """Declare the local model artifact present, without a developer's disk.

    HS-200-03: the admission path refuses with 409 `target_unavailable` when
    the configured local model file is missing. Route tests that inject their
    own engine are not testing artifact readiness, so they substitute the one
    readiness predicate rather than requiring `~/Models` to exist — which is
    what made them pass on the owner's machine and fail on every runner.
    Tests that DO mean to exercise a real artifact declare
    `@pytest.mark.requires_model` instead and skip when it is absent.
    """
    import holdspeak.inference_targets as inference_targets

    monkeypatch.setattr(
        inference_targets, "local_model_file_present", lambda _path: True
    )
    return inference_targets


@pytest.fixture(autouse=True)
def _reset_endpoint_health():
    """HS-103-04: `default_health` is one process-wide breaker so real call
    sites share state — but that makes it global mutable state across the
    WHOLE test session too. Without a reset, a test that deliberately drives
    an endpoint to consecutive failures could leave its circuit open for an
    unrelated later test keying into the same identity (e.g. the same
    default base URL). Reset before AND after so a test can't pollute a
    sibling either direction."""
    from holdspeak.intel.endpoint_health import default_health

    default_health.reset()
    yield
    default_health.reset()
