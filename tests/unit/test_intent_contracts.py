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


