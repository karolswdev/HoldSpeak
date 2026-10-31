"""PG-LANG LANG5 (2026-10-31): shaping a Program by voice.

PROGRAM-LANGUAGE-2026-10-31.md §4.2, §10; PROGRAM-JOURNEYS J3. Three spoken
sentences in a row each add their rows to the one change well: the hub
sends the text of the rows that wait (``pending``) in place of the current
text, so the engine adds to them; the rows stay against the current text.
On a call, a held ``program.shape`` is read back one row a sentence; his
yes applies the allowed rows, a row that lowers the bar waits on the desk,
"later" puts every row on the desk. The engine's answers are REAL
qwen3.8-27b replies (tests/fixtures/program_shape_reply.json: voice1,
voice2 recorded over voice1's text, voice3 over voice2's; call; mixed),
replayed through the runner.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.services import program_shaper, program_spoken
from holdspeak.services.program_service import ProgramRefused
from holdspeak.services.program_text import print_program
from tests.integration.program_rig import OWNER, Rig
from tests.integration.program_shape_seed import CHAINED, SENTENCES, seed
from tests.unit.test_program_shaper import reply, wire_engine

RECORDED = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "program_shape_reply.json").read_text())


@pytest.fixture(autouse=True)
def _fresh() -> None:
    program_spoken.reset()
    yield
    program_spoken.reset()


@pytest.fixture
def normal(tmp_path, monkeypatch):
    rig = Rig(tmp_path)
    rig.engine = wire_engine(rig, monkeypatch)
    rig.pid = seed(rig, control="normal")
    return rig


def _ids(answer):
    return [row["id"] for row in answer["changes"]]


def test_three_sentences_in_a_row_add_their_rows_to_the_one_well(normal) -> None:
    before = print_program(normal.service.get(OWNER, normal.pid))
    answers, pending = [], None
    for key in ("voice1", "voice2", "voice3"):
        normal.engine.replies = [reply(key)]
        answer = program_shaper.shape_program(normal.service, OWNER, normal.pid, SENTENCES[key], pending=pending)
        answers.append(answer)
        pending = answer["proposed_text"]
    # The engine read the text of the rows that wait: the prompt it was recorded on.
    for key, prompt in zip(("voice1", "voice2", "voice3"), normal.engine.prompts):
        assert prompt["user_prompt"] == RECORDED["replies"][key]["user_prompt"], key
    assert CHAINED == {"voice2": "voice1", "voice3": "voice2"}
    first, second, third = (_ids(answer) for answer in answers)
    assert set(first) < set(second) < set(third), (first, second, third)
    # The real engine wrote "R4" for the new ruff requirement (not "R+"): that
    # row is refused by name in every well after it; the rest are allowed.
    verdicts = {row["id"]: (row["verdict"], row["code"]) for row in answers[2]["changes"]}
    assert verdicts.pop(first[0]) == ("refused", "text_bad_value")
    assert {verdict for verdict, _code in verdicts.values()} == {"allowed"}, verdicts
    # Each answer is against the text as it is now; nothing was written.
    assert {answer["base"] for answer in answers} == {before}
    assert print_program(normal.service.get(OWNER, normal.pid)) == before
    # One Apply lands what can land of all three sentences (allowed_text).
    applied = normal.service.text_apply(OWNER, normal.pid, answers[2]["allowed_text"], dry_run=False,
                                        base=answers[2]["base"])
    assert applied["applied"] is True
    steps = applied["program"]["steps"]
    assert [step["title"] for step in steps] == ["Indexes", "People routes", "Loop watch", "The fan-out"]
    assert steps[3]["profile"] == "codex-default", steps[3]


def test_a_pending_text_the_parser_cannot_read_is_refused_and_no_engine_is_called(normal) -> None:
    with pytest.raises(ProgramRefused) as refused:
        program_shaper.shape_program(normal.service, OWNER, normal.pid, SENTENCES["voice2"], pending="step one\n  ???")
    assert refused.value.code == "pending_unreadable"
    assert normal.engine.prompts == []


# ── the spoken form (§10) ────────────────────────────────────────────

def test_the_read_back_is_one_sentence_a_row_and_names_what_waits_on_the_desk() -> None:
    rows = [
        {"verdict": "allowed", "say": "Step 1's agents is now Codex."},
        {"verdict": "lowers", "say": "Step 1's depth is now glance."},
    ]
    question, spoken = program_spoken.read_back("The hub stops stalling", rows)
    assert question == ("In the program The hub stops stalling: Step 1's agents is now Codex. One change lowers the "
                        "bar and waits for you on the desk: Step 1's depth is now glance. Apply?")
    assert spoken == ""
    question, spoken = program_spoken.read_back("The hub stops stalling", rows[1:])
    assert question == "" and spoken.endswith("Nothing changed on the call.")
    assert program_spoken.read_back("X", []) == ("", "Nothing in the program X changes.")


def _shots(rig) -> None:
    """The repository proves a shot (HoldSpeak's own has a shot command)."""
    folder = rig.repo / ".holdspeak"
    folder.mkdir(exist_ok=True)
    (folder / "program.json").write_text(json.dumps({"shot": "true {case} {width}"}))


def _dispatch(rig, monkeypatch, args):
    from holdspeak.mcp.families import program as program_family
    from holdspeak.services import program_service as program_module

    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: rig.service)
    return program_family.dispatch("program.shape", args, OWNER)


