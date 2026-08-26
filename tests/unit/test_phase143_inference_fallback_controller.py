"""Focused Story-06 durable fallback-controller laws."""

from __future__ import annotations

import hashlib
import inspect
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.inference_runner import (
    InferenceRunner,
    InvocationRequest,
    ServiceContract,
)
from holdspeak.kernel.provider_signals import (
    InferenceInvalidTypedOutput,
    ProviderCompatibilityRetry,
    ProviderIndeterminate,
    ProviderKnownNoGenerationTransient,
    ProviderPermanentNoGeneration,
    ProviderPermissionDenied,
)
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_fallback_controller import (
    INFERENCE_FALLBACK_AUTHORITY,
    InferenceFallbackController,
    RoutedAttemptRuntime,
)
from holdspeak.services.inference_route_plan_service import ROUTE_PLANNING_AUTHORITY
from holdspeak.services.sync_service import SyncService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile
from tests.unit.test_phase143_inference_route_plans import (
    _digest,
    _evidence_service,
    _ready_route,
)


def _command_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()


def _operation_plan(db: Database, *, total_tokens: int = 1024) -> tuple[str, object]:
    _ready_route(db, profiles=("quick",))
    with db._connection() as conn:
        conn.execute("UPDATE model_profile_readiness_observations SET state='ready'")
    service = _evidence_service(
        db,
        reference="fallback-start-evidence",
        entries=[{
            "route_leg_ordinal": 1,
            "eligibility": "executable",
            "reason_code": None,
            "admitted_request_id": "request:fallback-start",
            "admitted_request_sha256": _digest({"request": "fallback-start"}),
            "context_plan_sha256": _digest({"context": "fallback-start"}),
            "serialized_request_sha256": _digest({"serialized": "fallback-start"}),
        }],
        budgets=[{
            "route_leg_ordinal": 1,
            "admitted_request_id": "request:fallback-start",
            "admitted_request_sha256": _digest({"request": "fallback-start"}),
            "context_plan_sha256": _digest({"context": "fallback-start"}),
            "serialized_request_sha256": _digest({"serialized": "fallback-start"}),
            "input_tokens": total_tokens,
            "reserved_output_tokens": 0,
            "total_tokens": total_tokens,
            "reserved_cost_units": 0,
            "reserved_tool_calls": 0,
        }],
    )
    frozen = service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY,
        command_id="freeze-fallback-start",
        route_request={"capability_id": "ask.answer"},
        operation_id="fallback-start-operation",
        planning_reference="fallback-start-evidence",
    )
    return str(frozen["operation_request_plan"]["id"]), service


def _two_leg_operation_plan(
    db: Database, *, first_eligibility: str = "executable",
    first_context: int = 4096, second_context: int = 8192,
) -> tuple[str, object]:
    _profile(db, "route-first", context_ceiling=first_context)
    _profile(db, "route-second", context_ceiling=second_context)
    with db._connection() as conn:
        conn.execute("UPDATE model_profile_readiness_observations SET state='ready'")
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "assign-two-leg-route", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "ask.answer"},
        "entries": [
            {"profile_id": "route-first", "profile_revision": 1},
            {"profile_id": "route-second", "profile_revision": 1},
        ],
    })
    entries, budgets = [], []
    for ordinal, eligibility in ((1, first_eligibility), (2, "executable")):
        executable = eligibility == "executable"
        entries.append({
            "route_leg_ordinal": ordinal, "eligibility": eligibility,
            "reason_code": None if executable else "context_overflow",
            "admitted_request_id": f"request:two-leg:{ordinal}" if executable else None,
            "admitted_request_sha256": _digest({"request": ordinal}) if executable else None,
            "context_plan_sha256": _digest({"context": ordinal}) if executable else None,
            "serialized_request_sha256": _digest({"serialized": ordinal}) if executable else None,
        })
        budgets.append({
            "route_leg_ordinal": ordinal,
            "admitted_request_id": f"request:two-leg:{ordinal}" if executable else None,
            "admitted_request_sha256": _digest({"request": ordinal}) if executable else None,
            "context_plan_sha256": _digest({"context": ordinal}) if executable else None,
            "serialized_request_sha256": _digest({"serialized": ordinal}) if executable else None,
            "input_tokens": 512 if executable else 0, "reserved_output_tokens": 0,
            "total_tokens": 512 if executable else 0, "reserved_cost_units": 0,
            "reserved_tool_calls": 0,
        })
    service = _evidence_service(db, entries=entries, reference="two-leg-evidence", budgets=budgets)
    frozen = service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY, command_id="freeze-two-leg",
        route_request={"capability_id": "ask.answer"},
        operation_id="two-leg-operation", planning_reference="two-leg-evidence",
    )
    return str(frozen["operation_request_plan"]["id"]), service


def test_start_replays_exact_effect_and_refuses_binding_tamper(tmp_path: Path) -> None:
    db = Database(tmp_path / "fallback-controller.db")
    operation_plan_id, route_service = _operation_plan(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    created = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id="start-fallback-execution",
        operation_plan_id=operation_plan_id,
    )
    assert controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id="start-fallback-execution",
        operation_plan_id=operation_plan_id,
    ) == created
    with pytest.raises(ConflictError) as changed:
        controller.start_execution(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id="start-fallback-execution",
            operation_plan_id="different-operation-plan",
        )
    assert changed.value.code == "inference_route_execution_command_conflict"
    with db._connection() as conn:
        conn.execute(
            "UPDATE inference_route_executions SET route_plan_sha256=? WHERE id=?",
            (_digest({"tampered": True}), created["id"]),
        )
    with pytest.raises(ConflictError) as tampered:
        controller.start_execution(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id="start-fallback-execution",
            operation_plan_id=operation_plan_id,
        )
    assert tampered.value.code == "inference_route_execution_integrity_invalid"


def test_initial_reservation_is_opaque_replayable_and_budget_equality_is_allowed(tmp_path: Path) -> None:
    db = Database(tmp_path / "reserve-equality.db")
    operation_plan_id, route_service = _operation_plan(db, total_tokens=32_768)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-equality", operation_plan_id=operation_plan_id
    )
    first = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-equality", execution_id=execution["id"]
    )
    replay = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-equality", execution_id=execution["id"]
    )
    assert replay == first
    reservation = first["reservation"]
    assert reservation["route_leg_ordinal"] == 1
    assert reservation["physical_attempt_ordinal"] == 1
    assert reservation["leg_attempt_ordinal"] == 1
    assert reservation["purpose"] == "primary"
    assert reservation["nonce"]
    with db._connection() as conn:
        row = conn.execute("SELECT * FROM inference_route_attempts").fetchone()
        assert row["admission_nonce_sha256"] != reservation["nonce"]
        assert row["reserved_token_budget"] == 32_768


def test_token_budget_plus_one_refuses_without_attempt(tmp_path: Path) -> None:
    db = Database(tmp_path / "reserve-over-budget.db")
    operation_plan_id, route_service = _operation_plan(db, total_tokens=32_769)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-over", operation_plan_id=operation_plan_id
    )
    with pytest.raises(ConflictError) as exhausted:
        controller.reserve_next_attempt(
            INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-over", execution_id=execution["id"]
        )
    assert exhausted.value.code == "inference_route_token_budget_exhausted"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == 0


def test_concurrent_last_slot_reserves_exactly_once(tmp_path: Path) -> None:
    db = Database(tmp_path / "reserve-race.db")
    operation_plan_id, route_service = _operation_plan(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-race", operation_plan_id=operation_plan_id
    )

    def reserve(command: str) -> str:
        try:
            controller.reserve_next_attempt(
                INFERENCE_FALLBACK_AUTHORITY, command_id=command, execution_id=execution["id"]
            )
            return "reserved"
        except ConflictError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, ("reserve-race-a", "reserve-race-b")))
    assert results.count("reserved") == 1
    assert results.count("inference_route_attempt_outstanding") == 1
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == 1


