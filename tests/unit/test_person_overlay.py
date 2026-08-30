"""HS-150-03 -- the chief-of-staff overlay: five chartered pins.

1. Write-count spy (monday_briefs/_items/_shelf gain ZERO person rows).
2. pipeline_events content check (no person content in result_summary).
3. MondayBrief dataclass shape pin (no person_sections key in asdict).
4. F6 pin (planted leader_private never in MCP response; access-off -> absent).
5. L2 refusal (sidecar unavailable -> {"state":"unavailable"}).
6. D2 hygiene pin (no "/" path fragments in persisted item details).

All tests use the headless file keystore seam or MemoryKeyStore --
ZERO keyring/keychain calls.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import resources, tools
from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.monday_brief_service import MondayBrief, MondayBriefService
from holdspeak.services.person_overlay import compose_person_overlay
from holdspeak.services.people_service import PeopleService, UnavailablePeopleStore


OWNER = Principal(PrincipalKind.OWNER, "overlay-test-owner")


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


# -- Pin 1: write-count spy ---------------------------------------------------


class TestWriteCountSpy:
    """Generate+get cycle with People present must add ZERO rows to
    monday_briefs / monday_brief_items / monday_brief_item_shelf."""

    def test_zero_person_rows_in_brief_tables(
        self, db: Database, people_service: PeopleService,
    ) -> None:
        # Seed a relationship with a signal.
        rel = people_service.create_relationship(OWNER, {"display_name": "Ewa"})
        req = people_service.create_request(
            OWNER, rel["id"], {"body": "Review plan", "visibility": "shared_intent"},
        )
        people_service.accept_request(OWNER, req["id"])

        service = MondayBriefService(db)
        brief = service.generate(OWNER)

        # Count rows across the three brief tables.
        with db._connection() as conn:
            brief_count = conn.execute("SELECT COUNT(*) FROM monday_briefs").fetchone()[0]
            item_count = conn.execute("SELECT COUNT(*) FROM monday_brief_items").fetchone()[0]
            shelf_count = conn.execute("SELECT COUNT(*) FROM monday_brief_item_shelf").fetchone()[0]

        # Now compose the overlay (the adapter layer).
        from holdspeak.services.follow_through_service import FollowThroughService
        ft = FollowThroughService(db)
        overlay = compose_person_overlay(
            (brief.period_start, brief.period_end),
            people_service, ft, db, OWNER,
        )

        # Verify the overlay produced sections.
        assert overlay["state"] == "ready"
        assert len(overlay.get("sections", [])) >= 1

        # Verify ZERO new rows were written.
        with db._connection() as conn:
            assert conn.execute("SELECT COUNT(*) FROM monday_briefs").fetchone()[0] == brief_count
            assert conn.execute("SELECT COUNT(*) FROM monday_brief_items").fetchone()[0] == item_count
            assert conn.execute("SELECT COUNT(*) FROM monday_brief_item_shelf").fetchone()[0] == shelf_count


# -- Pin 2: pipeline_events content check ------------------------------------


class TestPipelineEventsContentCheck:
    """No person content in any result_summary after a generate+get cycle."""

    def test_no_person_content_in_pipeline_events(
        self, db: Database, people_service: PeopleService,
    ) -> None:
        rel = people_service.create_relationship(OWNER, {"display_name": "Marek"})
        people_service.create_request(
            OWNER, rel["id"], {"body": "Secret prep", "visibility": "leader_private"},
        )

        service = MondayBriefService(db)
        service.generate(OWNER)
        service.get_latest(OWNER)

        with db._connection() as conn:
            events = conn.execute(
                "SELECT result_summary FROM pipeline_events"
            ).fetchall()

        for event in events:
            summary = str(event["result_summary"] or "")
            assert "Marek" not in summary, f"Person name leaked: {summary}"
            assert "person_sections" not in summary, f"person_sections leaked: {summary}"
            assert "leader_private" not in summary.lower() or "redacted" in summary.lower(), (
                f"Leader-private content leaked: {summary}"
            )


# -- Pin 3: MondayBrief dataclass shape pin -----------------------------------


class TestDataclassShapePin:
    """asdict(MondayBrief) NEVER has a person_sections key."""

    def test_no_person_sections_in_asdict(self) -> None:
        brief = MondayBrief(
            id="test-brief",
            period_start="2026-08-25T17:00:00",
            period_end="2026-08-26T09:00:00",
            headline="Nothing.",
            sections={"changed": [], "broke": [], "waiting": [], "decisions": []},
            generated_at="2026-08-26T09:00:00",
        )
        d = asdict(brief)
        assert "person_sections" not in d, (
            f"person_sections appeared in asdict(MondayBrief): {list(d.keys())}"
        )

    def test_no_person_sections_field_on_class(self) -> None:
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(MondayBrief)}
        assert "person_sections" not in field_names


# -- Pin 4: F6 pin (MCP gate) ------------------------------------------------


class TestF6MondayBriefMcpGate:
    """Person_sections absent when access_mode == 'off'; planted leader_private never appears."""

    @pytest.fixture
    def mcp_db(self, db: Database, monkeypatch: pytest.MonkeyPatch) -> Database:
        monkeypatch.setattr(tools, "get_database", lambda: db)
        monkeypatch.setattr(tools, "get_observer", lambda: None)
        monkeypatch.setattr(resources, "get_database", lambda: db)
        return db

    def test_access_off_no_person_sections(
        self, mcp_db: Database, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from holdspeak.mcp.families import people as people_family
        monkeypatch.setenv(people_family.ACCESS_ENV, "off")

        result = tools.dispatch("monday_brief.generate", {}, OWNER)
        assert "person_sections" not in result, (
            "person_sections present when People access is off"
        )

    def test_leader_private_never_in_mcp_brief(
        self, mcp_db: Database, people_service: PeopleService, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from holdspeak.mcp.families import people as people_family
        monkeypatch.delenv(people_family.ACCESS_ENV, raising=False)
        monkeypatch.setattr(people_family, "build_people_service", lambda: people_service)

        rel = people_service.create_relationship(OWNER, {"display_name": "F6 person"})
        # Plant a leader_private commitment.
        req = people_service.create_request(
            OWNER, rel["id"], {"body": "PRIVATE SECRET", "visibility": "leader_private"},
        )
        people_service.accept_request(OWNER, req["id"])
        # And a shared one.
        req2 = people_service.create_request(
            OWNER, rel["id"], {"body": "Shared task", "visibility": "shared_intent"},
        )
        people_service.accept_request(OWNER, req2["id"])

        result = tools.dispatch("monday_brief.generate", {}, OWNER)
        result_str = json.dumps(result)

        assert "PRIVATE SECRET" not in result_str, (
            "Leader-private content appeared in MCP monday_brief"
        )


# -- Pin 5: L2 refusal -------------------------------------------------------


class TestL2Refusal:
    """Sidecar unavailable -> {"state":"unavailable"}, never silence."""

    def test_unavailable_sidecar_returns_unavailable(self, db: Database) -> None:
        from holdspeak.services.follow_through_service import FollowThroughService
        unavailable_svc = PeopleService(UnavailablePeopleStore())
        ft = FollowThroughService(db)

        overlay = compose_person_overlay(
            ("2026-08-25T17:00:00", "2026-08-26T09:00:00"),
            unavailable_svc, ft, db, OWNER,
        )

        assert overlay["state"] == "unavailable"


# -- Staleness fallback order pin (delegated_at ?? created_at) ----------------


class TestStalenessAgeOrder:
    """The ruled law: delegated_at wins when both present; created_at when
    only it exists; honest absence when neither."""

    def test_delegated_at_wins_when_both_present(self) -> None:
        from holdspeak.services.person_overlay import _stalest_age
        from types import SimpleNamespace
        import datetime

        today = datetime.date.today()
        old = (today - datetime.timedelta(days=10)).isoformat()
        recent = (today - datetime.timedelta(days=3)).isoformat()

        card = SimpleNamespace(delegated_at=recent, created_at=old, owner="Ewa")
        age = _stalest_age([card])
        assert age == 3, f"Expected 3 (delegated_at wins), got {age}"

    def test_created_at_when_only_it(self) -> None:
        from holdspeak.services.person_overlay import _stalest_age
        from types import SimpleNamespace
        import datetime

        today = datetime.date.today()
        created = (today - datetime.timedelta(days=7)).isoformat()

        card = SimpleNamespace(delegated_at=None, created_at=created, owner="Jan")
        age = _stalest_age([card])
        assert age == 7, f"Expected 7 (created_at fallback), got {age}"

    def test_absent_when_neither_exists(self) -> None:
        from holdspeak.services.person_overlay import _stalest_age
        from types import SimpleNamespace

        card = SimpleNamespace(delegated_at=None, created_at=None, owner="Ola")
        age = _stalest_age([card])
        assert age is None, f"Expected None (honest absence), got {age}"


# -- Pin 6: D2 hygiene pin (no path fragments in persisted details) -----------


class TestD2HygienePin:
    """Raw '/' path fragments from observer args_summary must never enter
    persisted monday_brief_items details."""

    def test_no_path_fragments_in_persisted_details(self, db: Database) -> None:
        import datetime

        service = MondayBriefService(db)
        now = datetime.datetime(2026, 8, 26, 9, 30)
        window_start, window_end = service.compute_window(now)

        # Seed a pipeline event with a raw filesystem path in args_summary.
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO pipeline_events
                   (event_id, timestamp, service, method, principal_kind,
                    args_summary, correlation_id, error)
                   VALUES (?, ?, ?, ?, 'test', ?, '', NULL)""",
                (
                    "ev-path-leak",
                    window_start.timestamp() + 60,
                    "SettingsService",
                    "update_settings",
                    '{"path": "/Users/karol/.config/holdspeak/settings.json"}',
                ),
            )

        brief = service.generate(OWNER, now=now)

        # Find the settings change item.
        for section_items in brief.sections.values():
            for item in section_items:
                if item.detail is not None:
                    assert "/" not in item.detail or "<path>" in item.detail, (
                        f"Raw path fragment leaked into persisted detail: {item.detail}"
                    )

    def test_sanitize_strips_filesystem_paths(self) -> None:
        from holdspeak.services.monday_brief_service import _sanitize_detail

        # A JSON string with a filesystem path.
        result = _sanitize_detail('{"path": "/Users/karol/.config/holdspeak/settings.json"}')
        assert result is None or "/" not in result or "<path>" in result

        # Empty args.
        assert _sanitize_detail("{}") is None

        # No path, normal args.
        result = _sanitize_detail('{"key": "value"}')
        assert result == '{"key": "value"}'


# -- briefs/latest resource shape pin -----------------------------------------


class TestResourceShapePin:
    """holdspeak://briefs/latest serves the person-free dataclass by construction."""

    def test_resource_has_no_person_sections(self, db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(resources, "get_database", lambda: db)

        MondayBriefService(db).generate(OWNER)
        result = resources.read_resource("holdspeak://briefs/latest", OWNER)
        contents = result["contents"][0]
        payload = json.loads(contents["text"])

        assert "person_sections" not in payload, (
            "person_sections appeared in briefs/latest resource"
        )
