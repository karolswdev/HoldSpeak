"""Phase 143 Story 08 migration-cutover proofs."""

from __future__ import annotations

import json
from types import SimpleNamespace
from pathlib import Path
import threading
from typing import Any

import numpy as np
import pytest

from holdspeak.db import Database
from holdspeak.intel import ActionItem, IntelResult
from holdspeak.services.errors import ConflictError
from holdspeak.meeting_session.models import Bookmark, TranscriptSegment
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_adoption_service import (
    MEETING_MIGRATION_FAMILY,
    MEETING_DEFERRED_MIGRATION_FAMILY,
    SPEECH_RECOGNITION_MIGRATION_FAMILY,
    RoutedInferenceCoordinator,
)
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, _set


OWNER = Principal(PrincipalKind.OWNER, "meeting-migration-owner")


def _meeting_config(profile_id: str, *, provider: str = "local") -> SimpleNamespace:
    return SimpleNamespace(
        meeting=SimpleNamespace(
            intel_profile_id=profile_id,
            intel_provider=provider,
        ),
        model=SimpleNamespace(name="base", backend="auto", language="auto"),
    )


def _assign_meeting_routes_without_speech(db: Database) -> None:
    capabilities = (
        "meeting.live_analysis",
        "meeting.bookmark_label",
        "meeting.auto_title",
    )
    _profile(
        db,
        "meeting-profile",
        claims=("language", "structured_output", *(_result_claim(item) for item in capabilities)),
        modalities=("language", "audio"),
    )
    assignments = InferenceAssignmentService(db)
    for ordinal, capability in enumerate(capabilities, 1):
        _set(
            assignments,
            f"day-one-meeting-assignment-{ordinal}",
            {"kind": "capability", "capability_id": capability},
            "meeting-profile",
        )


def test_meeting_assignment_migration_copies_exact_saved_profile_and_replays(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "meeting-migration.db")
    capabilities = (
        "meeting.live_analysis",
        "meeting.bookmark_label",
        "meeting.auto_title",
    )
    _profile(
        db,
        "saved-meeting-profile",
        claims=("language", *(_result_claim(capability) for capability in capabilities)),
    )
    service = RoutedInferenceCoordinator(db)

    migrated = service.migrate_meeting_route_assignments(
        OWNER, _meeting_config("saved-meeting-profile")
    )

    assert migrated["family"] == MEETING_MIGRATION_FAMILY
    assert migrated["status"] == "migrated"
    assert migrated["legacy_config_read"] is True
    assert len(migrated["assignments"]) == len(capabilities)
    assignments = InferenceAssignmentService(db)
    for capability in capabilities:
        resolved = assignments.get_assignment(
            OWNER, {"kind": "capability", "capability_id": capability}
        )
        assert [
            (entry["ordinal"], entry["profile_id"], entry["profile_revision"])
            for entry in resolved["entries"]
        ] == [(1, "saved-meeting-profile", 1)]
    assert assignments.migration_marker(OWNER, family=MEETING_MIGRATION_FAMILY)

    replay = service.migrate_meeting_route_assignments(OWNER, object())
    assert replay["status"] == "migrated"
    assert replay["legacy_config_read"] is False


def test_deferred_meeting_migration_is_narrow_marker_driven_and_replays(tmp_path: Path) -> None:
    db = Database(tmp_path / "deferred-meeting-migration.db")
    _profile(
        db,
        "saved-deferred-profile",
        claims=("language", _result_claim("meeting.deferred_analysis")),
    )
    service = RoutedInferenceCoordinator(db)

    migrated = service.migrate_meeting_deferred_route_assignments(
        OWNER, _meeting_config("saved-deferred-profile")
    )

    assert migrated["family"] == MEETING_DEFERRED_MIGRATION_FAMILY
    assert migrated["status"] == "migrated" and migrated["legacy_config_read"] is True
    assignment = InferenceAssignmentService(db).get_assignment(
        OWNER, {"kind": "capability", "capability_id": "meeting.deferred_analysis"}
    )
    assert [(entry["profile_id"], entry["profile_revision"]) for entry in assignment["entries"]] == [
        ("saved-deferred-profile", 1)
    ]
    replay = service.migrate_meeting_deferred_route_assignments(OWNER, object())
    assert replay["legacy_config_read"] is False


def test_deferred_meeting_migration_refuses_blank_saved_profile_without_marker(tmp_path: Path) -> None:
    db = Database(tmp_path / "deferred-meeting-refusal.db")
    service = RoutedInferenceCoordinator(db)

    issue = service.migrate_meeting_deferred_route_assignments(OWNER, _meeting_config(""))

    assert issue["family"] == MEETING_DEFERRED_MIGRATION_FAMILY
    assert issue["reason_code"] == "builtin_profile_required"
    assert InferenceAssignmentService(db).migration_marker(
        OWNER, family=MEETING_DEFERRED_MIGRATION_FAMILY
    ) is None


def test_blank_or_cloud_legacy_meeting_values_never_guess_an_assignment(tmp_path: Path) -> None:
    db = Database(tmp_path / "meeting-migration-refusal.db")
    service = RoutedInferenceCoordinator(db)

    issue = service.migrate_meeting_route_assignments(
        OWNER, _meeting_config("", provider="cloud")
    )

    assert issue == {
        "schema": "InferenceAssignmentMigrationIssue@1",
        "family": MEETING_MIGRATION_FAMILY,
        "status": "needs_attention",
        "reason_code": "builtin_profile_required",
        "repair": "choose_meeting_model_profile",
        "source_sha256": issue["source_sha256"],
    }
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_assignment_heads").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_migrations WHERE family=?",
            (MEETING_MIGRATION_FAMILY,),
        ).fetchone()[0] == 0


