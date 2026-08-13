"""HS-131-10 (Sol Amendment 3): the cardinality harness.

Counts TWO different things at TWO different seams and reconciles both against
the real kernel journal store (``kernel_operations`` / ``kernel_receipts``),
never against private bookkeeping alone:

* ``dispatch`` -- dispatched children, counted at ``InferenceRunner._dispatch``;
* the PHYSICAL LEAF -- counted inside the SDK/local-model/mesh/Whisper edge
  double itself (``chat.completions.create``, ``Llama.create_chat_completion``,
  the relay ``enqueue``, the Whisper backend's ``transcribe``).

Construction is deliberately NOT the physical counter. The first version of this
harness counted ``InferenceRunner._engine_factory`` calls and called them
"physical leaf attempts", which is false in the direction that matters: an
engine can be built and never reach a provider (``test_a_constructed_engine_...``
below builds one and proves ZERO attempts), so a green run proved only that the
runner had constructed something. ``engine_factory`` is still counted, as
CONSTRUCTIONS, because the gap between the two numbers is itself the proof.

Per DESIGN-HS-131-10.md #2 and Sol amendment 3, every scenario proves:

    child_operations == terminal_child_receipts                      (per attempt)
    physical_leaf_attempts == dispatched_children <= child_operations

A pre-dispatch refusal proves ONE child operation, ONE refused terminal
receipt, and ZERO physical leaf attempts. Retry/fallback proves one child, one
receipt, and one physical attempt PER attempt ordinal. Parent/session
operations and external-egress effect operations are asserted OUT of the
"inference.invoke" child cohort by operation name, and an egress receipt is
asserted causally linked to its invocation child without being counted as one.

Surfaces: the bare runner rig (test_inference_runner.py's harness, reproduced
here for the cheapest indeterminate/cancellation/pre-dispatch-refusal proofs),
plus three named product surfaces -- the dictation pipeline (Sol's OpenAI-
compatible ``response_format`` retry is the natural retry/fallback case),
Decision promotion (the cancellation-after-provider-return idiom), and manual
Workbench (the item-provider success/failure idiom).

Determinism: every wait uses a ``threading.Event`` handshake with a bounded
timeout (<=5s); no sleeps.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.deployment_revisions import capture_deployment_revision
from holdspeak.inference_targets import resolve_inference_target
from holdspeak.kernel.inference_runner import (
    InferenceRunner,
    InvocationRequest,
    ProviderIndeterminate,
    ServiceContract,
)
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind

pytestmark = pytest.mark.timeout(90, method="signal")

OWNER = Principal(PrincipalKind.OWNER, "cardinality-owner")


# --------------------------------------------------------------- instrument


class _Leaf:
    """The PHYSICAL counter: bumped at the network/model edge, nowhere else.

    Every fixture hands this to the innermost double it owns -- the fake SDK
    ``completions.create``, the fake ``Llama``, the relay queue, the Whisper
    backend -- so ``attempts`` counts requests that would have left the process
    (or entered a model), not objects that were constructed.
    """

    def __init__(self) -> None:
        self.attempts = 0

    def hit(self) -> None:
        self.attempts += 1


def _instrument(runner: InferenceRunner) -> dict[str, int]:
    """Count dispatched children, and (separately) engine CONSTRUCTIONS.

    Both wrappers are transparent pass-throughs onto the runner INSTANCE, and
    HS-131-10 gave every engine factory ONE calling convention
    (``factory(revision, *, warrant, context)``) that the runner applies
    unconditionally — there is no ``is build_intel_for_revision`` identity
    branch left to preserve. So counting here cannot change which factory runs,
    whether the dispatch context is minted, or whether it validates: an
    instrumented run and a bare run take exactly the same path.

    ``engine_factory`` is a CONSTRUCTION count and is never asserted as a
    physical attempt: that is what :class:`_Leaf` is for.
    """
    counts = {"engine_factory": 0, "dispatch": 0}
    real_factory = runner._engine_factory

    def factory(*args: Any, **kwargs: Any) -> Any:
        counts["engine_factory"] += 1
        return real_factory(*args, **kwargs)

    runner._engine_factory = factory
    real_dispatch = runner._dispatch

    def dispatch(*args: Any, **kwargs: Any) -> Any:
        counts["dispatch"] += 1
        return real_dispatch(*args, **kwargs)

    runner._dispatch = dispatch
    return counts


# ------------------------------------------------------------- journal reads


def _invoke_children(db: Database, parent_operation_id: str | None = None) -> list[dict[str, Any]]:
    """Real ``inference.invoke`` operation rows -- the ONLY child cohort."""
    with db._connection() as conn:
        if parent_operation_id is None:
            rows = conn.execute(
                "SELECT * FROM kernel_operations WHERE name='inference.invoke' ORDER BY created_at"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM kernel_operations WHERE name='inference.invoke'"
                " AND parent_operation_id=? ORDER BY created_at",
                (parent_operation_id,),
            ).fetchall()
    return [dict(row) for row in rows]


def _receipt(db: Database, operation_id: str) -> dict[str, Any] | None:
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM kernel_receipts WHERE operation_id=?", (operation_id,)
        ).fetchone()
    return None if row is None else dict(row)


def _operation(db: Database, operation_id: str) -> dict[str, Any] | None:
    with db._connection() as conn:
        row = conn.execute(
            "SELECT * FROM kernel_operations WHERE operation_id=?", (operation_id,)
        ).fetchone()
    return None if row is None else dict(row)


def _assert_reconciled(
    db: Database,
    *,
    parent_operation_id: str | None,
    counts: dict[str, int],
    leaf: _Leaf,
    expect_children: int,
    expect_physical: int | None = None,
) -> list[dict[str, Any]]:
    """The story's core equalities, read from the real store, not bookkeeping.

    ``expect_physical`` defaults to "every dispatched child reached its leaf",
    which is the production shape; a fixture that deliberately stops short of a
    provider passes the honest number and says why.
    """
    children = _invoke_children(db, parent_operation_id)
    assert len(children) == expect_children
    receipts = [_receipt(db, row["operation_id"]) for row in children]
    assert all(receipt is not None for receipt in receipts), "every child must have a terminal receipt"
    assert len(children) == len(receipts)  # child_operations == terminal_child_receipts
    physical = leaf.attempts
    expected = counts["dispatch"] if expect_physical is None else expect_physical
    assert physical == expected  # physical_leaf_attempts == dispatched_children
    assert physical <= counts["dispatch"] <= len(children)
    return children


# ---------------------------------------------------------------- bare rig


class _LeafEngine:
    """A stand-in for a provider engine whose ``run_prompt`` IS the model edge.

    The bare rig needs something at the bottom that can be counted; this is the
    smallest honest one. It counts BEFORE it decides to fail, because a provider
    that raises has still made its attempt (that is exactly what an
    indeterminate outcome means).
    """

    def __init__(self, leaf: _Leaf, result: str = "result", error: BaseException | None = None) -> None:
        self._leaf, self.result, self.error = leaf, result, error

    def run_prompt(self, *, system_prompt: str = "", user_prompt: str = "", **_: Any) -> str:
        self._leaf.hit()
        if self.error:
            raise self.error
        return self.result


class _Adapter:
    """The cheapest possible adapter: it dispatches THROUGH the engine's leaf.

    ``result``/``error`` keep the pre-HS-131-10 constructor working for the
    suites that import this rig (the provenance fence asks for a specific
    provider string), while the physical attempt now genuinely happens: the
    engine is reached first, and only then does the adapter shape the answer.
    """

    def __init__(self, result: Any = None, error: BaseException | None = None) -> None:
        self.result, self.error = result, error

    def dispatch(self, engine: Any, payload: Any, cancellation: Any) -> Any:
        text = engine.run_prompt(system_prompt="", user_prompt=str(payload))
        if self.error:
            raise self.error
        return text if self.result is None else self.result

    def cancel(self) -> str:
        return "cancelled"


class _LeaflessAdapter(_Adapter):
    """An adapter that answers WITHOUT touching the engine it was handed.

    Not a production shape — a deliberate fixture for the one proof that
    construction is not an attempt.
    """

    def dispatch(self, engine: Any, payload: Any, cancellation: Any) -> Any:
        return "answered without a provider"


class _RemoteAdapter(_Adapter):
    """A dispatch that carries a linked external-egress effect."""

    egress_destination = "cardinality.example.test"
    connector_id = "cardinality-provider"
    egress_data_classes = ("instruction",)


def _bare_rig(tmp_path: Path):
    db = Database(tmp_path / "bare.db")
    db.profiles.upsert(profile_id="local", name="Local", kind="onDevice", model_file="/model.gguf")
    revision = capture_deployment_revision(db, resolve_inference_target(db, "local"))
    broker = _configure(db)
    return db, broker, revision


def _bare_request(revision: Any, *, parent_operation_id: str = "", attempt_ordinal: int = 1) -> InvocationRequest:
    payload = {"probe": "cardinality", "attempt": attempt_ordinal}
    return InvocationRequest(
        deployment_revision=revision.id,
        definition_origin=ServiceContract.for_payload("cardinality-probe", "v1", payload),
        deadline_at=time.time() + 30,
        payload=payload,
        parent_operation_id=parent_operation_id,
        attempt_ordinal=attempt_ordinal,
    )


def _bare_request_named(revision: Any, invocation_id: str, *, attempt_ordinal: int = 1) -> InvocationRequest:
    """A bare request under a caller-chosen id — the id a cancellation can NAME."""
    payload = {"probe": "cardinality", "attempt": attempt_ordinal, "id": invocation_id}
    return InvocationRequest(
        deployment_revision=revision.id,
        definition_origin=ServiceContract.for_payload("cardinality-probe", "v1", payload),
        deadline_at=time.time() + 30,
        payload=payload,
        invocation_id=invocation_id,
        attempt_ordinal=attempt_ordinal,
    )


def _bare_runner(broker: Any, db: Any, *, engine_factory=None, leaf: _Leaf | None = None, error: BaseException | None = None) -> InferenceRunner:
    factory = engine_factory or (lambda _revision, **_: _LeafEngine(leaf or _Leaf(), error=error))
    return InferenceRunner(broker, db, engine_factory=factory, principal_provider=lambda: OWNER)


# =============================================================== SUCCESS
# Surface: manual Workbench (named product surface) -- one item, one child.


def test_success_workbench_one_item_is_one_child_one_receipt_one_physical_attempt(tmp_path, monkeypatch):
    """Scenario: success. Surface: manual Workbench."""
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db = Database(tmp_path / "workbench.db")
    profile = db.profiles.upsert(
        profile_id="wb-profile", name="Profile", kind="openAICompatible",
        base_url="http://wb-profile", model="wb-model",
    )
    recipe = db.recipes.upsert(
        recipe_id="wb-recipe", name="Runner", system_prompt="SYS", user_template="{input}",
    )
    workbench = db.workbenches.upsert(
        workbench_id="wb-run", name="Runner", recipe_id=recipe.id, profile_id=profile.id,
    )
    db.workbench_items.upsert(item_id="wb-item-1", workbench_id=workbench.id, title="Item 1", body="input 1")
    broker = _configure(db)

    leaf = _Leaf()
    broker.inference_runner._engine_factory = lambda _revision, **_: _LeafEngine(leaf, "provider output")
    counts = _instrument(broker.inference_runner)

    result = asyncio.run(WorkbenchRunner(db, broker).run(OWNER, workbench.id, memory_enabled=False))

    children = _assert_reconciled(
        db, parent_operation_id=result["parent_operation_id"], counts=counts, leaf=leaf,
        expect_children=1,
    )
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "succeeded"
    assert counts == {"engine_factory": 1, "dispatch": 1}
    # The parent itself is typed OUT of the child cohort by name.
    parent_row = _operation(db, result["parent_operation_id"])
    assert parent_row["name"] == "workbench.run" != "inference.invoke"


# =========================================================== PRE-DISPATCH REFUSAL
# Surface: bare runner rig (cheapest rig for a claim-time refusal).


def test_pre_dispatch_refusal_yields_one_child_one_refused_receipt_zero_physical_attempts(tmp_path):
    """Scenario: pre-dispatch refusal (parent not running at admission time).
    Surface: bare runner.

    The child IS admitted -- ``inference.invoke`` gets its own operation row --
    but the parent named in ``parent_operation_id`` was approved and never
    claimed/run, so the admission-time parent-liveness check refuses the child
    before authorization completes: ``ExecutorPlane``'s admission refusal path
    persists a real terminal receipt (``state=refused``,
    ``outcome=parent_operation_not_running``) BEFORE the runner ever resolves a
    revision, builds an engine, or calls dispatch -- exactly the
    zero-physical-attempt case Sol names. (The refused row's own
    ``parent_operation_id`` field is left empty by that early admission path --
    the refusal fires before parent linkage is persisted -- so the child cohort
    is read globally here rather than filtered by parent.)
    """
    db, broker, revision = _bare_rig(tmp_path)
    parent_raw = {
        "request_schema": 1, "request_id": "parent-not-running", "idempotency_key": "parent-not-running",
        "operation": {"name": "inference.run", "version": 1}, "target": {},
        "arguments": {
            "invocation_id": "parent-not-running", "definition_ref": "recipe:one", "definition_revision": "rev-1",
            "grounding_refs": [], "requested_target_id": "local", "deadline_at": time.time() + 30,
            "input_snapshot": {},
        },
    }
    parent = broker.submit(parent_raw, OWNER)
    parent = broker.decide(parent["operation_id"], "approve", parent["revision"], OWNER)
    parent_operation_id = parent["operation_id"]
    # Deliberately never claimed/run: the parent is "awaiting_execution", not
    # "running", so admission refuses the child before it can be authorized.
    assert _operation(db, parent_operation_id)["state"] != "running"

    leaf = _Leaf()
    runner = _bare_runner(broker, db, leaf=leaf)
    counts = _instrument(runner)
    outcome = runner.invoke(
        _bare_request(revision, parent_operation_id=parent_operation_id), _Adapter(),
    )

    assert outcome.outcome == "refused"
    children = _invoke_children(db)  # global: the refused row carries no parent link
    assert len(children) == 1
    assert children[0]["operation_id"] == outcome.operation_id
    receipt = _receipt(db, children[0]["operation_id"])
    assert receipt is not None and receipt["state"] == "refused"
    assert receipt["outcome"] == "parent_operation_not_running"
    assert leaf.attempts == 0  # ZERO physical attempts (Sol amendment 3)
    assert counts["engine_factory"] == 0  # nothing was even constructed
    assert counts["dispatch"] == 0
    assert counts["dispatch"] <= len(children)  # dispatched_children(0) <= child_operations(1)


# ================================================================ PROVIDER FAILURE
# Surface: manual Workbench.


def test_provider_failure_workbench_is_one_child_one_failed_receipt_one_physical_attempt(tmp_path):
    """Scenario: provider failure. Surface: manual Workbench."""
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db = Database(tmp_path / "workbench-fail.db")
    profile = db.profiles.upsert(
        profile_id="wb-fail-profile", name="Profile", kind="openAICompatible",
        base_url="http://wb-fail-profile", model="wb-model",
    )
    recipe = db.recipes.upsert(
        recipe_id="wb-fail-recipe", name="Runner", system_prompt="SYS", user_template="{input}",
    )
    workbench = db.workbenches.upsert(
        workbench_id="wb-fail-run", name="Runner", recipe_id=recipe.id, profile_id=profile.id,
    )
    db.workbench_items.upsert(item_id="wb-fail-item-1", workbench_id=workbench.id, title="Item 1", body="input 1")
    broker = _configure(db)

    leaf = _Leaf()
    broker.inference_runner._engine_factory = lambda _revision, **_: _LeafEngine(
        leaf, error=RuntimeError("provider said no")
    )
    counts = _instrument(broker.inference_runner)

    result = asyncio.run(WorkbenchRunner(db, broker).run(OWNER, workbench.id, memory_enabled=False))

    children = _assert_reconciled(
        db, parent_operation_id=result["parent_operation_id"], counts=counts, leaf=leaf,
        expect_children=1,
    )
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "failed"
    assert counts == {"engine_factory": 1, "dispatch": 1}
    assert leaf.attempts == 1  # the request reached the provider and it refused


# ==================================================================== CANCELLATION
# Surface: Decision promotion (named product surface: cancellation-after-provider-return).


def _accepted_meeting_decision(db: Database, decision_id: str) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decisions (
                   id, text, rationale, decided_at, date_basis, source_artifact_id,
                   source_meeting_id, source_state, lifecycle, created_at, updated_at,
                   last_modified, deleted
               ) VALUES (?, 'Use record-backed decisions.', 'One durable canon.',
                         '2026-08-07T00:00:00+00:00', 'meeting_date', 'artifact-cardinality',
                         'meeting-cardinality', 'linked', 'accepted', '2026-08-07T00:00:00+00:00',
                         '2026-08-07T00:00:00+00:00', '2026-08-07T00:00:00+00:00', 0)""",
            (decision_id,),
        )


