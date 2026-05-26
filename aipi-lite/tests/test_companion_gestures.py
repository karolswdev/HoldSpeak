"""Pure tests for the HS-22 companion gesture contract."""

from __future__ import annotations

import pytest

from bridge.companion_gestures import (
    REMOTE_GESTURES,
    CompanionAction,
    CompanionGesture,
    GestureOwner,
    resolve_gesture,
)
from bridge.companion_state import CompanionState


def test_remote_gesture_names_match_existing_cli_contract():
    assert REMOTE_GESTURES == {
        "left-short": CompanionGesture.LEFT_SINGLE_TAP,
        "left-long": CompanionGesture.LEFT_LONG_PRESS,
        "voice-typing": CompanionGesture.RIGHT_HOLD_TO_TALK,
    }


def test_left_single_tap_bookmarks_when_meeting_even_if_agent_waiting():
    decision = resolve_gesture(
        CompanionState.AGENT_WAITING,
        CompanionGesture.LEFT_SINGLE_TAP,
        meeting_recording=True,
    )

    assert decision.action == CompanionAction.BOOKMARK_MEETING
    assert decision.owner == GestureOwner.BRIDGE
    assert decision.wire_name == "long_press"


def test_left_double_tap_cycles_meeting_stats_when_meeting():
    decision = resolve_gesture(
        CompanionState.MEETING_RECORDING,
        CompanionGesture.LEFT_DOUBLE_TAP,
        meeting_recording=True,
    )

    assert decision.action == CompanionAction.CYCLE_MEETING_STATS
    assert decision.wire_name == "double_left_click"


def test_left_double_tap_agent_waiting_cycles_target_outside_meeting():
    decision = resolve_gesture(
        CompanionState.AGENT_WAITING,
        CompanionGesture.LEFT_DOUBLE_TAP,
        meeting_recording=False,
    )

    assert decision.action == CompanionAction.CYCLE_AGENT_TARGET
    assert decision.wire_name == "agent_next"


def test_left_double_tap_idle_outside_meeting_is_noop():
    decision = resolve_gesture(
        CompanionState.IDLE_CONNECTED,
        CompanionGesture.LEFT_DOUBLE_TAP,
        meeting_recording=False,
    )

    assert decision.action == CompanionAction.NOOP


def test_left_single_tap_agent_waiting_shows_question_outside_meeting():
    decision = resolve_gesture(
        CompanionState.AGENT_WAITING,
        CompanionGesture.LEFT_SINGLE_TAP,
        meeting_recording=False,
    )

    assert decision.action == CompanionAction.SHOW_AGENT_QUESTION
    assert decision.wire_name == "agent_question"


def test_left_single_tap_idle_shows_last_segment():
    decision = resolve_gesture(
        CompanionState.IDLE_CONNECTED,
        CompanionGesture.LEFT_SINGLE_TAP,
    )

    assert decision.action == CompanionAction.SHOW_LAST_SEGMENT
    assert decision.wire_name == "last_segment"


def test_right_hold_answers_agent_only_when_agent_waiting():
    waiting = resolve_gesture(
        CompanionState.AGENT_WAITING,
        CompanionGesture.RIGHT_HOLD_TO_TALK,
    )
    idle = resolve_gesture(
        CompanionState.IDLE_CONNECTED,
        CompanionGesture.RIGHT_HOLD_TO_TALK,
    )

    assert waiting.action == CompanionAction.START_AGENT_REPLY_CAPTURE
    assert waiting.wire_name == "start/stop"
    assert idle.action == CompanionAction.START_DICTATION_CAPTURE
    assert idle.wire_name == "start/stop"


def test_stale_agent_cannot_be_answered_by_voice():
    decision = resolve_gesture(
        CompanionState.STALE_CLEARED,
        CompanionGesture.RIGHT_HOLD_TO_TALK,
    )

    assert decision.action == CompanionAction.NOOP


def test_left_single_tap_clears_stale_agent():
    decision = resolve_gesture(
        CompanionState.STALE_CLEARED,
        CompanionGesture.LEFT_SINGLE_TAP,
    )

    assert decision.action == CompanionAction.CLEAR_STALE_AGENT


@pytest.mark.parametrize(
    "gesture",
    [
        CompanionGesture.LEFT_SINGLE_TAP,
        CompanionGesture.LEFT_DOUBLE_TAP,
        CompanionGesture.RIGHT_HOLD_TO_TALK,
    ],
)
def test_busy_suppresses_user_actions_except_firmware_ap_mode(gesture):
    decision = resolve_gesture(CompanionState.ERROR_BUSY, gesture)

    assert decision.action == CompanionAction.SUPPRESS_BUSY


def test_left_long_press_remains_firmware_ap_mode_even_when_busy():
    decision = resolve_gesture(
        CompanionState.ERROR_BUSY,
        CompanionGesture.LEFT_LONG_PRESS,
    )

    assert decision.action == CompanionAction.ENTER_AP_MODE
    assert decision.owner == GestureOwner.FIRMWARE
