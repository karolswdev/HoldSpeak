"""HS-200-42 — the hub drains the intel queue.

The 2026-09-13 operational-surface audit (§3.1) measured the defect: a stopped
meeting wrote an ``intel_jobs`` row and **nothing in the running product
executed it**.  ``IntelQueueWorker`` had zero production callers;
``drain_intel_queue`` was reachable only from the CLI and from
``POST /api/intel/process``, a route no face calls.  ``intel_snapshots`` on the
owner's desk was 0.

The ``reference_lying_test_doubles`` law governs this file: the ONLY faked
seam is the provider engine (through ``_queue_rig``, the same rig the deferred
admission suite uses).  The queue repository, the kernel parents, the bound
executor, the retry ledger, the conductor, the service verb and — for the
fence — the REAL hub lifespan are production code.
"""
from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.db import Database
from tests.unit.test_meeting_deferred_admission import (
    OWNER,
    _queue_rig,
    _queued_meeting,
    _rows,
)

pytestmark = pytest.mark.timeout(120, method="thread")


# ── rigs ──────────────────────────────────────────────────────────────


def _stop_all() -> None:
    from holdspeak import intel_queue_conductor as conductor

    conductor.stop_intel_queue_conductor()
    conductor.set_broadcast(None)


_CLAIMED: list[object] = []


@pytest.fixture(autouse=True)
def _clean_conductor():
    """No test leaves a drainer thread or an owner claim behind (HS-200-03).

    Counsel P2-10: the release is conditional. A blanket
    ``release_database()`` would drop a claim this test never took -- in a
    process where something else (a fixture, an earlier module) legitimately
    owns the database, that is a silent theft of another test's lock.
    """
    from holdspeak.runtime_lock import release_database

    _stop_all()
    _CLAIMED.clear()
    yield
    _stop_all()
    if _CLAIMED:
        release_database()
        _CLAIMED.clear()


def _own(db_path) -> None:
    """Take the REAL database owner claim this process would take at boot."""
    from holdspeak.runtime_lock import claim_database, current_lock

    assert current_lock() is None, (
        "this process already owns a database; the test would steal the claim"
    )
    lock = claim_database(db_path)
    assert lock.held, "the test process could not claim its own tmp database"
    _CLAIMED.append(lock)


def _wait(predicate, *, timeout: float = 30.0, nudge=None) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        if nudge is not None:
            nudge()
        time.sleep(0.05)
    return predicate()


# ── 1. the conductor: start, stop, idempotence ────────────────────────


def test_the_conductor_starts_a_live_drainer_and_stop_joins_the_thread(tmp_path, monkeypatch):
    from holdspeak import intel_queue_conductor as conductor

    db, _broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    _own(db.db_path)

    worker = conductor.start_intel_queue_conductor()
    assert worker is not None and worker.is_alive()
    assert conductor.drainer_state() == "running"
    # The brief's poll ruling: 15s at the hub (the worker's own floor is 5s).
    assert worker.poll_seconds == conductor.HUB_POLL_SECONDS == 15.0

    conductor.stop_intel_queue_conductor()
    assert worker.is_alive() is False
    assert conductor.drainer_state() == "absent"
    assert conductor.current_intel_queue_conductor() is None


def test_a_second_start_in_one_process_is_a_no_op_returning_the_live_worker(tmp_path, monkeypatch):
    from holdspeak import intel_queue_conductor as conductor

    db, *_ = _queue_rig(tmp_path, monkeypatch)
    _own(db.db_path)

    first = conductor.start_intel_queue_conductor()
    second = conductor.start_intel_queue_conductor()
    assert first is second
    assert threading.active_count  # sanity: the names below are the proof
    drainers = [t for t in threading.enumerate() if t.name == "HoldSpeakIntelQueue"]
    assert len(drainers) == 1, [t.name for t in drainers]


# ── 2. the second hub: ownership, proven not assumed ──────────────────


def test_a_process_that_does_not_own_the_database_starts_no_drainer(tmp_path, monkeypatch):
    """Ruling 2. A second hub normally cannot reach the lifespan at all:
    ``_claim_database`` raises ``SystemExit(1)``.  But
    ``HOLDSPEAK_ALLOW_UNOWNED_DB=1`` starts one anyway and promises
    *scheduled work OFF*.  Draining is scheduled work, so the conductor
    refuses on the claim, not on the env var.
    """
    from holdspeak import intel_queue_conductor as conductor

    db, *_ = _queue_rig(tmp_path, monkeypatch)
    # No claim taken: current_lock() is None — unknown, and not an owner.
    assert conductor.owns_database() is False
    assert conductor.start_intel_queue_conductor() is None
    assert conductor.drainer_state() == "absent"
    assert [t for t in threading.enumerate() if t.name == "HoldSpeakIntelQueue"] == []
    _ = db


