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


def test_the_engines_own_ledger_words_read_in_his_terms() -> None:
    """The live window quoted "Skipped the step" and "Could not hand the
    step: worktree_duplicate" (2026-11-01): the story says them plainly and
    never carries a wire code."""
    assert words.changed_line("Skipped the step") == "You skipped the step."
    assert words.changed_line("Resumed the step") == ""  # the brief and the row say it already
    assert words.changed_line("Could not hand the step: worktree_duplicate") == "HoldSpeak could not give the step to an agent."
    assert words.changed_line("Said it is done; the engine waits for the commit") == "The agent said it is done."
    assert words.changed_line("Handed to Claude Code in hs-program-step-c2f418bb1a7f") == "Handed to Claude Code."
    assert words.changed_line("git push failed; parked") == ""
    assert words.changed_line("The engine said: some_code here") == ""
    assert words.changed_line("Checked · green · under a minute · /tmp/a_b/step_x.log") == "The check ran green in under a minute."


def test_the_list_row_reads_like_a_line_from_a_chief_of_staff(tmp_path) -> None:
    """PG-WINDOW List: each Program's list row carries its line and its mini
    track, in plain words with no zero count."""
    import re

    rig, pid = _no_remote(tmp_path)
    [row] = [item for item in rig.service.list(None)["programs"] if item["id"] == pid]
    assert re.fullmatch(r"Step 1 of 3 waits on you since \d\d:\d\d", row["line"]), row["line"]
    assert [dot["mark"] for dot in row["track"]] == ["here", "planned", "planned"]
    assert words.fence_hits(row["line"]) == []
    assert words.list_line("drafting", [], []) == "Drafting, no steps yet"
    assert words.list_line("done", [], [], history={"words": "Merged 14 PRs · 28 Oct"}) == "Done, merged 14 PRs, 28 Oct"
