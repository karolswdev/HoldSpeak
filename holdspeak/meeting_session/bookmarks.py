"""Bookmark creation and read-only transcript views for a meeting session."""
from __future__ import annotations

import threading
from typing import Optional

from ..logging_config import get_logger
from .intel_admission import ROUTE_BOOKMARK_LABEL, MeetingIntelRefused
from .models import Bookmark, TranscriptSegment

log = get_logger("meeting_session")


class BookmarkViewsMixin:
    def add_bookmark(self, label: str = "", auto_label: bool = True) -> Optional[Bookmark]:
        """Add a bookmark at the current time, optionally labeling it from context.

        The DETERMINISTIC timestamp label is created first and is what the owner
        keeps unless an admitted model attempt earns a better one (HS-131-17).
        Automatic refinement runs only when the frozen plan carries
        ``bookmark-label`` and the live parent is still open, and it goes through
        ``_admitted_bookmark_label`` — one trusted child, one terminal receipt —
        never a direct engine call.
        """
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

            if label or not auto_label or not self._bookmark_label_admissible():
                return bookmark
            context = self._state.get_context_around(timestamp, window=10.0)
            if not context:
                # No transcript near this bookmark: there is nothing to label from,
                # so no model work exists and no child is admitted.
                return bookmark
            # The latest EARNED meeting summary grounds the label; an empty string
            # when no live window has published one yet.
            summary = str(getattr(self._state.intel, "summary", "") or "")
            threading.Thread(
                target=self._generate_bookmark_label,
                args=(bookmark, context, summary),
                daemon=True,
            ).start()
            return bookmark

    def _bookmark_label_admissible(self) -> bool:
        """Whether an automatic label may be attempted at all.

        Liveness is the explicit session state and the capability comes from the
        FROZEN plan — never from the presence of an engine object.
        """
        bundle = getattr(self, "_route_bundle", None)
        return bool(
            self._intel_live
            and not self._intel_closed
            and self._intel_parent is not None
            and any(
                item.get("capability_id") == ROUTE_BOOKMARK_LABEL
                for item in (bundle or {}).get("members", ())
            )
        )

    def _generate_bookmark_label(
        self, bookmark: Bookmark, context: str, meeting_summary: str = ""
    ) -> None:
        """Refine one bookmark label through the ONE admitted seam.

        Refusal, cancellation, provider failure, and a discarded projection all
        leave the deterministic label exactly as it was. A stop that wins the race
        raised ``_intel_closed``, and a late label may not overwrite what the
        handoff already published.
        """
        try:
            _, projection, _ = self._admitted_bookmark_label(
                local_context=context,
                meeting_summary=meeting_summary,
                timestamp=bookmark.timestamp,
            )
        except MeetingIntelRefused as exc:
            log.warning(
                "Bookmark label refused at %.1fs: %s", bookmark.timestamp, exc.reason
            )
            return
        except Exception as exc:
            log.error(f"Bookmark label generation failed: {exc}")
            return

        label = str((projection or {}).get("label") or "")
        if not label:
            log.info("Bookmark label at %.1fs did not publish", bookmark.timestamp)
            return
        with self._lock:
            if self._intel_closed:
                log.info("Discarding a late bookmark label: the stop handoff already fired")
                return
            bookmark.label = label
        log.info(f"Bookmark label updated: {label}")

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
