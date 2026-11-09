"""PARKED 20261108 (late evening): tests of routes parked in the left-routes pass.

From ``tests/unit/test_scheduled_recording_routes.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""


    def test_get(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Weekly",
            "cron_expr": "0 10 * * 1",
        })
        schedule_id = resp.json()["schedule"]["id"]

        resp = client.get(f"/api/scheduled-recordings/{schedule_id}")
        assert resp.status_code == 200
        assert resp.json()["schedule"]["title"] == "Weekly"

    def test_get_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/scheduled-recordings/sr_nonexistent")
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert body["code"] == "not_found"
