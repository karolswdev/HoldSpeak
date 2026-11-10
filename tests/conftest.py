"""Global test fixtures and configuration for HoldSpeak tests."""

from __future__ import annotations

import os

# Conductor R4: no test reaches the owner's real `gh` or `acli` through a
# production default runner (holdspeak/cli_guard.py). A hub a test starts
# inherits the flag; a test's own stub under the temp directory still runs.
# A real-metal run may set it to 0.
os.environ.setdefault("HOLDSPEAK_TEST_NO_REAL_CLI", "1")
# Betterment E2: a test hub lists no agent CLI from this machine's PATH under
# Found on this Mac. A test that needs agent engines turns them on and puts its
# fake `claude`/`codex` first on PATH (tests/fixtures/fake_agent_cli.py).
os.environ.setdefault("HOLDSPEAK_CLI_ENGINES", "off")
# A phone press or a manually ticked Program must not start the owner's CLI.
os.environ["HOLDSPEAK_AGENT_SPAWN"] = "off"
# AG15: ordinary tests must never enumerate the owner's local tmux panes. The
# isolated own-agent rig opts in only after it creates its own tmux server.
os.environ["HOLDSPEAK_OWN_AGENTS"] = "off"
# Betterment Q7: a test hub never asks an HTTP engine's server (the LAN engine
# of the fixture routes is real) whether it takes tool calls. A test of the
# Ask tool loop turns it on and replays a recorded answer.
os.environ.setdefault("HOLDSPEAK_ASK_SERVER_TOOLS", "off")
# Betterment daily D8: a finished automation run raises a desktop notice. No
# test posts one to the owner's Notification Center; a test of the post turns
# it on (or injects a notifier).
os.environ.setdefault("HOLDSPEAK_DESKTOP_NOTIFY", "0")
# Setup's LAN look is a real owner operation. Test hubs opt in only when they
# inject a deterministic producer; an isolated HOME alone never authorizes a
# probe of the host network.
os.environ["HOLDSPEAK_SETUP_LAN_SCAN"] = "off"

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
def whisper_on_device(monkeypatch):
    """Declare "the Whisper model is on this device" for a test that fakes the
    speech library itself (owner ruling 2026-10-05: a load reads only a local
    folder and never downloads).  The repository id stands in for the folder,
    so a fake mlx-whisper / faster-whisper sees the same string as before.
    The real disk check is fenced in tests/unit/test_local_ai_setup.py.
    """
    monkeypatch.setattr("holdspeak.transcribe._local_source", lambda repo: repo)
    monkeypatch.setattr("holdspeak.whisper_models.whisper_on_disk", lambda *a, **k: True)
    monkeypatch.setattr("holdspeak.whisper_models.local_whisper_dir", lambda repo, **k: Path(repo))
    # PHILO-17 speech: readiness also asks if the speech library can run here
    # (whisper_models.speech_readiness). A test that fakes the library says yes.
    import holdspeak.transcribe as _transcribe

    _real_resolve = _transcribe._resolve_backend

    def _resolve(backend: str) -> str:
        try:
            return _real_resolve(backend)
        except _transcribe.TranscriberError:
            return "mlx" if backend in ("auto", "mlx") else backend

    monkeypatch.setattr("holdspeak.transcribe._resolve_backend", _resolve)


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


# ============================================================
# Browser tests draw on the real GPU (owner ruling 2026-10-03: fast tests)
# ============================================================
#
# Headless Chromium draws WebGL in software (SwiftShader). The Floor's
# atmosphere is a full-viewport WebGL scene that draws every frame
# (web/src/desk/gl/atmosphereRuntime.ts), so one frame took 0.2 s to 1 s of
# CPU and every Playwright action waits for a frame. Measured on the desk
# debts rig at 1440: a 90-point pointer pass took 36.8 s in software and
# 0.8 s on Metal. That one cause was most of the browser suite's time.
#
# On macOS every Chromium a test launches gets `--use-angle=metal`, unless the
# test passes its own ANGLE flag. A CI runner is a VM with no dependable GPU,
# so the flag is off when CI is set. HOLDSPEAK_GLASS_GPU=0 turns it off;
# HOLDSPEAK_GLASS_GPU=1 turns it on anywhere.


