"""HS-149-04 -- the brief: read-time aggregation across the encrypted/plaintext boundary.

Every test uses the headless file keystore seam (HS-149-01) or the
MemoryKeyStore so ZERO keyring/keychain calls occur end-to-end.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.mcp import server
from holdspeak.mcp.families import people as people_family
from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.people.keys import FileKeyStore
from holdspeak.people.store import _dev_sidecar_path
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.people_service import PeopleService, PeopleServiceError


OWNER = Principal(PrincipalKind.OWNER, "brief-test-owner")


@pytest.fixture
def service(tmp_path: Path) -> PeopleService:
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    store.initialize()
    return PeopleService(store)


@pytest.fixture
def headless_service(tmp_path: Path) -> PeopleService:
    """Full headless lifecycle through the file keystore seam."""
    keyfile = tmp_path / "headless-keys.json"
    file_store = FileKeyStore(keyfile)
    sidecar = _dev_sidecar_path(keyfile)
    people_store = EncryptedPeopleStore(sidecar, file_store)
    people_store.initialize()
    return PeopleService(people_store)


def _make_plain_db(tmp_path: Path) -> Any:
    """Create a minimal plain DB with meetings, action_items, calendar_events, decision_records."""
    db_path = tmp_path / "plain.sqlite3"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("""CREATE TABLE calendar_events (
        id TEXT PRIMARY KEY, uid TEXT NOT NULL, title TEXT, starts_at TEXT,
        ends_at TEXT, location TEXT, meeting_url TEXT, last_seen_at REAL,
        subscription_revision TEXT, source_id TEXT NOT NULL DEFAULT '',
        source_label TEXT NOT NULL DEFAULT '')""")
    conn.execute("""CREATE TABLE meetings (
        id TEXT PRIMARY KEY, started_at TEXT NOT NULL, ended_at TEXT,
        title TEXT, calendar_event_id TEXT)""")
    conn.execute("""CREATE TABLE action_items (
        id TEXT PRIMARY KEY, meeting_id TEXT NOT NULL, task TEXT NOT NULL,
        owner TEXT, due TEXT, status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        delegated_at TEXT)""")
    conn.execute("""CREATE TABLE decision_records (
        id TEXT PRIMARY KEY, decision_text TEXT NOT NULL, rationale TEXT,
        lifecycle TEXT NOT NULL DEFAULT 'active',
        source_type TEXT NOT NULL, source_id TEXT NOT NULL,
        deleted INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')))""")
    conn.execute("""CREATE TABLE decision_record_sources (
        id TEXT PRIMARY KEY, record_id TEXT NOT NULL,
        source_type TEXT NOT NULL, source_ref TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')))""")
    conn.commit()
    # Return a mock DB with _connection() that returns the connection.
    db = SimpleNamespace()
    db._connection = lambda: conn
    return db


def _seed_plain_db(db: Any, calendar_events: list, meetings: list, action_items: list, decisions: list) -> None:
    """Seed the plain DB with test data."""
    conn = db._connection()
    for ev in calendar_events:
        conn.execute(
            "INSERT INTO calendar_events (id, uid, title, starts_at, ends_at, last_seen_at, subscription_revision, source_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ev["id"], ev["uid"], ev.get("title", ""), ev.get("starts_at", "2026-08-01"), ev.get("ends_at", "2026-08-01"), 0.0, "r1", ev.get("source_id", "")),
        )
    for m in meetings:
        conn.execute(
            "INSERT INTO meetings (id, started_at, ended_at, title, calendar_event_id) VALUES (?, ?, ?, ?, ?)",
            (m["id"], m.get("started_at", "2026-08-01T10:00:00"), m.get("ended_at"), m.get("title"), m.get("calendar_event_id")),
        )
    for ai in action_items:
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, due, status) VALUES (?, ?, ?, ?, ?, ?)",
            (ai["id"], ai["meeting_id"], ai["task"], ai.get("owner"), ai.get("due"), ai.get("status", "pending")),
        )
    for d in decisions:
        conn.execute(
            "INSERT INTO decision_records (id, decision_text, rationale, lifecycle, source_type, source_id) VALUES (?, ?, ?, ?, ?, ?)",
            (d["id"], d["decision_text"], d.get("rationale"), d.get("lifecycle", "active"), d.get("source_type", "meeting"), d["source_id"]),
        )
        # Also seed the decision_record_sources join table for meeting linkage.
        if d.get("meeting_id"):
            conn.execute(
                "INSERT INTO decision_record_sources (id, record_id, source_type, source_ref) VALUES (?, ?, 'meeting', ?)",
                (f"src-{d['id']}", d["id"], d["meeting_id"]),
            )
    conn.commit()


