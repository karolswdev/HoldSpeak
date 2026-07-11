from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_presence_hud_is_accessible_and_uses_the_one_bus() -> None:
    page = (ROOT / "web/src/pages/PresencePage.tsx").read_text()
    bus = (ROOT / "web/src/runtime/RuntimeBus.tsx").read_text()
    css = (ROOT / "web/src/styles/react-app.css").read_text()
    assert 'role="status"' in page and 'aria-live="polite"' in page
    assert 'useRuntimeFrame<Activity>("runtime_activity")' in page
    assert "new WebSocket" not in page
    assert "new WebSocket" in bus and "15_000" in bus and "reconnecting" in bus
    assert "prefers-reduced-motion" in css


def test_presence_route_serves_the_react_shell() -> None:
    from unittest.mock import MagicMock
    from fastapi.testclient import TestClient
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    client = TestClient(MeetingWebServer(WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}))).app)
    response = client.get("/presence")
    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text or "npm run build" in response.text