def test_the_second_hub_refusal_is_the_real_lock_not_a_flag(tmp_path, monkeypatch):
    """The refusal a second hub meets is the REAL owner lock in another pid.

    A live foreign holder of the flock makes this process's claim fail, and a
    failed claim is what ``_claim_database`` turns into ``SystemExit(1)``.
    """
    import os
    import subprocess
    import sys

    from holdspeak.runtime_lock import DatabaseOwnerLock, owner_lock_path

    db_path = tmp_path / "owned.db"
    db_path.write_bytes(b"")
    lock_path = owner_lock_path(db_path)
    holder = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import fcntl,os,sys,time\n"
            f"h=os.open({str(lock_path)!r}, os.O_RDWR|os.O_CREAT, 0o600)\n"
            "fcntl.flock(h, fcntl.LOCK_EX)\n"
            "sys.stdout.write('held\\n'); sys.stdout.flush()\n"
            "time.sleep(30)\n",
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "held"
        mine = DatabaseOwnerLock(db_path)
        assert mine.acquire() is False, "a foreign live holder must refuse this claim"
        assert mine.held is False
        owner = mine.owner()
        assert owner is None or owner.get("pid") != os.getpid()
    finally:
        holder.kill()
        holder.wait(timeout=10)


# ── 3. the verb is honest, and fast ───────────────────────────────────


def _service(db, notify=None):
    from holdspeak.services.meeting_intel_service import MeetingIntelService

    return MeetingIntelService(db, notify)


def _planned_selection_hash(db, meeting_id: str) -> str:
    """Read the exact SERVICE route disclosed before a run gesture."""
    from holdspeak.services.meeting_route_projection import project_route

    planned = project_route(db, invocation_id=f"meeting:{meeting_id}")
    assert planned["status"] == "ready", planned
    assert planned["legs"], planned
    selection_hash = planned["selection_hash"]
    assert selection_hash, planned
    return str(selection_hash)


def test_run_intelligence_names_an_absent_drainer_instead_of_claiming_it_runs(tmp_path, monkeypatch):
    db, *_ = _queue_rig(tmp_path, monkeypatch)
    _queued_meeting(db, "m-absent")

    result = _service(db).run_intelligence(
        OWNER,
        "m-absent",
        expected_selection_hash=_planned_selection_hash(db, "m-absent"),
    )
    assert result["state"] == "queued"
    assert result["drainer"] == "absent"
    assert result["expectedWithinSeconds"] is None


def test_run_intelligence_reports_a_running_drainer_and_wakes_it(tmp_path, monkeypatch):
    from holdspeak import intel_queue_conductor as conductor

    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    _own(db.db_path)
    state = _queued_meeting(db, "m-wake")
    # Clear the stop-handoff row: the verb enqueues its own.
    for job in db.intel.list_intel_jobs(status="all"):
        db.intel.skip_remaining_intel(job.meeting_id)

    worker = conductor.start_intel_queue_conductor()
    assert worker is not None
    before = worker.iterations

    result = _service(db).run_intelligence(
        OWNER,
        "m-wake",
        expected_selection_hash=_planned_selection_hash(db, "m-wake"),
    )
    assert result["drainer"] == "running"
    assert result["expectedWithinSeconds"] == 0

    # The wake is real: the loop turns again long before the 15s poll.
    assert _wait(lambda: worker.iterations > before, timeout=10.0), (
        "wake() did not make the drainer turn; it waited out the poll"
    )
    assert _wait(lambda: bool(_rows(db, "intel_snapshots")), timeout=30.0)
    assert engine.analyzed, "the real provider seam was never reached"
    _ = state


# ── 4. quiet hours govern NOTIFICATION, never computation ─────────────


