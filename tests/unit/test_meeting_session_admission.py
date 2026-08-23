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
from holdspeak.meeting_session.intel_plan import (
    CAPABILITY_AUTO_TITLE,
    CAPABILITY_BOOKMARK_LABEL,
    CAPABILITY_DEFERRED_ANALYSIS,
    CAPABILITY_LIVE_ANALYSIS,
    CAPABILITY_NOT_PLANNED,
    MeetingIntelRefused,
    PRINCIPAL_REQUIRED,
)
from holdspeak.meeting_session.models import Bookmark, TranscriptSegment
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


def legacy_start_admits_one_authenticated_parent_over_a_frozen_plan(tmp_path, monkeypatch):
    db, broker, session, _, _ = _rig(tmp_path, monkeypatch)
    state = session.start()

    rows = _parent_rows(db)
    assert len(rows) == 1
    parent = rows[0]
    assert parent["kind"] == "meeting.session"
    assert parent["definition_ref"] == f"meeting:{state.id}:intel"
    assert parent["state"] == "OPEN"
    # HS-131-09 Sol Amendment 6: a transcription-bearing session buys its own
    # headroom (4096 + ceil(12h / 10s) + 2), so 12 hours of intervals can no
    # longer deterministically exhaust the intelligence allocation.
    assert parent["child_budget"] == 8418

    plan = session._intel_plan
    assert plan is not None
    # The immutable definition revision IS the plan hash.
    assert parent["definition_revision"] == plan.sha256
    assert plan.deadline_at - plan.created_at == pytest.approx(12 * 60 * 60, abs=1)

    operation = _operations(db, name="meeting.session")
    assert len(operation) == 1
    assert operation[0]["principal_kind"] == "owner"
    assert operation[0]["principal_identity"] == "meeting-owner"
    assert operation[0]["idempotency_key"] == f"meeting-intel-session:{state.id}"

    # Every capability names an ORDERED set of frozen deployment revisions, and
    # each entry really exists in `deployment_revisions`.
    for capability in (
        CAPABILITY_LIVE_ANALYSIS,
        CAPABILITY_BOOKMARK_LABEL,
        CAPABILITY_AUTO_TITLE,
        CAPABILITY_DEFERRED_ANALYSIS,
    ):
        revisions = plan.revisions(capability)
        assert revisions and all(str(item).startswith("dep_") for item in revisions)
        with db._connection() as conn:
            found = conn.execute(
                "SELECT id FROM deployment_revisions WHERE id=?", (revisions[0],)
            ).fetchone()
        assert found is not None, capability
        assert plan.assert_planned(capability, revisions[0]) == revisions[0]

    # The durable parent snapshot is hashes, ids, and capability names only.
    snapshot = json.loads(parent["input_json"])
    assert snapshot["plan_sha256"] == plan.sha256
    assert set(snapshot["capabilities"]) == set(plan.capabilities)
    assert "transcript" not in json.dumps(snapshot).lower()


def _counted_engine(monkeypatch, engine: Any) -> list[dict[str, Any]]:
    """Count every ACTUAL engine construction at the one constructor left."""
    built: list[dict[str, Any]] = []

    def build(**kwargs: Any) -> Any:
        built.append(kwargs)
        return engine

    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", build)
    return built


# ------------------------------------------------ HS-131-17: the start sentinel


def legacy_start_freezes_the_plan_and_constructs_zero_engines(tmp_path, monkeypatch):
    """Start admits ONE parent over a frozen plan and builds no provider at all.

    The session used to preflight the provider runtime and construct a long-lived
    `MeetingIntel` beside the plan — a model loaded merely to announce that a
    meeting is live. Readiness is now a property of the FROZEN placement, so start
    reaches no constructor; the FIRST actual child builds the exact frozen
    revision, exactly once.
    """
    db, broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    built = _counted_engine(monkeypatch, engine)

    state = session.start()

    # The plan and the parent exist...
    assert session._intel_plan is not None
    assert session._intel_parent is not None
    assert len(_parent_rows(db)) == 1
    # ...liveness is EXPLICIT state, not an object...
    assert session._intel_live is True
    assert not hasattr(session, "_intel")
    assert state.intel_status == "live"
    # ...and nothing was constructed or dispatched.
    assert built == []
    assert requests == []
    assert engine.analyzed == []
    assert _operations(db, name="inference.invoke") == []

    # The FIRST actual child is what constructs, and it constructs exactly one
    # engine, from the plan's frozen revision.
    _add_segment(session, "The first window of real discussion", 0.0)
    session._run_intel_analysis()

    assert len(built) == 1
    children = _operations(db, name="inference.invoke")
    assert len(children) == 1
    assert requests[0].deployment_revision == session._intel_plan.primary(
        CAPABILITY_LIVE_ANALYSIS
    )


