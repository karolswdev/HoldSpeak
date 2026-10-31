"""Typed ``process.resize@1`` admission for a local terminal host PTY.

The codec stores only the immutable command reference, bounded dimensions and
its hash in the kernel journal.  The native tmux executor lives in the Delivery
command path, beside ``process.input@1``; terminal output/input bytes never
enter durable kernel content.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from typing import Any, Mapping

from .model import Admission, KernelRefused, OperationRequest, forbidden_content, valid_ref

MIN_WIDTH = 1
MAX_WIDTH = 500
MIN_HEIGHT = 1
MAX_HEIGHT = 300
_GENERATION = re.compile(r"^[A-Za-z0-9_.:-]{1,160}$")
_ALLOWED = frozenset(
    {
        "cols",
        "rows",
        "expected_generation",
        "expected_pane_id",
        "command_id",
        "session_key",
        "agent",
        "expected_sequence",
        "expires_in_seconds",
    }
)


def bounded_dimensions(width: Any, height: Any) -> tuple[int, int]:
    if type(width) is not int or type(height) is not int:
        raise KernelRefused("process_resize_dimensions_invalid")
    columns, rows = width, height
    if not MIN_WIDTH <= columns <= MAX_WIDTH or not MIN_HEIGHT <= rows <= MAX_HEIGHT:
        raise KernelRefused("process_resize_dimensions_out_of_bounds")
    return columns, rows


class ProcessResizeCodec:
    """Validate one typed resize intent without putting content in the journal."""

    name = "process.resize"
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
        target = request.target_ref
        generation = str(args.get("expected_generation") or "").strip()
        expected_pane_id = str(args.get("expected_pane_id") or "").strip()
        command_id = str(args.get("command_id") or "").strip()
        expected_sequence = args.get("expected_sequence")
        try:
            width, height = bounded_dimensions(args.get("cols"), args.get("rows"))
        except KernelRefused:
            raise
        if (
            not target.startswith("process:")
            or not valid_ref(target)
            or not _GENERATION.fullmatch(generation)
            or (
                expected_pane_id
                and not re.fullmatch(r"%[0-9]+", expected_pane_id)
            )
            or not isinstance(expected_sequence, int)
            or isinstance(expected_sequence, bool)
            or expected_sequence < 1
        ):
            raise KernelRefused("process_resize_prerequisite_failed")
        try:
            uuid.UUID(command_id)
        except (TypeError, ValueError) as exc:
            raise KernelRefused("process_resize_command_id_invalid") from exc
        raw_ttl = args.get("expires_in_seconds", 30.0)
        if isinstance(raw_ttl, bool) or not isinstance(raw_ttl, (int, float)):
            raise KernelRefused("process_resize_ttl_invalid")
        ttl = float(raw_ttl)
        if not math.isfinite(ttl) or ttl <= 0 or ttl > 300:
            raise KernelRefused("process_resize_ttl_invalid")
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
            head=f"terminal resize {width}x{height}",
            ttl_seconds=ttl,
            native_id=command_id,
        )

    def authorize(
        self,
        request: OperationRequest,
        admission: Admission,
        principal: Any,
        operation_id: str,
    ) -> Admission:
        return admission

    def admit(
        self,
        request: OperationRequest,
        admission: Admission,
        principal: Any,
        operation_id: str,
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


__all__ = [
    "MAX_HEIGHT",
    "MAX_WIDTH",
    "MIN_HEIGHT",
    "MIN_WIDTH",
    "ProcessResizeCodec",
    "bounded_dimensions",
]
