"""Phase 143 Story 08 migration-cutover proofs."""

from __future__ import annotations

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
    assert session._route_bundle is not None and session._route_bundle.get("derived_preloads")
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
        preload_count = conn.execute(
            """SELECT COUNT(*) FROM inference_route_executions e
                 JOIN inference_route_plans p ON p.id=e.route_plan_id
                WHERE p.capability_id='speech.preload' AND e.terminal_outcome='succeeded'"""
        ).fetchone()[0]
    assert tuple(readiness) == ("ready", "loaded_under_speech_preload")
    assert preload_count == 1


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
    # Same source/window/final tuple adopts the elected execution; source and
    # final-pass changes remain distinct recurring operations on the same bytes.
    assert transcriber.transcribe(
        audio,
        admission=session._transcription_admission(
            source_id="mic", interval_start=10.0, interval_end=11.0, final_pass=False
        ),
    ) == result
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
    with db._connection() as conn:
        material = conn.execute(
            "SELECT payload_json FROM inference_adoption_material_snapshots"
        ).fetchone()[0]
        executions = conn.execute(
            "SELECT terminal_outcome FROM inference_route_executions"
        ).fetchall()
    assert expected_sha in material
    assert "Exact routed transcript" not in material
    assert [row["terminal_outcome"] for row in executions] == ["succeeded"] * 4


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
    assert next(
        group for group in session._route_bundle["budget_groups"]
        if group["id"] == "meeting-preload"
    )["allocation"] == 1
    with db._connection() as conn:
        preload = conn.execute(
            """SELECT e.terminal_outcome FROM inference_route_executions e
                 JOIN inference_operation_route_request_plans o ON o.id=e.operation_plan_id
                 JOIN inference_route_plans r ON r.id=o.route_plan_id
                WHERE r.capability_id='speech.preload'"""
        ).fetchall()
    assert [row["terminal_outcome"] for row in preload] == ["succeeded"]


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
    with db._connection() as conn:
        attempts = conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0]
        outcome = conn.execute(
            "SELECT terminal_outcome FROM inference_route_executions"
        ).fetchone()[0]
    assert attempts == 1
    assert outcome == "indeterminate"


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
    with db._connection() as conn:
        executions = conn.execute(
            "SELECT terminal_outcome FROM inference_route_executions ORDER BY started_at"
        ).fetchall()
    assert [row["terminal_outcome"] for row in executions] == ["succeeded"] * 3


def test_replaying_identical_live_material_reuses_the_elected_execution(
    tmp_path: Path, monkeypatch
) -> None:
    """Deterministic operation/command identities prevent repeat model egress."""
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    engine = _LiveEngine()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    session.start()
    monkeypatch.setattr(type(session), "duration", property(lambda _self: 5.0))
    session._state.segments.append(
        TranscriptSegment(text="Repeat this exact window", speaker="Me", start_time=0.0, end_time=5.0)
    )

    session._run_intel_analysis()
    session._run_intel_analysis()
    first = session._admitted_auto_title("Repeat this exact window")
    second = session._admitted_auto_title("Repeat this exact window")

    assert engine.analysis_calls == 1
    assert engine.titles == 1
    assert first[1] == second[1] == {"title": "Budget review"}
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_executions").fetchone()[0] == 2


def test_assignment_edit_after_meeting_bundle_freeze_does_not_retarget_route(
    tmp_path: Path, monkeypatch
) -> None:
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, broker, session = _bundle_session(tmp_path, monkeypatch)
    session.start()
    member = next(
        item for item in session._route_bundle["members"]
        if item["capability_id"] == "meeting.live_analysis"
    )
    before = broker.inference_adoption_service.plans.get_route_plan(
        OWNER, member["route_plan_id"]
    )
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
            "command_id": "edit-meeting-after-freeze",
            "expected_revision": assignment["assignment"]["revision"],
            "scope": {"kind": "capability", "capability_id": "meeting.live_analysis"},
            "entries": [{"profile_id": "meeting-fallback-profile", "profile_revision": 1}],
        },
    )
    after = broker.inference_adoption_service.plans.get_route_plan(
        OWNER, member["route_plan_id"]
    )
    assert after["sha256"] == before["sha256"]
    assert [entry["deployment_revision_id"] for entry in after["entries"]] == [
        entry["deployment_revision_id"] for entry in before["entries"]
    ]


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
    with db._connection() as conn:
        execution = conn.execute(
            "SELECT id,winning_attempt_id,terminal_outcome FROM inference_route_executions"
        ).fetchone()
        attempts = conn.execute(
            """SELECT id,route_leg_ordinal,physical_attempt_ordinal,leg_attempt_ordinal,
                      purpose,disposition
                 FROM inference_route_attempts WHERE execution_id=?
                 ORDER BY physical_attempt_ordinal""",
            (execution["id"],),
        ).fetchall()
    assert [(row["route_leg_ordinal"], row["physical_attempt_ordinal"], row["leg_attempt_ordinal"], row["purpose"])
            for row in attempts] == [
        (1, 1, 1, "primary"),
        (1, 2, 2, "compatibility"),
        (2, 3, 1, "fallback"),
    ]
    assert [row["disposition"] for row in attempts] == [
        "known_no_generation_transient",
        "provider_permanent",
        "owner_terminal",
    ]
    assert execution["terminal_outcome"] == "succeeded"
    assert execution["winning_attempt_id"] == attempts[2]["id"]


