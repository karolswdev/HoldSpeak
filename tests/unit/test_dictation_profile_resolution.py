"""HS-84-02 — dictation runs on a profile.

`effective_dictation_llm` shares the ONE profile-adoption rule with meeting
intel (HS-84-01): a valid assigned ``openAICompatible`` RuntimeProfile shapes
the LLM leg AND selects the openai_compatible backend (assignment is the
user's explicit "run it there"); dangling/deleted/non-endpoint/lookup-failure
fall back to the configured backend + ``openai_compatible_*`` shape with a
named reason. Unset is byte-identical, locked here, not claimed. The setup
probe and setup status report the EFFECTIVE endpoint, not raw config fields.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from holdspeak.config import Config, DictationConfig, LLMRuntimeConfig
from holdspeak.db.models import ProfileRecord
from holdspeak.intel.providers import effective_dictation_llm, profile_key_env
from holdspeak.plugins.dictation.assembly import _try_build_runtime


def _profile(**overrides) -> ProfileRecord:
    fields = dict(
        id="p-43",
        name="LAN llama",
        kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1",
        model="Qwen3.5-9B-Q6_K",
    )
    fields.update(overrides)
    return ProfileRecord(**fields)


# ── the resolver ─────────────────────────────────────────────────────────


def test_unset_profile_is_the_legacy_shape_verbatim() -> None:
    runtime = LLMRuntimeConfig()
    eff = effective_dictation_llm(runtime, get_profile=lambda pid: pytest.fail("no lookup"))
    assert eff.model == "qwen3.5-8b-instruct"
    assert eff.base_url == "http://127.0.0.1:8000/v1"
    assert eff.api_key_env == "OPENAI_API_KEY"
    assert eff.profile_id is None and eff.reason is None


def test_valid_endpoint_profile_shapes_the_llm_leg(monkeypatch) -> None:
    monkeypatch.delenv(profile_key_env("p-43"), raising=False)
    runtime = LLMRuntimeConfig(profile_id="p-43")
    eff = effective_dictation_llm(runtime, get_profile=lambda pid: _profile())
    assert eff.base_url == "http://192.168.1.43:8080/v1"
    assert eff.model == "Qwen3.5-9B-Q6_K"
    assert eff.api_key_env == "OPENAI_API_KEY"  # no per-profile key ⇒ legacy env
    assert eff.profile_id == "p-43"


def test_dangling_profile_falls_back_with_a_named_reason() -> None:
    runtime = LLMRuntimeConfig(profile_id="gone")
    eff = effective_dictation_llm(runtime, get_profile=lambda pid: None)
    assert eff.base_url == "http://127.0.0.1:8000/v1"
    assert eff.profile_id is None
    assert "assigned profile missing: gone" in (eff.reason or "")


def test_ondevice_profile_runs_on_the_configured_backend() -> None:
    runtime = LLMRuntimeConfig(profile_id="p-dev")
    eff = effective_dictation_llm(
        runtime, get_profile=lambda pid: _profile(id="p-dev", kind="onDevice", base_url="")
    )
    assert eff.base_url == "http://127.0.0.1:8000/v1"
    assert "onDevice-kind" in (eff.reason or "")


# ── assembly honors the seam ─────────────────────────────────────────────


def _capture_factory(captured: dict):
    def factory(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(backend=kwargs["backend"])

    return factory


def test_assembly_unset_is_byte_identical() -> None:
    cfg = DictationConfig()
    cfg.runtime.backend = "mlx"
    captured: dict = {}
    runtime, status, _ = _try_build_runtime(cfg, _capture_factory(captured))
    assert status == "loaded" and runtime is not None
    assert captured["backend"] == "mlx"
    assert captured["openai_compatible_model"] == "qwen3.5-8b-instruct"
    assert captured["openai_compatible_base_url"] == "http://127.0.0.1:8000/v1"
    assert captured["openai_compatible_api_key_env"] == "OPENAI_API_KEY"


def test_assembly_adopted_profile_selects_the_endpoint_backend(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _profile()
    )
    cfg = DictationConfig()
    cfg.runtime.backend = "mlx"  # the assignment overrides the local backend
    cfg.runtime.profile_id = "p-43"
    captured: dict = {}
    _try_build_runtime(cfg, _capture_factory(captured))
    assert captured["backend"] == "openai_compatible"
    assert captured["openai_compatible_base_url"] == "http://192.168.1.43:8080/v1"
    assert captured["openai_compatible_model"] == "Qwen3.5-9B-Q6_K"


def test_assembly_dangling_profile_keeps_the_configured_backend(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: None
    )
    cfg = DictationConfig()
    cfg.runtime.backend = "mlx"
    cfg.runtime.profile_id = "gone"
    captured: dict = {}
    _try_build_runtime(cfg, _capture_factory(captured))
    assert captured["backend"] == "mlx"
    assert captured["openai_compatible_base_url"] == "http://127.0.0.1:8000/v1"


# ── the probe and status report the effective endpoint ──────────────────


def test_probe_runtime_tests_the_adopted_profile_endpoint(monkeypatch) -> None:
    from holdspeak.setup_runtime import probe_runtime

    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _profile()
    )
    cfg = DictationConfig()
    cfg.pipeline.enabled = True
    cfg.runtime.backend = "mlx"
    cfg.runtime.profile_id = "p-43"
    probed: dict = {}

    def _http_get(url, *, headers, timeout):
        probed["url"] = url
        return 200

    result = probe_runtime(cfg, http_get=_http_get)
    assert result["ok"] is True
    assert result["backend"] == "openai_compatible"
    assert probed["url"] == "http://192.168.1.43:8080/v1/models"


def test_setup_status_reports_the_effective_dictation_endpoint(monkeypatch) -> None:
    from holdspeak.setup_status import _trust_block

    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _profile()
    )
    cfg = Config()
    cfg.dictation.runtime.backend = "mlx"
    cfg.dictation.runtime.profile_id = "p-43"
    trust = _trust_block(cfg)
    assert "http://192.168.1.43:8080/v1" in trust["configured_endpoints"]

    # unset ⇒ a non-endpoint backend contributes no endpoint (byte-identical)
    cfg2 = Config()
    cfg2.dictation.runtime.backend = "mlx"
    assert "http://127.0.0.1:8000/v1" not in _trust_block(cfg2)["configured_endpoints"]


# ── config + settings carry the knob ─────────────────────────────────────


def test_config_round_trips_dictation_profile_id(tmp_path) -> None:
    path = tmp_path / "config.json"
    cfg = Config()
    cfg.dictation.runtime.profile_id = "p-43"
    cfg.save(path)
    assert Config.load(path).dictation.runtime.profile_id == "p-43"


def test_settings_route_round_trips_dictation_profile_id(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient

    import holdspeak.config as config_mod
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    monkeypatch.setattr(config_mod, "CONFIG_FILE", tmp_path / "config.json")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *a, **k: None,
            on_stop=lambda *a, **k: None,
            get_state=lambda: {"activity": {"state": "idle"}},
        ),
        host="127.0.0.1",
    )
    client = TestClient(server.app)

    before = client.get("/api/settings").json()
    assert before["dictation"]["runtime"]["profile_id"] is None, "default must be unset"

    resp = client.put(
        "/api/settings", json={"dictation": {"runtime": {"profile_id": "p-43"}}}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["settings"]["dictation"]["runtime"]["profile_id"] == "p-43"
    assert (
        client.get("/api/settings").json()["dictation"]["runtime"]["profile_id"]
        == "p-43"
    )

    # clearing writes None, not "" (whitespace normalizes away)
    resp = client.put(
        "/api/settings", json={"dictation": {"runtime": {"profile_id": "  "}}}
    )
    assert resp.status_code == 200, resp.text
    assert client.get("/api/settings").json()["dictation"]["runtime"]["profile_id"] is None
