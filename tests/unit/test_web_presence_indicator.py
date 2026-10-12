from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_presence_route_serves_the_react_shell() -> None:
    from unittest.mock import MagicMock
    from fastapi.testclient import TestClient
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    client = TestClient(MeetingWebServer(WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}))).app)
    response = client.get("/presence")
    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text or "npm run build" in response.text