def test_speech_recognition_without_a_saved_profile_refuses_without_preload_assignment(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "speech-migration-refusal.db")
    service = RoutedInferenceCoordinator(db)

    config = _meeting_config("saved-meeting-profile")
    config.model = SimpleNamespace(name="not-a-builtin-whisper-model", backend="auto", language="auto")
    issue = service.migrate_speech_recognition_route_assignments(OWNER, config)

    assert issue["schema"] == "InferenceAssignmentMigrationIssue@1"
    assert issue["family"] == SPEECH_RECOGNITION_MIGRATION_FAMILY
    assert issue["reason_code"] == "builtin_profile_required"
    assert issue["repair"] == "choose_audio_model_profile"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_assignment_heads").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_migrations WHERE family=?",
            (SPEECH_RECOGNITION_MIGRATION_FAMILY,),
        ).fetchone()[0] == 0


def test_builtin_local_whisper_migration_creates_one_visible_bound_profile_and_replays(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "speech-migration-happy.db")
    service = RoutedInferenceCoordinator(db)
    config = _meeting_config("saved-meeting-profile")
    config.model = SimpleNamespace(name="base", backend="mlx", language="en")

    migrated = service.migrate_speech_recognition_route_assignments(OWNER, config)

    assert migrated["family"] == SPEECH_RECOGNITION_MIGRATION_FAMILY
    assert migrated["status"] == "migrated"
    assignments = InferenceAssignmentService(db)
    assignment = assignments.get_assignment(
        OWNER, {"kind": "capability", "capability_id": "speech.transcribe"}
    )
    profile_id = assignment["entries"][0]["profile_id"]
    profile = service.plans._profiles.get_profile(OWNER, profile_id)
    assert profile["safe_presentation"]["badge"] == "legacy-model-config"
    assert profile["model_or_artifact_identity"].startswith("artifact-speech-migrated-")
    assert "speech_language:en" in profile["capability_manifest"]["claims"]
    assert assignments.migration_marker(
        OWNER, family=SPEECH_RECOGNITION_MIGRATION_FAMILY
    ) is not None
    assert not [
        item for item in assignments.list_assignments(OWNER)["assignments"]
        if item["scope"].get("capability_id") == "speech.preload"
    ]
    assert service.migrate_speech_recognition_route_assignments(OWNER, object())["legacy_config_read"] is False


def test_routed_uses_speech_marker_when_transcription_assignment_is_cleared(
    tmp_path: Path,
) -> None:
    """The speech cutover survives a cleared capability head."""
    db = Database(tmp_path / "speech-routed-marker.db")
    coordinator = RoutedInferenceCoordinator(db)
    migrated = coordinator.migrate_speech_recognition_route_assignments(
        OWNER, _meeting_config("unused")
    )
    assignments = InferenceAssignmentService(db)
    current = assignments.get_assignment(
        OWNER, {"kind": "capability", "capability_id": "speech.transcribe"}
    )
    assignments.clear_assignment(
        OWNER,
        {
            "command_id": "clear-speech-transcription",
            "expected_revision": current["revision"],
            "scope": {"kind": "capability", "capability_id": "speech.transcribe"},
            "capability_id": "speech.transcribe",
        },
    )

    assert migrated["family"] == SPEECH_RECOGNITION_MIGRATION_FAMILY
    assert assignments.routed("speech.transcribe") is True


def test_thoughts_marker_does_not_activate_unassigned_transcription(tmp_path: Path) -> None:
    """The thoughts/writing cutover cannot stand in for speech recognition."""
    db = Database(tmp_path / "thoughts-marker-only.db")
    _profile(db, "thought-v2", claims=("language", _result_claim("thought.interview")))
    _profile(db, "writing-v2", claims=("language", _result_claim("speech.intent_classify")))
    RoutedInferenceCoordinator(db).migrate_legacy_config(
        OWNER,
        SimpleNamespace(
            thoughts=SimpleNamespace(inference_target_id="thought-v2"),
            dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="writing-v2")),
        ),
    )
    assignments = InferenceAssignmentService(db)

    assert assignments.routed("speech.transcribe") is False
    # Preserve the existing family default for the unrelated provider route.
    assert assignments.routed("speech.rewrite") is True


def test_speech_session_freezes_only_assigned_provider_subset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing classifier route does not discard a chosen rewrite route."""
    from holdspeak.services import inference_assignment_service
    from holdspeak.speech_session.session import SpeechSession

    captured: dict[str, Any] = {}

    class _Assignments:
        def __init__(self, _db: Any) -> None:
            pass

        @staticmethod
        def routed(capability_id: str, **_selectors: Any) -> bool:
            return capability_id == "speech.rewrite"

    class _Adoption:
        @staticmethod
        def freeze_route_set(
            _principal: Any, *, command_id: str, routes: list[dict[str, str]]
        ) -> dict[str, dict[str, str]]:
            captured["command_id"] = command_id
            captured["routes"] = routes
            return {"rewrite": {"id": "rewrite-route"}}

    monkeypatch.setattr(
        inference_assignment_service, "InferenceAssignmentService", _Assignments
    )
    session = object.__new__(SpeechSession)
    session.broker = SimpleNamespace(
        database=object(), inference_adoption_service=_Adoption()
    )
    session.principal = OWNER
    session.plan = SimpleNamespace(session_id="speech-subset", has=lambda _key: True)
    session._routed_routes = {}

    session.freeze_assigned_provider_routes()

    assert captured["routes"] == [
        {
            "key": "rewrite",
            "capability_id": "speech.rewrite",
            "invocation_id": "speech-subset",
        }
    ]
    assert session._routed_routes == {"rewrite": {"id": "rewrite-route"}}



def _door_children(db: Database, prefix: str) -> list[str]:
    """The kernel receipt state of each door job whose run id starts with
    ``prefix`` (``meetingspeech`` / ``meetingpreload``), oldest first."""
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT r.state FROM kernel_operations o
                 JOIN kernel_receipts r ON r.operation_id=o.operation_id
                WHERE o.name='inference.invoke' AND o.native_id LIKE ? ESCAPE '\\'
                ORDER BY o.created_at""",
            (prefix + "\\_%",),
        ).fetchall()
    return [str(row["state"]) for row in rows]


