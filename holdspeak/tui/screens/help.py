"""Help screen with tabbed documentation."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static, TabbedContent, TabPane


class HelpScreen(ModalScreen[None]):
    """Comprehensive help and documentation screen."""

    BINDINGS = [("escape", "close", "Close")]

    def action_close(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        with Container(id="help_dialog"):
            yield Label("HoldSpeak Help", id="help_title")
            with TabbedContent(id="help_tabs"):
                with TabPane("Keybindings", id="keys_tab"):
                    with VerticalScroll():
                        yield Static(self._keybindings_content(), markup=True)
                with TabPane("Meeting Mode", id="meeting_tab"):
                    with VerticalScroll():
                        yield Static(self._meeting_content(), markup=True)
                with TabPane("Setup", id="setup_tab"):
                    with VerticalScroll():
                        yield Static(self._setup_content(), markup=True)
                with TabPane("Troubleshooting", id="trouble_tab"):
                    with VerticalScroll():
                        yield Static(self._troubleshooting_content(), markup=True)
            with Horizontal(id="help_actions"):
                yield Button("Close", id="help_close")
                yield Button("Open Logs", id="help_logs")

    def _keybindings_content(self) -> str:
        return """[bold]Global Hotkey[/]
  [bold cyan]Right Alt/Option (default)[/]  Hold to record, release to transcribe

[bold]Focused-only Hold-to-Talk (TUI)[/]
  [bold cyan]v[/]  Hold to record while HoldSpeak has focus (no global hotkey needed)

[bold]Navigation[/]
  [bold cyan]Tab[/]  Cycle Voice Typing / Meetings tabs
  [bold cyan]1[/]    Voice Typing tab
  [bold cyan]2[/]    Meetings tab
  [bold cyan]?[/]    Help
  [bold cyan]s[/]    Settings
  [bold cyan]d[/]    Diagnostics
  [bold cyan]q[/]    Quit

[bold]During Meeting[/]
  [bold cyan]b[/]   Add bookmark at current time
  [bold cyan]e[/]   Edit meeting title and tags
  [bold cyan]t[/]   View full transcript
  [bold cyan]w[/]   Open web dashboard
  [bold cyan]c[/]   Copy last transcription (voice typing tab)

[bold]In Lists[/]
  [bold cyan]Up/Down[/]     Navigate items
  [bold cyan]Enter/Space[/]  Select/activate item
  [bold cyan]Escape[/]       Close modal

[bold]Clipboard[/]
  Click a transcription to copy it to clipboard.
  Use [bold cyan]c[/] to copy the most recent transcription.
"""

    def _meeting_content(self) -> str:
        return """[bold]Meeting Mode[/]

Captures both your microphone and system audio (remote participants)
for complete meeting transcription with AI-powered intelligence.

[bold]Starting a Meeting[/]
  Press [bold cyan]m[/] to toggle meeting mode on/off.
  The meeting bar will appear at the top showing:
  - Duration
  - Segment count
  - Audio levels (mic and system)
  - Web dashboard URL

[bold]During a Meeting[/]
  - Speak normally - your voice is transcribed automatically
  - Remote participants are captured via system audio
  - Use [bold cyan]b[/] to bookmark important moments
  - Use [bold cyan]e[/] to set meeting title and tags

[bold]AI Intelligence[/]
  The meeting is analyzed in real-time to extract:
  - [bold]Topics[/] - Key subjects discussed
  - [bold]Action Items[/] - Tasks with owners
  - [bold]Summary[/] - Brief meeting overview

[bold]Web Dashboard[/]
  When a meeting starts, a web server provides a live dashboard
  accessible from any browser on your network. The URL is shown
  in the meeting bar.

[bold]After a Meeting[/]
  - Open the [bold]Meetings[/] tab to browse saved sessions
  - Use the web dashboard or meeting detail view for action items
  - Transcripts and intel are saved to the database
"""

    def _setup_content(self) -> str:
        return """[bold]Initial Setup[/]

[bold]1. Whisper Model[/]
  On first run, HoldSpeak downloads the Whisper model.
  Choose the model size in Settings ([bold cyan]s[/]):
  - [dim]tiny[/]   - Fastest, lower accuracy
  - [bold]base[/]   - Good balance (default)
  - [dim]small[/]  - Better accuracy, slower
  - [dim]medium[/] - High accuracy, slow
  - [dim]large[/]  - Best accuracy, very slow

[bold]2. Hotkey Configuration[/]
  The default hotkey is [bold cyan]Right Alt/Option[/].
  Change it in Settings if needed.

[bold]3. Meeting Mode Setup[/]
  [bold]Linux (Pulse/PipeWire)[/]
    1. Install Pulse utilities: `sudo apt-get install pulseaudio-utils`
    2. Verify monitor sources:
       `pactl list short sources | grep '\\.monitor'`
    3. Set `meeting.system_audio_device` to a monitor source name.

  [bold]macOS (BlackHole)[/]
    1. Install BlackHole: `brew install blackhole-2ch`
    2. Create a Multi-Output Device in Audio MIDI Setup
    3. Select BlackHole as system audio input in HoldSpeak Settings

[bold]4. Intel Model (Optional)[/]
  For AI meeting intelligence, configure a local LLM:
  - Download a GGUF model (e.g., Mistral-7B)
  - Set path in ~/.config/holdspeak/config.json
  - Requires llama-cpp-python (Metal acceleration optional on macOS)
"""

    def _troubleshooting_content(self) -> str:
        return """[bold]Troubleshooting[/]

[bold]No audio being recorded[/]
  - Check microphone permissions in system settings
  - Ensure correct input device is selected in Settings
  - Try a different input device

[bold]Poor transcription quality[/]
  - Speak clearly into the microphone
  - Reduce background noise
  - Try a larger Whisper model in Settings
  - Position microphone closer

[bold]System audio not captured[/]
  - Linux: verify monitor sources: `pactl list short sources | grep '\\.monitor'`
  - Linux: install `pulseaudio-utils` if `pactl` is missing
  - macOS: verify BlackHole install (`brew list blackhole-2ch`)
  - macOS: check Multi-Output Device + BlackHole routing

[bold]Meeting intel not working[/]
  - Check LLM model path in config.json
  - Verify model file exists and is readable
  - Check console for model loading errors
  - Try a smaller model if memory is limited

[bold]Web dashboard not accessible[/]
  - Check firewall settings
  - Try accessing from localhost first
  - Verify port 8765 is not in use

[bold]App crashes or freezes[/]
  - Check logs in ~/.local/share/holdspeak/logs/
  - Report issues at github.com/holdspeak/issues
  - Try resetting config: rm ~/.config/holdspeak/config.json

[bold]View Logs[/]
  Click "Open Logs" below or run:
  cat ~/.local/share/holdspeak/logs/holdspeak.log
"""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "help_close":
            self.app.pop_screen()
        elif event.button.id == "help_logs":
            import subprocess
            import sys
            from pathlib import Path

            log_dir = Path.home() / ".local" / "share" / "holdspeak" / "logs"
            log_file = log_dir / "holdspeak.log"

            if log_file.exists():
                # Open in default text editor
                if sys.platform == "darwin":
                    subprocess.Popen(["open", str(log_file)])
                else:
                    subprocess.Popen(["xdg-open", str(log_file)])
                self.app.notify("Opening log file...", timeout=1.5)
            else:
                self.app.notify(f"Log file not found: {log_file}", severity="warning", timeout=2.0)
