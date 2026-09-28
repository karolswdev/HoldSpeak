"""The Room's operations' kernel codec (PHILO-9-02).

One ``OperationSpec`` per Room kernel operation name, carved beside the desk
codec (the kernel density guard). Admission is the owner's gesture for an
OWNER; an AGENT is refused at admission with a receipt unless story 07's grant
names the operation (:func:`holdspeak.kernel.project.grant_code`); a SCHEDULER
only inside the hub's steward service, under the owner's recorded policy.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import replace
from typing import Any, Mapping

from ..principals import PrincipalKind
from . import project as rooms
from .model import Admission, KernelRefused, OperationRequest, valid_ref


class ProjectCodec:
    """One kernel operation spec per Room operation name.

    The payload is fixed at admission (XI.3): the request's ``arguments`` are
    ``{native_id, payload}``; only its hash reaches the journal.
    """

    version = 1

    def __init__(self, name: str, database: Any) -> None:
        if name not in rooms.PROJECT_KERNEL_OPERATIONS:
            raise ValueError(f"not a Room kernel operation: {name}")
        self.name = name
        self._database = database

    # -- admission -------------------------------------------------------

    def validate(self, request: OperationRequest) -> Admission:
        args = request.arguments
        native_id = str(args.get("native_id") or "")
        try:
            uuid.UUID(native_id)
        except (TypeError, ValueError) as exc:
            raise KernelRefused("project_native_id_invalid") from exc
        payload = args.get("payload")
        if not isinstance(payload, Mapping) or set(args) - {"native_id", "payload"}:
            raise KernelRefused("invalid_arguments")
        if not request.target_ref or not valid_ref(request.target_ref):
            raise KernelRefused("project_target_invalid")
        material = {"name": request.name, "version": request.version, "target_ref": request.target_ref,
                    "placement": request.placement, "arguments": {"native_id": native_id, "payload": dict(payload)}}
        canonical = json.dumps(material, separators=(",", ":"), sort_keys=True, default=str)
        return Admission(
            target_ref=request.target_ref, placement=request.placement,
            payload_hash="sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            refs=(request.target_ref,), head=self.name, ttl_seconds=30.0, native_id=native_id,
        )

    def authorize(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> Admission:
        target = {"target_ref": admission.target_ref}
        if not rooms.in_project_path():
            raise KernelRefused("project_operation_service_required", provenance=target)
        payload = request.arguments.get("payload") or {}
        context = rooms.current_steward_context()
        if principal.kind is PrincipalKind.OWNER:
            if context and request.parent_operation_id == str(context.get("operation_id") or ""):
                return _steward_basis(admission, context)
            return admission  # the owner's own gesture
        if principal.kind is PrincipalKind.SCHEDULER:
            root = rooms._SCHEDULER_ROOT.get()
            if self.name == "project.run_steward" and root is not None:
                return replace(admission, authority_basis=str(root.get("authority_basis") or ""),
                               delegator_kind=str(root.get("delegator_kind") or ""),
                               delegator_identity=str(root.get("delegator_identity") or ""))
            if context and request.parent_operation_id == str(context.get("operation_id") or ""):
                return _steward_basis(admission, context)
            raise KernelRefused("declared_capability_required", provenance=target)
        if principal.kind is not PrincipalKind.AGENT:
            raise KernelRefused("declared_capability_required", provenance=target)
        # An AGENT. R4-1: stop is bound to the stored run's requester, the
        # project resolved from the stored run (never from the request).
        project_id = str(payload.get("project_id") or "")
        if self.name == "project.stop_steward":
            run = self._database.steward_runs.get_run(str(payload.get("run_id") or ""))
            if run is None:
                raise KernelRefused("not_found", provenance=target)
            if str(run.get("requested_by") or "") != f"principal:{principal.identity}":
                raise KernelRefused(rooms.RUN_OWNER_REQUIRED, provenance=target)
            project_id = str(run.get("project_id") or "")
        with self._database._connection() as conn:
            code, basis = rooms.grant_code(conn, principal, self.name, project_id)
        if code:
            raise KernelRefused(code, provenance={**target, **dict(basis)})
        return replace(admission, **dict(basis))  # pragma: no cover - story 07

    def admit(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> None:
        return None

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> None:
        return None

    # -- the execution cutoff (the beat, section 3) -----------------------

    def validate_claim(self, operation: Mapping[str, Any]) -> None:
        """A steward child is re-checked AT THE CLAIM: a durable stop or a changed policy refuses it."""
        context = rooms.current_steward_context()
        if not context or str(operation.get("parent_operation_id") or "") != str(context.get("operation_id") or ""):
            return
        cutoff = context.get("cutoff")
        code = cutoff() if callable(cutoff) else ""
        if code:
            raise KernelRefused(code)

    # -- reads -------------------------------------------------------------

    def read_native(self, native_id: str) -> None:
        return None

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        """The steward's ``authority_details`` beside the receipt (the beat, section 4).

        For a steward run and each of its children: the run, the project, the
        grant (null until story 07), the policy id and hash, the owner
        operation that recorded the policy, and the delegator -- resolved from
        the run's FROZEN snapshot, never the current policy, so one
        ``kernel.receipt`` answer names both authorities.
        """
        with self._database._connection() as conn:
            operation = conn.execute(
                "SELECT operation_id, authority_basis FROM kernel_operations WHERE native_id=? ORDER BY created_at LIMIT 1",
                (native_id,),
            ).fetchone()
            if operation is None:
                return []
            basis = str(operation["authority_basis"] or "")
            run_id = basis.split(":", 2)[1] if basis.startswith("project-steward:") else ""
            run = (conn.execute("SELECT id, project_id, authority_json FROM steward_runs WHERE id=?", (run_id,)).fetchone()
                   if run_id else
                   conn.execute("SELECT id, project_id, authority_json FROM steward_runs WHERE operation_id=?",
                                (operation["operation_id"],)).fetchone())
        if run is None:
            return []
        try:
            frozen = json.loads(run["authority_json"] or "{}")
        except (TypeError, ValueError):
            frozen = {}
        return [{
            "kind": "authority_details",
            "run_id": run["id"],
            "project_id": run["project_id"],
            "grant_id": (frozen.get("grant") or {}).get("id") if frozen.get("grant") else None,
            "grant_sha256": (frozen.get("grant") or {}).get("terms_sha256") if frozen.get("grant") else None,
            "policy_id": frozen.get("policy_id"),
            "policy_sha256": frozen.get("policy_sha256"),
            "configure_operation_id": frozen.get("configure_operation_id"),
            "delegator_kind": frozen.get("delegator_kind"),
            "delegator_identity": frozen.get("delegator_identity"),
            "authority_sha256": frozen.get("authority_sha256"),
            "actor_kind": (frozen.get("authority_terms") or {}).get("actor_kind"),
        }]

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "process_id": f"process:{operation['operation_id']}", "kind": self.name,
            "principal": operation["principal_identity"], "generic_state": str(operation["state"]),
            "domain_state": str(operation["state"]), "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
        }


def _steward_basis(admission: Admission, context: Mapping[str, Any]) -> Admission:
    """A steward child names its run and the frozen authority (the beat, section 4)."""
    return replace(
        admission,
        authority_basis=f"project-steward:{context.get('run_id')}:{context.get('authority_sha256')}",
        delegator_kind=str(context.get("delegator_kind") or ""),
        delegator_identity=str(context.get("delegator_identity") or ""),
    )


def specs(database: Any) -> tuple[Any, ...]:
    """One ``OperationSpec`` per Room kernel operation (``kernel/runtime.py`` composes them)."""
    from .model import OperationSpec

    return tuple(
        OperationSpec(name, 1, ProjectCodec(name, database), "agent.submit", "propose")
        for name in sorted(rooms.PROJECT_KERNEL_OPERATIONS)
    )