@pytest.mark.parametrize("saved_backend", ["auto", "mlx"])
def test_migrated_local_whisper_bootstraps_ready_and_transcribes_first_meeting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, saved_backend: str
) -> None:
    """A never-loaded migrated model warms and serves its very first Meeting."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.meeting_session import MeetingSession
    from holdspeak.speech_session.transcription import audio_sha256
    from tests.unit.test_meeting_session_admission import FakeJournal, FakeRecorder

    db = Database(tmp_path / f"day-one-{saved_backend}.db")
    _assign_meeting_routes_without_speech(db)
    broker = _configure(db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", FakeRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", FakeJournal)
    # The auto decision is runtime's importability-only decision; no backend
    # constructor or model load happens while the migration runs.
    monkeypatch.setattr("holdspeak.transcribe._resolve_backend", lambda _value: "mlx")
    config = _meeting_config("saved-meeting-profile")
    config.model = SimpleNamespace(name="base", backend=saved_backend, language="auto")
    migrated = broker.inference_adoption_service.migrate_speech_recognition_route_assignments(
        OWNER, config
    )
    assert migrated["status"] == "migrated"
    speech_assignment = InferenceAssignmentService(db).get_assignment(
        OWNER, {"kind": "capability", "capability_id": "speech.transcribe"}
    )
    assert speech_assignment["entries"][0]["profile_id"].startswith("speech-migrated-")
    class _UnloadedMlx:
        backend = "mlx"
        model_name = "base"

        def __init__(self) -> None:
            self.loaded = False
            self.warm_calls = 0
            self.preload_outcome = ""

        def warm(self, admission: Any) -> None:
            self.warm_calls += 1
            outcome, _ = admission.preload_sequence(
                material={
                    "engine": "mlx",
                    "model": "base",
                    "language": "auto",
                    "candidate_ids": ["mlx-community/whisper-base-mlx", "mlx-community/whisper-base"],
                    "strategy_sequence": ["model-holder", "silent-audio"],
                    "stop_rules": ["success", "cancellation", "refusal", "deadline", "indeterminate", "exhaustion"],
                },
                run=lambda: "model-holder",
            )
            self.preload_outcome = outcome.outcome
            if outcome.outcome == "succeeded":
                self.loaded = True

        def transcribe(self, audio: np.ndarray, *, admission: Any) -> str:
            canonical = np.ascontiguousarray(audio, dtype=np.float32)
            outcome, text = admission.transcribe_child(
                material={
                    "audio_sha256": audio_sha256(canonical),
                    "sample_count": int(canonical.size),
                    "sample_rate": 16000,
                    "backend": "mlx",
                    "model": "base",
                    "language": "auto",
                },
                run=lambda: "day one exact",
                seed="ignored-by-interval-identity",
            )
            assert outcome.outcome == "succeeded"
            return str(text)

    transcriber = _UnloadedMlx()
    session = MeetingSession(
        transcriber,  # type: ignore[arg-type]
        principal=OWNER,
        intel_enabled=True,
        transcription_backend=saved_backend,
        transcription_model_name="base",
    )
    state = session.start()
    assert state.transcription_status == "active"
    assert transcriber.preload_outcome == "succeeded"
    assert transcriber.loaded is True and transcriber.warm_calls == 1
    assert session._speech_evidence is not None and session._speech_evidence["engine"] == "mlx"
    assert session._transcribe_audio(
        np.ones(16000, dtype=np.float32), source_id="mic", interval_start=0.0, interval_end=1.0
    ) == "day one exact"
    with db._connection() as conn:
        readiness = conn.execute(
            """SELECT o.state,o.reason_code
                 FROM model_profile_binding_heads h
                 JOIN model_profile_binding_revisions b
                   ON b.binding_id=h.binding_id AND b.revision=h.revision
                 JOIN model_profile_readiness_observations o
                   ON o.observation_id=b.readiness_observation_id
                WHERE b.profile_id LIKE 'speech-migrated-%'"""
        ).fetchone()
    assert tuple(readiness) == ("ready", "loaded_under_speech_preload")
    assert _door_children(db, "meetingpreload") == ["succeeded"]


def test_mlx_candidate_walk_runs_inside_one_meeting_preload_sequence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MLX keeps its physical candidate walk while Meeting receipts it once."""
    from holdspeak.transcribe import _MlxTranscriber

    impl = object.__new__(_MlxTranscriber)
    impl._path_or_hf_repo = None
    impl._candidates = ("mlx-community/whisper-base-mlx", "mlx-community/whisper-base")
    impl.model_name = "base"
    impl.language = None
    physical: list[tuple[str, str]] = []

    def holder(repo: str) -> str:
        physical.append(("model-holder", repo))
        if repo.endswith("-mlx"):
            raise RuntimeError("first candidate unavailable")
        return "model-holder"

    monkeypatch.setattr(impl, "_model_holder_get", holder)
    def silent(repo: str) -> str:
        physical.append(("silent-audio", repo))
        if repo.endswith("-mlx"):
            raise RuntimeError("first candidate fallback unavailable")
        return "silent-audio"

    monkeypatch.setattr(impl, "_silent_audio_load", silent)

    class _Admission:
        single_preload_sequence = True

        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def frozen_preload_material(self) -> dict[str, Any]:
            return {
                "engine": "mlx",
                "model": "base",
                "language": "auto",
                "candidate_ids": ["mlx-community/whisper-base-mlx", "mlx-community/whisper-base"],
                "strategy_sequence": ["model-holder", "silent-audio"],
                "stop_rules": ["success", "cancellation", "refusal", "deadline", "indeterminate", "exhaustion"],
            }

        def preload_sequence(self, *, material: dict[str, Any], run: Any) -> tuple[Any, Any]:
            self.calls.append(material)
            return SimpleNamespace(outcome="succeeded"), run(None)

    admission = _Admission()
    impl.ensure_loaded(admission)

    assert len(admission.calls) == 1
    assert admission.calls[0]["candidate_ids"] == list(impl._candidates)
    assert physical == [
        ("model-holder", "mlx-community/whisper-base-mlx"),
        ("silent-audio", "mlx-community/whisper-base-mlx"),
        ("model-holder", "mlx-community/whisper-base"),
    ]
    assert impl.loaded is True


