"""HS-2-06 / spec §9.6 — end-to-end MIR pipeline integration test.

Walks the full chain (windowing → scoring → transitions → dispatch →
persistence) over a fake meeting state without touching audio/Whisper/
MeetingSession threading. Verifies the pipeline produces typed output
that's consistent end-to-end and that re-running over the same state
short-circuits via the host's idempotency cache (MIR-F-008, MIR-F-009).
"""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db import MeetingDatabase, reset_database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.plugins.host import PluginHost
from holdspeak.plugins.pipeline import process_meeting_state


class _StubPlugin:
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


def _full_host() -> tuple[PluginHost, dict[str, _StubPlugin]]:
    host = PluginHost(default_timeout_seconds=1.0)
    stubs: dict[str, _StubPlugin] = {}
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
        stub = _StubPlugin(pid)
        stubs[pid] = stub
        host.register(stub)
    return host, stubs


def _state_with_arc() -> MeetingState:
    """Three windows worth of transcript covering an architecture →
    delivery → incident arc to exercise transitions + multi-intent."""
    return MeetingState(
        id="m-routing-int",
        started_at=datetime(2026, 4, 25, 10, 0, 0),
        title="MIR routing integration",
        segments=[
            TranscriptSegment(
                text="Architecture design ADR review for API schema and service interface.",
                speaker="Me",
                start_time=0.0,
                end_time=20.0,
            ),
            TranscriptSegment(
                text="Sprint milestone owner deadline planning and dependency mapping.",
                speaker="Remote",
                start_time=30.0,
                end_time=55.0,
            ),
            TranscriptSegment(
                text="Incident outage severity rollback mitigation and stakeholder update.",
                speaker="Me",
                start_time=70.0,
                end_time=95.0,
            ),
        ],
    )


@pytest.mark.integration
def test_pipeline_end_to_end_persists_typed_outputs(db) -> None:
    state = _state_with_arc()
    db.save_meeting(state)
    host, _stubs = _full_host()

    result = process_meeting_state(
        state,
        host,
        profile="balanced",
        threshold=0.4,
        db=db,
    )

    assert result.errors == []
    assert len(result.windows) >= 1
    assert len(result.scores) == len(result.windows)
    assert len(result.runs) >= len(result.windows)

    persisted_windows = db.list_intent_windows("m-routing-int")
    persisted_runs = db.list_plugin_runs("m-routing-int")
    assert {w.window_id for w in persisted_windows} == {w.window_id for w in result.windows}
    assert len(persisted_runs) == len(result.runs)


@pytest.mark.integration
def test_pipeline_rerun_dedupes_via_host_idempotency_cache(db) -> None:
    state = _state_with_arc()
    db.save_meeting(state)
    host, stubs = _full_host()

    first = process_meeting_state(state, host, profile="balanced", threshold=0.4, db=db)
    calls_after_first = {pid: stub.calls for pid, stub in stubs.items()}

    second = process_meeting_state(state, host, profile="balanced", threshold=0.4, db=db)
    calls_after_second = {pid: stub.calls for pid, stub in stubs.items()}

    # First pass executed plugins; second pass should be all cache hits.
    assert any(v > 0 for v in calls_after_first.values())
    assert calls_after_first == calls_after_second  # no new plugin invocations
    assert all(r.status == "deduped" for r in second.runs)


@pytest.mark.integration
def test_pipeline_emits_transitions_across_intent_arc(db) -> None:
    state = _state_with_arc()
    db.save_meeting(state)
    host, _stubs = _full_host()

    result = process_meeting_state(state, host, profile="balanced", threshold=0.4, db=db)

    # Transitions should mark at least one intent change as the transcript moves
    # from architecture-heavy to delivery-heavy to incident-heavy windows.
    assert len(result.transitions) >= 2
    seen_intents: set[str] = set()
    for transition in result.transitions:
        seen_intents.update(transition.added)
    assert {"architecture", "delivery"}.intersection(seen_intents) or {
        "architecture",
        "incident",
    }.intersection(seen_intents)
