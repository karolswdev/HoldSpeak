# PARKED: unused intent HTTP endpoints; their declared MCP operations remain.
from test_web_server import *

@pytest.mark.integration
class TestIntentRoutingControlEndpoints:
    """Tests for MIR control-plane endpoints."""

    def test_get_intent_controls_returns_safe_default_without_callback(self, test_client):
        response = test_client.get("/api/intents/control")
        assert response.status_code == 200
        payload = response.json()
        assert payload["enabled"] is False
        assert payload["profile"] == "balanced"
        assert payload["available_profiles"] == []
        assert payload["supported_intents"] == []

    def test_intent_profile_and_preview_require_callbacks(self, test_client):
        profile_response = test_client.put("/api/intents/profile", json={"profile": "architect"})
        assert profile_response.status_code == 501
        preview_response = test_client.post("/api/intents/preview", json={"profile": "architect"})
        assert preview_response.status_code == 501

    def test_intent_controls_round_trip_with_callbacks(self, mock_callbacks):
        controls = {
            "enabled": True,
            "profile": "balanced",
            "available_profiles": ["balanced", "architect"],
            "supported_intents": ["architecture", "delivery"],
            "override_intents": [],
            "threshold": 0.6,
            "last_preview": None,
        }

        def _get_controls() -> dict[str, object]:
            return deepcopy(controls)

        def _set_profile(profile: str) -> dict[str, object]:
            controls["profile"] = str(profile).strip().lower() or "balanced"
            return _get_controls()

        def _set_override(intents: list[str] | None) -> dict[str, object]:
            controls["override_intents"] = [str(intent).strip().lower() for intent in (intents or []) if str(intent).strip()]
            return _get_controls()

        def _preview_route(**kwargs) -> dict[str, object]:
            _ = kwargs
            route = {
                "profile": controls["profile"],
                "active_intents": list(controls["override_intents"]) or ["architecture"],
                "plugin_chain": ["requirements_extractor", "mermaid_architecture"],
                "intent_scores": {"architecture": 0.84},
                "threshold": 0.6,
                "hysteresis_applied": False,
                "override_intents": list(controls["override_intents"]),
            }
            controls["last_preview"] = route
            return route

        server = MeetingWebServer(
                     WebRuntimeCallbacks(
                         on_bookmark=mock_callbacks["on_bookmark"],
                         on_stop=mock_callbacks["on_stop"],
                         get_state=mock_callbacks["get_state"],
                         on_get_intent_controls=_get_controls,
                         on_set_intent_profile=_set_profile,
                         on_set_intent_override=_set_override,
                         on_route_preview=_preview_route,
                     ),
                     host="127.0.0.1",
                 )
        client = TestClient(server.app)

        initial = client.get("/api/intents/control")
        assert initial.status_code == 200
        assert initial.json()["profile"] == "balanced"

        profile_update = client.put("/api/intents/profile", json={"profile": "architect"})
        assert profile_update.status_code == 200
        assert profile_update.json()["controls"]["profile"] == "architect"

        preview = client.post("/api/intents/preview", json={"profile": "architect"})
        assert preview.status_code == 200
        route = preview.json()["route"]
        assert route["profile"] == "architect"
        assert route["active_intents"] == ["architecture"]
        assert "mermaid_architecture" in route["plugin_chain"]
