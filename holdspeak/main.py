"""Main entry point for HoldSpeak voice typing on macOS and Linux."""

from __future__ import annotations

import os
import threading
import time
from typing import Optional

# Disable HuggingFace progress bars - they use multiprocessing locks
# that conflict with Textual's file descriptor handling in Python 3.13
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

from .config import Config
from .hotkey import HotkeyListener
from .audio import AudioRecorder
from .transcribe import Transcriber
from .typer import TextTyper
from .text_processor import TextProcessor
from .tui import HoldSpeakApp
from .meeting_session import MeetingSession, TranscriptSegment, IntelSnapshot
from .logging_config import setup_logging, get_logger, LOG_FILE

log = get_logger("main")


def _auto_migrate_json_meetings_if_needed() -> None:
    """Import legacy JSON meetings into SQLite if DB is empty."""
    try:
        from .db import get_database

        db = get_database()
        if db.list_meetings(limit=1):
            return

        # Only import if there are JSON meetings present.
        from .db_migration import list_json_meetings, migrate_json_meetings

        if not list_json_meetings():
            return

        migrated, skipped, errors = migrate_json_meetings()
        if migrated:
            log.info(f"Auto-migrated {migrated} JSON meeting(s) into SQLite (skipped={skipped}, errors={len(errors)})")
    except Exception as exc:
        # Never block the app on migration; meetings UI can still function (empty).
        log.debug(f"Auto-migration skipped/failed: {exc}", exc_info=True)


