"""PHILO-15 15: YOLO means the agent works in its worktree; the desk answers
as the desk (rehearsal 1 part B, bounces B43 B44 B45 B47;
docs/internal/philo/phase-15/rehearsal-1b/BOUNCES-B.md).

B43  The nine held calls of the rehearsal, read again. The hub log of the
     rehearsal is not in the tree (its HOME was removed): each command is
     rebuilt from the head the Needs row showed (shots
     ``5.3-needs-held-1440.png``, ``5.3-held-heredoc-2-1440.png``,
     ``5.3-held-heredoc-3-1440.png``, ``5.3-held-approvable-1440.png``,
     ``5.3-held-applypatch-1440.png``, ``5.3-needs-held-push-393.png``) and
     the files the agent's PR #1 holds. Every write in the worktree passes;
     the ``/tmp`` probe stays held, with its reason.
B44  A DESIGN LIMIT (owner ruling on #998): the hub keeps 120 chars; a long
     held command is CUT and is approved in the pane (Raw); the row says
     CUT · APPROVE IN RAW. A hold's word leaves only when it is in that head.
B45  The lane reads a launch's holds by its launch-bound credential.
B47  The responder answers only a routine question, as the desk, once,
     and never after the agent reported its work done. The six exchanges of
     the rehearsal's last minute produce no answer.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from holdspeak.tool_gate_rules import (
    INSIDE,
    OUTSIDE,
    UNPARSED,
    classification_from_wire,
    classify_bash,
    hold_reason,
)

BRANCH = "hs/action-action_1ff5227ebc101ddbe1d827ba"

CONTRIBUTING = """# Contributing

Pull requests to this repository follow three rules:

1. Branch from `main`.
2. One change per pull request.
3. Every pull request names its test.

To verify the contribution rules are in place, run the test:

```sh
bash tests/contributing_test.sh
```
"""

#: The first heredoc (+1075 CHARS on the Needs row): the long CONTRIBUTING
#: draft with its "Why" paragraphs; the rebuilt body is the same length class.
CONTRIBUTING_LONG = CONTRIBUTING + "\n## Why these rules\n\n" + "\n".join(
    f"- Rule {n}: a reviewer reads one change, its branch from `main`, and the test it names." for n in range(1, 13)
) + "\n"

TEST_SCRIPT_PATCH = """*** Begin Patch
*** Update File: tests/contributing_test.sh
@@
 if [ ! -f "$contributing" ]; then
   echo "FAIL: CONTRIBUTING.md not found" >&2
   exit 1
 fi
