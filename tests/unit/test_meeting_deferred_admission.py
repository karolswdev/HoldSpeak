"""HS-131-08 Part B: the stop handoff and the admitted deferred queue job.

Sol Amendment 2 is the spine of this file: ``stop()`` CANCELS the live
``meeting.session`` parent and then durably enqueues the work it displaced —
final analysis, bookmark labels, auto-title, routed plugins — before it returns,
and the meeting never reports readiness while that job is outstanding.

Each claimed queue job then admits ONE short-lived
``meeting.deferred-intel-job`` parent under the narrow queue-worker service
principal, over a freshly frozen plan; the base analysis and every executed
routed plugin are trusted ``inference.invoke@1`` children of it, and every
durable plugin/artifact write is gated on the winning child receipt.

Only the provider engine and the plugin registry are faked; the plan, the
parents, the runner, the projections, the materializer, and the receipts are all
production code.
"""

from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import pytest

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.intel import ActionItem, IntelResult
from holdspeak.kernel.runtime import _configure
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.meeting_session.deferred_admission import (
    CONTRACT_DEFERRED_ANALYSIS,
    CONTRACT_PLUGIN_PREFIX,
    JOB_DEADLINE_SECONDS,
    PARENT_KIND,
    QUEUE_SERVICE_IDENTITY,
    job_child_budget,
)
from holdspeak.meeting_session.intel_plan import (
    CAPABILITY_DEFERRED_ANALYSIS,
    MeetingIntelRefused,
    SESSION_CLOSED,
)
from holdspeak.meeting_session.models import Bookmark
from holdspeak.plugins.host import PluginRunResult, build_idempotency_key
from holdspeak.principals import Principal, PrincipalKind

pytestmark = pytest.mark.timeout(90, method="signal")

OWNER = Principal(PrincipalKind.OWNER, "meeting-owner")
SENTINEL = "PINEAPPLEQUARTERLYSECRET"


# --------------------------------------------------------------------- fakes


class FakeIntel:
    """The one faked seam: the engine the admitted deployment revision builds."""

    active_provider = "test-provider"
    active_model = "test-model"

    def __init__(self) -> None:
        self.analyzed: list[str] = []
        self.titles: list[str] = []
        self.labels: list[dict[str, str]] = []
        self.completions: list[dict[str, Any]] = []
        self.stream_gate: threading.Event | None = None
        self.entered = threading.Event()
        self.error: str | None = None
        self.result = IntelResult(
            topics=["Budget"],
            action_items=[ActionItem(task="Send the deck", owner="Me")],
            summary="The team reviewed the budget.",
            raw_response="{}",
        )

    def _result(self) -> IntelResult:
        if self.error is None:
            return self.result
        return IntelResult(topics=[], action_items=[], summary="", raw_response="", error=self.error)

    def analyze(self, transcript: str, *, stream: bool = False) -> Any:
        self.analyzed.append(transcript)
        if not stream:
            return self._result()

        def generate() -> Iterator[Any]:
            self.entered.set()
            if self.stream_gate is not None:
                # A window that never comes back on its own: stop() must cancel it.
                self.stream_gate.wait(30.0)
            yield '{"topics":'
            yield self._result()

        return generate()

    def generate_bookmark_label_with_context(self, *, local_context: str, meeting_summary: str) -> str:
        self.labels.append({"context": local_context, "summary": meeting_summary})
        return "Budget decision"

    def generate_title(self, transcript: str) -> str:
        self.titles.append(transcript)
        return "Quarterly budget review"

    def _chat_completion_text(self, messages: Any, *, temperature: float, max_tokens: int) -> str:
        """The seam a routed plugin's admitted handle dispatches on (HS-131-14)."""
        self.completions.append({"messages": messages, "max_tokens": max_tokens})
        return "{}"


