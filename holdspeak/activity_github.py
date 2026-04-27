"""Read-only GitHub CLI enrichment for local activity records."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterable, Optional

from .db import ActivityAnnotation, ActivityRecord, MeetingDatabase

CONNECTOR_ID = "gh"
SUPPORTED_ENTITY_TYPES = frozenset({"github_pull_request", "github_issue"})
_GITHUB_ENTITY_RE = re.compile(r"^([^/\s#]+)/([^/\s#]+)#(\d+)$")

_PR_FIELDS = (
    "number,title,state,author,labels,assignees,reviewRequests,"
    "reviewDecision,mergeable,isDraft,headRefName,baseRefName,url"
)
_ISSUE_FIELDS = "number,title,state,author,labels,assignees,milestone,url"


@dataclass(frozen=True)
class GithubCliCommandPlan:
    """A read-only `gh` command derived from one local activity record."""

    activity_record_id: int
    entity_type: str
    entity_id: str
    repo: str
    number: int
    command: tuple[str, ...]
    annotation_type: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "activity_record_id": self.activity_record_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "repo": self.repo,
            "number": self.number,
            "command": list(self.command),
            "annotation_type": self.annotation_type,
        }


@dataclass(frozen=True)
class GithubCliRunResult:
    """Result for one attempted `gh` enrichment command."""

    plan: GithubCliCommandPlan
    annotation: Optional[ActivityAnnotation] = None
    error: Optional[str] = None

    def to_payload(self) -> dict[str, Any]:
        payload = {"plan": self.plan.to_payload(), "error": self.error}
        if self.annotation is not None:
            payload["annotation"] = {
                "id": self.annotation.id,
                "activity_record_id": self.annotation.activity_record_id,
                "source_connector_id": self.annotation.source_connector_id,
                "annotation_type": self.annotation.annotation_type,
                "title": self.annotation.title,
                "value": self.annotation.value,
                "confidence": self.annotation.confidence,
                "created_at": self.annotation.created_at.isoformat(),
                "updated_at": self.annotation.updated_at.isoformat(),
            }
        else:
            payload["annotation"] = None
        return payload


RunCommand = Callable[..., subprocess.CompletedProcess[str]]


def github_cli_status(*, gh_path: Optional[str] = None) -> dict[str, Any]:
    """Return local `gh` availability without running network commands."""
    resolved = gh_path or shutil.which("gh")
    return {
        "connector_id": CONNECTOR_ID,
        "available": bool(resolved),
        "command_path": resolved,
    }


def preview_github_cli_enrichment(
    records: Iterable[ActivityRecord],
    *,
    gh_path: Optional[str] = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Build read-only `gh` command plans for GitHub activity records."""
    plans = _github_cli_plans(records, gh_path=gh_path, limit=limit)
    return {
        **github_cli_status(gh_path=gh_path),
        "count": len(plans),
        "commands": [plan.to_payload() for plan in plans],
    }


def run_github_cli_enrichment(
    db: MeetingDatabase,
    records: Iterable[ActivityRecord],
    *,
    gh_path: Optional[str] = None,
    limit: int = 25,
    timeout_seconds: float = 5.0,
    max_bytes: int = 65536,
    run_command: Optional[RunCommand] = None,
) -> list[GithubCliRunResult]:
    """Run planned read-only `gh` commands and persist local annotations."""
    status = github_cli_status(gh_path=gh_path)
    command_path = status["command_path"]
    if not command_path:
        raise RuntimeError("gh CLI is not available")

    plans = _github_cli_plans(records, gh_path=str(command_path), limit=limit)
    runner = run_command or subprocess.run
    results: list[GithubCliRunResult] = []
    for plan in plans:
        try:
            completed = runner(
                list(plan.command),
                capture_output=True,
                text=True,
                timeout=max(0.1, float(timeout_seconds)),
                check=False,
            )
        except subprocess.TimeoutExpired:
            results.append(GithubCliRunResult(plan=plan, error="gh command timed out"))
            continue

        if completed.returncode != 0:
            stderr = str(completed.stderr or "").strip()
            results.append(
                GithubCliRunResult(
                    plan=plan,
                    error=stderr[:400] or f"gh exited with status {completed.returncode}",
                )
            )
            continue

        stdout = str(completed.stdout or "")
        if len(stdout.encode("utf-8")) > max(1, int(max_bytes)):
            results.append(GithubCliRunResult(plan=plan, error="gh output exceeded max_bytes"))
            continue

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as exc:
            results.append(GithubCliRunResult(plan=plan, error=f"gh returned invalid JSON: {exc}"))
            continue

        title = str(data.get("title") or plan.entity_id).strip()
        db.delete_activity_annotations(
            activity_record_id=plan.activity_record_id,
            source_connector_id=CONNECTOR_ID,
            annotation_type=plan.annotation_type,
        )
        annotation = db.create_activity_annotation(
            activity_record_id=plan.activity_record_id,
            source_connector_id=CONNECTOR_ID,
            annotation_type=plan.annotation_type,
            title=title,
            value={
                "entity_id": plan.entity_id,
                "repo": plan.repo,
                "number": plan.number,
                "command": list(plan.command),
                "gh": data,
            },
            confidence=1.0,
        )
        results.append(GithubCliRunResult(plan=plan, annotation=annotation))

    failures = [result.error for result in results if result.error]
    db.record_activity_enrichment_run(
        connector_id=CONNECTOR_ID,
        last_run_at=datetime.now(),
        last_error=f"{len(failures)} gh command(s) failed" if failures else "",
    )
    return results


def _github_cli_plans(
    records: Iterable[ActivityRecord],
    *,
    gh_path: Optional[str],
    limit: int,
) -> list[GithubCliCommandPlan]:
    command_path = gh_path or "gh"
    plans: list[GithubCliCommandPlan] = []
    seen: set[tuple[str, str]] = set()
    for record in records:
        if record.entity_type not in SUPPORTED_ENTITY_TYPES or not record.entity_id:
            continue
        parsed = _parse_github_entity(record.entity_id)
        if parsed is None:
            continue
        repo, number = parsed
        key = (str(record.entity_type), f"{repo}#{number}")
        if key in seen:
            continue
        seen.add(key)
        if record.entity_type == "github_pull_request":
            command = (
                command_path,
                "pr",
                "view",
                str(number),
                "--repo",
                repo,
                "--json",
                _PR_FIELDS,
            )
            annotation_type = "github_pr"
        else:
            command = (
                command_path,
                "issue",
                "view",
                str(number),
                "--repo",
                repo,
                "--json",
                _ISSUE_FIELDS,
            )
            annotation_type = "github_issue"
        plans.append(
            GithubCliCommandPlan(
                activity_record_id=record.id,
                entity_type=record.entity_type,
                entity_id=record.entity_id,
                repo=repo,
                number=number,
                command=command,
                annotation_type=annotation_type,
            )
        )
        if len(plans) >= max(1, min(int(limit), 500)):
            break
    return plans


def _parse_github_entity(entity_id: str) -> Optional[tuple[str, int]]:
    match = _GITHUB_ENTITY_RE.match(str(entity_id or "").strip())
    if match is None:
        return None
    owner, repo, number = match.groups()
    return f"{owner}/{repo}", int(number)
