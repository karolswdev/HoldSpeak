"""Transport-neutral durable Desk projection operations (HS-123-05)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

from typing import Any

from ..db.core import Database
from ..principals import Principal
from .errors import NotFound, ValidationError


@observe_service
class ProjectionService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def list(self, principal: Principal, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        filters = filters or {}
        kind = filters.get("kind")
        attention_state = filters.get("attention_state")
        if kind not in {None, "attention", "receipt"}:
            raise ValidationError("kind must be attention or receipt")
        if attention_state not in {None, "unseen", "needs_attention", "acknowledged", "resolved"}:
            raise ValidationError("invalid attention_state")
        return self._db.projections.list(
            search=str(filters.get("q") or ""), projection_kind=kind,
            attention_state=attention_state, subject_ref=filters.get("subject_ref"),
            include_dismissed=bool(filters.get("include_dismissed", False)),
            offset=filters.get("offset", 0), limit=filters.get("limit", 50),
        )

    def set_presentation(self, principal: Principal, projection_id: str, state: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(state, dict):
            raise ValidationError("expected a JSON object")
        action = str(state.get("action") or "")
        try:
            found = self._db.projections.set_presentation(projection_id, action=action)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        if not found:
            raise NotFound("Projection", projection_id)
        return {"success": True, "projection_id": projection_id, "action": action, "subject_unchanged": True}