def legacy_an_unreachable_planned_leg_keeps_the_queued_status_and_never_goes_live(
    tmp_path, monkeypatch
):
    """No preflight does NOT mean pretending. A leg that cannot run says so.

    The old runtime preflight produced `queued` (or `error` when deferral is off)
    with the reason on the meeting. That behavior is preserved from the plan's own
    readiness facts — and, critically, still constructs nothing.
    """
    db, _broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    built = _counted_engine(monkeypatch, engine)
    # The configured local model is gone: the frozen `this_machine` leg is not
    # reachable, and no cloud fallback is frozen (the plan's provider is `local`).
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path",
        lambda: str(tmp_path / "absent-model.gguf"),
    )

    state = session.start()

    assert session._intel_live is False
    assert state.intel_status == "queued"
    assert "absent-model.gguf" in str(state.intel_status_detail)
    # The parent is still admitted (transcription rides on it) and the plan is
    # still frozen — but no engine and no child exist.
    assert session._intel_parent is not None
    assert built == []
    assert requests == []
    assert _operations(db, name="inference.invoke") == []

    # ...and the live cadence stays shut: a window admits nothing.
    _add_segment(session, "A window nobody can analyze", 0.0)
    session._run_intel_analysis()
    assert requests == []
    assert engine.analyzed == []


def legacy_device_start_without_principal_refuses_intelligence_and_still_records(tmp_path, monkeypatch):
    db, broker, session, engine, requests = _rig(tmp_path, monkeypatch, principal=None)
    built = _counted_engine(monkeypatch, engine)
    state = session.start()
    assert built == []

    # Recording is unaffected.
    assert state.capture_status == "recording"
    assert session._recorder is not None

    # Intelligence is refused by name; no OWNER principal was synthesized.
    assert state.intel_status == "refused"
    assert PRINCIPAL_REQUIRED in str(state.intel_status_detail)
    assert session.intel_enabled is False
    assert session._intel_live is False
    assert session._intel_parent is None

    # ZERO kernel operations exist — and, HS-131-17, zero engines and zero
    # children: a recording-only session builds nothing at all.
    assert _parent_rows(db) == []
    assert _operations(db) == []
    assert requests == []
    assert engine.analyzed == []


def legacy_route_refusal_records_durable_record_only_and_starts_raw_audio(tmp_path, monkeypatch):
    """Phase-B capture refusal is visible on the Meeting, never an audio failure."""
    db, _broker, session, _engine, _requests = _rig(tmp_path, monkeypatch)

    def refuse(*_args: Any, **_kwargs: Any) -> Any:
        raise MeetingIntelRefused("no_assignment", "meeting.live_analysis")

    monkeypatch.setattr(
        "holdspeak.meeting_session.intel_admission.freeze_meeting_intel_plan", refuse
    )
    state = session.start()

    assert state.capture_status == "recording"
    assert session._recorder is not None and session._recorder.started is True
    assert state.transcription_status == "record_only"
    assert state.transcription_status_detail == {
        "family": "meeting-route-assignments",
        "reason_code": "no_assignment",
        "repair": "repair_meeting_route_assignment",
    }
    durable = db.meetings.get_meeting(state.id)
    assert durable is not None
    assert durable.transcription_status == "record_only"
    assert durable.transcription_status_detail == state.transcription_status_detail
    assert state.intel_status == "refused"


def legacy_late_transcriber_construction_failure_keeps_raw_capture_record_only(tmp_path, monkeypatch):
    _db, _broker, session, _engine, _requests = _rig(tmp_path, monkeypatch)
    session.transcriber = None

    def unavailable() -> Any:
        raise RuntimeError("model construction failed")

    session._transcriber_factory = unavailable
    state = session.start()

    assert state.capture_status == "recording"
    assert session._recorder is not None and session._recorder.started is True
    assert state.transcription_status == "record_only"
    assert state.transcription_status_detail == {
        "family": "speech-recognition-route-assignments",
        "reason_code": "transcriber_construction_failed",
        "repair": "repair_audio_model_lifecycle",
    }
    assert session._transcribe_thread is None


