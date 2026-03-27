"""Runtime controller and app wiring for HoldSpeak."""

from __future__ import annotations

import threading
import time
from typing import Optional

from .audio import AudioRecorder
from .config import Config
from .hotkey import HotkeyListener
from .logging_config import get_logger
from .meeting_session import IntelSnapshot, MeetingSession, TranscriptSegment
from .text_processor import TextProcessor
from .transcribe import Transcriber
from .tui import HoldSpeakApp
from .typer import TextTyper

log = get_logger("controller")


class HoldSpeakController:
    """Controller that wires TUI with audio/transcription pipeline."""

    def __init__(
        self,
        app: HoldSpeakApp,
        preloaded_transcriber: Optional[Transcriber] = None,
    ):
        log.info("Initializing HoldSpeakController")
        self.app = app
        self.config = app.config

        self._transcriber = preloaded_transcriber
        self._transcriber_model = preloaded_transcriber.model_name if preloaded_transcriber else None

        self.recorder = AudioRecorder(
            device=self.config.meeting.mic_device,
            on_level=self._on_audio_level,
        )
        self.text_processor = TextProcessor()
        self.typer: Optional[TextTyper] = None

        self._focused_hold_to_talk_key = getattr(self.app.ui_state, "focused_hold_to_talk_key", "v")
        self.app.set_focused_hold_to_talk_key(self._focused_hold_to_talk_key)

        self._text_injection_enabled = True
        self._text_injection_disabled_reason = ""
        try:
            self.typer = TextTyper()
        except Exception as exc:
            self.typer = None
            self._text_injection_enabled = False
            self._text_injection_disabled_reason = f"{type(exc).__name__}: {exc}"
        self.app.set_text_injection_status(self._text_injection_enabled, self._text_injection_disabled_reason)

        self.hotkey_listener: Optional[HotkeyListener] = None
        self._global_hotkey_enabled = True
        self._global_hotkey_disabled_reason = ""
        try:
            log.debug(f"Setting up hotkey listener with key: {self.config.hotkey.key}")
            self.hotkey_listener = HotkeyListener(
                on_press=self._on_hotkey_press,
                on_release=self._on_hotkey_release,
                hotkey=self.config.hotkey.key,
            )
        except Exception as exc:
            self.hotkey_listener = None
            self._global_hotkey_enabled = False
            self._global_hotkey_disabled_reason = f"{type(exc).__name__}: {exc}"
        self.app.set_global_hotkey_status(self._global_hotkey_enabled, self._global_hotkey_disabled_reason)

        self._transcription_lock = threading.Lock()

        self._meeting_session: Optional[MeetingSession] = None
        self._meeting_timer_thread: Optional[threading.Thread] = None
        self._meeting_stop_timer = threading.Event()
        self._meeting_stopping = False

        self._last_mic_level_update = 0.0
        self._last_system_level_update = 0.0
        self._level_update_interval = 0.066

        log.info(f"HoldSpeakController initialized (transcriber preloaded: {preloaded_transcriber is not None})")

    def _on_audio_level(self, level: float) -> None:
        self.app.set_audio_level(level)

    def _ensure_transcriber(self) -> Transcriber:
        model_name = self.app.config.model.name
        if self._transcriber is None or self._transcriber_model != model_name:
            self._transcriber = Transcriber(model_name=model_name)
            self._transcriber_model = model_name
        return self._transcriber

    def _on_hotkey_press(self) -> None:
        self.app.set_state("recording")
        self.app.set_audio_level(0.0)
        try:
            self.recorder.start_recording()
        except Exception as e:
            self.app.set_state("idle")
            self.app.notify(f"Recording failed: {e}", severity="error", timeout=3.0)

    def _on_hotkey_release(self) -> None:
        try:
            audio = self.recorder.stop_recording()
        except Exception as e:
            self.app.set_state("idle")
            self.app.notify(f"Recording error: {e}", severity="error", timeout=3.0)
            return

        if len(audio) < 1600:
            self.app.set_state("idle")
            self.app.notify("Recording too short", timeout=1.5)
            return

        try:
            import numpy as np

            audio_arr = np.asarray(audio, dtype=np.float32)
            max_abs = float(np.max(np.abs(audio_arr))) if audio_arr.size else 0.0
            rms = float(np.sqrt(np.mean(np.square(audio_arr)))) if audio_arr.size else 0.0
        except Exception:
            max_abs = 0.0
            rms = 0.0

        self.app.set_state("transcribing")
        self.app.set_audio_level(0.0)

        def transcribe_and_type():
            with self._transcription_lock:
                try:
                    transcriber = self._ensure_transcriber()
                    text = transcriber.transcribe(audio)
                    if text:
                        text = self.text_processor.process(text)
                        self.app.add_transcription(text)
                        if self._text_injection_enabled and self.typer is not None:
                            try:
                                self.typer.type_text(text)
                            except Exception as exc:
                                self._text_injection_enabled = False
                                self._text_injection_disabled_reason = f"{type(exc).__name__}: {exc}"
                                self.app.set_text_injection_status(
                                    self._text_injection_enabled,
                                    self._text_injection_disabled_reason,
                                )
                                copied = self.app.copy_to_clipboard(text)
                                if copied:
                                    self.app.notify("Typing unavailable; copied; paste manually", timeout=2.0)
                                else:
                                    self.app.notify("Typing unavailable; copy from history and paste manually", timeout=2.5)
                        else:
                            copied = self.app.copy_to_clipboard(text)
                            if copied:
                                self.app.notify("Copied; paste manually", timeout=2.0)
                            else:
                                self.app.notify("Copy from history and paste manually", timeout=2.5)
                    else:
                        if max_abs < 0.01 and rms < 0.003:
                            dev = self.config.meeting.mic_device or "default"
                            self.app.notify(
                                f"No speech detected (mic='{dev}', peak={max_abs:.4f}, rms={rms:.4f}). "
                                "Check input device/permissions in Settings.",
                                timeout=4.0,
                            )
                        else:
                            self.app.notify("No speech detected", timeout=1.5)
                except Exception as e:
                    self.app.notify(f"Transcription failed: {e}", severity="error", timeout=3.0)
                finally:
                    self.app.set_state("idle")

        threading.Thread(target=transcribe_and_type, daemon=True).start()

    def start(self) -> None:
        if self.hotkey_listener is None:
            self.app.set_global_hotkey_status(False, self._global_hotkey_disabled_reason or "unavailable")
            return
        try:
            self.hotkey_listener.start()
            self._global_hotkey_enabled = True
            self._global_hotkey_disabled_reason = ""
            self.app.set_global_hotkey_status(True, "")
        except Exception as exc:
            self._global_hotkey_enabled = False
            self._global_hotkey_disabled_reason = f"{type(exc).__name__}: {exc}"
            self.app.set_global_hotkey_status(False, self._global_hotkey_disabled_reason)

    def stop(self) -> None:
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()

    def update_hotkey(self, key: str) -> None:
        if self.hotkey_listener is not None:
            self.hotkey_listener.hotkey = key

    def start_voice_typing_recording(self) -> None:
        if not self.app.ui_state.is_idle:
            return
        if self._meeting_session is not None and self._meeting_session.is_active:
            return
        self._on_hotkey_press()

    def stop_voice_typing_recording(self) -> None:
        if not self.app.ui_state.is_recording:
            return
        self._on_hotkey_release()

    def toggle_meeting(self) -> None:
        if self._meeting_stopping:
            self.app.notify("Meeting is stopping...", timeout=1.0)
            return
        if self._meeting_session is not None and self._meeting_session.is_active:
            self._stop_meeting()
        else:
            self._start_meeting()

    def _start_meeting(self) -> None:
        if self._meeting_stopping:
            return
        transcriber = self._ensure_transcriber()

        self._meeting_session = MeetingSession(
            transcriber=transcriber,
            mic_label=self.config.meeting.mic_label,
            remote_label=self.config.meeting.remote_label,
            mic_device=self.config.meeting.mic_device,
            system_device=self.config.meeting.system_audio_device,
            on_segment=self._on_meeting_segment,
            on_mic_level=self._on_meeting_mic_level,
            on_system_level=self._on_meeting_system_level,
            on_intel=self._on_meeting_intel,
            intel_enabled=self.config.meeting.intel_enabled,
            intel_model_path=self.config.meeting.intel_realtime_model,
            web_enabled=self.config.meeting.web_enabled,
            diarization_enabled=self.config.meeting.diarization_enabled,
            diarize_mic=self.config.meeting.diarize_mic,
            cross_meeting_recognition=self.config.meeting.cross_meeting_recognition,
        )

        try:
            state = self._meeting_session.start()
            log.info(f"Meeting started: {state.id}")

            self.app.set_meeting_active(True)
            self.app.set_meeting_has_system_audio(self._meeting_session.has_system_audio)
            self.app.show_meeting_cockpit(
                title=state.title or "",
                has_system_audio=self._meeting_session.has_system_audio,
            )

            if state.web_url:
                self.app.set_meeting_web_url(state.web_url)
                self.app.notify(f"Meeting started - {state.web_url}", timeout=3.0, markup=False)
            else:
                self.app.notify("Meeting started", timeout=1.5)

            self._meeting_stop_timer.clear()
            self._meeting_timer_thread = threading.Thread(
                target=self._meeting_timer_loop,
                daemon=True,
            )
            self._meeting_timer_thread.start()

        except Exception as e:
            log.error(f"Failed to start meeting: {e}")
            self.app.notify(f"Meeting failed: {e}", severity="error", timeout=3.0, markup=False)
            self._meeting_session = None

    def _stop_meeting(self) -> None:
        if self._meeting_session is None:
            return

        self._meeting_stopping = True
        self._meeting_stop_timer.set()

        self.app.set_meeting_active(False)
        self.app.set_meeting_mic_level(0.0)
        self.app.set_meeting_system_level(0.0)
        self.app.hide_meeting_cockpit()
        self.app.notify("Stopping meeting...", timeout=1.0)

        session = self._meeting_session
        self._meeting_session = None

        def _do_stop() -> None:
            try:
                state = session.stop()
                log.info(f"Meeting stopped: {state.id}, {len(state.segments)} segments")

                try:
                    save_result = session.save()
                    if save_result.database_saved:
                        self.app.notify(f"Meeting saved: {len(state.segments)} segments", timeout=2.0)
                    elif save_result.json_saved:
                        self.app.notify(
                            "Meeting archived to JSON only; history DB save failed",
                            severity="warning",
                            timeout=3.0,
                        )
                    else:
                        self.app.notify(
                            "Meeting stop completed, but persistence failed",
                            severity="error",
                            timeout=3.0,
                        )
                except Exception as e:
                    log.error(f"Failed to save meeting: {e}")
                    self.app.notify(f"Save failed: {e}", severity="error", timeout=3.0)

            except Exception as e:
                log.error(f"Failed to stop meeting: {e}")
                self.app.notify(f"Stop failed: {e}", severity="error", timeout=3.0)
            finally:
                self._meeting_stopping = False

        threading.Thread(target=_do_stop, daemon=True).start()

    def _on_meeting_mic_level(self, level: float) -> None:
        now = time.monotonic()
        if now - self._last_mic_level_update < self._level_update_interval:
            return
        self._last_mic_level_update = now
        self.app.set_meeting_mic_level(level)

    def _on_meeting_system_level(self, level: float) -> None:
        now = time.monotonic()
        if now - self._last_system_level_update < self._level_update_interval:
            return
        self._last_system_level_update = now
        self.app.set_meeting_system_level(level)

    def _on_meeting_segment(self, segment: TranscriptSegment) -> None:
        if self._meeting_session:
            state = self._meeting_session.state
            if state:
                self.app.set_meeting_segment_count(len(state.segments))
        self.app.update_meeting_cockpit_segment(segment)

    def _on_meeting_intel(self, intel: IntelSnapshot) -> None:
        log.info(f"Intel update: {len(intel.topics)} topics, {len(intel.action_items)} actions")
        self.app.update_meeting_cockpit_intel(intel.topics, intel.action_items, intel.summary)
        if intel.topics:
            topics_str = ", ".join(intel.topics[:3])
            if len(intel.topics) > 3:
                topics_str += f" +{len(intel.topics) - 3} more"
            self.app.notify(f"Topics: {topics_str}", timeout=2.0)

    def _meeting_timer_loop(self) -> None:
        while not self._meeting_stop_timer.is_set():
            if self._meeting_session and self._meeting_session.state:
                duration = self._meeting_session.state.format_duration()
                self.app.set_meeting_duration(duration)
            self._meeting_stop_timer.wait(1.0)

    def add_meeting_bookmark(self) -> None:
        if self._meeting_session is None or not self._meeting_session.is_active:
            self.app.notify("No active meeting", timeout=1.5)
            return

        bookmark = self._meeting_session.add_bookmark()
        if bookmark:
            self.app.update_meeting_cockpit_bookmark(bookmark)
            self.app.notify(f"Bookmark at {bookmark.timestamp:.0f}s", timeout=1.0)

    def show_meeting_transcript(self) -> None:
        if self._meeting_session is None:
            self.app.notify("No meeting to show", timeout=1.5)
            return

        segments = self._meeting_session.get_transcript()
        bookmarks = self._meeting_session.get_bookmarks()
        self.app.show_meeting_transcript(segments, bookmarks)

    def show_meeting_metadata(self) -> None:
        if self._meeting_session is None or not self._meeting_session.is_active:
            self.app.notify("No active meeting", timeout=1.5)
            return

        title = self._meeting_session.get_title() or ""
        tags = self._meeting_session.get_tags()
        self.app.show_meeting_metadata(title, tags)

    def save_meeting_metadata(self, title: str, tags: list[str]) -> None:
        if self._meeting_session is None or not self._meeting_session.is_active:
            self.app.notify("No active meeting", timeout=1.5)
            return

        self._meeting_session.set_title(title)
        self._meeting_session.set_tags(tags)

        self.app.set_meeting_title(title)
        self.app.notify("Meeting details saved", timeout=1.5)

    def open_meeting_web(self) -> None:
        import webbrowser

        if self._meeting_session is None or not self._meeting_session.is_active:
            self.app.notify("No active meeting", timeout=1.5)
            return

        state = self._meeting_session.state
        if state and state.web_url:
            webbrowser.open(state.web_url)
            self.app.notify(f"Opened {state.web_url}", timeout=1.5)
        else:
            self.app.notify("Web dashboard not available", timeout=1.5)


