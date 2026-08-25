"""Trusted startup wiring and request-principal context for the broker."""
from __future__ import annotations

import atexit
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Mapping, Sequence

from ..privileged_effects.desktop_executor import DesktopEffectExecutor
from ..principals import Principal, PrincipalKind, UNAUTHENTICATED
from .actuator import ActuatorCodec
from .broker import Broker
from .desktop_type_text import DesktopTypeTextCodec
from .external_egress import ExternalEgressCodec
from .people_store_setup import PeopleStoreSetupCodec
from .inference import InferenceInvokeCodec, InferenceRunCodec
from .inference_cancel import InferenceCancelCodec
from .journal import JournalStore
from .model import OperationSpec
from .parent_run import ParentRunCodec, ParentRunController
from .process_input import ProcessInputCodec
from .process_spawn import ProcessSpawnCodec
from .subprocess_exec import SubprocessExecCodec
from .tool_call import ToolCallCodec
from .workbench_mint import WorkbenchMintCodec
from .workbench_triage import WorkbenchTriageCodec

_principal = ContextVar("kernel_principal", default=UNAUTHENTICATED)
_broker: Broker | None = None
_database_id: int | None = None


def _dispose(broker: Broker | None) -> None:
    """Close typed-codec resources without adding type dispatch to the broker."""
    if broker is None:
        return
    controller = getattr(broker, "parent_run_controller", None)
    shutdown = getattr(controller, "shutdown", None)
    if callable(shutdown):
        shutdown()
    for spec in broker._specs.values():
        close = getattr(spec.codec, "close", None)
        if callable(close):
            close()


def _mode() -> str:
    from ..config import Config

    return str(Config.load().control_mode)


