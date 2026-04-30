"""Registry of activity-enrichment connectors known to the local runtime.

HS-9-12 makes this list visible in the browser. Anything that
writes into `activity_annotations` or `activity_meeting_candidates`
is a connector and lives here so `/activity` can render its state,
toggle its enablement, and clear its output.

The registry is intentionally small and static. Phase 11 will
generalize it (manifest-driven connector packs); for now the three
in-tree connectors (gh, jira, calendar_activity) are enumerated
explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .activity_candidates import CALENDAR_CONNECTOR_ID
from .activity_github import CONNECTOR_ID as GH_CONNECTOR_ID, github_cli_status
from .activity_jira import CONNECTOR_ID as JIRA_CONNECTOR_ID, jira_cli_status


@dataclass(frozen=True)
class ConnectorDescriptor:
    """Static metadata for one known activity connector."""

    id: str
    label: str
    kind: str
    capabilities: tuple[str, ...]
    requires_cli: Optional[str] = None
    description: str = ""

    def cli_status(self) -> Optional[dict]:
        if self.id == GH_CONNECTOR_ID:
            return github_cli_status()
        if self.id == JIRA_CONNECTOR_ID:
            return jira_cli_status()
        return None


KNOWN_CONNECTORS: tuple[ConnectorDescriptor, ...] = (
    ConnectorDescriptor(
        id=GH_CONNECTOR_ID,
        label="GitHub CLI",
        kind="cli_enrichment",
        capabilities=("annotations",),
        requires_cli="gh",
        description=(
            "Read-only `gh` calls that attach local annotations to "
            "imported PR/issue activity. Disabled by default."
        ),
    ),
    ConnectorDescriptor(
        id=JIRA_CONNECTOR_ID,
        label="Jira CLI",
        kind="cli_enrichment",
        capabilities=("annotations",),
        requires_cli="jira",
        description=(
            "Read-only `jira` calls that attach local annotations "
            "to imported ticket activity. Disabled by default."
        ),
    ),
    ConnectorDescriptor(
        id=CALENDAR_CONNECTOR_ID,
        label="Calendar candidates",
        kind="candidate_inference",
        capabilities=("candidates",),
        requires_cli=None,
        description=(
            "Infers meeting candidates from existing calendar / "
            "video-call activity records. No network, no CLI."
        ),
    ),
)

KNOWN_CONNECTOR_IDS: frozenset[str] = frozenset(c.id for c in KNOWN_CONNECTORS)


def get_descriptor(connector_id: str) -> Optional[ConnectorDescriptor]:
    for descriptor in KNOWN_CONNECTORS:
        if descriptor.id == connector_id:
            return descriptor
    return None
