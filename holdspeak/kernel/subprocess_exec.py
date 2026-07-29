"""Typed ``subprocess.exec`` operation and subprocess-family triage.

C01/C04 execute connector commands: consequential process control, migrated
here. C02/C03 obtain GitHub/Jira metadata; C05 obtains Delivery Workbench and
GitHub receipt views: cheap reads guarded by principal plus named read authority.

Admission copies binary, argv, and cwd into a frozen native plan and hashes that
binding, so a decision cannot swap payload. A completed child means the operation
ran even at non-zero exit; an uncertain dispatch is receipted indeterminate and
never retried here.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

from ..principals import Principal, PrincipalKind
from .model import Admission, KernelRefused, OperationRequest, valid_ref

SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]
LOCAL_OWNER = Principal(PrincipalKind.OWNER, "local-owner")
LOCAL_NODE = Principal(PrincipalKind.NODE, "local")

class SubprocessOperationRefused(PermissionError):
    def __init__(self, binary: str, reason: str) -> None:
        self.binary = binary
        self.reason = reason
        super().__init__(f"subprocess {binary!r} refused: {reason}")

class SubprocessOutcomeIndeterminate(RuntimeError):
    def __init__(self, binary: str, operation_id: str, cause: BaseException) -> None:
        self.binary = binary
        self.operation_id = operation_id
        self.cause = cause
        super().__init__(
            f"subprocess {binary!r} outcome indeterminate in {operation_id}: {cause}"
        )

@dataclass(frozen=True)
class SubprocessPlan:
    native_id: str
    connector_id: str
    binary: str
    argv: tuple[str, ...]
    cwd: str
    kwargs: Mapping[str, Any]
    declared_permissions: tuple[str, ...]
    allowed_argv_prefixes: tuple[tuple[str, ...], ...]
    runner: SubprocessRunner = field(compare=False, repr=False)

class SubprocessExecutionStore:
    def __init__(self) -> None:
        self._plans: dict[str, SubprocessPlan] = {}
        self._operation_ids: dict[str, str] = {}
        self._results: dict[str, dict[str, Any]] = {}

    def bind(
        self,
        command: Sequence[str],
        *,
        connector_id: str,
        declared_permissions: Sequence[str],
        allowed_argv_prefixes: Sequence[Sequence[str]],
        runner: SubprocessRunner,
        kwargs: Mapping[str, Any],
    ) -> SubprocessPlan:
        argv = tuple(str(part) for part in command)
        cwd_value = kwargs.get("cwd")
        cwd = os.path.abspath(os.fspath(cwd_value)) if cwd_value is not None else os.getcwd()
        run_kwargs = dict(kwargs)
        run_kwargs["cwd"] = cwd
        native_id = "exec_" + uuid.uuid4().hex
        plan = SubprocessPlan(
            native_id=native_id,
            connector_id=str(connector_id or "connector"),
            binary=argv[0] if argv else "<empty>",
            argv=argv,
            cwd=cwd,
            kwargs=MappingProxyType(run_kwargs),
            declared_permissions=tuple(str(item) for item in declared_permissions),
            allowed_argv_prefixes=tuple(
                tuple(str(part) for part in prefix) for prefix in allowed_argv_prefixes
            ),
            runner=runner,
        )
        self._plans[native_id] = plan
        return plan

    def plan(self, native_id: str) -> SubprocessPlan | None:
        return self._plans.get(native_id)

    def admit(self, native_id: str, operation_id: str) -> None:
        self._operation_ids[native_id] = operation_id

    def record(self, native_id: str, **result: Any) -> None:
        plan = self._plans[native_id]
        self._results[native_id] = {
            "native_id": native_id,
            "operation_id": self._operation_ids.get(native_id, ""),
            "connector_id": plan.connector_id,
            "binary": plan.binary,
            "argv": list(plan.argv),
            "cwd": plan.cwd,
            **result,
        }
    def read(self, native_id: str) -> dict[str, Any] | None:
        result = self._results.get(native_id)
        if result is not None:
            return dict(result)
        plan = self._plans.get(native_id)
        if plan is None:
            return None
        return {
            "native_id": native_id,
            "operation_id": self._operation_ids.get(native_id, ""),
            "connector_id": plan.connector_id,
            "binary": plan.binary,
            "argv": list(plan.argv),
            "cwd": plan.cwd,
            "process_outcome": "not_started",
        }

EXECUTIONS = SubprocessExecutionStore()

class SubprocessExecCodec:
    name = "subprocess.exec"
    version = 1

    def __init__(self, executions: SubprocessExecutionStore = EXECUTIONS) -> None:
        self._executions = executions

    def validate(self, request: OperationRequest) -> Admission:
        if set(request.arguments) != {"execution_id"}:
            raise KernelRefused("subprocess_exec_arguments_invalid")
        native_id = str(request.arguments.get("execution_id") or "")
        plan = self._executions.plan(native_id)
        target_ref = f"subprocess:{native_id}"
        if plan is None or request.target_ref != target_ref or not valid_ref(target_ref):
            raise KernelRefused("subprocess_exec_plan_unknown")
        if request.placement != "node:local" or not plan.argv:
            raise KernelRefused("subprocess_exec_prerequisite_failed")
        if "shell:exec" not in plan.declared_permissions:
            raise KernelRefused(f"subprocess_permission_required:{plan.binary}")
        if plan.allowed_argv_prefixes and not any(
            len(prefix) <= len(plan.argv) and plan.argv[: len(prefix)] == prefix
            for prefix in plan.allowed_argv_prefixes
        ):
            raise KernelRefused(f"subprocess_argv_not_allowed:{plan.binary}")
        material = {
            "name": self.name,
            "version": self.version,
            "target_ref": target_ref,
            "placement": request.placement,
            "connector_id": plan.connector_id,
            "binary": plan.binary,
            "argv": plan.argv,
            "cwd": plan.cwd,
        }
        canonical = json.dumps(material, separators=(",", ":"), sort_keys=True)
        payload_hash = "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
        return Admission(
            target_ref=target_ref,
            placement=request.placement,
            payload_hash=payload_hash,
            refs=tuple(dict.fromkeys((*request.subject_refs, target_ref))),
            head=f"execute {plan.binary} ({len(plan.argv)} argv)",
            ttl_seconds=30.0,
            native_id=native_id,
        )

    def authorize(
        self, request: OperationRequest, admission: Admission,
        principal: Any, operation_id: str,
    ) -> Admission:
        plan = self._executions.plan(admission.native_id)
        if principal.kind is PrincipalKind.AGENT:
            binary = plan.binary if plan is not None else "unknown"
            raise KernelRefused(f"subprocess_agent_authority_required:{binary}")
        return admission

    def admit(
        self, request: OperationRequest, admission: Admission,
        principal: Any, operation_id: str,
    ) -> None:
        self._executions.admit(admission.native_id, operation_id)

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> None:
        return None

    def read_native(self, native_id: str) -> dict[str, Any] | None:
        return self._executions.read(native_id)

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        result = self._executions.read(native_id)
        if result is None or result.get("process_outcome") == "not_started":
            return []
        return [{
            "receipt_ref": f"subprocess-result:{native_id}",
            "native_id": native_id,
            "binary": result["binary"],
            "argv": result["argv"],
            "cwd": result["cwd"],
            "operation_outcome": result["operation_outcome"],
            "process_outcome": result["process_outcome"],
            "returncode": result.get("returncode"),
        }]

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
        result = self._executions.read(native_id) or {}
        process_outcome = str(result.get("process_outcome") or "unknown")
        return {
            "process_id": f"process:{operation['operation_id']}",
            "kind": self.name,
            "principal": operation["principal_identity"],
            "generic_state": "unknown" if process_outcome == "indeterminate" else operation["state"],
            "domain_state": process_outcome,
            "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
        }

def run_subprocess_operation(
    command: Sequence[str], *, connector_id: str,
    declared_permissions: Sequence[str],
    allowed_argv_prefixes: Sequence[Sequence[str]] = (),
    principal: Principal = LOCAL_OWNER,
    runner: SubprocessRunner = subprocess.run,
    broker: Any = None,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    if broker is None:
        from .runtime import _service

        broker = _service()
    plan = EXECUTIONS.bind(
        command,
        connector_id=connector_id,
        declared_permissions=declared_permissions,
        allowed_argv_prefixes=allowed_argv_prefixes,
        runner=runner,
        kwargs=kwargs,
    )
    request_id = str(uuid.uuid4())
    handle = broker.submit(
        {
            "request_schema": 1,
            "request_id": request_id,
            "idempotency_key": f"subprocess:{plan.native_id}",
            "operation": {"name": "subprocess.exec", "version": 1},
            "subject_refs": [f"connector:{plan.connector_id}"],
            "target": {"ref": f"subprocess:{plan.native_id}"},
            "arguments": {"execution_id": plan.native_id},
            "placement": "node:local",
        },
        principal,
    )
    if handle["state"] == "refused":
        receipt = handle.get("receipt") or {}
        raise SubprocessOperationRefused(plan.binary, str(receipt.get("outcome") or "kernel_refused"))
    if principal.kind is not PrincipalKind.OWNER:
        raise SubprocessOperationRefused(plan.binary, f"subprocess_agent_authority_required:{plan.binary}")
    approved = broker.decide(handle["operation_id"], "approve", handle["revision"], principal)
    claimed = broker.claim(LOCAL_NODE, plan.native_id).get("operations") or []
    if not claimed:
        raise SubprocessOperationRefused(plan.binary, "subprocess_execution_warrant_refused")
    result_ref = f"subprocess-result:{plan.native_id}"
    try:
        completed = plan.runner(list(plan.argv), **dict(plan.kwargs))
    except OSError as exc:
        EXECUTIONS.record(
            plan.native_id, operation_outcome="failed", process_outcome="not_started",
            returncode=None, error=f"{type(exc).__name__}: {exc}",
        )
        broker.receipt(approved["operation_id"], "failed", result_ref, LOCAL_NODE)
        raise
    except BaseException as exc:
        EXECUTIONS.record(
            plan.native_id, operation_outcome="indeterminate", process_outcome="indeterminate",
            returncode=None, error=f"{type(exc).__name__}: {exc}",
        )
        broker.receipt(approved["operation_id"], "indeterminate", result_ref, LOCAL_NODE)
        raise SubprocessOutcomeIndeterminate(plan.binary, approved["operation_id"], exc) from exc
    returncode = (
        completed.get("returncode")
        if isinstance(completed, Mapping)
        else completed.returncode
    )
    process_outcome = "exited_zero" if returncode == 0 else "nonzero_exit"
    EXECUTIONS.record(
        plan.native_id, operation_outcome="succeeded", process_outcome=process_outcome,
        returncode=int(returncode),
    )
    broker.receipt(approved["operation_id"], "succeeded", result_ref, LOCAL_NODE)
    return completed
