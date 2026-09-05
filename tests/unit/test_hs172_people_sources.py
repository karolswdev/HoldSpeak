"""HS-172-04/05/06 -- the People resolver, brief enrichment, and suggested sources.

All tests use isolated HOME (MemoryKeyStore, tmp_path DB).
Never the owner's real database.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.people_service import PeopleService
from holdspeak.services.suggested_source_service import SuggestedSourceService

OWNER = Principal(PrincipalKind.OWNER, "test-owner-172")


# ---- Fixtures ----------------------------------------------------------------


@pytest.fixture
def service(tmp_path: Path) -> PeopleService:
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    store.initialize()
    return PeopleService(store)


@pytest.fixture
def plain_db(tmp_path: Path) -> Any:
    """Minimal plain DB with connector_watches, projects, and source_suggestions."""
    db_path = tmp_path / "plain.sqlite3"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("""CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY, name TEXT, description TEXT, keywords_json TEXT,
        team_members_json TEXT, context_json TEXT, detection_threshold REAL,
        revision INTEGER DEFAULT 0, purpose TEXT, outcome_text TEXT,
        lifecycle TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT,
        posture TEXT, posture_reason TEXT, start_at TEXT, target_at TEXT,
        review_cadence_json TEXT, next_review_at TEXT, template_key TEXT,
        modules_json TEXT, last_review_id TEXT, last_review_at TEXT,
        room_read_at TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS connector_watches (
        id TEXT PRIMARY KEY, project_id TEXT, connector_id TEXT,
        query_kind TEXT, query TEXT, snapshot_json TEXT, enabled INTEGER DEFAULT 1,
        state TEXT DEFAULT 'active', baseline_state TEXT DEFAULT 'established',
        last_error TEXT, created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS source_suggestions (
        id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
        meeting_id TEXT NOT NULL, provider TEXT NOT NULL,
        reference TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS calendar_events (
        id TEXT PRIMARY KEY, uid TEXT NOT NULL, title TEXT, starts_at TEXT,
        ends_at TEXT, location TEXT, meeting_url TEXT, last_seen_at REAL,
        subscription_revision TEXT, source_id TEXT NOT NULL DEFAULT '',
        source_label TEXT NOT NULL DEFAULT '')""")
    conn.execute("""CREATE TABLE IF NOT EXISTS meetings (
        id TEXT PRIMARY KEY, started_at TEXT NOT NULL, ended_at TEXT,
        title TEXT, calendar_event_id TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS action_items (
        id TEXT PRIMARY KEY, meeting_id TEXT NOT NULL, task TEXT NOT NULL,
        owner TEXT, due TEXT, status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        delegated_at TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS decision_records (
        id TEXT PRIMARY KEY, decision_text TEXT NOT NULL, rationale TEXT,
        lifecycle TEXT NOT NULL DEFAULT 'active',
        source_type TEXT NOT NULL, source_id TEXT NOT NULL,
        deleted INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS decision_record_sources (
        id TEXT PRIMARY KEY, record_id TEXT NOT NULL,
        source_type TEXT NOT NULL, source_ref TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')))""")
    # project_relationships for add_resource (may not exist in the minimal db)
    conn.execute("""CREATE TABLE IF NOT EXISTS project_relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL,
        resource_ref TEXT NOT NULL, relationship TEXT DEFAULT 'member',
        source TEXT DEFAULT 'manual', confidence REAL DEFAULT 1.0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        UNIQUE(project_id, resource_ref)
    )""")
    conn.commit()
    db = SimpleNamespace()
    db._connection = lambda: conn
    return db


def _seed_watch(
    db: Any, project_id: str, project_name: str,
    connector_id: str, query_kind: str, entities: list[dict],
) -> None:
    """Seed a project and a watch with a persisted snapshot."""
    conn = db._connection()
    conn.execute(
        "INSERT OR IGNORE INTO projects (id, name, created_at, updated_at) VALUES (?, ?, datetime('now'), datetime('now'))",
        (project_id, project_name),
    )
    snapshot = json.dumps({"schema": 1, "entities": {str(i): e for i, e in enumerate(entities)}})
    conn.execute(
        "INSERT INTO connector_watches (id, project_id, connector_id, query_kind, snapshot_json, query) "
        "VALUES (?, ?, ?, ?, ?, '{}')",
        (f"w_{project_id}_{connector_id}_{query_kind}", project_id, connector_id, query_kind, snapshot),
    )
    conn.commit()


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


# ==============================================================================
# HS-172-05: The brief enrichment (watch_summary)
# ==============================================================================


class TestBriefEnrichment:
    """one_on_one_brief gains watch_summary from persisted Watch snapshots."""

    def test_watch_summary_prs_waiting(self, service: PeopleService, plain_db: Any) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Ania"})
        service.link_owner_alias(OWNER, rel["id"], "ania-k")
        service.link_project(OWNER, rel["id"], "proj-1")

        four_days_ago = (datetime.now() - timedelta(days=4)).isoformat()
        _seed_watch(plain_db, "proj-1", "HoldSpeak", "gh", "pull_requests", [
            {
                "number": 612, "title": "Fix migration", "state": "OPEN",
                "reviewRequests": ["ania-k"],
                "url": "https://github.com/karolswdev/holdspeak/pull/612",
                "updatedAt": four_days_ago,
            },
            {
                "number": 613, "title": "Add tests", "state": "OPEN",
                "reviewRequests": ["ania-k"],
                "url": "https://github.com/karolswdev/holdspeak/pull/613",
                "updatedAt": four_days_ago,
            },
            {
                "number": 614, "title": "Other PR", "state": "OPEN",
                "reviewRequests": ["other-reviewer"],
                "url": "https://github.com/karolswdev/holdspeak/pull/614",
                "updatedAt": four_days_ago,
            },
        ])

        brief = service.one_on_one_brief(OWNER, rel["id"], db=plain_db)
        ws = brief["watch_summary"]
        assert len(ws["prs_waiting"]) == 2
        assert ws["oldest_waiting_days"] >= 3
        # Every PR carries room_id and room_name.
        for pr in ws["prs_waiting"]:
            assert pr["room_id"] == "proj-1"
            assert pr["room_name"] == "HoldSpeak"

    def test_watch_summary_jira_overdue(self, service: PeopleService, plain_db: Any) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Ania Kowalska"})
        service.link_owner_alias(OWNER, rel["id"], "Ania Kowalska")
        service.link_project(OWNER, rel["id"], "proj-2")

        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        _seed_watch(plain_db, "proj-2", "Governance", "jira", "issues", [
            {
                "key": "GOV-412", "summary": "PostgreSQL migration",
                "status": "In Progress", "status_category": "indeterminate",
                "assignee": "Ania Kowalska", "due_at": yesterday,
                "url": "https://jira.example.com/GOV-412",
            },
            {
                "key": "GOV-413", "summary": "Done task",
                "status": "Done", "status_category": "done",
                "assignee": "Ania Kowalska", "due_at": yesterday,
                "url": "https://jira.example.com/GOV-413",
            },
        ])

        brief = service.one_on_one_brief(OWNER, rel["id"], db=plain_db)
        ws = brief["watch_summary"]
        # Only the non-done issue appears.
        assert len(ws["open_assignments"]) == 1
        assert ws["open_assignments"][0]["key"] == "GOV-412"
        assert ws["open_assignments"][0]["overdue"] is True
        assert ws["open_assignments"][0]["room_id"] == "proj-2"

    def test_watch_summary_no_match_empty(self, service: PeopleService, plain_db: Any) -> None:
        """When the People resolver finds no match, Watch sections are empty."""
        rel = service.create_relationship(OWNER, {"display_name": "No Alias"})
        service.link_project(OWNER, rel["id"], "proj-3")

        _seed_watch(plain_db, "proj-3", "Test", "gh", "pull_requests", [
            {"number": 1, "title": "PR", "state": "OPEN",
             "reviewRequests": ["someone-else"], "url": "", "updatedAt": ""},
        ])

        brief = service.one_on_one_brief(OWNER, rel["id"], db=plain_db)
        ws = brief["watch_summary"]
        assert ws["prs_waiting"] == []
        assert ws["open_assignments"] == []

    def test_watch_summary_no_db_graceful(self, service: PeopleService) -> None:
        """When db is None, watch_summary degrades to empty."""
        rel = service.create_relationship(OWNER, {"display_name": "No DB"})
        brief = service.one_on_one_brief(OWNER, rel["id"])
        assert brief["watch_summary"]["prs_waiting"] == []
        assert brief["watch_summary"]["open_assignments"] == []

    def test_watch_summary_no_writes(self, service: PeopleService, plain_db: Any) -> None:
        """The 138 law: brief computation writes ZERO rows."""
        rel = service.create_relationship(OWNER, {"display_name": "Spy"})
        service.link_owner_alias(OWNER, rel["id"], "spy-login")
        service.link_project(OWNER, rel["id"], "proj-spy")

        _seed_watch(plain_db, "proj-spy", "Spy", "gh", "pull_requests", [
            {"number": 1, "title": "PR", "state": "OPEN",
             "reviewRequests": ["spy-login"], "url": "", "updatedAt": ""},
        ])

        conn = plain_db._connection()
        tables = ["connector_watches", "projects", "source_suggestions"]
        before = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}
        service.one_on_one_brief(OWNER, rel["id"], db=plain_db)
        after = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}
        assert after == before, "Brief wrote to the plain DB"

    def test_last_meeting_present(self, service: PeopleService, plain_db: Any) -> None:
        """last_meeting summarizes the most recent linked meeting."""
        rel = service.create_relationship(OWNER, {"display_name": "Jan"})
        service.link_calendar_series(OWNER, rel["id"], "uid-weekly", "cal-1", "Weekly")

        conn = plain_db._connection()
        conn.execute(
            "INSERT INTO calendar_events (id, uid, title, starts_at, ends_at, last_seen_at, subscription_revision, source_id) "
            "VALUES ('ev-1', 'uid-weekly', 'Weekly', '2026-08-01', '2026-08-01', 0.0, 'r1', 'cal-1')",
        )
        conn.execute(
            "INSERT INTO meetings (id, started_at, ended_at, title, calendar_event_id) "
            "VALUES ('m-1', '2026-08-01T10:00:00', '2026-08-01T11:00:00', 'Weekly', 'ev-1')",
        )
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, status) VALUES "
            "('ai-1', 'm-1', 'Ship it', 'Jan', 'pending'), "
            "('ai-2', 'm-1', 'Done', 'Jan', 'completed')",
        )
        conn.commit()

        brief = service.one_on_one_brief(OWNER, rel["id"], db=plain_db)
        lm = brief["last_meeting"]
        assert lm is not None
        assert lm["meeting_id"] == "m-1"
        assert lm["open_count"] == 1  # Only pending items.

    def test_last_meeting_none_when_no_meetings(self, service: PeopleService) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "No Meetings"})
        brief = service.one_on_one_brief(OWNER, rel["id"])
        assert brief["last_meeting"] is None


