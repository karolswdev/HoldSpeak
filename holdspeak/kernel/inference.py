"""Historical inference-run reader and cancellation codec exports.

``inference.run@1`` remains registered only so durable historical operations
can be decoded and projected. New executable admission is intentionally retired:
all new provider work enters through a frozen routed controller execution.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .inference_shared import executor_identity
from .model import Admission, KernelRefused, OperationRequest


class InferenceRunCodec:
    """Read historical ``inference.run`` records; refuse new mutable admission."""

    name = "inference.run"
    version = 1

    def __init__(self, database: Any, **_unused: Any) -> None:
        self._database = database

    def validate(self, request: OperationRequest) -> Admission:
        # Do not inspect, normalize, or resolve `requested_target_id`: doing so
        # would retain a mutable route selector on the executable path. The
        # broker terminalizes this before authorization, claim, or dispatch.
        raise KernelRefused("inference_run_retired")

    def authorize(
        self,
        request: OperationRequest,
        admission: Admission,
        principal: Any,
        operation_id: str,
    ) -> Admission:
        raise KernelRefused("inference_run_retired")

    def admit(
        self,
        request: OperationRequest,
        admission: Admission,
        principal: Any,
        operation_id: str,
    ) -> Any:
        raise KernelRefused("inference_run_retired")

    def continuation_identities(self, native_id: str) -> tuple[str, ...]:
        # Historical operations predate immutable continuation projection. They
        # remain inspectable but can never gain fresh execution authority.
        return ()

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> Any:
        value = self._database.capability_invocations.get(native_id)
        if value is None:
            raise KernelRefused("inference_invocation_missing")
        return value

    def read_native(self, native_id: str) -> dict[str, Any] | None:
        value = self._database.capability_invocations.get(native_id)
        return value.to_dict() if value is not None else None

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
        value = self._database.capability_invocations.get(native_id)
        state = value.state if value is not None else "unknown"
        generic = "running" if state == "running" else state
        return {
            "process_id": f"process:{operation['operation_id']}",
            "kind": self.name,
            "principal": operation["principal_identity"],
            "generic_state": generic,
            "domain_state": state,
            "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
        }

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        return []


from .inference_cancel import InferenceCancelCodec
from .inference_invoke import InferenceInvocationAdmission, InferenceInvokeCodec
