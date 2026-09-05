"""HS-173-03 / HS-173-05 -- health signal derivation wire tests.

Verifies:
  - review_wait: per-reviewer median, overall median, waiting count,
    present flag, absent when no waiting PRs
  - issue_aging: aged count, present flag, absent when no Jira entities
  - ci_health: tone derivation, flaky branch detection, present flag
  - merge_queue_depth: counts open non-draft PRs with passing CI
  - readiness: composite tone, per-signal tones, absent when no data
  - GH_WATCH_FIELDS includes createdAt (additive, allowlist unchanged)
  - Room health read emits signals and present flags
  - Room needs-you emits review_bottleneck items for resolved reviewers
  - No raw login leaks into bottleneck items
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.connector_packs.github_cli import is_command_allowed
from holdspeak.db.core import Database
from holdspeak.services.project_service import ProjectService
from holdspeak.services.room_health_service import (
    ci_health,
    issue_aging,
    merge_queue_depth,
    readiness,
    review_wait,
)
from holdspeak.services.watch_sources import GH_WATCH_FIELDS


OWNER_PRINCIPAL = MagicMock()
NOW = datetime(2026, 9, 5, 12, 0, 0, tzinfo=timezone.utc)


# ── GH_WATCH_FIELDS includes createdAt ──────────────────────────────

class TestCreatedAtField:

    def test_gh_watch_fields_includes_created_at(self) -> None:
        assert "createdAt" in GH_WATCH_FIELDS

    def test_allowlist_unchanged_for_pr_list(self) -> None:
        """Adding a field to --json does not change the subcommand allowlist."""
        command = [
            "gh", "pr", "list", "--repo", "acme/app", "--state", "open",
            "--limit", "50", "--json", GH_WATCH_FIELDS,
        ]
        assert is_command_allowed(command) is True

    def test_allowlist_still_rejects_mutating_commands(self) -> None:
        assert is_command_allowed(["gh", "pr", "edit", "--repo", "a/b"]) is False
        assert is_command_allowed(["gh", "pr", "merge", "--repo", "a/b"]) is False


# ── review_wait ──────────────────────────────────────────────────────

class TestReviewWait:

    def _pr(
        self,
        number: int,
        reviewers: list[str],
        created_at: str,
        state: str = "OPEN",
        review_decision: str | None = None,
    ) -> dict[str, Any]:
        return {
            "number": number,
            "state": state,
            "reviewRequests": reviewers,
            "reviewDecision": review_decision,
            "createdAt": created_at,
            "title": f"PR #{number}",
            "url": f"https://github.com/org/repo/pull/{number}",
            "isDraft": False,
            "checks": "success",
        }

    def test_basic_median(self) -> None:
        """Two PRs, one reviewer each, different ages."""
        entities = [
            self._pr(1, ["alice"], "2026-09-03T12:00:00Z"),  # 2 days old
            self._pr(2, ["alice"], "2026-09-04T12:00:00Z"),  # 1 day old
        ]
        result = review_wait(entities, NOW)
        assert result["present"] is True
        assert result["tone"] == "amber"  # worst reviewer 1.5 d -> amber (1-2)
        assert result["waiting_count"] == 2
        assert result["median_days"] == 1.5
        assert len(result["per_reviewer"]) == 1
        assert result["per_reviewer"][0]["login"] == "alice"
        assert result["per_reviewer"][0]["count"] == 2

    def test_multiple_reviewers(self) -> None:
        """PRs spread across two reviewers."""
        entities = [
            self._pr(1, ["alice", "bob"], "2026-09-01T12:00:00Z"),  # 4 days
            self._pr(2, ["bob"], "2026-09-04T12:00:00Z"),  # 1 day
        ]
        result = review_wait(entities, NOW)
        assert result["present"] is True
        # alice has 1 PR at 4 d -> red; that sets the overall tone
        assert result["tone"] == "red"
        # waiting_count = number of PRs with pending reviews (2)
        assert result["waiting_count"] == 2
        per = {r["login"]: r for r in result["per_reviewer"]}
        assert per["alice"]["count"] == 1
        assert per["bob"]["count"] == 2

    def test_absent_when_no_waiting_prs(self) -> None:
        """No open PRs with pending review requests -> present=False."""
        entities = [
            self._pr(1, ["alice"], "2026-09-03T12:00:00Z",
                     review_decision="APPROVED"),
        ]
        result = review_wait(entities, NOW)
        assert result["present"] is False
        assert result["tone"] == "green"
        assert result["waiting_count"] == 0

    def test_absent_when_empty(self) -> None:
        result = review_wait([], NOW)
        assert result["present"] is False
        assert result["tone"] == "green"

    def test_closed_prs_excluded(self) -> None:
        entities = [
            self._pr(1, ["alice"], "2026-09-03T12:00:00Z", state="CLOSED"),
        ]
        result = review_wait(entities, NOW)
        assert result["present"] is False
        assert result["tone"] == "green"

    def test_review_required_counts(self) -> None:
        """reviewDecision=REVIEW_REQUIRED still counts as waiting."""
        entities = [
            self._pr(1, ["alice"], "2026-09-03T12:00:00Z",
                     review_decision="REVIEW_REQUIRED"),
        ]
        result = review_wait(entities, NOW)
        assert result["present"] is True
        assert result["tone"] == "amber"  # exactly 2.0 d -> 1-2 range -> amber
        assert result["waiting_count"] == 1

    def test_tone_green_under_one_day(self) -> None:
        """Reviewer median < 1 day -> green."""
        entities = [
            self._pr(1, ["alice"], "2026-09-05T06:00:00Z"),  # 6 h = 0.25 d
        ]
        result = review_wait(entities, NOW)
        assert result["tone"] == "green"

    def test_tone_amber_between_one_and_two_days(self) -> None:
        """Reviewer median 1-2 days -> amber."""
        entities = [
            self._pr(1, ["alice"], "2026-09-04T00:00:00Z"),  # 1.5 d
        ]
        result = review_wait(entities, NOW)
        assert result["tone"] == "amber"


# ── issue_aging ──────────────────────────────────────────────────────

class TestIssueAging:

    def _issue(
        self,
        key: str,
        created_at: str,
        status: str = "In Progress",
    ) -> dict[str, Any]:
        return {
            "key": key,
            "created_at": created_at,
            "status": status,
            "assignee": "someone",
        }

    def test_counts_aged_issues(self) -> None:
        entities = [
            self._issue("PROJ-1", "2026-08-01"),  # 35 days > 14
            self._issue("PROJ-2", "2026-09-01"),  # 4 days < 14
            self._issue("PROJ-3", "2026-08-10"),  # 26 days > 14
        ]
        result = issue_aging(entities, NOW, threshold_days=14)
        assert result["present"] is True
        assert result["tone"] == "amber"  # 2 aged -> 1-2 -> amber
        assert result["aged_count"] == 2
        assert result["threshold_days"] == 14

    def test_done_issues_excluded(self) -> None:
        entities = [
            self._issue("PROJ-1", "2026-08-01", status="Done"),
        ]
        result = issue_aging(entities, NOW, threshold_days=14)
        assert result["present"] is True
        assert result["tone"] == "green"  # 0 aged
        assert result["aged_count"] == 0

    def test_absent_when_empty(self) -> None:
        result = issue_aging([], NOW)
        assert result["present"] is False
        assert result["tone"] == "green"
        assert result["threshold_days"] == 14

    def test_present_true_at_green(self) -> None:
        """When Jira entities exist but none are aged, present=True, aged_count=0."""
        entities = [self._issue("PROJ-1", "2026-09-04")]  # 1 day < 14
        result = issue_aging(entities, NOW, threshold_days=14)
        assert result["present"] is True
        assert result["tone"] == "green"
        assert result["aged_count"] == 0

    def test_tone_red_three_or_more(self) -> None:
        """3+ aged issues -> red."""
        entities = [
            self._issue("PROJ-1", "2026-07-01"),
            self._issue("PROJ-2", "2026-07-10"),
            self._issue("PROJ-3", "2026-07-20"),
        ]
        result = issue_aging(entities, NOW, threshold_days=14)
        assert result["tone"] == "red"
        assert result["aged_count"] == 3

    def test_tone_amber_one_aged(self) -> None:
        """1 aged issue -> amber."""
        entities = [self._issue("PROJ-1", "2026-07-01")]
        result = issue_aging(entities, NOW, threshold_days=14)
        assert result["tone"] == "amber"
        assert result["aged_count"] == 1


# ── ci_health ────────────────────────────────────────────────────────

class TestCIHealth:

    def _run(self, conclusion: str, branch: str = "main") -> dict[str, Any]:
        return {"conclusion": conclusion, "branch": branch}

    def test_all_passing(self) -> None:
        history = [self._run("success"), self._run("success"), self._run("success")]
        result = ci_health(history)
        assert result["present"] is True
        assert result["tone"] == "green"
        assert result["failures_last_3"] == 0
        assert result["queue"] == 0  # default when not passed

    def test_one_failure_amber(self) -> None:
        history = [self._run("success"), self._run("failure"), self._run("success")]
        result = ci_health(history)
        assert result["tone"] == "amber"
        assert result["failures_last_3"] == 1
        assert result["queue"] == 0

    def test_two_failures_red(self) -> None:
        history = [self._run("failure"), self._run("failure"), self._run("success")]
        result = ci_health(history)
        assert result["tone"] == "red"
        assert result["failures_last_3"] == 2

    def test_absent_when_empty(self) -> None:
        result = ci_health([])
        assert result["present"] is False
        assert result["queue"] == 0

    def test_queue_passed_through(self) -> None:
        """merge-queue depth is carried on the signal."""
        history = [self._run("success")]
        result = ci_health(history, queue=5)
        assert result["queue"] == 5
        assert result["present"] is True

    def test_queue_on_absent(self) -> None:
        """queue appears even when present=False."""
        result = ci_health([], queue=3)
        assert result["present"] is False
        assert result["queue"] == 3

    def test_flaky_detection(self) -> None:
        """A branch with alternating results is flagged flaky."""
        history = [
            self._run("success", "dev"),
            self._run("failure", "dev"),
            self._run("success", "dev"),
            self._run("failure", "dev"),
        ]
        result = ci_health(history)
        assert result["flaky_branch_count"] == 1

    def test_timed_out_is_failure(self) -> None:
        history = [self._run("timed_out"), self._run("timed_out"), self._run("success")]
        result = ci_health(history)
        assert result["tone"] == "red"

    def test_cancelled_is_failure(self) -> None:
        history = [self._run("cancelled"), self._run("success"), self._run("success")]
        result = ci_health(history)
        assert result["tone"] == "amber"


# ── merge_queue_depth ────────────────────────────────────────────────

class TestMergeQueueDepth:

    def test_counts_merge_ready(self) -> None:
        entities = [
            {"state": "OPEN", "isDraft": False, "checks": "success"},
            {"state": "OPEN", "isDraft": False, "checks": "success"},
            {"state": "OPEN", "isDraft": True, "checks": "success"},  # draft
            {"state": "OPEN", "isDraft": False, "checks": "failing"},  # failing
            {"state": "CLOSED", "isDraft": False, "checks": "success"},  # closed
        ]
        assert merge_queue_depth(entities) == 2

    def test_empty(self) -> None:
        assert merge_queue_depth([]) == 0


# ── readiness ────────────────────────────────────────────────────────

class TestReadiness:

    def test_all_green(self) -> None:
        review = {"present": True, "per_reviewer": [{"login": "a", "median_days": 0.5, "count": 1}]}
        ci = {"present": True, "tone": "green"}
        result = readiness(review_signal=review, ci_signal=ci,
                           blocker_count=0, overdue_count=0)
        assert result["present"] is True
        assert result["tone"] == "green"
        assert result["composite"] == "green"
        assert result["signals"]["review_wait"] == "green"
        assert result["blockers"] == []
        assert result["blockers_count"] == 0

    def test_review_amber(self) -> None:
        review = {"present": True, "per_reviewer": [{"login": "a", "median_days": 1.5, "count": 1}]}
        ci = {"present": True, "tone": "green"}
        result = readiness(review_signal=review, ci_signal=ci)
        assert result["tone"] == "amber"
        assert result["composite"] == "amber"
        assert result["signals"]["review_wait"] == "amber"
        assert "review_wait" in result["blockers"]

    def test_review_red(self) -> None:
        review = {"present": True, "per_reviewer": [{"login": "a", "median_days": 3.0, "count": 1}]}
        ci = {"present": True, "tone": "green"}
        result = readiness(review_signal=review, ci_signal=ci)
        assert result["tone"] == "red"
        assert result["composite"] == "red"
        assert result["signals"]["review_wait"] == "red"
        assert "review_wait" in result["blockers"]

    def test_ci_red_dominates(self) -> None:
        review = {"present": True, "per_reviewer": [{"login": "a", "median_days": 0.5, "count": 1}]}
        ci = {"present": True, "tone": "red"}
        result = readiness(review_signal=review, ci_signal=ci)
        assert result["tone"] == "red"
        assert result["composite"] == "red"
        assert "ci" in result["blockers"]

    def test_blockers(self) -> None:
        review = {"present": False, "per_reviewer": []}
        ci = {"present": False, "tone": "green"}
        result = readiness(review_signal=review, ci_signal=ci,
                           blocker_count=2, overdue_count=0)
        assert result["present"] is True
        assert result["tone"] == "red"
        assert result["signals"]["blockers"] == "red"
        assert result["composite"] == "red"
        assert "blockers" in result["blockers"]

    def test_absent_when_no_data(self) -> None:
        review = {"present": False, "per_reviewer": []}
        ci = {"present": False, "tone": "green"}
        result = readiness(review_signal=review, ci_signal=ci,
                           blocker_count=0, overdue_count=0)
        assert result["present"] is False
        assert result["tone"] == "green"
        assert result["blockers"] == []

    def test_overdue_amber(self) -> None:
        review = {"present": False, "per_reviewer": []}
        ci = {"present": False, "tone": "green"}
        result = readiness(review_signal=review, ci_signal=ci,
                           blocker_count=0, overdue_count=1)
        assert result["present"] is True
        assert result["tone"] == "amber"
        assert result["signals"]["overdue"] == "amber"
        assert result["composite"] == "amber"
        assert "overdue" in result["blockers"]

    def test_multiple_blockers_named(self) -> None:
        """blockers lists every signal that is red or amber."""
        review = {"present": True, "per_reviewer": [{"login": "a", "median_days": 3.0, "count": 1}]}
        ci = {"present": True, "tone": "amber"}
        result = readiness(review_signal=review, ci_signal=ci,
                           blocker_count=1, overdue_count=0)
        assert result["tone"] == "red"
        # review_wait=red, ci=amber, blockers=amber -- all three appear
        assert "review_wait" in result["blockers"]
        assert "ci" in result["blockers"]
        assert "blockers" in result["blockers"]


# ── Room health read integration ─────────────────────────────────────

@pytest.fixture()
def db(tmp_path):
    return Database(tmp_path / "test.db")


@pytest.fixture()
def project_service(db):
    from holdspeak.db import get_observer
    return ProjectService(db, observer=get_observer())


def _seed_project(db: Database, project_id: str = "proj-1") -> str:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, NULL, "
            "'2026-09-01T00:00:00', '2026-09-05T10:00:00')",
            (project_id, "Test Project"),
        )
    return project_id


def _seed_watch(
    db: Database,
    project_id: str,
    watch_id: str,
    connector_id: str = "gh",
    query_kind: str = "pull_requests",
    query: dict | None = None,
    snapshot: list[dict[str, Any]] | None = None,
) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, "
            " created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'), NULL, ?, "
            "datetime('now'), datetime('now'))",
            (
                watch_id,
                connector_id,
                query_kind,
                f"{connector_id} {query_kind}",
                json.dumps(query or {}, sort_keys=True),
                json.dumps(snapshot or []),
                project_id,
            ),
        )


class TestRoomHealthSignals:

    def test_health_signals_present_in_room(self, db, project_service) -> None:
        """GET /api/projects/{id}/room health section includes signals."""
        pid = _seed_project(db)
        _seed_watch(db, pid, "w-pr", snapshot=[{
            "number": 1, "state": "OPEN", "isDraft": False,
            "reviewRequests": ["alice"], "reviewDecision": None,
            "createdAt": "2026-09-03T12:00:00Z",
            "updatedAt": "2026-09-05T10:00:00Z",
            "checks": "success", "url": "https://github.com/o/r/pull/1",
            "title": "Fix bug",
        }])
        _seed_watch(db, pid, "w-jira", connector_id="jira",
                    query_kind="issues", snapshot=[{
            "key": "PROJ-1", "status": "In Progress",
            "created_at": "2026-08-01", "assignee": "someone",
            "updated_at": "2026-09-01", "priority": "",
            "labels": [], "due_at": "",
        }])
        _seed_watch(db, pid, "w-ci", query_kind="branch_ci", snapshot=[{
            "id": "run-1", "conclusion": "success", "status": "completed",
            "name": "CI", "url": "https://github.com/o/r/actions/runs/1",
            "updated_at": "2026-09-05T10:00:00Z", "branch": "main",
        }])

        health = project_service._read_room_health(pid, None)

        # The traditional assessment is present
        assert "assessment" in health
        # HS-173 signals are present
        assert "signals" in health
        signals = health["signals"]
        assert "review_wait" in signals
        assert "issue_aging" in signals
        assert "ci" in signals
        assert "release" in signals

        # review_wait is present with data and carries tone
        assert signals["review_wait"]["present"] is True
        assert signals["review_wait"]["waiting_count"] == 1
        assert signals["review_wait"]["tone"] in ("green", "amber", "red")

        # issue_aging is present (Jira entities exist), carries tone + threshold_days
        assert signals["issue_aging"]["present"] is True
        assert signals["issue_aging"]["tone"] in ("green", "amber", "red")
        assert signals["issue_aging"]["threshold_days"] == 14

        # ci is present, carries tone + queue
        assert signals["ci"]["present"] is True
        assert signals["ci"]["tone"] in ("green", "amber", "red")
        assert "queue" in signals["ci"]

        # release is present, carries tone + blockers
        assert signals["release"]["present"] is True
        assert signals["release"]["tone"] in ("green", "amber", "red")
        assert signals["release"]["tone"] == signals["release"]["composite"]
        assert isinstance(signals["release"]["blockers"], list)

        # checked_at is present
        assert health["checked_at"] is not None

    def test_health_signals_absent_when_no_data(self, db, project_service) -> None:
        """All signals absent when no watches exist."""
        pid = _seed_project(db)
        health = project_service._read_room_health(pid, None)
        signals = health["signals"]
        assert signals["review_wait"]["present"] is False
        assert signals["review_wait"]["tone"] == "green"
        assert signals["issue_aging"]["present"] is False
        assert signals["issue_aging"]["tone"] == "green"
        assert signals["ci"]["present"] is False
        assert signals["ci"]["tone"] == "green"
        assert signals["ci"]["queue"] == 0
        assert signals["release"]["present"] is False
        assert signals["release"]["tone"] == "green"
        assert signals["release"]["blockers"] == []

    def test_merge_queue_depth_in_health(self, db, project_service) -> None:
        pid = _seed_project(db)
        _seed_watch(db, pid, "w-pr2", snapshot=[
            {"number": 1, "state": "OPEN", "isDraft": False,
             "reviewRequests": [], "reviewDecision": "APPROVED",
             "createdAt": "2026-09-03T12:00:00Z",
             "updatedAt": "2026-09-05T10:00:00Z",
             "checks": "success", "url": "https://github.com/o/r/pull/1",
             "title": "Ready to merge"},
            {"number": 2, "state": "OPEN", "isDraft": False,
             "reviewRequests": [], "reviewDecision": "APPROVED",
             "createdAt": "2026-09-03T12:00:00Z",
             "updatedAt": "2026-09-05T10:00:00Z",
             "checks": "success", "url": "https://github.com/o/r/pull/2",
             "title": "Also ready"},
        ])
        health = project_service._read_room_health(pid, None)
        assert health["merge_queue_depth"] == 2
        # queue also on ci signal
        assert health["signals"]["ci"]["queue"] == 2


class TestNeedsYouReviewBottleneck:

    def test_no_raw_login_in_bottleneck(self, db, project_service) -> None:
        """review_bottleneck items use display_name, never raw login."""
        pid = _seed_project(db)
        _seed_watch(db, pid, "w-pr3", snapshot=[{
            "number": 1, "state": "OPEN", "isDraft": False,
            "reviewRequests": ["alice-gh"],
            "reviewDecision": None,
            "createdAt": "2026-09-01T12:00:00Z",
            "updatedAt": "2026-09-05T10:00:00Z",
            "checks": "success",
            "url": "https://github.com/o/r/pull/1",
            "title": "Fix bug",
        }])

        # Mock the people resolver to map alice-gh -> Alice Kowalska
        mock_people = MagicMock()
        mock_people.resolve_relationship_by_watch_identity.return_value = {
            "state": "ready",
            "relationship": {
                "id": "rel-1",
                "display_name": "Alice Kowalska",
            },
        }

        # Set _people_service directly on the project_service instance
        project_service._people_service = mock_people
        try:
            needs = project_service._read_room_needs_you(pid)
        finally:
            del project_service._people_service

        bottleneck_items = [
            n for n in needs["items"] if n.get("kind") == "review_bottleneck"
        ]
        assert len(bottleneck_items) == 1
        item = bottleneck_items[0]
        assert item["title"] == "Alice Kowalska"
        assert "alice-gh" not in item["title"]
        assert "alice-gh" not in item["why"]
        assert item["verb"] == "nudge"
        assert item["relationship_id"] == "rel-1"

    def test_unresolved_reviewer_excluded(self, db, project_service) -> None:
        """Unresolved reviewers get no bottleneck row."""
        pid = _seed_project(db)
        _seed_watch(db, pid, "w-pr4", snapshot=[{
            "number": 1, "state": "OPEN", "isDraft": False,
            "reviewRequests": ["unknown-gh"],
            "reviewDecision": None,
            "createdAt": "2026-09-01T12:00:00Z",
            "updatedAt": "2026-09-05T10:00:00Z",
            "checks": "success",
            "url": "https://github.com/o/r/pull/1",
            "title": "PR 1",
        }])

        # Mock resolver returns no match
        mock_people = MagicMock()
        mock_people.resolve_relationship_by_watch_identity.return_value = {
            "state": "ready",
            "relationship": None,
        }

        project_service._people_service = mock_people
        try:
            needs = project_service._read_room_needs_you(pid)
        finally:
            del project_service._people_service

        bottleneck_items = [
            n for n in needs["items"] if n.get("kind") == "review_bottleneck"
        ]
        assert len(bottleneck_items) == 0
