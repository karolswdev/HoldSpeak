# PARKED 2026-11-09 (fix forward 2, after #2128): a crash after the model calls and BEFORE the publication starts
# (before_pending) now runs the summary call once more on recovery (2 calls, not 1). The route-plan controller's
# idempotent re-admission (a deterministic operation id that replayed the admitted execution) went with #2128; the
# door names each call with a fresh run id. Rows, ready state and plugin calls still recover exactly.
# Backlog: let the queue reuse the job's published analysis projection after that crash.
# Moved from tests/unit/test_phase200_meeting_outcomes.py (the other three boundaries stay live there).

import time

import pytest

from holdspeak.db import Database
from tests.unit.test_phase200_meeting_outcomes import *  # noqa: F401,F403
from tests.unit.test_phase200_meeting_outcomes import (  # noqa: F401
    _count, _latest_job, _meeting, _proposals, _rig,
)


@pytest.mark.parametrize("boundary", ["before_pending"])
def test_outcome_publication_crash_recovers_exact_rows_after_stale_parent_reconciliation(tmp_path, monkeypatch, boundary):
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.kernel.runtime import _configure

    db, engine = _rig(tmp_path, monkeypatch)
    state = _meeting(db, f"m-publication-crash-{boundary}")

    def process_loss(*args, **kwargs):
        raise KeyboardInterrupt("publication process lost")

    with monkeypatch.context() as crash:
        if boundary == "before_pending":
            crash.setattr(db.intel, "begin_bound_publication", process_loss)
        elif boundary == "before_bridge":
            crash.setattr("holdspeak.intel_queue._bridge_proposals", process_loss)
        elif boundary == "before_ready":
            crash.setattr(db.intel, "complete_bound_intel_job", process_loss)
        else:
            crash.setattr(db.meetings, "mark_ready_unseen", process_loss)
        with pytest.raises(KeyboardInterrupt):
            process_next_intel_job()
    job = _latest_job(db, state.id)
    saved_ids = {p["id"] for p in _proposals(db, state.id)}
    calls = (len(engine.analyzed), list(engine.plugin_calls))
    if boundary != "before_pending":
        with db._connection() as conn:
            conn.execute("UPDATE kernel_parent_runs SET lease_heartbeat_at=? WHERE operation_id=?",
                         (time.time() - 1000, job.parent_operation_id))
    fresh = Database(db.db_path)
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: fresh)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *a, **k: fresh)
    broker = _configure(fresh)
    assert broker.parent_run_controller.reconcile_abandoned() == 0
    assert process_next_intel_job() is True
    assert _latest_job(fresh, state.id).job_id == job.job_id
    assert fresh.meetings.get_meeting(state.id).intel_status == "ready"
    repaired_ids = {p["id"] for p in _proposals(fresh, state.id)}
    assert len(repaired_ids) == 5 and saved_ids <= repaired_ids
    assert (len(engine.analyzed), engine.plugin_calls) == calls
    assert _count(fresh, "intel_jobs", "WHERE origin_job_id=?", (job.job_id,)) == 0


