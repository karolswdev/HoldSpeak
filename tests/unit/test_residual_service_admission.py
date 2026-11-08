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
    # Production router ingredients: one ready visible Model Library profile and
    # the exact OWNER capability assignment.  The engine construction leaf below
    # is the only fake.
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile

    _profile(db, "cadence-route")
    InferenceAssignmentService(db).set_assignment(
        ASSIGNMENT_OWNER,
        {
            "command_id": "assign-cadence-route",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "background.cadence_draft"},
            "entries": [{"profile_id": "cadence-route", "profile_revision": 1}],
        },
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
    # The kernel refuses the unauthenticated invoke at admission.
    assert all(_receipt(db, row["operation_id"])["outcome"] != "succeeded" for row in _children(db))


def test_cadence_missing_assignment_returns_deterministic_action_with_one_refusal(
    tmp_path, monkeypatch
) -> None:
    """No engine assigned: the deterministic action, and no model call."""
    db, _broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER
    InferenceAssignmentService(db).clear_assignment(ASSIGNMENT_OWNER, {
        "command_id": "clear-cadence-route", "expected_revision": 1,
        "scope": {"kind": "capability", "capability_id": "background.cadence_draft"},
        "capability_id": "background.cadence_draft",
    })

    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["generated_by"] == "deterministic"
    assert leaf.attempts == 0
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

    assert resolutions == [], "Cadence must not consult legacy placement authority"
    children = _children(db)
    assert len(children) == 1
    target_ref = children[0]["target_ref"]
    assert target_ref.startswith("deployment-revision:"), target_ref
    frozen = resolve_deployment_revision(db, target_ref.split(":", 1)[1])
    assert frozen is not None, "the child names a revision that does not resolve"
    assert frozen.destination_id == THIS_MACHINE_ID
    assert [revision.id for revision in revisions] == [frozen.id]


# ============================================== 3. Cadence: exact cardinality


def test_cadence_draft_is_one_child_one_receipt_one_physical_attempt(
    tmp_path, monkeypatch
) -> None:
    """``child_operations == terminal_child_receipts == physical attempts == 1``:
    the draft is one root invoke through the engine door."""
    db, _broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)

    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["title"] == "Watchdog the intel queue"
    assert leaf.attempts == 1
    children = _children(db)
    assert len(children) == 1
    child_receipt = _receipt(db, children[0]["operation_id"])
    assert child_receipt is not None and child_receipt["outcome"] == "succeeded"
    assert not children[0]["parent_operation_id"]
    assert _parents(db) == []


def test_an_off_contract_draft_returns_the_deterministic_action(
    tmp_path, monkeypatch
) -> None:
    """A draft the domain rejected is not used: the provider answered (its
    receipt says so) and the caller gets the deterministic action."""
    db, _broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)
    leaf.output = "sure! here you go: not json"

    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["generated_by"] == "deterministic"
    assert leaf.attempts == 1
    children = _children(db)
    assert len(children) == 1
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "succeeded"


# ============================================ 4. Cadence: late publication


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