def test_meeting_kernel_refusal_is_terminal_without_retry_or_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from holdspeak.kernel.model import KernelRefused
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    _profile(
        db,
        "meeting-refusal-fallback",
        claims=("language", "structured_output", _result_claim("meeting.live_analysis")),
    )
    assignment = InferenceAssignmentService(db).resolve_effective(
        OWNER, capability_id="meeting.live_analysis"
    )
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "meeting-refusal-fallback",
            "expected_revision": assignment["assignment"]["revision"],
            "scope": {"kind": "capability", "capability_id": "meeting.live_analysis"},
            "entries": [
                {"profile_id": "meeting-profile", "profile_revision": 1},
                {"profile_id": "meeting-refusal-fallback", "profile_revision": 1},
            ],
        },
    )

    class RefusingEngine:
        active_provider = "fixture"
        active_model = "refusing"

        @staticmethod
        def analyze(_transcript: str, *, stream: bool = False) -> IntelResult:
            assert stream is False
            raise KernelRefused("meeting_provider_refused")

    engine = RefusingEngine()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    session.start()
    session._state.segments.append(
        TranscriptSegment(text="Refused work", speaker="Me", start_time=0.0, end_time=1.0)
    )
    session._run_intel_analysis()

    with db._connection() as conn:
        execution = conn.execute(
            """SELECT e.terminal_outcome
                 FROM inference_route_executions e
                 JOIN inference_operation_route_request_plans o ON o.id=e.operation_plan_id
                 JOIN inference_route_plans p ON p.id=o.route_plan_id
                WHERE p.capability_id='meeting.live_analysis'"""
        ).fetchone()
        attempts = conn.execute(
            """SELECT a.route_leg_ordinal,a.disposition
                 FROM inference_route_attempts a
                 JOIN inference_route_executions e ON e.id=a.execution_id
                 JOIN inference_operation_route_request_plans o ON o.id=e.operation_plan_id
                 JOIN inference_route_plans p ON p.id=o.route_plan_id
                WHERE p.capability_id='meeting.live_analysis'
                ORDER BY a.physical_attempt_ordinal"""
        ).fetchall()
    assert execution["terminal_outcome"] == "refused"
    assert [(row["route_leg_ordinal"], row["disposition"]) for row in attempts] == [
        (1, "dispatch_outcome_unknown")
    ]


def _admit_active_execution_for_each_bundle_member(broker: Any, session: Any) -> set[str]:
    """Start (but do not dispatch) one execution on each frozen live member."""
    assert session._route_bundle is not None
    execution_ids: set[str] = set()
    for member in session._route_bundle["members"]:
        capability = str(member["capability_id"])
        admitted = broker.inference_adoption_service.admit_on_frozen_route(
            OWNER,
            command_id=f"phase-b-stop-active-{capability}",
            route_plan_id=str(member["route_plan_id"]),
            capability_id=capability,
            operation_id=f"phase-b-stop-active-{capability}",
            payload={},
            reserved_output_tokens=16,
        )
        execution_ids.add(str(admitted["execution"]["id"]))
    return execution_ids


