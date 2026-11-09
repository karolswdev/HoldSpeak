"""PARKED 20261109 (lane door/rest-park-waist): WorkbenchService.resolve_voice and its adapter.
No product caller (only its tests; HANDOVER Part IV 5); it ran a model on the 143 waist, not the engine door. Not imported.
"""


class _VoiceResolutionAdapter:
    """Keep raw resolver text inside the frozen typed route contract."""

    connector_id = "inference-provider"

    def __init__(self) -> None:
        from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter
        self._inner = CanonicalPromptAdapter()

    def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: Any) -> dict[str, Any]:
        result = self._inner.dispatch(engine, payload, cancellation)
        return {"reference": str(result.get("output") or ""), "confidence": 1.0}

    def cancel(self) -> str:
        return self._inner.cancel()


class _ParkedBody:  # parked 2026-11-09: kept at method indent, never imported
    # ── Voice resolution ─────────────────────────────────────────────────

    def resolve_voice(
        self, principal: Principal, workbench_id: str, text: str, request_id: str
    ) -> dict[str, Any]:
        now = time.monotonic()
        if now - self._resolve_timestamps.get(workbench_id, 0.0) < 2.0:
            raise ServiceError("resolver_rate_limited", "Wait before retrying", context={"error": "resolver_rate_limited", "detail": "Wait before retrying"})
        self._resolve_timestamps[workbench_id] = now
        if not text.strip():
            raise ValidationError("transcript is required")
        if principal is None or principal.kind is PrincipalKind.NONE:
            raise ServiceError("resolver_principal_required", "Authenticated principal required", context={"error": "resolver_principal_required"})
        wb = self._require_workbench(workbench_id)
        from holdspeak.voice_resolver import ZoneCatalogEntry, _extract_json_from_response, _validate_response, build_resolver_prompt
        zones = [ZoneCatalogEntry(id=z.id, name=z.name, items=0) for z in self._db.directories.list() if not getattr(z, "deleted", False)]
        if not zones:
            return {"refs": [], "egress": {}, "request_id": request_id, "attempts": 0}
        from holdspeak.kernel.runtime import _configure
        from holdspeak.services.inference_parent_route_bundle_service import InferenceParentRouteBundleService
        broker = _configure(self._db) if getattr(self, "_kernel", None) is None else self._kernel
        if principal.kind is PrincipalKind.OWNER:
            broker.inference_adoption_service.migrate_recipe_workbench_subject_assignments(principal)
        deadline = time.time() + 30
        bundle = InferenceParentRouteBundleService(broker, broker.inference_adoption_service).start(
            principal, command_id=f"voice-route-{request_id or uuid.uuid4().hex}", parent_kind="voice_reference_resolve",
            definition_ref=f"workbench:{workbench_id}", definition_revision=str(getattr(wb, "last_modified", "1")),
            input_snapshot={"workbench_id": workbench_id, "transcript_hash": hashlib.sha256(text.encode()).hexdigest()},
            deadline_at=deadline, lifecycle_child_budget=0,
            routes=[{"key": "resolve", "capability_id": "voice.reference_resolve", "invocation_id": f"voice:{request_id or uuid.uuid4().hex}", "subject_kind": "workbench", "subject_id": workbench_id}],
            parent_command_id=request_id or None,
        )
        parent, member = bundle["parent"], bundle["bundle"]["members"][0]
        if parent.replayed:
            receipt = broker.store.receipt(parent.operation_id) or {}
            return {"refs": [], "error": str(receipt.get("outcome") or "resolver_replayed"), "egress": {}, "request_id": request_id, "attempts": 0}
        from holdspeak.services.inference_route_plan_service import ROUTE_PLANNING_AUTHORITY
        route = broker.inference_adoption_service.plans.get_route_plan(ROUTE_PLANNING_AUTHORITY, str(member["route_plan_id"]))
        entry = dict(route["entries"][0])
        egress = {"boundary": str(entry["boundary"]), "model": str(entry["profile_id"]).removeprefix("legacy-")}
        prompt = build_resolver_prompt(zones, text)
        payload = {"system_prompt": "", "user_prompt": prompt, "temperature": 0.1, "max_tokens": 128,
                   "transcript_hash": hashlib.sha256(text.encode()).hexdigest(),
                   "catalog_hash": hashlib.sha256("|".join(f"{z.id}:{z.name}" for z in zones).encode()).hexdigest()}
        operation_id = "voice_reference_" + uuid.uuid4().hex

        def publish(value: Any, reservation: dict[str, Any]) -> str:
            digest = "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
            return broker.projection_stager.stage(str(reservation["child_invocation_id"]), "voice-resolver-attempt", {"output": str(dict(value).get("reference") or "")}, result_sha256=digest, receipt_result_ref=f"inference-result:{reservation['child_invocation_id']}/{digest}").result_ref

        admitted = broker.inference_adoption_service.admit_on_frozen_route(
            principal, command_id=f"{operation_id}:admit", route_plan_id=str(route["id"]), capability_id="voice.reference_resolve",
            operation_id=operation_id, payload=payload, reserved_output_tokens=128, parent_operation_id=parent.operation_id,
        )
        routed = broker.inference_adoption_service.execute(
            principal, execution_id=admitted["execution"]["id"], adapter=_VoiceResolutionAdapter(), publish=publish,
            parent_context=parent.context, planned_node="voice.reference_resolve",
        )
        try:
            receipt = broker.parent_run_controller.close(
                parent.context, "succeeded" if routed["outcome"] == "succeeded" else "failed",
                f"workbench:{workbench_id}", principal=principal,
            )
        except Exception as exc:
            # Cancellation can elect the parent terminal receipt while the
            # controller-owned model attempt is returning. Adopt that durable
            # winner rather than trying to overwrite it with a local close.
            from holdspeak.kernel.model import KernelRefused
            if not isinstance(exc, KernelRefused) or exc.reason != "parent_context_invalid":
                raise
            receipt = broker.store.receipt(parent.operation_id)
            if receipt is None:
                raise
        if routed["outcome"] != "succeeded" or receipt["outcome"] != "succeeded":
            disposition = str(receipt["outcome"]) if receipt["outcome"] != "succeeded" else str(routed["outcome"])
            return {"refs": [], "error": f"resolver_{disposition}", "egress": egress, "request_id": request_id, "attempts": len(routed["receipt"]["attempts"]), "route_execution_receipt": routed["receipt"]}
        raw = str(routed["result"]["reference"])
        parsed = _extract_json_from_response(raw)
        ids = None if parsed is None else _validate_response(parsed, {zone.id for zone in zones})
        if ids is None:
            return {"refs": [], "error": "resolver_parse_failure", "egress": egress, "request_id": request_id, "attempts": len(routed["receipt"]["attempts"]), "route_execution_receipt": routed["receipt"]}
        by_id = {zone.id: zone for zone in zones}
        return {"refs": [{"name": by_id[item].name, "id": item, "ref": f"zone:{item}", "kind": "zone"} for item in ids], "egress": egress, "request_id": request_id, "attempts": len(routed["receipt"]["attempts"]), "route_execution_receipt": routed["receipt"]}
