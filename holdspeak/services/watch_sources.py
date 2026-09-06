"""Typed connector snapshot adapters used by Watches.

The adapter owns CLI output interpretation. Reactions only ever see normalized
entities and therefore never mine arbitrary tool presentation text.

HS-166-03: JiraWatchSource graduates the gate -- Jira watches now have
a local query adapter that compiles one JQL, fetches via the adapter's
search(enrich=True), and emits entities in the shape _normalize_entity
consumes.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import threading
from collections.abc import Callable
from typing import Any

from holdspeak.connector_packs import github_cli
from holdspeak.connector_runtime import PermissionGate
from holdspeak.delivery.pr_receipts import rollup_conclusion
from holdspeak.principals import Principal
from holdspeak.services.errors import ServiceError, ValidationError

# HS-167-02: thread-local to carry provider fetch metadata (calls count)
# from the snapshot adapter to the evaluate_core caller without changing
# the snapshot_fetcher return type.
_fetch_meta = threading.local()


Runner = Callable[..., subprocess.CompletedProcess[str]]

GH_WATCH_FIELDS = (
    "number,title,url,state,isDraft,reviewRequests,reviewDecision,"
    "statusCheckRollup,headRefOid,updatedAt,createdAt"
)


def _reviewer_names(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    names = []
    for reviewer in value:
        if isinstance(reviewer, dict):
            name = reviewer.get("login") or reviewer.get("name") or reviewer.get("slug")
        else:
            name = reviewer
        if str(name or "").strip():
            names.append(str(name).strip())
    return sorted(set(names))


GH_BRANCH_CI_FIELDS = "conclusion,status,name,url,updatedAt,headBranch"


class GitHubWatchSource:
    def __init__(self, *, runner: Runner | None = None) -> None:
        self._runner = runner

    def snapshot(self, principal: Principal, *, query_kind: str,
                 query: dict[str, Any]) -> list[dict[str, Any]]:
        if query_kind == "branch_ci":
            return self._snapshot_branch_ci(principal, query)
        if query_kind != "pull_requests":
            raise ValidationError("GitHub Watches support pull_requests and branch_ci")
        repository = str(query.get("repository") or "").strip()
        if "/" not in repository or repository.startswith("/") or repository.endswith("/"):
            raise ValidationError("GitHub Watch requires repository as owner/name")
        limit = max(1, min(int(query.get("limit", 50)), 100))
        state = str(query.get("state") or "open").lower()
        if state not in {"open", "closed", "merged", "all"}:
            raise ValidationError("GitHub Watch state must be open, closed, merged, or all")
        command = [
            "gh", "pr", "list", "--repo", repository, "--state", state,
            "--limit", str(limit), "--json", GH_WATCH_FIELDS,
        ]
        search = str(query.get("search") or "").strip()
        if search:
            command.extend(["--search", search])
        if not github_cli.is_command_allowed(command):
            raise ServiceError("connector_command_refused", "GitHub Watch command is not allowlisted")
        if self._runner is None and shutil.which("gh") is None:
            raise ServiceError("connector_unavailable", "GitHub CLI is not installed")
        completed = PermissionGate(github_cli.MANIFEST).run_read_subprocess(
            command, principal=principal, runner=self._runner,
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            errors="replace", timeout=github_cli.DEFAULT_TIMEOUT_SECONDS,
        )
        if completed.returncode != 0:
            detail = str(completed.stderr or "GitHub CLI query failed").strip()[:500]
            raise ServiceError("connector_refresh_failed", detail)
        try:
            rows = json.loads(completed.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise ServiceError("connector_invalid_output", "GitHub CLI returned invalid JSON") from exc
        if not isinstance(rows, list):
            raise ServiceError("connector_invalid_output", "GitHub CLI returned a non-array snapshot")
        entities = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            entities.append({
                "number": row.get("number"), "title": row.get("title"),
                "url": row.get("url"), "state": row.get("state"),
                "isDraft": bool(row.get("isDraft")),
                "reviewRequests": _reviewer_names(row.get("reviewRequests")),
                "reviewDecision": row.get("reviewDecision"),
                "checks": rollup_conclusion(row.get("statusCheckRollup")),
                "headRefOid": row.get("headRefOid"), "updatedAt": row.get("updatedAt"),
                "createdAt": row.get("createdAt"),
            })
        return entities

    # ── branch_ci kind (HS-169-04, counsel M1) ──────────────────────
    def _snapshot_branch_ci(
        self, principal: Principal, query: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """CI status on the base branch: `gh run list --branch <base> --limit N`.

        HS-173: the steward's OBSERVE phase passes ``limit=10`` in the
        query to get CI history for flaky-branch detection; the normal
        Watch evaluation keeps the default of 1.
        """
        repository = str(query.get("repository") or "").strip()
        if "/" not in repository or repository.startswith("/") or repository.endswith("/"):
            raise ValidationError("branch_ci requires repository as owner/name")
        base = str(query.get("base") or "main").strip()
        ci_limit = max(1, min(int(query.get("limit", 1)), 100))
        command = [
            "gh", "run", "list", "--repo", repository,
            "--branch", base, "--limit", str(ci_limit),
            "--json", GH_BRANCH_CI_FIELDS,
        ]
        if not github_cli.is_command_allowed(command):
            raise ServiceError("connector_command_refused", "GitHub Watch command is not allowlisted")
        if self._runner is None and shutil.which("gh") is None:
            raise ServiceError("connector_unavailable", "GitHub CLI is not installed")
        completed = PermissionGate(github_cli.MANIFEST).run_read_subprocess(
            command, principal=principal, runner=self._runner,
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            errors="replace", timeout=github_cli.DEFAULT_TIMEOUT_SECONDS,
        )
        if completed.returncode != 0:
            detail = str(completed.stderr or "GitHub CLI query failed").strip()[:500]
            raise ServiceError("connector_refresh_failed", detail)
        try:
            rows = json.loads(completed.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise ServiceError("connector_invalid_output", "GitHub CLI returned invalid JSON") from exc
        if not isinstance(rows, list):
            raise ServiceError("connector_invalid_output", "GitHub CLI returned a non-array snapshot")
        entities: list[dict[str, Any]] = []
        for idx, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            # HS-169-05: normalize_snapshot requires every entity to carry
            # id/number/key.  gh run list returns no native id in --json;
            # derive one from the URL (unique per run) or fall back to the
            # branch + index so baseline_watch does not fail with
            # "Every snapshot entity requires id, number, or key".
            run_url = str(row.get("url") or "")
            run_id = run_url.rsplit("/", 1)[-1] if "/" in run_url else ""
            if not run_id:
                run_id = f"{base}-{idx}"
            entities.append({
                "id": run_id,
                "conclusion": row.get("conclusion"),
                "status": row.get("status"),
                "name": row.get("name"),
                "url": run_url,
                "updated_at": row.get("updatedAt"),
                "branch": row.get("headBranch"),
            })
        return entities


# ── JiraWatchSource (HS-166-03) ─────────────────────────────────────


def _jql_quote(val: str) -> str:
    """Double-quote a JQL value, escaping internal quotes."""
    return '"' + val.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _compile_jql(query: dict[str, Any]) -> str:
    """Compile a watch query dict into a single JQL string.

    PURE: no DB, no IO.  Deterministic ordering.  Conditions that can
    be pushed server-side are expressed as JQL clauses; the remaining
    query keys (limit, due_within_days, inactive_days) are consumed
    by the caller.

    The owner's typed ``jql`` (if any) is appended verbatim as
    ``AND (<jql>)`` so it always combines with the structured filters.
    """
    clauses: list[str] = []

    # Helper: strip blank/whitespace-only entries so a stored [""]
    # compiles to no clause (HS-168-05 belt).
    def _clean(raw: list[str]) -> list[str]:
        return [v for v in raw if isinstance(v, str) and v.strip()]

    # project in (...)
    projects = query.get("projects", [])
    if isinstance(projects, list):
        projects = _clean(projects)
    if projects:
        vals = ", ".join(_jql_quote(p) for p in sorted(projects))
        clauses.append(f"project in ({vals})")

    # issuetype in (...)
    issue_types = query.get("issue_types", [])
    if isinstance(issue_types, list):
        issue_types = _clean(issue_types)
    if issue_types:
        vals = ", ".join(_jql_quote(t) for t in sorted(issue_types))
        clauses.append(f"issuetype in ({vals})")

    # statusCategory in (...)
    status_categories = query.get("status_categories", [])
    if isinstance(status_categories, list):
        status_categories = _clean(status_categories)
    if status_categories:
        vals = ", ".join(_jql_quote(c) for c in sorted(status_categories))
        clauses.append(f"statusCategory in ({vals})")

    # priority in (...)
    priorities = query.get("priorities", [])
    if isinstance(priorities, list):
        priorities = _clean(priorities)
    if priorities:
        vals = ", ".join(_jql_quote(p) for p in sorted(priorities))
        clauses.append(f"priority in ({vals})")

    # assignee in (...)
    assignees = query.get("assignees", [])
    if isinstance(assignees, list):
        assignees = _clean(assignees)
    if assignees:
        vals = ", ".join(_jql_quote(a) for a in sorted(assignees))
        clauses.append(f"assignee in ({vals})")

    # labels in (...)
    labels = query.get("labels", [])
    if isinstance(labels, list):
        labels = _clean(labels)
    if labels:
        vals = ", ".join(_jql_quote(lb) for lb in sorted(labels))
        clauses.append(f"labels in ({vals})")

    # component in (...)
    components = query.get("components", [])
    if isinstance(components, list):
        components = _clean(components)
    if components:
        vals = ", ".join(_jql_quote(c) for c in sorted(components))
        clauses.append(f"component in ({vals})")

    # sprint = "..."
    sprint = query.get("sprint")
    if sprint:
        clauses.append(f"sprint = {_jql_quote(str(sprint))}")

    # due <= Nd (due_within_days)
    due_within = query.get("due_within_days")
    if due_within is not None:
        try:
            days = int(due_within)
            clauses.append(f"due <= {days}d")
        except (TypeError, ValueError):
            pass

    # updated <= -Nd (inactive_days)
    inactive = query.get("inactive_days")
    if inactive is not None:
        try:
            days = int(inactive)
            clauses.append(f"updated <= -{days}d")
        except (TypeError, ValueError):
            pass

    # status in (...) (blocked_statuses)
    blocked = query.get("blocked_statuses", [])
    if isinstance(blocked, list) and blocked:
        vals = ", ".join(_jql_quote(s) for s in sorted(blocked))
        clauses.append(f"status in ({vals})")

    # Owner-typed JQL appended verbatim
    owner_jql = str(query.get("jql") or "").strip()
    if owner_jql:
        clauses.append(f"({owner_jql})")

    body = " AND ".join(clauses) if clauses else ""
    if body:
        return f"{body} ORDER BY updated DESC"
    return "ORDER BY updated DESC"


class JiraWatchSource:
    """Snapshot adapter for Jira Watches via JiraProviderAdapter.

    Compiles the watch query into ONE JQL, calls adapter.search with
    enrich=True, and emits entities in the shape _normalize_entity
    consumes.
    """

    def __init__(self, *, adapter: Any = None) -> None:
        self._adapter = adapter

    def snapshot(self, principal: Principal, *, query_kind: str,
                 query: dict[str, Any]) -> list[dict[str, Any]]:
        # M-1: clear-on-entry — prevent a previous call's stale metadata
        # from leaking into a later watch if this fetch raises mid-flight.
        drain_fetch_meta()
        if query_kind != "issues":
            raise ValidationError("Jira Watches support issues")

        connection_ref = str(query.get("connection_ref") or "").strip()
        if not connection_ref or "|" not in connection_ref:
            raise ValidationError(
                "Jira Watch requires connection_ref (site|email)"
            )

        adapter = self._adapter
        if adapter is None:
            # Lazy construction from the house DB
            from holdspeak.db import get_database
            from holdspeak.services.jira_provider import JiraProviderAdapter
            adapter = JiraProviderAdapter(db=get_database())

        jql = _compile_jql(query)
        limit = max(1, min(int(query.get("limit") or 50), 200))

        result = adapter.search(
            principal, connection_ref,
            jql=jql, limit=limit, enrich=True,
        )

        state = result.get("state", "")
        error_code = result.get("error_code")

        if state != "ready":
            # Map adapter error codes to ServiceError codes
            code_map = {
                "query_invalid": "connector_query_invalid",
                "authentication_required": "authentication_required",
                "unavailable": "connector_unavailable",
            }
            se_code = code_map.get(error_code or "", "connector_refresh_failed")
            detail = result.get("error_detail") or result.get("query_invalid") or "Jira query failed"
            raise ServiceError(se_code, str(detail)[:500])

        # HS-167-02: store calls count on thread-local for the evaluate
        # caller to pick up and persist on the evaluation record.
        calls = result.get("calls")
        if calls is not None:
            _fetch_meta.calls = int(calls)

        items = result.get("items", [])
        entities: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            entities.append({
                "id": item.get("key") or str(item.get("id", "")),
                "key": item.get("key", ""),
                "title": item.get("summary", ""),
                "summary": item.get("summary", ""),
                "url": item.get("url", ""),
                "status": item.get("status", ""),
                "status_category": item.get("status_category", ""),
                "issue_type": item.get("issue_type", ""),
                "assignee": item.get("assignee") or "",
                "assignee_id": item.get("assignee_id") or "",
                "priority": item.get("priority") or "",
                "resolution": item.get("resolution") or "",
                "due_at": item.get("due_at") or "",
                "updated_at": item.get("updated_at") or "",
                "created_at": item.get("created_at") or "",
                "status_changed_at": item.get("status_changed_at") or "",
                "labels": item.get("labels", []),
                "project_key": item.get("project_key") or "",
            })
        return entities


def drain_fetch_meta() -> dict[str, Any]:
    """Read and clear the thread-local fetch metadata (HS-167-02).

    Returns a dict with provider-reported metrics (e.g. ``calls``)
    from the most recent snapshot fetch on this thread, or ``{}``.
    """
    meta: dict[str, Any] = {}
    calls = getattr(_fetch_meta, "calls", None)
    if calls is not None:
        meta["calls"] = calls
        _fetch_meta.calls = None
    return meta


# ── MeetingWatchSource (HS-175-04) ─────────────────────────────────


class MeetingWatchSource:
    """Snapshot adapter for local meeting Watch entities.

    HS-175-04.  Reads from the local DB only (meetings, meeting_projects,
    intel_job_attempts, decision_records, decision_commitments).  Zero
    egress -- Article III satisfied.

    query_kind: ``"meetings"``
    query: ``{"project_id": "..."}``
    """

    def __init__(self, *, db: Any = None) -> None:
        self._db = db

    def snapshot(self, principal: Principal, *, query_kind: str,
                 query: dict[str, Any]) -> list[dict[str, Any]]:
        if query_kind != "meetings":
            raise ValidationError("Meeting Watches support meetings")

        project_id = str(query.get("project_id") or "").strip()
        if not project_id:
            raise ValidationError(
                "Meeting Watch requires project_id in the query"
            )

        db = self._db
        if db is None:
            from holdspeak.db import get_database
            db = get_database()

        with db._connection() as conn:
            # 1. Find meetings linked to this project
            meeting_rows = conn.execute(
                "SELECT meeting_id FROM meeting_projects WHERE project_id = ?",
                (project_id,),
            ).fetchall()
            if not meeting_rows:
                return []

            meeting_ids = [str(r["meeting_id"]) for r in meeting_rows]
            placeholders = ",".join("?" * len(meeting_ids))

            # 2. Load meeting data
            meetings = conn.execute(
                f"""SELECT id, title, started_at, ended_at,
                           intel_status, intel_completed_at
                    FROM meetings
                    WHERE id IN ({placeholders})
                    ORDER BY started_at DESC""",
                meeting_ids,
            ).fetchall()

            # 3. Count participants (speakers) per meeting
            participant_counts: dict[str, int] = {}
            for mid in meeting_ids:
                row = conn.execute(
                    "SELECT COUNT(DISTINCT speaker) AS cnt FROM segments WHERE meeting_id = ?",
                    (mid,),
                ).fetchone()
                participant_counts[mid] = int(row["cnt"]) if row and row["cnt"] else 0

            # 4. Count decisions per meeting (via decision_record_sources)
            decisions_counts: dict[str, int] = {}
            for mid in meeting_ids:
                row = conn.execute(
                    """SELECT COUNT(DISTINCT s.record_id) AS cnt
                       FROM decision_record_sources s
                       JOIN decision_records r ON r.id = s.record_id
                       WHERE s.source_type = 'meeting' AND s.source_ref = ?
                         AND r.deleted = 0""",
                    (mid,),
                ).fetchone()
                decisions_counts[mid] = int(row["cnt"]) if row and row["cnt"] else 0

            # 5. Count commitments per meeting (via decisions)
            commitments_counts: dict[str, int] = {}
            for mid in meeting_ids:
                row = conn.execute(
                    """SELECT COUNT(DISTINCT dc.id) AS cnt
                       FROM decision_commitments dc
                       JOIN decision_records r ON dc.decision_id = r.source_id
                       JOIN decision_record_sources s ON s.record_id = r.id
                       WHERE s.source_type = 'meeting' AND s.source_ref = ?
                         AND r.deleted = 0""",
                    (mid,),
                ).fetchone()
                commitments_counts[mid] = int(row["cnt"]) if row and row["cnt"] else 0

            # 6. Latest intel run timestamp per meeting
            intel_timestamps: dict[str, str] = {}
            for mid in meeting_ids:
                row = conn.execute(
                    """SELECT MAX(created_at) AS latest
                       FROM intel_job_attempts
                       WHERE meeting_id = ? AND outcome = 'success'""",
                    (mid,),
                ).fetchone()
                if row and row["latest"]:
                    intel_timestamps[mid] = str(row["latest"])

            # 7. Latest commitment updated_at per meeting
            commitment_timestamps: dict[str, str] = {}
            for mid in meeting_ids:
                row = conn.execute(
                    """SELECT MAX(dc.updated_at) AS latest
                       FROM decision_commitments dc
                       JOIN decision_records r ON dc.decision_id = r.source_id
                       JOIN decision_record_sources s ON s.record_id = r.id
                       WHERE s.source_type = 'meeting' AND s.source_ref = ?
                         AND r.deleted = 0""",
                    (mid,),
                ).fetchone()
                if row and row["latest"]:
                    commitment_timestamps[mid] = str(row["latest"])

        # Build entities
        entities: list[dict[str, Any]] = []
        for meeting in meetings:
            mid = str(meeting["id"])
            started_at = str(meeting["started_at"] or "")
            intel_status_raw = str(meeting["intel_status"] or "disabled")

            # Map intel_status to the brief vocabulary
            if intel_status_raw in ("completed", "success"):
                intel_status = "ran"
            elif intel_status_raw in ("failed", "error"):
                intel_status = "failed"
            else:
                intel_status = "off"

            # updated_at = max(intel run, commitment change, started_at)
            candidates = [started_at]
            if mid in intel_timestamps:
                candidates.append(intel_timestamps[mid])
            if mid in commitment_timestamps:
                candidates.append(commitment_timestamps[mid])
            updated_at = max(c for c in candidates if c) if candidates else started_at

            entities.append({
                "id": mid,
                "entity_type": "meeting",
                "title": str(meeting["title"] or "Untitled meeting"),
                "date": started_at,
                "participants": participant_counts.get(mid, 0),
                "decisions_count": decisions_counts.get(mid, 0),
                "commitments_count": commitments_counts.get(mid, 0),
                "intel_status": intel_status,
                "updated_at": updated_at,
            })

        return entities


# ── Snapshot fetcher factory (rider-a: one shape for all callers) ───


class ConfluenceWatchSource:
    """Snapshot adapter for Confluence Watches via ConfluenceProviderAdapter.

    HS-174-07.  Supports two query kinds:
    - ``recent_blogs``: ``blog list --space-id S`` entities.
    - ``pages_by_id``: ``page view --id`` for each configured page ID.

    No ``page list`` or ``page search`` -- a query asking for it gets
    a typed ``unsupported_by_cli`` error, never a silent empty snapshot.
    """

    def __init__(self, *, adapter: Any = None) -> None:
        self._adapter = adapter

    def snapshot(self, principal: Principal, *, query_kind: str,
                 query: dict[str, Any]) -> list[dict[str, Any]]:
        # M-1: clear-on-entry
        drain_fetch_meta()

        if query_kind not in ("recent_blogs", "pages_by_id"):
            raise ValidationError(
                f"Confluence Watches support recent_blogs and pages_by_id, "
                f"not {query_kind!r}"
            )

        connection_ref_str = str(query.get("connection_ref") or "").strip()
        if not connection_ref_str or "|" not in connection_ref_str:
            raise ValidationError(
                "Confluence Watch requires connection_ref (site|email)"
            )

        adapter = self._adapter
        if adapter is None:
            from holdspeak.db import get_database
            from holdspeak.services.confluence_provider import ConfluenceProviderAdapter
            adapter = ConfluenceProviderAdapter(db=get_database())

        if query_kind == "recent_blogs":
            space_id = str(query.get("space_id") or "").strip()
            if not space_id:
                raise ValidationError(
                    "recent_blogs requires space_id in the query"
                )
            limit = max(1, min(int(query.get("limit") or 25), 100))
            result = adapter.fetch_recent_blogs(
                principal, connection_ref_str,
                space_id=space_id, limit=limit,
            )
        elif query_kind == "pages_by_id":
            page_ids = query.get("page_ids") or []
            if not isinstance(page_ids, list):
                page_ids = [str(page_ids)]
            page_ids = [str(pid).strip() for pid in page_ids if str(pid).strip()]
            if not page_ids:
                # No page IDs configured -- return empty, not an error
                return []
            result = adapter.fetch_pages_by_id(
                principal, connection_ref_str,
                page_ids=page_ids,
            )
        else:
            raise ValidationError(f"Unsupported query kind: {query_kind!r}")

        state = result.get("state", "")
        error_code = result.get("error_code")

        if state != "ready":
            from holdspeak.services.confluence_provider import CODE_UNSUPPORTED_BY_CLI
            if error_code == CODE_UNSUPPORTED_BY_CLI:
                raise ServiceError(
                    "unsupported_by_cli",
                    result.get("error_detail") or "Operation not supported by acli confluence",
                )
            code_map = {
                "query_invalid": "connector_query_invalid",
                "authentication_required": "authentication_required",
                "unavailable": "connector_unavailable",
            }
            se_code = code_map.get(error_code or "", "connector_refresh_failed")
            detail = result.get("error_detail") or "Confluence query failed"
            raise ServiceError(se_code, str(detail)[:500])

        return result.get("items", [])


def default_snapshot_fetcher(
    *,
    github_runner: Runner | None = None,
    jira_adapter: Any | None = None,
    confluence_adapter: Any | None = None,
    meeting_db: Any | None = None,
) -> Callable[..., list[dict[str, Any]]]:
    """Build the canonical snapshot_fetcher callable.

    HS-166-03 rider-a / HS-174-07 / HS-175-04: ONE helper that web_server's
    _gh_watch_service_kwargs AND project.py's _watch_service() both use,
    ensuring the same provider injection shape for gh, jira, confluence,
    AND meeting.
    """
    def _fetcher(
        principal: Principal,
        *,
        connector_id: str,
        query_kind: str,
        query: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return fetch_watch_snapshot(
            principal,
            connector_id=connector_id,
            query_kind=query_kind,
            query=query,
            github_runner=github_runner,
            jira_adapter=jira_adapter,
            confluence_adapter=confluence_adapter,
            meeting_db=meeting_db,
        )
    return _fetcher


def fetch_watch_snapshot(principal: Principal, *, connector_id: str,
                         query_kind: str, query: dict[str, Any],
                         github_runner: Runner | None = None,
                         jira_adapter: Any | None = None,
                         confluence_adapter: Any | None = None,
                         meeting_db: Any | None = None) -> list[dict[str, Any]]:
    if connector_id == "gh":
        return GitHubWatchSource(runner=github_runner).snapshot(
            principal, query_kind=query_kind, query=query,
        )
    if connector_id == "jira":
        return JiraWatchSource(adapter=jira_adapter).snapshot(
            principal, query_kind=query_kind, query=query,
        )
    if connector_id == "confluence":
        return ConfluenceWatchSource(adapter=confluence_adapter).snapshot(
            principal, query_kind=query_kind, query=query,
        )
    if connector_id == "meeting":
        return MeetingWatchSource(db=meeting_db).snapshot(
            principal, query_kind=query_kind, query=query,
        )
    raise ServiceError(
        "connector_snapshot_adapter_unavailable",
        f"{connector_id} can accept pushed snapshots but has no local query adapter yet",
    )
