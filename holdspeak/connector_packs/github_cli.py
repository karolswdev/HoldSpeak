"""GitHub CLI connector pack.

HS-11-04. Wraps the phase-9 `activity_github` connector as a
phase-11 pack with a read-only `gh` command policy + manifest.

The pack's command policy is the *source of truth* for which
`gh` invocations the runtime is allowed to issue on behalf of
the user. Anything not on this list is rejected before exec.

`is_command_allowed(command)` is the validator. Pack-aware
runtimes call it before shelling out; the existing
`activity_github.run_github_cli_enrichment` already only ever
builds `gh pr view` / `gh issue view` plans, but having the
allowlist as a separate, testable policy guards against future
drift.
"""

from __future__ import annotations

from typing import Iterable

from ..activity_github import CONNECTOR_ID
from ..connector_sdk import ConnectorManifest, validate_manifest

# Allowed `gh` subcommand prefixes. A command is allowed if its
# first two argv tokens (subcommand + verb) match one of these
# tuples. The third+ tokens are subject only to the existing
# argument-shape checks in `activity_github`. Any new
# subcommand has to land here AND in the connector's plan
# generator before it can run.
ALLOWED_SUBCOMMANDS: frozenset[tuple[str, str]] = frozenset(
    {
        ("pr", "view"),
        ("issue", "view"),
    }
)

# Default tunables for runtime execution.
DEFAULT_TIMEOUT_SECONDS: float = 5.0
DEFAULT_MAX_BYTES: int = 65536
DEFAULT_LIMIT: int = 25


def is_command_allowed(command: Iterable[str]) -> bool:
    """Return True iff the given `gh` argv is on the read-only allowlist.

    The first token is expected to be the `gh` binary path (or
    just `"gh"`); the second + third tokens are the
    subcommand-verb pair we check against `ALLOWED_SUBCOMMANDS`.
    Mutating verbs like `pr edit`, `issue close`, `pr merge`,
    `auth login` are rejected.
    """
    tokens = list(command)
    if len(tokens) < 3:
        return False
    subcommand = (str(tokens[1]).lower(), str(tokens[2]).lower())
    return subcommand in ALLOWED_SUBCOMMANDS


MANIFEST: ConnectorManifest = validate_manifest(
    {
        "id": CONNECTOR_ID,
        "label": "GitHub CLI",
        "version": "0.1.0",
        "kind": "cli_enrichment",
        "capabilities": ["annotations", "commands"],
        "description": (
            "Read-only `gh pr view` / `gh issue view` calls for "
            "imported PR/issue activity. Disabled by default. "
            "No writes; no token management; no hidden network "
            "execution."
        ),
        "requires_cli": "gh",
        "requires_network": True,
        "permissions": [
            "read:activity_records",
            "write:activity_annotations",
            "shell:exec",
            "network:outbound",
        ],
        "source_boundary": (
            "Local `gh` CLI subprocess. Only commands listed in "
            "ALLOWED_SUBCOMMANDS are permitted; anything else is "
            "rejected before exec."
        ),
        "dry_run": True,
    }
)
