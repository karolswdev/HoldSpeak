"""Workbenches: CRUD for the Workbench primitive (HS-116-01).

A Workbench is a DeskPrimitive — one agent, one inference target, one schedule,
N items. The agent works through items and produces receipts.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body, _new_id

log = get_logger("web.routes.workbenches")


def build_workbenches_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _wb_payload(wb: Any) -> dict[str, Any]:
        d = wb.to_dict()
        from ....db import get_database
        db = get_database()
        items = db.workbench_items.list_for_workbench(wb.id)
        d["items"] = [it.to_dict() for it in items]
        d["item_count"] = len(items)
        d["pending_count"] = sum(1 for it in items if it.status == "pending")
        runs = db.workbench_runs.list_for_workbench(wb.id, limit=1)
        d["last_run"] = runs[0].to_dict() if runs else None
        return d

    def _wb_fields(body: dict[str, Any], existing=None) -> dict[str, Any]:
        def pick(key: str, default: Any) -> Any:
            return body[key] if key in body else default
        return {
            "name": str(pick("name", existing.name if existing else "")),
            "recipe_id": (pick("recipe_id", existing.recipe_id if existing else None) or None),
            "profile_id": (pick("profile_id", existing.profile_id if existing else None) or None),
            "schedule": (pick("schedule", existing.schedule if existing else None) or None),
            "schedule_enabled": bool(pick("schedule_enabled", existing.schedule_enabled if existing else False)),
            "item_order": list(pick("item_order", [])),
        }

    # ── Workbench CRUD ──────────────────────────────────────────────────────

    @router.get("/api/workbenches")
    async def api_list_workbenches() -> Any:
        try:
            from ....db import get_database
            wbs = get_database().workbenches.list()
            return JSONResponse({"workbenches": [_wb_payload(wb) for wb in wbs]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list workbenches")

    @router.post("/api/workbenches")
    async def api_create_workbench(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "Workbench name is required"}, status_code=400)
        try:
            from ....db import get_database
            wb = get_database().workbenches.upsert(
                workbench_id=str(body.get("id") or _new_id("workbench")),
                **_wb_fields(body),
            )
            return JSONResponse({"workbench": _wb_payload(wb)}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create workbench")

    @router.get("/api/workbenches/{workbench_id}")
    async def api_get_workbench(workbench_id: str) -> Any:
        try:
            from ....db import get_database
            wb = get_database().workbenches.get(workbench_id)
            if wb is None:
                return JSONResponse({"error": f"Unknown workbench: {workbench_id}"}, status_code=404)
            return JSONResponse({"workbench": _wb_payload(wb)})
        except Exception as exc:
            return error_500(exc, log, "Failed to get workbench")

    @router.put("/api/workbenches/{workbench_id}")
    async def api_update_workbench(workbench_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            existing = db.workbenches.get(workbench_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown workbench: {workbench_id}"}, status_code=404)
            wb = db.workbenches.upsert(workbench_id=workbench_id, **_wb_fields(body, existing))
            return JSONResponse({"workbench": _wb_payload(wb)})
        except Exception as exc:
            return error_500(exc, log, "Failed to update workbench")

    @router.delete("/api/workbenches/{workbench_id}")
    async def api_delete_workbench(workbench_id: str) -> Any:
        try:
            from ....db import get_database
            db = get_database()
            if db.workbench_items.has_active_items(workbench_id):
                return JSONResponse(
                    {"error": "Cannot delete workbench with active items. Wait for running items to complete."},
                    status_code=409,
                )
            removed = db.workbenches.delete(workbench_id)
            if not removed:
                return JSONResponse({"error": f"Unknown workbench: {workbench_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete workbench")

    # ── Item CRUD ───────────────────────────────────────────────────────────

    @router.post("/api/workbenches/{workbench_id}/items")
    async def api_add_item(workbench_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("title") or "").strip():
            return JSONResponse({"error": "Item title is required"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            wb = db.workbenches.get(workbench_id)
            if wb is None:
                return JSONResponse({"error": f"Unknown workbench: {workbench_id}"}, status_code=404)
            item = db.workbench_items.upsert(
                item_id=str(body.get("id") or _new_id("wbi")),
                workbench_id=workbench_id,
                title=str(body.get("title", "")),
                body=str(body.get("body", "")),
                priority=int(body.get("priority", 3)),
                grounding=body.get("grounding") or {},
                context=body.get("context") or {},
            )
            return JSONResponse({"item": item.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to add item")

    @router.put("/api/workbenches/{workbench_id}/items/{item_id}")
    async def api_update_item(workbench_id: str, item_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            existing = db.workbench_items.get(item_id)
            if existing is None or existing.workbench_id != workbench_id:
                return JSONResponse({"error": f"Unknown item: {item_id}"}, status_code=404)

            def pick(key: str, default: Any) -> Any:
                return body[key] if key in body else default

            item = db.workbench_items.upsert(
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
            return JSONResponse({"item": item.to_dict()})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update item")

    @router.delete("/api/workbenches/{workbench_id}/items/{item_id}")
    async def api_delete_item(workbench_id: str, item_id: str) -> Any:
        try:
            from ....db import get_database
            db = get_database()
            existing = db.workbench_items.get(item_id)
            if existing is None or existing.workbench_id != workbench_id:
                return JSONResponse({"error": f"Unknown item: {item_id}"}, status_code=404)
            if existing.status == "claimed":
                return JSONResponse({"error": "Cannot delete a claimed item"}, status_code=409)
            removed = db.workbench_items.delete(item_id)
            if not removed:
                return JSONResponse({"error": f"Unknown item: {item_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete item")

    # ── Retry mint (HS-118-06) ─────────────────────────────────────────────

    @router.post("/api/workbenches/{workbench_id}/items/{item_id}/retry-mint")
    async def api_retry_mint(workbench_id: str, item_id: str) -> Any:
        """Re-attempt the kernel-admitted auto-mint for a completed item."""
        try:
            from ....db import get_database
            db = get_database()
            item = db.workbench_items.get(item_id)
            if item is None or item.workbench_id != workbench_id:
                return JSONResponse({"error": f"Unknown item: {item_id}"}, status_code=404)
            if item.status != "done" or not item.result:
                return JSONResponse({"error": "Item is not done or has no result"}, status_code=400)
            if item.result_artifact_id:
                return JSONResponse({"artifact_id": item.result_artifact_id})

            wb = db.workbenches.get(workbench_id)
            if wb is None:
                return JSONResponse({"error": f"Unknown workbench: {workbench_id}"}, status_code=404)
            recipe = db.recipes.get(wb.recipe_id) if wb.recipe_id else None
            if recipe is None:
                return JSONResponse({"error": "No recipe assigned"}, status_code=400)

            from ....inference_targets import resolve_inference_target
            target = resolve_inference_target(db, wb.profile_id or "this_machine")

            # Issue 3 fix: use the item's original run_id, not the most recent run.
            # Look for an existing artifact with this item_id to get source_run_id,
            # or fall back to the item's completed_at-correlated run, then most recent.
            run_id = None
            with db._connection() as conn:
                existing = conn.execute(
                    "SELECT source_run_id FROM artifacts WHERE source_item_id = ? LIMIT 1",
                    (item_id,),
                ).fetchone()
                if existing and existing["source_run_id"]:
                    run_id = existing["source_run_id"]
            if not run_id:
                runs = db.workbench_runs.list_for_workbench(workbench_id, limit=1)
                if not runs:
                    return JSONResponse({"error": "No runs found for this workbench"}, status_code=400)
                run_id = runs[0].id

            from ....workbench_conductor import _auto_mint_artifact
            artifact_id = _auto_mint_artifact(
                db=db, item=item, recipe=recipe, workbench=wb,
                run_id=run_id, target=target, output=item.result,
            )
            if artifact_id:
                return JSONResponse({"artifact_id": artifact_id}, status_code=201)
            return JSONResponse({"error": "Mint failed"}, status_code=500)
        except Exception as exc:
            return error_500(exc, log, "Failed to retry mint")

    # ── Run (manual trigger) ───────────────────────────────────────────────

    @router.post("/api/workbenches/{workbench_id}/run")
    async def api_run_workbench(workbench_id: str) -> Any:
        try:
            from ....db import get_database
            db = get_database()
            wb = db.workbenches.get(workbench_id)
            if wb is None:
                return JSONResponse({"error": f"Unknown workbench: {workbench_id}"}, status_code=404)
            from ....workbench_conductor import run_workbench
            result = await run_workbench(workbench_id)
            return JSONResponse({"run": result})
        except Exception as exc:
            return error_500(exc, log, "Failed to run workbench")

    # ── Run history ─────────────────────────────────────────────────────────

    @router.get("/api/workbenches/{workbench_id}/runs")
    async def api_list_runs(workbench_id: str) -> Any:
        try:
            from ....db import get_database
            runs = get_database().workbench_runs.list_for_workbench(workbench_id)
            return JSONResponse({"runs": [r.to_dict() for r in runs]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list runs")

    # ── Templates ───────────────────────────────────────────────────────────

    @router.get("/api/workbench-templates")
    async def api_list_templates() -> Any:
        from ....workbench_templates import list_templates
        return JSONResponse({"templates": list_templates()})

    # ── Skills ───────────────────────────────────────────────────────────

    @router.get("/api/skills")
    async def api_list_skills() -> Any:
        try:
            from ....db import get_database
            skills = get_database().skills.list()
            return JSONResponse({"skills": [s.to_dict() for s in skills]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list skills")

    SKILL_BODY_LIMIT = 8192

    @router.post("/api/skills")
    async def api_create_skill(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("title") or "").strip():
            return JSONResponse({"error": "Skill title is required"}, status_code=400)
        skill_body = str(body.get("body", ""))
        if len(skill_body) > SKILL_BODY_LIMIT:
            return JSONResponse(
                {"error": f"Skill body exceeds {SKILL_BODY_LIMIT:,} byte limit (got {len(skill_body):,})"},
                status_code=400,
            )
        try:
            from ....db import get_database
            skill = get_database().skills.upsert(
                skill_id=str(body.get("id") or _new_id("skill")),
                title=str(body.get("title", "")),
                body=str(body.get("body", "")),
                source=str(body.get("source", "owner-authored")),
                status=str(body.get("status", "active")),
                recipe_ids=list(body.get("recipe_ids", [])),
                created_by=str(body.get("created_by", "")),
            )
            return JSONResponse({"skill": skill.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create skill")

    @router.put("/api/skills/{skill_id}")
    async def api_update_skill(skill_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            existing = db.skills.get(skill_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown skill: {skill_id}"}, status_code=404)
            def pick(key: str, default: Any) -> Any:
                return body[key] if key in body else default
            skill = db.skills.upsert(
                skill_id=skill_id,
                title=str(pick("title", existing.title)),
                body=str(pick("body", existing.body)),
                source=str(pick("source", existing.source)),
                status=str(pick("status", existing.status)),
                recipe_ids=list(pick("recipe_ids", existing.to_dict().get("recipe_ids", []))),
                created_by=str(pick("created_by", existing.created_by)),
            )
            return JSONResponse({"skill": skill.to_dict()})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update skill")

    @router.delete("/api/skills/{skill_id}")
    async def api_delete_skill(skill_id: str) -> Any:
        try:
            from ....db import get_database
            removed = get_database().skills.delete(skill_id)
            if not removed:
                return JSONResponse({"error": f"Unknown skill: {skill_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete skill")

    # ── Templates ───────────────────────────────────────────────────────────

    @router.post("/api/workbench-templates/{template_id}/instantiate")
    async def api_instantiate_template(template_id: str, request: Request) -> Any:
        body = await _json_body(request) or {}
        from ....workbench_templates import get_template
        template = get_template(template_id)
        if template is None:
            return JSONResponse({"error": f"Unknown template: {template_id}"}, status_code=404)
        try:
            from ....db import get_database
            db = get_database()
            recipe_data = template["recipe"]
            recipe = db.recipes.upsert(
                recipe_id=_new_id("recipe"),
                name=recipe_data.get("name", "Agent"),
                role=recipe_data.get("role", ""),
                system_prompt=recipe_data.get("system_prompt", ""),
                user_template=recipe_data.get("user_template", ""),
                profile_id=body.get("profile_id") or None,
            )
            wb_config = template.get("workbench", {})
            wb = db.workbenches.upsert(
                workbench_id=_new_id("workbench"),
                name=template["name"],
                recipe_id=recipe.id,
                profile_id=body.get("profile_id") or None,
                schedule=wb_config.get("schedule"),
                schedule_enabled=bool(wb_config.get("schedule")),
            )
            for starter in template.get("starter_items", []):
                db.workbench_items.upsert(
                    item_id=_new_id("wbi"),
                    workbench_id=wb.id,
                    title=starter.get("title", ""),
                    body=starter.get("body", ""),
                    priority=starter.get("priority", 3),
                )
            # Bind template skills to the recipe
            skill_names = template.get("skill_names", [])
            if skill_names:
                all_skills = db.skills.list()
                for skill in all_skills:
                    if skill.title in skill_names:
                        existing_ids = list(skill.to_dict().get("recipe_ids", []))
                        if recipe.id not in existing_ids:
                            existing_ids.append(recipe.id)
                            db.skills.upsert(
                                skill_id=skill.id,
                                title=skill.title,
                                body=skill.body,
                                source=skill.source,
                                status=skill.status,
                                recipe_ids=existing_ids,
                                created_by=skill.created_by,
                            )
            return JSONResponse({"workbench": _wb_payload(wb), "recipe": recipe.to_dict()}, status_code=201)
        except Exception as exc:
            return error_500(exc, log, "Failed to instantiate template")

    # ── Memory (HS-116-16) ────────────────────────────────────────────────

    @router.get("/api/workbenches/{workbench_id}/memory")
    async def api_list_memory(workbench_id: str) -> Any:
        try:
            from ....workbench_memory import read_memory
            entries = read_memory(workbench_id)
            return JSONResponse({"entries": entries})
        except Exception as exc:
            return error_500(exc, log, "Failed to read memory")

    @router.delete("/api/workbenches/{workbench_id}/memory")
    async def api_clear_memory(workbench_id: str) -> Any:
        try:
            from ....workbench_memory import clear_memory
            clear_memory(workbench_id)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to clear memory")

    @router.post("/api/workbenches/{workbench_id}/memory/{index}/promote")
    async def api_promote_memory(workbench_id: str, index: int, request: Request) -> Any:
        try:
            from ....workbench_memory import read_memory
            from ....db import get_database
            entries = read_memory(workbench_id)
            if index < 0 or index >= len(entries):
                return JSONResponse({"error": "Invalid memory index"}, status_code=400)
            entry = entries[index]
            db = get_database()
            wb = db.workbenches.get(workbench_id)
            if not wb or not wb.recipe_id:
                return JSONResponse({"error": "Workbench has no recipe"}, status_code=400)
            skill = db.skills.upsert(
                skill_id=_new_id("skill"),
                title=f"Learned: {entry.get('content', '')[:60]}",
                body=entry.get("content", ""),
                source="agent-proposed",
                status="draft",
                recipe_ids=[wb.recipe_id],
                created_by=f"memory:{workbench_id}",
            )
            return JSONResponse({"skill": skill.to_dict()}, status_code=201)
        except Exception as exc:
            return error_500(exc, log, "Failed to promote memory to skill")

    return router
