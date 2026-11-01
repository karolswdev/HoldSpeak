"""The owner's ruling of 2026-11-01: park stops the steps.

The live walk found a parked Program whose steps still read Working, with
breathing dots and Take it over. Now ``park()`` parks every open step with
it (``parked_by = program``, the state it had kept in ``facts.park_from``);
the engine hands, nudges and checks nothing on them, and an agent turn that
was running is left to end; each step's row reads one wait sentence; Resume
puts every step back where it was and the engine goes on.
"""
from __future__ import annotations

from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig
from tests.integration.test_desk_programs import _client, _fixture


def _program(rig: Rig) -> str:
    pid = rig.service.create(OWNER, title="Proof run", goal="Three parts.", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}", template="fast-cycle", control="yolo")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Part 1", "brief": "Write part 1."},
                                        {"title": "Part 2", "brief": "Write part 2."},
                                        {"title": "Part 3", "brief": "Write part 3.", "after": [2]}])
    rig.service.start(OWNER, pid)
    rig.tick()
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"part1.txt": "1\n"})
    rig.tick(3)
    return pid


def test_park_parks_every_open_step_and_resume_puts_them_back(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig)
    before = {n: rig.step(pid, n)["state"] for n in (1, 2, 3)}
    assert before[1] in ("merged", "done") and before[2] == "working" and before[3] == "planned", before
    launches = len(rig.ledger.list()) if hasattr(rig.ledger, "list") else None
    rig.service.park(OWNER, pid, reason="proof")
    wire = rig.program(pid)
    assert wire["steps"][0]["state"] == before[1]  # a merged step stays merged
    _fixture("program.parked_steps.json", _client(rig, monkeypatch).get(f"/api/programs/{pid}").json(), tmp_path)
    for n in (2, 3):
        step = rig.step(pid, n)
        assert step["state"] == "parked"
        assert step["wait"] == {"cause": "program_parked",
                                "line": f"Step {n} with Claude Code is parked with the program."}
    assert wire["your_turn_items"] == []  # a parked Program asks nothing
    # The agent's running turn ends; the engine hands, nudges and checks nothing.
    rig.agent.finish(rig.step(pid, 2)["launch_id"], {"part2.txt": "2\n"})
    rig.tick(3)
    assert [rig.step(pid, n)["state"] for n in (2, 3)] == ["parked", "parked"]
    if launches is not None:
        assert len(rig.ledger.list()) == launches  # no step was handed
    rig.service.resume(OWNER, pid)
    assert rig.step(pid, 2)["wait"] is None
    rig.tick(3)
    # Back where it was, and the engine goes on: part 2's commit is checked and merges; part 3 runs.
    assert rig.step(pid, 2)["state"] in ("checking", "merged", "done"), rig.step(pid, 2)["state"]
    assert rig.step(pid, 3)["state"] != "parked"