def test_migrated_mlx_preload_failure_keeps_raw_capture_durably_record_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from holdspeak.kernel.runtime import _configure
    from holdspeak.meeting_session import MeetingSession
    from tests.unit.test_meeting_session_admission import FakeJournal, FakeRecorder

    db = Database(tmp_path / "day-one-preload-failure.db")
    _assign_meeting_routes_without_speech(db)
    broker = _configure(db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", FakeRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", FakeJournal)
    config = _meeting_config("saved-meeting-profile")
    config.model = SimpleNamespace(name="base", backend="mlx", language="auto")
    assert broker.inference_adoption_service.migrate_speech_recognition_route_assignments(
        OWNER, config
    )["status"] == "migrated"

    class _BrokenMlx:
        backend = "mlx"
        model_name = "base"
        loaded = False

        @staticmethod
        def warm(admission: Any) -> None:
            outcome, _ = admission.preload_sequence(
                material={
                    "engine": "mlx", "model": "base", "language": "auto",
                    "candidate_ids": ["mlx-community/whisper-base-mlx", "mlx-community/whisper-base"],
                    "strategy_sequence": ["model-holder", "silent-audio"],
                    "stop_rules": ["success", "cancellation", "refusal", "deadline", "indeterminate", "exhaustion"],
                },
                run=lambda: (_ for _ in ()).throw(RuntimeError("load failed")),
            )
            raise RuntimeError(outcome.outcome)

        @staticmethod
        def transcribe(*_args: Any, **_kwargs: Any) -> str:
            raise AssertionError("record-only Meeting must not transcribe")

    session = MeetingSession(
        _BrokenMlx(),  # type: ignore[arg-type]
        principal=OWNER,
        intel_enabled=True,
        transcription_backend="mlx",
        transcription_model_name="base",
    )
    state = session.start()
    assert state.capture_status == "recording"
    assert state.transcription_status == "record_only"
    assert state.transcription_status_detail == {
        "family": "speech-recognition-route-assignments",
        "reason_code": "transcriber_preload_failed",
        "repair": "repair_audio_model_lifecycle",
    }
    assert session._recorder is not None and session._recorder.started
    durable = db.meetings.get_meeting(state.id)
    assert durable is not None and durable.transcription_status == "record_only"


def test_meeting_transcription_routes_actual_canonical_bytes_and_exact_result(
    tmp_path: Path, monkeypatch
) -> None:
    from holdspeak.speech_session.transcription import audio_sha256
    from holdspeak.transcribe import Transcriber
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, broker, session = _bundle_session(
        tmp_path, monkeypatch, requested=("remote-a",)
    )
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    session.start()

    class _Impl:
        device = "cpu"
        compute_type = "int8"
        loaded = True

        def __init__(self) -> None:
            self.calls = 0

        @staticmethod
        def ensure_loaded(_admission: Any) -> None:
            return None

        def transcribe(self, _audio: Any) -> str:
            self.calls += 1
            return "Exact routed transcript"

    transcriber = Transcriber.__new__(Transcriber)
    transcriber.backend = "fake"
    transcriber.language = None
    transcriber.timeout_seconds = 0.0
    impl = _Impl()
    transcriber._impl = impl
    transcriber.model_name = "base"
    transcriber.device = "cpu"
    transcriber.compute_type = "int8"
    audio = np.asfortranarray(np.arange(16_000, dtype=np.float32))
    expected_sha = audio_sha256(np.ascontiguousarray(audio, dtype=np.float32))

    result = transcriber.transcribe(
        audio,
        admission=session._transcription_admission(
            source_id="mic", interval_start=10.0, interval_end=11.0, final_pass=False
        ),
    )

    assert result == "Exact routed transcript"
    # Each interval is one door job; source and final-pass changes are
    # distinct jobs on the same bytes.
    for source_id, final_pass in (("system", False), ("device:remote-a", False), ("mic", True)):
        assert transcriber.transcribe(
            audio,
            admission=session._transcription_admission(
                source_id=source_id,
                interval_start=10.0 if not final_pass else 11.0,
                interval_end=11.0 if not final_pass else 12.0,
                final_pass=final_pass,
            ),
        ) == result
    assert impl.calls == 4
    assert _door_children(db, "meetingspeech") == ["succeeded"] * 4
    with db._connection() as conn:
        journal = json.dumps([dict(row) for table in ("kernel_operations", "kernel_receipts", "kernel_journal")
                              for row in conn.execute(f"SELECT * FROM {table}")], default=str)
    # The transcript never reaches the kernel's journal.
    assert "Exact routed transcript" not in journal
    del expected_sha


def test_deferred_faster_whisper_constructor_is_one_derived_preload_child(
    tmp_path: Path, monkeypatch
) -> None:
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, broker, session = _bundle_session(tmp_path, monkeypatch)
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    constructed: list[object] = []

    class _Transcriber:
        model_name = "base"
        backend = "faster-whisper"

        @staticmethod
        def transcribe(*_args: Any, **_kwargs: Any) -> str:
            return ""

    session.transcriber = None
    session._transcriber_factory = lambda _frozen: constructed.append(_Transcriber()) or constructed[-1]
    session._transcription_backend = "faster-whisper"
    session._transcription_model_name = "base"

    session.start()

    assert len(constructed) == 1
    assert _door_children(db, "meetingpreload") == ["succeeded"]


def test_meeting_transcription_refuses_a_device_absent_from_the_frozen_set(
    tmp_path: Path, monkeypatch
) -> None:
    from tests.unit.test_meeting_session_admission import _bundle_session

    _db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    session.start()
    admission = session._transcription_admission(
        source_id="device:not-frozen", interval_start=0.0, interval_end=1.0
    )
    with pytest.raises(RuntimeError, match="meeting_transcription_source_not_frozen"):
        admission.transcribe_child(
            material={"audio_sha256": "sha256:" + "0" * 64},
            run=lambda: "must not run",
            seed="ignored",
        )
    assert session._transcription_refusal == "meeting_transcription_source_not_frozen"


