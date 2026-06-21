"""The dictation capture path (HS-63-03).

Transcribe-and-type, the hotkey handlers, the tmux agent-reply path, and
voice-command dispatch — verbatim moves out of WebRuntime.
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
from ..dictation_runner import dispatch_voice_command, run_dictation_pipeline
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
from ..runtime_activity import RuntimeActivityTracker
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


class DictationCaptureMixin:
    def _transcribe_and_type(
        self,
        audio: np.ndarray,
        *,
        on_complete: Optional[Callable[[str], None]] = None,
        agent_reply_session: Any | None = None,
    ) -> None:
        """Run transcription, text processing, and typing for a captured chunk.

        Shared between the local hotkey path and the device-driven
        voice-typing path (HS-14-05). Always flips voice state back
        to ``idle`` in its ``finally``. ``on_complete`` (HS-14-07)
        receives the typed text on success and is intentionally
        invoked outside the typing try-block — typing failures
        still surface the transcript to the device.
        """
        completed_text: Optional[str] = None
        with self.transcription_lock:
            try:
                text = self._ensure_transcriber_loaded().transcribe(audio)
                if not text:
                    self._set_runtime_activity(
                        "complete",
                        source="dictation",
                        label="No speech",
                        detail="No speech detected.",
                        last_event="dictation_no_speech",
                        last_error="",
                    )
                    return
                text = self.text_processor.process(text)
                # HS-52-04: voice command dispatch. A configured, enabled keyword fires
                # an action instead of being typed; on a match we return early and type
                # nothing. Off by default and on no match this is inert (byte-identical).
                voice_command = self._maybe_dispatch_voice_command(text, agent_reply_session)
                if voice_command is not None:
                    if voice_command.ok:
                        self._set_runtime_activity(
                            "complete",
                            source="dictation",
                            label="Command",
                            detail=voice_command.preview,
                            last_event="voice_command_fired",
                            last_error="",
                        )
                        self._mark_first_dictation()
                    else:
                        with self.state_lock:
                            self.runtime_status["last_error"] = (
                                f"Voice command failed: {voice_command.error}"
                            )
                        self._set_runtime_activity(
                            "error",
                            source="dictation",
                            label="Command failed",
                            detail=voice_command.preview,
                            last_event="voice_command_failed",
                            last_error=voice_command.error,
                        )
                    return
                self._set_runtime_activity(
                    "processing",
                    source="dictation",
                    detail="Processing dictation.",
                    last_event="dictation_processing",
                    last_error="",
                )
                text = self._maybe_run_dictation_pipeline(
                    text,
                    audio_duration_s=len(audio) / 16000.0,
                    transcribed_at=datetime.now(),
                    agent_reply_session=agent_reply_session,
                )
                completed_text = text
                with self.state_lock:
                    self.runtime_status["last_transcription"] = text
                    self.runtime_status["last_error"] = ""
                print(f"-> {text}")
                delivered = self._try_tmux_agent_reply(text, agent_reply_session)
                if delivered:
                    self._set_runtime_activity(
                        "complete",
                        source="dictation",
                        label="Sent",
                        detail="Sent dictated text to the agent session.",
                        last_event="dictation_delivered",
                        last_error="",
                    )
                    self._mark_first_dictation()
                if not delivered and self.typer is not None:
                    try:
                        paste_target_profile = self._paste_target_profile(agent_reply_session)
                        self._set_runtime_activity(
                            "typing",
                            source="dictation",
                            detail="Typing dictated text.",
                            last_event="dictation_typing",
                            last_error="",
                        )
                        self.typer.type_text(
                            text,
                            target_profile=paste_target_profile,
                            submit=agent_reply_session is not None,
                        )
                        self._set_runtime_activity(
                            "complete",
                            source="dictation",
                            label="Typed",
                            detail="Dictated text was inserted.",
                            last_event="dictation_typed",
                            last_error="",
                        )
                        self._mark_first_dictation()
                    except Exception as exc:
                        with self.state_lock:
                            self.runtime_status["last_error"] = f"Typing failed: {exc}"
                            self.runtime_status["text_injection_enabled"] = False
                            self.runtime_status["text_injection_error"] = f"{type(exc).__name__}: {exc}"
                        self._set_runtime_activity(
                            "error",
                            source="dictation",
                            detail="Typing failed.",
                            last_event="dictation_typing_failed",
                            last_error=f"{type(exc).__name__}: {exc}",
                        )
                        log.warning(f"Typing failed in web mode: {exc}")
            except Exception as exc:
                with self.state_lock:
                    self.runtime_status["last_error"] = f"Transcription failed: {exc}"
                self._set_runtime_activity(
                    "error",
                    source="dictation",
                    detail="Transcription failed.",
                    last_event="dictation_transcription_failed",
                    last_error=f"{type(exc).__name__}: {exc}",
                )
                log.error(f"Transcription failed in web mode: {exc}")
            finally:
                self._set_voice_state("idle", update_activity=False)
        if on_complete is not None and completed_text is not None:
            try:
                on_complete(completed_text)
            except Exception as exc:
                log.warning(f"on_complete hook raised: {exc}")

    def _kick_off_transcribe(
        self,
        audio: np.ndarray,
        *,
        on_complete: Optional[Callable[[str], None]] = None,
        agent_reply_session: Any | None = None,
        source: str = "dictation",
    ) -> None:
        if len(audio) < 1600:
            self._set_voice_state("idle", update_activity=False)
            self._set_runtime_activity(
                "complete",
                source=source,
                label="Too short",
                detail="Recording was too short.",
                last_event="dictation_too_short",
                last_error="",
            )
            return
        self._set_voice_state(
            "transcribing",
            source=source,
            detail="Transcribing audio.",
            last_event="dictation_transcribing",
            last_error="",
        )
        threading.Thread(
            target=lambda: self._transcribe_and_type(
                audio,
                on_complete=on_complete,
                agent_reply_session=agent_reply_session,
            ),
            daemon=True,
        ).start()

    def _maybe_dispatch_voice_command(
        self, text: str, agent_reply_session: Any | None = None
    ) -> Any:
        # HS-52-04: thin delegate to the carved dispatch seam. Injects the runtime
        # typer for `type_text` macros and surfaces a matched command as a runtime
        # activity. Returns a VoiceCommandResult if a command fired (caller types
        # nothing), else None.
        def _type(t: str) -> None:
            if self.typer is not None:
                self.typer.type_text(
                    t, target_profile=self._paste_target_profile(agent_reply_session)
                )

        def _activity(label: str) -> None:
            self._set_runtime_activity(
                "processing",
                source="dictation",
                label=label,
                detail=label,
                last_event="voice_command_match",
                last_error="",
            )

        return dispatch_voice_command(
            text,
            config=self.config,
            type_writer=_type,
            on_activity=_activity,
        )

    def _maybe_run_dictation_pipeline(
        self,
        text: str,
        *,
        audio_duration_s: float,
        transcribed_at: datetime,
        agent_reply_session: Any | None = None,
        journal_source: str = "dictation",
    ) -> str:
        # HS-52-01: the orchestration was carved out of this god-object into
        # `holdspeak.dictation_runner`; this stays as the thin delegate the
        # transcription path calls. Behaviour is unchanged.
        return run_dictation_pipeline(
            text,
            config=self.config,
            server=self.server,
            audio_duration_s=audio_duration_s,
            transcribed_at=transcribed_at,
            agent_reply_session=agent_reply_session,
            journal_source=journal_source,
        )

    def _paste_target_profile(self, agent_reply_session: Any | None) -> str | None:
        if agent_reply_session is None:
            return None
        try:
            from holdspeak.agent_device import target_profile_override_for_agent

            return target_profile_override_for_agent(agent_reply_session)
        except Exception:
            return None

    def _try_tmux_agent_reply(self, text: str, agent_reply_session: Any | None) -> bool:
        pane = self._agent_tmux_pane(agent_reply_session)
        if not pane:
            return False
        try:
            from holdspeak.tmux_transport import send_text_to_pane

            send_text_to_pane(pane=pane, text=text, submit=True)
            return True
        except Exception as exc:
            with self.state_lock:
                self.runtime_status["last_error"] = f"tmux reply failed; fell back to typing: {exc}"
            log.warning(f"tmux reply failed; falling back to text injection: {exc}")
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

    def _deliver_remote_dictation(self, text: str) -> dict[str, Any]:
        """HSM-13-04 — deliver a companion-dictated answer into the waiting coder.

        The text was ALREADY run through the rich dictation pipeline by the
        ``/api/dictation/remote`` route, so this is **deliver-only** — it does not
        re-transcribe or re-run the pipeline. It reuses the exact path the local
        dictation loop uses (``_try_tmux_agent_reply`` → fall back to
        ``typer.type_text``), so an answer spoken on the iPad lands the same way one
        spoken at the desk does. Deliver-on-command (the client user pressed send);
        never autonomous. **Raises** when it cannot be delivered, so the client sees
        an honest failure rather than a false ack.
        """
        from ..agent_context import get_recent_awaiting_agent_session

        text = (text or "").strip()
        if not text:
            raise ValueError("remote dictation text is empty")
        session = get_recent_awaiting_agent_session(max_age_seconds=120)
        if self._try_tmux_agent_reply(text, session):
            self._mark_first_dictation()
            return {"delivered": True, "method": "tmux", "target": self._agent_tmux_pane(session)}
        if self.typer is not None:
            self.typer.type_text(
                text,
                target_profile=self._paste_target_profile(session),
                submit=session is not None,
            )
            self._mark_first_dictation()
            return {"delivered": True, "method": "type", "target": self._paste_target_profile(session)}
        raise RuntimeError(
            "no delivery target: no waiting agent tmux pane and text injection is unavailable"
        )

    def _on_hotkey_press(self) -> None:
        if self.runtime_stop_event.is_set():
            return
        if self.recorder is None:
            self._set_runtime_activity(
                "error",
                source="hotkey",
                detail="Voice typing hotkey is unavailable.",
                last_event="dictation_hotkey_unavailable",
                last_error=str(self.runtime_status.get("global_hotkey_error") or ""),
            )
            return
        # HS-32-03: no explicit "is a meeting active?" check — the shared
        # `voice_session` arbiter is the single owner model. While a meeting
        # holds the floor (owner="meeting"), `begin()` returns False here.
        try:
            accepted = self.voice_session.begin(self.recorder, owner="hotkey")
        except Exception as exc:
            with self.state_lock:
                self.runtime_status["last_error"] = f"Recording failed: {exc}"
            self._set_voice_state(
                "idle",
                source="hotkey",
                detail="Recording failed.",
                last_event="dictation_recording_failed",
                last_error=f"{type(exc).__name__}: {exc}",
            )
            log.error(f"Recording failed in web mode: {exc}")
            return
        if not accepted:
            log.info("hotkey_press_ignored_session_active")
            self._set_runtime_activity(
                "complete",
                source="hotkey",
                label="Busy",
                detail="Another HoldSpeak audio session is active.",
                last_event="dictation_recording_busy",
                last_error="",
            )
            return
        self._set_voice_state(
            "recording",
            source="hotkey",
            detail="HoldSpeak is listening.",
            last_event="dictation_recording_started",
            last_error="",
        )

    def _on_hotkey_release(self) -> None:
        # No meeting check: `end("hotkey")` returns None when the hotkey
        # doesn't own the floor (e.g. a meeting holds it), so this is a no-op.
        try:
            audio = self.voice_session.end(owner="hotkey")
        except Exception as exc:
            with self.state_lock:
                self.runtime_status["last_error"] = f"Recording error: {exc}"
            self._set_voice_state(
                "idle",
                source="hotkey",
                detail="Recording stop failed.",
                last_event="dictation_recording_stop_failed",
                last_error=f"{type(exc).__name__}: {exc}",
            )
            log.error(f"Recording error in web mode: {exc}")
            return
        if audio is None:
            self._set_voice_state("idle", source="hotkey", last_event="dictation_recording_ignored")
            return

        self._kick_off_transcribe(audio, source="hotkey")
