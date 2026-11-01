"""Programs: execution perfection (owner ruling 2026-10-31: Programs are the
flagship; delight = pure execution perfection).

The fence is :func:`test_execution_perfection_yolo_three_steps_reach_done_with_no_press`:
a 3-step program at YOLO on a scratch repository with a bare local remote,
the fake agent commits on each step (each commit held by the gate as the
owner's desk saw it, a ``$(printf ...)`` message that reads ``unparsed``),
every step pushes and merges, and the program reaches Done with ZERO Your
turn items at any tick and ZERO owner presses.

The other tests fence the three engine failures of program-ed167ae4478b
"README touch" (2026-10-31): a YOLO commit held for him; a Resume that
surfaced ``worktree_duplicate``; a push with no remote parked after the
agent worked (and said so in git's stderr); a skipped step counted done.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.services.needs_you_membership import program_items
from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig, git

PRINTF_COMMIT = 'git add -A && git commit -q -m "$(printf \'Step\\n\\nbody\')"'


def _program(rig: Rig, *, control: str = "yolo", title: str = "README touch", check: str | None = None) -> str:
    return rig.service.create(
        OWNER, title=title, goal="Show the repository has a friendly README.", repository=str(rig.repo),
        check_command=check or f"sh {FAKE_CHECK}", template="fast-cycle", control=control,
    )["id"]


def _worktree(rig: Rig, step: dict) -> Path:
    return Path(rig.ledger.get(step["launch_id"])["worktree_path"])


def _owner_presses(rig: Rig, pid: str) -> list[str]:
    setup = {"Made the program from the Fast cycle template", "Added 3 steps", "Added 1 step", "Started the program"}
    return [row["line"] for row in rig.program(pid)["checkpoints"] if row["by"] == "owner" and row["line"] not in setup]


def test_execution_perfection_yolo_three_steps_reach_done_with_no_press(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig)
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Add a welcome line", "brief": "Append a welcome line to README.md."},
        {"title": "Link the README from the docs", "brief": "Create docs/index.md.", "after": [1]},
        {"title": "Announce it", "brief": "Append a line to README.md.", "after": [2]},
    ])
    rig.service.start(OWNER, pid)
    files = {1: {"README.md": "# app\nWelcome.\n"}, 2: {"docs/index.md": "See ../README.md\n"},
             3: {"README.md": "# app\nWelcome.\nAnnounced.\n"}}
    for ordinal in (1, 2, 3):
        rig.tick()
        step = rig.step(pid, ordinal)
        assert step["state"] in ("briefed", "working"), step
        # The agent's first call is an unparsed pipe (step 2 of his program:
        # ``env | grep …`` waited and expired): at YOLO it goes on by rule.
        assert rig.gate.propose(step["launch_id"], "env | grep -i holdspeak | sed 's/x/y/'; ls -la",
                                worktree=_worktree(rig, step)) == "allowed"
        assert rig.gate.held(step["launch_id"]) == []
        # The gate holds the agent's commit as his desk saw it (unparsed: a
        # command substitution in the message), in the step's own worktree.
        rig.gate.hold_commit(step["launch_id"], f"gate-{ordinal}", scope="unparsed",
                             cwd=str(_worktree(rig, step)), head=PRINTF_COMMIT)
        rig.tick()
        assert rig.gate.decisions[-1][:2] == (f"gate-{ordinal}", True)
        assert rig.program(pid)["your_turn_items"] == []
        rig.agent.finish(step["launch_id"], files[ordinal], message=f"Step {ordinal}")
        for _ in range(4):
            rig.tick()
            assert rig.program(pid)["your_turn_items"] == [], rig.program(pid)["your_turn_items"]
            assert program_items(rig.service.needs_you_items()) == []
        step = rig.step(pid, ordinal)
        assert step["state"] in ("merged", "done"), step
        assert git(rig.repo, "ls-remote", "origin", step["branch"])  # really pushed to the bare remote
    rig.tick(2)
    program = rig.program(pid)
    assert program["state"] == "done", program["status_line"]
    assert program["done"] == 3 and program["skipped"] == 0
    assert program["your_turn_items"] == [] and program["your_turn"] == 0
    assert _owner_presses(rig, pid) == []
    lines = [row["line"] for row in program["checkpoints"]]
    assert lines.count("Allowed the commit by rule (YOLO)") == 3
    assert not any("waits for you" in line or "failed" in line for line in lines), lines
    assert len([call for call in rig.gh.calls if call[1:3] == ["pr", "merge"]]) == 3


def test_yolo_refuses_a_commit_outside_the_step_worktree_by_rule_never_a_row(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig)
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x"}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.gate.hold_commit(step["launch_id"], scope="outside", head="git -C /elsewhere commit -m x")
    rig.tick()
    assert rig.gate.decisions == [("gate-1", False, "YOLO: a commit outside the step's own worktree is refused")]
    assert rig.program(pid)["your_turn_items"] == []


def test_normal_still_holds_an_unparsed_commit_for_him(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x"}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.gate.hold_commit(step["launch_id"], scope="unparsed", cwd=str(_worktree(rig, step)), head=PRINTF_COMMIT)
    rig.tick()
    assert rig.gate.decisions == []
    assert [item["kind"] for item in rig.program(pid)["your_turn_items"]] == ["commit"]


def test_start_refuses_a_repository_with_no_remote_in_his_words(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig)
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x"}])
    git(rig.repo, "remote", "remove", "origin")
    with pytest.raises(ProgramRefused) as refused:
        rig.service.start(OWNER, pid)
    assert refused.value.code == "repository_no_remote"
    assert refused.value.detail.startswith("The repository has no remote to push to.")
    program = rig.program(pid)
    assert program["state"] == "drafting" and rig.hand.calls == []
    # A program whose steps keep their branches local starts.
    rig.service.change_step(OWNER, pid, rig.step(pid, 1)["id"], gate_merge="none")
    rig.service.start(OWNER, pid)
    assert rig.program(pid)["state"] != "drafting"


def test_start_refuses_a_check_whose_program_is_not_there(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, check="FOO=1 no-such-check-tool --fast")
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x"}])
    with pytest.raises(ProgramRefused) as refused:
        rig.service.start(OWNER, pid)
    assert refused.value.code == "check_not_found" and "no-such-check-tool" in refused.value.detail
    for check in ("sh -c 'echo QUICK CHECK GREEN'", f"FAKE_CHECK_RED=1 sh {FAKE_CHECK}"):
        rig.service.update(OWNER, pid, check_command=check)
        assert rig.service.start(OWNER, pid)["state"] != "drafting"
        rig.service.park(OWNER, pid)


def test_a_push_that_fails_says_it_in_words_and_resume_pushes_again_in_the_same_worktree(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig)
    rig.service.plan(OWNER, pid, steps=[{"title": "Add a welcome line", "brief": "x"}])
    rig.service.start(OWNER, pid)
    origin = git(rig.repo, "config", "--get", "remote.origin.url")  # as written (the rig's GitHub URL)
    git(rig.repo, "remote", "remove", "origin")  # gone after Start: the runtime path
    step = rig.step(pid, 1)
    worktree = _worktree(rig, step)
    rig.agent.finish(step["launch_id"], {"README.md": "# app\nWelcome.\n"})
    rig.tick(2)
    step = rig.step(pid, 1)
    assert step["state"] == "parked" and "does not appear to be a git repository" in step["parked_reason"]
    row = next(row for row in rig.program(pid)["checkpoints"] if row["line"].endswith("; parked"))
    assert row["line"] == "Could not push its branch: this repository has no remote; parked"
    assert "does not appear to be a git repository" in row["undo"]["detail"]
    item = next(item for item in rig.program(pid)["your_turn_items"] if item["kind"] == "parked")
    assert item["title"] == ("Parked step 1 “Add a welcome line”: it could not push its branch: "
                             "this repository has no remote")
    # He adds the remote and presses Resume: the step goes on from its green
    # check in the same worktree (no new agent, never worktree_duplicate).
    git(rig.repo, "remote", "add", "origin", origin)
    hands = len(rig.hand.calls)
    rig.service.decide(OWNER, pid, step["id"], kind="parked", choice="resume")
    rig.tick(3)
    step = rig.step(pid, 1)
    assert len(rig.hand.calls) == hands
    assert step["state"] in ("merged", "done"), step
    assert _worktree(rig, step) == worktree
    lines = [row["line"] for row in rig.program(pid)["checkpoints"]]
    assert "Resumed the step from its green check" in lines
    assert not any("worktree_duplicate" in line for line in lines)


def test_resume_of_a_red_step_hands_it_again_into_its_own_worktree(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, control="normal", check=f"FAKE_CHECK_RED_FILE={tmp_path}/red sh {FAKE_CHECK}")
    rig.service.plan(OWNER, pid, steps=[{"title": "Fails", "brief": "x"}])
    (tmp_path / "red").write_text("1", encoding="utf-8")
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    worktree = _worktree(rig, step)
    for n in (1, 2):
        rig.agent.finish(step["launch_id"], {"a.txt": f"{n}\n"})
        rig.tick()
        if n == 1:
            rig.agent.start_turn(step["launch_id"])
            rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] == "parked", step
    (tmp_path / "red").unlink()
    rig.service.decide(OWNER, pid, step["id"], kind="parked", choice="resume")
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] in ("briefed", "working"), step
    assert _worktree(rig, step) == worktree
    lines = [row["line"] for row in rig.program(pid)["checkpoints"]]
    assert not any("worktree_duplicate" in line for line in lines), lines
    rig.agent.finish(step["launch_id"], {"a.txt": "3\n"})
    rig.tick(3)
    assert rig.step(pid, 1)["state"] in ("merged", "done")


def test_a_skipped_step_is_never_counted_done(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, control="secure", check=f"FAKE_CHECK_RED=1 sh {FAKE_CHECK}")
    rig.service.plan(OWNER, pid, steps=[{"title": "Break it", "brief": "x"}, {"title": "After", "brief": "y",
                                                                               "after": [1]}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.agent.finish(step["launch_id"], {"a.txt": "1\n"})
    rig.tick()
    rig.agent.start_turn(step["launch_id"])
    rig.tick()
    rig.agent.finish(step["launch_id"], {"a.txt": "2\n"})
    rig.tick()
    assert rig.step(pid, 1)["state"] == "parked"
    rig.service.decide(OWNER, pid, step["id"], kind="parked", choice="skip")
    rig.tick()
    program = rig.program(pid)
    assert program["done"] == 0 and program["skipped"] == 1
    assert " · 0 of 2 done · 1 skipped" in program["status_line"]
    assert rig.step(pid, 2)["state"] in ("briefed", "working")  # its dependent runs on


def test_a_parked_program_asks_nothing_and_its_pages_revoke_resume_raises_them_again(tmp_path) -> None:
    """program-ed167ae4478b after Park still said "1 waits on you"."""
    from holdspeak.db.briefing import BriefingStore
    from holdspeak.services.briefing_service import BriefingService

    rig = Rig(tmp_path)
    pid = _program(rig, control="normal", check=f"FAKE_CHECK_RED=1 sh {FAKE_CHECK}")
    rig.service.plan(OWNER, pid, steps=[{"title": "Break it", "brief": "x"}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.agent.finish(step["launch_id"], {"a.txt": "1\n"})
    rig.tick()
    rig.agent.start_turn(step["launch_id"])
    rig.tick()
    rig.agent.finish(step["launch_id"], {"a.txt": "2\n"})
    rig.tick()
    [item] = rig.program(pid)["your_turn_items"]
    assert item["kind"] == "parked"
    made = BriefingService(rig.db, programs=lambda: rig.service).make(OWNER, [f"program:{pid}:{item['id']}"])
    rig.service.park(OWNER, pid)
    program = rig.program(pid)
    assert program["your_turn_items"] == [] and program["your_turn"] == 0
    assert program["status_line"].startswith("Parked · ") and "waits on you" not in program["status_line"]
    assert program_items(rig.service.needs_you_items()) == []
    assert BriefingStore(rig.db).get(made["id"])["revoked_at"]
    rig.service.resume(OWNER, pid)
    assert [row["kind"] for row in rig.program(pid)["your_turn_items"]] == ["parked"]


# ── the live proof's two causes (2026-11-01, his hub, program-2633c39e2151) ─

def test_execution_perfection_a_bare_remote_and_a_plain_check_reach_done_with_no_press(tmp_path) -> None:
    """His proof repository: a bare ``origin`` beside it (no GitHub, no PR)
    and a plain check command (``sh -c 'test -f README.md'``, no verdict
    line). The check is green by its exit; HoldSpeak merges each step into
    main on the remote itself; Done with zero Your turn items and no gh."""
    rig = Rig(tmp_path, github=False)
    pid = _program(rig, check="sh -c 'test -f README.md'")
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Add a line to the README", "brief": "x"},
        {"title": "Link the README from the docs", "brief": "y", "after": [1]},
        {"title": "Add a CHANGELOG line", "brief": "z", "after": [2]},
    ])
    rig.service.start(OWNER, pid)
    files = {1: {"README.md": "# app\nProof.\n"}, 2: {"docs/index.md": "See ../README.md\n"},
             3: {"CHANGELOG.md": "- The proof ran.\n"}}
    for ordinal in (1, 2, 3):
        rig.tick()
        step = rig.step(pid, ordinal)
        rig.agent.finish(step["launch_id"], files[ordinal], message=f"Step {ordinal}")
        for _ in range(4):
            rig.tick()
            assert rig.program(pid)["your_turn_items"] == []
        assert rig.step(pid, ordinal)["check"]["verdict"] == "green"
        assert rig.step(pid, ordinal)["state"] in ("merged", "done"), rig.step(pid, ordinal)
    rig.tick(2)
    program = rig.program(pid)
    assert program["state"] == "done" and program["done"] == 3, program["status_line"]
    assert _owner_presses(rig, pid) == [] and [call for call in rig.gh.calls if call[:2] == ["gh", "pr"]] == []
    git(rig.repo, "fetch", "-q", "origin", "main")
    shipped = git(rig.repo, "ls-tree", "-r", "--name-only", "FETCH_HEAD").splitlines()
    assert {"README.md", "docs/index.md", "CHANGELOG.md"} <= set(shipped)
    lines = [row["line"] for row in program["checkpoints"]]
    assert sum(1 for line in lines if line.startswith("Merged step ") and " into main on the remote" in line) == 3
    assert not any("asked the agent to commit" in line for line in lines)


def test_at_secure_a_bare_remote_merge_is_his_row_and_his_press_merges_it(tmp_path) -> None:
    rig = Rig(tmp_path, github=False)
    pid = _program(rig, control="secure", check="sh -c 'test -f README.md'")
    rig.service.plan(OWNER, pid, steps=[{"title": "Add a line", "brief": "x"}])
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"README.md": "# app\nProof.\n"})
    rig.tick(3)
    [item] = rig.program(pid)["your_turn_items"]
    assert item["kind"] == "merge" and item["title"] == "Merge step 1 “Add a line”? (into main, check green)"
    rig.service.decide(OWNER, pid, rig.step(pid, 1)["id"], kind="merge", choice="merge")
    rig.tick()
    assert rig.step(pid, 1)["state"] in ("merged", "done")


def test_a_red_checks_prompt_is_never_read_as_a_turn_with_no_commit(tmp_path) -> None:
    """The proof's ledger: "New commit …; the check runs", the check red, then
    "The turn ended with no commit; asked the agent to commit" for the turn
    that MADE the commit (it was still ending when the engine took it)."""
    rig = Rig(tmp_path)
    pid = _program(rig, control="normal", check="sh -c 'exit 1'")
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x"}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    worktree = Path(rig.ledger.get(step["launch_id"])["worktree_path"])
    (worktree / "a.txt").write_text("1\n", encoding="utf-8")
    git(worktree, "add", "-A")
    git(worktree, "commit", "-m", "work")  # the agent commits; its turn still runs
    row = rig.service.store.get_step(step["id"])
    row["facts"] = {**row["facts"], "said_done": True}
    rig.service.store.save_step(row)
    rig.tick()
    assert rig.step(pid, 1)["check"]["verdict"] == "red" and rig.step(pid, 1)["rounds"] == 1
    rig.agent.end_turn(step["launch_id"])  # the turn that made the commit ends now
    rig.tick()
    lines = [row["line"] for row in rig.program(pid)["checkpoints"]]
    assert not any("turn ended with no commit" in line for line in lines), lines
