"""HS-131-10 — the one-path fence: literal spine, every named surface.

Section 2 of DESIGN-HS-131-10.md (Sol-ratified 2026-08-11) requires that
every named product surface — FIFTEEN distinct entry forms, not the
charter's miscounted thirteen, and SIXTEEN once HS-131-13 migrated Cadence
onto the spine — reaches the SAME literal admission spine for every
physical model dispatch:

    1. InferenceRunner.invoke            (admission entry)
    2. Broker.submit_trusted_child (parent-scoped child) or Broker.submit
       (root), plus Broker._admit_authority
    3. Broker.claim
    4. InferenceRunner._dispatch
    5. ExecutorPlane._terminal            (receipt persistence)

This module monkeypatches those exact function OBJECTS (captured once, at
import time, from the kernel modules) so that a passing trace is proof the
surface really executed the imported functions — never a behaviorally
equivalent wrapper living somewhere else. Each surface driver builds the
cheapest REAL rig — a real ``Database`` in ``tmp_path`` plus the production
broker via ``holdspeak.kernel.runtime._configure`` — and fakes only the
engine/provider CONSTRUCTION seam, reusing the rigs named in the story
wherever one already exists in another test module (cross-module import of
their plain, undecorated helper functions; proven to work under this
repo's pytest configuration, since ``tests/`` has no package boundary that
would forbid it).
"""
from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from typing import Any, Callable

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.inference_targets import THIS_MACHINE_ID
from holdspeak.kernel.broker import Broker
from holdspeak.kernel.executor import ExecutorPlane
from holdspeak.kernel.inference_runner import InferenceRunner
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind

pytestmark = pytest.mark.timeout(120, method="signal")

OWNER = Principal(PrincipalKind.OWNER, "spine-owner")

#: The principal a web route resolves to when the request carries no explicit
#: one — ``holdspeak/principals.py:179`` and the identical default in every
#: ``holdspeak/web/routes/primitives/*`` module. The HTTP-driven surfaces below
#: therefore run as THIS, not as the module's ``OWNER``; asserting the
#: difference is part of proving the kernel stamps the real authenticated
#: caller rather than whatever the test happened to have in hand.
WEB_OWNER_SESSION = Principal(PrincipalKind.OWNER, "owner-session")


# ---------------------------------------------------------------------------
# What a driver leaves behind, so the fence can read the REAL rows back
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SurfaceRun:
    """The handles a surface driver hands back after really running.

    The spine test (below) only needs the driver to EXECUTE; the provenance
    suite (``test_one_path_provenance.py``) needs to find the rows that
    execution wrote. Rather than keep a second, drifting copy of every rig
    over there, every driver returns this: the database it actually used,
    the principal it authenticated as, the parent it ran under (``None`` for a
    root-shaped admission), the destination its plan froze, and how many
    ``inference.invoke`` children that exercise is expected to emit.

    ``expected_children`` is what forces EVERY emitted child to be inspected:
    a surface that quietly grows a second, unexamined dispatch fails the count
    before any per-row assertion runs.
    """

    db: Database
    principal: Principal
    parent_operation_id: str | None
    destination_id: str
    expected_children: int = 1
    parent_kind: str | None = None


def _parent_run_operation_id(db: Database, kind: str) -> str:
    """The operation id of the one live parent run of ``kind``.

    Read from the real ``kernel_parent_runs`` table rather than reconstructed,
    so a surface whose parent never registered fails here instead of silently
    handing the fence a plausible-looking id.
    """
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT operation_id FROM kernel_parent_runs WHERE kind=?", (kind,)
        ).fetchall()
    assert len(rows) == 1, f"expected exactly one {kind!r} parent run, found {len(rows)}"
    return rows[0][0]


# ---------------------------------------------------------------------------
# The shared trace: monkeypatch the LITERAL kernel functions, record identity
# ---------------------------------------------------------------------------

# Captured at import/collection time — before any test's monkeypatch fixture
# has touched anything — so these are unambiguously the production functions
# the kernel modules define, not whatever a previous test left behind.
_ORIGINAL_INVOKE = InferenceRunner.__dict__["invoke"]
_ORIGINAL_DISPATCH = InferenceRunner.__dict__["_dispatch"]
_ORIGINAL_SUBMIT = Broker.__dict__["submit"]
_ORIGINAL_SUBMIT_TRUSTED_CHILD = Broker.__dict__["submit_trusted_child"]
_ORIGINAL_ADMIT_AUTHORITY = Broker.__dict__["_admit_authority"]
_ORIGINAL_CLAIM = ExecutorPlane.__dict__["claim"]
_ORIGINAL_TERMINAL = ExecutorPlane.__dict__["_terminal"]

