"""Meeting-context pipeline pack.

HS-13-07. The first first-party `kind: pipeline` pack: it
fuses gh + jira annotations and calendar candidates with the
local activity ledger into a single per-project briefing
annotation. The output is mutation-safe — re-running the
pipeline updates each project's briefing in place rather than
appending duplicates.

The synthesizer is deterministic markdown for now: bullets
listing PRs touched, tickets seen, upcoming calendar events.
A future phase-14 story can layer an LLM summary on top of
the same `value` payload.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Iterable, Optional

from ..connector_sdk import ConnectorManifest, validate_manifest

CONNECTOR_ID = "meeting_context"
ANNOTATION_TYPE = "meeting_context_briefing"

# Briefing window: how far back to scan activity records when
# the connector has never run. Subsequent runs use the time
# since the last successful pipeline invocation, capped by this
# window so a long pause doesn't produce an unwieldy briefing.
DEFAULT_LOOKBACK_HOURS: int = 24

DEFAULT_LIMIT: int = 100


MANIFEST: ConnectorManifest = validate_manifest(
    {
        "id": CONNECTOR_ID,
        "label": "Meeting context",
        "version": "0.1.0",
        "kind": "pipeline",
        "capabilities": ["annotations"],
        "description": (
            "Per-project briefing fused from gh annotations, jira "
            "annotations, and calendar candidates — the visible "
            "payoff of the connector framework. Deterministic "
            "markdown; re-running updates each project's briefing "
            "in place."
        ),
        "requires_cli": None,
        "requires_network": False,
        "permissions": [
            "read:activity_records",
            "read:activity_annotations",
            "read:activity_meeting_candidates",
            "write:activity_annotations",
        ],
        "source_boundary": (
            "Pure read over local rows produced by upstream packs. "
            "Writes one annotation per active project to "
            "`activity_annotations` with source_connector_id = "
            "'meeting_context'."
        ),
        "dry_run": True,
        "consumes": [
            {"pack_id": "gh", "output_kind": "annotations"},
            {"pack_id": "jira", "output_kind": "annotations"},
            {"pack_id": "calendar_activity", "output_kind": "candidates"},
        ],
        "pipeline_freshness_seconds": 600,
        "settings_schema": [
            {
                "key": "lookback_hours",
                "type": "int",
                "default": DEFAULT_LOOKBACK_HOURS,
                "label": "Lookback window (hours)",
                "help": (
                    "How far back the briefing scans activity when "
                    "the pipeline has not run before. Subsequent "
                    "runs scan since the previous successful run, "
                    "capped by this value."
                ),
            },
        ],
    }
)


# ──────────────────────── Synthesizer ────────────────────────


def synthesize_briefing(
    *,
    project_name: str,
    gh_annotations: Iterable[Any],
    jira_annotations: Iterable[Any],
    calendar_candidates: Iterable[Any],
) -> str:
    """Render a deterministic markdown briefing.

    Pure function — no DB, no clock, no I/O. The shape is the
    contract phase-14 LLM swap-ins (or an alternate renderer)
    will preserve. Empty inputs render the "nothing changed"
    bullet rather than raising; that's the AC's "empty upstream
    → empty briefing annotation" path.
    """
    gh_list = sorted(
        (_label_for_gh(a) for a in gh_annotations if _label_for_gh(a)),
    )
    jira_list = sorted(
        (_label_for_jira(a) for a in jira_annotations if _label_for_jira(a)),
    )
    cal_list = sorted(
        (_label_for_candidate(c) for c in calendar_candidates if _label_for_candidate(c)),
        # Sort calendar entries by their starts_at if present
        # (already encoded in the label string), then alphabetic.
    )

    lines: list[str] = [f"# {project_name} — meeting context"]
    if gh_list:
        lines.append("")
        lines.append("## GitHub")
        lines.extend(f"- {entry}" for entry in gh_list)
    if jira_list:
        lines.append("")
        lines.append("## Jira")
        lines.extend(f"- {entry}" for entry in jira_list)
    if cal_list:
        lines.append("")
        lines.append("## Upcoming calendar")
        lines.extend(f"- {entry}" for entry in cal_list)
    if not (gh_list or jira_list or cal_list):
        lines.append("")
        lines.append("- No new activity since the last meeting.")
    return "\n".join(lines)


def _label_for_gh(annotation: Any) -> str:
    value = _annotation_value(annotation)
    entity_id = str(value.get("entity_id") or "").strip()
    title = str(getattr(annotation, "title", "") or "").strip()
    state = str(value.get("gh", {}).get("state") or "").strip().upper()
    if entity_id and title:
        if state:
            return f"{entity_id} — {title} ({state})"
        return f"{entity_id} — {title}"
    return title or entity_id


def _label_for_jira(annotation: Any) -> str:
    value = _annotation_value(annotation)
    issue_key = str(value.get("issue_key") or value.get("entity_id") or "").strip()
    title = str(getattr(annotation, "title", "") or "").strip()
    if issue_key and title:
        return f"{issue_key} — {title}"
    return title or issue_key


def _label_for_candidate(candidate: Any) -> str:
    title = str(getattr(candidate, "title", "") or "").strip()
    starts_at = getattr(candidate, "starts_at", None)
    if starts_at and isinstance(starts_at, datetime):
        return f"{starts_at.strftime('%Y-%m-%d %H:%M')} — {title}" if title else starts_at.isoformat()
    return title


def _annotation_value(annotation: Any) -> dict[str, Any]:
    value = getattr(annotation, "value", None)
    if isinstance(value, dict):
        return value
    return {}


# ──────────────────────────── Run ─────────────────────────────


def run(db: Any, *, limit: Optional[int] = None) -> dict[str, Any]:
    """Pipeline-runner entry point. HS-13-07.

    For each active project: gather recent activity records,
    fetch upstream gh / jira annotations and calendar
    candidates, synthesize markdown, persist exactly one
    `meeting_context_briefing` annotation per project. Old
    briefings for the same connector are deleted up front so
    re-running is mutation-safe.
    """
    started_at = datetime.now()

    capped = max(1, min(int(limit if limit is not None else DEFAULT_LIMIT), 1000))

    # Scan window: the last successful pipeline run (capped at
    # the lookback default), or `now - DEFAULT_LOOKBACK_HOURS`.
    state = db.get_activity_enrichment_connector(CONNECTOR_ID)
    settings = state.settings if state and state.settings else {}
    lookback_hours = int(settings.get("lookback_hours", DEFAULT_LOOKBACK_HOURS))
    fallback_since = started_at - timedelta(hours=max(1, lookback_hours))
    last_runs = db.list_connector_runs(connector_id=CONNECTOR_ID, limit=1)
    if last_runs and last_runs[0].succeeded:
        since = max(last_runs[0].finished_at, fallback_since)
    else:
        since = fallback_since

    # Fetch upstream output once. gh + jira annotations are
    # filtered after we know which records belong to which
    # project; calendar candidates apply globally.
    gh_anns = db.list_activity_annotations(source_connector_id="gh", limit=capped)
    jira_anns = db.list_activity_annotations(source_connector_id="jira", limit=capped)
    calendar_cands = db.list_activity_meeting_candidates(
        source_connector_id="calendar_activity", limit=capped
    )

    projects = [p for p in db.list_projects() if not p.is_archived]

    # HS-13-09: keep history. A run only writes a new
    # annotation per project when the synthesized markdown
    # differs from the most-recent briefing for that project —
    # so re-running with no upstream changes does not pile up
    # duplicates, but real upstream changes do append a new
    # snapshot for the /history timeline to walk.
    existing_by_project = {
        a.value.get("project_id"): a
        for a in db.list_activity_annotations(
            source_connector_id=CONNECTOR_ID,
            annotation_type=ANNOTATION_TYPE,
            limit=1000,
        )
        if isinstance(a.value, dict) and a.value.get("project_id")
    }

    created = 0
    for project in projects:
        # HS-13-09: scan the project's full record set rather
        # than time-slicing by `since`. The synthesizer dedupes
        # by content hash against the previous briefing — runs
        # that produce identical markdown skip the write — so a
        # narrow time window would mask new annotations on
        # older records (gh / jira can enrich existing PRs/
        # tickets long after they were first visited).
        records = db.list_activity_records(
            project_id=project.id,
            limit=capped,
        )
        record_ids = {r.id for r in records}
        project_gh = [a for a in gh_anns if a.activity_record_id in record_ids]
        project_jira = [a for a in jira_anns if a.activity_record_id in record_ids]
        project_calendar = [
            c
            for c in calendar_cands
            if c.source_activity_record_id in record_ids
        ]

        markdown = synthesize_briefing(
            project_name=project.name or project.id,
            gh_annotations=project_gh,
            jira_annotations=project_jira,
            calendar_candidates=project_calendar,
        )

        previous = existing_by_project.get(project.id)
        if previous is not None and isinstance(previous.value, dict):
            if previous.value.get("markdown") == markdown:
                # Idempotent re-run — nothing changed for this
                # project, so no new annotation row.
                continue

        db.create_activity_annotation(
            source_connector_id=CONNECTOR_ID,
            annotation_type=ANNOTATION_TYPE,
            title=f"{project.name or project.id} — meeting context",
            value={
                "project_id": project.id,
                "project_name": project.name or project.id,
                "since": since.isoformat(),
                "markdown": markdown,
                "gh_count": len(project_gh),
                "jira_count": len(project_jira),
                "calendar_count": len(project_calendar),
            },
            confidence=1.0,
        )
        created += 1

    finished_at = datetime.now()
    db.record_connector_run(
        connector_id=CONNECTOR_ID,
        started_at=started_at,
        finished_at=finished_at,
        succeeded=True,
        annotation_count=created,
    )
    db.record_activity_enrichment_run(
        connector_id=CONNECTOR_ID,
        last_run_at=finished_at,
        last_error="",
    )
    return {
        "connector_id": CONNECTOR_ID,
        "annotation_count": created,
        "since": since.isoformat(),
    }
