"""Typed ``process.spawn`` codec over the existing agent-launch records.

The codec admits one Story-bound launch.  ``LaunchService`` remains the driver:
it creates a worktree when requested, dispatches the existing ``factory.spawn``
command, and keeps both native command receipts.  The broker only stores the
immutable launch binding and projects the native launch/command records.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Mapping

from .model import Admission, KernelRefused, OperationRequest, forbidden_content, valid_ref

_ALLOWED = frozenset(
    {
        "launch_id",
        "agent_profile_id",
        "profile_id",
        "source_id",
        "worktree",
        "story_ref",
        "session_label",
        "options",
    }
)


class ProcessSpawnCodec:
    """Link one kernel operation to one durable ``LaunchService`` record."""

    name = "process.spawn"
    version = 1

    def __init__(self, service: Any, command_receipts: Any) -> None:
        self._service = service
        self._commands = command_receipts

    def validate(self, request: OperationRequest) -> Admission:
        args = request.arguments
        if forbidden_content(args):
            raise KernelRefused("journal_content_forbidden")
        unknown = set(args) - _ALLOWED
        if unknown:
            raise KernelRefused("operation_field_not_allowed", min(unknown))
        launch_id = str(args.get("launch_id") or "").strip()
        if not launch_id.startswith("launch_") or len(launch_id) > 80:
            raise KernelRefused("process_spawn_launch_id_invalid")
        target_ref = f"launch:{launch_id}"
        if request.target_ref != target_ref or not valid_ref(target_ref):
            raise KernelRefused("process_spawn_target_invalid")
        if request.placement != "node:local":
            raise KernelRefused("process_spawn_placement_invalid")
        launch_request = {key: value for key, value in args.items() if key != "launch_id"}
        try:
            validate = getattr(
                self._service, "validate_process_spawn", self._service.validate_request
            )
            validate(launch_request)
        except Exception as exc:
            raise KernelRefused(getattr(exc, "reason", "process_spawn_prerequisite_failed")) from exc
        material = {
            "name": self.name,
            "version": self.version,
            "target_ref": target_ref,
            "placement": request.placement,
            "arguments": dict(args),
        }
        canonical = json.dumps(material, separators=(",", ":"), sort_keys=True)
        digest = "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
        story = args.get("story_ref") if isinstance(args.get("story_ref"), Mapping) else {}
        source_id = str(args.get("source_id") or "")
        refs = tuple(
            dict.fromkeys(
                (
                    *request.subject_refs,
                    target_ref,
                    f"delivery-source:{source_id}",
                    f"story:{story.get('story_id')}",
                )
            )
        )
        return Admission(
            target_ref=target_ref,
            placement=request.placement,
            payload_hash=digest,
            refs=refs,
            head=f"spawn {args.get('agent_profile_id') or args.get('profile_id')} for {story.get('story_id')}",
            ttl_seconds=30.0,
            native_id=launch_id,
        )

    def authorize(
        self, request: OperationRequest, admission: Admission,
        principal: Any, operation_id: str,
    ) -> Admission:
        return admission

    def admit(
        self, request: OperationRequest, admission: Admission,
        principal: Any, operation_id: str,
    ) -> None:
        self._service.record_admitted(
            admission.native_id,
            {key: value for key, value in request.arguments.items() if key != "launch_id"},
            operation_id=operation_id,
        )

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> None:
        self._service.record_decision(native_id, decision, reason=reason)

    def read_native(self, native_id: str) -> dict[str, Any] | None:
        return self._service.launch_record(native_id)

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        launch = self._service.launch_record(native_id) or {}
        commands = launch.get("commands") or {}
        projected: list[dict[str, Any]] = []
        for kind in ("worktree_create", "spawn", "instruction"):
            command_id = str(commands.get(kind) or "")
            if not command_id:
                continue
            row = self._commands.get(command_id)
            projected.append(
                {
                    "receipt_ref": f"command:{command_id}",
                    "native_id": command_id,
                    "kind": kind,
                    "outcome": str(((row or {}).get("receipt") or {}).get("outcome") or (row or {}).get("hub_state") or "unknown"),
                }
            )
        return projected

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
        launch = self._service.launch_record(native_id) or {}
        domain_state = str(launch.get("state") or "unknown")
        generic = {
            "admitted": "waiting",
            "approved": "waiting",
            "starting": "starting",
            "launched": "running",
            "complete": "ended",
            "failed": "failed",
            "rejected": "ended",
        }.get(domain_state, "unknown")
        return {
            "process_id": f"process:{operation['operation_id']}",
            "kind": self.name,
            "principal": operation["principal_identity"],
            "generic_state": generic,
            "domain_state": domain_state,
            "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
            "launch_ref": f"launch:{native_id}",
        }


def new_launch_id() -> str:
    return "launch_" + uuid.uuid4().hex[:16]
