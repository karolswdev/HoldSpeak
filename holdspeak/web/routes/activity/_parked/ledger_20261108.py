"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/activity/ledger.py``: POST /api/activity/domains, DELETE /api/activity/domains/{domain}.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""HTTP adapters for the transport-neutral activity ledger service."""
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .....db import get_database, get_observer
from .....principals import UNAUTHENTICATED
from .....services.activity_ledger_service import ActivityLedgerService
from .....services.errors import ValidationError
from .....web_requests import _ActivityDomainRuleRequest
from ....context import WebContext
from ....runtime_support import error_500
from .....logging_config import get_logger
log = get_logger("web.routes.activity")
def _principal(request: Request): return getattr(request.state, "principal", UNAUTHENTICATED)
def _svc() -> ActivityLedgerService: return ActivityLedgerService(get_database(), observer=get_observer())
def parked_build_ledger_router(ctx: WebContext) -> APIRouter:
 router=APIRouter()
 @router.post("/api/activity/domains")
 def domain(request:Request,payload:_ActivityDomainRuleRequest)->Any:
  try:return JSONResponse(_svc().upsert_domain_rule(_principal(request),payload.domain,payload.action))
  except ValidationError as e:return JSONResponse({"error":str(e)},status_code=400)
  except Exception as e:return error_500(e,log,"Failed to update activity domain rule")
 @router.delete("/api/activity/domains/{domain}")
 def delete_domain(request:Request,domain:str)->Any:
  try:return JSONResponse(_svc().delete_domain_rule(_principal(request),domain))
  except Exception as e:return error_500(e,log,"Failed to delete activity domain rule")
 return router