# Broker inherits claim/_terminal from ExecutorPlane without overriding
# them. Confirm that ONCE here so patching ExecutorPlane really does
# intercept every Broker instance's dispatch — a literal-identity fence
# only means something if this holds.
assert Broker.claim is _ORIGINAL_CLAIM
assert Broker._terminal is _ORIGINAL_TERMINAL


@contextlib.contextmanager
def _spine_trace(monkeypatch: pytest.MonkeyPatch):
    """Wrap the six literal spine functions; yield the ordered call log.

    Each wrapper appends its label, then calls the CAPTURED ORIGINAL
    function object directly — never a re-lookup through the class — so a
    green trace proves the surface executed the imported kernel functions
    themselves. A same-behavior stand-in defined anywhere else would never
    make the wrapper fire, and the assertions below would fail closed.
    """
    calls: list[str] = []

    def _wrap(cls: type, name: str, original: Callable[..., Any], label: str) -> None:
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            calls.append(label)
            return original(self, *args, **kwargs)

        monkeypatch.setattr(cls, name, wrapper)

    _wrap(InferenceRunner, "invoke", _ORIGINAL_INVOKE, "invoke")
    _wrap(Broker, "submit", _ORIGINAL_SUBMIT, "submit")
    _wrap(Broker, "submit_trusted_child", _ORIGINAL_SUBMIT_TRUSTED_CHILD, "submit_trusted_child")
    _wrap(Broker, "_admit_authority", _ORIGINAL_ADMIT_AUTHORITY, "admit_authority")
    _wrap(ExecutorPlane, "claim", _ORIGINAL_CLAIM, "claim")
    _wrap(InferenceRunner, "_dispatch", _ORIGINAL_DISPATCH, "dispatch")
    _wrap(ExecutorPlane, "_terminal", _ORIGINAL_TERMINAL, "terminal")

    yield calls


def _assert_spine_reached(calls: list[str]) -> str:
    """Assert every literal step fired, in the required order, >=1 time.

    Anchored on the FIRST ``invoke`` call: some surfaces admit a root/parent
    operation (its own submit/admit_authority/claim trio) before ever
    reaching a child ``inference.invoke`` — e.g. ``ParentRunController.start``
    submits the parent kind through ``Broker.submit`` directly. Searching
    for each step from the position of the previous one (rather than the
    naive first-occurrence-anywhere) keeps the assertion anchored to the
    child invocation's OWN causal chain instead of accidentally being
    satisfied by the parent's unrelated admission.
    """
    assert "invoke" in calls, f"InferenceRunner.invoke was never reached: {calls}"
    start = calls.index("invoke")
    tail = calls[start:]
    admission_label = "submit_trusted_child" if "submit_trusted_child" in tail else "submit"
    for label in (admission_label, "admit_authority", "claim", "dispatch", "terminal"):
        assert label in tail, f"spine step {label!r} never fired after invoke: {calls}"
    order = ("invoke", admission_label, "admit_authority", "claim", "dispatch", "terminal")
    positions: list[int] = []
    cursor = start
    for label in order:
        cursor = calls.index(label, cursor)
        positions.append(cursor)
    assert positions == sorted(positions), f"spine steps out of order: {calls}"
    return admission_label


# ---------------------------------------------------------------------------
# NOTE on the fake engine factories below. HS-131-10 gave every engine factory
# ONE calling convention -- ``factory(revision, *, warrant, context)`` -- and
# `InferenceRunner.invoke` passes both keywords unconditionally, with no
# identity special-case for the production factory. A test double must
# therefore absorb them (``**_``); a one-argument lambda raises TypeError
# inside `invoke`, which the runner correctly converts into a `failed` receipt
# and the surface reports as a refused destination. That failure mode is
# indistinguishable from a real regression at the surface, so the ``**_`` is
# load-bearing, not cosmetic.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# The surface drivers. Each performs >=1 real model invocation through
# production admission code; only the engine/provider CONSTRUCTION seam is
# faked. Drivers run INSIDE the _spine_trace context (see the parametrized
# test at the bottom), so any rig that itself wraps
# ``broker.inference_runner.invoke`` at the instance level (several of the
# reused rigs do, to record InvocationRequest objects for their own
# assertions) still traces correctly: our class-level patch is captured as
# THEIR "real_invoke" closure, so the call chain still passes through it.
# ---------------------------------------------------------------------------


