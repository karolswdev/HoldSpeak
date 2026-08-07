"""Typed ``workbench_mint`` codec for kernel-admitted artifact minting.

HS-118-06: every successful workbench item auto-mints an artifact in
``pending-review`` through the kernel.  The codec validates arguments,
produces an admission, and stores no domain content in the journal --
only refs and a payload digest.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from .model import Admission, KernelRefused, OperationRequest


_REQUIRED_FIELDS = frozenset({"recipe_id", "run_id", "item_id", "workbench_id"})


@dataclass(frozen=True)
class MintAdmission(Admission):
    recipe_id: str = ""
    run_id: str = ""
    item_id: str = ""
    workbench_id: str = ""


class WorkbenchMintCodec:
    """Minimal codec: validates fields, builds admission, no side-effects."""

    name = "workbench_mint"
    version = 1

    def parse(self, request: OperationRequest) -> MintAdmission:
        args = dict(request.arguments)
        missing = _REQUIRED_FIELDS - set(args)
        if missing:
            raise KernelRefused("missing_arguments", f"Missing: {missing}")

        recipe_id = str(args["recipe_id"]).strip()
        run_id = str(args["run_id"]).strip()
        item_id = str(args["item_id"]).strip()
        workbench_id = str(args["workbench_id"]).strip()

        payload = json.dumps(
            {"recipe_id": recipe_id, "run_id": run_id, "item_id": item_id},
            separators=(",", ":"),
            sort_keys=True,
        )
        digest = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

        return MintAdmission(
            target_ref=f"workbench_item:{item_id}",
            placement="propose",
            payload_hash=digest,
            refs=(f"workbench:{workbench_id}", f"recipe:{recipe_id}"),
            head=f"mint:{run_id}:{item_id}",
            ttl_seconds=300.0,
            native_id=f"mint-{run_id}-{item_id}",
            recipe_id=recipe_id,
            run_id=run_id,
            item_id=item_id,
            workbench_id=workbench_id,
        )

    def admit(
        self,
        request: OperationRequest,
        admission: Any,
        principal: Any,
        operation_id: str,
    ) -> None:
        """No side-effects on admission -- minting happens outside the codec."""

    def decide(
        self,
        native_id: str,
        decision: str,
        principal: Any,
        reason: str = "",
    ) -> None:
        """Workbench mints auto-decide; no explicit owner decision needed."""
