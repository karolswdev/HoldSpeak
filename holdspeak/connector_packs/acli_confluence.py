"""Atlassian CLI (acli) Confluence connector pack.

HS-174-07. Read-only ``acli confluence`` command policy + manifest for the
V0 Confluence provider adapter.  Mirrors ``acli_jira.py``'s idiom -- the
allowlist is the source of truth, and anything not on it is rejected
before exec.

The acli CLI shapes commands as ``acli confluence <group> <verb>`` -- the
binary is ``acli`` and the first positional is always ``confluence`` (the
product selector).  The allowlist therefore uses **3-tuples**
``(product, group, verb)`` and the command validator expects at least
four tokens: ``[acli, confluence, <group>, <verb>, ...]``.

CRITICAL GAP (settled design D3): ``acli confluence page`` has NO
``list`` or ``search`` subcommand -- only ``page view --id``.  V0 watches
BLOG POSTS via ``blog list --space-id`` and PAGES BY KNOWN ID via
``page view --id``.  No ``page list``, no Confluence REST via curl.
"""
from __future__ import annotations

from typing import Any, Iterable

from ..connector_sdk import ConnectorManifest, validate_manifest

# -- Connector identity -----------------------------------------------

CONNECTOR_ID = "acli_confluence"

# -- Allowlist ---------------------------------------------------------
# 3-tuples: (product, group, verb).  The command shape is
# ``acli confluence <group> <verb> [flags...]``, so ``argv[1:]`` must
# start with one of these prefixes.
#
# Read-only verbs only.  ``blog create``, ``page create``,
# ``space create|archive`` and every other write verb are rejected.

ALLOWED_SUBCOMMANDS: frozenset[tuple[str, str, str]] = frozenset(
    {
        ("confluence", "auth", "status"),
        ("confluence", "auth", "switch"),
        ("confluence", "space", "list"),
        ("confluence", "space", "view"),
        ("confluence", "page", "view"),
        ("confluence", "blog", "list"),
        ("confluence", "blog", "view"),
    }
)

DEFAULT_TIMEOUT_SECONDS: float = 10.0
DEFAULT_MAX_BYTES: int = 131072


def is_command_allowed(command: Iterable[str]) -> bool:
    """Return True iff the given ``acli`` argv is on the read-only allowlist.

    The first token is expected to be the ``acli`` binary path (or
    just ``"acli"``); the second, third, and fourth tokens are the
    product-group-verb triple checked against ``ALLOWED_SUBCOMMANDS``.
    """
    tokens = list(command)
    if len(tokens) < 4:
        return False
    triple = (
        str(tokens[1]).lower(),
        str(tokens[2]).lower(),
        str(tokens[3]).lower(),
    )
    return triple in ALLOWED_SUBCOMMANDS


MANIFEST: ConnectorManifest = validate_manifest(
    {
        "id": CONNECTOR_ID,
        "label": "Atlassian CLI (Confluence)",
        "version": "0.1.0",
        "kind": "cli_enrichment",
        "capabilities": ["commands"],
        "description": (
            "Read-only ``acli confluence`` calls: auth status/switch, space "
            "list/view, page view, blog list/view. No writes, no creates, "
            "no token management. The owner authenticates via "
            "``acli confluence auth login``; HoldSpeak never stores credentials."
        ),
        "requires_cli": "acli",
        "requires_network": True,
        "permissions": [
            "shell:exec",
            "network:outbound",
        ],
        "source_boundary": (
            "Local ``acli`` CLI subprocess. Only commands listed in "
            "ALLOWED_SUBCOMMANDS are permitted; anything else is "
            "rejected before exec."
        ),
        "dry_run": True,
        "settings_schema": [
            {
                "key": "timeout_seconds",
                "type": "float",
                "default": DEFAULT_TIMEOUT_SECONDS,
                "label": "Timeout (seconds)",
                "help": (
                    "Per-command wall clock timeout. Commands that "
                    "exceed it are killed and recorded as timed out."
                ),
            },
            {
                "key": "max_bytes",
                "type": "int",
                "default": DEFAULT_MAX_BYTES,
                "label": "Max output bytes",
                "help": (
                    "Hard cap on per-command stdout the runner will "
                    "accept."
                ),
            },
        ],
    }
)