def _drive_ask(tmp_path, monkeypatch) -> SurfaceRun:
    from holdspeak.services.ask_service import AskService

    db = Database(tmp_path / "ask.db")
    profile = db.profiles.upsert(
        profile_id="prof_a", name="Alpha", kind="openAICompatible",
        base_url="http://192.168.1.50:8080", model="model-a", requires_key=False,
    )
    broker = _configure(db)

    class FakeIntel:
        active_provider = "openai_compatible"

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            return "ok"

    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda revision, **_: FakeIntel())
    service = AskService(db, hub_model=lambda: "", broker=broker)
    asyncio.run(service.ask(OWNER, "summarize", inference_target_id="prof_a", model="model-a"))
    return SurfaceRun(db, OWNER, None, profile.id)


def _ready_this_machine(tmp_path, monkeypatch) -> None:
    """Bind the production local-target resolver to a harmless readable artifact.

    ``this_machine_target`` reads ``configured_local_meeting_model_path`` directly;
    patching the retired private readiness helper does not make the real placement
    ready. The engine factory remains the sole external physical-boundary fake.
    """
    model_path = tmp_path / "spine-local.gguf"
    model_path.touch()
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path",
        lambda: str(model_path),
    )


def _recipe_rig(tmp_path, monkeypatch, name: str):
    from holdspeak.services.recipe_service import RecipeService

    db = Database(tmp_path / f"{name}.db")
    db.recipes.upsert(recipe_id="r1", name="Recipe", system_prompt="system")
    _ready_this_machine(tmp_path, monkeypatch)

    class Engine:
        active_provider = "test"
        active_model = "test-model"

        def run_prompt(self, **kwargs):
            return "runner recipe"

    broker = _configure(db)
    # HS-131-13: `this_machine` builds from the FROZEN revision, so the provider
    # double is injected at the runner's engine factory — the one construction
    # boundary a migrated surface actually goes through.
    broker.inference_runner._engine_factory = lambda _revision, **_: Engine()
    return db, RecipeService(db, broker=broker)


def _drive_recipe_run(tmp_path, monkeypatch) -> SurfaceRun:
    db, service = _recipe_rig(tmp_path, monkeypatch, "recipe_run")
    asyncio.run(service.run(OWNER, "r1", input="hello"))
    return SurfaceRun(db, OWNER, None, THIS_MACHINE_ID)


def _drive_recipe_chat(tmp_path, monkeypatch) -> SurfaceRun:
    db, service = _recipe_rig(tmp_path, monkeypatch, "recipe_chat")
    asyncio.run(service.chat(OWNER, "r1", question="hello"))
    return SurfaceRun(db, OWNER, None, THIS_MACHINE_ID)


