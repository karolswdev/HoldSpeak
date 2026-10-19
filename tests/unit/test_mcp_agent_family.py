"""Betterment AG11: agents that work together. Each helper tool's rules
(herdr's contract) and its place in the palettes."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from holdspeak.principals import PrincipalKind
from holdspeak.services import agent_helpers as helpers

HELPER_TOOLS = ("agent.start_helper", "agent.prompt", "agent.wait", "agent.read", "agent.answer")


class _Ledger:
    def __init__(self, *rows):
        self.rows = {r["launch_id"]: dict(r) for r in rows}

    def get(self, launch_id):
        return self.rows.get(launch_id)

    def list(self):
        return list(self.rows.values())

    def update(self, launch_id, **fields):
        row = self.rows.get(launch_id)
        if row is not None:
            row.update(fields)
        return row


PARENT = {"launch_id": "L1", "state": "registered", "branch": "hs/flag", "origin_ref": {"kind": "action", "id": "a1"}}
HELPER = {"launch_id": "H1", "state": "registered", "helper_of": "L1", "session": "hs-H1",
          "origin_ref": {"kind": "action", "id": "a1"}}


class _Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, seconds):
        self.t += seconds


def _states(monkeypatch, *states, key="claude:h1"):
    seq = list(states)

    def state(db, launch_id, ledger=None):
        word = seq.pop(0) if len(seq) > 1 else seq[0]
        if isinstance(word, tuple):
            return {"launch_id": launch_id, "state": word[0], "session_key": word[1], "turn_id": None}
        return {"launch_id": launch_id, "state": word, "session_key": key, "turn_id": "t1" if word == "done" else None}

    monkeypatch.setattr(helpers, "helper_state", state)
    monkeypatch.setattr(helpers, "last_words", lambda db, launch_id, ledger=None: "Done. Two findings.")
    monkeypatch.setattr(helpers, "_pane", lambda record: "%7")


def test_the_helper_tools_are_the_launchs_and_no_threads() -> None:
    from holdspeak.mcp.palettes import CONDUCTOR, resolve_palette
    from holdspeak.mcp.tool_authority import TOOL_AUTHORITY, WORK
    from holdspeak.services import thread_modes
    from holdspeak.services.conductor_launch import LAUNCH_RULES

    palette = resolve_palette(CONDUCTOR)
    for name in HELPER_TOOLS:
        assert TOOL_AUTHORITY[name] == WORK and name in palette, name
        assert name in LAUNCH_RULES, name   # own-only: the helper the launch made
        for mode_tools in (thread_modes._DESK_TOOLS, thread_modes._CHASE_TOOLS, thread_modes._PLAN_TOOLS):
            assert name not in mode_tools
    assert LAUNCH_RULES["agent.start_helper"][0] == "create"
    assert all(LAUNCH_RULES[n][:2] == ("own", "launch") for n in HELPER_TOOLS[1:])


def test_start_helper_hands_the_same_item_as_a_helper_once_and_secure_asks_for_one_owner_press() -> None:
    calls = []
    service = SimpleNamespace(hand=lambda principal, kind, item_id, **kw: calls.append((kind, item_id, kw)) or {
        "launch_id": "H1", "status": "launched", "worktree": {"name": "hs-a1-helper"}})
    secure = _Ledger(PARENT)
    asked = helpers.start_helper("L1", instruction="Review the diff", profile="codex-default", hand_service=service,
                                 control_mode=lambda: "secure", ledger=secure)
    assert asked["status"] == "awaiting_owner" and asked["owner_action"]["launch_id"] == "L1" and calls == []
    request_id = asked["owner_action"]["request_id"]
    allowed = helpers.allow_helper("L1", request_id=request_id, principal=SimpleNamespace(kind=PrincipalKind.OWNER),
                                   hand_service=service, ledger=secure)
    assert allowed["status"] == "launched" and allowed["helper_of"] == "L1"
    assert calls == [("action", "a1", {"instruction": "Review the diff", "profile": "codex-default", "helper_of": "L1"})]
    calls.clear()
    answer = helpers.start_helper("L1", instruction="Review the diff", profile="codex-default", hand_service=service,
                                  control_mode=lambda: "neutral", ledger=_Ledger(PARENT))
    assert answer == {"launch_id": "H1", "status": "launched", "helper_of": "L1", "worktree": {"name": "hs-a1-helper"}}
    assert calls == [("action", "a1", {"instruction": "Review the diff", "profile": "codex-default", "helper_of": "L1"})]
    with pytest.raises(helpers.HelperRefused) as again:
        helpers.start_helper("L1", instruction="x", profile=None, hand_service=service,
                             control_mode=lambda: "yolo", ledger=_Ledger(PARENT, HELPER))
    assert again.value.code == "helper_exists"


def test_prompt_with_wait_is_one_request_and_reads_the_helpers_words(monkeypatch) -> None:
    _states(monkeypatch, "quiet-start", "working", "working", "done")
    monkeypatch.setattr(helpers, "helper_state", _seq(["idle", "working", "working", "done", "done"]))
    clock = _Clock()
    sent = []
    answer = helpers.prompt(None, "L1", "H1", "Review the diff", wait=True, send=lambda **kw: sent.append(kw),
                            clock=clock, sleep=clock.sleep, ledger=_Ledger(PARENT, HELPER))
    assert sent == [{"pane": "%7", "text": "Review the diff", "submit": True}]
    assert answer == {"launch_id": "H1", "status": "sent", "state": "done", "said": "Done. Two findings."}


def _seq(words):
    seq = list(words)

    def state(db, launch_id, ledger=None):
        word = seq.pop(0) if len(seq) > 1 else seq[0]
        return {"launch_id": launch_id, "state": word, "session_key": "claude:h1",
                "turn_id": "t1" if word == "done" else None}

    return state


def test_prompt_refuses_a_blocked_helper_and_says_stalled_after_five_seconds(monkeypatch) -> None:
    _states(monkeypatch, "asks")
    with pytest.raises(helpers.HelperRefused) as blocked:
        helpers.prompt(None, "L1", "H1", "go on", send=lambda **kw: None, ledger=_Ledger(PARENT, HELPER))
    assert blocked.value.code == "agent_blocked"
    _states(monkeypatch, "idle")
    clock = _Clock()
    answer = helpers.prompt(None, "L1", "H1", "go on", send=lambda **kw: None, clock=clock, sleep=clock.sleep,
                            ledger=_Ledger(PARENT, HELPER))
    assert answer["status"] == "agent_prompt_stalled" and clock.t >= helpers.STALL_SECONDS


def test_only_its_own_helper_and_never_an_approval(monkeypatch) -> None:
    _states(monkeypatch, "approve")
    with pytest.raises(helpers.HelperRefused) as other:
        helpers.read(None, "L2", "H1", ledger=_Ledger(PARENT, HELPER))
    assert other.value.code == "not_your_helper"
    with pytest.raises(helpers.HelperRefused) as approval:
        helpers.answer(None, "L1", "H1", "1", send=lambda **kw: None, ledger=_Ledger(PARENT, HELPER))
    assert approval.value.code == "approval_is_owners"
    _states(monkeypatch, "asks")
    sent = []
    assert helpers.answer(None, "L1", "H1", " 1 ", send=lambda **kw: sent.append(kw),
                          ledger=_Ledger(PARENT, HELPER))["status"] == "sent"
    assert sent[0]["text"] == "1"


def test_wait_is_pinned_to_the_helpers_session(monkeypatch) -> None:
    _states(monkeypatch, ("working", "claude:h1"), ("working", "claude:h1"), ("working", "claude:OTHER"))
    clock = _Clock()
    with pytest.raises(helpers.HelperRefused) as replaced:
        helpers.wait_for(None, "L1", "H1", clock=clock, sleep=clock.sleep, ledger=_Ledger(PARENT, HELPER))
    assert replaced.value.code == "agent_replaced"


from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: E402,F401


def test_a_helper_gets_its_own_worktree_on_a_branch_from_its_parents(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    import subprocess

    rig = _rig(tmp_path, db, monkeypatch)
    parent = rig.hand.hand(OWNER, "action", "ai_1")
    record = _wait_for(lambda: rig.launches.get(parent["launch_id"]), "state", "registered")
    (rig.worktree / "BUILDER.md").write_text("the builder's work\n")
    subprocess.run(["git", "add", "."], cwd=rig.worktree, check=True)
    subprocess.run(["git", "-c", "user.name=b", "-c", "user.email=b@x.invalid", "commit", "-q", "-m", "work"],
                   cwd=rig.worktree, check=True)
    answer = helpers.start_helper(parent["launch_id"], instruction="Review the diff", profile=None,
                                  hand_service=rig.hand, control_mode=lambda: "yolo", ledger=rig.launches)
    helper = rig.launches.get(answer["launch_id"])
    assert helper["helper_of"] == parent["launch_id"]
    assert helper["branch"] == f"{record['branch']}-helper"
    helper_tree = rig.worktree.parent / f"{rig.worktree.name}-helper"
    assert (helper_tree / "BUILDER.md").read_text() == "the builder's work\n"   # it starts at the parent's branch
    with pytest.raises(helpers.HelperRefused) as again:
        helpers.start_helper(parent["launch_id"], instruction="again", profile=None, hand_service=rig.hand,
                             control_mode=lambda: "yolo", ledger=rig.launches)
    assert again.value.code == "helper_exists"
