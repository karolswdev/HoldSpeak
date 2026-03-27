"""Action item service functions for the TUI layer."""

from __future__ import annotations

from ... import db as db_module
from ...db import ActionItemSummary


def list_action_items(
    *, include_completed: bool = False, meeting_id: str | None = None, owner: str | None = None
) -> list[ActionItemSummary]:
    """List action items for TUI views."""
    db = db_module.get_database()
    return db.list_action_items(
        include_completed=include_completed,
        meeting_id=meeting_id,
        owner=owner,
    )


def update_action_item_status(action_id: str, status: str) -> bool:
    """Update a persisted action item's status."""
    db = db_module.get_database()
    return db.update_action_item_status(action_id, status)
