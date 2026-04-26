"""Main entry point for HoldSpeak voice typing on macOS and Linux."""

from __future__ import annotations

import os
import threading
from typing import Optional

# Disable HuggingFace progress bars - they use multiprocessing locks
# that conflict with Textual's file descriptor handling in Python 3.13
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

from .config import Config
from .hotkey import HotkeyListener
from .audio import AudioRecorder
from .controller import HoldSpeakAppWithController
from .transcribe import Transcriber
from .typer import TextTyper
from .text_processor import TextProcessor
from .commands.actions import run_actions_command
from .commands.dictation import (
    _build_argparse_subparsers as _build_dictation_subparsers,
    normalize_args as _normalize_dictation_args,
    run_dictation_command,
)
from .commands.doctor import run_doctor_command
from .commands.history import run_history_command
from .commands.intel import run_intel_command
from .logging_config import setup_logging, get_logger, LOG_FILE

log = get_logger("main")

def main():
    """Entry point for the holdspeak command."""
    import argparse

    parser = argparse.ArgumentParser(
        description="HoldSpeak - Voice typing for macOS and Linux. Hold, speak, release.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  holdspeak              # Launch web flagship runtime (default)
  holdspeak web          # Launch web flagship runtime explicitly
  holdspeak web --no-open  # Headless web service mode (no browser launch)
  holdspeak tui          # Launch legacy TUI mode explicitly
  holdspeak menubar      # Launch menu bar mode (macOS only)
  holdspeak meeting      # Start in meeting mode (capture mic + system audio)
  holdspeak meeting --setup  # Check system audio setup
  holdspeak doctor       # Verify runtime deps and setup
  holdspeak intel        # Inspect or process deferred meeting intelligence
  holdspeak intel --route-dry-run <MEETING_ID> --profile architect
                        # Simulate MIR route for a saved meeting
  holdspeak intel --reroute <MEETING_ID> --profile incident
                        # Persist manual MIR profile-override reroute window
  holdspeak --no-tui     # Deprecated alias for: holdspeak web --no-open
  holdspeak --verbose    # Show debug output in terminal

Logs are written to: {LOG_FILE}
        """,
    )
    parser.add_argument(
        "--no-tui",
        action="store_true",
        help="Deprecated: alias for `holdspeak web --no-open`",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging to stderr",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command")

    # Web mode
    web_parser = subparsers.add_parser(
        "web",
        help="Start web flagship runtime",
    )
    web_parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not auto-open browser (headless local service mode)",
    )
    web_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging to stderr",
    )

    # TUI mode
    tui_parser = subparsers.add_parser(
        "tui",
        help="Start legacy TUI voice-typing interface",
    )
    tui_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging to stderr",
    )

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

    # Intel subcommand
    intel_parser = subparsers.add_parser(
        "intel",
        help="Inspect deferred intel queue and run MIR route simulation/reroute tooling",
    )
    intel_actions = intel_parser.add_mutually_exclusive_group()
    intel_actions.add_argument(
        "--process",
        action="store_true",
        help="Process queued deferred-intel jobs now",
    )
    intel_actions.add_argument(
        "--retry",
        metavar="MEETING_ID",
        help="Requeue deferred intelligence for a specific meeting",
    )
    intel_actions.add_argument(
        "--retry-failed",
        action="store_true",
        help="Requeue failed deferred-intel jobs",
    )
    intel_actions.add_argument(
        "--route-dry-run",
        metavar="MEETING_ID",
        help="Simulate MIR routing for a saved meeting transcript (no DB writes)",
    )
    intel_actions.add_argument(
        "--reroute",
        metavar="MEETING_ID",
        help="Apply manual MIR profile override reroute for a saved meeting",
    )
    intel_parser.add_argument(
        "--status",
        choices=["all", "queued", "running", "failed"],
        default="all",
        help="Filter listed jobs by status (default: all)",
    )
    intel_parser.add_argument(
        "--limit", "-n",
        type=int,
        default=20,
        help="Number of jobs to list or retry (default: 20)",
    )
    intel_parser.add_argument(
        "--max-jobs",
        type=int,
        help="Maximum number of jobs to process with --process",
    )
    intel_parser.add_argument(
        "--retry-mode",
        choices=["respect-backoff", "retry-now"],
        default="respect-backoff",
        help="When processing queue: respect scheduled retry delays or force retry-now",
    )
    intel_parser.add_argument(
        "--profile",
        help="Routing profile override for --route-dry-run/--reroute (balanced, architect, delivery, product, incident)",
    )
    intel_parser.add_argument(
        "--override-intents",
        help="Comma-separated manual intent override set for --route-dry-run/--reroute",
    )
    intel_parser.add_argument(
        "--threshold",
        type=float,
        help="Intent threshold override for --route-dry-run/--reroute",
    )

    # Dictation subcommand (DIR-01)
    dictation_parser = subparsers.add_parser(
        "dictation",
        help="Inspect / dry-run the DIR-01 dictation pipeline",
    )
    _build_dictation_subparsers(dictation_parser)

    # Doctor subcommand
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Run environment checks and show setup fixes",
    )
    doctor_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures (non-zero exit)",
    )

    args = parser.parse_args()

    # Setup logging (always to file, optionally to stderr)
    setup_logging(verbose=args.verbose)

    if args.no_tui:
        _emit_no_tui_deprecation()

    # Handle web subcommand
    if args.command == "web":
        no_open = bool(args.no_open or args.no_tui)
        log.info(f"HoldSpeak web mode starting (no_open={no_open})")
        _run_web_mode(no_open=no_open)
        return

    # Handle tui subcommand
    if args.command == "tui":
        if args.no_tui:
            log.info("Ignoring deprecated --no-tui flag while running explicit `tui` mode")
        log.info("HoldSpeak TUI mode starting")
        _run_tui_mode()
        return

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
        run_history_command(args)
        return

    # Handle actions subcommand
    if args.command == "actions":
        run_actions_command(args)
        return

    # Handle intel subcommand
    if args.command == "intel":
        raise SystemExit(run_intel_command(args))

    # Handle dictation subcommand (DIR-01 CLI surface)
    if args.command == "dictation":
        raise SystemExit(run_dictation_command(_normalize_dictation_args(args)))

    # Handle doctor subcommand
    if args.command == "doctor":
        raise SystemExit(run_doctor_command(args))

    # Default mode: web-first runtime.
    no_open = bool(args.no_tui)
    log.info(f"HoldSpeak default mode routing to web (no_open={no_open})")
    _run_web_mode(no_open=no_open)


def _emit_no_tui_deprecation() -> None:
    import sys
    message = (
        "DEPRECATION: `--no-tui` is deprecated and will be removed in a future release. "
        "Use `holdspeak web --no-open` for headless web mode, or `holdspeak tui` for terminal UI."
    )
    print(message, file=sys.stderr)
    log.warning(message)


def _run_web_mode(*, no_open: bool = False) -> None:
    """Start web runtime lifecycle (staged Step 2 extraction)."""
    from .web_runtime import run_web_runtime

    run_web_runtime(no_open=no_open)


def _run_tui_mode() -> None:
    """Run the legacy TUI mode."""
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
        print("Try running the TUI (`holdspeak tui`) and use focused hold-to-talk.")
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


if __name__ == "__main__":
    main()
