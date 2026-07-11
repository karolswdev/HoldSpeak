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
    return (pages._HOLDSPEAK_DIR / "static" / "_built" / "index.html").exists()


def test_shell_carries_the_trust_chip_and_panel() -> None:
    resp = _client().get("/settings")
    assert resp.status_code == 200
    if not _built():
        return  # the Unit Tests CI job runs without the bundle
    assert '<div id="root"></div>' in resp.text
    source = (_REPO / "web/src/components/AppShell.tsx").read_text()
    assert "Privacy & Trust" in source and "trustOpen" in source
    assert "Current scope" in source and "Review privacy settings" in source


def test_trust_view_module_maps_postures() -> None:
    """The shell reads trust posture from the hub and maps the egress scope."""
    src = (_REPO / "web/src/components/AppShell.tsx").read_text()
    for marker in (
        "/api/setup/status",
        'transcript_egress === "none"',
        "enabledDestinations",
        "authority_basis",
        "revoke_action",
        "last_receipt",
    ):
        assert marker in src