class FakeHost:
    """The plugin registry seam: declares capabilities and executes the chain."""

    def __init__(self, plugins: tuple[str, ...]) -> None:
        self._plugins = list(plugins)
        self.executed: list[str] = []
        self.dispatches: list[Any] = []
        self.on_execute: Any = None
        # The engines the admitted path issued a handle over, in order.
        self.bound_engines: list[Any] = []
        # Every handle this host issued, and whether it was released on exit.
        self.issued: list[Any] = []

    def list_plugins(self) -> list[str]:
        return list(self._plugins)

    @contextmanager
    def issued_dispatch(self, engine: Any, cancellation: Any = None) -> Any:
        """The admitted seam: ONE handle per plugin child, released on exit.

        HS-131-14 — the host holds no engine and no handle between runs; the
        handle is issued over the admitted child's engine + cancellation signal
        and travels into exactly the invocation it authorizes.
        """
        from holdspeak.plugins.intelligence import _issue_plugin_dispatch

        self.bound_engines.append(engine)
        handle = _issue_plugin_dispatch(engine=engine, cancellation=cancellation)
        self.issued.append(handle)
        try:
            yield handle
        finally:
            handle.release()

    def execute_chain(
        self,
        chain: list[str],
        *,
        context: dict[str, Any],
        meeting_id: str,
        window_id: str,
        transcript_hash: str,
        timeout_seconds: float | None = None,
        defer_heavy: bool = True,
        dispatch: Any = None,
    ) -> list[PluginRunResult]:
        self.dispatches.append(dispatch)
        results: list[PluginRunResult] = []
        for plugin_id in chain:
            self.executed.append(plugin_id)
            if self.on_execute is not None:
                self.on_execute(plugin_id)
            results.append(PluginRunResult(
                plugin_id=plugin_id,
                plugin_version="1.0.0",
                status="success",
                idempotency_key=build_idempotency_key(
                    meeting_id=meeting_id, window_id=window_id,
                    plugin_id=plugin_id, transcript_hash=transcript_hash,
                ),
                duration_ms=3.0,
                output={"summary": f"{plugin_id} said something", "confidence_hint": 0.9},
            ))
        return results


class _Cfg:
    class meeting:  # noqa: N801 - config shape
        intent_router_enabled = True
        mir_profile = "balanced"


class _Route:
    def __init__(self, chain: tuple[str, ...]) -> None:
        self._chain = list(chain)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": "balanced",
            "threshold": 0.5,
            "active_intents": ["architecture"],
            "intent_scores": {"architecture": 0.9},
            "plugin_chain": list(self._chain),
        }


# ----------------------------------------------------------------------- rigs


def _observe(broker: Any, monkeypatch) -> list[Any]:
    requests: list[Any] = []
    real_invoke = broker.inference_runner.invoke

    def observed(request, *args, **kwargs):
        requests.append(request)
        return real_invoke(request, *args, **kwargs)

    monkeypatch.setattr(broker.inference_runner, "invoke", observed)
    return requests


def _session_rig(tmp_path: Path, monkeypatch, *, engine: Any = None):
    """A real database + broker + MeetingSession with a fake provider."""
    db = Database(tmp_path / "meeting.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *a, **k: db)
    broker = _configure(db)
    engine = engine if engine is not None else FakeIntel()

    # HS-131-13: the pinned `this_machine` branch builds `MeetingIntel` from the
    # FROZEN revision, so the double goes on the engine class the real path ends at.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", _FakeRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", _FakeJournal)
    # HS-131-17: the session imports no engine class and runs no provider
    # preflight. Live readiness is read off the FROZEN placement, so the honest
    # way to make the `this_machine` leg reachable is to give it a model file.
    model = tmp_path / "local-meeting-intel.gguf"
    model.write_bytes(b"gguf")
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path", lambda: str(model)
    )
    requests = _observe(broker, monkeypatch)

    from holdspeak.meeting_session import MeetingSession

    class _Transcriber:
        model_name = "test-model"

        def transcribe(self, *args: Any, **kwargs: Any) -> str:
            return ""

    session = MeetingSession(
        _Transcriber(),  # type: ignore[arg-type]
        intel_enabled=True,
        intel_deferred_enabled=True,
        principal=OWNER,
    )
    return db, broker, session, engine, requests


def _queue_rig(tmp_path: Path, monkeypatch, *, plugins: tuple[str, ...] = (), chain: tuple[str, ...] = ()):
    """A real database + broker + a queued meeting, with the queue's seams faked."""
    db = Database(tmp_path / "queue.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *a, **k: db)
    broker = _configure(db)
    engine = FakeIntel()
    host = FakeHost(plugins)

    # HS-131-13: same reason as `_session_rig` — the frozen-revision local branch
    # constructs the engine class directly and reads no configured default.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls: _Cfg))
    monkeypatch.setattr(
        "holdspeak.intel_queue.get_intel_runtime_status", lambda *a, **k: (True, "ready")
    )
    monkeypatch.setattr("holdspeak.intel_queue._routed_plugin_host", lambda enabled: host if enabled else None)
    monkeypatch.setattr(
        "holdspeak.plugins.router.preview_route_from_transcript",
        lambda **kwargs: _Route(chain),
    )
    requests = _observe(broker, monkeypatch)
    return db, broker, engine, host, requests


class _FakeRecorder:
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


class _FakeJournal:
    def __init__(self, meeting_id: str) -> None:
        self.meeting_id = meeting_id

    def append(self, *args: Any, **kwargs: Any) -> None:
        return None

    def finalize(self) -> None:
        return None

    def mark_recoverable(self, reason: str) -> None:
        return None


def _queued_meeting(
    db: Database,
    meeting_id: str,
    *,
    text: str = "we shipped the fix",
    title: str = "Deferred meeting",
    bookmarks: tuple[float, ...] = (),
    displaced_work: tuple[str, ...] = (),
) -> MeetingState:
    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 10, 9, 0, 0),
        ended_at=datetime(2026, 8, 10, 9, 30, 0),
        title=title,
        tags=["architecture"],
        segments=[TranscriptSegment(text=text, speaker="Me", start_time=0.0, end_time=5.0)],
        bookmarks=[Bookmark(timestamp=stamp, label="Bookmark") for stamp in bookmarks],
    )
    db.meetings.save_meeting(state)
    db.intel.enqueue_intel_job(
        meeting_id,
        transcript_hash=state.transcript_hash(),
        reason="stop handoff",
        displaced_work=displaced_work,
    )
    return state


