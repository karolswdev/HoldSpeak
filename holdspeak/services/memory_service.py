"""Transport-neutral long-horizon memory retrieval."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

from typing import Any

from ..db.core import Database
from ..principals import Principal, PrincipalKind, PrincipalRight, refusal
from .errors import ServiceError, ValidationError


@observe_service
class MemoryService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()
        #: ``MeaningSearchService`` (turn on / turn off / state), set where the
        #: hub composes its services.  None outside a hub.
        self.meaning: Any = None

    def search(
        self,
        principal: Principal,
        query: str,
        *,
        kind: str | None = None,
        project_id: str | None = None,
        time_from: str | None = None,
        time_to: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        if not principal.permits(PrincipalRight.READ):
            status = 401 if principal.kind is PrincipalKind.NONE else 403
            raise ServiceError(
                "read_forbidden",
                "principal does not permit memory reads",
                context={"status": status, "response": refusal(principal, PrincipalRight.READ)},
            )
        from ..memory.engine import memory_caller

        try:
            # The question's embedding call, when there is one, is admitted
            # for THIS principal: the receipt names who searched.
            with memory_caller(principal):
                return self._db.memory.search(
                    query,
                    kinds=kind,
                    project_id=project_id,
                    time_from=time_from,
                    time_to=time_to,
                    limit=limit,
                    offset=offset,
                ).to_dict()
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def observations(
        self,
        principal: Principal,
        *,
        project_id: str | None = None,
        scope: str | None = None,
        state: str | None = None,
        limit: int | None = 50,
    ) -> dict[str, Any]:
        """Observations (MEMORY-DESIGN.md §3.3): beliefs with their live
        evidence and history.  A read: no model call, no write.  ``scope``
        ``desk`` reads the desk's own; ``project_id`` one project's; neither,
        every scope.  ``state`` is ``current``, ``disputed`` or
        ``superseded`` (default: all three).  Nothing here comes from the
        People store: memory admits no People kind."""
        if not principal.permits(PrincipalRight.READ):
            status = 401 if principal.kind is PrincipalKind.NONE else 403
            raise ServiceError(
                "read_forbidden",
                "principal does not permit memory reads",
                context={"status": status, "response": refusal(principal, PrincipalRight.READ)},
            )
        from ..memory.consolidate import SERVED_STATES, read_observations

        chosen = str(scope or "").strip().lower()
        if chosen not in ("", "desk", "project"):
            raise ValidationError("scope must be desk or project")
        if chosen == "project" and not str(project_id or "").strip():
            raise ValidationError("scope project needs a project_id")
        states = SERVED_STATES
        if state:
            states = tuple(part.strip().lower() for part in str(state).split(",") if part.strip())
            if not states or set(states) - set(SERVED_STATES):
                raise ValidationError("state must be current, disputed or superseded")
        try:
            bounded = 50 if limit is None else int(limit)
        except (TypeError, ValueError) as exc:
            raise ValidationError("limit must be a number") from exc
        rows = read_observations(
            self._db,
            project_id=str(project_id or "").strip() or None,
            desk=chosen == "desk",
            states=states,
            limit=max(1, min(bounded, 200)),
        )
        return {"observations": rows, "count": len(rows)}

    def page(
        self,
        principal: Principal,
        *,
        slug: str,
        scope: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """One memory page (MEMORY-DESIGN.md §3.4): a standing answer with its
        sources, ``built_at``, ``stale`` and ``boundary``.  A read: NO model
        call, no write.  ``scope`` is ``project`` (needs ``project_id``) or
        ``desk``; with a ``project_id`` and no ``scope`` it is the project.
        No page, or no sentence of it live now: ``{"page": null}``.  Each
        sentence is served only while every input it cites is live in the
        scope now.  Nothing here comes from the People store."""
        if not principal.permits(PrincipalRight.READ):
            status = 401 if principal.kind is PrincipalKind.NONE else 403
            raise ServiceError(
                "read_forbidden",
                "principal does not permit memory reads",
                context={"status": status, "response": refusal(principal, PrincipalRight.READ)},
            )
        from ..memory.pages import PAGE_SET, read, spec_for

        project = str(project_id or "").strip()
        chosen = str(scope or "").strip().lower() or ("project" if project else "")
        if chosen not in PAGE_SET:
            raise ValidationError("scope must be desk or project")
        if chosen == "project" and not project:
            raise ValidationError("scope project needs a project_id")
        if chosen == "desk" and project:
            raise ValidationError("scope desk takes no project_id")
        try:
            spec_for(chosen, str(slug or "").strip())
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return {"page": read(self._db, chosen, project, str(slug).strip())}

    def standing_pages(
        self,
        principal: Principal,
        *,
        scope: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """The standing pages of one scope (canvas section 2, option B): the
        Room reads its project's, the Brief the desk's.  Each page is
        ``pages.read`` (NO model call, no write) with short ref tokens; a
        page with no live sentence is not in the list, and a withheld
        sentence is not in the shape at all.  Nothing here comes from the
        People store."""
        if not principal.permits(PrincipalRight.READ):
            status = 401 if principal.kind is PrincipalKind.NONE else 403
            raise ServiceError(
                "read_forbidden",
                "principal does not permit memory reads",
                context={"status": status, "response": refusal(principal, PrincipalRight.READ)},
            )
        from .memory_faces import standing_pages

        project = str(project_id or "").strip()
        chosen = str(scope or "").strip().lower() or ("project" if project else "")
        if chosen not in ("desk", "project"):
            raise ValidationError("scope must be desk or project")
        if chosen == "project" and not project:
            raise ValidationError("scope project needs a project_id")
        if chosen == "desk" and project:
            raise ValidationError("scope desk takes no project_id")
        return {"pages": standing_pages(self._db, chosen, project)}