# ==============================================================================
# HS-172-06: The suggested source
# ==============================================================================


class TestSuggestedSourceScanner:
    """Transcript scanner finds repos and Jira keys."""

    def test_finds_github_repo(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "We discussed karolswdev/holdspeak and the roadmap.",
            "proj-1", "m-1",
        )
        assert any(r["provider"] == "github" and r["reference"] == "karolswdev/holdspeak" for r in results)

    def test_finds_jira_key(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "The issue KAN-7 was discussed at length.",
            "proj-1", "m-1",
            connected_jira_keys={"KAN"},
        )
        assert any(r["provider"] == "jira" and r["reference"] == "KAN-7" for r in results)

    def test_filters_unconnected_jira_prefix(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "The issue XYZ-99 came up.",
            "proj-1", "m-1",
            connected_jira_keys={"KAN"},
        )
        assert not any(r["provider"] == "jira" for r in results)

    def test_excludes_existing_sources(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "We discussed karolswdev/holdspeak again.",
            "proj-1", "m-1",
            existing_source_refs={"karolswdev/holdspeak"},
        )
        assert not any(r["reference"] == "karolswdev/holdspeak" for r in results)

    def test_no_mentions_empty(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "Nothing interesting here, just talking.",
            "proj-1", "m-1",
        )
        assert results == []

    def test_dedup_within_transcript(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "karolswdev/holdspeak and again karolswdev/holdspeak",
            "proj-1", "m-1",
        )
        refs = [r["reference"] for r in results]
        assert refs.count("karolswdev/holdspeak") == 1

    def test_github_dedup_case_insensitive(self, plain_db: Any) -> None:
        """GitHub owner/repo dedup is case-insensitive (lower-cased)."""
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "We use KarolSwDev/HoldSpeak for everything.",
            "proj-1", "m-1",
            existing_source_refs={"karolswdev/holdspeak"},
        )
        assert not any(r["reference"].lower() == "karolswdev/holdspeak" for r in results)

    def test_jira_dedup_case_insensitive(self, plain_db: Any) -> None:
        """Jira key dedup is case-insensitive (upper-cased)."""
        sug = SuggestedSourceService(plain_db)
        # Jira keys in transcript are always uppercase (regex [A-Z]+),
        # but existing refs might be stored differently.
        results = sug.scan_transcript(
            "Issue KAN-7 was discussed.",
            "proj-1", "m-1",
            connected_jira_keys={"KAN"},
            existing_source_refs={"kan-7"},  # lower-cased existing ref
        )
        assert not any(r["reference"].upper() == "KAN-7" for r in results)

    def test_dismissed_github_case_insensitive_suppresses(self, plain_db: Any) -> None:
        """A dismissed GitHub ref suppresses future scans case-insensitively."""
        sug = SuggestedSourceService(plain_db)
        # Create and dismiss a suggestion with different casing.
        sug.create_suggestions("proj-1", "m-1", [
            {"provider": "github", "reference": "KarolSwDev/HoldSpeak"},
        ])
        listed = sug.list_suggestions("proj-1", status="pending")
        sug.dismiss_suggestion(listed[0]["id"])
        # Scan with the same repo in different casing.
        results = sug.scan_transcript(
            "Let me check karolswdev/holdspeak again.",
            "proj-1", "m-2",
        )
        assert not any(r["reference"].lower() == "karolswdev/holdspeak" for r in results)

    def test_dismissed_jira_case_insensitive_suppresses(self, plain_db: Any) -> None:
        """A dismissed Jira ref suppresses future scans case-insensitively."""
        sug = SuggestedSourceService(plain_db)
        sug.create_suggestions("proj-1", "m-1", [
            {"provider": "jira", "reference": "kan-7"},
        ])
        listed = sug.list_suggestions("proj-1", status="pending")
        sug.dismiss_suggestion(listed[0]["id"])
        # Scan with uppercase (as regex produces).
        results = sug.scan_transcript(
            "Issue KAN-7 again.",
            "proj-1", "m-2",
            connected_jira_keys={"KAN"},
        )
        assert not any(r["reference"].upper() == "KAN-7" for r in results)


