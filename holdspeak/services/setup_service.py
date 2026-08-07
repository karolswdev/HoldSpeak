"""Transport-neutral first-run setup and onboarding operations."""
from __future__ import annotations

from typing import Any

from ..db import FIRST_DICTATION_SUCCESS
from ..db.core import Database
from ..principals import Principal
from .errors import NotFound, ValidationError


class SetupService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def status(self, principal: Principal) -> dict[str, Any]:
        from ..setup_status import build_setup_status

        return build_setup_status(database=self._db)

    def test_runtime(self, principal: Principal, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        from ..config import Config
        from ..setup_runtime import probe_runtime

        return probe_runtime(Config.load().dictation)

    def set_onboarding_disposition(
        self, principal: Principal, payload: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            state = self._db.onboarding.set_disposition(str(payload.get("disposition") or ""))
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return {"success": True, "onboarding": state}

    def start_first_value(self, principal: Principal, payload: dict[str, Any]) -> dict[str, Any]:
        self._reject_content(payload)
        try:
            attempt = self._db.onboarding.start_attempt(
                destination=str(payload.get("destination") or "this_machine")
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return {"success": True, "attempt": attempt}

    def finish_first_value(
        self, principal: Principal, attempt_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self._reject_content(payload)
        try:
            attempt = self._db.onboarding.finish_attempt(
                attempt_id,
                outcome=str(payload.get("outcome") or ""),
                steps=payload.get("steps"),
                decisions=payload.get("decisions"),
                destination=str(payload.get("destination") or "this_machine"),
                failure_category=payload.get("failure_category"),
            )
        except KeyError as exc:
            raise NotFound("first-value attempt", attempt_id) from exc
        except (TypeError, ValueError) as exc:
            raise ValidationError(str(exc)) from exc
        if attempt.get("succeeded_at"):
            self._db.milestones.mark(FIRST_DICTATION_SUCCESS)
            self._db.onboarding.set_disposition("completed")
        return {"success": True, "attempt": attempt}

    @staticmethod
    def _reject_content(payload: dict[str, Any]) -> None:
        if {"text", "phrase", "transcript", "content", "audio"}.intersection(payload):
            raise ValidationError("First-value receipts never accept phrase content.")
