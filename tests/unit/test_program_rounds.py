"""PG-LANG LANG9 (2026-10-31): the interview rounds.

PROGRAM-LANGUAGE-2026-10-31.md §6.2, §6.5 station 3, §12. From a planning
draft, named rounds ask ONE question at a time; his answer is the ``=`` line
and one shaping call turns it into change rows that wait for Apply (source
``round:<name>``); Skip question, Skip round, Done with <round> (withheld
while a question waits), Ask more; rounds never gate Start; ``?`` lines are
the engine's. The engine's questions and shaped answers are REAL replies of
qwen3.8-27b on the home engine (tests/fixtures/program_round_reply.json,
written by scripts/record_program_round_reply.py over journey J1 at station
3, tests/integration/program_rounds_seed.py), replayed through the runner's
engine seam, never typed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from holdspeak.services import program_rounds
from holdspeak.services.program_service import ProgramRefused
from holdspeak.services.program_text import print_program
from tests.integration.program_rig import OWNER, Rig
from tests.integration.program_rounds_seed import drafted
from tests.unit.test_program_shaper import wire_engine

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
RECORDED = json.loads((FIXTURES / "program_round_reply.json").read_text(encoding="utf-8"))
MODEL = RECORDED["engine"]["model"]


STEPS = {row["label"]: row for row in RECORDED["sequence"]}


def recorded(label: str) -> dict[str, Any]:
    return STEPS[label]


def ask_reply(name: str) -> str:
    return recorded(f"{name.lower()}.next")["exchanges"][0]["reply_text"]


def shape_reply(name: str) -> str:
    return recorded(f"{name.lower()}.answer")["exchanges"][0]["reply_text"]


def said(name: str) -> str:
    return recorded(f"{name.lower()}.answer")["question"]["answer"]


@pytest.fixture
def desk(tmp_path, monkeypatch):
    rig = Rig(tmp_path)
    rig.engine = wire_engine(rig, monkeypatch)
    rig.pid = drafted(rig)
    return rig


def _wire(rig: Rig) -> dict[str, Any]:
    return rig.service.get(OWNER, rig.pid)


def _round(rig: Rig, name: str) -> dict[str, Any]:
    return next(row for row in _wire(rig)["rounds"] if row["name"] == name)


def _ask(rig: Rig, name: str) -> dict[str, Any]:
    rig.engine.replies = [ask_reply(name)]
    return program_rounds.ask(rig.service, OWNER, rig.pid, name)


# ── open ─────────────────────────────────────────────────────────────

def test_open_makes_the_five_default_rounds_once(desk) -> None:
    out = program_rounds.open_rounds(desk.service, OWNER, desk.pid)
    assert out["added"] == ["Architecture", "Product", "Stack", "Verification", "Delivery"]
    assert [(row["name"], row["state"], row["order"]) for row in out["program"]["rounds"]] == [
        ("Architecture", "open", 1), ("Product", "open", 2), ("Stack", "open", 3), ("Verification", "open", 4),
        ("Delivery", "open", 5)]
    again = program_rounds.open_rounds(desk.service, OWNER, desk.pid, ["Architecture", "Security"])
    assert again["added"] == ["Security"]
    assert [row["name"] for row in _wire(desk)["rounds"]][-1] == "Security"
    assert "\nround Architecture · open\n" in print_program(_wire(desk))


# ── ask (the recorded question) ──────────────────────────────────────

def test_ask_sends_the_round_contract_and_stores_one_question(desk) -> None:
    program_rounds.open_rounds(desk.service, OWNER, desk.pid)
    out = _ask(desk, "Architecture")
    (prompt,) = desk.engine.prompts
    system, user = prompt["system_prompt"], prompt["user_prompt"]
    assert "RULES FOR A QUESTION" in system and "THE PROGRAM TEXT (version 1)" in system
    assert prompt["response_format"]["json_schema"]["name"] == "program_round"
    assert prompt["response_format"]["json_schema"]["schema"]["required"] == ["question", "why_it_matters", "choices", "done"]
    assert "THE ROUND: Architecture\nIn this round you ask about the boundaries, the data, what must not change, " \
           "where the risk is." in user
    text_part = user.split("THE PROGRAM TEXT NOW\n", 1)[1].split("\n\nTHE ROUND", 1)[0]
    assert "step 3 Wire recap into meeting Stop" in text_part and "  # " not in text_part
    assert "FILES THE GOAL IS LIKELY ABOUT" in user
    want = recorded("architecture.next")["question"]
    question = out["question"]
    assert (question["text"], question["why"], question["choices"]) == (want["text"], want["why"], want["choices"])
    assert out["engine"] == MODEL and out["done"] is False
    row = _round(desk, "Architecture")
    assert row["state"] == "asking" and row["waiting"] == question["id"] and row["asked"] == 1
    assert f"round Architecture · asking\n  ? {want['text']}\n" in print_program(_wire(desk))
    # One at a time: asking again answers the waiting question, with no call.
    again = program_rounds.ask(desk.service, OWNER, desk.pid, "Architecture")
    assert again["question"]["id"] == question["id"] and len(desk.engine.prompts) == 1


def test_ask_opens_the_defaults_when_the_program_has_no_round(desk) -> None:
    _ask(desk, "Architecture")
    assert [row["name"] for row in _wire(desk)["rounds"]] == list(program_rounds.DEFAULT_ROUNDS)


def test_ask_with_no_engine_is_refused_by_name(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    rig.engine = wire_engine(rig, monkeypatch)
    rig.pid = drafted(rig)
    from holdspeak.services import program_shaper

    def no_engine(_db):
        raise program_shaper._refused("no_engine", "No engine is set for planning.")

    monkeypatch.setattr(program_shaper, "resolve_engine", no_engine)
    with pytest.raises(ProgramRefused) as caught:
        program_rounds.ask(rig.service, OWNER, rig.pid, "Architecture")
    assert caught.value.code == "no_engine"
    assert _round(rig, "Architecture")["asked"] == 0


# ── answer → rows ────────────────────────────────────────────────────

def test_an_answer_is_the_equals_line_and_one_shaping_call_whose_rows_wait(desk) -> None:
    asked = _ask(desk, "Architecture")
    before = _wire(desk)
    words = said("Architecture")
    assert words == asked["question"]["choices"][0]
    desk.engine.replies = [shape_reply("Architecture")]
    out = program_rounds.answer(desk.service, OWNER, desk.pid, "Architecture", None, choice=words)
    prompt = desk.engine.prompts[-1]
    assert prompt["response_format"]["json_schema"]["name"] == "program_shape"
    sentence = prompt["user_prompt"].split("THE SENTENCE\n", 1)[1]
    assert sentence.startswith(f"In the Architecture round, to '{asked['question']['text']}' (")
    assert f", the owner said '{words}'. Write this answer into the plan" in sentence
    # The round blocks never reach the shaping engine.
    assert "round Architecture" not in prompt["user_prompt"]
    assert [(row["op"], row["where"], row["field"], row["verdict"]) for row in out["changes"]] == [
        (row["op"], row["where"], row["field"], row["verdict"]) for row in recorded("architecture.answer")["changes"]]
    assert [(row["where"], row["field"], row["verdict"]) for row in out["changes"]] == [("step 3", "brief", "allowed")]
    assert {row["source"] for row in out["changes"]} == {"round:Architecture"} and out["applied"] is False
    assert out["round_question"]["became"] == ["step 3 brief"]
    # Nothing in the plan moved; the answer and what it became are on the round.
    after = _wire(desk)
    assert [step["brief"] for step in after["steps"]] == [step["brief"] for step in before["steps"]]
    row = _round(desk, "Architecture")
    assert row["answered"] == 1 and row["waiting"] is None and row["became"] == 1
    assert row["questions"][0]["answer"] == words and row["questions"][0]["answered_by"] == "owner"
    text = print_program(after)
    assert f"  = {words}" in text and "# → step 3 brief" in text
    # Apply: the rows land through the text.
    applied = desk.service.text_apply(OWNER, desk.pid, out["allowed_text"], dry_run=False, base=out["base"])
    assert applied["applied"] is True
    briefs = {step["ordinal"]: step["brief"] for step in applied["program"]["steps"]}
    assert briefs[3] != before["steps"][2]["brief"] and briefs[4] == before["steps"][3]["brief"]
    assert _round(desk, "Architecture")["questions"][0]["answer"] == words


def test_not_this_keeps_the_answer_and_it_became_nothing(desk) -> None:
    asked = _ask(desk, "Architecture")
    desk.engine.replies = [shape_reply("Architecture")]
    program_rounds.answer(desk.service, OWNER, desk.pid, "Architecture", said("Architecture"))
    program_rounds.not_this(desk.service, OWNER, desk.pid, "Architecture", asked["question"]["id"])
    row = _round(desk, "Architecture")
    assert row["questions"][0]["answer"] and row["questions"][0]["became"] == [] and row["became"] == 0


def test_an_answer_with_no_waiting_question_is_refused(desk) -> None:
    program_rounds.open_rounds(desk.service, OWNER, desk.pid)
    with pytest.raises(ProgramRefused) as caught:
        program_rounds.answer(desk.service, OWNER, desk.pid, "Architecture", "In the hub")
    assert caught.value.code == "no_question"


# ── skip, done, reopen ───────────────────────────────────────────────

def test_skip_question_then_done_with_the_round(desk) -> None:
    asked = _ask(desk, "Architecture")
    with pytest.raises(ProgramRefused) as caught:
        program_rounds.decide(desk.service, OWNER, desk.pid, "Architecture", "done")
    assert caught.value.code == "round_question_waits"
    program_rounds.skip_question(desk.service, OWNER, desk.pid, "Architecture")
    row = _round(desk, "Architecture")
    assert row["questions"][0]["skipped"] is True and row["waiting"] is None and row["questions"][0]["id"] == asked["question"]["id"]
    out = program_rounds.decide(desk.service, OWNER, desk.pid, "Architecture", "done")
    assert out["state"] == "done" and _round(desk, "Architecture")["state"] == "done"
    assert any(row["line"] == "Round Architecture done" for row in _wire(desk)["checkpoints"])
    # A done round asks nothing until Ask more.
    with pytest.raises(ProgramRefused) as closed:
        program_rounds.ask(desk.service, OWNER, desk.pid, "Architecture")
    assert closed.value.code == "round_closed"
    program_rounds.decide(desk.service, OWNER, desk.pid, "Architecture", "reopen")
    assert _round(desk, "Architecture")["state"] == "open"


def test_done_after_an_answer_counts_what_the_round_became(desk) -> None:
    _ask(desk, "Architecture")
    desk.engine.replies = [shape_reply("Architecture")]
    program_rounds.answer(desk.service, OWNER, desk.pid, "Architecture", said("Architecture"))
    program_rounds.decide(desk.service, OWNER, desk.pid, "Architecture", "done")
    assert any(row["line"] == "Round Architecture done: 1 change" for row in _wire(desk)["checkpoints"])


def test_skip_round_strikes_the_waiting_question_and_is_always_there(desk) -> None:
    _ask(desk, "Verification")
    out = program_rounds.decide(desk.service, OWNER, desk.pid, "Verification", "skip")
    row = _round(desk, "Verification")
    assert out["state"] == "skipped" and row["state"] == "skipped" and row["questions"][0]["skipped"] is True
    assert "\nround Verification · skipped\n" in print_program(_wire(desk))
    program_rounds.decide(desk.service, OWNER, desk.pid, "Verification", "reopen")
    assert _round(desk, "Verification")["state"] == "open"


def test_a_round_is_done_by_rule_after_the_few_questions(desk) -> None:
    program_rounds.open_rounds(desk.service, OWNER, desk.pid)
    stored = next(row for row in desk.service.store.list_rounds(desk.pid) if row["name"] == "Stack")
    stored["questions"] = [{"id": f"q{n}", "text": f"Question {n}?", "answer": "Yes.", "became": []}
                           for n in range(program_rounds.QUESTIONS_MAX)]
    desk.service.store.save_round({**stored, "updated_at": "2026-10-31T00:00:00+00:00"})
    out = program_rounds.ask(desk.service, OWNER, desk.pid, "Stack")
    assert out["done"] is True and _round(desk, "Stack")["state"] == "done" and desk.engine.prompts == []


# ── the text: `?` lines are the engine's ─────────────────────────────

def test_a_changed_question_line_is_refused_and_an_answer_line_applies(desk) -> None:
    asked = _ask(desk, "Architecture")
    text = print_program(_wire(desk))
    line = f"  ? {asked['question']['text']}"
    changed = desk.service.text_apply(OWNER, desk.pid, text.replace(line, "  ? Something else?"), dry_run=True)
    assert [(row["field"], row["verdict"], row["code"]) for row in changed["changes"]] == [
        ("question", "refused", "round_question")]
    answered = desk.service.text_apply(OWNER, desk.pid, text.replace(line, line + "\n  = In the hub."), dry_run=False)
    assert answered["applied"] is True
    assert _round(desk, "Architecture")["questions"][0]["answer"] == "In the hub."
    program_rounds.decide(desk.service, OWNER, desk.pid, "Architecture", "done")
    done_text = print_program(_wire(desk))
    again = desk.service.text_apply(OWNER, desk.pid, done_text.replace("= In the hub.", "= In the client."), dry_run=True)
    assert [(row["field"], row["code"]) for row in again["changes"]] == [("answer", "round_done")]
    asking = desk.service.text_apply(OWNER, desk.pid, done_text.replace("round Product · open", "round Product · asking"),
                                     dry_run=True)
    assert [(row["field"], row["code"]) for row in asking["changes"]] == [("state", "round_state")]


# ── rounds help; they do not gate Start ──────────────────────────────

def test_an_open_round_with_a_waiting_question_does_not_hold_start(desk) -> None:
    _ask(desk, "Architecture")
    assert _round(desk, "Architecture")["waiting"]
    started = desk.service.start(OWNER, desk.pid)
    assert started["state"] == "running"
    # Re-enterable while running: Done, then Ask more.
    program_rounds.skip_question(desk.service, OWNER, desk.pid, "Architecture")
    program_rounds.decide(desk.service, OWNER, desk.pid, "Architecture", "done")
    program_rounds.decide(desk.service, OWNER, desk.pid, "Architecture", "reopen")
    assert _round(desk, "Architecture")["state"] == "open"
