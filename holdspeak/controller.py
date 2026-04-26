"""Runtime controller and app wiring for HoldSpeak."""

from __future__ import annotations

import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .audio import AudioRecorder
from .config import Config
from .hotkey import HotkeyListener
from .intel_queue import IntelQueueWorker, start_intel_queue_worker
from .logging_config import get_logger
from .meeting_session import IntelSnapshot, MeetingSession, TranscriptSegment
from .text_processor import TextProcessor
from .transcribe import Transcriber
from .tui import HoldSpeakApp
from .typer import TextTyper

log = get_logger("controller")
dictation_log = get_logger("dictation.pipeline")

# Audio is captured at 16 kHz mono throughout HoldSpeak; expressing
# this here keeps the controller from needing to know about the
# transcriber's internals when it stamps `audio_duration_s` on the
# DIR-01 `Utterance`.
_AUDIO_SAMPLE_RATE_HZ = 16000

# Global blocks file location per spec §8.1. Kept at module scope so
# the dictation pipeline builder can be exercised without spinning
# up a controller in tests.
_GLOBAL_BLOCKS_PATH = Path.home() / ".config" / "holdspeak" / "blocks.yaml"


class HoldSpeakController:
    """Controller that wires TUI with audio/transcription pipeline."""

    def __init__(
        self,
        app: HoldSpeakApp,
        preloaded_transcriber: Optional[Transcriber] = None,
    ):
        log.info("Initializing HoldSpeakController")
        self.app = app
        config = self.app.config

        self._transcriber = preloaded_transcriber
        self._transcriber_model = preloaded_transcriber.model_name if preloaded_transcriber else None

        self.recorder = AudioRecorder(
            device=config.meeting.mic_device,
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
            log.debug(f"Setting up hotkey listener with key: {config.hotkey.key}")
            self.hotkey_listener = HotkeyListener(
                on_press=self._on_hotkey_press,
                on_release=self._on_hotkey_release,
                hotkey=config.hotkey.key,
            )
        except Exception as exc:
            self.hotkey_listener = None
            self._global_hotkey_enabled = False
            self._global_hotkey_disabled_reason = f"{type(exc).__name__}: {exc}"
        self.app.set_global_hotkey_status(self._global_hotkey_enabled, self._global_hotkey_disabled_reason)

        self._transcription_lock = threading.Lock()

        # DIR-01 dictation pipeline cache. Built lazily on the first
        # utterance when `dictation.pipeline.enabled` is true; stays
        # None when disabled so no module under
        # `holdspeak.plugins.dictation.*` is ever imported on the
        # default path (DIR-C-001 byte-identical guarantee).
        self._dictation_pipeline: Optional[Any] = None
        self._dictation_pipeline_failed: bool = False

        self._meeting_session: Optional[MeetingSession] = None
        self._meeting_timer_thread: Optional[threading.Thread] = None
        self._meeting_stop_thread: Optional[threading.Thread] = None
        self._meeting_stop_timer = threading.Event()
        self._meeting_stopping = False
        self._intel_queue_worker: Optional[IntelQueueWorker] = None

        self._last_mic_level_update = 0.0
        self._last_system_level_update = 0.0
        self._level_update_interval = 0.066

        self._sync_intel_queue_worker()

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
                        text = self._maybe_run_dictation_pipeline(
                            text,
                            audio_duration_s=len(audio) / _AUDIO_SAMPLE_RATE_HZ,
                            transcribed_at=datetime.now(),
                        )
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
                            dev = self.app.config.meeting.mic_device or "default"
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

    def stop(self, *, finalize_active_meeting: bool = False, notify: bool = False) -> None:
        if finalize_active_meeting:
            self._finalize_active_meeting_for_shutdown(notify=notify)
        if self._intel_queue_worker is not None:
            self._intel_queue_worker.stop(timeout=5.0)
            self._intel_queue_worker = None
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()

    def update_hotkey(self, key: str) -> None:
        if self.hotkey_listener is not None:
            self.hotkey_listener.hotkey = key

    def _maybe_run_dictation_pipeline(
        self,
        text: str,
        *,
        audio_duration_s: float,
        transcribed_at: datetime,
    ) -> str:
        """Run the DIR-01 dictation pipeline if enabled, else passthrough.

        Returns the (possibly enriched) text. Any unexpected failure
        falls back to the input text so the live voice-typing path
        keeps working — this is defense in depth on top of the
        executor's own per-stage error isolation (DIR-F-003).
        """
        cfg = self.app.config.dictation
        if not cfg.pipeline.enabled:
            return text

        pipeline = self._get_dictation_pipeline()
        if pipeline is None:
            return text

        try:
            from holdspeak.plugins.dictation.contracts import Utterance

            utt = Utterance(
                raw_text=text,
                audio_duration_s=audio_duration_s,
                transcribed_at=transcribed_at,
                project=None,
            )
            run = pipeline.run(utt)
            return run.final_text
        except Exception as exc:
            log.warning(f"Dictation pipeline raised; falling back to processed text: {exc}")
            return text

    def _get_dictation_pipeline(self) -> Optional[Any]:
        """Return the cached pipeline or build it on first use."""
        if self._dictation_pipeline is not None:
            return self._dictation_pipeline
        if self._dictation_pipeline_failed:
            return None
        try:
            self._dictation_pipeline = self._build_dictation_pipeline()
        except Exception as exc:
            self._dictation_pipeline_failed = True
            self._dictation_pipeline = None
            log.warning(f"Dictation pipeline build failed; staying disabled this session: {exc}")
            return None
        return self._dictation_pipeline

    def _build_dictation_pipeline(self) -> Any:
        """Lazy-construct the dictation pipeline.

        All `holdspeak.plugins.dictation.*` imports happen inside this
        method so the disabled path never touches the dictation
        modules (DIR-C-001 byte-identical guarantee). Assembly logic
        lives in `dictation.assembly` so the CLI (HS-1-08) and doctor
        (HS-1-09) share the same builder.
        """
        from holdspeak.plugins.dictation.assembly import build_pipeline

        result = build_pipeline(
            self.app.config.dictation,
            on_run=self._emit_pipeline_run,
            global_blocks_path=_GLOBAL_BLOCKS_PATH,
        )
        if result.runtime_status != "loaded":
            log.warning(
                f"Dictation runtime unavailable ({result.runtime_detail}); "
                "pipeline will run with intent-router skipped."
            )
        return result.pipeline

    def _emit_pipeline_run(self, run: Any) -> None:
        """DIR-O-001: structured log line for one pipeline run."""
        intent = run.intent
        dictation_log.info(
            "dictation_pipeline_run",
            extra={
                "stage_ids": [r.stage_id for r in run.stage_results],
                "elapsed_ms": {r.stage_id: r.elapsed_ms for r in run.stage_results},
                "total_elapsed_ms": run.total_elapsed_ms,
                "intent_matched": bool(intent and intent.matched),
                "intent_block_id": intent.block_id if intent else None,
                "warnings": run.warnings,
                "short_circuited": run.short_circuited,
            },
        )

    def apply_runtime_config(self) -> None:
        """Apply latest app config to long-lived runtime components."""
        config = self.app.config
        self.recorder.device = config.meeting.mic_device
        self.update_hotkey(config.hotkey.key)
        self._sync_intel_queue_worker()
        # Drop the cached pipeline so a `dictation.*` config edit
        # (e.g. enabling the feature, swapping backend, pointing at
        # a different blocks file) takes effect on the next utterance.
        self._dictation_pipeline = None
        self._dictation_pipeline_failed = False

    def _sync_intel_queue_worker(self) -> None:
        """Ensure deferred-intel worker matches current config."""
        config = self.app.config.meeting
        should_run = config.intel_enabled and config.intel_deferred_enabled
        desired_model = config.intel_realtime_model
        desired_provider = config.intel_provider
        desired_cloud_model = config.intel_cloud_model
        desired_cloud_api_key_env = config.intel_cloud_api_key_env
        desired_cloud_base_url = config.intel_cloud_base_url
        desired_cloud_reasoning_effort = config.intel_cloud_reasoning_effort
        desired_cloud_store = config.intel_cloud_store
        desired_retry_base_seconds = config.intel_retry_base_seconds
        desired_retry_max_seconds = config.intel_retry_max_seconds
        desired_retry_max_attempts = config.intel_retry_max_attempts
        desired_failure_alert_percent = config.intel_retry_failure_alert_percent
        desired_failure_hysteresis_minutes = config.intel_retry_failure_hysteresis_minutes
        desired_failure_webhook_url = config.intel_retry_failure_webhook_url
        desired_failure_webhook_header_name = config.intel_retry_failure_webhook_header_name
        desired_failure_webhook_header_value = config.intel_retry_failure_webhook_header_value
        desired_poll = max(5.0, float(config.intel_queue_poll_seconds))

        worker = self._intel_queue_worker
        if not should_run:
            if worker is not None:
                worker.stop(timeout=5.0)
                self._intel_queue_worker = None
            return

        if (
            worker is not None
            and worker.is_alive()
            and worker.model_path == desired_model
            and worker.provider == desired_provider
            and worker.cloud_model == desired_cloud_model
            and worker.cloud_api_key_env == desired_cloud_api_key_env
            and worker.cloud_base_url == desired_cloud_base_url
            and worker.cloud_reasoning_effort == desired_cloud_reasoning_effort
            and worker.cloud_store == desired_cloud_store
            and worker.retry_base_seconds == desired_retry_base_seconds
            and worker.retry_max_seconds == desired_retry_max_seconds
            and worker.retry_max_attempts == desired_retry_max_attempts
            and worker.failure_alert_percent == desired_failure_alert_percent
            and worker.failure_alert_hysteresis_seconds == max(0.0, float(desired_failure_hysteresis_minutes) * 60.0)
            and worker.failure_alert_webhook_url == ((desired_failure_webhook_url or "").strip() or None)
            and worker.failure_alert_webhook_header_name == ((desired_failure_webhook_header_name or "").strip() or None)
            and worker.failure_alert_webhook_header_value == ((desired_failure_webhook_header_value or "").strip() or None)
            and worker.poll_seconds == desired_poll
        ):
            return

        if worker is not None:
            worker.stop(timeout=5.0)

        self._intel_queue_worker = start_intel_queue_worker(
            model_path=desired_model,
            provider=desired_provider,
            cloud_model=desired_cloud_model,
            cloud_api_key_env=desired_cloud_api_key_env,
            cloud_base_url=desired_cloud_base_url,
            cloud_reasoning_effort=desired_cloud_reasoning_effort,
            cloud_store=desired_cloud_store,
            retry_base_seconds=desired_retry_base_seconds,
            retry_max_seconds=desired_retry_max_seconds,
            retry_max_attempts=desired_retry_max_attempts,
            failure_alert_percent=desired_failure_alert_percent,
            failure_alert_hysteresis_minutes=desired_failure_hysteresis_minutes,
            failure_alert_webhook_url=desired_failure_webhook_url,
            failure_alert_webhook_header_name=desired_failure_webhook_header_name,
            failure_alert_webhook_header_value=desired_failure_webhook_header_value,
            poll_seconds=desired_poll,
        )

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
        config = self.app.config

        self._meeting_session = MeetingSession(
            transcriber=transcriber,
            mic_label=config.meeting.mic_label,
            remote_label=config.meeting.remote_label,
            mic_device=config.meeting.mic_device,
            system_device=config.meeting.system_audio_device,
            on_segment=self._on_meeting_segment,
            on_mic_level=self._on_meeting_mic_level,
            on_system_level=self._on_meeting_system_level,
            on_intel=self._on_meeting_intel,
            on_settings_applied=self._on_web_settings_applied,
            intel_enabled=config.meeting.intel_enabled,
            intel_model_path=config.meeting.intel_realtime_model,
            intel_provider=config.meeting.intel_provider,
            intel_cloud_model=config.meeting.intel_cloud_model,
            intel_cloud_api_key_env=config.meeting.intel_cloud_api_key_env,
            intel_cloud_base_url=config.meeting.intel_cloud_base_url,
            intel_cloud_reasoning_effort=config.meeting.intel_cloud_reasoning_effort,
            intel_cloud_store=config.meeting.intel_cloud_store,
            intel_deferred_enabled=config.meeting.intel_deferred_enabled,
            web_enabled=config.meeting.web_enabled,
            diarization_enabled=config.meeting.diarization_enabled,
            diarize_mic=config.meeting.diarize_mic,
            cross_meeting_recognition=config.meeting.cross_meeting_recognition,
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

    def _on_web_settings_applied(self, updated_config: Config) -> None:
        """Apply settings saved from the web UI at runtime."""
        try:
            self.app.config = updated_config
            self.app.update_hotkey_display(updated_config.hotkey.display)
            self.apply_runtime_config()
            self.app.notify("Settings saved from web UI", timeout=1.8)
        except Exception as exc:
            log.error(f"Failed to apply web settings: {exc}")

    def _stop_meeting(self) -> None:
        session = self._prepare_meeting_stop(notify=True)
        if session is None:
            return

        def _do_stop() -> None:
            self._finalize_meeting_stop(session, notify=True)

        stop_thread = threading.Thread(target=_do_stop, daemon=True)
        self._meeting_stop_thread = stop_thread
        stop_thread.start()

    def _prepare_meeting_stop(self, *, notify: bool) -> Optional[MeetingSession]:
        if self._meeting_session is None:
            return None

        self._meeting_stopping = True
        self._meeting_stop_timer.set()

        self.app.set_meeting_active(False)
        self.app.set_meeting_mic_level(0.0)
        self.app.set_meeting_system_level(0.0)
        self.app.hide_meeting_cockpit()
        if notify:
            self.app.notify("Stopping meeting...", timeout=1.0)

        session = self._meeting_session
        self._meeting_session = None
        return session

    def _finalize_meeting_stop(self, session: MeetingSession, *, notify: bool) -> None:
        try:
            try:
                state = session.stop()
                log.info(f"Meeting stopped: {state.id}, {len(state.segments)} segments")
            except Exception as e:
                log.error(f"Failed to stop meeting: {e}")
                if notify:
                    self.app.notify(f"Stop failed: {e}", severity="error", timeout=3.0)
                return

            try:
                save_result = session.save()
            except Exception as e:
                log.error(f"Failed to save meeting: {e}")
                if notify:
                    self.app.notify(f"Save failed: {e}", severity="error", timeout=3.0)
                return

            if not notify:
                return

            if save_result.database_saved:
                if save_result.intel_job_enqueued:
                    self.app.notify(
                        "Meeting saved; intelligence queued for later processing",
                        timeout=3.0,
                    )
                else:
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
        finally:
            self._meeting_stopping = False
            if threading.current_thread() is self._meeting_stop_thread:
                self._meeting_stop_thread = None

    def _finalize_active_meeting_for_shutdown(self, *, notify: bool) -> None:
        if self._meeting_session is not None and self._meeting_session.is_active and not self._meeting_stopping:
            session = self._prepare_meeting_stop(notify=notify)
            if session is not None:
                self._finalize_meeting_stop(session, notify=notify)

        stop_thread = self._meeting_stop_thread
        if stop_thread is not None and stop_thread.is_alive() and stop_thread is not threading.current_thread():
            stop_thread.join(timeout=30.0)

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
            self._controller.stop(finalize_active_meeting=True, notify=False)

    def on_settings_screen_applied(self, message) -> None:
        super().on_settings_screen_applied(message)
        if self._controller:
            self._controller.apply_runtime_config()

    def request_quit(self) -> None:
        if self._controller:
            self._controller.stop(finalize_active_meeting=True, notify=False)
        self.exit()

    async def action_quit(self) -> None:
        self.request_quit()

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
