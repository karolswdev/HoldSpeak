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
    if _built("setup", "index.html"):
        assert "setupApp" in resp.text  # the page's Alpine factory
    else:
        assert "HoldSpeak Setup" in resp.text


def test_dashboard_has_the_first_run_guard() -> None:
    resp = _client().get("/")
    assert resp.status_code == 200
    if _built("index.html"):
        # The inline guard redirects a first-run / hard-blocked user to /setup.
        assert "/api/setup/status" in resp.text
        assert '"/setup"' in resp.text


# ── the CLI launch nudge (WebRuntime._print_setup_nudge) ──────────────


def _nudge_output(monkeypatch, status: dict) -> str:
    from holdspeak.web_runtime import WebRuntime

    rt = WebRuntime.__new__(WebRuntime)
    rt.runtime_url = "http://127.0.0.1:9999"
    monkeypatch.setattr("holdspeak.setup_status.build_setup_status", lambda **_: status)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rt._print_setup_nudge()
    return buf.getvalue()


def test_cli_nudge_points_first_run_user_at_setup(monkeypatch) -> None:
    out = _nudge_output(
        monkeypatch,
        {
            "first_run": True,
            "overall": "needs_attention",
            "primary_action": {"label": "Enable microphone access"},
            "sections": [
                {"status": "pass"},
                {"status": "warn"},
                {"status": "fail"},
            ],
        },
    )
    assert "/setup" in out
    assert "2 things need attention" in out
    assert "Enable microphone access" in out


def test_cli_nudge_is_silent_for_a_healthy_returning_user(monkeypatch) -> None:
    out = _nudge_output(
        monkeypatch,
        {"first_run": False, "overall": "ready", "primary_action": None, "sections": [{"status": "pass"}]},
    )
    assert out.strip() == ""


def test_cli_nudge_never_raises(monkeypatch) -> None:
    from holdspeak.web_runtime import WebRuntime

    rt = WebRuntime.__new__(WebRuntime)
    rt.runtime_url = "http://127.0.0.1:9999"

    def _boom(**_):
        raise RuntimeError("status unavailable")

    monkeypatch.setattr("holdspeak.setup_status.build_setup_status", _boom)
    # Must not raise — a nudge can never block boot.
    rt._print_setup_nudge()