def test_preflight_unavailable_records_consideration_and_zero_attempts(tmp_path: Path) -> None:
    db = Database(tmp_path / "reserve-unavailable.db")
    _ready_route(db, profiles=("offline",))
    service = _evidence_service(
        db,
        reference="fallback-unavailable-evidence",
        entries=[{
            "route_leg_ordinal": 1,
            "eligibility": "known_preflight_unavailable",
            "reason_code": "binding_not_ready",
        }],
        budgets=[{
            "route_leg_ordinal": 1,
            "admitted_request_id": None,
            "admitted_request_sha256": None,
            "context_plan_sha256": None,
            "serialized_request_sha256": None,
            "input_tokens": 0,
            "reserved_output_tokens": 0,
            "total_tokens": 0,
            "reserved_cost_units": 0,
            "reserved_tool_calls": 0,
        }],
    )
    frozen = service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY,
        command_id="freeze-unavailable",
        route_request={"capability_id": "ask.answer"},
        operation_id="fallback-unavailable-operation",
        planning_reference="fallback-unavailable-evidence",
    )
    controller = InferenceFallbackController(db, route_plan_service=service)
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id="start-unavailable",
        operation_plan_id=frozen["operation_request_plan"]["id"],
    )
    effect = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id="reserve-unavailable",
        execution_id=execution["id"],
    )
    assert effect["terminal"] == "preflight_unavailable"
    assert effect["reservation"] is None
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == 0
        skip = conn.execute("SELECT * FROM inference_route_execution_skips").fetchone()
        assert (skip["route_leg_ordinal"], skip["disposition"], skip["reason_code"]) == (1, "preflight_unavailable", "binding_not_ready")


def _broker_child(broker: object, reservation: dict[str, object], *, suffix: str) -> str:
    owner = Principal(PrincipalKind.OWNER, "owner")
    raw = {
        "request_schema": 1,
        "request_id": f"request-{suffix}",
        "idempotency_key": reservation["child_invocation_id"],
        "operation": {"name": "inference.invoke", "version": 1},
        "target": {},
        "arguments": {
            "invocation_id": reservation["child_invocation_id"],
            "deployment_revision": reservation["deployment_revision_id"],
            "definition_origin": {"kind": "service", "contract": "ask", "revision": "v1", "payload_hash": "sha256:" + "0" * 64},
            "deadline_at": datetime.now(timezone.utc).timestamp() + 30,
            "attempt_ordinal": reservation["physical_attempt_ordinal"],
        },
    }
    submitted = broker.submit(raw, owner)
    approved = broker.decide(submitted["operation_id"], "approve", submitted["revision"], owner)
    operation = broker.store.operation(approved["operation_id"])
    node = Principal(PrincipalKind.NODE, operation["placement"].removeprefix("node:"))
    claimed = broker.claim(node, reservation["child_invocation_id"])
    assert claimed["operations"][0]["operation_id"] == operation["operation_id"]
    return operation["operation_id"]


@pytest.mark.parametrize(
    ("column", "forged"),
    (
        ("target_ref", "deployment-revision:forged"),
        ("envelope_sha256", "sha256:" + "f" * 64),
        ("placement", "node:forged"),
        ("policy_version", 999),
        ("native_id", "invocation-forged"),
        ("claimed_by", "forged"),
        ("principal_identity", "forged-owner"),
        ("parent_operation_id", "op_forged_parent"),
    ),
)
def test_claimed_child_reconstruction_cross_binds_signed_warrant(
    tmp_path: Path, column: str, forged: object,
) -> None:
    db = Database(tmp_path / f"signed-child-{column}.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"start-{column}",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"reserve-{column}",
        execution_id=execution["id"],
    )["reservation"]
    controller.claim_reservation(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"claim-{reservation['attempt_id']}",
        reservation=reservation,
    )
    child_id = _broker_child(broker, reservation, suffix=column)
    assert broker.reconstruct_claimed_inference_child(child_id) is not None

    with db._connection() as conn:
        conn.execute(f"UPDATE kernel_operations SET {column}=? WHERE operation_id=?", (forged, child_id))
    assert broker.reconstruct_claimed_inference_child(child_id) is None


def test_claimed_child_reconstruction_rejects_revoked_expired_and_unsigned_rows(tmp_path: Path) -> None:
    db = Database(tmp_path / "signed-child-negative.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-negative-child",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-negative-child",
        execution_id=execution["id"],
    )["reservation"]
    controller.claim_reservation(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"claim-{reservation['attempt_id']}",
        reservation=reservation,
    )
    child_id = _broker_child(broker, reservation, suffix="negative")

    with db._connection() as conn:
        conn.execute("UPDATE kernel_operations SET warrant_revoked=1 WHERE operation_id=?", (child_id,))
    assert broker.reconstruct_claimed_inference_child(child_id) is None

    # A row that merely resembles a claimed inference child has no signed
    # admission authority, even if all of its public columns look plausible.
    with db._connection() as conn:
        source = conn.execute("SELECT * FROM kernel_operations WHERE operation_id=?", (child_id,)).fetchone()
        columns = tuple(source.keys())
        values = dict(source)
        values.update(
            operation_id="op_unsigned_child",
            request_id="request-unsigned-child",
            idempotency_key="unsigned-child",
            warrant_json="{}",
            warrant_revoked=0,
        )
        conn.execute(
            f"INSERT INTO kernel_operations({','.join(columns)}) VALUES({','.join('?' for _ in columns)})",
            tuple(values[name] for name in columns),
        )
    assert broker.reconstruct_claimed_inference_child("op_unsigned_child") is None


def test_broker_unstarted_closure_cross_binds_principal_native_and_target(tmp_path: Path) -> None:
    from holdspeak.kernel.model import KernelRefused

    db = Database(tmp_path / "unstarted-closure-authority.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-unstarted-authority",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-unstarted-authority",
        execution_id=execution["id"],
    )["reservation"]
    owner = Principal(PrincipalKind.OWNER, "owner")
    raw = {
        "request_schema": 1, "request_id": "request-unstarted-authority",
        "idempotency_key": reservation["child_invocation_id"],
        "operation": {"name": "inference.invoke", "version": 1}, "target": {},
        "arguments": {
            "invocation_id": reservation["child_invocation_id"],
            "deployment_revision": reservation["deployment_revision_id"],
            "definition_origin": {"kind": "service", "contract": "ask", "revision": "v1", "payload_hash": "sha256:" + "0" * 64},
            "deadline_at": datetime.now(timezone.utc).timestamp() + 30,
            "attempt_ordinal": reservation["physical_attempt_ordinal"],
        },
    }
    submitted = broker.submit(raw, owner)
    attacks = (
        {"principal": Principal(PrincipalKind.OWNER, "attacker"), "native_id": reservation["child_invocation_id"], "deployment_revision_id": reservation["deployment_revision_id"]},
        {"principal": owner, "native_id": "invoke_cross_child", "deployment_revision_id": reservation["deployment_revision_id"]},
        {"principal": owner, "native_id": reservation["child_invocation_id"], "deployment_revision_id": "deployment-revision-cross-target"},
    )
    for attack in attacks:
        with pytest.raises(KernelRefused) as refused:
            broker.refuse_unstarted_inference_child(
                submitted["operation_id"], expected_state="awaiting_decision", **attack,
            )
        assert refused.value.reason == "inference_unstarted_closure_conflict"
    closed = broker.refuse_unstarted_inference_child(
        submitted["operation_id"], expected_state="awaiting_decision",
        principal=owner, native_id=reservation["child_invocation_id"],
        deployment_revision_id=reservation["deployment_revision_id"],
    )
    assert (closed["state"], closed["receipt"]["state"]) == ("refused", "refused")


def test_unstarted_closure_has_only_the_composed_runner_caller() -> None:
    root = Path(__file__).resolve().parents[2] / "holdspeak"
    callers = []
    for source in root.rglob("*.py"):
        text = source.read_text()
        if ".refuse_unstarted_inference_child(" in text:
            callers.append(source.relative_to(root).as_posix())
    assert callers == ["kernel/inference_runner.py"]
    runner = (root / "kernel/inference_runner.py").read_text()
    assert runner.count(".refuse_unstarted_inference_child(") == 2


class _Adapter:
    def dispatch(self, _engine: object, _payload: object, _cancelled: object) -> str:
        return "routed-result"

    def cancel(self) -> str:
        return "cancelled"


class _RaisingAdapter(_Adapter):
    def __init__(self, error: BaseException) -> None:
        self.error = error

    def dispatch(self, _engine: object, _payload: object, _cancelled: object) -> str:
        raise self.error


def test_bound_pre_dispatch_hook_failure_settles_pre_send_without_followup(tmp_path: Path) -> None:
    db = Database(tmp_path / "bound-pre-dispatch-failure.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-bound-pre-dispatch",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-bound-pre-dispatch",
        execution_id=execution["id"],
    )["reservation"]

    def refuse_before_send(*_args: object) -> None:
        raise RuntimeError("domain fence refused")

    payload = {"question": "private"}
    outcome = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    ).invoke(InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
        before_physical_dispatch=refuse_before_send,
    ), _Adapter())
    assert (outcome.outcome, outcome.runner_signal, outcome.send_phase) == (
        "failed", "unclassified_pre_send", "pre_send",
    )
    receipt = controller.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert (
        receipt["state"], receipt["disposition"],
        sum(item["physical_attempts"] for item in receipt["considerations"]),
    ) == (
        "terminal", "policy_refused", 0,
    )
    assert receipt["considerations"][0]["status"] == "not_started"
    with pytest.raises(ConflictError):
        controller.reserve_next_attempt(
            INFERENCE_FALLBACK_AUTHORITY, command_id="forbidden-bound-followup",
            execution_id=execution["id"],
        )