def test_cancellation_after_provider_return_is_one_child_one_receipt_one_physical_attempt(tmp_path):
    """Scenario: cancellation (durable parent cancel lands while provider is in flight).

    Surface: Decision promotion. The child's provider work completed and EARNED
    a succeeded receipt; the parent cancellation elects PUBLICATION fencing
    instead. Reconciliation is at the child cohort: one admitted child, one
    (succeeded) terminal receipt, one physical attempt -- the parent's own
    ``cancelled`` receipt is a SEPARATE, non-child row.
    """
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
    from holdspeak.services.errors import ConflictError

    db = Database(tmp_path / "promotion-cardinality.db")
    _accepted_meeting_decision(db, "dec-cardinality")
    profile = db.profiles.upsert(
        profile_id="promotion-cardinality", name="Promotion", kind="openAICompatible",
        base_url="http://promotion-cardinality", model="promotion-model",
    )
    broker = _configure(db)
    owner = Principal(PrincipalKind.OWNER, "promotion-cardinality-owner")

    leaf = _Leaf()

    class CancellingIntel:
        def run_prompt(self, **_: Any) -> str:
            leaf.hit()
            with db._connection() as conn:
                parent_id = conn.execute(
                    "SELECT operation_id FROM kernel_parent_runs WHERE kind='decision.promotion-draft'"
                ).fetchone()[0]
            broker.parent_run_controller.cancel_by_operation_id(owner, parent_id)
            return "late draft that must not publish"

    broker.inference_runner._engine_factory = lambda _revision, **_: CancellingIntel()
    counts = _instrument(broker.inference_runner)
    service = DecisionLifecycleService(db, kernel=broker)

    with pytest.raises(ConflictError, match="decision_promotion_cancelled"):
        asyncio.run(service.draft_promoted_with_model(
            owner, "dec-cardinality", "note", {"inference_target_id": profile.id},
        ))

    with db._connection() as conn:
        parent_id = conn.execute(
            "SELECT operation_id FROM kernel_parent_runs WHERE kind='decision.promotion-draft'"
        ).fetchone()[0]

    children = _assert_reconciled(
        db, parent_operation_id=parent_id, counts=counts, leaf=leaf, expect_children=1,
    )
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "succeeded"
    # The parent's OWN receipt is cancelled -- a separate row, never counted as
    # a child, and never conflated with the child's earned outcome.
    parent_receipt = _receipt(db, parent_id)
    assert parent_receipt is not None and parent_receipt["outcome"] == "cancelled"
    parent_row = _operation(db, parent_id)
    assert parent_row["name"] != "inference.invoke"


