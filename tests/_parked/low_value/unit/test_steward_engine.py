# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_steward_engine.py to restore.

# ruff: noqa


# --- TestPhaseCheckpoints::test_six_steps_created: P6/P5: counts step rows and checks seq numbers and key prefixes; test_steps_cover_all_phases already checks the phases
# (was a method of class TestPhaseCheckpoints)
def test_six_steps_created(self, tmp_path: Path) -> None:
    conn = _make_conn(tmp_path)
    svc, db = _make_service(conn)
    run_id = svc.run_once(_principal(), "proj-1")

    steps = db.steward_steps.list_steps(run_id)
    assert len(steps) == 6


# --- TestPhaseCheckpoints::test_steps_have_sequential_seq: P6/P5: counts step rows and checks seq numbers and key prefixes; test_steps_cover_all_phases already checks the phases
# (was a method of class TestPhaseCheckpoints)
def test_steps_have_sequential_seq(self, tmp_path: Path) -> None:
    conn = _make_conn(tmp_path)
    svc, db = _make_service(conn)
    run_id = svc.run_once(_principal(), "proj-1")

    steps = db.steward_steps.list_steps(run_id)
    seqs = [s["seq"] for s in steps]
    assert seqs == [0, 1, 2, 3, 4, 5]


# --- TestPhaseCheckpoints::test_steps_have_idempotency_keys: P6/P5: counts step rows and checks seq numbers and key prefixes; test_steps_cover_all_phases already checks the phases
# (was a method of class TestPhaseCheckpoints)
def test_steps_have_idempotency_keys(self, tmp_path: Path) -> None:
    conn = _make_conn(tmp_path)
    svc, db = _make_service(conn)
    run_id = svc.run_once(_principal(), "proj-1")

    steps = db.steward_steps.list_steps(run_id)
    for step in steps:
        assert step["idempotency_key"].startswith(run_id + ":")
