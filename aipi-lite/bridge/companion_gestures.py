"""Pure HS-22 gesture contract for AI PI companion actions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from bridge.companion_state import CompanionState


class CompanionGesture(str, Enum):
    LEFT_SINGLE_TAP = "left_single_tap"
    LEFT_DOUBLE_TAP = "left_double_tap"
    LEFT_LONG_PRESS = "left_long_press"
    RIGHT_HOLD_TO_TALK = "right_hold_to_talk"


class CompanionAction(str, Enum):
    BOOKMARK_MEETING = "bookmark_meeting"
    CYCLE_MEETING_STATS = "cycle_meeting_stats"
    SHOW_LAST_SEGMENT = "show_last_segment"
    SHOW_AGENT_QUESTION = "show_agent_question"
    CYCLE_AGENT_TARGET = "cycle_agent_target"
    START_AGENT_REPLY_CAPTURE = "start_agent_reply_capture"
    START_DICTATION_CAPTURE = "start_dictation_capture"
    CLEAR_STALE_AGENT = "clear_stale_agent"
    ENTER_AP_MODE = "enter_ap_mode"
    SUPPRESS_BUSY = "suppress_busy"
    NOOP = "noop"


class GestureOwner(str, Enum):
    BRIDGE = "bridge"
    FIRMWARE = "firmware"
    HOLDSPEAK = "holdspeak"


@dataclass(frozen=True)
class GestureDecision:
    gesture: CompanionGesture
    state: CompanionState
    action: CompanionAction
    owner: GestureOwner
    wire_name: str | None = None
    reason: str = ""


REMOTE_GESTURES: dict[str, CompanionGesture] = {
    "left-short": CompanionGesture.LEFT_SINGLE_TAP,
    "left-long": CompanionGesture.LEFT_LONG_PRESS,
    "voice-typing": CompanionGesture.RIGHT_HOLD_TO_TALK,
}


def resolve_gesture(
    state: CompanionState,
    gesture: CompanionGesture,
    *,
    meeting_recording: bool = False,
) -> GestureDecision:
    """Return the deterministic action for a gesture in the current state.

    `meeting_recording` intentionally remains an explicit signal because some
    middle-priority states, such as `agent_waiting`, can coexist with the
    meeting bottom baseline. Meeting gestures stay deterministic in that case.
    """

    if gesture == CompanionGesture.LEFT_LONG_PRESS:
        return GestureDecision(
            gesture=gesture,
            state=state,
            action=CompanionAction.ENTER_AP_MODE,
            owner=GestureOwner.FIRMWARE,
            reason="Left long-press keeps the existing firmware AP-mode behavior.",
        )

    if state == CompanionState.ERROR_BUSY:
        return GestureDecision(
            gesture=gesture,
            state=state,
            action=CompanionAction.SUPPRESS_BUSY,
            owner=GestureOwner.BRIDGE,
            reason="Do not start another capture or emit meeting events while HoldSpeak is busy.",
        )

    if gesture == CompanionGesture.RIGHT_HOLD_TO_TALK:
        if state == CompanionState.STALE_CLEARED:
            return GestureDecision(
                gesture=gesture,
                state=state,
                action=CompanionAction.NOOP,
                owner=GestureOwner.BRIDGE,
                reason="Stale agent context is not replyable.",
            )
        if state == CompanionState.AGENT_WAITING:
            return GestureDecision(
                gesture=gesture,
                state=state,
                action=CompanionAction.START_AGENT_REPLY_CAPTURE,
                owner=GestureOwner.FIRMWARE,
                wire_name="start/stop",
                reason="Explicit user speech answers the waiting agent through the existing voice path.",
            )
        return GestureDecision(
            gesture=gesture,
            state=state,
            action=CompanionAction.START_DICTATION_CAPTURE,
            owner=GestureOwner.FIRMWARE,
            wire_name="start/stop",
            reason="Normal hold-to-talk dictation path.",
        )

    if gesture == CompanionGesture.LEFT_DOUBLE_TAP:
        if meeting_recording:
            return GestureDecision(
                gesture=gesture,
                state=state,
                action=CompanionAction.CYCLE_MEETING_STATS,
                owner=GestureOwner.BRIDGE,
                wire_name="double_left_click",
                reason="Preserve existing meeting-stat cycle gesture.",
            )
        if state == CompanionState.AGENT_WAITING:
            return GestureDecision(
                gesture=gesture,
                state=state,
                action=CompanionAction.CYCLE_AGENT_TARGET,
                owner=GestureOwner.BRIDGE,
                wire_name="agent_next",
                reason="Outside a meeting, double-tap cycles the selected waiting agent.",
            )
        return GestureDecision(
            gesture=gesture,
            state=state,
            action=CompanionAction.NOOP,
            owner=GestureOwner.BRIDGE,
            reason="Double-tap has no meaning outside an active meeting.",
        )

    if gesture == CompanionGesture.LEFT_SINGLE_TAP:
        if meeting_recording:
            return GestureDecision(
                gesture=gesture,
                state=state,
                action=CompanionAction.BOOKMARK_MEETING,
                owner=GestureOwner.BRIDGE,
                wire_name="long_press",
                reason="Preserve existing meeting bookmark gesture.",
            )
        if state == CompanionState.STALE_CLEARED:
            return GestureDecision(
                gesture=gesture,
                state=state,
                action=CompanionAction.CLEAR_STALE_AGENT,
                owner=GestureOwner.BRIDGE,
                reason="A stale agent question can be cleared but not answered.",
            )
        if state == CompanionState.AGENT_WAITING:
            return GestureDecision(
                gesture=gesture,
                state=state,
                action=CompanionAction.SHOW_AGENT_QUESTION,
                owner=GestureOwner.BRIDGE,
                wire_name="agent_question",
                reason="Outside a meeting, left tap reveals the waiting question.",
            )
        return GestureDecision(
            gesture=gesture,
            state=state,
            action=CompanionAction.SHOW_LAST_SEGMENT,
            owner=GestureOwner.BRIDGE,
            wire_name="last_segment",
            reason="Preserve existing outside-meeting last-segment query.",
        )

    return GestureDecision(
        gesture=gesture,
        state=state,
        action=CompanionAction.NOOP,
        owner=GestureOwner.BRIDGE,
        reason="Gesture is intentionally unassigned.",
    )


__all__ = [
    "REMOTE_GESTURES",
    "CompanionAction",
    "CompanionGesture",
    "GestureDecision",
    "GestureOwner",
    "resolve_gesture",
]
