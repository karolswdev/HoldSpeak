"""Runtime activity, state, and status payloads (HS-63-04).

The activity broadcasts, the voice-state machine, the idle/state/status
payload builders, and the intel-egress summary — verbatim moves out of
WebRuntime.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import numpy as np

from ..logging_config import get_logger
from ..plugins.router import (
    DEFAULT_INTENT_THRESHOLD,
    SUPPORTED_INTENTS,
    available_profiles,
)

log = get_logger("web_runtime")

# HS-32-03: the owner string a meeting uses to hold the shared
# ``VoiceTypingSession`` audio floor. One arbiter for hotkey / device /
# meeting capture; while a meeting holds this, hotkey/device ``begin()``
# is rejected, and a meeting can't start while either holds the floor.
_MEETING_AUDIO_OWNER = "meeting"



log = get_logger("web_runtime")


class RuntimeActivityMixin:
    def _broadcast_runtime_activity(self, activity: dict[str, object]) -> None:
        # Fan the activity snapshot out to: (1) the opt-in desktop presence host
        # (HS-41-03 — None unless HOLDSPEAK_DESKTOP_PRESENCE=1 and a native
        # renderer is available), and (2) web clients over the websocket.
        if self.desktop_presence is not None:
            try:
                self.desktop_presence.handle_activity(activity)
            except Exception as exc:
                log.debug(f"Desktop presence update failed: {exc}")
        if self.server is None:
            return
        try:
            self.server.broadcast("runtime_activity", activity)
        except Exception as exc:
            log.debug(f"Failed to broadcast runtime_activity: {exc}")

    def _set_runtime_activity(
        self,
        state: str,
        *,
        source: str = "runtime",
        label: Optional[str] = None,
        detail: str = "",
        last_event: str = "",
        last_error: Optional[str] = None,
    ) -> dict[str, object]:
        with self.state_lock:
            activity = self.activity_tracker.update(
                state,
                source=source,
                label=label,
                detail=detail,
                last_event=last_event,
                last_error=last_error,
            )
            self.runtime_status["activity"] = activity
        self._broadcast_runtime_activity(activity)
        return activity

    def _set_voice_state(
        self,
        value: str,
        *,
        source: str = "voice",
        detail: str = "",
        last_event: str = "",
        last_error: Optional[str] = None,
        update_activity: bool = True,
    ) -> None:
        with self.state_lock:
            self.runtime_status["voice_state"] = value
        if not update_activity:
            return
        activity_state = value if value in {"idle", "recording", "transcribing"} else "processing"
        self._set_runtime_activity(
            activity_state,
            source=source,
            detail=detail,
            last_event=last_event,
            last_error=last_error,
        )

    def _runtime_idle_state(self) -> dict[str, object]:
        runtime_uptime = max(0.0, (datetime.now() - self.runtime_started_at).total_seconds())
        with self.state_lock:
            idle_title = self.pending_title or ""
            idle_tags = list(self.pending_tags) if self.pending_tags is not None else []
            runtime_snapshot = dict(self.runtime_status)
            mir_snapshot = {
                "enabled": bool(self.mir_enabled),
                "profile": str(self.mir_profile),
                "available_profiles": available_profiles(),
                "supported_intents": list(SUPPORTED_INTENTS),
                "override_intents": list(self.mir_override_intents),
                "last_preview": dict(self.last_route_preview) if isinstance(self.last_route_preview, dict) else None,
                "threshold": float(DEFAULT_INTENT_THRESHOLD),
            }

        return {
            "id": "web-runtime",
            "mode": "web",
            "meeting_active": False,
            "meeting_id": None,
            "started_at": None,
            "ended_at": None,
            "duration": 0.0,
            "formatted_duration": "00:00",
            "title": idle_title,
            "tags": idle_tags,
            "web_url": self.runtime_url,
            "runtime_started_at": self.runtime_started_at.isoformat(),
            "runtime_uptime": runtime_uptime,
            "bookmarks": list(self.bookmarks),
            "segments": [],
            "topics": [],
            "action_items": [],
            "summary": "",
            "intel_status": {
                "state": "idle",
                "detail": "No meeting active. Start a meeting from web controls.",
                "requested_at": None,
                "completed_at": None,
            },
            "mir": mir_snapshot,
            "runtime": runtime_snapshot,
            "activity": runtime_snapshot.get("activity") if isinstance(runtime_snapshot.get("activity"), dict) else {},
        }

    def _get_state(self) -> dict[str, object]:
        session = self._active_meeting_session()
        if session is None:
            return self._runtime_idle_state()

        state = session.state
        if state is None:
            return self._runtime_idle_state()

        payload = state.to_dict()
        payload["mode"] = "web"
        payload["meeting_active"] = session.is_active
        payload["meeting_id"] = payload.get("id")
        payload["runtime_started_at"] = self.runtime_started_at.isoformat()
        payload["runtime_uptime"] = max(0.0, (datetime.now() - self.runtime_started_at).total_seconds())
        if self.runtime_url and not payload.get("web_url"):
            payload["web_url"] = self.runtime_url
        with self.state_lock:
            payload["runtime"] = dict(self.runtime_status)
            payload["activity"] = (
                dict(self.runtime_status["activity"])
                if isinstance(self.runtime_status.get("activity"), dict)
                else {}
            )
        payload["mir"] = self._mir_controls_payload()
        return payload

    def _get_runtime_status(self) -> dict[str, object]:
        state = self._get_state()
        runtime = state.get("runtime") if isinstance(state.get("runtime"), dict) else {}
        meeting_active = bool(state.get("meeting_active"))
        meeting = self._meeting_summary_from_state(state)
        with self.state_lock:
            last_meeting = dict(self.last_meeting_snapshot) if isinstance(self.last_meeting_snapshot, dict) else None
            runtime_snapshot = dict(self.runtime_status)
        return {
            "status": "ok",
            "mode": "web",
            "url": self.runtime_url,
            "meeting_active": meeting_active,
            "meeting_id": state.get("id") if meeting_active else None,
            "meeting": meeting,
            "last_meeting": last_meeting,
            "voice_state": runtime.get("voice_state", runtime_snapshot.get("voice_state", "idle")),
            "activity": runtime_snapshot.get("activity") if isinstance(runtime_snapshot.get("activity"), dict) else {},
            "text_injection_enabled": runtime_snapshot.get("text_injection_enabled"),
            "text_injection_error": runtime_snapshot.get("text_injection_error", ""),
            "llm_capability_enabled": self.llm_capability_enabled,
            "transcription": {
                "model": runtime_snapshot.get("transcription_model", self.config.model.name),
                "warm_on_start": runtime_snapshot.get("transcription_warm_on_start", False),
                "status": runtime_snapshot.get("transcription_status", "not_loaded"),
                "error": runtime_snapshot.get("transcription_error", ""),
            },
            "intel_egress": self._intel_egress_payload(),
            "mir": self._mir_controls_payload(),
            "state": state,
        }

    def _intel_egress_payload(self) -> dict[str, object]:
        """Egress posture for the web intel-status surface (HS-25-01).

        Lets the UI state plainly whether transcripts can leave the machine
        without anyone reading logs.
        """
        from ..intel import intel_egress_posture

        meeting = self.config.meeting
        if not meeting.intel_enabled:
            return {
                "enabled": False,
                "provider": meeting.intel_provider,
                "can_transmit_offmachine": False,
                "egress": "Disabled — no transcript leaves this machine.",
            }
        can_transmit, description = intel_egress_posture(meeting.intel_provider)
        return {
            "enabled": True,
            "provider": meeting.intel_provider,
            "can_transmit_offmachine": can_transmit,
            "egress": description,
        }