@pytest.mark.parametrize("failure_site", ["engine", "hook"])
@pytest.mark.parametrize(
    "error",
    [
        ProviderIndeterminate(),
        ProviderCompatibilityRetry("max_completion_tokens"),
        ProviderKnownNoGenerationTransient(),
        ProviderPermanentNoGeneration(),
        ProviderPermissionDenied(),
        InferenceInvalidTypedOutput(),
    ],
    ids=["indeterminate", "compatibility", "transient", "permanent", "permission", "typed-output"],
)
def test_typed_provider_signals_before_intent_close_conservatively(
    tmp_path: Path, failure_site: str, error: BaseException,
) -> None:
    db = Database(tmp_path / f"pre-intent-{failure_site}-{type(error).__name__}.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"start-pre-intent-{failure_site}-{type(error).__name__}",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"reserve-pre-intent-{failure_site}-{type(error).__name__}",
        execution_id=execution["id"],
    )["reservation"]

    def engine_factory(_revision: object, **_kw: object) -> object:
        if failure_site == "engine":
            raise error
        return object()

    def before_send(*_args: object) -> None:
        if failure_site == "hook":
            raise error

    payload = {"question": "private"}
    outcome = InferenceRunner(
        broker, db, engine_factory=engine_factory,
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    ).invoke(InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
        before_physical_dispatch=before_send,
    ), _Adapter())
    assert (outcome.outcome, outcome.runner_signal, outcome.send_phase) == (
        "failed", "unclassified_pre_send", "pre_send",
    )
    receipt = controller.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert (receipt["state"], receipt["disposition"]) == ("terminal", "policy_refused")
    assert receipt["considerations"][0]["status"] == "not_started"
    assert receipt["considerations"][0]["physical_attempts"] == 0
    with pytest.raises(ConflictError):
        controller.reserve_next_attempt(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"forbidden-pre-intent-{failure_site}-{type(error).__name__}",
            execution_id=execution["id"],
        )


def test_bound_pre_send_cancellation_settles_owner_cancelled(tmp_path: Path) -> None:
    db = Database(tmp_path / "bound-pre-send-cancel.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-bound-pre-send-cancel",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-bound-pre-send-cancel",
        execution_id=execution["id"],
    )["reservation"]
    loading, release = threading.Event(), threading.Event()

    def engine_factory(_revision: object, **_kw: object) -> object:
        loading.set()
        assert release.wait(2)
        return object()

    runner = InferenceRunner(
        broker, db, engine_factory=engine_factory,
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    )
    payload = {"question": "private"}
    request = InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
    )
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(runner.invoke, request, _Adapter())
        assert loading.wait(2)
        assert runner.cancel(reservation["child_invocation_id"]) in {"pending", "cancelled"}
        release.set()
        outcome = future.result(timeout=2)
    assert (outcome.outcome, outcome.runner_signal, outcome.send_phase) == (
        "cancelled", "none", "pre_send",
    )
    receipt = controller.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert (receipt["state"], receipt["disposition"]) == ("terminal", "owner_cancelled")
    assert receipt["considerations"][0]["status"] == "not_started"


@pytest.mark.parametrize(
    "publisher",
    [
        lambda _value: "not a result ref",
        lambda _value: (_ for _ in ()).throw(RuntimeError("projection failed")),
    ],
)
def test_provider_returned_projection_failure_is_effect_indeterminate(
    tmp_path: Path, publisher: object,
) -> None:
    db = Database(tmp_path / "projection-effect-indeterminate.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-projection-effect",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-projection-effect",
        execution_id=execution["id"],
    )["reservation"]
    payload = {"question": "private"}
    outcome = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    ).invoke(InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
    ), _Adapter(), publish=publisher)
    assert (outcome.outcome, outcome.runner_signal, outcome.send_phase) == (
        "failed", "effect_indeterminate", "provider_returned",
    )
    receipt = controller.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert (
        receipt["state"], receipt["disposition"],
        sum(item["physical_attempts"] for item in receipt["considerations"]),
    ) == (
        "terminal", "effect_indeterminate", 1,
    )
    with pytest.raises(ConflictError):
        controller.reserve_next_attempt(
            INFERENCE_FALLBACK_AUTHORITY, command_id="forbidden-effect-followup",
            execution_id=execution["id"],
        )


def test_journal_cannot_mint_runner_disposition_evidence_from_public_strings(tmp_path: Path) -> None:
    db = Database(tmp_path / "journal-runner-evidence-bypass.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-journal-bypass",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-journal-bypass",
        execution_id=execution["id"],
    )["reservation"]
    controller.claim_reservation(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"claim-{reservation['attempt_id']}",
        reservation=reservation,
    )
    child_id = _broker_child(broker, reservation, suffix="journal-bypass")
    controller.bind_admitted_child(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"bind-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"], child_operation_id=child_id,
    )
    controller.mark_dispatch_intent(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"dispatch-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
    )
    assert "runner_signal" not in inspect.signature(broker.store.transition_and_receipt).parameters
    assert "send_phase" not in inspect.signature(broker.store.transition_and_receipt).parameters
    assert "runner_signal" not in inspect.signature(broker.store.add_receipt).parameters
    assert "send_phase" not in inspect.signature(broker.store.add_receipt).parameters
    operation = broker.store.operation(child_id)
    with pytest.raises(TypeError):
        broker.store.transition_and_receipt(
            child_id, int(operation["revision"]), "failed", "failed", "",
            runner_signal="provider_permanent_no_generation",
            send_phase="provider_no_generation",
        )
    with pytest.raises(TypeError):
        broker.store.add_receipt(
            child_id, "failed", "failed", "",
            runner_signal="provider_permanent_no_generation",
            send_phase="provider_no_generation",
        )
    broker.store.transition_and_receipt(
        child_id, int(operation["revision"]), "failed", "failed", "",
    )
    reconstructed = broker.reconstruct_inference_child_receipt(child_id)
    assert reconstructed["terminal_attestation"]["runner_signal"] == "none"
    assert reconstructed["terminal_attestation"]["send_phase"] == "pre_send"
    with pytest.raises(ConflictError) as refused:
        controller.settle_attempt(
            INFERENCE_FALLBACK_AUTHORITY, command_id="settle-journal-bypass",
            attempt_id=reservation["attempt_id"],
        )
    assert refused.value.code == "inference_route_disposition_evidence_invalid"


