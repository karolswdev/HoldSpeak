"""Transport-neutral coder-session operations (HS-122-05)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from ..db.core import Database
from ..principals import Principal
from .primitive_service import NotFound, ValidationError


class CoderService:
    def __init__(
        self,
        db: Database,
        *,
        reply_sender: Callable[[str, str], Any] | None = None,
    ) -> None:
        self._db = db
        self._reply_sender = reply_sender

    def list_sessions(
        self,
        principal: Principal,
        *,
        agent: str | None = None,
        include_ended: bool = True,
    ) -> list[dict[str, Any]]:
        from ..agent_context import DEFAULT_LIFECYCLE_DEAD_SECONDS, LIFECYCLE_ENDED, effective_state, list_agent_sessions
        from ..agent_device import build_agent_identity_payload

        now = datetime.now(timezone.utc)
        items: list[dict[str, Any]] = []
        for session in list_agent_sessions(agent=agent):
            age = self._age_seconds(session.updated_at, now)
            if age is not None and age > DEFAULT_LIFECYCLE_DEAD_SECONDS:
                continue
            state = effective_state(session, now=now)
            if state == LIFECYCLE_ENDED and not include_ended:
                continue
            payload = session.to_dict()
            payload["state"] = state
            items.append({"session": payload, "age_seconds": age, "identity": build_agent_identity_payload(session)})
        return items

    def get_session(self, principal: Principal, session_id: str) -> dict[str, Any]:
        agent, raw_session_id = self._split_session_id(session_id)
        from ..agent_context import list_agent_sessions

        session = next(
            (
                item for item in list_agent_sessions(agent=agent)
                if item.session_id == raw_session_id
            ),
            None,
        )
        if session is None:
            raise NotFound("coder session", session_id)
        return session.to_dict()

    def select_session(self, principal: Principal, session_id: str) -> dict[str, Any]:
        agent, raw_session_id = self._split_session_id(session_id)
        from ..agent_context import select_awaiting_agent_session

        session = select_awaiting_agent_session(agent, raw_session_id)
        if session is None:
            raise NotFound("coder session", session_id)
        return session.to_dict()

    def reply(self, principal: Principal, session_id: str, text: str) -> dict[str, Any]:
        clean_text = str(text or "").strip()
        if not clean_text:
            raise ValidationError("text must be a non-empty string")
        session = self.get_session(principal, session_id)
        if self._reply_sender is None:
            raise ValidationError("coder reply delivery is unavailable")
        outcome = self._reply_sender(session_id, clean_text)
        return {"success": True, "session": session, "reply": outcome}

    @staticmethod
    def _split_session_id(value: str) -> tuple[str, str]:
        agent, separator, session_id = str(value or "").partition(":")
        if not separator or not agent.strip() or not session_id.strip():
            raise ValidationError("session_id must be agent:session_id")
        return agent.strip(), session_id.strip()

    @staticmethod
    def _age_seconds(stamp: str | None, now: datetime) -> int | None:
        if not isinstance(stamp, str) or not stamp.strip():
            return None
        try:
            parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return max(0, int((now - parsed).total_seconds()))