def test_meeting_transcription_timeout_is_unknown_and_never_starts_a_second_model(
    tmp_path: Path, monkeypatch
) -> None:
    import time

    from holdspeak.transcribe import Transcriber, TranscriberTimeoutError
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, broker, session = _bundle_session(tmp_path, monkeypatch)
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    session.start()

    class _SlowImpl:
        device = "cpu"
        compute_type = "int8"
        loaded = True

        @staticmethod
        def ensure_loaded(_admission: Any) -> None:
            return None

        @staticmethod
        def transcribe(_audio: Any) -> str:
            time.sleep(0.2)
            return "late"

    transcriber = Transcriber.__new__(Transcriber)
    transcriber.backend = "fake"
    transcriber.language = None
    transcriber.timeout_seconds = 0.01
    transcriber._impl = _SlowImpl()
    transcriber.model_name = "base"
    transcriber.device = "cpu"
    transcriber.compute_type = "int8"
    with pytest.raises(TranscriberTimeoutError):
        transcriber.transcribe(
            np.ones(16_000, dtype=np.float32),
            admission=session._transcription_admission(
                source_id="mic", interval_start=0.0, interval_end=1.0
            ),
        )
    # One job, its outcome unknown; the door never retries a speech job.
    assert _door_children(db, "meetingspeech") == ["indeterminate"]


class _LiveEngine:
    active_provider = "fixture"
    active_model = "meeting-profile"

    def __init__(self) -> None:
        self.analysis_calls = 0
        self.labels = 0
        self.titles = 0

    def analyze(self, _transcript: str, *, stream: bool = False) -> Any:
        self.analysis_calls += 1
        assert stream is False  # Phase-B buffers; no primary token channel.
        return IntelResult(
            topics=["Budget"],
            action_items=[ActionItem(task="Send deck", owner="Me")],
            summary="Budget review.",
            raw_response="private",
        )

    def generate_bookmark_label_with_context(self, **_kwargs: Any) -> str:
        self.labels += 1
        return "Budget decision"

    def generate_title(self, _transcript: str) -> str:
        self.titles += 1
        return "Budget review"


def _door_runs(db: Any, job: str) -> list[tuple[str, str]]:
    """Each run of ``job`` through the engine door, in order: (the run id's
    tail after the door nonce, the receipt's outcome)."""
    prefix = "door_" + job.encode().hex() + "_"
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT o.native_id, r.outcome FROM kernel_operations o
                 JOIN kernel_receipts r ON r.operation_id=o.operation_id
                WHERE o.name='inference.invoke' AND o.native_id LIKE ? ORDER BY o.created_at""",
            (prefix + "%",),
        ).fetchall()
    return [("_".join(str(row["native_id"]).split("_")[5:]), str(row["outcome"])) for row in rows]


def test_live_bundle_routes_analysis_label_and_title_after_receipt_election(
    tmp_path: Path, monkeypatch
) -> None:
    """One elected validated result reaches each Meeting surface, never tokens."""
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    engine = _LiveEngine()
    broadcasts: list[tuple[str, Any]] = []
    session.on_broadcast = lambda kind, value: broadcasts.append((kind, value))
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)

    session.start()
    session._state.segments.append(
        TranscriptSegment(text="Discussed the budget", speaker="Me", start_time=0.0, end_time=5.0)
    )
    session._run_intel_analysis(final=True)
    session._state.bookmarks.append(Bookmark(timestamp=2.0, label="Bookmark @ 00:02"))
    session._refine_bookmark_labels("Budget review.")
    _outcome, title, _result = session._admitted_auto_title("Discussed the budget")

    assert session._state.intel is not None
    assert session._state.intel.summary == "Budget review."
    assert session._state.bookmarks[0].label == "Budget decision"
    assert title == {"title": "Budget review"}
    assert (engine.analysis_calls, engine.labels, engine.titles) == (1, 1, 1)
    assert not [event for event in broadcasts if event[0] == "intel_token"]
    # One job through the engine door each, each one receipt.
    for job in ("meeting.live_analysis", "meeting.bookmark_label", "meeting.auto_title"):
        assert [run[1] for run in _door_runs(db, job)] == ["succeeded"], job



def test_assignment_edit_during_a_meeting_reaches_its_next_text_call(
    tmp_path: Path, monkeypatch
) -> None:
    """The door reads a text job's engine at each call: nothing is frozen."""
    from holdspeak.services import engine_door
    from tests.unit.test_meeting_session_admission import FakeIntel, _bundle_session

    db, broker, session = _bundle_session(tmp_path, monkeypatch)
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: FakeIntel()
    session.start()
    _profile(
        db,
        "meeting-fallback-profile",
        claims=("language", "structured_output", _result_claim("meeting.live_analysis")),
    )
    assignment = InferenceAssignmentService(db).resolve_effective(
        OWNER, capability_id="meeting.live_analysis"
    )
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "edit-meeting-during-capture",
            "expected_revision": assignment["assignment"]["revision"],
            "scope": {"kind": "capability", "capability_id": "meeting.live_analysis"},
            "entries": [{"profile_id": "meeting-fallback-profile", "profile_revision": 1}],
        },
    )
    edited = engine_door.engine_for(broker, "meeting.live_analysis")
    assert edited.profile == "meeting-fallback-profile"
    session._state.segments.append(
        TranscriptSegment(text="After the edit", speaker="Me", start_time=0.0, end_time=1.0)
    )
    session._current_analysis_id = "after-edit"
    outcome, _projection, _value = session._admitted_live_window(
        "After the edit", final=False, analysis_id="after-edit"
    )
    assert outcome.outcome == "succeeded"
    with db._connection() as conn:
        target = conn.execute(
            """SELECT target_ref FROM kernel_operations
                WHERE name='inference.invoke' AND parent_operation_id=?
                ORDER BY created_at DESC LIMIT 1""",
            (session._intel_parent.operation_id,),
        ).fetchone()["target_ref"]
    assert target == f"deployment-revision:{edited.revision}"


