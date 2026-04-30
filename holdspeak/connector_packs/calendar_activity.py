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

from ..activity_candidates import CALENDAR_CONNECTOR_ID, CALENDAR_DOMAINS
from ..connector_sdk import ConnectorManifest, validate_manifest

DEFAULT_LIMIT: int = 50

RECOGNIZED_DOMAINS: frozenset[str] = CALENDAR_DOMAINS

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
    }
)
