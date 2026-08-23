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
from .intel_admission import ROUTE_LIVE_ANALYSIS

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
        bundle = getattr(self, "_route_bundle", None)
        self._intel_live = False
        self._segments_since_intel = 0
        if self._state is None:
            return
        member = next(
            (
                item for item in (bundle or {}).get("members", ())
                if item.get("capability_id") == ROUTE_LIVE_ANALYSIS
            ),
            None,
        )
        if member is None:
            self._defer_live_intelligence(_NOT_ADMITTED)
            return

        # Read the frozen leg's own admission evidence.  A bundle member alone
        # proves selection, not that its first physical leg was eligible.
        from ..db import get_database

        with get_database()._connection() as conn:
            preflight = conn.execute(
                """SELECT eligibility,reason_code
                     FROM inference_route_plan_preflight_evidence
                    WHERE plan_id=? AND route_leg_ordinal=1""",
                (str(member["route_plan_id"]),),
            ).fetchone()
        if preflight is None or str(preflight["eligibility"]) == "known_preflight_unavailable":
            self._defer_live_intelligence(
                "" if preflight is None else str(preflight["reason_code"] or _UNAVAILABLE)
            )
            return

        # The bundle route is already frozen and preflighted.  Do not re-resolve
        # placement here: a first actual operation lets the controller interpret
        # the immutable availability evidence.
        self._intel_live = True
        self._deferred_intel_reason = None
        self._state.intel_status = "live"
        self._state.intel_status_detail = _DEFAULT_DETAIL
        log.info(
            "live meeting intelligence bundle ready: route=%s",
            member["route_plan_id"],
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
