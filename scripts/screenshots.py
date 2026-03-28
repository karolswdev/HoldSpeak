#!/usr/bin/env python3
"""Screenshot automation utility for HoldSpeak documentation.

Generates consistent PNG screenshots of the TUI and Web Dashboard
for documentation and visual reference.

Usage:
    python scripts/screenshots.py          # Generate all screenshots
    python scripts/screenshots.py tui      # TUI screenshots only
    python scripts/screenshots.py web      # Web dashboard screenshots only
    python scripts/screenshots.py --list   # List available scenarios
"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Ensure holdspeak package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "screenshots"


# ============================================================
# Sample Data
# ============================================================

SAMPLE_TRANSCRIPTIONS = [
    "Let me check the documentation for that API endpoint.",
    "The deployment should complete in about five minutes.",
    "Can you share your screen so we can review the changes?",
    "I think we should schedule a follow-up meeting for next week.",
]

SAMPLE_SEGMENTS = [
    {
        "text": "I think we should focus on the Q1 roadmap priorities first. We have some key deliverables that need attention.",
        "speaker": "Me",
        "start_time": 0.0,
        "end_time": 15.0,
        "is_bookmarked": False,
    },
    {
        "text": "Agreed. For the auth system, I've been researching OAuth 2.0 and OpenID Connect. It looks like the standard approach would work well for our use case.",
        "speaker": "Remote",
        "start_time": 18.0,
        "end_time": 42.0,
        "is_bookmarked": False,
    },
    {
        "text": "Let's go with OAuth then. It's more secure and reduces our maintenance burden. I'll draft a proposal by Thursday.",
        "speaker": "Me",
        "start_time": 45.0,
        "end_time": 68.0,
        "is_bookmarked": False,
    },
    {
        "text": "Perfect. Can you also loop in the security team? They should review our implementation plan before we start coding.",
        "speaker": "Remote",
        "start_time": 70.0,
        "end_time": 88.0,
        "is_bookmarked": False,
    },
    {
        "text": "Absolutely. I'll set up a meeting with them for early next week. What about the dashboard redesign?",
        "speaker": "Me",
        "start_time": 92.0,
        "end_time": 105.0,
        "is_bookmarked": False,
    },
    {
        "text": "The designs are almost ready. Sarah said she'll have the final mockups by Friday. We can review them together next Monday.",
        "speaker": "Remote",
        "start_time": 108.0,
        "end_time": 128.0,
        "is_bookmarked": False,
    },
]

SAMPLE_INTEL = {
    "timestamp": 128.0,
    "topics": [
        "Q1 Roadmap",
        "Authentication System",
        "OAuth Implementation",
        "Security Review",
        "Dashboard Redesign",
    ],
    "action_items": [
        {"task": "Draft OAuth proposal", "owner": "Me", "due": "Thursday"},
        {"task": "Schedule security team review", "owner": "Me", "due": "Early next week"},
        {"task": "Finalize dashboard mockups", "owner": "Sarah", "due": "Friday"},
        {"task": "Review mockups together", "owner": "Team", "due": "Monday"},
    ],
    "summary": "Team discussed Q1 priorities focusing on authentication system (decided on OAuth 2.0 approach) and dashboard redesign. Key decisions: OAuth over custom JWT for security and maintainability. Security team involvement required before implementation starts. Dashboard redesign mockups expected by Friday.",
}

SAMPLE_BOOKMARK = {
    "timestamp": 45.0,
    "label": "OAuth decision",
    "created_at": datetime.now().isoformat(),
}

SAMPLE_MEETING_TITLE = "Q1 Planning & Auth Discussion"
SAMPLE_MEETING_TAGS = ["planning", "auth", "q1"]


# ============================================================
# TUI Screenshots
# ============================================================

async def capture_tui_screenshots() -> bool:
    """Capture all TUI screenshots using Textual's pilot API."""
    print("  Importing TUI modules...")

    try:
        from holdspeak.tui import HoldSpeakApp
        from holdspeak.tui.screens import SettingsScreen, MeetingTranscriptScreen, MeetingMetadataScreen
        from holdspeak.config import Config
        from holdspeak.meeting_session import TranscriptSegment, Bookmark
    except ImportError as e:
        print(f"  ERROR: Could not import TUI modules: {e}")
        return False

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config = Config()  # Use default config

    print("  Capturing TUI idle state...")
    app = HoldSpeakApp(config=config)
    async with app.run_test(size=(112, 30)) as pilot:
        # Add some history items
        for text in SAMPLE_TRANSCRIPTIONS:
            app.add_transcription(text)
        app.set_state("idle")
        await pilot.pause()
        app.save_screenshot(str(OUTPUT_DIR / "tui_idle.svg"))

    print("  Capturing TUI recording state...")
    app = HoldSpeakApp(config=config)
    async with app.run_test(size=(112, 30)) as pilot:
        for text in SAMPLE_TRANSCRIPTIONS[:2]:
            app.add_transcription(text)
        app.set_state("recording")
        app.set_audio_level(0.65)
        await pilot.pause()
        app.save_screenshot(str(OUTPUT_DIR / "tui_recording.svg"))

    print("  Capturing TUI transcribing state...")
    app = HoldSpeakApp(config=config)
    async with app.run_test(size=(112, 30)) as pilot:
        for text in SAMPLE_TRANSCRIPTIONS[:3]:
            app.add_transcription(text)
        app.set_state("transcribing")
        await pilot.pause()
        app.save_screenshot(str(OUTPUT_DIR / "tui_transcribing.svg"))

    print("  Capturing TUI meeting cockpit...")
    app = HoldSpeakApp(config=config)
    async with app.run_test(size=(120, 34)) as pilot:
        app.show_meeting_cockpit(title=SAMPLE_MEETING_TITLE, has_system_audio=True)
        await pilot.pause()
        app.set_meeting_duration("05:23")
        app.set_meeting_segment_count(len(SAMPLE_SEGMENTS))
        app.set_meeting_mic_level(0.61)
        app.set_meeting_system_level(0.54)
        for seg in SAMPLE_SEGMENTS[:4]:
            app.update_meeting_cockpit_segment(
                TranscriptSegment(
                    text=seg["text"],
                    speaker=seg["speaker"],
                    start_time=seg["start_time"],
                    end_time=seg["end_time"],
                )
            )
        app.update_meeting_cockpit_bookmark(Bookmark(timestamp=45.0, label="OAuth decision"))
        app.update_meeting_cockpit_intel(
            SAMPLE_INTEL["topics"],
            SAMPLE_INTEL["action_items"],
            SAMPLE_INTEL["summary"],
        )
        await pilot.pause()
        app.save_screenshot(str(OUTPUT_DIR / "tui_meeting.svg"))

    print("  Capturing TUI meeting metadata modal...")
    app = HoldSpeakApp(config=config)
    async with app.run_test(size=(112, 32)) as pilot:
        for text in SAMPLE_TRANSCRIPTIONS[:2]:
            app.add_transcription(text)
        app.set_meeting_active(True)
        app.set_meeting_duration("02:45")
        app.push_screen(MeetingMetadataScreen(SAMPLE_MEETING_TITLE, SAMPLE_MEETING_TAGS))
        await pilot.pause()
        app.save_screenshot(str(OUTPUT_DIR / "tui_metadata.svg"))

    print("  Capturing TUI settings modal...")
    app = HoldSpeakApp(config=config)
    async with app.run_test(size=(112, 32)) as pilot:
        for text in SAMPLE_TRANSCRIPTIONS[:2]:
            app.add_transcription(text)
        app.push_screen(SettingsScreen(config))
        await pilot.pause()
        app.save_screenshot(str(OUTPUT_DIR / "tui_settings.svg"))

    print("  Capturing TUI transcript modal...")
    app = HoldSpeakApp(config=config)
    async with app.run_test(size=(120, 34)) as pilot:
        # Create sample TranscriptSegment objects
        segments = [
            TranscriptSegment(
                text=s["text"],
                speaker=s["speaker"],
                start_time=s["start_time"],
                end_time=s["end_time"],
            )
            for s in SAMPLE_SEGMENTS[:4]
        ]
        # Create sample bookmarks
        bookmarks = [
            Bookmark(timestamp=45.0, label="OAuth decision"),
        ]
        app.push_screen(MeetingTranscriptScreen(segments, bookmarks))
        await pilot.pause()
        app.save_screenshot(str(OUTPUT_DIR / "tui_transcript.svg"))

    return True


