"""HS-169-04 -- the wire for the four questions.

Characterization tests over a fixture desk: needsYou rows from
real-shaped entities, health derivation, sinceRead phrases, decisions
via the meeting link, the read marker route, the meeting template
retirement, branch_ci compile + snapshot, and MCP parity.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import server
from holdspeak.mcp.families import project as project_family
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.project_service import ProjectService
from holdspeak.services.watch_sources import GitHubWatchSource
from holdspeak.services.errors import ValidationError

OWNER = Principal(PrincipalKind.OWNER, "wire-owner")


# ── fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "wire.db")
    yield database
    reset_database()


def _seed_project(
    db: Database,
    project_id: str = "proj-wire-1",
    name: str = "Wire Test",
    target_at: str | None = None,
) -> str:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, ?, "
            "'2026-09-01T00:00:00', '2026-09-04T10:00:00')",
            (project_id, name, target_at),
        )
    return project_id


def _seed_watch(
    db: Database,
    project_id: str,
    *,
    watch_id: str = "watch-gh-prs",
    connector_id: str = "gh",
    query_kind: str = "pull_requests",
    query: dict[str, Any] | None = None,
    snapshot: list[dict[str, Any]] | dict[str, Any] | None = None,
    last_success_at: str | None = "2026-09-04T10:00:00",
    last_error: str | None = None,
    enabled: bool = True,
) -> str:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, "
            " created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
            (
                watch_id,
                connector_id,
                query_kind,
                f"{connector_id} {query_kind}",
                json.dumps(query or {}, sort_keys=True),
                json.dumps(snapshot or []),
                int(enabled),
                last_success_at,
                last_error,
                project_id,
            ),
        )
    return watch_id


def _seed_meeting_link(
    db: Database,
    project_id: str,
    meeting_id: str,
) -> None:
    """Seed a meeting row + meeting-project link."""
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, title, started_at, created_at) "
            "VALUES (?, ?, datetime('now'), datetime('now'))",
            (meeting_id, f"Meeting {meeting_id}"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO meeting_projects "
            "(meeting_id, project_id, source, confidence, detected_at) "
            "VALUES (?, ?, 'manual', 1.0, datetime('now'))",
            (meeting_id, project_id),
        )


def _seed_decision_record(
    db: Database,
    record_id: str,
    meeting_id: str,
    decision_text: str = "Use acli for Jira",
    *,
    decisions_id: str | None = None,
) -> str:
    """Seed a decision record with a meeting source.

    *decisions_id*: the id of the corresponding row in the ``decisions``
    table.  When given, a ``decisions`` row is seeded and
    ``decision_records.source_id`` points to it (HS-172-03 join path:
    ``decision_records.source_id = decisions.id``).  Callers that verify
    commitments MUST supply this so the ``_read_room_commitments`` join
    can resolve.
    """
    with db._connection() as conn:
        # If a decisions row is expected, seed it.
        if decisions_id:
            conn.execute(
                "INSERT OR IGNORE INTO meetings "
                "(id, title, started_at, created_at) "
                "VALUES (?, 'Seeded meeting', datetime('now'), datetime('now'))",
                (meeting_id,),
            )
            conn.execute(
                "INSERT OR IGNORE INTO decisions "
                "(id, text, decided_at, source_artifact_id, "
                " source_meeting_id, created_at, updated_at, last_modified) "
                "VALUES (?, ?, datetime('now'), ?, ?, "
                " datetime('now'), datetime('now'), datetime('now'))",
                (decisions_id, decision_text, f"art-{decisions_id}", meeting_id),
            )

        source_id = decisions_id or meeting_id
        conn.execute(
            "INSERT INTO decision_records "
            "(id, decision_text, source_type, source_id, lifecycle, "
            " created_at, updated_at) "
            "VALUES (?, ?, 'meeting', ?, 'active', datetime('now'), datetime('now'))",
            (record_id, decision_text, source_id),
        )
        conn.execute(
            "INSERT INTO decision_record_sources "
            "(id, record_id, source_type, source_ref, created_at) "
            "VALUES (?, ?, 'meeting', ?, datetime('now'))",
            (f"src-{record_id}", record_id, meeting_id),
        )
    return record_id


def _seed_commitment(
    db: Database,
    commitment_id: str,
    decision_id: str,
    text: str = "Review PR #612",
    due_at: str | None = "2026-09-10",
    owner: str | None = "karol",
) -> str:
    """Seed a commitment for a decision."""
    with db._connection() as conn:
        # Need an action item first; also need the dummy meeting
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, title, started_at, created_at) "
            "VALUES ('dummy-meeting', 'Dummy', datetime('now'), datetime('now'))"
        )
        conn.execute(
            "INSERT OR IGNORE INTO action_items "
            "(id, task, owner, due, status, meeting_id, created_at) "
            "VALUES (?, ?, ?, ?, 'open', 'dummy-meeting', datetime('now'))",
            (f"ai-{commitment_id}", text, owner, due_at),
        )
        conn.execute(
            "INSERT INTO decision_commitments "
            "(id, decision_id, action_item_id, owner, due_at, status, "
            " created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'open', datetime('now'), datetime('now'))",
            (commitment_id, decision_id, f"ai-{commitment_id}", owner, due_at),
        )
    return commitment_id


def _seed_project_change(
    db: Database,
    project_id: str,
    change_kind: str = "project.updated",
    summary: dict[str, Any] | None = None,
    created_at: str | None = None,
) -> None:
    import uuid
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO project_changes "
            "(id, project_id, project_revision, change_kind, summary_json, created_at) "
            "VALUES (?, ?, 1, ?, ?, ?)",
            (
                f"chg-{uuid.uuid4().hex[:8]}",
                project_id,
                change_kind,
                json.dumps(summary or {}),
                created_at or datetime.now().isoformat(),
            ),
        )


# ── needsYou ──────────────────────────────────────────────────────────

class TestNeedsYou:
    """3 needsYou rows from real-shaped entities, ordered by severity."""

    def test_three_needs_you_rows_ordered_by_severity(self, db: Database) -> None:
        project_id = _seed_project(db)
        now = datetime.now()

        # 1. PR with owner in reviewRequests (warning), aged 3 days
        _seed_watch(db, project_id, watch_id="w-pr", connector_id="gh",
                    query_kind="pull_requests",
                    query={"repository": "acme/app"},
                    snapshot=[{
                        "number": 612, "title": "Rig settles animations",
                        "url": "https://github.com/acme/app/pull/612",
                        "state": "OPEN", "isDraft": False,
                        "reviewRequests": ["wire-owner"],
                        "reviewDecision": "REVIEW_REQUIRED",
                        "checks": "passing",
                        "updatedAt": (now - timedelta(days=3)).isoformat(),
                    }])

        # Seed a provider connection so the owner login resolves
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO watch_provider_connections "
                "(id, provider_id, external_connection_ref, state, "
                " created_at, updated_at) "
                "VALUES ('wpc-gh', 'github', 'wire-owner', 'connected', "
                " datetime('now'), datetime('now'))"
            )

        # 2. branch_ci failure (danger)
        _seed_watch(db, project_id, watch_id="w-ci", connector_id="gh",
                    query_kind="branch_ci",
                    query={"repository": "acme/app", "base": "main"},
                    snapshot=[{
                        "conclusion": "failure", "status": "completed",
                        "name": "CI", "url": "https://github.com/acme/app/actions/1",
                        "updated_at": now.isoformat(), "branch": "main",
                    }])

        # 3. Jira overdue issue (danger)
        _seed_watch(db, project_id, watch_id="w-jira", connector_id="jira",
                    query_kind="issues",
                    query={"projects": ["KAN"]},
                    snapshot=[{
                        "key": "KAN-42", "summary": "Update docs",
                        "url": "https://jira.example.com/KAN-42",
                        "due_at": (now - timedelta(days=2)).isoformat(),
                    }])

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)

        needs = room["needsYou"]
        assert needs["state"] == "ok"
        items = needs["items"]
        assert len(items) == 3

        # danger items first (CI + Jira overdue), then warning (PR review)
        severities = [i["severity"] for i in items]
        assert severities[0] == "danger"
        assert severities[1] == "danger"
        assert severities[2] == "warning"

        # Verify CI row title
        ci_rows = [i for i in items if "CI failing" in i["title"]]
        assert len(ci_rows) == 1
        assert ci_rows[0]["verb"] == "open"

        # Verify PR review row
        pr_rows = [i for i in items if "612" in i["title"]]
        assert len(pr_rows) == 1
        assert "WAITING ON YOUR REVIEW" in pr_rows[0]["why"]

        # Verify Jira overdue row
        jira_rows = [i for i in items if "KAN-42" in i["title"]]
        assert len(jira_rows) == 1
        assert "OVERDUE" in jira_rows[0]["why"]


# ── health ────────────────────────────────────────────────────────────

class TestHealth:
    """Health derivation: AT RISK with reason, and ON TRACK."""

    def test_at_risk_reason_overdue(self, db: Database) -> None:
        project_id = _seed_project(db)
        now = datetime.now()

        _seed_watch(db, project_id, watch_id="w-jira-h", connector_id="jira",
                    query_kind="issues",
                    snapshot=[
                        {"key": "X-1", "due_at": (now - timedelta(days=1)).isoformat()},
                        {"key": "X-2", "due_at": (now - timedelta(days=2)).isoformat()},
                        {"key": "X-3", "due_at": (now - timedelta(days=3)).isoformat()},
                    ])

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        health = room["health"]
        assert health["state"] == "ok"
        assert health["state"] == "ok"  # section state
        assert health["inputs"]["overdue"] == 3
        assert health["assessment"] == "at_risk"
        assert health["reason"] == "3 OVERDUE"

    def test_on_track_when_nothing_wrong(self, db: Database) -> None:
        project_id = _seed_project(db)

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        health = room["health"]
        assert health["state"] == "ok"  # section state
        assert health["assessment"] == "on_track"
        assert health["reason"] is None
        assert health["inputs"]["overdue"] == 0
        assert health["inputs"]["ciFailing"] is False

    def test_ci_failing_is_at_risk(self, db: Database) -> None:
        project_id = _seed_project(db)
        _seed_watch(db, project_id, watch_id="w-ci-h", connector_id="gh",
                    query_kind="branch_ci",
                    snapshot=[{"conclusion": "failure", "status": "completed",
                               "name": "CI", "branch": "main"}])

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        health = room["health"]
        assert health["assessment"] == "at_risk"
        assert health["inputs"]["ciFailing"] is True
        assert health["reason"] == "CI RED"

    def test_target_passed_is_at_risk(self, db: Database) -> None:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        project_id = _seed_project(db, target_at=yesterday)

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        health = room["health"]
        assert health["assessment"] == "at_risk"
        assert health["inputs"]["targetPassed"] is True
        assert health["reason"] == "TARGET PASSED"


# ── sinceRead ─────────────────────────────────────────────────────────

class TestSinceRead:
    """sinceRead groups phrases and the no-raw-kind guard."""

    def test_since_read_groups_with_phrases(self, db: Database) -> None:
        project_id = _seed_project(db)
        # Set read marker to yesterday
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        db.projects.set_room_read_at(project_id, yesterday)

        # Seed changes after the read marker
        _seed_project_change(db, project_id, "project.updated",
                             {"action": "renamed"})
        _seed_project_change(db, project_id, "project.resource.linked",
                             {"name": "note:abc"})

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        since = room["sinceRead"]
        assert since["state"] == "ok"
        assert since["readAt"] == yesterday
        assert len(since["groups"]) > 0

    def test_no_raw_kind_leaks_into_phrases(self, db: Database) -> None:
        """Guard: no raw kind string (snake_case with underscores) in phrases."""
        from holdspeak.services.project_service import ProjectService as PS
        for kind, phrase in PS._CHANGE_KIND_PHRASES.items():
            # Raw kinds have underscores; phrases should not
            assert "_" not in phrase, f"Raw kind leaked: {kind} -> {phrase}"

    def test_empty_since_read_when_no_marker(self, db: Database) -> None:
        project_id = _seed_project(db)
        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        since = room["sinceRead"]
        assert since["state"] == "ok"
        assert since["readAt"] is None
        assert since["groups"] == []


# ── decisions via meeting link ────────────────────────────────────────

class TestDecisions:
    """Decisions and commitments via the meeting link."""

    def test_decisions_from_linked_meeting(self, db: Database) -> None:
        project_id = _seed_project(db)
        meeting_id = "mtg-wire-1"
        _seed_meeting_link(db, project_id, meeting_id)
        _seed_decision_record(db, "dr-1", meeting_id, "Use acli for Jira")

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        decisions = room["decisions"]
        assert decisions["state"] == "ok"
        assert len(decisions["items"]) == 1
        assert decisions["items"][0]["text"] == "Use acli for Jira"

    def test_no_decisions_when_no_meeting_linked(self, db: Database) -> None:
        project_id = _seed_project(db)
        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        decisions = room["decisions"]
        assert decisions["state"] == "ok"
        assert decisions["items"] == []

    def test_commitments_via_decision(self, db: Database) -> None:
        project_id = _seed_project(db)
        meeting_id = "mtg-wire-2"
        _seed_meeting_link(db, project_id, meeting_id)
        # HS-172-03: the commitment join walks
        # decision_records.source_id -> decisions.id ->
        # decision_commitments.decision_id, so the seed must supply
        # a decisions_id and the commitment must reference it.
        _seed_decision_record(db, "dr-2", meeting_id, "Ship it",
                              decisions_id="dec-2")
        _seed_commitment(db, "cmt-1", "dec-2", "Review PR #612",
                         due_at="2026-09-10", owner="karol")

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        commitments = room["commitments"]
        assert commitments["state"] == "ok"
        assert len(commitments["items"]) == 1
        assert commitments["items"][0]["text"] == "Review PR #612"
        assert commitments["items"][0]["owner"] == "karol"


# ── read marker ───────────────────────────────────────────────────────

class TestReadMarker:
    """The read marker route round trip."""

    def test_mark_room_read_round_trip(self, db: Database) -> None:
        project_id = _seed_project(db)
        svc = ProjectService(db)

        # Initially null
        room = svc.room(OWNER, project_id)
        assert room["sinceRead"]["readAt"] is None

        # Mark read
        result = svc.mark_room_read(OWNER, project_id)
        assert "readAt" in result
        assert result["readAt"] is not None

        # Verify it persists
        room = svc.room(OWNER, project_id)
        assert room["sinceRead"]["readAt"] is not None


# ── meeting template retirement ───────────────────────────────────────

class TestMeetingTemplateRetired:
    """The meeting template absent from suggestions on a fresh desk."""

    def test_no_meeting_template_in_suggestions(self, db: Database) -> None:
        """A fresh suggest() call never offers a meetings Watch."""
        from holdspeak.services.project_setup_service import ProjectSetupService
        svc = ProjectSetupService(db)

        # Start a setup session
        session = svc.start_setup(OWNER)
        session_id = session["id"]

        # Answer the outcome question
        svc.answer(OWNER, session_id, "outcome", {
            "text": "Ship the Q4 platform",
        })

        # Get suggestions — returns a list of proposals
        proposals = svc.suggest(OWNER, session_id)

        # No proposal should have kind=meetings
        meetings_specific = [
            p for p in proposals
            if (p.get("spec") or {}).get("subject", {}).get("kind") == "meetings"
        ]
        assert len(meetings_specific) == 0, \
            "The meeting template must not be offered (HS-169-04)"


# ── existing meeting watch plainReason ────────────────────────────────

class TestMeetingWatchPlainReason:
    """An existing meeting watch reports its plainReason."""

    def test_native_meeting_watch_reports_cant_check(self, db: Database) -> None:
        project_id = _seed_project(db)
        _seed_watch(db, project_id, watch_id="w-mtg", connector_id="native",
                    query_kind="meetings",
                    snapshot=[],
                    last_error=None)

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        sources = room["sources"]
        assert sources["state"] == "ok"
        mtg_sources = [s for s in sources["items"] if s["provider"] == "native"]
        assert len(mtg_sources) == 1
        assert mtg_sources[0]["state"] == "cant_check"
        assert mtg_sources[0]["plainReason"] == "No local adapter for meeting activity yet"


# ── branch_ci ─────────────────────────────────────────────────────────

class TestBranchCi:
    """branch_ci compile + snapshot with a faked gh."""

    def test_branch_ci_compile(self) -> None:
        """The branch_ci template compiles to a valid WatchSpec@1."""
        from holdspeak.github_templates import compile as gh_compile
        spec = gh_compile("watch.github.branch_ci", "acme/app")
        assert spec["subject"]["kind"] == "branch_ci"
        assert spec["subject"]["query"]["base"] == "main"
        assert spec["name"] == "CI"

    def test_branch_ci_snapshot_with_faked_gh(self) -> None:
        """branch_ci snapshot parses gh run list output."""
        captured = {}

        def runner(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            captured["command"] = command
            return subprocess.CompletedProcess(command, 0, json.dumps([{
                "conclusion": "failure",
                "status": "completed",
                "name": "CI",
                "url": "https://github.com/acme/app/actions/runs/1",
                "updatedAt": "2026-09-04T10:00:00Z",
                "headBranch": "main",
            }]), "")

        source = GitHubWatchSource(runner=runner)
        entities = source.snapshot(
            OWNER, query_kind="branch_ci",
            query={"repository": "acme/app", "base": "main"},
        )
        # Verify command shape
        cmd = captured["command"]
        assert cmd[:3] == ["gh", "run", "list"]
        assert "--branch" in cmd
        assert "main" in cmd
        assert "--limit" in cmd
        assert "1" in cmd

        # Verify entity normalization
        assert len(entities) == 1
        assert entities[0]["conclusion"] == "failure"
        assert entities[0]["branch"] == "main"
        assert entities[0]["url"] == "https://github.com/acme/app/actions/runs/1"

    def test_branch_ci_normalize_snapshot_with_url(self) -> None:
        """HS-169-05 law: branch_ci entities carry a run id derived from
        the URL, so normalize_snapshot validates them (the baseline_watch
        path that every default CI watch hits)."""
        from holdspeak.services.reaction_service import normalize_snapshot

        def runner(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, json.dumps([{
                "conclusion": "success",
                "status": "completed",
                "name": "CI",
                "url": "https://github.com/acme/app/actions/runs/42",
                "updatedAt": "2026-09-04T10:00:00Z",
                "headBranch": "main",
            }]), "")

        source = GitHubWatchSource(runner=runner)
        entities = source.snapshot(
            OWNER, query_kind="branch_ci",
            query={"repository": "acme/app", "base": "main"},
        )
        assert len(entities) == 1
        assert entities[0]["id"] == "42", (
            f"Run id must be derived from the URL; got: {entities[0].get('id')}"
        )
        # normalize_snapshot must not raise
        result = normalize_snapshot("gh", entities)
        assert "42" in result["entities"]

    def test_branch_ci_normalize_snapshot_fallback_id(self) -> None:
        """HS-169-05 law: when the URL has no run id, the entity id falls
        back to {base}-{idx}."""
        from holdspeak.services.reaction_service import normalize_snapshot

        def runner(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, json.dumps([{
                "conclusion": "success",
                "status": "completed",
                "name": "CI",
                "url": "",
                "updatedAt": "2026-09-04T10:00:00Z",
                "headBranch": "develop",
            }]), "")

        source = GitHubWatchSource(runner=runner)
        entities = source.snapshot(
            OWNER, query_kind="branch_ci",
            query={"repository": "acme/app", "base": "develop"},
        )
        assert len(entities) == 1
        assert entities[0]["id"] == "develop-0", (
            f"Fallback id must be base-idx; got: {entities[0].get('id')}"
        )
        result = normalize_snapshot("gh", entities)
        assert "develop-0" in result["entities"]

    def test_branch_ci_requires_repository(self) -> None:
        """branch_ci validates repository."""
        source = GitHubWatchSource(runner=lambda *a, **kw: None)
        with pytest.raises(ValidationError, match="owner/name"):
            source.snapshot(OWNER, query_kind="branch_ci",
                            query={"repository": "bad"})


# ── MCP parity ────────────────────────────────────────────────────────

class TestMcpParity:
    """MCP project.get_room returns the same shape as the service."""

    @pytest.fixture(autouse=True)
    def _wire_mcp(self, db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(project_family, "get_database", lambda: db)
        monkeypatch.setattr(
            server, "resolve_auth",
            lambda: SimpleNamespace(principal=OWNER),
        )
        monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "off")

    def test_room_shape_parity(self, db: Database) -> None:
        """Route shape == MCP shape for the same project."""
        project_id = _seed_project(db)
        svc = ProjectService(db)
        service_result = svc.room(OWNER, project_id)

        response = server.handle_message({
            "jsonrpc": "2.0", "id": "parity",
            "method": "tools/call",
            "params": {
                "name": "project.get_room",
                "arguments": {"project_id": project_id},
            },
        })
        assert response is not None
        result = response["result"]
        mcp_result = json.loads(result["content"][0]["text"])

        assert mcp_result == service_result, (
            "MCP project.get_room must return the same shape as ProjectService.room()"
        )

    def test_room_has_new_sections(self, db: Database) -> None:
        """The new HS-169-04 sections are present in the room response."""
        project_id = _seed_project(db)
        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)

        new_sections = ["needsYou", "sources", "health", "sinceRead",
                        "decisions", "commitments", "target"]
        for section in new_sections:
            assert section in room, f"Missing section: {section}"
            assert "state" in room[section], f"Section {section} has no state"


# ── sources ───────────────────────────────────────────────────────────

class TestSources:
    """Sources section with count tokens."""

    def test_zero_count_tokens_yield_clear(self, db: Database) -> None:
        """Zero-count tokens are omitted; a live source reads CLEAR (D5 law)."""
        project_id = _seed_project(db)
        # Empty snapshot = zero counts everywhere
        _seed_watch(db, project_id, watch_id="w-empty", connector_id="gh",
                    query_kind="pull_requests",
                    query={"repository": "acme/app"},
                    snapshot=[])

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        sources = room["sources"]
        assert sources["state"] == "ok"
        items = sources["items"]
        assert len(items) == 1
        # A live source with nothing to report shows CLEAR
        assert items[0]["tokens"] == ["CLEAR"]

    def test_source_host_egress(self, db: Database) -> None:
        """Each source row carries its host (egress chip)."""
        project_id = _seed_project(db)
        _seed_watch(db, project_id, connector_id="gh",
                    query_kind="pull_requests",
                    query={"repository": "acme/app"},
                    snapshot=[])

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        sources = room["sources"]
        assert sources["items"][0]["host"] == "github.com"

    def test_source_has_next_check_at(self, db: Database) -> None:
        """Each source item carries nextCheckAt from the watch."""
        project_id = _seed_project(db)
        next_eval = "2026-09-04T10:35:00"
        _seed_watch(db, project_id, connector_id="gh",
                    query_kind="pull_requests",
                    query={"repository": "acme/app"},
                    snapshot=[])
        # Set next_evaluation_at on the watch
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET next_evaluation_at = ? WHERE id = ?",
                (next_eval, "watch-gh-prs"),
            )

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        sources = room["sources"]
        assert sources["items"][0]["nextCheckAt"] == next_eval

    def test_room_top_level_next_check_at(self, db: Database) -> None:
        """Room top-level nextCheckAt = soonest non-null over live sources."""
        project_id = _seed_project(db)
        _seed_watch(db, project_id, watch_id="w-a", connector_id="gh",
                    query_kind="pull_requests",
                    query={"repository": "acme/app"},
                    snapshot=[])
        _seed_watch(db, project_id, watch_id="w-b", connector_id="gh",
                    query_kind="branch_ci",
                    query={"repository": "acme/app", "base": "main"},
                    snapshot=[])
        # Set different next_evaluation_at values
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET next_evaluation_at = ? WHERE id = ?",
                ("2026-09-04T11:00:00", "w-a"),
            )
            conn.execute(
                "UPDATE connector_watches SET next_evaluation_at = ? WHERE id = ?",
                ("2026-09-04T10:35:00", "w-b"),
            )

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        # Top-level is the soonest
        assert room["nextCheckAt"] == "2026-09-04T10:35:00"

    def test_room_next_check_at_null_when_no_watches(self, db: Database) -> None:
        """Room top-level nextCheckAt is null when no watches exist."""
        project_id = _seed_project(db)
        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        assert room["nextCheckAt"] is None

    def test_two_github_watches_one_repo_merged(self, db: Database) -> None:
        """Two GitHub watches on the same repo merge into one source item."""
        project_id = _seed_project(db)

        # Watch 1: OPEN PRS
        _seed_watch(db, project_id, watch_id="w-pr-merge",
                    connector_id="gh", query_kind="pull_requests",
                    query={"repository": "karolswdev/HoldSpeak", "state": "open"},
                    snapshot={"schema": 1, "entities": {
                        "500": {"id": "500", "title": "A PR", "state": "open",
                                "review_requests": [], "review_decision": "",
                                "checks": "passing", "updated_at": "2026-09-04T10:00:00Z"},
                    }},
                    last_success_at="2026-09-04T10:00:00")

        # Watch 2: CI on the same repo
        _seed_watch(db, project_id, watch_id="w-ci-merge",
                    connector_id="gh", query_kind="branch_ci",
                    query={"repository": "karolswdev/HoldSpeak", "base": "main"},
                    snapshot={"schema": 1, "entities": {
                        "1": {"id": "1", "conclusion": "success", "status": "completed",
                              "name": "CI", "branch": "main"},
                    }},
                    last_success_at="2026-09-04T10:05:00")

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        sources = room["sources"]
        assert sources["state"] == "ok"

        # ONE item, not two
        gh_items = [s for s in sources["items"] if s["provider"] == "github"]
        assert len(gh_items) == 1
        item = gh_items[0]

        # Both watchIds present
        assert "w-pr-merge" in item["watchIds"]
        assert "w-ci-merge" in item["watchIds"]
        assert len(item["watchIds"]) == 2

        # Tokens from both watches merged
        assert "1 OPEN PRS" in item["tokens"]
        assert "CI GREEN" in item["tokens"]

        # checkedAt is the latest
        assert item["checkedAt"] == "2026-09-04T10:05:00"

        # sources.count reflects the group count
        assert sources["count"] == 1

    def test_pr_checks_failing_and_ci_green_both_show(self, db: Database) -> None:
        """A PR watch with a failing check + a branch_ci success in one
        scope must show both tokens: CHECKS FAILING (PR-level) and
        CI GREEN (base-branch). Two different facts, never collapsed."""
        project_id = _seed_project(db)

        # Watch 1: PR with failing checks
        _seed_watch(db, project_id, watch_id="w-pr-fail",
                    connector_id="gh", query_kind="pull_requests",
                    query={"repository": "karolswdev/HoldSpeak", "state": "open"},
                    snapshot={"schema": 1, "entities": {
                        "526": {"id": "526", "title": "Footer fix", "state": "open",
                                "review_requests": [], "review_decision": "",
                                "checks": "failing",
                                "updated_at": "2026-09-03T10:00:00Z"},
                        "527": {"id": "527", "title": "Docs update", "state": "open",
                                "review_requests": [], "review_decision": "",
                                "checks": "passing",
                                "updated_at": "2026-09-03T11:00:00Z"},
                        "528": {"id": "528", "title": "Rig settle", "state": "open",
                                "review_requests": [], "review_decision": "",
                                "checks": "passing",
                                "updated_at": "2026-09-03T12:00:00Z"},
                    }})

        # Watch 2: branch_ci success on the same repo
        _seed_watch(db, project_id, watch_id="w-ci-green",
                    connector_id="gh", query_kind="branch_ci",
                    query={"repository": "karolswdev/HoldSpeak", "base": "main"},
                    snapshot={"schema": 1, "entities": {
                        "1": {"id": "1", "conclusion": "success", "status": "completed",
                              "name": "CI", "branch": "main"},
                    }})

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        sources = room["sources"]

        # ONE merged item
        gh_items = [s for s in sources["items"] if s["provider"] == "github"]
        assert len(gh_items) == 1
        tokens = gh_items[0]["tokens"]

        # Both facts present
        assert "3 OPEN PRS" in tokens
        assert "1 CHECKS FAILING" in tokens
        assert "CI GREEN" in tokens

        # Order: OPEN PRS before CHECKS FAILING before CI
        pr_idx = tokens.index("3 OPEN PRS")
        chk_idx = tokens.index("1 CHECKS FAILING")
        ci_idx = tokens.index("CI GREEN")
        assert pr_idx < chk_idx < ci_idx


# ── target ────────────────────────────────────────────────────────────

class TestTarget:
    """Target section with daysLeft and passed."""

    def test_target_with_future_date(self, db: Database) -> None:
        future = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        project_id = _seed_project(db, target_at=future)
        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        target = room["target"]
        assert target["state"] == "ok"
        assert target["targetAt"] == future
        assert target["daysLeft"] is not None
        assert target["daysLeft"] >= 29
        assert target["passed"] is False

    def test_target_with_past_date(self, db: Database) -> None:
        past = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        project_id = _seed_project(db, target_at=past)
        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        target = room["target"]
        assert target["state"] == "ok"
        assert target["passed"] is True
        assert target["daysLeft"] is None

    def test_target_null_when_not_set(self, db: Database) -> None:
        project_id = _seed_project(db)
        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        target = room["target"]
        assert target["state"] == "ok"
        assert target["targetAt"] is None
        assert target["passed"] is False


# ── real-desk characterization (HS-169-05 defect) ─────────────────────

class TestRealDeskSnapshot:
    """Characterization against the REAL desk's snapshot shape:
    entities stored as a DICT keyed by PR number (normalize_snapshot),
    Jira connection_ref with pipe separator, CLEAR token for empty live,
    and PR-level checks failing rule."""

    # The real snapshot shape from the owner's desk: dict entities
    REAL_GH_SNAPSHOT = {
        "schema": 1,
        "entities": {
            "526": {
                "id": "526",
                "title": "Footer never truncates a host",
                "url": "https://github.com/karolswdev/HoldSpeak/pull/526",
                "state": "open",
                "is_draft": False,
                "review_requests": ["wire-owner"],
                "review_decision": "review_required",
                "checks": "failing",
                "head_sha": "3d4bd46ab",
                "updated_at": "2026-09-03T10:00:00Z",
            },
        },
    }

    def test_dict_entities_produce_tokens(self, db: Database) -> None:
        """A dict-keyed snapshot yields correct source tokens."""
        project_id = _seed_project(db)

        # Seed provider connection so owner login resolves
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO watch_provider_connections "
                "(id, provider_id, external_connection_ref, state, "
                " created_at, updated_at) "
                "VALUES ('wpc-real', 'github', 'wire-owner', 'connected', "
                " datetime('now'), datetime('now'))"
            )

        _seed_watch(db, project_id, watch_id="w-real-gh",
                    connector_id="gh", query_kind="pull_requests",
                    query={"repository": "karolswdev/HoldSpeak", "state": "open", "base": "main"},
                    snapshot=self.REAL_GH_SNAPSHOT)

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)

        # Sources tokens: 1 open PR + 1 waiting on you + 1 checks failing
        sources = room["sources"]
        assert sources["state"] == "ok"
        gh_source = [s for s in sources["items"] if s["provider"] == "github"][0]
        assert "1 OPEN PRS" in gh_source["tokens"]
        assert "1 WAITING ON YOU" in gh_source["tokens"]
        assert "1 CHECKS FAILING" in gh_source["tokens"]

    def test_dict_entities_produce_needs_you(self, db: Database) -> None:
        """A PR with checks failing that awaits the owner's review is a needs-you row."""
        project_id = _seed_project(db)

        with db._connection() as conn:
            conn.execute(
                "INSERT INTO watch_provider_connections "
                "(id, provider_id, external_connection_ref, state, "
                " created_at, updated_at) "
                "VALUES ('wpc-ny', 'github', 'wire-owner', 'connected', "
                " datetime('now'), datetime('now'))"
            )

        _seed_watch(db, project_id, watch_id="w-ny-gh",
                    connector_id="gh", query_kind="pull_requests",
                    query={"repository": "karolswdev/HoldSpeak"},
                    snapshot=self.REAL_GH_SNAPSHOT)

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)

        needs = room["needsYou"]
        assert needs["state"] == "ok"
        assert needs["count"] == 1
        item = needs["items"][0]
        assert item["source"] == "github"
        assert "526" in item["title"]
        # PR awaits the owner's review AND checks are failing -> CHECKS FAILING
        assert item["why"].startswith("CHECKS FAILING")
        assert item["severity"] == "danger"

    def test_jira_host_strips_pipe_email(self, db: Database) -> None:
        """Jira connection_ref 'site|email' -> host is the site part."""
        project_id = _seed_project(db)
        _seed_watch(db, project_id, watch_id="w-jira-host",
                    connector_id="jira", query_kind="issues",
                    query={
                        "connection_ref": "karolsaneapple.atlassian.net|karolsane+apple@gmail.com",
                        "projects": ["KAN"],
                    },
                    snapshot={"schema": 1, "entities": {}})

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        sources = room["sources"]
        jira_source = [s for s in sources["items"] if s["provider"] == "jira"][0]
        assert jira_source["host"] == "karolsaneapple.atlassian.net"

    def test_clear_token_for_empty_live_source(self, db: Database) -> None:
        """A live source with no entities returns the CLEAR token, not []."""
        project_id = _seed_project(db)
        _seed_watch(db, project_id, watch_id="w-clear",
                    connector_id="gh", query_kind="pull_requests",
                    query={"repository": "acme/app"},
                    snapshot={"schema": 1, "entities": {}})

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)
        sources = room["sources"]
        gh_source = [s for s in sources["items"] if s["provider"] == "github"][0]
        assert gh_source["tokens"] == ["CLEAR"]

    def test_pr_checks_failing_not_owner_is_source_token_only(self, db: Database) -> None:
        """A PR with failing checks that does NOT await the owner's review
        is a source token (CHECKS FAILING) but NOT a needs-you row."""
        project_id = _seed_project(db)

        with db._connection() as conn:
            conn.execute(
                "INSERT INTO watch_provider_connections "
                "(id, provider_id, external_connection_ref, state, "
                " created_at, updated_at) "
                "VALUES ('wpc-no', 'github', 'wire-owner', 'connected', "
                " datetime('now'), datetime('now'))"
            )

        _seed_watch(db, project_id, watch_id="w-other",
                    connector_id="gh", query_kind="pull_requests",
                    query={"repository": "acme/app"},
                    snapshot={"schema": 1, "entities": {
                        "99": {
                            "id": "99", "title": "Someone else's PR",
                            "state": "open", "review_requests": ["other-dev"],
                            "review_decision": "", "checks": "failing",
                            "updated_at": "2026-09-03T10:00:00Z",
                        },
                    }})

        svc = ProjectService(db)
        room = svc.room(OWNER, project_id)

        # Source token: 1 CHECKS FAILING present
        sources = room["sources"]
        gh_source = [s for s in sources["items"] if s["provider"] == "github"][0]
        assert "1 CHECKS FAILING" in gh_source["tokens"]

        # Needs-you: no row for this PR (not the owner's review)
        needs = room["needsYou"]
        pr_rows = [n for n in needs["items"] if "99" in n.get("title", "")]
        assert len(pr_rows) == 0
