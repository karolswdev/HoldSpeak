"""HS-93-06 — the deterministic fault plane: off by default, explicit-env only,
and every declared point fires exactly where the census says it does."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

import holdspeak.db as hsdb
from holdspeak import faults
from holdspeak.db import Database, reset_database
from holdspeak.faults import FAULT_ENV, FAULT_POINTS, PLUGIN_FAULT_PREFIX
from holdspeak.meeting_capture_journal import MeetingCaptureJournal
from holdspeak.meeting_recorder import AudioChunk
from holdspeak.meeting_session import MeetingSession, MeetingState, TranscriptSegment

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# The plane itself: inert unless HOLDSPEAK_FAULT names a point explicitly.
# ---------------------------------------------------------------------------


def test_fault_plane_is_inert_by_default(monkeypatch):
    monkeypatch.delenv(FAULT_ENV, raising=False)
    assert faults.active_faults() == frozenset()
    assert faults.fault_enabled("meeting.transcribe") is False
    assert faults.faulted_plugin_keys() == frozenset()
    faults.trip("meeting.transcribe")  # must not raise
    faults.trip("meeting.checkpoint_write", OSError)  # must not raise

    killed: list = []
    monkeypatch.setattr(faults.os, "kill", lambda *a: killed.append(a))
    faults.kill_process("meeting.finalize_kill")
    assert killed == []

    monkeypatch.setenv(FAULT_ENV, "")
    assert faults.active_faults() == frozenset()


def test_armed_point_fires_and_names_itself(monkeypatch):
    monkeypatch.setenv(FAULT_ENV, "meeting.transcribe,intel.plugin:risk_heatmap")
    assert faults.fault_enabled("meeting.transcribe") is True
    assert faults.fault_enabled("meeting.finalize_kill") is False
    assert faults.faulted_plugin_keys() == frozenset({"risk_heatmap"})
    with pytest.raises(faults.FaultInjected, match="meeting.transcribe"):
        faults.trip("meeting.transcribe")

    killed: list = []
    monkeypatch.setattr(faults.os, "kill", lambda *a: killed.append(a))
    monkeypatch.setenv(FAULT_ENV, "meeting.finalize_kill")
    faults.kill_process("meeting.finalize_kill")
    assert len(killed) == 1


def test_unknown_or_bare_fault_point_refuses(monkeypatch):
    monkeypatch.setenv(FAULT_ENV, "meeting.transcrib")
    with pytest.raises(ValueError, match="unknown fault point"):
        faults.active_faults()
    # The bare parameterized prefix names no plugin — refuse, don't no-op.
    monkeypatch.setenv(FAULT_ENV, PLUGIN_FAULT_PREFIX)
    with pytest.raises(ValueError, match="unknown fault point"):
        faults.active_faults()


def test_census_each_fault_point_locks_to_its_declared_site():
    """Every fault point is referenced by exactly its one declared module."""
    py_files = [
        p for p in (REPO_ROOT / "holdspeak").rglob("*.py")
        if p.relative_to(REPO_ROOT).as_posix() != "holdspeak/faults.py"
    ]
    contents = {p: p.read_text(encoding="utf-8") for p in py_files}
    for point, declared in FAULT_POINTS.items():
        needle = "faulted_plugin_keys" if point == PLUGIN_FAULT_PREFIX else f'"{point}"'
        hits = {
            p.relative_to(REPO_ROOT).as_posix()
            for p, text in contents.items()
            if needle in text
        }
        assert hits == {declared}, (
            f"fault point {point!r} must inject only at {declared}, found {sorted(hits)}"
        )
    # And nothing outside the declared sites imports the plane's triggers.
    trigger_users = {
        p.relative_to(REPO_ROOT).as_posix()
        for p, text in contents.items()
        if "from .faults import" in text or "from ..faults import" in text
    }
    assert trigger_users == set(FAULT_POINTS.values())


# ---------------------------------------------------------------------------
# Session-path fixtures (the durability-test pattern: real DB, stub recorder).
# ---------------------------------------------------------------------------


class _Recorder:
    def __init__(self, **kwargs):
        self.on_audio_chunk = kwargs.get("on_audio_chunk")

    def start(self):
        pass

    def stop(self):
        audio = np.zeros(32000, dtype=np.float32)
        return [AudioChunk(audio=audio, timestamp=0.0, source="mic", duration=2.0)], []

    def get_pending_chunks(self, since=0.0):
        return [], []

    def get_pending_device_chunks(self):
        return {}

    def trim_before(self, timestamp):
        pass


class _Transcriber:
    def transcribe(self, _audio):
        return "words that must survive"


@pytest.fixture
def session_env(tmp_path, monkeypatch):
    import holdspeak.meeting_session.session as session_module

    db = Database(tmp_path / "meetings.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(session_module, "MeetingRecorder", _Recorder)
    return db


def test_meeting_transcribe_fault_drops_segment_and_keeps_meeting(
    session_env, monkeypatch
):
    db = session_env
    # Control first: the identical run without the env produces a segment.
    session = MeetingSession(transcriber=_Transcriber())
    state = session.start()
    final = session.stop()
    assert [s.text for s in final.segments] == ["words that must survive"]
    assert db.meetings.get_meeting(state.id).capture_status == "finalized"

    # Treatment: transcription fails mid-meeting; the segment is dropped, the
    # meeting still finalizes with no exception and no false transcript.
    monkeypatch.setenv(FAULT_ENV, "meeting.transcribe")
    session = MeetingSession(transcriber=_Transcriber())
    state = session.start()
    final = session.stop()
    assert final.segments == []
    assert final.capture_status == "finalized"
    assert db.meetings.get_meeting(state.id).capture_status == "finalized"


def test_checkpoint_write_fault_marks_capture_recoverable(session_env, monkeypatch):
    db = session_env
    events: list[tuple[str, object]] = []
    monkeypatch.setenv(FAULT_ENV, "meeting.checkpoint_write")

    session = MeetingSession(
        transcriber=_Transcriber(),
        on_broadcast=lambda kind, data: events.append((kind, data)),
    )
    state = session.start()
    final = session.stop()

    # The disk refused the checkpoint: the capture is recoverable, the failure
    # is named, and the recovery broadcast carried retry/discard actions.
    assert final.capture_status == "recoverable"
    assert "Checkpoint failed" in (final.capture_failure or "") or (
        "Audio finalization failed" in (final.capture_failure or "")
    )
    saved = db.meetings.get_meeting(state.id)
    assert saved.capture_status == "recoverable"
    recovery_events = [d for k, d in events if k == "capture_recovery"]
    assert recovery_events and recovery_events[0]["actions"] == ["retry", "discard"]
    # The transcript that made it in before the failed write is retained.
    assert [s.text for s in saved.segments] == ["words that must survive"]


def test_checkpoint_write_fault_fires_in_journal(tmp_path, monkeypatch):
    root = tmp_path / "captures"
    journal = MeetingCaptureJournal(
        "meeting-fault", sample_rate=4, directory=root, checkpoint_seconds=1000
    )
    journal.append("mic", np.asarray([0.1, 0.2], dtype=np.float32))

    monkeypatch.setenv(FAULT_ENV, "meeting.checkpoint_write")
    with pytest.raises(OSError, match="meeting.checkpoint_write"):
        journal.checkpoint()
    assert "meeting.checkpoint_write" in (journal.error or "")
    with pytest.raises(OSError):
        journal.finalize()
    manifest = json.loads(journal.manifest_path.read_text())
    assert manifest["status"] == "recoverable"
    # No durable bytes were falsely claimed for the failed write.
    assert manifest["durable_bytes"] == {}
    assert MeetingCaptureJournal.recoverable(root)[0]["meeting_id"] == "meeting-fault"


# ---------------------------------------------------------------------------
# Intelligence-side points.
# ---------------------------------------------------------------------------


def _saved_meeting(db, meeting_id="m-fault"):
    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 7, 12, 10, 0, 0),
        ended_at=datetime(2026, 7, 12, 10, 30, 0),
        title="Fault walk",
        tags=["architecture"],
        segments=[
            TranscriptSegment(
                text=(
                    "Architecture review of the write path. We decided to adopt an "
                    "event sourced append log with hourly snapshots."
                ),
                speaker="Alex",
                start_time=0.0,
                end_time=50.0,
            ),
            TranscriptSegment(
                text="Action item: prove snapshot plus log tail rebuilds balances.",
                speaker="Mara",
                start_time=60.0,
                end_time=110.0,
            ),
        ],
    )
    db.meetings.save_meeting(state)
    return db.meetings.get_meeting(meeting_id)


@pytest.fixture
def intel_env(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *a, **k: db)
    yield db
    reset_database()


def test_intel_model_unavailable_fault_schedules_bounded_retry(
    intel_env, monkeypatch
):
    db = intel_env
    meeting = _saved_meeting(db, "m-model-gone")
    db.intel.enqueue_intel_job(
        "m-model-gone", transcript_hash=meeting.transcript_hash(), reason="test"
    )
    monkeypatch.setattr(
        "holdspeak.intel_queue.get_intel_runtime_status", lambda *a, **k: (True, "ready")
    )
    monkeypatch.setenv(FAULT_ENV, "intel.model_unavailable")

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    job = db.intel.get_intel_job("m-model-gone")
    assert job is not None, "the job must remain recoverable, not vanish"
    assert "intel.model_unavailable" in (job.last_error or "")
    assert int(job.attempts) == 1
    attempts = db.intel.list_intel_job_attempts("m-model-gone")
    assert attempts and attempts[0].outcome == "scheduled_retry"
    # No false Ready: the meeting never gained a completion stamp.
    refreshed = db.meetings.get_meeting("m-model-gone")
    assert refreshed.intel_status != "ready"
    assert refreshed.intel_completed_at is None


def test_named_plugin_fault_fails_exactly_that_key_then_exact_retry(
    intel_env, monkeypatch
):
    from holdspeak.meeting_plugins import run_meeting_plugin_chain
    from holdspeak.plugins.host import PluginRunResult, build_idempotency_key

    db = intel_env

    class _Host:
        def __init__(self):
            self.calls: list[list[str]] = []

        def execute_chain(
            self, plugin_chain, *, context, meeting_id, window_id,
            transcript_hash, defer_heavy,
        ):
            _ = context, defer_heavy
            self.calls.append(list(plugin_chain))
            return [
                PluginRunResult(
                    plugin_id=plugin_id,
                    plugin_version="test",
                    status="success",
                    idempotency_key=build_idempotency_key(
                        meeting_id=meeting_id, window_id=window_id,
                        plugin_id=plugin_id, transcript_hash=transcript_hash,
                    ),
                    duration_ms=1.0,
                    output={},
                    error=None,
                )
                for plugin_id in plugin_chain
            ]

    # Learn the routed chain on a control meeting with the plane unarmed.
    control_host = _Host()
    control = run_meeting_plugin_chain(
        db, _saved_meeting(db, "m-plugin-control"), profile="architect",
        host=control_host,
    )
    chain = list(control["plugin_chain"])
    assert chain, "the architect profile must route at least one plugin"
    faulted_key = chain[0]
    assert all(s == "success" for s in control["plugin_statuses"].values())

    # Treatment: fault exactly one named key on a fresh meeting.
    monkeypatch.setenv(FAULT_ENV, f"{PLUGIN_FAULT_PREFIX}{faulted_key}")
    meeting = _saved_meeting(db, "m-plugin-fault")
    treated_host = _Host()
    treated = run_meeting_plugin_chain(
        db, meeting, profile="architect", host=treated_host
    )
    assert treated["plugin_statuses"][faulted_key] == "error"
    assert all(
        status == "success"
        for plugin_id, status in treated["plugin_statuses"].items()
        if plugin_id != faulted_key
    )
    # The faulted key never reached the host; a real error run was persisted.
    assert all(faulted_key not in call for call in treated_host.calls)
    error_runs = [
        run for run in db.plugins.list_plugin_runs("m-plugin-fault", limit=100)
        if run.plugin_id == faulted_key
    ]
    assert error_runs and str(error_runs[0].status) == "error"
    assert "intel.plugin" in (error_runs[0].error or "")

    # Disarm and retry: only the faulted key executes, then everything resolves.
    monkeypatch.delenv(FAULT_ENV)
    retry_host = _Host()
    retried = run_meeting_plugin_chain(
        db, meeting, profile="architect", host=retry_host
    )
    assert retry_host.calls == [[faulted_key]]
    assert all(
        status in {"success", "deduped"}
        for status in retried["plugin_statuses"].values()
    )
