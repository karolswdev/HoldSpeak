# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_people_brief.py to restore.

# ruff: noqa


# --- TestF6GatePin::test_f7_policy_block_present: P1: asserts the response carries a constant policy dict with two literal values
# (was a method of class TestF6GatePin)
def test_f7_policy_block_present(
    self, people_service_mcp: PeopleService,
) -> None:
    """F7: the response carries the policy disclosure block."""
    svc = people_service_mcp
    rel = svc.create_relationship(OWNER, {"display_name": "F7 test"})
    failed, brief = self._call("people.one_on_one.brief", {"relationship_id": rel["id"]})
    assert failed is False
    assert "policy" in brief
    assert brief["policy"]["visibility"] == "shared_intent_only"
    assert brief["policy"]["employment_decisions"] == "prohibited"
