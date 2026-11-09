"""PARKED 20261108 (evening): tests of routes parked with the unreached-routes census.

From ``tests/unit/test_one_dial.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""
def test_profiles_api_reads_retired_writes_still_refused(client, db) -> None:
    """HS-134-02: GET /api/profiles retired; reads go through
    /api/inference-targets; writes still rejected with 405."""
    db.profiles.upsert(
        profile_id="p-1", name="A", kind="openAICompatible",
        base_url="http://h:1/v1", model="m",
    )
    # HS-134-02: read through the target contract.
    targets = client.get("/api/inference-targets").json()["targets"]
    assert any(t["id"] == "p-1" for t in targets)

    for resp in (
        client.post("/api/profiles", json={"name": "B"}),
        client.put("/api/profiles/p-1", json={"name": "B"}),
        client.delete("/api/profiles/p-1"),
    ):
        assert resp.status_code == 405
        assert resp.json()["write_path"] == "/api/inference-targets"
    # Nothing changed.
    assert db.profiles.get("p-1").name == "A"
