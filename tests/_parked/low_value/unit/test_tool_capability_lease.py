# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_tool_capability_lease.py to restore.

# ruff: noqa


# --- test_result_limitation_default_is_false: P1/P3: asserts a dataclass field default is False
def test_result_limitation_default_is_false() -> None:
    result = ToolResultEnvelope("unavailable", None, 0, 0)
    assert result.final_answer_may_name_limitation is False
