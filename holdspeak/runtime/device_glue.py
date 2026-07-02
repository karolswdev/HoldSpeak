"""The AIPI-Lite device glue (HS-63-03).

Device voice sessions, events, health, and queries — verbatim moves out
of WebRuntime.
"""

from __future__ import annotations

import hashlib
import os
import signal
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

from ..audio import AudioRecorder
from ..config import Config
from ..audio import AudioSource
from ..device_audio import DeviceRegistry, ensure_device_psk
from ..web_auth import ensure_web_token
from ..device_recording_tick import RecordingTicker
from ..device_meeting_stats import pick_next_view
from ..device_status import (
    DeviceStatusEmitter,
    push_intel_to_devices,
    push_segment_to_devices,
)
from ..desktop_presence import DesktopPresenceHost, build_desktop_presence_host
from ..hotkey import HotkeyListener
from ..voice_typing import VoiceTypingSession
from ..logging_config import get_logger
from ..meeting_session import MeetingSession
from ..plugins.router import (
    DEFAULT_INTENT_THRESHOLD,
    SUPPORTED_INTENTS,
    available_profiles,
    normalize_override_intents,
    normalize_profile,
    preview_route,
)
from ..plugins.builtin import register_builtin_plugins
from ..plugins.host import PluginHost, build_idempotency_key
from ..plugins.project_detector import ProjectDetectorPlugin
from ..plugins.queue import drain_plugin_run_queue, process_next_plugin_run_job
from ..plugins.signals import extract_intent_signals
from ..activity_tracker import RuntimeActivityTracker
from ..text_processor import TextProcessor
from ..transcribe import Transcriber
from ..typer import TextTyper
from ..web.runtime_support import _UnknownDeviceError
from ..web_server import MeetingWebServer, WebRuntimeCallbacks

log = get_logger("web_runtime")

# HS-32-03: the owner string a meeting uses to hold the shared
# ``VoiceTypingSession`` audio floor. One arbiter for hotkey / device /
# meeting capture; while a meeting holds this, hotkey/device ``begin()``
# is rejected, and a meeting can't start while either holds the floor.
_MEETING_AUDIO_OWNER = "meeting"



log = get_logger("web_runtime")


