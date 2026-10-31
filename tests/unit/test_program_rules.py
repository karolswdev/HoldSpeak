"""Programs §6 Control: one test per row of the table per level, and the
core-question list (``holdspeak/services/program_rules.py``)."""
from __future__ import annotations

import pytest

from holdspeak.services.program_rules import CoreQuestion, Decision, decide, is_core, level_of

S, N, Y = "secure", "normal", "yolo"


def _engine(outcome, choice):
    assert isinstance(outcome, Decision), outcome
    assert outcome.choice == choice and outcome.rule
    return outcome


def _him(outcome, *, core=False):
    assert isinstance(outcome, CoreQuestion), outcome
    assert outcome.core is core and outcome.rule
    return outcome


@pytest.mark.parametrize("level", [S, N, Y])
def test_routine_work_and_the_pr_are_the_engines_at_every_level(level) -> None:
    _engine(decide(level, "routine"), "act")
    _engine(decide(level, "open_pr"), "open")


@pytest.mark.parametrize("level, his", [(S, True), (N, False), (Y, False)])
def test_merge_on_green_and_pass(level, his) -> None:
    outcome = decide(level, "merge", {"check_green": True, "review_pass": True})
    if his:
        _him(outcome)
    else:
        assert "merges on a green check" in _engine(outcome, "merge").rule
        assert not outcome.overturnable  # a merge is never undone


@pytest.mark.parametrize("level", [S, N, Y])
def test_no_merge_without_green(level) -> None:
    _him(decide(level, "merge", {"check_green": False, "review_pass": True}))


@pytest.mark.parametrize("level, rounds_to_builder", [(S, 2), (N, 2), (Y, 3)])
def test_required_findings_go_back_then_to_him(level, rounds_to_builder) -> None:
    for done in range(rounds_to_builder):
        _engine(decide(level, "finding_required", {"round": done}), "fix")
    _him(decide(level, "finding_required", {"round": rounds_to_builder}))


def test_should_findings() -> None:
    _him(decide(S, "finding_should"))
    later = _engine(decide(N, "finding_should"), "later")
    assert later.overturnable
    _engine(decide(Y, "finding_should", {"round_open": True}), "fix")
    _engine(decide(Y, "finding_should", {"round_open": False}), "later")


@pytest.mark.parametrize("level", [S, N, Y])
def test_note_findings_are_skipped_and_logged(level) -> None:
    assert _engine(decide(level, "finding_note"), "skip").overturnable


def test_routine_agent_questions_follow_the_desks_responder() -> None:
    _him(decide(S, "agent_question", {"routine": True}))
    _engine(decide(N, "agent_question", {"routine": True}), "type_draft")
    _engine(decide(Y, "agent_question", {"routine": True}), "type_draft")
    _him(decide(Y, "agent_question", {"routine": False}), core=True)


def test_gate_approvals() -> None:
    _him(decide(S, "gate_approval", {"gate_allows": True}))
    _engine(decide(N, "gate_approval", {"gate_allows": True}), "allow")
    _engine(decide(Y, "gate_approval", {"gate_allows": True}), "allow")
    _him(decide(N, "gate_approval", {"gate_allows": False}), core=True)


@pytest.mark.parametrize("level, retries", [(S, 2), (N, 2), (Y, 3)])
def test_failed_check_rounds(level, retries) -> None:
    for done in range(retries):
        _engine(decide(level, "check_failed", {"round": done}), "retry")
    after = decide(level, "check_failed", {"round": retries})
    if level == S:
        _him(after)
    elif level == N:
        assert _engine(after, "park").overturnable
    else:
        _engine(after, "replan")
        _engine(decide(level, "check_failed", {"round": retries, "replanned": True}), "park")


def test_a_failed_step() -> None:
    _him(decide(S, "step_failed"))
    assert "carries on" in _engine(decide(N, "step_failed"), "park").rule
    _engine(decide(Y, "step_failed"), "replan")
    _engine(decide(Y, "step_failed", {"replanned": True}), "park")


