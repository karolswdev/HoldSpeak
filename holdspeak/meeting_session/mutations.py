"""Action-item, title, and tag mutations (HS-63-02).

Verbatim method moves out of MeetingSession; `self` is the session.
"""

from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, TYPE_CHECKING
import json

import numpy as np

from ..meeting_recorder import MeetingRecorder, concatenate_chunks, AudioChunk
from ..transcribe import Transcriber
from ..logging_config import get_logger

if TYPE_CHECKING:
    from ..audio import AudioSource
    from ..device_audio import DeviceDescriptor

# Optional imports for intel (the same guarded pattern as session.py).
try:
    from ..intel import (
        MeetingIntel,
        IntelResult,
        ActionItem,
        get_intel_runtime_status,
        resolve_intel_provider,
    )
except ImportError:
    MeetingIntel = None  # type: ignore
    IntelResult = None  # type: ignore
    ActionItem = None  # type: ignore
    get_intel_runtime_status = None  # type: ignore
    resolve_intel_provider = None  # type: ignore

try:
    from ..speaker_intel import SpeakerDiarizer
except ImportError:
    SpeakerDiarizer = None  # type: ignore

from .models import (
    Bookmark,
    IntelSnapshot,
    MeetingSaveResult,
    MeetingState,
    TranscriptSegment,
)

log = get_logger("meeting_session")