class DeviceGlueMixin:
    def _on_device_voice_start(self, device_id: str, source: AudioSource) -> bool:
        """Begin a device-driven voice-typing session.

        Returns ``False`` (so the WS dispatcher emits a
        ``session_busy`` error frame) when:
        - a meeting is active and this device is *not* attached
          to it (meeting holds the audio floor);
        - the local hotkey or another device already owns the
          voice session.

        When this device *is* attached to the active meeting, the
        meeting already started its recorder — return ``True``
        without claiming the voice session so the WS keeps pumping
        binary frames into the meeting's drain path.
        """
        active_meeting = self._active_meeting_session()
        if active_meeting is not None:
            if active_meeting.is_device_attached(device_id):
                return True
            self._set_runtime_activity(
                "complete",
                source="device",
                label="Device busy",
                detail="Meeting audio is already active.",
                last_event="device_dictation_busy",
                last_error="",
            )
            return False
        from ..agent_context import get_recent_awaiting_agent_session

        agent_reply_session = get_recent_awaiting_agent_session(max_age_seconds=120)
        if not self._agent_reply_deliverable(agent_reply_session):
            with self.state_lock:
                self.runtime_status["last_error"] = "Agent reply target unavailable"
            self.device_status.send(device_id, "No reply target", ttl_ms=3000)
            log.info(
                "device_voice_start_rejected_no_agent_reply_target",
                extra={"device_id": device_id},
            )
            self._set_runtime_activity(
                "error",
                source="device",
                detail="Agent reply target unavailable.",
                last_event="device_dictation_no_reply_target",
                last_error="Agent reply target unavailable",
            )
            return False
        owner = f"device:{device_id}"
        try:
            accepted = self.voice_session.begin(source, owner=owner)
        except Exception as exc:
            log.error(f"Device voice-typing start failed: {exc}")
            self._set_runtime_activity(
                "error",
                source="device",
                detail="Device recording failed.",
                last_event="device_dictation_recording_failed",
                last_error=f"{type(exc).__name__}: {exc}",
            )
            return False
        if not accepted:
            self._set_runtime_activity(
                "complete",
                source="device",
                label="Device busy",
                detail="Another HoldSpeak audio session is active.",
                last_event="device_dictation_busy",
                last_error="",
            )
            return False
        self._set_voice_state(
            "recording",
            source="device",
            detail="Device voice input is recording.",
            last_event="device_dictation_recording_started",
            last_error="",
        )
        # AIPI-4-13: TX state lives in the device's firmware-side
        # tx_label glyph (top-right, ↑ during right-button hold).
        # No "Listening..." pushback — would clobber the bottom
        # widget's persistent meeting/idle text.
        return True

    def _on_device_voice_stop(
        self, device_id: str, source: AudioSource
    ) -> Optional[np.ndarray]:
        active_meeting = self._active_meeting_session()
        if active_meeting is not None and active_meeting.is_device_attached(device_id):
            # The meeting owns this device's audio routing.
            return None
        owner = f"device:{device_id}"
        try:
            audio = self.voice_session.end(owner=owner)
        except Exception as exc:
            log.error(f"Device voice-typing stop failed: {exc}")
            self._set_voice_state(
                "idle",
                source="device",
                detail="Device recording stop failed.",
                last_event="device_dictation_recording_stop_failed",
                last_error=f"{type(exc).__name__}: {exc}",
            )
            return None
        if audio is None:
            self._set_voice_state("idle", source="device", last_event="device_dictation_recording_ignored")
            return None

        # AIPI-4-13: no "Thinking..." pushback to bottom — the absent
        # tx_label arrow after release already signals "we're done
        # capturing, processing now". Transcript snippet lands in
        # the middle slot below.

        from ..agent_context import get_recent_awaiting_agent_session

        agent_reply_session = get_recent_awaiting_agent_session(max_age_seconds=120)

        def _device_transcript_complete(text: str) -> None:
            snippet = (text or "").strip()[:150]
            self.device_status.send(device_id, snippet, ttl_ms=4000)

        self._kick_off_transcribe(
            audio,
            on_complete=_device_transcript_complete,
            agent_reply_session=agent_reply_session,
            source="device",
        )
        return audio

    def _on_device_voice_cancel(self, device_id: str) -> None:
        self.voice_session.cancel(owner=f"device:{device_id}")

    def _on_device_event(self, device_id: str, name: str, at: Optional[float]) -> None:
        """Inbound device event from the WS.

        - ``long_press`` (HS-14-07): bookmark gesture in an active
          meeting where this device is attached.
        - ``double_left_click`` (AIPI-4-14): cycle through meeting-stat
          views (Numbers → Speakers → Intel) on the device's middle
          slot.
        """
        if name == "long_press":
            active = self._active_meeting_session()
            if active is None or not active.is_device_attached(device_id):
                return
            bookmark = active.add_bookmark(label="", auto_label=True)
            if bookmark is None:
                return
            attached_ids = [d.id for d in active.state.devices] if active.state else []
            self.device_status.broadcast(
                attached_ids,
                f"Bookmark @ {bookmark.timestamp:.0f}s",
                ttl_ms=2500,
            )
            return

        if name == "double_left_click":
            active = self._active_meeting_session()
            if active is None or active.state is None:
                log.info(
                    "device_event_double_tap_ignored",
                    extra={"device_id": device_id, "reason": "no_active_meeting"},
                )
                return
            if not active.is_device_attached(device_id):
                log.info(
                    "device_event_double_tap_ignored",
                    extra={"device_id": device_id, "reason": "device_not_attached"},
                )
                return
            current = self.device_stats_cycle.get(device_id, -1)
            next_index, view_id, formatter = pick_next_view(current)
            self.device_stats_cycle[device_id] = next_index
            payload = formatter(active.state)
            self.device_status.send(device_id, payload, ttl_ms=4000)
            log.info(
                "device_event_double_tap_cycled",
                extra={"device_id": device_id, "view": view_id, "index": next_index},
            )
            return

        log.info(
            "device_event_ignored",
            extra={"device_id": device_id, "event_name": name},
        )

    def _on_device_health(self, descriptor: object) -> None:
        active = self._active_meeting_session()
        if active is None:
            return
        updater = getattr(active, "update_device_descriptor", None)
        if callable(updater):
            updater(descriptor)
        if self.server is not None:
            try:
                from ..meeting_session import _device_descriptor_to_dict

                self.server.broadcast("device_health", _device_descriptor_to_dict(descriptor))
            except Exception as exc:
                log.debug(f"Failed to broadcast device health: {exc}")

    def _on_device_query(
        self,
        device_id: str,
        name: str,
        at: Optional[float],
    ) -> Optional[dict[str, object]]:
        from ..agent_context import (
            get_recent_awaiting_agent_session,
            select_next_awaiting_agent_session,
        )
        from ..agent_device import (
            AGENT_NEXT_QUERY,
            AGENT_QUERY_NAMES,
            build_agent_query_response,
        )

        if name in AGENT_QUERY_NAMES:
            if name == AGENT_NEXT_QUERY:
                session = select_next_awaiting_agent_session(max_age_seconds=120)
                response_name = "agent_status"
            else:
                session = get_recent_awaiting_agent_session(max_age_seconds=120)
                response_name = name
            response = build_agent_query_response(response_name, session)
            if response is not None:
                return response

        if name != "last_segment":
            log.info(
                "device_query_ignored",
                extra={"device_id": device_id, "query_name": name, "at": at},
            )
            return {"text": f"Unknown query: {name}"[:500], "ttl_ms": 3000}
        active = self._active_meeting_session()
        if active is None or active.state is None:
            return {"text": "No transcript yet", "ttl_ms": 5000}
        for segment in reversed(active.state.segments):
            if getattr(segment, "device_id", None) != device_id:
                continue
            speaker = getattr(segment, "speaker", None) or "?"
            text = getattr(segment, "text", "") or ""
            return {
                "text": f"{speaker}: {text}"[:500],
                "ttl_ms": 5000,
            }
        return {"text": "No transcript yet", "ttl_ms": 5000}
