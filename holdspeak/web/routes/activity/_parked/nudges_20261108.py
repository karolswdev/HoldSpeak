"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/activity/nudges.py``: POST /api/activity/nudges/select/clear.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""HTTP adapters for activity nudge operations."""
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .....db import get_database, get_observer
from .....principals import UNAUTHENTICATED
from .....services.activity_nudge_service import ActivityNudgeService
from ....context import WebContext
from ....runtime_support import error_500
from .....logging_config import get_logger
log=get_logger("web.routes.activity.nudges")
def _svc()->ActivityNudgeService:return ActivityNudgeService(get_database(), observer=get_observer())
def _principal(r:Request):return getattr(r.state,"principal",UNAUTHENTICATED)
def parked_build_nudges_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 @router.post("/api/activity/nudges/select/clear")
 def clear()->Any:
  try:
   from .....dictation_selection import clear_selected_record
   clear_selected_record();return JSONResponse({"cleared":True})
  except Exception as e:return error_500(e,log,"Failed to clear activity selection")
 return router
