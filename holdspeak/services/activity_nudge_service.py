"""Transport-neutral activity nudge operations (HS-123-07)."""
from __future__ import annotations
from typing import Any
from ..db.core import Database
from ..principals import Principal
from .errors import ValidationError


class ActivityNudgeService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def list(self, principal: Principal, project_id: str | None, limit: int) -> dict[str, Any]:
        from ..activity_nudges import compute_nudges
        nudges = compute_nudges(self._db, project_id=project_id, limit=limit)
        settings = self._db.activity.get_activity_privacy_settings()
        return {"nudges": [n.to_dict() for n in nudges], "activity_enabled": bool(settings.get("enabled", False))}

    def dismiss(self, principal: Principal, nudge_id: str) -> dict[str, Any]:
        clean = (nudge_id or "").strip()
        if not clean: raise ValidationError("nudge_id is required")
        try: self._db.activity.dismiss_nudge(clean)
        except ValueError as exc: raise ValidationError(str(exc)) from exc
        return {"dismissed": clean}

    def select(self, principal: Principal, record_id: Any) -> dict[str, Any]:
        try: parsed = int(record_id)
        except (TypeError, ValueError) as exc: raise ValidationError("record_id (int) is required") from exc
        if self._db.activity.get_activity_record(parsed) is None: raise ValidationError(f"unknown record_id {parsed}")
        from ..dictation_selection import set_selected_record
        set_selected_record(parsed)
        return {"selected": parsed}