# --------------------------------------------------------------- live windows


def legacy_two_model_windows_admit_two_distinct_children_and_empty_window_admits_none(tmp_path, monkeypatch):
    db, broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    session.start()
    parent_id = session.intel_session_operation_id()

    _add_segment(session, f"First window about {SENTINEL}", 0.0)
    session._run_intel_analysis()
    _add_segment(session, "Second window with more detail", 10.0)
    session._run_intel_analysis()

    children = [row for row in _operations(db, name="inference.invoke") if row["parent_operation_id"] == parent_id]
    assert len(children) == 2
    assert len({row["native_id"] for row in children}) == 2
    assert all(broker.store.receipt(row["operation_id"])["outcome"] == "succeeded" for row in children)
    assert len(engine.analyzed) == 2
    assert [request.definition_origin.contract for request in requests] == [
        "holdspeak.meeting-live-analysis",
        "holdspeak.meeting-live-analysis",
    ]
    # Each child repeats the exact plan-selected revision for its capability.
    planned = session._intel_plan.primary(CAPABILITY_LIVE_ANALYSIS)
    assert {request.deployment_revision for request in requests} == {planned}
    # The earned result reached meeting state only through the staged projection.
    assert session._state.intel is not None
    assert session._state.intel_status == "ready"

    # An empty window is not model work: it admits nothing.
    session._state.segments.clear()
    session._run_intel_analysis()
    still = [row for row in _operations(db, name="inference.invoke") if row["parent_operation_id"] == parent_id]
    assert len(still) == 2
    assert len(engine.analyzed) == 2


def legacy_already_running_window_is_skipped_without_admitting(tmp_path, monkeypatch):
    _db, _broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    session.start()
    _add_segment(session, "Some discussion", 0.0)

    class _AliveThread:
        def is_alive(self) -> bool:
            return True

    session._intel_thread = _AliveThread()  # type: ignore[assignment]
    session._maybe_run_intel()
    assert requests == []
    assert engine.analyzed == []


def legacy_cancelled_parent_refuses_the_next_window_before_any_provider_call(tmp_path, monkeypatch):
    db, broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    session.start()
    parent = session._intel_parent
    _add_segment(session, "First window", 0.0)
    session._run_intel_analysis()
    assert len(engine.analyzed) == 1

    broker.parent_run_controller.cancel(parent.context, OWNER)

    _add_segment(session, "Window after cancellation", 10.0)
    session._run_intel_analysis()

    # The second window was refused at admission: no operation, no provider call.
    assert len(engine.analyzed) == 1
    assert len(_operations(db, name="inference.invoke")) == 1
    assert session._state.intel_status == "refused"
    detail = str(session._state.intel_status_detail)
    assert any(
        reason in detail for reason in ("parent_context_invalid", "parent_operation_not_running")
    ), detail


# ----------------------------------------------------------- absorbed seams


def legacy_bookmark_label_and_auto_title_run_as_session_children(tmp_path, monkeypatch):
    db, broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    session.start()
    parent_id = session.intel_session_operation_id()
    _add_segment(session, "We agreed to cut the travel budget", 0.0)
    session._state.bookmarks.append(Bookmark(timestamp=2.0, label="Bookmark 1"))

    session._refine_bookmark_labels("The team reviewed the budget.")
    _, projection, _ = session._admitted_auto_title("We agreed to cut the travel budget")

    assert engine.labels and engine.titles
    assert session._state.bookmarks[0].label == "Budget decision"
    assert str((projection or {}).get("title")) == "Quarterly budget review"

    contracts = [request.definition_origin.contract for request in requests]
    assert contracts == ["holdspeak.meeting-bookmark-label", "holdspeak.meeting-auto-title"]
    children = [row for row in _operations(db, name="inference.invoke") if row["parent_operation_id"] == parent_id]
    assert len(children) == 2
    assert all(broker.store.receipt(row["operation_id"])["outcome"] == "succeeded" for row in children)


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