# -- Brief aggregation tests ---------------------------------------------------


class TestBriefAggregation:
    def test_brief_returns_open_commitments_and_agenda(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Ewa"})
        # Create a request, accept it -> commitment.
        req = service.create_request(OWNER, rel["id"], {"body": "Review the Q3 plan", "visibility": "shared_intent"})
        service.accept_request(OWNER, req["id"])
        # Create a session + agenda item.
        session = service.create_one_on_one(OWNER, rel["id"], {"visibility": "shared_intent"})
        service.add_agenda_item(OWNER, session["id"], {"body": "Discuss roadmap", "visibility": "shared_intent"})
        # Create a grounding note.
        service.create_note(OWNER, rel["id"], {"body": "Prefers async", "visibility": "shared_intent"})

        brief = service.one_on_one_brief(OWNER, rel["id"])
        assert brief["relationship_id"] == rel["id"]
        assert brief["display_name"] == "Ewa"
        assert len(brief["open_commitments"]) == 1
        assert brief["open_commitments"][0]["body"] == "Review the Q3 plan"
        assert len(brief["agenda_items"]) == 1
        assert brief["agenda_items"][0]["body"] == "Discuss roadmap"
        assert brief["grounding_note_count"] == 1

    def test_brief_linked_meetings_via_uid_chain(self, service: PeopleService, tmp_path: Path) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Jan"})
        service.link_calendar_series(OWNER, rel["id"], "uid-weekly", "cal-1", "Weekly 1:1")

        db = _make_plain_db(tmp_path)
        _seed_plain_db(db,
            calendar_events=[
                {"id": "ev-1", "uid": "uid-weekly", "source_id": "cal-1", "title": "Weekly 1:1", "starts_at": "2026-08-01"},
                {"id": "ev-2", "uid": "uid-weekly", "source_id": "cal-1", "title": "Weekly 1:1", "starts_at": "2026-08-08"},
            ],
            meetings=[
                {"id": "m-1", "title": "1:1 w/ Jan", "started_at": "2026-08-01T10:00:00", "calendar_event_id": "ev-1"},
                {"id": "m-2", "title": "1:1 w/ Jan #2", "started_at": "2026-08-08T10:00:00", "calendar_event_id": "ev-2"},
            ],
            action_items=[
                {"id": "ai-1", "meeting_id": "m-1", "task": "Ship the feature", "owner": "Jan", "status": "pending"},
                {"id": "ai-2", "meeting_id": "m-1", "task": "Done task", "owner": "Jan", "status": "completed"},
                {"id": "ai-3", "meeting_id": "m-2", "task": "Review docs", "status": "pending"},
            ],
            decisions=[
                {"id": "d-1", "decision_text": "Approved the architecture", "source_type": "meeting", "source_id": "m-1", "meeting_id": "m-1"},
            ],
        )

        brief = service.one_on_one_brief(OWNER, rel["id"], db=db)
        assert len(brief["linked_meetings"]) == 2
        # Newest first.
        assert brief["linked_meetings"][0]["meeting_id"] == "m-2"
        assert brief["linked_meetings"][1]["meeting_id"] == "m-1"
        # Open action items only (pending).
        assert len(brief["linked_meetings"][1]["open_action_items"]) == 1
        assert brief["linked_meetings"][1]["open_action_items"][0]["task"] == "Ship the feature"
        # Decision record.
        assert len(brief["linked_meetings"][1]["decisions"]) == 1
        assert brief["linked_meetings"][1]["decisions"][0]["decision_text"] == "Approved the architecture"

    def test_brief_unlinked_meeting_count_f11(self, service: PeopleService, tmp_path: Path) -> None:
        """F11: the brief names the count of un-linked meetings in its window."""
        rel = service.create_relationship(OWNER, {"display_name": "Kate"})
        service.link_calendar_series(OWNER, rel["id"], "uid-kate", "cal-1", "1:1")

        db = _make_plain_db(tmp_path)
        _seed_plain_db(db,
            calendar_events=[{"id": "ev-kate", "uid": "uid-kate", "source_id": "cal-1"}],
            meetings=[
                {"id": "m-linked", "title": "Linked", "started_at": "2026-08-01T10:00:00", "calendar_event_id": "ev-kate"},
                {"id": "m-unlinked", "title": "Unlinked", "started_at": "2026-08-02T10:00:00", "calendar_event_id": None},
                {"id": "m-unlinked-2", "title": "Also unlinked", "started_at": "2026-08-03T10:00:00", "calendar_event_id": ""},
            ],
            action_items=[], decisions=[],
        )

        brief = service.one_on_one_brief(OWNER, rel["id"], db=db)
        assert brief["unlinked_meeting_count"] == 2

    def test_brief_no_db_graceful_degradation(self, service: PeopleService) -> None:
        """When db is None, plaintext sections degrade to empty."""
        rel = service.create_relationship(OWNER, {"display_name": "No DB"})
        service.link_calendar_series(OWNER, rel["id"], "uid-x", "cal-x", "Series")
        brief = service.one_on_one_brief(OWNER, rel["id"])
        assert brief["linked_meetings"] == []
        assert brief["unlinked_meeting_count"] == 0

    def test_brief_excludes_satisfied_commitments(self, service: PeopleService) -> None:
        """Only OPEN commitments appear in the brief."""
        rel = service.create_relationship(OWNER, {"display_name": "Satisfied"})
        req = service.create_request(OWNER, rel["id"], {"body": "Done task", "visibility": "shared_intent"})
        commitment = service.accept_request(OWNER, req["id"])
        service.satisfy_commitment(OWNER, commitment["id"])
        brief = service.one_on_one_brief(OWNER, rel["id"])
        assert len(brief["open_commitments"]) == 0


# -- The never-persist pin (acceptance 3) --------------------------------------


class TestWriteCountSpy:
    """Acceptance 3: brief generation writes ZERO rows to either DB."""

    def test_brief_writes_zero_rows_to_encrypted_store(self, tmp_path: Path) -> None:
        """The encrypted store must not be written to during brief computation."""
        store = EncryptedPeopleStore(tmp_path / "spy.sqlite3", MemoryKeyStore())
        store.initialize()
        svc = PeopleService(store)
        rel = svc.create_relationship(OWNER, {"display_name": "Spy"})
        # Seed some data.
        req = svc.create_request(OWNER, rel["id"], {"body": "Test", "visibility": "shared_intent"})
        svc.accept_request(OWNER, req["id"])
        session = svc.create_one_on_one(OWNER, rel["id"], {"visibility": "shared_intent"})
        svc.add_agenda_item(OWNER, session["id"], {"body": "Agenda", "visibility": "shared_intent"})

        # Count rows before.
        before_count = self._row_count(store)
        svc.one_on_one_brief(OWNER, rel["id"])
        after_count = self._row_count(store)
        assert after_count == before_count, "Brief wrote to the encrypted store"

    def test_brief_writes_zero_rows_to_plain_db(self, service: PeopleService, tmp_path: Path) -> None:
        """The plain DB must not be written to during brief computation."""
        rel = service.create_relationship(OWNER, {"display_name": "Plain spy"})
        service.link_calendar_series(OWNER, rel["id"], "uid-spy", "cal-spy", "Spy series")

        db = _make_plain_db(tmp_path)
        _seed_plain_db(db,
            calendar_events=[{"id": "ev-spy", "uid": "uid-spy", "source_id": "cal-spy"}],
            meetings=[{"id": "m-spy", "title": "Spy meeting", "started_at": "2026-08-01T10:00:00", "calendar_event_id": "ev-spy"}],
            action_items=[{"id": "ai-spy", "meeting_id": "m-spy", "task": "Spy task"}],
            decisions=[],
        )

        conn = db._connection()
        before = self._plain_row_count(conn)
        service.one_on_one_brief(OWNER, rel["id"], db=db)
        after = self._plain_row_count(conn)
        assert after == before, "Brief wrote to the plain DB"

    @staticmethod
    def _row_count(store: EncryptedPeopleStore) -> int:
        """Count total rows in the encrypted store's records table."""
        import sqlite3 as _sqlite3
        conn = _sqlite3.connect(str(store.path))
        try:
            row = conn.execute("SELECT COUNT(*) FROM records").fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    @staticmethod
    def _plain_row_count(conn: sqlite3.Connection) -> dict[str, int]:
        """Count rows across all plain tables."""
        counts = {}
        for table in ("meetings", "action_items", "calendar_events", "decision_records"):
            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            counts[table] = row[0] if row else 0
        return counts


# -- F6 gate pin (acceptance 5) ------------------------------------------------


class TestF6GatePin:
    """F6: _require_access + leader_private items NEVER in the MCP response."""

    @pytest.fixture
    def people_service_mcp(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PeopleService:
        store = EncryptedPeopleStore(tmp_path / "f6.sqlite3", MemoryKeyStore())
        store.initialize()
        svc = PeopleService(store)
        monkeypatch.setattr(people_family, "build_people_service", lambda: svc)
        monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
        monkeypatch.delenv(people_family.ACCESS_ENV, raising=False)
        return svc

    def _call(self, name: str, arguments: dict[str, Any] | None = None) -> tuple[bool, Any]:
        response = server.handle_message({
            "jsonrpc": "2.0", "id": name, "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        })
        assert response is not None
        result = response["result"]
        return result["isError"], json.loads(result["content"][0]["text"])

    def test_leader_private_commitment_never_in_mcp_brief(
        self, people_service_mcp: PeopleService, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A planted leader_private record NEVER appears in the tool response."""
        svc = people_service_mcp
        rel = svc.create_relationship(OWNER, {"display_name": "F6 test"})
        # Shared commitment.
        req_shared = svc.create_request(OWNER, rel["id"], {"body": "Shared task", "visibility": "shared_intent"})
        svc.accept_request(OWNER, req_shared["id"])
        # Leader-private commitment (the planted record).
        req_private = svc.create_request(OWNER, rel["id"], {"body": "PRIVATE SECRET", "visibility": "leader_private"})
        svc.accept_request(OWNER, req_private["id"])
        # Leader-private agenda item.
        session = svc.create_one_on_one(OWNER, rel["id"], {"visibility": "shared_intent"})
        svc.add_agenda_item(OWNER, session["id"], {"body": "PRIVATE AGENDA", "visibility": "leader_private"})
        svc.add_agenda_item(OWNER, session["id"], {"body": "Shared agenda", "visibility": "shared_intent"})

        failed, brief = self._call("people.one_on_one.brief", {"relationship_id": rel["id"]})
        assert failed is False
        # The leader_private commitment must not appear.
        commitment_bodies = [c["body"] for c in brief.get("open_commitments", [])]
        assert "PRIVATE SECRET" not in commitment_bodies
        assert "Shared task" in commitment_bodies
        # The leader_private agenda item must not appear.
        agenda_bodies = [a["body"] for a in brief.get("agenda_items", [])]
        assert "PRIVATE AGENDA" not in agenda_bodies
        assert "Shared agenda" in agenda_bodies

    def test_f7_policy_block_present(
        self, people_service_mcp: PeopleService,
    ) -> None:
        """F7: the response carries the policy disclosure block."""
        svc = people_service_mcp
        rel = svc.create_relationship(OWNER, {"display_name": "F7 test"})
        failed, brief = self._call("people.one_on_one.brief", {"relationship_id": rel["id"]})
        assert failed is False
        assert "policy" in brief
        assert brief["policy"]["visibility"] == "shared_intent_only"
        assert brief["policy"]["employment_decisions"] == "prohibited"

    def test_access_off_refuses(
        self, people_service_mcp: PeopleService, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Access off -> tool refuses."""
        svc = people_service_mcp
        rel = svc.create_relationship(OWNER, {"display_name": "Off test"})
        monkeypatch.setenv(people_family.ACCESS_ENV, "off")
        failed, error = self._call("people.one_on_one.brief", {"relationship_id": rel["id"]})
        assert failed is True
        assert error.get("error") == "people_mcp_access_disabled"


# -- L2 honest refusal --------------------------------------------------------


class TestL2HonestRefusal:
    """Locked sidecar -> the brief refuses honestly, never renders half-true."""

    def test_locked_sidecar_raises(self) -> None:
        from holdspeak.services.people_service import PeopleUnavailable, UnavailablePeopleStore
        svc = PeopleService(UnavailablePeopleStore())
        with pytest.raises(PeopleUnavailable):
            svc.one_on_one_brief(OWNER, "nonexistent")


# -- F8 PREP-absent pin -------------------------------------------------------


class TestF8PrepAbsentPin:
    """F8: PREP rendered ONLY when person_label is present. Tested via door_service."""

    def test_calendar_event_item_no_prep_without_person(self) -> None:
        from holdspeak.services.door_service import DoorService
        from holdspeak.db.calendar_events import CalendarEvent

        event = CalendarEvent(
            id="ev-1", uid="uid-1", title="Test", starts_at="2026-08-01",
            ends_at="2026-08-01", location=None, meeting_url=None,
            last_seen_at=0.0, subscription_revision="r1",
        )
        item = DoorService._calendar_event_item(event)
        assert "person_label" not in item
        assert "person_relationship_id" not in item

    def test_calendar_event_item_has_prep_with_person(self) -> None:
        from holdspeak.services.door_service import DoorService
        from holdspeak.db.calendar_events import CalendarEvent

        event = CalendarEvent(
            id="ev-1", uid="uid-1", title="Test", starts_at="2026-08-01",
            ends_at="2026-08-01", location=None, meeting_url=None,
            last_seen_at=0.0, subscription_revision="r1",
        )
        person_index = {("uid-1", ""): ("Ewa", "rel-1")}
        item = DoorService._calendar_event_item(event, person_index=person_index)
        assert item["person_label"] == "Ewa"
        assert item["person_relationship_id"] == "rel-1"


# -- The 138 law pin -----------------------------------------------------------


class TestCommitmentTriadUntouched:
    """The brief NEVER enters action_items/cadence_*/caches/exports.

    The brief only READS action items by reference; the action_items table
    must remain untouched (no rows inserted, updated, or deleted).
    """

    def test_action_items_unchanged_after_brief(self, service: PeopleService, tmp_path: Path) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Triad"})
        service.link_calendar_series(OWNER, rel["id"], "uid-triad", "cal-triad", "Triad series")

        db = _make_plain_db(tmp_path)
        _seed_plain_db(db,
            calendar_events=[{"id": "ev-triad", "uid": "uid-triad", "source_id": "cal-triad"}],
            meetings=[{"id": "m-triad", "started_at": "2026-08-01T10:00:00", "calendar_event_id": "ev-triad"}],
            action_items=[
                {"id": "ai-triad-1", "meeting_id": "m-triad", "task": "Task 1", "status": "pending"},
                {"id": "ai-triad-2", "meeting_id": "m-triad", "task": "Task 2", "status": "completed"},
            ],
            decisions=[],
        )

        conn = db._connection()
        before = conn.execute("SELECT * FROM action_items ORDER BY id").fetchall()
        before_data = [(row["id"], row["task"], row["status"]) for row in before]

        service.one_on_one_brief(OWNER, rel["id"], db=db)

        after = conn.execute("SELECT * FROM action_items ORDER BY id").fetchall()
        after_data = [(row["id"], row["task"], row["status"]) for row in after]
        assert after_data == before_data, "Brief modified action_items"


class TestMeetingObserverRedaction:
    """HS-149 close-counsel finding 1: person_label never persists into
    plaintext pipeline_events via the MeetingService observer."""

    def test_person_label_redacted_from_result_summary(self):
        from dataclasses import dataclass, field
        from holdspeak.services.meeting_service import _MeetingPersonRedactor

        captured = []

        class Sink:
            def on_event(self, event):
                captured.append(event)

        @dataclass
        class FakeEvent:
            service: str = "MeetingService"
            method: str = "get_meeting"
            args_summary: str = "{}"
            result_summary: str = '{"id":"m1","person_label":"Ewa"}'
            error: object = None
            error_code: object = None

        _MeetingPersonRedactor(Sink()).on_event(FakeEvent())
        assert "Ewa" not in captured[0].result_summary
        assert "person_label" not in captured[0].result_summary
        assert "redacted" in captured[0].result_summary

    def test_untouched_when_no_projection(self):
        from dataclasses import dataclass
        from holdspeak.services.meeting_service import _MeetingPersonRedactor

        captured = []

        class Sink:
            def on_event(self, event):
                captured.append(event)

        @dataclass
        class FakeEvent:
            service: str = "MeetingService"
            method: str = "get_meeting"
            args_summary: str = "{}"
            result_summary: str = '{"id":"m1","title":"planning"}'
            error: object = None
            error_code: object = None

        _MeetingPersonRedactor(Sink()).on_event(FakeEvent())
        assert captured[0].result_summary == '{"id":"m1","title":"planning"}'
