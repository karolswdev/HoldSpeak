"""The live intel cadence (HS-63-02).

The should-run check, the analysis pass, and bookmark-label refinement,
moved verbatim out of MeetingSession; `self` is the session.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime
from typing import Any

from ..logging_config import get_logger

# Optional imports for intel (the same guarded pattern as session.py).
try:
    from ..intel import (
        IntelResult,
        ActionItem,
        get_intel_runtime_status,
        resolve_intel_provider,
    )
except ImportError:
    IntelResult = None  # type: ignore
    ActionItem = None  # type: ignore
    get_intel_runtime_status = None  # type: ignore
    resolve_intel_provider = None  # type: ignore

try:
    from ..speaker_intel import SpeakerDiarizer
except ImportError:
    SpeakerDiarizer = None  # type: ignore

from .models import IntelSnapshot

log = get_logger("meeting_session")


class IntelAnalysisMixin:
    def _maybe_run_intel(self) -> None:
        """Run intel analysis in background if not already running."""
        if not self._intel_live:
            return

        # Check if intel thread is already running
        if self._intel_thread is not None and self._intel_thread.is_alive():
            log.debug("Intel analysis already in progress, skipping")
            return

        self._segments_since_intel = 0
        self._set_intel_status("running", "Analyzing the latest transcript window.")
        self._intel_thread = threading.Thread(
            target=self._run_intel_analysis,
            daemon=True,
        )
        self._intel_thread.start()

    def _run_intel_analysis(self, final: bool = False) -> None:
        """Run one live analysis window as ONE admitted trusted child (HS-131-08).

        An empty transcript window and a window skipped because another is
        already running are not model work and admit nothing. Streamed tokens
        stay ephemeral; the snapshot lands only from the winning child receipt's
        staged projection, so a cancelled session cannot publish late output.

        HS-131-17: liveness is the explicit ``_intel_live`` state, not the
        presence of an engine object. The engine for this window is built inside
        the admitted child, from the plan's exact frozen revision.
        """
        if not self._intel_live:
            return

        # Get current transcript
        transcript = self.get_formatted_transcript()
        if not transcript:
            return

        log.info(f"Running intel analysis (final={final}, streaming=True)")

        # Generate a unique analysis ID to handle interruptions
        analysis_id = str(uuid.uuid4())[:8]
        self._current_analysis_id = analysis_id

        from .intel_plan import MeetingIntelRefused

        try:
            outcome, projection, result = self._admitted_live_window(
                transcript, final=final, analysis_id=analysis_id
            )
        except MeetingIntelRefused as exc:
            log.warning("Live analysis window refused: %s", exc.reason)
            self._set_intel_status(
                "refused", f"Meeting intelligence refused: {exc.reason}."
            )
            return
        except Exception as e:
            self._defer_or_error_intel(e)
            return

        if outcome.outcome != "succeeded":
            # A superseded window, a cancelled session, or an unknown provider
            # disposition never becomes meeting state.
            if outcome.outcome == "failed":
                # A provider that RETURNED an error result now closes its child
                # `failed` too (its receipt carries only the sanitized reason), so
                # the owner-facing deferral reason still comes from the in-memory
                # result — exactly the text this path reported before.
                provider_error = "" if result is None else str(
                    getattr(result, "error", "") or ""
                )
                self._defer_or_error_intel(
                    provider_error or outcome.error or "live analysis failed"
                )
            else:
                log.info(
                    "Live analysis window %s did not publish: %s",
                    analysis_id,
                    outcome.outcome,
                )
            return
        if projection is None:
            log.info("Live analysis window %s discarded before publication", analysis_id)
            return
        if result is None:
            self._defer_or_error_intel("live analysis returned no result")
            return
        if getattr(result, "error", None):
            self._defer_or_error_intel(result.error)
            return
        self._apply_live_window(result, final=final)

    def _defer_or_error_intel(self, error: Any) -> None:
        """The pre-existing deferred/error branch, shared by every failure path."""
        log.error(f"Intel analysis failed: {error}")
        # A failed provider leg is not live, whether the owner permits deferred
        # aftercare or asked for an immediate terminal error (HS-131-17).
        with self._lock:
            self._intel_live = False
        if self.intel_deferred_enabled:
            self._deferred_intel_reason = str(error)
            self._set_intel_status("queued", f"Deferred intel required: {error}")
        else:
            self._set_intel_status("error", str(error), completed_at=datetime.now())

    def _apply_live_window(self, result: Any, *, final: bool) -> bool:
        """Publish one earned live-analysis result into meeting state.

        HS-131-08 (D4): the apply is gated on the SAME election as the projection.
        The caller only reaches here from a successfully finalized projection, and
        the closed flag is re-checked UNDER THE SESSION LOCK — so a child that
        finalized just before ``stop()`` cancelled the parent can no longer stamp
        `ready` behind the handoff's `queued`. Returns whether the window landed.
        """
        # The routed path returns only the closed, elected result shape.  Rebuild
        # the domain objects here, after election, rather than letting an attempt
        # publish a provider object or token stream.
        if isinstance(result, dict):
            action_items = [
                ActionItem(
                    task=str(item.get("task") or ""),
                    owner=item.get("owner"),
                    due=item.get("due"),
                )
                for item in result.get("action_items", [])
                if isinstance(item, dict)
            ]
            topics = [str(topic) for topic in result.get("topics", [])]
            summary = str(result.get("summary") or "")
        else:
            action_items = result.action_items
            topics = result.topics
            summary = result.summary
        snapshot = IntelSnapshot(
            timestamp=self.duration,
            topics=topics,
            action_items=action_items,
            summary=summary,
        )

        # Update state
        with self._lock:
            if getattr(self, "_intel_closed", False):
                log.info(
                    "Discarding a late live-analysis window: the stop handoff already fired"
                )
                return False
            if self._state:
                self._state.intel = snapshot
                self._state.intel_status = "ready"
                self._state.intel_status_detail = (
                    "Meeting intelligence ready."
                    if not final
                    else "Final meeting intelligence ready."
                )
                self._state.intel_completed_at = datetime.now()

        # Emit completion to any observer (web dashboard)
        self._emit_broadcast("intel_complete", snapshot.to_dict())
        self._emit_broadcast(
            "intel_status",
            self._get_state_dict().get("intel_status", {}),
        )

        # Callback
        if self.on_intel:
            try:
                self.on_intel(snapshot)
            except Exception as e:
                log.error(f"on_intel callback error: {e}")

        log.info(f"Intel analysis complete: {len(snapshot.topics)} topics, {len(snapshot.action_items)} action items")

        # Refine bookmark labels with full meeting context (final pass only)
        if final:
            self._refine_bookmark_labels(snapshot.summary)
        return True

    def _refine_bookmark_labels(self, meeting_summary: str) -> None:
        """Refine all bookmark labels using full meeting context.

        Called during final analysis to improve bookmark labels with:
        - High-level meeting summary for grounding
        - Local ±10s context around each bookmark

        HS-131-17: the gate is the frozen plan's ``bookmark-label`` capability,
        never an engine object. A plan without it refuses by name inside the seam.
        """
        if self._state is None or not self._bookmark_label_admissible():
            return

        bookmarks = self._state.bookmarks
        if not bookmarks:
            return

        log.info(f"Refining {len(bookmarks)} bookmark labels with meeting context")

        from .intel_plan import MeetingIntelRefused

        for bookmark in bookmarks:
            try:
                # Get local context around bookmark
                local_context = self._state.get_context_around(bookmark.timestamp, window=10.0)
                if not local_context:
                    continue  # No transcript near this bookmark

                # HS-131-08: one admitted child per actual label dispatch
                # (holdspeak.meeting-bookmark-label@1). A capability absent from
                # the frozen plan refuses by name; it is never a direct call.
                _, projection, _ = self._admitted_bookmark_label(
                    local_context=local_context,
                    meeting_summary=meeting_summary,
                    timestamp=bookmark.timestamp,
                )
                label = str((projection or {}).get("label") or "")
                if label and label != bookmark.label:
                    old_label = bookmark.label
                    with self._lock:
                        bookmark.label = label
                    log.info(f"Refined bookmark: '{old_label}' -> '{label}'")

            except MeetingIntelRefused as exc:
                log.warning(
                    "Bookmark label refused at %.1fs: %s", bookmark.timestamp, exc.reason
                )
            except Exception as e:
                log.error(f"Failed to refine bookmark at {bookmark.timestamp:.1f}s: {e}")
