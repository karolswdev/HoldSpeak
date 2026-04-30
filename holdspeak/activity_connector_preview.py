"""Shared dry-run harness for activity-enrichment connectors.

HS-9-13. Each known connector (gh, jira, calendar_activity) describes
what it *would* do via this harness without writing to the database.
The result shape is the same for every connector so the browser can
render a single dry-run preview surface.

Mutation-free guarantee:

  - The harness only reads from the database (`list_activity_records`).
  - It calls each connector's preview helper, which itself does not
    mutate state (`preview_github_cli_enrichment`, `preview_jira_cli_enrichment`,
    `preview_calendar_meeting_candidates`).
  - It does not call any *_run_* helper.

Tests in `tests/integration/test_web_activity_api.py` assert that
the row counts of `activity_annotations` and
`activity_meeting_candidates` are unchanged after a dry-run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from .activity_candidates import (
    CALENDAR_CONNECTOR_ID,
    preview_calendar_meeting_candidates,
)
from .activity_connectors import KNOWN_CONNECTORS, get_descriptor
from .activity_github import (
    CONNECTOR_ID as GH_CONNECTOR_ID,
    SUPPORTED_ENTITY_TYPES as GH_SUPPORTED_ENTITY_TYPES,
    preview_github_cli_enrichment,
)
from .activity_jira import (
    CONNECTOR_ID as JIRA_CONNECTOR_ID,
    SUPPORTED_ENTITY_TYPES as JIRA_SUPPORTED_ENTITY_TYPES,
    preview_jira_cli_enrichment,
)
from .db import MeetingDatabase

DEFAULT_LIMIT = 25
MAX_LIMIT = 100

# A safety cap on the per-section length of the dry-run payload so a
# pathological local dataset cannot blow up the API response. Each
# section (commands / proposed_annotations / proposed_candidates) is
# truncated to this length and the result is flagged `truncated=True`.
PAYLOAD_SECTION_CAP = 100


@dataclass(frozen=True)
class ConnectorDryRunResult:
    """Uniform dry-run preview produced by `dry_run()`.

    Every connector returns this shape. The browser renders the same
    surface (commands → CommandPreview, proposed_* → list of cards,
    warnings + permission_notes → inline messages) regardless of the
    underlying connector kind.
    """

    connector_id: str
    kind: str
    capabilities: tuple[str, ...]
    enabled: bool
    cli_required: Optional[str]
    cli_available: Optional[bool]
    commands: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    proposed_annotations: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    proposed_candidates: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    permission_notes: tuple[str, ...] = field(default_factory=tuple)
    truncated: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "kind": self.kind,
            "capabilities": list(self.capabilities),
            "enabled": self.enabled,
            "cli_required": self.cli_required,
            "cli_available": self.cli_available,
            "commands": list(self.commands),
            "proposed_annotations": list(self.proposed_annotations),
            "proposed_candidates": list(self.proposed_candidates),
            "warnings": list(self.warnings),
            "permission_notes": list(self.permission_notes),
            "truncated": self.truncated,
        }


class UnknownConnectorError(ValueError):
    """Raised when `dry_run()` is given a connector id that isn't registered."""


