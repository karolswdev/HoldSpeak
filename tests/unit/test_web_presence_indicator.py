from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_runtime_presence_card_is_accessible_and_reduced_motion_safe() -> None:
    page_source = (ROOT / "web/src/pages/index.astro").read_text()

    assert 'class="presence-card"' in page_source
    assert 'role="status"' in page_source
    assert 'aria-live="polite"' in page_source
    assert "@media (prefers-reduced-motion: reduce)" in page_source
    assert ".presence-ring.is-live { animation: none; }" in page_source


def test_dashboard_handles_runtime_activity_messages() -> None:
    script_source = (ROOT / "web/src/scripts/dashboard-app.js").read_text()

    assert "applyActivity(activity)" in script_source
    assert 'if (type === "runtime_activity")' in script_source
    assert "if (data && typeof data === \"object\") this.applyActivity(data)" in script_source
    assert "activityWindowLabel()" in script_source


# ── HS-41-03: the /presence HUD page ──────────────────────────────────


def test_presence_hud_page_is_standalone_and_token_styled() -> None:
    page_source = (ROOT / "web/src/pages/presence.astro").read_text()
    # Standalone HUD: no AppLayout chrome, transparent body, the card.
    assert "<AppLayout" not in page_source
    assert "import AppLayout" not in page_source
    assert "background: transparent" in page_source
    assert 'id="presence-card"' in page_source
    assert 'role="status"' in page_source
    assert 'aria-live="polite"' in page_source
    assert "@media (prefers-reduced-motion: reduce)" in page_source


def test_presence_hud_driver_consumes_runtime_activity() -> None:
    script_source = (ROOT / "web/src/scripts/presence-app.js").read_text()
    assert 'msg.type === "runtime_activity"' in script_source
    assert "applyActivity(msg.data)" in script_source
    assert "/api/state" in script_source          # seeds from current state
    assert "/ws" in script_source                  # live websocket
    assert "setTimeout(connect" in script_source   # auto-reconnect


def test_presence_route_serves_the_hud() -> None:
    from unittest.mock import MagicMock

    from fastapi.testclient import TestClient

    import holdspeak.web.routes.pages as pages
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        )
    )
    client = TestClient(server.app)
    resp = client.get("/presence")
    assert resp.status_code == 200

    # The route is build-agnostic: when the web bundle is built it serves the
    # Signal presence card; when it isn't (e.g. the Unit Tests CI job, which runs
    # against source without the gitignored `_built/` bundle) it returns a 200
    # fallback that still identifies the presence HUD. Assert the right one for
    # the current state so the test is green in both.
    built = (
        pages._HOLDSPEAK_DIR / "static" / "_built" / "presence" / "index.html"
    ).exists()
    if built:
        assert 'id="presence-card"' in resp.text
    else:
        assert "HoldSpeak Presence" in resp.text
