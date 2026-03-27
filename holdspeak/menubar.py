"""Menu bar application for HoldSpeak.

Provides a macOS menu bar interface for voice-to-text transcription
without needing a terminal window.
"""

from __future__ import annotations

import os
import subprocess
import threading
import webbrowser
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Callable

# Disable HuggingFace progress bars
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

try:
    import rumps
except ImportError:
    raise ImportError(
        "rumps is required for menu bar mode. Install with: uv pip install rumps"
    )

from .config import Config, KEY_DISPLAY
from .hotkey import HotkeyListener
from .audio import AudioRecorder
from .transcribe import Transcriber
from .typer import TextTyper
from .text_processor import TextProcessor
from .logging_config import get_logger

log = get_logger("menubar")


# Unicode symbols for status (no icon files needed)
ICON_IDLE = "mic"  # Will use title instead
ICON_RECORDING = "mic.fill"  # Will use title instead
ICON_PROCESSING = "mic.badge.ellipsis"  # Will use title instead

# Title text for menu bar
TITLE_IDLE = "HoldSpeak"
TITLE_RECORDING = "Recording..."
TITLE_PROCESSING = "Processing..."
TITLE_MEETING = "Meeting"


@dataclass
class RecentTranscription:
    """A recent transcription entry."""
    text: str
    timestamp: datetime

    @property
    def preview(self) -> str:
        """Short preview for menu display."""
        text = self.text.strip()
        if len(text) > 40:
            return text[:40] + "..."
        return text

    @property
    def time_str(self) -> str:
        """Formatted time string."""
        return self.timestamp.strftime("%H:%M")


