"""Pure tests for the HS-22 AI PI companion state model."""

from __future__ import annotations

from bridge.companion_state import (
    AGENT_STALE_AFTER_S,
    STALE_CLEAR_FLASH_MS,
    STATE_CONTRACTS,
    CompanionOwner,
    CompanionSignals,
    CompanionState,
    LcdLifetime,
    build_lcd_plan,
    is_agent_stale,
)
from bridge.lcd import ERROR_FLASH_MS, LINK_OFFLINE, LINK_ONLINE, SESSION_BUSY_FLASH_MS


def test_state_contract_covers_every_state():
    assert set(STATE_CONTRACTS) == set(CompanionState)
    assert all(contract.owner in CompanionOwner for contract in STATE_CONTRACTS.values())


def test_idle_connected_plan():
    plan = build_lcd_plan(CompanionSignals())

    assert plan.primary_state == CompanionState.IDLE_CONNECTED
    assert plan.top_right.text == LINK_ONLINE
    assert plan.bottom.text == "Ready"
    assert plan.middle.lifetime == LcdLifetime.CLEAR


def test_disconnected_link_wins_primary_state():
    plan = build_lcd_plan(
        CompanionSignals(connected=False, meeting_recording=True, agent_waiting=True)
    )

    assert plan.primary_state == CompanionState.DISCONNECTED
    assert plan.top_right.text == LINK_OFFLINE
    assert plan.bottom.text == "Recording"


def test_meeting_recording_is_bottom_baseline():
    plan = build_lcd_plan(CompanionSignals(meeting_recording=True))

    assert plan.primary_state == CompanionState.MEETING_RECORDING
    assert plan.bottom.text == "Recording"
    assert plan.bottom.lifetime == LcdLifetime.STICKY
    assert plan.middle.text == ""


def test_agent_waiting_uses_middle_without_clobbering_meeting():
    plan = build_lcd_plan(
        CompanionSignals(
            meeting_recording=True,
            agent_waiting=True,
            agent_label="Codex",
            agent_question="Run the hardware check?",
            agent_age_s=15,
        )
    )

    assert plan.primary_state == CompanionState.AGENT_WAITING
    assert plan.bottom.text == "Recording"
    assert plan.middle.text == "Codex waiting\nRun the hardware check?"
    assert plan.middle.lifetime == LcdLifetime.STICKY


def test_reply_capture_supersedes_waiting_question():
    plan = build_lcd_plan(
        CompanionSignals(
            agent_waiting=True,
            agent_label="Claude",
            agent_question="Proceed?",
            reply_capture=True,
        )
    )

    assert plan.primary_state == CompanionState.REPLY_CAPTURE
    assert plan.bottom.text == "Listening..."
    assert plan.middle.text == "Replying to Claude"


def test_transcribing_sets_bottom_but_does_not_hide_agent_waiting():
    plan = build_lcd_plan(
        CompanionSignals(
            transcribing=True,
            agent_waiting=True,
            agent_label="Codex",
            agent_question="Commit this?",
        )
    )

    assert plan.primary_state == CompanionState.AGENT_WAITING
    assert plan.bottom.text == "Transcribing..."
    assert plan.middle.text == "Codex waiting\nCommit this?"


def test_busy_and_error_are_middle_flash_priority():
    busy = build_lcd_plan(CompanionSignals(agent_waiting=True, busy=True))
    error = build_lcd_plan(
        CompanionSignals(agent_waiting=True, error_text="text insertion failed")
    )

    assert busy.primary_state == CompanionState.ERROR_BUSY
    assert busy.middle.text == "Busy"
    assert busy.middle.lifetime == LcdLifetime.FLASH
    assert busy.middle.ttl_ms == SESSION_BUSY_FLASH_MS
    assert error.primary_state == CompanionState.ERROR_BUSY
    assert error.middle.text == "Error: text insertion failed"
    assert error.middle.ttl_ms == ERROR_FLASH_MS


def test_stale_agent_question_clears_instead_of_showing_old_question():
    signals = CompanionSignals(
        agent_waiting=True,
        agent_label="Codex",
        agent_question="Old question?",
        agent_age_s=AGENT_STALE_AFTER_S + 1,
    )
    plan = build_lcd_plan(signals)

    assert is_agent_stale(signals) is True
    assert plan.primary_state == CompanionState.STALE_CLEARED
    assert plan.middle.text == "Agent stale; cleared"
    assert plan.middle.lifetime == LcdLifetime.FLASH
    assert plan.middle.ttl_ms == STALE_CLEAR_FLASH_MS


def test_agent_question_at_exact_freshness_boundary_is_still_fresh():
    signals = CompanionSignals(
        agent_waiting=True,
        agent_label="Codex",
        agent_question="Still valid?",
        agent_age_s=AGENT_STALE_AFTER_S,
    )
    plan = build_lcd_plan(signals)

    assert is_agent_stale(signals) is False
    assert plan.primary_state == CompanionState.AGENT_WAITING
    assert plan.middle.text == "Codex waiting\nStill valid?"


def test_transcript_flash_is_below_agent_attention():
    transcript_only = build_lcd_plan(
        CompanionSignals(transcript_flash="Karol: yes, continue")
    )
    with_agent = build_lcd_plan(
        CompanionSignals(
            agent_waiting=True,
            agent_label="Claude",
            agent_question="Answer me?",
            transcript_flash="Karol: yes, continue",
        )
    )

    assert transcript_only.primary_state == CompanionState.IDLE_CONNECTED
    assert transcript_only.middle.text == "Karol: yes, continue"
    assert transcript_only.middle.lifetime == LcdLifetime.PERSIST_UNTIL_REPLACED
    assert with_agent.primary_state == CompanionState.AGENT_WAITING
    assert with_agent.middle.text == "Claude waiting\nAnswer me?"