class HoldSpeakController:
    """Controller that wires TUI with audio/transcription pipeline.

    Runs hotkey listener in background, updates TUI from callbacks.
    """

    def __init__(
        self,
        app: HoldSpeakApp,
        preloaded_transcriber: Optional[Transcriber] = None,
    ):
        log.info("Initializing HoldSpeakController")
        self.app = app
        self.config = app.config

        # Use preloaded transcriber if provided, otherwise lazy-load
        self._transcriber = preloaded_transcriber
        self._transcriber_model = preloaded_transcriber.model_name if preloaded_transcriber else None

        self.recorder = AudioRecorder(
            device=self.config.meeting.mic_device,
            on_level=self._on_audio_level,
        )
        self.text_processor = TextProcessor()
        self.typer: Optional[TextTyper] = None

        # Focused-only control path (works without global hooks).
        self._focused_hold_to_talk_key = getattr(self.app.ui_state, "focused_hold_to_talk_key", "v")
        self.app.set_focused_hold_to_talk_key(self._focused_hold_to_talk_key)

        # Text injection (best-effort; commonly unavailable on Wayland/headless).
        self._text_injection_enabled = True
        self._text_injection_disabled_reason = ""
        try:
            self.typer = TextTyper()
        except Exception as exc:
            self.typer = None
            self._text_injection_enabled = False
            self._text_injection_disabled_reason = f"{type(exc).__name__}: {exc}"
        self.app.set_text_injection_status(self._text_injection_enabled, self._text_injection_disabled_reason)

        # Global hotkey listener (best-effort; may be unavailable on Wayland/headless).
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

        # Meeting session
        self._meeting_session: Optional[MeetingSession] = None
        self._meeting_timer_thread: Optional[threading.Thread] = None
        self._meeting_stop_timer = threading.Event()
        self._meeting_stopping = False  # Guard against starting while stopping

        # Throttle audio level UI updates (max ~15 FPS to avoid overwhelming Textual)
        self._last_mic_level_update = 0.0
        self._last_system_level_update = 0.0
        self._level_update_interval = 0.066  # ~15 FPS

        log.info(f"HoldSpeakController initialized (transcriber preloaded: {preloaded_transcriber is not None})")

    def _on_audio_level(self, level: float) -> None:
        """Called from audio thread with real-time level (0.0-1.0)."""
        self.app.set_audio_level(level)

    def _ensure_transcriber(self) -> Transcriber:
        """Lazy-load transcriber, reload if model changed."""
        model_name = self.app.config.model.name
        if self._transcriber is None or self._transcriber_model != model_name:
            self._transcriber = Transcriber(model_name=model_name)
            self._transcriber_model = model_name
        return self._transcriber

    def _on_hotkey_press(self) -> None:
        """Called when hotkey is pressed - start recording."""
        self.app.set_state("recording")
        self.app.set_audio_level(0.0)
        try:
            self.recorder.start_recording()
        except Exception as e:
            self.app.set_state("idle")
            self.app.notify(f"Recording failed: {e}", severity="error", timeout=3.0)

    def _on_hotkey_release(self) -> None:
        """Called when hotkey is released - stop recording and transcribe."""
        try:
            audio = self.recorder.stop_recording()
        except Exception as e:
            self.app.set_state("idle")
            self.app.notify(f"Recording error: {e}", severity="error", timeout=3.0)
            return

        if len(audio) < 1600:  # Less than 0.1s at 16kHz
            self.app.set_state("idle")
            self.app.notify("Recording too short", timeout=1.5)
            return

        # Capture basic audio stats for diagnostics when users get repeated empty transcriptions.
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

        # Transcribe in background thread
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
                        # Give actionable hints when the captured audio looks silent/near-silent.
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
        """Start the hotkey listener."""
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
        """Stop the hotkey listener."""
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()

    def update_hotkey(self, key: str) -> None:
        """Update the hotkey at runtime."""
        if self.hotkey_listener is not None:
            self.hotkey_listener.hotkey = key

    def start_voice_typing_recording(self) -> None:
        """Start recording via focused-only TUI control."""
        if not self.app.ui_state.is_idle:
            return
        if self._meeting_session is not None and self._meeting_session.is_active:
            return
        self._on_hotkey_press()

    def stop_voice_typing_recording(self) -> None:
        """Stop recording via focused-only TUI control."""
        if not self.app.ui_state.is_recording:
            return
        self._on_hotkey_release()

    # Meeting methods
    def toggle_meeting(self) -> None:
        """Toggle meeting recording on/off."""
        if self._meeting_stopping:
            self.app.notify("Meeting is stopping...", timeout=1.0)
            return
        if self._meeting_session is not None and self._meeting_session.is_active:
            self._stop_meeting()
        else:
            self._start_meeting()

    def _start_meeting(self) -> None:
        """Start a new meeting session."""
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
            # Default to the meeting cockpit during recording to avoid a "banner" UX.
            self.app.show_meeting_cockpit(
                title=state.title or "",
                has_system_audio=self._meeting_session.has_system_audio,
            )

            # Notify with web URL if available
            if state.web_url:
                self.app.set_meeting_web_url(state.web_url)
                self.app.notify(f"Meeting started - {state.web_url}", timeout=3.0, markup=False)
            else:
                self.app.notify("Meeting started", timeout=1.5)

            # Start timer thread
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
        """Stop the current meeting session."""
        if self._meeting_session is None:
            return

        # Set stopping flag to prevent re-entry
        self._meeting_stopping = True

        # Stop timer first
        self._meeting_stop_timer.set()

        # Hide meeting bar immediately (before blocking on session.stop())
        self.app.set_meeting_active(False)
        self.app.set_meeting_mic_level(0.0)
        self.app.set_meeting_system_level(0.0)
        self.app.hide_meeting_cockpit()
        self.app.notify("Stopping meeting...", timeout=1.0)

        # Capture session reference before clearing
        session = self._meeting_session
        self._meeting_session = None

        # Run the actual stop in a background thread to avoid blocking the UI
        # (the stop() method waits for threads to join, which can cause deadlock
        # if audio callbacks are trying to update the UI via call_from_thread)
        def _do_stop() -> None:
            try:
                state = session.stop()
                log.info(f"Meeting stopped: {state.id}, {len(state.segments)} segments")

                # Save meeting
                try:
                    session.save()
                    self.app.notify(f"Meeting saved: {len(state.segments)} segments", timeout=2.0)
                except Exception as e:
                    log.error(f"Failed to save meeting: {e}")

            except Exception as e:
                log.error(f"Failed to stop meeting: {e}")
                self.app.notify(f"Stop failed: {e}", severity="error", timeout=3.0)
            finally:
                # Clear stopping flag when done
                self._meeting_stopping = False

        threading.Thread(target=_do_stop, daemon=True).start()

    def _on_meeting_mic_level(self, level: float) -> None:
        """Called with mic audio level during meeting (throttled)."""
        now = time.monotonic()
        if now - self._last_mic_level_update < self._level_update_interval:
            return
        self._last_mic_level_update = now
        self.app.set_meeting_mic_level(level)

    def _on_meeting_system_level(self, level: float) -> None:
        """Called with system audio level during meeting (throttled)."""
        now = time.monotonic()
        if now - self._last_system_level_update < self._level_update_interval:
            return
        self._last_system_level_update = now
        self.app.set_meeting_system_level(level)

    def _on_meeting_segment(self, segment: TranscriptSegment) -> None:
        """Called when a new segment is transcribed."""
        if self._meeting_session:
            state = self._meeting_session.state
            if state:
                self.app.set_meeting_segment_count(len(state.segments))
        # Update cockpit transcript if it's open.
        self.app.update_meeting_cockpit_segment(segment)

    def _on_meeting_intel(self, intel: IntelSnapshot) -> None:
        """Called when new intel is generated."""
        log.info(f"Intel update: {len(intel.topics)} topics, {len(intel.action_items)} actions")
        self.app.update_meeting_cockpit_intel(intel.topics, intel.action_items, intel.summary)
        if intel.topics:
            topics_str = ", ".join(intel.topics[:3])
            if len(intel.topics) > 3:
                topics_str += f" +{len(intel.topics) - 3} more"
            self.app.notify(f"Topics: {topics_str}", timeout=2.0)

    def _meeting_timer_loop(self) -> None:
        """Update meeting duration display periodically."""
        while not self._meeting_stop_timer.is_set():
            if self._meeting_session and self._meeting_session.state:
                duration = self._meeting_session.state.format_duration()
                self.app.set_meeting_duration(duration)
            self._meeting_stop_timer.wait(1.0)

    def add_meeting_bookmark(self) -> None:
        """Add a bookmark to the current meeting."""
        if self._meeting_session is None or not self._meeting_session.is_active:
            self.app.notify("No active meeting", timeout=1.5)
            return

        bookmark = self._meeting_session.add_bookmark()
        if bookmark:
            self.app.update_meeting_cockpit_bookmark(bookmark)
            self.app.notify(f"Bookmark at {bookmark.timestamp:.0f}s", timeout=1.0)

    def show_meeting_transcript(self) -> None:
        """Show the current meeting transcript with bookmarks."""
        if self._meeting_session is None:
            self.app.notify("No meeting to show", timeout=1.5)
            return

        segments = self._meeting_session.get_transcript()
        bookmarks = self._meeting_session.get_bookmarks()
        self.app.show_meeting_transcript(segments, bookmarks)

    def show_meeting_metadata(self) -> None:
        """Show the meeting metadata editor."""
        if self._meeting_session is None or not self._meeting_session.is_active:
            self.app.notify("No active meeting", timeout=1.5)
            return

        title = self._meeting_session.get_title() or ""
        tags = self._meeting_session.get_tags()
        self.app.show_meeting_metadata(title, tags)

    def save_meeting_metadata(self, title: str, tags: list[str]) -> None:
        """Save meeting metadata from editor."""
        if self._meeting_session is None or not self._meeting_session.is_active:
            self.app.notify("No active meeting", timeout=1.5)
            return

        # Update session
        self._meeting_session.set_title(title)
        self._meeting_session.set_tags(tags)

        # Update UI
        self.app.set_meeting_title(title)
        self.app.notify("Meeting details saved", timeout=1.5)

    def open_meeting_web(self) -> None:
        """Open the meeting web dashboard in browser."""
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
        # Start controller after TUI is mounted
        self._controller = HoldSpeakController(self, self._preloaded_transcriber)
        self._controller.start()

        if self._preloaded_transcriber:
            # Model already loaded before TUI started
            self.set_state("idle")
        else:
            # No preloaded model - show error
            self.set_state("error")
            self.notify("Model failed to load - check logs", severity="error", timeout=5.0)

    def on_unmount(self) -> None:
        if self._controller:
            self._controller.stop()

    def on_settings_screen_applied(self, message) -> None:
        """Handle settings changes - update hotkey."""
        super().on_settings_screen_applied(message)
        if self._controller:
            self._controller.update_hotkey(self.config.hotkey.key)

    def on_meeting_toggle(self, message) -> None:
        """Handle meeting toggle request."""
        if self._controller:
            self._controller.toggle_meeting()

    def on_meeting_bookmark(self, message) -> None:
        """Handle meeting bookmark request."""
        if self._controller:
            self._controller.add_meeting_bookmark()

    def on_meeting_show_transcript(self, message) -> None:
        """Handle show transcript request."""
        if self._controller:
            self._controller.show_meeting_transcript()

    def on_meeting_edit_metadata(self, message) -> None:
        """Handle edit metadata request."""
        if self._controller:
            self._controller.show_meeting_metadata()

    def on_meeting_metadata_saved(self, message) -> None:
        """Handle metadata saved from modal."""
        if self._controller:
            self._controller.save_meeting_metadata(message.title, message.tags)

    def on_meeting_open_web(self, message) -> None:
        """Handle open web dashboard request."""
        if self._controller:
            self._controller.open_meeting_web()

    def on_voice_typing_start_recording(self, _message) -> None:
        if self._controller:
            self._controller.start_voice_typing_recording()

    def on_voice_typing_stop_recording(self, _message) -> None:
        if self._controller:
            self._controller.stop_voice_typing_recording()


