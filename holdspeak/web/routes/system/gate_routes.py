"""HTTP adapters for the tool-call gate."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....agent_capabilities import Capability, require_capability
from ....db.gate import APPROVED, DENIED, HELD
from ....logging_config import get_logger
from ....services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.gate")


def _error(exc: ServiceError) -> JSONResponse:
    if isinstance(exc, ValidationError):
        return JSONResponse({"error": exc.detail}, status_code=400)
    if isinstance(exc, NotFound):
        return JSONResponse({"error": "unknown_proposal"}, status_code=404)
    if isinstance(exc, ConflictError):
        if exc.code == "args_mismatch":
            return JSONResponse({"error": exc.code, **exc.context, "reason": exc.detail}, status_code=409)
        if exc.code == "already_decided":
            return JSONResponse({"error": exc.code, **exc.context}, status_code=409)
        return JSONResponse({"error": exc.code}, status_code=409)
    response = exc.context.get("response")
    if isinstance(response, dict):
        return JSONResponse(response, status_code=int(exc.context.get("status") or 400))
    payload = {"error": exc.code}
    if "operation_id" in exc.context:
        payload["operation_id"] = exc.context["operation_id"] or None
    return JSONResponse(payload, status_code=int(exc.context.get("status") or 400))


def build_gate_router(ctx: WebContext) -> APIRouter:
    service = ctx.gate_service
    if service is None:
        raise RuntimeError("GateService must be supplied at application composition")
    router = APIRouter()

    @router.post("/api/principals/agents")
    async def api_issue_agent_principal(request: Request) -> Any:
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse({"error": "body must be an object"}, status_code=400)
        identity = str(body.get("identity") or "").strip()
        if not identity:
            return JSONResponse({"error": "identity is required"}, status_code=400)
        credential = request.app.state.agent_credentials.issue(identity)
        return JSONResponse({"principal": credential.principal.name, "identity": credential.principal.identity, "credential": credential.token}, status_code=201)

    @router.delete("/api/principals/agents/{identity}")
    async def api_revoke_agent_principal(identity: str, request: Request) -> Any:
        return JSONResponse({"principal": "agent", "identity": identity, "revoked": request.app.state.agent_credentials.revoke(identity)})

    @router.delete("/api/principals/self")
    async def api_revoke_self(request: Request) -> Any:
        principal = request.state.principal
        return JSONResponse({"principal": principal.name, "identity": principal.identity, "revoked": request.app.state.agent_credentials.revoke(principal.identity)})

    @router.post("/api/gate/proposals")
    async def api_gate_propose(request: Request) -> Any:
        require_capability("claude-code-hooks", Capability.TOOL_HOOKS)
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse({"error": "body must be an object"}, status_code=400)
        try:
            return JSONResponse(service.propose(request.state.principal, body))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to propose gate operation")

    @router.get("/api/gate/proposals/{proposal_id}")
    async def api_gate_read(proposal_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service.get_proposal(request.state.principal, proposal_id))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read gate proposal")

    @router.get("/api/gate/proposals")
    async def api_gate_list(request: Request, state: str = HELD) -> Any:
        try:
            return JSONResponse(service.list_proposals(request.state.principal, {"state": state}))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to list gate proposals")

    @router.post("/api/gate/proposals/{proposal_id}/decide")
    async def api_gate_decide(proposal_id: str, request: Request) -> Any:
        require_capability("claude-code-hooks", Capability.BLOCKING)
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse({"error": "body must be an object"}, status_code=400)
        try:
            return JSONResponse(service.decide(request.state.principal, proposal_id, body))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to decide gate proposal")

    @router.post("/api/gate/proposals/{proposal_id}/receipt")
    async def api_gate_receipt(proposal_id: str, request: Request) -> Any:
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse({"error": "body must be an object"}, status_code=400)
        try:
            return JSONResponse(service.record_receipt(request.state.principal, proposal_id, body), status_code=202)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to record gate receipt")

    @router.post("/api/gate/usage")
    async def api_gate_usage(request: Request) -> Any:
        require_capability("claude-code-hooks", Capability.USAGE_TOKENS)
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse({"error": "body must be an object"}, status_code=400)
        try:
            return JSONResponse(service.record_usage(request.state.principal, body))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to record gate usage")

    @router.get("/api/sessions/{session_key}/receipt")
    async def api_session_receipt(session_key: str, request: Request) -> Any:
        try:
            return JSONResponse(service.get_session_receipt(request.state.principal, session_key))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read session receipt")

    @router.get("/api/gate/audit")
    async def api_gate_audit(request: Request, limit: int = 100) -> Any:
        try:
            return JSONResponse(service.audit(request.state.principal, {"limit": limit}))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read gate audit")

    @router.get("/api/gate/config")
    async def api_gate_config() -> Any:
        from ....coder_gate import load_gate_config
        return JSONResponse(load_gate_config().to_dict())

    return router


def invalidate_held_on_startup(service: Any) -> int:
    """Invalidate pre-restart held proposals and terminalize their kernel rows."""
    flipped, recovered = service.invalidate_held_on_startup()
    if flipped:
        log.info("gate: invalidated %s held proposal(s) on startup; kernel terminalized %s", len(flipped), recovered)
    return len(flipped)
