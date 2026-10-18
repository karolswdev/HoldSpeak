"""HS-92-03 Desk-first arrival locks."""
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

_REPO = Path(__file__).resolve().parents[2]


def _client() -> TestClient:
    return TestClient(MeetingWebServer(WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}))).app)


def test_welcome_route_serves_the_one_react_shell() -> None:
    response = _client().get("/welcome")
    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text or "npm run build" in response.text


def test_runtime_discovery_routes_are_real() -> None:
    client = _client()
    options = client.get("/api/setup/runtime-options")
    assert options.status_code == 200
    assert {"mlx", "gguf", "context_presets", "platform"} <= set(options.json())
    invalid = client.post("/api/setup/discover-models", json={"base_url": "not-a-server"})
    assert invalid.status_code == 422
    assert invalid.json()["models"] == []


def test_discover_models_uses_the_typed_key_before_the_env_fallback(monkeypatch) -> None:
    """PHILO-15 02: the Concierge's Key field reaches Check. #1248: an empty
    key falls back to the environment key only for https://api.openai.com;
    a LAN address gets no key."""
    client = _client()
    seen: list = []

    def discover(base_url, *, api_key=None, **_kwargs):
        seen.append(api_key)
        return {"ok": True, "models": ["qwen3.8-27b"], "detail": "Found 1 model."}

    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models", discover)
    url = "http://192.168.1.43:8080/v1"

    typed = client.post("/api/setup/discover-models", json={"base_url": url, "api_key": " local "})
    assert typed.status_code == 200
    assert "local" not in typed.text  # the key is never echoed
    blank = client.post("/api/setup/discover-models", json={"base_url": url, "api_key": "  "})
    assert blank.status_code == 200
    absent = client.post("/api/setup/discover-models", json={"base_url": url})
    assert absent.status_code == 200
    openai = client.post("/api/setup/discover-models", json={"base_url": "https://api.openai.com/v1"})
    assert openai.status_code == 200
    assert seen == ["local", None, None, "env-key"]