def test_cancellation_reaches_the_adapter_before_publish_bare_rig(tmp_path):
    """Scenario: cancellation (mid-dispatch, adapter-side). Surface: bare runner.

    Cheaper than a product surface for proving the runner-level cancel
    machinery: a blocked adapter, released only after ``cancel()`` is
    observed, via a ``threading.Event`` handshake (bounded, no sleeps).
    """
    import threading

    db, broker, revision = _bare_rig(tmp_path)
    started = threading.Event()
    release = threading.Event()
    leaf = _Leaf()

    class _Slow(_Adapter):
        """A blocked provider whose CANCEL aborts the in-flight request.

        Releasing from the test's main thread deadlocks: the cancel election
        waits for the dispatcher to leave ``DISPATCHING`` while the dispatcher
        waits for the release, so the wait times out and the "dispatch" never
        reaches a provider at all. (The previous version of this test did
        exactly that, and passed, because the harness counted engine
        CONSTRUCTIONS and called them physical attempts. The leaf counter is
        what caught it.) A real adapter's ``cancel`` unblocks its own request,
        so this one does too.
        """

        def dispatch(self, engine: Any, payload: Any, cancellation: Any) -> Any:
            started.set()
            assert release.wait(5), "cancel never released the in-flight request"
            return engine.run_prompt(system_prompt="", user_prompt="late output")

        def cancel(self) -> str:
            release.set()
            return "cancelled"

    runner = _bare_runner(broker, db, leaf=leaf)
    counts = _instrument(runner)
    result: list[Any] = []
    thread = threading.Thread(
        target=lambda: result.append(
            runner.invoke(
                InvocationRequest(**{**_bare_request(revision).__dict__, "invocation_id": "cardinality_cancel"}),
                _Slow(),
            )
        )
    )
    thread.start()
    assert started.wait(5), "dispatch never started"
    assert runner.cancel("cardinality_cancel") == "cancelled"
    release.set()  # belt and braces; the adapter's own cancel already released it
    thread.join(5)
    assert not thread.is_alive(), "the dispatch thread never finished"
    assert result and result[0].outcome == "cancelled"

    children = _assert_reconciled(
        db, parent_operation_id=None, counts=counts, leaf=leaf, expect_children=1,
    )
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "cancelled"
    assert counts == {"engine_factory": 1, "dispatch": 1}


# ==================================================================== RETRY / FALLBACK
# Surface: dictation pipeline (named product surface): the OpenAI-compatible
# ``response_format`` compatibility retry is Sol's named natural case.


def test_retry_fallback_dictation_response_format_is_two_children_two_receipts_two_physical_attempts(
    tmp_path, monkeypatch
):
    """Scenario: retry/fallback. Surface: dictation pipeline.

    Each attempt (the rejected ``response_format`` leg, then the compatibility
    retry) is a SEPARATE ``inference.invoke`` child with its own attempt
    ordinal, receipt, and physical dispatch -- never one logical retry hiding
    inside a single admitted child.
    """
    import json

    from holdspeak.config import Config
    from holdspeak.plugins.dictation.grammars import StructuredOutputSchema
    from holdspeak.plugins.dictation.runtime_openai_compatible import OpenAICompatibleRuntime
    from holdspeak.speech_session import AdmittedDictationRuntime, admit_hold_session

    db = Database(tmp_path / "dictation-cardinality.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    db.profiles.upsert(
        profile_id="prof_cardinality", name="prof_cardinality", kind="openAICompatible",
        base_url="http://127.0.0.1:1234/v1", model="qwen-local",
    )
    broker = _configure(db)
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: object()
    )
    counts = _instrument(broker.inference_runner)

    config = Config()
    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["intent-router", "project-rewriter"]
    config.dictation.runtime.profile_id = "prof_cardinality"
    session = admit_hold_session(config_snapshot=config)

    leaf = _Leaf()

    class _RejectingCompletions:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def create(self, **kwargs: Any) -> dict[str, Any]:
            leaf.hit()
            self.calls.append(kwargs)
            if "response_format" in kwargs:
                raise _BadRequest("unsupported response_format")
            return {
                "choices": [{"message": {"content": json.dumps(
                    {"matched": True, "block_id": "ai_prompt_buildout", "confidence": 0.8, "extras": {}}
                )}}]
            }

    class _BadRequest(Exception):
        __name__ = "BadRequestError"

    completions = _RejectingCompletions()

    class _Client:
        def __init__(self, **kwargs: Any) -> None:
            self.chat = type("_Chat", (), {"completions": completions})()

    backend = OpenAICompatibleRuntime(
        model="qwen-local", base_url="http://127.0.0.1:1234/v1", api_key_env="", client_factory=_Client,
    )
    schema = StructuredOutputSchema(
        block_ids=("ai_prompt_buildout",), extras_per_block={"ai_prompt_buildout": {}},
    )
    runtime = AdmittedDictationRuntime(backend, session.provider())

    result = runtime.classify("CARDINALITY_RETRY_PROBE", schema, max_tokens=64, temperature=0.0)

    assert result["block_id"] == "ai_prompt_buildout"
    assert len(completions.calls) == 2  # two REAL requests to the endpoint

    children = _assert_reconciled(
        db, parent_operation_id=session.operation_id, counts=counts, leaf=leaf,
        expect_children=2,
    )
    outcomes = [_receipt(db, row["operation_id"])["outcome"] for row in children]
    assert outcomes == ["failed", "succeeded"]  # one per attempt, in attempt order
    assert [row["parent_operation_id"] for row in children] == [session.operation_id, session.operation_id]
    assert counts == {"engine_factory": 2, "dispatch": 2}