def _parents(db: Database, kind: str = "") -> list[dict[str, Any]]:
    query = "SELECT * FROM kernel_parent_runs"
    parameters: tuple[Any, ...] = ()
    if kind:
        query += " WHERE kind=?"
        parameters = (kind,)
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(query + " ORDER BY created_at", parameters)]


def _children(db: Database, parent_operation_id: str) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM kernel_operations WHERE parent_operation_id=? AND name='inference.invoke' ORDER BY created_at",
            (parent_operation_id,),
        )]


def _rows(db: Database, table: str) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(f"SELECT * FROM {table}")]


def _add_segment(session: Any, text: str, start: float) -> None:
    session._state.segments.append(
        TranscriptSegment(text=text, speaker="Me", start_time=start, end_time=start + 5.0)
    )


# ------------------------------------------------- Amendment 2: the stop handoff


def test_stop_cancels_the_live_parent_and_durably_enqueues_the_displaced_work(tmp_path, monkeypatch):
    engine = FakeIntel()
    engine.stream_gate = threading.Event()
    db, broker, session, engine, _requests = _session_rig(tmp_path, monkeypatch, engine=engine)
    state = session.start()
    parent_id = session.intel_session_operation_id()
    _add_segment(session, f"Live window about {SENTINEL}", 0.0)
    session._state.bookmarks.append(Bookmark(timestamp=2.0, label="Bookmark 1"))

    # A live window is mid-stream (blocked inside the provider) when stop lands.
    window = threading.Thread(target=session._run_intel_analysis, daemon=True)
    window.start()
    assert engine.entered.wait(10.0), "the live window never reached the provider"

    final = session.stop()
    window.join(15.0)

    # 1. The live parent is CANCELLED, not succeeded, and closed exactly once.
    parent = [row for row in _parents(db, "meeting.session") if row["operation_id"] == parent_id][0]
    assert parent["state"] == "CANCELLED", parent["state"]
    assert broker.store.receipt(parent_id)["outcome"] == "cancelled"

    # 2. Provider cancellation was attempted and the child never published.
    children = _children(db, parent_id)
    assert len(children) == 1
    outcome = broker.store.receipt(children[0]["operation_id"])["outcome"]
    assert outcome in {"cancelled", "indeterminate"}, outcome
    stage = broker.projection_stager.get(children[0]["native_id"])
    assert stage is None or stage.state != "PUBLISHED"
    assert session._state.intel is None

    # 3. The displaced final work is durably enqueued BEFORE stop() returned.
    job = db.intel.get_intel_job(state.id)
    assert job is not None
    assert job.status == "queued"
    assert job.transcript_hash == final.transcript_hash()
    for displaced in ("final analysis", "bookmark labels", "auto title"):
        assert displaced in str(job.intel_status_detail or ""), job.intel_status_detail

    # 4. Nothing reports readiness while the deferred job is outstanding, and no
    #    post-close provider dispatch happened inside stop().
    assert final.intel_status == "queued"
    assert final.intel_completed_at is None
    persisted = db.meetings.get_meeting(state.id)
    assert persisted is not None
    assert persisted.intel_status == "queued"
    assert persisted.intel_completed_at is None
    assert engine.titles == [] and engine.labels == []
    engine.stream_gate.set()


