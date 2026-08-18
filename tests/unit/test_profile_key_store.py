from __future__ import annotations

import os
import stat

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.intel.providers import profile_key_env
from holdspeak.profile_key_store import ProfileKeyStore, ProfileKeyStoreError, resolve_profile_key
from holdspeak.services.errors import NotFound, ServiceError, ValidationError
from holdspeak.services.profile_key_service import ProfileKeyService


def test_set_replace_fresh_read_delete_and_env_tombstone(tmp_path, monkeypatch):
    path = tmp_path / "profile-keys.json"
    slot = "HOLDSPEAK_PROFILE_ALPHA_KEY"
    monkeypatch.setenv(slot, "inherited-key")
    first = ProfileKeyStore(path)
    assert resolve_profile_key(slot, store=first) == "inherited-key"

    first.set(slot, "stored-key")
    assert ProfileKeyStore(path).state(slot) == ("set", "stored-key")
    assert resolve_profile_key(slot, store=ProfileKeyStore(path)) == "stored-key"
    first.set(slot, "replacement-key")
    assert resolve_profile_key(slot, store=ProfileKeyStore(path)) == "replacement-key"

    first.delete(slot)
    assert ProfileKeyStore(path).state(slot) == ("deleted", None)
    assert resolve_profile_key(slot, store=ProfileKeyStore(path)) is None


def test_store_writes_private_atomic_file(tmp_path):
    path = tmp_path / "profile-keys.json"
    store = ProfileKeyStore(path)
    store.set("HOLDSPEAK_PROFILE_ALPHA_KEY", "stored-key")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert not list(tmp_path.glob(".profile-keys-*"))


@pytest.mark.parametrize("payload", ["not-json", '{"version": 9, "entries": {}}', '{"version": 1, "entries": []}'])
def test_malformed_or_unknown_schema_fails_closed(tmp_path, payload):
    path = tmp_path / "profile-keys.json"
    path.write_text(payload)
    path.chmod(0o600)
    with pytest.raises(ProfileKeyStoreError, match="Profile key store is unavailable") as error:
        ProfileKeyStore(path).state("HOLDSPEAK_PROFILE_ALPHA_KEY")
    assert "stored-key" not in str(error.value)


def test_symlink_and_permissive_store_fail_closed(tmp_path):
    target = tmp_path / "real.json"
    target.write_text('{"version":1,"entries":{}}')
    target.chmod(0o600)
    link = tmp_path / "profile-keys.json"
    link.symlink_to(target)
    with pytest.raises(ProfileKeyStoreError, match="Profile key store is unavailable"):
        ProfileKeyStore(link).state("HOLDSPEAK_PROFILE_ALPHA_KEY")


def test_permissive_or_symlinked_parent_fails_before_lock_or_temp(tmp_path):
    parent = tmp_path / "custody"
    parent.mkdir(mode=0o755)
    store = ProfileKeyStore(parent / "keys.json")
    with pytest.raises(ProfileKeyStoreError, match="Profile key store is unavailable"):
        store.set("HOLDSPEAK_PROFILE_ALPHA_KEY", "stored-key")
    assert not list(parent.iterdir())

    target = tmp_path / "real-custody"
    target.mkdir(mode=0o700)
    link = tmp_path / "linked-custody"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ProfileKeyStoreError, match="Profile key store is unavailable"):
        ProfileKeyStore(link / "keys.json").state("HOLDSPEAK_PROFILE_ALPHA_KEY")
    assert not list(target.iterdir())

    link.unlink()
    link.write_text('{"version":1,"entries":{}}')
    link.chmod(0o644)
    with pytest.raises(ProfileKeyStoreError, match="Profile key store is unavailable"):
        ProfileKeyStore(link).state("HOLDSPEAK_PROFILE_ALPHA_KEY")


def test_store_never_mutates_process_environment(tmp_path, monkeypatch):
    slot = "HOLDSPEAK_PROFILE_ALPHA_KEY"
    monkeypatch.delenv(slot, raising=False)
    ProfileKeyStore(tmp_path / "profile-keys.json").set(slot, "stored-key")
    assert slot not in os.environ


def test_absent_custody_read_does_not_create_parent_and_falls_back_to_env(tmp_path, monkeypatch):
    path = tmp_path / "absent-custody" / "profile-keys.json"
    slot = "HOLDSPEAK_PROFILE_ALPHA_KEY"
    monkeypatch.setenv(slot, "inherited-key")
    store = ProfileKeyStore(path)
    assert store.state(slot) == ("missing", None)
    assert resolve_profile_key(slot, store=store) == "inherited-key"
    assert not path.parent.exists()
    assert not path.exists()


class _Profiles:
    def __init__(self, record):
        self.record = record

    def get(self, _profile_id):
        return self.record


class _Db:
    def __init__(self, record):
        self.profiles = _Profiles(record)


class _Profile:
    id = "profile-a"
    kind = "openAICompatible"
    requires_key = True


def test_owner_key_service_is_write_only_and_validates(tmp_path):
    store = ProfileKeyStore(tmp_path / "keys.json")
    service = ProfileKeyService(_Db(_Profile()), store=store)
    owner = Principal(PrincipalKind.OWNER, "owner")
    assert service.set(owner, "profile-a", {"value": " stored-key "}) == {
        "success": True, "secret": {"required": True, "present": True},
    }
    assert resolve_profile_key(profile_key_env("profile-a"), store=store) == "stored-key"
    with pytest.raises(ValidationError):
        service.set(owner, "profile-a", {"value": "stored-key", "extra": True})
    with pytest.raises(ValidationError):
        service.set(owner, "profile-a", {"value": "   "})
    with pytest.raises(ServiceError):
        service.set(Principal(PrincipalKind.AGENT, "agent"), "profile-a", {"value": "stored-key"})
    assert service.delete(owner, "profile-a") == {
        "success": True, "secret": {"required": True, "present": False},
    }


def test_owner_key_service_refuses_unknown_or_non_endpoint(tmp_path):
    owner = Principal(PrincipalKind.OWNER, "owner")
    missing = ProfileKeyService(_Db(None), store=ProfileKeyStore(tmp_path / "keys.json"))
    with pytest.raises(NotFound):
        missing.set(owner, "missing", {"value": "stored-key"})
    record = _Profile()
    record.kind = "meshNode"
    service = ProfileKeyService(_Db(record), store=ProfileKeyStore(tmp_path / "keys2.json"))
    with pytest.raises(ValidationError):
        service.set(owner, "profile-a", {"value": "stored-key"})
