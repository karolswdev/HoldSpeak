"""PARKED 20261108 (evening): tests of routes parked with the unreached-routes census.

From ``tests/unit/test_web_routes_missioncontrol.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""
class TestRailsRemoteEvents:
    """The cross-machine reach (HS-88-04): a remote node's envelope
    through the real route into the observer's buffer, events-only."""

    def test_remote_envelope_is_accepted_and_buffered(self, tmp_path):
        from holdspeak import rails_observer

        rails_observer.clear_remote_buffer()
        client = _client(_make_map(tmp_path), _runner_for({}))
        res = client.post(
            "/api/missioncontrol/rails/remote-events",
            json={"node": "beta", "ts": "t1", "events": [{"ts": "t1", "event": "story_status", "story": "HS-1"}]},
        )
        assert res.status_code == 200
        assert res.json() == {"accepted": True, "node": "beta", "events": 1}
        drained = rails_observer.drain_remote_events()
        assert drained[0]["origin_node"] == "beta"
        rails_observer.clear_remote_buffer()

    def test_remote_envelope_with_a_file_body_is_refused(self, tmp_path):
        from holdspeak import rails_observer

        rails_observer.clear_remote_buffer()
        client = _client(_make_map(tmp_path), _runner_for({}))
        res = client.post(
            "/api/missioncontrol/rails/remote-events",
            json={"node": "beta", "events": [{"event": "x", "body_markdown": "a story file"}]},
        )
        assert res.status_code == 400
        assert "events only" in res.json()["reason"]
        assert rails_observer.drain_remote_events() == []  # nothing buffered

    def test_remote_envelope_without_a_node_is_refused(self, tmp_path):
        client = _client(_make_map(tmp_path), _runner_for({}))
        res = client.post("/api/missioncontrol/rails/remote-events", json={"events": []})
        assert res.status_code == 400
