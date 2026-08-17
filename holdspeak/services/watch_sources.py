"""Typed connector snapshot adapters used by Watches.

The adapter owns CLI output interpretation. Reactions only ever see normalized
entities and therefore never mine arbitrary tool presentation text.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from typing import Any

from holdspeak.connector_packs import github_cli
from holdspeak.connector_runtime import PermissionGate
from holdspeak.delivery.pr_receipts import rollup_conclusion
from holdspeak.principals import Principal
from holdspeak.services.errors import ServiceError, ValidationError


Runner = Callable[..., subprocess.CompletedProcess[str]]

GH_WATCH_FIELDS = (
    "number,title,url,state,isDraft,reviewRequests,reviewDecision,"
    "statusCheckRollup,headRefOid,updatedAt"
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


class GitHubWatchSource:
    def __init__(self, *, runner: Runner | None = None) -> None:
        self._runner = runner

    def snapshot(self, principal: Principal, *, query_kind: str,
                 query: dict[str, Any]) -> list[dict[str, Any]]:
        if query_kind != "pull_requests":
            raise ValidationError("GitHub Watches support pull_requests")
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
            })
        return entities


def fetch_watch_snapshot(principal: Principal, *, connector_id: str,
                         query_kind: str, query: dict[str, Any],
                         github_runner: Runner | None = None) -> list[dict[str, Any]]:
    if connector_id == "gh":
        return GitHubWatchSource(runner=github_runner).snapshot(
            principal, query_kind=query_kind, query=query,
        )
    raise ServiceError(
        "connector_snapshot_adapter_unavailable",
        f"{connector_id} can accept pushed snapshots but has no local query adapter yet",
    )
