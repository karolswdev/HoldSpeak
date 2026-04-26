"""HS-2-09 / spec §9.9 — MeetingConfig flows through to MeetingSession's MIR pipeline."""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.config import MeetingConfig
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
    """MeetingSession.stop() doesn't touch the transcriber when no recording started."""


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


def _seed_active_state(session: MeetingSession, db: MeetingDatabase) -> MeetingState:
    state = MeetingState(
        id="m-cfg",
        started_at=datetime(2026, 4, 26, 10, 0, 0),
        title="Config integration",
        segments=[
            TranscriptSegment(
                text="Sprint milestone owner deadline planning.",
                speaker="Me",
                start_time=0.0,
                end_time=10.0,
            ),
            TranscriptSegment(
                text="Architecture API schema review with delivery alignment.",
                speaker="Remote",
                start_time=15.0,
                end_time=30.0,
            ),
        ],
    )
    db.save_meeting(state)
    session._state = state  # type: ignore[attr-defined]
    return state


def _build_session_from_config(
    cfg: MeetingConfig, *, host: PluginHost, db: MeetingDatabase
) -> MeetingSession:
    """Same wiring a future top-level entry point would do (HS-2-09 callers)."""
    return MeetingSession(
        transcriber=_NoOpTranscriber(),  # type: ignore[arg-type]
        mir_routing_enabled=cfg.intent_router_enabled,
        mir_profile=cfg.plugin_profile,
        mir_plugin_host=host,
        mir_db=db,
        mir_window_seconds=float(cfg.intent_window_seconds),
        mir_step_seconds=float(cfg.intent_step_seconds),
        mir_score_threshold=cfg.intent_score_threshold,
        mir_hysteresis=cfg.intent_hysteresis(),
    )


@pytest.mark.timeout(15)
@pytest.mark.integration
def test_disabled_router_config_keeps_pipeline_off(db) -> None:
    cfg = MeetingConfig()  # intent_router_enabled defaults to False
    session = _build_session_from_config(cfg, host=_full_host(), db=db)
    _seed_active_state(session, db)

    session.stop()

    # Pipeline did not run — no MIR persistence, no parked result.
    assert db.list_intent_windows("m-cfg") == []
    assert db.list_plugin_runs("m-cfg") == []
    assert session._mir_last_result is None  # type: ignore[attr-defined]


@pytest.mark.timeout(15)
@pytest.mark.integration
def test_enabled_router_config_drives_pipeline_with_tuned_threshold(db) -> None:
    # Threshold of 0.4 should let the keyword-heavy transcripts activate
    # both architecture and delivery intents. Profile "architect" picks
    # the architecture-leaning chain.
    cfg = MeetingConfig(
        intent_router_enabled=True,
        intent_window_seconds=60,
        intent_step_seconds=20,
        intent_score_threshold=0.4,
        intent_hysteresis_windows=1,
        plugin_profile="architect",
    )
    session = _build_session_from_config(cfg, host=_full_host(), db=db)
    _seed_active_state(session, db)

    session.stop()

    persisted_windows = db.list_intent_windows("m-cfg")
    assert len(persisted_windows) >= 1
    # Profile from config flowed through to persisted rows.
    assert all(w.profile == "architect" for w in persisted_windows)
    # Threshold from config flowed through.
    assert all(abs(w.threshold - 0.4) < 1e-6 for w in persisted_windows)
    # Pipeline result parked on the session.
    last = session._mir_last_result  # type: ignore[attr-defined]
    assert last is not None
    assert last.errors == []


@pytest.mark.timeout(15)
@pytest.mark.integration
def test_window_step_seconds_change_window_count(db) -> None:
    cfg_long = MeetingConfig(
        intent_router_enabled=True,
        intent_window_seconds=120,
        intent_step_seconds=120,  # one window per 120s -> few windows
        intent_score_threshold=0.4,
    )
    cfg_short = MeetingConfig(
        intent_router_enabled=True,
        intent_window_seconds=15,
        intent_step_seconds=5,  # tight stride -> many windows
        intent_score_threshold=0.4,
    )

    long_session = _build_session_from_config(cfg_long, host=_full_host(), db=db)
    _seed_active_state(long_session, db)
    long_session.stop()
    long_count = len(db.list_intent_windows("m-cfg"))

    # Reset DB rows for the second pass against a fresh meeting id.
    short_state = MeetingState(
        id="m-cfg-short",
        started_at=datetime(2026, 4, 26, 10, 0, 0),
        title="short windows",
        segments=long_session._state.segments,  # type: ignore[attr-defined]
    )
    db.save_meeting(short_state)
    short_session = MeetingSession(
        transcriber=_NoOpTranscriber(),  # type: ignore[arg-type]
        mir_routing_enabled=cfg_short.intent_router_enabled,
        mir_profile=cfg_short.plugin_profile,
        mir_plugin_host=_full_host(),
        mir_db=db,
        mir_window_seconds=float(cfg_short.intent_window_seconds),
        mir_step_seconds=float(cfg_short.intent_step_seconds),
        mir_score_threshold=cfg_short.intent_score_threshold,
        mir_hysteresis=cfg_short.intent_hysteresis(),
    )
    short_session._state = short_state  # type: ignore[attr-defined]
    short_session.stop()
    short_count = len(db.list_intent_windows("m-cfg-short"))

    # Smaller step → more windows. The exact ratio depends on segment
    # spacing, so just assert the qualitative direction.
    assert short_count > long_count
