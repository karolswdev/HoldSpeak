"""program.park reason (2026-11-01): a proof run or a Program he is done with
is parked with its reason, and the list can fold it (``parked_as``)."""
from __future__ import annotations

import pytest

from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig


def _made(rig: Rig, title: str) -> str:
    pid = rig.service.create(OWNER, title=title, repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="fast-cycle", control="yolo")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x"}])
    return pid


def test_a_park_reason_rides_the_list_and_the_ledger(tmp_path) -> None:
    rig = Rig(tmp_path)
    proof, done, plain = _made(rig, "Proof 3"), _made(rig, "Old one"), _made(rig, "Paused")
    rig.service.park(OWNER, proof, reason="proof")
    rig.service.park(OWNER, done, reason="done-with-it")
    rig.service.park(OWNER, plain)
    rows = {row["id"]: row for row in rig.service.list(OWNER)["programs"]}
    assert (rows[proof]["parked_as"], rows[done]["parked_as"], rows[plain]["parked_as"]) == ("proof", "done_with_it", None)
    lines = [row["line"] for row in rig.program(proof)["checkpoints"]]
    assert "Parked the program; the worktrees stay (a proof run)" in lines
    rig.service.resume(OWNER, proof)
    assert "parked_as" not in rig.program(proof)
    with pytest.raises(ProgramRefused) as refused:
        rig.service.park(OWNER, plain, reason="bored")
    assert refused.value.code == "park_reason_invalid"
