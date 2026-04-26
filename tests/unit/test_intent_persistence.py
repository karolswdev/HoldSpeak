"""Unit tests for the typed MIR persistence adapters (HS-2-05 / spec §9.5)."""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db import MeetingDatabase, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.plugins.contracts import (
    ArtifactLineage,
    IntentScore,
    IntentWindow,
    PluginRun,
)
from holdspeak.plugins.persistence import (
    record_artifact_with_lineage,
    record_intent_window,
    record_plugin_run,
    record_plugin_runs,
)


@pytest.fixture
def temp_db_path():
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    yield db_path
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def db(temp_db_path):
    return MeetingDatabase(temp_db_path)


@pytest.fixture
def saved_meeting(db):
    state = MeetingState(
        id="m1",
        started_at=datetime(2026, 4, 25, 10, 0, 0),
        ended_at=datetime(2026, 4, 25, 11, 0, 0),
        title="HS-2-05 typed-persistence smoke",
        tags=["test"],
    )
    db.save_meeting(state)
    return state


def _window(window_id: str = "m1:w0001") -> IntentWindow:
    return IntentWindow(
        window_id=window_id,
        meeting_id="m1",
        start_seconds=0.0,
        end_seconds=90.0,
        transcript="Architecture design ADR review with delivery milestone planning.",
        tags=["design"],
        metadata={"source": "test"},
    )


def _score(window_id: str = "m1:w0001", *, threshold: float = 0.6) -> IntentScore:
    return IntentScore(
        window_id=window_id,
        scores={
            "architecture": 0.83,
            "delivery": 0.71,
            "product": 0.10,
            "incident": 0.05,
            "comms": 0.05,
        },
        threshold=threshold,
    )


def _plugin_run(plugin_id: str = "requirements_extractor", *, status: str = "success") -> PluginRun:
    return PluginRun(
        plugin_id=plugin_id,
        plugin_version="1.0.0",
        window_id="m1:w0001",
        meeting_id="m1",
        profile="balanced",
        status=status,
        idempotency_key=f"key-{plugin_id}-{status}",
        started_at=1000.0,
        finished_at=1000.42,
        duration_ms=420.0,
    )


def test_record_intent_window_round_trips_typed_score(db, saved_meeting) -> None:
    record_intent_window(
        db,
        _window(),
        _score(),
        profile="balanced",
        transcript_hash="hash-abc",
    )

    persisted = db.list_intent_windows("m1")
    assert len(persisted) == 1
    row = persisted[0]
    assert row.window_id == "m1:w0001"
    assert row.threshold == pytest.approx(0.6)
    assert row.intent_scores["architecture"] == pytest.approx(0.83)
    # active_intents was derived from labels_above_threshold (architecture=0.83, delivery=0.71)
    assert set(row.active_intents) == {"architecture", "delivery"}
    assert row.profile == "balanced"
    assert row.tags == ["design"]
    assert row.metadata["source"] == "test"


def test_record_intent_window_rejects_window_id_mismatch(db, saved_meeting) -> None:
    with pytest.raises(ValueError, match="does not match"):
        record_intent_window(db, _window("m1:w0001"), _score("m1:w9999"))


def test_record_plugin_run_round_trips_typed_record(db, saved_meeting) -> None:
    # Window must exist first because plugin_runs.window_id is meaningful as a join.
    record_intent_window(db, _window(), _score(), transcript_hash="hash-abc")

    record_plugin_run(db, _plugin_run("requirements_extractor", status="success"))

    runs = db.list_plugin_runs("m1")
    assert len(runs) == 1
    assert runs[0].plugin_id == "requirements_extractor"
    assert runs[0].status == "success"
    assert runs[0].duration_ms == pytest.approx(420.0)
    assert runs[0].idempotency_key == "key-requirements_extractor-success"
    assert runs[0].deduped is False


def test_record_plugin_run_marks_deduped_status_with_dedup_flag(db, saved_meeting) -> None:
    record_intent_window(db, _window(), _score(), transcript_hash="hash-abc")
    record_plugin_run(db, _plugin_run(status="deduped"))

    runs = db.list_plugin_runs("m1")
    assert runs[0].status == "deduped"
    assert runs[0].deduped is True


def test_record_plugin_runs_persists_batch_in_order(db, saved_meeting) -> None:
    record_intent_window(db, _window(), _score(), transcript_hash="hash-abc")

    runs = [
        _plugin_run("requirements_extractor", status="success"),
        _plugin_run("action_owner_enforcer", status="success"),
        _plugin_run("milestone_planner", status="error"),
    ]
    record_plugin_runs(db, runs)

    persisted = db.list_plugin_runs("m1")
    assert {r.plugin_id for r in persisted} == {
        "requirements_extractor",
        "action_owner_enforcer",
        "milestone_planner",
    }
    statuses = {r.plugin_id: r.status for r in persisted}
    assert statuses["milestone_planner"] == "error"


def test_record_artifact_with_lineage_packs_window_and_plugin_run_sources(
    db, saved_meeting
) -> None:
    record_intent_window(db, _window(), _score(), transcript_hash="hash-abc")

    lineage = ArtifactLineage(
        artifact_id="art-001",
        meeting_id="m1",
        window_ids=["m1:w0001", "m1:w0002"],
        plugin_run_keys=["key-a", "key-b"],
    )

    record_artifact_with_lineage(
        db,
        artifact_id="art-001",
        meeting_id="m1",
        artifact_type="requirements_summary",
        title="Requirements summary",
        body_markdown="- Req 1\n- Req 2",
        plugin_id="requirements_extractor",
        plugin_version="1.0.0",
        lineage=lineage,
        confidence=0.92,
        status="needs_review",
    )

    artifacts = db.list_artifacts("m1")
    assert len(artifacts) == 1
    art = artifacts[0]
    assert art.id == "art-001"
    assert art.title == "Requirements summary"
    assert art.confidence == pytest.approx(0.92)
    assert art.status == "needs_review"

    # Lineage round-trip: sources should include both window and plugin_run rows.
    sources = {(s["source_type"], s["source_ref"]) for s in art.sources}
    assert ("window", "m1:w0001") in sources
    assert ("window", "m1:w0002") in sources
    assert ("plugin_run", "key-a") in sources
    assert ("plugin_run", "key-b") in sources


def test_record_artifact_rejects_lineage_id_mismatch(db, saved_meeting) -> None:
    bad_lineage = ArtifactLineage(
        artifact_id="art-DIFFERENT",
        meeting_id="m1",
        window_ids=[],
        plugin_run_keys=[],
    )
    with pytest.raises(ValueError, match="ArtifactLineage.artifact_id"):
        record_artifact_with_lineage(
            db,
            artifact_id="art-001",
            meeting_id="m1",
            artifact_type="t",
            title="t",
            body_markdown="",
            plugin_id="p",
            plugin_version="v",
            lineage=bad_lineage,
        )


def test_back_compat_meeting_without_intent_data_loads_clean_mir_d_006(
    db, saved_meeting
) -> None:
    # No intent windows or plugin runs persisted for this meeting.
    assert db.list_intent_windows("m1") == []
    assert db.list_plugin_runs("m1") == []
    assert db.list_artifacts("m1") == []
