"""Transport-neutral Workbench operations (HS-122-02)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import hashlib
import time
import uuid
from typing import Any

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, NotFound, ServiceError, ValidationError


SKILL_BODY_LIMIT = 8192


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@observe_service
class WorkbenchService:
    # Route adapters create a short-lived service per request; limiter state is shared.
    _resolve_timestamps: dict[str, float] = {}

    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    # ── Workbenches ──────────────────────────────────────────────────────

    def list_workbenches(self, principal: Principal) -> list[dict[str, Any]]:
        return [self._wb_payload(wb) for wb in self._db.workbenches.list()]

    def get_workbench(self, principal: Principal, workbench_id: str) -> dict[str, Any]:
        wb = self._require_workbench(workbench_id)
        return self._wb_payload(wb)

    def create_workbench(self, principal: Principal, *, name: str, **fields: Any) -> dict[str, Any]:
        if not name.strip():
            raise ValidationError("Workbench name is required")
        body = {"name": name, **fields}
        fields = self._wb_fields(body)
        if fields["schedule_enabled"] and principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("owner_principal_required", "Only the owner can enable a schedule", context={"status": 403})
        workbench_id = str(body.pop("id", "") or _new_id("workbench"))
        if not fields["schedule_enabled"]:
            wb = self._db.workbenches.upsert(workbench_id=workbench_id, **fields)
            return self._wb_payload(wb)
        # The owner's single enable gesture commits its configuration, captured
        # deployment revision, and local delegation as one crash-consistent unit.
        from .schedule_delegation import ScheduleDelegationService
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            wb = self._db.workbenches.upsert_in_transaction(conn, workbench_id=workbench_id, **fields)
            ScheduleDelegationService(self._db).enable_from_owner_in_transaction(principal, wb, conn)
        return self._wb_payload(wb)

    def update_workbench(
        self, principal: Principal, workbench_id: str, **fields: Any
    ) -> dict[str, Any]:
        existing = self._require_workbench(workbench_id)
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
            return self._wb_payload(wb)
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
        return self._wb_payload(wb)

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
        from holdspeak.inference_targets import resolve_placement
        # One placement authority (HS-130-01): Workbench override → Agent
        # default (recipe.profile_id) → named global default. Retry inherits
        # the same precedence the run used; no invocation override here.
        target = resolve_placement(
            self._db, workbench=wb.profile_id, agent=recipe.profile_id
        ).target

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

    async def run(self, principal: Principal, workbench_id: str, *, memory_enabled: bool = True) -> dict[str, Any]:
        self._require_workbench(workbench_id)
        from holdspeak.workbench_conductor import run_workbench
        return await run_workbench(workbench_id, principal, memory_enabled=memory_enabled)

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
        return {"workbench": self._wb_payload(wb), "recipe": recipe.to_dict()}

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
        wb = self._require_workbench(workbench_id)
        if not wb.resolver_profile_id:
            raise ServiceError("resolver_not_configured", "No resolver profile set on this workbench", context={"error": "resolver_not_configured", "detail": "No resolver profile set on this workbench"})
        from holdspeak.inference_targets import resolve_placement
        target = resolve_placement(self._db, invocation=wb.resolver_profile_id).target
        if not target.ready:
            raise ServiceError("resolver_unavailable", target.readiness_reason, context={"error": "resolver_unavailable", "detail": target.readiness_reason})
        from holdspeak.voice_resolver import ZoneCatalogEntry, resolve_voice_references
        zones = [
            ZoneCatalogEntry(id=z.id, name=z.name, items=0)
            for z in self._db.directories.list() if not getattr(z, "deleted", False)
        ]
        egress = {"boundary": target.boundary, "model": target.model}
        if not zones:
            return {"refs": [], "egress": egress, "request_id": request_id}

        if principal is None or principal.kind is PrincipalKind.NONE:
            raise ServiceError("resolver_principal_required", "Authenticated principal required", context={"error": "resolver_principal_required"})
        from holdspeak.deployment_revisions import capture_deployment_revision
        from holdspeak.kernel.inference_runner import InvocationRequest, ServiceContract
        from holdspeak.kernel.model import KernelRefused
        from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter
        from holdspeak.kernel.runtime import _as_principal, _service
        broker = _service() if getattr(self, "_kernel", None) is None else self._kernel
        revision = capture_deployment_revision(self._db, target)
        try:
            parent = broker.parent_run_controller.start(principal, kind="voice_reference_resolve", definition_ref=f"workbench:{workbench_id}", definition_revision=str(getattr(wb, "last_modified", "1")), input_snapshot={"workbench_id": workbench_id, "profile_id": wb.resolver_profile_id, "transcript_hash": hashlib.sha256(text.encode()).hexdigest()}, deadline_at=time.time() + 30, child_budget=3, idempotency_key=request_id or None)
        except KernelRefused as exc:
            raise ServiceError("resolver_refused", exc.reason, context={"error": "resolver_refused", "detail": exc.reason}) from exc
        attempts = 0
        def run_prompt_fn(*, prompt: str, profile_id: str, max_tokens: int, timeout: float) -> str:
            nonlocal attempts
            parent_receipt = broker.store.receipt(parent.operation_id)
            if parent_receipt is not None and parent_receipt["outcome"] in {"cancelled", "indeterminate"}:
                raise TimeoutError("voice_resolver_parent_deadline_cancelled")
            attempts += 1
            payload = {"system_prompt": "", "user_prompt": prompt, "temperature": 0.1, "max_tokens": max_tokens, "transcript_hash": hashlib.sha256(text.encode()).hexdigest(), "catalog_hash": hashlib.sha256("|".join(f"{z.id}:{z.name}" for z in zones).encode()).hexdigest(), "selected_target": profile_id, "timeout": timeout, "retry_index": attempts}
            request = InvocationRequest(revision.id, ServiceContract.for_payload("holdspeak.voice-reference-resolve", "1", payload), time.time() + timeout, payload, "voice_" + uuid.uuid4().hex, parent.operation_id, attempts)
            with _as_principal(principal):
                outcome = broker.inference_runner.invoke(request, CanonicalPromptAdapter(), parent_context=parent.context, publish=broker.projection_stager.publisher(request.invocation_id, "voice-resolver-attempt", lambda output: {"output": str(dict(output).get("output") or "")}))
            if outcome.outcome == "succeeded":
                projection = broker.projection_stager.finalize(request.invocation_id)
                if projection is None: raise RuntimeError("voice_resolution_projection_not_published")
                return str(projection["output"])
            if outcome.outcome == "cancelled":
                raise TimeoutError("voice_resolver_deadline_cancelled")
            raise RuntimeError(f"voice_resolver_{outcome.outcome}")
        result = resolve_voice_references(zones=zones, transcript=text, run_prompt_fn=run_prompt_fn, profile_id=wb.resolver_profile_id, request_id=request_id)
        outcome = "succeeded" if result.terminal_state == "success" else ("cancelled" if result.terminal_state == "timeout" else "failed")
        parent_receipt = broker.store.receipt(parent.operation_id)
        if parent_receipt is None:
            parent_receipt = broker.parent_run_controller.close(parent.context, outcome, f"workbench:{workbench_id}", principal=principal)
        if parent_receipt["outcome"] in {"cancelled", "indeterminate"}:
            return {"refs": [], "error": "resolver_cancelled", "egress": egress,
                    "request_id": request_id, "attempts": result.attempts}
        if result.terminal_state == "timeout":
            return {"refs": [], "error": "resolver_timeout", "egress": egress,
                    "request_id": request_id, "attempts": result.attempts}
        if result.terminal_state in ("parse_failure", "error"):
            return {"refs": [], "error": f"resolver_{result.terminal_state}", "egress": egress,
                    "request_id": request_id, "attempts": result.attempts}
        return {"refs": [{"name": r.name, "id": r.id, "ref": r.ref, "kind": r.kind} for r in result.refs],
                "egress": egress, "request_id": request_id, "attempts": result.attempts}

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

    def _wb_payload(self, wb: Any) -> dict[str, Any]:
        payload = wb.to_dict()
        items = self._db.workbench_items.list_for_workbench(wb.id)
        payload["items"] = [item.to_dict() for item in items]
        payload["item_count"] = len(items)
        payload["pending_count"] = sum(1 for item in items if item.status == "pending")
        runs = self._db.workbench_runs.list_for_workbench(wb.id, limit=1)
        payload["last_run"] = runs[0].to_dict() if runs else None
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
