"""PARKED 20261108 (evening): tests of routes parked with the unreached-routes census.

From ``tests/unit/test_delivery_node_routes.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""
    def test_explicit_disconnect_projects_offline(self, client, state):
        token = _pair(state)
        _hello(client, token)
        gone = client.post(
            "/api/delivery/node/disconnect",
            json={"name": "studio-mac"},
            headers={"X-HoldSpeak-Node-Token": token},
        )
        assert gone.status_code == 200
        view = client.get("/api/delivery/nodes").json()
        row = next(r for r in view["nodes"] if r["name"] == "studio-mac")
        assert row["status"] == "offline"
        assert row["last_seen"]