def test_live_analysis_controller_owns_compatibility_retry_then_fallback(
    tmp_path: Path, monkeypatch
) -> None:
    """Meeting routing records 1/1, 1/2, then 2/3 before one UI publication."""
    from holdspeak.kernel.provider_signals import (
        ProviderCompatibilityRetry,
        ProviderPermanentNoGeneration,
    )
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, broker, session = _bundle_session(tmp_path, monkeypatch)
    _profile(
        db,
        "meeting-fallback-profile",
        claims=("language", "structured_output", _result_claim("meeting.live_analysis")),
    )
    assignments = InferenceAssignmentService(db)
    current = assignments.resolve_effective(OWNER, capability_id="meeting.live_analysis")
    assignments.set_assignment(
        OWNER,
        {
            "command_id": "two-entry-live-analysis",
            "expected_revision": current["assignment"]["revision"],
            "scope": {"kind": "capability", "capability_id": "meeting.live_analysis"},
            "entries": [
                {"profile_id": "meeting-profile", "profile_revision": 1},
                {"profile_id": "meeting-fallback-profile", "profile_revision": 1},
            ],
        },
    )

    class _ScriptedEngine:
        active_provider = "fixture"
        active_model = "scripted"

        def __init__(self) -> None:
            self.calls = 0

        def analyze(self, _transcript: str, *, stream: bool = False) -> IntelResult:
            assert stream is False
            self.calls += 1
            if self.calls == 1:
                raise ProviderCompatibilityRetry("json_mode", detail="PRIMARY_LOSER_TEXT")
            if self.calls == 2:
                raise ProviderPermanentNoGeneration()
            assert self.calls == 3
            return IntelResult(
                topics=["Elected topic"],
                action_items=[ActionItem(task="Elected action")],
                summary="ELECTED_WINNER",
                raw_response="private",
            )

    engine = _ScriptedEngine()
    received: list[str] = []
    session.on_intel = lambda snapshot: received.append(snapshot.summary)
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)

    session.start()
    session._state.segments.append(
        TranscriptSegment(text="Controller retry material", speaker="Me", start_time=0.0, end_time=5.0)
    )
    session._run_intel_analysis()

    assert engine.calls == 3
    assert received == ["ELECTED_WINNER"]
    assert "PRIMARY_LOSER_TEXT" not in received
    # The runner's dialect retry (``_r2``) on the first engine, then the door's
    # one retry on the next engine of the chain (``_n2``, attempt 2).
    assert _door_runs(db, "meeting.live_analysis") == [
        ("", "failed"), ("r2", "failed"), ("n2", "succeeded"),
    ]



def test_stop_ends_the_parent_queues_the_owed_work_and_refuses_a_late_job(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stop stops the live jobs, ends the parent and queues one deferred job."""
    from holdspeak.meeting_session.intel_plan import MeetingIntelRefused
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    state = session.start()
    parent_id = session._intel_parent.operation_id
    state.segments.append(
        TranscriptSegment(text="Stop aftercare transcript", speaker="Me", start_time=0.0, end_time=1.0)
    )
    state.bookmarks.append(Bookmark(timestamp=0.5, label="Bookmark"))

    session.stop()

    with db._connection() as conn:
        parent = conn.execute(
            "SELECT state FROM kernel_parent_runs WHERE operation_id=?", (parent_id,)
        ).fetchone()
        queued = conn.execute(
            "SELECT status,displaced_work FROM intel_jobs WHERE meeting_id=?", (state.id,)
        ).fetchall()
    assert parent is not None and parent["state"] != "OPEN"
    assert len(queued) == 1 and queued[0]["status"] == "queued"
    assert queued[0]["displaced_work"] == (
        '["final-analysis","bookmark-labels","auto-title"]'
    )
    with pytest.raises(MeetingIntelRefused):
        session._admitted_auto_title("late")


def test_stop_discards_a_late_routed_live_result_and_signals_its_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A result settling after the durable Stop fence reaches no Meeting callback."""
    from tests.unit.test_meeting_session_admission import _bundle_session

    _db, broker, session = _bundle_session(tmp_path, monkeypatch)
    entered = threading.Event()
    release = threading.Event()
    child_cancellations: list[str] = []

    class _BlockingEngine:
        active_provider = "fixture"
        active_model = "meeting-profile"

        @staticmethod
        def analyze(_transcript: str, *, stream: bool = False) -> IntelResult:
            assert stream is False
            entered.set()
            assert release.wait(timeout=2.0)
            return IntelResult(
                topics=["late"],
                action_items=[ActionItem(task="must not publish")],
                summary="late routed result",
                raw_response="private",
            )

    engine = _BlockingEngine()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    real_cancel = broker.inference_runner.cancel

    def observe_cancel(child_invocation_id: str) -> str:
        child_cancellations.append(child_invocation_id)
        return real_cancel(child_invocation_id)

    monkeypatch.setattr(broker.inference_runner, "cancel", observe_cancel)
    published: list[str] = []
    session.on_intel = lambda snapshot: published.append(snapshot.summary)
    session.start()
    session._state.segments.append(
        TranscriptSegment(text="Route this before Stop", speaker="Me", start_time=0.0, end_time=1.0)
    )

    worker = threading.Thread(target=session._run_intel_analysis, daemon=True)
    worker.start()
    assert entered.wait(timeout=2.0)

    # This is the exact Stop fence after the final transcription slot: it closes
    # live admission before the in-flight route can settle.
    session._handoff_intel_at_stop(session._state)
    release.set()
    worker.join(timeout=2.0)

    assert not worker.is_alive()
    assert child_cancellations
    assert published == []
    assert session._state.intel is None

    # The same fence gates transcript projection: a child result that reaches the
    # segment publisher after Stop is not appended or sent to the UI callback.
    transcript_callbacks: list[str] = []
    session.on_segment = lambda segment: transcript_callbacks.append(segment.text)
    late_segments: list[TranscriptSegment] = []
    session._publish_transcript_segment(
        TranscriptSegment(text="late routed transcript", speaker="Me", start_time=1.0, end_time=2.0),
        late_segments,
    )
    assert transcript_callbacks == []
    assert late_segments == []
    assert "late routed transcript" not in [segment.text for segment in session._state.segments]


@pytest.mark.parametrize("bundle_backed", [True, False])
def test_stop_aftercare_upserts_one_legacy_deferred_row_for_bundle_and_record_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bundle_backed: bool
) -> None:
    """Only an admitted Meeting hands displaced work to the deferred queue."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.meeting_session import MeetingSession
    from tests.unit.test_meeting_session_admission import FakeJournal, FakeRecorder, _bundle_session

    if bundle_backed:
        db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    else:
        from holdspeak.services import engine_door

        def no_engine(*_args: Any, **_kwargs: Any) -> Any:
            raise engine_door.EngineDoorError("no_engine", "nothing assigned")

        monkeypatch.setattr(engine_door, "engine_for", no_engine)
        db = Database(tmp_path / "record-only-stop.db")
        _configure(db)
        monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
        monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", FakeRecorder)
        monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", FakeJournal)

        class _Transcriber:
            model_name = "meeting-profile"

            def transcribe(self, *_args: Any, **_kwargs: Any) -> str:
                return ""

        session = MeetingSession(_Transcriber(), principal=OWNER, intel_enabled=True)  # type: ignore[arg-type]

    state = session.start()
    parent_id = session._intel_parent.operation_id if session._intel_parent is not None else ""
    state.segments.append(
        TranscriptSegment(text="Deferred aftercare", speaker="Me", start_time=0.0, end_time=1.0)
    )
    state.bookmarks.append(Bookmark(timestamp=0.5, label="Bookmark"))
    session.stop()
    # A repeated Stop handoff is idempotent for an admitted bundle and inert for
    # a refused/unassigned recording.
    session._handoff_intel_at_stop(state)

    with db._connection() as conn:
        rows = conn.execute(
            "SELECT status,displaced_work FROM intel_jobs WHERE meeting_id=?", (state.id,)
        ).fetchall()
        parent = (
            conn.execute(
                "SELECT state FROM kernel_parent_runs WHERE operation_id=?",
                (parent_id,),
            ).fetchone()
            if bundle_backed
            else None
        )

    if bundle_backed:
        # An admitted Meeting queues its owed work once and ends its parent.
        assert [(row["status"], row["displaced_work"]) for row in rows] == [(
            "queued", '["final-analysis","bookmark-labels","auto-title"]'
        )]
        assert parent is not None and parent["state"] != "OPEN"
    else:
        # A refused/unassigned recording has no parent or text work to hand off.
        assert rows == []
        assert session._live_engines is None
        assert state.transcription_status == "record_only"
        assert state.transcription_status_detail["reason_code"] == "no_assignment"
        assert state.intel_status == "refused"


def test_stop_aftercare_predicate_does_not_enqueue_empty_meeting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No transcript, bookmarks, or title need means no legacy deferred row."""
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    state = session.start()
    state.title = "Already titled"
    session.stop()

    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM intel_jobs WHERE meeting_id=?", (state.id,)
        ).fetchone()[0] == 0


