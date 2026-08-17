"""Hostile boundary checks for confidential People material."""

from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db.core import Database, backup_database
from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.people_service import PeopleService, PeopleUnavailable
from holdspeak.services.sync_service import SYNC_REGISTRY


OWNER = Principal(PrincipalKind.OWNER, "people-leak-owner")
SENTINELS = (
    "PEOPLE-SENTINEL-NAME",
    "PEOPLE-SENTINEL-PRIVATE-PREP",
    "PEOPLE-SENTINEL-AGENDA",
    "PEOPLE-SENTINEL-REQUEST",
)


def _assert_absent(path: Path) -> None:
    if not path.exists():
        return
    raw = path.read_bytes()
    for sentinel in SENTINELS:
        assert sentinel.encode() not in raw, f"confidential sentinel escaped into {path.name}"


def test_full_people_lifecycle_leaves_no_plaintext_in_durable_product_planes(tmp_path: Path) -> None:
    """Only authorized responses decrypt; every durable generic plane stays blind."""
    main_db = Database(tmp_path / "holdspeak.db")
    store = EncryptedPeopleStore(
        tmp_path / "people-private" / "people.v1.sqlite3",
        MemoryKeyStore(),
    )
    store.initialize()
    people = PeopleService(store)

    relationship = people.create_relationship(OWNER, {"display_name": SENTINELS[0]})
    session = people.create_one_on_one(
        OWNER,
        relationship["id"],
        {"private_prep": SENTINELS[1], "visibility": "leader_private"},
    )
    people.add_agenda_item(
        OWNER,
        session["id"],
        {"body": SENTINELS[2], "visibility": "shared_intent"},
    )
    request = people.create_request(
        OWNER,
        relationship["id"],
        {"body": SENTINELS[3], "visibility": "shared_intent"},
    )
    commitment = people.accept_request(OWNER, request["id"])

    follow_through = FollowThroughService(main_db, people_projection=people)
    card = next(
        card
        for lane in follow_through.board(OWNER).__dict__.values()
        for card in lane
        if card.id == f"people:{commitment['id']}"
    )
    follow_through.complete(OWNER, card.id, "done")
    follow_through.complete(OWNER, card.id, "reopen")

    # The ordinary database includes action_items, Cadence, FTS, kernel journal,
    # receipts, sync inbox/outbox, and export metadata. A raw scan covers all of
    # those tables plus their SQLite free pages and journal files.
    main_db.close()
    backup = backup_database(main_db.db_path)
    for path in (
        main_db.db_path,
        main_db.db_path.with_name(main_db.db_path.name + "-wal"),
        main_db.db_path.with_name(main_db.db_path.name + "-shm"),
        backup,
        store.path,
        store.path.with_name(store.path.name + "-wal"),
        store.path.with_name(store.path.name + "-shm"),
        tmp_path / "holdspeak.log",
    ):
        _assert_absent(path)

    assert "people" not in SYNC_REGISTRY
    assert not list(store.directory.glob("*.bak"))


def test_store_failure_never_echoes_payload_through_service_error() -> None:
    class FailingStore:
        def readiness(self) -> str:
            return "ready"

        def create(self, kind, payload):
            raise RuntimeError(f"driver failure containing {payload!r}")

    service = PeopleService(FailingStore())
    with pytest.raises(PeopleUnavailable) as caught:
        service.create_relationship(OWNER, {"display_name": SENTINELS[0]})

    assert str(caught.value) == "people_store_write_failed"
    for sentinel in SENTINELS:
        assert sentinel not in str(caught.value)
