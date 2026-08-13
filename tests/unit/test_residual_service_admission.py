"""HS-131-13 — the residual service seams: admitted, or gone.

Three families left the blocking ledger in this story, and each one has to be
provable at the PRODUCTION boundary rather than in a diagram:

* **Cadence** migrated. Request-time next-action drafting now opens an
  authenticated ``cadence.next-action-draft`` parent, freezes its deployment
  BEFORE admission, admits exactly one ``inference.invoke`` child, stages its
  output, and closes on a terminal receipt. It must never manufacture an owner or
  a scheduler: an unauthenticated read gets the deterministic action and reaches
  no provider at all.
* **The second Decisions seam** was deleted. The route holds no engine, no
  ``run_prompt`` callable, and no ``model_generator`` injection point; drafting is
  the admitted Decision promotion child that HS-131-07 already shipped.
* **Dormant Delivery review** was deleted. ``prepare_pr_review`` had no caller and
  built an engine from a MUTABLE target with no admitted child behind it.

...and with the last caller gone, ``build_intel_for_target`` itself is deleted —
not wrapped, not deprecated. The deletion assertions at the bottom are the half
that keeps this story from being undone by a well-meaning re-import.

Everything here runs against a real ``Database`` in ``tmp_path`` plus the
production broker (``kernel.runtime._configure``); only the engine/provider
CONSTRUCTION seam is faked, exactly as the one-path suites do.
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.cadence.models import OpenLoop
from holdspeak.config.integrations import CadenceConfig
from holdspeak.db import Database, reset_database
from holdspeak.deployment_revisions import resolve_deployment_revision
from holdspeak.inference_targets import THIS_MACHINE_ID
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import UNAUTHENTICATED, Principal, PrincipalKind
from holdspeak.services.cadence_service import CadenceService

pytestmark = pytest.mark.timeout(90, method="signal")

REPO = Path(__file__).resolve().parents[2]
CALLER = Principal(PrincipalKind.OWNER, "cadence-caller")

#: What a well-formed CAD-7 draft looks like on the wire.
DRAFT = '{"kind":"create_issue","title":"Watchdog the intel queue","body_markdown":"## Problem"}'


class _Leaf:
    """The PHYSICAL counter, bumped at the provider edge and nowhere else."""

    def __init__(self, output: str = DRAFT) -> None:
        self.attempts = 0
        self.output = output
        self.before: Any = None

    def hit(self) -> None:
        self.attempts += 1


def _rig(tmp_path, monkeypatch, *, use_llm: bool = True):
    """A real cadence loop, a real broker, and a counted fake provider."""
    reset_database()
    db = Database(tmp_path / "cadence-admission.db")
    monkeypatch.setattr(
        "holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", "")
    )
    loop = db.cadence.upsert_loop(
        OpenLoop(
            source_type="meeting_action", source_id="a1",
            title="Ship the watchdog", owner="Karol",
        )
    )
    broker = _configure(db)
    leaf = _Leaf()
    revisions: list[Any] = []

    class FakeIntel:
        active_provider = "local"

        def run_prompt(self, **_: Any) -> str:
            leaf.hit()
            return leaf.output

    def factory(revision, **_: Any):
        revisions.append(revision)
        return FakeIntel()

    broker.inference_runner._engine_factory = factory
    service = CadenceService(db, CadenceConfig(use_llm=use_llm), kernel=broker)
    return db, broker, service, loop, leaf, revisions


def _rows(db: Database, sql: str, *args: Any) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(sql, args).fetchall()]


def _parents(db: Database) -> list[dict[str, Any]]:
    return _rows(db, "SELECT * FROM kernel_parent_runs ORDER BY created_at")


def _children(db: Database) -> list[dict[str, Any]]:
    return _rows(
        db,
        "SELECT * FROM kernel_operations WHERE name='inference.invoke' ORDER BY created_at",
    )


def _receipt(db: Database, operation_id: str) -> dict[str, Any] | None:
    rows = _rows(db, "SELECT * FROM kernel_receipts WHERE operation_id=?", operation_id)
    return rows[0] if rows else None


# =========================================================== 1. Cadence: identity


def test_cadence_draft_authenticates_as_the_caller_never_the_owner_or_scheduler(
    tmp_path, monkeypatch
) -> None:
    """HS-131-06's distinction survives the migration.

    Request-time cadence intelligence is a foreground READ under whoever the
    transport authenticated. Both the parent and its child must carry THAT
    identity, and no row may acquire the internal scheduler identity — which is
    exactly the manufactured authority a service is never allowed to mint.
    """
    db, _broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)

    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["generated_by"] == "llm"
    assert leaf.attempts == 1
    parents = _parents(db)
    assert [row["kind"] for row in parents] == ["cadence.next-action-draft"]
    everything = _rows(db, "SELECT * FROM kernel_operations")
    assert everything, "the run left no kernel operations at all"
    for row in everything:
        if row["principal_kind"] == PrincipalKind.NODE.value:
            continue  # the executor node identity the kernel derives itself
        assert row["principal_kind"] == PrincipalKind.OWNER.value, row["name"]
        assert row["principal_identity"] == "cadence-caller", row["name"]
    assert not [
        row for row in everything
        if row["principal_kind"] == PrincipalKind.SCHEDULER.value
    ], "a request-time draft must never acquire scheduler authority"


def test_cadence_refuses_an_unauthenticated_read_without_reaching_a_provider(
    tmp_path, monkeypatch
) -> None:
    """No principal, no admission, no provider — and still an honest answer.

    The fail-closed CAD-7 contract is preserved (the caller gets the
    deterministic action), but the important half is what did NOT happen: the
    kernel refused the parent, so nothing was built and nothing was dispatched.
    """
    db, _broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)

    detail = asyncio.run(service.get_loop(UNAUTHENTICATED, loop.id))

    assert detail["next_action"]["generated_by"] == "deterministic"
    assert leaf.attempts == 0
    assert _parents(db) == []
    assert _children(db) == []


def test_cadence_does_not_admit_anything_when_the_capability_is_off(
    tmp_path, monkeypatch
) -> None:
    """``use_llm=False`` is the default. It must stay a NO-OP, not a refused run."""
    db, _broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch, use_llm=False)

    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["generated_by"] == "deterministic"
    assert leaf.attempts == 0
    assert _parents(db) == []
    assert _children(db) == []


# ================================================ 2. Cadence: frozen revision


def test_a_config_edit_after_capture_cannot_change_the_model_cadence_loads(
    tmp_path, monkeypatch
) -> None:
    """The HS-131-13 hostile finding, as a production regression.

    Cadence froze deployment ``A`` and its child row named ``A`` — but the
    ``this_machine`` factory reached ``configured_meeting_intel``, whose body
    re-reads ``Config.load().meeting`` and hands ``MeetingIntel`` the CURRENT
    ``intel_realtime_model``. An owner who changed the meeting model between
    capture and dispatch therefore got model ``B`` executed under a receipt, a
    child row, and a durable revision that all said ``A``. Article XI.3 makes the
    target immutable after admission; this is that, executably.

    Nothing here fakes the factory: the real
    ``build_intel_for_revision -> local_pinned_meeting_intel -> _local_pinned_engine``
    chain runs, and only the final engine CLASS is a recorder. The saved config is
    mutated the moment the parent opens — after the revision is captured, before a
    single provider object exists.
    """
    db, broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)
    model_a = str(tmp_path / "cadence-captured-A.gguf")
    model_b = str(tmp_path / "cadence-retargeted-B.gguf")
    saved = {"model": model_a}

    # The rig's convenience factory is REMOVED for this one: the whole point is to
    # run the production revision -> engine chain, not to skip it.
    from holdspeak.inference_targets import build_intel_for_revision

    broker.inference_runner._engine_factory = build_intel_for_revision

    built: list[dict[str, Any]] = []

    class _Recorder:
        active_provider = "local"

        def __init__(self, **kwargs: Any) -> None:
            built.append(kwargs)
            self.provider = kwargs.get("provider")
            self.model_path = kwargs.get("model_path")

        def run_prompt(self, **_: Any) -> str:
            leaf.hit()
            return DRAFT

    # The ONE mutable source both the frozen revision and the legacy configured
    # constructor read. Freezing reads it first; the edit below moves it to B.
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path",
        lambda: saved["model"],
    )
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", _Recorder)
    # Stands in for the legacy body this branch used to call. If the fix regresses
    # and `configured_meeting_intel` is reached again, THIS is what answers — with
    # whatever the config says at that moment, which is the defect.
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine",
        lambda: _Recorder(provider="local", model_path=saved["model"]),
    )

    # The owner edits the saved meeting model while the request is in flight:
    # after `capture_deployment_revision`, before the engine is constructed.
    real_start = broker.parent_run_controller.start

    def start_then_edit(*args: Any, **kwargs: Any):
        parent = real_start(*args, **kwargs)
        saved["model"] = model_b
        return parent

    monkeypatch.setattr(broker.parent_run_controller, "start", start_then_edit)

    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["generated_by"] == "llm"
    assert leaf.attempts == 1
    # The engine actually loaded A -- the model the revision named, not the edit.
    assert built == [{"provider": "local", "model_path": model_a}], built
    # ...and the immutable revision the child names still says A, so the receipt
    # and the execution agree. Pre-fix this asserted A while B had run.
    children = _children(db)
    assert len(children) == 1
    frozen = resolve_deployment_revision(db, children[0]["target_ref"].split(":", 1)[1])
    assert frozen is not None and frozen.model_path == model_a
    assert saved["model"] == model_b, "the test never actually moved the config"


def test_cadence_dispatches_the_exact_revision_it_froze_before_admission(
    tmp_path, monkeypatch
) -> None:
    """One placement decision, taken once, frozen, and never re-resolved.

    The child's ``target_ref`` names an immutable ``deployment_revisions`` row; the
    engine factory is handed THAT row and no other; and ``resolve_placement`` — the
    one mutable-config read in the whole path — happens exactly once, before the
    provider is ever reached. A second resolution after admission is precisely how
    a run silently retargets while its receipt still names the frozen destination.
    """
    db, _broker, service, loop, leaf, revisions = _rig(tmp_path, monkeypatch)
    import holdspeak.inference_targets as targets

    real_resolve = targets.resolve_placement
    resolutions: list[int] = []

    def counting_resolve(*args: Any, **kwargs: Any):
        resolutions.append(leaf.attempts)
        return real_resolve(*args, **kwargs)

    monkeypatch.setattr(targets, "resolve_placement", counting_resolve)

    asyncio.run(service.get_loop(CALLER, loop.id))

    assert resolutions == [0], "placement was resolved after the provider ran, or twice"
    children = _children(db)
    assert len(children) == 1
    target_ref = children[0]["target_ref"]
    assert target_ref.startswith("deployment-revision:"), target_ref
    frozen = resolve_deployment_revision(db, target_ref.split(":", 1)[1])
    assert frozen is not None, "the child names a revision that does not resolve"
    assert frozen.destination_id == THIS_MACHINE_ID
    assert [revision.id for revision in revisions] == [frozen.id]


# ============================================== 3. Cadence: exact cardinality


def test_cadence_draft_is_one_parent_one_child_one_receipt_one_physical_attempt(
    tmp_path, monkeypatch
) -> None:
    """``child_operations == terminal_child_receipts == physical attempts == 1``.

    Plus the two rows that must NOT be conflated: the parent is its own
    (non-``inference.invoke``) operation with its own terminal receipt, and the
    drafted text crosses the publication boundary as a STAGED projection rather
    than being applied straight out of the provider's answer.
    """
    db, _broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)

    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["title"] == "Watchdog the intel queue"
    assert leaf.attempts == 1
    children = _children(db)
    assert len(children) == 1
    child_receipt = _receipt(db, children[0]["operation_id"])
    assert child_receipt is not None and child_receipt["outcome"] == "succeeded"

    parents = _parents(db)
    assert len(parents) == 1
    parent_id = parents[0]["operation_id"]
    assert children[0]["parent_operation_id"] == parent_id
    parent_receipt = _receipt(db, parent_id)
    assert parent_receipt is not None and parent_receipt["outcome"] == "succeeded"
    assert _rows(db, "SELECT * FROM kernel_operations WHERE operation_id=?", parent_id)[0][
        "name"
    ] == "cadence.next-action-draft"

    stages = _rows(db, "SELECT * FROM kernel_projection_stages")
    assert [(row["kind"], row["state"]) for row in stages] == [
        ("cadence-next-action", "PUBLISHED")
    ]


def test_an_off_contract_draft_fails_the_parent_and_returns_the_deterministic_action(
    tmp_path, monkeypatch
) -> None:
    """Article VI at the receipt: a draft the domain rejected is not a success.

    The CHILD honestly succeeded — the provider answered — and its immutable
    receipt says so. The PARENT is the operation that was supposed to produce a
    usable draft, so it closes ``failed``, and the caller gets the deterministic
    action rather than a fabricated one.
    """
    db, _broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)
    leaf.output = "sure! here you go: not json"

    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["generated_by"] == "deterministic"
    assert leaf.attempts == 1
    children = _children(db)
    assert len(children) == 1
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "succeeded"
    assert _receipt(db, _parents(db)[0]["operation_id"])["outcome"] == "failed"


# ============================================ 4. Cadence: late publication


def test_a_cancelled_cadence_parent_never_publishes_its_late_draft(
    tmp_path, monkeypatch
) -> None:
    """Cancellation lands while the provider is in flight: nothing publishes.

    The child EARNED its receipt and keeps it — the provider really did answer, and
    rewriting that row would be the dishonest fix. What is fenced is PUBLICATION:
    the stage is discarded, the caller receives the deterministic action, and no
    drafted text reaches the surface.
    """
    db, broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)

    class CancellingIntel:
        active_provider = "local"

        def run_prompt(self, **_: Any) -> str:
            leaf.hit()
            parent_id = _parents(db)[0]["operation_id"]
            broker.parent_run_controller.cancel_by_operation_id(CALLER, parent_id)
            return DRAFT

    broker.inference_runner._engine_factory = lambda _revision, **_: CancellingIntel()

    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["generated_by"] == "deterministic"
    assert "Watchdog the intel queue" not in str(detail["next_action"])
    assert leaf.attempts == 1
    children = _children(db)
    assert len(children) == 1
    assert _receipt(db, children[0]["operation_id"]) is not None
    assert _receipt(db, _parents(db)[0]["operation_id"])["outcome"] == "cancelled"
    stages = _rows(db, "SELECT * FROM kernel_projection_stages")
    assert [(row["kind"], row["state"]) for row in stages] == [
        ("cadence-next-action", "DISCARDED")
    ], stages


def _wait(predicate, *, timeout: float = 5.0) -> bool:
    """Bounded poll — no sleeps in the assertion path, no unbounded waits."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_cancelling_the_request_task_cancels_the_parent_and_publishes_nothing(
    tmp_path, monkeypatch
) -> None:
    """The realistic disconnect: the REQUEST goes away, the provider does not.

    Cancelling the awaiting coroutine cancels nothing inside ``asyncio.to_thread``
    — the provider thread runs to completion regardless. The pre-fix service
    caught that ``CancelledError`` in its generic arm and closed the parent
    ``failed``, which is both a lie (nobody failed; the caller left) and unsafe:
    ``FAILED`` is not one of the states the projection stager fences on, so the
    surviving thread's output published through the next recovery pass.

    A durable CANCELLED parent is what makes late output unpublishable, so that is
    what this asserts — together with the child keeping whatever terminal receipt
    it honestly earned.
    """
    db, broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)
    entered = threading.Event()
    release = threading.Event()

    class BlockingIntel:
        active_provider = "local"

        def run_prompt(self, **_: Any) -> str:
            leaf.hit()
            entered.set()
            release.wait(5.0)
            return DRAFT

    broker.inference_runner._engine_factory = lambda _revision, **_: BlockingIntel()

    async def drive() -> None:
        task = asyncio.create_task(service.get_loop(CALLER, loop.id))
        while not entered.is_set():
            await asyncio.sleep(0.01)
        # The client is gone. Nothing has told the provider thread yet.
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        # Only now does the provider answer -- into a request that no longer exists.
        release.set()

    asyncio.run(drive())

    assert leaf.attempts == 1
    parents = _parents(db)
    assert len(parents) == 1
    parent_receipt = _receipt(db, parents[0]["operation_id"])
    assert parent_receipt is not None, "the cancelled parent must still terminalize"
    assert parent_receipt["outcome"] == "cancelled", parent_receipt["outcome"]

    children = _children(db)
    assert len(children) == 1
    assert _wait(lambda: _receipt(db, children[0]["operation_id"]) is not None), (
        "the admitted child never reached a terminal receipt"
    )
    # Recovery is the pass that used to turn the survivor's output into PUBLISHED.
    broker.projection_stager.recover()
    published = [
        row for row in _rows(db, "SELECT * FROM kernel_projection_stages")
        if row["state"] == "PUBLISHED"
    ]
    assert published == [], f"late output published after cancellation: {published}"


