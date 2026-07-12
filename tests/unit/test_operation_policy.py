from __future__ import annotations

import pytest

from holdspeak.operation_policy import (
    HARD_INVARIANTS,
    commitment_labels,
    describe_operation,
    resolve_policy,
    steering_ttl_for_mode,
)


def _operation(family: str, **overrides):
    values = {
        "operation_id": f"test:{family}",
        "family": family,
        "effect_class": "slack/post_message"
        if family == "external_write"
        else f"{family}/run",
        "actor": "karol",
        "destination": "slack:sha256:fixed" if family == "external_write" else "local",
        "data_classes": ("proposed_content",),
        "fixed_destination": family == "external_write",
        "consequence": "execute_now",
    }
    values.update(overrides)
    return describe_operation(**values)


def _grant(operation):
    return {
        "state": "active",
        "actor": operation.actor,
        "operation_family": operation.family,
        "effect_class": operation.effect_class,
        "destination": operation.destination,
        "data_classes": list(operation.data_classes),
        "project_scope": operation.project_scope,
        "resource_scope": operation.resource_scope,
    }


@pytest.mark.parametrize("mode", ["safe", "neutral", "yolo"])
@pytest.mark.parametrize(
    "family", ["dictation_commit", "coder_steering", "external_write", "sync_cadence"]
)
def test_every_mode_preserves_identical_hard_invariants(mode: str, family: str) -> None:
    decision = resolve_policy(_operation(family), mode=mode)
    assert decision.hard_invariants == HARD_INVARIANTS
    assert decision.precedence[0] == "hard_invariants"


def test_dictation_matrix() -> None:
    operation = _operation("dictation_commit")
    assert resolve_policy(operation, mode="safe").outcome == "review_required"
    assert resolve_policy(operation, mode="neutral").outcome == "allowed"
    assert (
        resolve_policy(operation, mode="neutral", configured_preview=True).outcome
        == "review_required"
    )
    assert (
        resolve_policy(operation, mode="yolo", configured_preview=True).outcome
        == "allowed"
    )


@pytest.mark.parametrize("mode", ["safe", "neutral", "yolo"])
def test_steering_always_requires_an_exact_grant(mode: str) -> None:
    operation = _operation("coder_steering")
    assert resolve_policy(operation, mode=mode).outcome == "grant_required"
    assert (
        resolve_policy(operation, mode=mode, grant=_grant(operation)).outcome
        == "allowed"
    )


def test_external_write_matrix_and_explicit_authorization() -> None:
    operation = _operation("external_write")
    assert resolve_policy(operation, mode="safe").outcome == "authorization_required"
    assert resolve_policy(operation, mode="neutral").outcome == "authorization_required"
    automatic = resolve_policy(operation, mode="yolo")
    assert automatic.outcome == "allowed"
    assert automatic.reason_code == "configured_destination_posture_allowed"
    assert automatic.authority_basis == "control_posture"
    assert automatic.next_state == "execute_now"
    reusable = resolve_policy(operation, mode="neutral", grant=_grant(operation))
    assert reusable.reason_code == "scoped_grant_active"
    assert reusable.authority_basis == "scoped_grant"
    for mode in ("safe", "neutral", "yolo"):
        decision = resolve_policy(operation, mode=mode, explicit_authorization=True)
        assert decision.outcome == "allowed"


def test_grant_scope_mismatch_refuses() -> None:
    operation = _operation("external_write", project_scope="acme/app")
    grant = _grant(operation)
    grant["project_scope"] = "acme/other"
    assert (
        resolve_policy(operation, mode="neutral", grant=grant).outcome
        == "authorization_required"
    )


def test_sync_matrix_and_unsupported_fail_closed() -> None:
    sync = _operation("sync_cadence")
    assert resolve_policy(sync, mode="safe").outcome == "authorization_required"
    assert resolve_policy(sync, mode="neutral").outcome == "allowed"
    assert resolve_policy(sync, mode="yolo").outcome == "allowed"
    unknown = _operation("future_arbitrary_shell")
    decision = resolve_policy(unknown, mode="yolo")
    assert decision.outcome == "refused"
    assert decision.reason_code == "unsupported_operation_family"
    assert decision.eligible is False


def test_yolo_refuses_an_unregistered_external_destination() -> None:
    operation = _operation("external_write", fixed_destination=False)
    decision = resolve_policy(operation, mode="yolo")
    assert decision.outcome == "refused"
    assert decision.reason_code == "registered_destination_required"
    assert decision.authority_basis == "none"
    assert decision.next_state == "refused"


def test_steering_ttl_presets_cap_future_arms() -> None:
    assert steering_ttl_for_mode("safe") == 300
    assert steering_ttl_for_mode("safe", 3600) == 300
    assert steering_ttl_for_mode("neutral") == 900
    assert steering_ttl_for_mode("yolo", 1800) == 1800
    assert steering_ttl_for_mode("yolo", 7200) == 3600


def test_commitment_names_effect_and_destination() -> None:
    operation = _operation("external_write")
    assert commitment_labels(operation)["approve"] == "Approve and send to Slack"