def main():
    """Entry point for the holdspeak command."""
    import argparse

    parser = argparse.ArgumentParser(
        description="HoldSpeak - Voice typing for macOS and Linux. Hold, speak, release.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  holdspeak              # Launch TUI with default settings
  holdspeak menubar      # Launch menu bar mode (macOS only)
  holdspeak meeting      # Start in meeting mode (capture mic + system audio)
  holdspeak meeting --setup  # Check system audio setup
  holdspeak --no-tui     # Run in simple terminal mode (legacy)
  holdspeak --verbose    # Show debug output in terminal

Logs are written to: {LOG_FILE}
        """,
    )
    parser.add_argument(
        "--no-tui",
        action="store_true",
        help="Run without TUI (simple terminal output)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging to stderr",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command")

    # Meeting mode
    meeting_parser = subparsers.add_parser(
        "meeting",
        help="Start in meeting mode (capture mic + system audio)",
    )
    meeting_parser.add_argument(
        "--setup",
        action="store_true",
        help="Check system audio setup and show instructions",
    )
    meeting_parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List all audio devices",
    )
    meeting_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging to stderr",
    )

    # Menu bar mode
    menubar_parser = subparsers.add_parser(
        "menubar",
        help="Run as menu bar app (macOS only, no terminal window needed)",
    )
    menubar_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging to stderr",
    )

    # History subcommand
    history_parser = subparsers.add_parser(
        "history",
        help="Browse meeting history",
    )
    history_parser.add_argument(
        "meeting_id",
        nargs="?",
        help="Show details for specific meeting ID",
    )
    history_parser.add_argument(
        "--limit", "-n",
        type=int,
        default=20,
        help="Number of meetings to show (default: 20)",
    )
    history_parser.add_argument(
        "--search", "-s",
        help="Search transcripts for text",
    )
    history_parser.add_argument(
        "--from",
        dest="date_from",
        help="Filter meetings from date (YYYY-MM-DD)",
    )
    history_parser.add_argument(
        "--to",
        dest="date_to",
        help="Filter meetings to date (YYYY-MM-DD)",
    )
    history_parser.add_argument(
        "--export",
        choices=["json", "txt", "markdown"],
        help="Export meeting to file",
    )
    history_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show full transcript",
    )

    # Actions subcommand
    actions_parser = subparsers.add_parser(
        "actions",
        help="Manage action items across meetings",
    )
    actions_parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Include completed/dismissed items",
    )
    actions_parser.add_argument(
        "--owner", "-o",
        help="Filter by owner (Me, Remote, or name)",
    )
    actions_parser.add_argument(
        "--meeting", "-m",
        help="Filter by meeting ID",
    )
    actions_parser.add_argument(
        "--done", "-d",
        metavar="ID",
        help="Mark action item as done",
    )
    actions_parser.add_argument(
        "--dismiss",
        metavar="ID",
        help="Dismiss action item",
    )

    # Migrate subcommand
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Migrate JSON meetings to database",
    )
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without changing anything",
    )

    args = parser.parse_args()

    # Setup logging (always to file, optionally to stderr)
    setup_logging(verbose=args.verbose)

    # If the DB is empty but JSON meetings exist, import them automatically so
    # the Meetings Hub and `holdspeak history` work out of the box.
    if args.command in (None, "history", "actions"):
        _auto_migrate_json_meetings_if_needed()

    # Handle meeting subcommand
    if args.command == "meeting":
        log.info(f"HoldSpeak meeting mode starting (setup={args.setup}, list_devices={args.list_devices})")
        _run_meeting_mode(args)
        return

    # Handle menubar subcommand
    if args.command == "menubar":
        log.info("HoldSpeak menu bar mode starting")
        _run_menubar_mode()
        return

    # Handle history subcommand
    if args.command == "history":
        _run_history_command(args)
        return

    # Handle actions subcommand
    if args.command == "actions":
        _run_actions_command(args)
        return

    # Handle migrate subcommand
    if args.command == "migrate":
        _run_migrate_command(args)
        return

    log.info(f"HoldSpeak starting (verbose={args.verbose}, no_tui={args.no_tui})")

    if args.no_tui:
        # Legacy mode without TUI
        _run_simple_mode()
    else:
        # TUI mode - preload model BEFORE starting Textual to avoid
        # multiprocessing conflicts with file descriptors
        config = Config.load()
        transcriber = _preload_model_before_tui(config.model.name)
        app = HoldSpeakAppWithController(config=config, preloaded_transcriber=transcriber)
        app.run()


def _preload_model_before_tui(model_name: str) -> Optional[Transcriber]:
    """Load the Whisper model before starting Textual.

    This avoids multiprocessing/tqdm conflicts with Textual's fd handling.
    """
    import sys
    print(f"Loading Whisper model '{model_name}'... ", end="", flush=True)
    try:
        transcriber = Transcriber(model_name=model_name)
        print("ready!")
        return transcriber
    except Exception as e:
        print(f"failed: {e}", file=sys.stderr)
        log.error(f"Failed to preload model: {e}", exc_info=True)
        return None


def _run_menubar_mode():
    """Run in menu bar mode (no terminal needed)."""
    try:
        from .menubar import run_menubar
    except ImportError as e:
        import sys
        print(f"Menu bar mode requires rumps. Install with: uv pip install rumps", file=sys.stderr)
        print(f"Or: uv pip install -e '.[menubar]'", file=sys.stderr)
        log.error(f"Failed to import menubar: {e}")
        sys.exit(1)

    config = Config.load()
    run_menubar(config)


def _run_simple_mode():
    """Run in simple terminal mode without TUI (legacy)."""
    import sys
    import signal

    config = Config.load()

    print(f"🎙️  HoldSpeak initializing...")
    print(f"   Loading Whisper '{config.model.name}' model...")

    transcriber = Transcriber(model_name=config.model.name)
    recorder = AudioRecorder()
    try:
        typer: Optional[TextTyper] = TextTyper()
    except Exception:
        typer = None
    text_processor = TextProcessor()

    print("   ✓ Ready!")
    print()
    print(f"   Hold {config.hotkey.display} key and speak. Release to transcribe.")
    print("   Press Ctrl+C to quit.")
    print()

    transcription_lock = threading.Lock()

    def on_press():
        print("🔴 Recording...", end="", flush=True)
        recorder.start_recording()

    def on_release():
        try:
            audio = recorder.stop_recording()
        except Exception:
            print(" (error)")
            return

        if len(audio) < 1600:
            print(" (too short)")
            return

        print(" transcribing...", end="", flush=True)

        def transcribe():
            with transcription_lock:
                text = transcriber.transcribe(audio)
                if text:
                    text = text_processor.process(text)
                    print(f" ✓")
                    print(f"   → \"{text}\"")
                    if typer is not None:
                        try:
                            typer.type_text(text)
                        except Exception:
                            pass
                else:
                    print(" (no speech)")

        threading.Thread(target=transcribe, daemon=True).start()

    try:
        listener = HotkeyListener(
            on_press=on_press,
            on_release=on_release,
            hotkey=config.hotkey.key,
        )
    except Exception as exc:
        print(f"\nGlobal hotkey unavailable: {exc}")
        print("Try running the TUI (`holdspeak`) and use focused hold-to-talk.")
        return

    def signal_handler(sig, frame):
        print("\n\n👋 Goodbye!")
        listener.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    listener.start()
    listener.wait()


def _run_meeting_mode(args):
    """Run in meeting mode - capture mic + system audio."""
    import sys
    import signal
    import time

    from .audio_devices import check_blackhole_setup, list_devices_formatted
    from .meeting import MeetingRecorder, concatenate_chunks

    # Handle --list-devices
    if args.list_devices:
        print(list_devices_formatted())
        return

    # Handle --setup
    if args.setup:
        status = check_blackhole_setup()
        if status["installed"]:
            device = status["device"]
            if sys.platform.startswith("linux"):
                print("PulseAudio monitor source detected and ready!")
            else:
                print("BlackHole is installed and ready!")
            print(f"  Device: {device.name} (index {device.index})")
            print(f"\nYou can start meeting mode with: holdspeak meeting")
        else:
            print(status["setup_instructions"])
        return

    # Check system audio before starting
    status = check_blackhole_setup()
    if not status["installed"]:
        if sys.platform.startswith("linux"):
            print("WARNING: No PulseAudio monitor source found - system audio capture unavailable.")
        else:
            print("WARNING: BlackHole not detected - system audio capture unavailable.")
        print("Only your microphone will be recorded.")
        print("Run 'holdspeak meeting --setup' for installation instructions.\n")

    config = Config.load()

    print("Meeting Mode - Recording Setup")
    print("=" * 40)

    # Load transcriber
    print(f"Loading Whisper '{config.model.name}' model...")
    transcriber = Transcriber(model_name=config.model.name)
    print("Model ready!")
    print()

    # Initialize recorder
    recorder = MeetingRecorder(
        system_device=config.meeting.system_audio_device,
        on_mic_level=lambda l: None,  # Suppress for now
        on_system_level=lambda l: None,
    )

    mic_label = config.meeting.mic_label
    remote_label = config.meeting.remote_label

    print(f"Microphone: Recording (labeled as '{mic_label}')")
    if recorder.has_system_audio:
        print(f"System audio: Recording (labeled as '{remote_label}')")
    else:
        print("System audio: Not available")
    print()
    print("Press Ctrl+C to stop recording and transcribe.")
    print("-" * 40)

    # Start recording
    recorder.start()
    start_time = time.time()

    # Handle Ctrl+C
    stop_event = threading.Event()

    def signal_handler(sig, frame):
        print("\n\nStopping recording...")
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)

    # Show recording progress
    try:
        while not stop_event.is_set():
            elapsed = time.time() - start_time
            mins, secs = divmod(int(elapsed), 60)
            print(f"\rRecording: {mins:02d}:{secs:02d}", end="", flush=True)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

    # Stop and get chunks
    mic_chunks, system_chunks = recorder.stop()
    print()
    print()
    print("=" * 40)
    print("Processing recordings...")
    print()

    results = []

    # Transcribe mic audio
    if mic_chunks:
        print(f"Transcribing {len(mic_chunks)} mic chunks...")
        mic_audio = concatenate_chunks(mic_chunks)
        if len(mic_audio) > 1600:  # At least 0.1s
            mic_text = transcriber.transcribe(mic_audio)
            if mic_text:
                results.append((mic_label, mic_text))

    # Transcribe system audio
    if system_chunks:
        print(f"Transcribing {len(system_chunks)} system audio chunks...")
        system_audio = concatenate_chunks(system_chunks)
        if len(system_audio) > 1600:
            system_text = transcriber.transcribe(system_audio)
            if system_text:
                results.append((remote_label, system_text))

    # Display results
    print()
    print("=" * 40)
    print("MEETING TRANSCRIPT")
    print("=" * 40)
    print()

    if not results:
        print("No speech detected.")
    else:
        for speaker, text in results:
            print(f"{speaker}:")
            print(f"  {text}")
            print()

    # Export if configured
    if config.meeting.auto_export and results:
        export_path = _export_transcript(results, config.meeting.export_format)
        if export_path:
            print(f"Transcript saved to: {export_path}")


def _export_transcript(results: list[tuple[str, str]], format: str) -> Optional[str]:
    """Export transcript to file."""
    from pathlib import Path
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = {"markdown": "md", "txt": "txt", "json": "json"}.get(format, "txt")
    filename = f"meeting_{timestamp}.{ext}"
    filepath = Path.home() / "Documents" / filename

    try:
        if format == "json":
            import json
            data = [{"speaker": s, "text": t} for s, t in results]
            filepath.write_text(json.dumps(data, indent=2))
        elif format == "markdown":
            lines = ["# Meeting Transcript", "", f"*{datetime.now().strftime('%Y-%m-%d %H:%M')}*", ""]
            for speaker, text in results:
                lines.append(f"## {speaker}")
                lines.append("")
                lines.append(text)
                lines.append("")
            filepath.write_text("\n".join(lines))
        else:  # txt
            lines = []
            for speaker, text in results:
                lines.append(f"{speaker}: {text}")
            filepath.write_text("\n".join(lines))
        return str(filepath)
    except Exception as e:
        log.error(f"Failed to export transcript: {e}")
        return None


def _run_history_command(args) -> None:
    """Handle the 'history' subcommand."""
    import sys
    from datetime import datetime
    from .db import get_database

    db = get_database()

    # Search mode
    if args.search:
        results = db.search_transcripts(args.search, limit=args.limit)
        if not results:
            print(f"No matches found for: {args.search}")
            return

        print(f"Found {len(results)} matching segment(s):\n")
        for meeting_id, segment in results:
            # Truncate text for display
            display_text = segment.text[:100] + "..." if len(segment.text) > 100 else segment.text
            print(f"  [{meeting_id[:8]}] {segment.speaker} @ {segment.start_time:.0f}s: {display_text}")
        return

    # Parse date filters
    date_from = None
    date_to = None
    if args.date_from:
        try:
            date_from = datetime.strptime(args.date_from, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date format: {args.date_from} (use YYYY-MM-DD)", file=sys.stderr)
            sys.exit(1)
    if args.date_to:
        try:
            date_to = datetime.strptime(args.date_to, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date format: {args.date_to} (use YYYY-MM-DD)", file=sys.stderr)
            sys.exit(1)

    # Specific meeting detail
    if args.meeting_id:
        meeting = db.get_meeting(args.meeting_id)
        if not meeting:
            print(f"Meeting not found: {args.meeting_id}", file=sys.stderr)
            sys.exit(1)

        # Export mode
        if args.export:
            filepath = _export_meeting(meeting, args.export)
            if filepath:
                print(f"Exported to: {filepath}")
            else:
                print("Export failed", file=sys.stderr)
                sys.exit(1)
            return

        # Display meeting details
        _display_meeting_detail(meeting, verbose=args.verbose)
        return

    # List meetings
    meetings = db.list_meetings(
        limit=args.limit,
        date_from=date_from,
        date_to=date_to,
    )

    if not meetings:
        print("No meetings found.")
        return

    print(f"{'ID':<12} {'Date':<12} {'Duration':<10} {'Segments':<10} {'Title'}")
    print("-" * 70)

    for m in meetings:
        title = m.title or "(untitled)"
        if len(title) > 30:
            title = title[:27] + "..."
        date_str = m.started_at.strftime("%Y-%m-%d")
        duration = _format_duration_simple(m.duration_seconds) if m.duration_seconds else "--:--"
        print(f"{m.id[:12]:<12} {date_str:<12} {duration:<10} {m.segment_count:<10} {title}")


def _display_meeting_detail(meeting, verbose: bool = False) -> None:
    """Display detailed meeting information."""
    state = meeting  # MeetingState object

    print(f"Meeting: {state.id}")
    print(f"  Title: {state.title or '(untitled)'}")
    print(f"  Started: {state.started_at.strftime('%Y-%m-%d %H:%M')}")
    if state.ended_at:
        print(f"  Ended: {state.ended_at.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Duration: {state.format_duration()}")
    print(f"  Segments: {len(state.segments)}")

    if state.tags:
        print(f"  Tags: {', '.join(state.tags)}")

    if state.bookmarks:
        print(f"\nBookmarks ({len(state.bookmarks)}):")
        for b in state.bookmarks:
            label = f" - {b.label}" if b.label else ""
            print(f"  [{b.timestamp:.0f}s]{label}")

    if state.intel:
        intel = state.intel
        if intel.topics:
            print(f"\nTopics: {', '.join(intel.topics)}")
        if intel.action_items:
            print(f"\nAction Items ({len(intel.action_items)}):")
            for item in intel.action_items:
                status = item.get("status", "pending")
                status_icon = {"done": "[x]", "dismissed": "[-]", "pending": "[ ]"}.get(status, "[ ]")
                owner = item.get("owner", "")
                owner_str = f" @{owner}" if owner else ""
                print(f"  {status_icon} {item.get('task', '')}{owner_str}")
        if intel.summary:
            print(f"\nSummary:\n  {intel.summary}")

    if verbose and state.segments:
        print(f"\nTranscript:")
        print("-" * 40)
        for seg in state.segments:
            timestamp = f"[{seg.start_time:.0f}s]"
            bookmark = " *" if seg.is_bookmarked else ""
            print(f"{timestamp} {seg.speaker}: {seg.text}{bookmark}")


def _export_meeting(meeting, format: str) -> Optional[str]:
    """Export a meeting to file."""
    import json
    from pathlib import Path
    from datetime import datetime

    state = meeting
    timestamp = state.started_at.strftime("%Y%m%d_%H%M%S")
    ext = {"markdown": "md", "txt": "txt", "json": "json"}.get(format, "txt")
    filename = f"meeting_{state.id[:8]}_{timestamp}.{ext}"
    filepath = Path.home() / "Documents" / filename

    try:
        if format == "json":
            data = state.to_dict()
            filepath.write_text(json.dumps(data, indent=2))
        elif format == "markdown":
            lines = [
                f"# {state.title or 'Meeting Transcript'}",
                "",
                f"**Date:** {state.started_at.strftime('%Y-%m-%d %H:%M')}",
                f"**Duration:** {state.format_duration()}",
                "",
            ]
            if state.intel and state.intel.summary:
                lines.extend(["## Summary", "", state.intel.summary, ""])
            if state.intel and state.intel.topics:
                lines.extend(["## Topics", "", ", ".join(state.intel.topics), ""])
            if state.intel and state.intel.action_items:
                lines.append("## Action Items")
                lines.append("")
                for item in state.intel.action_items:
                    status = item.get("status", "pending")
                    check = "x" if status == "done" else " "
                    owner = item.get("owner", "")
                    owner_str = f" (@{owner})" if owner else ""
                    lines.append(f"- [{check}] {item.get('task', '')}{owner_str}")
                lines.append("")
            lines.append("## Transcript")
            lines.append("")
            for seg in state.segments:
                bookmark = " **[BOOKMARK]**" if seg.is_bookmarked else ""
                lines.append(f"**{seg.speaker}** [{seg.start_time:.0f}s]: {seg.text}{bookmark}")
                lines.append("")
            filepath.write_text("\n".join(lines))
        else:  # txt
            lines = [
                f"Meeting: {state.title or state.id}",
                f"Date: {state.started_at.strftime('%Y-%m-%d %H:%M')}",
                f"Duration: {state.format_duration()}",
                "",
                "Transcript:",
                "-" * 40,
            ]
            for seg in state.segments:
                bookmark = " *" if seg.is_bookmarked else ""
                lines.append(f"[{seg.start_time:.0f}s] {seg.speaker}: {seg.text}{bookmark}")
            filepath.write_text("\n".join(lines))
        return str(filepath)
    except Exception as e:
        log.error(f"Failed to export meeting: {e}")
        return None


def _run_actions_command(args) -> None:
    """Handle the 'actions' subcommand."""
    import sys
    from .db import get_database

    db = get_database()

    # Mark as done
    if args.done:
        success = db.update_action_item_status(args.done, "done")
        if success:
            print(f"Marked as done: {args.done}")
        else:
            print(f"Action item not found: {args.done}", file=sys.stderr)
            sys.exit(1)
        return

    # Dismiss
    if args.dismiss:
        success = db.update_action_item_status(args.dismiss, "dismissed")
        if success:
            print(f"Dismissed: {args.dismiss}")
        else:
            print(f"Action item not found: {args.dismiss}", file=sys.stderr)
            sys.exit(1)
        return

    # List action items
    include_completed = args.all
    items = db.list_action_items(
        include_completed=include_completed,
        owner=args.owner,
        meeting_id=args.meeting,
    )

    if not items:
        if args.all:
            print("No action items found.")
        else:
            print("No pending action items. Use --all to include completed/dismissed.")
        return

    print(f"{'ID':<12} {'Status':<10} {'Owner':<10} {'Meeting':<10} Task")
    print("-" * 80)

    for item in items:
        status_icon = {
            "done": "[x]",
            "dismissed": "[-]",
            "pending": "[ ]",
        }.get(item.status, "[ ]")
        owner = item.owner or "-"
        if len(owner) > 8:
            owner = owner[:7] + "."
        task = item.task
        if len(task) > 40:
            task = task[:37] + "..."
        meeting_short = item.meeting_id[:8] if item.meeting_id else "-"
        print(f"{item.id[:12]:<12} {status_icon:<10} {owner:<10} {meeting_short:<10} {task}")


def _run_migrate_command(args) -> None:
    """Handle the 'migrate' subcommand."""
    from .db_migration import migrate_json_meetings, list_json_meetings

    if args.dry_run:
        # Show what would be migrated
        json_meetings = list_json_meetings()
        if not json_meetings:
            print("No JSON meeting files found to migrate.")
            return

        print(f"Found {len(json_meetings)} JSON meeting file(s):\n")
        for path, meeting_id, started_at in json_meetings:
            date_str = started_at.strftime("%Y-%m-%d %H:%M")
            print(f"  {meeting_id[:12]} ({date_str}) - {path.name}")

        print(f"\nRun 'holdspeak migrate' (without --dry-run) to import these.")
        return

    # Run migration
    print("Migrating JSON meetings to database...")
    migrated, skipped, errors = migrate_json_meetings()

    print(f"\nMigration complete:")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped (already exist): {skipped}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for err in errors:
            print(f"    - {err}")


def _format_duration_simple(seconds: Optional[float]) -> str:
    """Format duration as MM:SS or HH:MM:SS."""
    if seconds is None:
        return "--:--"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    mins, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


if __name__ == "__main__":
    main()