def test_recovery_discards_a_cadence_stage_left_by_a_cancelled_request(
    tmp_path, monkeypatch
) -> None:
    """The other ordering: the provider WON the race and already staged.

    Here the child completes and stages its projection before the cancellation
    lands, so a stage row genuinely exists — this is the exact shape the HS-131-13
    audit reproduced, where ``ProjectionStager.recover`` finalized the survivor
    into ``PUBLISHED``. With the parent durably CANCELLED the discard rule
    registered for ``cadence-next-action`` fires instead, so the row ends
    ``DISCARDED`` and no drafted text is ever materialized.
    """
    db, broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)
    staged = threading.Event()
    release = threading.Event()
    real_stage = broker.projection_stager.stage

    def blocking_stage(*args: Any, **kwargs: Any):
        # Stage for real (the row becomes durable), then hold the worker thread
        # right there so the cancellation is guaranteed to land AFTER staging.
        result = real_stage(*args, **kwargs)
        staged.set()
        release.wait(5.0)
        return result

    monkeypatch.setattr(broker.projection_stager, "stage", blocking_stage)

    async def drive() -> None:
        task = asyncio.create_task(service.get_loop(CALLER, loop.id))
        while not staged.is_set():
            await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        release.set()

    asyncio.run(drive())

    assert leaf.attempts == 1
    stages = _rows(db, "SELECT * FROM kernel_projection_stages")
    assert [row["kind"] for row in stages] == ["cadence-next-action"], stages
    assert _receipt(db, _parents(db)[0]["operation_id"])["outcome"] == "cancelled"
    children = _children(db)
    assert len(children) == 1
    assert _wait(lambda: _receipt(db, children[0]["operation_id"]) is not None)

    # The pass that used to publish it.
    broker.projection_stager.recover()

    stages = _rows(db, "SELECT * FROM kernel_projection_stages")
    assert [(row["kind"], row["state"]) for row in stages] == [
        ("cadence-next-action", "DISCARDED")
    ], stages


