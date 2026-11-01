"""The first real night (2026-11-01): a step's reviewer got the BUILDER's
brief (``compose_agent_brief`` sends a program_step to the step's own brief
and dropped the review instruction), took itself for the builder, and wrote
no MUST line: "Reviewer result is unclear" and "R1 has no answer" went to
him at YOLO. A step's helper with an instruction now gets the review brief:
the instruction first, the step as data, never the builder's rules."""
from __future__ import annotations

from holdspeak.services.program_brief import compose_review
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig
from tests.unit.test_agent_hand import db  # noqa: F401  (fixture)

INSTRUCTION = ("Review item program_step:x — Define program.\nRound 1. The builder commit is abc. Review the diff of "
               "this branch against main.\nAcceptance checks:\n- Review depth: glance.\n- Answer each of the owner's "
               "requirements on its own line: REQ R1: MET · <one line> or REQ R1: UNMET · <what is missing>.\n"
               "- R1 · The change does only what its brief says.\n\nRead the worktree only. Change nothing and do not "
               "commit.\nList findings one per line with MUST or SHOULD, file and line when known. End with MUST: none "
               "when no MUST finding remains.")


def test_a_reviewer_gets_the_review_instruction_and_the_step_as_data(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Night proof", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="build-and-review")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Define program", "brief": "Create docs/glossary.md.",
                                         "owns": ["docs/glossary.md"]}])
    step = rig.service.store.list_steps(pid)[0]
    brief = compose_review(rig.db, step["id"], INSTRUCTION)
    text = brief["text"]
    assert text.startswith("HoldSpeak: you REVIEW step 1 of the program “Night proof”. You do not build it.")
    assert "End with MUST: none when no MUST finding remains." in text and "REQ R1: MET" in text
    assert "Create docs/glossary.md." in text and "- docs/glossary.md" in text
    # Never the builder's rules.
    assert "program.step_done" not in text and "Commit your work" not in text
    assert brief["refs"] == [f"program_step:{step['id']}"]


def test_the_hand_sends_a_step_helper_the_review_brief(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """The real hand (``AgentHandService`` over the hand rig): a Program
    step's helper started with an instruction gets the review brief."""
    from tests.unit.test_program_control_level import _step_launch

    rig, helper, pending, _argv = _step_launch(tmp_path, db, monkeypatch, agent="claude", desk="yolo",
                                               control="yolo", helper=True)
    assert pending is None
    text = rig.launches.get(helper["launch_id"])["brief_text"]
    assert text.startswith("HoldSpeak: you REVIEW step 1 of the program “The hub stops stalling”.")
    assert "Read the diff." in text and "Add the three indexes." in text
    assert "program.step_done" not in text


def test_the_review_brief_carries_the_diff_so_the_reviewer_never_reads_outside(tmp_path) -> None:
    """The second real night: a read-only reviewer with no shell read the
    main checkout to compare, and Claude Code held it on its "read outside
    the working directories" prompt. The diff is in the brief now."""
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Night proof", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="build-and-review", control="yolo")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Define program", "brief": "Create docs/glossary.md."}])
    rig.service.start(OWNER, pid)
    rig.tick()
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"docs/glossary.md": "A program is a goal in steps.\n"})
    rig.tick()
    step = rig.service.store.list_steps(pid)[0]
    text = compose_review(rig.db, step["id"], INSTRUCTION)["text"]
    assert "```diff" in text and "+A program is a goal in steps." in text and "docs/glossary.md" in text
    assert "Do not read outside your worktree." in text


def test_a_long_diff_is_cut_in_whole_lines() -> None:
    from types import SimpleNamespace

    from holdspeak.services.program_brief import REVIEW_DIFF_BYTES, step_diff

    long = "\n".join(f"+line {n} " + "x" * 60 for n in range(400)) + "\n"
    run = lambda argv, **_kw: SimpleNamespace(returncode=0, stdout=long)  # noqa: E731
    cut = step_diff({"worktree": "/w", "head_commit": "b", "facts": {"base_commit": "a"}}, runner=run)
    assert len(cut.encode("utf-8")) <= REVIEW_DIFF_BYTES + 80 and cut.endswith("the rest is in your worktree's files)")
    assert step_diff({"worktree": "/w", "head_commit": "a", "facts": {"base_commit": "a"}}, runner=run) == ""
