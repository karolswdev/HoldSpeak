"""HS-84-01 — meeting intelligence runs on a profile.

`effective_intel_cloud` is the ONE resolution seam: a valid assigned
``openAICompatible`` RuntimeProfile shapes the cloud leg; anything else
(unset, dangling, deleted, non-endpoint kind, lookup unavailable) falls back
to the legacy ``intel_cloud_*`` config shape — with a named reason, never a
crash. Unset is byte-identical, locked here, not claimed. ``intel_provider``
local/auto/cloud semantics are untouched.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import holdspeak.intel as intel_module
from holdspeak.db.models import ProfileRecord
from holdspeak.intel.providers import (
    EffectiveEndpoint,
    build_configured_meeting_intel,
    effective_intel_cloud,
    profile_key_env,
    resolve_llm_capability,
)


def _meeting_cfg(**overrides):
    base = dict(
        intel_provider="cloud",
        intel_cloud_model="legacy-model",
        intel_cloud_api_key_env="LEGACY_KEY_ENV",
        intel_cloud_base_url="http://legacy.example:8000/v1",
        intel_cloud_reasoning_effort=None,
        intel_cloud_store=False,
        intel_realtime_model=None,
        intel_profile_id=None,
        intel_enabled=True,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


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


# ── the resolution matrix ────────────────────────────────────────────────


def test_unset_profile_is_the_legacy_shape_verbatim() -> None:
    eff = effective_intel_cloud(_meeting_cfg(), get_profile=lambda pid: pytest.fail("no lookup"))
    assert eff == EffectiveEndpoint(
        model="legacy-model",
        api_key_env="LEGACY_KEY_ENV",
        base_url="http://legacy.example:8000/v1",
    )
    assert eff.profile_id is None and eff.reason is None


def test_valid_endpoint_profile_shapes_the_cloud_leg(monkeypatch) -> None:
    monkeypatch.delenv(profile_key_env("p-43"), raising=False)
    eff = effective_intel_cloud(
        _meeting_cfg(intel_profile_id="p-43"), get_profile=lambda pid: _profile()
    )
    assert eff.base_url == "http://192.168.1.43:8080/v1"
    assert eff.model == "Qwen3.5-9B-Q6_K"
    # no per-profile key in the env ⇒ the legacy env is the fallback
    assert eff.api_key_env == "LEGACY_KEY_ENV"
    assert eff.profile_id == "p-43" and eff.profile_name == "LAN llama"
    assert eff.reason is None


def test_profile_key_env_wins_when_set(monkeypatch) -> None:
    monkeypatch.setenv(profile_key_env("p-43"), "sk-profile-secret")
    eff = effective_intel_cloud(
        _meeting_cfg(intel_profile_id="p-43"), get_profile=lambda pid: _profile()
    )
    assert eff.api_key_env == profile_key_env("p-43")


def test_profile_without_model_keeps_the_legacy_model() -> None:
    eff = effective_intel_cloud(
        _meeting_cfg(intel_profile_id="p-43"), get_profile=lambda pid: _profile(model="")
    )
    assert eff.model == "legacy-model"
    assert eff.base_url == "http://192.168.1.43:8080/v1"


def test_dangling_profile_falls_back_with_a_named_reason() -> None:
    eff = effective_intel_cloud(
        _meeting_cfg(intel_profile_id="gone"), get_profile=lambda pid: None
    )
    assert eff.base_url == "http://legacy.example:8000/v1"
    assert eff.profile_id is None
    assert "assigned profile missing: gone" in (eff.reason or "")


def test_deleted_profile_counts_as_missing() -> None:
    eff = effective_intel_cloud(
        _meeting_cfg(intel_profile_id="p-43"),
        get_profile=lambda pid: _profile(deleted=True),
    )
    assert eff.base_url == "http://legacy.example:8000/v1"
    assert "assigned profile missing" in (eff.reason or "")


def test_ondevice_profile_runs_on_the_hub_engine() -> None:
    eff = effective_intel_cloud(
        _meeting_cfg(intel_profile_id="p-dev"),
        get_profile=lambda pid: _profile(id="p-dev", kind="onDevice", base_url=""),
    )
    assert eff.base_url == "http://legacy.example:8000/v1"
    assert "onDevice-kind" in (eff.reason or "")


def test_lookup_failure_degrades_never_raises() -> None:
    def _boom(pid: str):
        raise RuntimeError("no db on this path")

    eff = effective_intel_cloud(_meeting_cfg(intel_profile_id="p-43"), get_profile=_boom)
    assert eff.base_url == "http://legacy.example:8000/v1"
    assert "profile lookup unavailable" in (eff.reason or "")


def test_cfg_without_the_field_at_all_is_legacy() -> None:
    cfg = _meeting_cfg()
    delattr(cfg, "intel_profile_id")
    eff = effective_intel_cloud(cfg, get_profile=lambda pid: pytest.fail("no lookup"))
    assert eff.base_url == "http://legacy.example:8000/v1" and eff.reason is None


# ── the constructors honor the seam ──────────────────────────────────────


def test_build_configured_unset_is_byte_identical(monkeypatch) -> None:
    cfg = SimpleNamespace(meeting=_meeting_cfg())
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls, path=None: cfg))

    intel = build_configured_meeting_intel()
    assert intel.provider == "cloud"
    assert intel.cloud_model == "legacy-model"
    assert intel.cloud_api_key_env == "LEGACY_KEY_ENV"
    assert intel.cloud_base_url == "http://legacy.example:8000/v1"


def test_build_configured_adopts_the_assigned_profile(monkeypatch) -> None:
    cfg = SimpleNamespace(meeting=_meeting_cfg(intel_profile_id="p-43"))
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls, path=None: cfg))
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _profile()
    )

    intel = build_configured_meeting_intel()
    assert intel.cloud_base_url == "http://192.168.1.43:8080/v1"
    assert intel.cloud_model == "Qwen3.5-9B-Q6_K"


def test_llm_capability_judges_the_effective_endpoint(monkeypatch) -> None:
    captured: dict = {}

    def _capture(provider, **kwargs):
        captured.update(kwargs, provider=provider)
        return "cloud", None

    monkeypatch.setattr(intel_module, "resolve_intel_provider", _capture)
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _profile()
    )
    ok = resolve_llm_capability(_meeting_cfg(intel_profile_id="p-43"))
    # the capability probe must see the PROFILE's endpoint, not the legacy one
    assert ok is True
    assert captured["cloud_base_url"] == "http://192.168.1.43:8080/v1"
    assert captured["cloud_model"] == "Qwen3.5-9B-Q6_K"


def test_llm_capability_knows_the_mesh(monkeypatch) -> None:
    """The HS-85-05 walk find: a mesh-adopted endpoint has no base_url, so the
    endpoint resolver says no — and every LLM plugin silently skipped while the
    reroute still reported executed=True. The capability must say yes for a
    named node; liveness is judged at run time with a named refusal."""
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record",
        lambda pid: _profile(kind="meshNode", base_url=None, node="walk-edge"),
    )
    monkeypatch.setattr(
        intel_module, "resolve_intel_provider",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not consult the endpoint resolver")),
    )
    assert resolve_llm_capability(_meeting_cfg(intel_profile_id="p-43")) is True


# ── config + settings carry the knob ─────────────────────────────────────


def test_config_round_trips_intel_profile_id(tmp_path) -> None:
    from holdspeak.config import Config

    path = tmp_path / "config.json"
    cfg = Config()
    cfg.meeting.intel_profile_id = "p-43"
    cfg.save(path)
    assert Config.load(path).meeting.intel_profile_id == "p-43"


def test_settings_route_round_trips_intel_profile_id(tmp_path, monkeypatch) -> None:
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
    assert before["meeting"]["intel_profile_id"] is None, "default must be unset"

    resp = client.put("/api/settings", json={"meeting": {"intel_profile_id": "p-43"}})
    assert resp.status_code == 200, resp.text
    assert resp.json()["settings"]["meeting"]["intel_profile_id"] == "p-43"
    assert client.get("/api/settings").json()["meeting"]["intel_profile_id"] == "p-43"

    # clearing writes None, not "" (whitespace normalizes away)
    resp = client.put("/api/settings", json={"meeting": {"intel_profile_id": "  "}})
    assert resp.status_code == 200, resp.text
    assert client.get("/api/settings").json()["meeting"]["intel_profile_id"] is None