def test_stop_with_an_unacknowledging_provider_leaves_the_child_indeterminate(tmp_path, monkeypatch):
    """An adapter that never acknowledges cancellation is indeterminate, not guessed."""
    db, broker, session, engine, _requests = _session_rig(tmp_path, monkeypatch)
    monkeypatch.setattr(broker.inference_runner, "_cancel_timeout", 0.2, raising=False)

    class _DeafAdapter:
        connector_id = "inference-provider"

        def __init__(self) -> None:
            self.result = None
            self.dispatching = threading.Event()

        def dispatch(self, engine_: Any, payload: Any, cancellation: threading.Event) -> Any:
            self.dispatching.set()
            cancellation.wait(5.0)
            return {"contract": "deaf"}

        def cancel(self) -> str:
            # Never comes back inside the cancellation timeout: disposition unknown.
            threading.Event().wait(5.0)
            return "cancelled"

    deaf = _DeafAdapter()
    from holdspeak.meeting_session import intel_child

    monkeypatch.setattr(intel_child, "MeetingAdapter", lambda *a, **k: deaf)

    session.start()
    parent_id = session.intel_session_operation_id()
    _add_segment(session, "A window with a deaf provider", 0.0)
    window = threading.Thread(target=session._run_intel_analysis, daemon=True)
    window.start()
    assert deaf.dispatching.wait(10.0)

    session.stop()
    window.join(20.0)

    children = _children(db, parent_id)
    assert len(children) == 1
    assert broker.store.receipt(children[0]["operation_id"])["outcome"] == "indeterminate"
    assert session._state.intel is None
    # The meeting is still handed off honestly, never left silently empty.
    assert db.intel.get_intel_job(session._state.id) is not None


def test_a_closed_live_session_is_never_revived(tmp_path, monkeypatch):
    _db, _broker, session, engine, requests = _session_rig(tmp_path, monkeypatch)
    session.start()
    _add_segment(session, "Something worth summarizing", 0.0)
    session.stop()
    before = len(requests)

    with pytest.raises(MeetingIntelRefused) as refusal:
        session._admitted_auto_title("Anything at all")
    assert refusal.value.reason == SESSION_CLOSED
    assert engine.titles == []
    assert len(requests) == before


# --------------------------------------------- the admitted deferred queue job


def test_claim_admits_one_job_parent_with_base_and_plugin_children(tmp_path, monkeypatch):
    db, broker, engine, host, requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor", "risk_heatmap", "unrouted_plugin"),
        chain=("requirements_extractor", "risk_heatmap"),
    )
    state = _queued_meeting(db, "m-deferred")

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    # ONE job parent, under the narrow queue-worker SERVICE principal.
    parents = _parents(db, PARENT_KIND)
    assert len(parents) == 1
    parent = parents[0]
    assert parent["definition_ref"] == f"meeting:{state.id}:deferred:1"
    assert parent["state"] == "SUCCEEDED"
    with db._connection() as conn:
        operation = dict(conn.execute(
            "SELECT * FROM kernel_operations WHERE operation_id=?", (parent["operation_id"],)
        ).fetchone())
    assert operation["principal_kind"] == "service"
    assert operation["principal_identity"] == QUEUE_SERVICE_IDENTITY
    assert operation["name"] == PARENT_KIND

    # A FRESH plan: its revision is the plan hash, its envelope is finite, and its
    # budget is 1 base + one per planned plugin + the declared retry allowance.
    snapshot = json.loads(parent["input_json"])
    assert snapshot["plan_sha256"] == parent["definition_revision"]
    assert snapshot["queue_attempt"] == 1
    assert set(snapshot["capabilities"]) == {
        CAPABILITY_DEFERRED_ANALYSIS,
        "plugin:requirements_extractor",
        "plugin:risk_heatmap",
        "plugin:unrouted_plugin",
    }
    assert parent["child_budget"] == job_child_budget(3) == 6
    assert parent["deadline_at"] - snapshot["deadline_at"] == pytest.approx(0.0, abs=1)
    assert JOB_DEADLINE_SECONDS == 30 * 60

    # Base analysis + EACH executed plugin = one trusted child.
    children = _children(db, parent["operation_id"])
    assert len(children) == 3
    assert [request.definition_origin.contract for request in requests] == [
        CONTRACT_DEFERRED_ANALYSIS,
        f"{CONTRACT_PLUGIN_PREFIX}requirements_extractor",
        f"{CONTRACT_PLUGIN_PREFIX}risk_heatmap",
    ]
    assert all(broker.store.receipt(row["operation_id"])["outcome"] == "succeeded" for row in children)
    # Route order was preserved, and the unrouted planned plugin ran nothing.
    assert host.executed == ["requirements_extractor", "risk_heatmap"]

    # The domain outcome is unchanged: base analysis, runs, artifacts, Ready.
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed is not None
    assert refreshed.intel is not None
    assert refreshed.intel.summary == "The team reviewed the budget."
    assert refreshed.intel_status == "ready"
    assert refreshed.intel_completed_at is not None
    assert {row["plugin_id"] for row in _rows(db, "plugin_runs")} == {
        "requirements_extractor", "risk_heatmap"
    }
    assert len(db.plugins.list_artifacts(state.id)) == 2
    assert db.intel.get_intel_job(state.id) is None


