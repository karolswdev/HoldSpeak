"""HS-4-04: integration tests for dictation runtime config via `/api/settings`.

Covers GET enrichment with `_runtime_status`, PUT validation and
round-trip on every dictation field, the `apply_runtime_config` hook
firing via `on_settings_applied`, the read-only nature of
`_runtime_status`, and validation rejection of bad payloads.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.config import Config, DeviceConfig
from holdspeak.plugins.dictation import runtime_counters
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


@pytest.fixture(autouse=True)
def reset_counters_before_each() -> None:
    runtime_counters.reset_counters()


@pytest.fixture
def on_settings_applied() -> MagicMock:
    return MagicMock()


@pytest.fixture
def test_client(on_settings_applied: MagicMock) -> TestClient:
    server = MeetingWebServer(
                 WebRuntimeCallbacks(
                     on_bookmark=MagicMock(),
                     on_stop=MagicMock(),
                     get_state=MagicMock(return_value={}),
                     on_settings_applied=on_settings_applied,
                 )
             )
    return TestClient(server.app)


# ── GET enrichment ────────────────────────────────────────────────────


class TestSettingsGetIncludesRuntimeStatus:
    def test_get_returns_dictation_block(self, test_client: TestClient, settings_path: Path) -> None:
        response = test_client.get("/api/settings")
        assert response.status_code == 200
        body = response.json()
        assert "dictation" in body
        assert "pipeline" in body["dictation"]
        assert "runtime" in body["dictation"]

    def test_get_includes_runtime_status(self, test_client: TestClient, settings_path: Path) -> None:
        response = test_client.get("/api/settings")
        body = response.json()
        assert "_runtime_status" in body
        rs = body["_runtime_status"]
        assert "counters" in rs and "session" in rs
        assert set(rs["counters"]) == {
            "model_loads",
            "classify_calls",
            "classify_failures",
            "constrained_retries",
        }
        assert rs["session"] == {"llm_disabled_for_session": False, "disabled_reason": None}

    def test_get_surfaces_session_disabled_state(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        runtime_counters._set_session_disabled("cold-start exceeded cap")
        response = test_client.get("/api/settings")
        rs = response.json()["_runtime_status"]
        assert rs["session"]["llm_disabled_for_session"] is True
        assert "cold-start" in rs["session"]["disabled_reason"]


# ── PUT round-trip ────────────────────────────────────────────────────


class TestSettingsPutPersistsDictation:
    def test_put_persists_pipeline_and_runtime_fields(
        self,
        test_client: TestClient,
        settings_path: Path,
        on_settings_applied: MagicMock,
    ) -> None:
        payload = {
            "dictation": {
                "pipeline": {
                    "enabled": True,
                    "stages": ["intent-router", "project-rewriter", "kb-enricher"],
                    "max_total_latency_ms": 800,
                    "target_profile_override": "codex_cli",
                },
                "runtime": {
                    "backend": "mlx",
                    "mlx_model": "~/Models/mlx/Qwen3.5-8B-MLX-4bit",
                    "llama_cpp_model_path": "~/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf",
                    "openai_compatible_model": "qwen-local",
                    "openai_compatible_base_url": "http://127.0.0.1:8000/v1",
                    "openai_compatible_api_key_env": "LOCAL_LLM_KEY",
                    "openai_compatible_timeout_seconds": 4.5,
                    "warm_on_start": True,
                },
            }
        }
        response = test_client.put("/api/settings", json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        out = data["settings"]["dictation"]
        assert out["pipeline"]["enabled"] is True
        assert out["pipeline"]["stages"] == ["intent-router", "project-rewriter", "kb-enricher"]
        assert out["pipeline"]["max_total_latency_ms"] == 800
        assert out["pipeline"]["target_profile_override"] == "codex_cli"
        assert out["runtime"]["backend"] == "mlx"
        assert out["runtime"]["openai_compatible_model"] == "qwen-local"
        assert out["runtime"]["openai_compatible_base_url"] == "http://127.0.0.1:8000/v1"
        assert out["runtime"]["openai_compatible_api_key_env"] == "LOCAL_LLM_KEY"
        assert out["runtime"]["openai_compatible_timeout_seconds"] == 4.5
        assert out["runtime"]["warm_on_start"] is True
        on_settings_applied.assert_called_once()

        persisted = Config.load(path=settings_path)
        assert persisted.dictation.pipeline.enabled is True
        assert persisted.dictation.pipeline.stages == ["intent-router", "project-rewriter", "kb-enricher"]
        assert persisted.dictation.pipeline.max_total_latency_ms == 800
        assert persisted.dictation.pipeline.target_profile_override == "codex_cli"
        assert persisted.dictation.runtime.backend == "mlx"
        assert persisted.dictation.runtime.openai_compatible_model == "qwen-local"
        assert persisted.dictation.runtime.openai_compatible_base_url == "http://127.0.0.1:8000/v1"
        assert persisted.dictation.runtime.openai_compatible_api_key_env == "LOCAL_LLM_KEY"
        assert persisted.dictation.runtime.openai_compatible_timeout_seconds == 4.5
        assert persisted.dictation.runtime.warm_on_start is True

    def test_put_omitting_dictation_preserves_existing(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        # Seed a non-default value first.
        seed = test_client.put(
            "/api/settings",
            json={"dictation": {"pipeline": {"enabled": True}}},
        )
        assert seed.status_code == 200

        # PUT with only a meeting field — dictation must be preserved.
        response = test_client.put(
            "/api/settings",
            json={"meeting": {"similarity_threshold": 0.55}},
        )
        assert response.status_code == 200
        out = response.json()["settings"]["dictation"]
        assert out["pipeline"]["enabled"] is True

    def test_partial_put_enables_pipeline_and_preserves_runtime(
        self,
        test_client: TestClient,
        settings_path: Path,
        on_settings_applied: MagicMock,
    ) -> None:
        cfg = Config()
        cfg.dictation.pipeline.enabled = False
        cfg.dictation.runtime.backend = "llama_cpp"
        cfg.save(path=settings_path)

        response = test_client.put(
            "/api/settings",
            json={"dictation": {"pipeline": {"enabled": True}}},
        )

        assert response.status_code == 200, response.text
        out = response.json()["settings"]["dictation"]
        assert out["pipeline"]["enabled"] is True
        assert out["runtime"]["backend"] == "llama_cpp"
        persisted = Config.load(path=settings_path)
        assert persisted.dictation.pipeline.enabled is True
        assert persisted.dictation.runtime.backend == "llama_cpp"
        on_settings_applied.assert_called_once()

    def test_partial_put_preserves_device_config(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        cfg = Config()
        cfg.device = DeviceConfig(psk="dogfood-psk")
        cfg.save(path=settings_path)

        response = test_client.put(
            "/api/settings",
            json={"dictation": {"pipeline": {"enabled": True}}},
        )

        assert response.status_code == 200, response.text
        body = response.json()["settings"]
        assert "psk" not in body["device"]
        assert body["_secrets"]["device_psk"] == {"configured": True}
        persisted = Config.load(path=settings_path)
        assert persisted.device.psk == "dogfood-psk"

    def test_put_drops_runtime_status_if_echoed_back(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        get_resp = test_client.get("/api/settings")
        echoed = get_resp.json()
        # Mutate one dictation field; echo `_runtime_status` back as a
        # naive client would after re-saving the entire settings object.
        echoed["dictation"]["pipeline"]["enabled"] = True
        response = test_client.put("/api/settings", json=echoed)
        assert response.status_code == 200, response.text
        # `_runtime_status` must not leak into the persisted config.
        persisted = Config.load(path=settings_path)
        assert not hasattr(persisted, "_runtime_status")


# ── PUT validation ────────────────────────────────────────────────────


class TestSettingsPutValidatesDictation:
    def test_invalid_backend_400(self, test_client: TestClient, settings_path: Path) -> None:
        response = test_client.put(
            "/api/settings", json={"dictation": {"runtime": {"backend": "tensorflow"}}}
        )
        assert response.status_code == 400
        assert "backend" in response.json()["error"]

    def test_zero_latency_400(self, test_client: TestClient, settings_path: Path) -> None:
        response = test_client.put(
            "/api/settings", json={"dictation": {"pipeline": {"max_total_latency_ms": 0}}}
        )
        assert response.status_code == 400

    def test_non_integer_latency_400(self, test_client: TestClient, settings_path: Path) -> None:
        response = test_client.put(
            "/api/settings", json={"dictation": {"pipeline": {"max_total_latency_ms": "fast"}}}
        )
        assert response.status_code == 400

    def test_unknown_stage_id_400(self, test_client: TestClient, settings_path: Path) -> None:
        # `DictationConfigError` from `DictationPipelineConfig.__post_init__`
        # surfaces as 400 with the canonical error message.
        response = test_client.put(
            "/api/settings",
            json={"dictation": {"pipeline": {"stages": ["intent-router", "bogus-stage"]}}},
        )
        assert response.status_code == 400
        assert "bogus-stage" in response.json()["error"]

    def test_unknown_target_profile_override_400(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        response = test_client.put(
            "/api/settings",
            json={"dictation": {"pipeline": {"target_profile_override": "spreadsheet"}}},
        )

        assert response.status_code == 400
        assert "target_profile_override" in response.json()["error"]


# ── HS-40-01: the four Phase-39 depth knobs ───────────────────────────


class TestSettingsPipelineDepthKnobs:
    """The cockpit (HS-40-03) wires controls to these — they must survive a
    PUT→GET round-trip and reject out-of-range input with a clean 4xx."""

    KNOB_KEYS = (
        "rewrite_passes",
        "corrections_enabled",
        "target_detect_llm_enabled",
        "target_detect_llm_below",
    )

    def test_get_includes_all_four_knobs(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        pipeline = test_client.get("/api/settings").json()["dictation"]["pipeline"]
        for key in self.KNOB_KEYS:
            assert key in pipeline, f"GET /api/settings missing dictation.pipeline.{key}"
        # Defaults (off-by-default invariant).
        assert pipeline["rewrite_passes"] == 1
        assert pipeline["corrections_enabled"] is False
        assert pipeline["target_detect_llm_enabled"] is False
        assert pipeline["target_detect_llm_below"] == 0.8

    def test_put_round_trips_all_four_knobs(
        self,
        test_client: TestClient,
        settings_path: Path,
        on_settings_applied: MagicMock,
    ) -> None:
        payload = {
            "dictation": {
                "pipeline": {
                    "rewrite_passes": 3,
                    "corrections_enabled": True,
                    "target_detect_llm_enabled": True,
                    "target_detect_llm_below": 0.55,
                }
            }
        }
        response = test_client.put("/api/settings", json=payload)
        assert response.status_code == 200, response.text
        out = response.json()["settings"]["dictation"]["pipeline"]
        assert out["rewrite_passes"] == 3
        assert out["corrections_enabled"] is True
        assert out["target_detect_llm_enabled"] is True
        assert out["target_detect_llm_below"] == 0.55
        on_settings_applied.assert_called_once()

        # A fresh GET reflects the new values…
        got = test_client.get("/api/settings").json()["dictation"]["pipeline"]
        assert got["rewrite_passes"] == 3
        assert got["corrections_enabled"] is True
        assert got["target_detect_llm_enabled"] is True
        assert got["target_detect_llm_below"] == 0.55
        # …and they survive a reload from disk (true persistence).
        persisted = Config.load(path=settings_path)
        assert persisted.dictation.pipeline.rewrite_passes == 3
        assert persisted.dictation.pipeline.corrections_enabled is True
        assert persisted.dictation.pipeline.target_detect_llm_enabled is True
        assert persisted.dictation.pipeline.target_detect_llm_below == 0.55

    def test_partial_put_preserves_unsent_knobs(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        # Seed all four to non-defaults.
        seed = test_client.put(
            "/api/settings",
            json={
                "dictation": {
                    "pipeline": {
                        "rewrite_passes": 4,
                        "corrections_enabled": True,
                        "target_detect_llm_enabled": True,
                        "target_detect_llm_below": 0.42,
                    }
                }
            },
        )
        assert seed.status_code == 200

        # PUT only one knob — the other three must be preserved, not reset.
        response = test_client.put(
            "/api/settings",
            json={"dictation": {"pipeline": {"rewrite_passes": 2}}},
        )
        assert response.status_code == 200, response.text
        out = response.json()["settings"]["dictation"]["pipeline"]
        assert out["rewrite_passes"] == 2
        assert out["corrections_enabled"] is True
        assert out["target_detect_llm_enabled"] is True
        assert out["target_detect_llm_below"] == 0.42

    @pytest.mark.parametrize("bad_passes", [0, 6, 99])
    def test_rewrite_passes_out_of_range_400(
        self, test_client: TestClient, settings_path: Path, bad_passes: int
    ) -> None:
        response = test_client.put(
            "/api/settings",
            json={"dictation": {"pipeline": {"rewrite_passes": bad_passes}}},
        )
        assert response.status_code == 400
        assert "rewrite_passes" in response.json()["error"]

    def test_rewrite_passes_non_integer_400(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        response = test_client.put(
            "/api/settings",
            json={"dictation": {"pipeline": {"rewrite_passes": "three"}}},
        )
        assert response.status_code == 400
        assert "rewrite_passes must be an integer" in response.json()["error"]

    @pytest.mark.parametrize("bad_below", [-0.1, 1.5, 2.0])
    def test_target_detect_below_out_of_range_400(
        self, test_client: TestClient, settings_path: Path, bad_below: float
    ) -> None:
        response = test_client.put(
            "/api/settings",
            json={"dictation": {"pipeline": {"target_detect_llm_below": bad_below}}},
        )
        assert response.status_code == 400
        assert "target_detect_llm_below" in response.json()["error"]

    def test_target_detect_below_non_numeric_400(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        response = test_client.put(
            "/api/settings",
            json={"dictation": {"pipeline": {"target_detect_llm_below": "high"}}},
        )
        assert response.status_code == 400
        assert "target_detect_llm_below must be a number" in response.json()["error"]

    def test_out_of_range_put_does_not_persist(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        # A rejected PUT must leave the on-disk value untouched.
        before = Config.load(path=settings_path).dictation.pipeline.rewrite_passes
        rejected = test_client.put(
            "/api/settings",
            json={"dictation": {"pipeline": {"rewrite_passes": 9}}},
        )
        assert rejected.status_code == 400
        after = Config.load(path=settings_path).dictation.pipeline.rewrite_passes
        assert after == before


# ── Page surface ──────────────────────────────────────────────────────


def test_dictation_page_includes_runtime_section() -> None:
    server = MeetingWebServer(
                 WebRuntimeCallbacks(
                     on_bookmark=MagicMock(),
                     on_stop=MagicMock(),
                     get_state=MagicMock(return_value={}),
                 )
             )
    client = TestClient(server.app)
    response = client.get("/dictation")
    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text
    source = (Path(__file__).resolve().parents[2] / "web/src/pages/cores/DictationCore.tsx").read_text()
    assert '["runtime", "Runtime"]' in source
    assert "Dictation runtime" in source and 'label="Runs on"' in source


def test_dictation_page_includes_copilot_depth_controls() -> None:
    """HS-40-03: the cockpit exposes a control for every Phase-39 depth knob."""
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        )
    )
    client = TestClient(server.app)
    assert '<div id="root"></div>' in client.get("/dictation").text
    settings = (Path(__file__).resolve().parents[2] / "web/src/pages/cores/SettingsCore.tsx").read_text()
    # The recursive typed settings editor exposes every safe knob returned by
    # the hub, including new depth knobs, without a duplicate hardcoded form.
    assert "SettingsFields" in settings and "typeof item" in settings
    assert "dictation" in settings


class TestVoiceMacrosSettingsApi:
    """HS-52-02: the voice command macros section of `/api/settings`."""

    def test_get_includes_macros_off_by_default(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        body = test_client.get("/api/settings").json()
        macros = body["dictation"]["macros"]
        assert macros == {"enabled": False, "items": []}

    def test_put_persists_macros_of_each_kind(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        payload = {
            "dictation": {
                "macros": {
                    "enabled": True,
                    "items": [
                        {"keyword": "docs", "action": {"kind": "open_url", "payload": "https://docs.example"}},
                        {"keyword": "terminal", "action": {"kind": "launch_app", "payload": "Terminal"}},
                        {"keyword": "ship it", "action": {"kind": "shell", "payload": "git push origin HEAD"}},
                        {"keyword": "standup", "action": {"kind": "type_text", "payload": "## Standup"}},
                    ],
                }
            }
        }
        response = test_client.put("/api/settings", json=payload)
        assert response.status_code == 200, response.text
        out = response.json()["settings"]["dictation"]["macros"]
        assert out["enabled"] is True
        assert [m["keyword"] for m in out["items"]] == ["docs", "terminal", "ship it", "standup"]
        assert {m["action"]["kind"] for m in out["items"]} == {
            "open_url",
            "launch_app",
            "shell",
            "type_text",
        }

        persisted = Config.load(settings_path)
        assert persisted.dictation.macros.enabled is True
        assert persisted.dictation.macros.items[2].action.payload == "git push origin HEAD"

    def test_put_rejects_unknown_action_kind(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        payload = {
            "dictation": {
                "macros": {
                    "enabled": True,
                    "items": [{"keyword": "x", "action": {"kind": "telepathy", "payload": "y"}}],
                }
            }
        }
        response = test_client.put("/api/settings", json=payload)
        assert response.status_code == 400
        assert "voice macro" in response.json()["error"].lower()

    def test_put_rejects_empty_keyword(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        payload = {
            "dictation": {
                "macros": {
                    "enabled": True,
                    "items": [{"keyword": "  ", "action": {"kind": "shell", "payload": "ls"}}],
                }
            }
        }
        response = test_client.put("/api/settings", json=payload)
        assert response.status_code == 400

    def test_put_omitting_macros_preserves_them(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        # Seed a macro, then PUT an unrelated change; the macro must survive.
        seed = {
            "dictation": {
                "macros": {
                    "enabled": True,
                    "items": [{"keyword": "docs", "action": {"kind": "open_url", "payload": "https://x"}}],
                }
            }
        }
        assert test_client.put("/api/settings", json=seed).status_code == 200
        # A PUT that touches only the UI theme, not macros.
        assert test_client.put("/api/settings", json={"ui": {"theme": "light"}}).status_code == 200
        persisted = Config.load(settings_path)
        assert persisted.dictation.macros.enabled is True
        assert persisted.dictation.macros.items[0].keyword == "docs"


class TestSettingsCompanionConnectors:
    """HSM-14 / EQ-21-03: the iPad desk's Webhook + GitHub connectors are
    configured from the hub's settings, same posture as the Slack field."""

    def test_put_round_trips_companion_webhook_and_github(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        secret = test_client.put(
            "/api/settings/secrets/companion_webhook_url",
            json={"value": "https://hooks.example.com/abc"},
        )
        assert secret.status_code == 200, secret.text
        response = test_client.put(
            "/api/settings",
            json={"meeting": {"companion_github_repo": "karolswdev/HoldSpeak"}},
        )
        assert response.status_code == 200, response.text
        out = response.json()["settings"]["meeting"]
        assert "companion_webhook_url" not in out
        assert out["companion_github_repo"] == "karolswdev/HoldSpeak"
        assert response.json()["settings"]["_secrets"]["companion_webhook_url"] == {
            "configured": True,
            "destination": "hooks.example.com",
        }

        persisted = Config.load(path=settings_path)
        assert persisted.meeting.companion_webhook_url == "https://hooks.example.com/abc"
        assert persisted.meeting.companion_github_repo == "karolswdev/HoldSpeak"

        # The GET path surfaces only state + destination, never the credential URL.
        got_body = test_client.get("/api/settings").json()
        got = got_body["meeting"]
        assert "companion_webhook_url" not in got
        assert got["companion_github_repo"] == "karolswdev/HoldSpeak"
        assert got_body["_secrets"]["companion_webhook_url"]["destination"] == "hooks.example.com"

    def test_put_rejects_non_https_companion_webhook(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        response = test_client.put(
            "/api/settings/secrets/companion_webhook_url",
            json={"value": "http://hooks.example.com/x"},
        )
        assert response.status_code == 400
        assert "https" in response.json()["error"]

    def test_put_rejects_malformed_companion_github_repo(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        response = test_client.put(
            "/api/settings",
            json={"meeting": {"companion_github_repo": "not-a-slug"}},
        )
        assert response.status_code == 400
        assert "companion_github_repo" in response.json()["error"]

    def test_put_omitting_connectors_preserves_them(
        self, test_client: TestClient, settings_path: Path
    ) -> None:
        assert test_client.put(
            "/api/settings/secrets/companion_webhook_url",
            json={"value": "https://hooks.example.com/keep"},
        ).status_code == 200
        assert test_client.put(
            "/api/settings", json={"meeting": {"companion_github_repo": "owner/repo"}}
        ).status_code == 200
        assert test_client.put("/api/settings", json={"ui": {"theme": "light"}}).status_code == 200
        persisted = Config.load(settings_path)
        assert persisted.meeting.companion_webhook_url == "https://hooks.example.com/keep"
        assert persisted.meeting.companion_github_repo == "owner/repo"
