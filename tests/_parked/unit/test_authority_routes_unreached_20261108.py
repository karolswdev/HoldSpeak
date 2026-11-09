"""PARKED 20261108 (evening): tests of routes parked with the unreached-routes census.

From ``tests/unit/test_authority_routes.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""
def test_grants_issue_only_from_fixed_proposal_and_expose_use_receipts(rig) -> None:
    db, client = rig
    proposal = db.actuators.record_proposal(
        meeting_id=None,
        origin="desk",
        window_id="desk:1",
        plugin_id="github",
        plugin_version="1",
        idempotency_key="route-grant",
        target="github",
        action="create_issue",
        preview="Create issue",
        payload={"repo": "acme/app", "title": "Follow up"},
    )
    client.put("/api/authority/control-mode", json={"control_mode": "yolo"})
    yolo = client.post("/api/authority/grants", json={"proposal_id": proposal.id})
    assert yolo.status_code == 409
    assert "captured posture" in yolo.json()["error"]
    client.put("/api/authority/control-mode", json={"control_mode": "Normal"})
    issued = client.post(
        "/api/authority/grants",
        json={
            "proposal_id": proposal.id,
            "actor": "karol",
            "ttl_seconds": 600,
            "max_uses": 2,
        },
    )
    assert issued.status_code == 201, issued.text
    grant = issued.json()["grant"]
    assert grant["project_scope"] == "acme/app"
    assert grant["remaining_uses"] == 2

    db.actuators.consume_grant(grant["id"], operation_id=f"actuator:{proposal.id}")
    uses = client.get(f"/api/authority/grants/{grant['id']}/uses")
    assert uses.status_code == 200
    assert uses.json()["uses"][0]["operation_id"] == f"actuator:{proposal.id}"
    assert (
        client.delete(f"/api/authority/grants/{grant['id']}").json()["state"]
        == "revoked"
    )

    arbitrary = client.post(
        "/api/authority/grants",
        json={"operation": {"family": "external_write", "destination": "new.example"}},
    )
    assert arbitrary.status_code == 404
