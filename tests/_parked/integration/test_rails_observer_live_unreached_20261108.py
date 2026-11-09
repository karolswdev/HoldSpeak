"""PARKED 20261108 (evening): tests of routes parked with the unreached-routes census.

From ``tests/integration/test_rails_observer_live.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""
def test_remote_flip_reaches_the_journal_node_named(tmp_path, monkeypatch):
    """HS-88-04, the two-process flow in one process: a remote node's
    envelope (what its worker would POST after tailing its own dw events)
    reaches the journal through the real route + the observer's merge,
    with the origin node named. No LLM: a fake summarizer."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from holdspeak.db.core import Database, reset_database
    from holdspeak.services.mission_control_service import MissionControlService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.missioncontrol import build_missioncontrol_router

    rails_observer.clear_remote_buffer()
    reset_database()
    db = Database(tmp_path / "hs.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)

    map_path = tmp_path / "map.json"
    map_path.write_text('{"projects": {}, "default": null}')
    app = FastAPI()
    app.include_router(
        build_missioncontrol_router(
            # HS-132-12: the journal route reads through the COMPOSED
            # MissionControlService (`missioncontrol.py:_service`), so the
            # context must carry one bound to this test's database. Composing
            # it here is what the hub does at `_create_app`; leaving it None
            # made the route swallow "not composed" and answer an empty list,
            # which silently un-tested the whole remote-flip path.
            WebContext(
                get_state=lambda: {},
                mission_control_service=MissionControlService(db),
            ),
            map_path=map_path,
        )
    )
    client = TestClient(app)

    # The "remote worker" pushes a real flip it saw on its own rails.
    res = client.post(
        "/api/missioncontrol/rails/remote-events",
        json={
            "node": "walk-remote",
            "ts": "t1",
            "events": [{"ts": "t1", "event": "story_status", "story": "HS-1", "detail": {"to": "done"}}],
        },
    )
    assert res.json()["accepted"] is True

    # One observer tick: drain the remote buffer, summarize, journal.
    fresh = rails_observer.drain_remote_events()
    assert fresh and fresh[0]["origin_node"] == "walk-remote"
    batch = rails_observer.summarize_batch(
        fresh, summarize_fn=lambda s, u: "A remote story flipped to done."
    )
    rails_observer.record_journal_entry(db, batch, title="Rails journal")

    entries = client.get("/api/missioncontrol/rails/journal").json()["entries"]
    assert len(entries) == 1
    assert "@walk-remote" in entries[0]["body_markdown"]  # the origin, named
    rails_observer.clear_remote_buffer()
    reset_database()
