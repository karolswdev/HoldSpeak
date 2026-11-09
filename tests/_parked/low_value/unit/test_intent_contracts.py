# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_intent_contracts.py to restore.

# ruff: noqa


# --- test_intent_score_is_frozen: P3: tests that a frozen dataclass raises FrozenInstanceError
def test_intent_score_is_frozen() -> None:
    score = IntentScore(window_id="w", scores={"architecture": 0.9}, threshold=0.6)
    with pytest.raises(FrozenInstanceError):
        score.threshold = 0.5  # type: ignore[misc]


# --- test_contracts_re_exported_from_plugins_package: P8: pins that four names are re-exported from a package (an HS-2 import path)
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


# --- test_intent_transition_round_trips_to_dict: P1: builds a contract dataclass from literals and reads the same literals back from to_dict
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


# --- test_plugin_run_accepts_known_statuses: P1: builds a contract dataclass from literals and reads the same literals back from to_dict
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


# --- test_artifact_lineage_preserves_window_and_plugin_run_links: P1: builds a contract dataclass from literals and reads the same literals back from to_dict
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
