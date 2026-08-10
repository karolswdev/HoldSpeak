"""Typed admission codec for one actual inference provider dispatch."""
from __future__ import annotations

import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ..deployment_revisions import resolve_deployment_revision
from .inference_shared import _REVISION, digest, executor_identity
from .model import Admission, KernelRefused, OperationRequest, forbidden_content, valid_ref

_INVOKE_FIELDS = frozenset(
    {
        "invocation_id", "deployment_revision", "definition_origin",
        "deadline_at", "attempt_ordinal",
    }
)


@dataclass(frozen=True)
class InferenceInvocationAdmission(Admission):
    deployment_revision: str
    definition_origin: Mapping[str, str]
    deadline_at: float
    attempt_ordinal: int


class InferenceInvokeCodec:
    """Admission for one actual provider dispatch, never an outer domain run."""

    name = "inference.invoke"
    version = 1

    def __init__(self, database: Any, store: Any, *, clock: Any = time.time) -> None:
        self._database = database
        self._store = store
        self._clock = clock

    @staticmethod
    def _origin(value: Any) -> dict[str, str]:
        if not isinstance(value, Mapping):
            raise KernelRefused("inference_definition_origin_invalid")
        kind = str(value.get("kind") or "")
        if kind == "saved":
            if set(value) != {"kind", "ref", "revision"}:
                raise KernelRefused("inference_saved_definition_invalid")
            ref, revision = str(value["ref"]).strip(), str(value["revision"]).strip()
            if not valid_ref(ref) or not _REVISION.fullmatch(revision):
                raise KernelRefused("inference_saved_definition_invalid")
            return {"kind": kind, "ref": ref, "revision": revision}
        if kind == "service":
            if set(value) != {"kind", "contract", "revision", "payload_hash"}:
                raise KernelRefused("inference_service_contract_invalid")
            contract = str(value["contract"]).strip()
            revision = str(value["revision"]).strip()
            payload_hash = str(value["payload_hash"]).strip()
            if not contract or not _REVISION.fullmatch(revision) or not re.fullmatch(r"sha256:[0-9a-f]{64}", payload_hash):
                raise KernelRefused("inference_service_contract_invalid")
            return {"kind": kind, "contract": contract, "revision": revision, "payload_hash": payload_hash}
        raise KernelRefused("inference_definition_origin_invalid")

    def validate(self, request: OperationRequest) -> Admission:
        args = request.arguments
        if forbidden_content(args):
            raise KernelRefused("journal_content_forbidden")
        if set(args) != _INVOKE_FIELDS or request.target_ref or request.placement:
            raise KernelRefused("inference_invoke_prerequisite_failed")
        invocation_id = str(args.get("invocation_id") or "").strip()
        revision = str(args.get("deployment_revision") or "").strip()
        try:
            deadline = float(args.get("deadline_at"))
            ordinal = int(args.get("attempt_ordinal"))
        except (TypeError, ValueError) as exc:
            raise KernelRefused("inference_invoke_prerequisite_failed") from exc
        if not invocation_id or not revision or deadline <= self._clock() or ordinal < 1:
            raise KernelRefused("inference_invoke_prerequisite_failed")
        origin = self._origin(args.get("definition_origin"))
        return InferenceInvocationAdmission(
            target_ref=f"invocation:{invocation_id}", placement="", payload_hash="", refs=(),
            head="", ttl_seconds=max(0.1, deadline - self._clock()), native_id=invocation_id,
            deployment_revision=revision, definition_origin=origin, deadline_at=deadline,
            attempt_ordinal=ordinal,
        )

    def authorize(
        self, request: OperationRequest, admission: InferenceInvocationAdmission,
        principal: Any, operation_id: str,
    ) -> InferenceInvocationAdmission:
        revision = resolve_deployment_revision(self._database, admission.deployment_revision)
        if revision is None:
            raise KernelRefused("inference_deployment_revision_unknown")
        placement = f"node:{executor_identity(revision.destination_id)}"
        material = {
            "name": self.name, "version": self.version,
            "deployment_revision": revision.id, "definition_origin": admission.definition_origin,
            "deadline_at": admission.deadline_at, "attempt_ordinal": admission.attempt_ordinal,
            "placement": placement,
        }
        return InferenceInvocationAdmission(
            **{
                **admission.__dict__, "placement": placement,
                "payload_hash": digest(material),
                "refs": (
                    f"deployment-revision:{revision.id}",
                    f"egress:{revision.boundary}",
                    *(() if admission.definition_origin["kind"] == "service" else (admission.definition_origin["ref"],)),
                ),
                "head": f"invoke {revision.engine} egress:{revision.boundary}",
            }
        )

    def admit(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> None:
        return None

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> None:
        return None

    def validate_claim(self, operation: Mapping[str, Any]) -> None:
        if float(operation["warrant"].get("execution_expires_at") or 0) <= self._clock():
            raise KernelRefused("inference_execution_expired")
        parent_id = str(operation.get("parent_operation_id") or "")
        while parent_id:
            parent = self._store.operation(parent_id)
            if (
                parent is None or parent["state"] != "claimed"
                or bool(parent["warrant_revoked"])
                or not self._store.valid_warrant(parent["warrant"])
                or float(parent["warrant"].get("execution_expires_at") or 0) <= self._clock()
            ):
                raise KernelRefused("inference_parent_not_live")
            parent_id = str(parent.get("parent_operation_id") or "")

    def read_native(self, native_id: str) -> dict[str, Any]:
        return {"invocation_id": native_id}

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "process_id": f"process:{operation['operation_id']}", "kind": self.name,
            "principal": operation["principal_identity"], "generic_state": operation["state"],
            "domain_state": operation["state"], "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
        }

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        return []