def test_claim_bind_and_dispatch_intent_are_one_shot_and_restart_safe(tmp_path: Path) -> None:
    db = Database(tmp_path / "claim-bind-dispatch.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service, kernel_child_reader=broker.reconstruct_claimed_inference_child)
    execution = controller.start_execution(INFERENCE_FALLBACK_AUTHORITY, command_id="start-cbd", operation_plan_id=operation_plan_id)
    reservation = controller.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-cbd", execution_id=execution["id"])["reservation"]

    claim_command = f"claim-{reservation['attempt_id']}"
    bind_command = f"bind-{reservation['attempt_id']}"
    dispatch_command = f"dispatch-{reservation['attempt_id']}"
    claim = controller.claim_reservation(INFERENCE_FALLBACK_AUTHORITY, command_id=claim_command, reservation=reservation)
    restarted = InferenceFallbackController(db, route_plan_service=route_service, kernel_child_reader=broker.reconstruct_claimed_inference_child)
    assert restarted.claim_reservation(INFERENCE_FALLBACK_AUTHORITY, command_id=claim_command, reservation=reservation) == claim
    wrong_nonce = {**reservation, "nonce": "x" * 48}
    with pytest.raises(ConflictError) as crossed:
        controller.claim_reservation(INFERENCE_FALLBACK_AUTHORITY, command_id="claim-crossed", reservation=wrong_nonce)
    assert crossed.value.code == "inference_route_execution_command_conflict"
    with pytest.raises(ConflictError) as twice:
        controller.claim_reservation(INFERENCE_FALLBACK_AUTHORITY, command_id="claim-twice", reservation=reservation)
    assert twice.value.code == "inference_route_execution_command_conflict"

    copied_command = "dispatch-copied-claim"
    copied_request = _command_hash({"action": "dispatch_intent", "command_id": copied_command, "attempt_id": reservation["attempt_id"]})
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO inference_route_execution_commands VALUES (?,?,?,?,?,?,?)",
            (copied_command, "dispatch_intent", copied_request, execution["id"], json.dumps(claim, sort_keys=True, separators=(",", ":")), _command_hash(claim), "2026-08-22T00:00:00Z"),
        )
    with pytest.raises(ConflictError) as copied:
        controller.mark_dispatch_intent(INFERENCE_FALLBACK_AUTHORITY, command_id=copied_command, attempt_id=reservation["attempt_id"])
    assert copied.value.code == "inference_route_execution_command_conflict"

    child = _broker_child(broker, reservation, suffix="cbd")
    bound = controller.bind_admitted_child(INFERENCE_FALLBACK_AUTHORITY, command_id=bind_command, attempt_id=reservation["attempt_id"], child_operation_id=child)
    assert restarted.bind_admitted_child(INFERENCE_FALLBACK_AUTHORITY, command_id=bind_command, attempt_id=reservation["attempt_id"], child_operation_id=child) == bound
    with pytest.raises(ConflictError) as rebound:
        controller.bind_admitted_child(INFERENCE_FALLBACK_AUTHORITY, command_id="bind-again", attempt_id=reservation["attempt_id"], child_operation_id=child)
    assert rebound.value.code == "inference_route_execution_command_conflict"

    intent = controller.mark_dispatch_intent(INFERENCE_FALLBACK_AUTHORITY, command_id=dispatch_command, attempt_id=reservation["attempt_id"])
    assert restarted.mark_dispatch_intent(INFERENCE_FALLBACK_AUTHORITY, command_id=dispatch_command, attempt_id=reservation["attempt_id"]) == intent
    with db._connection() as conn:
        row = conn.execute("SELECT state,dispatch_intent_at FROM inference_route_attempts WHERE id=?", (reservation["attempt_id"],)).fetchone()
        assert row["state"] == "dispatch_intent" and row["dispatch_intent_at"]
    stopped = controller.request_stop(INFERENCE_FALLBACK_AUTHORITY, command_id="stop-after-intent", execution_id=execution["id"])
    assert stopped["effect"]["elected_state"] == "stopping"
    assert stopped["execution"]["state"] == "stopping"
    with db._connection() as conn:
        conn.execute("UPDATE kernel_operations SET state='succeeded',revision=revision+1 WHERE operation_id=?", (child,))
        conn.execute(
            "INSERT INTO kernel_receipts VALUES (?,?,?,?,?,?)",
            ("receipt-cbd", child, "succeeded", "succeeded", "result:success", 2.0),
        )
    replay_stop = restarted.request_stop(INFERENCE_FALLBACK_AUTHORITY, command_id="stop-after-intent", execution_id=execution["id"])
    assert replay_stop["effect"] == stopped["effect"]
    assert replay_stop["execution"]["state"] == "stopping"
    assert replay_stop["execution"]["terminal_outcome"] is None


def test_stop_and_deadline_fence_reservation_claim(tmp_path: Path) -> None:
    db = Database(tmp_path / "claim-fences.db")
    operation_plan_id, route_service = _operation_plan(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(INFERENCE_FALLBACK_AUTHORITY, command_id="start-stop", operation_plan_id=operation_plan_id)
    reservation = controller.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-stop", execution_id=execution["id"])["reservation"]
    controller.request_stop(INFERENCE_FALLBACK_AUTHORITY, command_id="stop-before-claim", execution_id=execution["id"])
    with pytest.raises(ConflictError) as stopped:
        controller.claim_reservation(INFERENCE_FALLBACK_AUTHORITY, command_id=f"claim-{reservation['attempt_id']}", reservation=reservation)
    assert stopped.value.code == "inference_route_execution_terminal"

    db2 = Database(tmp_path / "claim-deadline.db")
    operation_plan_id2, route_service2 = _operation_plan(db2)
    live = InferenceFallbackController(db2, route_plan_service=route_service2)
    execution2 = live.start_execution(INFERENCE_FALLBACK_AUTHORITY, command_id="start-deadline", operation_plan_id=operation_plan_id2)
    reservation2 = live.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-deadline", execution_id=execution2["id"])["reservation"]
    late = InferenceFallbackController(db2, route_plan_service=route_service2, clock=lambda: datetime.now(timezone.utc) + timedelta(days=1))
    with pytest.raises(ConflictError) as expired:
        late.claim_reservation(INFERENCE_FALLBACK_AUTHORITY, command_id=f"claim-{reservation2['attempt_id']}", reservation=reservation2)
    assert expired.value.code == "inference_route_deadline_exhausted"


def test_deadline_terminal_then_stop_preserves_deadline_winner_and_stop_replay_is_verified(tmp_path: Path) -> None:
    db = Database(tmp_path / "deadline-stop.db")
    operation_plan_id, route_service = _operation_plan(db)
    live = InferenceFallbackController(db, route_plan_service=route_service)
    execution = live.start_execution(INFERENCE_FALLBACK_AUTHORITY, command_id="start-deadline-stop", operation_plan_id=operation_plan_id)
    late = InferenceFallbackController(db, route_plan_service=route_service, clock=lambda: datetime.now(timezone.utc) + timedelta(days=1))
    terminal = late.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-deadline-stop", execution_id=execution["id"])
    assert terminal["terminal"] == "deadline_exhausted"
    stopped = late.request_stop(INFERENCE_FALLBACK_AUTHORITY, command_id="stop-after-deadline", execution_id=execution["id"])
    assert stopped["effect"]["observed_state"] == "terminal"
    assert stopped["effect"]["elected_state"] == "terminal"
    assert stopped["execution"]["terminal_disposition"] == "deadline_exhausted"
    assert stopped["execution"]["stop_requested"] is False
    with db._connection() as conn:
        conn.execute("DROP TRIGGER inference_route_execution_commands_no_update")
        forged = {**stopped["effect"], "elected_state": "stopped"}
        conn.execute(
            "UPDATE inference_route_execution_commands SET effect_json=?,effect_sha256=? WHERE command_id='stop-after-deadline'",
            (json.dumps(forged, sort_keys=True, separators=(",", ":")), _command_hash(forged)),
        )
    with pytest.raises(ConflictError) as invalid:
        late.request_stop(INFERENCE_FALLBACK_AUTHORITY, command_id="stop-after-deadline", execution_id=execution["id"])
    assert invalid.value.code == "inference_route_execution_command_integrity_invalid"


def test_stop_and_dispatch_intent_race_has_one_coherent_winner(tmp_path: Path) -> None:
    db = Database(tmp_path / "stop-intent-race.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service, kernel_child_reader=broker.reconstruct_claimed_inference_child)
    execution = controller.start_execution(INFERENCE_FALLBACK_AUTHORITY, command_id="start-intent-race", operation_plan_id=operation_plan_id)
    reservation = controller.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-intent-race", execution_id=execution["id"])["reservation"]
    controller.claim_reservation(INFERENCE_FALLBACK_AUTHORITY, command_id=f"claim-{reservation['attempt_id']}", reservation=reservation)
    child = _broker_child(broker, reservation, suffix="race")
    controller.bind_admitted_child(INFERENCE_FALLBACK_AUTHORITY, command_id=f"bind-{reservation['attempt_id']}", attempt_id=reservation["attempt_id"], child_operation_id=child)

    def intent() -> str:
        try:
            controller.mark_dispatch_intent(INFERENCE_FALLBACK_AUTHORITY, command_id=f"dispatch-{reservation['attempt_id']}", attempt_id=reservation["attempt_id"])
            return "intent"
        except ConflictError as exc:
            return exc.code

    def stop() -> str:
        return controller.request_stop(INFERENCE_FALLBACK_AUTHORITY, command_id="stop-intent-race", execution_id=execution["id"])["execution"]["state"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [pool.submit(intent), pool.submit(stop)]
        outcomes = [future.result() for future in results]
    with db._connection() as conn:
        head = conn.execute("SELECT state FROM inference_route_executions WHERE id=?", (execution["id"],)).fetchone()["state"]
        attempt = conn.execute("SELECT state FROM inference_route_attempts WHERE id=?", (reservation["attempt_id"],)).fetchone()["state"]
    assert (head, attempt) in {("stopped", "admitted"), ("stopping", "dispatch_intent")}
    assert "intent" in outcomes or "inference_route_execution_terminal" in outcomes


def test_stop_transition_chain_refuses_alternate_command_and_revision_forgery(tmp_path: Path) -> None:
    db = Database(tmp_path / "stop-chain.db")
    operation_plan_id, route_service = _operation_plan(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(INFERENCE_FALLBACK_AUTHORITY, command_id="start-stop-chain", operation_plan_id=operation_plan_id)
    controller.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-stop-chain", execution_id=execution["id"])
    stopped = controller.request_stop(INFERENCE_FALLBACK_AUTHORITY, command_id="stop-chain", execution_id=execution["id"])

    copied = dict(stopped["effect"])
    alternate = "stop-chain-alternate"
    request_hash = _command_hash({"action": "stop", "command_id": alternate, "execution_id": execution["id"]})
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO inference_route_execution_commands VALUES (?,?,?,?,?,?,?)",
            (alternate, "stop", request_hash, execution["id"], json.dumps(copied, sort_keys=True, separators=(",", ":")), _command_hash(copied), "2026-08-22T00:00:00Z"),
        )
    with pytest.raises(ConflictError) as substituted:
        controller.request_stop(INFERENCE_FALLBACK_AUTHORITY, command_id=alternate, execution_id=execution["id"])
    assert substituted.value.code == "inference_route_execution_command_integrity_invalid"

    with db._connection() as conn:
        conn.execute("UPDATE inference_route_executions SET revision=999 WHERE id=?", (execution["id"],))
    with pytest.raises(ConflictError) as revision:
        controller.request_stop(INFERENCE_FALLBACK_AUTHORITY, command_id="stop-chain", execution_id=execution["id"])
    assert revision.value.code == "inference_route_execution_integrity_invalid"


def test_composed_runner_uses_ticket_only_and_real_signed_kernel_child(tmp_path: Path) -> None:
    db = Database(tmp_path / "routed-runner.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db,
        route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(INFERENCE_FALLBACK_AUTHORITY, command_id="start-routed-runner", operation_plan_id=operation_plan_id)
    reservation = controller.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-routed-runner", execution_id=execution["id"])["reservation"]
    payload = {"question": "private"}
    request = InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30,
        payload=payload,
        invocation_id=reservation["child_invocation_id"],
        attempt_ordinal=reservation["physical_attempt_ordinal"],
        route_attempt_reservation=reservation,
    )
    without_runtime = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(), principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner")
    )
    with pytest.raises(Exception, match="inference_routed_attempt_runtime_missing"):
        without_runtime.invoke(request, _Adapter())
    assert broker.store.operation_for_native(reservation["child_invocation_id"]) is None

    runner = InferenceRunner(
        broker,
        db,
        engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    )
    outcome = runner.invoke(request, _Adapter())
    assert outcome.outcome == "succeeded"
    child = broker.reconstruct_claimed_inference_child(outcome.operation_id)
    # The runner has already terminalized the kernel child, so the claimed-only
    # reconstruction correctly stops authorizing it after bind.
    assert child is None
    with db._connection() as conn:
        attempt = conn.execute("SELECT * FROM inference_route_attempts WHERE id=?", (reservation["attempt_id"],)).fetchone()
        assert attempt["child_operation_id"] == outcome.operation_id
        assert attempt["state"] == "terminal"
    settled = controller.settle_attempt(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"settle-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
    )
    assert settled["outcome"] == "succeeded"
    assert settled["disposition"] == "owner_terminal"
    assert settled["route_execution_receipt"]["winning_attempt_id"] == reservation["attempt_id"]
    assert controller.settle_attempt(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"settle-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
    ) == settled


def test_dispatch_intent_without_receipt_reconciles_indeterminate_and_never_advances(tmp_path: Path) -> None:
    db = Database(tmp_path / "reconcile-missing-receipt.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-reconcile-missing",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-reconcile-missing",
        execution_id=execution["id"],
    )["reservation"]
    controller.claim_reservation(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"claim-{reservation['attempt_id']}",
        reservation=reservation,
    )
    child_id = _broker_child(broker, reservation, suffix="reconcile-missing")
    controller.bind_admitted_child(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"bind-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"], child_operation_id=child_id,
    )
    controller.mark_dispatch_intent(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"dispatch-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
    )
    effect = controller.reconcile_dispatch_intent(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reconcile-missing",
        attempt_id=reservation["attempt_id"],
    )
    assert (effect["disposition"], effect["outcome"], effect["terminal_state"]) == (
        "dispatch_outcome_unknown", "indeterminate", "terminal",
    )
    assert effect["route_execution_receipt"]["attempts"][0]["child_receipt_sha256"] is None
    with pytest.raises(ConflictError) as no_advance:
        controller.reserve_next_attempt(
            INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-after-unknown",
            execution_id=execution["id"],
        )
    assert no_advance.value.code == "inference_route_execution_terminal"


def test_terminal_receipt_attestation_rejects_paired_operation_and_receipt_forgery(tmp_path: Path) -> None:
    db = Database(tmp_path / "terminal-attestation-forgery.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-attestation-forgery",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-attestation-forgery",
        execution_id=execution["id"],
    )["reservation"]
    payload = {"question": "attestation"}
    result = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    ).invoke(InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
    ), _Adapter())
    child_id = result.operation_id
    with db._connection() as conn:
        conn.execute("UPDATE kernel_operations SET state='failed' WHERE operation_id=?", (child_id,))
        conn.execute("UPDATE kernel_receipts SET state='failed',outcome='failed',result_ref='' WHERE operation_id=?", (child_id,))
    assert broker.reconstruct_inference_child_receipt(child_id) is None
    with pytest.raises(ConflictError) as forged:
        controller.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert forged.value.code == "inference_route_execution_integrity_invalid"