def _http_engine_rig(tmp_path, monkeypatch, name: str):
    """The off-the-loop route rig (test_engine_off_the_loop.py), reimplemented
    as a plain function since the original is a pytest fixture and cannot be
    called directly."""
    import holdspeak.db as hsdb
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes import build_primitives_router

    reset_database()
    db = Database(tmp_path / f"{name}.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    _ready_this_machine(tmp_path, monkeypatch)

    class _Engine:
        active_provider = "local"

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            return "spine-output"

    engine = _Engine()
    monkeypatch.setitem(InferenceRunner.__init__.__kwdefaults__, "engine_factory", lambda revision, **_: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)

    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    return db, TestClient(app)


def _drive_sequence(tmp_path, monkeypatch) -> SurfaceRun:
    db, client = _http_engine_rig(tmp_path, monkeypatch, "sequence")
    rid = client.post(
        "/api/recipes", json={"name": "Seq", "system_prompt": "SYS", "user_template": "{input}"},
    ).json()["recipe"]["id"]
    cid = client.post("/api/chains", json={"name": "seq", "steps": [rid]}).json()["chain"]["id"]
    response = client.post(f"/api/chains/{cid}/run", json={"input": "hi"})
    assert response.status_code == 200, response.text
    return SurfaceRun(
        db, WEB_OWNER_SESSION, _parent_run_operation_id(db, "sequence"), THIS_MACHINE_ID,
        parent_kind="sequence",
    )


def _drive_workflow(tmp_path, monkeypatch) -> SurfaceRun:
    db, client = _http_engine_rig(tmp_path, monkeypatch, "workflow")
    graph = {
        "entry": "entry",
        "nodes": [
            {"id": "entry", "kind": {"entry": {}}},
            {"id": "model", "kind": {"summarize": {}}},
            {"id": "out", "kind": {"output": {}}},
        ],
        "exec_edges": [
            {"from": {"node": "entry", "name": "then"}, "to": "model"},
            {"from": {"node": "model", "name": "then"}, "to": "out"},
        ],
    }
    wid = client.post(
        "/api/workflows", json={"id": "wf_spine", "name": "Spine", "graph_json": graph},
    ).json()["workflow"]["id"]
    response = client.post(f"/api/workflows/{wid}/run", json={"input": "hi"})
    assert response.status_code == 200, response.text
    return SurfaceRun(
        db, WEB_OWNER_SESSION, _parent_run_operation_id(db, "workflow"), THIS_MACHINE_ID,
        parent_kind="workflow",
    )


def _drive_workbench_manual(tmp_path, monkeypatch) -> SurfaceRun:
    from tests.unit.test_workbench_runner_migration import OWNER as WORKBENCH_OWNER
    from tests.unit.test_workbench_runner_migration import _run as _workbench_run
    from tests.unit.test_workbench_runner_migration import _setup_runner

    db, broker, workbench, _items, _state = _setup_runner(tmp_path, monkeypatch)
    result = _workbench_run(db, broker, workbench.id, memory_enabled=False)
    return SurfaceRun(
        db, WORKBENCH_OWNER, result["parent_operation_id"], workbench.profile_id,
        parent_kind="workbench",
    )


def _drive_workbench_memory(tmp_path, monkeypatch) -> SurfaceRun:
    from tests.unit.test_workbench_runner_migration import OWNER as WORKBENCH_OWNER
    from tests.unit.test_workbench_runner_migration import _run as _workbench_run
    from tests.unit.test_workbench_runner_migration import _setup_runner

    db, broker, workbench, _items, _state = _setup_runner(tmp_path, monkeypatch)
    result = _workbench_run(db, broker, workbench.id, memory_enabled=True)
    # Memory writeback is the SECOND admitted child of the same parent: one
    # item dispatch, then the writeback dispatch. Both must be inspected.
    return SurfaceRun(
        db, WORKBENCH_OWNER, result["parent_operation_id"], workbench.profile_id,
        expected_children=2, parent_kind="workbench",
    )


def _drive_workbench_scheduled(tmp_path, monkeypatch) -> SurfaceRun:
    from tests.unit.test_schedule_delegations import OWNER as SCHEDULE_OWNER
    from tests.unit.test_schedule_delegations import SCHEDULER
    from tests.unit.test_schedule_delegations import _rig as _schedule_rig
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db, service, wid = _schedule_rig(tmp_path)
    db.workbench_items.upsert(item_id="i-spine", workbench_id=wid, title="scheduled")
    service.update_workbench(SCHEDULE_OWNER, wid, schedule_enabled=True)

    class FakeIntel:
        def run_prompt(self, **_):
            return "scheduled output"

    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: FakeIntel())
    broker = _configure(db)
    result = asyncio.run(WorkbenchRunner(db, broker).run_scheduled(SCHEDULER, wid, due_minute=999))
    # The scheduled run leaves memory writeback ON, so the same parent emits
    # the item child and the writeback child.
    return SurfaceRun(
        db, SCHEDULER, result["parent_operation_id"], db.workbenches.get(wid).profile_id,
        expected_children=2, parent_kind="workbench",
    )


def _drive_rails(tmp_path, monkeypatch) -> SurfaceRun:
    """Run Rails through the real SERVICE bundle, route, and controller path."""
    from holdspeak import rails_observer
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile

    reset_database()
    db = Database(tmp_path / "rails.db")
    # This makes a fully versioned production-shaped profile, binding, readiness
    # observation, deployment revision, and artifact. The service then elects its
    # route from the exact capability assignment below rather than from a legacy
    # profile pointer or a decorated router fake.
    _profile(db, "rails")
    InferenceAssignmentService(db).set_assignment(
        ASSIGNMENT_OWNER,
        {
            "command_id": "rails-spine-assignment",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "background.rails_summary"},
            "entries": [{"profile_id": "rails", "profile_revision": 1}],
        },
    )
    principal = Principal(
        PrincipalKind.SERVICE,
        "rails-observer",
        frozenset(
            {
                ("rails.observer-batch", 1),
                ("inference.invoke", 1),
                ("inference.cancel", 1),
            }
        ),
        "rails-observer:journal-only",
    )
    broker = _configure(db)

    class FakeIntel:
        def run_prompt(self, **_):
            return "Only the observed facts."

    broker.inference_runner._engine_factory = lambda _revision, **_: FakeIntel()
    summarizer = rails_observer.build_profile_summarizer(db=db, broker=broker, principal=principal)
    batch = rails_observer.summarize_batch(
        [{"ts": "t1", "event": "gate_pass", "story": "", "repo": "code"}], summarize_fn=summarizer,
    )
    assert not batch["degraded"], batch
    return SurfaceRun(
        db,
        principal,
        _parent_run_operation_id(db, "rails.observer-batch"),
        THIS_MACHINE_ID,
        parent_kind="rails.observer-batch",
    )