# ============================================================
# Web Dashboard Screenshots
# ============================================================

async def capture_web_screenshots() -> bool:
    """Capture all web dashboard screenshots using Playwright."""
    print("  Checking Playwright installation...")

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  ERROR: Playwright not installed.")
        print("  Install with: pip install playwright && playwright install chromium")
        return False

    print("  Checking web server dependencies...")
    try:
        from holdspeak.web_server import MeetingWebServer
    except ImportError:
        print("  ERROR: Web server dependencies not installed.")
        print("  Install with: pip install fastapi uvicorn")
        return False
    except RuntimeError as e:
        print(f"  ERROR: {e}")
        return False

    from holdspeak.meeting_session import MeetingState, TranscriptSegment, Bookmark, IntelSnapshot

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create mock meeting state
    started_at = datetime.now() - timedelta(minutes=5, seconds=23)
    mock_state = MeetingState(
        id="abc12345",
        started_at=started_at,
        title=SAMPLE_MEETING_TITLE,
        tags=SAMPLE_MEETING_TAGS,
        intel_status="live",
        intel_status_detail="Live meeting intelligence active.",
        mic_label="Me",
        remote_label="Remote",
    )

    def mock_on_bookmark(label: str) -> dict:
        return {"timestamp": 120.5, "label": label, "created_at": datetime.now().isoformat()}

    def mock_on_stop() -> dict:
        return {"status": "stopped"}

    def mock_get_state() -> dict:
        return mock_state.to_dict()

    # Start web server
    print("  Starting mock web server...")
    server = MeetingWebServer(
        on_bookmark=mock_on_bookmark,
        on_stop=mock_on_stop,
        get_state=mock_get_state,
    )

    try:
        url = server.start()
        print(f"  Server started at {url}")
    except Exception as e:
        print(f"  ERROR: Failed to start web server: {e}")
        return False

    # Give server time to fully start
    await asyncio.sleep(0.5)

    try:
        async with async_playwright() as p:
            print("  Launching browser...")
            try:
                browser = await p.chromium.launch()
            except Exception as e:
                if "executable doesn't exist" in str(e).lower():
                    print("  ERROR: Chromium browser not installed.")
                    print("  Run: playwright install chromium")
                    return False
                raise

            page = await browser.new_page(viewport={"width": 1280, "height": 900})

            # Screenshot 1: Empty state
            print("  Capturing dashboard empty state...")
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(0.3)  # Let Alpine.js initialize
            await page.screenshot(path=str(OUTPUT_DIR / "dashboard_empty.png"))

            # Screenshot 2: With transcript
            print("  Capturing dashboard with transcript...")
            for segment in SAMPLE_SEGMENTS:
                server.broadcast("segment", segment)
                await asyncio.sleep(0.05)  # Small delay between segments
            await asyncio.sleep(0.3)  # Let WebSocket deliver
            await page.screenshot(path=str(OUTPUT_DIR / "dashboard_transcript.png"))

            # Screenshot 3: With intelligence
            print("  Capturing dashboard with intelligence...")
            server.broadcast("intel", SAMPLE_INTEL)
            await asyncio.sleep(0.3)
            await page.screenshot(path=str(OUTPUT_DIR / "dashboard_intel.png"))

            # Screenshot 4: With bookmarks
            print("  Capturing dashboard with bookmarks...")
            server.broadcast("bookmark", SAMPLE_BOOKMARK)
            await asyncio.sleep(0.3)
            await page.screenshot(path=str(OUTPUT_DIR / "dashboard_bookmarks.png"))

            await browser.close()

    finally:
        print("  Stopping web server...")
        server.stop()

    return True