def test_the_drainer_computes_during_quiet_hours_and_notifies_nobody(tmp_path, monkeypatch):
    """Ruling 4, with the honest finding attached.

    There is NO ``aftercare_ready`` -> desktop-notification path in this
    product: ``desktop_notify`` has exactly two callers
    (``services/heartbeat_service.py`` and ``mcp/families/heartbeat.py``) and
    ``aftercare_ready`` is a WebSocket frame to an open browser only.  So the
    thing to prove is (a) the drainer computes regardless of the hour and
    (b) it reaches no desktop notifier at all, while (c) the one real
    quiet-hours gate still holds the notification it governs.
    """
    from holdspeak import intel_queue_conductor as conductor
    import holdspeak.desktop_notify as desktop_notify

    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    _own(db.db_path)
    _queued_meeting(db, "m-quiet")

    posted: list[tuple[str, str]] = []
    monkeypatch.setattr(
        desktop_notify, "notify", lambda title, body, **kw: posted.append((title, body)) or True
    )

    # The real validator, on a real quiet hour.
    from holdspeak.cadence.scheduler import in_quiet_hours

    assert in_quiet_hours(datetime(2026, 9, 14, 23, 30, 0), 22, 8) is True

    # A quiet window that contains the clock this test actually runs on, so
    # the gate below is exercised by the REAL `datetime.now()` inside
    # `heartbeat_notify` rather than by a patched clock.
    now = datetime.now()
    quiet_start, quiet_end = now.hour, (now.hour + 1) % 24
    assert in_quiet_hours(now, quiet_start, quiet_end) is True

    worker = conductor.start_intel_queue_conductor()
    assert worker is not None
    assert _wait(lambda: bool(_rows(db, "intel_snapshots")), timeout=30.0, nudge=worker.wake), (
        "the drainer refused to compute at 23:30 — quiet hours are not a compute gate"
    )
    assert engine.analyzed
    assert posted == [], "the drainer must not post a desktop notification"

    # (c) The real gate the product HAS still holds, at this same hour.
    receipts: list[dict[str, Any]] = []
    result = desktop_notify.heartbeat_notify(
        3,
        1,
        edge=desktop_notify.EdgeDetector(),
        quiet_hours_start=quiet_start,
        quiet_hours_end=quiet_end,
        receipt_writer=receipts.append,
        _notifier=lambda *a, **k: posted.append(("heartbeat", "fired")) or True,
    )
    assert result["held"] is True and result["reason"] == "quiet_hours"
    assert posted == [], "quiet hours must hold the notification it governs"
    assert receipts and receipts[0]["result_summary"].startswith("held:quiet_hours")


# ── 5. retry, backoff, ceiling — through the real worker loop ─────────


def test_a_failing_provider_retries_with_backoff_then_lands_failed_on_the_face(tmp_path, monkeypatch):
    """Ruling 5. The fake is the PROVIDER (``engine.analyze`` returns an
    errored ``IntelResult``), never a status field.  Everything the
    assertions read — attempts, ``requested_at``, ``last_error``, the
    terminal status, and ``list_jobs`` (the face's own data) — is written by
    production code.
    """
    from holdspeak.intel_queue import start_intel_queue_worker

    # A routed plugin chain: the shape a real meeting claim has.  With an
    # EMPTY chain the claim planner re-freezes the descriptor on every claim
    # and resets `attempts` to 0 -- the ceiling is then unreachable.  That is
    # a pre-existing `db/intel.py` defect, reported with HS-200-42 and NOT
    # papered over here; this test asserts the ladder the product must have.
    db, _broker, engine, _host, _requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("decision_capture",), chain=("decision_capture",),
    )
    engine.error = "provider exploded"
    _queued_meeting(db, "m-retry")

    started = datetime.now()
    worker = start_intel_queue_worker(
        None,
        retry_base_seconds=1,
        retry_max_seconds=2,
        retry_max_attempts=2,
        poll_seconds=5.0,
    )
    try:
        def terminal() -> bool:
            jobs = db.intel.list_intel_jobs(status="all")
            return any(j.status == "failed" and int(j.attempts) >= 2 for j in jobs)

        assert _wait(terminal, timeout=60.0, nudge=worker.wake), [
            (j.job_id[:10], j.status, j.attempts) for j in db.intel.list_intel_jobs(status="all")
        ]
    finally:
        worker.stop()

    # The whole row chain, not the head: the ladder lives across rows.
    rows = _rows(db, "intel_jobs")
    ladder = sorted(int(r["attempts"]) for r in rows if r["status"] == "failed")
    assert ladder == [1, 2], rows
    # Backoff: the retry was scheduled into the FUTURE, not re-run immediately.
    successors = [r for r in rows if int(r["attempts"]) == 2]
    assert successors, rows
    assert datetime.fromisoformat(successors[0]["requested_at"]) > started, (
        "the retry did not move requested_at forward"
    )
    assert all(r["last_error"] for r in rows if r["status"] == "failed")
    # The ceiling's own sentence, written by the repository.
    assert any(
        "after 2 attempt(s)" in str(r["last_error"]) for r in rows if r["status"] == "failed"
    ), rows
    # No queued survivor: the ceiling terminalized the chain.
    assert [r for r in rows if r["status"] == "queued"] == []
    # And the FACE's data shows it (the real read model, not the raw row).
    listed = _service(db).list_jobs(OWNER, {"status": "all", "limit": 50})["jobs"]
    failed = [j for j in listed if j["status"] == "failed"]
    assert failed, listed
    assert any(j["attempts"] == 2 for j in failed), failed
    assert all(j["last_error"] for j in failed)
    # Nothing is still scheduled: the chain is terminal, not waiting.
    assert all(j["retry_scheduled"] is False for j in failed), failed
    assert all(j["next_retry_at"] is None for j in failed), failed
    # The retry ledger the face reads is populated too.
    assert any(j["retry_history"] for j in failed), failed
    assert any(
        e["outcome"] == "scheduled_retry"
        for j in failed for e in j["retry_history"]
    ), failed


