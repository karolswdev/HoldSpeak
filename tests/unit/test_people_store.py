from __future__ import annotations

import os

import pytest

from holdspeak.people.keys import MemoryKeyStore
from holdspeak.people.store import EncryptedPeopleStore, PeopleReadiness, PeopleStoreError


def _store(tmp_path):
    return EncryptedPeopleStore(tmp_path / "private" / "people.v1.sqlite3", MemoryKeyStore())


def test_sidecar_encrypts_sensitive_payload_before_sqlite_and_round_trips(tmp_path) -> None:
    store = _store(tmp_path)
    assert store.readiness() == PeopleReadiness.UNCONFIGURED
    assert store.initialize() == PeopleReadiness.READY
    relationship = store.create("relationship", {"display_name": "SENTINEL NAME", "role": "SENTINEL ROLE"})
    request = store.create("request", {"relationship_id": relationship["id"], "body": "SENTINEL REQUEST"})

    assert store.get(request["id"], "request")["body"] == "SENTINEL REQUEST"
    raw = store.path.read_bytes()
    for value in (b"SENTINEL NAME", b"SENTINEL ROLE", b"SENTINEL REQUEST"):
        assert value not in raw
    assert store.list(relationship_id=relationship["id"])[0]["id"] == request["id"]


def test_missing_key_and_unsafe_permissions_fail_closed(tmp_path) -> None:
    store = _store(tmp_path)
    store.initialize()
    store.key_store.values.clear()
    assert store.readiness() == PeopleReadiness.KEY_UNAVAILABLE
    with pytest.raises(PeopleStoreError) as caught:
        store.create("relationship", {"display_name": "never persisted"})
    assert caught.value.readiness == PeopleReadiness.KEY_UNAVAILABLE
    assert str(caught.value) == "people_store_key_unavailable"

    secure = _store(tmp_path / "other")
    secure.initialize()
    os.chmod(secure.path, 0o644)
    assert secure.readiness() == PeopleReadiness.UNSAFE_PERMISSIONS


def test_sidecar_and_sqlite_journals_are_private_from_creation(tmp_path) -> None:
    store = _store(tmp_path)
    store.initialize()
    store.create("relationship", {"display_name": "SENTINEL"})
    for candidate in (store.path, store.path.with_name(store.path.name + "-wal"), store.path.with_name(store.path.name + "-shm")):
        if candidate.exists():
            assert candidate.stat().st_mode & 0o077 == 0


def test_commitment_list_is_encrypted_authority_and_archive_changes_lifecycle(tmp_path) -> None:
    store = _store(tmp_path)
    store.initialize()
    closed = store.create("commitment", {"body": "old", "lifecycle": "done"})
    opened = store.create("commitment", {"body": "SENTINEL OPEN", "lifecycle": "open"})
    assert [item["id"] for item in store.open_commitments()] == [opened["id"]]
    assert store.archive(opened["id"])["lifecycle"] == "archived"
    assert store.open_commitments() == []
    assert store.get(closed["id"])["body"] == "old"


def test_accepting_request_is_atomic_and_idempotently_returns_one_commitment(tmp_path) -> None:
    store = _store(tmp_path)
    store.initialize()
    relationship = store.create("relationship", {"display_name": "SENTINEL PERSON", "state": "active", "lifecycle": "active"})
    request = store.create("request", {"relationship_id": relationship["id"], "body": "SENTINEL REQUEST"})
    accepted, commitment = store.accept_request(request["id"], {"body": "SENTINEL COMMITMENT"})
    retried, same_commitment = store.accept_request(request["id"], {"body": "must not replace"})
    assert accepted["lifecycle"] == "accepted"
    assert commitment["lifecycle"] == "open"
    assert retried["accepted_commitment_id"] == commitment["id"]
    assert same_commitment["id"] == commitment["id"]
    assert len(store.open_commitments()) == 1


def test_atomic_accept_refuses_an_archived_relationship(tmp_path) -> None:
    store = _store(tmp_path)
    store.initialize()
    relationship = store.create("relationship", {"display_name": "Archived", "state": "active", "lifecycle": "active"})
    request = store.create("request", {"relationship_id": relationship["id"], "body": "Never commit"})
    store.archive(relationship["id"])

    with pytest.raises(ValueError, match="people_relationship_inactive"):
        store.accept_request(request["id"], {"body": "Never commit"})
    assert store.open_commitments() == []


def test_store_owns_canonical_ids_and_payload_cannot_override_metadata(tmp_path) -> None:
    store = _store(tmp_path)
    store.initialize()
    created = store.create("relationship", {"id": "caller-id", "kind": "lie", "lifecycle": "lie", "display_name": "SENTINEL"})
    assert created["id"] != "caller-id"
    assert created["kind"] == "relationship"
    assert store.get(created["id"])["display_name"] == "SENTINEL"
    replaced = store.replace(created["id"], {"id": "second-lie", "lifecycle": "active", "display_name": "updated"})
    assert replaced["id"] == created["id"]
    assert store.get(created["id"])["display_name"] == "updated"