def test_a_deduped_plugin_admits_no_child(tmp_path, monkeypatch):
    db, _broker, _engine, host, requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor", "risk_heatmap"),
        chain=("requirements_extractor", "risk_heatmap"),
    )
    state = _queued_meeting(db, "m-dedup")
    window_id = f"{state.id}:full"
    transcript_hash = __import__("hashlib").sha256(
        f"Me: {state.segments[0].text}".encode()
    ).hexdigest()
    db.plugins.record_plugin_run(
        meeting_id=state.id, window_id=window_id, plugin_id="risk_heatmap",
        plugin_version="1.0.0", status="success",
        idempotency_key=build_idempotency_key(
            meeting_id=state.id, window_id=window_id,
            plugin_id="risk_heatmap", transcript_hash=transcript_hash,
        ),
        duration_ms=1.0, output={"summary": "already done"},
    )

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    parent = _parents(db, PARENT_KIND)[0]
    # Base analysis + the ONE remaining plugin. The deduped plugin issues no child.
    assert len(_children(db, parent["operation_id"])) == 2
    assert host.executed == ["requirements_extractor"]
    assert [request.definition_origin.contract for request in requests] == [
        CONTRACT_DEFERRED_ANALYSIS,
        f"{CONTRACT_PLUGIN_PREFIX}requirements_extractor",
    ]
    assert db.meetings.get_meeting(state.id).intel_status == "ready"


def test_each_queue_retry_admits_a_new_job_parent(tmp_path, monkeypatch):
    db, broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr("holdspeak.intel_queue._routed_plugin_host", lambda enabled: None)
    monkeypatch.setattr(_Cfg.meeting, "intent_router_enabled", False, raising=False)
    state = _queued_meeting(db, "m-retry")

    from holdspeak.intel_queue import process_next_intel_job

    engine.error = "the provider refused"
    assert process_next_intel_job() is True
    first = _parents(db, PARENT_KIND)
    assert len(first) == 1
    assert first[0]["state"] == "FAILED"
    job = db.intel.get_intel_job(state.id)
    assert job is not None and job.status == "queued" and job.attempts == 1

    engine.error = None
    assert process_next_intel_job(include_scheduled=True) is True

    parents = _parents(db, PARENT_KIND)
    assert len(parents) == 2, "a retry must be a NEW job parent, never a reopened epoch"
    assert parents[0]["operation_id"] != parents[1]["operation_id"]
    assert parents[0]["execution_epoch"] == parents[1]["execution_epoch"] == 1
    assert parents[0]["state"] == "FAILED" and parents[1]["state"] == "SUCCEEDED"
    assert json.loads(parents[1]["input_json"])["queue_attempt"] == 2
    assert db.meetings.get_meeting(state.id).intel_status == "ready"


def test_a_returned_error_result_fails_the_base_child_and_keeps_the_queue_vocabulary(tmp_path, monkeypatch):
    """A RETURNED provider error closes its child `failed`, sanitized, and retries.

    The queue's failure vocabulary is unchanged: it still reads the returned
    result's ``.error`` for the owner-facing reason, and the job still takes its
    existing retry path. What changes is the receipt — an attempt the domain
    calls failed can no longer be journaled as `succeeded`.
    """
    db, broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr("holdspeak.intel_queue._routed_plugin_host", lambda enabled: None)
    monkeypatch.setattr(_Cfg.meeting, "intent_router_enabled", False, raising=False)
    state = _queued_meeting(db, "m-error-result")

    from holdspeak.intel_queue import process_next_intel_job

    engine.error = f"the endpoint echoed {SENTINEL}"
    assert process_next_intel_job() is True

    parent = _parents(db, PARENT_KIND)[0]
    assert parent["state"] == "FAILED"
    children = _children(db, parent["operation_id"])
    assert len(children) == 1, "one frozen entry means exactly one attempt"
    receipt = broker.store.receipt(children[0]["operation_id"])
    assert receipt["outcome"] == "failed"
    assert [request.definition_origin.contract for request in requests] == [
        CONTRACT_DEFERRED_ANALYSIS
    ]

    # The queue's own path is untouched: retried, with the provider's reason.
    job = db.intel.get_intel_job(state.id)
    assert job is not None and job.status == "queued" and job.attempts == 1
    assert SENTINEL in str(job.last_error)
    meeting = db.meetings.get_meeting(state.id)
    assert meeting.intel is None and meeting.intel_status != "ready"

    # ...and the sanitized receipt carries no provider text at all.
    for table in ("kernel_receipts", "kernel_operations", "kernel_journal"):
        for row in _rows(db, table):
            assert SENTINEL not in json.dumps(row, default=str)