def _glass_gpu_enabled() -> bool:
    import os
    import sys

    choice = os.environ.get("HOLDSPEAK_GLASS_GPU", "")
    if choice in ("0", "1"):
        return choice == "1"
    return sys.platform == "darwin" and not os.environ.get("CI")


def _launch_chromium_on_the_gpu() -> None:
    if not _glass_gpu_enabled():
        return
    try:
        from playwright.sync_api import BrowserType
    except ImportError:  # the base test environment has no Playwright
        return
    original = BrowserType.launch
    if getattr(original, "_holdspeak_gpu", False):
        return

    def launch(self, *args, **kwargs):
        if self.name == "chromium":
            flags = list(kwargs.get("args") or [])
            if not any("use-angle" in flag or "use-gl" in flag for flag in flags):
                kwargs["args"] = [*flags, "--use-angle=metal"]
        return original(self, *args, **kwargs)

    launch._holdspeak_gpu = True
    BrowserType.launch = launch


_launch_chromium_on_the_gpu()


# ============================================================
# PHILO-14 A1: the Chair is the screen of objects
# ============================================================
#
# Board A-1 (ratified 2026-10-07): a fresh desk opens with the Chair
# windows (Needs you, Capture; Betterment daily D5 retired Brief and The week
# into Today) closed; the owner opens them
# from the screen, the Dock or Window > Chair. A browser spec that reads a
# Chair window's body declares `pytest.mark.chair_windows_open`: every
# context and page it makes then starts with the four windows open (a stored
# Chair section, as the desk remembers it after he opens them). A Chair
# section the page already stored is kept, so a reload keeps what he closed.
# PHILO-16 (16b): the hub owns the windows, so the seam opens the four on the
# hub as well, the first time it writes the section in a browser.

CHAIR_WINDOWS_OPEN_JS = """(() => { try {
  const key = "hs.desk.workspace.v1";
  const raw = localStorage.getItem(key);
  const doc = raw ? JSON.parse(raw) : null;
  if (doc && doc.chair) return;
  const next = doc && doc.version === 1 ? doc : { version: 1 };
  next.chair = { closed: [], phone: "chair:needs" };
  localStorage.setItem(key, JSON.stringify(next));
  // PHILO-16 (16b): the hub owns the desk's windows, so the four are opened
  // on the hub too (before the page reads it: synchronous), Needs you last
  // (in front). A page with no token (no hub session yet) keeps the cache.
  if (!/^https?:$/.test(location.protocol)) return;
  const token = new URLSearchParams(location.search).get("token") || localStorage.getItem("hs.web.token") || sessionStorage.getItem("hs.web.token");
  if (!token) return;
  for (const id of ["chair:capture", "chair:needs"]) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/desk/windows/" + encodeURIComponent(id) + "/open", false);
    xhr.setRequestHeader("Authorization", "Bearer " + token);
    xhr.setRequestHeader("Content-Type", "application/json");
    try { xhr.send("{}"); } catch (e) {}
  }
} catch (e) {} })();"""

_CHAIR_WINDOWS_OPEN = {"on": False}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item):
    # Before any fixture of the item (a class- or module-scoped context too).
    _CHAIR_WINDOWS_OPEN["on"] = item.get_closest_marker("chair_windows_open") is not None
    # A new test database is a copy of one schema template (tests/_template_db.py).
    from tests import _template_db

    _template_db.install()
    _template_db.set_real_schema(item.get_closest_marker("real_schema") is not None)
    yield


def _chair_windows_open_seam() -> None:
    try:
        from playwright.sync_api import Browser
    except ImportError:  # the base test environment has no Playwright
        return
    if getattr(Browser.new_context, "_holdspeak_chair", False):
        return
    new_context, new_page = Browser.new_context, Browser.new_page

    def context(self, *args, **kwargs):
        ctx = new_context(self, *args, **kwargs)
        if _CHAIR_WINDOWS_OPEN["on"]:
            ctx.add_init_script(CHAIR_WINDOWS_OPEN_JS)
        return ctx

    def page(self, *args, **kwargs):
        pg = new_page(self, *args, **kwargs)
        if _CHAIR_WINDOWS_OPEN["on"]:
            pg.add_init_script(CHAIR_WINDOWS_OPEN_JS)
        return pg

    context._holdspeak_chair = True
    Browser.new_context, Browser.new_page = context, page


