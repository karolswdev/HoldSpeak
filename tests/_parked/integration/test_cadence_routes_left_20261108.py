"""PARKED 20261108 (late evening): tests of routes parked in the left-routes pass.

From ``tests/integration/test_cadence_routes.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""


def test_loop_detail_404_then_ok(client):
    c, _ = client
    assert c.get("/api/cadence/loops/nope").status_code == 404
    c.post("/api/cadence/run-now")
    loop_id = c.get("/api/cadence/loops").json()["loops"][0]["id"]
    assert c.get(f"/api/cadence/loops/{loop_id}").json()["id"] == loop_id