def _drive_decision(tmp_path, monkeypatch) -> SurfaceRun:
    from tests.unit.test_decision_record_service import _accepted_meeting_decision
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService

    db = Database(tmp_path / "decision.db")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-127", "2026-08-07T00:00:00+00:00", "Spine meeting"),
        )
    _accepted_meeting_decision(db, "dec-spine")
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile
    _profile(db, "decision-profile")
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-spine-decision", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
        "entries": [{"profile_id": "decision-profile", "profile_revision": 1}],
    })
    broker = _configure(db)

    class Intel:
        def run_prompt(self, **_):
            return "Adopt this."

    broker.inference_runner._engine_factory = lambda _revision, **_: Intel()
    service = DecisionLifecycleService(db, kernel=broker)
    asyncio.run(
        service.draft_promoted_with_model(OWNER, "dec-spine", "note", {})
    )
    return SurfaceRun(
        db, OWNER, _parent_run_operation_id(db, "decision.promotion-draft"), THIS_MACHINE_ID,
        parent_kind="decision.promotion-draft",
    )


def _drive_delivery_review(tmp_path, monkeypatch) -> SurfaceRun:
    import holdspeak.db as hsdb
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.delivery_prs import build_delivery_prs_router

    reset_database()
    db = Database(tmp_path / "delivery.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    _ready_this_machine(tmp_path, monkeypatch)
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile
    _profile(db, "delivery-profile")
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-spine-delivery", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "delivery.pr_review_draft"},
        "entries": [{"profile_id": "delivery-profile", "profile_revision": 1}],
    })

    class FakeEngine:
        active_provider = "test"
        active_model = "test-model"

        def run_prompt(self, **_):
            return "Looks fine."

    # The engine-factory kwdefault must be patched BEFORE the broker (and its
    # one InferenceRunner) is built — the factory is bound onto the instance
    # at construction time, so patching after `_configure` would silently
    # leave the real `build_intel_for_revision` in place.
    monkeypatch.setitem(InferenceRunner.__init__.__kwdefaults__, "engine_factory", lambda revision, **_: FakeEngine())
    _configure(db)

    class _FakeDeliveryService:
        def action_context(self, source_id, number):
            return {"status": "ok", "row": {"verbs": {"draft_review": {"available": True}}}}

        def review_material(self, source_id, number):
            return {"status": "ok", "diff": "diff --git a/x b/x\n+hi", "revision": "rev-spine", "linked": []}

    ctx = WebContext(get_state=lambda: {}, delivery_service=object())
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_delivery_prs_router(ctx, service=_FakeDeliveryService()))
    with TestClient(app) as client:
        response = client.post(
            "/api/delivery/prs/spine-source/1/draft-review",
            json={},
        )
        replay = client.post(
            "/api/delivery/prs/spine-source/1/draft-review",
            json={},
        )
        assert response.status_code == replay.status_code == 200, (response.text, replay.text)
        assert response.json()["artifact_id"] == replay.json()["artifact_id"]
        assert response.json()["placement"]["egress"] == {"scope": "local"}
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 1
    return SurfaceRun(
        db, OWNER, _parent_run_operation_id(db, "delivery.pr-review-draft"), THIS_MACHINE_ID,
        parent_kind="delivery.pr-review-draft",
    )


def _drive_voice(tmp_path, monkeypatch) -> SurfaceRun:
    from tests.unit.test_voice_resolve import OWNER as VOICE_OWNER
    from tests.unit.test_voice_resolve import _admitted_voice_rig

    db, service, broker, workbench_id = _admitted_voice_rig(tmp_path)

    class FakeIntel:
        def run_prompt(self, **_):
            return '{"zone_ids":["zone-a"]}'

    broker.inference_runner._engine_factory = lambda _revision, **_: FakeIntel()
    service.resolve_voice(VOICE_OWNER, workbench_id, "find Alpha", "voice-spine")
    return SurfaceRun(
        db, VOICE_OWNER, _parent_run_operation_id(db, "voice_reference_resolve"),
        db.workbenches.get(workbench_id).resolver_profile_id,
        parent_kind="voice_reference_resolve",
    )


