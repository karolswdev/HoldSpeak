from __future__ import annotations

from types import SimpleNamespace

from holdspeak.inference_targets import target_from_profile
from holdspeak.intel.providers import profile_key_env
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.profile_key_store import ProfileKeyStore
from holdspeak.services.profile_service import ProfileService


OWNER = Principal(PrincipalKind.OWNER, "profile-key-test")


class _Profiles:
    def __init__(self, profile): self.profile = profile
    def get(self, _id): return self.profile


class _Db:
    def __init__(self, profile): self.profiles = _Profiles(profile)


def _profile():
    return SimpleNamespace(
        id="profile-a", name="Endpoint", kind="openAICompatible",
        base_url="https://endpoint.example/v1", node="", model="m",
        model_file="", requires_key=True, context_limit=16384,
    )


def test_stored_key_changes_readiness_and_probe_then_delete_suppresses_env(tmp_path, monkeypatch):
    profile = _profile()
    slot = profile_key_env(profile.id)
    store = ProfileKeyStore(tmp_path / "keys.json")
    monkeypatch.setattr("holdspeak.profile_key_store._default_profile_key_store", lambda: store)
    monkeypatch.setenv(slot, "inherited-sentinel")
    assert target_from_profile(profile).key_present is True

    store.set(slot, "stored-sentinel")
    assert target_from_profile(profile).key_present is True
    seen = {}
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models", lambda _url, api_key=None: seen.update(api_key=api_key) or {"ok": True, "models": ["m"]})
    result = ProfileService(_Db(profile)).probe_inference_target(OWNER, profile.id)
    assert result["reachable"] is True
    assert seen["api_key"] == "stored-sentinel"

    store.delete(slot)
    assert target_from_profile(profile).key_present is False
    ProfileService(_Db(profile)).probe_inference_target(OWNER, profile.id)
    assert seen["api_key"] is None