def test_generic_post_intent_exception_is_unknown_terminal_with_exactly_one_child(tmp_path: Path) -> None:
    db = Database(tmp_path / "generic-post-intent.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-generic-post",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-generic-post",
        execution_id=execution["id"],
    )["reservation"]
    payload = {"question": "private"}
    runner = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    )
    outcome = runner.invoke(InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
    ), _RaisingAdapter(RuntimeError("ambiguous provider failure")))
    assert outcome.outcome == "failed"
    with db._connection() as conn:
        attempts = conn.execute("SELECT * FROM inference_route_attempts WHERE execution_id=?", (execution["id"],)).fetchall()
        head = conn.execute("SELECT * FROM inference_route_executions WHERE id=?", (execution["id"],)).fetchone()
    assert len(attempts) == 1
    assert attempts[0]["disposition"] == "dispatch_outcome_unknown"
    assert (head["state"], head["terminal_outcome"]) == ("terminal", "failed")


def test_compatibility_signal_survives_crash_after_kernel_receipt_and_reserves_new_child(tmp_path: Path) -> None:
    class _CrashAfterReceipt(RoutedAttemptRuntime):
        def settle(self, reservation: dict[str, object], outcome: object) -> dict[str, object]:
            raise RuntimeError("crash-after-kernel-receipt")

    db = Database(tmp_path / "compatibility-crash.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-compat-crash",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-compat-crash",
        execution_id=execution["id"],
    )["reservation"]
    payload = {"question": "private"}
    runner = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=_CrashAfterReceipt(controller),
    )
    with pytest.raises(RuntimeError, match="crash-after-kernel-receipt"):
        runner.invoke(InvocationRequest(
            deployment_revision=reservation["deployment_revision_id"],
            definition_origin=ServiceContract.for_payload("ask", "v1", payload),
            deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
            invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
            route_attempt_reservation=reservation,
        ), _RaisingAdapter(ProviderCompatibilityRetry("json_mode")))

    restarted = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    settled = restarted.settle_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"settle-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
    )
    assert (settled["disposition"], settled["terminal_state"]) == (
        "known_no_generation_transient", "active",
    )
    follow = restarted.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-compat-followup",
        execution_id=execution["id"],
    )["reservation"]
    assert (follow["physical_attempt_ordinal"], follow["leg_attempt_ordinal"], follow["purpose"]) == (2, 2, "compatibility")