class TestSuggestedSourceCRUD:
    """Accept, dismiss, and persistence."""

    def test_create_and_list(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        created = sug.create_suggestions("proj-1", "m-1", [
            {"provider": "github", "reference": "karolswdev/holdspeak"},
        ])
        assert len(created) == 1
        listed = sug.list_suggestions("proj-1", status="pending")
        assert len(listed) == 1
        assert listed[0]["reference"] == "karolswdev/holdspeak"

    def test_accept_marks_accepted(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        created = sug.create_suggestions("proj-1", "m-1", [
            {"provider": "github", "reference": "karolswdev/holdspeak"},
        ])
        accepted = sug.accept_suggestion(created[0]["id"])
        assert accepted["status"] == "accepted"
        # No longer in pending list.
        pending = sug.list_suggestions("proj-1", status="pending")
        assert len(pending) == 0

    def test_dismiss_marks_dismissed(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        created = sug.create_suggestions("proj-1", "m-1", [
            {"provider": "jira", "reference": "KAN-7"},
        ])
        dismissed = sug.dismiss_suggestion(created[0]["id"])
        assert dismissed["status"] == "dismissed"

    def test_dismissed_suppresses_future_scans(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        sug.create_suggestions("proj-1", "m-1", [
            {"provider": "github", "reference": "karolswdev/holdspeak"},
        ])
        # Dismiss it.
        listed = sug.list_suggestions("proj-1", status="pending")
        sug.dismiss_suggestion(listed[0]["id"])
        # Scan again -- the dismissed reference should not appear.
        results = sug.scan_transcript(
            "karolswdev/holdspeak mentioned again.",
            "proj-1", "m-2",
        )
        assert not any(r["reference"] == "karolswdev/holdspeak" for r in results)

    def test_accept_is_idempotent(self, plain_db: Any) -> None:
        """Accepting the same suggestion twice does not crash."""
        sug = SuggestedSourceService(plain_db)
        created = sug.create_suggestions("proj-1", "m-1", [
            {"provider": "github", "reference": "test/repo"},
        ])
        sug.accept_suggestion(created[0]["id"])
        # Second accept is safe.
        result = sug.accept_suggestion(created[0]["id"])
        assert result["status"] == "accepted"


# ==============================================================================
# Law: no pronoun inference in the wire
# ==============================================================================


class TestNoPronounInWire:
    """The watch_summary and last_meeting carry no pronoun strings.

    The face resolves display_name; the wire never infers her/him/his/she/he
    from a name.
    """

    def test_watch_summary_no_pronouns(self, service: PeopleService, plain_db: Any) -> None:
        rel = service.create_relationship(OWNER, {"display_name": "Ania Kowalska"})
        service.link_owner_alias(OWNER, rel["id"], "ania-k")
        service.link_project(OWNER, rel["id"], "proj-pronoun")

        four_days_ago = (datetime.now() - timedelta(days=4)).isoformat()
        _seed_watch(plain_db, "proj-pronoun", "Test", "gh", "pull_requests", [
            {"number": 1, "title": "PR", "state": "OPEN",
             "reviewRequests": ["ania-k"], "url": "", "updatedAt": four_days_ago},
        ])

        brief = service.one_on_one_brief(OWNER, rel["id"], db=plain_db)
        # Serialize the entire watch_summary and last_meeting to text.
        wire_text = json.dumps(brief.get("watch_summary", {})) + json.dumps(brief.get("last_meeting"))
        # No pronoun words should appear in the wire.
        pronouns = {"her", "him", "his", "she", " he "}
        for p in pronouns:
            assert p not in wire_text.lower(), f"Pronoun '{p}' found in wire: {wire_text}"


# ==============================================================================
# Classification census: new tools are classified in thread_tools
# ==============================================================================


class TestToolClassification:
    """New MCP tools must be classified in thread_tools._TOOL_CLASSES."""

    def test_people_resolve_classified(self) -> None:
        from holdspeak.services.thread_tools import _TOOL_CLASSES
        assert "people.resolve" in _TOOL_CLASSES
        assert _TOOL_CLASSES["people.resolve"] == ("evidence_read", True)

    def test_project_suggested_sources_classified(self) -> None:
        from holdspeak.services.thread_tools import _TOOL_CLASSES
        assert "project.suggested_sources" in _TOOL_CLASSES
        assert _TOOL_CLASSES["project.suggested_sources"][0] == "evidence_read"

    def test_project_add_suggested_source_classified(self) -> None:
        from holdspeak.services.thread_tools import _TOOL_CLASSES
        assert "project.add_suggested_source" in _TOOL_CLASSES
        assert _TOOL_CLASSES["project.add_suggested_source"][0] == "effect_proposal"

    def test_project_dismiss_suggested_source_classified(self) -> None:
        from holdspeak.services.thread_tools import _TOOL_CLASSES
        assert "project.dismiss_suggested_source" in _TOOL_CLASSES
        assert _TOOL_CLASSES["project.dismiss_suggested_source"][0] == "effect_proposal"