+
+content="$(tr "[:upper:]" "[:lower:]" < "$contributing" | tr -d "\\`" | tr -s " \\t" " ")"
*** End Patch"""

ADD_TEST_PATCH = """*** Begin Patch
*** Add File: tests/contributing_test.sh
+#!/usr/bin/env bash
+# Test for action:action_1ff5227ebc101ddbe1d827ba
+set -euo pipefail
+repo_root="$(cd "$(dirname "$0")/.." && pwd)"
+contributing="$repo_root/CONTRIBUTING.md"
*** End Patch"""

#: The nine held calls of rehearsal 1 part B (16:26 to 16:45), in order.
NINE = [
    ("contributing-long", f"cat > CONTRIBUTING.md <<'EOF'\n{CONTRIBUTING_LONG}EOF"),
    ("contributing", f"cat > CONTRIBUTING.md <<'EOF'\n{CONTRIBUTING}EOF"),
    ("probe-tmp", 'echo "test write" > /tmp/hs_write_probe.txt && cat /tmp/hs_write_probe.txt'),
    ("probe", "cat > tests/probe.txt <<'EOF'\nhello\nEOF\necho ok"),
    ("probe2", "cat > tests/probe2.md <<'EOF'\n# probe two\nEOF\necho ok"),
    ("probe3", "cat > tests/probe3.md <<'EOF'\nprobe three\nEOF\nls tests"),
    ("apply-patch-add", f"apply_patch <<'PATCH'\n{ADD_TEST_PATCH}\nPATCH"),
    ("apply-patch-update", f"apply_patch '{TEST_SCRIPT_PATCH}'"),
    ("push", "git push -u origin HEAD"),
]


@pytest.fixture
def worktree(tmp_path: Path) -> Path:
    """The agent's worktree: a git worktree on the launch's branch."""
    root = tmp_path / "wt"
    (root / "tests").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", BRANCH, str(root)], check=True)
    return root.resolve()


@pytest.mark.parametrize("name, command", NINE, ids=[n for n, _ in NINE])
def test_the_nine_rehearsal_holds_are_read_again(worktree: Path, name: str, command: str) -> None:
    verdict = classify_bash(command, cwd=str(worktree), root=str(worktree))
    if name == "probe-tmp":
        # A write outside the worktree still waits, and says why.
        assert (verdict.scope, verdict.rule) == (OUTSIDE, "redirect_outside_worktree")
        assert hold_reason(verdict.scope, verdict.rule, verdict.target) == (
            "OUTSIDE THE WORKTREE · /tmp/hs_write_probe.txt"
        )
        return
    assert verdict.scope == INSIDE, (name, verdict)
    assert hold_reason(verdict.scope, verdict.rule, verdict.target) == ""
    if name == "push":
        # HEAD is read from the worktree: the hub compares it with the launch's branch.
        assert (verdict.rule, verdict.push_branch) == ("git_push_launch_branch", BRANCH)


def test_eight_of_the_nine_pass_and_the_tmp_probe_waits(worktree: Path) -> None:
    scopes = [classify_bash(c, cwd=str(worktree), root=str(worktree)).scope for _, c in NINE]
    assert scopes.count(INSIDE) == 8 and scopes.count(OUTSIDE) == 1


def test_the_heredoc_reading_matches_what_bash_writes(worktree: Path) -> None:
    """The body the reading takes as data is the body bash writes."""
    command = NINE[1][1]
    subprocess.run(["bash", "-c", command], cwd=worktree, check=True)
    assert (worktree / "CONTRIBUTING.md").read_text() == CONTRIBUTING
    assert classify_bash(command, cwd=str(worktree), root=str(worktree)).scope == INSIDE


@pytest.mark.parametrize("command, scope, rule, reason", [
    # A write target outside the worktree.
    ("cat > ../outside.md <<'EOF'\nx\nEOF", OUTSIDE, "redirect_outside_worktree", "OUTSIDE THE WORKTREE · ../outside.md"),
    ("tee /tmp/notes.md <<'EOF'\nx\nEOF", OUTSIDE, "path_outside_worktree", "OUTSIDE THE WORKTREE · /tmp/notes.md"),
    ("cat >> ~/.zshrc <<'EOF'\nx\nEOF", OUTSIDE, "redirect_outside_worktree", "OUTSIDE THE WORKTREE · ~/.zshrc"),
    ("apply_patch '*** Begin Patch\n*** Add File: ../x.txt\n+hi\n*** End Patch'", OUTSIDE, "patch_outside_worktree", "OUTSIDE THE WORKTREE · ../x.txt"),
    ("apply_patch <<'EOF'\n*** Begin Patch\n*** Update File: a.txt\n*** Move to: /etc/a.txt\n*** End Patch\nEOF", OUTSIDE, "patch_outside_worktree", "OUTSIDE THE WORKTREE · /etc/a.txt"),
    # A target the reading cannot resolve.
    ('echo x > "$OUT"', UNPARSED, "shell_expansion", "UNRESOLVED TARGET · $OUT"),
    ("cat > notes.md <<EOF\n$(rm -rf ..)\nEOF", UNPARSED, "heredoc_expansion", "UNRESOLVED TARGET · $(rm"),
    ("cat > notes.md <<'EOF'\nno tag line", UNPARSED, "here_document", "UNRESOLVED TARGET · EOF"),
    ("apply_patch 'not a patch'", UNPARSED, "apply_patch_form", "UNRESOLVED TARGET · not a patch"),
    # Code the reading cannot see.
    ("python3 - <<'EOF'\nimport os\nEOF", UNPARSED, "heredoc_to_interpreter", "RUNS CODE · python3"),
    ("bash <<'EOF'\nrm -rf ..\nEOF", UNPARSED, "heredoc_to_interpreter", "RUNS CODE · bash"),
    # HEAD may be another branch after a switch in the same call.
    ("git switch -c other && git push -u origin HEAD", OUTSIDE, "git_push_unbound", "PUSH TO ANOTHER BRANCH · HEAD"),
])
def test_writes_outside_or_unresolved_are_held_with_the_reason(worktree: Path, command, scope, rule, reason) -> None:
    verdict = classify_bash(command, cwd=str(worktree), root=str(worktree))
    assert (verdict.scope, verdict.rule) == (scope, rule), verdict
    assert hold_reason(verdict.scope, verdict.rule, verdict.target) == reason


def test_a_name_lookup_runs_nothing_and_passes(worktree: Path) -> None:
    """Seen on the lane 15 launch: ``command -v gh`` held as RUNS CODE."""
    assert classify_bash("command -v gh && gh auth status 2>&1", cwd=str(worktree), root=str(worktree)).scope == INSIDE
    assert classify_bash("command rm -rf ..", cwd=str(worktree), root=str(worktree)).rule == "indirect_command"


def test_a_symlink_out_is_held_and_named(worktree: Path, tmp_path: Path) -> None:
    (worktree / "out").symlink_to(tmp_path)
    verdict = classify_bash("cat > out/x.md <<'EOF'\nx\nEOF", cwd=str(worktree), root=str(worktree))
    assert (verdict.scope, verdict.rule) == (OUTSIDE, "symlink_out_of_worktree")
    assert hold_reason(verdict.scope, verdict.rule, verdict.target) == "SYMLINK OUT OF THE WORKTREE · out/x.md"


def test_the_target_crosses_the_wire_and_the_hub_keeps_it() -> None:
    wire = classification_from_wire({
        "scope": "outside", "rule": "redirect_outside_worktree", "target": "/tmp/x",
        "proposal_id": "p", "args_sha256": "s",
    })
    assert wire is not None and wire["target"] == "/tmp/x"
    from holdspeak.kernel.tool_call import _VERDICT_KEYS

    assert "target" in _VERDICT_KEYS


def test_the_hook_and_the_hub_keep_the_same_head() -> None:
    from holdspeak import coder_gate
    from holdspeak.db import gate

    # Owner ruling on #998 (Astra r1): the Phase 14 head stays 120.
    assert coder_gate.ARGS_HEAD_CHARS == gate.ARGS_HEAD_CHARS == 120


# ── B45: the lane reads the launch's holds ───────────────────────────


def test_the_lane_reads_the_holds_of_the_launch_credential(tmp_path: Path) -> None:
    from holdspeak.db.core import Database
    from holdspeak.services.launch_lane import _launch_proposals

    db = Database(tmp_path / "hs.db")
    for n, key in enumerate(("agent:launch:L1", "codex:s1", "agent:launch:L2")):
        db.gate.propose(
            proposal_id=f"p{n}", session_key=key, agent="agent", tool="Bash",
            args_sha256=str(n) * 64, args_head='{"command":"ls"}', cwd="/w", ttl_seconds=60,
        )
    found = [p.id for p in _launch_proposals(db, "codex:s1", "L1")]
    assert found == ["p0", "p1"]  # its own credential and its session, never L2's


# ── B47: the desk answers as the desk ────────────────────────────────

from holdspeak.services import agent_responder as ar  # noqa: E402

#: The last minute of the rehearsal (16:45 to 16:46; codex-pane.txt and
#: BOUNCES-B B47): what the agent wrote, and what the responder typed back
#: in the owner's voice. The agent's first and last messages are not in the
#: pane capture (it holds the last screen only); they are rebuilt from the
#: answers the responder gave to them.
SIX = [
    ("PR #1 is open: https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/1. "
     "tests/contributing_test.sh passes.",
     "Confirmed — PR #1 is open and the test passes, so the item meets its acceptance criteria. "
     "I'll mark action:action_1ff5227ebc101ddbe1d827ba as done on the desk. You're clear."),
    ("Thanks for confirming. The work is done.", "All good, thanks. You're clear."),
    ("Great, thanks!", "You're welcome — take care!"),
    ("You're welcome — take care!", "You're welcome! Glad I could help. 🚪"),
    ("Thanks! Safe travels. 🚪", "Goodbye! 👋"),
    ("Hello! What would you like me to work on?",
     "Hi! Go ahead and create the CONTRIBUTING.md in the rehearsal repository with the three rules ..."),
]


BRIEF = (
    "Add CONTRIBUTING.md.\n"
    "- Run bash tests/contributing_test.sh before you open the pull request.\n"
    "- Commit your work, push the branch, and open a pull request."
)
REAL_REPLY = '{"verdict": "real", "reason": "a change of scope", "answer": ""}'


class _Session:
    def __init__(self, question: str, wait_id: str) -> None:
        self.agent = "codex"
        self.session_id = "s1"
        self.question = question
        self.wait_id = wait_id
        self.state = "awaiting_response"
        self.wait_kind = "answer"

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


class _Rig:
    """A responder with its seams as plain doubles: the model, the pane, the
    store, the registry. The decision code under test is the real one."""

    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, replies: list[str]) -> None:
        self.session: _Session | None = None
        self.prompts: list[str] = []
        self.typed: list[str] = []
        self.receipts: list[dict[str, Any]] = []
        replies = list(replies)
        monkeypatch.setattr("holdspeak.agent_context.models.is_blocked", lambda s: True)
        monkeypatch.setattr("holdspeak.agent_context.models.wait_kind", lambda s: "answer")

        def drafter(**kw: Any) -> str:
            self.prompts.append(kw["question"])
            return replies.pop(0)

        rig = self

        class _Steering:
            def record(self, **kw: Any) -> int:
                rig.receipts.append(kw)
                return len(rig.receipts)

        class _Db:
            steering = _Steering()

        self.responder = ar.AgentResponder(
            _Db(), control_mode=lambda: "yolo", drafter=drafter,
            store=ar.AnswerStore(tmp_path / "answers.json"),
            sessions=lambda: [self.session] if self.session else [],
        )
        self.responder._launch_for = lambda key: {"launch_id": "L1", "brief_text": BRIEF}

        def deliver(launch: Any, key: str, agent: str, text: str) -> dict[str, Any]:
            self.typed.append(text)
            return {"receipt": {"outcome": "delivered"}, "operation_id": f"op{len(self.typed)}"}

        self.responder._deliver = deliver

    def ask(self, text: str, n: int) -> dict[str, Any]:
        self.session = _Session(text, f"w{n}")
        self.responder.triage(["codex:s1"])  # the watcher's call: the wait's record
        return self.responder.decide("codex:s1")

    def shown(self) -> bool:
        """The wait is a Needs you row (membership's own read)."""
        from holdspeak.services.needs_you_membership import coder_items

        from datetime import datetime, timezone

        session = {**self.session.to_dict(), "awaiting_response": True,
                   "updated_at": datetime.now(timezone.utc).isoformat()}
        return bool(coder_items(ar.annotate_sessions([session], store=self.responder._store)))


def test_the_six_rehearsal_exchanges_get_no_answer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rig = _Rig(tmp_path, monkeypatch, [answer for _, answer in SIX])
    results = [rig.ask(agent, n) for n, (agent, _) in enumerate(SIX)]
    assert rig.typed == [], "the desk typed nothing into the agent"
    assert rig.prompts == [], "no model was asked: none of the six is a routine question"
    assert all(r.get("silent") for r in results)
    reasons = [r["draft"]["reason"] for r in results]
    assert reasons[0].startswith("the agent reports its work done")
    # After the report, nothing is answered again (the sixth is a question).
    assert ar.message_kind(SIX[5][0]) == "question"
    assert reasons[5].startswith("the agent reported its work done")
    # Each one is a receipt on the session (the lane's answers), as the desk's.
    assert len(rig.receipts) == 6 and {r["outcome"] for r in rig.receipts} == {"answer_drafted"}
    # Coordinator ruling (the A5 law): a done report is not a Needs you row.
    # The first five end DONE (hidden, nobody notified); the sixth asks a
    # question after the report: it goes to the owner, unanswered.
    assert [r["outcome"] for r in results] == [ar.DONE_TURN] * 5 + [ar.ESCALATED]
    assert rig.shown() is True


def test_a_real_question_after_done_goes_to_the_owner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rig = _Rig(tmp_path, monkeypatch, [])
    assert rig.ask("PR #3 is open and the test passes.", 1)["outcome"] == ar.DONE_TURN
    asked = rig.ask("CI failed on the lint step. Shall I fix it on this branch?", 2)
    assert asked["outcome"] == ar.ESCALATED and rig.typed == [] and rig.prompts == []
    assert rig.shown() is True  # the owner sees a real question


def test_a_statement_with_no_question_is_idle_not_the_owners(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rig = _Rig(tmp_path, monkeypatch, [])
    assert rig.ask("I created CONTRIBUTING.md.", 1)["outcome"] == ar.IDLE_TURN
    assert rig.typed == [] and rig.prompts == []


def test_the_lane_says_done_with_the_agents_last_words(tmp_path: Path) -> None:
    from holdspeak.services.launch_lane import _wait

    store = ar.AnswerStore(tmp_path / "answers.json")
    session = {"agent": "codex", "session_id": "s1", "state": "awaiting_response", "awaiting_response": True,
               "question": "PR #3 is open; both tests pass.", "wait_id": "w1", "wait_started_at": "2026-10-07T23:30:17Z",
               "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}
    store.put_wait("codex:s1", {"wait_id": "w1", "state": ar.DONE_TURN, "launch_id": "L1", "at": 1.0})
    wait = _wait(session, store)
    assert wait is not None and wait["kind"] == "DONE" and wait["turn_end"] == "done"
    assert wait["question"] == "PR #3 is open; both tests pass."
    from holdspeak.services.needs_you_membership import coder_items

    assert coder_items(ar.annotate_sessions([session], store=store)) == []
    # The same wait as the owner's (escalated) IS a row: the DONE state hides it.
    store.put_wait("codex:s1", {"wait_id": "w1", "state": ar.ESCALATED, "launch_id": "L1", "at": 1.0})
    assert len(coder_items(ar.annotate_sessions([session], store=store))) == 1


def test_a_routine_question_is_answered_once_as_the_desk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reply = ('{"verdict": "routine", "reason": "the brief names the test", "answer": '
             '"Yes. The brief says: \\"Run bash tests/contributing_test.sh before you open the pull request.\\""}')
    rig = _Rig(tmp_path, monkeypatch, [reply, reply])
    question = "Shall I run bash tests/contributing_test.sh before I open the pull request?"
    first = rig.ask(question, 1)
    assert first["outcome"] == ar.ANSWERED
    assert rig.typed == ['The desk: Yes. The brief says: "Run bash tests/contributing_test.sh before you open the pull request."']
    assert [r["outcome"] for r in rig.receipts] == ["auto_answered"]
    # The same question again: no second answer (at most one per question).
    again = rig.ask(question, 2)
    assert again["outcome"] == ar.ESCALATED and len(rig.typed) == 1
    assert again["draft"]["reason"] == "the desk answered this question before"


@pytest.mark.parametrize("answer", [
    "You're welcome! Glad I could help.",
    "I'll mark the item done on the desk.",
    "Hi! Go ahead and create the CONTRIBUTING.md again.",
    "Goodbye! 👋",
])
def test_an_answer_in_a_person_voice_is_never_typed(answer: str) -> None:
    draft = ar.guard("Shall I proceed?", ar.Draft(ar.ROUTINE, "r", answer))
    assert draft.verdict == ar.REAL and "as a person" in draft.reason


def test_the_prompt_says_the_ruling() -> None:
    system, user = ar.answer_prompt("brief", "screen", "Shall I proceed?")
    for words in (
        "You are NOT the owner", "Answer ONLY a routine QUESTION", "never answered",
        "Never give the agent new work", "never tell it to do work again", "Never thank",
    ):
        assert words in system, words
    assert "as the desk, never as the owner" in user


def test_the_desk_voice_is_said_once() -> None:
    assert ar.desk_voice("The desk: yes.") == "The desk: yes."
    assert ar.desk_voice("yes.") == "The desk: yes."
    assert ar.desk_voice("") == ""


@pytest.mark.parametrize("text, kind", [
    ("Shall I run the tests?", "question"),
    ("I made the file.\nShould I also add a test?", "question"),
    ("I created CONTRIBUTING.md.", "statement"),
    ("Goodbye! 👋", "chitchat"),
    ("PR #4 is open and the checks pass.", "done"),
    # Astra r1 on #998: a question first, whatever else the message holds.
    ("I opened the pull request. Anything else?", "question"),
    ("Should I mark this task as done once PR #3 is merged?", "question"),
    ("Hello! What would you like me to work on?", "question"),
    ("Hi. Should I push the branch now", "question"),
    ("PR #3 is open but the lint check failed.", "problem"),
])
def test_the_message_kinds(text: str, kind: str) -> None:
    assert ar.message_kind(text) == kind


def test_conductor_doc_names_the_ruling() -> None:
    text = (Path(__file__).resolve().parents[2] / "docs/internal/CONDUCTOR.md").read_text(encoding="utf-8")
    assert "The desk: " in text and "UNRESOLVED TARGET" in text


@pytest.mark.parametrize("message, outcome, shown", [
    # A conditional completion is a question: the model drafts, REAL, the owner sees it.
    ("Should I mark this task as done once PR #3 is merged?", ar.ESCALATED, True),
    # A greeting does not swallow the question after it.
    ("Hi! Should I squash the two commits before the review?", ar.ESCALATED, True),
    # A failed check beside an open PR is the owner's, never DONE.
    ("PR #3 is open, but the lint check failed on tests/notes_test.sh.", ar.ESCALATED, True),
    # A completion report with no question: DONE, not a Needs you row.
    ("PR #3 is open; both tests pass.", ar.DONE_TURN, False),
])
def test_stop_to_responder_to_needs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, message, outcome, shown) -> None:
    rig = _Rig(tmp_path, monkeypatch, [REAL_REPLY])
    assert rig.ask(message, 1)["outcome"] == outcome
    assert rig.typed == [] and rig.shown() is shown
    # Only a question reached the model; nothing was marked done but a report.
    assert bool(rig.responder._store.read()["done"]) is (outcome == ar.DONE_TURN)


@pytest.mark.parametrize("answer, reason", [
    ("Yes. Run the tests, then open the pull request.", "the answer gives the agent work"),
    ("Yes, go ahead and add a CHANGELOG too.", "the answer gives the agent work"),
    ("Yes. The tests come first.", "the answer quotes no line of the brief"),
    ('Yes. "The staging box comes first."', "the answer quotes no line of the brief"),
])
def test_a_routine_answer_cites_the_brief_and_gives_no_work(answer: str, reason: str) -> None:
    draft = ar.guard("Shall I run the tests first?", ar.Draft(ar.ROUTINE, "r", answer), BRIEF)
    assert (draft.verdict, draft.reason) == (ar.REAL, reason)
    ok = ar.guard("Shall I run the tests first?", ar.Draft(
        ar.ROUTINE, "r", 'Yes. The brief says: "Run bash tests/contributing_test.sh before you open the pull request."'), BRIEF)
    assert ok.verdict == ar.ROUTINE


# ── Astra r1 on #998: pipelines, folders, targets ────────────────────

@pytest.mark.parametrize("command, rule, reason", [
    ("tee local.py <<'EOF' | python3\nopen('../outside-pipe', 'w').write('review')\nEOF",
     "pipe_to_interpreter", "RUNS CODE · python3"),
    ("cat notes.md | node", "pipe_to_interpreter", "RUNS CODE · node"),
    ("cat notes.md | env python3", "pipe_to_interpreter", "RUNS CODE · env"),
    ("cd missing || cat > ../outside <<'EOF'\nx\nEOF", "cd_unresolved", "FOLDER NOT RESOLVED · missing"),
    ("cd tests | ls", "cd_in_pipeline", "FOLDER NOT RESOLVED · tests"),
])
def test_pipelines_and_unresolved_folders_are_held(worktree: Path, command: str, rule: str, reason: str) -> None:
    verdict = classify_bash(command, cwd=str(worktree), root=str(worktree))
    assert (verdict.scope, verdict.rule) == (UNPARSED, rule), verdict
    assert hold_reason(verdict.scope, verdict.rule, verdict.target) == reason


def test_in_worktree_heredocs_still_pass_after_a_real_cd(worktree: Path) -> None:
    command = "cd tests && cat > probe.txt <<'EOF'\nhello\nEOF\napply_patch <<'P'\n*** Begin Patch\n*** Add File: a.txt\n+x\n*** End Patch\nP"
    assert classify_bash(command, cwd=str(worktree), root=str(worktree)).scope == INSIDE


SECRET = "ExampleCredential-k3y9Q"  # an unknown shape: redaction does not know it


def _hook_body(command: str, worktree: Path) -> dict[str, Any]:
    """One real PreToolUse arrival through ``run_hook``; the body it posts."""
    from holdspeak.coder_gate import GateConfig, run_hook

    posted: list[dict[str, Any]] = []

    def post(url: str, body: dict, timeout: float):
        posted.append(body)
        return 200, {"state": "approved"}

    run_hook(
        {"session_id": "s", "tool_name": "Bash", "tool_use_id": "t1", "tool_input": {"command": command},
         "cwd": str(worktree)},
        config=GateConfig(armed=True, repos={str(worktree): ["Bash"]}, armed_paths=[str(worktree)]),
        http_post=post, http_get=lambda url, timeout: (200, {"state": "approved"}), agent_credential="x",
    )
    return posted[-1]


@pytest.mark.parametrize("command", [
    # The word that decides is past the 120-char head.
    "echo " + "pad " * 40 + f"> /tmp/{SECRET}.txt",
    # An expanding heredoc: the literal in front of ``$`` never leaves.
    f"cat > notes.md <<EOF\nsk-{SECRET}$SUFFIX\nEOF",
])
def test_a_secret_never_rides_the_target(worktree: Path, command: str) -> None:
    body = _hook_body(command, worktree)
    verdict = body["classification"]
    assert SECRET not in json.dumps(verdict), "the verdict never carries it"
    assert SECRET not in hold_reason(verdict["scope"], verdict["rule"], verdict["target"])
