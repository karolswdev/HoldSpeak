"""PG-LANG LANG6 (2026-10-31): planning inference, a goal becomes a draft.

PROGRAM-LANGUAGE-2026-10-31.md §5. A Program in Drafting, its goal and its
template go to ONE call on the shaper's machinery (``agent.plan``); the
engine answers the whole text; the hub keeps his words and the template's,
sizes each step (§5.4) and asks once to split what does not fit; the rows
are the LANG2 rows with source ``plan``. The engine's answers are REAL
replies of qwen3.8-27b on the home engine (tests/fixtures/
program_plan_reply.json, written by scripts/record_program_plan_reply.py
over the cases of tests/integration/program_plan_seed.py), replayed through
the runner's engine seam; the rig's repository holds the owned files at the
sizes the recording read, so the sizes here are the recorded sizes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from holdspeak.services import program_planner, program_sizing
from holdspeak.services.program_service import ProgramRefused
from holdspeak.services.program_text import print_program
from tests.integration.program_plan_seed import CASES, create
from tests.integration.program_rig import OWNER, Rig
from tests.unit.test_program_shaper import UNREADABLE, wire_engine

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
RECORDED = json.loads((FIXTURES / "program_plan_reply.json").read_text(encoding="utf-8"))
MODEL = RECORDED["engine"]["model"]


def case(key: str) -> dict[str, Any]:
    return RECORDED["cases"][key]


def replies(key: str) -> list[str]:
    return [row["reply_text"] for row in case(key)["exchanges"]]


def split_replies(key: str) -> list[str]:
    """The replies to the face's Split on the draft's row that is still too big."""
    return [row["reply_text"] for row in case(key)["split_exchanges"]]


def desk_for(tmp_path: Path, monkeypatch, key: str, *, engine: bool = True) -> Rig:
    rig = Rig(tmp_path)
    rig.engine = wire_engine(rig, monkeypatch) if engine else None
    rig.pid = create(rig, CASES[key], file_bytes=case(key)["file_bytes"])
    return rig


def _plan(rig: Rig, key: str, **kw: Any) -> program_planner.PlanResult:
    return program_planner.plan(rig.service, OWNER, rig.pid, budget=CASES[key]["budget"], **kw)


# ── the prompt contract ──────────────────────────────────────────────

def test_the_prompt_carries_the_card_the_template_the_goal_the_repository_and_the_size_rule(tmp_path, monkeypatch) -> None:
    rig = desk_for(tmp_path, monkeypatch, "j1")
    rig.engine.replies = replies("j1")
    before = print_program(rig.service.get(OWNER, rig.pid))
    result = _plan(rig, "j1")

    (prompt,) = rig.engine.prompts
    system, user = prompt["system_prompt"], prompt["user_prompt"]
    assert "THE PROGRAM TEXT (version 1)" in system and "RULES FOR A DRAFT" in system and "step + <title>" in system
    assert "THE TEMPLATE: Build and review" in system
    assert ("- Its requirements (they are in the text already): review: The change does only what its brief says.; "
            "review: Each new behaviour has a test.") in system
    assert ("The agent that builds each step (Claude Code) has a context of 64k tokens; a step must fit in 32k tokens"
            in system) and "at most 3 owned files, a brief under 400 words" in system
    assert "- requirement kinds: check, review, shot, word, measure" in system
    text_part = user.split("THE PROGRAM TEXT NOW\n", 1)[1].split("\n\n", 1)[0]
    assert text_part.startswith("# program text 1\nprogram Meeting recap in the Note\n  goal\n  > After a meeting")
    assert text_part.endswith("\n  check scripts/quick_check.sh\n  budget 64k") or "\n  budget 64k\n" in text_part
    assert "  # " not in text_part
    assert "THE GOAL (the owner's words)\n" + CASES["j1"]["goal"] in user
    # The repository map: the top folders and the files the goal is likely about, with their size.
    assert "THE REPOSITORY: TOP FOLDERS\n" in user
    likely = user.split("FILES THE GOAL IS LIKELY ABOUT (size in tokens)\n", 1)[1].split("\n\n", 1)[0].split("\n")
    assert "holdspeak/runtime/meeting_stop.py  (2k)" in likely
    assert "web/src/desk/noteOutcomes.ts  (1k)" in likely
    assert "THE LAST CHANGES MERGED (how this repository cuts its work)\n- files\n- seed" in user
    assert prompt["temperature"] == 0.2 and prompt["response_format"]["json_schema"]["name"] == "program_plan"
    assert program_planner.MIN_TOKENS <= prompt["max_tokens"] <= program_planner.MAX_TOKENS
    # The answer: the engine's whole text, diffed and sized by the hub.
    assert result.engine == MODEL and result.attempts == 1 and result.capability == "agent.plan"
    assert result.budget == 65536 and result.split == []
    assert [(row["place"], row["title"], row["words"]) for row in result.sizes] == [
        (row["place"], row["title"], row["words"]) for row in case("j1")["result"]["sizes"]]
    assert [row["words"] for row in result.sizes] == ["7k of 32k", "4k of 32k", "5k of 32k", "3k of 32k"]
    assert all(row["fits"] for row in result.sizes)
    rows = [(row.op, row.where, row.field) for row in result.rows]
    assert ("change", "program", "budget") not in rows  # the Program's own budget line
    assert [r for r in rows if r[2] == "step"] == [("add", f"step {n}", "step") for n in (1, 2, 3, 4)]
    assert sum(1 for r in rows if r[2] == "requirement") == 6
    # One row is refused by the service's own check: the rig has no Alice in People.
    assert [(row.where, row.field, row.code) for row in result.rows if row.verdict != "allowed"] == [
        ("program", "for", "person_unknown")]
    assert all(row.data["source"] == "plan" for row in result.rows)
    added = [row for row in result.rows if row.data.get("kind") == "add_step"]
    assert [row.data["size"]["words"] for row in added] == [row["words"] for row in result.sizes]
    # Nothing is written.
    assert print_program(rig.service.get(OWNER, rig.pid)) == before


def test_the_hub_keeps_his_goal_and_what_the_template_set(tmp_path, monkeypatch) -> None:
    rig = desk_for(tmp_path, monkeypatch, "j1")
    rig.engine.replies = replies("j1")
    result = _plan(rig, "j1")
    # The engine wrote "in wt-pg-plan" (the repository it was recorded on); the rig's stays.
    assert "in wt-pg-plan" in replies("j1")[0]
    assert "\n  in app · main · project HoldSpeak\n" in result.proposed_text
    assert "\n  template build and review\n" in result.proposed_text
    assert "> After a meeting, the meeting's Note should end with a short recap" in result.proposed_text
    assert "\n  budget 64k\n" in result.proposed_text
    # The engine numbered its new requirements (R3, R4): the hub reads them as new.
    assert "R3 measure:" in json.loads(replies("j1")[0])["text"]
    assert [row.code for row in result.rows if row.verdict == "refused"] == ["person_unknown"]
    assert [row.after for row in result.rows if row.where == "at the end"] == [
        "R+ measure: The recap appears in the Note within 20 seconds of Stop on the owner's Mac.",
        "R+ word: Alice has seen the recap section in her team's standup Note before this ships."]


def test_a_budget_he_names_for_the_plan_is_written_into_the_draft(tmp_path, monkeypatch) -> None:
    rig = desk_for(tmp_path, monkeypatch, "j1")
    rig.service.update(OWNER, rig.pid, budget_tokens=None)
    rig.engine.replies = replies("j1")
    result = _plan(rig, "j1")
    assert "SIZE\nThe agent that builds each step (Claude Code) has a context of 64k" in rig.engine.prompts[0]["system_prompt"]
    budget = next(row for row in result.rows if (row.where, row.field) == ("program", "budget"))
    assert (budget.op, budget.after, budget.verdict) == ("change", "64k", "allowed")
    # With no budget at all, Claude Code has none: the lamps are the estimate only.
    rig.engine.replies = replies("j1")
    bare = program_planner.plan(rig.service, OWNER, rig.pid)
    assert "SIZE" not in rig.engine.prompts[1]["system_prompt"]
    assert [row["words"] for row in bare.sizes] == ["7k", "4k", "5k", "3k"] and bare.budget is None


def test_an_unreadable_answer_is_sent_back_once_with_the_parsers_words(tmp_path, monkeypatch) -> None:
    rig = desk_for(tmp_path, monkeypatch, "j1")
    rig.engine.replies = [UNREADABLE["reply_text"], *replies("j1")]
    result = _plan(rig, "j1")
    assert result.attempts == 2 and len(rig.engine.prompts) == 2
    retry = rig.engine.prompts[1]["user_prompt"]
    assert "YOUR LAST ANSWER COULD NOT BE READ. The parser said:\nLine 35: merge is level, owner or none." in retry
    assert len(result.sizes) == 4


def test_two_unreadable_answers_are_an_honest_refusal(tmp_path, monkeypatch) -> None:
    rig = desk_for(tmp_path, monkeypatch, "j1")
    rig.engine.replies = [UNREADABLE["reply_text"], UNREADABLE["reply_text"]]
    with pytest.raises(ProgramRefused) as refused:
        _plan(rig, "j1")
    assert refused.value.code == "engine_unusable"
    assert refused.value.detail == "The engine's answer could not be read. The program is unchanged. Try again."
    assert rig.service.get(OWNER, rig.pid)["steps"] == []


def test_no_engine_is_a_refusal_by_name(tmp_path, monkeypatch) -> None:
    rig = desk_for(tmp_path, monkeypatch, "j1", engine=False)
    with pytest.raises(ProgramRefused) as refused:
        _plan(rig, "j1")
    assert (refused.value.code, refused.value.detail) == (
        "no_engine", "No engine is set for planning. The program is unchanged. Choose one in Engines.")


def test_plan_it_is_for_drafting_and_needs_a_goal(tmp_path, monkeypatch) -> None:
    rig = desk_for(tmp_path, monkeypatch, "j1")
    rig.service.update(OWNER, rig.pid, goal="")
    with pytest.raises(ProgramRefused) as refused:
        _plan(rig, "j1")
    assert refused.value.code == "goal_required"
    rig.service.update(OWNER, rig.pid, goal="x" * 9000)
    with pytest.raises(ProgramRefused) as refused:
        _plan(rig, "j1", goal_text="y" * 9000)
    assert refused.value.code == "goal_too_long"
    with pytest.raises(ProgramRefused) as refused:
        _plan(rig, "j1", goal_text="Recap the meeting.", template="race")
    assert refused.value.code == "field_fixed"


def test_a_running_program_is_shaped_not_planned(tmp_path, monkeypatch) -> None:
    rig = desk_for(tmp_path, monkeypatch, "j1")
    with rig.db._connection() as conn:
        conn.execute("UPDATE programs SET state='running' WHERE id=?", (rig.pid,))
    with pytest.raises(ProgramRefused) as refused:
        _plan(rig, "j1")
    assert (refused.value.code, refused.value.detail) == (
        "plan_drafting_only", "Plan it works while the program is in Drafting. Shape it instead.")


def test_the_goal_he_typed_goes_to_the_engine_and_into_the_draft(tmp_path, monkeypatch) -> None:
    rig = desk_for(tmp_path, monkeypatch, "j1")
    rig.service.update(OWNER, rig.pid, goal="Something older.")
    rig.engine.replies = replies("j1")
    result = _plan(rig, "j1", goal_text=CASES["j1"]["goal"])
    assert "THE GOAL (the owner's words)\n" + CASES["j1"]["goal"] in rig.engine.prompts[0]["user_prompt"]
    goal = next(row for row in result.rows if row.where == "program" and row.field == "goal")
    assert goal.verdict == "allowed" and goal.before.startswith("Something older")


# ── sizing and the split ─────────────────────────────────────────────

def test_a_step_over_the_working_share_is_split_once_and_what_still_does_not_fit_is_marked(tmp_path, monkeypatch) -> None:
    rig = desk_for(tmp_path, monkeypatch, "big_file")
    rig.engine.replies = replies("big_file")
    result = _plan(rig, "big_file")
    assert result.attempts == 2 and len(rig.engine.prompts) == 2
    # The first draft's one step owns program_service.py (about 60k tokens alone).
    assert result.split == case("big_file")["result"]["split"]
    assert (result.split[0]["place"], result.split[0]["words"]) == (1, "Too big for Claude Code · 61k of 32k")
    second = rig.engine.prompts[1]
    assert "SPLIT A STEP" in second["system_prompt"] and "RULES FOR A DRAFT" not in second["system_prompt"]
    assert ("THESE STEPS ARE TOO BIG\n- step 1 Extract text_apply into its own module: Too big for Claude Code · "
            "61k of 32k (owns holdspeak/services/program_text_apply.py, holdspeak/services/program_service.py)"
            ) in second["user_prompt"]
    assert "step + Extract text_apply into its own module" in second["user_prompt"].split("THE GOAL")[0]
    # The engine split it in two; the part that owns the 60k file still does not fit: it stays marked.
    words = [row["words"] for row in result.sizes]
    assert words == [row["words"] for row in case("big_file")["result"]["sizes"]]
    assert words == ["1k of 32k", "Too big for Claude Code · 61k of 32k"]
    too_big = [row for row in result.sizes if row["fits"] is False]
    assert [row["code"] for row in too_big] == ["step_too_big"]
    added = [row for row in result.rows if row.data.get("kind") == "add_step"]
    assert [row.data["size"]["code"] for row in added] == [None, "step_too_big"]
    # A too-big step is still a row he may apply (the dispatcher holds it, LANG8).
    assert all(row.verdict == "allowed" for row in added)


def test_split_on_a_draft_row_makes_only_the_split_call(tmp_path, monkeypatch) -> None:
    rig = desk_for(tmp_path, monkeypatch, "big_file")
    rig.engine.replies = replies("big_file")
    draft = _plan(rig, "big_file")
    recorded = case("big_file")["split_result"]
    assert recorded["place"] == 2
    rig.engine.replies = split_replies("big_file")
    result = _plan(rig, "big_file", text=draft.proposed_text, split=2)
    prompt = rig.engine.prompts[-1]
    assert len(rig.engine.prompts) == 3
    assert "SPLIT A STEP" in prompt["system_prompt"]
    assert ("- step 2 Delegate from program_service.py: Too big for Claude Code · 61k of 32k "
            "(owns holdspeak/services/program_service.py)") in prompt["user_prompt"]
    assert [(row["title"], row["words"]) for row in result.sizes] == [
        (row["title"], row["words"]) for row in recorded["sizes"]]
    assert [row["words"] for row in result.sizes] == [
        "1k of 32k", "Too big for Claude Code · 61k of 32k", "Too big for Claude Code · 61k of 32k"]
    # The rows are against the Program as it is (still no steps): three new steps.
    assert [row.where for row in result.rows if row.data.get("kind") == "add_step"] == ["step 1", "step 2", "step 3"]


def test_the_size_words_name_the_working_share() -> None:
    assert program_sizing.WORKING_SHARE == 0.5
    assert program_sizing.size(18 * 1024, 65536, "qwen")["words"] == "18k of 32k"
    big = program_sizing.size(41 * 1024, 65536, "qwen")
    assert (big["words"], big["fits"], big["code"]) == ("Too big for qwen · 41k of 32k", False, "step_too_big")
    assert program_sizing.size(32768, 65536, "qwen")["fits"] is True
    none = program_sizing.size(5000, None, "Claude Code")
    assert (none["words"], none["fits"], none["budget"]) == ("5k", None, None)


def test_a_path_outside_the_repository_is_never_read(tmp_path) -> None:
    (tmp_path / "repo" / "src").mkdir(parents=True)
    (tmp_path / "repo" / "src" / "a.py").write_text("x" * 4000)
    (tmp_path / "repo" / "src" / "b.py").write_text("x" * 400)
    (tmp_path / "secret.txt").write_text("x" * 99999)
    root = str(tmp_path / "repo")
    assert program_sizing.path_bytes(root, "src/a.py") == 4000
    assert program_sizing.path_bytes(root, "src") == 4400
    assert program_sizing.path_bytes(root, "../secret.txt") == 0
    assert program_sizing.path_bytes(root, str(tmp_path / "secret.txt")) == 0
    assert program_sizing.path_bytes(root, "src/new.py") == 0


def test_pi_without_a_budget_is_sized_to_its_engine_window(tmp_path) -> None:
    rig = Rig(tmp_path)
    budget, word = program_sizing.budget_of(rig.service, explicit=None, program_budget=None, step_budget=None,
                                            agent=("pi-default", None), default_engine=None)
    assert (budget, word) == (32768, "pi")
    assert program_sizing.budget_of(rig.service, explicit=None, program_budget=None, step_budget=None,
                                    agent=("claude-default", None), default_engine=None) == (None, "Claude Code")


# ── the guard ────────────────────────────────────────────────────────

def test_a_draft_that_lowers_the_bar_or_reaches_outside_waits_for_his_press(tmp_path, monkeypatch) -> None:
    """The recorded engine kept to the rules; this answer is a FAKE, typed
    here, to prove the guard behind the rules: a step with 'check off' lowers
    the bar, a file outside the repository and a phone call are core
    questions, a removed template requirement stays."""
    rig = desk_for(tmp_path, monkeypatch, "j1")
    base = program_planner.shaper.stripped_text(print_program(rig.service.get(OWNER, rig.pid)))
    fake = (base.replace("  R2 review: Each new behaviour has a test.\n", "")
            + "\nstep + Reach out\n  owns /etc/hosts\n  check off\n  may call\n  brief\n  > Read the hosts file.\n")
    result = _plan(rig, "j1", invoke_fn=lambda payload: (json.dumps({"say": "1 step", "text": fake}), "fake"))
    by = {(row.where, row.field): row for row in result.rows}
    assert (by[("step 1", "step")].verdict, by[("step 1", "step")].code) == ("lowers", "core_question")
    assert by[("R2", "requirement")].code == "requirement_stays"


# ── Apply in Drafting writes the draft ───────────────────────────────

def test_apply_in_drafting_writes_the_steps_and_requirements_and_each_step_carries_its_size(tmp_path, monkeypatch) -> None:
    rig = desk_for(tmp_path, monkeypatch, "j1")
    rig.engine.replies = replies("j1")
    answer = rig.service.plan_draft(OWNER, rig.pid)
    assert answer["source"] == "plan" and answer["engine"] == MODEL
    assert answer["counts"] == {"steps": 4, "requirements": 6, "too_big": 0} and answer["refused"] == 1
    assert answer["say"] == json.loads(replies("j1")[0])["say"]
    assert answer["words"] == "4 steps · 6 requirements" and answer["share"] == 32768
    sized = [row for row in answer["changes"] if row["size"]]
    assert [row["size"]["words"] for row in sized] == ["7k of 32k", "4k of 32k", "5k of 32k", "3k of 32k"]
    assert all(row["source"] == "plan" for row in answer["changes"])
    # Apply 10: the allowed text (the refused 'for Alice' put back).
    applied = rig.service.text_apply(OWNER, rig.pid, answer["allowed_text"], dry_run=False, base=answer["base"])
    assert applied["applied"] is True
    program = applied["program"]
    assert program["state"] == "drafting" and program["budget_tokens"] == 65536
    assert [step["title"] for step in program["steps"]] == [row["title"] for row in answer["sizes"]]
    assert [step["estimate"]["words"] for step in program["steps"]] == [row["words"] for row in answer["sizes"]]
    assert program["steps"][1]["after"] == [1]
    reqs = rig.service.requirements(rig.pid)
    # The template's two every-step lines, their copy on each of the 4 steps, and the draft's 6.
    assert len(reqs) == 2 + 4 * 2 + 6
