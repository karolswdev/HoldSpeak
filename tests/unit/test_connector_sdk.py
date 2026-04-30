"""Unit tests for HS-11-01 connector manifest + SDK shape."""

from __future__ import annotations

import pytest

from holdspeak.connector_sdk import (
    KNOWN_CAPABILITIES,
    KNOWN_KINDS,
    Clear,
    ConnectorManifest,
    ConnectorManifestError,
    Discover,
    Enrich,
    Preview,
    validate_manifest,
)


def _good_manifest(**overrides):
    base = {
        "id": "github_cli",
        "label": "GitHub CLI",
        "version": "1.0.0",
        "kind": "cli_enrichment",
        "capabilities": ["annotations", "commands"],
        "description": "Read-only `gh` enrichment for visited PR/issue activity.",
        "requires_cli": "gh",
        "requires_network": False,
        "permissions": [
            "read:activity_records",
            "write:activity_annotations",
            "shell:exec",
        ],
        "source_boundary": "Local activity_records via gh CLI subprocess",
        "dry_run": True,
    }
    base.update(overrides)
    return base


def test_validate_manifest_round_trips_a_well_formed_manifest():
    manifest = validate_manifest(_good_manifest())
    assert isinstance(manifest, ConnectorManifest)
    payload = manifest.to_payload()
    # Round-tripping the payload through validate_manifest yields
    # an equivalent manifest — important for pack persistence.
    assert validate_manifest(payload) == manifest


def test_validate_manifest_returns_immutable_dataclass():
    manifest = validate_manifest(_good_manifest())
    with pytest.raises(Exception):
        manifest.id = "other"  # type: ignore[misc]


def test_validate_manifest_rejects_non_object_root():
    with pytest.raises(ConnectorManifestError) as exc:
        validate_manifest("not-a-mapping")  # type: ignore[arg-type]
    assert any(e.code == "must_be_object" for e in exc.value.errors)


@pytest.mark.parametrize(
    "bad_id",
    ["", "1starts_with_digit", "Has-Caps", "with space", "way_too_long_" + "x" * 30],
)
def test_validate_manifest_rejects_malformed_ids(bad_id):
    with pytest.raises(ConnectorManifestError) as exc:
        validate_manifest(_good_manifest(id=bad_id))
    codes = {e.code for e in exc.value.errors}
    assert "id_format" in codes or "required_string" in codes


@pytest.mark.parametrize(
    "bad_version", ["", "1.0", "v1.0.0", "1.0.0.0", "1.0.0+build", "latest"]
)
def test_validate_manifest_rejects_malformed_versions(bad_version):
    with pytest.raises(ConnectorManifestError) as exc:
        validate_manifest(_good_manifest(version=bad_version))
    codes = {e.code for e in exc.value.errors}
    assert "version_format" in codes or "required_string" in codes


def test_validate_manifest_rejects_unknown_kind():
    with pytest.raises(ConnectorManifestError) as exc:
        validate_manifest(_good_manifest(kind="oauth_cloud"))
    assert any(e.code == "unknown_kind" for e in exc.value.errors)


def test_validate_manifest_rejects_empty_capabilities():
    with pytest.raises(ConnectorManifestError) as exc:
        validate_manifest(_good_manifest(capabilities=[]))
    assert any(e.code == "required_list" for e in exc.value.errors)


def test_validate_manifest_rejects_unknown_capability():
    with pytest.raises(ConnectorManifestError) as exc:
        validate_manifest(_good_manifest(capabilities=["annotations", "magic"]))
    assert any(e.code == "unknown_capability" for e in exc.value.errors)


def test_validate_manifest_requires_cli_when_kind_is_cli_enrichment():
    with pytest.raises(ConnectorManifestError) as exc:
        validate_manifest(_good_manifest(requires_cli=None))
    assert any(e.code == "required_for_cli_enrichment" for e in exc.value.errors)


