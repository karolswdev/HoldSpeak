# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_intel_queue_drain.py to restore.

# ruff: noqa


# --- test_the_fence_trips_on_the_pre_fix_lifespan: P2: patches the product back to its pre-fix shape to prove the test above can fail; tests the test
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
