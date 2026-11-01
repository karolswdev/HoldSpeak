"""PG-LANG §13b JRN11 and JRN12 (journey J8, "Teaching the engine").

The lesson rule over the real engine (``program_rig``): the same red cause
of the check on two steps, or the same reviewer finding on three, is one
Lesson row (Keep for this program · Keep for HoldSpeak · Skip), never kept
by rule at any level. Keep for this program adds an every-step requirement;
Keep for HoldSpeak adds a tiny step whose diff is one JSON change to
``.holdspeak/program.json``, checked and merged as any step; a new Program
plants the kept requirement from the repository. A skipped cause is not
proposed again. The rows are stored for the face (``lesson.row.json``).
"""
from __future__ import annotations

import json
from pathlib import Path

from holdspeak.services.needs_you_membership import program_items
from holdspeak.services.program_lessons import key_of, red_cause
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig, git
from tests.integration.test_desk_programs import _fixture

RED = "E   ModuleNotFoundError: No module named 'pytest_xdist'"


def _red_check(tmp_path: Path) -> Path:
    """A check that is red with one line while ``RED`` is in the worktree's
    ``red.txt``, else the rig's green check."""
    script = tmp_path / "check.sh"
    script.write_text(
        "#!/bin/sh\n"
        "if [ -f red.txt ]; then echo \"$(cat red.txt)\"; echo 'FAILED'; exit 1; fi\n"
        f"exec sh {FAKE_CHECK} \"$@\"\n", encoding="utf-8")
    return script


def _program(rig: Rig, check: Path, control: str = "yolo", steps: int = 3) -> str:
    pid = rig.service.create(OWNER, title="The words wave", goal="Plain words.", repository=str(rig.repo),
                             check_command=f"sh {check}", template="fast-cycle", control=control)["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": f"Step {n}", "brief": f"Do part {n}."} for n in range(1, steps + 1)])
    rig.service.start(OWNER, pid)
    rig.tick()
    return pid


def _lessons(rig: Rig, pid: str) -> list[dict]:
    return [item for item in rig.program(pid)["your_turn_items"] if item["kind"] == "lesson"]


def _go_red(rig: Rig, pid: str, ordinal: int) -> None:
    step = rig.step(pid, ordinal)
    rig.agent.finish(step["launch_id"], {"red.txt": RED + "\n", f"part{ordinal}.txt": "x\n"}, message=f"Part {ordinal}")
    rig.tick(2)


def test_two_reds_with_one_cause_raise_one_lesson_and_keep_for_this_program(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, _red_check(tmp_path))
    _go_red(rig, pid, 1)
    assert _lessons(rig, pid) == []  # one step red for it: not a lesson yet
    _go_red(rig, pid, 2)
    [row] = _lessons(rig, pid)
    assert row["title"].startswith("Lesson · the check is red with “") and row["title"].endswith(": 2 steps red for it")
    assert row["choices"] == ["keep_program", "keep_repo", "skip"] and row["steps"] == [1, 2]
    assert row["brief"]["question"] == "Keep this lesson, and where?"
    [needs] = [item for item in program_items(rig.service.needs_you_items()) if item["program"]["kind"] == "lesson"]
    assert needs["why"] == "TO DECIDE" and needs["program"]["lessonId"] == row["lesson_id"]
    _fixture("lesson.row.json", row, tmp_path)
    rig.tick(3)
    assert len(_lessons(rig, pid)) == 1  # the rule runs again; one lesson, never kept by rule at YOLO
    answer = rig.service.decide(OWNER, pid, row["step_id"], kind="lesson", choice="keep_program",
                                proposal_id=row["lesson_id"])
    reqs = [req for req in rig.service.requirements(pid) if req["text"] == row["requirement"]]
    [parent] = [req for req in reqs if not req.get("step_id")]
    assert parent["each_step"] and parent["kind"] == "review" and len(reqs) == 4  # the parent and each step's copy
    assert answer["requirement_id"] == parent["id"] and _lessons(rig, pid) == []
    assert "Lesson kept for this program: " + row["requirement"] in [c["line"] for c in rig.program(pid)["checkpoints"]]


