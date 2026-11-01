"""PG-WINDOW W1 (PROGRAM-WINDOW-2026-10-31): the Program window reads the
brief in his terms, on the Programs rig.

On his desk the window's one line for a parked step was the raw git stderr.
The wire now carries, on each ``your_turn_items`` row, ``brief``: the same
lines the briefing page reads (the goal, the step, what happened, the
question, what waits on the answer, each choice's consequence), and on each
step ``story``: at most three plain lines of what the agent did. Every line
passes the BRIEF RULE's fence (no ``fatal:``, path, command or hash).
The status line names the check's script, never a flag (``check: -c``).
"""
from __future__ import annotations

from holdspeak.services import brief_words as words
from holdspeak.services.program_service import _check_name
from tests.unit.test_brief_in_his_terms import _no_remote


def test_the_held_item_carries_the_brief_in_his_terms(tmp_path) -> None:
    rig, pid = _no_remote(tmp_path)
    wire = rig.program(pid)
    item = next(row for row in wire["your_turn_items"] if row["kind"] == "parked")
    brief = item["brief"]
    assert brief["goal"] == "Goal: Show the repo has a friendly README."
    assert brief["doing"] == "Step 1, “Add one line to the README”: Append one line under the title."
    assert brief["happened"] == "The step could not push its branch: this repository has no remote."
    assert brief["question"] == "Start the step again, or stop it?"
    assert brief["blocked"] == [2, 3]
    assert brief["blocked_words"] == "2 steps wait on this: 2 Link the README, 3 Announce it."
    assert brief["consequences"] == {
        "resume": "Try the step again. It will fail the same way until the repository has a remote.",
        "skip": "Stop this step. The 2 steps that wait on it wait too.",
    }
    for line in [brief["goal"], brief["doing"], brief["happened"], brief["question"], brief["blocked_words"],
                 *brief["consequences"].values()]:
        assert words.fence_hits(line) == [], line
    # The raw reason stays where it was (the step's parked_reason), never a brief line.
    step = next(row for row in wire["steps"] if row["ordinal"] == 1)
    assert "fatal:" in step["parked_reason"]


def test_each_step_carries_its_story_in_plain_lines(tmp_path) -> None:
    rig, pid = _no_remote(tmp_path)
    wire = rig.program(pid)
    first, second = (next(row for row in wire["steps"] if row["ordinal"] == n) for n in (1, 2))
    story = first["story"]
    assert 1 <= len(story) <= 3
    assert all(words.fence_hits(row["line"]) == [] for row in story), story
    assert "The check ran green in under a minute." in [row["line"] for row in story]
    assert [row["at"] for row in story] == sorted(row["at"] for row in story)
    # A step that has not started has no story (never an empty line).
    assert second["story"] == []


def test_the_check_is_named_by_its_script_never_a_flag() -> None:
    assert _check_name("FOO=1 sh scripts/quick_check.sh --fast") == "quick_check.sh"
    assert _check_name('sh -c "test -f README.md && grep -q Hello README.md"') == "test"
    assert _check_name("uv run pytest -q tests/unit/test_a.py") == "pytest"
