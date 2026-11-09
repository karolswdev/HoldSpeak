"""PARKED 20261108 (late evening): tests of routes parked in the left-routes pass.

From ``tests/unit/test_delivery_terminal_routes.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""



def test_target_issue_and_dead_pane_refusal(rig) -> None:
    issued = _target(rig)
    assert issued["status"] == "issued"
    assert issued["pane_id"] == "%5"
    assert issued["node_id"] == "local"
    gone = rig.client.post(
        "/api/delivery/terminal/targets", json={"ref": "pane:%404"}
    )
    assert gone.status_code == 404
    assert gone.json()["status"] == "pane_gone"


def test_unknown_command_id_receipt_is_404(rig) -> None:
    res = rig.client.get(
        "/api/delivery/terminal/commands/99999999-0000-0000-0000-000000000000"
    )
    assert res.status_code == 404
    assert res.json()["error"] == "unknown_command_id"
