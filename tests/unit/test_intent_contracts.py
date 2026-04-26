"""Unit tests for the typed MIR contracts added by HS-2-02 (spec §5.1)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from holdspeak.plugins.contracts import (
    PLUGIN_RUN_STATUSES,
    ArtifactLineage,
    IntentScore,
    IntentTransition,
    PluginRun,
)


def test_intent_score_labels_above_threshold_orders_by_score_then_label() -> None:
    score = IntentScore(
        window_id="m1:w0001",
        scores={"architecture": 0.81, "delivery": 0.76, "incident": 0.42, "comms": 0.81},
        threshold=0.6,
    )

    assert score.labels_above_threshold() == ["architecture", "comms", "delivery"]
    assert score.to_dict()["scores"]["architecture"] == 0.81


def test_intent_score_is_frozen() -> None:
    score = IntentScore(window_id="w", scores={"architecture": 0.9}, threshold=0.6)
    with pytest.raises(FrozenInstanceError):
        score.threshold = 0.5  # type: ignore[misc]


def test_intent_transition_round_trips_to_dict() -> None:
    transition = IntentTransition(
        window_id="m1:w0002",
        previous_active=["architecture"],
        current_active=["architecture", "delivery"],
        added=["delivery"],
        removed=[],
    )

    payload = transition.to_dict()
    assert payload["window_id"] == "m1:w0002"
    assert payload["added"] == ["delivery"]
    assert payload["removed"] == []
    assert payload["current_active"] == ["architecture", "delivery"]


def test_plugin_run_accepts_known_statuses() -> None:
    run = PluginRun(
        plugin_id="requirements_extractor",
        plugin_version="1.0.0",
        window_id="m1:w0001",
        meeting_id="m1",
        profile="balanced",
        status="success",
        idempotency_key="abc",
        started_at=1000.0,
        finished_at=1000.25,
        duration_ms=250.0,
    )

    assert run.status in PLUGIN_RUN_STATUSES
    assert run.error is None
    assert run.to_dict()["duration_ms"] == 250.0


def test_plugin_run_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="status='bogus'"):
        PluginRun(
            plugin_id="x",
            plugin_version="1.0",
            window_id="w",
            meeting_id="m",
            profile="balanced",
            status="bogus",
            idempotency_key="k",
            started_at=0.0,
            finished_at=0.0,
            duration_ms=0.0,
        )


def test_artifact_lineage_preserves_window_and_plugin_run_links() -> None:
    lineage = ArtifactLineage(
        artifact_id="art-001",
        meeting_id="m1",
        window_ids=["m1:w0001", "m1:w0002"],
        plugin_run_keys=["m1:w0001:requirements_extractor", "m1:w0002:adr_drafter"],
    )

    payload = lineage.to_dict()
    assert payload["window_ids"] == ["m1:w0001", "m1:w0002"]
    assert "m1:w0002:adr_drafter" in payload["plugin_run_keys"]


def test_contracts_re_exported_from_plugins_package() -> None:
    from holdspeak.plugins import (
        ArtifactLineage as ReArtifact,
        IntentScore as ReScore,
        IntentTransition as ReTransition,
        PluginRun as RePluginRun,
    )

    assert ReArtifact is ArtifactLineage
    assert ReScore is IntentScore
    assert ReTransition is IntentTransition
    assert RePluginRun is PluginRun