def test_an_unexpected_crash_still_terminalizes_the_cadence_parent(
    tmp_path, monkeypatch
) -> None:
    """No OPEN parent is left behind waiting for the lease reaper.

    ``get_loop`` is fail-closed by charter, so a crash inside the draft is
    invisible to the caller — which is exactly how a parent operation ends up with
    no terminal receipt for a lease window. Article XI.2 admits no such gap: the
    parent closes ``failed`` on the way out, in the same request.
    """
    db, broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)

    def exploding_finalize(*_args: Any, **_kwargs: Any):
        raise RuntimeError("projection store went away")

    monkeypatch.setattr(broker.projection_stager, "finalize", exploding_finalize)

    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["generated_by"] == "deterministic"
    parents = _parents(db)
    assert len(parents) == 1
    receipt = _receipt(db, parents[0]["operation_id"])
    assert receipt is not None and receipt["outcome"] == "failed"
    # The child that really ran keeps its own honest, separate receipt.
    children = _children(db)
    assert len(children) == 1
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "succeeded"


# ================================================= 5. The deletions, pinned


def test_the_legacy_uncontextual_target_factory_no_longer_exists() -> None:
    """No factory, no shim, no re-export. Importing it must fail."""
    import holdspeak.inference_targets as targets

    assert not hasattr(targets, "build_intel_for_target")
    with pytest.raises(ImportError):
        from holdspeak.inference_targets import build_intel_for_target  # noqa: F401


