"""PG-IMPORT IMP2 (BROCREW-IMPORT-2026-11-01): the to-do row and the ending word.

BroCrew's to-do: "Ada asks you to do this · W3.1", Done / Can't do it, an
optional note; after the press the agent is told. Ours: a required Your word
requirement with walk lines is a Your turn row of kind ``todo`` from the
step's start to its merge. Done writes it Met (his word, his note); Can't do
it writes it Unmet with his note and leaves it on the step (Send back or
Waive next). The agent is told in the step's next prompt.

BroCrew's ending word: "the status column answers 'is this conversation
over' … it has never answered 'did the work in it finish'". Each step
carries ``ending`` apart from its state: a cut-off lane is interrupted, a
green finish is finished.
"""
from __future__ import annotations

from typing import Any

from holdspeak.services import brief_words as words
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig


def _walk(tmp_path) -> tuple[Rig, str, dict[str, Any]]:
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Atlas at 393", goal="The atlas reads well on a phone.",
                             repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", template="fast-cycle",
                             control="normal")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Atlas anchors", "brief": "Cite each anchor once."}])
    step = rig.step(pid, 1)
    rig.service.require(OWNER, pid, text="The atlas reads well at 393", kind="word", step_id=step["id"],
                        spec={"walk": ["Open the atlas at 393", "Read the first section"]})
    rig.service.start(OWNER, pid)
    rig.tick()
    item = next(row for row in rig.program(pid)["your_turn_items"] if row["kind"] == "todo")
    return rig, pid, item


def test_a_walk_is_a_todo_row_while_the_step_runs(tmp_path) -> None:
    rig, pid, item = _walk(tmp_path)
    assert rig.step(pid, 1)["state"] in ("briefed", "working")
    assert item["head"] == "Claude Code asks you to do this · step 1"
    assert item["walk"] == ["Open the atlas at 393", "Read the first section"]
    assert item["choices"] == ["done", "cant"]
    brief = item["brief"]
    assert brief["question"] == "Did you do it?"
    assert brief["consequences"]["done"] == "The requirement is met. Claude Code is told."
    for line in [brief["happened"], brief["question"], *brief["consequences"].values()]:
        assert words.fence_hits(line) == [], line
    # Never a second row for the same requirement (no Your word row too).
    assert [row["kind"] for row in rig.program(pid)["your_turn_items"]] == ["todo"]


def test_done_writes_it_met_and_the_agent_is_told(tmp_path) -> None:
    rig, pid, item = _walk(tmp_path)
    rig.service.decide_requirement(OWNER, pid, item["requirement_id"], "done", line="Looks right on my phone")
    step = rig.step(pid, 1)
    row = next(req for req in step["requirements"] if req["id"] == item["requirement_id"])
    assert row["state"] == "met" and row["evidence"]["by"] == "owner"
    assert row["evidence"]["line"].endswith("Looks right on my phone")
    told = step["amendments"][-1]
    assert told["by"] == "owner" and told["sent_at"] is None  # typed at the next turn boundary
    assert told["line"].startswith("The owner did R1 by hand") and "Looks right on my phone" in told["line"]
    assert not [row for row in rig.program(pid)["your_turn_items"] if row["kind"] == "todo"]


def test_cant_do_it_writes_it_unmet_and_leaves_it_on_the_step(tmp_path) -> None:
    rig, pid, item = _walk(tmp_path)
    rig.service.decide_requirement(OWNER, pid, item["requirement_id"], "cant", line="No phone with me")
    step = rig.step(pid, 1)
    row = next(req for req in step["requirements"] if req["id"] == item["requirement_id"])
    assert row["state"] == "unmet"
    assert "cannot do R1" in step["amendments"][-1]["line"]
    kinds = {row["kind"]: row for row in rig.program(pid)["your_turn_items"]}
    assert "todo" not in kinds and kinds["requirement_left"]["choices"] == ["send_back", "waive"]


def test_the_ending_word_beside_the_state(tmp_path) -> None:
    rig, pid, _item = _walk(tmp_path)
    step = rig.step(pid, 1)
    assert step["ending"] == "none"
    rig.states[step["launch_id"]] = {"state": "ended", "turn_id": None}  # the lane was cut off
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] == "parked" and step["ending"] == "interrupted"
    line = next(row for row in rig.service.list(OWNER)["programs"] if row["id"] == pid)["line"]
    assert line.endswith(" · interrupted"), line


def test_a_green_finish_is_finished(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Docs", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="fast-cycle", control="normal")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Docs", "brief": "x"}])
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"docs/a.md": "x\n"})
    rig.tick(3)
    step = rig.step(pid, 1)
    assert step["state"] in ("merged", "done") and step["ending"] == "finished"
