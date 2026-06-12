"""The wake-word runtime glue (HS-63-03, originally HS-60).

Listener lifecycle, the armed-capture handoff, the preview/type fork, and
the one-shot token store — verbatim moves out of WebRuntime.
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


class WakeWordGlueMixin:
    # ── HS-60: the wake word ────────────────────────────────────────────

    def _sync_wake_word(self) -> None:
        """Start/stop the wake listener to match config (live via settings)."""
        want = bool(getattr(getattr(self.config, "wake_word", None), "enabled", False))
        have = self._wake_listener is not None
        if want and not have:
            self._start_wake_listener()
        elif not want and have:
            self._stop_wake_listener()

    def _start_wake_listener(self) -> None:
        from ..wake_word import (
            FRAME_SAMPLES,
            SAMPLE_RATE as WAKE_RATE,
            OpenWakeWordDetector,
            WakeWordListener,
            wake_word_available,
        )

        if not wake_word_available():
            log.warning(
                "Wake word is enabled but the engine is not installed; "
                "install it with: pip install 'holdspeak[wakeword]'"
            )
            return
        cfg = self.config.wake_word
        try:
            detector = OpenWakeWordDetector(cfg.model)
        except Exception:
            # First enable: fetch the models — the feature's ONE network
            # moment (~7 MB from the openWakeWord GitHub releases), stated in
            # the settings copy and the docs.
            try:
                from ..wake_word import download_wake_models

                log.info(
                    f"Downloading the wake models for {cfg.model!r} "
                    "(one-time, from the openWakeWord GitHub releases)…"
                )
                download_wake_models(cfg.model)
                detector = OpenWakeWordDetector(cfg.model)
            except Exception as exc:
                log.warning(f"Wake model {cfg.model!r} unavailable: {exc}")
                return
        import queue as queue_mod

        try:
            import sounddevice as sd
        except Exception as exc:  # pragma: no cover - portaudio missing
            log.warning(f"Wake word needs sounddevice: {exc}")
            return

        wake_queue: Any = queue_mod.Queue(maxsize=64)

        def _cb(indata, _frames, _time, _status) -> None:
            try:
                wake_queue.put_nowait(indata[:, 0].copy())
            except queue_mod.Full:  # drop, never block the audio thread
                pass

        try:
            stream = sd.InputStream(
                samplerate=WAKE_RATE,
                channels=1,
                dtype="int16",
                blocksize=FRAME_SAMPLES,
                callback=_cb,
            )
            stream.start()
        except Exception as exc:
            log.warning(f"Wake word could not open the microphone: {exc}")
            return
        self._wake_queue = wake_queue
        self._wake_stream = stream

        def _frames():
            # Self-healing floor respect: while ANY owner holds the audio
            # floor (hotkey, device, meeting, or a wake capture), the
            # listener pauses (frames drain unscored); it resumes when free.
            listener = self._wake_listener
            if listener is not None:
                if self.voice_session.active_owner is not None:
                    listener.pause()
                else:
                    listener.resume()
            try:
                return wake_queue.get(timeout=0.5)
            except queue_mod.Empty:
                # Keep the loop alive through quiet stream hiccups.
                return np.zeros(FRAME_SAMPLES, dtype=np.int16)

        self._wake_listener = WakeWordListener(
            detector=detector,
            frames=_frames,
            on_detect=self._on_wake_detect,
            threshold=cfg.threshold,
        )
        self._wake_listener.start()
        log.info(f"Wake word active: {cfg.model!r} (threshold {cfg.threshold})")

    def _stop_wake_listener(self) -> None:
        listener, self._wake_listener = self._wake_listener, None
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass
        stream, self._wake_stream = self._wake_stream, None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
        self._wake_queue = None

    def _on_wake_detect(self, score: float) -> None:
        """A detection: acquire the floor, arm visibly, capture, hand off.

        Runs on the listener thread; the frame queue keeps filling from the
        stream callback, so the capture reads the same source.
        """
        from ..wake_word import ArmedCapture, FRAME_SAMPLES

        cfg = self.config.wake_word
        if not self.voice_session.acquire("wake"):
            return  # someone holds the floor; never contend
        audio = None
        try:
            self._set_runtime_activity(
                "armed",
                source="wake",
                label="Armed",
                detail=f"Say your sentence ({int(cfg.armed_window_seconds)} s window).",
                last_event="wake_armed",
                last_error="",
            )
            try:
                self.server.broadcast(
                    "wake_armed",
                    {"window_seconds": cfg.armed_window_seconds, "score": round(float(score), 3)},
                )
            except Exception:
                pass
            capture = ArmedCapture(window_seconds=cfg.armed_window_seconds)
            # A hard iteration cap so a dead stream can never wedge the floor.
            max_iterations = int((cfg.armed_window_seconds + 20.0) / 0.08)
            queue_ref = self._wake_queue
            for _ in range(max_iterations):
                if capture.state in ("captured", "expired"):
                    break
                if self.runtime_stop_event.is_set() or queue_ref is None:
                    break
                try:
                    frame = queue_ref.get(timeout=1.0)
                except Exception:
                    continue
                capture.feed(frame)
            audio = capture.result()
        finally:
            self.voice_session.release("wake")
        if audio is None or len(audio) < 1600:
            self._set_runtime_activity(
                "complete",
                source="wake",
                label="Disarmed",
                detail="Nothing was spoken.",
                last_event="wake_disarmed",
                last_error="",
            )
            return
        self._transcribe_wake(audio)

    def _transcribe_wake(self, audio: np.ndarray) -> None:
        """The wake outcome: the NORMAL pipeline, then preview or (opt-in) type.

        `action="preview"` (the default) journals the run (source `wake`),
        stores a one-shot preview token, and broadcasts `wake_preview` —
        it NEVER types. `action="type"` is the user's explicit opt-in and
        behaves like a hotkey run's tail.
        """
        cfg = self.config.wake_word
        with self.transcription_lock:
            try:
                self._set_runtime_activity(
                    "transcribing",
                    source="wake",
                    detail="Turning your speech into text…",
                    last_event="wake_transcribing",
                    last_error="",
                )
                text = self._ensure_transcriber_loaded().transcribe(audio)
                if not text:
                    self._set_runtime_activity(
                        "complete",
                        source="wake",
                        label="No speech",
                        detail="No speech detected.",
                        last_event="wake_no_speech",
                        last_error="",
                    )
                    return
                text = self.text_processor.process(text)
                final = self._maybe_run_dictation_pipeline(
                    text,
                    audio_duration_s=len(audio) / 16000.0,
                    transcribed_at=datetime.now(),
                    journal_source="wake",
                )
                if cfg.action == "type":
                    self._set_runtime_activity(
                        "typing",
                        source="wake",
                        detail="Typing into the active app.",
                        last_event="wake_typing",
                        last_error="",
                    )
                    self.typer.type_text(final)
                    self._set_runtime_activity(
                        "complete",
                        source="wake",
                        label="Typed",
                        detail=final[:120],
                        last_event="wake_typed",
                        last_error="",
                    )
                    return
                # The preview default: one active preview at a time.
                import uuid as uuid_mod

                token = uuid_mod.uuid4().hex
                self.wake_previews.clear()
                self.wake_previews[token] = {
                    "text": final,
                    "transcript": text,
                    "created_at": datetime.now().isoformat(),
                }
                try:
                    self.server.broadcast(
                        "wake_preview",
                        {"token": token, "transcript": text, "text": final},
                    )
                except Exception:
                    pass
                self._set_runtime_activity(
                    "complete",
                    source="wake",
                    label="Preview ready",
                    detail=final[:120],
                    last_event="wake_preview",
                    last_error="",
                )
            except Exception as exc:
                self._set_runtime_activity(
                    "error",
                    source="wake",
                    detail="Wake transcription failed.",
                    last_event="wake_failed",
                    last_error=f"{type(exc).__name__}: {exc}",
                )

    def consume_wake_preview(self, token: str) -> Optional[str]:
        """One-shot: return the stored preview text and burn the token."""
        entry = self.wake_previews.pop(str(token or ""), None)
        return None if entry is None else str(entry.get("text", ""))

    def _type_wake_preview(self, token: str) -> Optional[str]:
        """The Type-it route's handler: burn the token, type the stored text."""
        text = self.consume_wake_preview(token)
        if text is None:
            return None
        try:
            self.typer.type_text(text)
        except Exception as exc:
            self._set_runtime_activity(
                "error",
                source="wake",
                detail="Typing the wake preview failed.",
                last_event="wake_type_failed",
                last_error=f"{type(exc).__name__}: {exc}",
            )
            return None
        self._set_runtime_activity(
            "complete",
            source="wake",
            label="Typed",
            detail=text[:120],
            last_event="wake_preview_typed",
            last_error="",
        )
        return text