def test_stop_fences_every_bundle_member_refuses_reservation_and_survives_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stop owns the complete live bundle, rather than a legacy live-plan child."""
    from holdspeak.kernel.runtime import _configure
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, broker, session = _bundle_session(tmp_path, monkeypatch)
    state = session.start()
    execution_ids = _admit_active_execution_for_each_bundle_member(broker, session)
    state.segments.append(
        TranscriptSegment(text="Stop aftercare transcript", speaker="Me", start_time=0.0, end_time=1.0)
    )
    state.bookmarks.append(Bookmark(timestamp=0.5, label="Bookmark"))

    session.stop()

    with db._connection() as conn:
        executions = conn.execute(
            "SELECT id,state FROM inference_route_executions WHERE id IN ({})".format(
                ",".join("?" for _ in execution_ids)
            ),
            tuple(sorted(execution_ids)),
        ).fetchall()
        parent = conn.execute(
            "SELECT state FROM kernel_parent_runs WHERE operation_id=?",
            (session._route_bundle["parent_operation_id"],),
        ).fetchone()
        queued = conn.execute(
            "SELECT status,displaced_work FROM intel_jobs WHERE meeting_id=?", (state.id,)
        ).fetchall()

    assert {str(row["id"]) for row in executions} == execution_ids
    assert {str(row["state"]) for row in executions} == {"stopped"}
    assert parent is not None and parent["state"] == "CANCELLING"
    assert len(queued) == 1 and queued[0]["status"] == "queued"
    assert queued[0]["displaced_work"] == (
        '["final-analysis","bookmark-labels","auto-title"]'
    )

    member = session._route_bundle["members"][0]
    with pytest.raises(ConflictError) as sealed:
        broker.inference_adoption_service.admit_on_frozen_route(
            OWNER,
            command_id="phase-b-stop-late-reservation",
            route_plan_id=str(member["route_plan_id"]),
            capability_id=str(member["capability_id"]),
            operation_id="phase-b-stop-late-reservation",
            payload={},
            reserved_output_tokens=16,
        )
    assert sealed.value.code == "inference_route_execution_parent_sealed"

    # A fresh process receives the same durable seal; it cannot resume these live
    # executions or open a new one on their frozen bundle route.
    fresh = _configure(db)
    with db._connection() as conn:
        resumed = conn.execute(
            "SELECT state FROM inference_route_executions WHERE id IN ({})".format(
                ",".join("?" for _ in execution_ids)
            ),
            tuple(sorted(execution_ids)),
        ).fetchall()
    assert {str(row["state"]) for row in resumed} == {"stopped"}
    with pytest.raises(ConflictError) as restarted:
        fresh.inference_adoption_service.admit_on_frozen_route(
            OWNER,
            command_id="phase-b-stop-restart-reservation",
            route_plan_id=str(member["route_plan_id"]),
            capability_id=str(member["capability_id"]),
            operation_id="phase-b-stop-restart-reservation",
            payload={},
            reserved_output_tokens=16,
        )
    assert restarted.value.code == "inference_route_execution_parent_sealed"
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM intel_jobs WHERE meeting_id=?", (state.id,)
        ).fetchone()[0] == 1


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
    """Aftercare remains the legacy Meeting-keyed queue authority in Phase B."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.meeting_session import MeetingSession
    from tests.unit.test_meeting_session_admission import FakeJournal, FakeRecorder, _bundle_session

    if bundle_backed:
        db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    else:
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
    state.segments.append(
        TranscriptSegment(text="Deferred aftercare", speaker="Me", start_time=0.0, end_time=1.0)
    )
    state.bookmarks.append(Bookmark(timestamp=0.5, label="Bookmark"))
    session.stop()
    # A Stop retry/recovery uses the existing Meeting-keyed ON CONFLICT upsert.
    session._handoff_intel_at_stop(state)

    with db._connection() as conn:
        rows = conn.execute(
            "SELECT status,displaced_work FROM intel_jobs WHERE meeting_id=?", (state.id,)
        ).fetchall()
    assert [(row["status"], row["displaced_work"]) for row in rows] == [(
        "queued", '["final-analysis","bookmark-labels","auto-title"]'
    )]


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


def test_unavailable_frozen_live_member_stays_queued_not_live(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Live readiness reads frozen preflight eligibility rather than member presence."""
    from tests.unit.test_meeting_session_admission import _bundle_session

    db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    with db._connection() as conn:
        conn.execute(
            "UPDATE model_profile_readiness_observations SET state='unavailable',reason_code='fault-injected-unavailable'"
        )
    state = session.start()
    assert session._route_bundle is not None
    assert state.intel_status == "queued"
    assert state.intel_status_detail == "Queued for later processing: binding_not_ready"