def _build(database: Any, *, clock: Any = None) -> Broker:
    store = JournalStore(database._connection, **({"clock": clock} if clock else {}))
    from ..delivery.factory_launch import default_launch_service

    tool_calls = ToolCallCodec(database.gate, _mode)
    process_input = ProcessInputCodec(database.delivery_receipts)
    desktop_type_text = DesktopTypeTextCodec(
        database.desktop_type_receipts,
        DesktopEffectExecutor(store._secret()),
    )
    launch_service = default_launch_service(database)
    process_spawn = ProcessSpawnCodec(launch_service, database.delivery_receipts)
    subprocess_exec = SubprocessExecCodec()
    external_egress = ExternalEgressCodec()
    people_store_setup = PeopleStoreSetupCodec()
    actuator = ActuatorCodec(database.actuators, _mode)
    inference = InferenceRunCodec(database, **({"clock": clock} if clock else {}))
    invocation = InferenceInvokeCodec(database, store, **({"clock": clock} if clock else {}))
    cancellation = InferenceCancelCodec(database, store)
    voice_resolve = ParentRunCodec("voice_reference_resolve", operation_name="voice_reference_resolve", **({"clock": clock} if clock else {}))
    workbench_mint = WorkbenchMintCodec()
    workbench_triage = WorkbenchTriageCodec()
    sequence_run = ParentRunCodec("sequence", **({"clock": clock} if clock else {}))
    workflow_run = ParentRunCodec("workflow", **({"clock": clock} if clock else {}))
    workbench_run = ParentRunCodec("workbench", **({"clock": clock} if clock else {}))
    decision_draft = ParentRunCodec("decision.promotion-draft", operation_name="decision.promotion-draft", **({"clock": clock} if clock else {}))
    delivery_draft = ParentRunCodec("delivery.pr-review-draft", operation_name="delivery.pr-review-draft", **({"clock": clock} if clock else {}))
    cadence_draft = ParentRunCodec("cadence.next-action-draft", operation_name="cadence.next-action-draft", **({"clock": clock} if clock else {}))
    rails_observer_batch = ParentRunCodec("rails.observer-batch", operation_name="rails.observer-batch", **({"clock": clock} if clock else {}))
    meeting_session = ParentRunCodec("meeting.session", operation_name="meeting.session", **({"clock": clock} if clock else {}))
    meeting_deferred = ParentRunCodec("meeting.deferred-intel-job", operation_name="meeting.deferred-intel-job", **({"clock": clock} if clock else {}))
    dictation_session = ParentRunCodec("dictation.session", operation_name="dictation.session", **({"clock": clock} if clock else {}))
    wake_session = ParentRunCodec("wake.session", operation_name="wake.session", **({"clock": clock} if clock else {}))
    tool_turn = ParentRunCodec("tool.turn", operation_name="tool.turn", **({"clock": clock} if clock else {}))
    specs = (
        OperationSpec(tool_calls.name, tool_calls.version, tool_calls, "agent.submit", "propose"),
        OperationSpec(process_input.name, process_input.version, process_input, "agent.submit", "propose"),
        OperationSpec(
            desktop_type_text.name,
            desktop_type_text.version,
            desktop_type_text,
            "agent.submit",
            "propose",
        ),
        OperationSpec(process_spawn.name, process_spawn.version, process_spawn, "agent.submit", "propose"),
        OperationSpec(subprocess_exec.name, subprocess_exec.version, subprocess_exec, "agent.submit", "propose"),
        OperationSpec(external_egress.name, external_egress.version, external_egress, "agent.submit", "propose"),
        OperationSpec(people_store_setup.name, people_store_setup.version, people_store_setup, "agent.submit", "propose"),
        OperationSpec(actuator.name, actuator.version, actuator, "agent.submit", "propose"),
        OperationSpec(inference.name, inference.version, inference, "agent.submit", "propose"),
        OperationSpec(invocation.name, invocation.version, invocation, "agent.submit", "propose"),
        OperationSpec(cancellation.name, cancellation.version, cancellation, "agent.submit", "propose"),
        OperationSpec(voice_resolve.name, voice_resolve.version, voice_resolve, "agent.submit", "propose"),
        OperationSpec(workbench_mint.name, workbench_mint.version, workbench_mint, "agent.submit", "propose"),
        OperationSpec(workbench_triage.name, workbench_triage.version, workbench_triage, "agent.submit", "propose"),
        OperationSpec(sequence_run.name, sequence_run.version, sequence_run, "agent.submit", "propose"),
        OperationSpec(workflow_run.name, workflow_run.version, workflow_run, "agent.submit", "propose"),
        OperationSpec(workbench_run.name, workbench_run.version, workbench_run, "agent.submit", "propose"),
        OperationSpec(decision_draft.name, decision_draft.version, decision_draft, "agent.submit", "propose"),
        OperationSpec(delivery_draft.name, delivery_draft.version, delivery_draft, "agent.submit", "propose"),
        OperationSpec(cadence_draft.name, cadence_draft.version, cadence_draft, "agent.submit", "propose"),
        OperationSpec(rails_observer_batch.name, rails_observer_batch.version, rails_observer_batch, "agent.submit", "propose"),
        OperationSpec(meeting_session.name, meeting_session.version, meeting_session, "agent.submit", "propose"),
        OperationSpec(meeting_deferred.name, meeting_deferred.version, meeting_deferred, "agent.submit", "propose"),
        OperationSpec(dictation_session.name, dictation_session.version, dictation_session, "agent.submit", "propose"),
        OperationSpec(wake_session.name, wake_session.version, wake_session, "agent.submit", "propose"),
        OperationSpec(tool_turn.name, tool_turn.version, tool_turn, "agent.submit", "propose"),
    )
    broker = Broker(store, specs, **({"clock": clock} if clock else {}))
    # Phase 143's capability/retry law is pure composition truth.  Building it
    # here makes malformed, duplicate, confusable, or schema-drifted definitions
    # a startup failure before a profile, deployment, or physical runner exists.
    # The registry is deliberately not a second gateway or execution registry.
    from ..inference_capabilities import process_inference_capability_registry
    from ..services.inference_capability_service import InferenceCapabilityApplicationService

    broker.inference_capability_registry = process_inference_capability_registry()
    broker.inference_capability_service = InferenceCapabilityApplicationService(
        broker.inference_capability_registry
    )
    # Services must never pair a runner database with a broker codec built for
    # another database singleton; invoke admission validates revisions there.
    broker.database = database
    broker.parent_run_controller = ParentRunController(broker, database,
        operation_names={"sequence":"sequence.run", "workflow":"workflow.run", "workbench":"workbench.run", "decision.promotion-draft":"decision.promotion-draft", "delivery.pr-review-draft":"delivery.pr-review-draft", "cadence.next-action-draft":"cadence.next-action-draft", "rails.observer-batch":"rails.observer-batch", "voice_reference_resolve":"voice_reference_resolve", "meeting.session":"meeting.session", "meeting.deferred-intel-job":"meeting.deferred-intel-job", "dictation.session":"dictation.session", "wake.session":"wake.session", "tool.turn":"tool.turn"}, **({"clock": clock} if clock else {}))
    # The liveness reaper runs before stage recovery: an expired claimed
    # invocation first receives its authoritative indeterminate receipt.
    from .projection_stager import ProjectionStager
    broker.projection_stager = ProjectionStager(database, broker, **({"clock": clock} if clock else {}))
    # Recovery may encounter a durable projection before a web route has ever
    # constructed its service. Register all migrated production materializers
    # before the first recovery pass, never after it.
    from .ask_projection import register as register_ask_projection
    from .recipe_projection import register as register_recipe_projection
    from .meeting_plugin_projection import register as register_meeting_plugin_projection
    from .rails_journal_projection import register as register_rails_journal_projection
    from .sequence_workflow_projection import register as register_sequence_workflow_projection
    from .workbench_projection import register as register_workbench_projection
    register_ask_projection(broker.projection_stager)
    register_recipe_projection(broker.projection_stager)
    register_rails_journal_projection(broker.projection_stager)
    register_meeting_plugin_projection(broker.projection_stager)
    register_sequence_workflow_projection(broker.projection_stager)
    register_workbench_projection(broker.projection_stager)
    # Compose the routed controller before candidate recovery so every staged
    # inference result is interpreted against its logical route winner.
    from ..services.inference_adoption_service import RoutedInferenceCoordinator

    broker.inference_adoption_service = RoutedInferenceCoordinator(
        database, broker=broker, registry=broker.inference_capability_registry
    )
    # The one-way adapter is startup-owned.  It either installs the exact
    # family marker or records no authority change and returns a deterministic
    # repair issue; request paths never invoke it opportunistically.
    from ..config import Config
    broker.inference_adoption_migration = (
        broker.inference_adoption_service.migrate_startup_legacy_assignments(
            Principal(PrincipalKind.OWNER, "inference-adoption-startup"), Config.load
        )
    )
    broker.parent_run_controller.reconcile_abandoned()
    broker.inference_adoption_recovery = broker.inference_adoption_service.recover_route_executions()
    broker.projection_stager.recover()
    # One inference runner per configured broker: the runner's in-process
    # invocation registry is what makes cancellation reachable, so every
    # service (and every per-request route construction) must share it. The
    # acting principal rides the existing `_principal` context (services wrap
    # calls in `_as_principal`).
    from .inference_runner import InferenceRunner
    broker.inference_runner = InferenceRunner(
        broker, database, principal_provider=_principal.get,
        **({"clock": clock} if clock else {}),
    )
    # HS-143-07: the first production adopters are process composition, not a
    # request-supplied controller.  One evidence owner, route planner, fallback
    # controller, and routed runtime are installed beside the singleton Runner.
    from ..services.inference_fallback_controller import RoutedAttemptRuntime

    broker.inference_runner._routed_attempt_runtime = RoutedAttemptRuntime(
        broker.inference_adoption_service.controller
    )
    launch_service.bind_kernel(broker)
    return broker


