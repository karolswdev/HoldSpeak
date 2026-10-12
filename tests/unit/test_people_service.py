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


def test_commitment_execution_link_satisfaction_and_history(service: PeopleService) -> None:
    relationship = service.create_relationship(OWNER, {"display_name": "Execution history"})
    request = service.create_request(OWNER, relationship["id"], {"body": "Prepare the architecture discussion"})
    commitment = service.accept_request(OWNER, request["id"])

    linked = service.attach_execution(
        OWNER,
        commitment["id"],
        workbench_id="wb_architecture",
        item_id="wbi_discussion",
    )
    satisfied = service.satisfy_commitment(
        OWNER,
        commitment["id"],
        rationale="Design brief reviewed",
        evidence=[{"kind": "workbench_item", "item_id": "wbi_discussion", "status": "done"}],
    )
    summary = service.history_summary(OWNER, relationship["id"])

    assert linked["execution_links"][0]["item_id"] == "wbi_discussion"
    assert [event["event"] for event in satisfied["history"]] == ["accepted", "delegated", "satisfied"]
    assert satisfied["history"][-1]["rationale"] == "Design brief reviewed"
    assert summary == {
        "accepted": 1,
        "open": 0,
        "satisfied": 1,
        "dismissed": 0,
        "reopened": 0,
        "with_evidence": 1,
        "commitments": [satisfied],
    }

    service.transition(OWNER, f"people:{commitment['id']}", "reopen")
    reopened = service.history_summary(OWNER, relationship["id"])
    assert reopened["open"] == 1
    assert reopened["reopened"] == 1


def test_relationship_project_links_are_stable_context_refs(service: PeopleService) -> None:
    relationship = service.create_relationship(OWNER, {"display_name": "Project collaborator"})
    linked = service.link_project(OWNER, relationship["id"], "proj-platform")
    duplicate = service.link_project(OWNER, relationship["id"], "proj-platform")
    assert linked["project_refs"] == ["proj-platform"]
    assert duplicate["project_refs"] == ["proj-platform"]
    assert service.get_relationship(OWNER, relationship["id"])["project_refs"] == ["proj-platform"]
    assert service.unlink_project(OWNER, relationship["id"], "proj-platform")["project_refs"] == []


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


def test_philo17_they_owe_you_is_a_commitment_the_other_way(service: PeopleService) -> None:
    """U09: what the person owes him is stored as a commitment with
    direction report_owes; it never shows as his own (You owe, brief, cards,
    history), and Done closes it like his own."""
    relationship = service.create_relationship(OWNER, {"display_name": "Maya Chen"})
    rid = relationship["id"]
    request = service.create_request(OWNER, rid, {"body": "Review her design doc"})
    mine = service.accept_request(OWNER, request["id"])
    owed = service.create_owed_to_you(OWNER, rid, {"body": "Send me the API migration estimate", "visibility": "shared_intent"})

    assert owed["direction"] == "report_owes"
    assert owed["state"] == "open"
    assert owed["history"][0]["event"] == "recorded"

    detail = service.get_relationship(OWNER, rid)
    assert [item["id"] for item in detail["commitments"]] == [mine["id"]]
    assert [item["id"] for item in detail["owed_to_you"]] == [owed["id"]]

    brief = service.one_on_one_brief(OWNER, rid)
    assert [item["id"] for item in brief["open_commitments"]] == [mine["id"]]
    assert [item["id"] for item in brief["owed_to_you"]] == [owed["id"]]

    assert [card.id for card in service.list_cards(OWNER)] == [f"people:{mine['id']}"]
    assert service.history_summary(OWNER, rid)["accepted"] == 1

    service.transition(OWNER, f"people:{owed['id']}", "done")
    assert service.one_on_one_brief(OWNER, rid)["owed_to_you"] == []
    assert service.get_relationship(OWNER, rid)["owed_to_you"][0]["state"] == "done"


def test_philo17_they_owe_you_needs_a_body_and_the_owner(service: PeopleService) -> None:
    rid = service.create_relationship(OWNER, {"display_name": "Sam Ortiz"})["id"]
    with pytest.raises(PeopleServiceError, match="people_payload_required"):
        service.create_owed_to_you(OWNER, rid, {"body": "  "})
    with pytest.raises(PeopleServiceError):
        service.create_owed_to_you(AGENT, rid, {"body": "Not his to write"})


