# PARKED 2026-11-09 (door/own-choice-park-waist): the deferred queue's model call runs through the engine door; the route controller's execution rows and replay are not written.
# Moved from tests/unit/test_meeting_deferred_admission.py; its helpers are still there.

from tests.unit.test_meeting_deferred_admission import *  # noqa: F401,F403


def test_stale_takeover_reconciles_only_its_own_execution(tmp_path, monkeypatch):
    """Recovering stale B cannot terminalize healthy in-flight A."""
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    db, broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state_b = _queued_meeting(
        db, "m-scoped-recovery-b", text="meeting-b stale transcript", legacy_claimed=False,
    )
    stale_b = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert stale_b is not None and stale_b.meeting_id == state_b.id
    state_a = _queued_meeting(
        db, "m-scoped-recovery-a", text="meeting-a healthy transcript", legacy_claimed=False,
    )
    entered, release = threading.Event(), threading.Event()
    physical_a = 0

    def analysis(transcript: str, *, stream: bool = False):
        nonlocal physical_a
        assert stream is False
        if "meeting-a healthy" in transcript:
            physical_a += 1
            entered.set()
            assert release.wait(timeout=5.0)
        return engine._result()

    monkeypatch.setattr(engine, "analyze", analysis)
    a_result: list[bool] = []
    worker_a = threading.Thread(target=lambda: a_result.append(process_next_intel_job()))
    worker_a.start()
    assert entered.wait(timeout=2.0)

    # B lost its process; a normal Process/CLI path adopts it while A's dispatch
    # is still live. Scoped recovery may inspect B only, never A's intent.
    with db._connection() as conn:
        conn.execute("UPDATE intel_jobs SET executor_lease_expires_at=0 WHERE job_id=?", (stale_b.job_id,))
    assert process_next_intel_job() is True
    with db._connection() as conn:
        a_execution = conn.execute(
            """SELECT execution.state FROM inference_route_executions execution
               JOIN inference_route_attempts attempt ON attempt.execution_id=execution.id
               JOIN kernel_operations child ON child.operation_id=attempt.child_operation_id
               WHERE child.parent_operation_id=(SELECT parent_operation_id FROM intel_jobs WHERE meeting_id=?)""",
            (state_a.id,),
        ).fetchone()
    assert a_execution is not None and a_execution["state"] == "active"

    release.set()
    worker_a.join(timeout=5.0)
    assert not worker_a.is_alive() and a_result == [True] and physical_a == 1
    with db._connection() as conn:
        a_job = conn.execute("SELECT status FROM intel_jobs WHERE meeting_id=?", (state_a.id,)).fetchone()
        snapshots = conn.execute(
            "SELECT COUNT(*) FROM intel_snapshots WHERE meeting_id=?", (state_a.id,)
        ).fetchone()[0]
        retries = conn.execute(
            "SELECT COUNT(*) FROM intel_job_attempts WHERE meeting_id=? AND outcome='scheduled_retry'",
            (state_a.id,),
        ).fetchone()[0]
        successors = conn.execute(
            "SELECT COUNT(*) FROM intel_jobs WHERE meeting_id=? AND origin_job_id IS NOT NULL",
            (state_a.id,),
        ).fetchone()[0]
    assert a_job["status"] == "succeeded"
    assert snapshots == 1 and retries == 0 and successors == 1