def test_a_failing_job_with_no_routed_chain_still_reaches_its_ceiling(tmp_path, monkeypatch):
    """The runaway the drainer made reachable — fenced.

    PRE-FIX STATE, measured on this exact rig (``retry_max_attempts=2``,
    empty plugin chain), one line per drain round::

        0 1 [('ij_345bbb','superseded',0), ('ij_68683b','failed',1), ('ij_fa05e7','queued',1)]
        2 1 [... ('ij_fa05e7','superseded',1), ('ij_1d58bc','failed',1), ('ij_6c0b46','queued',1)]
        4 1 [... ('ij_6c0b46','superseded',1), ('ij_b86cc3','failed',1), ('ij_dfa9a3','queued',1)]
        6 1 [... ('ij_dfa9a3','superseded',1), ('ij_784e80','failed',1), ('ij_2c4eaf','queued',1)]

    ``attempts`` never leaves 1, the ceiling is unreachable, a ``queued``
    survivor is always present, and ``intel_jobs`` grows by TWO rows every
    retry — forever, on a 15s hub poll.  The cause was in claim planning
    (``db/intel.py``): ``_frozen_plugin_members`` is falsy whenever the routed
    chain is empty, so every claim superseded a descriptor identical to the
    one it minted and inserted the replacement with ``attempts`` reset to 0.

    Every assertion below fails on that pre-fix tree.
    """
    from holdspeak.intel_queue import start_intel_queue_worker

    # No plugins, no chain: the owner's ordinary meeting.
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    engine.error = "provider exploded"
    _queued_meeting(db, "m-nochain")

    worker = start_intel_queue_worker(
        None,
        retry_base_seconds=1,
        retry_max_seconds=2,
        retry_max_attempts=2,
        poll_seconds=5.0,
    )
    try:
        def terminal() -> bool:
            rows = _rows(db, "intel_jobs")
            return any(
                r["status"] == "failed" and int(r["attempts"]) >= 2 for r in rows
            )

        assert _wait(terminal, timeout=60.0, nudge=worker.wake), [
            (r["job_id"][:9], r["status"], r["attempts"]) for r in _rows(db, "intel_jobs")
        ]
        # The loop must also STOP: give it several more poll-and-wake rounds
        # and the row count must not move.
        settled = len(_rows(db, "intel_jobs"))
        for _ in range(20):
            worker.wake()
            time.sleep(0.1)
        assert len(_rows(db, "intel_jobs")) == settled, _rows(db, "intel_jobs")
    finally:
        worker.stop()

    rows = _rows(db, "intel_jobs")
    # Terminal, with the repository's own ceiling sentence.
    assert any(
        r["status"] == "failed"
        and int(r["attempts"]) == 2
        and "after 2 attempt(s)" in str(r["last_error"])
        for r in rows
    ), rows
    # No queued survivor: nothing is left for the drainer to pick up again.
    assert [r for r in rows if r["status"] == "queued"] == [], rows
    # BOUNDED: with max_attempts=2 the chain is exactly three rows —
    #   1. the pre-C2 stop-handoff row, superseded once by the real freeze,
    #   2. the first bound attempt, failed at attempts=1,
    #   3. its backoff successor, failed at attempts=2 (the ceiling).
    # Pre-fix this grew without limit.
    assert len(rows) == 3, rows
    assert sorted(r["status"] for r in rows) == ["failed", "failed", "superseded"], rows
    assert sorted(int(r["attempts"]) for r in rows if r["status"] == "failed") == [1, 2], rows
    # And the face can show it.
    listed = _service(db).list_jobs(OWNER, {"status": "all", "limit": 50})["jobs"]
    assert any(
        j["status"] == "failed" and j["attempts"] == 2 and j["last_error"] for j in listed
    ), listed