def test_validate_manifest_requires_network_perm_when_requires_network_true():
    with pytest.raises(ConnectorManifestError) as exc:
        validate_manifest(
            _good_manifest(
                requires_network=True,
                permissions=["read:activity_records"],
            )
        )
    assert any(e.code == "network_permission_required" for e in exc.value.errors)


def test_validate_manifest_accepts_loopback_only_extension_pack():
    manifest = validate_manifest(
        {
            "id": "firefox_ext",
            "label": "Firefox companion",
            "version": "0.1.0",
            "kind": "extension_events",
            "capabilities": ["records"],
            "requires_network": True,
            "permissions": ["loopback:http", "write:activity_records"],
            "source_boundary": "Loopback POSTs from a local Firefox WebExtension",
        }
    )
    assert manifest.requires_network is True
    assert "loopback:http" in manifest.permissions


def test_validate_manifest_rejects_unknown_permission():
    with pytest.raises(ConnectorManifestError) as exc:
        validate_manifest(
            _good_manifest(permissions=["read:activity_records", "magic:do-everything"])
        )
    assert any(e.code == "unknown_permission" for e in exc.value.errors)


def test_validate_manifest_collects_every_error_at_once():
    """One pass through validate_manifest should report *every* problem
    so connector authors fix them all in one edit, not one per CI loop."""
    raw = {
        "id": "Has-Caps",
        "label": "",                # required_string
        "version": "vX",            # version_format
        "kind": "oauth_cloud",      # unknown_kind
        "capabilities": ["wrong"],  # unknown_capability
        "requires_cli": None,       # required_for_cli_enrichment (kind=cli_enrichment? no — kind invalid)
        "permissions": ["lol"],     # unknown_permission
    }
    # kind is invalid so "required_for_cli_enrichment" doesn't apply,
    # but every other error should fire.
    with pytest.raises(ConnectorManifestError) as exc:
        validate_manifest(raw)
    codes = {e.code for e in exc.value.errors}
    assert {
        "id_format",
        "required_string",       # label
        "version_format",
        "unknown_kind",
        "unknown_capability",
        "unknown_permission",
    }.issubset(codes)


def test_validate_manifest_default_dry_run_is_true():
    raw = _good_manifest()
    raw.pop("dry_run", None)
    manifest = validate_manifest(raw)
    assert manifest.dry_run is True


def test_validate_manifest_dry_run_must_be_bool():
    with pytest.raises(ConnectorManifestError) as exc:
        validate_manifest(_good_manifest(dry_run="yes"))
    assert any(e.code == "must_be_bool" for e in exc.value.errors)


def test_known_constants_match_phase_9_shape():
    """Sanity: the kinds + capabilities here cover what phase 9
    actually shipped, so phase-11 connector packs slot in cleanly."""
    assert {"cli_enrichment", "candidate_inference", "extension_events"} <= KNOWN_KINDS
    assert {"annotations", "candidates", "commands", "records"} <= KNOWN_CAPABILITIES


def test_sdk_protocols_are_runtime_checkable():
    """A connector class implementing the right method satisfies the
    Protocol via duck-typing; isinstance() reports it correctly."""

    class FakeConnector:
        def preview(self, db, *, limit=25):  # noqa: ARG002
            return {}

        def enrich(self, db, *, limit=25):  # noqa: ARG002
            return {}

        def clear(self, db, *, capability):  # noqa: ARG002
            return 0

        def discover(self, db, *, limit=25):  # noqa: ARG002
            return []

    instance = FakeConnector()
    assert isinstance(instance, Preview)
    assert isinstance(instance, Enrich)
    assert isinstance(instance, Clear)
    assert isinstance(instance, Discover)


def test_partial_implementations_are_partial_isinstance():
    """A pack that only previews is a Preview, not an Enrich."""

    class PreviewOnly:
        def preview(self, db, *, limit=25):  # noqa: ARG002
            return {}

    instance = PreviewOnly()
    assert isinstance(instance, Preview)
    assert not isinstance(instance, Enrich)
    assert not isinstance(instance, Clear)
