"""First-party connector packs.

HS-11-03..05 + HS-13-01. Each pack module exports:

  - `MANIFEST` — a `ConnectorManifest` describing the pack.
  - Pack-specific policy data (e.g. allowed CLI commands for
    gh/jira, captured fields + forbidden fields for firefox_ext,
    recognised domains for calendar_activity).

`ALL_PACKS` is the list of pack modules in canonical order
(records ingester first, then enrichment kinds). Phase 13's
runtime registry derives from this list — it is the source of
truth, not `activity_connectors.KNOWN_CONNECTORS` (which is now
a thin wrapper over the pack manifests).
"""

from __future__ import annotations

from . import (
    calendar_activity,
    firefox_ext,
    github_cli,
    jira_cli,
    meeting_context,
)

ALL_PACKS = (
    firefox_ext,
    github_cli,
    jira_cli,
    calendar_activity,
    meeting_context,
)

__all__ = [
    "ALL_PACKS",
    "calendar_activity",
    "firefox_ext",
    "github_cli",
    "jira_cli",
    "meeting_context",
]
