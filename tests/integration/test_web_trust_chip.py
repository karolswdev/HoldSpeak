"""HS-42-05: the ambient trust chip + Trust & Privacy panel ship in the shell."""
from __future__ import annotations

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


def _built() -> bool:
    return (pages._HOLDSPEAK_DIR / "static" / "_built" / "settings" / "index.html").exists()


def test_shell_carries_the_trust_chip_and_panel() -> None:
    resp = _client().get("/settings")
    assert resp.status_code == 200
    if not _built():
        return  # the Unit Tests CI job runs without the bundle
    html = resp.text
    # The ambient chip (opens the panel) + the panel dialog + its honest default.
    assert "data-trust-open" in html
    assert 'id="trust-panel"' in html
    assert "Local only" in html  # the server-rendered honest default
    assert "data-trust-rows" in html


def test_trust_view_module_maps_postures() -> None:
    """Guard the source-of-truth posture rules in trust-view.js (the JS the
    shell imports). A Node harness asserts the live mappings; here we lock the
    rule strings so a regression in the mapping is visible in review."""
    src = (_REPO / "web" / "src" / "scripts" / "trust-view.js").read_text()
    for marker in (
        "Needs attention",        # off-loopback + no auth
        "Writes need approval",   # actuators enabled
        "Configured endpoint",    # transcript egress != none
        "Local only",             # default
        "actuators_enabled",
        "transcript_egress",
        "auth_token_set",
    ):
        assert marker in src, f"missing trust-view rule: {marker}"
