# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_mcp_long_tools.py to restore.

# ruff: noqa


# --- test_tools_whose_overlap_was_not_proved_safe_stay_in_the_ordered_queue: P1: asserts eight literal names are absent from a hand-kept constant dict
def test_tools_whose_overlap_was_not_proved_safe_stay_in_the_ordered_queue() -> None:
    for name in ("project.open_review", "watch.refresh", "reaction.process", "heartbeat.run_now",
                 "concierge.detect", "concierge.probe", "concierge.download", "model_library.download"):
        assert name not in LONG_TOOLS, name
