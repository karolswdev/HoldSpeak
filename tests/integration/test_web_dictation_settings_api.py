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
from holdspeak.config import Config
from holdspeak.plugins.dictation import runtime_counters
from holdspeak.web_server import MeetingWebServer


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
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={}),
        on_settings_applied=on_settings_applied,
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
                "pipeline": {"enabled": True, "max_total_latency_ms": 800},
                "runtime": {
                    "backend": "mlx",
                    "mlx_model": "~/Models/mlx/Qwen3-8B-MLX-4bit",
                    "llama_cpp_model_path": "~/Models/gguf/Qwen2.5-3B-Instruct-Q4_K_M.gguf",
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
        assert out["pipeline"]["max_total_latency_ms"] == 800
        assert out["runtime"]["backend"] == "mlx"
        assert out["runtime"]["warm_on_start"] is True
        on_settings_applied.assert_called_once()

        persisted = Config.load(path=settings_path)
        assert persisted.dictation.pipeline.enabled is True
        assert persisted.dictation.pipeline.max_total_latency_ms == 800
        assert persisted.dictation.runtime.backend == "mlx"
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


# ── Page surface ──────────────────────────────────────────────────────


def test_dictation_page_includes_runtime_section() -> None:
    server = MeetingWebServer(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={}),
    )
    client = TestClient(server.app)
    response = client.get("/dictation")
    assert response.status_code == 200
    body = response.text
    assert 'data-section="runtime"' in body
    assert "Dictation Runtime" in body
    assert "cold-start cap" in body
