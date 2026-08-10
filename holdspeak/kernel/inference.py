"""Typed inference-run and cancellation codecs over durable invocations."""
from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ..inference_targets import resolve_inference_target
from ..principals import PrincipalKind
from .inference_shared import _REVISION, digest as _digest, executor_identity
from .model import (
    Admission,
    KernelRefused,
    OperationRequest,
    forbidden_content,
    valid_ref,
)

_RUN_FIELDS = frozenset(
    {
        "invocation_id", "definition_ref", "definition_revision", "grounding_refs",
        "requested_target_id", "deadline_at", "input_snapshot", "continuation_identities",
    }
)

@dataclass(frozen=True)
class InferenceAdmission(Admission):
    definition_ref: str
    definition_revision: str
    grounding: tuple[tuple[str, str], ...]
    requested_target_id: str
    deadline_at: float
    input_snapshot: Mapping[str, Any]
    continuation_identities: tuple[str, ...] = ()
    target: Any = None
    egress: str = ""


class InferenceRunCodec:
    """Derive an inference attempt's machine, model, and egress at admission."""

    name = "inference.run"
    version = 1

    def __init__(self, database: Any, *, clock: Any = time.time) -> None:
        self._database = database
        self._clock = clock
        self._continuations: dict[str, tuple[str, ...]] = {}

    def validate(self, request: OperationRequest) -> Admission:
        args = request.arguments
        if forbidden_content(args):
            raise KernelRefused("journal_content_forbidden")
        unknown = set(args) - _RUN_FIELDS
        if unknown:
            raise KernelRefused("operation_field_not_allowed", min(unknown))
        if request.target_ref or request.placement:
            raise KernelRefused("inference_placement_not_client_settable")
        invocation_id = str(args.get("invocation_id") or "").strip()
        definition_ref = str(args.get("definition_ref") or "").strip()
        revision = str(args.get("definition_revision") or "").strip()
        grounding_raw = args.get("grounding_refs") or []
        snapshot = args.get("input_snapshot") or {}
        continuations_raw = args.get("continuation_identities") or []
        try:
            deadline = float(args.get("deadline_at"))
        except (TypeError, ValueError) as exc:
            raise KernelRefused("inference_deadline_invalid") from exc
        if (
            not invocation_id or not valid_ref(definition_ref) or not definition_ref
            or not _REVISION.fullmatch(revision) or deadline <= self._clock()
            or not isinstance(snapshot, Mapping) or not isinstance(grounding_raw, list)
            or not isinstance(continuations_raw, list)
            or not all(isinstance(item, str) and item.strip() for item in continuations_raw)
        ):
            raise KernelRefused("inference_run_prerequisite_failed")
        grounding: list[tuple[str, str]] = []
        for item in grounding_raw:
            if not isinstance(item, Mapping) or set(item) != {"ref", "revision"}:
                raise KernelRefused("inference_grounding_revision_required")
            ref, ref_revision = str(item["ref"]).strip(), str(item["revision"]).strip()
            if not valid_ref(ref) or not ref or not _REVISION.fullmatch(ref_revision):
                raise KernelRefused("inference_grounding_revision_required")
            grounding.append((ref, ref_revision))
        requested = str(args.get("requested_target_id") or "this_machine").strip()
        return InferenceAdmission(
            target_ref=f"invocation:{invocation_id}", placement="", payload_hash="",
            refs=(), head="", ttl_seconds=max(1.0, deadline - self._clock()),
            native_id=invocation_id, definition_ref=definition_ref,
            definition_revision=revision, grounding=tuple(grounding),
            requested_target_id=requested, deadline_at=deadline,
            input_snapshot=dict(snapshot),
            continuation_identities=tuple(sorted({item.strip() for item in continuations_raw})),
        )

    def authorize(
        self, request: OperationRequest, admission: InferenceAdmission,
        principal: Any, operation_id: str,
    ) -> InferenceAdmission:
        if admission.continuation_identities and principal.kind is not PrincipalKind.OWNER:
            raise KernelRefused("continuation_identities_owner_required")
        target = resolve_inference_target(self._database, admission.requested_target_id)
        placement = f"node:{executor_identity(target.id)}"
        egress = "none" if target.boundary == "same_device" else target.boundary
        material = {
            "name": self.name, "version": self.version,
            "definition_ref": admission.definition_ref,
            "definition_revision": admission.definition_revision,
            "grounding": admission.grounding, "deadline_at": admission.deadline_at,
            "input_snapshot": admission.input_snapshot,
            "continuation_identities": admission.continuation_identities,
            "placement": placement, "target_id": target.id,
            "model": target.model, "engine": target.engine, "egress": egress,
        }
        refs = tuple(
            dict.fromkeys(
                (
                    admission.definition_ref,
                    f"revision:{admission.definition_revision}",
                    *(ref for ref, _ in admission.grounding),
                    *(f"revision:{revision}" for _, revision in admission.grounding),
                    f"inference-target:{target.id}", f"egress:{egress}",
                )
            )
        )
        return InferenceAdmission(
            **{
                **admission.__dict__, "placement": placement,
                "payload_hash": _digest(material), "refs": refs,
                "head": f"run {target.id} {target.model or target.engine} egress:{egress}",
                "target": target, "egress": egress,
            }
        )

    def admit(
        self, request: OperationRequest, admission: InferenceAdmission,
        principal: Any, operation_id: str,
    ) -> Any:
        self._continuations[admission.native_id] = admission.continuation_identities
        grounding = [ref for ref, _ in admission.grounding]
        return self._database.capability_invocations.begin(
            invocation_id=admission.native_id,
            definition_ref=admission.definition_ref,
            initiator=principal.name,
            grounding_refs=grounding,
            requested_placement=admission.requested_target_id,
            input_snapshot=dict(admission.input_snapshot),
        )

    def continuation_identities(self, native_id: str) -> tuple[str, ...]:
        return self._continuations.get(native_id, ())

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
            "process_id": f"process:{operation['operation_id']}", "kind": self.name,
            "principal": operation["principal_identity"], "generic_state": generic,
            "domain_state": state, "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
        }

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        return []


from .inference_cancel import InferenceCancelCodec
from .inference_invoke import InferenceInvocationAdmission, InferenceInvokeCodec