def test_his_yes_applies_the_allowed_rows_and_the_lowering_row_waits_on_the_desk(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    engine = wire_engine(rig, monkeypatch)
    pid = seed(rig)  # yolo: the recording of "mixed"; a call's yes is his press at any level
    engine.replies = [reply("mixed")]
    held = program_spoken.prepare(rig.service, OWNER, {"name": "stalling", "sentence": SENTENCES["mixed"]})
    assert held["state"] == "asked" and held["question"].endswith("Apply?"), held
    assert "waits for you on the desk" in held["question"]
    # Asked, not answered: the tool is a preview, nothing applies.
    program_spoken.answered(pid, SENTENCES["mixed"], "approve")
    answer = _dispatch(rig, monkeypatch, {"name": "stalling", "sentence": SENTENCES["mixed"]})
    assert answer["applied"] is True and answer["on_desk"] == 1, answer
    assert answer["spoken"] == "Done: the program The hub stops stalling has one change. One waits for you on the desk."
    program = rig.service.get(OWNER, pid)
    assert program["steps"][0]["profile"] == "codex-default"
    waiting = program["held_shape"]
    assert [row["verdict"] for row in waiting["changes"]] == ["lowers"] and waiting["source"] == "call"
    assert any(frame[0] == "program_changed" and frame[1].get("held_shape") for frame in rig.frames), rig.frames
    # His press on the desk applies it; the rows leave the well.
    applied = rig.service.text_apply(OWNER, pid, waiting["proposed_text"], base=waiting["base"], dry_run=False,
                                     allow_lower=waiting["lowers"])
    assert applied["applied"] is True and "held_shape" not in applied["program"]


def test_later_puts_every_row_on_the_desk_and_no_keeps_nothing(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    engine = wire_engine(rig, monkeypatch)
    pid = seed(rig, control="normal")
    _shots(rig)
    before = print_program(rig.service.get(OWNER, pid))
    engine.replies = [reply("call")]
    program_spoken.prepare(rig.service, OWNER, {"program_id": pid, "sentence": SENTENCES["call"]})
    program_spoken.answered(pid, SENTENCES["call"], "later")
    answer = _dispatch(rig, monkeypatch, {"program_id": pid, "sentence": SENTENCES["call"]})
    assert answer["applied"] is False and answer["on_desk"] == len(rig.service.get(OWNER, pid)["held_shape"]["changes"])
    assert answer["spoken"].startswith("Nothing changed yet.") and answer["spoken"].endswith("on the desk.")
    assert print_program(rig.service.get(OWNER, pid)) == before
    rig.service.drop_held_shape(OWNER, pid)
    assert "held_shape" not in rig.service.get(OWNER, pid)

    engine.replies = [reply("call")]
    program_spoken.prepare(rig.service, OWNER, {"program_id": pid, "sentence": SENTENCES["call"]})
    program_spoken.answered(pid, SENTENCES["call"], "deny")
    assert program_spoken.take(pid, SENTENCES["call"]) is None
    assert "held_shape" not in rig.service.get(OWNER, pid)


def test_a_program_the_call_names_that_does_not_exist_is_said_so(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    wire_engine(rig, monkeypatch)
    seed(rig)
    assert program_spoken.prepare(rig.service, OWNER, {"name": "garden", "sentence": "add a step"}) is None
    answer = _dispatch(rig, monkeypatch, {"name": "garden", "sentence": "add a step"})
    assert answer == {"found": False, "applied": False,
                      "spoken": "There is no program with the name garden. Nothing changed."}
