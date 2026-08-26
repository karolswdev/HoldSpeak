"""Transport-neutral Workbench operations (HS-122-02)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import hashlib
import json
import time
import uuid
from typing import Any

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, NotFound, ServiceError, ValidationError


SKILL_BODY_LIMIT = 8192


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


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


@observe_service
class WorkbenchService:
    # Route adapters create a short-lived service per request; limiter state is shared.
    _resolve_timestamps: dict[str, float] = {}

    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def _refuse_post_marker_pointer_write(self, principal: Principal, fields: dict[str, Any]) -> None:
        """Compatibility selectors are write-through inputs, never execution truth."""
        # Kept as the existing call-site seam for browser/MCP compatibility. The
        # actual canonical mutation happens after the durable Workbench write.
        return None

    def _write_legacy_pointer_compatibility(self, principal: Principal, workbench_id: str, fields: dict[str, Any]) -> None:
        from .inference_adoption_service import RECIPE_WORKBENCH_MIGRATION_FAMILY
        from .inference_assignment_service import InferenceAssignmentService
        assignments = InferenceAssignmentService(self._db)
        if assignments.migration_marker(principal, family=RECIPE_WORKBENCH_MIGRATION_FAMILY) is None:
            return
        for field, capability_id in (("profile_id", "workbench.item"), ("resolver_profile_id", "voice.reference_resolve")):
            if field not in fields:
                continue
            scope = {"kind": "subject", "subject_kind": "workbench", "subject_id": workbench_id, "capability_id": capability_id}
            try:
                current = assignments.get_assignment(principal, scope)
            except NotFound:
                current = None
            profile_id = str(fields[field] or "").strip()
            if not profile_id:
                if current is not None:
                    assignments.clear_assignment(principal, {"command_id": f"workbench-pointer-clear-{workbench_id}-{capability_id}", "expected_revision": current["revision"], "scope": scope, "capability_id": capability_id, "subject_kind": "workbench", "subject_id": workbench_id})
                continue
            with self._db._connection() as conn:
                row = conn.execute("SELECT MAX(revision) FROM model_profile_revisions WHERE profile_id=?", (profile_id,)).fetchone()
                legacy = conn.execute("SELECT 1 FROM profiles WHERE id=? AND deleted=0", (profile_id,)).fetchone()
            entry = profile_id if int(row[0] or 0) else (f"legacy-{profile_id}" if legacy is not None else profile_id)
            assignments.set_assignment(principal, {"command_id": f"workbench-pointer-write-{workbench_id}-{capability_id}", "expected_revision": 0 if current is None else current["revision"], "scope": scope, "entries": [{"profile_id": entry}]})

    # ── Workbenches ──────────────────────────────────────────────────────

    def list_workbenches(self, principal: Principal) -> list[dict[str, Any]]:
        return [self._wb_payload(wb, principal) for wb in self._db.workbenches.list()]

    def get_workbench(self, principal: Principal, workbench_id: str) -> dict[str, Any]:
        wb = self._require_workbench(workbench_id)
        return self._wb_payload(wb, principal)

    def create_workbench(self, principal: Principal, *, name: str, **fields: Any) -> dict[str, Any]:
        if not name.strip():
            raise ValidationError("Workbench name is required")
        self._refuse_post_marker_pointer_write(principal, fields)
        body = {"name": name, **fields}
        fields = self._wb_fields(body)
        if fields["schedule_enabled"] and principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("owner_principal_required", "Only the owner can enable a schedule", context={"status": 403})
        workbench_id = str(body.pop("id", "") or _new_id("workbench"))
        if not fields["schedule_enabled"]:
            wb = self._db.workbenches.upsert(workbench_id=workbench_id, **fields)
            self._write_legacy_pointer_compatibility(principal, wb.id, body)
            return self._wb_payload(wb, principal)
        # The owner's single enable gesture commits its configuration, captured
        # deployment revision, and local delegation as one crash-consistent unit.
        from holdspeak.kernel.runtime import _configure
        _configure(self._db)
        from .schedule_delegation import ScheduleDelegationService
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            wb = self._db.workbenches.upsert_in_transaction(conn, workbench_id=workbench_id, **fields)
            ScheduleDelegationService(self._db).enable_from_owner_in_transaction(principal, wb, conn)
        self._write_legacy_pointer_compatibility(principal, wb.id, body)
        return self._wb_payload(wb, principal)

    def update_workbench(
        self, principal: Principal, workbench_id: str, **fields: Any
    ) -> dict[str, Any]:
        existing = self._require_workbench(workbench_id)
        if principal.kind is PrincipalKind.OWNER:
            from holdspeak.kernel.runtime import _configure
            _configure(self._db).inference_adoption_service.migrate_recipe_workbench_subject_assignments(principal)
        self._refuse_post_marker_pointer_write(principal, fields)
        proposed = self._wb_fields(fields, existing)
        bound_changed = any(proposed[key] != getattr(existing, key) for key in ("schedule", "schedule_enabled", "recipe_id", "profile_id"))
        enabling = not existing.schedule_enabled and proposed["schedule_enabled"]
        if enabling and principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("owner_principal_required", "Only the owner can enable a schedule", context={"status": 403})
        if bound_changed:
            proposed["schedule_revision"] = existing.schedule_revision + 1
        else:
            proposed["schedule_revision"] = existing.schedule_revision
        if not bound_changed:
            wb = self._db.workbenches.upsert(workbench_id=workbench_id, **proposed)
            self._write_legacy_pointer_compatibility(principal, wb.id, fields)
            return self._wb_payload(wb, principal)
        # Bound configuration and the authority it invalidates share one lock.
        # A provider is only signalled after the epoch fence has committed.
        from .schedule_delegation import ScheduleDelegationService
        service = ScheduleDelegationService(self._db)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            wb = self._db.workbenches.upsert_in_transaction(conn, workbench_id=workbench_id, **proposed)
            fenced = service.revoke_in_transaction(
                conn, workbench_id,
                "schedule_disabled" if not wb.schedule_enabled else "bound_terms_changed",
            )
            if enabling:
                service.enable_from_owner_in_transaction(principal, wb, conn)
        service.complete_fenced(fenced)
        self._write_legacy_pointer_compatibility(principal, wb.id, fields)
        return self._wb_payload(wb, principal)

    def delete_workbench(self, principal: Principal, workbench_id: str) -> bool:
        if self._db.workbench_items.has_active_items(workbench_id):
            raise ConflictError(
                "Cannot delete workbench with active items. Wait for running items to complete."
            )
        if not self._db.workbenches.delete(workbench_id):
            raise NotFound("workbench", workbench_id)
        return True

    # ── Items ────────────────────────────────────────────────────────────

    def get_item(self, principal: Principal, workbench_id: str, item_id: str) -> dict[str, Any]:
        return self._require_item(workbench_id, item_id).to_dict()

    def add_item(
        self, principal: Principal, workbench_id: str, *, title: str, **fields: Any
    ) -> dict[str, Any]:
        if not title.strip():
            raise ValidationError("Item title is required")
        self._require_workbench(workbench_id)
        item = self._db.workbench_items.upsert(
            item_id=str(fields.get("id") or _new_id("wbi")),
            workbench_id=workbench_id,
            title=title,
            body=str(fields.get("body", "")),
            priority=int(fields.get("priority", 3)),
            grounding=fields.get("grounding") or {},
            context=fields.get("context") or {},
        )
        return item.to_dict()

    def update_item(
        self, principal: Principal, workbench_id: str, item_id: str, **fields: Any
    ) -> dict[str, Any]:
        existing = self._require_item(workbench_id, item_id)

        def pick(key: str, default: Any) -> Any:
            return fields[key] if key in fields else default

        item = self._db.workbench_items.upsert(
            item_id=item_id,
            workbench_id=workbench_id,
            title=str(pick("title", existing.title)),
            body=str(pick("body", existing.body)),
            priority=int(pick("priority", existing.priority)),
            status=str(pick("status", existing.status)),
            grounding=pick("grounding", None),
            context=pick("context", None),
            result=pick("result", existing.result),
            result_egress=pick("result_egress", None),
            tokens_consumed=int(pick("tokens_consumed", existing.tokens_consumed)),
            claimed_at=pick("claimed_at", existing.claimed_at),
            completed_at=pick("completed_at", existing.completed_at),
        )
        return item.to_dict()

    def delete_item(self, principal: Principal, workbench_id: str, item_id: str) -> bool:
        item = self._require_item(workbench_id, item_id)
        if item.status == "claimed":
            raise ConflictError("Cannot delete a claimed item")
        if not self._db.workbench_items.delete(item_id):
            raise NotFound("item", item_id)
        return True

    def retry_mint(self, principal: Principal, workbench_id: str, item_id: str) -> dict[str, Any]:
        item = self._require_item(workbench_id, item_id)
        if item.status != "done" or not item.result:
            raise ValidationError("Item is not done or has no result")
        if item.result_artifact_id:
            return {"artifact_id": item.result_artifact_id, "created": False}

        wb = self._require_workbench(workbench_id)
        recipe = self._db.recipes.get(wb.recipe_id) if wb.recipe_id else None
        if recipe is None:
            raise ValidationError("No recipe assigned")
        # Retry is historical projection work: recover the completed item's
        # frozen route evidence instead of resolving today's placement.
        from types import SimpleNamespace
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT attempt.deployment_revision_id,attempt.boundary,plan.profile_id
                   FROM inference_route_attempts attempt
                   JOIN inference_route_executions execution ON execution.id=attempt.execution_id
                   JOIN inference_operation_route_request_plans operation ON operation.id=execution.operation_plan_id
                   JOIN inference_adoption_route_evidence evidence ON evidence.evidence_ref=operation.admission_evidence_ref
                   JOIN inference_adoption_material_snapshots material ON material.planning_reference=evidence.planning_reference
                   JOIN inference_route_plan_entries plan ON plan.plan_id=operation.route_plan_id
                    AND plan.route_leg_ordinal=attempt.route_leg_ordinal
                   JOIN kernel_operations child ON child.operation_id=attempt.child_operation_id
                  WHERE child.parent_operation_id IN (
                    SELECT parent_operation_id FROM workbench_runs WHERE workbench_id=?
                  )
                    AND json_extract(material.payload_json, '$.item_id')=?
                    AND json_extract(material.payload_json, '$.source_item_operation_id') IS NULL
                  ORDER BY attempt.terminal_at DESC LIMIT 1""",
                (workbench_id, item_id),
            ).fetchone()
        if row is None:
            raise ValidationError("No frozen route evidence found for this Workbench item")
        target = SimpleNamespace(boundary=str(row["boundary"]), model=str(row["profile_id"]).removeprefix("legacy-"))

        run_id = None
        with self._db._connection() as conn:
            existing = conn.execute(
                "SELECT source_run_id FROM artifacts WHERE source_item_id = ? LIMIT 1",
                (item_id,),
            ).fetchone()
            if existing and existing["source_run_id"]:
                run_id = existing["source_run_id"]
        if not run_id:
            runs = self._db.workbench_runs.list_for_workbench(workbench_id, limit=1)
            if not runs:
                raise ValidationError("No runs found for this workbench")
            run_id = runs[0].id

        from holdspeak.workbench_conductor import _auto_mint_artifact
        artifact_id = _auto_mint_artifact(
            db=self._db, item=item, recipe=recipe, workbench=wb,
            run_id=run_id, target=target, output=item.result,
        )
        if not artifact_id:
            raise ServiceError("artifact_persist_failed", "Mint failed")
        return {"artifact_id": artifact_id, "created": True}

    async def run(self, principal: Principal, workbench_id: str, *, memory_enabled: bool = True,
                  request_id: str | None = None,
                  source_event: dict[str, str] | None = None) -> dict[str, Any]:
        self._require_workbench(workbench_id)
        from holdspeak.workbench_conductor import run_workbench
        if request_id or source_event:
            from holdspeak.kernel.runtime import _service
            from holdspeak.services.workbench_runner import WorkbenchRunner
            return await WorkbenchRunner(self._db, _service()).run(
                principal, workbench_id, memory_enabled=memory_enabled,
                request_id=request_id, source_event=source_event,
            )
        return await run_workbench(workbench_id, principal, memory_enabled=memory_enabled)

    async def run_item(
        self,
        principal: Principal,
        workbench_id: str,
        item_id: str,
        *,
        memory_enabled: bool = True,
        request_id: str | None = None,
        source_event: dict[str, str] | None = None,
        deadline_seconds: float = 600,
    ) -> dict[str, Any]:
        """Admit exactly one causal Workbench item, never the pending batch."""
        self._require_item(workbench_id, item_id)
        from holdspeak.kernel.runtime import _service
        from holdspeak.services.workbench_runner import WorkbenchRunner

        return await WorkbenchRunner(self._db, _service()).run(
            principal,
            workbench_id,
            memory_enabled=memory_enabled,
            request_id=request_id,
            source_event=source_event,
            deadline_seconds=deadline_seconds,
            item_ids=[item_id],
        )

    def cancel_run(self, principal: Principal, parent_operation_id: str) -> str:
        """Cancel exactly the authenticated parent, never a Workbench lookup."""
        from holdspeak.kernel.runtime import _service
        return _service().parent_run_controller.cancel_by_operation_id(principal, parent_operation_id)

    def list_runs(self, principal: Principal, workbench_id: str) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._db.workbench_runs.list_for_workbench(workbench_id)]

    # ── Templates and skills ─────────────────────────────────────────────

    def list_templates(self, principal: Principal) -> list[dict[str, Any]]:
        from holdspeak.workbench_templates import list_templates
        return list_templates()

    def instantiate_template(
        self, principal: Principal, template_id: str, profile_id: str | None = None
    ) -> dict[str, Any]:
        from holdspeak.workbench_templates import get_template
        template = get_template(template_id)
        if template is None:
            raise NotFound("template", template_id)
        recipe_data = template["recipe"]
        recipe = self._db.recipes.upsert(
            recipe_id=_new_id("recipe"), name=recipe_data.get("name", "Agent"),
            role=recipe_data.get("role", ""), system_prompt=recipe_data.get("system_prompt", ""),
            user_template=recipe_data.get("user_template", ""), profile_id=profile_id or None,
        )
        wb_config = template.get("workbench", {})
        wb = self._db.workbenches.upsert(
            workbench_id=_new_id("workbench"), name=template["name"], recipe_id=recipe.id,
            profile_id=profile_id or None, schedule=wb_config.get("schedule"),
            # Instantiating a template is not recurring-inference approval.
            schedule_enabled=False,
        )
        for starter in template.get("starter_items", []):
            self._db.workbench_items.upsert(
                item_id=_new_id("wbi"), workbench_id=wb.id, title=starter.get("title", ""),
                body=starter.get("body", ""), priority=starter.get("priority", 3),
            )
        skill_names = template.get("skill_names", [])
        if skill_names:
            for skill in self._db.skills.list():
                if skill.title in skill_names:
                    recipe_ids = list(skill.to_dict().get("recipe_ids", []))
                    if recipe.id not in recipe_ids:
                        recipe_ids.append(recipe.id)
                        self._db.skills.upsert(
                            skill_id=skill.id, title=skill.title, body=skill.body,
                            source=skill.source, status=skill.status, recipe_ids=recipe_ids,
                            created_by=skill.created_by,
                        )
        # Template profile selection is a compatibility input until Story 13's
        # shared assignment glass exists. Once the one-way marker is present it
        # must update the same exact subject assignments as the legacy editors.
        if profile_id is not None:
            from .recipe_service import RecipeService
            RecipeService(self._db)._write_legacy_profile_compatibility(principal, recipe.id, profile_id)
            self._write_legacy_pointer_compatibility(principal, wb.id, {"profile_id": profile_id})
        return {"workbench": self._wb_payload(wb, principal), "recipe": recipe.to_dict()}

    def list_skills(
        self, principal: Principal, recipe_id: str | None = None
    ) -> list[dict[str, Any]]:
        skills = [skill.to_dict() for skill in self._db.skills.list()]
        if recipe_id is not None:
            skills = [skill for skill in skills if recipe_id in skill.get("recipe_ids", [])]
        return skills

    def create_skill(self, principal: Principal, *, title: str, body: str, **fields: Any) -> dict[str, Any]:
        if not title.strip():
            raise ValidationError("Skill title is required")
        if len(body) > SKILL_BODY_LIMIT:
            raise ValidationError(
                f"Skill body exceeds {SKILL_BODY_LIMIT:,} byte limit (got {len(body):,})"
            )
        skill = self._db.skills.upsert(
            skill_id=str(fields.get("id") or _new_id("skill")), title=title, body=body,
            source=str(fields.get("source", "owner-authored")),
            status=str(fields.get("status", "active")),
            recipe_ids=list(fields.get("recipe_ids", [])),
            created_by=str(fields.get("created_by", "")),
        )
        return skill.to_dict()

    def update_skill(self, principal: Principal, skill_id: str, **fields: Any) -> dict[str, Any]:
        existing = self._db.skills.get(skill_id)
        if existing is None:
            raise NotFound("skill", skill_id)

        def pick(key: str, default: Any) -> Any:
            return fields[key] if key in fields else default

        skill = self._db.skills.upsert(
            skill_id=skill_id, title=str(pick("title", existing.title)),
            body=str(pick("body", existing.body)), source=str(pick("source", existing.source)),
            status=str(pick("status", existing.status)),
            recipe_ids=list(pick("recipe_ids", existing.to_dict().get("recipe_ids", []))),
            created_by=str(pick("created_by", existing.created_by)),
        )
        return skill.to_dict()

    def delete_skill(self, principal: Principal, skill_id: str) -> bool:
        if not self._db.skills.delete(skill_id):
            raise NotFound("skill", skill_id)
        return True

    # ── Memory ───────────────────────────────────────────────────────────

    def list_memory(self, principal: Principal, workbench_id: str) -> list[dict[str, Any]]:
        from holdspeak.workbench_memory import read_memory
        return read_memory(workbench_id)

    def clear_memory(self, principal: Principal, workbench_id: str) -> bool:
        from holdspeak.workbench_memory import clear_memory
        clear_memory(workbench_id)
        return True

    def promote_memory(self, principal: Principal, workbench_id: str, index: int) -> dict[str, Any]:
        from holdspeak.workbench_memory import read_memory
        entries = read_memory(workbench_id)
        if index < 0 or index >= len(entries):
            raise ValidationError("Invalid memory index")
        wb = self._db.workbenches.get(workbench_id)
        if not wb or not wb.recipe_id:
            raise ValidationError("Workbench has no recipe")
        entry = entries[index]
        skill = self._db.skills.upsert(
            skill_id=_new_id("skill"), title=f"Learned: {entry.get('content', '')[:60]}",
            body=entry.get("content", ""), source="agent-proposed", status="draft",
            recipe_ids=[wb.recipe_id], created_by=f"memory:{workbench_id}",
        )
        return skill.to_dict()

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

    # ── Internal ─────────────────────────────────────────────────────────

    def _require_workbench(self, workbench_id: str) -> Any:
        wb = self._db.workbenches.get(workbench_id)
        if wb is None:
            raise NotFound("workbench", workbench_id)
        return wb

    def _require_item(self, workbench_id: str, item_id: str) -> Any:
        item = self._db.workbench_items.get(item_id)
        if item is None or item.workbench_id != workbench_id:
            raise NotFound("item", item_id)
        return item

    def _wb_payload(self, wb: Any, principal: Principal) -> dict[str, Any]:
        payload = wb.to_dict()
        items = self._db.workbench_items.list_for_workbench(wb.id)
        payload["items"] = [item.to_dict() for item in items]
        payload["item_count"] = len(items)
        payload["pending_count"] = sum(1 for item in items if item.status == "pending")
        runs = self._db.workbench_runs.list_for_workbench(wb.id, limit=1)
        payload["last_run"] = runs[0].to_dict() if runs else None
        if principal.kind is PrincipalKind.OWNER:
            from .inference_assignment_service import InferenceAssignmentService

            effective = InferenceAssignmentService(self._db).resolve_effective(
                principal,
                capability_id="workbench.item",
                subject_kind="workbench",
                subject_id=wb.id,
            )
            assignment = effective.get("assignment") or {}
            payload["assignment_summary"] = {
                "status": effective["status"],
                "source": effective.get("inherited_from"),
                "chain": [str(entry["label"]) for entry in assignment.get("entries", [])],
                "repair": effective.get("repair"),
            }
        return payload

    @staticmethod
    def _wb_fields(body: dict[str, Any], existing: Any = None) -> dict[str, Any]:
        def pick(key: str, default: Any) -> Any:
            return body[key] if key in body else default
        return {
            "name": str(pick("name", existing.name if existing else "")),
            "recipe_id": pick("recipe_id", existing.recipe_id if existing else None) or None,
            "profile_id": pick("profile_id", existing.profile_id if existing else None) or None,
            "resolver_profile_id": pick("resolver_profile_id", existing.resolver_profile_id if existing else None) or None,
            "schedule": pick("schedule", existing.schedule if existing else None) or None,
            "schedule_enabled": bool(pick("schedule_enabled", existing.schedule_enabled if existing else False)),
            "schedule_revision": int(pick("schedule_revision", existing.schedule_revision if existing else 1)),
            "item_order": list(pick("item_order", [])),
        }
