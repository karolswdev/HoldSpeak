"""PARKED 20261109 (lane door/own-choice-park-waist): no product caller after the engine door chose on its own (the door, schedules, pi and Meetings read the assignment chain).
Moved from holdspeak/services/inference_adoption_service.py. Not imported.
"""



class _ParkedBody:
    def admit_in_transaction(
        self,
        principal: Principal,
        conn: Any,
        *,
        command_id: str,
        capability_id: str,
        operation_id: str,
        payload: Mapping[str, Any],
        invocation_id: str | None = None,
        reserved_output_tokens: int = 512,
    ) -> dict[str, Any]:
        """Bind an adopter's logical reservation to route+controller atomically."""
        if principal.kind is not PrincipalKind.OWNER:
            raise ValidationError("Owner authority is required.", code="inference_adoption_owner_required")
        capability = self._registry.require(capability_id)
        command, operation = _safe(command_id, field="command_id"), _safe(operation_id, field="operation_id")
        reference = "iam_" + hashlib.sha256(
            f"{command}:{operation}:{_sha256(dict(payload))}".encode()
        ).hexdigest()[:32]
        route_request: dict[str, Any] = {"capability_id": capability.id}
        if invocation_id:
            route_request["invocation_id"] = _safe(invocation_id, field="invocation_id")
        return self._admit_in_conn(
            conn, command=command, capability=capability, operation=operation,
            payload=payload, reserved_output_tokens=reserved_output_tokens,
            reference=reference, route_request=route_request,
        )

    def admit_composite(
        self,
        principal: Principal,
        *,
        command_id: str,
        operations: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Atomically reserve every constituent route/execution or none."""
        if principal.kind is not PrincipalKind.OWNER:
            raise ValidationError(
                "Owner authority is required.", code="inference_adoption_owner_required"
            )
        command = _safe(command_id, field="command_id")
        if not operations or len(operations) > 5:
            raise ValidationError(
                "Composite operations are invalid.",
                code="inference_adoption_composite_invalid",
            )
        request = [dict(value) for value in operations]
        request_sha = _sha256(request)
        for item in request:
            required = {"capability_id", "operation_id", "payload"}
            if set(item) - (required | {"reserved_output_tokens", "invocation_id", "subject_kind", "subject_id"}) or not required.issubset(item):
                raise ValidationError(
                    "Composite operation has an invalid shape.",
                    code="inference_adoption_composite_invalid",
                )
        composite_id = "iac_" + hashlib.sha256(
            f"{command}:{request_sha}".encode()
        ).hexdigest()[:32]
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                existing = conn.execute(
                    "SELECT * FROM inference_adoption_composites WHERE command_id=?",
                    (command,),
                ).fetchone()
                if existing is not None:
                    if str(existing["request_sha256"]) != request_sha:
                        raise ConflictError("Composite command changed.", code="inference_adoption_composite_conflict")
                    operation_plan_ids = json.loads(str(existing["operation_plan_ids_json"]))
                    result = {"schema": "InferenceAdoptionComposite@1", "id": str(existing["composite_id"]), "operation_plan_ids": operation_plan_ids}
                    if str(existing["result_sha256"]) != _sha256(result):
                        raise ConflictError("Composite evidence changed.", code="inference_adoption_composite_integrity_invalid")
                    conn.commit()
                    return result
                admitted = []
                for ordinal, item in enumerate(request, 1):
                    capability = self._registry.require(str(item["capability_id"]))
                    operation = _safe(item["operation_id"], field="operation_id")
                    subcommand = f"{command}-{ordinal}"
                    reference = "iam_" + hashlib.sha256(
                        f"{subcommand}:{operation}:{_sha256(dict(item['payload']))}".encode()
                    ).hexdigest()[:32]
                    route_request: dict[str, Any] = {"capability_id": capability.id}
                    for name in ("invocation_id", "subject_kind", "subject_id"):
                        if item.get(name):
                            route_request[name] = item[name]
                    admitted.append(self._admit_in_conn(
                        conn, command=subcommand, capability=capability,
                        operation=operation, payload=dict(item["payload"]),
                        reserved_output_tokens=int(item.get("reserved_output_tokens", 512)),
                        reference=reference, route_request=route_request,
                    ))
                operation_plan_ids = [value["operation_request_plan"]["id"] for value in admitted]
                result = {"schema": "InferenceAdoptionComposite@1", "id": composite_id, "operation_plan_ids": operation_plan_ids}
                conn.execute(
                    "INSERT INTO inference_adoption_composites (composite_id, command_id, request_sha256, operation_plan_ids_json, result_sha256, created_at) VALUES (?,?,?,?,?,?)",
                    (
                        composite_id, command, request_sha,
                        _canonical(operation_plan_ids), _sha256(result), _now(),
                    ),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return result

    def freeze_routes(
        self,
        principal: Principal,
        *,
        command_id: str,
        deadline_at: float,
        routes: Sequence[Mapping[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Freeze a parent's named future routes in one canonical transaction.

        Unlike ``InferenceParentRouteBundleService``, a linear Sequence may need
        several routes of the same capability (one per saved Recipe).  This
        façade deliberately freezes route evidence only; each later child still
        attaches its private operation material through ``admit_on_frozen_route``
        and executes under the controller.  Nothing here selects a target.
        """
        if principal.kind is not PrincipalKind.OWNER or not routes:
            raise ValidationError(
                "Parent routes are invalid.", code="inference_adoption_composite_invalid"
            )
        command = _safe(command_id, field="command_id")
        try:
            deadline = float(deadline_at)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "Parent route deadline is invalid.",
                code="inference_adoption_composite_invalid",
            ) from exc
        if deadline <= time.time():
            raise ValidationError(
                "Parent route deadline has elapsed.",
                code="inference_adoption_composite_invalid",
            )
        frozen: dict[str, dict[str, Any]] = {}
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                for ordinal, raw in enumerate(routes, 1):
                    if not isinstance(raw, Mapping):
                        raise ValidationError(
                            "Parent route is invalid.",
                            code="inference_adoption_composite_invalid",
                        )
                    required = {"key", "capability_id", "invocation_id"}
                    optional = {"subject_kind", "subject_id"}
                    if (
                        not required.issubset(raw)
                        or set(raw) - (required | optional)
                        or (("subject_kind" in raw) != ("subject_id" in raw))
                    ):
                        raise ValidationError(
                            "Parent route is invalid.",
                            code="inference_adoption_composite_invalid",
                        )
                    key = _safe(raw["key"], field="route_key")
                    if key in frozen:
                        raise ValidationError(
                            "Parent route keys must be unique.",
                            code="inference_adoption_composite_invalid",
                        )
                    request: dict[str, Any] = {
                        "capability_id": _safe(raw["capability_id"], field="capability_id"),
                        "invocation_id": _safe(raw["invocation_id"], field="invocation_id"),
                        "deadline_at": deadline,
                    }
                    if "subject_kind" in raw:
                        request["subject_kind"] = _safe(raw["subject_kind"], field="subject_kind")
                        request["subject_id"] = _safe(raw["subject_id"], field="subject_id")
                    frozen[key] = self.plans.freeze_route_plan_in_transaction(
                        ROUTE_PLANNING_AUTHORITY,
                        conn,
                        command_id=f"{command}-{ordinal}",
                        **request,
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return frozen

    def execute_stream(
        self,
        principal: Principal,
        *,
        execution_id: str,
        adapter: Any,
        on_delta: Any,
        publish: Callable[[Any, Mapping[str, Any]], str] | None = None,
        before_physical_dispatch: Callable[[str, str, int], None] | None = None,
        parent_context: Any = None,
        planned_node: str = "",
        payload_redactor: Callable[[dict, Mapping[str, Any]], dict] | None = None,
    ) -> dict[str, Any]:
        """Streaming twin of ``execute`` (HS-151-04).

        Identical admitted-execution bookkeeping (frozen plan, attempt rows,
        receipt attestation, disposition) but calls
        ``InferenceRunner.invoke_stream`` and forwards each ``Delta`` to
        *on_delta*, returning the same result shape at the end.

        *payload_redactor*, when provided, is called with ``(payload, route)``
        after the payload is reconstructed from frozen evidence and before it
        is handed to the InvocationRequest / runner.  The frozen route plan's
        boundary is known at this point, so the redactor can apply
        egress-dependent transformations (e.g. People M1 redaction on cloud
        egress).  The admission evidence itself is never altered.
        """
        if self._broker is None:
            raise ServiceError(
                "inference_adoption_runner_missing",
                "Production execution requires a composed broker",
            )
        runner = self._broker.inference_runner
        runtime = getattr(runner, "_routed_attempt_runtime", None)
        if runtime is None or getattr(runtime, "_controller", None) is not self.controller:
            raise ServiceError(
                "inference_adoption_runtime_misconfigured",
                "The process-owned routed runtime is not composed",
            )
        execution = self.controller._execution(None, execution_id)
        receipt_authority = INFERENCE_FALLBACK_AUTHORITY
        operation = self.plans.get_operation_request_plan(
            ROUTE_PLANNING_AUTHORITY, execution["operation_plan_id"]
        )
        route = self.plans.get_route_plan(
            ROUTE_PLANNING_AUTHORITY, operation["route_plan_id"]
        )
        frozen_definition = self._frozen_capability_definition(str(route["id"]))
        if execution["state"] in {"terminal", "stopped"}:
            receipt = self.controller.get_route_execution_receipt(
                receipt_authority, execution_id=execution_id
            )
            replay: dict[str, Any] = {
                "outcome": receipt["outcome"],
                "result": self._durable_winner_result(receipt),
                "receipt": receipt,
            }
            if receipt["outcome"] == "succeeded":
                winning = self._winning_reservation(
                    execution_id, str(receipt.get("winning_attempt_id") or "")
                )
                replay["winning_reservation"] = winning
                self._publish_winner_if_unstaged(publish, replay["result"], winning)
            return replay
        frozen_deadline = datetime.fromisoformat(
            str(route["deadline_at"]).replace("Z", "+00:00")
        ).timestamp()
        next_attempt = int(execution.get("attempts_reserved") or 0) + 1
        while True:
            effect = self.controller.reserve_next_attempt(
                INFERENCE_FALLBACK_AUTHORITY,
                command_id=f"reserve-{execution_id}-{next_attempt}",
                execution_id=execution_id,
            )
            next_attempt += 1
            reservation = effect["reservation"]
            if reservation is None:
                receipt = self.controller.get_route_execution_receipt(
                    receipt_authority, execution_id=execution_id
                )
                replay = {
                    "outcome": receipt["outcome"],
                    "result": self._durable_winner_result(receipt),
                    "receipt": receipt,
                }
                if receipt["outcome"] == "succeeded":
                    winning = self._winning_reservation(
                        execution_id, str(receipt.get("winning_attempt_id") or "")
                    )
                    replay["winning_reservation"] = winning
                    self._publish_winner_if_unstaged(publish, replay["result"], winning)
                return replay
            serialized = self.evidence.serialized_request(
                operation["admission_evidence_ref"],
                int(reservation["route_leg_ordinal"]),
            )
            payload = dict(serialized["payload"])
            # HS-151-04 M5: apply caller-supplied redaction AFTER the payload
            # is reconstructed from frozen evidence and BEFORE it reaches the
            # engine.  The frozen route plan (``route``) carries the boundary
            # the redactor needs.  Admission evidence is never altered.
            if payload_redactor is not None:
                payload = payload_redactor(payload, route)
            captured: dict[str, Any] = {}

            def project(value: Any) -> str:
                try:
                    self._validate_frozen_result(frozen_definition, value)
                except Exception as exc:
                    from ..kernel.provider_signals import InferenceInvalidTypedOutput
                    raise InferenceInvalidTypedOutput() from exc
                captured["value"] = value
                result_json, result_sha = _canonical(value), _sha256(value)
                producer_result_ref = (
                    f"inference-result:{reservation['child_invocation_id']}/{result_sha}"
                )
                with self._db._connection() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    prior = conn.execute(
                        "SELECT * FROM inference_adoption_attempt_results WHERE attempt_id=?",
                        (str(reservation["attempt_id"]),),
                    ).fetchone()
                    if prior is None:
                        conn.execute(
                            "INSERT INTO inference_adoption_attempt_results (attempt_id, child_invocation_id, producer_result_ref, result_json, result_sha256, created_at) VALUES (?,?,?,?,?,?)",
                            (
                                str(reservation["attempt_id"]),
                                str(reservation["child_invocation_id"]),
                                producer_result_ref,
                                result_json,
                                result_sha,
                                _now(),
                            ),
                        )
                    elif (
                        str(prior["child_invocation_id"]) != str(reservation["child_invocation_id"])
                        or str(prior["producer_result_ref"]) != producer_result_ref
                        or str(prior["result_json"]) != result_json
                        or str(prior["result_sha256"]) != result_sha
                    ):
                        raise ConflictError("Attempt result changed.", code="inference_adoption_result_integrity_invalid")
                return producer_result_ref

            request = InvocationRequest(
                str(reservation["deployment_revision_id"]),
                ServiceContract.for_payload(
                    str(serialized["contract"]),
                    str(serialized["contract_revision"]),
                    payload,
                ),
                frozen_deadline,
                payload,
                str(reservation["child_invocation_id"]),
                parent_operation_id=str(
                    getattr(parent_context, "operation_id", "") or ""
                ),
                attempt_ordinal=int(reservation["physical_attempt_ordinal"]),
                route_attempt_reservation=reservation,
                before_physical_dispatch=before_physical_dispatch,
            )
            from ..kernel.runtime import _as_principal

            with _as_principal(principal):
                runner_outcome = runner.invoke_stream(
                    request, adapter, on_delta=on_delta,
                    publish=project, parent_context=parent_context,
                    planned_node=planned_node,
                )
            receipt = self.controller.get_route_execution_receipt(
                receipt_authority, execution_id=execution_id
            )
            if receipt["outcome"] == "succeeded":
                winning = self._winning_reservation(
                    execution_id, str(receipt.get("winning_attempt_id") or "")
                )
                value = self._durable_winner_result(receipt)
                if value is None:
                    raise ConflictError(
                        "Winner result is missing.",
                        code="inference_adoption_result_integrity_invalid",
                    )
                self._publish_winner_if_unstaged(publish, value, winning)
                return {
                    "outcome": "succeeded",
                    "result": value,
                    "receipt": receipt,
                    "winning_reservation": winning,
                }
            if receipt["state"] == "terminal":
                return {
                    "outcome": receipt["outcome"],
                    "result": None,
                    "receipt": receipt,
                    "error": str(getattr(runner_outcome, "error", "") or ""),
                }
            execution = self.controller._execution(None, execution_id)

    def stop_operation(
        self, principal: Principal, *, command_id: str, operation_id: str
    ) -> dict[str, Any]:
        """Stop the controller owning one logical adopted operation."""
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT e.id FROM inference_route_executions e
                   JOIN inference_operation_route_request_plans o ON o.id=e.operation_plan_id
                   WHERE o.operation_id=? ORDER BY o.created_at DESC LIMIT 1""",
                (_safe(operation_id, field="operation_id"),),
            ).fetchone()
        if row is None:
            return {"execution": {"state": "not_started"}, "child_signal": "not_dispatched"}
        return self.stop(
            principal, command_id=command_id, execution_id=str(row["id"])
        )

    def next_run_summary(
        self,
        principal: Principal,
        *,
        capability_id: str,
        invocation_id: str | None = None,
        subject_kind: str | None = None,
        subject_id: str | None = None,
    ) -> dict[str, Any]:
        if principal.kind is not PrincipalKind.OWNER:
            raise ValidationError(
                "Owner authority is required.", code="inference_adoption_owner_required"
            )
        try:
            capability = self._registry.require(capability_id)
            operation_policy = self.plans._operation_policy(capability, None)
            with self._db._connection() as conn:
                conn.execute("BEGIN")
                route, _revisions, preflight = self.plans._resolve_in_conn(
                    conn,
                    capability=capability,
                    operation_policy_revision=operation_policy,
                    invocation_id=invocation_id,
                    subject_kind=subject_kind,
                    subject_id=subject_id,
                    plan_id=None,
                )
                active_row = None
                if invocation_id:
                    active_row = conn.execute(
                        """SELECT e.id,e.state,e.terminal_outcome,e.winning_attempt_id,
                                  e.route_plan_id,e.operation_plan_id
                             FROM inference_route_executions e
                             JOIN inference_operation_route_request_plans o
                               ON o.id=e.operation_plan_id
                            WHERE o.operation_id=?
                            ORDER BY e.rowid DESC LIMIT 1""",
                        (invocation_id,),
                    ).fetchone()
                conn.rollback()
        except ServiceError as exc:
            repair = {
                "no_assignment": "choose_model",
                "no_compatible_assignment": "choose_compatible_model",
                "inference_route_profile_unavailable": "repair_model",
            }.get(exc.code, "review_model_setup")
            return {
                "schema": "InferenceNextRunSummary@1",
                "capability_id": capability_id,
                "status": "needs_attention",
                "repair": repair,
                "reason_code": exc.code,
                "chain": [],
                "active_execution": None,
            }
        executable = [item for item in preflight if item["eligibility"] == "executable"]
        reason = next(
            (str(item.get("reason_code") or "model_not_ready") for item in preflight
             if item["eligibility"] != "executable"),
            None,
        )
        repair = {
            "binding_disabled": "enable_model_binding",
            "binding_not_ready": "repair_model_readiness",
            "context_overflow": "choose_larger_context_model",
        }.get(reason or "", "review_model_setup") if not executable else None
        return {
            "schema": "InferenceNextRunSummary@1",
            "capability_id": capability_id,
            "status": "ready" if executable else "needs_attention",
            "repair": repair,
            "reason_code": None if executable else reason,
            "source": route["source"]["inherited_from"],
            "chain": [
                {
                    "ordinal": leg["ordinal"],
                    "profile_id": leg["profile_id"],
                    "profile_revision": leg["profile_revision"],
                    "boundary": leg["boundary"],
                    "context_tokens": leg["context_support"]["maximum_tokens"],
                    "eligibility": preflight[index]["eligibility"],
                    "reason_code": preflight[index].get("reason_code"),
                }
                for index, leg in enumerate(route["entries"])
            ],
            "active_execution": None if active_row is None else {
                "execution_id": str(active_row["id"]),
                "route_plan_id": str(active_row["route_plan_id"]),
                "operation_plan_id": str(active_row["operation_plan_id"]),
                "state": str(active_row["state"]),
                "terminal_outcome": active_row["terminal_outcome"],
                "winning_attempt_id": active_row["winning_attempt_id"],
                "frozen": True,
            },
        }

    def apply_next_run_override(
        self,
        principal: Principal,
        *,
        command_id: str,
        invocation_id: str,
        capability_id: str,
        entries: Sequence[Mapping[str, Any]],
        expected_revision: int = 0,
    ) -> dict[str, Any]:
        return InferenceAssignmentService(self._db, registry=self._registry).set_assignment(
            principal,
            {
                "command_id": command_id,
                "expected_revision": expected_revision,
                "scope": {
                    "kind": "invocation",
                    "invocation_id": invocation_id,
                    "capability_id": capability_id,
                },
                "entries": [dict(value) for value in entries],
            },
        )

