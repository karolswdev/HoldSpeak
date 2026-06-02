"""Calendar-candidates connector pack.

HS-13-01. Wraps the phase-9 `activity_candidates` calendar
extractor as a phase-13 pack with a manifest. Same shape as
`firefox_ext` / `github_cli` / `jira_cli`: the manifest is
the source of truth for the pack's identity, capabilities,
and permission surface; the inference logic itself stays in
`activity_candidates`.

This pack is the calendar arm of the activity-enrichment
trio — it never shells out, never opens a network socket,
and never touches files outside HoldSpeak's data dir. All
it does is read existing `activity_records` rows for known
calendar / video-call domains and propose meeting candidates.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from ..activity_candidates import (
    CALENDAR_CONNECTOR_ID,
    CALENDAR_DOMAINS,
    preview_calendar_meeting_candidates,
)
from ..connector_sdk import ConnectorManifest, validate_manifest

DEFAULT_LIMIT: int = 50

RECOGNIZED_DOMAINS: frozenset[str] = CALENDAR_DOMAINS


def run(db: Any, *, limit: Optional[int] = None) -> dict[str, Any]:
    """Pipeline-runner entry point. HS-13-06.

    Walks the local activity ledger for calendar / video-call
    domains and persists each derived preview as an
    `activity_meeting_candidates` row. Pure read-and-derive
    over local rows — no network, no CLI.
    """
    capped = max(1, min(int(limit if limit is not None else DEFAULT_LIMIT), 200))
    started_at = datetime.now()
    records = db.activity.list_activity_records(limit=max(capped * 4, 50))
    previews = preview_calendar_meeting_candidates(records, limit=capped)
    persisted = 0
    output_bytes = 0
    for preview in previews:
        db.activity.create_activity_meeting_candidate(
            source_connector_id=CALENDAR_CONNECTOR_ID,
            source_activity_record_id=preview.source_activity_record_id,
            title=preview.title,
            starts_at=preview.starts_at,
            ends_at=preview.ends_at,
            meeting_url=preview.meeting_url,
            confidence=preview.confidence,
        )
        persisted += 1
        output_bytes += len(preview.title.encode("utf-8")) + len(
            (preview.meeting_url or "").encode("utf-8")
        )
    finished_at = datetime.now()
    db.activity.record_connector_run(
        connector_id=CALENDAR_CONNECTOR_ID,
        started_at=started_at,
        finished_at=finished_at,
        succeeded=True,
        output_bytes=output_bytes,
        candidate_count=persisted,
    )
    return {"connector_id": CALENDAR_CONNECTOR_ID, "candidate_count": persisted}

MANIFEST: ConnectorManifest = validate_manifest(
    {
        "id": CALENDAR_CONNECTOR_ID,
        "label": "Calendar candidates",
        "version": "0.1.0",
        "kind": "candidate_inference",
        "capabilities": ["candidates"],
        "description": (
            "Infers meeting candidates from existing calendar / "
            "video-call activity records. No network, no CLI."
        ),
        "requires_cli": None,
        "requires_network": False,
        "permissions": [
            "read:activity_records",
            "write:activity_meeting_candidates",
        ],
        "source_boundary": (
            "Pure read over local `activity_records`. The pack "
            "matches records whose domain is in "
            "RECOGNIZED_DOMAINS (Google Calendar, Outlook, Meet, "
            "Teams) and proposes candidates only — it does not "
            "touch any other table or external resource."
        ),
        "dry_run": True,
        "settings_schema": [
            {
                "key": "limit",
                "type": "int",
                "default": DEFAULT_LIMIT,
                "label": "Candidates per run",
                "help": (
                    "Max number of meeting candidates inferred per "
                    "preview / dry-run pass."
                ),
            },
        ],
    }
)