# ============================================================
# CLI Interface
# ============================================================

SCENARIOS = {
    "tui": [
        ("tui_idle.svg", "TUI in idle state with transcription history"),
        ("tui_recording.svg", "TUI recording with audio level bar active"),
        ("tui_transcribing.svg", "TUI in transcribing state"),
        ("tui_meeting.svg", "TUI meeting cockpit with live transcript and intelligence"),
        ("tui_metadata.svg", "Meeting metadata modal for title/tags editing"),
        ("tui_settings.svg", "Settings modal open"),
        ("tui_transcript.svg", "Meeting transcript modal with segments"),
    ],
    "web": [
        ("dashboard_empty.png", "Web dashboard empty state (with title/tags)"),
        ("dashboard_transcript.png", "Web dashboard with transcript"),
        ("dashboard_intel.png", "Web dashboard with intelligence panel"),
        ("dashboard_bookmarks.png", "Web dashboard with bookmarks"),
    ],
}


def print_available_scenarios() -> None:
    """Print list of available screenshot scenarios."""
    print("\nAvailable screenshot scenarios:")
    print("\nTUI Screenshots:")
    for filename, desc in SCENARIOS["tui"]:
        print(f"  - {filename}: {desc}")
    print("\nWeb Dashboard Screenshots:")
    for filename, desc in SCENARIOS["web"]:
        print(f"  - {filename}: {desc}")
    print(f"\nOutput directory: {OUTPUT_DIR}")


def main() -> int:
    """Main entry point for screenshot generation."""
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0

    if "--list" in args:
        print_available_scenarios()
        return 0

    run_tui = "tui" in args or not args or args == []
    run_web = "web" in args or not args or args == []

    # If specific args provided, only run those
    if args and args != []:
        run_tui = "tui" in args
        run_web = "web" in args

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}\n")

    success = True

    if run_tui:
        print("Generating TUI screenshots...")
        try:
            result = asyncio.run(capture_tui_screenshots())
            if result:
                print(f"  TUI screenshots saved to {OUTPUT_DIR}\n")
            else:
                success = False
        except Exception as e:
            print(f"  ERROR: TUI screenshot generation failed: {e}\n")
            success = False

    if run_web:
        print("Generating web dashboard screenshots...")
        try:
            result = asyncio.run(capture_web_screenshots())
            if result:
                print(f"  Web screenshots saved to {OUTPUT_DIR}\n")
            else:
                success = False
        except Exception as e:
            print(f"  ERROR: Web screenshot generation failed: {e}\n")
            success = False

    if success:
        print("All screenshots generated successfully.")
    else:
        print("Some screenshots failed to generate. See errors above.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
