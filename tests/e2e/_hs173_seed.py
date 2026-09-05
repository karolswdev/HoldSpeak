"""HS-173 e2e seed helper -- shared by the health glass rig and the walk.

Seeds a Room with:
  - PR snapshot entities carrying createdAt and reviewRequests
  - Jira issue entities past the aging threshold
  - CI history (multiple runs for flaky detection)

Usage::

    from tests.e2e._hs173_seed import seed_health_room

    project_id = seed_health_room(db, ...)
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any


def seed_health_room(
    db: Any,
    project_id: str | None = None,
    project_name: str = "Health Test Project",
    *,
    pr_entities: list[dict[str, Any]] | None = None,
    jira_entities: list[dict[str, Any]] | None = None,
    ci_history: list[dict[str, Any]] | None = None,
    ci_snapshot_entities: list[dict[str, Any]] | None = None,
) -> str:
    """Seed a project with Watch snapshots suitable for health derivation tests.

    Parameters
    ----------
    db : Database
        The test database instance.
    project_id : str, optional
        Project ID; generated if omitted.
    project_name : str
        Project display name.
    pr_entities : list, optional
        PR snapshot entities.  Defaults to two PRs with review requests and
        createdAt timestamps (one 4 days old, one 1 day old).
    jira_entities : list, optional
        Jira issue entities.  Defaults to two issues: one aged (30 days), one
        fresh (2 days).
    ci_history : list, optional
        CI run history (for seeding a steward OBSERVE step).  Defaults to 5
        runs with one failure in position 2.
    ci_snapshot_entities : list, optional
        CI entities for the branch_ci watch snapshot.  Defaults to the first
        entry from ci_history.

    Returns
    -------
    str
        The project ID.
    """
    pid = project_id or f"proj-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    # Default PR entities
    if pr_entities is None:
        pr_entities = [
            {
                "number": 101,
                "title": "Add feature X",
                "url": "https://github.com/org/repo/pull/101",
                "state": "OPEN",
                "isDraft": False,
                "reviewRequests": ["alice", "bob"],
                "reviewDecision": None,
                "checks": "success",
                "headRefOid": "abc123",
                "updatedAt": (now - timedelta(hours=6)).isoformat(),
                "createdAt": (now - timedelta(days=4)).isoformat(),
            },
            {
                "number": 102,
                "title": "Fix CI pipeline",
                "url": "https://github.com/org/repo/pull/102",
                "state": "OPEN",
                "isDraft": False,
                "reviewRequests": ["bob"],
                "reviewDecision": "REVIEW_REQUIRED",
                "checks": "success",
                "headRefOid": "def456",
                "updatedAt": (now - timedelta(hours=2)).isoformat(),
                "createdAt": (now - timedelta(days=1)).isoformat(),
            },
        ]

    # Default Jira entities
    if jira_entities is None:
        jira_entities = [
            {
                "key": "PROJ-100",
                "title": "Legacy debt cleanup",
                "summary": "Legacy debt cleanup",
                "url": "https://jira.example.com/browse/PROJ-100",
                "status": "In Progress",
                "status_category": "In Progress",
                "issue_type": "Task",
                "assignee": "carol",
                "assignee_id": "",
                "priority": "",
                "resolution": "",
                "due_at": "",
                "updated_at": (now - timedelta(days=5)).isoformat(),
                "created_at": (now - timedelta(days=30)).isoformat(),
                "status_changed_at": "",
                "labels": [],
                "project_key": "PROJ",
            },
            {
                "key": "PROJ-101",
                "title": "New feature spec",
                "summary": "New feature spec",
                "url": "https://jira.example.com/browse/PROJ-101",
                "status": "To Do",
                "status_category": "To Do",
                "issue_type": "Story",
                "assignee": "dave",
                "assignee_id": "",
                "priority": "",
                "resolution": "",
                "due_at": "",
                "updated_at": (now - timedelta(days=1)).isoformat(),
                "created_at": (now - timedelta(days=2)).isoformat(),
                "status_changed_at": "",
                "labels": [],
                "project_key": "PROJ",
            },
        ]

    # Default CI history
    if ci_history is None:
        ci_history = [
            _ci_run("success", now - timedelta(hours=1)),
            _ci_run("success", now - timedelta(hours=3)),
            _ci_run("failure", now - timedelta(hours=6)),
            _ci_run("success", now - timedelta(hours=12)),
            _ci_run("success", now - timedelta(days=1)),
        ]

    if ci_snapshot_entities is None:
        ci_snapshot_entities = ci_history[:1] if ci_history else []

    # ── Seed project ──
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, NULL, "
            "'2026-09-01T00:00:00', ?)",
            (pid, project_name, now.isoformat()),
        )

    # ── Seed watches ──
    _seed_watch(db, pid, f"{pid}-pr", "gh", "pull_requests",
                {"repository": "org/repo"}, pr_entities)
    _seed_watch(db, pid, f"{pid}-jira", "jira", "issues",
                {"project_key": "PROJ"}, jira_entities)
    _seed_watch(db, pid, f"{pid}-ci", "gh", "branch_ci",
                {"repository": "org/repo", "base": "main"}, ci_snapshot_entities)

    # ── Seed steward OBSERVE step with ci_history ──
    if ci_history:
        _seed_steward_ci_history(db, pid, ci_history)

    return pid


def _ci_run(
    conclusion: str,
    updated_at: datetime,
    branch: str = "main",
) -> dict[str, Any]:
    """Build a CI run entity."""
    run_id = uuid.uuid4().hex[:8]
    return {
        "id": run_id,
        "conclusion": conclusion,
        "status": "completed",
        "name": "CI",
        "url": f"https://github.com/org/repo/actions/runs/{run_id}",
        "updated_at": updated_at.isoformat(),
        "branch": branch,
    }


def _seed_watch(
    db: Any,
    project_id: str,
    watch_id: str,
    connector_id: str,
    query_kind: str,
    query: dict[str, Any],
    snapshot: list[dict[str, Any]],
) -> None:
    """Insert a connector_watches row."""
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
                json.dumps(query, sort_keys=True),
                json.dumps(snapshot),
                project_id,
            ),
        )


def _seed_steward_ci_history(
    db: Any,
    project_id: str,
    ci_history: list[dict[str, Any]],
) -> None:
    """Create a completed steward run with an OBSERVE step carrying ci_history."""
    run_id = f"stw-run-{uuid.uuid4().hex[:8]}"
    step_id = f"stw-step-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    observed = json.dumps({"coverage": {}, "ci_history": ci_history}, default=str)

    with db._connection() as conn:
        conn.execute(
            "INSERT INTO steward_runs "
            "(id, project_id, state, phase, summary_json, created_at, updated_at) "
            "VALUES (?, ?, 'completed', 'record', '{}', ?, ?)",
            (run_id, project_id, now_iso, now_iso),
        )
        conn.execute(
            "INSERT INTO steward_steps "
            "(id, run_id, phase, seq, effect_kind, state, "
            " expected_state_json, observed_state_json, "
            " idempotency_key, receipt_json, created_at, updated_at) "
            "VALUES (?, ?, 'observe', 1, '', 'completed', "
            " '{}', ?, ?, NULL, ?, ?)",
            (step_id, run_id, observed,
             f"observe-{run_id}", now_iso, now_iso),
        )
