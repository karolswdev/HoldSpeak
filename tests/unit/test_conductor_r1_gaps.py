"""Conductor R1, the real-use gaps the real loop found (coordinator plan B).

1. In YOLO and Normal a launched Claude edits its worktree with no prompt in
   the pane; Secure is unchanged.
2. A held gate call of a HoldSpeak launch is in Needs you (TO APPROVE).
3. A steer carries only what the owner attached: text that names an item
   pulls nothing in.
"""
from __future__ import annotations

import pytest

from tests.unit.test_web_routes_coders_steer import (  # noqa: F401  (env is a fixture)
    _pin_identity,
    _register,
    _seed_meeting,
    _session,
    env,
)


# ── 3. a steer grounds only what was attached ────────────────────────


def _steer(env, body: dict) -> str:  # noqa: F811
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch)
    env.client.post("/api/coders/claude:abc/arm", json={})
    res = env.client.post("/api/coders/claude:abc/steer", json={"submit": False, **body})
    assert res.status_code == 200, res.json()
    assert res.json()["status"] == "delivered"
    return env.sent[-1]["text"]


@pytest.mark.parametrize("grounding", [
    None,  # nothing attached
    {"meeting_ids": [], "artifact_ids": [], "refs": [], "expand": "summary"},  # an empty pick
])
def test_a_steer_that_names_an_item_pulls_nothing_in(env, grounding) -> None:  # noqa: F811
    """On the real desk a one-line answer that named action:<id> reached the
    agent with five grounded objects (memory recall over the text)."""
    mid = _seed_meeting(env.db)
    text = f"verify; see meeting:{mid} about the ship Friday decision (Kickoff)"
    body = {"text": text} if grounding is None else {"text": text, "grounding": grounding}
    sent = _steer(env, body)
    assert sent == text
    assert "--- from" not in sent and "grounded" not in sent
    assert env.db.steering.list()[0].grounding == []


def test_an_attached_ref_still_rides_along(env) -> None:  # noqa: F811
    mid = _seed_meeting(env.db)
    sent = _steer(env, {"text": "verify", "grounding": {"meeting_ids": [mid]}})
    assert '--- from meeting: "Kickoff"' in sent
    assert sent.rstrip().endswith("(1 object grounded)")


# ── 1. Normal and YOLO accept edits in the worktree ──────────────────

import shlex  # noqa: E402

from holdspeak.delivery import agent_mcp  # noqa: E402
from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: E402,F401  (db is a fixture)
from tests.unit.test_conductor_k6_agent_mcp import _spawn  # noqa: E402


@pytest.mark.parametrize("mode, accept", [("yolo", True), ("neutral", True), ("safe", False), ("Secure", False)])
def test_a_launched_claude_accepts_edits_in_normal_and_yolo(tmp_path, db, monkeypatch, mode, accept) -> None:  # noqa: F811
    """On the real desk every Edit of a launched Claude asked in the pane
    ("Do you want to make this edit to RUNBOOK.md?"), a TO APPROVE row per
    file change, in YOLO too."""
    rig = _rig(tmp_path / "rig", db, monkeypatch)
    rig.service._control_mode = lambda: mode
    result = rig.hand.hand(OWNER, "action", "ai_1")
    assert result["status"] == "launched", result
    _argv, command = _spawn(rig)
    agent_argv = shlex.split(command.split(" exec ", 1)[1])
    if accept:
        assert agent_argv[agent_argv.index("--permission-mode") + 1] == "acceptEdits"
        assert agent_argv.count("--permission-mode") == 1
    else:
        assert "--permission-mode" not in agent_argv
    # The tool gate still decides Bash; the allow list is last and unchanged.
    assert agent_argv[agent_argv.index("--allowedTools") + 1] == "Bash"
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    rig.tmux.ended = True


def test_a_permission_mode_the_launch_names_is_kept() -> None:
    assert agent_mcp.claude_permission_args("yolo", ["claude", "--permission-mode", "plan"]) == []
    assert agent_mcp.claude_permission_args("yolo", ["claude"]) == ["--permission-mode", "acceptEdits"]


# ── 2. a held call of a launch is in Needs you (TO APPROVE) ──────────

from holdspeak.db.gate import APPROVED, HELD  # noqa: E402
from holdspeak.principals import Principal, PrincipalKind  # noqa: E402
from holdspeak.services.needs_you_membership import (  # noqa: E402
    TO_APPROVE,
    _read_gate_holds,
    compute_needs_you,
)
from tests.unit.test_conductor_k5_supervision import AGENT, _call, _mode, launched  # noqa: E402,F401


def _gate_rows(rig) -> list[dict]:
    holds = _read_gate_holds(rig.db, ledger=rig.launches)
    return [row for row in compute_needs_you(gate_holds=holds)["unmutedItems"] if row["kind"] == "gate"]


def test_a_held_call_of_a_launch_is_a_to_approve_row_and_notifies(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    """On the real desk `ls /private/tmp/r1w` waited 240 s for the owner and
    Needs you showed nothing."""
    _mode(tmp_path, monkeypatch, "yolo")
    edges: list[str] = []
    launched.gate._on_launch_hold = edges.append
    held = _call(launched, "ls /etc")
    assert held.proposal.state == HELD
    rows = _gate_rows(launched)
    assert [row["id"] for row in rows] == [f"gate:{held.proposal.id}"]
    row = rows[0]
    assert row["why"] == TO_APPROVE and row["openRef"] == f"gate:{held.proposal.id}"
    assert row["title"] == "Approve: ls /etc"
    assert row["launchId"] == launched.launch_id and row["sessionKey"] == AGENT.identity
    assert edges == [f"gate:{held.proposal.id}"]  # the K3 immediate edge, once

    # A call the mode passes is neither a row nor an edge.
    passed = _call(launched, "git status")
    assert passed.proposal.state == APPROVED
    assert [r["id"] for r in _gate_rows(launched)] == [f"gate:{held.proposal.id}"]
    assert len(edges) == 1

    # Decided by the owner: the row goes.
    launched.gate.decide(Principal(PrincipalKind.OWNER, "owner"), held.proposal.id, {"decision": "denied"})
    assert _gate_rows(launched) == []


def test_a_hold_that_is_no_launchs_is_not_a_row(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    _mode(tmp_path, monkeypatch, "yolo")
    edges: list[str] = []
    launched.gate._on_launch_hold = edges.append
    other = Principal(PrincipalKind.AGENT, "claude:owner-terminal")
    held = _call(launched, "ls /etc", principal=other)
    assert held.proposal.state == HELD
    assert _gate_rows(launched) == [] and edges == []


def test_an_expired_hold_is_not_a_row(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    _mode(tmp_path, monkeypatch, "yolo")
    held = _call(launched, "ls /etc")
    holds = _read_gate_holds(launched.db, ledger=launched.launches, now=held.proposal.expires_at + 1)
    assert holds == []