def test_frozen_speech_deployment_replaces_mutable_large_instance_before_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A migrated base route cannot physically execute a stale large instance."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.meeting_session import MeetingSession
    from holdspeak.speech_session.transcription import audio_sha256
    from tests.unit.test_meeting_session_admission import FakeJournal, FakeRecorder

    db = Database(tmp_path / "frozen-base.db")
    _assign_meeting_routes_without_speech(db)
    broker = _configure(db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", FakeRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", FakeJournal)
    config = _meeting_config("meeting-profile")
    config.model = SimpleNamespace(name="base", backend="mlx", language="auto")
    assert broker.inference_adoption_service.migrate_speech_recognition_route_assignments(
        OWNER, config
    )["status"] == "migrated"
    constructed: list[dict[str, str]] = []

    class StaleLarge:
        backend = "mlx"
        model_name = "large"
        language = None
        loaded = True

    class FrozenTranscriber:
        loaded = True

        def __init__(self, frozen: dict[str, str]) -> None:
            constructed.append(dict(frozen))
            self.backend = frozen["backend"]
            self.model_name = frozen["model"]
            self.language = None if frozen["language"] == "auto" else frozen["language"]

        def transcribe(self, audio: np.ndarray, *, admission: Any) -> str:
            canonical = np.ascontiguousarray(audio, dtype=np.float32)
            outcome, result = admission.transcribe_child(
                material={
                    "audio_sha256": audio_sha256(canonical),
                    "sample_count": int(canonical.size),
                    "sample_rate": 16000,
                    "backend": self.backend,
                    "model": self.model_name,
                    "language": self.language or "auto",
                },
                run=lambda: f"physical-{self.model_name}",
                seed="ignored",
            )
            assert outcome.outcome == "succeeded"
            return str(result)

    # These mutable constructor values disagree with the previously migrated,
    # admitted route.  The factory receives only frozen bundle evidence.
    session = MeetingSession(
        StaleLarge(),  # type: ignore[arg-type]
        transcriber_factory=lambda frozen: FrozenTranscriber(frozen),
        principal=OWNER,
        intel_enabled=True,
        transcription_backend="mlx",
        transcription_model_name="large",
    )
    state = session.start()
    assert state.transcription_status == "active"
    assert constructed == [{
        "backend": "mlx", "model": "base", "language": "auto",
        "deployment_revision_id": constructed[0]["deployment_revision_id"],
    }]
    assert session.transcriber.model_name == "base"
    assert session._transcribe_audio(
        np.ones(16_000, dtype=np.float32), source_id="mic", interval_start=0.0, interval_end=1.0
    ) == "physical-base"


