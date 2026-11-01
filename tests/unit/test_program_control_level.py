"""Programs PG13: a Program's own control level drives the desk's routine
answers and the tool gate for its steps' agents (design §6, the rows "a
routine agent question" and "an approval the gate can allow by its own
rules").

The resolver (``services/control_level.level_for_launch``) answers the
Program's control for a step's launch, else the desk's Control mode. The
responder and the gate run over the K5 rig (a real launch in a real git
worktree, the real kernel ``tool.call`` codec, the real hook ingestion; tmux
and the agent faked at the process edge), with the launch bound to a
Program step at a level the desk does not have. The Programs rig shows a
step's routine question waiting at Secure.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.db.gate import APPROVED, DENIED, HELD
from holdspeak.services.agent_responder import ANSWERED, ESCALATED, AgentResponder, AnswerStore
from holdspeak.services.control_level import level_for_launch, mode_for_launch, step_of_launch
from holdspeak.services.program_service import ProgramService
from tests.unit.test_agent_hand import OWNER, db  # noqa: F401  (db is a fixture)
from tests.unit.test_conductor_k5_supervision import (  # noqa: F401  (launched is a fixture)
    KEY,
    ROUTINE_ANSWER,
    ROUTINE_REPLY,
    _ask,
    _call,
    _members,
    _mode,
    _model,
    _responder,
    launched,
)


def _repo(root: Path) -> Path:
    repo = root / "app"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    return repo


def _bind(database: Any, repository: Path, launch_id: str, control: str) -> tuple[ProgramService, str]:
    """A Program at ``control`` whose one step runs ``launch_id``."""
    service = ProgramService(database, kernel=lambda **_kw: None)
    pid = service.create(OWNER, title="The hub stops stalling", repository=str(repository), control=control)["id"]
    service.plan(OWNER, pid, steps=[{"title": "Indexes", "brief": "Add the three indexes."}])
    [step] = service.store.list_steps(pid)
    step.update(launch_id=launch_id, state="working")
    service.store.save_step(step)
    return service, pid


def _decided(service: ProgramService, pid: str) -> list[dict[str, Any]]:
    return service.get(OWNER, pid)["decided_for_you"]


# ── the resolver ─────────────────────────────────────────────────────


@pytest.mark.parametrize("control, desk, level, word", [
    ("secure", "yolo", "secure", "safe"),
    ("normal", "safe", "normal", "neutral"),
    ("yolo", "neutral", "yolo", "yolo"),
])
def test_a_step_launch_follows_its_program(tmp_path, control, desk, level, word) -> None:
    database = Database(tmp_path / "hub.db")
    _bind(database, _repo(tmp_path), "launch_step", control)
    assert level_for_launch("launch_step", db=database, desk=lambda: desk) == level
    assert mode_for_launch("launch_step", db=database, desk=lambda: desk) == word
    program, step = step_of_launch("launch_step", db=database)
    assert program["control"] == control and step["launch_id"] == "launch_step"


@pytest.mark.parametrize("desk, level", [("safe", "secure"), ("neutral", "normal"), ("yolo", "yolo")])
def test_a_plain_launch_follows_the_desk(tmp_path, desk, level) -> None:
    database = Database(tmp_path / "hub.db")
    _bind(database, _repo(tmp_path), "launch_step", "secure")
    for launch_id in ("launch_plain", "", None):
        assert level_for_launch(launch_id, db=database, desk=lambda: desk) == level
        assert mode_for_launch(launch_id, db=database, desk=lambda: desk) == desk
    assert step_of_launch("launch_plain", db=database) is None


def test_a_database_with_no_programs_store_is_the_desk() -> None:
    class _NoStore:
        pass

    assert level_for_launch("launch_x", db=_NoStore(), desk=lambda: "safe") == "secure"


# ── the responder ────────────────────────────────────────────────────


def test_program_secure_on_a_yolo_desk_waits_in_needs_you(launched, tmp_path, monkeypatch) -> None:
    engine = _model(launched, tmp_path, monkeypatch, ROUTINE_REPLY)
    service, pid = _bind(launched.db, launched.worktree, launched.launch_id, "secure")
    _ask(launched, tmp_path, monkeypatch, "Shall I run the tests before I open the pull request?")
    responder = _responder(launched, tmp_path, "yolo")
    typed_before = len(launched.typed)

    assert responder.triage([KEY]) == {"notify": [KEY], "decide": []}
    [row] = _members(launched, tmp_path)  # in Needs you at once
    assert "draft" not in row
    assert engine.prompts == [] and launched.typed[typed_before:] == []
    assert _decided(service, pid) == []


def test_program_yolo_on_a_normal_desk_types_the_routine_draft(launched, tmp_path, monkeypatch) -> None:
    _model(launched, tmp_path, monkeypatch, ROUTINE_REPLY)
    service, pid = _bind(launched.db, launched.worktree, launched.launch_id, "yolo")
    _ask(launched, tmp_path, monkeypatch, "Shall I run the tests before I open the pull request?")
    responder = _responder(launched, tmp_path, "neutral")
    typed_before = len(launched.typed)

    assert responder.triage([KEY]) == {"notify": [], "decide": [KEY]}
    assert _members(launched, tmp_path) == []  # held back while deciding
    result = responder.decide(KEY)
    assert result["outcome"] == ANSWERED, result
    assert [text for _pane, text in launched.typed[typed_before:]] == ["The desk: " + ROUTINE_ANSWER]
    assert _members(launched, tmp_path) == [] and launched.notified == []
    [line] = _decided(service, pid)
    assert line["kind"] == "agent_question" and line["choice"] == "type_draft"
    assert line["line"] == ("Answered for you: The desk: " + ROUTINE_ANSWER)[:200]
    assert line["rule"] == "YOLO: the desk's ROUTINE draft is typed (AgentResponder)"
    assert line["step_id"] == service.store.list_steps(pid)[0]["id"]


def test_program_normal_types_the_routine_draft_by_the_table(launched, tmp_path, monkeypatch) -> None:
    """Design §6: at Normal a step's routine question gets the desk's draft
    typed (the desk's own Normal only stores the draft)."""
    _model(launched, tmp_path, monkeypatch, ROUTINE_REPLY)
    service, pid = _bind(launched.db, launched.worktree, launched.launch_id, "normal")
    _ask(launched, tmp_path, monkeypatch, "Shall I run the tests before I open the pull request?")
    responder = _responder(launched, tmp_path, "safe")
    assert responder.triage([KEY]) == {"notify": [], "decide": [KEY]}
    assert responder.decide(KEY)["outcome"] == ANSWERED
    [line] = _decided(service, pid)
    assert line["rule"] == "Normal: the desk's ROUTINE draft is typed (AgentResponder)"


def test_a_plain_launch_keeps_the_desks_mode(launched, tmp_path, monkeypatch) -> None:
    """No Program: a Normal desk stores the draft and types nothing."""
    _model(launched, tmp_path, monkeypatch, ROUTINE_REPLY)
    _ask(launched, tmp_path, monkeypatch, "Shall I run the tests before I open the pull request?")
    responder = _responder(launched, tmp_path, "neutral")
    typed_before = len(launched.typed)
    assert responder.triage([KEY]) == {"notify": [KEY], "decide": [KEY]}
    assert responder.decide(KEY)["outcome"] == "drafted"
    assert launched.typed[typed_before:] == []


# ── the gate ─────────────────────────────────────────────────────────


def test_program_secure_on_a_yolo_desk_holds_the_call(launched, tmp_path, monkeypatch) -> None:
    _mode(tmp_path, monkeypatch, "yolo")
    service, pid = _bind(launched.db, launched.worktree, launched.launch_id, "secure")
    call = _call(launched, "pytest -q")
    assert call.decision.deny is not None
    assert call.proposal.state == HELD and call.proposal.decided_by is None
    assert call.proposal.policy_snapshot["mode"] == "safe"
    assert call.proposal.policy_snapshot["reason_code"] == "secure_holds_every_call"
    assert _decided(service, pid) == []


def test_program_yolo_on_a_normal_desk_allows_what_yolo_allows(launched, tmp_path, monkeypatch) -> None:
    _mode(tmp_path, monkeypatch, "neutral")
    service, pid = _bind(launched.db, launched.worktree, launched.launch_id, "yolo")
    call = _call(launched, "rm -rf build && git add -A && git commit -m 'fix'")
    assert call.decision.deny is None
    assert call.proposal.state == APPROVED and call.proposal.decided_by == "control-mode"
    assert call.proposal.policy_snapshot["mode"] == "yolo"
    assert call.proposal.policy_snapshot["reason_code"] == "yolo_inside_own_worktree"
    # Outside its worktree it is refused by rule (never held for him).
    outside = _call(launched, "cat /etc/passwd").proposal
    assert outside.state == DENIED and outside.decided_by == "control-mode"
    assert outside.policy_snapshot["reason_code"] == "yolo_program_outside"
    refused, line = _decided(service, pid)
    assert refused["line"] == "Refused by rule (YOLO): cat"
    assert line["kind"] == "gate_approval" and line["line"] == "Allowed: Bash"
    assert line["rule"] == "YOLO: the gate allows a read, a build or a test by its own rules"
    # A second allowed call of the same tool under the same rule: one line.
    assert _call(launched, "pytest -q").proposal.state == APPROVED
    assert len(_decided(service, pid)) == 2
    assert "Allowed: Bash" in launched.db.notes.get(f"program-{pid}").body_markdown


def test_program_yolo_allows_an_unparsed_call_in_its_worktree_by_rule(launched, tmp_path, monkeypatch) -> None:
    """program-ed167ae4478b step 2 (2026-10-31): ``env | grep …`` read
    ``unparsed`` and waited until it expired. At YOLO a step's unparsed call
    in its own worktree goes on by rule; a destructive word is refused."""
    _mode(tmp_path, monkeypatch, "neutral")
    service, pid = _bind(launched.db, launched.worktree, launched.launch_id, "yolo")
    call = _call(launched, "env | grep -i holdspeak | sed 's/x/y/'; ls -la")
    assert call.decision.deny is None
    assert call.proposal.state == APPROVED and call.proposal.decided_by == "control-mode"
    assert call.proposal.policy_snapshot["reason_code"] == "yolo_program_unparsed_inside"
    for command, word in (("sudo $(echo ls)", "sudo"), ("echo $(rm -rf ../x)", "rm -r/-f")):
        refused = _call(launched, command)
        assert refused.decision.deny is not None
        assert refused.proposal.state == DENIED and refused.proposal.decided_by == "control-mode"
        assert refused.proposal.policy_snapshot["reason_code"] == "yolo_program_destructive"
        assert word in str(refused.proposal.reason)
    lines = {row["line"]: row["rule"] for row in _decided(service, pid)}
    assert lines == {
        "Allowed by rule (YOLO): env": "YOLO: a call in the step's own worktree goes on by rule",
        "Refused by rule (YOLO): sudo": "YOLO: a call outside the step's worktree, or a destructive one, is refused by rule",
        "Refused by rule (YOLO): rm -r/-f": "YOLO: a call outside the step's worktree, or a destructive one, is refused by rule",
    }
    assert service.get(OWNER, pid)["your_turn_items"] == []


@pytest.mark.parametrize("control", ["normal", "secure"])
def test_program_normal_and_secure_still_hold_an_unparsed_call(launched, tmp_path, monkeypatch, control) -> None:
    _mode(tmp_path, monkeypatch, "yolo")
    _bind(launched.db, launched.worktree, launched.launch_id, control)
    assert _call(launched, "env | grep -i holdspeak").proposal.state == HELD


def test_a_plain_launch_at_desk_yolo_still_holds_an_unparsed_call(launched, tmp_path, monkeypatch) -> None:
    _mode(tmp_path, monkeypatch, "yolo")
    call = _call(launched, "env | grep -i holdspeak")
    assert call.proposal.state == HELD
    assert call.proposal.policy_snapshot["reason_code"] == "yolo_unparsed_command"


def test_a_plain_launch_keeps_the_desks_gate(launched, tmp_path, monkeypatch) -> None:
    _mode(tmp_path, monkeypatch, "neutral")
    call = _call(launched, "rm -rf build")
    assert call.proposal.state == HELD
    assert call.proposal.policy_snapshot["reason_code"] == "normal_holds_this_call"


# ── the Programs rig: a three-step Program at Secure ─────────────────


class _Session:
    def __init__(self, question: str) -> None:
        self.agent = "claude"
        self.session_id = "step-1"
        self.question = question
        self.wait_id = "w1"
        self.state = "awaiting_response"
        self.wait_kind = "answer"

    def to_dict(self) -> dict[str, Any]:
        return dict(vars(self))


def test_the_rigs_secure_program_shows_its_steps_routine_question_waiting(tmp_path, monkeypatch) -> None:
    from tests.integration.program_rig import Rig
    from tests.integration.test_program_run import _plan_three, _program

    monkeypatch.setattr("holdspeak.agent_context.models.is_blocked", lambda s: True)
    monkeypatch.setattr("holdspeak.agent_context.models.wait_kind", lambda s: "answer")
    rig = Rig(tmp_path)
    pid = _program(rig, reviewer_profile="codex-default", control="secure")
    _plan_three(rig, pid)
    rig.service.start(OWNER, pid)
    one = rig.step(pid, 1)
    session = _Session("Shall I run the tests before I open the pull request?")
    drafts: list[str] = []
    responder = AgentResponder(
        rig.db, control_mode=lambda: "yolo", store=AnswerStore(tmp_path / "answers.json"),
        drafter=lambda **kw: drafts.append(kw["question"]) or ROUTINE_REPLY,
        sessions=lambda: [session],
    )
    responder._launch_for = lambda key: {**rig.ledger.get(one["launch_id"]), "brief_text": "Run the tests."}
    key = "claude:step-1"
    assert responder.triage([key]) == {"notify": [key], "decide": []}
    assert responder.decide(key)["outcome"] == ESCALATED
    assert drafts == []  # Secure drafts nothing: the question is his
    assert rig.service.get(OWNER, pid)["decided_for_you"] == []


# ── PG13b: the launch flags follow the Program's level ───────────────


def _step_launch(
    tmp_path, database, monkeypatch, *, agent: str, desk: str, control: str = "", helper: bool = False,
    review: Any = None,
):
    """Hand a Program step at ``control`` (or the plain item ``action:ai_1``
    when ``control`` is empty) on a desk at ``desk``; the agent's argv as
    tmux receives it. ``helper``: then a helper of that launch, by the
    agent's own Start helper (``agent_helpers.start_helper``)."""
    import shlex

    from tests.unit._spawn_env import command_of
    from tests.unit.test_agent_hand import _rig

    rig = _rig(tmp_path, database, monkeypatch, agent=agent)
    rig.service._control_mode = lambda: desk
    rig.service._db = database
    rig.hand._control_mode = lambda: desk
    profile = f"{agent}-default"
    if control:
        service = ProgramService(database, kernel=lambda **_kw: None)
        pid = service.create(OWNER, title="The hub stops stalling", repository=str(rig.repo), control=control)["id"]
        service.plan(OWNER, pid, steps=[{"title": "Indexes", "brief": "Add the three indexes."}])
        [step] = service.store.list_steps(pid)
        kind, item_id = "program_step", step["id"]
    else:
        kind, item_id = "action", "ai_1"
    result = rig.hand.hand(OWNER, kind, item_id, profile=profile)
    assert result["status"] == "launched", result
    if control:
        step.update(launch_id=result["launch_id"], state="working")
        service.store.save_step(step)
    if helper:
        from holdspeak.services.agent_helpers import start_helper

        before = len([c for c in rig.tmux.calls if c[1] == "new-session"])
        answer = start_helper(
            result["launch_id"], instruction="Read the diff.", profile=profile,
            hand_service=rig.hand, control_mode=lambda: desk, ledger=rig.launches, review=review,
        )
        spawns = [c for c in rig.tmux.calls if c[1] == "new-session"]
        rig.tmux.ended = True
        if answer.get("status") == "awaiting_owner":
            assert len(spawns) == before
            return rig, result, answer, None
        result = answer
        spawn = spawns[-1]
    else:
        spawn = next(c for c in rig.tmux.calls if c[1] == "new-session")
        rig.tmux.ended = True
    command = command_of(spawn)
    return rig, result, None, shlex.split(command.split(" exec ", 1)[1])


def _codex_mode_flags(argv: list[str]) -> list[str]:
    at = argv.index("--ask-for-approval")
    return argv[at:at + 2] + (argv[argv.index("--sandbox"):argv.index("--sandbox") + 2] if "--sandbox" in argv else [])


@pytest.mark.parametrize("control, desk, edits", [
    ("secure", "yolo", False), ("normal", "safe", True), ("yolo", "neutral", True),
])
def test_a_step_launch_of_claude_code_takes_its_programs_level(tmp_path, db, monkeypatch, control, desk, edits) -> None:  # noqa: F811
    from holdspeak.delivery.agent_mcp import CLAUDE_ALLOW_RULE

    rig, result, _, argv = _step_launch(tmp_path, db, monkeypatch, agent="claude", desk=desk, control=control)
    assert ("acceptEdits" in argv) is edits
    assert (CLAUDE_ALLOW_RULE in argv) is edits  # the holdspeak tools: pre-approved at Normal and YOLO only
    record = rig.launches.get(result["launch_id"])
    assert record["control_mode"] == {"secure": "safe", "normal": "neutral", "yolo": "yolo"}[control]
    assert result["control_mode"] == record["control_mode"]


@pytest.mark.parametrize("control, desk, flags", [
    ("secure", "yolo", ["--ask-for-approval", "on-request"]),
    ("normal", "yolo", ["--ask-for-approval", "on-request"]),
    ("yolo", "neutral", ["--ask-for-approval", "never", "--sandbox", "workspace-write"]),
])
def test_a_step_launch_of_codex_takes_its_programs_level(tmp_path, db, monkeypatch, control, desk, flags) -> None:  # noqa: F811
    rig, result, _, argv = _step_launch(tmp_path, db, monkeypatch, agent="codex", desk=desk, control=control)
    assert _codex_mode_flags(argv) == flags
    if control == "yolo":
        # YOLO writes inside its own worktree and that worktree's git folder only.
        worktree = rig.launches.get(result["launch_id"])
        dirs = [argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"]
        assert dirs and all(os.path.realpath(rig.repo / ".git") in d for d in dirs), (dirs, worktree)
        assert "-c" in argv and "sandbox_workspace_write.network_access=true" in argv
    else:
        assert "--sandbox" not in argv and "--add-dir" not in argv


@pytest.mark.parametrize("agent, desk, word", [
    ("claude", "safe", None), ("claude", "yolo", "acceptEdits"),
    ("codex", "safe", "on-request"), ("codex", "yolo", "never"),
])
def test_a_plain_launch_keeps_the_desks_flags(tmp_path, db, monkeypatch, agent, desk, word) -> None:  # noqa: F811
    rig, result, _, argv = _step_launch(tmp_path, db, monkeypatch, agent=agent, desk=desk)
    if agent == "claude":
        assert ("acceptEdits" in argv) is (word is not None)
    else:
        assert _codex_mode_flags(argv)[1] == word
    assert rig.launches.get(result["launch_id"])["control_mode"] == desk


def test_a_helper_of_a_yolo_step_on_a_secure_desk_starts_at_yolo(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    rig, helper, pending, argv = _step_launch(
        tmp_path, db, monkeypatch, agent="codex", desk="safe", control="yolo", helper=True,
    )
    assert pending is None, pending  # the desk's Secure would wait for his press
    assert _codex_mode_flags(argv) == ["--ask-for-approval", "never", "--sandbox", "workspace-write"]
    assert rig.launches.get(helper["launch_id"])["control_mode"] == "yolo"


def test_a_helper_of_a_secure_step_on_a_yolo_desk_waits_for_him(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    _rig_, _parent, pending, argv = _step_launch(
        tmp_path, db, monkeypatch, agent="claude", desk="yolo", control="secure", helper=True,
    )
    assert argv is None and pending["status"] == "awaiting_owner"


def test_a_reviewer_helper_inherits_the_steps_level_after_his_press(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    """A Secure step on a YOLO desk: the reviewer helper waits for his press
    (the desk's YOLO would start it at once), and then it runs at Secure,
    read-only (Claude Code's plan mode, the holdspeak tools not pre-approved)."""
    from holdspeak.services.agent_helpers import allow_helper

    review = {"role": "reviewer", "requested": "claude", "round": 1, "read_only": True}
    rig, parent, pending, _argv = _step_launch(
        tmp_path, db, monkeypatch, agent="claude", desk="yolo", control="secure", helper=True, review=review,
    )
    rig.tmux.ended = False
    answer = allow_helper(
        parent["launch_id"], request_id=pending["owner_action"]["request_id"], principal=OWNER,
        hand_service=rig.hand, ledger=rig.launches,
    )
    assert answer["status"] == "launched", answer
    record = rig.launches.get(answer["launch_id"])
    assert record["control_mode"] == "safe" and record["role"] == "reviewer" and record["read_only"] is True
    assert record["mcp"]["pre_approved"] is False


# ── PG13b: the words ─────────────────────────────────────────────────


def test_a_level_is_printed_secure_normal_yolo() -> None:
    from holdspeak.services.program_rules import decide, level_word

    assert [level_word(word) for word in ("secure", "normal", "yolo", "safe", "neutral", "", None)] == [
        "Secure", "Normal", "YOLO", "Secure", "Normal", "Normal", "Normal",
    ]
    assert decide("yolo", "merge", {"check_green": True}).rule == "YOLO merges on a green check and a passed review"
    assert decide("yolo", "agent_question", {"routine": True}).rule.startswith("YOLO: ")
    for control, word in (("secure", "Secure"), ("normal", "Normal"), ("yolo", "YOLO")):
        assert decide(control, "step_failed", {}).rule.startswith(f"{word}: ")


def test_the_programs_wire_says_yolo(tmp_path) -> None:
    database = Database(tmp_path / "hub.db")
    service, pid = _bind(database, _repo(tmp_path), "launch_step", "yolo")
    program = service.get(OWNER, pid)
    assert program["control_word"] == "YOLO"
    assert program["status_line"].endswith("control YOLO")


def test_a_refused_call_keeps_its_whole_command_and_cwd_on_the_ledger(launched, tmp_path, monkeypatch) -> None:
    """The live proof (2026-11-01): the refusal line kept only the 120-char
    head, so its cause could not be read. The checkpoint's detail now holds
    the whole redacted command and the folder the gate saw."""
    _mode(tmp_path, monkeypatch, "neutral")
    service, pid = _bind(launched.db, launched.worktree, launched.launch_id, "yolo")
    command = ('git add README.md && git commit -q -m "Add the line\n\nCo-Authored-By: Claude <noreply@anthropic.com>" '
               '&& git log --oneline -1 && echo done > /etc/holdspeak-outside-log')
    assert len(command) > 120
    refused = _call(launched, command).proposal
    assert refused.state == DENIED
    row = next(row for row in service.store.list_checkpoints(pid) if row["line"].startswith("Refused by rule"))
    detail = row["undo"]["detail"]
    assert f"cwd {launched.worktree}" in detail and "rule redirect_outside_worktree · scope outside" in detail
    assert "/etc/holdspeak-outside-log" in detail  # past the 120-char head