def legacy_automatic_bookmark_label_runs_as_one_admitted_child_with_context(tmp_path, monkeypatch):
    """`add_bookmark` reaches the model ONLY through the admitted seam.

    The deterministic timestamp label is written first, ONE trusted child does the
    refinement (carrying the local context AND the latest earned meeting summary),
    it earns one terminal receipt, and only then does the label change.
    """
    db, broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    session.start()
    parent_id = session.intel_session_operation_id()
    _add_segment(session, "We agreed to cut the travel budget", 0.0)
    # An earned live window supplies the grounding summary the seam must pass.
    session._run_intel_analysis()
    assert session._state.intel is not None
    engine.labels.clear()
    before = {row["operation_id"] for row in _children_of(db, parent_id)}
    built = _counted_engine(monkeypatch, engine)
    workers = _capture_threads(monkeypatch)

    bookmark = session.add_bookmark()
    assert bookmark is not None
    # The deterministic label exists BEFORE any model work.
    assert bookmark.label.startswith("Bookmark @ ")
    _join(workers)

    # Exactly ONE new child, and it is the bookmark-label contract.
    new_children = [
        row for row in _children_of(db, parent_id) if row["operation_id"] not in before
    ]
    assert len(new_children) == 1
    receipt = broker.store.receipt(new_children[0]["operation_id"])
    assert receipt is not None and receipt["outcome"] == "succeeded"
    label_requests = [
        request for request in requests
        if request.definition_origin.contract == "holdspeak.meeting-bookmark-label"
    ]
    assert len(label_requests) == 1
    # One engine construction for that one child, from the frozen revision.
    assert len(built) == 1
    assert label_requests[0].deployment_revision == session._intel_plan.primary(
        CAPABILITY_BOOKMARK_LABEL
    )
    # The seam carried BOTH the local context and the earned meeting summary.
    assert len(engine.labels) == 1
    assert "travel budget" in engine.labels[0]["context"]
    assert engine.labels[0]["summary"] == session._state.intel.summary
    # ...and the earned label replaced the deterministic one.
    assert bookmark.label == "Budget decision"


def legacy_a_bookmark_with_no_earned_summary_yet_passes_the_empty_summary(tmp_path, monkeypatch):
    """"...or the empty summary when none exists" — never a fabricated one."""
    _db, _broker, session, engine, _requests = _rig(tmp_path, monkeypatch)
    session.start()
    _add_segment(session, "Opening remarks about the budget", 0.0)
    workers = _capture_threads(monkeypatch)

    bookmark = session.add_bookmark()
    _join(workers)

    assert len(engine.labels) == 1
    assert engine.labels[0]["summary"] == ""
    assert bookmark.label == "Budget decision"


# Phase-B design §45-51: following legacy tests preserve v1 reader law only.
@pytest.mark.parametrize(
    "kwargs,segments,note",
    [
        ({"label": "Owner typed this"}, True, "an explicit label is the owner's"),
        ({"auto_label": False}, True, "auto labeling was switched off"),
        ({}, False, "no transcript context near the bookmark"),
    ],
    ids=["explicit-label", "auto-label-off", "no-context"],
)
def legacy_deterministic_bookmarks_admit_nothing(tmp_path, monkeypatch, kwargs, segments, note):
    """The deterministic cases create NO child and reach no provider."""
    db, _broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    session.start()
    built = _counted_engine(monkeypatch, engine)
    if segments:
        _add_segment(session, "Some discussion worth bookmarking", 0.0)
    workers = _capture_threads(monkeypatch)

    bookmark = session.add_bookmark(**kwargs)
    _join(workers)

    assert bookmark is not None, note
    expected = kwargs.get("label") or "Bookmark @ "
    assert bookmark.label.startswith(expected), note
    assert requests == [], note
    assert built == [], note
    assert engine.labels == [], note
    assert _operations(db, name="inference.invoke") == [], note


def legacy_a_bookmark_without_the_planned_capability_keeps_its_timestamp_label(tmp_path, monkeypatch):
    """A capability absent from the FROZEN plan is a refusal, not a direct call."""
    from dataclasses import replace

    db, _broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    session.start()
    _add_segment(session, "Something worth labeling", 0.0)
    plan = session._intel_plan
    session._intel_plan = replace(
        plan,
        capabilities={
            name: value for name, value in plan.capabilities.items()
            if name != CAPABILITY_BOOKMARK_LABEL
        },
    )
    workers = _capture_threads(monkeypatch)

    bookmark = session.add_bookmark()
    _join(workers)

    assert bookmark.label.startswith("Bookmark @ ")
    assert engine.labels == []
    assert requests == []
    assert _operations(db, name="inference.invoke") == []


