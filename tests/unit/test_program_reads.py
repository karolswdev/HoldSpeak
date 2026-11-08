"""The Program reads live in program_reads; ProgramService delegates (2026-11-08).

The move changes no answer: each ``ProgramService`` read gives the same
answer as the module function for one seeded Program, and the module loads
without the Program runtime.
"""
from __future__ import annotations

import subprocess
import sys
from typing import Any

from holdspeak.services import program_reads as reads
from holdspeak.services import program_service
from holdspeak.services.program_service import ProgramService
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig


def test_the_program_reads_module_does_not_reach_the_program_runtime() -> None:
    probe = ("import sys, holdspeak.services.program_reads; "
             "print(' '.join(sorted(m for m in sys.modules if m.startswith('holdspeak'))))")
    loaded = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, check=True).stdout.split()
    assert "holdspeak.services.program_reads" in loaded, loaded
    for module in loaded:
        assert not module.endswith(("program_service", "program_runner", "program_text")), loaded
        assert not module.startswith(("holdspeak.web", "holdspeak.runtime")), loaded


def test_each_delegating_method_answers_what_the_module_function_answers(tmp_path) -> None:
    rig = Rig(tmp_path)
    svc = rig.service
    pid = svc.create(OWNER, title="Reads", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                     control="secure")["id"]
    svc.plan(OWNER, pid, steps=[{"title": "First", "brief": "Do one thing.", "owns": ["a.py"]},
                                {"title": "Second", "brief": "Do the next.", "after": [1]}])
    svc.start(OWNER, pid)
    program = svc.store.get_program(pid)
    steps = svc.store.list_steps(pid)
    checkpoints = svc.store.list_checkpoints(pid)
    db = svc.db
    seams = {"clock": svc._clock, "person_name": svc.person_name}
    wire = {**seams, "engine": svc.engine, "estimate": svc._estimate}
    pairs: list[tuple[Any, Any]] = [
        (svc._program(pid), reads.require_program(db, pid)),
        (svc._step(program, steps[0]["id"]), reads.require_step(db, program, steps[0]["id"])),
        (svc.requirements(pid), reads.requirement_rows(db, pid)),
        (svc.proposals(pid), reads.proposal_rows(db, pid)),
        (svc._turn(program, steps), reads._turn(db, program, steps, clock=svc._clock)),
        (svc._state(program, steps), reads._state(db, program, steps)),
        (svc._summary(program, steps), reads._summary(db, program, steps, **seams)),
        (svc._wire(program, steps), reads._wire(db, program, steps, **wire)),
        (svc.get(OWNER, pid), reads.get(db, OWNER, pid, **wire, reach=svc.checkpoint_reach)),
        (svc.list(OWNER), reads.program_list(db, OWNER, **seams)),
        (svc.list(OWNER, q="reads"), reads.program_list(db, OWNER, q="reads", **seams)),
        (svc.family(program), reads.family(db, program, **seams)),
        (svc.parent_id(program), reads.parent_of(db, program)),
        (svc.find(OWNER, name="reads"), reads.find(db, OWNER, name="reads")),
        (svc.needs_you_items(), reads.needs_you_items(db, clock=svc._clock)),
        (svc.since_morning(OWNER), reads.since_morning(db, OWNER)),
        (svc.step_wire(program, steps[0], checkpoints),
         reads.step_wire(db, program, steps[0], checkpoints, engine=svc.engine, person_name=svc.person_name,
                         estimate=svc._estimate)),
        (svc._place(program), reads._place(db, program, person_name=svc.person_name)),
        (svc._language_wire(program), reads._language_wire(db, program, engine=svc.engine)),
        (svc.entry_wire({"profile": "claude-default"}), reads.entry_wire({"profile": "claude-default"}, engine=svc.engine)),
        (svc._waits_on(program), reads._waits_on(db, program)),
        (svc.decided_for_you(pid), reads.decided_for_you(db, pid)),
    ]
    for via_service, via_module in pairs:
        # The wire carries the seconds since a change: the two reads may sit a second apart.
        assert _still(via_service) == _still(via_module)
    # The seed is visible: two steps on the wire, the Program runs.
    assert [row["title"] for row in pairs[7][0]["steps"]] == ["First", "Second"]
    assert pairs[5][0] in ("running", "waiting")
    # The pure reads are the module's own function objects (one owner).
    assert ProgramService.runs_on_of is reads.runs_on_of
    assert ProgramService._status_line is reads._status_line
    assert ProgramService.requirement_wire is reads.requirement_wire
    assert program_service.your_turn is reads.your_turn
    assert program_service.program_state is reads.program_state


def _still(value: Any) -> Any:
    """``value`` without the keys that count seconds since now."""
    if isinstance(value, dict):
        return {key: _still(item) for key, item in value.items()
                if key not in ("in_state_seconds", "elapsed_seconds", "elapsed")}
    if isinstance(value, list):
        return [_still(item) for item in value]
    return value
