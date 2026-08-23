"""HS-131-08 Part A: live meeting intelligence is admitted per session.

One authenticated ``meeting.session`` parent over one frozen
``MeetingIntelPlan@1``; every ACTUAL provider dispatch during the live session
is one trusted ``inference.invoke@1`` child. A start with no authenticated
principal records without admitting anything. No transcript ever reaches the
kernel journal.

Only the admitted provider constructor is faked; the plan, the parent, the
runner, the projections, and the receipts are production code.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Iterator

import pytest

from holdspeak.db import Database
from holdspeak.intel import ActionItem, IntelResult
from holdspeak.kernel.runtime import _configure
from holdspeak.meeting_session.intel_plan import CAPABILITY_LIVE_ANALYSIS
from holdspeak.meeting_session.models import TranscriptSegment
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, _set

pytestmark = pytest.mark.timeout(60, method="signal")

OWNER = Principal(PrincipalKind.OWNER, "meeting-owner")
SENTINEL = "PINEAPPLEQUARTERLYSECRET"


class FakeIntel:
    """The one faked seam: the engine the admitted deployment revision builds."""

    active_provider = "test-provider"
    active_model = "test-model"

    def __init__(self) -> None:
        self.analyzed: list[str] = []
        self.labels: list[dict[str, str]] = []
        self.titles: list[str] = []
        self.result = IntelResult(
            topics=["Budget"],
            action_items=[ActionItem(task="Send the deck", owner="Me")],
            summary="The team reviewed the budget.",
            raw_response="{}",
        )

    def analyze(self, transcript: str, *, stream: bool = False) -> Iterator[Any]:
        self.analyzed.append(transcript)
        if not stream:
            return self.result

        def generate() -> Iterator[Any]:
            yield '{"topics":'
            yield ' ["Budget"]}'
            yield self.result

        return generate()

    def generate_bookmark_label_with_context(self, *, local_context: str, meeting_summary: str) -> str:
        self.labels.append({"context": local_context, "summary": meeting_summary})
        return "Budget decision"

    def generate_title(self, transcript: str) -> str:
        self.titles.append(transcript)
        return "Quarterly budget review"


class FakeRecorder:
    def __init__(self, **kwargs: Any) -> None:
        self.started = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> tuple[list[Any], list[Any]]:
        return [], []

    def get_pending_chunks(self, since: float = 0.0) -> tuple[list[Any], list[Any]]:
        return [], []

    def get_pending_device_chunks(self) -> list[Any]:
        return []


class FakeJournal:
    def __init__(self, meeting_id: str) -> None:
        self.meeting_id = meeting_id

    def append(self, *args: Any, **kwargs: Any) -> None:
        return None

    def finalize(self) -> None:
        return None

    def mark_recoverable(self, reason: str) -> None:
        return None


def _local_model_is_present(tmp_path: Path, monkeypatch) -> Path:
    """Make the `this_machine` leg REACHABLE, the way a real desk has it.

    HS-131-17: start no longer preflights a provider runtime — readiness is a
    property of the FROZEN placement (`_this_machine_readiness()` asks whether the
    configured local meeting model actually exists). Pointing that at a real file
    is the honest replacement for the old `get_intel_runtime_status -> (True, None)`
    patch: it makes the plan's live-analysis leg ready without constructing a
    single engine.
    """
    model = tmp_path / "local-meeting-intel.gguf"
    model.write_bytes(b"gguf")
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path",
        lambda: str(model),
    )
    return model


def _rig(tmp_path: Path, monkeypatch, *, principal: Any = OWNER, intel_enabled: bool = True):
    """Build a real database + broker + MeetingSession with a fake provider."""
    db = Database(tmp_path / "meeting.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    broker = _configure(db)
    engine = FakeIntel()
    _local_model_is_present(tmp_path, monkeypatch)

    # `build_intel_for_revision` resolves `this_machine` through the pinned local
    # branch, so the production revision -> engine path is exercised, not bypassed.
    # HS-131-13 made that branch construct `MeetingIntel` straight from the FROZEN
    # revision's `model_path` (it used to re-read mutable meeting config through
    # `build_configured_meeting_intel`), so the provider double is injected at the
    # engine class — the last constructor on the real path — rather than at the
    # configured-default seam that path no longer touches.
    # HS-131-17: the session module no longer imports `MeetingIntel`,
    # `get_intel_runtime_status`, or `resolve_intel_provider` at all — start
    # constructs nothing and preflights nothing — so the ONLY constructor left to
    # double is the one the admitted child reaches through `InferenceRunner`.
    # `_counted_engine` below re-patches this exact seam to COUNT constructions.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", FakeRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", FakeJournal)

    requests: list[Any] = []
    real_invoke = broker.inference_runner.invoke

    def observed_invoke(request, *args, **kwargs):
        requests.append(request)
        return real_invoke(request, *args, **kwargs)

    monkeypatch.setattr(broker.inference_runner, "invoke", observed_invoke)

    from holdspeak.meeting_session import MeetingSession

    class _Transcriber:
        model_name = "test-model"

        def transcribe(self, *args: Any, **kwargs: Any) -> str:
            return ""

    session = MeetingSession(
        _Transcriber(),  # type: ignore[arg-type]
        intel_enabled=intel_enabled,
        intel_deferred_enabled=True,
        principal=principal,
    )
    return db, broker, session, engine, requests


def _split_legs(monkeypatch, *, local: Any, cloud: Any) -> None:
    """Tell an ``auto`` plan's two frozen entries apart at their ONE constructor.

    HS-131-13 made the pinned ``this_machine`` branch build ``MeetingIntel``
    straight from the frozen revision instead of re-reading the configured default,
    so BOTH legs of an ``auto`` plan now reach this class. Production separates
    them by the provider it pins (``local`` on the same-device branch, ``cloud`` on
    the hub-default leg) and so does this double — patching the class flat would
    hand the local entry the cloud engine and quietly collapse the two-child proof.
    """
    monkeypatch.setattr(
        "holdspeak.intel.engine.MeetingIntel",
        lambda **kwargs: local if str(kwargs.get("provider")) == "local" else cloud,
    )


def _parent_rows(db: Database) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM kernel_parent_runs")]


def _operations(db: Database, *, name: str = "") -> list[dict[str, Any]]:
    query = "SELECT * FROM kernel_operations"
    parameters: tuple[Any, ...] = ()
    if name:
        query += " WHERE name=?"
        parameters = (name,)
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(query + " ORDER BY created_at", parameters)]


def _add_segment(session: Any, text: str, start: float) -> None:
    session._state.segments.append(
        TranscriptSegment(text=text, speaker="Me", start_time=start, end_time=start + 5.0)
    )


# --------------------------------------------------------------- the parent




def _counted_engine(monkeypatch, engine: Any) -> list[dict[str, Any]]:
    """Count every ACTUAL engine construction at the one constructor left."""
    built: list[dict[str, Any]] = []

    def build(**kwargs: Any) -> Any:
        built.append(kwargs)
        return engine

    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", build)
    return built


# ------------------------------------------------ HS-131-17: the start sentinel












# --------------------------------------------------------------- live windows








# ----------------------------------------------------------- absorbed seams




# -------------------------------------------- HS-131-17: automatic bookmarks


def _children_of(db: Database, parent_id: str) -> list[dict[str, Any]]:
    return [
        row for row in _operations(db, name="inference.invoke")
        if row["parent_operation_id"] == parent_id
    ]


def _capture_threads(monkeypatch) -> list[Any]:
    """Record every thread started from here on, so a test can join it.

    `add_bookmark` refines in the background exactly as it always did; the proof
    is about WHAT that worker reaches, not about it being synchronous.
    """
    started: list[Any] = []
    real = threading.Thread

    class _Recorded(real):  # type: ignore[misc, valid-type]
        def start(self) -> None:
            started.append(self)
            super().start()

    monkeypatch.setattr(threading, "Thread", _Recorded)
    return started


def _join(threads: list[Any], timeout: float = 10.0) -> None:
    for thread in list(threads):
        thread.join(timeout=timeout)
        assert not thread.is_alive(), "a bookmark refinement worker never finished"






# Phase-B design §45-51: following legacy tests preserve v1 reader law only.










# ------------------------------- Amendment 1: the frozen `auto` cloud fallback


class _AutoConfig:
    """A meeting config with no adopted destination and the `auto` intent."""

    intel_enabled = True
    intel_provider = "auto"
    intel_profile_id = ""
    intel_deferred_enabled = True
    intel_realtime_model = ""
    disabled_plugins: list[str] = []
    intel_cloud_reasoning_effort = None
    intel_cloud_store = False


def _freeze_auto_plan(db: Database, *, cloud: bool, monkeypatch) -> Any:
    from holdspeak.intel import providers as providers_module
    from holdspeak.meeting_session.intel_plan import freeze_meeting_intel_plan

    monkeypatch.setattr(
        providers_module,
        "get_cloud_intel_runtime_status",
        lambda **kwargs: (True, None) if cloud else (False, "Missing API key in $OPENAI_API_KEY"),
    )
    return freeze_meeting_intel_plan(
        db,
        meeting_id="m-auto",
        capabilities=(CAPABILITY_LIVE_ANALYSIS,),
        deadline_at=9e9,
        child_budget=8,
        meeting_config=_AutoConfig(),
    )


def _revision_rows(db: Database, revision_ids: tuple[str, ...]) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [
            dict(
                conn.execute(
                    "SELECT * FROM deployment_revisions WHERE id=?", (revision_id,)
                ).fetchone()
            )
            for revision_id in revision_ids
        ]








def _error_window(message: str):
    """A streaming window whose engine RETURNS a provider error result."""

    def analyze(transcript: str, *, stream: bool = False):
        result = IntelResult(
            topics=[], action_items=[], summary="", raw_response="", error=message
        )
        if not stream:
            return result

        def generate() -> Iterator[Any]:
            yield '{"topics":'
            yield result

        return generate()

    return analyze


def _auto_two_entry_session(tmp_path, monkeypatch):
    """A live session whose live-analysis capability has TWO frozen entries."""
    from dataclasses import replace

    db, broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    session.start()
    plan = _freeze_auto_plan(db, cloud=True, monkeypatch=monkeypatch)
    session._intel_plan = replace(plan, meeting_id=session._state.id)
    entries = session._intel_plan.revisions(CAPABILITY_LIVE_ANALYSIS)
    assert len(entries) == 2
    return db, broker, session, engine, requests, entries










# ------------------------------------------------------------ journal hygiene




# Phase-B bundle admission is deliberately separate from the v1 reader cases above.
_BUNDLE_CAPABILITIES = (
    "meeting.live_analysis",
    "meeting.bookmark_label",
    "meeting.auto_title",
    "speech.transcribe",
)


def _assign_bundle_routes(db: Database) -> None:
    _profile(
        db,
        "meeting-profile",
        claims=(
            "language",
            "structured_output",
            *(_result_claim(capability) for capability in _BUNDLE_CAPABILITIES),
        ),
        modalities=("language", "audio"),
    )
    assignments = InferenceAssignmentService(db)
    for ordinal, capability in enumerate(_BUNDLE_CAPABILITIES, 1):
        _set(
            assignments,
            f"meeting-bundle-assignment-{ordinal}",
            {"kind": "capability", "capability_id": capability},
            "meeting-profile",
        )


def _bundle_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, requested: tuple[str, ...] = ()
) -> tuple[Database, Any, Any]:
    db = Database(tmp_path / "bundle-meeting.db")
    _assign_bundle_routes(db)
    broker = _configure(db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", FakeRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", FakeJournal)

    class _Transcriber:
        model_name = "meeting-profile"

        def transcribe(self, *_args: Any, **_kwargs: Any) -> str:
            return ""

    from holdspeak.meeting_session import MeetingSession

    return db, broker, MeetingSession(
        _Transcriber(),  # type: ignore[arg-type]
        principal=OWNER,
        intel_enabled=True,
        requested_remote_device_ids=requested,
    )


@pytest.mark.parametrize(
    ("requested", "transcription", "parent_budget"),
    [
        ((), 17_286, 21_383),
        (("remote-a", "remote-b"), 34_570, 38_667),
    ],
)
def test_start_admits_complete_live_bundle_with_exact_aggregate_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    requested: tuple[str, ...],
    transcription: int,
    parent_budget: int,
) -> None:
    _db, _broker, session = _bundle_session(tmp_path, monkeypatch, requested=requested)

    state = session.start()

    bundle = session._route_bundle
    assert bundle is not None
    assert state.capture_status == "recording"
    assert bundle["parent_kind"] == "meeting.session"
    assert bundle["parent_child_budget"] == parent_budget
    assert bundle.get("requested_remote_device_ids", []) == list(requested)
    assert bundle["budget_groups"] == [
        {"id": "meeting-intelligence", "allocation": 4096, "member_keys": ["auto-title", "bookmark-label", "live-analysis"]},
        {"id": "meeting-preload", "allocation": 1, "member_keys": ["preload"]},
        {"id": "meeting-transcription", "allocation": transcription, "member_keys": ["transcription"]},
    ]
    assert {member["capability_id"] for member in bundle["members"]} == {
        *_BUNDLE_CAPABILITIES,
        "speech.preload",
    }


def test_route_refusal_keeps_raw_capture_in_durable_record_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = Database(tmp_path / "refusal.db")
    _configure(db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", FakeRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", FakeJournal)
    from holdspeak.meeting_session import MeetingSession

    class _Transcriber:
        model_name = "meeting-profile"

        def transcribe(self, *_args: Any, **_kwargs: Any) -> str:
            return ""

    session = MeetingSession(_Transcriber(), principal=OWNER, intel_enabled=True)  # type: ignore[arg-type]
    state = session.start()

    assert state.capture_status == "recording"
    assert session._recorder is not None and session._recorder.started
    assert state.transcription_status == "record_only"
    assert state.intel_status == "refused"
    durable = db.meetings.get_meeting(state.id)
    assert durable is not None and durable.transcription_status == "record_only"


def test_recorder_start_failure_fences_committed_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, _broker, session = _bundle_session(tmp_path, monkeypatch)

    def fail_start(self: FakeRecorder) -> None:
        self.started = True
        raise RuntimeError("device unavailable")

    monkeypatch.setattr(FakeRecorder, "start", fail_start)
    with pytest.raises(RuntimeError, match="device unavailable"):
        session.start()

    assert session._route_bundle is not None
    parent_id = session._route_bundle["parent_operation_id"]
    with db._connection() as conn:
        active = conn.execute(
            "SELECT COUNT(*) FROM inference_route_executions WHERE state IN ('active','stopping')"
        ).fetchone()[0]
        parent = conn.execute(
            "SELECT state FROM kernel_parent_runs WHERE operation_id=?", (parent_id,)
        ).fetchone()
    assert active == 0
    assert parent is not None and parent["state"] != "OPEN"


def test_late_transcriber_construction_failure_keeps_raw_capture_record_only(tmp_path, monkeypatch):
    """A frozen-route construction failure never prevents durable raw capture."""
    _db, _broker, session = _bundle_session(tmp_path, monkeypatch)
    session.transcriber = None

    def unavailable(_frozen):
        raise RuntimeError("model construction failed")

    session._transcriber_factory = unavailable
    state = session.start()
    assert state.capture_status == "recording"
    assert session._recorder is not None and session._recorder.started
    assert state.transcription_status == "record_only"
    assert state.transcription_status_detail == {
        "family": "speech-recognition-route-assignments",
        "reason_code": "transcriber_construction_failed",
        "repair": "repair_audio_model_lifecycle",
    }


def test_live_bundle_journal_never_contains_transcript_material(tmp_path, monkeypatch):
    """Live routed material stays private across operation, receipt, and journal rows."""
    db, broker, session = _bundle_session(tmp_path, monkeypatch)
    engine = FakeIntel()
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: engine
    state = session.start()
    state.segments.append(TranscriptSegment(SENTINEL, "Me", 0.0, 1.0))
    session._current_analysis_id = "privacy-window"
    session._admitted_live_window(SENTINEL, final=False, analysis_id="privacy-window")
    with db._connection() as conn:
        rows = []
        for table in ("kernel_operations", "kernel_receipts", "kernel_journal"):
            rows.extend(dict(row) for row in conn.execute(f"SELECT * FROM {table}"))
    assert rows
    assert all(SENTINEL not in json.dumps(row, default=str) for row in rows)
