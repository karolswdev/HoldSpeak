"""HS-35-02 — PluginManifest validation tests.

Mirrors the connector_sdk validator contract: every problem is collected
and surfaced at once, each as a `ManifestError` with a stable `code`.
"""

from __future__ import annotations

import pytest

from holdspeak.plugin_sdk import (
    KNOWN_INTENTS,
    KNOWN_PROFILES,
    PluginManifest,
    PluginManifestError,
    validate_manifest,
)


def _good(**overrides):
    base = {
        "id": "my_plugin",
        "label": "My Plugin",
        "version": "1.2.3",
        "kind": "synthesizer",
    }
    base.update(overrides)
    return base


# ──────────────────────────── Happy path ──────────────────────────────


def test_minimal_valid_manifest() -> None:
    manifest = validate_manifest(_good())
    assert isinstance(manifest, PluginManifest)
    assert manifest.id == "my_plugin"
    assert manifest.kind == "synthesizer"
    assert manifest.execution_mode == "inline"
    assert manifest.required_capabilities == ()
    assert manifest.profiles == ()
    assert manifest.intents == ()


def test_full_manifest_round_trips_through_payload() -> None:
    manifest = validate_manifest(
        _good(
            required_capabilities=["llm"],
            description="Does a thing.",
            execution_mode="deferred",
            profiles=["balanced", "incident"],
            intents=["incident", "comms"],
        )
    )
    assert manifest.required_capabilities == ("llm",)
    assert manifest.execution_mode == "deferred"
    assert manifest.profiles == ("balanced", "incident")
    assert manifest.intents == ("incident", "comms")
    # to_payload() must re-validate cleanly (the loader relies on this).
    assert validate_manifest(manifest.to_payload()) == manifest


def test_duplicate_and_unknown_members_are_normalized() -> None:
    manifest = validate_manifest(
        _good(intents=["incident", "incident"], profiles=["balanced"])
    )
    assert manifest.intents == ("incident",)


# ──────────────────────────── Validation ──────────────────────────────


def test_missing_required_fields_collects_all() -> None:
    with pytest.raises(PluginManifestError) as exc_info:
        validate_manifest({})
    codes = {e.code for e in exc_info.value.errors}
    assert {"required_string"} <= codes  # id/label/version/kind all missing
    fields = {e.field for e in exc_info.value.errors}
    assert {"id", "label", "version", "kind"} <= fields


def test_bad_id_format() -> None:
    with pytest.raises(PluginManifestError) as exc_info:
        validate_manifest(_good(id="Bad-Id"))
    assert any(e.code == "id_format" for e in exc_info.value.errors)


def test_bad_version_format() -> None:
    with pytest.raises(PluginManifestError) as exc_info:
        validate_manifest(_good(version="v1"))
    assert any(e.code == "version_format" for e in exc_info.value.errors)


def test_unknown_kind() -> None:
    with pytest.raises(PluginManifestError) as exc_info:
        validate_manifest(_good(kind="frobnicator"))
    assert any(e.code == "unknown_kind" for e in exc_info.value.errors)


def test_actuator_kind_is_rejected_this_phase() -> None:
    # Actuators are deferred to a later phase — the manifest can't declare one.
    with pytest.raises(PluginManifestError) as exc_info:
        validate_manifest(_good(kind="actuator"))
    assert any(e.code == "unknown_kind" for e in exc_info.value.errors)


def test_unknown_capability() -> None:
    with pytest.raises(PluginManifestError) as exc_info:
        validate_manifest(_good(required_capabilities=["llm", "gpu"]))
    assert any(e.code == "unknown_capability" for e in exc_info.value.errors)


def test_invalid_execution_mode() -> None:
    with pytest.raises(PluginManifestError) as exc_info:
        validate_manifest(_good(execution_mode="someday"))
    assert any(e.code == "invalid_execution_mode" for e in exc_info.value.errors)


def test_unknown_profile_and_intent() -> None:
    with pytest.raises(PluginManifestError) as exc_info:
        validate_manifest(_good(profiles=["nope"], intents=["nope"]))
    codes = {e.code for e in exc_info.value.errors}
    assert {"unknown_profile", "unknown_intent"} <= codes


def test_non_object_manifest() -> None:
    with pytest.raises(PluginManifestError) as exc_info:
        validate_manifest(["not", "a", "mapping"])  # type: ignore[arg-type]
    assert exc_info.value.errors[0].code == "must_be_object"


# ─────────────────── Drift guard against the router ────────────────────


def test_known_profiles_and_intents_match_router() -> None:
    """The SDK hardcodes the valid profiles/intents (dependency-light);
    this guard fails loudly if the router's sets drift away from them."""
    from holdspeak.plugins.router import (
        PROFILE_PLUGIN_BASE_CHAINS,
        SUPPORTED_INTENTS,
    )

    assert KNOWN_PROFILES == frozenset(PROFILE_PLUGIN_BASE_CHAINS.keys())
    assert KNOWN_INTENTS == frozenset(SUPPORTED_INTENTS)
