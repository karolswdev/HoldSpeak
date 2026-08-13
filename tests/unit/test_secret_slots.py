"""HS-130-02 — Collision-free secret slots: the exfiltration path closes.

The legacy ``profile_key_env`` mapped every non-alphanumeric char to ``_``, so
``foo-bar``, ``foo_bar`` and ``foo.bar`` all resolved to one env name. Profile
ids are client-supplied and sync merges profiles by id from any peer, so a
synced profile could shape its id to collide with an existing destination and
receive that destination's real key at its own attacker-controlled endpoint.
These tests reproduce that crossover and prove it closed.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.intel.providers import (
    build_meeting_intel_for_profile,
    profile_key_env,
    profile_slot_id,
)
from tests.unit.admitted_context import admitted_context


ADVERSARIAL_IDS = ["foo-bar", "foo_bar", "foo.bar", "foo bar"]


def frozen(profile_id: str) -> Any:
    """The immutable revision this child was admitted for."""
    return SimpleNamespace(
        id=f"dep_{profile_id or 'blank'}", destination_id=profile_id or "unnamed"
    )


def admitted(profile_id: str) -> Any:
    """HS-131-10: the profile factory only builds for an admitted child.

    Round 2: the context must arrive WITH the revision it was minted for — a
    factory given nothing to compare against now refuses, because "some child was
    admitted somewhere" was never authority to build this profile's engine.
    """
    return admitted_context(revision=frozen(profile_id))


def test_adversarial_ids_map_to_distinct_slots() -> None:
    """The four ids that collapsed to one slot now resolve to four distinct ones."""
    slots = [profile_slot_id(pid) for pid in ADVERSARIAL_IDS]
    assert len(set(slots)) == len(ADVERSARIAL_IDS) == 4
    envs = [profile_key_env(pid) for pid in ADVERSARIAL_IDS]
    assert len(set(envs)) == 4


def test_slot_is_deterministic_across_calls() -> None:
    """A synced profile resolves the same slot everywhere / across restarts."""
    assert profile_slot_id("foo-bar") == profile_slot_id("foo-bar")
    assert profile_key_env("svc-42") == profile_key_env("svc-42")


def test_env_name_is_a_valid_shell_identifier() -> None:
    for pid in ADVERSARIAL_IDS + ["p-43", "Client.Prod/EU"]:
        env = profile_key_env(pid)
        assert env.startswith("HOLDSPEAK_PROFILE_") and env.endswith("_KEY")
        core = env[len("HOLDSPEAK_PROFILE_") : -len("_KEY")]
        assert core and all(c.isalnum() or c == "_" for c in core)


def test_blank_id_refuses_rather_than_sharing_a_name() -> None:
    """A blank id has no unique slot; it refuses instead of falling back."""
    for blank in ["", "   ", None]:  # type: ignore[list-item]
        with pytest.raises(ValueError):
            profile_key_env(blank)  # type: ignore[arg-type]


def test_key_never_crosses_between_punctuation_siblings(monkeypatch) -> None:
    """The exfiltration regression: foo-bar has the real key; foo_bar (attacker
    base_url) must NOT be able to read it. Under the legacy slug both share
    ``HOLDSPEAK_PROFILE_FOO_BAR_KEY``; under the injective slot they cannot."""
    victim_env = profile_key_env("foo-bar")
    attacker_env = profile_key_env("foo_bar")
    assert victim_env != attacker_env

    monkeypatch.setenv(victim_env, "sk-REAL-VICTIM-KEY")
    monkeypatch.delenv(attacker_env, raising=False)

    victim = build_meeting_intel_for_profile(
        kind="openAICompatible",
        base_url="https://victim.example/v1",
        model="m",
        profile_id="foo-bar",
        deployment_revision=frozen("foo-bar"),
        context=admitted("foo-bar"),
    )
    attacker = build_meeting_intel_for_profile(
        kind="openAICompatible",
        base_url="https://attacker.evil/v1",
        model="m",
        profile_id="foo_bar",
        deployment_revision=frozen("foo_bar"),
        context=admitted("foo_bar"),
    )
    # Each intel names ONLY its own slot; the attacker's env is empty.
    assert victim.cloud_api_key_env == victim_env
    assert attacker.cloud_api_key_env == attacker_env
    assert attacker.cloud_api_key_env != victim_env


def test_blank_profile_id_never_sends_out_under_a_shared_slot() -> None:
    """A cloud build with a blank id refuses to egress; it falls to the local
    engine rather than borrow a collided credential."""
    intel = build_meeting_intel_for_profile(
        kind="openAICompatible",
        base_url="https://attacker.evil/v1",
        model="m",
        profile_id="",
        deployment_revision=frozen(""),
        context=admitted(""),
    )
    # No attacker endpoint was adopted; the local/configured engine was chosen.
    assert getattr(intel, "cloud_base_url", None) != "https://attacker.evil/v1"


def test_profile_key_present_is_true_only_for_own_slot(monkeypatch) -> None:
    from holdspeak.inference_targets import _profile_key_present

    monkeypatch.setenv(profile_key_env("foo-bar"), "sk-victim")
    monkeypatch.delenv(profile_key_env("foo_bar"), raising=False)

    assert _profile_key_present("foo-bar") is True
    # The punctuation-sibling has no key of its own -> not ready.
    assert _profile_key_present("foo_bar") is False
    # A blank id is never "ready".
    assert _profile_key_present("") is False


def test_sync_serializer_emits_no_secret_material() -> None:
    """The profiles sync record carries shape only — never key material."""
    from holdspeak.db.models.knowledge import ProfileRecord
    from holdspeak.services.sync_service import _primitive_record

    rec = ProfileRecord(
        id="svc",
        name="OpenRouter",
        kind="openAICompatible",
        base_url="https://openrouter.ai/api/v1",
        model="claude",
        requires_key=True,
        last_modified="2026-08-09T00:00:00Z",
    )
    record = _primitive_record(rec, "profile")
    value = record["value"] or {}
    forbidden = {"api_key", "apikey", "key", "secret", "token", "api_key_env"}
    for field_name, field_val in value.items():
        assert field_name.lower() not in forbidden, f"secret field leaked: {field_name}"
        # No value should carry the literal secret either.
        assert "sk-" not in str(field_val)