# =================================================================== INDETERMINATE
# Surface: bare runner rig (cheapest rig for a provider that cannot report).


def test_indeterminate_recovery_bare_rig_is_one_child_one_indeterminate_receipt(tmp_path):
    """Scenario: indeterminate recovery. Surface: bare runner.

    A provider that raises ``ProviderIndeterminate`` still gets ONE admitted
    child and ONE terminal (indeterminate) receipt -- the runner's finish path
    persists a real receipt row rather than leaving the child open.
    """
    db, broker, revision = _bare_rig(tmp_path)
    leaf = _Leaf()
    runner = _bare_runner(broker, db, leaf=leaf, error=ProviderIndeterminate())
    counts = _instrument(runner)

    outcome = runner.invoke(_bare_request(revision), _Adapter())

    assert outcome.outcome == "indeterminate"
    children = _assert_reconciled(
        db, parent_operation_id=None, counts=counts, leaf=leaf, expect_children=1,
    )
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "indeterminate"
    assert counts == {"engine_factory": 1, "dispatch": 1}
    # The attempt was PHYSICAL: "indeterminate" means the provider was reached
    # and could not report, which is precisely why it is not a refusal.
    assert leaf.attempts == 1


# ============================================================ PARENT/EGRESS TYPING


def test_parent_and_egress_operations_are_typed_out_of_the_child_cohort(tmp_path):
    """The child cohort is EXACTLY ``inference.invoke`` rows.

    A parent operation (a different name entirely) and an external-egress
    effect operation (causally linked to, but distinct from, its invocation
    child) must never inflate ``child_operations``. The egress receipt is
    asserted causally linked to the invocation child via ``parent_operation_id``
    but is never counted among the child's own terminal receipts.
    """
    db, broker, _revision = _bare_rig(tmp_path)
    db.profiles.upsert(
        profile_id="remote-cardinality", name="Remote", kind="openAICompatible",
        base_url="https://cardinality.example.test/v1", model="remote-model",
    )
    remote_revision = capture_deployment_revision(db, resolve_inference_target(db, "remote-cardinality"))
    leaf = _Leaf()
    runner = _bare_runner(broker, db, leaf=leaf)
    counts = _instrument(runner)

    outcome = runner.invoke(_bare_request(remote_revision), _RemoteAdapter())

    assert outcome.outcome == "succeeded"
    # Exactly one inference.invoke child -- the egress effect does NOT count.
    children = _invoke_children(db, None)
    assert len(children) == 1
    assert counts == {"engine_factory": 1, "dispatch": 1}
    assert leaf.attempts == 1  # one physical attempt, one child, one egress effect

    events = broker.events(0, {}, OWNER)["events"]
    egress_admission = next(event for event in events if "egress:cardinality.example.test" in event["refs"])
    egress = _operation(db, egress_admission["operation_id"])
    assert egress is not None
    assert egress["name"] == "external.egress" != "inference.invoke"
    assert egress["parent_operation_id"] == outcome.operation_id  # causally linked to the child
    egress_receipt = _receipt(db, egress["operation_id"])
    assert egress_receipt is not None and egress_receipt["outcome"] == "succeeded"
    # The egress receipt is a SEPARATE row from the child's own terminal receipt.
    child_receipt = _receipt(db, outcome.operation_id)
    assert child_receipt is not None
    assert egress_receipt["operation_id"] != child_receipt["operation_id"]
    # Re-querying the child cohort after the egress effect still yields exactly
    # the one inference.invoke row: the egress operation is typed out by name.
    assert len(_invoke_children(db, None)) == 1


# ============================================ CONSTRUCTION IS NOT AN ATTEMPT


def test_a_constructed_engine_that_never_reaches_a_provider_counts_zero_physical(tmp_path):
    """The proof that the engine factory cannot BE the physical counter.

    The runner resolves the revision, mints the context, and constructs an
    engine — one ``engine_factory`` call — and then the adapter answers without
    touching it. Nothing was sent anywhere, so the honest physical count is
    ZERO while the child, its dispatch, and its receipt are all real. Counting
    constructions would report one attempt here, which is exactly the number
    that lets a "physical cardinality" proof pass with no physics in it.
    """
    db, broker, revision = _bare_rig(tmp_path)
    leaf = _Leaf()
    runner = _bare_runner(broker, db, leaf=leaf)
    counts = _instrument(runner)

    outcome = runner.invoke(_bare_request(revision), _LeaflessAdapter())

    assert outcome.outcome == "succeeded"
    children = _assert_reconciled(
        db, parent_operation_id=None, counts=counts, leaf=leaf, expect_children=1,
        expect_physical=0,
    )
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "succeeded"
    assert counts == {"engine_factory": 1, "dispatch": 1}
    assert leaf.attempts == 0


# ================================================= PRODUCTION LEAVES: CLOUD SDK


def _endpoint_revision(db: Database, profile_id: str, base_url: str) -> Any:
    db.profiles.upsert(
        profile_id=profile_id, name=profile_id, kind="openAICompatible",
        base_url=base_url, model="leaf-model",
    )
    return capture_deployment_revision(db, resolve_inference_target(db, profile_id))


def _fake_openai(leaf: _Leaf, calls: list[dict[str, Any]], *, reject_max_tokens: bool = False):
    """A double at the WIRE: the SDK client, counted at `chat.completions.create`."""
    from types import SimpleNamespace

    class _Completions:
        def create(self, **kwargs: Any) -> Any:
            leaf.hit()
            calls.append(kwargs)
            if reject_max_tokens and "max_tokens" in kwargs:
                raise TypeError("unknown argument: max_tokens")
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="cloud text"))]
            )

    class _Client:
        def __init__(self, **kwargs: Any) -> None:
            self.chat = SimpleNamespace(completions=_Completions())

    return _Client


def _prompt_request(revision: Any, contract: str, invocation_id: str = "") -> InvocationRequest:
    payload = {"system_prompt": "s", "user_prompt": "u"}
    return InvocationRequest(
        deployment_revision=revision.id,
        definition_origin=ServiceContract.for_payload(contract, "v1", payload),
        deadline_at=time.time() + 30,
        payload=payload,
        invocation_id=invocation_id,
    )


def test_production_cloud_sdk_leaf_is_one_create_one_child_one_receipt(tmp_path, monkeypatch):
    """The real `MeetingIntel` cloud branch, stubbed only at the SDK boundary."""
    import holdspeak.intel as intel_pkg
    from holdspeak.intel.engine import MeetingIntel, forget_endpoint_dialects
    from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter

    forget_endpoint_dialects()
    db, broker, _revision = _bare_rig(tmp_path)
    revision = _endpoint_revision(db, "cloud-leaf", "https://cloud-leaf.example.test/v1")
    leaf: _Leaf = _Leaf()
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(intel_pkg, "OpenAI", _fake_openai(leaf, calls))

    def factory(_revision: Any, **_: Any) -> Any:
        return MeetingIntel(
            provider="cloud", cloud_model="leaf-model",
            cloud_base_url="https://cloud-leaf.example.test/v1",
            cloud_api_key_env="HOLDSPEAK_CLOUD_LEAF_KEY",
        )

    runner = _bare_runner(broker, db, engine_factory=factory)
    counts = _instrument(runner)

    outcome = runner.invoke(
        _prompt_request(revision, "cardinality-cloud"), CanonicalPromptAdapter()
    )

    assert outcome.outcome == "succeeded"
    children = _assert_reconciled(
        db, parent_operation_id=None, counts=counts, leaf=leaf, expect_children=1,
    )
    assert len(calls) == 1 and "max_tokens" in calls[0]
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "succeeded"