def legacy_a_closed_session_cannot_publish_a_late_bookmark_label(tmp_path, monkeypatch):
    """Stop wins: a label that lands after the handoff never reaches the bookmark."""
    _db, _broker, session, engine, _requests = _rig(tmp_path, monkeypatch)
    session.start()
    _add_segment(session, "A late label candidate", 0.0)
    bookmark = session.add_bookmark(label="Bookmark @ 00:00")

    # The stop handoff already fired; the refinement worker is then a no-op.
    session._intel_closed = True
    session._generate_bookmark_label(bookmark, "A late label candidate", "")

    assert bookmark.label == "Bookmark @ 00:00"
    assert engine.labels == []


def legacy_a_discarded_bookmark_projection_leaves_the_deterministic_label(tmp_path, monkeypatch):
    """A child that publishes nothing must not silently blank the label."""
    _db, _broker, session, engine, _requests = _rig(tmp_path, monkeypatch)
    session.start()
    _add_segment(session, "A window that will not publish", 0.0)
    bookmark = session.add_bookmark(label="Bookmark @ 00:07")

    monkeypatch.setattr(
        session, "_admitted_bookmark_label", lambda **kwargs: (object(), None, None)
    )
    session._generate_bookmark_label(bookmark, "A window that will not publish", "")
    assert bookmark.label == "Bookmark @ 00:07"

    # ...and so does a provider failure inside the seam.
    def explode(**kwargs: Any):
        raise RuntimeError("provider is down")

    monkeypatch.setattr(session, "_admitted_bookmark_label", explode)
    session._generate_bookmark_label(bookmark, "A window that will not publish", "")
    assert bookmark.label == "Bookmark @ 00:07"


def legacy_capability_absent_from_the_plan_refuses_with_no_direct_dispatch(tmp_path, monkeypatch):
    from dataclasses import replace

    _db, _broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    session.start()
    plan = session._intel_plan
    reduced = {
        name: value for name, value in plan.capabilities.items() if name != CAPABILITY_AUTO_TITLE
    }
    session._intel_plan = replace(plan, capabilities=reduced)

    with pytest.raises(MeetingIntelRefused) as refusal:
        session._admitted_auto_title("Anything at all")
    assert refusal.value.reason == CAPABILITY_NOT_PLANNED
    assert refusal.value.capability == CAPABILITY_AUTO_TITLE
    assert engine.titles == []
    assert requests == []


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


def legacy_auto_placement_freezes_the_cloud_fallback_as_a_real_second_entry(tmp_path, monkeypatch):
    """The internal local->cloud retarget becomes a NAMED second plan entry."""
    from holdspeak.inference_targets import HUB_DEFAULT_CLOUD_ID, THIS_MACHINE_ID

    db = Database(tmp_path / "auto.db")
    plan = _freeze_auto_plan(db, cloud=True, monkeypatch=monkeypatch)

    entries = plan.revisions(CAPABILITY_LIVE_ANALYSIS)
    assert len(entries) == 2, entries
    rows = _revision_rows(db, entries)
    assert rows[0]["destination_id"] == THIS_MACHINE_ID
    assert rows[1]["destination_id"] == HUB_DEFAULT_CLOUD_ID
    assert rows[1]["engine"] == "openai_compatible"
    assert rows[1]["boundary"] == "external_service"
    assert rows[1]["model"], "the frozen cloud leg must name the model it would use"
    # No credential material is ever frozen — only the slot NAME.
    assert rows[1]["secret_slot"] and "sk-" not in str(rows[1]["secret_slot"])

    placement = plan.placement(CAPABILITY_LIVE_ANALYSIS)
    assert placement["auto_cloud_fallback"] == "frozen"
    assert placement["internal_provider_fallback"] is False
    assert placement["auto_cloud_fallback_boundary"] == "external_service"
    # Both entries are selectable by a child; neither is resolved late.
    for entry in entries:
        assert plan.assert_planned(CAPABILITY_LIVE_ANALYSIS, entry) == entry