class MeetingMutationsMixin:
    def update_action_item(self, item_id: str, status: str) -> Optional[dict]:
        """Update the status of an action item.

        Args:
            item_id: The unique ID of the action item.
            status: New status ("done", "pending", or "dismissed").

        Returns:
            The updated action item as a dict, or None if not found.
        """
        with self._lock:
            if self._state is None or self._state.intel is None:
                return None

            normalized = str(status).strip().lower()
            if normalized not in {"done", "pending", "dismissed"}:
                log.warning(f"Unknown action item status: {status}")
                return None

            for item in self._state.intel.action_items:
                if hasattr(item, "id") and item.id == item_id:
                    if normalized == "done":
                        item.mark_done()
                    elif normalized == "dismissed":
                        item.dismiss()
                    else:
                        item.status = "pending"
                        item.completed_at = None
                    log.info(f"Action item {item_id} updated to status={normalized}")
                    return item.to_dict()

                if isinstance(item, dict) and item.get("id") == item_id:
                    item["status"] = normalized
                    if normalized == "pending":
                        item["completed_at"] = None
                    else:
                        item["completed_at"] = datetime.now().isoformat()
                    log.info(f"Action item {item_id} updated to status={normalized}")
                    return item

            log.warning(f"Action item not found: {item_id}")
            return None

    def update_action_item_review(self, item_id: str, review_state: str) -> Optional[dict]:
        """Update review state of an action item.

        Args:
            item_id: The unique ID of the action item.
            review_state: New review state ("pending" or "accepted").

        Returns:
            Updated action item dict, or None if not found/invalid.
        """
        with self._lock:
            if self._state is None or self._state.intel is None:
                return None

            normalized = str(review_state).strip().lower()
            if normalized not in {"pending", "accepted"}:
                log.warning(f"Unknown action item review_state: {review_state}")
                return None

            for item in self._state.intel.action_items:
                if hasattr(item, "id") and item.id == item_id:
                    if normalized == "accepted":
                        if hasattr(item, "accept"):
                            item.accept()
                        else:
                            item.review_state = "accepted"
                            item.reviewed_at = datetime.now().isoformat()
                    else:
                        item.review_state = "pending"
                        item.reviewed_at = None
                    log.info(f"Action item {item_id} updated to review_state={normalized}")
                    return item.to_dict()

                if isinstance(item, dict) and item.get("id") == item_id:
                    item["review_state"] = normalized
                    item["reviewed_at"] = datetime.now().isoformat() if normalized == "accepted" else None
                    log.info(f"Action item {item_id} updated to review_state={normalized}")
                    return item

            log.warning(f"Action item not found: {item_id}")
            return None

    def edit_action_item(
        self,
        item_id: str,
        *,
        task: str,
        owner: Optional[str],
        due: Optional[str],
    ) -> Optional[dict]:
        """Edit action-item content and mark it accepted.

        Args:
            item_id: The unique ID of the action item.
            task: New task text.
            owner: Optional owner text (None/empty clears).
            due: Optional due text (None/empty clears).

        Returns:
            Updated action item dict, or None if not found/invalid.
        """
        clean_task = str(task).strip()
        if not clean_task:
            return None

        clean_owner = owner.strip() if isinstance(owner, str) else None
        clean_due = due.strip() if isinstance(due, str) else None

        with self._lock:
            if self._state is None or self._state.intel is None:
                return None

            for item in self._state.intel.action_items:
                if hasattr(item, "id") and item.id == item_id:
                    item.task = clean_task
                    item.owner = clean_owner or None
                    item.due = clean_due or None
                    if hasattr(item, "accept"):
                        item.accept()
                    else:
                        item.review_state = "accepted"
                        item.reviewed_at = datetime.now().isoformat()
                    log.info(f"Action item {item_id} edited and accepted")
                    return item.to_dict()

                if isinstance(item, dict) and item.get("id") == item_id:
                    item["task"] = clean_task
                    item["owner"] = clean_owner or None
                    item["due"] = clean_due or None
                    item["review_state"] = "accepted"
                    item["reviewed_at"] = datetime.now().isoformat()
                    log.info(f"Action item {item_id} edited and accepted")
                    return item

            log.warning(f"Action item not found: {item_id}")
            return None

    def set_title(self, title: str) -> None:
        """Set meeting title.

        Args:
            title: The meeting title. Empty string clears the title.
        """
        with self._lock:
            if self._state:
                self._state.title = title.strip() or None
                log.info(f"Meeting title set: {self._state.title}")
                self._emit_broadcast("meeting_updated", {
                    "title": self._state.title,
                    "tags": self._state.tags,
                })

    def get_title(self) -> Optional[str]:
        """Get current meeting title."""
        with self._lock:
            if self._state:
                return self._state.title
            return None

    def add_tag(self, tag: str) -> bool:
        """Add a tag to the meeting.

        Args:
            tag: Tag to add (will be lowercased and trimmed).

        Returns:
            True if tag was added, False if already exists or invalid.
        """
        with self._lock:
            if self._state and tag.strip():
                clean_tag = tag.strip().lower()
                if clean_tag not in self._state.tags:
                    self._state.tags.append(clean_tag)
                    log.info(f"Tag added: {clean_tag}")
                    self._emit_broadcast("meeting_updated", {
                        "title": self._state.title,
                        "tags": self._state.tags,
                    })
                    return True
        return False

    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the meeting.

        Args:
            tag: Tag to remove.

        Returns:
            True if tag was removed, False if not found.
        """
        with self._lock:
            if self._state:
                clean_tag = tag.strip().lower()
                if clean_tag in self._state.tags:
                    self._state.tags.remove(clean_tag)
                    log.info(f"Tag removed: {clean_tag}")
                    self._emit_broadcast("meeting_updated", {
                        "title": self._state.title,
                        "tags": self._state.tags,
                    })
                    return True
        return False

    def set_tags(self, tags: list[str]) -> None:
        """Replace all tags with a new list.

        Args:
            tags: List of tags (will be lowercased and trimmed).
        """
        with self._lock:
            if self._state:
                self._state.tags = [t.strip().lower() for t in tags if t.strip()]
                log.info(f"Tags set: {self._state.tags}")
                self._emit_broadcast("meeting_updated", {
                    "title": self._state.title,
                    "tags": self._state.tags,
                })

    def get_tags(self) -> list[str]:
        """Get current meeting tags."""
        with self._lock:
            if self._state:
                return list(self._state.tags)
            return []
