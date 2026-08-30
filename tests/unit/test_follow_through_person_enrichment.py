"""HS-150-07 -- follow-through route adapter person enrichment: four pins.

(a) Route response carries person_label for a mapped owner and NOT for
    an unmapped one (no inference).
(b) MCP follow_through.board output contains no person_label with the
    same data planted (person-free pin).
(c) pipeline_events content check across the route call (the observer
    sees the service result, not the enriched response).
(d) Sidecar-unavailable degrades to the plain board without error.

All tests use the headless file keystore seam or MemoryKeyStore --
ZERO keyring/keychain calls.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import resources, tools
from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.people_service import PeopleService, UnavailablePeopleStore


OWNER = Principal(PrincipalKind.OWNER, "ft-person-enrichment-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


@pytest.fixture
def people_service(tmp_path: Path) -> PeopleService:
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    store.initialize()
    return PeopleService(store)


def _seed_mapped_and_unmapped(db: Database, people_service: PeopleService) -> str:
    """Seed two action items: one with a mapped owner, one unmapped.

    Returns the relationship id for the mapped owner.
    """
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("m-person-1", "2026-08-01T09:00:00", "Planning"),
        )
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'open', 'accepted', ?)",
            ("action-mapped", "m-person-1", "Review proposal", "Ewa Kowalska",
             date.today().isoformat(), "2026-08-25T10:00:00"),
        )
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'open', 'accepted', ?)",
            ("action-unmapped", "m-person-1", "Check dashboard", "Unknown Person",
             date.today().isoformat(), "2026-08-25T10:00:00"),
        )

    # Map "Ewa Kowalska" to a People relationship.
    rel = people_service.create_relationship(OWNER, {"display_name": "Ewa"})
    people_service.link_owner_alias(OWNER, rel["id"], "Ewa Kowalska")
    return str(rel["id"])


# -- Pin (a): route adapter carries person_label for mapped, NOT for unmapped --


class TestRouteAdapterPersonLabel:
    """The _enrich_board function stamps person_label on mapped cards and
    does NOT infer identity for unmapped ones."""

    def test_mapped_owner_gets_person_label(
        self, db: Database, people_service: PeopleService, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        rel_id = _seed_mapped_and_unmapped(db, people_service)
        service = FollowThroughService(db)
        board = service.board(OWNER)

        from holdspeak.web.routes.follow_through import _board_dict, _enrich_board
        import holdspeak.people as _people_mod

        # Monkeypatch production_people_store to use our test store.
        monkeypatch.setattr(
            _people_mod, "production_people_store",
            lambda: people_service._store,
        )

        board_dict = _board_dict(board)
        enriched = _enrich_board(board_dict, board)

        # Find the mapped and unmapped cards.
        all_cards = []
        for lane in enriched.values():
            all_cards.extend(lane)

        mapped = [c for c in all_cards if c.get("owner") == "Ewa Kowalska"]
        unmapped = [c for c in all_cards if c.get("owner") == "Unknown Person"]

        assert len(mapped) == 1, f"Expected 1 mapped card, got {len(mapped)}"
        assert mapped[0]["person_label"] == "Ewa"
        assert mapped[0]["person_relationship_id"] == rel_id

        assert len(unmapped) == 1, f"Expected 1 unmapped card, got {len(unmapped)}"
        assert "person_label" not in unmapped[0], (
            f"Unmapped card should not have person_label: {unmapped[0]}"
        )


# -- Pin (b): MCP follow_through.board stays person-free ----------------------


class TestMcpFollowThroughPersonFree:
    """The MCP tool calls the service directly and must NEVER carry
    person_label, even when owner aliases are configured."""

    def test_mcp_board_no_person_label(
        self, db: Database, people_service: PeopleService, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_mapped_and_unmapped(db, people_service)

        monkeypatch.setattr(tools, "get_database", lambda: db)
        monkeypatch.setattr(tools, "get_observer", lambda: None)
        monkeypatch.setattr(resources, "get_database", lambda: db)

        # The MCP tool calls follow_through.board via the service directly.
        board = tools.dispatch("follow_through.board", {}, OWNER)

        all_cards: list[dict[str, Any]] = []
        for lane in board.values():
            all_cards.extend(lane)

        for card in all_cards:
            assert "person_label" not in card, (
                f"MCP board must be person-free but found person_label on card: {card}"
            )
            assert "person_relationship_id" not in card, (
                f"MCP board must be person-free but found person_relationship_id on card: {card}"
            )


# -- Pin (c): pipeline_events content check ------------------------------------


class TestPipelineEventsPersonFree:
    """The observer sees the service result, not the enriched response.
    No person content in pipeline_events after a board read through the
    service."""

    def test_no_person_content_in_pipeline_events(
        self, db: Database, people_service: PeopleService,
    ) -> None:
        _seed_mapped_and_unmapped(db, people_service)

        from holdspeak.services.sqlite_observer import SQLiteObserver
        observer = SQLiteObserver(db._connection)
        service = FollowThroughService(db, observer=observer)

        # The service.board call is observed.
        service.board(OWNER)

        with db._connection() as conn:
            events = conn.execute(
                "SELECT result_summary FROM pipeline_events"
            ).fetchall()

        for event in events:
            summary = str(event["result_summary"] or "")
            assert "person_label" not in summary, (
                f"person_label leaked into pipeline_events: {summary}"
            )
            assert "Ewa" not in summary, (
                f"Person name leaked into pipeline_events: {summary}"
            )


# -- Pin (d): sidecar unavailable degrades gracefully -------------------------


class TestSidecarUnavailableDegrades:
    """When the People sidecar is unavailable, the enrichment degrades
    to the plain board without error."""

    def test_unavailable_sidecar_returns_plain_board(
        self, db: Database, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Seed an action item with an owner.
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
                ("m-degrade-1", "2026-08-01T09:00:00", "Planning"),
            )
            conn.execute(
                "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state) "
                "VALUES (?, ?, ?, ?, ?, 'open', 'accepted')",
                ("action-degrade", "m-degrade-1", "Review plan", "Some Owner",
                 date.today().isoformat()),
            )

        service = FollowThroughService(db)
        board = service.board(OWNER)

        from holdspeak.web.routes.follow_through import _board_dict, _enrich_board
        import holdspeak.people as _people_mod

        # Force the sidecar to be unavailable by making production_people_store raise.
        def _broken_store():
            raise RuntimeError("Sidecar unavailable")

        monkeypatch.setattr(
            _people_mod, "production_people_store",
            _broken_store,
        )

        board_dict = _board_dict(board)
        enriched = _enrich_board(board_dict, board)

        # The board should be returned unchanged (no error, no person_label).
        all_cards: list[dict[str, Any]] = []
        for lane in enriched.values():
            all_cards.extend(lane)

        for card in all_cards:
            assert "person_label" not in card, (
                f"Sidecar unavailable should not add person_label: {card}"
            )
