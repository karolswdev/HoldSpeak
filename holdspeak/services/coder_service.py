"""Transport-neutral coder-session operations (HS-122-05)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from ..db.core import Database
from ..principals import Principal
from holdspeak.services.errors import NotFound, ValidationError


class CoderService:
    def __init__(
        self,
        db: Database | None = None,
        *,
        reply_sender: Callable[[str, str], Any] | None = None,
    ) -> None:
        if db is None:
            from ..db import get_database

            db = get_database()
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

    def list_steering_audit(
        self, principal: Principal, session_key: str | None, limit: int
    ) -> list[dict[str, Any]]:
        """Return the bounded, content-safe steering audit trail."""
        try:
            clean_limit = int(limit)
        except (TypeError, ValueError) as exc:
            raise ValidationError("limit must be an integer") from exc
        clean_session_key = str(session_key).strip() if session_key is not None else None
        entries = self._db.steering.list(
            session_key=clean_session_key or None,
            limit=clean_limit,
        )
        return [entry.to_dict() for entry in entries]

    def keep_note(
        self, principal: Principal, session_key: str, content: dict[str, Any]
    ) -> dict[str, Any]:
        """Persist a session-derived note after the route resolves its session."""
        if not str(session_key or "").strip():
            raise ValidationError("session_key must be non-empty")
        if not isinstance(content, dict):
            raise ValidationError("note content must be an object")
        title = str(content.get("title") or "").strip()
        body_markdown = str(content.get("body_markdown") or "").strip()
        if not title:
            raise ValidationError("note title must be non-empty")
        if not body_markdown:
            raise ValidationError("note body must be non-empty")
        raw_tags = content.get("tags") or []
        if not isinstance(raw_tags, list) or not all(isinstance(tag, str) for tag in raw_tags):
            raise ValidationError("note tags must be strings")
        from uuid import uuid4

        note = self._db.notes.upsert(
            note_id=f"note-{uuid4().hex}",
            title=title,
            body_markdown=body_markdown,
            tags=[tag.strip() for tag in raw_tags if tag.strip()],
        )
        return note.to_dict()

    def hydrate_refs(
        self,
        principal: Principal,
        meeting_ids: list[str],
        artifact_ids: list[str],
        expand: str,
    ) -> tuple[list[Any], list[str]]:
        """Hydrate steer grounding through the application's database boundary."""
        from ..grounding import hydrate_refs

        return hydrate_refs(self._db, meeting_ids, artifact_ids, expand)

    def process_input_commands(self, targets: Any) -> Any:
        """Compose the local process-input command service for coder steering."""
        from ..db.delivery_receipts import NodeReceiptLedger
        from ..delivery.commands import HubCommandService, NodeCommandProcessor

        ledger = self._db.db_path.with_name(f"{self._db.db_path.stem}-coder-node-ledger.db")
        return HubCommandService(
            repo=self._db.delivery_receipts,
            processor=NodeCommandProcessor(
                node_id="local", targets=targets, ledger=NodeReceiptLedger(ledger)
            ),
            local_node_id="local",
        )

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
