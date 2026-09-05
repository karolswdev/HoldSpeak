"""HS-169-02: The Streamlined Door — one-screen project creation.

Composes existing services (no new tables).  Two routes:
  POST /api/projects/door/count  — live snapshot counts
  POST /api/projects/door         — one-call project + watches

The count path builds the SAME stored query shape and runs the SAME
WatchSource.snapshot the evaluation path uses.  Parity is tested in
tests/unit/test_hs169_door.py.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from holdspeak.principals import Principal
from holdspeak.services.errors import ServiceError

DOOR_DEFAULTS: dict[str, list[dict[str, Any]]] = {
    "github": [
        {"key": "open_prs", "label": "OPEN PRS", "template_id": "watch.github.review_queue", "on": True},
        {"key": "ci", "label": "CI", "template_id": "watch.github.branch_ci", "on": True},
    ],
    "jira": [
        {"key": "overdue", "label": "OVERDUE", "template_id": "watch.jira.due_risk", "on": True},
        {"key": "due_7_days", "label": "DUE 7 DAYS", "template_id": "watch.jira.delivery_flow", "on": True},
        {"key": "blocked", "label": "BLOCKED", "template_id": "watch.jira.blockers", "on": False},
    ],
}

_DEFAULTS_BY_KEY: dict[str, dict[str, Any]] = {}
for _provider_rows in DOOR_DEFAULTS.values():
    for _row in _provider_rows:
        _DEFAULTS_BY_KEY[_row["key"]] = _row


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _egress_host(provider: str, scope: Any) -> str:
    if provider == "github":
        return "GITHUB.COM"
    if provider == "jira" and isinstance(scope, dict):
        ref = str(scope.get("connection_ref") or "")
        site = ref.split("|")[0].strip() if "|" in ref else ref
        if site:
            return site.upper()
    return ""


def _flatten_github_query(spec: dict[str, Any]) -> dict[str, Any]:
    """Flatten a compiled GitHub WatchSpec into the stored query shape
    that create_from_setup uses (project_service.py ~L630)."""
    subject = spec.get("subject", {})
    query = dict(subject.get("query", {}))
    repos = subject.get("scope", {}).get("repositories", [])
    if repos:
        query["repository"] = repos[0]
    return query


def _flatten_jira_query(spec: dict[str, Any]) -> dict[str, Any]:
    """Flatten a compiled Jira WatchSpec into the stored query shape
    that create_from_setup uses (project_service.py ~L636)."""
    subject = spec.get("subject", {})
    query = dict(subject.get("query", {}))
    scope = subject.get("scope", {})
    conn_ref = scope.get("connection_ref") or spec.get("provider", {}).get("connection_ref")
    if conn_ref:
        query["connection_ref"] = conn_ref
    projects = scope.get("projects", [])
    if projects:
        query["projects"] = list(projects)
    issue_types = scope.get("issue_types", [])
    if issue_types:
        query["issue_types"] = list(issue_types)
    return query


def _ci_label(entities: list[dict[str, Any]]) -> str:
    """Derive a CI label from branch_ci snapshot entities."""
    if not entities:
        return "CI —"
    conclusion = entities[0].get("conclusion")
    if conclusion == "success":
        return "CI green"
    if conclusion in ("failure", "timed_out", "cancelled"):
        return "CI red"
    status = entities[0].get("status")
    if status == "in_progress":
        return "CI running"
    return "CI —"


def _count_label(key: str, count: int, entities: list[dict[str, Any]]) -> str:
    if key == "ci":
        return _ci_label(entities)
    labels: dict[str, str] = {
        "open_prs": "open PRs",
        "overdue": "overdue",
        "due_7_days": "due this week",
        "blocked": "blocked",
    }
    suffix = labels.get(key, key)
    return f"{count} {suffix}"


class ProjectDoorService:
    def __init__(
        self,
        *,
        project_service: Any = None,
        watch_service: Any = None,
        gh_runner: Any = None,
        jira_adapter: Any = None,
    ) -> None:
        self._project_service = project_service
        self._watch_service = watch_service
        self._gh_runner = gh_runner
        self._jira_adapter = jira_adapter

    def count(
        self,
        principal: Principal,
        provider: str,
        scope: Any,
        watches: list[str],
        adjust: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        host = _egress_host(provider, scope)
        now = _iso_now()
        adjust = adjust or {}

        try:
            tokens: list[dict[str, Any]] = []
            for key in watches:
                default = _DEFAULTS_BY_KEY.get(key)
                if not default:
                    continue
                entities = self._snapshot_for_key(
                    principal, provider, scope, key, default["template_id"], adjust,
                )
                count = len(entities)
                label = _count_label(key, count, entities)
                tokens.append({"key": key, "label": label, "count": count})

            plain = " · ".join(t["label"] for t in tokens)
            return {
                "tokens": tokens,
                "plain": plain,
                "checkedAt": now,
                "host": host,
                "state": "live",
                "reason": None,
            }
        except ServiceError as exc:
            return {
                "tokens": [],
                "plain": "",
                "checkedAt": now,
                "host": host,
                "state": "cant_check",
                "reason": str(exc.detail)[:500],
            }
        except Exception as exc:
            return {
                "tokens": [],
                "plain": "",
                "checkedAt": now,
                "host": host,
                "state": "cant_check",
                "reason": str(exc)[:500],
            }

    def _snapshot_for_key(
        self,
        principal: Principal,
        provider: str,
        scope: Any,
        key: str,
        template_id: str,
        adjust: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Run the snapshot for one door default using the SAME path
        that evaluation uses."""
        from holdspeak.services.watch_sources import (
            GitHubWatchSource,
            JiraWatchSource,
        )

        if provider == "github":
            repo = str(scope) if isinstance(scope, str) else ""
            if key == "ci":
                spec = self._compile_ci_watch(repo, adjust)
                stored_query = _flatten_github_query(spec)
                return GitHubWatchSource(runner=self._gh_runner).snapshot(
                    principal, query_kind="branch_ci", query=stored_query,
                )
            spec = self._compile_github(template_id, repo, adjust)
            stored_query = _flatten_github_query(spec)
            return GitHubWatchSource(runner=self._gh_runner).snapshot(
                principal, query_kind="pull_requests", query=stored_query,
            )

        if provider == "jira":
            jira_scope = scope if isinstance(scope, dict) else {}
            spec = self._compile_jira(template_id, jira_scope, adjust)
            stored_query = _flatten_jira_query(spec)
            return JiraWatchSource(adapter=self._jira_adapter).snapshot(
                principal, query_kind="issues", query=stored_query,
            )

        raise ServiceError("unknown_provider", f"Unknown provider: {provider}")

    def _compile_github(
        self,
        template_id: str,
        repo: str,
        adjust: dict[str, Any],
    ) -> dict[str, Any]:
        from holdspeak import github_templates
        options: dict[str, Any] = {}
        if "base" in adjust:
            options["base"] = adjust["base"]
        if "labels" in adjust:
            options["labels"] = adjust["labels"]
        return github_templates.compile(template_id, repo, options)

    def _compile_jira(
        self,
        template_id: str,
        scope: dict[str, Any],
        adjust: dict[str, Any],
    ) -> dict[str, Any]:
        from holdspeak import jira_templates
        site_scope = {
            "connection_ref": scope.get("connection_ref", ""),
            "projects": scope.get("projects", []),
            "issue_types": adjust.get("issueTypes", []),
        }
        spec = jira_templates.compile(template_id, site_scope)
        if adjust.get("jql"):
            spec["subject"]["query"]["jql"] = adjust["jql"]
        return spec

    def create(
        self,
        principal: Principal,
        outcome: str,
        sources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if self._project_service is None:
            raise ServiceError(
                "project_service_missing",
                "ProjectDoorService requires a composed ProjectService",
            )

        name = (outcome[:80]).strip() or "New Project"

        proposals: list[dict[str, Any]] = []
        for source in sources:
            provider = source.get("provider", "")
            scope = source.get("scope")
            watch_keys = source.get("watches", [])
            adjust = source.get("adjust") or {}

            for key in watch_keys:
                default = _DEFAULTS_BY_KEY.get(key)
                if not default:
                    continue

                template_id = default["template_id"]
                if provider == "github":
                    repo = str(scope) if isinstance(scope, str) else ""
                    if key == "ci":
                        spec = self._compile_ci_watch(repo, adjust)
                    else:
                        spec = self._compile_github(template_id, repo, adjust)
                elif provider == "jira":
                    jira_scope = scope if isinstance(scope, dict) else {}
                    spec = self._compile_jira(template_id, jira_scope, adjust)
                else:
                    continue

                proposals.append({
                    "id": f"door_{uuid.uuid4().hex[:12]}",
                    "spec": spec,
                    "state": "selected",
                    "test_state": "passed",
                })

        setup_payload = {
            "name": name,
            "purpose": outcome,
            "outcome_text": outcome,
            "lifecycle": "active",
            "proposals": proposals,
            "session_id": None,
        }

        cmd_id = f"pcmd_{uuid.uuid4().hex[:12]}"
        result = self._project_service.create_from_setup(
            principal, setup_payload, command_id=cmd_id,
        )

        activated = result.get("activated_watches", [])
        if activated and self._watch_service is not None:
            for aw in activated:
                wid = aw.get("watch_id", "")
                if not wid:
                    continue
                try:
                    self._watch_service.baseline_watch(principal, wid)
                except Exception:
                    try:
                        self._watch_service._repo.update_watch_spec(
                            wid, baseline_state="pending",
                        )
                    except Exception:
                        pass

        return {"projectId": result.get("project_id", "")}

    def _compile_ci_watch(
        self,
        repo: str,
        adjust: dict[str, Any],
    ) -> dict[str, Any]:
        """Compile the CI Watch spec using branch_ci query kind.

        Uses the branch_ci template from github_templates but overrides
        subject.kind to "branch_ci" (the generic compile hard-codes
        "pull_request"; branch_ci needs its own kind for query routing).
        """
        from holdspeak import github_templates
        options: dict[str, Any] = {}
        if "base" in adjust:
            options["base"] = adjust["base"]
        spec = github_templates.compile("watch.github.branch_ci", repo, options)
        spec["subject"]["kind"] = "branch_ci"
        return spec