def legacy_auto_placement_with_an_unreachable_cloud_leg_keeps_one_entry_and_pins_local(tmp_path, monkeypatch):
    """With no reachable cloud leg the list stays ONE entry and nothing retargets."""
    from holdspeak.deployment_revisions import resolve_deployment_revision
    from holdspeak.inference_targets import build_intel_for_revision

    db = Database(tmp_path / "auto-nocloud.db")
    plan = _freeze_auto_plan(db, cloud=False, monkeypatch=monkeypatch)

    entries = plan.revisions(CAPABILITY_LIVE_ANALYSIS)
    assert len(entries) == 1, entries
    placement = plan.placement(CAPABILITY_LIVE_ANALYSIS)
    assert placement["auto_cloud_fallback"] == "unconfigured"
    assert "Missing API key" in placement["auto_cloud_fallback_reason"]
    assert placement["internal_provider_fallback"] is False

    # ...and the engine built from that ONE entry cannot silently reach the cloud
    # endpoint under a receipt naming this_machine.
    #
    # HS-131-13 strengthened HOW that holds. It used to be a CORRECTION: the branch
    # built the configured default (which could arrive with `provider="auto"` and an
    # already-resolved cloud runtime) and then overwrote `provider`/`_active_provider`
    # afterwards. Now it is a CONSTRUCTION: the branch builds `MeetingIntel` from the
    # frozen revision with `provider="local"` and the revision's own `model_path`, so
    # a cloud-capable adapter for a same-device child never exists at any instant —
    # and the mutable config the old path re-read is not consulted at all.
    from tests.unit.admitted_context import admitted_context

    built_with: list[dict[str, Any]] = []

    class _Built:
        def __init__(self, **kwargs: Any) -> None:
            built_with.append(kwargs)
            self.provider = kwargs.get("provider")
            self.model_path = kwargs.get("model_path")
            self._active_provider = None

    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", _Built)
    # If the frozen path were ignored, the live config would win — so make them
    # DIFFER, then prove the frozen one is what got built.
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path",
        lambda: "/mutated-after-freeze.gguf",
    )

    # HS-131-10: the factory is context-requiring, so mint the runner's context
    # for exactly this revision (a missing one refuses `adapter_context_required`).
    frozen = resolve_deployment_revision(db, entries[0])
    built = build_intel_for_revision(
        frozen,
        context=admitted_context(revision=frozen),
    )
    assert built.provider == "local"
    assert built._active_provider is None
    assert built.model_path == frozen.model_path != "/mutated-after-freeze.gguf"
    assert built_with == [{
        "provider": "local",
        "model_path": frozen.model_path,
        "n_ctx": frozen.context_ceiling or 4096,
    }]


def legacy_a_failed_local_entry_admits_a_second_child_naming_the_cloud_revision(tmp_path, monkeypatch):
    """A provider failure on entry 1 runs entry 2 as its OWN admitted child."""
    from holdspeak.inference_targets import HUB_DEFAULT_CLOUD_ID

    db, broker, session, engine, requests = _rig(tmp_path, monkeypatch)
    session.start()
    parent_id = session.intel_session_operation_id()

    # The live parent stays exactly as admitted; only the plan is re-frozen (by
    # production code) so the `auto` path's two entries are in play.
    plan = _freeze_auto_plan(db, cloud=True, monkeypatch=monkeypatch)
    from dataclasses import replace

    session._intel_plan = replace(plan, meeting_id=session._state.id)
    entries = session._intel_plan.revisions(CAPABILITY_LIVE_ANALYSIS)
    assert len(entries) == 2

    # Entry 1 (this_machine) fails at the provider; entry 2 is a distinct cloud
    # engine built from the cloud revision.
    cloud = FakeIntel()
    _split_legs(monkeypatch, local=engine, cloud=cloud)

    def explode(transcript: str, *, stream: bool = False):
        raise RuntimeError("local engine is out of memory")

    monkeypatch.setattr(engine, "analyze", explode)

    _add_segment(session, "A window that fails locally", 0.0)
    session._run_intel_analysis()

    # TWO children, each naming the entry it really used, at distinct attempts.
    assert [request.deployment_revision for request in requests] == [entries[0], entries[1]]
    assert [request.attempt_ordinal for request in requests] == [1, 2]
    assert len({request.invocation_id for request in requests}) == 2
    children = [
        row for row in _operations(db, name="inference.invoke")
        if row["parent_operation_id"] == parent_id
    ]
    assert len(children) == 2
    assert [broker.store.receipt(row["operation_id"])["outcome"] for row in children] == [
        "failed",
        "succeeded",
    ]
    # The cloud engine is the one that actually ran the second attempt.
    assert cloud.analyzed and "fails locally" in cloud.analyzed[0]
    with db._connection() as conn:
        row = dict(conn.execute(
            "SELECT * FROM deployment_revisions WHERE id=?", (entries[1],)
        ).fetchone())
    assert row["destination_id"] == HUB_DEFAULT_CLOUD_ID
    # The earned result published, and it published under the cloud entry.
    assert session._state.intel is not None
    assert session._state.intel_status == "ready"


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