def test_routed_submit_refusal_is_attested_and_settled_pre_send_with_zero_egress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = Database(tmp_path / "pre-send-refusal.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-pre-send-refusal",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-pre-send-refusal",
        execution_id=execution["id"],
    )["reservation"]
    codec = broker._specs[("inference.invoke", 1)].codec

    def refuse_after_decode(*_args: object, **_kwargs: object) -> None:
        from holdspeak.kernel.model import KernelRefused
        raise KernelRefused("admitted_test_refusal")

    monkeypatch.setattr(codec, "admit", refuse_after_decode)
    adapter = _Adapter()
    calls = 0
    original_dispatch = adapter.dispatch

    def counted_dispatch(*args: object) -> str:
        nonlocal calls
        calls += 1
        return original_dispatch(*args)

    monkeypatch.setattr(adapter, "dispatch", counted_dispatch)
    payload = {"question": "private"}
    runner = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    )
    outcome = runner.invoke(InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
    ), adapter)
    assert outcome.outcome == "refused"
    assert calls == 0
    with db._connection() as conn:
        attempt = conn.execute("SELECT * FROM inference_route_attempts WHERE id=?", (reservation["attempt_id"],)).fetchone()
        head = conn.execute("SELECT * FROM inference_route_executions WHERE id=?", (execution["id"],)).fetchone()
    assert (attempt["state"], attempt["send_phase"], attempt["disposition"]) == (
        "terminal", "pre_send", "policy_refused",
    )
    assert (head["state"], head["terminal_outcome"]) == ("terminal", "refused")
    receipt = controller.get_route_execution_receipt(
        Principal(PrincipalKind.OWNER, "owner"), execution_id=execution["id"]
    )
    assert receipt["considerations"][0]["status"] == "not_started"
    assert receipt["considerations"][0]["physical_attempts"] == 0
    assert receipt["all_models_physically_failed"] is False


@pytest.mark.parametrize("stage", ("decision_exception", "claim_empty"))
def test_routed_pre_child_failure_is_broker_cas_closed_and_restart_adoptable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str,
) -> None:
    db = Database(tmp_path / f"pre-child-{stage}.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"start-{stage}",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"reserve-{stage}",
        execution_id=execution["id"],
    )["reservation"]
    if stage == "decision_exception":
        monkeypatch.setattr(
            broker, "decide",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("opaque decision crash")),
        )
    else:
        monkeypatch.setattr(broker, "claim", lambda *_args, **_kwargs: {"operations": []})
    calls = 0

    class CountingAdapter(_Adapter):
        def dispatch(self, *args: object) -> str:
            nonlocal calls
            calls += 1
            return super().dispatch(*args)

    payload = {"question": "private"}
    outcome = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    ).invoke(InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
    ), CountingAdapter())
    assert (outcome.outcome, outcome.send_phase, calls) == ("refused", "pre_send", 0)
    reconstructed = broker.reconstruct_inference_child_receipt(outcome.operation_id)
    assert reconstructed is not None
    assert reconstructed["terminal_attestation"]["send_phase"] == "pre_send"
    restarted = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    receipt = restarted.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert receipt["state"] == "terminal"
    assert receipt["considerations"][0]["status"] == "not_started"
    assert receipt["all_models_physically_failed"] is False


def test_claim_empty_race_with_real_claim_elects_indeterminate_and_never_falls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = Database(tmp_path / "claim-empty-race.db")
    operation_plan_id, route_service = _two_leg_operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-claim-race",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-claim-race",
        execution_id=execution["id"],
    )["reservation"]
    real_claim = broker.claim

    def lose_claim_response(*args: object, **kwargs: object) -> dict[str, object]:
        claimed = real_claim(*args, **kwargs)
        assert claimed["operations"]
        return {"operations": []}

    monkeypatch.setattr(broker, "claim", lose_claim_response)
    payload = {"question": "private"}
    outcome = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    ).invoke(InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
    ), _Adapter())
    assert (outcome.outcome, outcome.send_phase) == ("indeterminate", "dispatch_intent")
    receipt = controller.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert (receipt["state"], receipt["disposition"]) == ("terminal", "dispatch_outcome_unknown")
    assert receipt["considerations"][0]["status"] == "possibly_started"
    assert receipt["all_models_physically_failed"] is False
    with pytest.raises(ConflictError) as no_fallback:
        controller.reserve_next_attempt(
            INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-after-claim-race",
            execution_id=execution["id"],
        )
    assert no_fallback.value.code == "inference_route_execution_terminal"


def test_real_claim_validation_refusal_is_adopted_as_attested_pre_send_truth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.kernel.model import KernelRefused

    db = Database(tmp_path / "claim-validation-refusal.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-claim-validation",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-claim-validation",
        execution_id=execution["id"],
    )["reservation"]
    codec = broker._specs[("inference.invoke", 1)].codec
    monkeypatch.setattr(
        codec, "validate_claim",
        lambda _operation: (_ for _ in ()).throw(KernelRefused("fixed_claim_refusal")),
    )
    payload = {"question": "private"}
    outcome = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    ).invoke(InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
    ), _Adapter())
    assert (outcome.outcome, outcome.send_phase) == ("refused", "pre_send")
    receipt = controller.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert (receipt["state"], receipt["outcome"]) == ("terminal", "refused")
    assert receipt["considerations"][0]["status"] == "not_started"


@pytest.mark.parametrize(
    ("first_context", "second_context", "advances"),
    ((32768, 65536, True), (32768, 32768, False), (65536, 32768, False)),
)
def test_initial_context_overflow_advances_only_to_strictly_larger_frozen_leg_without_attempt(
    tmp_path: Path, first_context: int, second_context: int, advances: bool,
) -> None:
    db = Database(tmp_path / f"context-overflow-{second_context}.db")
    operation_plan_id, route_service = _two_leg_operation_plan(
        db, first_eligibility="known_context_overflow",
        first_context=first_context, second_context=second_context,
    )
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"start-overflow-{second_context}",
        operation_plan_id=operation_plan_id,
    )
    effect = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id=f"reserve-overflow-{second_context}",
        execution_id=execution["id"],
    )
    with db._connection() as conn:
        attempts = conn.execute("SELECT * FROM inference_route_attempts WHERE execution_id=?", (execution["id"],)).fetchall()
        skips = conn.execute("SELECT * FROM inference_route_execution_skips WHERE execution_id=?", (execution["id"],)).fetchall()
    assert len(skips) == 1
    assert (skips[0]["route_leg_ordinal"], skips[0]["disposition"]) == (1, "context_overflow")
    if advances:
        assert len(attempts) == 1
        reservation = effect["reservation"]
        assert (reservation["route_leg_ordinal"], reservation["physical_attempt_ordinal"], reservation["purpose"]) == (2, 1, "fallback")
    else:
        assert attempts == []
        assert effect["terminal"] == "context_overflow"


def test_skip_projection_is_immutable_and_reconstructed_from_frozen_reserve_authority(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "skip-authority.db")
    operation_plan_id, route_service = _two_leg_operation_plan(
        db, first_eligibility="known_context_overflow",
        first_context=32768, second_context=65536,
    )
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-skip-authority",
        operation_plan_id=operation_plan_id,
    )
    controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-skip-authority",
        execution_id=execution["id"],
    )
    with db._connection() as conn:
        with pytest.raises(sqlite3.IntegrityError, match="immutable inference route execution skip"):
            conn.execute(
                "UPDATE inference_route_execution_skips SET reason_code='forged' WHERE execution_id=?",
                (execution["id"],),
            )
        conn.execute("DROP TRIGGER inference_route_execution_skips_no_update")
        conn.execute(
            "UPDATE inference_route_execution_skips SET reason_code='forged' WHERE execution_id=?",
            (execution["id"],),
        )
    with pytest.raises(ConflictError) as forged:
        controller.get_route_execution_receipt(
            Principal(PrincipalKind.OWNER, "owner"), execution_id=execution["id"],
        )
    assert forged.value.code == "inference_route_execution_integrity_invalid"


def test_inserted_skip_cannot_authorize_a_leg_jump_or_alter_receipt(tmp_path: Path) -> None:
    db = Database(tmp_path / "inserted-skip.db")
    operation_plan_id, route_service = _two_leg_operation_plan(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-inserted-skip",
        operation_plan_id=operation_plan_id,
    )
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO inference_route_execution_skips VALUES (?,?,?,?,?,?)",
            (f"{execution['id']}:1", execution["id"], 1, "context_overflow", "forged", datetime.now(timezone.utc).isoformat()),
        )
    with pytest.raises(ConflictError) as forged:
        controller.get_route_execution_receipt(
            Principal(PrincipalKind.OWNER, "owner"), execution_id=execution["id"],
        )
    assert forged.value.code == "inference_route_execution_integrity_invalid"


def test_every_story06_authority_table_is_sync_forbidden(tmp_path: Path) -> None:
    db = Database(tmp_path / "fallback-sync-forbidden.db")
    forbidden = (
        "inference_route_executions", "inference_route_attempts",
        "inference_route_execution_skips", "inference_route_execution_commands",
        "inference_route_execution_transitions", "kernel_inference_receipt_attestations",
    )
    pulled = SyncService(db).pull(OWNER)
    assert not (set(forbidden) & set(pulled))
    for bucket in forbidden:
        with pytest.raises(Exception) as refusal:
            SyncService(db).push(OWNER, {bucket: [{"id": "forged"}]})
        assert getattr(refusal.value, "code", "") == "sync_hub_local_bucket_forbidden"