class HoldSpeakMenuBar(rumps.App):
    """Menu bar application for HoldSpeak voice typing.

    Provides:
    - Status indicator in menu bar
    - Hotkey-triggered recording (hold to record)
    - Manual recording via menu
    - Recent transcriptions list
    - Meeting mode submenu
    - Settings access
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize the menu bar app.

        Args:
            config: Configuration object. Loads from file if None.
        """
        super().__init__(
            name="HoldSpeak",
            title=TITLE_IDLE,
            quit_button=None,  # We'll add our own quit
        )

        self.config = config or Config.load()
        self._state = "loading"

        # Transcription components (lazy loaded)
        self._transcriber: Optional[Transcriber] = None
        self._transcriber_model: Optional[str] = None
        self._recorder: Optional[AudioRecorder] = None
        self._typer: Optional[TextTyper] = None
        self._text_processor: TextProcessor = TextProcessor()
        self._hotkey_listener: Optional[HotkeyListener] = None

        # State
        self._is_recording = False
        self._transcription_lock = threading.Lock()
        self._recent: deque[RecentTranscription] = deque(maxlen=10)

        # Meeting state
        self._meeting_session = None
        self._meeting_timer_thread: Optional[threading.Thread] = None
        self._meeting_stop_timer = threading.Event()

        # Build initial menu
        self._build_menu()

        log.info("HoldSpeakMenuBar initialized")

    def _build_menu(self) -> None:
        """Build the menu structure."""
        # Status item (non-clickable)
        self._status_item = rumps.MenuItem(
            "Status: Loading...",
            callback=None,
        )

        # Recording button
        hotkey_display = KEY_DISPLAY.get(self.config.hotkey.key, self.config.hotkey.key)
        self._record_item = rumps.MenuItem(
            f"Start Recording ({hotkey_display})",
            callback=self._toggle_recording,
        )

        # Recent transcriptions submenu
        self._recent_menu = rumps.MenuItem("Recent")
        self._recent_menu.add(rumps.MenuItem("No recent transcriptions"))

        # Meeting mode submenu
        self._meeting_menu = rumps.MenuItem("Meeting Mode")
        self._meeting_start_item = rumps.MenuItem(
            "Start Meeting",
            callback=self._start_meeting,
        )
        self._meeting_dashboard_item = rumps.MenuItem(
            "Open Dashboard",
            callback=self._open_dashboard,
        )
        self._meeting_stop_item = rumps.MenuItem(
            "Stop Meeting",
            callback=self._stop_meeting,
        )
        self._meeting_menu.add(self._meeting_start_item)
        self._meeting_menu.add(self._meeting_dashboard_item)
        self._meeting_menu.add(self._meeting_stop_item)
        self._meeting_dashboard_item.set_callback(None)  # Disabled initially
        self._meeting_stop_item.set_callback(None)  # Disabled initially

        # Settings
        self._settings_item = rumps.MenuItem(
            "Settings...",
            callback=self._open_settings,
        )

        # Open TUI
        self._tui_item = rumps.MenuItem(
            "Open TUI",
            callback=self._open_tui,
        )

        # Quit
        self._quit_item = rumps.MenuItem(
            "Quit HoldSpeak",
            callback=self._quit,
        )

        # Assemble menu
        self.menu = [
            self._status_item,
            None,  # Separator
            self._record_item,
            self._recent_menu,
            None,  # Separator
            self._meeting_menu,
            None,  # Separator
            self._settings_item,
            self._tui_item,
            None,  # Separator
            self._quit_item,
        ]

    def _initialize_components(self) -> None:
        """Initialize audio/transcription components in background."""
        def init():
            try:
                log.info(f"Loading Whisper model: {self.config.model.name}")
                self._update_status("Loading model...")

                self._transcriber = Transcriber(model_name=self.config.model.name)
                self._transcriber_model = self.config.model.name

                self._recorder = AudioRecorder()
                self._typer = TextTyper()

                # Setup hotkey listener
                self._hotkey_listener = HotkeyListener(
                    on_press=self._on_hotkey_press,
                    on_release=self._on_hotkey_release,
                    hotkey=self.config.hotkey.key,
                )
                self._hotkey_listener.start()

                self._state = "idle"
                self._update_status("Ready")
                self.title = TITLE_IDLE

                log.info("Components initialized successfully")
                rumps.notification(
                    title="HoldSpeak",
                    subtitle="Ready",
                    message=f"Hold {KEY_DISPLAY.get(self.config.hotkey.key, self.config.hotkey.key)} to record",
                )

            except Exception as e:
                log.error(f"Failed to initialize: {e}", exc_info=True)
                self._state = "error"
                self._update_status(f"Error: {e}")
                rumps.notification(
                    title="HoldSpeak",
                    subtitle="Error",
                    message=f"Failed to initialize: {e}",
                )

        threading.Thread(target=init, daemon=True).start()

    def _update_status(self, status: str) -> None:
        """Update the status menu item."""
        self._status_item.title = f"Status: {status}"

    def _set_state(self, state: str) -> None:
        """Set the application state and update UI."""
        self._state = state

        if state == "idle":
            self.title = TITLE_IDLE
            self._update_status("Ready")
            self._record_item.title = f"Start Recording ({KEY_DISPLAY.get(self.config.hotkey.key, '')})"
        elif state == "recording":
            self.title = TITLE_RECORDING
            self._update_status("Recording...")
            self._record_item.title = "Stop Recording"
        elif state == "processing":
            self.title = TITLE_PROCESSING
            self._update_status("Processing...")
            self._record_item.title = "Processing..."
        elif state == "meeting":
            self.title = TITLE_MEETING
            self._update_status("Meeting in progress")

    def _on_hotkey_press(self) -> None:
        """Called when hotkey is pressed - start recording."""
        if self._state not in ("idle", "meeting"):
            return

        self._start_recording()

    def _on_hotkey_release(self) -> None:
        """Called when hotkey is released - stop and transcribe."""
        if not self._is_recording:
            return

        self._stop_recording_and_transcribe()

    def _toggle_recording(self, _sender: rumps.MenuItem) -> None:
        """Toggle recording via menu click."""
        if self._is_recording:
            self._stop_recording_and_transcribe()
        elif self._state in ("idle", "meeting"):
            self._start_recording()

    def _start_recording(self) -> None:
        """Start audio recording."""
        if self._recorder is None:
            return

        try:
            self._recorder.start_recording()
            self._is_recording = True
            self._set_state("recording")
            log.info("Recording started")
        except Exception as e:
            log.error(f"Failed to start recording: {e}")
            rumps.notification(
                title="HoldSpeak",
                subtitle="Error",
                message=f"Recording failed: {e}",
            )

    def _stop_recording_and_transcribe(self) -> None:
        """Stop recording and transcribe in background."""
        if self._recorder is None:
            return

        try:
            audio = self._recorder.stop_recording()
            self._is_recording = False
        except Exception as e:
            log.error(f"Failed to stop recording: {e}")
            self._is_recording = False
            self._set_state("idle")
            return

        if len(audio) < 1600:  # Less than 0.1s at 16kHz
            log.info("Recording too short, ignoring")
            self._set_state("idle")
            return

        self._set_state("processing")

        def transcribe():
            with self._transcription_lock:
                try:
                    if self._transcriber is None:
                        return

                    text = self._transcriber.transcribe(audio)

                    if text:
                        # Process punctuation commands and clipboard substitution
                        text = self._text_processor.process(text)

                        # Add to recent
                        recent = RecentTranscription(text=text, timestamp=datetime.now())
                        self._recent.appendleft(recent)
                        self._update_recent_menu()

                        # Type into active app
                        if self._typer:
                            self._typer.type_text(text)

                        # Show notification
                        preview = text[:100] + "..." if len(text) > 100 else text
                        rumps.notification(
                            title="HoldSpeak",
                            subtitle="Transcribed",
                            message=preview,
                        )
                        log.info(f"Transcribed: {preview}")
                    else:
                        rumps.notification(
                            title="HoldSpeak",
                            subtitle="No speech detected",
                            message="Try speaking louder or closer to the mic",
                        )
                        log.info("No speech detected")

                except Exception as e:
                    log.error(f"Transcription failed: {e}", exc_info=True)
                    rumps.notification(
                        title="HoldSpeak",
                        subtitle="Error",
                        message=f"Transcription failed: {e}",
                    )
                finally:
                    # Reset state based on meeting status
                    if self._meeting_session and self._meeting_session.is_active:
                        self._set_state("meeting")
                    else:
                        self._set_state("idle")

        threading.Thread(target=transcribe, daemon=True).start()

    def _update_recent_menu(self) -> None:
        """Update the recent transcriptions menu."""
        self._recent_menu.clear()

        if not self._recent:
            self._recent_menu.add(rumps.MenuItem("No recent transcriptions"))
            return

        for i, entry in enumerate(self._recent):
            item = rumps.MenuItem(
                f"[{entry.time_str}] {entry.preview}",
                callback=self._make_copy_callback(entry.text),
            )
            self._recent_menu.add(item)

        # Add separator and clear option
        self._recent_menu.add(None)
        self._recent_menu.add(rumps.MenuItem(
            "Clear Recent",
            callback=self._clear_recent,
        ))

    def _make_copy_callback(self, text: str) -> Callable:
        """Create a callback that copies text to clipboard."""
        def callback(_sender):
            import pyperclip
            pyperclip.copy(text)
            rumps.notification(
                title="HoldSpeak",
                subtitle="Copied",
                message="Text copied to clipboard",
            )
        return callback

    def _clear_recent(self, _sender: rumps.MenuItem) -> None:
        """Clear recent transcriptions."""
        self._recent.clear()
        self._update_recent_menu()

    def _start_meeting(self, _sender: rumps.MenuItem) -> None:
        """Start a meeting session."""
        try:
            from .meeting_session import MeetingSession
        except ImportError:
            rumps.notification(
                title="HoldSpeak",
                subtitle="Error",
                message="Meeting mode requires: pip install -e '.[meeting]'",
            )
            return

        if self._transcriber is None:
            rumps.notification(
                title="HoldSpeak",
                subtitle="Error",
                message="Please wait for model to load",
            )
            return

        def start():
            try:
                from .meeting_session import MeetingSession

                self._meeting_session = MeetingSession(
                    transcriber=self._transcriber,
                    mic_label=self.config.meeting.mic_label,
                    remote_label=self.config.meeting.remote_label,
                    mic_device=self.config.meeting.mic_device,
                    system_device=self.config.meeting.system_audio_device,
                    intel_enabled=self.config.meeting.intel_enabled,
                    intel_model_path=self.config.meeting.intel_realtime_model,
                    web_enabled=self.config.meeting.web_enabled,
                )

                state = self._meeting_session.start()
                log.info(f"Meeting started: {state.id}")

                self._set_state("meeting")

                # Update menu items
                self._meeting_start_item.set_callback(None)  # Disable start
                self._meeting_stop_item.set_callback(self._stop_meeting)
                if state.web_url:
                    self._meeting_dashboard_item.set_callback(self._open_dashboard)
                    self._meeting_dashboard_item.title = f"Open Dashboard ({state.web_url})"

                msg = f"Meeting started"
                if state.web_url:
                    msg += f" - Dashboard at {state.web_url}"
                    if self.config.meeting.web_auto_open:
                        webbrowser.open(state.web_url)

                rumps.notification(
                    title="HoldSpeak",
                    subtitle="Meeting Started",
                    message=msg,
                )

            except Exception as e:
                log.error(f"Failed to start meeting: {e}", exc_info=True)
                rumps.notification(
                    title="HoldSpeak",
                    subtitle="Error",
                    message=f"Failed to start meeting: {e}",
                )
                self._meeting_session = None

        threading.Thread(target=start, daemon=True).start()

    def _stop_meeting(self, _sender: rumps.MenuItem) -> None:
        """Stop the current meeting."""
        if self._meeting_session is None:
            return

        def stop():
            try:
                state = self._meeting_session.stop()
                log.info(f"Meeting stopped: {state.id}, {len(state.segments)} segments")

                # Save meeting and report the actual persistence outcome.
                try:
                    save_result = self._meeting_session.save()
                    if save_result.database_saved:
                        rumps.notification(
                            title="HoldSpeak",
                            subtitle="Meeting Saved",
                            message=f"{len(state.segments)} segments recorded",
                        )
                    elif save_result.json_saved:
                        rumps.notification(
                            title="HoldSpeak",
                            subtitle="Partial Save",
                            message="Saved to JSON only; database save failed",
                        )
                    else:
                        rumps.notification(
                            title="HoldSpeak",
                            subtitle="Save Failed",
                            message="Meeting stopped, but persistence failed",
                        )
                except Exception as e:
                    log.error(f"Failed to save meeting: {e}")
                    rumps.notification(
                        title="HoldSpeak",
                        subtitle="Save Failed",
                        message=f"Failed to save meeting: {e}",
                    )

                self._meeting_session = None
                self._set_state("idle")

                # Update menu items
                self._meeting_start_item.set_callback(self._start_meeting)
                self._meeting_stop_item.set_callback(None)
                self._meeting_dashboard_item.set_callback(None)
                self._meeting_dashboard_item.title = "Open Dashboard"

            except Exception as e:
                log.error(f"Failed to stop meeting: {e}", exc_info=True)
                rumps.notification(
                    title="HoldSpeak",
                    subtitle="Error",
                    message=f"Failed to stop meeting: {e}",
                )

        threading.Thread(target=stop, daemon=True).start()

    def _open_dashboard(self, _sender: rumps.MenuItem) -> None:
        """Open the meeting dashboard in browser."""
        if self._meeting_session and self._meeting_session.state:
            url = self._meeting_session.state.web_url
            if url:
                webbrowser.open(url)

    def _open_settings(self, _sender: rumps.MenuItem) -> None:
        """Open settings (launches TUI in settings mode or shows dialog)."""
        # For now, show a notification about settings location
        # In future, could open a native dialog or TUI settings
        config_path = "~/.config/holdspeak/config.json"
        rumps.notification(
            title="HoldSpeak",
            subtitle="Settings",
            message=f"Edit config at {config_path}\nOr run: holdspeak --tui",
        )

        # Open config file in default editor
        config_file = os.path.expanduser(config_path)
        if os.path.exists(config_file):
            subprocess.run(["open", config_file])

    def _open_tui(self, _sender: rumps.MenuItem) -> None:
        """Open the full TUI in a terminal."""
        # Open Terminal and run holdspeak
        script = '''
        tell application "Terminal"
            activate
            do script "holdspeak"
        end tell
        '''
        subprocess.run(["osascript", "-e", script])

    def _quit(self, _sender: rumps.MenuItem) -> None:
        """Quit the application cleanly."""
        log.info("Quitting HoldSpeak menu bar")

        # Stop hotkey listener
        if self._hotkey_listener:
            self._hotkey_listener.stop()

        # Stop meeting if active
        if self._meeting_session and self._meeting_session.is_active:
            try:
                self._meeting_session.stop()
            except Exception:
                pass

        rumps.quit_application()

    def run(self) -> None:
        """Run the menu bar application."""
        # Initialize components in background after app starts
        self._initialize_components()
        super().run()


def run_menubar(config: Optional[Config] = None) -> None:
    """Entry point for menu bar mode.

    Args:
        config: Optional configuration object.
    """
    log.info("Starting HoldSpeak menu bar mode")
    app = HoldSpeakMenuBar(config=config)
    app.run()


if __name__ == "__main__":
    from .logging_config import setup_logging
    setup_logging(verbose=True)
    run_menubar()