def test_the_dormant_delivery_review_helper_no_longer_exists() -> None:
    from holdspeak.services.delivery_service import DeliveryService

    assert not hasattr(DeliveryService, "prepare_pr_review")


def test_the_decisions_route_holds_no_model_seam() -> None:
    """The route may compose the service; it may not execute a model.

    Checked structurally rather than by grep-for-a-string: every call and every
    first-class reference in the module is inspected, so a renamed local or a
    bound method handed to a thread pool is caught as readily as a direct call.
    """
    source = (REPO / "holdspeak/web/routes/decisions.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {
        "build_intel_for_target", "build_intel_for_revision", "run_prompt",
        "build_configured_meeting_intel", "MeetingIntel", "_chat_completion_text",
    }
    named = {
        node.attr if isinstance(node, ast.Attribute) else node.id
        for node in ast.walk(tree)
        if isinstance(node, (ast.Attribute, ast.Name))
    }
    assert not (named & forbidden), sorted(named & forbidden)
    assert "model_generator" not in source


def test_the_decision_service_no_longer_takes_a_model_generator() -> None:
    """The injection point is gone, so a second Decision seam cannot be wired back."""
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService

    parameters = inspect.signature(DecisionLifecycleService.__init__).parameters
    assert "model_generator" not in parameters
    assert set(parameters) == {"self", "db", "kernel", "observer"}


def test_the_cadence_service_constructs_no_engine_of_its_own() -> None:
    """Domain shaping stays; construction left. The service names no engine verb."""
    source = (REPO / "holdspeak/services/cadence_service.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    named = {
        node.attr if isinstance(node, ast.Attribute) else node.id
        for node in ast.walk(tree)
        if isinstance(node, (ast.Attribute, ast.Name))
    }
    assert not (named & {
        "build_configured_meeting_intel", "configured_meeting_intel", "run_prompt",
        "build_intel_for_target", "build_intel_for_revision", "MeetingIntel",
    }), sorted(named)
    # It DOES still own the domain half — the prompt and the validation — which is
    # what keeps the generic runner from branching on Cadence.
    assert "next_action_prompt" in source and "next_action_from_output" in source


def test_the_generic_runner_never_learned_a_cadence_branch() -> None:
    """The migration must not leak a domain name into the kernel."""
    for relative in (
        "holdspeak/kernel/inference_runner.py",
        "holdspeak/kernel/projection_stager.py",
        "holdspeak/kernel/broker.py",
    ):
        source = (REPO / relative).read_text(encoding="utf-8").lower()
        assert "cadence" not in source, relative