def _service() -> Broker:
    global _broker, _database_id
    from ..db import get_database

    database = get_database()
    if _broker is None or _database_id != id(database):
        _dispose(_broker)
        _broker = _build(database)
        _database_id = id(database)
    return _broker


def _configure(database: Any, *, clock: Any = None) -> Broker:
    """Test/startup seam; deliberately private, never an operation registration API.

    Idempotent for the same database: rebuilding on every call would dispose the
    parent-run controller (clearing issued contexts and lease refreshers) under
    every in-flight run, so per-request callers must reuse the live broker. A
    custom clock always rebuilds — it is a test seam that must take effect.
    """
    global _broker, _database_id
    if _broker is not None and _database_id == id(database) and clock is None:
        return _broker
    _dispose(_broker)
    _broker = _build(database, clock=clock)
    _database_id = id(database)
    return _broker


def _shutdown() -> None:
    _dispose(_broker)


atexit.register(_shutdown)


@contextmanager
def _as_principal(principal: Any):
    token = _principal.set(principal)
    try:
        yield
    finally:
        _principal.reset(token)


def read(refs: Sequence[str], view: str = "state", consistency: str = "committed") -> dict[str, Any]:
    return _service().read(refs, view, consistency, _principal.get())


def submit(request: Mapping[str, Any]) -> dict[str, Any]:
    return _service().submit(request, _principal.get())


def decide(operation_id: str, decision: str, expected_revision: int) -> dict[str, Any]:
    return _service().decide(operation_id, decision, expected_revision, _principal.get())


def events(after_cursor: int = 0, filter: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _service().events(after_cursor, filter or {}, _principal.get())


def claim() -> dict[str, Any]:
    """Claim work as an out-of-process executor would.

    HS-131-10: the in-memory claim witness never leaves the process. It is proof
    that THIS runtime claimed the child (an object identity, not a token), so it
    is meaningless — and unserializable — on the wire. In-process callers that
    need it (the inference runner) claim through the broker directly.
    """
    result = _service().claim(_principal.get())
    operations = [
        {key: value for key, value in operation.items() if key != "claim_witness"}
        for operation in result.get("operations", [])
    ]
    return {**result, "operations": operations}


def receipt(operation_id: str, outcome: str, result_ref: str = "") -> dict[str, Any]:
    return _service().receipt(operation_id, outcome, result_ref, _principal.get())


def reconcile(operation_id: str) -> dict[str, Any]:
    return _service().reconcile(operation_id, _principal.get())
