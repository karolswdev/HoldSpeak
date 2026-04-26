"""HS-2-07 / spec §9.7 — end-to-end pipeline including synthesis.

Verifies `process_meeting_state(synthesize=True)` runs the full chain
(windowing → scoring → dispatch → persistence → synthesis) and lands
typed artifacts + lineage on disk.
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


class _PayloadStub:
    """Stub plugin returning deterministic output so the synthesizer has
    something to dedupe + summarize."""

    def __init__(self, plugin_id: str, summary: str, confidence: float = 0.8) -> None:
        self.id = plugin_id
        self.version = "1.0.0"
        self._summary = summary
        self._confidence = confidence
        self.calls = 0

    def run(self, context: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        # Deliberately omit context-derived fields (active_intents, window_id)
        # so identical runs across windows hash to the same dedup key — the
        # synthesizer hashes the full output dict.
        return {
            "summary": self._summary,
            "confidence_hint": self._confidence,
        }


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
    plugins = {
        "project_detector": ("Project: holdspeak", 0.9),
        "requirements_extractor": ("Define API contract.", 0.85),
        "action_owner_enforcer": ("Owner: alice", 0.8),
        "milestone_planner": ("Milestone: M1", 0.75),
        "dependency_mapper": ("Depends on auth", 0.7),
        "mermaid_architecture": ("graph TD; A-->B", 0.65),
        "adr_drafter": ("ADR-001: Adopt X", 0.6),
        "scope_guard": ("Scope: in", 0.6),
        "customer_signal_extractor": ("Signal: feature", 0.6),
        "incident_timeline": ("Incident timeline", 0.6),
        "risk_heatmap": ("Risk: medium", 0.55),
        "stakeholder_update_drafter": ("Update: shipped", 0.55),
        "decision_announcement_drafter": ("Decision: yes", 0.55),
        "runbook_delta": ("Runbook: updated", 0.55),
    }
    for pid, (summary, conf) in plugins.items():
        host.register(_PayloadStub(pid, summary, conf))
    return host


def _state_with_arc() -> MeetingState:
    return MeetingState(
        id="m-synth-pipe",
        started_at=datetime(2026, 4, 25, 10, 0, 0),
        title="MIR synthesis pipeline integration",
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
        ],
    )


@pytest.mark.integration
def test_process_meeting_state_synthesizes_when_flag_set(db) -> None:
    state = _state_with_arc()
    db.save_meeting(state)

    result = process_meeting_state(
        state,
        _full_host(),
        profile="balanced",
        threshold=0.4,
        db=db,
        synthesize=True,
    )

    assert result.errors == []
    assert len(result.artifacts) >= 1
    assert len(result.artifact_lineages) == len(result.artifacts)

    # Each artifact has a matching lineage by artifact_id.
    by_id = {l.artifact_id: l for l in result.artifact_lineages}
    for art in result.artifacts:
        assert art.artifact_id in by_id

    # Persistence: every drafted artifact is on disk.
    persisted = db.list_artifacts("m-synth-pipe")
    assert {a.id for a in persisted} == {a.artifact_id for a in result.artifacts}


@pytest.mark.integration
def test_process_meeting_state_synthesize_off_by_default(db) -> None:
    state = _state_with_arc()
    db.save_meeting(state)

    result = process_meeting_state(
        state,
        _full_host(),
        profile="balanced",
        threshold=0.4,
        db=db,
        # synthesize=False (default)
    )

    assert result.artifacts == []
    assert result.artifact_lineages == []
    # Plugin runs still persisted; just no synthesis.
    assert db.list_artifacts("m-synth-pipe") == []
    assert len(db.list_plugin_runs("m-synth-pipe")) >= 1


@pytest.mark.integration
def test_synthesis_dedupes_identical_outputs_across_overlapping_windows(db) -> None:
    state = _state_with_arc()
    db.save_meeting(state)

    result = process_meeting_state(
        state,
        _full_host(),
        profile="balanced",
        threshold=0.4,
        db=db,
        synthesize=True,
    )

    # Each plugin returns the same `summary` regardless of which window
    # invoked it, so synthesis should produce at most one artifact per
    # plugin id (MIR-F-009).
    by_plugin: dict[str, int] = {}
    for art in result.artifacts:
        by_plugin[art.plugin_id] = by_plugin.get(art.plugin_id, 0) + 1
    assert all(count == 1 for count in by_plugin.values())