def test_the_cloud_dialect_fallback_is_two_creates_two_children_two_receipts(tmp_path, monkeypatch):
    """Sol Amendment 3, at the site that violated it (HS-131-10 Terra finding B).

    ``MeetingIntel`` used to answer a ``max_tokens`` rejection with a SECOND
    ``chat.completions.create`` inside the same call: two physical requests, one
    child, one receipt. The engine now performs exactly one request and NAMES
    the dialect; the runner admits the retry as its own child with the next
    attempt ordinal, so the journal counts what the network saw.
    """
    import holdspeak.intel as intel_pkg
    from holdspeak.intel.engine import MeetingIntel, forget_endpoint_dialects
    from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter

    forget_endpoint_dialects()
    db, broker, _revision = _bare_rig(tmp_path)
    revision = _endpoint_revision(db, "dialect-leaf", "https://dialect-leaf.example.test/v1")
    leaf: _Leaf = _Leaf()
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(intel_pkg, "OpenAI", _fake_openai(leaf, calls, reject_max_tokens=True))

    def factory(_revision: Any, **_: Any) -> Any:
        return MeetingIntel(
            provider="cloud", cloud_model="leaf-model",
            cloud_base_url="https://dialect-leaf.example.test/v1",
            cloud_api_key_env="HOLDSPEAK_DIALECT_LEAF_KEY",
        )

    runner = _bare_runner(broker, db, engine_factory=factory)
    counts = _instrument(runner)

    outcome = runner.invoke(
        _prompt_request(revision, "cardinality-dialect", "dialect_probe"),
        CanonicalPromptAdapter(),
    )

    try:
        assert outcome.outcome == "succeeded"
        # TWO real requests to the endpoint: the rejected one, then the dialect one.
        assert len(calls) == 2
        assert "max_tokens" in calls[0] and "max_completion_tokens" not in calls[0]
        assert "max_completion_tokens" in calls[1] and "max_tokens" not in calls[1]
        children = _assert_reconciled(
            db, parent_operation_id=None, counts=counts, leaf=leaf, expect_children=2,
        )
        outcomes = [_receipt(db, row["operation_id"])["outcome"] for row in children]
        assert outcomes == ["failed", "succeeded"]  # one receipt per physical attempt
        assert [row["native_id"] for row in children] == ["dialect_probe", "dialect_probe_r2"]
        assert counts == {"engine_factory": 2, "dispatch": 2}
    finally:
        forget_endpoint_dialects()


# =============================================== PRODUCTION LEAVES: LOCAL LLAMA


def test_production_local_llama_leaf_is_one_completion_one_child_one_receipt(tmp_path, monkeypatch):
    """The real `MeetingIntel` local branch, stubbed at the llama.cpp boundary."""
    import holdspeak.intel as intel_pkg
    from holdspeak.intel.engine import MeetingIntel
    from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter

    db, broker, revision = _bare_rig(tmp_path)
    model_file = tmp_path / "leaf-model.gguf"
    model_file.write_bytes(b"gguf")
    leaf = _Leaf()

    class _Llama:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        def create_chat_completion(self, **_: Any) -> dict[str, Any]:
            leaf.hit()
            return {"choices": [{"message": {"content": "local text"}}]}

    monkeypatch.setattr(intel_pkg, "Llama", _Llama)
    runner = _bare_runner(
        broker, db,
        engine_factory=lambda _revision, **_: MeetingIntel(
            provider="local", model_path=str(model_file)
        ),
    )
    counts = _instrument(runner)

    outcome = runner.invoke(
        _prompt_request(revision, "cardinality-local"), CanonicalPromptAdapter()
    )

    assert outcome.outcome == "succeeded"
    _assert_reconciled(
        db, parent_operation_id=None, counts=counts, leaf=leaf, expect_children=1,
    )


# ================================================= PRODUCTION LEAVES: MESH SEND


def test_production_mesh_sender_leaf_is_one_enqueue_one_child_one_receipt(tmp_path):
    """The real `MeshRelayIntel`, stubbed at the relay queue (the mesh wire)."""
    from datetime import datetime, timedelta
    from types import SimpleNamespace

    from holdspeak.intel.mesh_relay import MeshRelayIntel
    from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter

    db, broker, _revision = _bare_rig(tmp_path)
    db.profiles.upsert(
        profile_id="mesh-leaf", name="Mesh", kind="meshNode", node="node-leaf", model="mesh-model",
    )
    revision = capture_deployment_revision(db, resolve_inference_target(db, "mesh-leaf"))
    leaf = _Leaf()

    class _Relay:
        """The hub relay queue: `enqueue` is the moment the job leaves this hub."""

        def __init__(self) -> None:
            self.envelopes: list[dict[str, Any]] = []

        def worker_last_seen(self, node: str) -> Any:
            return datetime.now() - timedelta(seconds=1)

        def enqueue(self, **kwargs: Any) -> Any:
            leaf.hit()
            self.envelopes.append(kwargs)
            return SimpleNamespace(id="mesh-job-1")

        def get(self, job_id: str, now: Any = None) -> Any:
            return SimpleNamespace(id=job_id, status="completed", result="mesh text", error="")

    relay = _Relay()

    def factory(frozen: Any, *, warrant: Any = None, context: Any = None) -> Any:
        return MeshRelayIntel(
            node="node-leaf", model_hint="mesh-model", relay=relay,
            deployment_revision=frozen, warrant=dict(warrant or {}),
        )

    runner = _bare_runner(broker, db, engine_factory=factory)
    counts = _instrument(runner)

    outcome = runner.invoke(
        _prompt_request(revision, "cardinality-mesh"), CanonicalPromptAdapter()
    )

    assert outcome.outcome == "succeeded"
    children = _assert_reconciled(
        db, parent_operation_id=None, counts=counts, leaf=leaf, expect_children=1,
    )
    # The envelope that crossed the wire carries THIS child's frozen revision.
    assert relay.envelopes[0]["envelope"]["deployment_revision"]["id"] == revision.id
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "succeeded"


# ==================================================== PRODUCTION LEAVES: WHISPER


