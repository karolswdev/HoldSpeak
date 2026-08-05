"""Typed ``workbench_triage`` codec for kernel-admitted artifact triage.

HS-118-09: the owner triages workbench-minted artifacts — accept, reject,
or rework. Each triage verb is a consequential operation admitted through
the kernel with a terminal receipt. The codec validates arguments,
produces an admission, and stores no domain content in the journal.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from .model import Admission, KernelRefused, OperationRequest


_REQUIRED_FIELDS = frozenset({"workbench_id", "item_id", "artifact_id", "action"})
_VALID_ACTIONS = frozenset({"accept", "reject", "rework"})


@dataclass(frozen=True)
class TriageAdmission(Admission):
    workbench_id: str = ""
    item_id: str = ""
    artifact_id: str = ""
    action: str = ""


class WorkbenchTriageCodec:
    """Minimal codec: validates fields, builds admission, no side-effects."""

    name = "workbench_triage"
    version = 1

    def parse(self, request: OperationRequest) -> TriageAdmission:
        args = dict(request.arguments)
        missing = _REQUIRED_FIELDS - set(args)
        if missing:
            raise KernelRefused("missing_arguments", f"Missing: {missing}")

        workbench_id = str(args["workbench_id"]).strip()
        item_id = str(args["item_id"]).strip()
        artifact_id = str(args["artifact_id"]).strip()
        action = str(args["action"]).strip()

        if action not in _VALID_ACTIONS:
            raise KernelRefused("invalid_action", f"Invalid triage action: {action}")

        payload = json.dumps(
            {"item_id": item_id, "artifact_id": artifact_id, "action": action},
            separators=(",", ":"),
            sort_keys=True,
        )
        digest = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

        return TriageAdmission(
            target_ref=f"artifact:{artifact_id}",
            placement="propose",
            payload_hash=digest,
            refs=(f"workbench:{workbench_id}", f"workbench_item:{item_id}"),
            head=f"triage:{action}:{item_id}",
            ttl_seconds=300.0,
            native_id=f"triage-{action}-{item_id}",
            workbench_id=workbench_id,
            item_id=item_id,
            artifact_id=artifact_id,
            action=action,
        )

    def admit(
        self,
        request: OperationRequest,
        admission: Any,
        principal: Any,
        operation_id: str,
    ) -> None:
        """No side-effects on admission -- triage happens outside the codec."""

    def decide(
        self,
        native_id: str,
        decision: str,
        principal: Any,
        reason: str = "",
    ) -> None:
        """Triage auto-decides; no explicit owner decision needed."""