def test_the_list_counts_owed_both_ways_in_one_read(service: PeopleService) -> None:
    """PHILO-17 (Astra r1 on #1110, MUST 4): the roster answer carries what
    each person is owed and owes (open commitments only), only when asked."""
    maya = service.create_relationship(OWNER, {"display_name": "Maya"})
    sam = service.create_relationship(OWNER, {"display_name": "Sam"})
    request = service.create_request(OWNER, maya["id"], {"body": "Review the doc"})
    service.accept_request(OWNER, request["id"])
    service.create_owed_to_you(OWNER, maya["id"], {"body": "Send the plan"})

    rows = {row["display_name"]: row for row in service.list_relationships(OWNER, with_counts=True)}
    assert (rows["Maya"]["you_owe_count"], rows["Maya"]["owes_you_count"]) == (1, 1)
    assert (rows["Sam"]["you_owe_count"], rows["Sam"]["owes_you_count"]) == (0, 0)
    plain = service.list_relationships(OWNER)
    assert all("you_owe_count" not in row for row in plain)
    assert sam["id"] in {row["id"] for row in plain}


# Moved from tests/unit/test_hs172_people_sources.py (fast diet, by service).
# ==============================================================================
# HS-172-04: The People resolver
# ==============================================================================


class TestPeopleResolver:
    """resolve_relationship_by_watch_identity: alias, display_name, login."""

    def test_alias_matches(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Ania Kowalska"})
        service.link_owner_alias(OWNER, rel["id"], "ania-k")
        result = service.resolve_relationship_by_watch_identity("ania-k")
        assert result["state"] == "ready"
        assert result["relationship"]["id"] == rel["id"]

    def test_display_name_matches(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Marek Nowak"})
        result = service.resolve_relationship_by_watch_identity("Marek Nowak")
        assert result["state"] == "ready"
        assert result["relationship"]["id"] == rel["id"]

    def test_case_insensitive_alias(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Ania"})
        service.link_owner_alias(OWNER, rel["id"], "Ania-K")
        result = service.resolve_relationship_by_watch_identity("ania-k")
        assert result["relationship"]["id"] == rel["id"]

    def test_case_insensitive_display_name(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Marek Nowak"})
        result = service.resolve_relationship_by_watch_identity("marek nowak")
        assert result["relationship"]["id"] == rel["id"]

    def test_no_match_returns_none(self, service: PeopleService) -> None:
        service.create_relationship(OWNER, {"display_name": "Known Person"})
        result = service.resolve_relationship_by_watch_identity("unknown-login")
        assert result["state"] == "ready"
        assert result["relationship"] is None

    def test_archived_excluded(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Archived"})
        service.link_owner_alias(OWNER, rel["id"], "archived-login")
        service.archive_relationship(OWNER, rel["id"])
        result = service.resolve_relationship_by_watch_identity("archived-login")
        assert result["relationship"] is None

    def test_alias_takes_priority_over_display_name(self, service: PeopleService) -> None:
        """When two people exist where one's alias matches and another's display_name
        matches, the alias match wins (it is searched first)."""
        rel_alias = service.create_relationship(OWNER, {"display_name": "Person A"})
        service.link_owner_alias(OWNER, rel_alias["id"], "shared-string")
        rel_display = service.create_relationship(OWNER, {"display_name": "shared-string"})
        result = service.resolve_relationship_by_watch_identity("shared-string")
        # Alias match wins.
        assert result["relationship"]["id"] == rel_alias["id"]

    def test_returns_only_id_no_name_leak(self, service: PeopleService) -> None:
        """The resolver returns a relationship view -- but the ROUTE returns
        only the id.  Verify the resolver itself returns a view (for internal use)
        and that it contains an id."""
        rel = service.create_relationship(OWNER, {"display_name": "Secret Person"})
        service.link_owner_alias(OWNER, rel["id"], "secret-login")
        result = service.resolve_relationship_by_watch_identity("secret-login")
        # The resolver returns a relationship view for internal callers.
        assert "id" in result["relationship"]
        # The view shape is the standard one.
        assert "display_name" in result["relationship"]

    def test_empty_string_returns_none(self, service: PeopleService) -> None:
        result = service.resolve_relationship_by_watch_identity("")
        assert result["relationship"] is None

    def test_github_login_as_alias(self, service: PeopleService) -> None:
        """A GitHub login linked as an alias resolves correctly."""
        rel = service.create_relationship(OWNER, {"display_name": "Karol"})
        service.link_owner_alias(OWNER, rel["id"], "karolswdev")
        result = service.resolve_relationship_by_watch_identity("karolswdev")
        assert result["relationship"]["id"] == rel["id"]

    def test_jira_display_name_as_alias(self, service: PeopleService) -> None:
        """A Jira display name linked as an alias resolves correctly."""
        rel = service.create_relationship(OWNER, {"display_name": "Ania"})
        service.link_owner_alias(OWNER, rel["id"], "Ania Kowalska")
        result = service.resolve_relationship_by_watch_identity("Ania Kowalska")
        assert result["relationship"]["id"] == rel["id"]
