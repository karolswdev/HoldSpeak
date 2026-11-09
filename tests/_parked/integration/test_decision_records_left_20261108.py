"""PARKED 20261108 (late evening): tests of routes parked in the left-routes pass.

From ``tests/integration/test_decision_records.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""


def _reject_fragment(owner, decision_id):
    """Fragment of the mixed authority test: the reject route's 409."""
    illegal = owner.post(f"/api/decisions/{decision_id}/reject")
    assert illegal.status_code == 409
    assert illegal.json()["error"] == "illegal_decision_lifecycle_transition"
