"""History subcommand for HoldSpeak."""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Optional

from ..db import get_database
from ..logging_config import get_logger
from ..meeting_exports import write_meeting_export

log = get_logger("commands.history")


def run_history_command(args) -> None:
    """Handle the `history` subcommand."""
    db = get_database()

    if args.search:
        results = db.search_transcripts(args.search, limit=args.limit)
        if not results:
            print(f"No matches found for: {args.search}")
            return

        print(f"Found {len(results)} matching segment(s):\n")
        for meeting_id, segment in results:
            display_text = segment.text[:100] + "..." if len(segment.text) > 100 else segment.text
            print(f"  [{meeting_id[:8]}] {segment.speaker} @ {segment.start_time:.0f}s: {display_text}")
        return

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

    if args.meeting_id:
        meeting = db.get_meeting(args.meeting_id)
        if not meeting:
            print(f"Meeting not found: {args.meeting_id}", file=sys.stderr)
            sys.exit(1)

        if args.export:
            filepath = export_meeting(meeting, args.export)
            if filepath:
                print(f"Exported to: {filepath}")
            else:
                print("Export failed", file=sys.stderr)
                sys.exit(1)
            return

        display_meeting_detail(meeting, verbose=args.verbose)
        return

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

    for meeting in meetings:
        title = meeting.title or "(untitled)"
        if len(title) > 30:
            title = title[:27] + "..."
        date_str = meeting.started_at.strftime("%Y-%m-%d")
        duration = format_duration_simple(meeting.duration_seconds) if meeting.duration_seconds else "--:--"
        print(f"{meeting.id[:12]:<12} {date_str:<12} {duration:<10} {meeting.segment_count:<10} {title}")


def display_meeting_detail(meeting, verbose: bool = False) -> None:
    """Display detailed meeting information."""
    state = meeting

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
        for bookmark in state.bookmarks:
            label = f" - {bookmark.label}" if bookmark.label else ""
            print(f"  [{bookmark.timestamp:.0f}s]{label}")

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
        print("\nTranscript:")
        print("-" * 40)
        for segment in state.segments:
            timestamp = f"[{segment.start_time:.0f}s]"
            bookmark = " *" if segment.is_bookmarked else ""
            print(f"{timestamp} {segment.speaker}: {segment.text}{bookmark}")


def export_meeting(meeting, format: str) -> Optional[str]:
    """Export a meeting to file."""
    try:
        return str(write_meeting_export(meeting, format))  # type: ignore[arg-type]
    except Exception as exc:
        log.error(f"Failed to export meeting: {exc}")
        return None


def format_duration_simple(seconds: Optional[float]) -> str:
    """Format duration as MM:SS or HH:MM:SS."""
    if seconds is None:
        return "--:--"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    mins, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"
