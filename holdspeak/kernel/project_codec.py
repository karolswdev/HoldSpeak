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
import time
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

    def __init__(self, name: str, database: Any, *, clock: Any = time.time) -> None:
        if name not in rooms.PROJECT_KERNEL_OPERATIONS:
            raise ValueError(f"not a Room kernel operation: {name}")
        self.name = name
        self._database = database
        self._clock = clock

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
        # An AGENT.
        if self.name in rooms.PROJECT_DELEGATION_OPERATIONS:
            # XI.4: only the owner delegates; an agent can never grant itself.
            raise KernelRefused(rooms.OWNER_REQUIRED, provenance=target)
        if rooms.agent_steward_child(self.name, principal, request.parent_operation_id):
            # PHILO-9-07 (R4-1): a child of the agent's own run acts under the
            # run's FROZEN grant (G1, never a newer G2) and the owner's policy.
            # Admitted as the run's child; its approval and its claim re-check
            # the frozen grant, so a refused child keeps its parent and receipt.
            return _steward_basis(admission, context or {})
        # R4-1: the project is resolved from the stored run or update, never
        # from the request; stop is bound to the stored run's requester.
        project_id = self._project_of(payload)
        if self.name == "project.stop_steward":
            run = self._database.steward_runs.get_run(str(payload.get("run_id") or ""))
            if run is None:
                raise KernelRefused("not_found", provenance=target)
            if not self._agent_started(run, principal):
                raise KernelRefused(rooms.RUN_OWNER_REQUIRED, provenance=target)
        with self._database._connection() as conn:
            code, basis = rooms.grant_code(conn, principal, self.name, project_id, self._clock())
        if code:
            raise KernelRefused(code, provenance={**target, **{k: v for k, v in dict(basis).items() if k != "target_ref"}})
        # Frozen at admission: the grant id and its terms hash.
        return replace(admission, **dict(basis))

    def _agent_started(self, run: Mapping[str, Any], principal: Any) -> bool:
        """The run is THIS agent's: its stored run operation's authenticated actor KIND and identity.

        ``requested_by`` alone is a string (``principal:<identity>``): an agent
        named ``owner-session`` would match the owner's run (Codex Astra r1
        finding 1). The run operation records who was authenticated.
        """
        if str(run.get("requested_by") or "") != f"principal:{principal.identity}":
            return False
        with self._database._connection() as conn:
            actor = conn.execute(
                "SELECT principal_kind, principal_identity FROM kernel_operations WHERE operation_id=?",
                (str(run.get("operation_id") or ""),)).fetchone()
        return actor is not None and (str(actor["principal_kind"]), str(actor["principal_identity"])) == (
            "agent", str(principal.identity))

    def _project_of(self, payload: Mapping[str, Any]) -> str:
        """The operation's project, from the STORED object it acts on (a spoofed project_id is ignored)."""
        with self._database._connection() as conn:
            if self.name == "project.stop_steward":
                row = conn.execute("SELECT project_id FROM steward_runs WHERE id=?",
                                   (str(payload.get("run_id") or ""),)).fetchone()
                return str(row["project_id"]) if row is not None else ""
            if payload.get("update_id"):
                row = conn.execute("SELECT project_id FROM project_updates WHERE id=?",
                                   (str(payload.get("update_id") or ""),)).fetchone()
                return str(row["project_id"]) if row is not None else ""
        return str(payload.get("project_id") or "")

    def admit(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> None:
        return None

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> None:
        return None

    # -- the execution cutoff (the beat, section 3) -----------------------

    def validate_claim(self, operation: Mapping[str, Any]) -> None:
        """The execution cutoff, AT THE CLAIM (the beat, section 3; Phase 7's invariant 3).

        A steward child: a durable stop, a changed policy or a lost frozen
        grant refuses it. An agent's own granted operation: the grant its
        frozen basis names must still be LIVE and unexpired.
        """
        context = rooms.current_steward_context()
        if context and str(operation.get("parent_operation_id") or "") == str(context.get("operation_id") or ""):
            cutoff = context.get("cutoff")
            code = cutoff() if callable(cutoff) else ""
            if code:
                raise KernelRefused(code)
            return
        if self.name not in rooms.PROJECT_GRANT_OPERATIONS or str(operation.get("principal_kind")) != "agent":
            return
        # The project was bound to the stored object at admission and a run's
        # or an update's project never changes: the frozen row's own project.
        with self._database._connection() as conn:
            code = rooms.by_basis(conn, operation, None, self._clock(), authoritative=True)
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


def specs(database: Any, *, clock: Any = None) -> tuple[Any, ...]:
    """One ``OperationSpec`` per Room kernel operation (``kernel/runtime.py`` composes them)."""
    from .model import OperationSpec

    kwargs = {"clock": clock} if clock else {}
    return tuple(
        OperationSpec(name, 1, ProjectCodec(name, database, **kwargs), "agent.submit", "propose")
        for name in sorted(rooms.PROJECT_KERNEL_OPERATIONS)
    )