class HoldSpeakAppWithController(HoldSpeakApp):
    """Extended app that manages the controller lifecycle."""

    def __init__(
        self,
        config: Optional[Config] = None,
        preloaded_transcriber: Optional[Transcriber] = None,
    ):
        super().__init__(config)
        self._controller: Optional[HoldSpeakController] = None
        self._preloaded_transcriber = preloaded_transcriber

    def on_mount(self) -> None:
        super().on_mount()
        self._controller = HoldSpeakController(self, self._preloaded_transcriber)
        self._controller.start()

        if self._preloaded_transcriber:
            self.set_state("idle")
        else:
            self.set_state("error")
            self.notify("Model failed to load - check logs", severity="error", timeout=5.0)

    def on_unmount(self) -> None:
        if self._controller:
            self._controller.stop()

    def on_settings_screen_applied(self, message) -> None:
        super().on_settings_screen_applied(message)
        if self._controller:
            self._controller.update_hotkey(self.config.hotkey.key)

    def on_meeting_toggle(self, message) -> None:
        if self._controller:
            self._controller.toggle_meeting()

    def on_meeting_bookmark(self, message) -> None:
        if self._controller:
            self._controller.add_meeting_bookmark()

    def on_meeting_show_transcript(self, message) -> None:
        if self._controller:
            self._controller.show_meeting_transcript()

    def on_meeting_edit_metadata(self, message) -> None:
        if self._controller:
            self._controller.show_meeting_metadata()

    def on_meeting_metadata_saved(self, message) -> None:
        if self._controller:
            self._controller.save_meeting_metadata(message.title, message.tags)

    def on_meeting_open_web(self, message) -> None:
        if self._controller:
            self._controller.open_meeting_web()

    def on_voice_typing_start_recording(self, _message) -> None:
        if self._controller:
            self._controller.start_voice_typing_recording()

    def on_voice_typing_stop_recording(self, _message) -> None:
        if self._controller:
            self._controller.stop_voice_typing_recording()