def test_a_skipped_cause_is_not_proposed_again(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, _red_check(tmp_path))
    _go_red(rig, pid, 1)
    _go_red(rig, pid, 2)
    [row] = _lessons(rig, pid)
    rig.service.decide(OWNER, pid, row["step_id"], kind="lesson", choice="skip", proposal_id=row["lesson_id"])
    _go_red(rig, pid, 3)
    assert _lessons(rig, pid) == []
    again = rig.service.decide
    try:
        again(OWNER, pid, row["step_id"], kind="lesson", choice="skip", proposal_id=row["lesson_id"])
    except Exception as exc:  # the row is answered
        assert getattr(exc, "code", "") == "not_waiting"
    else:
        raise AssertionError("a second press was taken")


def test_note_findings_and_the_red_cause_by_rule() -> None:
    from holdspeak.services import program_lessons

    facts = [{}, {}, {}]
    for n, fact in enumerate(facts):
        program_lessons.note_findings(fact, [{"text": "A raw <button> in the toolbar."},
                                             {"text": f"R{n + 1} is unmet: x"}])
    keys = [set(fact["lesson_seen"]) for fact in facts]
    assert keys[0] == keys[1] == keys[2] and len(keys[0]) == 1
    assert red_cause(["the section pytest is red", "a line is red: E   boom 12"]) == "E   boom 12"
    assert key_of("red", "E boom 12") == key_of("red", "e   BOOM 13")


def test_keep_for_the_repository_is_a_step_of_one_json_change_the_next_program_reads(tmp_path) -> None:
    rig = Rig(tmp_path, github=False)  # a bare remote: HoldSpeak merges into its main itself
    pid = _program(rig, _red_check(tmp_path), steps=2)
    _go_red(rig, pid, 1)
    _go_red(rig, pid, 2)
    [row] = _lessons(rig, pid)
    answer = rig.service.decide(OWNER, pid, row["step_id"], kind="lesson", choice="keep_repo",
                                proposal_id=row["lesson_id"])
    rig.tick()
    keep = next(step for step in rig.program(pid)["steps"] if step["id"] == answer["step_id"])
    assert keep["origin_ref"] == f"lesson:{row['lesson_id']}" and keep["owns"] == [".holdspeak/program.json"]
    assert keep["gate"]["check"] is True and keep["gate"]["merge"] == "level"
    assert "requirements" in keep["brief"] and row["requirement"] in keep["brief"]
    # The agent makes the one JSON change; the step is checked and merged as any step.
    body = {"requirements": [{"text": row["requirement"], "kind": "review", "each_step": True, "required": True}]}
    rig.agent.finish(keep["launch_id"], {".holdspeak/program.json": json.dumps(body, indent=2) + "\n"},
                     message="Keep the lesson")
    rig.tick(6)
    keep = next(step for step in rig.program(pid)["steps"] if step["id"] == answer["step_id"])
    assert keep["state"] in ("merged", "done"), keep
    # His checkout has the merge (a pull); the step's diff is the one JSON file.
    git(rig.repo, "pull", "-q", "origin", "main")
    assert git(rig.repo, "log", "-1", "--name-only", "--format=") == ".holdspeak/program.json"
    # The next Program plants the lesson from the repository.
    nxt = rig.service.create(OWNER, title="Next", repository=str(rig.repo), template="build-and-review")["id"]
    assert row["requirement"] in [req["text"] for req in rig.service.requirements(nxt)]


def test_three_steps_with_one_review_finding_raise_a_lesson(tmp_path) -> None:
    from holdspeak.services import program_lessons

    rig = Rig(tmp_path)
    pid = _program(rig, _red_check(tmp_path))
    for ordinal in (1, 2, 3):
        step = rig.service.store.get_step(rig.step(pid, ordinal)["id"])
        program_lessons.note_findings(step["facts"], [{"level": "SHOULD", "text": "A raw `<button>` in the toolbar"}])
        rig.service.save_step(step)
        rig.service.changed(pid)
        assert len(_lessons(rig, pid)) == (1 if ordinal == 3 else 0)
    [row] = _lessons(rig, pid)
    assert row["title"] == "Lesson · “A raw `<button>` in the toolbar” on 3 steps" and row["source"] == "finding"
    assert row["requirement"] == "The change does not repeat this finding: A raw `<button>` in the toolbar"
