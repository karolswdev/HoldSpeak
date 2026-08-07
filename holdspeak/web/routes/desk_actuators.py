"""Desk actuator transport adapters."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ...principals import UNAUTHENTICATED
from ...services.errors import NotFound, ServiceError, ValidationError
from ...web_requests import _CompanionSlackRequest, _ProposalDecisionRequest
from ..context import WebContext
from ..runtime_support import error_500
from ...logging_config import get_logger
log = get_logger("web.routes.desk_actuators")


def _error(exc: ServiceError) -> JSONResponse:
    status = 404 if isinstance(exc, NotFound) else 400
    return JSONResponse({"success": False, "error": exc.detail, **exc.context}, status_code=status)


def build_desk_actuators_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(); service = ctx.actuator_service
    if service is None: raise RuntimeError("ActuatorProposalService is not composed")
    principal = lambda request: getattr(request.state, "principal", UNAUTHENTICATED)

    @router.get("/api/desk/actuators/status")
    async def api_desk_actuators_status() -> Any:
        config = service._config_provider().meeting
        return {"slack_configured": bool(config.slack_webhook_url), "webhook_configured": bool(config.companion_webhook_url), "github_configured": bool(config.companion_github_repo)}

    def proposal_route(method: Any):
        async def handler(request: Request, payload: _CompanionSlackRequest) -> Any:
            try: return JSONResponse(method(principal(request), payload))
            except ServiceError as exc: return _error(exc)
            except Exception as exc: return error_500(exc, log, "Failed to propose desk actuator")
        return handler

    def decision_route(method: Any):
        async def handler(proposal_id: str, request: Request, payload: _ProposalDecisionRequest) -> Any:
            try: return JSONResponse(method(principal(request), proposal_id, payload))
            except ServiceError as exc: return _error(exc)
            except Exception as exc: return error_500(exc, log, "Failed to decide desk actuator")
        return handler

    router.add_api_route("/api/desk/actuators/slack/propose", proposal_route(service.propose_slack), methods=["POST"])
    router.add_api_route("/api/desk/actuators/slack/{proposal_id}/decision", decision_route(service.decide_slack), methods=["POST"])
    router.add_api_route("/api/desk/actuators/webhook/propose", proposal_route(service.propose_webhook), methods=["POST"])
    router.add_api_route("/api/desk/actuators/webhook/{proposal_id}/decision", decision_route(service.decide_webhook), methods=["POST"])
    router.add_api_route("/api/desk/actuators/github/propose", proposal_route(service.propose_github), methods=["POST"])
    router.add_api_route("/api/desk/actuators/github/{proposal_id}/decision", decision_route(service.decide_github), methods=["POST"])
    return router