def _drive_meeting_live(tmp_path, monkeypatch) -> SurfaceRun:
    from tests.unit.test_meeting_session_admission import (
        OWNER as MEETING_OWNER,
        _assign_bundle_routes,
        _rig as _meeting_live_rig,
    )
    from holdspeak.meeting_session.models import TranscriptSegment

    db, _broker, session, _engine, _requests = _meeting_live_rig(tmp_path, monkeypatch)
    _assign_bundle_routes(db)
    session.start()
    session._state.segments.append(
        TranscriptSegment(text="spine window", speaker="Me", start_time=0.0, end_time=5.0)
    )
    session._run_intel_analysis()
    return SurfaceRun(
        db, MEETING_OWNER, _parent_run_operation_id(db, "meeting.session"), THIS_MACHINE_ID,
        parent_kind="meeting.session",
    )


def _drive_meeting_deferred(tmp_path, monkeypatch) -> SurfaceRun:
    from tests.unit.test_meeting_deferred_admission import _queue_rig, _queued_meeting
    from holdspeak.intel_queue import process_next_intel_job

    db, _broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    _queued_meeting(db, "m-spine")
    assert process_next_intel_job() is True
    # The queue runs as its own sealed service principal, never as the owner
    # who recorded the meeting. Reuse the production factory so provenance
    # checks its actual narrow authority basis rather than a guessed identity.
    from holdspeak.meeting_session.deferred_bound import queue_service_principal

    queue_principal = queue_service_principal()
    return SurfaceRun(
        db, queue_principal, _parent_run_operation_id(db, "meeting.deferred-intel-job"),
        THIS_MACHINE_ID, parent_kind="meeting.deferred-intel-job",
    )


def _drive_dictation(tmp_path, monkeypatch) -> SurfaceRun:
    from tests.unit.test_dictation_pipeline_admission import FROZEN_PROFILE_ID
    from tests.unit.test_dictation_pipeline_admission import FakeBackend, FakeSchema
    from tests.unit.test_dictation_pipeline_admission import _rig as _dictation_rig
    from holdspeak.speech_session import AdmittedDictationRuntime

    db, _broker, session, _engine, _requests = _dictation_rig(tmp_path, monkeypatch)
    runtime = AdmittedDictationRuntime(FakeBackend(), session.provider())
    runtime.classify("spine prompt", FakeSchema(), max_tokens=64, temperature=0.0)
    return SurfaceRun(
        db, WEB_OWNER_SESSION, session.operation_id, FROZEN_PROFILE_ID,
        parent_kind="dictation.session",
    )


def _drive_cadence(tmp_path, monkeypatch) -> SurfaceRun:
    """HS-131-13: request-time Cadence next-action drafting.

    The sixteenth surface. It is a distinct entry form, not a variant of an
    existing one: a foreground READ (`GET /api/cadence/loops/{id}`) that draws one
    model draft under the caller the transport authenticated — never the owner and
    never the scheduler, which is the distinction HS-131-06 drew and this story
    had to keep while moving the work onto the admitted spine.
    """
    from holdspeak.cadence.models import OpenLoop
    from holdspeak.config.integrations import CadenceConfig
    from holdspeak.services.cadence_service import CadenceService

    reset_database()
    db = Database(tmp_path / "cadence.db")
    _ready_this_machine(tmp_path, monkeypatch)
    loop = db.cadence.upsert_loop(
        OpenLoop(source_type="meeting_action", source_id="a1", title="Ship the watchdog", owner="Karol")
    )
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile
    _profile(db, "cadence-profile")
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-spine-cadence", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "background.cadence_draft"},
        "entries": [{"profile_id": "cadence-profile", "profile_revision": 1}],
    })
    broker = _configure(db)

    class FakeIntel:
        active_provider = "local"

        def run_prompt(self, **_):
            return '{"kind":"create_issue","title":"Watchdog the queue","body_markdown":"body"}'

    broker.inference_runner._engine_factory = lambda _revision, **_: FakeIntel()
    service = CadenceService(db, CadenceConfig(use_llm=True), kernel=broker)
    detail = asyncio.run(service.get_loop(WEB_OWNER_SESSION, loop.id))
    assert detail["next_action"]["generated_by"] == "llm", detail["next_action"]
    return SurfaceRun(
        db, WEB_OWNER_SESSION, _parent_run_operation_id(db, "cadence.next-action-draft"),
        THIS_MACHINE_ID, parent_kind="cadence.next-action-draft",
    )