def legacy_a_returned_error_result_fails_its_child_and_admits_the_cloud_entry(tmp_path, monkeypatch):
    """A provider failure the engine RETURNS is a failure, not a `succeeded` child.

    An ``IntelResult`` carrying ``.error`` is the domain's established way to say
    "the provider failed" (``intel_analysis`` defers on it, the queue retries on
    it). It must therefore close its child ``failed`` — sanitized — and let the
    frozen cloud entry take its own admitted attempt.
    """
    db, broker, session, engine, requests, entries = _auto_two_entry_session(tmp_path, monkeypatch)
    parent_id = session.intel_session_operation_id()

    cloud = FakeIntel()
    _split_legs(monkeypatch, local=engine, cloud=cloud)
    monkeypatch.setattr(engine, "analyze", _error_window(f"local engine said {SENTINEL}"))

    _add_segment(session, "A window whose local engine returns an error", 0.0)
    session._run_intel_analysis()

    # Two children, each naming the entry it really used, at distinct attempts.
    assert [request.deployment_revision for request in requests] == [entries[0], entries[1]]
    assert [request.attempt_ordinal for request in requests] == [1, 2]
    children = [
        row for row in _operations(db, name="inference.invoke")
        if row["parent_operation_id"] == parent_id
    ]
    receipts = [broker.store.receipt(row["operation_id"]) for row in children]
    assert [receipt["outcome"] for receipt in receipts] == ["failed", "succeeded"]
    # The cloud engine ran the second attempt and ITS result is the domain result.
    assert cloud.analyzed and "returns an error" in cloud.analyzed[0]
    assert session._state.intel is not None
    assert session._state.intel.summary == cloud.result.summary
    assert session._state.intel_status == "ready"
    # No provider text reached the journal rows.
    with db._connection() as conn:
        rows = [dict(row) for row in conn.execute("SELECT * FROM kernel_receipts")]
        rows += [dict(row) for row in conn.execute("SELECT * FROM kernel_operations")]
        rows += [dict(row) for row in conn.execute("SELECT * FROM kernel_journal")]
    for row in rows:
        assert SENTINEL not in json.dumps(row, default=str)


def legacy_a_one_entry_plan_fails_its_child_sanitized_and_still_returns_the_error_result(tmp_path, monkeypatch):
    """One frozen entry: the child fails by NAME, the caller still reads `.error`."""
    from holdspeak.meeting_session.intel_admission import CONTRACT_LIVE_ANALYSIS

    db, _broker, session, engine, _requests = _rig(tmp_path, monkeypatch)
    session.start()
    assert len(session._intel_plan.revisions(CAPABILITY_LIVE_ANALYSIS)) == 1
    monkeypatch.setattr(engine, "analyze", _error_window(f"provider said {SENTINEL}"))
    _add_segment(session, "One entry, one error result", 0.0)

    session._current_analysis_id = "a1"
    outcome, projection, result = session._admitted_live_window(
        session.get_formatted_transcript(), final=False, analysis_id="a1"
    )
    assert outcome.outcome == "failed"
    # Sanitized: contract + classification, never the provider's own words.
    assert outcome.error == f"{CONTRACT_LIVE_ANALYSIS}:provider_error_result"
    assert SENTINEL not in str(outcome.error)
    assert projection is None
    # ...and the pre-existing domain vocabulary is intact: the returned result
    # still carries the provider's error for the deferral/queue paths to read.
    assert result is not None and SENTINEL in str(result.error)


