"""HS-84-04 — the honest doctor + one egress derivation.

Doctor names the RuntimeProfile each pipeline resolves to; dangling
assignments and missing per-profile keys are visible WARNs with the exact
env var named; the egress badge has ONE constructor (`endpoint_egress`) so
routes, cadence, and audit can't drift shape; the run badge reports the
endpoint the default engine ACTUALLY used (the effective shape), never the
raw legacy field.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from holdspeak.commands import doctor
from holdspeak.db.models import ProfileRecord
from holdspeak.intel.providers import endpoint_egress, profile_key_env


def _profile(**overrides) -> ProfileRecord:
    fields = dict(
        id="p-43",
        name="LAN box",
        kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1",
        model="Qwen3.5-9B-Q6_K",
        requires_key=False,
    )
    fields.update(overrides)
    return ProfileRecord(**fields)


def _config(
    *,
    intel_profile_id=None,
    dictation_profile_id=None,
    intel_enabled=True,
    pipeline_enabled=True,
    provider="cloud",
) -> SimpleNamespace:
    return SimpleNamespace(
        meeting=SimpleNamespace(
            intel_enabled=intel_enabled,
            intel_provider=provider,
            intel_cloud_model="legacy-model",
            intel_cloud_api_key_env="LEGACY_KEY_ENV",
            intel_cloud_base_url="http://legacy.example:8000/v1",
            intel_profile_id=intel_profile_id,
        ),
        dictation=SimpleNamespace(
            pipeline=SimpleNamespace(enabled=pipeline_enabled),
            runtime=SimpleNamespace(
                backend="openai_compatible",
                mlx_model="~/Models/mlx/x",
                llama_cpp_model_path="~/Models/gguf/x.gguf",
                openai_compatible_model="legacy-dict-model",
                openai_compatible_base_url="http://127.0.0.1:8000/v1",
                openai_compatible_api_key_env="OPENAI_API_KEY",
                profile_id=dictation_profile_id,
            ),
        ),
    )


# ── the one egress constructor ───────────────────────────────────────────


def test_endpoint_egress_shapes() -> None:
    assert endpoint_egress(cloud=False) == {"scope": "local"}
    assert endpoint_egress(cloud=False, label="Local only") == {
        "scope": "local",
        "label": "Local only",
    }
    assert endpoint_egress(cloud=True, base_url="http://192.168.1.43:8080/v1") == {
        "scope": "cloud",
        "host": "192.168.1.43",
    }
    # a cloud badge with no URL is the default OpenAI endpoint, never blank
    assert endpoint_egress(cloud=True, base_url=None)["host"] == "api.openai.com"


def test_the_scattered_egress_sites_use_the_one_constructor() -> None:
    from holdspeak.cadence.audit import export_audit
    from holdspeak.web.routes.cadence import _LOCAL_EGRESS

    assert _LOCAL_EGRESS == endpoint_egress(cloud=False, label="Local only")

    class _Loops:
        def list_loops(self, **kwargs):
            return []

        def list_nudges(self, **kwargs):
            return []

        def list_policies(self, **kwargs):
            return []

    snapshot = export_audit(SimpleNamespace(cadence=_Loops()))
    assert snapshot["egress"] == endpoint_egress(
        cloud=False, label="Local audit — nothing leaves this machine"
    )


def test_run_egress_default_cloud_reports_the_effective_endpoint(monkeypatch) -> None:
    # HS-84-01 made the default engine adopt the assigned intel profile; the
    # badge must report THAT endpoint, not the raw legacy config field.
    from holdspeak.web.routes.primitives.ask import _run_egress

    cfg = SimpleNamespace(meeting=_config(intel_profile_id="p-43").meeting)
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls, path=None: cfg))
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _profile()
    )

    egress, model = _run_egress(
        ctx=None, prof=None, intel=SimpleNamespace(active_provider="cloud")
    )
    assert egress == {"scope": "cloud", "host": "192.168.1.43"}
    assert model == "Qwen3.5-9B-Q6_K"


# ── doctor: the Runtime profiles check ───────────────────────────────────


def test_runtime_profiles_pass_names_both_pipelines(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _profile()
    )
    monkeypatch.delenv(profile_key_env("p-43"), raising=False)
    check = doctor._check_runtime_profiles(
        _config(intel_profile_id="p-43", dictation_profile_id="p-43")
    )
    assert check.status == "PASS"
    assert "meeting intel: profile 'LAN box' (192.168.1.43)" in check.detail
    assert "dictation: profile 'LAN box' (192.168.1.43)" in check.detail


def test_runtime_profiles_unset_reports_hub_default() -> None:
    check = doctor._check_runtime_profiles(_config())
    assert check.status == "PASS"
    assert "meeting intel: hub default" in check.detail
    assert "dictation: hub default" in check.detail


def test_runtime_profiles_dangling_is_a_visible_warn(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: None
    )
    check = doctor._check_runtime_profiles(_config(intel_profile_id="gone"))
    assert check.status == "WARN"
    assert "meeting intel: assigned profile missing: gone" in check.detail
    assert "Re-pick" in (check.fix or "")


def test_runtime_profiles_requires_key_without_key_names_the_env(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record",
        lambda pid: _profile(requires_key=True),
    )
    monkeypatch.delenv(profile_key_env("p-43"), raising=False)
    monkeypatch.delenv("LEGACY_KEY_ENV", raising=False)
    check = doctor._check_runtime_profiles(_config(intel_profile_id="p-43"))
    assert check.status == "WARN"
    assert "requires a key" in check.detail
    assert profile_key_env("p-43") in (check.fix or "")


def test_runtime_profiles_requires_key_with_key_passes(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record",
        lambda pid: _profile(requires_key=True),
    )
    monkeypatch.setenv(profile_key_env("p-43"), "sk-set")
    check = doctor._check_runtime_profiles(_config(intel_profile_id="p-43"))
    assert check.status == "PASS"


def test_runtime_profiles_nothing_enabled_is_a_quiet_pass() -> None:
    check = doctor._check_runtime_profiles(
        _config(intel_enabled=False, pipeline_enabled=False)
    )
    assert check.status == "PASS"
    assert "no pipeline enabled" in check.detail


# ── doctor: the per-pipeline checks name the profile ─────────────────────


def test_intel_egress_warn_names_the_adopted_profile(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _profile()
    )
    check = doctor._check_meeting_intel_egress(_config(intel_profile_id="p-43"))
    assert check.status == "WARN"  # cloud egress stays loud, as ever
    assert "Runs on profile 'LAN box' (192.168.1.43)" in check.detail


def test_intel_egress_unset_detail_is_unchanged() -> None:
    check = doctor._check_meeting_intel_egress(_config())
    assert check.status == "WARN"
    assert check.detail.startswith("provider=`cloud`: Cloud — transcripts are sent")
    assert "profile" not in check.detail


def test_dictation_runtime_adopted_profile_reports_it(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _profile()
    )
    check = doctor._check_dictation_runtime(_config(dictation_profile_id="p-43"))
    assert check.status == "PASS"
    assert "runs on profile 'LAN box'" in check.detail
    assert "http://192.168.1.43:8080/v1" in check.detail


def test_dictation_runtime_dangling_profile_warns_with_reason(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: None
    )
    check = doctor._check_dictation_runtime(_config(dictation_profile_id="gone"))
    assert check.status == "WARN"
    assert "assigned profile missing: gone" in check.detail
    assert "Re-pick a profile" in (check.fix or "")
