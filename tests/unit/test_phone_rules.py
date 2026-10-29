"""Phone (2026-10-28): the Reach table per row and level (design §6)."""
from __future__ import annotations

import pytest

from holdspeak.phone.phone_rules import Hold, Reach, reach

WAITED = {"messaged": True, "minutes_without_reply": 11}


@pytest.mark.parametrize("kind,level,facts,want", [
    ("core_question", "secure", {"may_call": True}, "message"),
    ("core_question", "normal", {"may_call": True}, "message"),
    ("core_question", "normal", {"may_call": True, **WAITED}, "call"),
    ("core_question", "normal", {"may_call": False, **WAITED}, "message"),
    ("core_question", "yolo", {"may_call": True}, "call"),
    ("core_question", "yolo", {}, "message"),
    ("step_red", "secure", {"may_call": True, "night_program": True}, "message"),
    ("step_red", "normal", {"may_call": True, "night_program": True}, "message"),
    ("step_red", "yolo", {"may_call": True}, "message"),
    ("step_red", "yolo", {"may_call": True, "night_program": True}, "call"),
    ("program_done", "secure", {}, None),
    ("program_done", "normal", {}, "message"),
    ("program_done", "yolo", {}, "message"),
    ("heartbeat_security", "secure", {}, "message"),
    ("heartbeat_security", "normal", {}, "call"),
    ("heartbeat_security", "yolo", {}, "call_urgent"),
    ("aftercare", "secure", {}, None),
    ("aftercare", "normal", {}, "message"),
    ("aftercare", "yolo", {}, "message"),
    ("agent_question", "secure", {}, "message"),
    ("agent_question", "normal", {**WAITED}, "message"),
    ("agent_question", "normal", {**WAITED, "away": True}, "call"),
    ("agent_question", "yolo", {}, "call"),
])
def test_the_table_row_by_row(kind: str, level: str, facts: dict, want: str | None) -> None:
    outcome = reach(level, kind, facts)
    if want is None:
        assert isinstance(outcome, Hold) and not outcome.queued
        return
    assert isinstance(outcome, Reach), outcome
    assert outcome.channel == ("call" if want.startswith("call") else "message")
    assert outcome.urgent == (want == "call_urgent")
    assert outcome.rule


def test_his_own_word_wins_over_the_level() -> None:
    assert isinstance(reach("normal", "program_done", {"word": "nothing"}), Hold)
    assert reach("yolo", "agent_question", {"word": "message"}).channel == "message"
    assert reach("secure", "aftercare", {"word": "call"}).channel == "call"


def test_a_reply_ends_it_and_never_twice_in_five_minutes() -> None:
    assert reach("yolo", "core_question", {"may_call": True, "replied": True}).reason == "he answered the message"
    held = reach("normal", "program_done", {"recent_minutes": 2})
    assert isinstance(held, Hold) and "5 minutes" in held.rule
    assert isinstance(reach("normal", "program_done", {"recent_minutes": 6}), Reach)


def test_no_call_while_a_call_is_on() -> None:
    outcome = reach("yolo", "agent_question", {"call_active": True})
    assert isinstance(outcome, Reach) and outcome.channel == "message" and "a call is on" in outcome.rule


def test_quiet_hours_queue_a_message_and_let_only_urgent_ring() -> None:
    message = reach("normal", "program_done", {"quiet": True})
    assert isinstance(message, Hold) and message.queued
    call = reach("normal", "heartbeat_security", {"quiet": True})
    assert isinstance(call, Hold) and call.queued and "urgent" in call.reason
    urgent = reach("yolo", "heartbeat_security", {"quiet": True})
    assert isinstance(urgent, Reach) and urgent.channel == "call" and urgent.urgent


def test_an_unknown_kind_and_the_desk_words_for_the_levels() -> None:
    assert isinstance(reach("yolo", "lunch", {}), Hold)
    assert reach("safe", "program_done", {}).held  # the desk's Safe is Secure
    assert reach("neutral", "program_done", {}).channel == "message"
