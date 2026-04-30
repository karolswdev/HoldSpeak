"""First-party connector packs.

HS-11-03..05. Each pack module exports:

  - `MANIFEST` — a `ConnectorManifest` describing the pack.
  - Pack-specific policy data (e.g. allowed CLI commands for
    gh/jira, captured fields + forbidden fields for firefox_ext).

`ALL_PACKS` is the list of pack modules in canonical order.
Phase-11 future work will register them with the runtime; for
now the packs sit alongside the existing `activity_connectors`
registry as the manifest-shaped representation of the same
three connectors.
"""

from __future__ import annotations

from . import firefox_ext, github_cli, jira_cli

ALL_PACKS = (firefox_ext, github_cli, jira_cli)

__all__ = ["ALL_PACKS", "firefox_ext", "github_cli", "jira_cli"]
