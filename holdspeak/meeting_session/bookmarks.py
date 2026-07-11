"""Bookmark creation and read-only transcript views for a meeting session."""
from __future__ import annotations

import threading
from typing import Optional

from ..logging_config import get_logger
from .models import Bookmark, TranscriptSegment

log = get_logger("meeting_session")


class BookmarkViewsMixin:
    def add_bookmark(self, label: str = "", auto_label: bool = True) -> Optional[Bookmark]:
        """Add a bookmark at the current time, optionally labeling it from context."""
        with self._lock:
            if self._state is None or not self._state.is_active:
                return None

            timestamp = self._state.duration
            mins = int(timestamp // 60)
            secs = int(timestamp % 60)
            bookmark = Bookmark(
                timestamp=timestamp,
                label=label or f"Bookmark @ {mins:02d}:{secs:02d}",
            )
            self._state.bookmarks.append(bookmark)
            log.info(f"Bookmark added at {bookmark.timestamp:.1f}s: {bookmark.label}")

            if not label and auto_label and self._intel is not None:
                context = self._state.get_context_around(timestamp, window=10.0)
                if context:
                    threading.Thread(
                        target=self._generate_bookmark_label,
                        args=(bookmark, context),
                        daemon=True,
                    ).start()
            return bookmark

    def _generate_bookmark_label(self, bookmark: Bookmark, context: str) -> None:
        """Generate and update a bookmark label in the background."""
        try:
            if self._intel is None:
                return
            label = self._intel.generate_bookmark_label(context)
            if label:
                with self._lock:
                    bookmark.label = label
                log.info(f"Bookmark label updated: {label}")
        except Exception as exc:
            log.error(f"Bookmark label generation failed: {exc}")

    def get_transcript(self) -> list[TranscriptSegment]:
        """Get all transcript segments."""
        with self._lock:
            if self._state is None:
                return []
            return list(self._state.segments)

    def get_bookmarks(self) -> list[Bookmark]:
        """Get all bookmarks."""
        with self._lock:
            if self._state is None:
                return []
            return list(self._state.bookmarks)

    def get_formatted_transcript(self) -> str:
        """Get transcript as formatted text."""
        return "\n".join(str(segment) for segment in self.get_transcript())
