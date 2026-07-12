"""HS-92-03 Desk-first arrival locks."""
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


def test_welcome_is_the_same_one_step_first_value_surface_as_the_desk() -> None:
    page = _page()
    desk = (_REPO / "web/src/desk/components/EmptyDesk.tsx").read_text()
    assert "FirstWords" in page and "FirstWords" in desk
    assert "STEPS" not in page and "Model" not in page
    assert 'navigate("/", { replace: true })' in page


def test_basic_value_precedes_optional_runs_on_setup() -> None:
    first_words = (_REPO / "web/src/desk/components/FirstWords.tsx").read_text()
    assert "Dictate one sentence" in first_words
    basic_value = first_words.index("Dictation is ready on this machine.")
    optional_runs = first_words.index("Configure rewrite destination")
    assert basic_value < optional_runs
    assert 'to="/profiles"' in first_words


def test_first_dictation_retains_editable_text_and_all_recovery_doors() -> None:
    page = (_REPO / "web/src/desk/components/FirstWords.tsx").read_text()
    recovery = (_REPO / "web/src/lib/dictationRecovery.ts").read_text()
    tracker = (_REPO / "web/src/desk/firstValue.ts").read_text()
    for marker in (
        "Hold to retry",
        "Copy",
        "Keep as Note",
        "Setup",
        "Continue later",
    ):
        assert marker in page
    assert "DICTATION_FAILURES" in page and "dictationFailure" in page
    for failure in (
        "permission_denied",
        "missing_model",
        "rejected_token",
        "unreachable_hub",
        "delivery_conflict",
    ):
        assert failure in recovery
    assert "<TextArea" in page and "onChange" in page
    assert "FirstValueTracker" in page
    assert "/api/setup/first-value/start" in tracker
    assert "/api/setup/onboarding" in page


def test_runtime_discovery_routes_are_real() -> None:
    client = _client()
    options = client.get("/api/setup/runtime-options")
    assert options.status_code == 200
    assert {"mlx", "gguf", "context_presets", "platform"} <= set(options.json())
    invalid = client.post("/api/setup/discover-models", json={"base_url": "not-a-server"})
    assert invalid.status_code == 422
    assert invalid.json()["models"] == []
