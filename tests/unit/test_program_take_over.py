"""PG-IMPORT IMP6 (BROCREW-IMPORT-2026-11-01): take it over, hand it back.

BroCrew: "It says 'take it over', because it IS that act", and Hand it back
"still asks once and never twice: a confirmation in front of a REVERSIBLE act
teaches a person the act weighs what an irreversible one does". On the
Programs rig: while he has the lane the tick types nothing into it, never
nudges, never parks the step for a turn with no commit, and never reads a hold
as ended; a commit on the branch still goes to the check. Hand it back gives
the lane to the engine again.
"""
from __future__ import annotations

import pytest

from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig


def _running(tmp_path) -> tuple[Rig, str, dict]:
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Atlas", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="fast-cycle", control="normal")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Anchors", "brief": "x"}, {"title": "Index", "brief": "y", "after": [1]}])
    rig.service.start(OWNER, pid)
    rig.tick()
    return rig, pid, rig.step(pid, 1)


def test_while_he_has_the_lane_the_engine_types_nothing_and_parks_nothing(tmp_path) -> None:
    rig, pid, step = _running(tmp_path)
    wire = rig.service.take_over(OWNER, pid, step["id"])
    assert next(row for row in wire["steps"] if row["id"] == step["id"])["taken"] is True
    assert wire["checkpoints"][0]["line"] == "You took the lane over" and wire["checkpoints"][0]["by"] == "owner"
    typed = len(rig.prompts)
    for turn in range(3):  # three turns end with no commit: no nudge, no park
        rig.states[step["launch_id"]] = {"state": "done", "turn_id": f"t-{turn}"}
        rig.tick()
    assert len(rig.prompts) == typed
    assert rig.step(pid, 1)["state"] in ("briefed", "working")
    rig.service.amend(OWNER, pid, step["id"], "Cite the anchors in order")
    rig.tick()
    assert len(rig.prompts) == typed  # his amendment waits until he hands the lane back
    # His own commit still goes to the check.
    rig.agent.finish(step["launch_id"], {"docs/atlas.md": "x\n"})
    rig.tick()
    assert rig.step(pid, 1)["state"] not in ("briefed", "working")


def test_hand_it_back_and_the_engine_goes_on(tmp_path) -> None:
    rig, pid, step = _running(tmp_path)
    rig.service.take_over(OWNER, pid, step["id"])
    wire = rig.service.hand_back(OWNER, pid, step["id"])
    assert next(row for row in wire["steps"] if row["id"] == step["id"])["taken"] is False
    assert wire["checkpoints"][0]["line"] == "You handed the lane back"
    rig.states[step["launch_id"]] = {"state": "done", "turn_id": "t-1"}
    typed = len(rig.prompts)
    rig.tick()
    assert len(rig.prompts) == typed + 1  # the engine asks the agent to commit again


def test_only_a_running_lane_and_only_the_owner(tmp_path) -> None:
    rig, pid, step = _running(tmp_path)
    assert rig.step(pid, 2)["state"] == "planned"
    with pytest.raises(ProgramRefused) as refused:
        rig.service.take_over(OWNER, pid, rig.step(pid, 2)["id"])
    assert refused.value.code == "no_lane"
    with pytest.raises(ProgramRefused) as refused:
        rig.service.take_over(None, pid, step["id"])
    assert refused.value.code == "owner_required"
