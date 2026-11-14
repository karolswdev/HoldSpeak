"""HS-162-04: Project Update routes -- the verb wire.

GET  /api/projects/{id}/updates       -- list (lifecycle-filterable)
POST /api/projects/{id}/updates/draft -- draft (body {generator})
PUT  /api/updates/{id}                -- save the owner's edit (draft only)
POST /api/updates/{id}/regenerate     -- supersede + fresh draft
POST /api/updates/{id}/publish        -- lifecycle publish + project revision law
POST /api/updates/{id}/engine-pass    -- Betterment P1: improve a draft in the background
GET  /api/update-jobs/{id}            -- the engine pass, polled
POST /api/update-jobs/{id}/stop       -- stop it (its late answer is dropped)
POST /api/update-jobs/{id}/apply      -- save its draft (refused if the owner edited, unless force)
GET  /api/updates/{id}/markdown       -- the copyable artifact (text/markdown)

Parse-and-serialize ONLY; the service owns logic.
Owner-scoped; typed errors -> correct statuses.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.concurrency import run_in_threadpool

from ...db.updates import PublishedUpdateError
from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...project_operations import PROJECT_OPERATIONS, enrich_update
from ...services.errors import NotFound, ServiceError, ValidationError
from ..operation_routes import ContractRefusal, operation_router
from ._mount import mount_router
from ._produced import produced
from ..context import WebContext
from ..runtime_support import error_500
from ._room_kernel import body_or_refusal, kernel_fields, kernel_refusal, refusal_fields

log = get_logger("web.routes.project_updates")


_enrich_update = enrich_update


async def _answer(fn: Any, *, status: int = 200) -> Any:
    """The envelope of the produced update routes: the words these routes answered with."""
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ContractRefusal as exc:
        return JSONResponse({"success": False, "code": "validation", "message": exc.detail}, status_code=400)
    except PublishedUpdateError as exc:
        return JSONResponse({"success": False, "error_code": "published_update", "error": str(exc)}, status_code=409)
    except NotFound as exc:
        return JSONResponse({"success": False, "code": exc.code, "message": exc.detail}, status_code=404)
    except ValidationError as exc:
        status = 403 if exc.code == "claim_review_forbidden" else 400
        return JSONResponse({"success": False, "code": exc.code, "message": exc.detail}, status_code=status)
    except ServiceError as exc:
        return JSONResponse({"success": False, "code": exc.code, "message": exc.detail,
                             "reason": exc.context.get("reason"), "detail": exc.context.get("detail")},
                            status_code=int(exc.context.get("status") or 409))
    except Exception as exc:
        return error_500(exc, log, "Failed to run the update verb")


def _request_hash(payload: dict[str, Any]) -> str:
    """Deterministic hash for idempotency (mirrors project_service)."""
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def build_project_updates_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    if ctx.project_update_service is not None:
        ctx.project_update_service.bind_workbench(ctx.workbench_service)

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def ops() -> Any:
        """PHILO-9-01: the Room's declared operations, bound to the hub's services."""
        return operations.for_context(ctx)

    # 2026-11-09 (ops/projects): the update read, the regenerate, the claim
    # review and the engine pass are produced from their declared rows
    # (``project_operations.py``).
    mount_router(router, produced(ctx, [d for d in PROJECT_OPERATIONS if d.service == "project_update_service"],
                                  _answer, module=__name__))

    # ── GET /api/projects/{project_id}/updates ─────────────────────

    @router.get("/api/projects/{project_id}/updates")
    def api_list_updates(
        project_id: str, request: Request,
        lifecycle: str | None = None,
    ) -> Any:
        try:
            updates = ops().invoke(principal(request), "project.list_updates", {
                "project_id": project_id, "lifecycle": lifecycle,
            })
            enriched = [_enrich_update(u) for u in updates]
            # The null value is intentional when the lifecycle filter returns
            # no published rows, including a draft-only request.
            latest_published_update_id = next(
                (
                    update["id"]
                    for update in enriched
                    if update.get("lifecycle") == "published"
                ),
                None,
            )
            return JSONResponse({
                "updates": enriched,
                "latest_published_update_id": latest_published_update_id,
            })
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to list updates")

    # ── POST /api/projects/{project_id}/updates/draft ──────────────

    async def api_draft_update(
        project_id: str, payload: dict[str, Any], request: Request,
    ) -> Any:
        try:
            generator = str(payload.get("generator") or "deterministic").strip()
            cmd_id = payload.get("command_id")
            # P0 (betterment/projects): a model draft takes a minute or more.
            # It runs off the event loop, so every other window keeps working.
            result = await asyncio.to_thread(
                ops().invoke, principal(request), "project.draft_update", {
                    "project_id": project_id, "generator": generator, "command_id": cmd_id,
                    "strict_model_failure": True, "audience": str(payload.get("audience") or "manager"),
                },
            )
            return JSONResponse({"success": True, "update": _enrich_update(result)})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "code": "validation", "message": exc.detail}, status_code=400)
        except NotFound as exc:
            return JSONResponse(
                {"success": False, "code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ValidationError as exc:
            return JSONResponse(
                {"success": False, "code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except ServiceError as exc:
            return JSONResponse(
                {
                    "success": False,
                    "code": exc.code,
                    "message": exc.detail,
                    "reason": exc.context.get("reason"),
                    "detail": exc.context.get("detail"),
                },
                status_code=int(exc.context.get("status") or 409),
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to draft update")

    mount_router(router, operation_router(
        [operations.PROJECT_DRAFT_UPDATE], ops, _answer, module=__name__,
        hand_written={"project.draft_update": lambda d: api_draft_update}))

    # ── PUT /api/updates/{update_id} ───────────────────────────────

    @router.put("/api/updates/{update_id}")
    def api_save_update(
        update_id: str, payload: dict[str, Any], request: Request,
    ) -> Any:
        try:
            body_md = payload.get("body_md")
            cmd_id = payload.get("command_id")
            result = ops().invoke(principal(request), "project.update_draft", {
                "update_id": update_id, "body_md": body_md, "command_id": cmd_id,
                **({"claim_edits": payload["claim_edits"]} if "claim_edits" in payload else {}),
            })
            return JSONResponse({"success": True, "update": _enrich_update(result)})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "code": "validation", "message": exc.detail}, status_code=400)
        except PublishedUpdateError as exc:
            return JSONResponse(
                {"success": False, "error_code": "published_update",
                 "error": str(exc)},
                status_code=409,
            )
        except NotFound as exc:
            return JSONResponse(
                {"success": False, "code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ValidationError as exc:
            return JSONResponse(
                {"success": False, "code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except ServiceError as exc:
            return JSONResponse(
                {
                    "success": False,
                    "code": exc.code,
                    "message": exc.detail,
                    "reason": exc.context.get("reason"),
                    "detail": exc.context.get("detail"),
                },
                status_code=int(exc.context.get("status") or 409),
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to save update")

    # ── POST /api/updates/{update_id}/publish ──────────────────────

    @router.post("/api/updates/{update_id}/publish")
    async def api_publish_update(update_id: str, request: Request) -> Any:
        # PHILO-9-02: admitted (story 01's row, enforced): one operation, one
        # receipt; an agent is refused project_delegation_required with one.
        body, refused = await body_or_refusal(request, ops(), principal(request), "project.publish_update",
                                              optional=True)
        if refused is not None:
            return refused
        try:
            result, kernel = ops().invoke_receipted(principal(request), "project.publish_update", {
                "update_id": update_id, "command_id": body.get("command_id"),
            })
            return JSONResponse({"success": True, "update": _enrich_update(result), **kernel_fields(kernel)})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "code": "validation", "message": exc.detail,
                                 **refusal_fields(exc)}, status_code=400)
        except PublishedUpdateError as exc:
            return JSONResponse(
                {"success": False, "error_code": "published_update",
                 "error": str(exc), **refusal_fields(exc)},
                status_code=409,
            )
        except ServiceError as exc:
            if (refused := kernel_refusal(exc)) is not None:
                return refused
            status = 404 if isinstance(exc, NotFound) else int(exc.context.get("status") or 409)
            return JSONResponse({"success": False, "code": exc.code, "message": exc.detail,
                                 **refusal_fields(exc)}, status_code=status)
        except Exception as exc:
            return error_500(exc, log, "Failed to publish update")

    # ── POST /api/updates/{update_id}/delivered (PHILO-9-02; the Q0 ruling) ─

    @router.post("/api/updates/{update_id}/delivered")
    async def api_mark_update_delivered(update_id: str, request: Request) -> Any:
        """Mark it delivered: one admitted record per confirmation (R4-2).

        Body (optional): ``{delivered_to, command_id}``. The face mints ONE
        ``command_id`` per press of Mark delivered and keeps it across its
        retries; a repeat of that key answers the original record.
        """
        body, refused = await body_or_refusal(request, ops(), principal(request), "project.mark_update_delivered",
                                              optional=True)
        if refused is not None:
            return refused
        try:
            args = {"update_id": update_id, **{k: v for k, v in body.items()}}
            if "update_id" in body:
                raise OperationRefused("invalid_arguments", "project.mark_update_delivered",
                                       "Invalid arguments for project.mark_update_delivered: "
                                       "update_id comes from the path, not the body")
            result, kernel = ops().invoke_receipted(principal(request), "project.mark_update_delivered", args)
            return JSONResponse({**result, **kernel_fields(kernel)})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "code": "invalid_arguments", "message": exc.detail,
                                 **refusal_fields(exc)}, status_code=400)
        except ServiceError as exc:
            if (refused := kernel_refusal(exc)) is not None:
                return refused
            status = 404 if isinstance(exc, NotFound) else 400 if isinstance(exc, ValidationError) else 409
            return JSONResponse({"success": False, "code": exc.code, "message": exc.detail,
                                 **refusal_fields(exc)}, status_code=status)
        except Exception as exc:
            return error_500(exc, log, "Failed to mark the update delivered")

    # ── GET /api/updates/{update_id}/markdown ──────────────────────

    @router.get("/api/updates/{update_id}/markdown")
    def api_update_markdown(update_id: str, request: Request) -> Any:
        try:
            update = ops().invoke(principal(request), "project.update.get", {"update_id": update_id})["update"]
            from ...services.channel_contract import stored_claims, without_desk_marks

            return PlainTextResponse(
                without_desk_marks(update.get("body_md", ""), claims=stored_claims(update)),
                media_type="text/markdown",
            )
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to get update markdown")

    return router