def test_paired_attempt_state_child_and_timestamp_edits_cannot_forge_dispatch_intent(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "forged-dispatch-state.db")
    operation_plan_id, route_service = _operation_plan(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-forged-dispatch",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-forged-dispatch",
        execution_id=execution["id"],
    )["reservation"]
    forged_at = datetime.now(timezone.utc).isoformat()
    with db._connection() as conn:
        conn.execute("DROP TRIGGER inference_route_attempt_authority_immutable")
        conn.execute(
            """UPDATE inference_route_attempts
                  SET state='dispatch_intent',admitted_at=?,dispatch_intent_at=?,
                      child_operation_id='forged-child'
                WHERE id=?""",
            (forged_at, forged_at, reservation["attempt_id"]),
        )
        forged_commands = (
            (
                "alternate-claim", "claim",
                {"action": "claim", "command_id": "alternate-claim", "reservation": reservation},
                {
                    "schema": "InferenceRouteAttemptClaim@1",
                    "attempt_id": reservation["attempt_id"],
                    "child_invocation_id": reservation["child_invocation_id"],
                    "deployment_revision_id": reservation["deployment_revision_id"],
                    "physical_attempt_ordinal": reservation["physical_attempt_ordinal"],
                },
            ),
            (
                "alternate-bind", "bind",
                {"action": "bind", "command_id": "alternate-bind", "attempt_id": reservation["attempt_id"], "child_operation_id": "forged-child"},
                {"schema": "InferenceRouteChildBinding@1", "attempt_id": reservation["attempt_id"], "child_invocation_id": reservation["child_invocation_id"], "child_operation_id": "forged-child"},
            ),
            (
                "alternate-dispatch", "dispatch_intent",
                {"action": "dispatch_intent", "command_id": "alternate-dispatch", "attempt_id": reservation["attempt_id"]},
                {"schema": "InferenceRouteDispatchIntent@1", "attempt_id": reservation["attempt_id"], "child_operation_id": "forged-child", "physical_attempt_ordinal": reservation["physical_attempt_ordinal"]},
            ),
        )
        for command_id, action, request, effect in forged_commands:
            conn.execute(
                "INSERT INTO inference_route_execution_commands VALUES (?,?,?,?,?,?,?)",
                (command_id, action, _command_hash(request), execution["id"],
                 json.dumps(effect, sort_keys=True, separators=(",", ":")),
                 _command_hash(effect), forged_at),
            )
    with pytest.raises(ConflictError) as forged:
        controller.get_route_execution_receipt(
            Principal(PrincipalKind.OWNER, "owner"), execution_id=execution["id"],
        )
    assert forged.value.code == "inference_route_execution_integrity_invalid"


def test_typed_provider_permanent_failure_falls_back_to_exact_next_frozen_leg(tmp_path: Path) -> None:
    db = Database(tmp_path / "provider-permanent-fallback.db")
    operation_plan_id, route_service = _two_leg_operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-provider-permanent",
        operation_plan_id=operation_plan_id,
    )
    first = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-provider-permanent",
        execution_id=execution["id"],
    )["reservation"]
    payload = {"question": "private"}
    runner = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    )
    runner.invoke(InvocationRequest(
        deployment_revision=first["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=first["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=first,
    ), _RaisingAdapter(ProviderPermanentNoGeneration()))
    follow = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-provider-fallback",
        execution_id=execution["id"],
    )["reservation"]
    assert (follow["route_leg_ordinal"], follow["leg_attempt_ordinal"], follow["purpose"]) == (2, 1, "fallback")
    succeeded = runner.invoke(InvocationRequest(
        deployment_revision=follow["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=follow["child_invocation_id"], attempt_ordinal=2,
        route_attempt_reservation=follow,
    ), _Adapter())
    assert succeeded.outcome == "succeeded"
    receipt = controller.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert (receipt["state"], receipt["outcome"]) == ("terminal", "succeeded")
    assert receipt["winning_attempt_id"] == follow["attempt_id"]
    assert [item["status"] for item in receipt["considerations"]] == ["attempted", "attempted"]
    assert receipt["winning_boundary"] == "local"
    assert receipt["all_models_physically_failed"] is False


def test_retryable_transient_exhausts_same_leg_before_fallback_then_succeeds(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "retry-then-fallback.db")
    operation_plan_id, route_service = _two_leg_operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-retry-fallback",
        operation_plan_id=operation_plan_id,
    )
    runner = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    )
    payload = {"question": "private"}
    first = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-retry-first",
        execution_id=execution["id"],
    )["reservation"]
    runner.invoke(InvocationRequest(
        deployment_revision=first["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=first["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=first,
    ), _RaisingAdapter(ProviderKnownNoGenerationTransient()))
    retry = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-retry-second",
        execution_id=execution["id"],
    )["reservation"]
    assert (retry["route_leg_ordinal"], retry["leg_attempt_ordinal"], retry["purpose"]) == (1, 2, "retry")
    runner.invoke(InvocationRequest(
        deployment_revision=retry["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=retry["child_invocation_id"], attempt_ordinal=2,
        route_attempt_reservation=retry,
    ), _RaisingAdapter(ProviderKnownNoGenerationTransient()))
    fallback = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-retry-fallback",
        execution_id=execution["id"],
    )["reservation"]
    assert (fallback["route_leg_ordinal"], fallback["leg_attempt_ordinal"], fallback["purpose"]) == (2, 1, "fallback")
    success = runner.invoke(InvocationRequest(
        deployment_revision=fallback["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=fallback["child_invocation_id"], attempt_ordinal=3,
        route_attempt_reservation=fallback,
    ), _Adapter())
    assert success.outcome == "succeeded"
    receipt = controller.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert [item["leg_attempt_ordinal"] for item in receipt["attempts"]] == [1, 2, 1]
    assert receipt["winning_attempt_id"] == fallback["attempt_id"]


def test_invalid_typed_output_is_attested_content_free_and_policy_retryable(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "invalid-typed-output.db")
    operation_plan_id, route_service = _operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-invalid-typed",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-invalid-typed",
        execution_id=execution["id"],
    )["reservation"]
    payload = {"secret": "must-not-enter-evidence"}
    InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    ).invoke(InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
    ), _RaisingAdapter(InferenceInvalidTypedOutput()))
    with db._connection() as conn:
        attempt = conn.execute(
            "SELECT * FROM inference_route_attempts WHERE id=?", (reservation["attempt_id"],),
        ).fetchone()
    assert (attempt["disposition"], attempt["send_phase"]) == (
        "invalid_typed_output", "provider_returned",
    )
    assert "must-not-enter-evidence" not in str(attempt["disposition_evidence_json"])
    follow = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-invalid-typed-retry",
        execution_id=execution["id"],
    )["reservation"]
    assert (follow["route_leg_ordinal"], follow["leg_attempt_ordinal"], follow["purpose"]) == (1, 2, "retry")


def test_all_models_failed_is_true_only_after_every_frozen_leg_physically_failed(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "all-models-failed.db")
    operation_plan_id, route_service = _two_leg_operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-all-failed",
        operation_plan_id=operation_plan_id,
    )
    runner = InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    )
    payload = {"question": "private"}
    for physical, command in ((1, "reserve-all-failed-primary"), (2, "reserve-all-failed-fallback")):
        reservation = controller.reserve_next_attempt(
            INFERENCE_FALLBACK_AUTHORITY, command_id=command,
            execution_id=execution["id"],
        )["reservation"]
        runner.invoke(InvocationRequest(
            deployment_revision=reservation["deployment_revision_id"],
            definition_origin=ServiceContract.for_payload("ask", "v1", payload),
            deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
            invocation_id=reservation["child_invocation_id"], attempt_ordinal=physical,
            route_attempt_reservation=reservation,
        ), _RaisingAdapter(ProviderPermanentNoGeneration()))
    receipt = controller.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert (receipt["state"], receipt["outcome"]) == ("terminal", "failed")
    assert receipt["all_models_physically_failed"] is True
    assert receipt["physically_failed_attempt_count"] == 2
    assert [item["status"] for item in receipt["considerations"]] == ["attempted", "attempted"]


def test_permission_denied_is_terminal_and_never_falls_back(tmp_path: Path) -> None:
    db = Database(tmp_path / "permission-terminal.db")
    operation_plan_id, route_service = _two_leg_operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-permission-terminal",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-permission-terminal",
        execution_id=execution["id"],
    )["reservation"]
    payload = {"question": "private"}
    InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    ).invoke(InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
    ), _RaisingAdapter(ProviderPermissionDenied()))
    receipt = controller.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert (receipt["state"], receipt["disposition"]) == ("terminal", "permission_denied")
    with pytest.raises(ConflictError):
        controller.reserve_next_attempt(
            INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-after-permission",
            execution_id=execution["id"],
        )


