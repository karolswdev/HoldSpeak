"""Follow-Through board transport adapters.

HS-150-07: person enrichment is composed at the ROUTE ADAPTER layer
after the service returns -- the service stays person-free for observers
and the MCP follow_through.board tool.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request

from ...principals import UNAUTHENTICATED
from ...services.follow_through_service import FollowThroughBoard, FollowThroughCard, FollowThroughService
from ..context import WebContext


def _board_dict(board: FollowThroughBoard) -> dict[str, list[dict[str, Any]]]:
    return {
        "now": [asdict(card) for card in board.now],
        "waiting": [asdict(card) for card in board.waiting],
        "unassigned": [asdict(card) for card in board.unassigned],
        "overdue": [asdict(card) for card in board.overdue],
    }


def _enrich_board(
    board_dict: dict[str, list[dict[str, Any]]],
    board: FollowThroughBoard,
) -> dict[str, list[dict[str, Any]]]:
    """HS-150-07: resolve mapped owner strings to person labels at the route
    adapter, mirroring door_service._build_owner_person_index.

    The enrichment is readiness-guarded: a locked, absent, or broken sidecar
    degrades to the plain board silently and honestly (no error, no partial
    results).
    """
    from ...services.people_service import PeopleService, UnavailablePeopleStore

    try:
        from ...people import production_people_store
        people_svc = PeopleService(production_people_store())
    except Exception:
        return board_dict

    # One resolve per distinct owner string, memoized per request.
    all_cards: list[FollowThroughCard] = list(board.now) + list(board.waiting) + list(board.unassigned) + list(board.overdue)
    seen: dict[str, tuple[str, str] | None] = {}
    for card in all_cards:
        if not card.owner or card.owner in seen:
            continue
        try:
            result = people_svc.resolve_relationship_by_owner(card.owner)
        except Exception:
            seen[card.owner] = None
            continue
        if result.get("state") != "ready":
            seen[card.owner] = None
            continue
        rel = result.get("relationship")
        if rel is not None:
            name = str(rel.get("display_name") or "")
            rel_id = str(rel.get("id") or "")
            seen[card.owner] = (name, rel_id) if name else None
        else:
            seen[card.owner] = None

    index = {k: v for k, v in seen.items() if v}
    if not index:
        return board_dict

    # Stamp person_label / person_relationship_id on matching card dicts.
    for lane_cards in board_dict.values():
        for card_dict in lane_cards:
            owner = card_dict.get("owner")
            if owner and owner in index:
                label, rel_id = index[owner]
                card_dict["person_label"] = label
                if rel_id:
                    card_dict["person_relationship_id"] = rel_id

    return board_dict


def build_follow_through_router(ctx: WebContext) -> APIRouter:
    """Expose the Follow-Through board through the Desk's HTTP surface."""
    router = APIRouter(prefix="/api/follow-through", tags=["follow-through"])
    service = ctx.follow_through_service
    if service is None:
        from ...db import get_database, get_observer

        service = FollowThroughService(get_database(), observer=get_observer())
    principal = lambda request: getattr(request.state, "principal", UNAUTHENTICATED)

    @router.get("/board")
    async def board(
        request: Request,
        project_id: str | None = None,
        owner: str | None = None,
        state: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        try:
            raw_board = service.board(principal(request), project_id=project_id, owner=owner, state=state)
            board_dict = _board_dict(raw_board)
            return _enrich_board(board_dict, raw_board)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/complete")
    async def complete(request: Request, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return service.complete(
                principal(request),
                str(body.get("card_id") or ""),
                str(body.get("verb") or ""),
                body.get("payload"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/commit-decision")
    async def commit_decision(request: Request, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return service.commit_decision(
                principal(request),
                str(body.get("decision_id") or ""),
                owner=body.get("owner"),
                due_at=body.get("due_at"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
