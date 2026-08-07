"""Transport-neutral capability invocation inspection and cancellation."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import uuid
from typing import Any

from ..db.core import Database
from ..principals import Principal, PrincipalKind
from .errors import ConflictError, NotFound


@observe_service
class InvocationService:
    """Own the durable invocation receipt and cancellation operation boundary."""

    def __init__(self, db: Database, broker: Any, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._broker = broker
        self._observer = observer or NullObserver()

    @classmethod
    def from_runtime(cls) -> "InvocationService":
        """Compose the production collaborators outside the HTTP adapter."""
        from ..db import get_database
        from ..kernel.runtime import _service

        return cls(get_database(), _service())

    @classmethod
    def recover_inference_on_startup(cls) -> list[str]:
        """Mark claimed inference invocations unknown after an unclean hub exit."""
        service = cls.from_runtime()
        claimed = [
            item
            for item in service._broker.store.operations_in_state("claimed")
            if item["name"] == "inference.run"
        ]
        recovered = service._db.capability_invocations.recover_running_unknown(
            [item["native_id"] for item in claimed]
        )
        for operation in claimed:
            if operation["native_id"] in recovered:
                node = Principal(PrincipalKind.NODE, operation["claimed_by"])
                service._broker.receipt(
                    operation["operation_id"],
                    "indeterminate",
                    f"invocation:{operation['native_id']}",
                    node,
                )
        return recovered

    def list(self, principal: Principal, *, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._db.capability_invocations.list(limit=limit)
        return [row.to_dict() for row in rows]

    def get(self, principal: Principal, invocation_id: str) -> dict[str, Any]:
        row = self._db.capability_invocations.get(invocation_id)
        if row is None:
            raise NotFound("invocation", invocation_id)
        return row.to_dict()

    def cancel(self, principal: Principal, invocation_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Record an approved owner cancellation and return its durable receipt."""
        parent = self._broker.store.operation_for_native(invocation_id)
        if parent is None or parent["name"] != "inference.run":
            raise NotFound("inference run", invocation_id)
        signal_id = str((payload or {}).get("signal_id") or "cancel_" + uuid.uuid4().hex)
        handle = self._broker.submit(
            {
                "request_schema": 1,
                "request_id": signal_id,
                "idempotency_key": signal_id,
                "operation": {"name": "inference.cancel", "version": 1},
                "parent_operation_id": parent["operation_id"],
                "target": {},
                "arguments": {
                    "invocation_id": invocation_id,
                    "signal_id": signal_id,
                    "reason": str((payload or {}).get("reason") or "owner_cancelled"),
                },
            },
            principal,
        )
        if handle["state"] == "refused":
            raise ConflictError(
                str(handle.get("receipt", {}).get("outcome") or "cancellation refused"),
                code="cancellation_refused",
                context={"handle": handle},
            )
        handle = self._broker.decide(
            handle["operation_id"], "approve", handle["revision"], principal
        )
        node = Principal(
            PrincipalKind.NODE, str(parent["placement"]).removeprefix("node:")
        )
        claimed = self._broker.claim(node, signal_id)
        if not claimed["operations"]:
            raise ConflictError("cancellation claim failed", code="cancellation_claim_failed")
        invocation = self._db.capability_invocations.cancel(invocation_id)
        receipt = self._broker.receipt(
            handle["operation_id"], "succeeded", f"invocation:{invocation_id}", node
        )
        return {
            "invocation": invocation.to_dict(),
            "operation_id": handle["operation_id"],
            "receipt": receipt,
        }
