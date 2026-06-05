#!/usr/bin/env python
"""Smoke fixtures for HoldSpeak desktop presence rendering.

Default mode is CI-safe: it prints renderer-ready view data for each activity
state without opening windows. Use `--render tk` only from an interactive
desktop session when manually checking the transient native window path.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from holdspeak.desktop_presence import (  # noqa: E402
    DesktopPresenceHost,
    TkPresenceRenderer,
    build_presence_window_view,
)
from holdspeak.runtime_activity import RuntimeActivityTracker  # noqa: E402


STATES: tuple[tuple[str, str, str], ...] = (
    ("idle", "runtime", "Waiting for activity."),
    ("listening", "hotkey", "Hotkey accepted."),
    ("recording", "hotkey", "Recording microphone input."),
    ("transcribing", "dictation", "Turning speech into text."),
    ("processing", "dictation", "Applying dictation pipeline."),
    ("typing", "dictation", "Typing into the target app."),
    ("complete", "dictation", "Typed successfully."),
    ("meeting_live", "meeting", "Segment captured."),
    ("saving", "meeting", "Saving meeting artifacts."),
    ("error", "runtime", "Fixture error."),
)


def build_activities() -> list[dict[str, object]]:
    tracker = RuntimeActivityTracker()
    activities: list[dict[str, object]] = []
    for state, source, detail in STATES:
        activities.append(
            tracker.update(
                state,
                source=source,
                detail=detail,
                last_event=f"fixture_{state}",
                last_error=detail if state == "error" else None,
            )
        )
    return activities


def render_view_fixture() -> int:
    views = [asdict(build_presence_window_view(activity)) for activity in build_activities()]
    print(json.dumps(views, indent=2, sort_keys=True))
    return 0


def render_tk_sequence(delay_seconds: float) -> int:
    try:
        host = DesktopPresenceHost(TkPresenceRenderer())
    except RuntimeError as exc:
        print(f"unsupported: {exc}")
        return 2
    try:
        for activity in build_activities():
            host.handle_activity(activity)
            time.sleep(delay_seconds)
    finally:
        host.close()
    print("tk smoke completed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--render",
        choices=("view", "tk"),
        default="view",
        help="Renderer smoke mode. 'view' is CI-safe; 'tk' opens transient windows.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.45,
        help="Seconds between Tk fixture states.",
    )
    args = parser.parse_args()

    if args.render == "tk":
        return render_tk_sequence(args.delay)
    return render_view_fixture()


if __name__ == "__main__":
    raise SystemExit(main())
