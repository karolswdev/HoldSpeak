"""HS-13-03 — connector pack settings schema tests.

Settings are now declared on the manifest as a
`settings_schema` list of `{key, type, default, label, help}`
entries. The runtime resolves a setting via
`resolve_setting(manifest, connector.settings, key)`, which
returns the user value if present and well-typed, otherwise
the schema default.
"""

from __future__ import annotations

import pytest

from holdspeak.connector_sdk import (
    ConnectorManifestError,
    SettingDescriptor,
    resolve_setting,
    validate_manifest,
)


def _base_manifest(**overrides):
    base = {
        "id": "test_pack",
        "label": "Test pack",
        "version": "0.1.0",
        "kind": "candidate_inference",
        "capabilities": ["candidates"],
        "permissions": ["read:activity_records"],
    }
    base.update(overrides)
    return base


# ──────────────────────── schema validation ─────────────────────


def test_settings_schema_defaults_to_empty_tuple():
    manifest = validate_manifest(_base_manifest())
    assert manifest.settings_schema == ()
    assert manifest.setting_keys() == frozenset()


def test_well_formed_settings_schema_round_trips():
    raw_schema = [
        {
            "key": "limit",
            "type": "int",
            "default": 25,
            "label": "Records per run",
            "help": "Cap on the per-run record count.",
        },
    ]
    manifest = validate_manifest(_base_manifest(settings_schema=raw_schema))
    assert manifest.settings_schema == (
        SettingDescriptor(
            key="limit",
            type="int",
            default=25,
            label="Records per run",
            help="Cap on the per-run record count.",
        ),
    )
    # to_payload + re-validate is the loader contract for any
    # JSON-persisted manifest store.
    again = validate_manifest(manifest.to_payload())
    assert again == manifest


@pytest.mark.parametrize(
    "bad_entry, expected_field",
    [
        ({"key": "Bad-Key", "type": "int", "default": 1}, "key"),
        ({"key": "x", "type": "complex", "default": 1}, "type"),
        ({"key": "x", "type": "int"}, "default"),
        ({"key": "x", "type": "int", "default": "not-an-int"}, "default"),
        # bool is a subclass of int but the schema treats them as
        # distinct — a pack that wants a bool default must say so
        # explicitly with type=bool.
        ({"key": "x", "type": "int", "default": True}, "default"),
        ({"key": "x", "type": "str", "default": 7}, "default"),
    ],
)
def test_malformed_settings_schema_entry_fails_validation(bad_entry, expected_field):
    with pytest.raises(ConnectorManifestError) as exc_info:
        validate_manifest(_base_manifest(settings_schema=[bad_entry]))
    fields = {e.field.split(".", 1)[-1] for e in exc_info.value.errors}
    assert expected_field in fields


def test_duplicate_setting_keys_fail_validation():
    schema = [
        {"key": "limit", "type": "int", "default": 10},
        {"key": "limit", "type": "int", "default": 20},
    ]
    with pytest.raises(ConnectorManifestError) as exc_info:
        validate_manifest(_base_manifest(settings_schema=schema))
    codes = {e.code for e in exc_info.value.errors}
    assert "duplicate_key" in codes


def test_settings_schema_must_be_a_list():
    with pytest.raises(ConnectorManifestError) as exc_info:
        validate_manifest(_base_manifest(settings_schema={"not": "a list"}))
    codes = {e.code for e in exc_info.value.errors}
    assert "must_be_list" in codes


# ───────────────────── resolve_setting behaviour ────────────────


def test_resolve_setting_returns_user_value_when_well_typed():
    manifest = validate_manifest(
        _base_manifest(
            settings_schema=[
                {"key": "limit", "type": "int", "default": 25},
            ]
        )
    )
    assert resolve_setting(manifest, {"limit": 50}, "limit") == 50


def test_resolve_setting_falls_back_to_default_when_unset():
    manifest = validate_manifest(
        _base_manifest(
            settings_schema=[
                {"key": "limit", "type": "int", "default": 25},
            ]
        )
    )
    assert resolve_setting(manifest, None, "limit") == 25
    assert resolve_setting(manifest, {}, "limit") == 25
    assert resolve_setting(manifest, {"other": 1}, "limit") == 25


def test_resolve_setting_falls_back_when_user_value_is_wrong_type():
    """A user value that doesn't match the declared type is
    silently ignored in favour of the default. The PUT endpoint
    has a chance to reject up front — this layer is the safety
    net for stale settings that a schema update has just narrowed."""
    manifest = validate_manifest(
        _base_manifest(
            settings_schema=[
                {"key": "timeout_seconds", "type": "float", "default": 5.0},
            ]
        )
    )
    assert resolve_setting(manifest, {"timeout_seconds": "ten"}, "timeout_seconds") == 5.0
    assert resolve_setting(manifest, {"timeout_seconds": True}, "timeout_seconds") == 5.0


def test_resolve_setting_int_default_accepts_int_user_value_only():
    """type=int rejects a bool user value (bool is a subclass of
    int in Python but the schema treats them as distinct)."""
    manifest = validate_manifest(
        _base_manifest(
            settings_schema=[{"key": "limit", "type": "int", "default": 25}]
        )
    )
    assert resolve_setting(manifest, {"limit": True}, "limit") == 25
    assert resolve_setting(manifest, {"limit": 50}, "limit") == 50


def test_resolve_setting_unknown_key_raises():
    manifest = validate_manifest(_base_manifest())
    with pytest.raises(KeyError):
        resolve_setting(manifest, {"limit": 50}, "limit")


# ────────────────── first-party pack schemas ────────────────────


def test_github_pack_declares_runtime_tunables():
    from holdspeak.connector_packs import github_cli

    keys = github_cli.MANIFEST.setting_keys()
    assert keys == frozenset({"timeout_seconds", "max_bytes", "limit"})
    # Defaults match the legacy module constants so the wiring
    # change is byte-stable for honest packs.
    assert github_cli.MANIFEST.setting_default("timeout_seconds") == 5.0
    assert github_cli.MANIFEST.setting_default("max_bytes") == 65536
    assert github_cli.MANIFEST.setting_default("limit") == 25


def test_jira_pack_declares_runtime_tunables():
    from holdspeak.connector_packs import jira_cli

    keys = jira_cli.MANIFEST.setting_keys()
    assert keys == frozenset({"timeout_seconds", "max_bytes", "limit"})


def test_calendar_pack_declares_only_a_limit():
    from holdspeak.connector_packs import calendar_activity

    keys = calendar_activity.MANIFEST.setting_keys()
    assert keys == frozenset({"limit"})
    assert calendar_activity.MANIFEST.setting_default("limit") == 50


def test_firefox_pack_declares_an_empty_schema():
    """The firefox companion ingester takes no tunables — the
    parser is the contract. An empty schema means PUT settings
    on this pack with any key returns 400."""
    from holdspeak.connector_packs import firefox_ext

    assert firefox_ext.MANIFEST.settings_schema == ()