def test_production_whisper_leaf_is_one_transcribe_one_child_one_receipt(tmp_path, monkeypatch):
    """The real `Transcriber`, stubbed at the Whisper backend itself.

    Transcription is admitted per utterance (HS-131-09), so the leaf that runs
    the model has its own child and terminal receipt exactly like a completion.
    """
    import numpy as np

    import holdspeak.transcribe as transcribe_mod
    from holdspeak.config import Config
    from holdspeak.speech_session import admit_hold_session

    db = Database(tmp_path / "whisper-cardinality.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    broker = _configure(db)
    leaf = _Leaf()

    class _Backend:
        device = "cpu"
        compute_type = "int8"
        loaded = True

        def __init__(self, **_: Any) -> None:
            pass

        def ensure_loaded(self, admission: Any) -> None:
            return None  # preload children are proven in the HS-131-09 suite

        def transcribe(self, audio_array: Any) -> str:
            leaf.hit()
            return "whisper text"

    monkeypatch.setattr(transcribe_mod, "_resolve_backend", lambda _b: "mlx")
    monkeypatch.setattr(transcribe_mod, "_MlxTranscriber", _Backend)
    counts = _instrument(broker.inference_runner)

    session = admit_hold_session(config_snapshot=Config())
    transcriber = transcribe_mod.Transcriber(model_name="base")

    text = transcriber.transcribe(
        np.zeros(16000, dtype="float32"), admission=session.transcription()
    )

    assert text == "whisper text"
    children = _invoke_children(db, session.operation_id)
    receipts = [_receipt(db, row["operation_id"]) for row in children]

    # The full equality, not an inequality (HS-131-10 round 2, Terra blocker 9).
    # This asserted only ``dispatch <= children``, which a run that dispatched
    # ZERO times would also satisfy — so the proof that transcription is admitted
    # LIKE a completion was weaker than the physics it was describing. The real
    # shape here is exactly one of each, all the way down.
    assert leaf.attempts == counts["dispatch"] == len(children) == len(receipts) == 1
    assert [receipt["outcome"] for receipt in receipts] == ["succeeded"]
    # Preload/warmup remain SEPARATE children (proved in the HS-131-09 suite);
    # this backend's `ensure_loaded` is a no-op precisely so this count is the
    # transcribe leaf alone.
    assert counts["engine_factory"] == 1


def test_the_dispatch_context_is_minted_from_the_CHILD_claim_not_a_parent(tmp_path):
    """The witness proof, end to end, plus the child-warrant fix (Terra finding A).

    Two things are true here and neither was before:

    * the context the factory receives was minted from a witness that
      ``ExecutorPlane.claim`` issued — there is no other way to obtain one, so
      every green run of this suite is also a proof that admission happened;
    * its authenticated basis is THIS CHILD's warrant. The claim's ancestor walk
      used to assign through the same local name, so a claimed child was handed
      back its last PARENT's warrant, and everything downstream (the mesh
      envelope, the context basis) was bound to the wrong operation.
    """
    from holdspeak.kernel.claim_witness import ClaimWitness
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db = Database(tmp_path / "witness.db")
    profile = db.profiles.upsert(
        profile_id="witness-profile", name="Profile", kind="openAICompatible",
        base_url="http://witness-profile", model="wb-model",
    )
    recipe = db.recipes.upsert(
        recipe_id="witness-recipe", name="Runner", system_prompt="SYS", user_template="{input}",
    )
    workbench = db.workbenches.upsert(
        workbench_id="witness-run", name="Runner", recipe_id=recipe.id, profile_id=profile.id,
    )
    db.workbench_items.upsert(
        item_id="witness-item-1", workbench_id=workbench.id, title="Item 1", body="input 1",
    )
    broker = _configure(db)
    leaf = _Leaf()
    seen: dict[str, Any] = {}

    def factory(_revision: Any, *, warrant: Any = None, context: Any = None) -> Any:
        seen["context"], seen["warrant"] = context, dict(warrant or {})
        return _LeafEngine(leaf, "provider output")

    broker.inference_runner._engine_factory = factory
    counts = _instrument(broker.inference_runner)

    result = asyncio.run(WorkbenchRunner(db, broker).run(OWNER, workbench.id, memory_enabled=False))

    children = _assert_reconciled(
        db, parent_operation_id=result["parent_operation_id"], counts=counts, leaf=leaf,
        expect_children=1,
    )
    child_id = children[0]["operation_id"]
    child_warrant = broker.store.operation(child_id)["warrant"]
    parent_warrant = broker.store.operation(result["parent_operation_id"])["warrant"]

    assert seen["context"].operation_id == child_id  # the CHILD it just claimed
    assert seen["warrant"] == dict(child_warrant)
    assert seen["context"].warrant_basis == str(child_warrant["signature"])
    assert str(child_warrant["signature"]) != str(parent_warrant["signature"])
    # The witness itself is spent: one claim mints exactly one context.
    from holdspeak.kernel.claim_witness import consume_claim_witness
    from holdspeak.kernel.model import KernelRefused as _Refused

    stale = ClaimWitness.__new__(ClaimWitness)
    with pytest.raises(_Refused):
        consume_claim_witness(stale)


# ======================================================= ROUND 2: THE REPAIRS
# Six defects Terra's hostile pass found in the first repair round. Each test
# below is the probe that found one, made permanent.


def _stream_openai(leaf: _Leaf, calls: list[dict[str, Any]], *, reject_max_tokens: bool = False):
    """A wire double that answers BOTH dialects and streams (Terra blocker 1).

    `_fake_openai` returns a non-iterable object, so it can only model the
    non-streaming leg. The dialect signal has to survive the STREAMING path too:
    `_analyze_stream` opens the stream inside a generator, which is a different
    unwinding path through the same sanitizing adapter.
    """
    from types import SimpleNamespace

    def _chunk(text: str) -> Any:
        return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])

    class _Completions:
        def create(self, **kwargs: Any) -> Any:
            leaf.hit()
            calls.append(kwargs)
            if reject_max_tokens and "max_tokens" in kwargs:
                raise TypeError("unknown argument: max_tokens")
            if kwargs.get("stream"):
                return iter([_chunk('{"topics": [], "action_items": [], "summary": "s"}')])
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="cloud text"))]
            )

    class _Client:
        def __init__(self, **kwargs: Any) -> None:
            self.chat = SimpleNamespace(completions=_Completions())

    return _Client


@pytest.mark.parametrize("form", ["text", "stream"])
def test_the_meeting_adapter_lets_the_dialect_signal_reach_the_runner(form, tmp_path, monkeypatch):
    """Terra blocker 1: the sanitizer swallowed a KERNEL signal, not provider text.

    `MeetingAdapter.dispatch` wraps its provider call in
    ``except BaseException -> MeetingProviderFailure`` so no transcript fragment,
    echoed prompt, or endpoint body can reach a journal field. That is right about
    CONTENT and was wrong about CONTROL: it also caught
    `ProviderCompatibilityRetry`, so a compatible endpoint produced ONE physical
    request, ONE `failed` receipt, and no second child — the runner never learned
    a retry was warranted, and the user saw a working endpoint reported broken.

    Proved for both dialect-bearing legs, because they unwind differently: the
    text leg raises out of a call, the streaming leg out of a generator.
    """
    import holdspeak.intel as intel_pkg
    from holdspeak.intel.engine import MeetingIntel, forget_endpoint_dialects
    from holdspeak.meeting_session.intel_child import MeetingAdapter

    forget_endpoint_dialects()
    db, broker, _revision = _bare_rig(tmp_path)
    base_url = f"https://meeting-{form}.example.test/v1"
    revision = _endpoint_revision(db, f"meeting-{form}", base_url)
    leaf: _Leaf = _Leaf()
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        intel_pkg, "OpenAI", _stream_openai(leaf, calls, reject_max_tokens=True)
    )

    def factory(_revision: Any, **_: Any) -> Any:
        return MeetingIntel(
            provider="cloud", cloud_model="leaf-model", cloud_base_url=base_url,
            cloud_api_key_env="HOLDSPEAK_DIALECT_LEAF_KEY",
        )

    if form == "text":
        def call(engine: Any, _payload: Any, _cancellation: Any) -> Any:
            return engine.run_prompt(system_prompt="s", user_prompt="u")
    else:
        def call(engine: Any, _payload: Any, _cancellation: Any) -> Any:
            return list(engine.analyze("stream transcript", stream=True))

    contexts: list[Any] = []

    def recording_factory(_revision: Any, **kwargs: Any) -> Any:
        contexts.append(kwargs["context"])
        return factory(_revision, **kwargs)

    runner = _bare_runner(broker, db, engine_factory=recording_factory)
    counts = _instrument(runner)

    try:
        outcome = runner.invoke(
            _prompt_request(revision, f"meeting-{form}", f"meeting_{form}"),
            MeetingAdapter(f"meeting-adapter-{form}", call),
        )

        assert outcome.outcome == "succeeded"
        # TWO physical requests left the process, in two dialects.
        assert len(calls) == 2
        assert "max_tokens" in calls[0] and "max_completion_tokens" not in calls[0]
        assert "max_completion_tokens" in calls[1] and "max_tokens" not in calls[1]
        # ...and the journal counts what the network saw.
        children = _assert_reconciled(
            db, parent_operation_id=None, counts=counts, leaf=leaf, expect_children=2,
        )
        assert [row["native_id"] for row in children] == [
            f"meeting_{form}", f"meeting_{form}_r2"
        ]
        assert [
            _receipt(db, row["operation_id"])["outcome"] for row in children
        ] == ["failed", "succeeded"]
        # Two DISTINCT immutable receipts, and two distinct native ids.
        assert len({row["operation_id"] for row in children}) == 2
        # Attempt ordinals, read from the contexts the runner MINTED for each
        # claimed child (`kernel_operations` stores no arguments), and each bound
        # to its own operation.
        assert [context.attempt_ordinal for context in contexts] == [1, 2]
        assert [context.operation_id for context in contexts] == [
            row["operation_id"] for row in children
        ]
        # Same frozen revision and destination for both attempts...
        assert {context.revision_id for context in contexts} == {revision.id}
        assert len({context.destination_id for context in contexts}) == 1
        assert {row["target_ref"] for row in children} == {
            f"deployment-revision:{revision.id}"
        }
        # ...and the same causal parent.
        assert len({str(row["parent_operation_id"] or "") for row in children}) == 1
        assert counts == {"engine_factory": 2, "dispatch": 2}
    finally:
        forget_endpoint_dialects()


