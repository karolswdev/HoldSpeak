"""The engine door chooses on its own: the owner's live assignment chain.

For every job the door names (``JOB_WORDS``), the first engine of the
assigned chain runs and the second is its one retry. The door reads the
assignment store; it writes no route plan.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.db import Database
from holdspeak.services import engine_door
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim


def _revision(db: Database, profile_id: str) -> str:
    return engine_door._bound_revision(db, profile_id)


def _assign(db: Database, command: str, scope: dict[str, str], *profiles: str) -> None:
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": command, "expected_revision": 0, "scope": scope,
        "entries": [{"profile_id": p, "profile_revision": 1} for p in profiles],
    })


def _route_plan_tables(db: Database) -> int:
    with db._connection() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='inference_route_plans'").fetchone()[0])


@pytest.fixture
def desk(tmp_path: Path) -> SimpleNamespace:
    db = Database(tmp_path / "door.db")
    claims = ("language", _result_claim("agent.plan"))
    _profile(db, "codex-first", model="codex", claims=claims)
    _profile(db, "gemini-second", model="gemini", claims=claims)
    _assign(db, "global-chain", {"kind": "global"}, "codex-first", "gemini-second")
    return SimpleNamespace(db=db, broker=SimpleNamespace(database=db))


@pytest.mark.parametrize("job", sorted(engine_door.JOB_WORDS))
def test_every_job_runs_on_the_first_engine_and_falls_back_to_the_second(desk: SimpleNamespace, job: str) -> None:
    engine = engine_door.engine_for(desk.broker, job)
    assert (engine.revision, engine.profile) == (_revision(desk.db, "codex-first"), "codex-first")
    assert engine.fallback is not None
    assert (engine.fallback.revision, engine.fallback.profile) == (_revision(desk.db, "gemini-second"), "gemini-second")
    assert engine.assignment == engine.fallback.assignment != ""
    assert _route_plan_tables(desk.db) == 0


def test_a_job_row_of_its_own_wins_over_the_default(desk: SimpleNamespace) -> None:
    _assign(desk.db, "plan-row", {"kind": "capability", "capability_id": "agent.plan"}, "gemini-second", "codex-first")
    engine = engine_door.engine_for(desk.broker, "agent.plan")
    assert engine.profile == "gemini-second" and engine.fallback.profile == "codex-first"
    assert engine_door.engine_for(desk.broker, "ask.answer").profile == "codex-first"
    assert _route_plan_tables(desk.db) == 0


def test_a_subject_row_wins_for_its_subject_only(desk: SimpleNamespace) -> None:
    _assign(desk.db, "wb-row", {"kind": "subject", "subject_kind": "workbench", "subject_id": "wb1",
                                "capability_id": "workbench.item"}, "gemini-second")
    assert engine_door.engine_for(desk.broker, "workbench.item", subject=("workbench", "wb1")).profile == "gemini-second"
    assert engine_door.engine_for(desk.broker, "workbench.item", subject=("workbench", "wb2")).profile == "codex-first"
    assert engine_door.engine_for(desk.broker, "workbench.item", subject=("workbench", "wb1")).fallback is None


def test_no_assignment_is_no_engine(tmp_path: Path) -> None:
    db = Database(tmp_path / "empty.db")
    with pytest.raises(engine_door.EngineDoorError) as caught:
        engine_door.engine_for(SimpleNamespace(database=db), "ask.answer")
    assert caught.value.code == "no_engine"
