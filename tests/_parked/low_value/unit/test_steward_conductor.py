# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_steward_conductor.py to restore.

# ruff: noqa


# --- TestBlockIsolation::test_conductor_never_calls_evaluate_due: P7/P6: asserts the tick's internal call list ('calls == ["run_due", "projections"]') and that event facts have keys
# (was a method of class TestBlockIsolation)
def test_conductor_never_calls_evaluate_due(
    self, tmp_path, monkeypatch,
) -> None:
    """TST-COND-001 (HS-200-43 R1): the tick does not evaluate watches.

    A watch service wired into the conductor that would RAISE if
    called proves the block is gone, not merely quiet -- and run_due
    still executes past it.
    """
    calls: list[str] = []

    class _PoisonWatch:
        def evaluate_due(self, principal):
            calls.append("evaluate_due")
            raise RuntimeError("poisoned evaluate_due")

    class _TrackSteward:
        def run_due(self, principal):
            calls.append("run_due")
            return []

        def project_cadence_projections(self, principal):
            calls.append("projections")
            return []

    self._tick_with(monkeypatch, tmp_path, _PoisonWatch(), _TrackSteward())
    assert "evaluate_due" not in calls
    assert calls == ["run_due", "projections"]


# --- TestBlockIsolation::test_conductor_tick_both_blocks_run: P7/P6: asserts the tick's internal call list ('calls == ["run_due", "projections"]') and that event facts have keys
# (was a method of class TestBlockIsolation)
def test_conductor_tick_both_blocks_run(
    self, tmp_path, monkeypatch,
) -> None:
    """TST-COND-003: healthy services; the steward block ticks.

    HS-200-43 R1: there is no watch block in the conductor any more,
    so the wired watch service is never touched.
    """
    calls: list[str] = []

    class _W:
        def evaluate_due(self, principal):
            calls.append("evaluate_due")
            return [{"watch_id": "cw_x", "outcome": "evaluated"}]

    class _S:
        def run_due(self, principal):
            calls.append("run_due")
            return [{"outcome": "run_started"}]

        def project_cadence_projections(self, principal):
            calls.append("projections")
            return []

    self._tick_with(monkeypatch, tmp_path, _W(), _S())
    assert calls == ["run_due", "projections"]


# --- TestStepCompletedEvent: P7/P6: asserts the tick's internal call list ('calls == ["run_due", "projections"]') and that event facts have keys
class TestStepCompletedEvent:
    """steward.step_completed emits per phase step."""

    def test_step_completed_per_phase(self, tmp_path) -> None:
        """TST-COND-005."""
        conn = _make_conn(tmp_path)
        db, svc = _make_service(conn)
        _seed_policy(conn)
        p = _principal()

        run_id = svc.insert_run(p, "proj-1")
        svc.execute_phases(p, run_id, "proj-1")

        events = db.automations.events
        step_completed = [
            e for e in events
            if e.get("event_type") == "steward.step_completed"
        ]
        # At least 6 phase steps (observe, compare, propose, act, verify, record)
        assert len(step_completed) >= len(PHASES), (
            f"Expected at least {len(PHASES)} step_completed events, "
            f"got {len(step_completed)}"
        )
        # Each has ref-oriented payload
        for evt in step_completed:
            assert "run_id" in evt["facts"]
            assert "phase" in evt["facts"]
            assert "step_id" in evt["facts"]
