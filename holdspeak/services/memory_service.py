"""Transport-neutral long-horizon memory retrieval."""
from __future__ import annotations

from typing import Any

from ..db.core import Database
from ..principals import Principal, PrincipalKind, PrincipalRight, refusal
from .errors import ServiceError, ValidationError


class MemoryService:
    def __init__(self, db: Database) -> None:
        self._db = db

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
        try:
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