# ── 6. THE FENCE: the real hub lifespan ───────────────────────────────


def _hub(monkeypatch):
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    return MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={"activity": {"state": "idle"}}),
        ),
        host="127.0.0.1",
    )


def test_the_real_hub_lifespan_starts_drains_and_stops_the_intel_drainer(tmp_path, monkeypatch):
    """The fence. No CLI, no ``/api/intel/process``: the lifespan alone.

    (a) the drainer is alive after startup,
    (b) a meeting with a real transcript, enqueued through
        ``request_intel_retry``, reaches an ``intel_snapshots`` row,
    (c) the drainer thread is dead after shutdown.
    """
    from fastapi.testclient import TestClient

    from holdspeak import intel_queue_conductor as conductor

    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    _own(db.db_path)
    state = _queued_meeting(db, "m-fence", text="we agreed to ship on Friday")
    # Settle the stop-handoff row so the only job is the one the face's verb
    # enqueues below.
    db.intel.skip_remaining_intel("m-fence")
    assert db.meetings.get_meeting("m-fence").segments

    server = _hub(monkeypatch)
    with TestClient(server.app):
        # (a) the lifespan started it.
        worker = conductor.current_intel_queue_conductor()
        assert worker is not None and worker.is_alive(), (
            "the hub lifespan started no intel drainer"
        )
        assert conductor.drainer_state() == "running"

        # (b) the real enqueue path, then the drainer alone.
        outcome = db.intel.request_intel_retry("m-fence", reason="Run intelligence")
        assert outcome not in {"missing", "empty", "reserved", "running"}, outcome
        assert db.intel.list_intel_jobs(status="queued"), "nothing was enqueued"
        assert _wait(
            lambda: bool(_rows(db, "intel_snapshots")), timeout=60.0, nudge=worker.wake
        ), "the drainer never produced an intel snapshot"
        assert engine.analyzed, "the provider seam was never reached"
        assert db.intel.list_intel_jobs(status="queued") == []

    # (c) shutdown joined it.
    assert worker.is_alive() is False
    assert conductor.current_intel_queue_conductor() is None
    _ = state


def test_the_fence_trips_on_the_pre_fix_lifespan(tmp_path, monkeypatch):
    """The pre-fix proof for (a).

    The ONLY difference from the test above is that the lifespan's call to
    ``start_intel_queue_conductor`` is replaced with the no-op it effectively
    was before HS-200-42 (the hub started three conductors and not this one).
    The fence's assertion trips: no drainer, no snapshot.
    """
    from fastapi.testclient import TestClient

    from holdspeak import intel_queue_conductor as conductor

    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    _own(db.db_path)
    _queued_meeting(db, "m-prefix", text="we agreed to ship on Friday")

    monkeypatch.setattr(
        conductor, "start_intel_queue_conductor", lambda **kwargs: None
    )

    server = _hub(monkeypatch)
    with TestClient(server.app):
        # Fence assertion (a), verbatim, against the pre-fix lifespan.
        with pytest.raises(AssertionError):
            worker = conductor.current_intel_queue_conductor()
            assert worker is not None and worker.is_alive(), (
                "the hub lifespan started no intel drainer"
            )
        assert conductor.drainer_state() == "absent"
        # The pre-fix verb: it returns `queued` and nothing executes it.
        result = _service(db).run_intelligence(
            OWNER,
            "m-prefix",
            expected_selection_hash=_planned_selection_hash(db, "m-prefix"),
        )
        assert result["state"] == "queued"
        assert result["drainer"] == "absent"
        # Give a drainer that does not exist a generous window to act.
        time.sleep(1.0)
        assert _rows(db, "intel_snapshots") == [], (
            "something drained the queue — the pre-fix proof is not isolating "
            "the conductor"
        )
        assert engine.analyzed == []
        assert db.intel.list_intel_jobs(status="queued"), "the job left the queue"


