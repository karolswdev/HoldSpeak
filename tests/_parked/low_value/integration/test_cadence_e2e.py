# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/integration/test_cadence_e2e.py to restore.

# ruff: noqa


# --- test_audit_is_local_and_serializable: P4/P6: asserts json.dumps works and a label contains 'nothing leaves'; the egress scope is already checked in test_full_chief_of_staff_flow
def test_audit_is_local_and_serializable(db):
    import json

    CadenceService(db, CadenceConfig()).tick(NOON)
    audit = export_audit(db, now=NOON)
    # round-trips as JSON (no non-serializable objects) and never claims off-machine egress
    dumped = json.loads(json.dumps(audit))
    assert dumped["egress"]["scope"] == "local"
    assert "nothing leaves" in dumped["egress"]["label"].lower()