def test_cancelling_the_job_parent_mid_plugin_writes_no_run_and_no_artifact(tmp_path, monkeypatch):
    db, broker, _engine, host, _requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor",), chain=("requirements_extractor",),
    )
    state = _queued_meeting(db, "m-cancel")

    jobs: list[Any] = []
    from holdspeak.meeting_session.deferred_admission import DeferredIntelJob

    real_admit = DeferredIntelJob.admit

    def capture(cls_db, **kwargs):
        job = real_admit(cls_db, **kwargs)
        jobs.append(job)
        return job

    monkeypatch.setattr(DeferredIntelJob, "admit", classmethod(lambda cls, d, **k: capture(d, **k)))

    def cancel_mid_plugin(plugin_id: str) -> None:
        jobs[0].cancel()

    host.on_execute = cancel_mid_plugin

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    # The provider really ran, and nothing it produced crossed the boundary.
    assert host.executed == ["requirements_extractor"]
    assert _rows(db, "plugin_runs") == []
    assert db.plugins.list_artifacts(state.id) == []
    for stage in _rows(db, "kernel_projection_stages"):
        if str(stage["kind"]) == "meeting-plugin-result":
            assert str(stage["state"]) == "DISCARDED", dict(stage)
    # The job is honestly unresolved, never Ready.
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed.intel_status != "ready"
    assert refreshed.intel_completed_at is None


def test_an_executed_plugin_runs_on_the_engine_its_frozen_revision_built(tmp_path, monkeypatch):
    """D2: the plugin's provider work uses the ADMITTED engine, not its own."""
    db, _broker, engine, host, requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor",), chain=("requirements_extractor",),
    )
    state = _queued_meeting(db, "m-engine")

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    # The engine bound for the plugin execution IS the engine the child's frozen
    # deployment revision built (identity, not equality) — the same object the
    # admitted base analysis ran on.
    assert host.bound_engines and all(bound is engine for bound in host.bound_engines)
    assert len(host.bound_engines) == 1
    assert host.executed == ["requirements_extractor"]
    plugin_requests = [
        request for request in requests
        if request.definition_origin.contract.startswith(CONTRACT_PLUGIN_PREFIX)
    ]
    assert len(plugin_requests) == 1
    # The revision the child NAMES is the revision whose engine ran the plugin:
    # the plan's frozen entry for that plugin capability, and the same revision
    # the base-analysis child used (one placement, one engine).
    parent = _parents(db, PARENT_KIND)[0]
    frozen = json.loads(parent["input_json"])["capabilities"]
    assert plugin_requests[0].deployment_revision == frozen["plugin:requirements_extractor"][0]
    assert plugin_requests[0].deployment_revision == requests[0].deployment_revision
    assert {row["plugin_id"] for row in _rows(db, "plugin_runs")} == {"requirements_extractor"}


def test_an_llm_plugin_with_no_admitted_handle_is_refused_by_name(tmp_path, monkeypatch):
    """An llm plugin never self-builds: with no handle it refuses, by name.

    HS-131-08 phrased this as "the engine cannot be injected"; HS-131-14 makes the
    seam per-invocation, so the honest statement is simpler — an `llm` plugin that
    was handed no admitted handle does no model work and says which rule refused.
    """
    from holdspeak.plugins.host import (
        PLUGIN_LLM_ENGINE_NOT_INJECTABLE,
        PluginEngineNotInjectable,
        PluginHost,
    )
    from holdspeak.plugins.intelligence import PLUGIN_DISPATCH_REQUIRED

    class _SelfBuilding:
        id = "self_builder"
        version = "1.0.0"
        required_capabilities = ["llm"]

        def run(self, context: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
            raise AssertionError("an unadmitted llm plugin must refuse before run()")

    host = PluginHost(enabled_capabilities={"llm"})
    host.register(_SelfBuilding())
    result = host.execute(
        "self_builder", context={"transcript": "t"}, meeting_id="m",
        window_id="m:full", transcript_hash="h",
    )
    assert result.status == "error"
    assert PLUGIN_DISPATCH_REQUIRED in str(result.error)
    # The host-seam refusal keeps its own name: a HOST that cannot be handed the
    # admitted child's engine at all (no `issued_dispatch`) is a different fault.
    assert PluginEngineNotInjectable("x").reason == PLUGIN_LLM_ENGINE_NOT_INJECTABLE


def test_the_plugin_provider_call_runs_inside_the_admitted_child_dispatch(tmp_path, monkeypatch):
    """D2: cancelling the job parent mid-plugin cannot publish the plugin's work."""
    db, broker, engine, host, _requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor",), chain=("requirements_extractor",),
    )
    state = _queued_meeting(db, "m-inside")

    jobs: list[Any] = []
    from holdspeak.meeting_session.deferred_admission import DeferredIntelJob

    real_admit = DeferredIntelJob.admit
    monkeypatch.setattr(
        DeferredIntelJob, "admit",
        classmethod(lambda cls, d, **k: jobs.append(real_admit(d, **k)) or jobs[-1]),
    )

    observed: dict[str, Any] = {}

    def observe_then_cancel(plugin_id: str) -> None:
        # While the plugin is executing, its own admitted child is OPEN (no
        # receipt yet) — proof the provider work happens inside the dispatch.
        with db._connection() as conn:
            observed["open"] = [
                dict(row) for row in conn.execute(
                    """SELECT o.native_id FROM kernel_operations o
                       LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id
                       WHERE o.parent_operation_id=? AND o.name='inference.invoke'
                         AND r.operation_id IS NULL""",
                    (jobs[0].parent.operation_id,),
                )
            ]
        observed["engine_bound"] = host.bound_engines[-1] is engine
        jobs[0].cancel()

    host.on_execute = observe_then_cancel

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    assert len(observed["open"]) == 1, observed
    assert observed["engine_bound"] is True
    # Cancelled inside its own dispatch: nothing the plugin produced is durable.
    assert _rows(db, "plugin_runs") == []
    assert db.plugins.list_artifacts(state.id) == []
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed.intel_status != "ready"