# ── 7. the finished job reaches the open browser ──────────────────────


def test_a_finished_job_broadcasts_aftercare_ready_and_the_queue_frame(tmp_path, monkeypatch):
    from holdspeak import intel_queue_conductor as conductor

    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    _own(db.db_path)
    _queued_meeting(db, "m-frames")

    frames: list[tuple[str, dict]] = []
    worker = conductor.start_intel_queue_conductor(
        broadcast=lambda t, d: frames.append((t, d))
    )
    assert worker is not None
    assert _wait(lambda: bool(_rows(db, "intel_snapshots")), timeout=30.0, nudge=worker.wake)
    assert _wait(lambda: any(t == "runtime_queue" for t, _ in frames), timeout=10.0)

    kinds = {t for t, _ in frames}
    assert "runtime_queue" in kinds, kinds
    assert "aftercare_ready" in kinds, kinds
    queue_frame = [d for t, d in frames if t == "runtime_queue"][-1]
    assert set(queue_frame) >= {"jobs", "queued", "running", "failed"}
    assert engine.analyzed


# ── counsel P1-1: shutdown custody ────────────────────────────────────


def test_a_stuck_drainer_is_named_in_the_log_before_the_lock_is_released(
    tmp_path, monkeypatch, caplog
):
    """Counsel P1-1(c). The join is bounded, so a stuck drainer must be LOUD.

    The provider is slow (3s inside the drain call) and the join is 1s, so
    ``stop`` returns with the thread still alive.  The warning has to name the
    meeting whose job is in flight and say how it is recovered.
    """
    import logging

    from holdspeak import intel_queue_conductor as conductor
    import holdspeak.intel_queue as intel_queue_module

    db, *_ = _queue_rig(tmp_path, monkeypatch)
    _own(db.db_path)
    _queued_meeting(db, "m-stuck")
    # Put the job in the state a real in-flight drain leaves it in, through
    # the real repository claim.
    assert db.intel.claim_next_intel_job() is not None

    entered = threading.Event()

    def slow_drain(*args, **kwargs):
        entered.set()
        time.sleep(3.0)
        return 0

    monkeypatch.setattr(intel_queue_module, "drain_intel_queue", slow_drain)

    worker = conductor.start_intel_queue_conductor()
    assert worker is not None
    assert entered.wait(10.0), "the drainer never entered the slow provider call"

    with caplog.at_level(logging.WARNING):
        conductor.stop_intel_queue_conductor(timeout=1.0)

    assert worker.is_alive() is True, "the rig did not reproduce a stuck drainer"
    warnings = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    stuck = [m for m in warnings if "did not stop within" in m]
    assert stuck, warnings
    assert "m-stuck" in stuck[0], stuck
    assert "takeover" in stuck[0] or "take_over" in stuck[0], stuck
    # And the conductor really did let go, so the hub can finish shutting down.
    assert conductor.current_intel_queue_conductor() is None
    worker.stop(timeout=10.0)


def test_the_hub_releases_the_database_only_after_the_conductors_are_stopped():
    """Counsel P1-1(b). Source order is the contract; assert it by position."""
    from pathlib import Path as _Path

    root = _Path(__file__).resolve().parents[2] / "holdspeak"
    runtime = (root / "web_runtime.py").read_text(encoding="utf-8")
    # The hub's own order: stop the server (which runs the app shutdown hook
    # and joins the conductors) BEFORE the combined stop-writers-then-release.
    stop_server = runtime.index("self.server.stop()")
    handback = runtime.index("self._stop_writers_and_release_database()")
    assert stop_server < handback, (
        "the database owner lock is released before the server is stopped"
    )
    # And inside that method, the drainer join precedes the release.
    ownership = (root / "runtime" / "ownership.py").read_text(encoding="utf-8")
    body = ownership.split("def _stop_writers_and_release_database", 1)[1].split(
        "def _release_database", 1
    )[0]
    assert body.index("stop_intel_queue_conductor()") < body.index(
        "self._release_database()"
    ), "the owner lock is released before the drainer is joined"


