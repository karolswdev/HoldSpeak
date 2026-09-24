"""Monday Brief read and generation transport adapters.

HS-150-03: person_sections is composed at the adapter layer AFTER the
observed service returns -- the MondayBrief dataclass NEVER carries it.
"""
from __future__ import annotations

import datetime
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request

from ... import operations
from ...db import get_database, get_observer
from ...principals import UNAUTHENTICATED
from ...services.monday_brief_service import MondayBriefService
from ...services.person_overlay import compose_person_overlay
from ..context import WebContext


_MONTHS = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
]


def _period_label(brief_dict: dict[str, Any]) -> str | None:
    generated_at = brief_dict.get("generated_at", "")
    if not generated_at:
        return None
    try:
        gen_dt = datetime.datetime.fromisoformat(
            str(generated_at).replace("Z", "+00:00")
        )
        days_since_monday = gen_dt.weekday()
        monday = gen_dt - datetime.timedelta(days=days_since_monday)
        mon_month = _MONTHS[monday.month - 1]
        gen_month = _MONTHS[gen_dt.month - 1]
        if monday.month == gen_dt.month:
            return f"{mon_month} {monday.day:02d} – {gen_dt.day:02d}"
        return f"{mon_month} {monday.day:02d} – {gen_month} {gen_dt.day:02d}"
    except (ValueError, TypeError):
        return None


def _generated_label(brief_dict: dict[str, Any]) -> str | None:
    generated_at = brief_dict.get("generated_at", "")
    if not generated_at:
        return None
    try:
        dt = datetime.datetime.fromisoformat(
            str(generated_at).replace("Z", "+00:00")
        )
        month = _MONTHS[dt.month - 1]
        return f"GENERATED {month} {dt.day:02d} {dt.hour:02d}:{dt.minute:02d}"
    except (ValueError, TypeError):
        return None


def _compose_overlay(brief_dict: dict[str, Any], service: MondayBriefService, request: Request) -> dict[str, Any]:
    """Merge person_sections into the response dict (never into the dataclass)."""
    from ...services.people_service import PeopleService, UnavailablePeopleStore
    from ...services.follow_through_service import FollowThroughService

    principal = getattr(request.state, "principal", UNAUTHENTICATED)
    db = get_database()

    # Build the brief window from the response dict.
    brief_window = (brief_dict.get("period_start", ""), brief_dict.get("period_end", ""))

    # The people service -- compose at request time, degrade gracefully.
    try:
        from ...people import production_people_store
        people_svc = PeopleService(production_people_store())
    except Exception:
        people_svc = PeopleService(UnavailablePeopleStore())

    follow_through = FollowThroughService(db)

    overlay = compose_person_overlay(
        brief_window, people_svc, follow_through, db, principal,
    )

    if overlay.get("state") == "ready":
        brief_dict["person_sections"] = overlay.get("sections", [])
    elif overlay.get("state") == "unavailable":
        # L2: explicit honesty -- the caller sees the sidecar is closed.
        brief_dict["person_sections_state"] = "unavailable"

    return brief_dict


def build_monday_brief_router(ctx: WebContext) -> APIRouter:
    """Expose the durable Monday Brief through the web API.

    PHILO-5-02: every verb goes through the hub's bound contract, whose brief
    service carries the producer clock (gap A). The router builds no service
    of its own; a partially wired context gets one over its own clock.
    """
    router = APIRouter(prefix="/api/brief", tags=["monday-brief"])
    principal = lambda request: getattr(request.state, "principal", UNAUTHENTICATED)

    def ops() -> operations.OperationRegistry:
        # In the hub: ctx.operations, and nothing is built here. A partially
        # wired context (a route test) gets a bare brief service over its own
        # clock, through this module's database seams.
        return operations.for_context(ctx, monday_brief_service=lambda: MondayBriefService(
            get_database(), observer=get_observer(), clock=getattr(ctx, "brief_clock", None),
        ))

    @router.get("/latest")
    async def latest(request: Request) -> dict[str, Any] | None:
        registry = ops()
        brief = registry.invoke(principal(request), "brief.latest", {})
        if brief is None:
            return None
        result = asdict(brief)
        result["period_label"] = _period_label(result)
        result["generated_label"] = _generated_label(result)
        return _compose_overlay(result, registry.target("brief.latest"), request)

    @router.post("/generate")
    async def generate(request: Request) -> dict[str, Any]:
        registry = ops()
        result = asdict(registry.invoke(principal(request), "brief.generate", {}))
        result["period_label"] = _period_label(result)
        result["generated_label"] = _generated_label(result)
        return _compose_overlay(result, registry.target("brief.generate"), request)

    # HS-132-08 -- brief triage is a durable owner verb, not React state.
    @router.get("/shelf")
    async def read_shelf(request: Request) -> dict[str, str]:
        return ops().invoke(principal(request), "brief.shelf.read", {})

    @router.post("/items/{item_id}/shelf")
    async def write_shelf(
        request: Request,
        item_id: str,
        body: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        state = body.get("state")
        if state is not None and not isinstance(state, str):
            raise HTTPException(status_code=422, detail="state must be a string")
        try:
            return ops().invoke(principal(request), "brief.shelf.write", {"item_id": item_id, "state": state})
        except LookupError as unknown_item:
            raise HTTPException(status_code=404, detail=str(unknown_item)) from unknown_item
        except ValueError as unknown_state:
            raise HTTPException(status_code=422, detail=str(unknown_state)) from unknown_state

    return router
