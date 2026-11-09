# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_connector_packs.py to restore.

# ruff: noqa


# --- test_firefox_pack_manifest_shape: P1: re-reads each pack's MANIFEST constants field by field
def test_firefox_pack_manifest_shape():
    manifest = firefox_ext.MANIFEST
    assert manifest.id == "firefox_ext"
    assert manifest.kind == "extension_events"
    assert manifest.capabilities == ("records",)
    assert manifest.requires_cli is None
    assert manifest.requires_network is True
    assert "loopback:http" in manifest.permissions


# --- test_github_pack_manifest_shape: P1: re-reads each pack's MANIFEST constants field by field
def test_github_pack_manifest_shape():
    manifest = github_cli.MANIFEST
    assert manifest.id == "gh"
    assert manifest.kind == "cli_enrichment"
    assert "annotations" in manifest.capabilities
    assert manifest.requires_cli == "gh"
    assert manifest.requires_network is True
    assert "shell:exec" in manifest.permissions


# --- test_jira_pack_manifest_shape: P1: re-reads each pack's MANIFEST constants field by field
def test_jira_pack_manifest_shape():
    manifest = jira_cli.MANIFEST
    assert manifest.id == "jira"
    assert manifest.kind == "cli_enrichment"
    assert "annotations" in manifest.capabilities
    assert manifest.requires_cli == "jira"
    assert manifest.requires_network is True
    assert "shell:exec" in manifest.permissions


# --- test_acli_jira_pack_manifest_shape: P1: re-reads each pack's MANIFEST constants field by field
def test_acli_jira_pack_manifest_shape():
    manifest = acli_jira.MANIFEST
    assert manifest.id == "acli_jira"
    assert manifest.kind == "cli_enrichment"
    assert "commands" in manifest.capabilities
    assert manifest.requires_cli == "acli"
    assert manifest.requires_network is True
    assert "shell:exec" in manifest.permissions


# --- test_calendar_pack_manifest_shape: P1: re-reads each pack's MANIFEST constants field by field
def test_calendar_pack_manifest_shape():
    manifest = calendar_activity.MANIFEST
    assert manifest.id == "calendar_activity"
    assert manifest.kind == "candidate_inference"
    assert manifest.capabilities == ("candidates",)
    assert manifest.requires_cli is None
    assert manifest.requires_network is False
    assert "read:activity_records" in manifest.permissions
    assert "write:activity_meeting_candidates" in manifest.permissions
    # No shell, no network — the calendar pack is read-only over
    # local rows.
    assert "shell:exec" not in manifest.permissions
    assert not (set(manifest.permissions) & NETWORK_PERMISSIONS)
