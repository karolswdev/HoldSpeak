"""Typed ``process.input`` codec over the existing terminal command record."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any, Mapping

from .model import Admission, KernelRefused, OperationRequest, forbidden_content, valid_ref

_GENERATION = re.compile(r"^[A-Za-z0-9_.:-]{1,160}$")
_ALLOWED = frozenset(
    {
        "text",
        "submit",
        "expected_generation",
        "command_id",
        "session_key",
        "agent",
        "expected_sequence",
        "expires_in_seconds",
    }
)


class ProcessInputCodec:
    """Validate terminal semantics while the broker remains driver-blind.

    The delivery command table owns the native send.  The kernel journal keeps
    only its command ref and the immutable payload hash.
    """

    name = "process.input"
    version = 1

    def __init__(self, commands: Any) -> None:
        self._commands = commands

    def validate(self, request: OperationRequest) -> Admission:
        args = request.arguments
        if forbidden_content(args):
            raise KernelRefused("journal_content_forbidden")
        unknown = set(args) - _ALLOWED
        if unknown:
            raise KernelRefused("operation_field_not_allowed", sorted(unknown)[0])
        text = args.get("text")
        submit = args.get("submit")
        generation = str(args.get("expected_generation") or "").strip()
        command_id = str(args.get("command_id") or "").strip()
        expected_sequence = args.get("expected_sequence")
        target = request.target_ref
        if (
            not isinstance(text, str)
            or not text.strip()
            or not isinstance(submit, bool)
            or not isinstance(expected_sequence, int)
            or isinstance(expected_sequence, bool)
            or expected_sequence < 1
            or not target.startswith("process:")
            or not valid_ref(target)
            or not _GENERATION.fullmatch(generation)
        ):
            raise KernelRefused("process_input_prerequisite_failed")
        try:
            uuid.UUID(command_id)
        except (TypeError, ValueError) as exc:
            raise KernelRefused("process_input_command_id_invalid") from exc
        try:
            ttl = float(args.get("expires_in_seconds") or 30.0)
        except (TypeError, ValueError) as exc:
            raise KernelRefused("process_input_ttl_invalid") from exc
        if ttl <= 0 or ttl > 300:
            raise KernelRefused("process_input_ttl_invalid")
        material = {
            "name": request.name,
            "version": request.version,
            "target_ref": target,
            "placement": request.placement,
            "arguments": dict(args),
        }
        canonical = json.dumps(material, separators=(",", ":"), sort_keys=True)
        payload_hash = "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
        refs = tuple(dict.fromkeys((*request.subject_refs, f"command:{command_id}")))
        return Admission(
            target_ref=target,
            placement=request.placement,
            payload_hash=payload_hash,
            refs=refs,
            head=f"terminal text {len(text.encode('utf-8'))} bytes submit={submit}",
            ttl_seconds=ttl,
            native_id=command_id,
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
        return None

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> None:
        return None

    def read_native(self, native_id: str) -> dict[str, Any] | None:
        return self._commands.get(native_id)

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        return []

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
        native = self._commands.get(native_id)
        domain_state = str((native or {}).get("hub_state") or "unknown")
        generic = {
            "sent": "waiting",
            "claimed": "running",
            "unknown": "unknown",
            "complete": "ended",
            "not_executed": "failed",
            "indeterminate_after_node_reset": "unknown",
        }.get(domain_state, "unknown")
        return {
            "process_id": f"process:{operation['operation_id']}",
            "kind": self.name,
            "principal": operation["principal_identity"],
            "generic_state": generic,
            "domain_state": domain_state,
            "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
            "command_ref": f"command:{native_id}",
        }
