"""PARKED 20261109 (lane door/own-choice-park-waist): no product caller after the engine door chose on its own (the door, schedules, pi and Meetings read the assignment chain).
Moved from holdspeak/services/inference_route_plan_service.py. Not imported.
"""



class _ParkedBody:
    def register_operation_evidence_provider(
        self, provider: RouteAdmissionEvidenceProvider
    ) -> None:
        """Register one internal evidence owner before any route is frozen.

        This remains a composition seam, not a feature request surface.  A
        ToolTurn parent needs its own evidence owner so no Ask/Recipe/Workbench
        adopter can accidentally become the first tool-bearing executor.
        """
        _safe_id(provider.id, field="evidence_provider_id")
        if (
            type(provider.revision) is not int
            or provider.revision < 1
            or not callable(provider.freeze)
            or not callable(provider.reconstruct)
            or (provider.reconstruct_attempt_budgets is not None and not callable(provider.reconstruct_attempt_budgets))
            or (provider.freeze_resolved is not None and not callable(provider.freeze_resolved))
        ):
            raise ValueError("invalid route admission evidence provider")
        if provider.id in self._operation_evidence_providers:
            raise ValueError("duplicate route admission evidence provider")
        claims = {
            (capability, policy)
            for capability in provider.capabilities
            for policy in provider.operation_policy_revisions
        }
        existing = {
            (capability, policy)
            for registered in self._operation_evidence_providers.values()
            for capability in registered.capabilities
            for policy in registered.operation_policy_revisions
        }
        if claims & existing:
            raise ValueError("ambiguous route admission evidence provider")
        self._operation_evidence_providers[provider.id] = provider

    def resolve_deployments(
        self, authority: Principal, *, capability_id: str,
    ) -> list[tuple[DeploymentRevision, bool]]:
        """Pure resolution, private side: each route leg's deployment and
        whether its preflight says it can run, in route order. For an
        executor outside the hub's own runner (a pi launch runs on the
        engine for coding work, ``delivery.pi_launch``). No durable or
        external effect; the deployment carries no key value."""
        self._require_planner(authority)
        capability = self._registry.require(capability_id)
        policy_revision = self._operation_policy(capability, None)
        with self._db._connection() as conn:
            conn.execute("BEGIN")
            try:
                _result, revisions, preflight = self._resolve_in_conn(
                    conn,
                    capability=capability,
                    operation_policy_revision=policy_revision,
                    invocation_id=None,
                    subject_kind=None,
                    subject_id=None,
                    plan_id=None,
                )
                conn.rollback()
            except Exception:
                conn.rollback()
                raise
        return [
            (revision, str((leg or {}).get("eligibility") or "") == "executable")
            for revision, leg in zip(revisions, preflight)
        ]

    def freeze_legacy_one_leg_plan(
        self,
        authority: Principal,
        *,
        command_id: str,
        capability_id: str,
        legacy_profile_id: str,
        operation_policy_revision: str | None = None,
        **extras: Any,
    ) -> dict[str, Any]:
        """Adapt exact stored v1 bytes to one explicit, replay-safe route plan."""
        self._require_planner(authority)
        if extras:
            raise ValidationError("Legacy route request has an invalid shape.", code="inference_route_plan_invalid")
        capability = self._registry.require(capability_id)
        policy = self._registry.retry_policy(capability.default_retry_policy_id)
        command = _safe_id(command_id, field="command_id")
        source_id = _safe_id(legacy_profile_id, field="legacy_profile_id")
        request_hash = _sha256({"command_id": command, "capability_id": capability.id, "legacy_profile_id": source_id, "operation_policy_revision": operation_policy_revision})
        expected_plan_id = self._deterministic_id("legacy-route", command, request_hash)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                replay = conn.execute("SELECT * FROM inference_route_plan_commands WHERE command_id=?", (command,)).fetchone()
                if replay is not None:
                    if str(replay["request_sha256"]) != request_hash:
                        raise ConflictError("Route command changed.", code="inference_route_plan_command_conflict")
                    result = self._route_from_row(conn, conn.execute("SELECT * FROM inference_route_plans WHERE id=?", (replay["plan_id"],)).fetchone())
                    if str(replay["plan_sha256"]) != result["sha256"] or result["id"] != expected_plan_id:
                        raise ConflictError("Stored route command effect is invalid.", code="inference_route_plan_command_integrity_invalid")
                    conn.commit()
                    return result
                row = conn.execute("SELECT * FROM profiles WHERE id=? AND deleted=0", (source_id,)).fetchone()
                if row is None:
                    raise NotFound("legacy profile", source_id)
                self._refuse_route_identity_collision(conn, expected_plan_id)
                source = SimpleNamespace(**dict(row))
                adapted = adapt_v1_profile(source)
                deployment_revision = self._legacy_deployment(source)
                context_limit = int(row["context_limit"] or 0)
                if context_limit > 0:
                    deployment_revision = _replace(deployment_revision, context_ceiling=context_limit)
                boundary = _BOUNDARIES.get(deployment_revision.boundary)
                if boundary not in capability.allowed_boundaries:
                    raise ValidationError("Legacy target boundary is not permitted.", code="inference_route_boundary_unsupported")
                context = self._context_support({"mode": "bounded", "maximum_tokens": context_limit})
                self._validate_legacy_compatibility(capability, context, boundary)
                created = self._clock()
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                digest = hashlib.sha256(deployment_revision.id.encode()).hexdigest()[:24]
                material = self._legacy_material(
                    capability=capability, policy=policy, adapted=adapted,
                    deployment_revision=deployment_revision, boundary=boundary,
                    context=context, digest=digest, created=created,
                    operation_policy_revision=operation_policy_revision, plan_id=expected_plan_id,
                )
                route_hash = _sha256(material)
                self._insert_route(conn, material, route_hash, [deployment_revision], capability_definition=capability.canonical_dict(), retry_policy_definition=policy.canonical_dict(), frozen_preflight=({"route_leg_ordinal": 1, "eligibility": "executable", "reason_code": None},))
                conn.execute("INSERT INTO inference_route_plan_commands (command_id, request_sha256, plan_id, plan_sha256, created_at) VALUES (?,?,?,?,?)", (command, request_hash, material["id"], route_hash, material["created_at"]))
                conn.commit()
                return {**material, "sha256": route_hash}
            except Exception:
                conn.rollback()
                raise

    def freeze_operation_for_route(
        self,
        authority: Principal,
        *,
        command_id: str,
        route_plan_id: str,
        operation_id: str,
        planning_reference: str,
    ) -> dict[str, Any]:
        """Attach exact operation material to an already-frozen route.

        Speech sessions freeze assignment/deployment truth at logical admission,
        then use this seam once transcript-derived material exists. No mutable
        assignment, profile, binding, readiness, or Config selector is reread.
        """
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                result = self.freeze_operation_for_route_in_transaction(
                    authority, conn, command_id=command_id,
                    route_plan_id=route_plan_id, operation_id=operation_id,
                    planning_reference=planning_reference,
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return result

    def route_leg_evidence(
        self,
        authority: Principal,
        *,
        operation_plan_id: str,
        route_leg_ordinal: int,
    ) -> dict[str, Any]:
        """Return a non-authorizing leg template; Story 06 owns attempts."""
        self._require_planner(authority)
        if type(route_leg_ordinal) is not int or route_leg_ordinal < 1:
            raise ValidationError("route leg ordinal is invalid", code="inference_route_plan_invalid")
        operation = self.get_operation_request_plan(authority, operation_plan_id)
        leg = next(
            (item for item in operation["entries"] if item["route_leg_ordinal"] == route_leg_ordinal),
            None,
        )
        if leg is None or leg["eligibility"] != "executable":
            raise ValidationError("route leg is not executable", code="inference_route_leg_unavailable")
        route = self.get_route_plan(authority, operation["route_plan_id"])
        route_leg = route["entries"][route_leg_ordinal - 1]
        return {
            "schema": "InferenceRouteLegEvidence@1",
            "route_plan_id": route["id"],
            "route_plan_sha256": route["sha256"],
            "operation_request_plan_id": operation["id"],
            "operation_request_plan_sha256": operation["sha256"],
            "route_leg_ordinal": route_leg_ordinal,
            "deployment_revision_id": route_leg["deployment_revision_id"],
            "admitted_request_id": leg["admitted_request_id"],
            "admitted_request_sha256": leg["admitted_request_sha256"],
            "context_plan_sha256": leg["context_plan_sha256"],
            "serialized_request_sha256": leg["serialized_request_sha256"],
        }



class _ParkedBody:
    def _legacy_material(self, *, capability: Any, policy: Any, adapted: Mapping[str, Any], deployment_revision: DeploymentRevision, boundary: str, context: Mapping[str, Any], digest: str, created: datetime, operation_policy_revision: Any, plan_id: str | None) -> dict[str, Any]:
        return {
            "schema": ROUTE_PLAN_SCHEMA,
            "id": _safe_id(plan_id or "irp_" + uuid.uuid4().hex, field="plan_id"),
            "capability": {
                "id": capability.id,
                "revision": capability.revision,
                "schema_sha256": capability.schema_sha256,
            },
            "source": {
                "assignment_id": f"legacy-target-{digest}",
                "assignment_revision": 1,
                "assignment_sha256": _sha256({"legacy_deployment_revision_id": deployment_revision.id}),
                "inherited_from": "legacy_override",
            },
            "entries": [{
                "ordinal": 1,
                "profile_id": f"legacy-target-{digest}",
                "profile_revision": 1,
                "profile_schema_version": 1,
                "binding_id": f"legacy-binding-{digest}",
                "binding_revision": 1,
                "deployment_head_id": f"legacy-target-{digest}",
                "deployment_configuration_revision": 1,
                "deployment_revision_id": deployment_revision.id,
                "capability_manifest_sha256": adapted["profile"]["capability_manifest"]["sha256"],
                "boundary": boundary,
                "context_support": context,
            }],
            "retry_policy": {
                "id": policy.id,
                "revision": policy.revision,
                "sha256": policy.sha256,
                "per_entry_attempts": policy.per_entry_attempts,
                "total_physical_attempts": policy.total_physical_attempts,
                "deadline_ms": policy.deadline_ms,
                "token_budget": policy.token_budget,
                "cost_budget": policy.cost_budget,
                "tool_call_budget": policy.tool_call_budget,
                "fallback_dispositions": list(policy.fallback_dispositions),
                "retryable_dispositions": list(policy.retryable_dispositions),
            },
            "operation_policy_revision": self._operation_policy(capability, operation_policy_revision),
            "created_at": _timestamp(created),
            "deadline_at": _timestamp(created + timedelta(milliseconds=policy.deadline_ms)),
        }

    @staticmethod
    def _validate_legacy_compatibility(capability: Any, context: Mapping[str, Any], boundary: str) -> None:
        requires = capability.requires
        language_input = set(capability.input_modalities).issubset({"text"})
        if (
            not language_input
            or requires.structured_output
            or requires.structured_tools
            or requires.audio
            or requires.vision
            or requires.capability_classes
            or int(context["maximum_tokens"]) < requires.minimum_context_tokens
            or boundary not in capability.allowed_boundaries
        ):
            raise ValidationError(
                "Legacy model lacks exact capability evidence.",
                code="no_compatible_assignment",
                context={"capability_id": capability.id},
            )

