"""Jira CLI connector pack.

HS-11-05. Wraps the phase-9 `activity_jira` connector as a
phase-11 pack with a read-only `jira` command policy +
manifest.

Same shape as `github_cli.py` — see that module for the policy
rationale. Mutating verbs (`issue create`, `issue assign`,
`issue transition`, `auth login`) are explicitly rejected.
"""

from __future__ import annotations

from typing import Iterable

from ..activity_jira import CONNECTOR_ID
from ..connector_sdk import ConnectorManifest, validate_manifest

# Allowed `jira` subcommand prefixes — read-only verbs only.
# `jira issue view KEY --plain` is the canonical enrichment
# call; `--plain` is just an output flag and not enforced here
# (the pack's caller supplies the args).
ALLOWED_SUBCOMMANDS: frozenset[tuple[str, str]] = frozenset(
    {
        ("issue", "view"),
    }
)

DEFAULT_TIMEOUT_SECONDS: float = 5.0
DEFAULT_MAX_BYTES: int = 65536
DEFAULT_LIMIT: int = 25


def is_command_allowed(command: Iterable[str]) -> bool:
    """Return True iff the given `jira` argv is on the read-only allowlist."""
    tokens = list(command)
    if len(tokens) < 3:
        return False
    subcommand = (str(tokens[1]).lower(), str(tokens[2]).lower())
    return subcommand in ALLOWED_SUBCOMMANDS


MANIFEST: ConnectorManifest = validate_manifest(
    {
        "id": CONNECTOR_ID,
        "label": "Jira CLI",
        "version": "0.1.0",
        "kind": "cli_enrichment",
        "capabilities": ["annotations", "commands"],
        "description": (
            "Read-only `jira issue view KEY --plain` calls for "
            "imported ticket activity. Disabled by default. No "
            "writes, no transitions, no hidden network execution."
        ),
        "requires_cli": "jira",
        "requires_network": True,
        "permissions": [
            "read:activity_records",
            "write:activity_annotations",
            "shell:exec",
            "network:outbound",
        ],
        "source_boundary": (
            "Local `jira` CLI subprocess. Only commands listed "
            "in ALLOWED_SUBCOMMANDS are permitted; anything "
            "else is rejected before exec."
        ),
        "dry_run": True,
    }
)
