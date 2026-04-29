"""Read-only Jira CLI enrichment for local activity records."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterable, Optional

from .db import ActivityAnnotation, ActivityRecord, MeetingDatabase

CONNECTOR_ID = "jira"
SUPPORTED_ENTITY_TYPES = frozenset({"jira_ticket"})
_JIRA_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{1,9}-\d+$")


@dataclass(frozen=True)
class JiraCliCommandPlan:
    """A read-only `jira` command derived from one local activity record."""

    activity_record_id: int
    entity_type: str
    entity_id: str
    issue_key: str
    command: tuple[str, ...]
    annotation_type: str = "jira_ticket"

    def to_payload(self) -> dict[str, Any]:
        return {
            "activity_record_id": self.activity_record_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "issue_key": self.issue_key,
            "command": list(self.command),
            "annotation_type": self.annotation_type,
        }


@dataclass(frozen=True)
class JiraCliRunResult:
    """Result for one attempted `jira` enrichment command."""

    plan: JiraCliCommandPlan
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


def jira_cli_status(*, jira_path: Optional[str] = None) -> dict[str, Any]:
    """Return local `jira` availability without running network commands."""
    resolved = jira_path or shutil.which("jira")
    return {
        "connector_id": CONNECTOR_ID,
        "available": bool(resolved),
        "command_path": resolved,
    }


def preview_jira_cli_enrichment(
    records: Iterable[ActivityRecord],
    *,
    jira_path: Optional[str] = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Build read-only `jira` command plans for Jira activity records."""
    plans = _jira_cli_plans(records, jira_path=jira_path, limit=limit)
    return {
        **jira_cli_status(jira_path=jira_path),
        "count": len(plans),
        "commands": [plan.to_payload() for plan in plans],
    }


def run_jira_cli_enrichment(
    db: MeetingDatabase,
    records: Iterable[ActivityRecord],
    *,
    jira_path: Optional[str] = None,
    limit: int = 25,
    timeout_seconds: float = 5.0,
    max_bytes: int = 65536,
    run_command: Optional[RunCommand] = None,
) -> list[JiraCliRunResult]:
    """Run planned read-only `jira` commands and persist local annotations."""
    status = jira_cli_status(jira_path=jira_path)
    command_path = status["command_path"]
    if not command_path:
        raise RuntimeError("jira CLI is not available")

    plans = _jira_cli_plans(records, jira_path=str(command_path), limit=limit)
    runner = run_command or subprocess.run
    results: list[JiraCliRunResult] = []
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
            results.append(JiraCliRunResult(plan=plan, error="jira command timed out"))
            continue

        if completed.returncode != 0:
            stderr = str(completed.stderr or "").strip()
            results.append(
                JiraCliRunResult(
                    plan=plan,
                    error=stderr[:400] or f"jira exited with status {completed.returncode}",
                )
            )
            continue

        stdout = str(completed.stdout or "")
        if len(stdout.encode("utf-8")) > max(1, int(max_bytes)):
            results.append(JiraCliRunResult(plan=plan, error="jira output exceeded max_bytes"))
            continue

        parsed = _parse_jira_output(stdout)
        title = _jira_title(plan.issue_key, parsed)
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
                "issue_key": plan.issue_key,
                "command": list(plan.command),
                "jira": parsed,
            },
            confidence=1.0,
        )
        results.append(JiraCliRunResult(plan=plan, annotation=annotation))

    failures = [result.error for result in results if result.error]
    db.record_activity_enrichment_run(
        connector_id=CONNECTOR_ID,
        last_run_at=datetime.now(),
        last_error=f"{len(failures)} jira command(s) failed" if failures else "",
    )
    return results


def _jira_cli_plans(
    records: Iterable[ActivityRecord],
    *,
    jira_path: Optional[str],
    limit: int,
) -> list[JiraCliCommandPlan]:
    command_path = jira_path or "jira"
    plans: list[JiraCliCommandPlan] = []
    seen: set[str] = set()
    for record in records:
        if record.entity_type not in SUPPORTED_ENTITY_TYPES or not record.entity_id:
            continue
        issue_key = str(record.entity_id).strip().upper()
        if not _JIRA_KEY_RE.match(issue_key) or issue_key in seen:
            continue
        seen.add(issue_key)
        plans.append(
            JiraCliCommandPlan(
                activity_record_id=record.id,
                entity_type=record.entity_type,
                entity_id=issue_key,
                issue_key=issue_key,
                command=(command_path, "issue", "view", issue_key, "--plain"),
            )
        )
        if len(plans) >= max(1, min(int(limit), 500)):
            break
    return plans


def _parse_jira_output(stdout: str) -> dict[str, Any]:
    raw = str(stdout or "").strip()
    if not raw:
        return {"raw": ""}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}
    return parsed if isinstance(parsed, dict) else {"value": parsed}


def _jira_title(issue_key: str, parsed: dict[str, Any]) -> str:
    for key in ("summary", "title", "name", "key"):
        value = parsed.get(key)
        if value not in (None, ""):
            return str(value).strip()
    fields = parsed.get("fields")
    if isinstance(fields, dict):
        summary = fields.get("summary")
        if summary not in (None, ""):
            return str(summary).strip()
    return issue_key
