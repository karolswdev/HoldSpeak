"""Read current bindings for existing service/HTTP scenarios, as their client would.

Missing/stale binding regressions call the services and routes directly.
"""
from __future__ import annotations

from dataclasses import asdict
import re
from typing import Any

from holdspeak.services.room_binding import room_binding, watch_binding


def saved_binding(service: Any, method: str, *args: Any) -> Any:
    db = service._db
    if method in ("confirm_proposal", "dismiss_proposal"):
        row = db.proposals.get_proposal(args[1])
        return room_binding(asdict(row)) if row else None
    if method == "retire_watch":
        row = db.automations.get_watch(args[1])
        return watch_binding(row) if row else None
    if method == "discard":
        return service.get_brief(args[0], args[1])["binding"]
    if method == "accept_review":
        try:
            return service.get_review(args[0], args[1], args[2])["binding"]
        except Exception:
            return None
    row = db.project_observations.get_proposal(args[2])
    return room_binding(row) if row else None


def http_binding(path: str, database: Any = None) -> Any:
    from holdspeak.db import get_database
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService
    from holdspeak.services.preparation_brief_service import PreparationBriefService
    from holdspeak.services.project_delta_service import ProjectDeltaService
    from holdspeak.principals import Principal, PrincipalKind
    db = database if database is not None else get_database()
    owner = Principal(PrincipalKind.OWNER, "test-binding-read")
    if match := re.fullmatch(r"/api/proposals/([^/]+)/(confirm|dismiss)", path):
        return saved_binding(ProposalBridgeService(db), match[2] + "_proposal", owner, match[1])
    if match := re.fullmatch(r"/api/watches/([^/]+)/retire", path):
        row = db.automations.get_watch(match[1])
        return watch_binding(row) if row else None
    if match := re.fullmatch(r"/api/briefs/([^/]+)/discard", path):
        return saved_binding(PreparationBriefService(db, project_service=None), "discard", owner, match[1])
    if match := re.fullmatch(r"/api/projects/([^/]+)/reviews/([^/]+)(/accept|/proposals/([^/]+)/decide)", path):
        service = ProjectDeltaService(db, None)
        return saved_binding(service, "accept_review", owner, match[1], match[2]) if match[3] == "/accept" else saved_binding(service, "decide_proposal", owner, match[1], match[4])
    return None


def mcp_binding(db: Any, name: str, args: dict[str, Any]) -> Any:
    if name == "project.watch.retire":
        return http_binding(f"/api/watches/{args.get('watch_id', '')}/retire", db)
    pid, rid = args.get("project_id", ""), args.get("review_id", "")
    if name == "project.accept_review":
        return http_binding(f"/api/projects/{pid}/reviews/{rid}/accept", db)
    if name == "project.decide_proposal":
        return http_binding(f"/api/projects/{pid}/reviews/{rid}/proposals/{args.get('proposal_id', '')}/decide", db)
    return None