def test_a_successful_retry_stages_against_the_child_that_succeeded(tmp_path, monkeypatch):
    """Terra blocker 2: the winning attempt published under the losing child.

    `InferenceRunner.invoke` reused the publisher the caller built around the
    FIRST invocation id. `ProjectionStager.stage` resolves its operation by
    ``native_id``, so the retry that SUCCEEDED staged against the child that
    FAILED; finalization then read that child's `failed` receipt and discarded
    the only output the run produced. Two real requests, one honest receipt each,
    and nothing published.
    """
    import holdspeak.intel as intel_pkg
    from holdspeak.intel.engine import MeetingIntel, forget_endpoint_dialects
    from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter

    forget_endpoint_dialects()
    db, broker, _revision = _bare_rig(tmp_path)
    base_url = "https://retry-publication.example.test/v1"
    revision = _endpoint_revision(db, "retry-publication", base_url)
    leaf: _Leaf = _Leaf()
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(intel_pkg, "OpenAI", _fake_openai(leaf, calls, reject_max_tokens=True))

    published: list[Mapping[str, Any]] = []

    def materialize(conn: Any, stage: Any, permit: Any) -> Mapping[str, Any]:
        permit.use(conn)
        published.append(dict(stage.projection))
        return dict(stage.projection)

    broker.projection_stager.register("retry-publication-probe", materialize)

    def factory(_revision: Any, **_: Any) -> Any:
        return MeetingIntel(
            provider="cloud", cloud_model="leaf-model", cloud_base_url=base_url,
            cloud_api_key_env="HOLDSPEAK_DIALECT_LEAF_KEY",
        )

    runner = _bare_runner(broker, db, engine_factory=factory)
    first_id = "retry_publication"
    publisher = broker.projection_stager.publisher(
        first_id, "retry-publication-probe", lambda output: {"output": str(output)}
    )

    try:
        outcome = runner.invoke(
            _prompt_request(revision, "retry-publication-probe", first_id),
            CanonicalPromptAdapter(),
            publish=publisher,
        )

        assert outcome.outcome == "succeeded" and len(calls) == 2
        children = _invoke_children(db)
        assert [row["native_id"] for row in children] == [first_id, f"{first_id}_r2"]
        assert [
            _receipt(db, row["operation_id"])["outcome"] for row in children
        ] == ["failed", "succeeded"]
        winner = children[1]["operation_id"]
        assert outcome.operation_id == winner

        # The FAILED first attempt staged nothing at all; only the winner did.
        assert broker.projection_stager.get(first_id) is None
        stage = broker.projection_stager.get(f"{first_id}_r2")
        assert stage is not None and stage.operation_id == winner
        # The result ref is the stage's own — never a fabricated one.
        assert outcome.result_ref == stage.result_ref
        assert _receipt(db, winner)["result_ref"] == stage.result_ref

        # A caller that only remembers the id it asked for still publishes, ONCE,
        # and publishes the WINNING attempt's staged projection.
        assert broker.projection_stager.finalize(first_id) == dict(stage.projection)
        assert published == [dict(stage.projection)]
        assert "cloud text" in str(stage.projection["output"])
        assert broker.projection_stager.get(f"{first_id}_r2").state == "PUBLISHED"
        assert broker.projection_stager.finalize(first_id) == dict(stage.projection)
        assert len(published) == 1, "finalization published twice"
    finally:
        forget_endpoint_dialects()


class _DialectThenSucceed:
    """Signals a dialect mismatch once, then answers. Counts real dispatches."""

    def __init__(self) -> None:
        self.dispatches = 0

    def dispatch(self, engine: Any, payload: Any, cancellation: Any) -> Any:
        self.dispatches += 1
        if self.dispatches == 1:
            from holdspeak.kernel.provider_signals import ProviderCompatibilityRetry

            raise ProviderCompatibilityRetry("max_completion_tokens")
        return "retry output"

    def cancel(self) -> str:
        return "cancelled"


def test_a_cancellation_during_the_retry_handoff_stops_every_later_attempt(tmp_path):
    """Terra blocker 3: cancel landed in the gap between attempts and was ignored.

    Attempt one terminalizes `failed` on a dialect signal and leaves the runner's
    active registry. For an instant nothing is registered under the id the caller
    holds, so `cancel(original_id)` fell through to "read whatever receipt
    exists", answered `failed` — and `_r2` then dispatched and PUBLISHED after the
    caller had been told the work was over.

    Deterministic: the test releases the handoff only after `cancel` has returned.
    No sleeps.
    """
    import threading

    import holdspeak.kernel.inference_runner as runner_module

    db, broker, revision = _bare_rig(tmp_path)
    runner = _bare_runner(broker, db, engine_factory=lambda _revision, **_: object())
    adapter = _DialectThenSucceed()
    publications: list[Any] = []
    entered, release = threading.Event(), threading.Event()
    original = runner_module.compatibility_follow_up

    def paused_follow_up(request: Any, invocation_id: str) -> Any:
        entered.set()
        assert release.wait(5), "the test never released the handoff"
        return original(request, invocation_id)

    runner_module.compatibility_follow_up = paused_follow_up
    result: list[Any] = []
    try:
        worker = threading.Thread(
            target=lambda: result.append(
                runner.invoke(
                    _bare_request_named(revision, "retry_cancel_handoff"),
                    adapter,
                    publish=lambda output: publications.append(output) or "result:handoff",
                )
            )
        )
        worker.start()
        assert entered.wait(5), "the retry handoff was never reached"
        disposition = runner.cancel("retry_cancel_handoff")
        release.set()
        worker.join(5)
        assert not worker.is_alive()
    finally:
        runner_module.compatibility_follow_up = original

    # The cancellation is answered honestly: it took effect.
    assert disposition == "cancelled"
    # ONE physical dispatch happened, and nothing was published after cancel.
    assert adapter.dispatches == 1
    assert publications == []
    # The LOGICAL outcome reflects the cancellation the caller was granted — not
    # the dialect `failed` of the one attempt that ran (round 2c).
    assert result[0].outcome == "cancelled"

    # ...and the retry was never ADMITTED. Round 2b stopped it from dispatching
    # but still submitted and claimed a terminal `cancelled` `_r2`; a retry that
    # has not been admitted when the cancellation lands must not become a child
    # at all (round 2c, Terra MANDATORY 2).
    children = _invoke_children(db)
    assert [row["native_id"] for row in children] == ["retry_cancel_handoff"]
    receipt = _receipt(db, children[0]["operation_id"])
    # The one child keeps its own honest, immutable receipt.
    assert receipt["outcome"] == "failed" and receipt["result_ref"] == ""
    assert result[0].operation_id == children[0]["operation_id"]
    assert dict(result[0].receipt)["outcome"] == "failed"