# ------------------------------------- D3: the displaced work actually executes


def test_a_stop_displaced_job_runs_the_bookmark_and_title_children(tmp_path, monkeypatch):
    from holdspeak.meeting_session.deferred_admission import (
        CONTRACT_AUTO_TITLE,
        CONTRACT_BOOKMARK_LABEL,
    )
    from holdspeak.meeting_session.intel_plan import (
        CAPABILITY_AUTO_TITLE,
        CAPABILITY_BOOKMARK_LABEL,
        DISPLACED_AUTO_TITLE,
        DISPLACED_BOOKMARK_LABELS,
        DISPLACED_FINAL_ANALYSIS,
    )

    db, broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr("holdspeak.intel_queue._routed_plugin_host", lambda enabled: None)
    monkeypatch.setattr(_Cfg.meeting, "intent_router_enabled", False, raising=False)
    state = _queued_meeting(
        db, "m-displaced",
        text="we agreed to cut the travel budget",
        title="",
        bookmarks=(2.0,),
        displaced_work=(
            DISPLACED_FINAL_ANALYSIS, DISPLACED_BOOKMARK_LABELS, DISPLACED_AUTO_TITLE,
        ),
    )
    job = db.intel.get_intel_job(state.id)
    assert job.displaced_work == (
        DISPLACED_FINAL_ANALYSIS, DISPLACED_BOOKMARK_LABELS, DISPLACED_AUTO_TITLE,
    )

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    # The displaced capabilities are FROZEN in this job's plan and each displaced
    # dispatch is one trusted child of the job parent.
    parent = _parents(db, PARENT_KIND)[0]
    snapshot = json.loads(parent["input_json"])
    assert {CAPABILITY_BOOKMARK_LABEL, CAPABILITY_AUTO_TITLE} <= set(snapshot["capabilities"])
    assert snapshot["displaced_work"] == list(job.displaced_work)
    assert [request.definition_origin.contract for request in requests] == [
        CONTRACT_DEFERRED_ANALYSIS, CONTRACT_BOOKMARK_LABEL, CONTRACT_AUTO_TITLE,
    ]
    assert len(_children(db, parent["operation_id"])) == 3
    assert engine.labels and engine.titles

    # The outputs landed through receipt-gated materializers, in the DB.
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed.title == "Quarterly budget review"
    assert [bookmark.label for bookmark in refreshed.bookmarks] == ["Budget decision"]
    kinds = {
        str(row["kind"]): str(row["state"]) for row in _rows(db, "kernel_projection_stages")
    }
    assert kinds["meeting-deferred-bookmark-label"] == "PUBLISHED"
    assert kinds["meeting-deferred-auto-title"] == "PUBLISHED"
    # Only now is the meeting Ready.
    assert refreshed.intel_status == "ready"
    assert refreshed.intel_completed_at is not None
    assert db.intel.get_intel_job(state.id) is None


def test_the_meeting_is_not_ready_until_the_displaced_work_settles(tmp_path, monkeypatch):
    from holdspeak.meeting_session.intel_plan import (
        DISPLACED_AUTO_TITLE,
        DISPLACED_FINAL_ANALYSIS,
    )

    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr("holdspeak.intel_queue._routed_plugin_host", lambda enabled: None)
    monkeypatch.setattr(_Cfg.meeting, "intent_router_enabled", False, raising=False)
    state = _queued_meeting(
        db, "m-displaced-fails", title="",
        displaced_work=(DISPLACED_FINAL_ANALYSIS, DISPLACED_AUTO_TITLE),
    )

    def explode(transcript: str) -> str:
        raise RuntimeError("the title endpoint refused")

    monkeypatch.setattr(engine, "generate_title", explode)

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    refreshed = db.meetings.get_meeting(state.id)
    # The base analysis is retained, but the meeting is NOT Ready and the job is
    # still outstanding: displaced work that did not settle blocks readiness.
    assert refreshed.intel is not None
    assert refreshed.intel_status != "ready"
    assert refreshed.intel_completed_at is None
    assert refreshed.title in (None, "")
    job = db.intel.get_intel_job(state.id)
    assert job is not None
    assert DISPLACED_AUTO_TITLE in job.displaced_work, "a retry must still know its displaced work"


