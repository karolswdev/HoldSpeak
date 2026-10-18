"""The desk's own answers (Betterment agents, AG0's part of AG3).

RECON step 10: under YOLO the question offered "Answer 1 for config, 2 for
env" and the desk typed `Yes, "The rollback flag moves into
config/flags.yaml."` into the agent. That draft is the recorded LAN draft
(qwen3.8-27b, the recon walk); here the guard makes it REAL (the owner's),
and a draft that picks a choice stays ROUTINE.
"""
from __future__ import annotations

from holdspeak.services.agent_responder import REAL, ROUTINE, Draft, guard, offered_choices, picked_choice

QUESTION = ("I found two places for the rollback flag. Should it live in "
            "config/flags.yaml (shared with staging) or in an env var (per host)? "
            "Answer 1 for config, 2 for env.")
BRIEF = "Decision: The rollback flag moves into config/flags.yaml.\nOwner: Theo, due Friday."
RECORDED = 'Yes, "The rollback flag moves into config/flags.yaml."'


def test_the_choices_a_question_offers():
    assert offered_choices(QUESTION) == ["1", "2"]
    assert offered_choices("Do you want to proceed?\n ❯ 1. Yes\n   2. No, and tell Claude") == ["1", "2"]
    assert offered_choices("Should I run the tests?") == []
    assert offered_choices("I ran 3 for the suite. Should I push?") == []


def test_a_choice_question_answered_yes_is_real():
    draft = guard(QUESTION, Draft(ROUTINE, "the brief names the file", RECORDED), BRIEF)
    assert draft.verdict == REAL
    assert "picks none" in draft.reason


def test_a_choice_question_answered_with_a_choice_stays_routine():
    answer = '1, "The rollback flag moves into config/flags.yaml."'
    assert picked_choice(answer, ["1", "2"]) == "1"
    assert guard(QUESTION, Draft(ROUTINE, "the brief names the file", answer), BRIEF).verdict == ROUTINE
    assert picked_choice('3, "x"', ["1", "2"]) is None


def test_a_yes_no_question_is_unchanged():
    question = "Should I keep the flag in config/flags.yaml?"
    assert guard(question, Draft(ROUTINE, "brief", RECORDED), BRIEF).verdict == ROUTINE
