"""PG-LANG LANG8 (2026-10-31): sizing at dispatch, and the split by level.

PROGRAM-LANGUAGE-2026-10-31.md §5.4 and §15.8. Before the runner hands a
step, its estimate is read against its budget's working share; a step that
does not fit is held ("Too big for Claude Code · 36k of 32k") and the rule
``step_too_big`` decides: YOLO splits it (one planning call, Decided for you,
Overturn), Secure and Normal get the split as a ``step_change`` proposal
(Apply splits, Skip runs it as it is), and no planner is a core question
(Go on runs it as it is). The planner's answers are REAL replies of
qwen3.8-27b (tests/fixtures/program_night_reply.json, written by
scripts/record_program_night_reply.py over tests/integration/
program_night_seed.py), replayed through the runner's engine seam; the
rig's repository holds the owned files at the recorded sizes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from holdspeak.services import program_split
from holdspeak.services.program_rules import decide
from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_night_seed import SPLIT_STEP, make_split
from tests.integration.program_rig import OWNER, Rig
from tests.unit.test_program_shaper import wire_engine

RECORDED = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "program_night_reply.json")
                      .read_text(encoding="utf-8"))
SPLIT = RECORDED["cases"]["split"]
REPLIES = [row["reply_text"] for row in SPLIT["exchanges"]]


def desk(tmp_path: Path, monkeypatch, control: str, *, engine: bool = True) -> tuple[Rig, str, str]:
    rig = Rig(tmp_path)
    rig.engine = wire_engine(rig, monkeypatch) if engine else None
    if engine:
        rig.engine.replies = list(REPLIES)
    pid, sid = make_split(rig, file_bytes=SPLIT["file_bytes"], control=control)
    return rig, pid, sid


def handed(rig: Rig) -> list[str]:
    return [item_id for kind, item_id, _kw in rig.hand.calls if kind == "program_step"]


def lines(rig: Rig, pid: str) -> list[str]:
    return [row["line"] for row in reversed(rig.service.store.list_checkpoints(pid))]


# ── the rule ─────────────────────────────────────────────────────────

def test_the_rule_splits_at_yolo_and_asks_at_secure_and_normal() -> None:
    yolo = decide("yolo", "step_too_big", {})
    assert not yolo.to_owner and yolo.choice == "split" and yolo.overturnable
    for level in ("secure", "normal"):
        outcome = decide(level, "step_too_big", {})
        assert outcome.to_owner and not outcome.core


# ── Normal: the split is a proposal ──────────────────────────────────

def test_a_step_over_its_budget_is_held_with_his_words_and_the_split_is_his(tmp_path, monkeypatch) -> None:
    rig, pid, sid = desk(tmp_path, monkeypatch, "normal")
    rig.service.start(OWNER, pid)

    step = rig.step(pid, 1)
    assert step["state"] == "ready" and step["held_reason"] == "Too big for Claude Code · 36k of 32k"
    assert step["state_word"] == "Ready · Too big for Claude Code · 36k of 32k"
    assert step["estimate"]["code"] == "step_too_big" and step["estimate"]["words"] == SPLIT["size"]["words"]
    assert sid not in handed(rig)
    assert ("Step 1 is too big for one agent run (about 36k tokens against 32k, half of the 64k budget)"
            in lines(rig, pid))
    # ONE planning call, on the step alone: its brief, its owned files with their size, the share.
    (prompt,) = rig.engine.prompts
    assert prompt["response_format"]["json_schema"]["name"] == "program_split"
    assert "a part must fit in 32k tokens" in prompt["system_prompt"]
    assert "THE STEP (too big: about 36k of 32k tokens)" in prompt["user_prompt"]
    assert "- holdspeak/services/program_shaper.py  (10k)" in prompt["user_prompt"]
    # His row: the step_change proposal with the parts, Apply / Skip.
    (item,) = [row for row in rig.service.needs_you_items() if row["program_id"] == pid]
    assert item["kind"] == "step_change" and item["choices"] == ["apply", "skip"]
    titles = [part["title"] for part in SPLIT["parts"]]
    assert item["title"] == ("Split step 1 (too big for Claude Code · 36k of 32k) into 3 parts: "
                             + " · ".join(titles) + ". Skip runs it as it is.")[:400]
    # Another tick asks nothing more.
    rig.tick(2)
    assert len(rig.engine.prompts) == 1 and len(rig.service.needs_you_items()) == 1


def test_apply_puts_the_parts_in_its_place_and_the_step_after_it_waits_for_the_last(tmp_path, monkeypatch) -> None:
    rig, pid, sid = desk(tmp_path, monkeypatch, "normal")
    rig.service.start(OWNER, pid)
    (item,) = rig.service.needs_you_items()
    rig.service.decide(OWNER, pid, "", kind="step_change", choice="apply", proposal_id=item["proposal_id"])

    steps = rig.program(pid)["steps"]
    assert [step["title"] for step in steps] == [part["title"] for part in SPLIT["parts"]] + ["Say it in the docs"]
    assert [step["ordinal"] for step in steps] == [1, 2, 3, 4]
    assert [step["owns"] for step in steps[:3]] == [part["owns"] for part in SPLIT["parts"]]
    assert [step["after"] for step in steps] == [[], [1], [2], [3]]
    assert sid not in {step["id"] for step in steps}
    # The first part fits and is handed; the parts after it wait.
    assert all(step["estimate"] is None or step["estimate"]["fits"] for step in steps)
    assert handed(rig) == [steps[0]["id"]]
    assert "Split step 1 into 3 parts" in lines(rig, pid)
    assert rig.service.needs_you_items() == []


def test_skip_runs_it_as_it_is_and_the_estimate_is_in_the_checkpoint(tmp_path, monkeypatch) -> None:
    rig, pid, sid = desk(tmp_path, monkeypatch, "secure")
    rig.service.start(OWNER, pid)
    (item,) = rig.service.needs_you_items()
    rig.service.decide(OWNER, pid, "", kind="step_change", choice="skip", proposal_id=item["proposal_id"])

    assert handed(rig) == [sid]
    assert "Runs as it is: step 1 (about 36k of 32k tokens)" in lines(rig, pid)
    assert [step["title"] for step in rig.program(pid)["steps"]] == [SPLIT_STEP["title"], "Say it in the docs"]


# ── YOLO: the planner splits it, with Overturn ───────────────────────

def test_yolo_splits_it_says_so_and_overturn_brings_the_step_back_as_his_proposal(tmp_path, monkeypatch) -> None:
    rig, pid, sid = desk(tmp_path, monkeypatch, "yolo")
    rig.service.start(OWNER, pid)
    rig.tick()  # the parts are Planned; the next tick promotes and hands the first

    steps = rig.program(pid)["steps"]
    assert [step["title"] for step in steps] == [part["title"] for part in SPLIT["parts"]] + ["Say it in the docs"]
    (row,) = [row for row in rig.service.decided_for_you(pid) if row["kind"] == "step_too_big"]
    assert row["line"] == "Split step 1 (too big for Claude Code · 36k of 32k) into 3 parts: steps 1–3"
    assert row["rule"] == "YOLO: the planner splits a step too big for its budget and says so" and row["overturnable"]
    assert rig.service.needs_you_items() == []
    # The first part was handed at once; Overturn waits until no part started.
    first = steps[0]["id"]
    assert handed(rig) == [first]
    with pytest.raises(ProgramRefused) as refused:
        rig.service.overturn(OWNER, pid, row["id"])
    assert refused.value.code == "not_overturnable"


def test_overturn_while_every_part_is_planned_restores_the_step(tmp_path, monkeypatch) -> None:
    rig, pid, sid = desk(tmp_path, monkeypatch, "yolo")
    rig.hand.working_at_once = 0  # no free agent: the parts stay Ready
    rig.service.start(OWNER, pid)
    (row,) = [row for row in rig.service.decided_for_you(pid) if row["kind"] == "step_too_big"]
    rig.service.overturn(OWNER, pid, row["id"])

    steps = rig.program(pid)["steps"]
    assert [step["title"] for step in steps] == [SPLIT_STEP["title"], "Say it in the docs"]
    assert steps[1]["after"] == [1] and steps[0]["owns"] == SPLIT_STEP["owns"]
    # The split is his now: the same parts as a proposal, no second call.
    (item,) = rig.service.needs_you_items()
    assert item["kind"] == "step_change" and item["title"].startswith("Split step 1 (too big for Claude Code")
    assert len(rig.engine.prompts) == 1
    assert handed(rig) == []


# ── no planner, and a part still too big ─────────────────────────────

def test_with_no_planning_engine_the_too_big_step_is_a_core_question_and_go_on_runs_it(tmp_path, monkeypatch) -> None:
    rig, pid, sid = desk(tmp_path, monkeypatch, "yolo", engine=False)
    rig.service.start(OWNER, pid)

    (item,) = rig.service.needs_you_items()
    assert item["kind"] == "core" and item["choices"] == ["go_on", "park"]
    assert item["reason"].startswith("step 1 is too big for one agent run (about 36k of 32k tokens) and the planner "
                                     "could not split it")
    assert handed(rig) == []
    rig.service.decide(OWNER, pid, sid, kind="core", choice="go_on")
    assert handed(rig) == [sid]


def test_a_part_still_too_big_after_the_split_is_not_cut_again(tmp_path, monkeypatch) -> None:
    rig, pid, sid = desk(tmp_path, monkeypatch, "yolo")
    # A 32k budget: the step and its first part (about 23k) are over its 16k share.
    rig.service.update(OWNER, pid, budget_tokens="32k")
    rig.service.start(OWNER, pid)
    rig.tick()

    first = rig.step(pid, 1)
    assert first["title"] == SPLIT["parts"][0]["title"] and first["estimate"]["fits"] is False
    (item,) = [row for row in rig.service.needs_you_items() if row["kind"] == "core"]
    assert item["step_id"] == first["id"] and "still too big after a split" in item["reason"]
    assert len(rig.engine.prompts) == 1 and handed(rig) == []


def test_a_step_that_fits_is_handed_with_no_call(tmp_path, monkeypatch) -> None:
    rig, pid, sid = desk(tmp_path, monkeypatch, "normal")
    rig.service.update(OWNER, pid, budget_tokens="128k")
    rig.service.start(OWNER, pid)
    assert handed(rig) == [sid] and rig.engine.prompts == []


# ── the answer's checks ──────────────────────────────────────────────

@pytest.mark.parametrize(("answer", "reason"), [
    ({"say": "", "parts": [{"title": "One", "brief": "b", "owns": list(SPLIT_STEP["owns"])}]}, "Give 2 to 4 parts."),
    ({"say": "", "parts": [{"title": "A", "brief": "b", "owns": ["holdspeak/services/program_rounds.py"]},
                           {"title": "B", "brief": "b", "owns": ["web/src/desk/x.ts"]}]},
     "Part 2 owns web/src/desk/x.ts, which the step does not own."),
    ({"say": "", "parts": [{"title": "A", "brief": "b", "owns": ["holdspeak/services/program_rounds.py"]},
                           {"title": "B", "brief": "b", "owns": ["holdspeak/services/program_rules.py"]}]},
     "No part owns holdspeak/services/program_shaper.py: together the parts own what the step owns."),
])
def test_an_answer_that_does_not_cover_the_step_is_refused_by_name(answer: dict[str, Any], reason: str) -> None:
    parts, error = program_split.read_parts(json.dumps(answer), SPLIT_STEP)
    assert parts is None and error == reason
    good, error = program_split.read_parts(REPLIES[0], SPLIT_STEP)
    assert error is None and [part["title"] for part in good["parts"]] == [part["title"] for part in SPLIT["parts"]]