_chair_windows_open_seam()


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


def pytest_unconfigure(config):
    """Stop the run's own tmux server and remove its socket dir (see pytest_configure)."""
    import os
    import shutil
    import subprocess

    from tests import _template_db

    _template_db.cleanup()
    tmux_dir = os.environ.get("TMUX_TMPDIR", "")
    if not os.path.basename(tmux_dir).startswith("hs-tmux-"):
        return
    if shutil.which("tmux"):
        subprocess.run(["tmux", "kill-server"], capture_output=True, timeout=10, check=False)
    shutil.rmtree(tmux_dir, ignore_errors=True)


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
    from tests._process_guard import ProcessGuard

    config._holdspeak_process_guard = ProcessGuard()
    config._holdspeak_process_guard.install()
    config.addinivalue_line(
        "markers",
        "real_schema: a new database runs the real schema script and reconcile, never the template copy (tests/_template_db.py)",
    )
    config.addinivalue_line(
        "markers",
        "chair_windows_open: the browser spec reads a Chair window; its pages start with the four open (PHILO-14 A1)",
    )

    worker = os.environ.get("PYTEST_XDIST_WORKER")
    if worker:
        per_worker = Path(os.environ["HOME"]) / f"xdist-{worker}"
        per_worker.mkdir(parents=True, exist_ok=True)
        os.environ["HOME"] = str(per_worker)
    # tmux finds its server by TMUX_TMPDIR (default /tmp) and $TMUX, never by
    # HOME: an isolated HOME still listed the machine's real tmux sessions on
    # the Delivery board, and a test's session landed on the real server. Each
    # run (each xdist worker) gets its own socket dir. It is not under HOME: a
    # unix socket path has a 104-byte limit on macOS, and a mktemp HOME plus
    # xdist-gwN/tmux-UID/default is longer. Child hubs inherit it;
    # pytest_unconfigure stops that server and removes the dir.
    import tempfile

    os.environ["TMUX_TMPDIR"] = tempfile.mkdtemp(prefix="hs-tmux-", dir="/tmp")
    os.environ.pop("TMUX", None)
    os.environ.pop("TMUX_PANE", None)
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
    config.addinivalue_line(
        "markers",
        "requires_openai_client: requires the `openai` client package (the "
        "`meeting` / `dictation-openai` extras) on this machine",
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
    """Why this machine cannot give the engine door a local speech engine.

    The startup migration assigns ``speech.transcribe`` to the built-in
    Whisper profile of the backend ``auto`` resolves to (MLX on Apple silicon,
    faster-whisper elsewhere). Neither package is a core dependency, so on a
    runner with neither the chain has no engine and a capture refuses
    ``no_engine``. That is the environment, not a product defect.
    """
    try:
        from holdspeak.transcribe import _resolve_backend

        _resolve_backend("auto")
    except Exception as exc:  # pragma: no cover - environment-dependent
        return f"this machine has no local Whisper backend: {type(exc).__name__}: {exc}"
    return ""


def missing_openai_client_reason() -> str:
    """Why no OpenAI-compatible endpoint can be called on this machine.

    The product's ONLY transport for an OpenAI-compatible endpoint is the
    `openai` package (`holdspeak/intel/__init__.py` imports it, and
    `get_cloud_intel_runtime_status` answers "openai package is not available"
    without it). It is not a core dependency: it lives in the `meeting` and
    `dictation-openai` extras (pyproject.toml), and the CI Integration job
    installs `--extra test` only.

    The HS-200-08 evaluation harness substitutes the MODEL and nothing else:
    its `--engine canned` stub is a real local OpenAI-compatible HTTP server
    that the product's own client, egress guard and admission path call. With
    no client package the route probes UNREACHABLE
    (`reason_code: inference_failed`) and every model-bearing leg fails. That
    is the environment, not a product defect, so the tests that need the
    canned model to actually answer declare the dependency and skip with this
    reason. The tests that prove the harness's own behaviour when a model
    CANNOT be reached stay ungated and run everywhere.
    """
    import importlib.util

    try:
        if importlib.util.find_spec("openai") is not None:
            return ""
    except Exception as exc:  # pragma: no cover - broken namespace package
        return f"the openai client package is not importable: {exc}"
    return (
        "the `openai` client package is not installed on this machine; it is "
        "an optional extra (`meeting` / `dictation-openai`) and the product "
        "has no other transport for an OpenAI-compatible endpoint"
    )


_DEPENDENCY_PROBES = {
    "requires_model": missing_local_model_reason,
    "requires_mlx_whisper": missing_mlx_whisper_reason,
    "requires_local_dictation_route": missing_local_dictation_route_reason,
    "requires_openai_client": missing_openai_client_reason,
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


@pytest.fixture(scope="session", autouse=True)
def _git_without_the_xcrun_shim(tmp_path_factory):
    """On macOS ``/usr/bin/git`` is an xcrun shim: 12 ms a call against 5 ms
    for the real binary. The Programs rig and the engine run hundreds of git
    calls per test (test_program_delivery: 23 s to 17 s at -n 4). Put the
    real binary first on PATH for this run; elsewhere this does nothing."""
    import shutil
    import subprocess
    import sys

    if sys.platform != "darwin" or shutil.which("git") != "/usr/bin/git":
        yield
        return
    found = subprocess.run(["xcrun", "--find", "git"], capture_output=True, text=True)
    real = found.stdout.strip()
    if found.returncode != 0 or not real or not os.access(real, os.X_OK):
        yield
        return
    shim_dir = tmp_path_factory.mktemp("git-bin")
    (shim_dir / "git").symlink_to(real)
    before = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{shim_dir}{os.pathsep}{before}"
    yield
    os.environ["PATH"] = before


@pytest.fixture(autouse=True)
def _bare_composition_root():
    """HS-200-45: install a BARE composition root for every test, ALWAYS.

    Outside a hub, `holdspeak.runtime.composition.current()` refuses to
    improvise a root — that refusal is the fence that stops the MCP sidecar
    becoming a second writer on the owner's live database. A unit test is
    exactly the lawful exception: it runs on an isolated HOME (enforced by
    `_enforce_isolated_home` below) and it owns whatever database it opens.

    The bare root shares NO database handle (`db=None`), which is
    load-bearing: every MCP module keeps falling back to its own
    `get_database` symbol, so the ~40 test files that monkeypatch
    `<module>.get_database` per module keep working unchanged. A test that
    builds a real hub app gets that hub's root installed over this one by
    `_create_app`, and the next test gets a fresh bare one.
    """
    from holdspeak.runtime import composition

    composition.install(composition.bare(label="pytest"))
    try:
        yield
    finally:
        composition.uninstall()


@pytest.fixture(autouse=True)
def _no_leaked_database_or_owner_claim():
    """A test gives back the process-wide database state it took, ALWAYS.

    xdist runs many files in one worker process. Main went red on all three
    of these leaks, 2026-10-12:

    * the DB singleton (`holdspeak.db.core._db`) left on a test's tmp file:
      a later test reads a database without its tables ("no such table");
    * the needs-you last-known store (`needs_you_aggregate._LAST_KNOWN`)
      bound once to a test's tmp database: a later hub adopts the store and
      writes its rows to that foreign file;
    * the owner claim (`runtime_lock._LOCK`) left held: a later test's claim
      fails ("this process already owns a database").

    Only what THIS test took is given back: state that a wider fixture made
    before the test starts stays. A leaked singleton or store binding is
    reset quietly (cheap; more than 100 tests leave a singleton). A leaked
    claim is released and the test fails, so the leaker is named at its
    source.
    """
    from holdspeak import runtime_lock
    from holdspeak.db import core as db_core
    from holdspeak.services import needs_you_aggregate

    store = needs_you_aggregate._LAST_KNOWN
    db_before = db_core._db
    store_bound_before = store._db_factory
    lock_before = runtime_lock._LOCK
    yield
    if db_core._db is not None and db_before is None:
        db_core.reset_database()
    if store._db_factory is not None and store_bound_before is None:
        with store._lock:
            store._db_factory = None
            store._by_source.clear()
    lock = runtime_lock._LOCK
    if lock is not None and lock is not lock_before:
        held_path = lock.db_path
        runtime_lock.release_database()
        pytest.fail(
            f"the test left the database owner claim held on {held_path}; "
            "release it (runtime_lock.release_database) before the test ends"
        )


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
    from holdspeak.net_bounds import endpoint_checks

    # Lane HUB TIMEOUTS: the endpoints' last checks are process-wide too.
    default_health.reset()
    endpoint_checks.reset()
    yield
    default_health.reset()
    endpoint_checks.reset()


@pytest.fixture(autouse=True)
def _agent_spawn_isolated(monkeypatch, request, tmp_path_factory):
    """Even a preceding opt-in cannot let another test start an agent."""
    monkeypatch.setenv("HOLDSPEAK_AGENT_SPAWN", "off")
    yield
    guard = getattr(request.config, "_holdspeak_process_guard", None)
    if guard is not None:
        guard.paths[request.node.nodeid] = str(
            request.node.funcargs.get("tmp_path", tmp_path_factory.getbasetemp())
        )


@pytest.fixture
def allow_fake_agent_spawn(monkeypatch, tmp_path):
    """Opt in by naming the executable this test made, never a PATH default."""
    def allow(path):
        fake = Path(path).resolve(strict=True)
        assert fake.is_relative_to(tmp_path.resolve()) and os.access(fake, os.X_OK), fake
        monkeypatch.setenv("PATH", f"{fake.parent}{os.pathsep}{os.environ.get('PATH', '')}")
        monkeypatch.setenv("HOLDSPEAK_AGENT_SPAWN", "on")
        return fake

    return allow


def pytest_sessionfinish(session, exitstatus):
    guard = getattr(session.config, "_holdspeak_process_guard", None)
    if guard is None:
        return
    # multiprocessing keeps its resource tracker alive until interpreter exit.
    # Finish that runtime-owned helper before looking for test-owned leaks;
    # a surviving worker is still a leak and must keep the guard red.
    from multiprocessing import active_children, resource_tracker

    if not active_children():
        resource_tracker._resource_tracker._stop()
    leaks = guard.finish(os.environ.get("TMUX_TMPDIR", ""))
    leaks += getattr(session.config, "_holdspeak_worker_leaks", [])
    if not leaks:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter:
            reporter.write_line("process guard: ps found no live run-owned child (claude, codex and tmux included)")
    if leaks:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter:
            reporter.write_sep("=", "test processes leaked (killed)", red=True)
            for leak in leaks:
                reporter.write_line(leak, red=True)
        if hasattr(session.config, "workeroutput"):
            session.config.workeroutput["holdspeak_process_leaks"] = leaks


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node, error):
    leaks = node.workeroutput.get("holdspeak_process_leaks", [])
    if leaks:
        node.config._holdspeak_worker_leaks = getattr(node.config, "_holdspeak_worker_leaks", []) + leaks


@pytest.fixture
def db_stamp_clock(monkeypatch):
    """Move store time explicitly, preserving each store's timestamp shape."""
    from datetime import datetime, timedelta, timezone
    from holdspeak.db import primitives, refinement_thoughts, meetings
    from holdspeak.services import refinement_thought_service

    class Clock:
        now = datetime.now(timezone.utc).replace(microsecond=0)

        def advance(self):
            self.now += timedelta(seconds=2)

        def iso(self):
            return self.now.isoformat()

        def z(self):
            return self.now.isoformat(timespec="seconds").replace("+00:00", "Z")

    clock = Clock()
    monkeypatch.setattr(primitives, "_now_iso", clock.z)
    monkeypatch.setattr(refinement_thoughts, "_now", clock.z)
    monkeypatch.setattr(refinement_thought_service, "_now", clock.z)
    monkeypatch.setattr(meetings, "utc_now_iso", clock.iso)
    return clock