def test_a_normal_deferred_job_runs_no_title_or_bookmark_children(tmp_path, monkeypatch):
    from holdspeak.meeting_session.intel_plan import (
        CAPABILITY_AUTO_TITLE,
        CAPABILITY_BOOKMARK_LABEL,
    )

    db, _broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr("holdspeak.intel_queue._routed_plugin_host", lambda enabled: None)
    monkeypatch.setattr(_Cfg.meeting, "intent_router_enabled", False, raising=False)
    state = _queued_meeting(db, "m-normal", title="", bookmarks=(2.0,))

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    parent = _parents(db, PARENT_KIND)[0]
    snapshot = json.loads(parent["input_json"])
    assert snapshot["displaced_work"] == []
    assert set(snapshot["capabilities"]) == {CAPABILITY_DEFERRED_ANALYSIS}
    assert CAPABILITY_BOOKMARK_LABEL not in snapshot["capabilities"]
    assert CAPABILITY_AUTO_TITLE not in snapshot["capabilities"]
    assert [request.definition_origin.contract for request in requests] == [
        CONTRACT_DEFERRED_ANALYSIS
    ]
    assert engine.titles == [] and engine.labels == []
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed.title in (None, "")
    assert [bookmark.label for bookmark in refreshed.bookmarks] == ["Bookmark"]
    assert refreshed.intel_status == "ready"


# ------------------------------------------- D4: no late ready around the stop


def test_a_child_finalizing_during_stop_cannot_stamp_ready(tmp_path, monkeypatch):
    """The apply is gated on the same election: a late window is DISCARDED."""
    db, broker, session, engine, _requests = _session_rig(tmp_path, monkeypatch)
    session.start()
    parent_id = session.intel_session_operation_id()
    _add_segment(session, "A window that finalizes just before stop", 0.0)

    finalized = threading.Event()
    release = threading.Event()
    real_finalize = broker.projection_stager.finalize

    def gated_finalize(invocation_id: str):
        projection = real_finalize(invocation_id)
        if projection is not None and str(projection.get("capability") or "") == "live-analysis":
            # The child WON: its receipt is durable and its projection published.
            finalized.set()
            release.wait(20.0)
        return projection

    monkeypatch.setattr(broker.projection_stager, "finalize", gated_finalize)

    window = threading.Thread(target=session._run_intel_analysis, daemon=True)
    window.start()
    assert finalized.wait(15.0), "the live window never finalized its projection"

    # stop() now cancels, closes and stamps `queued` while that apply is pending.
    final = session.stop()
    assert final.intel_status == "queued"
    child = _children(db, parent_id)[0]
    assert broker.store.receipt(child["operation_id"])["outcome"] == "succeeded"

    # Release the lingering apply: it must be discarded by the closed-flag gate.
    release.set()
    window.join(15.0)
    assert not window.is_alive()

    assert session._state.intel is None, "a late window stamped meeting state"
    assert session._state.intel_status == "queued"
    assert session._state.intel_completed_at is None
    persisted = db.meetings.get_meeting(final.id)
    assert persisted.intel_status == "queued"
    assert persisted.intel_completed_at is None
    assert persisted.intel is None
    # The handoff still happened, so the displaced work is durably queued.
    assert db.intel.get_intel_job(final.id) is not None


def test_no_transcript_material_reaches_the_kernel_journal_on_the_deferred_path(tmp_path, monkeypatch):
    db, _broker, engine, host, _requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor",), chain=("requirements_extractor",),
    )
    state = _queued_meeting(db, "m-journal", text=f"the revenue number is {SENTINEL}")

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    # A second job whose provider FAILS with text quoting the transcript.
    db.intel.enqueue_intel_job(
        state.id, transcript_hash=state.transcript_hash(), reason="second pass"
    )

    def explode(transcript: str, *, stream: bool = False):
        raise RuntimeError(f"endpoint echoed: {transcript}")

    monkeypatch.setattr(engine, "analyze", explode)
    assert process_next_intel_job() is True

    # The provider really received the material...
    assert any(SENTINEL in text for text in engine.analyzed)
    # ...and no kernel row carries it.
    for table in ("kernel_operations", "kernel_receipts", "kernel_journal", "kernel_parent_runs"):
        rows = _rows(db, table)
        assert rows, table
        for row in rows:
            assert SENTINEL not in json.dumps(row, default=str), table
    outcomes = {str(row["outcome"]) for row in _rows(db, "kernel_receipts")}
    assert {"succeeded", "failed"} <= outcomes, outcomes