def dry_run(
    db: MeetingDatabase,
    connector_id: str,
    *,
    limit: int = DEFAULT_LIMIT,
) -> ConnectorDryRunResult:
    """Build a uniform mutation-free preview for one connector.

    Returns a `ConnectorDryRunResult`. The caller is responsible for
    serializing it via `to_payload()`. The harness does not raise on
    a disabled connector or a missing CLI — those land in
    `permission_notes` so the browser can render the would-do plan
    alongside the reason it can't currently run.
    """
    descriptor = get_descriptor(connector_id)
    if descriptor is None:
        raise UnknownConnectorError(connector_id)

    capped_limit = max(1, min(int(limit), MAX_LIMIT))
    state = db.get_activity_enrichment_connector(descriptor.id)
    enabled = bool(state.enabled) if state is not None else False

    cli_required = descriptor.requires_cli
    cli_status = descriptor.cli_status() if cli_required else None
    cli_available = bool(cli_status.get("available")) if cli_status else None

    permission_notes: list[str] = []
    if not enabled:
        permission_notes.append(
            f"{descriptor.label} is currently disabled. Dry-run shows what "
            "the connector would do if you enabled it; nothing runs."
        )
    if cli_required and cli_available is False:
        permission_notes.append(
            f"`{cli_required}` CLI was not found on PATH. Install and "
            "authenticate it before enabling this connector."
        )

    warnings: list[str] = []
    commands: list[Mapping[str, Any]] = []
    proposed_annotations: list[Mapping[str, Any]] = []
    proposed_candidates: list[Mapping[str, Any]] = []

    if descriptor.id == GH_CONNECTOR_ID:
        records = []
        for entity_type in GH_SUPPORTED_ENTITY_TYPES:
            records.extend(
                db.list_activity_records(entity_type=entity_type, limit=capped_limit)
            )
        records = records[:capped_limit]
        if not records:
            warnings.append(
                "No GitHub PR or issue activity has been imported yet. "
                "Visit a PR or issue page in your browser, then refresh "
                "the activity ledger."
            )
        preview = preview_github_cli_enrichment(records, limit=capped_limit)
        commands = list(preview.get("commands", []))
        for command in commands:
            proposed_annotations.append(
                {
                    "annotation_type": command.get("annotation_type"),
                    "activity_record_id": command.get("activity_record_id"),
                    "entity_id": command.get("entity_id"),
                    "title": f"Local {command.get('annotation_type')} annotation",
                    "from_command": list(command.get("command", [])),
                }
            )

    elif descriptor.id == JIRA_CONNECTOR_ID:
        records = []
        for entity_type in JIRA_SUPPORTED_ENTITY_TYPES:
            records.extend(
                db.list_activity_records(entity_type=entity_type, limit=capped_limit)
            )
        records = records[:capped_limit]
        if not records:
            warnings.append(
                "No Jira ticket activity has been imported yet. Visit "
                "an Atlassian ticket in your browser, then refresh the "
                "activity ledger."
            )
        preview = preview_jira_cli_enrichment(records, limit=capped_limit)
        commands = list(preview.get("commands", []))
        for command in commands:
            proposed_annotations.append(
                {
                    "annotation_type": command.get("annotation_type"),
                    "activity_record_id": command.get("activity_record_id"),
                    "entity_id": command.get("entity_id"),
                    "title": f"Local {command.get('annotation_type')} annotation",
                    "from_command": list(command.get("command", [])),
                }
            )

    elif descriptor.id == CALENDAR_CONNECTOR_ID:
        records = db.list_activity_records(limit=max(capped_limit * 4, 50))
        previews = preview_calendar_meeting_candidates(records, limit=capped_limit)
        if not previews:
            warnings.append(
                "No calendar / video-call activity has been imported "
                "yet. Visit a Google Calendar event, Outlook event, or "
                "Meet/Teams link, then refresh the activity ledger."
            )
        for preview in previews:
            proposed_candidates.append(
                {
                    "title": preview.title,
                    "starts_at": preview.starts_at.isoformat() if preview.starts_at else None,
                    "ends_at": preview.ends_at.isoformat() if preview.ends_at else None,
                    "meeting_url": preview.meeting_url,
                    "source_activity_record_id": preview.source_activity_record_id,
                    "source_connector_id": preview.source_connector_id,
                    "confidence": preview.confidence,
                }
            )

    truncated = False
    if len(commands) > PAYLOAD_SECTION_CAP:
        commands = commands[:PAYLOAD_SECTION_CAP]
        truncated = True
    if len(proposed_annotations) > PAYLOAD_SECTION_CAP:
        proposed_annotations = proposed_annotations[:PAYLOAD_SECTION_CAP]
        truncated = True
    if len(proposed_candidates) > PAYLOAD_SECTION_CAP:
        proposed_candidates = proposed_candidates[:PAYLOAD_SECTION_CAP]
        truncated = True

    return ConnectorDryRunResult(
        connector_id=descriptor.id,
        kind=descriptor.kind,
        capabilities=descriptor.capabilities,
        enabled=enabled,
        cli_required=cli_required,
        cli_available=cli_available,
        commands=tuple(commands),
        proposed_annotations=tuple(proposed_annotations),
        proposed_candidates=tuple(proposed_candidates),
        warnings=tuple(warnings),
        permission_notes=tuple(permission_notes),
        truncated=truncated,
    )


def known_connector_ids() -> tuple[str, ...]:
    return tuple(c.id for c in KNOWN_CONNECTORS)
