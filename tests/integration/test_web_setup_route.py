"""HS-42-03: the welcome/setup route, the / first-run guard, and the CLI nudge."""
from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import holdspeak.web.routes.pages as pages
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

_REPO = Path(__file__).resolve().parents[2]


def _client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        )
    )
    return TestClient(server.app)


def _built(*parts: str) -> bool:
    return (pages._HOLDSPEAK_DIR / "static" / "_built" / Path(*parts)).exists()


def test_setup_route_serves_the_setup_page() -> None:
    resp = _client().get("/setup")
    assert resp.status_code == 200
    if _built("index.html"):
        assert '<div id="root"></div>' in resp.text
        assert "/_built/assets/" in resp.text
    else:
        assert "npm run build" in resp.text


def test_dashboard_owns_first_value_without_redirecting() -> None:
    resp = _client().get("/")
    assert resp.status_code == 200
    desk = (_REPO / "web" / "src" / "desk" / "DeskApp.tsx").read_text()
    assert "setup?.arrival_required" in desk
    assert "arrivalRequired" in desk
    assert 'navigate("/welcome"' not in desk
    assert 'navigate("/setup"' not in desk


# ── the CLI launch nudge (WebRuntime._print_setup_nudge) ──────────────


def _nudge_output(monkeypatch, status: dict) -> str:
    from holdspeak.config import Config
    from holdspeak.web_runtime import WebRuntime

    rt = WebRuntime.__new__(WebRuntime)
    rt.runtime_url = "http://127.0.0.1:9999"
    # HS-202-02: the nudge now tokens its URLs, so it reads the config the
    # way every real runtime has one.
    config = Config()
    config.meeting.web_auth_token = "NUDGETOKEN"
    rt.config = config
    monkeypatch.setattr("holdspeak.setup_status.build_setup_status", lambda **_: status)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rt._print_setup_nudge()
    return buf.getvalue()


def test_cli_nudge_points_first_run_user_at_the_desk(monkeypatch) -> None:
    out = _nudge_output(
        monkeypatch,
        {"first_run": True, "arrival_required": True, "overall": "needs_attention", "primary_action": None, "sections": []},
    )
    assert "open http://127.0.0.1:9999/" in out
    assert "/welcome" not in out
    assert "Welcome" in out


def test_cli_nudge_points_blocked_returning_user_at_setup(monkeypatch) -> None:
    out = _nudge_output(
        monkeypatch,
        {
            "first_run": False,
            "overall": "blocked",
            "primary_action": {"label": "Enable microphone access"},
            "sections": [{"status": "pass"}, {"status": "fail"}],
        },
    )
    assert "/setup" in out
    assert "1 thing needs attention" in out
    assert "Enable microphone access" in out
    assert "Enable microphone access" in out


def test_cli_nudge_is_silent_for_a_healthy_returning_user(monkeypatch) -> None:
    out = _nudge_output(
        monkeypatch,
        {"first_run": False, "overall": "ready", "primary_action": None, "sections": [{"status": "pass"}]},
    )
    assert out.strip() == ""


def test_cli_nudge_never_raises(monkeypatch) -> None:
    from holdspeak.config import Config
    from holdspeak.web_runtime import WebRuntime

    rt = WebRuntime.__new__(WebRuntime)
    rt.runtime_url = "http://127.0.0.1:9999"
    rt.config = Config()

    def _boom(**_):
        raise RuntimeError("status unavailable")

    monkeypatch.setattr("holdspeak.setup_status.build_setup_status", _boom)
    # Must not raise — a nudge can never block boot.
    rt._print_setup_nudge()


# ── HS-202-02 job 2: every printed URL carries the tab-scoped token ────
#
# The surface inventory (04-sober-eye.md, rank 1) found the first-run nudge
# and the setup nudge printing bare URLs: a user who opens one lands on
# `principal_right_required`, because the runtime needs `?token=` even on
# loopback. Every OTHER printed URL in the same block already goes through
# `authenticated_browser_url` (web_runtime.py:567-577).


def _nudge_output_with_token(monkeypatch, status: dict, token: str = "TESTTOKEN123") -> str:
    from holdspeak.config import Config
    from holdspeak.web_runtime import WebRuntime

    rt = WebRuntime.__new__(WebRuntime)
    rt.runtime_url = "http://127.0.0.1:9999"
    config = Config()
    config.meeting.web_auth_token = token
    rt.config = config
    monkeypatch.setattr("holdspeak.setup_status.build_setup_status", lambda **_: status)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rt._print_setup_nudge()
    return buf.getvalue()


def test_first_run_nudge_url_carries_the_token(monkeypatch) -> None:
    out = _nudge_output_with_token(
        monkeypatch,
        {"first_run": True, "arrival_required": True, "overall": "needs_attention", "primary_action": None, "sections": []},
    )
    assert "token=TESTTOKEN123" in out, out
    assert "9999/ " not in out and not out.rstrip().endswith("9999/"), out


def test_blocked_setup_nudge_url_carries_the_token(monkeypatch) -> None:
    out = _nudge_output_with_token(
        monkeypatch,
        {
            "first_run": False,
            "overall": "blocked",
            "primary_action": {"label": "Enable microphone access"},
            "sections": [{"status": "fail"}],
        },
    )
    assert "/setup?token=TESTTOKEN123" in out, out


def test_optional_setup_nudge_url_carries_the_token(monkeypatch) -> None:
    out = _nudge_output_with_token(
        monkeypatch,
        {
            "first_run": False,
            "overall": "needs_attention",
            "primary_action": None,
            "sections": [{"status": "warn"}],
        },
    )
    assert "/setup?token=TESTTOKEN123" in out, out
