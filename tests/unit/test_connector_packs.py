"""HS-11-03/04/05 — connector pack tests.

Each first-party pack ships a `MANIFEST` (validated against
the phase-11 connector SDK) and pack-specific policy data
(captured/forbidden fields for firefox_ext; allowed CLI
subcommands for github_cli + jira_cli). The tests here lock
both layers down.
"""

from __future__ import annotations

import pytest

from holdspeak.connector_packs import ALL_PACKS, firefox_ext, github_cli, jira_cli
from holdspeak.connector_sdk import (
    KNOWN_KINDS,
    ConnectorManifest,
    NETWORK_PERMISSIONS,
    validate_manifest,
)


def test_all_packs_export_a_validated_manifest():
    """Every pack module re-validates its manifest at import time
    via `validate_manifest`. This test asserts the imports
    survived (no ConnectorManifestError) and the manifests are
    instances of the immutable dataclass."""
    assert len(ALL_PACKS) == 3
    for pack in ALL_PACKS:
        assert isinstance(pack.MANIFEST, ConnectorManifest)
        # Round-trip: the payload validates again, so any loader
        # that persists the manifest as JSON gets the same shape
        # back.
        round_tripped = validate_manifest(pack.MANIFEST.to_payload())
        assert round_tripped == pack.MANIFEST


def test_every_pack_kind_is_known():
    for pack in ALL_PACKS:
        assert pack.MANIFEST.kind in KNOWN_KINDS


def test_network_capable_packs_declare_a_network_permission():
    for pack in ALL_PACKS:
        manifest = pack.MANIFEST
        if manifest.requires_network:
            assert set(manifest.permissions) & NETWORK_PERMISSIONS, (
                f"pack {manifest.id} requires_network=True but declares "
                f"no network permission ({manifest.permissions!r})"
            )


# ─────────────────────── HS-11-03 firefox_ext ────────────────────


def test_firefox_pack_manifest_shape():
    manifest = firefox_ext.MANIFEST
    assert manifest.id == "firefox_ext"
    assert manifest.kind == "extension_events"
    assert manifest.capabilities == ("records",)
    assert manifest.requires_cli is None
    assert manifest.requires_network is True
    assert "loopback:http" in manifest.permissions


def test_firefox_pack_captured_fields_match_parser():
    """The pack's CAPTURED_FIELDS export must mirror the parser's
    ALLOWED_FIELDS — drift would mean the pack documents a
    privacy contract the parser doesn't actually enforce."""
    from holdspeak.activity_extension import ALLOWED_FIELDS, FORBIDDEN_FIELDS

    assert firefox_ext.CAPTURED_FIELDS == ALLOWED_FIELDS
    assert firefox_ext.REJECTED_FIELDS == FORBIDDEN_FIELDS

    # Sanity: captured + rejected sets are disjoint.
    assert not (firefox_ext.CAPTURED_FIELDS & firefox_ext.REJECTED_FIELDS)


# ─────────────────────── HS-11-04 github_cli ────────────────────


def test_github_pack_manifest_shape():
    manifest = github_cli.MANIFEST
    assert manifest.id == "gh"
    assert manifest.kind == "cli_enrichment"
    assert "annotations" in manifest.capabilities
    assert manifest.requires_cli == "gh"
    assert manifest.requires_network is True
    assert "shell:exec" in manifest.permissions


@pytest.mark.parametrize(
    "command,allowed",
    [
        # Allowed: pr view / issue view in canonical form.
        (("gh", "pr", "view", "1", "--repo", "o/r"), True),
        (("/usr/local/bin/gh", "pr", "view", "42", "--repo", "anthropic/holdspeak"), True),
        (("gh", "issue", "view", "12", "--repo", "o/r"), True),
        # Rejected: mutating verbs.
        (("gh", "pr", "edit", "1", "--repo", "o/r"), False),
        (("gh", "pr", "merge", "1", "--repo", "o/r"), False),
        (("gh", "pr", "close", "1"), False),
        (("gh", "issue", "close", "1"), False),
        (("gh", "issue", "create", "--title", "x"), False),
        (("gh", "auth", "login"), False),
        (("gh", "repo", "delete", "o/r"), False),
        # Rejected: too short to even contain a verb.
        (("gh",), False),
        (("gh", "pr"), False),
    ],
)
def test_github_pack_command_policy(command, allowed):
    assert github_cli.is_command_allowed(command) is allowed


# ─────────────────────── HS-11-05 jira_cli ──────────────────────


def test_jira_pack_manifest_shape():
    manifest = jira_cli.MANIFEST
    assert manifest.id == "jira"
    assert manifest.kind == "cli_enrichment"
    assert "annotations" in manifest.capabilities
    assert manifest.requires_cli == "jira"
    assert manifest.requires_network is True
    assert "shell:exec" in manifest.permissions


@pytest.mark.parametrize(
    "command,allowed",
    [
        # Allowed: only `jira issue view`.
        (("jira", "issue", "view", "HS-101", "--plain"), True),
        (("/usr/local/bin/jira", "issue", "view", "HS-101"), True),
        # Rejected: mutating verbs.
        (("jira", "issue", "create", "--summary", "x"), False),
        (("jira", "issue", "assign", "HS-101", "user"), False),
        (("jira", "issue", "transition", "HS-101", "Done"), False),
        (("jira", "issue", "delete", "HS-101"), False),
        (("jira", "auth", "login"), False),
        # Rejected: too short.
        (("jira",), False),
        (("jira", "issue"), False),
    ],
)
def test_jira_pack_command_policy(command, allowed):
    assert jira_cli.is_command_allowed(command) is allowed