def legacy_provider_failure_closes_live_cadence_when_deferral_is_disabled(
    tmp_path, monkeypatch
):
    """A terminal error is not a live provider and cannot schedule another window."""
    _db, _broker, session, engine, _requests = _rig(tmp_path, monkeypatch)
    session.intel_deferred_enabled = False
    session.start()
    monkeypatch.setattr(engine, "analyze", _error_window("provider unavailable"))
    _add_segment(session, "A window that reaches a terminal provider error", 0.0)

    session._run_intel_analysis()

    assert session._intel_live is False
    assert session._state.intel_status == "error"
    assert "provider unavailable" in str(session._state.intel_status_detail)


def legacy_error_results_on_every_frozen_entry_fail_both_children_and_defer(tmp_path, monkeypatch):
    """Exhausting the entries keeps the caller's existing error vocabulary."""
    db, broker, session, engine, requests, _entries = _auto_two_entry_session(tmp_path, monkeypatch)
    parent_id = session.intel_session_operation_id()

    cloud = FakeIntel()
    _split_legs(monkeypatch, local=engine, cloud=cloud)
    monkeypatch.setattr(engine, "analyze", _error_window("local engine is out of memory"))
    monkeypatch.setattr(cloud, "analyze", _error_window("cloud endpoint returned 503"))

    _add_segment(session, "A window that fails at both entries", 0.0)
    session._run_intel_analysis()

    children = [
        row for row in _operations(db, name="inference.invoke")
        if row["parent_operation_id"] == parent_id
    ]
    assert len(children) == 2
    assert [broker.store.receipt(row["operation_id"])["outcome"] for row in children] == [
        "failed",
        "failed",
    ]
    assert len(requests) == 2
    # ...and the live session takes its PRE-EXISTING deferral path, with the
    # provider's own reason, exactly as a returned error result always did.
    assert session._state.intel is None
    assert session._state.intel_status == "queued"
    assert "cloud endpoint returned 503" in str(session._state.intel_status_detail)
    assert session._state.intel_completed_at is None


# ------------------------------------------------------------ journal hygiene


def legacy_no_transcript_material_reaches_the_kernel_journal(tmp_path, monkeypatch):
    db, broker, session, engine, _requests = _rig(tmp_path, monkeypatch)
    session.start()
    _add_segment(session, f"The revenue number is {SENTINEL}", 0.0)
    session._state.bookmarks.append(Bookmark(timestamp=1.0, label="Bookmark 1"))

    # (1) success + bookmark label, (2) auto title
    session._run_intel_analysis(final=True)
    session._admitted_auto_title(f"Closing note: {SENTINEL}")

    # (3) a provider FAILURE whose exception text quotes the transcript
    def explode(transcript: str, *, stream: bool = False):
        raise RuntimeError(f"endpoint echoed: {transcript}")

    monkeypatch.setattr(engine, "analyze", explode)
    _add_segment(session, f"More about {SENTINEL}", 10.0)
    session._run_intel_analysis()
    assert SENTINEL not in str(session._state.intel_status_detail)

    # (4) a REFUSED window under a cancelled parent. The failure above turned the
    # explicit liveness state off (the deferral path); raise it again so the
    # window is refused at ADMISSION rather than skipped before it.
    session._intel_live = True
    broker.parent_run_controller.cancel(session._intel_parent.context, OWNER)
    _add_segment(session, f"Even more {SENTINEL}", 20.0)
    session._run_intel_analysis()

    # The provider really received the material...
    assert any(SENTINEL in text for text in engine.analyzed)
    assert any(SENTINEL in text for text in engine.titles)

    # ...and no kernel operation or receipt row carries it.
    with db._connection() as conn:
        operations = [dict(row) for row in conn.execute("SELECT * FROM kernel_operations")]
        receipts = [dict(row) for row in conn.execute("SELECT * FROM kernel_receipts")]
        events = [dict(row) for row in conn.execute("SELECT * FROM kernel_journal")]
    # Success, failure, and cancellation receipts are all represented.
    outcomes = {str(row["outcome"]) for row in receipts}
    assert {"succeeded", "failed"} <= outcomes, outcomes
    assert operations and receipts
    for row in operations + receipts + events:
        assert SENTINEL not in json.dumps(row, default=str)


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
        ((), 17_286, 21_382),
        (("remote-a", "remote-b"), 34_570, 38_666),
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
        {"id": "meeting-preload", "allocation": 0, "member_keys": ["preload"]},
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