SURFACE_DRIVERS: dict[str, Callable[[Any, Any], SurfaceRun]] = {
    "Ask": _drive_ask,
    "Recipe run": _drive_recipe_run,
    "Recipe chat": _drive_recipe_chat,
    "Sequence": _drive_sequence,
    "Workflow": _drive_workflow,
    "manual Workbench": _drive_workbench_manual,
    "scheduled Workbench": _drive_workbench_scheduled,
    "memory writeback": _drive_workbench_memory,
    "Rails": _drive_rails,
    "Decision promotion": _drive_decision,
    "Delivery review": _drive_delivery_review,
    "voice": _drive_voice,
    "meeting live": _drive_meeting_live,
    "meeting deferred": _drive_meeting_deferred,
    "dictation pipeline": _drive_dictation,
    "cadence next action": _drive_cadence,
}

#: HS-131-10 named fifteen; HS-131-13 migrated Cadence onto the spine and it takes
#: its seat here rather than riding in unproven. The other two families that story
#: closed added no surface: both were DELETED as duplicates of a surface already
#: below (Decision promotion, Delivery review).
assert len(SURFACE_DRIVERS) == 16, "every named surface form is proven here; none may be collapsed"

#: Which admission shape each surface uses. Module-level (rather than buried in
#: the sanity test below) because ``test_one_path_provenance.py`` imports these
#: to cross-check the DECLARED shape against the shape the stored row actually
#: shows — the two files cannot drift apart without one of them failing.
ROOT_SHAPED_SURFACES = frozenset({"Ask", "Recipe run", "Recipe chat"})
CHILD_SHAPED_SURFACES = frozenset({
    "Sequence", "Workflow", "manual Workbench", "scheduled Workbench",
    "memory writeback", "Rails", "Decision promotion", "Delivery review", "voice",
    "meeting live", "meeting deferred", "dictation pipeline", "cadence next action",
})


@pytest.mark.parametrize("surface", sorted(SURFACE_DRIVERS), ids=sorted(SURFACE_DRIVERS))
def test_surface_reaches_the_literal_admission_spine(surface: str, tmp_path, monkeypatch) -> None:
    """Every one of the named surfaces reaches the SAME literal
    InferenceRunner.invoke -> Broker.{submit_trusted_child,submit} ->
    Broker._admit_authority -> Broker.claim -> InferenceRunner._dispatch ->
    ExecutorPlane._terminal spine, in that order, at least once."""
    driver = SURFACE_DRIVERS[surface]
    with _spine_trace(monkeypatch) as calls:
        driver(tmp_path, monkeypatch)
    _assert_spine_reached(calls)


def test_the_two_admission_shapes_both_appear_across_every_surface() -> None:
    """Sanity on the trace mechanism itself: the fence would be worthless if
    every surface happened to use the same admission shape — prove both a
    root (Broker.submit) and a parent-scoped child (Broker.submit_trusted_child)
    admission are exercised somewhere in the matrix above."""
    import inspect

    assert ROOT_SHAPED_SURFACES | CHILD_SHAPED_SURFACES == set(SURFACE_DRIVERS)
    assert not (ROOT_SHAPED_SURFACES & CHILD_SHAPED_SURFACES)
    assert ROOT_SHAPED_SURFACES and CHILD_SHAPED_SURFACES
    for name in SURFACE_DRIVERS:
        assert inspect.isfunction(SURFACE_DRIVERS[name])


def test_each_driver_reports_the_run_it_actually_performed(tmp_path, monkeypatch) -> None:
    """The declared admission shape must match what the driver hands back.

    ``SurfaceRun.parent_operation_id`` is the handle the provenance suite reads
    its rows through, so a driver that stopped running under its parent — or
    started running under one — has to be caught HERE rather than quietly
    changing which cohort the fence inspects. Exercised on one surface of each
    shape; the provenance suite re-checks every one against the stored rows.
    """
    for surface in ("Ask", "manual Workbench"):
        run = SURFACE_DRIVERS[surface](tmp_path / surface.replace(" ", "-"), monkeypatch)
        assert isinstance(run, SurfaceRun), f"{surface}: driver returned {run!r}"
        assert run.destination_id, f"{surface}: driver named no destination"
        assert run.expected_children >= 1
        if surface in ROOT_SHAPED_SURFACES:
            assert run.parent_operation_id is None and run.parent_kind is None
        else:
            assert run.parent_operation_id and run.parent_kind


# ============================================ ROUND 2: the sanitizers' fence
# Terra blocker 1: a wrapper that protects the journal from provider TEXT must
# not also swallow the kernel's own typed CONTROL signals.


