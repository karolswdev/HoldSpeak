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
