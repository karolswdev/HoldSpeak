"""PG-LANG LANG3 (2026-10-31): shaping a Program by a typed sentence.

PROGRAM-LANGUAGE-2026-10-31.md §4. One sentence and the Program's text go
to ONE call on the ``agent.plan`` assignment; the engine answers the whole
text; the hub diffs it with the LANG1 machinery. The engine's answers are
REAL replies of qwen3.8-27b on the home engine (tests/fixtures/
program_shape_reply.json, written by scripts/record_program_shape_reply.py
over the seed Program of tests/integration/program_shape_seed.py), replayed
through the runner's engine seam (``_engine_factory``), never typed.
Covered: the prompt contract, the one retry on an unreadable answer, the
refusals (no engine, the engine fails, two unreadable answers), the guard
(a row that lowers the bar, a waive, a core question), YOLO's apply with
its Decided for you row and Overturn, and a question back.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from holdspeak.services import program_shaper
from holdspeak.services.program_service import ProgramRefused
from holdspeak.services.program_text import diff_program_text, parse_program_text, print_program
from tests.integration.program_rig import OWNER, Rig
from tests.integration.program_shape_seed import SENTENCES, seed

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
RECORDED = json.loads((FIXTURES / "program_shape_reply.json").read_text(encoding="utf-8"))
UNREADABLE = json.loads((FIXTURES / "program_shape_unreadable_reply.json").read_text(encoding="utf-8"))
MODEL = RECORDED["engine"]["model"]


class RecordedEngine:
    """The engine the runner loads: answers with recorded replies, in turn."""

    active_provider = "recorded"
    active_model = MODEL

    def __init__(self) -> None:
        self.replies: list[str] = []
        self.prompts: list[dict[str, Any]] = []
        self.fail = False

    def run_prompt(self, **kwargs: Any) -> str:
        if self.fail:
            raise RuntimeError("the engine stopped")
        self.prompts.append(kwargs)
        return self.replies.pop(0)


def wire_engine(rig: Rig, monkeypatch, capability: str = "agent.plan") -> RecordedEngine:
    from holdspeak.inference_capabilities import process_inference_capability_registry
    from holdspeak.kernel.runtime import _configure
    from tests.unit.test_phase143_inference_assignments import _profile
    from tests.unit.test_phase200_readiness import _assign

    engine = RecordedEngine()
    broker = _configure(rig.db)
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda revision, **_kw: engine)
    schema = process_inference_capability_registry().require(capability)
    _profile(rig.db, "home-engine", claims=("language", f"result_schema:{schema.output_schema_sha256}"))
    _assign(rig.db, capability, ["home-engine"])
    return engine


def reply(key: str) -> str:
    return RECORDED["replies"][key]["reply_text"]


@pytest.fixture
def desk(tmp_path, monkeypatch):
    rig = Rig(tmp_path)
    rig.engine = wire_engine(rig, monkeypatch)
    rig.pid = seed(rig)
    return rig


def _rows(answer: dict[str, Any]) -> list[tuple[str, str, str, str]]:
    return [(row["op"], row["where"], row["field"], row["verdict"]) for row in answer["changes"]]


# ── the prompt contract ──────────────────────────────────────────────

def test_the_prompt_carries_the_card_the_text_without_lamps_the_grounding_and_the_sentence(desk) -> None:
    desk.engine.replies = [reply("shape")]
    before = print_program(desk.service.get(OWNER, desk.pid))
    result = program_shaper.shape(desk.service, OWNER, desk.pid, SENTENCES["shape"])

    (prompt,) = desk.engine.prompts
    system, user = prompt["system_prompt"], prompt["user_prompt"]
    assert "THE PROGRAM TEXT (version 1)" in system and "RULES" in system and "Never write 'waived'" not in system
    assert "never write 'waived'" in system and "step + <title>" in system
    assert "- agents: " in system and "Codex" in system and "requirement kinds: check, review, shot, word" in system
    # The text without its lamps (the run is never sent as definition).
    assert "  # " in before
    text_part = user.split("THE PROGRAM TEXT NOW\n", 1)[1].split("\n\n", 1)[0]
    assert text_part.startswith("# program text 1\nprogram The hub stops stalling\n")
    assert "  # " not in user.split("FILES IN THE REPOSITORY")[0]
    # Grounding: the repository map cut to the folders the steps own.
    files = user.split("FILES IN THE REPOSITORY (under the folders the steps own)\n", 1)[1].split("\n\n", 1)[0].split("\n")
    assert files == ["holdspeak/db/programs.py", "holdspeak/db/schema.py", "holdspeak/web/fanout.py",
                     "holdspeak/web/routes/people.py", "holdspeak/web/routes/programs.py"]
    assert user.rstrip().endswith("THE SENTENCE\n" + SENTENCES["shape"])
    assert prompt["temperature"] == 0.2 and prompt["response_format"]["json_schema"]["name"] == "program_shape"
    assert prompt["max_tokens"] == program_shaper.token_cap(program_shaper.stripped_text(before))
    # The answer: the engine's whole text, diffed by the hub.
    assert result.engine == MODEL and result.attempts == 1 and result.capability == "agent.plan"
    assert result.grounded_on["repo_paths"] == 5 and result.latency_ms >= 0
    assert [(row.op, row.where, row.field, row.verdict) for row in result.rows] == [
        ("change", "step 2", "agent", "allowed"),
        ("add", "step 4", "step", "allowed"),
        ("move", "step 4", "position", "allowed"),
        ("change", "step 3", "merge", "allowed"),
    ]
    assert result.say == json.loads(reply("shape"))["say"]
    # Nothing is written.
    assert print_program(desk.service.get(OWNER, desk.pid)) == before


def test_an_unreadable_answer_is_sent_back_once_with_the_parsers_words(desk) -> None:
    desk.engine.replies = [UNREADABLE["reply_text"], reply("shape")]
    result = program_shaper.shape(desk.service, OWNER, desk.pid, SENTENCES["shape"])
    assert result.attempts == 2 and len(desk.engine.prompts) == 2
    retry = desk.engine.prompts[1]["user_prompt"]
    assert "YOUR LAST ANSWER COULD NOT BE READ. The parser said:\nLine 35: merge is level, owner or none." in retry
    assert result.rows


def test_two_unreadable_answers_are_an_honest_refusal(desk) -> None:
    desk.engine.replies = [UNREADABLE["reply_text"], UNREADABLE["reply_text"]]
    before = print_program(desk.service.get(OWNER, desk.pid))
    with pytest.raises(ProgramRefused) as refused:
        program_shaper.shape(desk.service, OWNER, desk.pid, SENTENCES["shape"])
    assert refused.value.code == "engine_unusable"
    assert refused.value.detail == "The engine's answer could not be read. The program is unchanged. Try again."
    assert print_program(desk.service.get(OWNER, desk.pid)) == before


def test_no_engine_is_a_refusal_by_name(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = seed(rig)
    with pytest.raises(ProgramRefused) as refused:
        program_shaper.shape(rig.service, OWNER, pid, SENTENCES["shape"])
    assert (refused.value.code, refused.value.detail) == (
        "no_engine", "No engine is set for planning. The program is unchanged. Choose one in Engines.")
    assert rig.service.shape_engine(OWNER, pid)["engine"] is None


def test_the_ask_engine_shapes_when_agent_plan_has_no_route(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    engine = wire_engine(rig, monkeypatch, capability="ask.answer")
    pid = seed(rig)
    engine.replies = [reply("glance")]
    result = program_shaper.shape(rig.service, OWNER, pid, SENTENCES["glance"])
    assert result.capability == "ask.answer" and result.rows
    assert rig.service.shape_engine(OWNER, pid) == {
        "program_id": pid, "engine": "Home Engine", "capability": "ask.answer", "profile": "home-engine"}


def test_an_engine_that_fails_is_named(desk) -> None:
    desk.engine.fail = True
    with pytest.raises(ProgramRefused) as refused:
        program_shaper.shape(desk.service, OWNER, desk.pid, SENTENCES["shape"])
    assert refused.value.code == "engine_failed"
    assert refused.value.detail == "Home Engine did not answer. The program is unchanged. Try again."


def test_an_empty_sentence_is_refused(desk) -> None:
    with pytest.raises(ProgramRefused) as refused:
        program_shaper.shape(desk.service, OWNER, desk.pid, "   ")
    assert refused.value.code == "sentence_required"


# ── the guard ────────────────────────────────────────────────────────

def test_a_row_that_lowers_the_bar_never_applies_at_yolo(desk) -> None:
    desk.engine.replies = [reply("glance")]
    before = print_program(desk.service.get(OWNER, desk.pid))
    answer = desk.service.shape(OWNER, desk.pid, SENTENCES["glance"], apply=True)
    assert _rows(answer) == [("change", "step 1", "review depth", "lowers")]
    assert answer["lowers"] == ["step-1.depth"] and answer["applied"] is False
    assert print_program(desk.service.get(OWNER, desk.pid)) == before
    assert desk.service.decided_for_you(desk.pid) == []
    # His own press applies it (the well's Apply this, then Apply).
    pressed = desk.service.text_apply(OWNER, desk.pid, answer["proposed_text"], dry_run=False, base=answer["base"],
                                      allow_lower=answer["lowers"])
    assert pressed["applied"] is True


def test_the_engine_never_waives_and_a_core_question_waits_for_his_press(desk) -> None:
    """The recorded engine kept to the rules (the 'lowers' sentence came
    back unchanged); this text is a FAKE answer, typed here, to prove the
    guard behind the rules: a waive line is refused, a file outside the
    repository and a new phone call wait for his press."""
    wire = desk.service.get(OWNER, desk.pid)
    base = print_program(wire)
    fake = (program_shaper.stripped_text(base)
            .replace("  owns holdspeak/db/schema.py", "  owns /etc/hosts")
            .replace("  owns holdspeak/web/fanout.py", "  owns holdspeak/web/fanout.py\n  may call")
            .replace("is green", "is green\n    waived: it is slow"))
    rows = diff_program_text(parse_program_text(base), parse_program_text(fake), record=wire)
    desk.service._check_text_rows(OWNER, desk.service._program(desk.pid), wire, rows)
    program_shaper.guard(rows, wire)
    by = {row.id: row for row in rows}
    assert (by["step-1.owns"].verdict, by["step-1.owns"].code, by["step-1.owns"].reason) == (
        "lowers", "core_question", "A file outside the repository.")
    assert (by["step-3.may-call"].verdict, by["step-3.may-call"].code, by["step-3.may-call"].reason) == (
        "lowers", "core_question", "The engine may call your phone.")
    assert (by["R3.waive"].verdict, by["R3.waive"].code) == ("refused", "shape_no_waive")


def test_a_waive_row_from_the_engine_is_refused() -> None:
    from holdspeak.services.program_text import Change

    row = Change(id="R3.waive", op="change", where="R3", field="waived", after="it is slow", lowers_bar=True,
                 verdict="lowers", data={"kind": "waive", "rid": 3, "line": "it is slow"})
    program_shaper.guard([row], {})
    assert (row.verdict, row.code) == ("refused", "shape_no_waive")
    assert row.reason == "R3: Only you waive. Press Waive on the requirement."


# ── YOLO applies, Decided for you, Overturn ─────────────────────────

def test_at_yolo_the_allowed_rows_apply_at_once_and_overturn_puts_them_back(desk) -> None:
    desk.engine.replies = [reply("shape")]
    before = desk.service.get(OWNER, desk.pid)
    answer = desk.service.shape(OWNER, desk.pid, SENTENCES["shape"], apply=True)
    assert answer["applied"] is True and answer["changes"] == []
    assert [row["id"] for row in answer["applied_rows"]] == ["step-2.agents", "step-4.add", "step-4.move", "step-3.merge"]
    after = answer["program"]
    titles = [step["title"] for step in after["steps"]]
    assert titles == ["Indexes", "People routes", "Loop watch", "The fan-out"]
    assert after["steps"][1]["profile"] == "codex-default"
    assert after["steps"][3]["gate"]["merge"] == "owner"
    (decision,) = desk.service.decided_for_you(desk.pid)
    assert decision["rule"] == program_shaper.YOLO_RULE and decision["overturnable"] is True
    assert decision["line"].startswith("Shaped by a sentence: ")
    assert answer["decision"]["id"] == decision["id"]

    desk.service.overturn(OWNER, desk.pid, decision["id"])
    back = desk.service.get(OWNER, desk.pid)
    assert program_shaper.stripped_text(print_program(back)) == program_shaper.stripped_text(print_program(before))
    assert desk.service.decided_for_you(desk.pid)[0]["overturned_at"]


def test_overturn_is_withheld_once_a_touched_step_started(desk) -> None:
    desk.engine.replies = [reply("shape")]
    answer = desk.service.shape(OWNER, desk.pid, SENTENCES["shape"], apply=True)
    decision = answer["decision"]
    step = desk.service.store.get_step(answer["program"]["steps"][1]["id"])
    step["state"] = "working"
    desk.service.store.save_step(step)
    with pytest.raises(ProgramRefused) as refused:
        desk.service.overturn(OWNER, desk.pid, decision["id"])
    assert (refused.value.code, refused.value.detail) == (
        "not_overturnable", "Step 2 started. The shaped change stays.")


def test_below_yolo_nothing_applies_without_apply(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    engine = wire_engine(rig, monkeypatch)
    pid = seed(rig, control="normal")
    engine.replies = [reply("shape")]
    before = print_program(rig.service.get(OWNER, pid))
    answer = rig.service.shape(OWNER, pid, SENTENCES["shape"], apply=True)
    assert answer["applied"] is False and answer["held"] == "At Secure and Normal a shaped change waits for Apply."
    # The recorded text says control yolo: on a Normal program that row lowers the bar.
    assert ("change", "program", "control", "lowers") in _rows(answer)
    assert print_program(rig.service.get(OWNER, pid)) == before


def test_a_question_comes_back_as_one_question(desk) -> None:
    desk.engine.replies = [reply("question")]
    answer = desk.service.shape(OWNER, desk.pid, SENTENCES["question"])
    assert answer["question"] == json.loads(reply("question"))["question"]
    assert answer["changes"] == [] and answer["applied"] is False


def test_at_yolo_a_mixed_answer_applies_the_allowed_row_and_keeps_the_lowering_for_his_press(desk) -> None:
    """The recorded engine lowered the review depth although the rules say
    never lower a gate: the guard is what holds it."""
    desk.engine.replies = [reply("mixed")]
    answer = desk.service.shape(OWNER, desk.pid, SENTENCES["mixed"], apply=True)
    assert answer["applied"] is True
    assert [row["id"] for row in answer["applied_rows"]] == ["step-1.agents"]
    assert answer["program"]["steps"][0]["profile"] == "codex-default"
    # Against the text as it is now, one row waits: the glance review.
    assert _rows(answer) == [("change", "step 1", "review depth", "lowers")]
    assert answer["base"] == answer["text"] and "agent Codex" in answer["base"]
    pressed = desk.service.text_apply(OWNER, desk.pid, answer["proposed_text"], dry_run=False, base=answer["base"],
                                      allow_lower=answer["lowers"])
    assert pressed["applied"] is True and "review agent at glance" in pressed["text"]