# ── counsel P1-2: the receipt host is the EXECUTION host ──────────────


def _route_host(db, meeting_id: str) -> str:
    from holdspeak.meeting_session.deferred_bound import BoundDeferredIntelJob

    job = db.intel.get_intel_job(meeting_id)
    bound = BoundDeferredIntelJob.reconstruct(db, job)
    return bound.egress_model_host(db, "meeting.deferred_analysis")


def test_the_model_host_is_restated_from_the_route_the_run_actually_takes(
    tmp_path, monkeypatch
):
    """Counsel P1-2, Article III.

    The enqueue-time host comes from ``resolve_meeting_placement(Config)``
    (`intel/providers.py:666`); execution goes through the deployment
    revision frozen into the bundle member's route plan, which is what
    `_engine_for_revision` (`inference_targets.py:721`) builds from.  Those
    are different sources and are NOT guaranteed to agree, so the row must be
    re-stated from the second one before the model call.
    """
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    _queued_meeting(db, "m-host")

    # The enqueue-time estimate, written by the real verb.
    result = _service(db).run_intelligence(
        OWNER,
        "m-host",
        expected_selection_hash=_planned_selection_hash(db, "m-host"),
    )
    estimate = str(result["host"])
    db.intel.set_intel_job_model_host("m-host", "ESTIMATE-FROM-CONFIG")
    assert db.intel.get_intel_job_model_host("m-host") == "ESTIMATE-FROM-CONFIG"

    from holdspeak.intel_queue import drain_intel_queue

    assert drain_intel_queue(max_jobs=2) >= 1
    assert _rows(db, "intel_snapshots"), "the run never reached the provider"

    recorded = db.intel.get_intel_job_model_host("m-host")
    assert recorded and recorded != "ESTIMATE-FROM-CONFIG", (
        "the row still carries the enqueue-time estimate, not the executed route"
    )
    # And it is a value the FROZEN deployment revisions actually carry —
    # not a second guess, and not the config-shaped estimate.
    from holdspeak.intel.providers import endpoint_host

    with db._connection() as conn:
        revisions = [
            dict(r) for r in conn.execute(
                "SELECT node,endpoint,boundary FROM deployment_revisions"
            )
        ]
    candidates: set[str] = set()
    for revision in revisions:
        if revision["node"]:
            candidates.add(str(revision["node"]))
        host = endpoint_host(revision["endpoint"])
        if host:
            candidates.add(host)
        if revision["boundary"]:
            candidates.add(str(revision["boundary"]))
    assert recorded in candidates, (recorded, candidates)
    _ = estimate, engine


def test_the_claim_planner_carries_the_recorded_host_onto_its_replacement_row(
    tmp_path, monkeypatch
):
    """Counsel P1-2, second half: no successor relies on the ancestor fallback."""
    db, *_ = _queue_rig(tmp_path, monkeypatch)
    _queued_meeting(db, "m-carry")
    db.intel.set_intel_job_model_host("m-carry", "walked.example")

    from holdspeak.intel_queue import drain_intel_queue

    drain_intel_queue(max_jobs=2)

    rows = _rows(db, "intel_jobs")
    planned = [r for r in rows if r["origin_job_id"]]
    assert planned, rows
    assert all(r["model_host"] for r in planned), [
        (r["job_id"][:9], r["status"], r["model_host"]) for r in rows
    ]


# ── counsel P1-4: the failure-alert accessor, fenced ──────────────────


def test_the_failure_alert_check_reads_the_real_database_surface(
    tmp_path, monkeypatch, caplog
):
    """Counsel P1-4.

    `_check_failure_alerts` read `get_database().get_intel_queue_summary()`.
    `Database` has never carried that accessor (it is
    `db.intel.get_intel_queue_summary`, `db/intel.py:2260`), so every check
    raised AttributeError into the surrounding `except` — silent while the
    worker had zero callers, an ERROR line every poll once the hub had one.
    """
    import logging

    from holdspeak.intel_queue import start_intel_queue_worker

    db, *_ = _queue_rig(tmp_path, monkeypatch)
    _queued_meeting(db, "m-alert")

    caplog.set_level(logging.DEBUG)
    worker = start_intel_queue_worker(None, poll_seconds=5.0)
    try:
        assert _wait(lambda: worker.iterations >= 1, timeout=30.0, nudge=worker.wake)
        # The check runs against the REAL Database and completes.
        worker._check_failure_alerts()
    finally:
        worker.stop()

    broken = [
        r.getMessage() for r in caplog.records
        if "Deferred intel failure-alert check failed" in r.getMessage()
    ]
    assert broken == [], broken
    # It also reached the REAL summary rather than dying early.
    assert db.intel.get_intel_queue_summary() is not None


