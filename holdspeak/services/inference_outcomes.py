"""One typed service boundary for admitted inference terminal outcomes."""
from __future__ import annotations
from typing import Any
from ..kernel.inference_runner import InvocationOutcome
from ..kernel.model import KernelRefused
from .errors import ServiceError

def map_inference_outcome(outcome: InvocationOutcome | None, refused: KernelRefused | None, *, target: Any = None) -> ServiceError:
    if refused is not None:
        return ServiceError(refused.reason, str(refused), context={"machine_code": refused.reason, "operation_id": refused.operation_id, "status": 409})
    assert outcome is not None
    code = outcome.outcome
    detail = outcome.error or code
    context = {"machine_code": code, "invocation_id": outcome.invocation_id, "operation_id": outcome.operation_id, "receipt": dict(outcome.receipt), "result_ref": outcome.result_ref, "status": 502 if code == "failed" else 409}
    if code == "failed" and target is not None and outcome.error:
        from ..inference_targets import target_runtime_error
        detail = target_runtime_error(target, outcome.error)
        context["alternate_target_id"] = "this_machine"
    return ServiceError(code, detail, context=context)
