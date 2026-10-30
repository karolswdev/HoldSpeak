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

import subprocess
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.db.gate import APPROVED, HELD
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
    assert line["rule"] == "Yolo: the desk's ROUTINE draft is typed (AgentResponder)"
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
    # Outside its worktree it still waits for him.
    assert _call(launched, "cat /etc/passwd").proposal.state == HELD
    [line] = _decided(service, pid)
    assert line["kind"] == "gate_approval" and line["line"] == "Allowed: Bash"
    assert line["rule"] == "Yolo: the gate allows a read, a build or a test by its own rules"
    # A second allowed call of the same tool under the same rule: one line.
    assert _call(launched, "pytest -q").proposal.state == APPROVED
    assert len(_decided(service, pid)) == 1
    assert "Allowed: Bash" in launched.db.notes.get(f"program-{pid}").body_markdown


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
