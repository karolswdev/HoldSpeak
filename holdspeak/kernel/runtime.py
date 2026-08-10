"""Trusted startup wiring and request-principal context for the broker."""
from __future__ import annotations

import atexit
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Mapping, Sequence

from ..privileged_effects.desktop_executor import DesktopEffectExecutor
from ..principals import UNAUTHENTICATED
from .actuator import ActuatorCodec
from .broker import Broker
from .desktop_type_text import DesktopTypeTextCodec
from .external_egress import ExternalEgressCodec
from .inference import InferenceInvokeCodec, InferenceRunCodec
from .inference_cancel import InferenceCancelCodec
from .journal import JournalStore
from .model import OperationSpec
from .process_input import ProcessInputCodec
from .process_spawn import ProcessSpawnCodec
from .subprocess_exec import SubprocessExecCodec
from .tool_call import ToolCallCodec
from .voice_resolve import VoiceResolveCodec
from .workbench_mint import WorkbenchMintCodec
from .workbench_triage import WorkbenchTriageCodec

_principal = ContextVar("kernel_principal", default=UNAUTHENTICATED)
_broker: Broker | None = None
_database_id: int | None = None


def _dispose(broker: Broker | None) -> None:
    """Close typed-codec resources without adding type dispatch to the broker."""
    if broker is None:
        return
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
    actuator = ActuatorCodec(database.actuators, _mode)
    inference = InferenceRunCodec(database, **({"clock": clock} if clock else {}))
    invocation = InferenceInvokeCodec(database, store, **({"clock": clock} if clock else {}))
    cancellation = InferenceCancelCodec(database, store)
    voice_resolve = VoiceResolveCodec()
    workbench_mint = WorkbenchMintCodec()
    workbench_triage = WorkbenchTriageCodec()
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
        OperationSpec(actuator.name, actuator.version, actuator, "agent.submit", "propose"),
        OperationSpec(inference.name, inference.version, inference, "agent.submit", "propose"),
        OperationSpec(invocation.name, invocation.version, invocation, "agent.submit", "propose"),
        OperationSpec(cancellation.name, cancellation.version, cancellation, "agent.submit", "propose"),
        OperationSpec(voice_resolve.name, voice_resolve.version, voice_resolve, "agent.submit", "propose"),
        OperationSpec(workbench_mint.name, workbench_mint.version, workbench_mint, "agent.submit", "propose"),
        OperationSpec(workbench_triage.name, workbench_triage.version, workbench_triage, "agent.submit", "propose"),
    )
    broker = Broker(store, specs, **({"clock": clock} if clock else {}))
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
    """Test/startup seam; deliberately private, never an operation registration API."""
    global _broker, _database_id
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
    return _service().claim(_principal.get())


def receipt(operation_id: str, outcome: str, result_ref: str = "") -> dict[str, Any]:
    return _service().receipt(operation_id, outcome, result_ref, _principal.get())


def reconcile(operation_id: str) -> dict[str, Any]:
    return _service().reconcile(operation_id, _principal.get())
