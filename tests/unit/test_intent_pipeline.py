"""Unit tests for the MIR end-to-end pipeline (HS-2-06 / spec §9.6)."""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db import MeetingDatabase, reset_database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.plugins.host import PluginHost
from holdspeak.plugins.pipeline import MIRPipelineResult, process_meeting_state


class StubPlugin:
    def __init__(self, plugin_id: str) -> None:
        self.id = plugin_id
        self.version = "1.0.0"
        self.calls = 0

    def run(self, context: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        return {"id": self.id}


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
        id="m-pipeline",
        started_at=datetime(2026, 4, 25, 10, 0, 0),
        ended_at=datetime(2026, 4, 25, 11, 0, 0),
        title="Pipeline test",
    )
    db.save_meeting(state)
    return state


def _meeting_with_segments(segments: list[TranscriptSegment]) -> MeetingState:
    return MeetingState(
        id="m-pipeline",
        started_at=datetime(2026, 4, 25, 10, 0, 0),
        ended_at=datetime(2026, 4, 25, 11, 0, 0),
        title="Pipeline test",
        segments=segments,
    )


def _balanced_host() -> PluginHost:
    host = PluginHost(default_timeout_seconds=1.0)
    # Register the full union of every plugin id any profile/intent chain references
    # so end-to-end tests don't accidentally hit "unknown plugin" errors when an
    # incidental keyword in the test transcript activates an unexpected intent.
    for pid in (
        "project_detector",
        "requirements_extractor",
        "action_owner_enforcer",
        "milestone_planner",
        "dependency_mapper",
        "mermaid_architecture",
        "adr_drafter",
        "scope_guard",
        "customer_signal_extractor",
        "incident_timeline",
        "risk_heatmap",
        "stakeholder_update_drafter",
        "decision_announcement_drafter",
        "runbook_delta",
    ):
        host.register(StubPlugin(pid))
    return host


def test_process_meeting_state_returns_empty_result_for_empty_segments() -> None:
    state = _meeting_with_segments([])
    result = process_meeting_state(state, _balanced_host())

    assert isinstance(result, MIRPipelineResult)
    assert result.windows == []
    assert result.scores == []
    assert result.runs == []
    assert result.errors == []


def test_process_meeting_state_returns_error_when_id_missing() -> None:
    state = MeetingState(id="", started_at=datetime.now())
    result = process_meeting_state(state, _balanced_host())

    assert result.windows == []
    assert any("state.id" in err for err in result.errors)


def test_process_meeting_state_runs_full_pipeline_end_to_end() -> None:
    state = _meeting_with_segments(
        [
            TranscriptSegment(
                text="Sprint milestone owner deadline planning for the upcoming release.",
                speaker="Me",
                start_time=0.0,
                end_time=12.0,
            ),
            TranscriptSegment(
                text="Architecture design ADR review with API schema interface alignment.",
                speaker="Remote",
                start_time=15.0,
                end_time=28.0,
            ),
        ]
    )

    result = process_meeting_state(state, _balanced_host(), threshold=0.4)

    assert result.errors == []
    assert len(result.windows) >= 1
    assert len(result.scores) == len(result.windows)
    assert len(result.runs) >= len(result.windows)  # at least one plugin per window
    # Every run carries the meeting id and a known status.
    assert all(r.meeting_id == "m-pipeline" for r in result.runs)
    assert all(r.status in {"success", "deduped"} for r in result.runs)


def test_process_meeting_state_persists_when_db_supplied(db, saved_meeting) -> None:
    state = _meeting_with_segments(
        [
            TranscriptSegment(
                text="Sprint milestone owner deadline.",
                speaker="Me",
                start_time=0.0,
                end_time=10.0,
            ),
            TranscriptSegment(
                text="Architecture API schema review.",
                speaker="Remote",
                start_time=12.0,
                end_time=22.0,
            ),
        ]
    )

    result = process_meeting_state(state, _balanced_host(), db=db, threshold=0.4)

    assert result.errors == []
    persisted_windows = db.list_intent_windows("m-pipeline")
    assert len(persisted_windows) == len(result.windows)
    persisted_runs = db.list_plugin_runs("m-pipeline")
    assert len(persisted_runs) == len(result.runs)


def test_process_meeting_state_dispatch_failure_is_recorded_not_raised() -> None:
    # Build a host with NO plugins registered → every plugin lookup raises KeyError,
    # which dispatch_window catches and surfaces as PluginRun(status="error"). The
    # pipeline's outer try/except is therefore not the one that catches; the
    # dispatcher's per-plugin try/except is. Verify the result still completes.
    state = _meeting_with_segments(
        [
            TranscriptSegment(
                text="Sprint milestone owner deadline planning.",
                speaker="Me",
                start_time=0.0,
                end_time=10.0,
            )
        ]
    )

    result = process_meeting_state(state, PluginHost(), threshold=0.4)

    assert isinstance(result, MIRPipelineResult)
    # Pipeline returned a result instead of raising.
    assert len(result.runs) >= 1
    assert all(r.status == "error" for r in result.runs)
    # Outer pipeline did not record a top-level dispatch error (the inner
    # try/except handled it cleanly per-plugin).
    assert not any(err.startswith("dispatch[") for err in result.errors)
