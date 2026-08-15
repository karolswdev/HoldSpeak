"""Whether live meeting intelligence may schedule work (HS-131-17).

One concern only: turning the FROZEN plan's placement facts into the session's
explicit ``_intel_live`` state and an honest meeting status.

`MeetingSession.start()` used to preflight the provider runtime and then
construct a long-lived ``MeetingIntel`` beside the plan it had just frozen — a
model loaded merely to announce that a meeting is live. Both are gone. Placement
resolution already recorded, per capability, whether the planned leg is
reachable, so readiness is read from the plan and NOTHING is constructed here.
The first actual child builds the exact frozen revision inside
``InferenceRunner``; a construction or provider failure then takes the existing
queued/error path.
"""

from __future__ import annotations

from ..logging_config import get_logger
from .intel_plan import CAPABILITY_LIVE_ANALYSIS

log = get_logger("meeting_session")

#: The boundary a frozen placement names, and the sentence the meeting shows.
_BOUNDARY_DETAIL = {
    "same_device": "Local meeting intelligence active.",
    "external_service": "Cloud meeting intelligence active.",
}
_DEFAULT_DETAIL = "Meeting intelligence active."
_NOT_ADMITTED = "Live meeting analysis was not admitted."
_UNAVAILABLE = "Meeting intelligence unavailable."


class LiveReadinessMixin:
    """Decide live readiness from the frozen plan; construct nothing."""

    def _open_live_intelligence(self) -> None:
        """Set ``_intel_live`` and the meeting's intel status from plan facts.

        A plan whose live-analysis leg is not reachable — and that has no frozen
        cloud fallback to take instead — keeps the pre-existing behavior: the same
        `queued` (or `error`, with deferral off) status and the same sentence the
        runtime preflight produced, with no child and no engine.
        """
        plan = self._intel_plan
        self._intel_live = False
        self._segments_since_intel = 0
        if self._state is None:
            return
        if plan is None or not plan.has(CAPABILITY_LIVE_ANALYSIS):
            self._defer_live_intelligence(_NOT_ADMITTED)
            return

        placement = plan.placement(CAPABILITY_LIVE_ANALYSIS)
        planned_ready = bool(placement.get("target_ready"))
        fallback_frozen = str(placement.get("auto_cloud_fallback") or "") == "frozen"
        if not planned_ready and not fallback_frozen:
            self._defer_live_intelligence(str(placement.get("target_readiness_reason") or ""))
            return

        # The leg that would actually run names the boundary the owner is told
        # about: the planned target when it is ready, otherwise the frozen
        # fallback entry the first child would select.
        boundary = str(
            (
                placement.get("boundary")
                if planned_ready
                else placement.get("auto_cloud_fallback_boundary")
            )
            or ""
        )
        self._intel_live = True
        self._deferred_intel_reason = None
        self._state.intel_status = "live"
        self._state.intel_status_detail = _BOUNDARY_DETAIL.get(boundary, _DEFAULT_DETAIL)
        log.info(
            "live meeting intelligence ready: revision=%s boundary=%s",
            plan.primary(CAPABILITY_LIVE_ANALYSIS),
            boundary or "unknown",
        )

    def _defer_live_intelligence(self, reason: str) -> None:
        """The pre-existing not-ready branch, now fed by plan readiness facts."""
        if self._state is None:
            return
        self._deferred_intel_reason = reason or None
        if self.intel_deferred_enabled:
            self._state.intel_status = "queued"
            self._state.intel_status_detail = (
                f"Queued for later processing: {reason}"
                if reason
                else "Queued for later processing."
            )
        else:
            self._state.intel_status = "error"
            self._state.intel_status_detail = reason or _UNAVAILABLE


__all__ = ["LiveReadinessMixin"]