def test_a_cancellation_after_the_retry_registers_is_an_admitted_cancelled_child(tmp_path):
    """The OTHER cohort, kept deliberately: cancel lands once `_r2` is real.

    Sol Amendment 3 models a pre-dispatch cancellation as a genuine child with its
    own terminal receipt and ZERO physical attempts, and that is the honest record
    once the follow-up has been submitted, claimed, and registered — the work was
    admitted, then stopped. Fencing that away would be a lie in the other
    direction, so 2c narrows only the window BEFORE admission.

    Deterministic: the second attempt is parked inside its engine factory, which
    runs after registration and before any dispatch.
    """
    import threading

    db, broker, revision = _bare_rig(tmp_path)
    adapter = _DialectThenSucceed()
    publications: list[Any] = []
    registered, release = threading.Event(), threading.Event()
    builds = {"count": 0}

    def factory(_revision: Any, **_kwargs: Any) -> Any:
        builds["count"] += 1
        if builds["count"] == 2:  # the follow-up: admitted, claimed, registered
            registered.set()
            assert release.wait(5), "the test never released the retry"
        return object()

    runner = _bare_runner(broker, db, engine_factory=factory)
    result: list[Any] = []
    worker = threading.Thread(
        target=lambda: result.append(
            runner.invoke(
                _bare_request_named(revision, "retry_after_registration"),
                adapter,
                publish=lambda output: publications.append(output) or "result:registered",
            )
        )
    )
    worker.start()
    assert registered.wait(5), "the follow-up never registered"
    disposition = runner.cancel("retry_after_registration")
    release.set()
    worker.join(5)
    assert not worker.is_alive()

    assert disposition == "cancelled"
    assert adapter.dispatches == 1, "the registered retry reached a provider anyway"
    assert publications == []
    children = _invoke_children(db)
    assert [row["native_id"] for row in children] == [
        "retry_after_registration", "retry_after_registration_r2"
    ]
    assert [
        _receipt(db, row["operation_id"])["outcome"] for row in children
    ] == ["failed", "cancelled"]
    assert all(_receipt(db, row["operation_id"])["result_ref"] == "" for row in children)


def test_a_cancellation_racing_the_dialect_signal_never_admits_the_retry(tmp_path):
    """The other half of blocker 3: cancel lands while attempt one is DISPATCHING.

    `_attempt` could then return `cancelled` (or `indeterminate`) while still
    having recorded a dialect signal, and `invoke` retried unconditionally on the
    signal alone. The gate is now the honest first outcome: only a `failed`
    compatibility attempt earns a follow-up.
    """
    import threading

    db, broker, revision = _bare_rig(tmp_path)
    dispatching, proceed = threading.Event(), threading.Event()

    class _Adapter:
        def __init__(self) -> None:
            self.dispatches = 0

        def dispatch(self, engine: Any, payload: Any, cancellation: Any) -> Any:
            self.dispatches += 1
            dispatching.set()
            assert proceed.wait(5), "the test never released the dispatch"
            from holdspeak.kernel.provider_signals import ProviderCompatibilityRetry

            raise ProviderCompatibilityRetry("max_completion_tokens")

        def cancel(self) -> str:
            return "cancelled"

    runner = _bare_runner(broker, db, engine_factory=lambda _revision, **_: object())
    adapter = _Adapter()
    publications: list[Any] = []
    result: list[Any] = []
    worker = threading.Thread(
        target=lambda: result.append(
            runner.invoke(
                _bare_request_named(revision, "signal_vs_cancel"),
                adapter,
                publish=lambda output: publications.append(output) or "result:race",
            )
        )
    )
    worker.start()
    assert dispatching.wait(5), "the adapter never reached its dispatch"
    disposition = runner.cancel("signal_vs_cancel")
    proceed.set()
    worker.join(5)
    assert not worker.is_alive()

    assert disposition == "cancelled"
    assert adapter.dispatches == 1, "the retry ran despite a cancelled first attempt"
    assert publications == []
    assert result[0].outcome == "cancelled"
    children = _invoke_children(db)
    assert [row["native_id"] for row in children] == ["signal_vs_cancel"]
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "cancelled"



def test_a_signal_left_by_a_non_failed_attempt_never_earns_a_retry() -> None:
    """The second half of blocker 3's gate, isolated from the fence.

    ``invoke`` retried on the PRESENCE of a dialect signal alone. But ``_attempt``
    can record a signal and still return a terminal ``cancelled`` or
    ``indeterminate`` outcome — the compatibility exception is caught, the signal
    is appended, and `_finish` then elects the disposition the cancellation
    machinery already decided. Retrying such an attempt would call the provider
    again for an invocation that has already terminalized.

    Every route that produces that shape today also trips the logical
    cancellation fence, so this is defence in depth — which is exactly why it
    needs its own test: the fence would otherwise be the only thing keeping the
    gate honest, and a fence change could silently remove it. Driven at
    ``_attempt`` so the gate is the ONLY thing under test.
    """
    from holdspeak.kernel.inference_runner import InferenceRunner, InvocationOutcome
    from holdspeak.kernel.invocation_sequence import SequenceRegistry
    from holdspeak.kernel.provider_signals import ProviderCompatibilityRetry

    def attempts_for(terminal: str) -> tuple[list[str], Any]:
        runner = InferenceRunner.__new__(InferenceRunner)
        runner._sequences = SequenceRegistry()
        seen: list[str] = []

        def attempt(request, adapter, *, signal=None, sequence=None, **_kwargs):
            seen.append(request.invocation_id)
            if signal is not None:  # the FIRST attempt records a dialect signal…
                signal.append(ProviderCompatibilityRetry("max_completion_tokens"))
            # …and still terminalizes as something other than `failed`.
            return InvocationOutcome("op_only", request.invocation_id, terminal, "", {}, "")

        runner._attempt = attempt
        outcome = runner.invoke(
            _bare_request_named(SimpleNamespace(id="dep_x"), "gated"), object()
        )
        return seen, outcome

    for terminal in ("cancelled", "indeterminate", "refused"):
        seen, outcome = attempts_for(terminal)
        assert seen == ["gated"], f"{terminal}: a retry ran anyway ({seen})"
        assert outcome.outcome == terminal


def test_a_concurrent_child_never_borrows_another_childs_engine_context(tmp_path):
    """Terra blocker 6: a shared engine let one child read another's admission.

    The runner accepted a reused engine whose context merely agreed on
    revision/destination, then OVERWROTE that context with its own. Two children
    of the same revision sharing a cached engine therefore raced: A wrote its
    context, B overwrote it, and A — still in flight — read B's operation and
    refused its own work. Whoever got there second won, which is the wrong way
    round for an admission fence.

    An engine already bound to another child's context is now refused before
    dispatch, and the binding is released as each attempt ends. Deterministic:
    B runs to completion while A is parked inside `_dispatch`.
    """
    import threading

    db, broker, revision = _bare_rig(tmp_path)

    class _Engine:
        def run_prompt(self, **_: Any) -> str:
            return "shared result"

    shared = _Engine()
    runner = _bare_runner(broker, db, engine_factory=lambda _revision, **_: shared)
    at_dispatch, release_first = threading.Event(), threading.Event()
    real_dispatch = runner._dispatch
    seen = {"count": 0}

    def ordered_dispatch(*args: Any, **kwargs: Any) -> Any:
        seen["count"] += 1
        if seen["count"] == 1:
            at_dispatch.set()
            assert release_first.wait(5), "the test never released the first dispatch"
        return real_dispatch(*args, **kwargs)

    runner._dispatch = ordered_dispatch
    outcomes: dict[str, Any] = {}

    def run(label: str) -> None:
        outcomes[label] = runner.invoke(_bare_request_named(revision, label), _Adapter())

    first = threading.Thread(target=run, args=("shared_a",))
    first.start()
    assert at_dispatch.wait(5), "the first child never reached dispatch"
    second = threading.Thread(target=run, args=("shared_b",))
    second.start()
    second.join(5)
    release_first.set()
    first.join(5)
    assert not first.is_alive() and not second.is_alive()

    # The child that was ALREADY admitted and dispatching wins its own work...
    assert outcomes["shared_a"].outcome == "succeeded"
    # ...and the latecomer refuses rather than borrowing a live admission.
    assert outcomes["shared_b"].outcome == "refused"
    assert _receipt(db, outcomes["shared_b"].operation_id)["outcome"] == "refused"
    # Cardinality is intact, and no context outlives its attempt.
    from holdspeak.kernel.dispatch_context import dispatch_context_of

    assert len(_invoke_children(db)) == 2
    assert dispatch_context_of(shared) is None
