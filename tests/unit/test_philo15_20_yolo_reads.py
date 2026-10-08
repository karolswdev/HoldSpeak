"""PHILO-15 20: YOLO lets the agent read; Raw is where a cut call is
approved (rehearsal 2, docs/internal/philo/phase-15/rehearsal-2/BOUNCES-C.md).

B62  The calls YOLO held in rehearsal 2, word for word, pass: a git config
     read, ``gh --version``, ``$?`` and a read in ``$( ... )`` printed by
     ``echo``, a script in the worktree. Config writes, pushes to another
     branch and anything outside the worktree still hold.
B63  The hub keeps the whole redacted call of a cut hold for the owner's
     Raw read only, and drops it when the hold ends (the real hub fence is
     ``tests/integration/test_philo15_20_yolo_reads_real_hub.py``).
B66  A Deny names the hold's reason to the agent.
B67  A queued Re-brief can be taken back; its receipt is TAKEN BACK.
B68  The agent's finished report (shot 49, its exact words) reads DONE.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from holdspeak.agent_context.models import TURN_DONE, asks_a_question, reports_a_problem, turn_end
from holdspeak.services import launch_rebrief
from holdspeak.tool_gate_rules import INSIDE, OUTSIDE, UNPARSED, classify_bash, hold_reason
from tests.unit.test_agent_hand import OWNER
from tests.unit.test_conductor_k5_supervision import (  # noqa: F401  (fixtures)
    KEY,
    _members,
    _responder,
    db,
    launched,
)
from tests.unit.test_philo15_codex_launch_truth import _flush, _hook, _idle, _lane, _press, _texts, _working

#: Shot 49 / 48 (BOUNCES-C B67, B68): the agent's last words, transcribed.
B68_REPORT = (
    "Confirmed — already conforming to the re-brief: - No files written outside the worktree. Only "
    "`CODEOWNERS` and `tests/codeowners_test.sh` were created, both inside the worktree. (The earlier "
    "`/tmp` write attempts were blocked, so nothing landed outside.) - PR opened via `gh pr create` with "
    "the body passed inline through `--body`. **Current state** - Worktree clean; branch "
    "`hs/action-action_8ea0eb39eb080881760399af` pushed, not on main. - PR "
    "https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/4 — `OPEN`, `MERGEABLE`, body "
    "names `action:action_8ea0eb39eb080881760399af` and its test `tests/codeowners_test.sh`. - "
    "`CODEOWNERS` maps `*` → Kiraal Swedeva; test passes. Item meets the done criteria (PR open, tests "
    "pass). I left the merge to you per the Squash-Merge-only decision."
)


@pytest.fixture
def worktree(tmp_path: Path) -> Path:
    root = tmp_path / "wt"
    (root / "tests").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "hs/action-x", str(root)], check=True)
    (root / "tests" / "codeowners_test.sh").write_text("#!/bin/sh\ntest -f CODEOWNERS\n", encoding="utf-8")
    (root / "VERSION").write_text("1.0\n", encoding="utf-8")
    return root.resolve()


# ── B62 ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("command", [
    "git config user.name; git config user.email",
    "command -v gh && gh --version",
    'bash tests/codeowners_test.sh; echo "exit=$?"',
    'git status --short && echo "HEAD=$(git rev-parse HEAD)"',
    'git config user.name && git config user.email && git config --get remote.origin.url',
    "git config get user.name",
    "gh version",
    "gh auth status",
    "gh pr view 4",
    'printf "%s\\n" "$(git log -1 --format=%H)"',
    "[ $? -eq 0 ] && echo ok",
    "./tests/codeowners_test.sh",
    # Astra's ruling on #1011: the read and the output both in the worktree.
    'echo "$(cat VERSION)" > out.txt',
    "printf '%s' \"$(git rev-parse HEAD)\" | tee note.txt",
])
def test_the_agents_reads_and_its_own_test_run_are_inside(worktree: Path, command: str) -> None:
    verdict = classify_bash(command, cwd=str(worktree), root=str(worktree))
    assert verdict.scope == INSIDE, verdict


@pytest.mark.parametrize("command, scope, reason", [
    ("git config user.name Bob", OUTSIDE, "SHARED GIT STATE"),
    ("git config --global user.email bob@example.test", OUTSIDE, "SHARED GIT STATE"),
    ("git config --unset user.name", OUTSIDE, "SHARED GIT STATE"),
    ("git config --add user.name Bob", OUTSIDE, "SHARED GIT STATE"),
    ("git config set user.name Bob", OUTSIDE, "SHARED GIT STATE"),
    ("gh pr merge 4 --squash", OUTSIDE, "GITHUB ACTION FOR YOU"),
    ("gh api /user", OUTSIDE, "GITHUB ACTION FOR YOU"),
    ("bash /tmp/run.sh", OUTSIDE, "OUTSIDE THE WORKTREE · /tmp/run.sh"),
    ('echo "$(git rev-parse HEAD)" > /tmp/head.txt', OUTSIDE, "OUTSIDE THE WORKTREE · /tmp/head.txt"),
    ("printf '%s' \"$(git rev-parse HEAD)\" | tee /tmp/note.txt", OUTSIDE, "OUTSIDE THE WORKTREE · /tmp/note.txt"),
    ('echo "$(cat ../VERSION)" > out.txt', UNPARSED, "UNRESOLVED TARGET · $(cat ../VERSION)"),
    ('cat "$(git rev-parse --show-toplevel)/../x"', UNPARSED, "UNRESOLVED TARGET · $(git rev-parse --show-toplevel)"),
    ("echo $(rm -rf ../x)", UNPARSED, "UNRESOLVED TARGET · $(rm -rf ../x)"),
    ('echo "$(git push origin HEAD)"', UNPARSED, "UNRESOLVED TARGET · $(git push origin HEAD)"),
    ("echo $(cat ../secret)", UNPARSED, "UNRESOLVED TARGET · $(cat ../secret)"),
    ("echo $(bash tests/codeowners_test.sh)", UNPARSED, "UNRESOLVED TARGET · $(bash tests/codeowners_test.sh)"),
    ('echo "$(curl example.test)"', UNPARSED, "UNRESOLVED TARGET · $(curl example.test)"),
    # Astra r1 on #1011 (P1-3): a test operand can be a file test: it holds like a path.
    ('test -f "$(git rev-parse --show-toplevel)/../outside"', UNPARSED, "UNRESOLVED TARGET · $(git rev-parse --show-toplevel)"),
    ("[ -f $(git rev-parse --show-toplevel)/x ]", UNPARSED, "UNRESOLVED TARGET · $(git rev-parse --show-toplevel)"),
    ('test -n "$(git rev-parse HEAD)"', UNPARSED, "UNRESOLVED TARGET · $(git rev-parse HEAD)"),
    ("X=$? ls", UNPARSED, "UNRESOLVED TARGET · $?"),
    ("echo hi > $(git rev-parse --show-toplevel)/x", UNPARSED, "UNRESOLVED TARGET · $(git rev-parse --show-toplevel)"),
    ('git push origin "$(git branch --show-current)"', UNPARSED, "UNRESOLVED TARGET · $(git branch --show-current)"),
    ("echo $HOME", UNPARSED, "UNRESOLVED TARGET · $HOME"),
])
def test_writes_pushes_and_the_outside_still_hold(worktree: Path, command: str, scope: str, reason: str) -> None:
    verdict = classify_bash(command, cwd=str(worktree), root=str(worktree))
    assert verdict.scope == scope, verdict
    assert hold_reason(verdict.scope, verdict.rule, verdict.target) == reason


def test_a_substitution_is_read_in_the_folder_after_cd(worktree: Path, tmp_path: Path) -> None:
    """Astra r1 on #1011 (P1-4), her producer probe: ``sub/secret`` is a
    symlink out of the worktree; ``cd sub && echo "$(cat secret)"`` printed
    the outside file. The substitution is read where it runs (after the cd,
    symlinks resolved): it holds. Run by bash, it would print the outside."""
    outside = tmp_path / "outside-secret"
    outside.write_text("outside content\n", encoding="utf-8")
    (worktree / "sub").mkdir()
    (worktree / "sub" / "secret").symlink_to(outside)
    (worktree / "sub" / "inside.txt").write_text("in\n", encoding="utf-8")
    probe = 'cd sub && echo "$(cat secret)"'
    ran = subprocess.run(["bash", "-c", probe], cwd=worktree, capture_output=True, text=True)
    assert ran.stdout == "outside content\n"  # what an approval would have printed
    verdict = classify_bash(probe, cwd=str(worktree), root=str(worktree))
    assert verdict.scope == UNPARSED
    assert hold_reason(verdict.scope, verdict.rule, verdict.target) == "UNRESOLVED TARGET · $(cat secret)"
    # The same read of a file inside the worktree passes.
    assert classify_bash('cd sub && echo "$(cat inside.txt)"', cwd=str(worktree), root=str(worktree)).scope == INSIDE


def test_a_read_in_a_substitution_keeps_the_normal_read_rule(worktree: Path) -> None:
    verdict = classify_bash('git status --short && echo "HEAD=$(git rev-parse HEAD)"',
                            cwd=str(worktree), root=str(worktree))
    assert verdict.read_rule == "git-status+echo"


# ── B63 (the repository) ──────────────────────────────────────────────


def test_the_whole_call_is_kept_only_while_held_and_only_when_it_matches_the_head(db) -> None:
    from holdspeak.coder_gate import redact_call

    command = "cat > /tmp/x <<'EOF'\n" + "a long body line\n" * 12 + "EOF"
    call = redact_call({"command": command})
    assert call.full and len(call.full) > 120 and call.full.startswith(call.head)
    short = redact_call({"command": "ls"})
    assert short.full == ""

    gate = db.gate
    gate.propose(proposal_id="p1", session_key="codex:s", agent="codex", tool="Bash",
                 args_sha256=call.sha256, args_head=call.head, cwd="/w", ttl_seconds=60)
    assert gate.store_full_call("p1", "something else entirely " * 10) is False
    assert gate.full_call("p1") is None
    assert gate.store_full_call("p1", call.full) is True
    assert gate.full_call("p1") == call.full
    gate.decide("p1", decision="denied", decided_by="owner")
    assert gate.full_call("p1") is None
    assert gate.store_full_call("p1", call.full) is False  # no longer held


def test_a_decision_between_the_held_read_and_the_insert_has_the_last_word(db, monkeypatch) -> None:
    """Astra r1 on #1011 (P2-7), her interleaving: storage reads HELD, the
    decision flips the state and deletes, then storage inserts. The insert
    is conditional on HELD in one statement: no row survives the decision."""
    from holdspeak.coder_gate import redact_call

    call = redact_call({"command": "cat > /tmp/x <<'EOF'\n" + "a long body line\n" * 12 + "EOF"})
    gate = db.gate
    gate.propose(proposal_id="p2", session_key="codex:s", agent="codex", tool="Bash",
                 args_sha256=call.sha256, args_head=call.head, cwd="/w", ttl_seconds=60)
    held = gate.get("p2")
    real_get = gate.get

    def stale_then_decide(proposal_id):
        # The storage's HELD read, then the decision lands before its insert.
        monkeypatch.setattr(gate, "get", real_get)
        gate.decide("p2", decision="denied", decided_by="owner")
        return held

    monkeypatch.setattr(gate, "get", stale_then_decide)
    assert gate.store_full_call("p2", call.full) is False
    assert real_get("p2").state == "denied"
    assert gate.full_call("p2") is None


# ── B66 ───────────────────────────────────────────────────────────────


def test_a_deny_tells_the_agent_the_reason_and_to_stop() -> None:
    from holdspeak.coder_gate import _deny_reason

    said = _deny_reason({"state": "denied", "reason": "OUTSIDE THE WORKTREE · /tmp/pr_body.md"})
    assert said == (
        "denied from the desk: OUTSIDE THE WORKTREE · /tmp/pr_body.md. "
        "The owner denied this call. Do not try it again in a different form."
    )
    assert _deny_reason({"state": "expired"}) == "the hold expired with no decision"


# ── B67 ───────────────────────────────────────────────────────────────


def test_a_queued_rebrief_is_taken_back_with_a_receipt(launched, tmp_path, monkeypatch) -> None:
    _working(launched, tmp_path, monkeypatch)
    before = len(launched.typed)
    queued = _press(launched, tmp_path, "Re-brief: do not write outside the worktree.")
    assert queued["status"] == launch_rebrief.QUEUED
    taken = launch_rebrief.take_back(launched.launch_id, queued["command_id"], OWNER, service=launched.service)
    assert taken["status"] == launch_rebrief.TAKEN_BACK
    record = launched.launches.get(launched.launch_id)
    assert record["queued_rebriefs"] == [] and record.get("queued_rebrief") is None
    [receipt] = record["rebriefs"]
    assert receipt["state"] == launch_rebrief.TAKEN_BACK and receipt["detail"] == "BY YOU"
    assert receipt["text_head"] == "Re-brief: do not write outside the worktree."
    assert receipt["press_id"] == queued["command_id"] and receipt["approved_at"]

    # The turn ends: nothing is typed.
    _idle(launched, tmp_path, monkeypatch)
    assert _flush(launched, tmp_path) == []
    assert _texts(launched, before) == []
    # A second press of Take back changes nothing.
    again = launch_rebrief.take_back(launched.launch_id, queued["command_id"], OWNER, service=launched.service)
    assert again["status"] == "not_queued"


def test_a_sent_rebrief_cannot_be_taken_back(launched, tmp_path, monkeypatch) -> None:
    _working(launched, tmp_path, monkeypatch)
    queued = _press(launched, tmp_path, "Re-brief: one.")
    _idle(launched, tmp_path, monkeypatch)
    assert _flush(launched, tmp_path) == [KEY]
    result = launch_rebrief.take_back(launched.launch_id, queued["command_id"], OWNER, service=launched.service)
    assert result["status"] == "not_queued"
    assert launched.launches.get(launched.launch_id)["rebriefs"][-1]["state"] == launch_rebrief.SENT


# ── B68 ───────────────────────────────────────────────────────────────


def test_the_finished_report_of_shot_49_is_done() -> None:
    assert not asks_a_question(B68_REPORT)
    assert not reports_a_problem(B68_REPORT)
    stop = {"hook_event_name": "Stop", "awaiting_response": True, "question": B68_REPORT}
    assert turn_end(stop, work_done=True) == TURN_DONE


@pytest.mark.parametrize("text, problem", [
    ("The earlier /tmp write attempts were blocked, so nothing landed outside.", False),
    ("The push was denied by the gate; the branch stays local.", False),
    ("The lint check failed on PR #3.", True),
    ("The build is blocked on a missing secret.", True),
    ("Tests failed after the write attempts were blocked.", True),
    # Astra's ruling on #1011: by the desk / gate / owner / from the desk is a
    # decision; blocked by anything else is a problem.
    ("The write was blocked by the desk.", False),
    ("The call was denied from the desk.", False),
    ("The API call was blocked by a firewall.", True),
    ("The push was blocked by branch protection.", True),
    ("The merge attempts were blocked by a failing check.", True),
    ("The deploy was blocked by the hook.", True),
])
def test_a_gate_decision_is_not_a_problem_but_a_failure_is(text: str, problem: bool) -> None:
    assert reports_a_problem(text) is problem


def test_the_report_is_no_needs_row_and_the_lane_says_done(launched, tmp_path, monkeypatch) -> None:
    """The report as the wait's words (Codex's Stop carries its last message
    as the wait; here the real ingestion of a waiting turn end with them)."""
    from holdspeak import agent_context

    _responder(launched, tmp_path, "yolo")
    monkeypatch.setattr(agent_context, "AGENT_CONTEXT_FILE", tmp_path / "agent_sessions.json")
    _hook(launched, tmp_path, "Notification", notification_type="idle_prompt", message=B68_REPORT)
    assert _lane(launched, tmp_path)["wait"]["question"].startswith("Confirmed — already conforming")
    assert _members(launched, tmp_path) == []
    launched.launches.update(launched.launch_id, follow_through={"pr": {
        "number": 4, "url": "https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/4", "state": "open",
    }})
    assert _lane(launched, tmp_path)["wait"]["turn_end"] == TURN_DONE
