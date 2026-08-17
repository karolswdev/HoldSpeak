"""People domain and ephemeral Follow-through projection coverage."""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.people_service import PeopleService, PeopleServiceError
from holdspeak.services.sqlite_observer import SQLiteObserver


OWNER = Principal(PrincipalKind.OWNER, "people-owner")
AGENT = Principal(PrincipalKind.AGENT, "not-the-owner")


@pytest.fixture
def service(tmp_path: Path) -> PeopleService:
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    store.initialize()
    return PeopleService(store)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def test_manual_relationship_one_on_one_request_and_explicit_commitment(service: PeopleService) -> None:
    relationship = service.create_relationship(OWNER, {"display_name": "Sentinel Person"})
    one_on_one = service.create_one_on_one(OWNER, relationship["id"], {"agenda": "Discuss continuity"})
    agenda = service.add_agenda_item(OWNER, one_on_one["id"], {"body": "Bring context", "visibility": "shared_intent"})
    request = service.create_request(OWNER, relationship["id"], {"body": "Make an introduction"})

    assert service.list_cards(OWNER) == []
    commitment = service.accept_request(OWNER, request["id"])
    retried = service.accept_request(OWNER, request["id"])
    detail = service.get_relationship(OWNER, relationship["id"])

    assert commitment["id"] == retried["id"]
    assert agenda["body"] == "Bring context"
    assert detail["sessions"][0]["agenda"][0]["body"] == "Bring context"
    assert detail["requests"][0]["state"] == "accepted"
    assert detail["commitments"][0]["id"] == commitment["id"]
    assert [card.id for card in service.list_cards(OWNER)] == [f"people:{commitment['id']}"]


def test_relationship_kinds_and_encrypted_grounding_notes(service: PeopleService) -> None:
    for kind in ("direct_report", "peer", "extended"):
        relationship = service.create_relationship(OWNER, {
            "display_name": f"{kind} relationship",
            "relationship_kind": kind,
        })
        shared = service.create_note(OWNER, relationship["id"], {
            "topic": "Working context",
            "body": f"Shared {kind} context",
            "visibility": "shared_intent",
        })
        private = service.create_note(OWNER, relationship["id"], {
            "body": f"Private {kind} context",
            "visibility": "leader_private",
        })
        detail = service.get_relationship(OWNER, relationship["id"])
        assert detail["relationship_kind"] == kind
        assert [note["id"] for note in detail["notes"]] == [shared["id"], private["id"]]
        assert all(note["source"] == "manual" for note in detail["notes"])


def test_roll_forward_closes_source_and_only_links_same_session(service: PeopleService) -> None:
    relationship = service.create_relationship(OWNER, {"display_name": "Roll sentinel"})
    session = service.create_one_on_one(OWNER, relationship["id"], {})
    source = service.add_agenda_item(OWNER, session["id"], {"body": "Carry this", "visibility": "leader_private"})
    successor = service.add_agenda_item(OWNER, session["id"], {"body": "Carry this", "visibility": "leader_private", "rolled_from_id": source["id"]})
    agenda = service.list_one_on_ones(OWNER, relationship["id"])[0]["agenda"]

    source_after = next(item for item in agenda if item["id"] == source["id"])
    assert source_after["state"] == "rolled"
    assert successor["rolled_from_id"] == source["id"]
    with pytest.raises(PeopleServiceError, match="people_agenda_item_not_rollable"):
        service.add_agenda_item(OWNER, session["id"], {"body": "Again", "rolled_from_id": source["id"]})


def test_follow_through_hydrates_people_only_in_memory(service: PeopleService, db: Database) -> None:
    relationship = service.create_relationship(OWNER, {"display_name": "Sentinel Person"})
    request = service.create_request(OWNER, relationship["id"], {"body": "Private manager promise"})
    commitment = service.accept_request(OWNER, request["id"])
    follow_through = FollowThroughService(db, people_projection=service)

    board = follow_through.board(OWNER)
    card = board.now[0]
    assert card.id == f"people:{commitment['id']}"
    assert card.target_ref == f"people:{relationship['id']}"
    assert follow_through.complete(OWNER, card.id, "done") == {"card_id": card.id, "verb": "done"}
    assert follow_through.board(OWNER).waiting == []
    assert follow_through.complete(OWNER, card.id, "reopen") == {"card_id": card.id, "verb": "reopen"}
    with pytest.raises(ValueError, match="people_commitment_verb_unsupported"):
        follow_through.complete(OWNER, card.id, "snooze", {"until": "2099-01-01"})

    raw = db.db_path.read_bytes()
    assert b"Sentinel Person" not in raw
    assert b"Private manager promise" not in raw


def test_follow_through_observer_redacts_decrypted_people_cards(service: PeopleService, db: Database) -> None:
    relationship = service.create_relationship(OWNER, {"display_name": "Observer Sentinel Person"})
    request = service.create_request(OWNER, relationship["id"], {"body": "Observer Sentinel Promise"})
    commitment = service.accept_request(OWNER, request["id"])

    follow_through = FollowThroughService(
        db,
        people_projection=service,
        observer=SQLiteObserver(db._connection),
    )
    follow_through.board(OWNER)
    follow_through.complete(
        OWNER,
        f"people:{commitment['id']}",
        "done",
        {"untrusted_payload": "Observer Sentinel Transition Payload"},
    )

    with db._connection() as conn:
        events = conn.execute(
            "SELECT method,args_summary,result_summary,error,error_code FROM pipeline_events WHERE service='FollowThroughService' ORDER BY timestamp"
        ).fetchall()
    assert [event[0] for event in events] == ["board", "complete"]
    assert events[0][2] == '{"board":"redacted"}'
    assert events[1][1:] == (
        '{"people_transition":"redacted"}',
        '{"people_transition":"redacted"}',
        None,
        None,
    )
    assert "Observer Sentinel" not in str([tuple(event) for event in events])
    assert b"Observer Sentinel" not in db.db_path.read_bytes()


def test_archived_relationship_is_hidden_and_cannot_mint_commitments(service: PeopleService) -> None:
    relationship = service.create_relationship(OWNER, {"display_name": "Archived Sentinel"})
    request = service.create_request(OWNER, relationship["id"], {"body": "Must not become a card"})
    service.archive_relationship(OWNER, relationship["id"])

    with pytest.raises(PeopleServiceError, match="people_relationship_not_found"):
        service.get_relationship(OWNER, relationship["id"])
    with pytest.raises(PeopleServiceError, match="people_relationship_not_found"):
        service.accept_request(OWNER, request["id"])
    assert service.list_cards(OWNER) == []


def test_people_requires_owner(service: PeopleService) -> None:
    with pytest.raises(PeopleServiceError, match="people_owner_required"):
        service.list_relationships(AGENT)


def test_readiness_reports_existing_encrypted_store_without_key(tmp_path: Path) -> None:
    keys = MemoryKeyStore()
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", keys)
    store.initialize()
    keys.values.clear()

    status = PeopleService(store).readiness(OWNER)

    assert status["state"] == "key_unavailable"
    assert status["store"] == "encrypted"
    assert status["reason_code"] == "people_store_key_unavailable"
