"""Thread HTTP routes (HS-151-04).

CRUD + turn + abort + branch + regenerate + keep + import.
No SSE — the bus is the one live channel (Art. I, one bus).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ... import db as hsdb
from ...principals import Principal, PrincipalKind
from ...services.errors import ServiceError, ValidationError
from ...services.thread_service import ThreadService, _UNSET
from ..context import WebContext
from ..runtime_support import error_500
from ...logging_config import get_logger

log = get_logger("web.routes.threads")


def _database() -> Any:
    return getattr(hsdb, "get_database")()


async def _json_body(request: Request) -> dict[str, Any] | None:
    try:
        body = await request.json()
        return body if isinstance(body, dict) else None
    except Exception:
        return None


def _normalize_refs(raw: Any) -> list[str] | None:
    """Accept refs as ``["kind:id", ...]`` OR ``[{ref_kind, ref_id}, ...]``.

    The composer sends the object shape; the CLI may send strings.  Normalize
    both to qualified ``"kind:id"`` strings for ``start_turn``.
    """
    if not isinstance(raw, list):
        return None
    result: list[str] = []
    for item in raw:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict) and item.get("ref_kind") and item.get("ref_id"):
            result.append(f"{item['ref_kind']}:{item['ref_id']}")
        elif isinstance(item, dict) and item.get("kind") and item.get("id"):
            result.append(f"{item['kind']}:{item['id']}")
    return result or None


def build_threads_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _principal(request: Request) -> Principal:
        return getattr(
            request.state,
            "principal",
            Principal(PrincipalKind.OWNER, "owner-session"),
        )

    def _service() -> ThreadService:
        # One factory shared with the recipe chat alias (HS-151-04).
        from ._thread_factory import thread_service_from_ctx
        return thread_service_from_ctx(ctx)

    def _error(exc: ServiceError) -> JSONResponse:
        payload = dict(exc.context)
        payload.setdefault("error", exc.detail)
        status = int(payload.pop("status", 400 if exc.code == "validation_error" else 409))
        return JSONResponse(payload, status_code=status)

    # ── Thread CRUD ─────────────────────────────────────────────────

    @router.post("/api/threads/{thread_id}/interview")
    async def api_interview_command(thread_id: str, request: Request) -> Any:
        from ...services.interview_service import InterviewService
        body = await _json_body(request)
        if body is None or set(body) != {"command_id", "expected_revision", "event"}:
            return JSONResponse({"error": "Expected command_id, expected_revision, and event"}, status_code=400)
        # The direct controls edit local interview state; domain execution still
        # goes through the existing conversation/tool and citizen services.
        event = body["event"]
        if not isinstance(event, dict) or event.get("kind") not in {"section", "remove_fact", "disposition", "status"}:
            return JSONResponse({"error": "Unsupported interview control"}, status_code=400)
        try:
            return JSONResponse(InterviewService(_service()._db).command(_principal(request), thread_id, **body))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/threads")
    async def api_create_thread(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = _service().create(
                title=str(body.get("title") or ""),
                recipe_id=str(body.get("recipe_id") or ""),
                seed_refs=body.get("seed_refs") if isinstance(body.get("seed_refs"), list) else None,
                profile_override=str(body.get("profile_override") or ""),
            )
            return JSONResponse(result, status_code=201)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to create thread")

    @router.get("/api/threads")
    async def api_list_threads(request: Request) -> Any:
        try:
            limit = int(request.query_params.get("limit", 100))
            ref_id = str(request.query_params.get("ref_id", ""))
            return JSONResponse({"threads": _service().list_threads(limit=limit, ref_id=ref_id)})
        except Exception as exc:
            return error_500(exc, log, "Failed to list threads")

    @router.get("/api/threads/{thread_id}")
    async def api_get_thread(thread_id: str, request: Request) -> Any:
        try:
            return JSONResponse(_service().get(thread_id))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get thread")

    @router.patch("/api/threads/{thread_id}")
    async def api_patch_thread(thread_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            # HS-153-03: toggle_guardrail toggles a guardrail on the thread's mode recipe.
            toggle_guardrail_id = body.get("toggle_guardrail")
            if toggle_guardrail_id:
                from holdspeak.services.thread_modes import toggle_guardrail_on_mode
                svc = _service()
                thread = svc._db.threads.get(thread_id)
                if thread and thread.recipe_id:
                    # S2 fix: read enable from body, default True for backward compat.
                    enable = body.get("toggle_guardrail_enable", True)
                    toggle_guardrail_on_mode(
                        svc._db, thread.recipe_id, str(toggle_guardrail_id), enable=bool(enable),
                    )
            # HS-154-03: call_mode toggle (0 or 1).
            raw_call_mode = body.get("call_mode")
            # S2: non-numeric call_mode -> 400, not 500.
            call_mode_val = None
            if raw_call_mode is not None:
                try:
                    call_mode_val = int(raw_call_mode)
                except (ValueError, TypeError):
                    return JSONResponse(
                        {"error": "invalid_call_mode", "detail": "call_mode must be an integer"},
                        status_code=400,
                    )
            result = _service().patch(
                thread_id,
                title=body.get("title"),
                profile_override=body.get("profile_override"),
                recipe_id=body.get("recipe_id"),
                call_mode=call_mode_val,
            )
            return JSONResponse(result)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc), "code": exc.code}, status_code=400)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to patch thread")

    @router.delete("/api/threads/{thread_id}")
    async def api_delete_thread(thread_id: str, request: Request) -> Any:
        try:
            deleted = _service().soft_delete(thread_id)
            if not deleted:
                return JSONResponse({"error": "thread_not_found"}, status_code=404)
            return JSONResponse({"deleted": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete thread")

    # ── Turn ────────────────────────────────────────────────────────

    @router.post("/api/threads/{thread_id}/turns")
    async def api_start_turn(thread_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = await _service().start_turn(
                _principal(request),
                thread_id,
                str(body.get("text") or ""),
                refs=_normalize_refs(body.get("refs")),
                parent_id=body.get("parent_id") if "parent_id" in body else _UNSET,
            )
            return JSONResponse(result, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc), "code": exc.code}, status_code=400)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to start turn")

    # ── Abort ───────────────────────────────────────────────────────

    @router.post("/api/threads/{thread_id}/abort")
    async def api_abort(thread_id: str, request: Request) -> Any:
        try:
            result = _service().abort(thread_id)
            return JSONResponse(result)
        except Exception as exc:
            return error_500(exc, log, "Failed to abort")

    # ── Branch ──────────────────────────────────────────────────────

    @router.post("/api/threads/{thread_id}/branch")
    async def api_branch(thread_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = await _service().branch(
                _principal(request),
                thread_id,
                str(body.get("message_id") or ""),
                str(body.get("text") or ""),
            )
            return JSONResponse(result, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc), "code": exc.code}, status_code=400)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to branch")

    # ── Regenerate ──────────────────────────────────────────────────

    @router.post("/api/threads/{thread_id}/regenerate")
    async def api_regenerate(thread_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = await _service().regenerate(
                _principal(request),
                thread_id,
                str(body.get("message_id") or ""),
            )
            return JSONResponse(result, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc), "code": exc.code}, status_code=400)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to regenerate")

    # ── Keep ────────────────────────────────────────────────────────

    @router.post("/api/threads/{thread_id}/keep")
    async def api_keep(thread_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = _service().keep(
                _principal(request),
                thread_id,
                str(body.get("message_id") or ""),
                as_kind=str(body.get("as") or "artifact"),
            )
            return JSONResponse(result, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc), "code": exc.code}, status_code=400)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to keep")

    # ── Import ──────────────────────────────────────────────────────

    @router.post("/api/threads/import")
    async def api_import_threads(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            payload = body.get("threads") if isinstance(body.get("threads"), list) else []
            result = _service().import_threads(payload)
            return JSONResponse({"imported": result})
        except Exception as exc:
            return error_500(exc, log, "Failed to import threads")

    # ── Tool decision (HS-152-02) ──────────────────────────────────

    @router.post("/api/threads/{thread_id}/decide")
    async def api_decide_tool(thread_id: str, request: Request) -> Any:
        """Resolve a held tool call: approve or deny, with optional answer."""
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        call_id = str(body.get("call_id") or "")
        decision = str(body.get("decision") or "")
        if not call_id or decision not in ("approve", "deny"):
            return JSONResponse(
                {"error": "call_id and decision (approve|deny) are required"},
                status_code=400,
            )
        answer = body.get("answer")
        always = bool(body.get("always", False))
        try:
            svc = _service()
            # The executor is wired by the loop builder (story 01);
            # this route resolves a pending decision through it.
            executor = getattr(svc, "_tool_executor", None)
            if executor is None:
                return JSONResponse(
                    {"error": "tool_executor_unavailable", "code": "tool_executor_unavailable"},
                    status_code=503,
                )
            handle = executor._handles.get(call_id)
            if handle is None or handle.thread_id != thread_id:
                return JSONResponse(
                    {"error": "tool_call_not_found", "code": "tool_call_not_found"},
                    status_code=404,
                )
            # HS-152-06 (close counsel S1): a decision lands once. A second
            # POST for a call that is no longer held is a conflict, not a
            # mutation of a dead handle.
            if handle.state != "awaiting_decision":
                return JSONResponse(
                    {"error": "tool_call_not_pending", "code": "tool_call_not_pending",
                     "state": handle.state},
                    status_code=409,
                )
            # HS-152-04: Allow-always writes an "allow" policy row BEFORE
            # deciding so that future calls to the same tool auto-admit.
            if always and decision == "approve":
                db = _database()
                db.threads.set_tool_policy(thread_id, handle.name, "allow")
            executor.decide(handle, decision, answer=answer)
            return JSONResponse({
                "call_id": call_id,
                "decision": decision,
                "always": always,
                "state": handle.state,
            })
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to decide tool call")

    # ── Annotations (HS-153-04) ────────────────────────────────────

    @router.post("/api/threads/{thread_id}/annotations")
    async def api_add_annotation(thread_id: str, request: Request) -> Any:
        """Add an owner annotation to the thread's draft message."""
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        message_id = str(body.get("message_id") or "")
        quote = str(body.get("quote") or "")
        comment = str(body.get("comment") or "")
        if not message_id or not quote:
            return JSONResponse(
                {"error": "message_id and quote are required"},
                status_code=400,
            )
        try:
            import json as _json
            db = _database()
            threads = db.threads

            # Validate the source message exists and belongs to this thread.
            source_msg = threads.get_message(message_id)
            if source_msg is None or source_msg.thread_id != thread_id:
                return JSONResponse(
                    {"error": "message_not_found"},
                    status_code=404,
                )

            # Check if the source part is sensitive (for the fence).
            source_parts = threads.get_parts(message_id)
            source_sensitive = any(p.sensitive for p in source_parts if p.kind == "text")

            # Get or create the draft message.
            draft_msg = threads.draft_message_for(thread_id)
            if draft_msg is None:
                # Auto-chain to the current leaf.
                path = threads.list_path(thread_id)
                parent_id = path[-1].id if path else None
                draft_msg = threads.append_message(
                    thread_id,
                    role="user",
                    parent_id=parent_id,
                )

            meta = {
                "source": "owner",
                "quote": quote,
                "comment": comment,
                "anchor_message_id": message_id,
            }
            part = threads.append_part(
                draft_msg.id,
                kind="annotation",
                text=f'The owner annotated: «{quote}» — {comment}',
                meta_json=_json.dumps(meta, separators=(",", ":"), sort_keys=True),
                sensitive=source_sensitive,
                draft=True,
            )
            return JSONResponse({
                "id": part.id,
                "kind": part.kind,
                "text": part.text,
                "ordinal": part.ordinal,
                "sensitive": part.sensitive,
                "draft": part.draft,
                "meta_json": meta,
            }, status_code=201)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to add annotation")

    # ── HS-153-05: compaction + todo ─────────────────────────────────

    @router.post("/api/threads/{thread_id}/compact")
    async def api_compact_thread(thread_id: str, request: Request) -> Any:
        try:
            result = await _service().compact_thread(_principal(request), thread_id)
            return result
        except (ServiceError, ValidationError) as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to compact thread")

    @router.post("/api/threads/{thread_id}/todo")
    async def api_todo(thread_id: str, request: Request) -> Any:
        body = await _json_body(request)
        text = str((body or {}).get("text", "")).strip()
        if not text:
            return JSONResponse(
                {"error": "todo_empty", "message": "Text is required"},
                status_code=400,
            )
        try:
            result = await _service().todo_from_thread(
                _principal(request), thread_id, text,
            )
            return result
        except (ServiceError, ValidationError) as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to add todo")

    @router.delete("/api/threads/{thread_id}/annotations/{part_id}")
    async def api_delete_annotation(thread_id: str, part_id: str, request: Request) -> Any:
        """Delete a draft annotation part."""
        try:
            db = _database()
            threads = db.threads
            # Verify the part belongs to this thread.
            parts = threads.draft_parts(thread_id)
            if not any(p.id == part_id for p in parts):
                return JSONResponse(
                    {"error": "annotation_not_found"},
                    status_code=404,
                )
            deleted = threads.delete_part(part_id)
            if not deleted:
                return JSONResponse(
                    {"error": "annotation_not_found"},
                    status_code=404,
                )
            return JSONResponse({"deleted": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete annotation")

    return router
