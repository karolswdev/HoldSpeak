"""HS-2-06 / spec §9.6 — MeetingSession.stop() with MIR routing enabled.

Verifies the stop-path wiring runs the MIR pipeline against the
finalized state, persists results, and never deadlocks. Builds the
session by hand (no real audio) and seeds a finalized
`MeetingState` so `stop()` walks its full code path without depending
on Whisper / mic / system-audio devices.
"""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db import MeetingDatabase, reset_database
from holdspeak.meeting_session import (
    MeetingSession,
    MeetingState,
    TranscriptSegment,
)
from holdspeak.plugins.host import PluginHost


class _StubPlugin:
    def __init__(self, plugin_id: str) -> None:
        self.id = plugin_id
        self.version = "1.0.0"

    def run(self, context: dict[str, object]) -> dict[str, object]:
        return {"id": self.id}


class _NoOpTranscriber:
    """Minimal Transcriber stand-in — `MeetingSession.stop()` only touches
    the transcriber via the recording loop, which we never start."""


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


def _full_host() -> PluginHost:
    host = PluginHost(default_timeout_seconds=1.0)
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
        host.register(_StubPlugin(pid))
    return host


def _seed_active_state(session: MeetingSession, db: MeetingDatabase | None = None) -> MeetingState:
    state = MeetingState(
        id="m-stop-path",
        started_at=datetime(2026, 4, 25, 10, 0, 0),
        title="MIR stop-path integration",
        segments=[
            TranscriptSegment(
                text="Sprint milestone owner deadline planning for next release.",
                speaker="Me",
                start_time=0.0,
                end_time=12.0,
            ),
            TranscriptSegment(
                text="Architecture API schema review with delivery alignment.",
                speaker="Remote",
                start_time=14.0,
                end_time=27.0,
            ),
        ],
    )
    if db is not None:
        # The meeting must exist before MIR persistence can FK-link windows / plugin runs to it.
        db.save_meeting(state)
    # MeetingSession.stop() requires `_state.is_active` (ended_at is None).
    session._state = state  # type: ignore[attr-defined]
    return state


@pytest.mark.timeout(15)
@pytest.mark.integration
def test_meeting_session_stop_runs_mir_pipeline_when_enabled(db) -> None:
    host = _full_host()
    session = MeetingSession(
        transcriber=_NoOpTranscriber(),  # type: ignore[arg-type]
        mir_routing_enabled=True,
        mir_profile="balanced",
        mir_plugin_host=host,
        mir_db=db,
    )
    _seed_active_state(session, db)

    final_state = session.stop()

    assert final_state.id == "m-stop-path"
    assert final_state.ended_at is not None  # stop() set ended_at

    # MIR persisted intent windows + plugin runs for the meeting.
    persisted_windows = db.list_intent_windows("m-stop-path")
    persisted_runs = db.list_plugin_runs("m-stop-path")
    assert len(persisted_windows) >= 1
    assert len(persisted_runs) >= 1

    # Pipeline result is parked on the session for downstream introspection.
    last = session._mir_last_result  # type: ignore[attr-defined]
    assert last is not None
    assert last.errors == []


@pytest.mark.timeout(15)
@pytest.mark.integration
def test_meeting_session_stop_is_byte_identical_when_mir_disabled(db) -> None:
    session = MeetingSession(
        transcriber=_NoOpTranscriber(),  # type: ignore[arg-type]
        # mir_routing_enabled defaults to False; explicit for clarity.
        mir_routing_enabled=False,
        mir_db=db,
    )
    _seed_active_state(session, db)

    session.stop()

    # No MIR persistence happened.
    assert db.list_intent_windows("m-stop-path") == []
    assert db.list_plugin_runs("m-stop-path") == []
    assert session._mir_last_result is None  # type: ignore[attr-defined]


@pytest.mark.timeout(15)
@pytest.mark.integration
def test_meeting_session_stop_survives_mir_pipeline_exception(db) -> None:
    """If the pipeline blows up, stop() still completes and returns the state."""

    class _ExplodingHost:
        # Looks like a PluginHost to the pipeline up until first method call.
        def execute(self, *args, **kwargs):  # noqa: ANN001, ANN002
            raise RuntimeError("intentional pipeline blow-up")

    session = MeetingSession(
        transcriber=_NoOpTranscriber(),  # type: ignore[arg-type]
        mir_routing_enabled=True,
        mir_plugin_host=_ExplodingHost(),
        mir_db=db,
    )
    _seed_active_state(session, db)

    # stop() must not propagate the pipeline exception.
    final_state = session.stop()
    assert final_state.id == "m-stop-path"