# ── counsel P2-5 / P2-9 ───────────────────────────────────────────────


def test_the_already_frozen_guard_holds_under_the_real_router(tmp_path, monkeypatch):
    """Counsel P2-5: no route monkeypatch — the product's own router decides.

    Two claims of the same descriptor must mint no supersede.  With the real
    `preview_route_from_transcript` the chain for this transcript is whatever
    the product says it is; the guard's contract is that a SECOND claim of an
    unchanged row replaces nothing.
    """
    db = Database(tmp_path / "real-router.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *a, **k: db)
    import holdspeak.db as hsdb

    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    from tests.unit.test_meeting_deferred_admission import (
        FakeIntel,
        _assign_deferred_queue_routes,
    )
    from holdspeak.kernel.runtime import _configure

    _assign_deferred_queue_routes(db)
    _configure(db)
    engine = FakeIntel()
    engine.error = "provider exploded"
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    # NOTE: preview_route_from_transcript is deliberately NOT patched.

    _queued_meeting(db, "m-realrouter")

    from holdspeak.intel_queue import drain_intel_queue

    drain_intel_queue(retry_base_seconds=1, retry_max_seconds=2,
                      retry_max_attempts=6, max_jobs=1)
    first = _rows(db, "intel_jobs")
    supersedes_after_first = [
        r for r in first
        if r["status"] == "superseded"
        and "Installed plugin membership frozen" in str(r["last_error"] or "")
    ]
    assert len(supersedes_after_first) <= 1, first

    # The second claim of the successor: the descriptor is unchanged, so the
    # planner must replace nothing.
    assert _wait(lambda: True, timeout=0)
    time.sleep(1.2)
    drain_intel_queue(retry_base_seconds=1, retry_max_seconds=2,
                      retry_max_attempts=6, max_jobs=1)
    second = _rows(db, "intel_jobs")
    supersedes_after_second = [
        r for r in second
        if r["status"] == "superseded"
        and "Installed plugin membership frozen" in str(r["last_error"] or "")
    ]
    assert supersedes_after_second == supersedes_after_first, [
        (r["job_id"][:9], r["status"], str(r["last_error"])[:40]) for r in second
    ]


def test_a_dead_cached_worker_is_replaced_not_returned(tmp_path, monkeypatch):
    """Counsel P2-9: a dead thread is not a drainer."""
    from holdspeak import intel_queue_conductor as conductor

    db, *_ = _queue_rig(tmp_path, monkeypatch)
    _own(db.db_path)

    first = conductor.start_intel_queue_conductor()
    assert first is not None and first.is_alive()
    # Kill it the way an escaped exception would: stop the thread but leave
    # the module's cached reference in place.
    first.stop(timeout=10.0)
    conductor._conductor = first
    assert first.is_alive() is False
    assert conductor.drainer_state() == "absent"

    second = conductor.start_intel_queue_conductor()
    assert second is not None and second is not first
    assert second.is_alive()
    assert conductor.drainer_state() == "running"


# ── counsel N1: the frame carries who will execute the queue ──────────


def test_the_runtime_queue_frame_names_the_drainer(tmp_path, monkeypatch):
    """Counsel N1. "Queued" alone was the true-and-useless sentence.

    The frame the faces already consume (the ambient HUD chip reads it) now
    says whether anything will execute the jobs it counts, so a row can be
    durably honest instead of flashing the click receipt for a second.
    """
    from holdspeak import intel_queue_conductor as conductor
    from holdspeak.intel_queue import build_runtime_queue_frame

    db, *_ = _queue_rig(tmp_path, monkeypatch)
    _queued_meeting(db, "m-frame")

    absent = build_runtime_queue_frame(db)
    assert absent["drainer"] == "absent"
    assert absent["queued"] >= 1, absent

    _own(db.db_path)
    worker = conductor.start_intel_queue_conductor()
    assert worker is not None
    running = build_runtime_queue_frame(db)
    assert running["drainer"] == "running", running

    conductor.stop_intel_queue_conductor()
    assert build_runtime_queue_frame(db)["drainer"] == "absent"