def test_race_winner_add_step_and_done() -> None:
    _him(decide(S, "race_winner"))
    _engine(decide(N, "race_winner"), "pick")
    _engine(decide(Y, "race_winner"), "pick")
    _him(decide(S, "add_step"))
    _him(decide(N, "add_step"))
    assert _engine(decide(Y, "add_step"), "add").overturnable
    _him(decide(S, "program_done"))
    _engine(decide(N, "program_done"), "close")
    _engine(decide(Y, "program_done"), "close")


@pytest.mark.parametrize("facts, words", [
    ({"goal_change": True}, "goal"),
    ({"outside_repo": True}, "outside the program's repository"),
    ({"outside_owned": ["web/x.ts"]}, "no step owns (web/x.ts)"),
    ({"egress": True}, "send something"),
    ({"spend_usd": 0.5}, "no spend limit"),
    ({"spend_usd": 5, "spend_limit_usd": 2}, "limit of $2.00"),
    ({"authority": True}, "who or what may act"),
    ({"config": True}, "settings"),
    ({"gate_hold": True}, "gate holds"),
    ({"finding_text": "SQL injection in the search route"}, "security"),
    ({"finding_tags": ["security"]}, "security"),
    ({"finding_text": "this drops rows from the users table"}, "data loss"),
    ({"tests_deleted": True}, "deletes tests"),
    ({"destructive_migration": True}, "drops or rewrites rows"),
    ({"no_rule": True}, "no rule"),
])
def test_each_core_question_goes_to_him_at_every_level(facts, words) -> None:
    assert words in is_core(facts)
    for level in (S, N, Y):
        _him(decide(level, "merge", {"check_green": True, "review_pass": True, **facts}), core=True)


def test_not_core_and_the_ladder_words() -> None:
    assert is_core({}) == ""
    assert is_core({"spend_usd": 1, "spend_limit_usd": 5}) == ""
    assert is_core({"finding_text": "rename the variable"}) == ""
    assert [level_of(word) for word in ("safe", "neutral", "yolo", "SECURE", None)] == [S, N, Y, S, N]
    _him(decide(N, "something_new"), core=True)


# ── PG-REQ §6: the requirement rows, at each level ───────────────────

@pytest.mark.parametrize("level, rounds_to_builder", [(S, 2), (N, 2), (Y, 3)])
@pytest.mark.parametrize("kind, choice", [("requirement_red", "retry"), ("requirement_unmet", "fix")])
def test_a_red_or_unmet_requirement_goes_back_then_is_left(level, rounds_to_builder, kind, choice) -> None:
    for done in range(rounds_to_builder):
        _engine(decide(level, kind, {"round": done}), choice)
    left = decide(level, kind, {"round": rounds_to_builder})
    if level == S:
        _him(left)
    elif level == N:
        assert _engine(left, "park").overturnable
    else:
        _engine(left, "replan")
        assert _engine(decide(level, kind, {"round": rounds_to_builder, "replanned": True}), "park").overturnable


def test_an_unanswered_requirement() -> None:
    _him(decide(S, "requirement_unanswered"))
    for level in (N, Y):
        _engine(decide(level, "requirement_unanswered", {"asked": False}), "reask")
        _him(decide(level, "requirement_unanswered", {"asked": True}))


@pytest.mark.parametrize("level", [S, N, Y])
def test_your_word_holds_the_merge_at_every_level(level) -> None:
    _him(decide(level, "merge", {"check_green": True, "review_pass": True, "requirements_met": False}))


def test_requirement_left_by_level() -> None:
    _him(decide(S, "requirement_left"))
    assert _engine(decide(N, "requirement_left"), "park").overturnable
    _engine(decide(Y, "requirement_left"), "replan")
    _engine(decide(Y, "requirement_left", {"replanned": True}), "park")


def test_proposals_by_level() -> None:
    for kind, yolo in (("requirement_proposed", "add"), ("step_change", "apply"), ("step_amend", "send")):
        _him(decide(S, kind))
        _him(decide(N, kind))
        _engine(decide(Y, kind), yolo)
    assert decide(Y, "requirement_proposed").overturnable and decide(Y, "step_change").overturnable


@pytest.mark.parametrize("level", [S, N, Y])
def test_a_requirement_with_no_proof_is_a_core_question(level) -> None:
    _him(decide(level, "requirement_unprovable"), core=True)
