"""Actions subcommand for HoldSpeak."""

from __future__ import annotations

import sys

from ..db import get_database


def run_actions_command(args) -> None:
    """Handle the `actions` subcommand."""
    db = get_database()

    if args.done:
        success = db.update_action_item_status(args.done, "done")
        if success:
            print(f"Marked as done: {args.done}")
        else:
            print(f"Action item not found: {args.done}", file=sys.stderr)
            sys.exit(1)
        return

    if args.dismiss:
        success = db.update_action_item_status(args.dismiss, "dismissed")
        if success:
            print(f"Dismissed: {args.dismiss}")
        else:
            print(f"Action item not found: {args.dismiss}", file=sys.stderr)
            sys.exit(1)
        return

    items = db.list_action_items(
        include_completed=args.all,
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
