"""HS-92-04 — provisional identity, bounded-loss journal, recovery and conflicts."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import numpy as np
import pytest

from holdspeak.db import Database
from holdspeak.meeting_capture_journal import MeetingCaptureJournal
from holdspeak.meeting_session import MeetingSession, MeetingState, TranscriptSegment


def test_provisional_meeting_round_trips_and_recovers_same_id(tmp_path):
    db = Database(tmp_path / "meetings.db")
    started = datetime.now() - timedelta(seconds=12)
    checkpoint = started + timedelta(seconds=10)
    state = MeetingState(
        id="meeting-1",
        started_at=started,
        segments=[TranscriptSegment("durable words", "Me", 0, 8)],
        capture_status="recording",
        capture_checkpoint_at=checkpoint,
        capture_checkpoint_seconds=10,
        provenance="desktop",
    )

    db.meetings.save_meeting(state)
    provisional = db.meetings.get_meeting("meeting-1")
    assert provisional is not None
    assert provisional.ended_at is None
    assert provisional.capture_status == "recording"
    assert [segment.text for segment in provisional.segments] == ["durable words"]

    recovered = db.meetings.recover_capture("meeting-1")
    assert recovered is not None
    assert recovered.id == "meeting-1"
    assert recovered.ended_at == checkpoint
    assert recovered.capture_status == "recovered"


def test_desktop_opens_recorder_only_after_provisional_commit(
    tmp_path, monkeypatch
):
    import holdspeak.db as db_module
    import holdspeak.meeting_session.session as session_module

    db = Database(tmp_path / "meetings.db")
    monkeypatch.setattr(db_module, "get_database", lambda: db)
    monkeypatch.setenv("HOME", str(tmp_path))
    observed: dict[str, str] = {}

    class Recorder:
        def __init__(self, **kwargs):
            self.on_audio_chunk = kwargs.get("on_audio_chunk")

        def start(self):
            rows = db.meetings.list_meetings()
            assert len(rows) == 1, "the Meeting must commit before capture.start"
            observed["status_at_open"] = rows[0].capture_status

        def stop(self):
            return [], []

        def get_pending_device_chunks(self):
            return {}

    class Transcriber:
        def transcribe(self, _audio):
            return ""

    monkeypatch.setattr(session_module, "MeetingRecorder", Recorder)
    session = MeetingSession(transcriber=Transcriber())
    started = session.start()
    assert observed == {"status_at_open": "provisional"}
    assert db.meetings.get_meeting(started.id).capture_status == "recording"

    stopped = session.stop()
    assert stopped.id == started.id
    assert db.meetings.get_meeting(started.id).capture_status == "finalized"


def test_audio_journal_manifest_only_claims_fsynced_bytes(tmp_path):
    root = tmp_path / "captures"
    journal = MeetingCaptureJournal(
        "meeting-2", sample_rate=4, directory=root, checkpoint_seconds=1
    )
    journal.append("mic", np.asarray([0.1, 0.2, 0.3, 0.4], dtype=np.float32))

    manifest = json.loads(journal.manifest_path.read_text())
    assert manifest["status"] == "recording"
    assert manifest["durable_bytes"] == {"mic": 16}
    assert MeetingCaptureJournal.recoverable(root)[0]["meeting_id"] == "meeting-2"

    journal.finalize()
    manifest = json.loads(journal.manifest_path.read_text())
    assert manifest["status"] == "finalized"
    assert MeetingCaptureJournal.recoverable(root) == []


def test_equal_clock_conflict_keeps_losing_value_once(tmp_path):
    db = Database(tmp_path / "meetings.db")
    state = MeetingState(id="meeting-3", started_at=datetime.now(), title="Local")
    db.meetings.save_meeting(state)

    first = db.meetings.record_sync_conflict(
        "meeting-3",
        local_value=state.to_dict(),
        incoming_value={**state.to_dict(), "title": "Native"},
    )
    second = db.meetings.record_sync_conflict(
        "meeting-3",
        local_value=state.to_dict(),
        incoming_value={**state.to_dict(), "title": "Native"},
    )

    conflicts = db.meetings.list_sync_conflicts("meeting-3")
    assert first == second
    assert len(conflicts) == 1
    assert conflicts[0]["winner"] == "local"
    assert conflicts[0]["incoming"]["title"] == "Native"


def _routed_recovery_session(tmp_path, monkeypatch):
    """Create a migrated speech bundle with no physical model work."""
    from types import SimpleNamespace

    from holdspeak.kernel.runtime import _configure
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_adoption_service import RoutedInferenceCoordinator
    from holdspeak.meeting_session import MeetingSession
    from tests.unit.test_meeting_session_admission import FakeJournal, FakeRecorder
    from tests.unit.test_phase143_meeting_live_cutover import (
        _assign_meeting_routes_without_speech,
        _meeting_config,
    )

    owner = Principal(PrincipalKind.OWNER, "recovery-owner")
    db = Database(tmp_path / "recovery-route.db")
    _assign_meeting_routes_without_speech(db)
    broker = _configure(db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", FakeRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", FakeJournal)
    config = _meeting_config("meeting-profile")
    config.model = SimpleNamespace(name="base", backend="mlx", language="auto")
    assert RoutedInferenceCoordinator(db).migrate_speech_recognition_route_assignments(
        owner, config
    )["status"] == "migrated"

    class LoadedMlx:
        backend = "mlx"
        model_name = "base"
        language = None
        loaded = True

        def transcribe(self, *_args, **_kwargs):
            return ""

    session = MeetingSession(
        LoadedMlx(), principal=owner, intel_enabled=True,
        transcription_backend="mlx", transcription_model_name="base",
    )
    return db, broker, session


def _parent_state(db, bundle_id):
    with db._connection() as conn:
        return conn.execute(
            """SELECT p.state FROM kernel_parent_runs p
                 JOIN inference_parent_route_bundles b ON b.parent_operation_id=p.operation_id
                WHERE b.id=?""",
            (bundle_id,),
        ).fetchone()[0]


def test_recovery_converges_prefence_and_postfence_process_loss_to_one_aftercare_row(
    tmp_path, monkeypatch
):
    """Fault-injection: either Stop crash window recovers queue plus non-OPEN fence."""
    from holdspeak.meeting_session.models import TranscriptSegment
    from holdspeak.services.inference_parent_route_bundle_service import (
        InferenceParentRouteBundleService,
    )

    for point in ("before-fence", "inside-fence-transaction"):
        db, _broker, session = _routed_recovery_session(tmp_path / point, monkeypatch)
        state = session.start()
        state.segments.append(TranscriptSegment("aftercare", "Me", 0.0, 1.0))
        original_fence = InferenceParentRouteBundleService.fence_cancel
        original_enqueue = db.intel.enqueue_intel_job
        if point == "before-fence":
            monkeypatch.setattr(
                InferenceParentRouteBundleService,
                "fence_cancel",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(SystemExit("before fence")),
            )
        else:
            monkeypatch.setattr(
                db.intel,
                "enqueue_intel_job",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(SystemExit("inside fence")),
            )
        with pytest.raises(SystemExit):
            session.stop()
        # A process death rolls back the composed fence/upsert transaction; no
        # durable half-effect may exist before recovery owns the same predicate.
        assert _parent_state(db, session._route_bundle["id"]) == "OPEN"
        with db._connection() as conn:
            assert conn.execute("SELECT COUNT(*) FROM intel_jobs WHERE meeting_id=?", (state.id,)).fetchone()[0] == 0
        monkeypatch.setattr(InferenceParentRouteBundleService, "fence_cancel", original_fence)
        monkeypatch.setattr(db.intel, "enqueue_intel_job", original_enqueue)
        recovered = db.meetings.recover_capture(state.id)
        assert recovered is not None and recovered.capture_status == "recovered"
        with db._connection() as conn:
            assert conn.execute("SELECT COUNT(*) FROM intel_jobs WHERE meeting_id=?", (state.id,)).fetchone()[0] == 1
        assert _parent_state(db, session._route_bundle["id"]) != "OPEN"


def test_stop_persists_fence_retry_obligation_and_recovery_clears_it(tmp_path, monkeypatch):
    """Fault-injection: two fence failures retain aftercare and a durable retry path."""
    from holdspeak.meeting_session.models import TranscriptSegment
    from holdspeak.services.inference_parent_route_bundle_service import (
        InferenceParentRouteBundleService,
    )

    db, _broker, session = _routed_recovery_session(tmp_path, monkeypatch)
    state = session.start()
    state.segments.append(TranscriptSegment("aftercare", "Me", 0.0, 1.0))
    original = InferenceParentRouteBundleService.fence_cancel
    calls = []

    def fail(*_args, **_kwargs):
        calls.append(1)
        raise RuntimeError("fence fault")

    monkeypatch.setattr(InferenceParentRouteBundleService, "fence_cancel", fail)
    session.stop()
    assert len(calls) == 2
    with db._connection() as conn:
        marker = conn.execute(
            "SELECT route_fence_pending,route_fence_error FROM meetings WHERE id=?", (state.id,)
        ).fetchone()
        assert tuple(marker)[0] == 1 and "fence fault" in tuple(marker)[1]
        assert conn.execute("SELECT COUNT(*) FROM intel_jobs WHERE meeting_id=?", (state.id,)).fetchone()[0] == 1
    assert _parent_state(db, session._route_bundle["id"]) == "OPEN"

    monkeypatch.setattr(InferenceParentRouteBundleService, "fence_cancel", original)
    assert db.meetings.recover_capture(state.id) is not None
    with db._connection() as conn:
        assert conn.execute("SELECT route_fence_pending FROM meetings WHERE id=?", (state.id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM intel_jobs WHERE meeting_id=?", (state.id,)).fetchone()[0] == 1
    assert _parent_state(db, session._route_bundle["id"]) != "OPEN"


def test_pending_fence_aftercare_is_not_claimable_until_recovery_fences(tmp_path, monkeypatch):
    """Boundary: a durable fence retry marker blocks aftercare execution."""
    from holdspeak.meeting_session.models import TranscriptSegment
    from holdspeak.services.inference_parent_route_bundle_service import (
        InferenceParentRouteBundleService,
    )

    db, _broker, session = _routed_recovery_session(tmp_path, monkeypatch)
    state = session.start()
    state.segments.append(TranscriptSegment("aftercare", "Me", 0.0, 1.0))
    original = InferenceParentRouteBundleService.fence_cancel
    monkeypatch.setattr(
        InferenceParentRouteBundleService,
        "fence_cancel",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("fence fault")),
    )
    session.stop()

    assert db.intel.claim_next_intel_job() is None
    monkeypatch.setattr(InferenceParentRouteBundleService, "fence_cancel", original)
    assert db.meetings.recover_capture(state.id) is not None
    assert _parent_state(db, session._route_bundle["id"]) != "OPEN"
    first_claim = db.intel.claim_next_intel_job()
    assert first_claim is not None and first_claim.meeting_id == state.id
    assert first_claim.attempts == 1
    assert db.intel.claim_next_intel_job() is None


def test_recovery_enqueue_does_not_reclaim_running_aftercare(tmp_path, monkeypatch):
    """Fault-injection: recovery leaves a concurrently claimed job with its owner."""
    db, _broker, session = _routed_recovery_session(tmp_path, monkeypatch)
    state = session.start()
    state.segments.append(TranscriptSegment("atomic handoff", "Me", 0.0, 1.0))
    original_handoff = session._handoff_intel_at_stop

    def die_after_handoff(stop_state):
        original_handoff(stop_state)
        raise SystemExit("after atomic handoff")

    monkeypatch.setattr(session, "_handoff_intel_at_stop", die_after_handoff)
    with pytest.raises(SystemExit, match="after atomic handoff"):
        session.stop()

    original_save = db.meetings.save_meeting
    first_claim = []

    def save_then_claim(meeting):
        result = original_save(meeting)
        if meeting.id == state.id and meeting.capture_status == "recovered" and not first_claim:
            first_claim.append(db.intel.claim_next_intel_job())
        return result

    monkeypatch.setattr(db.meetings, "save_meeting", save_then_claim)
    assert db.meetings.recover_capture(state.id) is not None
    job = db.intel.get_intel_job(state.id)
    assert first_claim and first_claim[0] is not None
    assert job is not None and job.status == "running" and job.attempts == 1
    assert db.intel.claim_next_intel_job() is None
