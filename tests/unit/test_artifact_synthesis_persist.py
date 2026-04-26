"""Unit tests for the HS-2-07 synthesis-persistence bridge."""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.artifacts import ArtifactDraft, ArtifactSourceRef
from holdspeak.db import MeetingDatabase, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.plugins.contracts import ArtifactLineage
from holdspeak.plugins.synthesis import (
    synthesize_and_persist,
    to_artifact_lineage,
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
        id="m-synth",
        started_at=datetime(2026, 4, 25, 10, 0, 0),
        ended_at=datetime(2026, 4, 25, 11, 0, 0),
        title="Synthesis test",
    )
    db.save_meeting(state)
    return state


def test_to_artifact_lineage_separates_window_and_plugin_run_sources() -> None:
    draft = ArtifactDraft(
        artifact_id="art-001",
        meeting_id="m-1",
        artifact_type="requirements",
        title="Requirements summary",
        body_markdown="body",
        structured_json={},
        confidence=0.8,
        status="draft",
        plugin_id="requirements_extractor",
        plugin_version="1.0.0",
        sources=[
            ArtifactSourceRef(source_type="intent_window", source_ref="m-1:w0001"),
            ArtifactSourceRef(source_type="intent_window", source_ref="m-1:w0002"),
            ArtifactSourceRef(source_type="plugin_run", source_ref="101"),
            ArtifactSourceRef(source_type="plugin_run", source_ref="102"),
        ],
    )

    lineage = to_artifact_lineage(draft)

    assert isinstance(lineage, ArtifactLineage)
    assert lineage.artifact_id == "art-001"
    assert lineage.meeting_id == "m-1"
    assert lineage.window_ids == ["m-1:w0001", "m-1:w0002"]
    assert lineage.plugin_run_keys == ["101", "102"]


def test_to_artifact_lineage_empty_sources_yields_empty_lists() -> None:
    draft = ArtifactDraft(
        artifact_id="art-empty",
        meeting_id="m-1",
        artifact_type="t",
        title="t",
        body_markdown="",
        structured_json={},
        confidence=0.5,
        status="needs_review",
        plugin_id="p",
        plugin_version="v",
        sources=[],
    )

    lineage = to_artifact_lineage(draft)

    assert lineage.window_ids == []
    assert lineage.plugin_run_keys == []


def test_synthesize_and_persist_writes_artifacts_with_lineage(db, saved_meeting) -> None:
    # Seed window + plugin_runs the synthesizer can chew on.
    db.record_intent_window(
        meeting_id="m-synth",
        window_id="m-synth:w0001",
        start_seconds=0.0,
        end_seconds=90.0,
        transcript_hash="h1",
        intent_scores={"architecture": 0.9},
    )
    db.record_intent_window(
        meeting_id="m-synth",
        window_id="m-synth:w0002",
        start_seconds=30.0,
        end_seconds=120.0,
        transcript_hash="h2",
        intent_scores={"architecture": 0.85},
    )
    db.record_plugin_run(
        meeting_id="m-synth",
        window_id="m-synth:w0001",
        plugin_id="requirements_extractor",
        plugin_version="1.0.0",
        status="success",
        idempotency_key="key-1",
        duration_ms=10.0,
        output={"summary": "Define API contract.", "confidence_hint": 0.85},
    )
    db.record_plugin_run(
        meeting_id="m-synth",
        window_id="m-synth:w0002",
        plugin_id="requirements_extractor",
        plugin_version="1.0.0",
        status="deduped",
        idempotency_key="key-2",
        duration_ms=0.0,
        output={"summary": "Define API contract.", "confidence_hint": 0.85},
    )

    drafts, lineages = synthesize_and_persist(db, "m-synth")

    # Identical-output dedup → exactly one artifact, lineage spans both windows + runs.
    assert len(drafts) == 1
    assert len(lineages) == 1
    lineage = lineages[0]
    assert lineage.artifact_id == drafts[0].artifact_id
    assert set(lineage.window_ids) == {"m-synth:w0001", "m-synth:w0002"}
    assert len(lineage.plugin_run_keys) == 2

    # Persistence round-trip: artifact is on disk with the right source rows.
    persisted = db.list_artifacts("m-synth")
    assert len(persisted) == 1
    art = persisted[0]
    assert art.id == drafts[0].artifact_id
    source_refs = {(s["source_type"], s["source_ref"]) for s in art.sources}
    assert ("intent_window", "m-synth:w0001") in source_refs
    assert ("intent_window", "m-synth:w0002") in source_refs


def test_synthesize_and_persist_empty_meeting_returns_empty_pair(db, saved_meeting) -> None:
    drafts, lineages = synthesize_and_persist(db, "m-synth")
    assert drafts == []
    assert lineages == []
    assert db.list_artifacts("m-synth") == []


def test_synthesize_and_persist_accepts_explicit_plugin_runs_iterable(db, saved_meeting) -> None:
    # When plugin_runs is supplied explicitly, db.list_plugin_runs is bypassed.
    runs = [
        SimpleNamespace(
            id=999,
            meeting_id="m-synth",
            window_id="m-synth:w0001",
            plugin_id="action_owner_enforcer",
            plugin_version="1.0.0",
            status="success",
            output={"summary": "Owner: alice", "confidence_hint": 0.9},
            created_at="2026-04-25T10:30:00",
        )
    ]

    drafts, lineages = synthesize_and_persist(db, "m-synth", plugin_runs=runs)

    assert len(drafts) == 1
    assert drafts[0].plugin_id == "action_owner_enforcer"
    assert lineages[0].plugin_run_keys == ["999"]
