from __future__ import annotations

import pytest

from holdspeak.people.keys import NativeKeyStore, PeopleKeyError


def test_native_key_store_refuses_unknown_or_file_backends() -> None:
    class FileBackend:
        pass

    with pytest.raises(PeopleKeyError, match="not_native"):
        NativeKeyStore(backend=FileBackend())


def test_native_key_store_accepts_only_allowlisted_backend_and_round_trips() -> None:
    class Keyring:
        values: dict[tuple[str, str], str] = {}

        def get_password(self, service: str, key_id: str) -> str | None:
            return self.values.get((service, key_id))

        def set_password(self, service: str, key_id: str, value: str) -> None:
            self.values[(service, key_id)] = value

        def delete_password(self, service: str, key_id: str) -> None:
            self.values.pop((service, key_id), None)

    Keyring.__module__ = "keyring.backends.macOS"
    store = NativeKeyStore(backend=Keyring())
    key = b"a" * 32
    store.put("people-key-v1:test", key)
    assert store.get("people-key-v1:test") == key
    store.delete("people-key-v1:test")
    with pytest.raises(PeopleKeyError, match="missing"):
        store.get("people-key-v1:test")


def test_a_home_with_no_keychain_never_asks_the_keychain(tmp_path, monkeypatch):
    """A rig's scratch HOME has no keychain: macOS would pop "A keychain cannot
    be found" on the owner's screen, so the stores refuse before asking."""
    import sys

    from keyring.backends import macOS

    from holdspeak.services.channel_email import EmailKeyError, NativeEmailKeyStore
    from holdspeak.services.channel_slack import NativeSlackKeyStore, SlackKeyError

    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setenv("HOME", str(tmp_path))

    def asked(*_args, **_kwargs):
        raise AssertionError("the Keychain was asked")

    for name in ("get_password", "set_password", "delete_password"):
        monkeypatch.setattr(macOS.Keyring, name, asked)
    monkeypatch.setattr("keyring.get_keyring", lambda: macOS.Keyring())

    people = NativeKeyStore()  # building a store asks nothing; only a read or write would
    for call in (lambda: people.get("k"), lambda: people.put("k", b"x" * 32), lambda: people.delete("k")):
        with pytest.raises(PeopleKeyError, match="people_key_store_unavailable"):
            call()
    for store, error in ((NativeEmailKeyStore(), EmailKeyError), (NativeSlackKeyStore(), SlackKeyError)):
        with pytest.raises(error, match="key_store_unavailable"):
            store.get("ref")
        with pytest.raises(error, match="key_store_unavailable"):
            store.put("ref", "secret")
