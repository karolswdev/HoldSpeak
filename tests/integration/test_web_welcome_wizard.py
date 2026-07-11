"""Phase-91 React arrival and runtime-discovery locks."""
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

_REPO = Path(__file__).resolve().parents[2]


def _client() -> TestClient:
    return TestClient(MeetingWebServer(WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}))).app)


def _page() -> str:
    return (_REPO / "web/src/pages/WelcomePage.tsx").read_text()


def test_welcome_route_serves_the_one_react_shell() -> None:
    response = _client().get("/welcome")
    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text or "npm run build" in response.text


def test_wizard_is_a_focus_safe_six_step_funnel() -> None:
    page = _page()
    for step in ("Welcome", "Permissions", "Model", "First dictation", "Presence", "Done"):
        assert f'"{step}"' in page
    assert "heading.current?.focus()" in page
    assert "Step {step + 1} of {STEPS.length}" in page
    assert "Back" in page and "Continue" in page


def test_model_step_discovers_saves_and_tests_real_runtimes() -> None:
    page = _page()
    for backend in ("basic", "mlx", "llama_cpp", "openai_compatible"):
        assert f'"{backend}"' in page
    for endpoint in ("/api/setup/runtime-options", "/api/setup/discover-models", "/api/profiles", "/api/settings", "/api/setup/runtime-test"):
        assert endpoint in page
    assert "requires_key" in page and "context_limit" in page


def test_first_dictation_and_presence_use_live_hub_state() -> None:
    page = _page()
    assert "useRuntimeFrame" in page
    assert "It worked" in page
    assert "hotkey" in page
    assert "Desktop Presence" in page and "setPresence" in page


def test_runtime_discovery_routes_are_real() -> None:
    client = _client()
    options = client.get("/api/setup/runtime-options")
    assert options.status_code == 200
    assert {"mlx", "gguf", "context_presets", "platform"} <= set(options.json())
    invalid = client.post("/api/setup/discover-models", json={"base_url": "not-a-server"})
    assert invalid.status_code == 422
    assert invalid.json()["models"] == []