@pytest.mark.parametrize("base_here", [True, False])
def test_speech_readiness_asks_the_frozen_route_model_not_the_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, base_here: bool
) -> None:
    """PHILO-17 speech (Astra r1, MUST 1): the admitted route froze `base`;
    the mutable config says `large`. The readiness question is asked for
    `base`: with base here the meeting transcribes (a missing `large` does not
    force audio-only); with base missing it is audio-only (a present `large`
    cannot make it look ready)."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.meeting_session import MeetingSession
    from tests.unit.test_meeting_session_admission import FakeJournal, FakeRecorder

    db = Database(tmp_path / "frozen-readiness.db")
    _assign_meeting_routes_without_speech(db)
    broker = _configure(db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", FakeRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", FakeJournal)
    config = _meeting_config("meeting-profile")
    config.model = SimpleNamespace(name="base", backend="mlx", language="auto")
    assert broker.inference_adoption_service.migrate_speech_recognition_route_assignments(
        OWNER, config
    )["status"] == "migrated"
    asked: list[tuple[str, str]] = []
    constructed: list[str] = []

    def speech_ready(model: str, backend: str) -> bool:
        asked.append((model, backend))
        return base_here if model == "base" else not base_here

    class Frozen:
        loaded = True
        language = None

        def __init__(self, frozen: dict[str, str]) -> None:
            constructed.append(frozen["model"])
            self.backend = frozen["backend"]
            self.model_name = frozen["model"]

    session = MeetingSession(
        None,
        transcriber_factory=lambda frozen: Frozen(frozen),
        principal=OWNER,
        intel_enabled=True,
        transcription_backend="mlx",
        transcription_model_name="large",
        speech_ready=speech_ready,
    )
    state = session.start()

    assert asked == [("base", "mlx")]
    if base_here:
        assert state.transcription_status == "active"
        assert constructed == ["base"]
    else:
        assert state.transcription_status == "record_only"
        assert state.transcription_status_detail["reason_code"] == "speech_not_set_up"
        assert constructed == []


def test_removed_locator_free_speech_revision_requires_migration_provenance(tmp_path: Path) -> None:
    """Only the migration's known built-in declaration may await first load."""
    from holdspeak.deployment_revisions import resolve_deployment_revision
    from holdspeak.services.inference_adoption_service import RoutedInferenceCoordinator

    db = Database(tmp_path / "resolver-provenance.db")
    config = _meeting_config("meeting-profile")
    config.model = SimpleNamespace(name="base", backend="mlx", language="auto")
    assert RoutedInferenceCoordinator(db).migrate_speech_recognition_route_assignments(
        OWNER, config
    )["status"] == "migrated"
    with db._connection() as conn:
        revision_id = conn.execute(
            "SELECT deployment_revision_id FROM model_profile_binding_revisions"
        ).fetchone()[0]
        artifact_id = conn.execute(
            "SELECT artifact_id FROM deployment_revisions WHERE id=?", (revision_id,)
        ).fetchone()[0]
    assert resolve_deployment_revision(db, revision_id) is not None
    with db._connection() as conn:
        conn.execute(
            "UPDATE inference_model_artifacts SET source_kind='huggingface-download' WHERE artifact_id=?",
            (artifact_id,),
        )
    assert resolve_deployment_revision(db, revision_id) is None


def test_mlx_preload_sequence_stops_before_a_second_physical_call_after_cancellation() -> None:
    """The P=1 lifecycle child observes cancellation between frozen strategies."""
    from types import MethodType
    from holdspeak.kernel.model import KernelRefused
    from holdspeak.transcribe import _MlxTranscriber

    impl = object.__new__(_MlxTranscriber)
    impl.model_name = "base"
    impl.language = None
    impl._path_or_hf_repo = None
    impl._candidates = ("repo-a", "repo-b")
    cancelled = threading.Event()
    physical: list[tuple[str, str]] = []

    def holder(_self: Any, repo: str) -> str:
        physical.append(("model-holder", repo))
        cancelled.set()
        raise RuntimeError("in-flight fault")

    impl._model_holder_get = MethodType(holder, impl)
    impl._silent_audio_load = MethodType(lambda _self, repo: (_ for _ in ()).throw(AssertionError(repo)), impl)
    with pytest.raises(KernelRefused, match="speech_preload_cancelled"):
        impl._load_candidate_sequence(
            candidates=("repo-a", "repo-b"),
            strategies=("model-holder", "silent-audio"),
            cancellation=cancelled,
        )
    assert physical == [("model-holder", "repo-a")]


def test_persisted_v1_plan_is_displayable_history_without_a_resume_route() -> None:
    """A historical v1 plan can render, but cannot regain routing authority."""
    from holdspeak.meeting_session.intel_plan import (
        MeetingIntelPlan,
        decode_meeting_intel_plan_v1,
    )

    persisted = json.dumps(
        {
            "schema": 1,
            "meeting_id": "legacy-plan-meeting",
            "provenance": "meeting-stop",
            "config_revision": "config-v1",
            "routing_hash": "sha256:stored-routing",
            "plugin_registry_hash": "sha256:stored-plugins",
            "created_at": 1_700_000_000.0,
            "deadline_at": 1_700_001_800.0,
            "child_budget": 4,
            "capabilities": {
                "deferred-base-analysis": ["analysis-v1"],
                "plugin:follow-through": ["plugin-v1"],
            },
            "placements": {
                "deferred-base-analysis": {
                    "provider": "local",
                    "model": "historical-model",
                }
            },
            "sha256": "sha256:persisted-v1-plan",
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    plan = decode_meeting_intel_plan_v1(persisted)

    assert isinstance(plan, MeetingIntelPlan)
    assert plan.summary() == {
        "plan_schema": 1,
        "meeting_id": "legacy-plan-meeting",
        "provenance": "meeting-stop",
        "plan_sha256": "sha256:persisted-v1-plan",
        "config_revision": "config-v1",
        "routing_hash": "sha256:stored-routing",
        "plugin_registry_hash": "sha256:stored-plugins",
        "deadline_at": 1_700_001_800.0,
        "child_budget": 4,
        "capabilities": {
            "deferred-base-analysis": ["analysis-v1"],
            "plugin:follow-through": ["plugin-v1"],
        },
        "placements": {
            "deferred-base-analysis": {
                "provider": "local",
                "model": "historical-model",
            }
        },
    }
    for retired_execution_entrance in (
        "freeze_meeting_intel_plan",
        "resolve_placement",
        "resolve_meeting_placement",
        "admit",
        "execute",
        "resume",
        "replay",
        "assert_planned",
    ):
        assert not hasattr(plan, retired_execution_entrance)