def test_local_capacity_pre_send_failure_falls_back_with_zero_physical_primary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.kernel import local_runtime_lease
    from holdspeak.kernel.model import KernelRefused

    db = Database(tmp_path / "local-capacity-fallback.db")
    operation_plan_id, route_service = _two_leg_operation_plan(db)
    broker = _configure(db)
    controller = InferenceFallbackController(
        db, route_plan_service=route_service,
        kernel_child_reader=broker.reconstruct_claimed_inference_child,
        kernel_receipt_reader=broker.reconstruct_inference_child_receipt,
    )
    execution = controller.start_execution(
        INFERENCE_FALLBACK_AUTHORITY, command_id="start-local-capacity",
        operation_plan_id=operation_plan_id,
    )
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-local-capacity",
        execution_id=execution["id"],
    )["reservation"]
    monkeypatch.setattr(
        local_runtime_lease, "acquire_local_runtime_lease",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(KernelRefused("inference_local_runtime_busy")),
    )
    payload = {"question": "private"}
    InferenceRunner(
        broker, db, engine_factory=lambda _revision, **_kw: object(),
        principal_provider=lambda: Principal(PrincipalKind.OWNER, "owner"),
        routed_attempt_runtime=RoutedAttemptRuntime(controller),
    ).invoke(InvocationRequest(
        deployment_revision=reservation["deployment_revision_id"],
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=datetime.now(timezone.utc).timestamp() + 30, payload=payload,
        invocation_id=reservation["child_invocation_id"], attempt_ordinal=1,
        route_attempt_reservation=reservation,
    ), _Adapter())
    receipt = controller.get_route_execution_receipt(OWNER, execution_id=execution["id"])
    assert receipt["considerations"][0]["status"] == "not_started"
    assert receipt["considerations"][0]["physical_attempts"] == 0
    fallback = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-after-local-capacity",
        execution_id=execution["id"],
    )["reservation"]
    assert (fallback["route_leg_ordinal"], fallback["purpose"]) == (2, "fallback")


def test_forged_self_hashed_reserve_effect_is_not_authority(tmp_path: Path) -> None:
    db = Database(tmp_path / "forged-reserve.db")
    operation_plan_id, route_service = _operation_plan(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(INFERENCE_FALLBACK_AUTHORITY, command_id="start-forged", operation_plan_id=operation_plan_id)
    command = "reserve-forged"
    request_hash = _command_hash({"action": "reserve", "command_id": command, "execution_id": execution["id"]})
    evil = {"schema": "EVIL@1", "execution_id": execution["id"], "terminal": None, "reservation": {"nonce": "attacker"}}
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO inference_route_execution_commands VALUES (?,?,?,?,?,?,?)",
            (command, "reserve", request_hash, execution["id"], json.dumps(evil, sort_keys=True, separators=(",", ":")), _command_hash(evil), "2026-08-22T00:00:00Z"),
        )
    with pytest.raises(ConflictError) as refused:
        controller.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id=command, execution_id=execution["id"])
    assert refused.value.code == "inference_route_execution_command_integrity_invalid"


@pytest.mark.parametrize(
    ("attempt_sql", "attempt_value", "execution_sql", "execution_value"),
    [
        ("reserved_token_budget=?", 1, "tokens_reserved=?", 1),
        ("deployment_revision_id=?", "deployment-revision-forged", "revision=revision+?", 1),
        ("boundary=?", "cloud", "revision=revision+?", 1),
    ],
)
def test_attempt_and_execution_paired_forgery_refuses(
    tmp_path: Path,
    attempt_sql: str,
    attempt_value: object,
    execution_sql: str,
    execution_value: object,
) -> None:
    db = Database(tmp_path / f"paired-{str(attempt_value).replace('/', '-')}.db")
    operation_plan_id, route_service = _operation_plan(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(INFERENCE_FALLBACK_AUTHORITY, command_id="start-paired", operation_plan_id=operation_plan_id)
    controller.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-paired", execution_id=execution["id"])
    with db._connection() as conn:
        conn.execute("DROP TRIGGER inference_route_attempt_authority_immutable")
        conn.execute(f"UPDATE inference_route_attempts SET {attempt_sql}", (attempt_value,))
        conn.execute(f"UPDATE inference_route_executions SET {execution_sql} WHERE id=?", (execution_value, execution["id"]))
    with pytest.raises(ConflictError) as forged:
        controller.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-paired", execution_id=execution["id"])
    assert forged.value.code == "inference_route_execution_integrity_invalid"


def test_valid_shape_changed_nonce_and_rehashed_effect_refuses(tmp_path: Path) -> None:
    db = Database(tmp_path / "nonce-effect.db")
    operation_plan_id, route_service = _operation_plan(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(INFERENCE_FALLBACK_AUTHORITY, command_id="start-nonce", operation_plan_id=operation_plan_id)
    effect = controller.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-nonce", execution_id=execution["id"])
    changed = json.loads(json.dumps(effect))
    changed["reservation"]["nonce"] = "z" * 48
    with db._connection() as conn:
        conn.execute("DROP TRIGGER inference_route_execution_commands_no_update")
        conn.execute(
            "UPDATE inference_route_execution_commands SET effect_json=?,effect_sha256=? WHERE command_id='reserve-nonce'",
            (json.dumps(changed, sort_keys=True, separators=(",", ":")), _command_hash(changed)),
        )
    with pytest.raises(ConflictError) as forged:
        controller.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-nonce", execution_id=execution["id"])
    assert forged.value.code == "inference_route_execution_integrity_invalid"


def test_nonce_hash_and_second_valid_reserve_command_cannot_replace_mint_provenance(tmp_path: Path) -> None:
    db = Database(tmp_path / "nonce-provenance.db")
    operation_plan_id, route_service = _operation_plan(db)
    controller = InferenceFallbackController(db, route_plan_service=route_service)
    execution = controller.start_execution(INFERENCE_FALLBACK_AUTHORITY, command_id="start-provenance", operation_plan_id=operation_plan_id)
    original = controller.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-provenance", execution_id=execution["id"])
    attempt_id = original["reservation"]["attempt_id"]
    with db._connection() as conn, pytest.raises(
        sqlite3.IntegrityError, match="immutable inference route attempt authority"
    ):
        conn.execute("UPDATE inference_route_attempts SET admission_nonce_sha256=? WHERE id=?", (_command_hash({"nonce": "new"}), attempt_id))

    replacement = json.loads(json.dumps(original))
    replacement["reservation"]["nonce"] = "n" * 48
    second_command = "reserve-provenance-copy"
    second_request = _command_hash({"action": "reserve", "command_id": second_command, "execution_id": execution["id"]})
    with db._connection() as conn:
        conn.execute("DROP TRIGGER inference_route_attempt_authority_immutable")
        conn.execute(
            "UPDATE inference_route_attempts SET admission_nonce_sha256=? WHERE id=?",
            (_command_hash({"nonce": replacement["reservation"]["nonce"]}), attempt_id),
        )
        conn.execute(
            "INSERT INTO inference_route_execution_commands VALUES (?,?,?,?,?,?,?)",
            (second_command, "reserve", second_request, execution["id"], json.dumps(replacement, sort_keys=True, separators=(",", ":")), _command_hash(replacement), "2026-08-22T00:00:00Z"),
        )
    with pytest.raises(ConflictError) as forged:
        controller.reserve_next_attempt(INFERENCE_FALLBACK_AUTHORITY, command_id="reserve-provenance", execution_id=execution["id"])
    assert forged.value.code == "inference_route_execution_integrity_invalid"


def test_legacy_workflow_policy_aliases_decode_without_local_retry_authority() -> None:
    from holdspeak.services.support import GraphNode, _norm_failure_policy, on_node_error, resolved_failure_policy

    carry = GraphNode("legacy-carry", "summarize", {}, _norm_failure_policy("fallbackOnDevice"))
    hold = GraphNode("legacy-hold", "summarize", {}, _norm_failure_policy("retryThenQueue"))

    assert (carry.failure_policy, resolved_failure_policy(carry), on_node_error(carry, "input")) == (
        "carry", "carry", "input"
    )
    assert (hold.failure_policy, resolved_failure_policy(hold), on_node_error(hold, "input")) == (
        "hold", "hold", None
    )
    # The alias decoder only reports a local disposition. It does not mint a
    # controller fallback/retry reservation or receipt.
    assert "fallback" not in resolved_failure_policy(carry)
    assert "retry" not in resolved_failure_policy(hold)
