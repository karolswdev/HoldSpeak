"""Agent and focused-target delivery for processed dictation."""
from __future__ import annotations

from typing import Any

from ..logging_config import get_logger

log = get_logger("web_runtime")


class DictationDeliveryMixin:
    def _paste_target_profile(self, agent_reply_session: Any | None) -> str | None:
        if agent_reply_session is None:
            return None
        try:
            from holdspeak.agent_device import target_profile_override_for_agent

            return target_profile_override_for_agent(agent_reply_session)
        except Exception:
            return None

    def _try_tmux_agent_reply(
        self, text: str, agent_reply_session: Any | None
    ) -> bool:
        pane = self._agent_tmux_pane(agent_reply_session)
        if not pane:
            return False
        try:
            from ..delivery.direct_gesture_input import (
                submit_process_input_from_owner_gesture,
            )

            result = submit_process_input_from_owner_gesture(
                pane=pane,
                text=text,
                session_key=str(
                    getattr(agent_reply_session, "session_id", None)
                    or getattr(agent_reply_session, "id", None)
                    or f"pane:{pane}"
                ),
                agent=str(getattr(agent_reply_session, "agent", "") or ""),
            )
            with self.state_lock:
                self.runtime_status["last_kernel_operation_id"] = result["operation_id"]
            return True
        except Exception as exc:
            with self.state_lock:
                self.runtime_status["last_error"] = (
                    f"process input refused; fell back to current focus: {exc}"
                )
            log.warning(f"process input refused; falling back to current focus: {exc}")
            return False

    def _agent_tmux_pane(self, agent_reply_session: Any | None) -> str | None:
        if agent_reply_session is None:
            return None
        pane = getattr(agent_reply_session, "tmux_pane", None)
        return str(pane).strip() if pane else None

    def _agent_reply_deliverable(self, agent_reply_session: Any | None) -> bool:
        if agent_reply_session is None:
            return True
        if self._agent_tmux_pane(agent_reply_session):
            return True
        return self.typer is not None

    def _deliver_remote_dictation(self, text: str, *, target: str = "agent") -> dict[str, Any]:
        """Deliver processed companion text to a process or bound desktop focus."""
        text = (text or "").strip()
        if not text:
            raise ValueError("remote dictation text is empty")
        if target == "focused":
            return self._deliver_remote_dictation_focused(text)

        from ..agent_context import get_recent_awaiting_agent_session

        session = get_recent_awaiting_agent_session(max_age_seconds=120)
        if self._try_tmux_agent_reply(text, session):
            self._mark_first_dictation()
            return {"delivered": True, "method": "process.input", "target": self._agent_tmux_pane(session)}
        from ..desktop_typing import type_text_from_owner_gesture

        profile = self._paste_target_profile(session)
        typed = type_text_from_owner_gesture(
            text,
            typer=self.typer,
            gesture="companion_send",
            target_profile=profile,
            submit=False,
            requested_target="agent_fallback",
            delivery_method="desktop_fallback",
        )
        self._mark_first_dictation()
        return {
            "delivered": True,
            "method": "desktop.type_text",
            "target": typed["target_ref"],
            "operation_id": typed["operation_id"],
        }

    def _deliver_remote_dictation_focused(self, text: str) -> dict[str, Any]:
        """Free-type already-processed text into the focused Mac app."""
        target_profile = self._focused_target_profile()
        from ..desktop_typing import type_text_from_owner_gesture

        typed = type_text_from_owner_gesture(
            text,
            typer=self.typer,
            gesture="companion_send",
            target_profile=target_profile,
            submit=False,
            requested_target="focused",
            delivery_method="remote_focused",
        )
        self._mark_first_dictation()
        return {
            "delivered": True,
            "method": "desktop.type_text",
            "target": typed["target_ref"],
            "operation_id": typed["operation_id"],
        }

    def _focused_target_profile(self) -> str | None:
        """Return the configured target-profile override, if any."""
        try:
            override = self.config.dictation.pipeline.target_profile_override
        except Exception:
            return None
        cleaned = str(override or "auto").strip().lower()
        if cleaned in ("", "auto"):
            return None
        return cleaned
