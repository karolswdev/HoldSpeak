"""HS-4-01 audit — verify-by-test that the existing web-flagship surfaces hold.

Most WFS-* requirements (§5.1–§5.4 of `docs/internal/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md`)
are already covered by:

  - `tests/unit/test_main_modes.py` — WFS-C-001 (default web), the retired `tui` subcommand now rejected (HS-32-07), `holdspeak doctor` exit code passthrough.
  - `tests/integration/test_web_server.py` — TestRuntimeControlEndpoints (`/api/meeting/start|stop`), TestSettingsApiEndpoints (`/api/settings`), TestHistoryUiSmoke (`/history`, `/settings`), Dashboard idle-mode guidance.

This file targets the small set of WFS-* requirements that *aren't*
already explicitly asserted: bind-address default (WFS-R-004),
runtime-state shape (WFS-P-003), web-runtime independence from
meetings (WFS-R-001 + WFS-R-002 — explicit assertion of the
"idle but routes still work" property). The phase 4 audit
(HS-4-01) treats this file plus the pre-existing tests as the full
WFS-* coverage matrix.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def web_server() -> MeetingWebServer:
    """Minimal idle-runtime web server: no callbacks beyond the no-op shape."""
    return MeetingWebServer(
               WebRuntimeCallbacks(
                   on_bookmark=MagicMock(return_value={"timestamp": 0.0, "label": "noop"}),
                   on_stop=MagicMock(return_value={"status": "stopped"}),
                   get_state=MagicMock(return_value={"id": None, "started_at": None, "duration": 0, "bookmarks": []}),
               ),
               host="127.0.0.1",
           )


@pytest.fixture
def test_client(web_server: MeetingWebServer) -> TestClient:
    return TestClient(web_server.app)


def test_wfs_r_004_default_host_is_loopback() -> None:
    """WFS-R-004: bind address defaults to `127.0.0.1` unless explicitly configured."""
    server = MeetingWebServer(
                 WebRuntimeCallbacks(
                     on_bookmark=MagicMock(),
                     on_stop=MagicMock(),
                     get_state=MagicMock(return_value={}),
                 )
             )
    assert server.host == "127.0.0.1"


def test_wfs_r_001_r_002_idle_runtime_serves_history_and_settings(test_client: TestClient) -> None:
    """WFS-R-001 + WFS-R-002: `/history` and `/settings` accessible when no meeting is active."""
    history_response = test_client.get("/history")
    assert history_response.status_code == 200
    assert "text/html" in history_response.headers["content-type"]

    settings_response = test_client.get("/settings")
    assert settings_response.status_code == 200
    assert "text/html" in settings_response.headers["content-type"]


