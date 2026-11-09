"""PARKED 20261109 (lane door/own-choice-park-waist): no product caller after the engine door chose on its own (the door, schedules, pi and Meetings read the assignment chain).
Moved from holdspeak/services/inference_parent_route_bundle_service.py. Not imported.
"""



class _ParkedBody:
    def record_pre_route_refusal(
        self,
        principal: Principal,
        *,
        command_id: str,
        parent_kind: str,
        definition_ref: str,
        definition_revision: str,
        input_snapshot: Mapping[str, Any],
        deadline_at: float,
        reason: str,
    ) -> dict[str, Any]:
        """Durably terminalize a deterministic parent when route freeze cannot start.

        This deliberately happens outside the route transaction: no bundle, route,
        execution, or model child exists on this path.  Adopters call it only for
        pre-route ``ValidationError`` outcomes; controller-owned attempt outcomes
        retain their real child receipts instead.
        """
        command = _safe(command_id, field="command_id")
        refusal = _safe(reason, field="refusal_reason")
        # A pre-route refusal is a different terminal action from the later
        # executable bundle.  Its identity is deterministic for an identical
        # refusal, content-free, and reason-bound, but it deliberately never
        # reuses the executable command identity: a repair (for example an
        # assignment created after a refusal) must be able to freeze its route.
        refusal_identity = "pre-route-refusal:" + _sha256({
            "schema": "InferencePreRouteRefusalIdentity@1",
            "command_id": command,
            "reason": refusal,
        }).removeprefix("sha256:")
        parent = self._parents.start(
            principal,
            kind=str(parent_kind),
            definition_ref=str(definition_ref),
            definition_revision=str(definition_revision),
            input_snapshot=dict(input_snapshot),
            deadline_at=float(deadline_at),
            child_budget=0,
            idempotency_key=refusal_identity,
        )
        existing = self._broker.store.receipt(parent.operation_id)
        if existing is None:
            existing = self._parents.close(
                parent.context,
                "refused",
                f"parent-route-bundle:{refusal}",
                principal=principal,
            )
        if str(existing.get("outcome") or "") != "refused":
            # Never reinterpret an executable (or any other) terminal receipt
            # as a refusal merely because an identity store returned it.
            raise ConflictError(
                "Pre-route refusal identity resolved to a non-refusal receipt.",
                code="inference_pre_route_refusal_identity_conflict",
            )
        return {"parent": parent, "receipt": dict(existing)}