#: Every production adapter that sanitizes an arbitrary provider exception into a
#: domain failure, and therefore sits between an engine and `InferenceRunner`.
#: Adding a sanitizer without adding it here is what this list exists to catch.
SANITIZING_ADAPTERS: tuple[tuple[str, str], ...] = (
    ("holdspeak/meeting_session/intel_child.py", "MeetingAdapter.dispatch"),
    ("holdspeak/speech_session/child.py", "SpeechAdapter.dispatch"),
    # HS-131-14: a routed plugin's completion goes through the dispatch handle,
    # which wraps the provider exception so a plugin's `except Exception` cannot
    # turn a physical failure into a summary string. That wrapper is a sanitizer
    # and inherits the same ordering duty.
    ("holdspeak/plugins/intelligence.py", "PluginDispatch.chat"),
)


def _dispatch_body(path: str, scope: str) -> Any:
    import ast
    from pathlib import Path as _Path

    repo = _Path(__file__).resolve().parents[2]
    tree = ast.parse((repo / path).read_text(encoding="utf-8"))
    owner, wanted = scope.split(".")
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == owner:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == wanted:
                    return child
    raise AssertionError(f"{path}:{scope} not found")


@pytest.mark.parametrize(("path", "scope"), SANITIZING_ADAPTERS)
def test_every_sanitizing_adapter_reraises_control_signals_first(path: str, scope: str) -> None:
    """Structurally: the CONTROL_SIGNALS clause precedes the BaseException clause.

    Ordering is the whole property. ``except BaseException`` first would catch a
    dialect signal no matter what the later clauses say, which is exactly the bug
    this pins: one physical attempt, one dead receipt, and an endpoint that would
    have answered reported as failed.
    """
    import ast

    body = _dispatch_body(path, scope)
    handlers = [
        handler for node in ast.walk(body)
        if isinstance(node, ast.Try) for handler in node.handlers
    ]
    names = [ast.unparse(handler.type) if handler.type else "bare" for handler in handlers]
    assert "CONTROL_SIGNALS" in names, f"{path}:{scope} does not name CONTROL_SIGNALS"
    catch_all = [
        index for index, name in enumerate(names)
        if name in {"BaseException", "Exception", "bare"}
    ]
    assert catch_all, f"{path}:{scope} no longer sanitizes; re-review this entry"
    assert names.index("CONTROL_SIGNALS") < min(catch_all), (
        f"{path}:{scope} sanitizes BEFORE it re-raises control signals"
    )


@pytest.mark.parametrize(
    "signal_name", ["ProviderCompatibilityRetry", "ProviderIndeterminate"]
)
def test_both_sanitizing_adapters_let_a_typed_signal_through_at_runtime(signal_name: str) -> None:
    """And at runtime: the signal object itself arrives, not a domain failure.

    The structural test above cannot see whether the tuple actually holds the
    right classes; this one raises each signal through both real adapters and
    asserts identity of what comes out.
    """
    import threading

    from holdspeak.kernel.provider_signals import (
        ProviderCompatibilityRetry,
        ProviderIndeterminate,
    )
    from holdspeak.meeting_session.intel_child import MeetingAdapter, MeetingProviderFailure
    from holdspeak.speech_session.child import SpeechAdapter, SpeechProviderFailure

    signal: BaseException = (
        ProviderCompatibilityRetry("max_completion_tokens")
        if signal_name == "ProviderCompatibilityRetry"
        else ProviderIndeterminate("the provider cannot say")
    )

    def raising(_engine: Any, _payload: Any, _cancellation: Any) -> Any:
        raise signal

    for adapter, sanitized in (
        (MeetingAdapter("meeting-contract", raising), MeetingProviderFailure),
        (SpeechAdapter("speech-contract", raising), SpeechProviderFailure),
    ):
        with pytest.raises(type(signal)) as raised:
            adapter.dispatch(object(), {}, threading.Event())
        assert raised.value is signal, "the signal was re-wrapped on the way out"
        assert not isinstance(raised.value, sanitized)

    # ...while ordinary provider failures are STILL sanitized to a safe reason.
    leaky = "TRANSCRIPT-FRAGMENT-THAT-MUST-NOT-REACH-THE-JOURNAL"

    def leaking(_engine: Any, _payload: Any, _cancellation: Any) -> Any:
        raise RuntimeError(leaky)

    with pytest.raises(MeetingProviderFailure) as meeting:
        MeetingAdapter("meeting-contract", leaking).dispatch(object(), {}, threading.Event())
    assert leaky not in str(meeting.value)
    with pytest.raises(SpeechProviderFailure) as speech:
        SpeechAdapter("speech-contract", leaking).dispatch(object(), {}, threading.Event())
    assert leaky not in str(speech.value)
