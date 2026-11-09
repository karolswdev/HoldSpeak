# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_philo15_01_summaries_blocker.py to restore.

# ruff: noqa


# --- test_policy_names_the_queue_sources: P1: re-types the built-in route policy's source tuple
def test_policy_names_the_queue_sources() -> None:
    found = builtin_service_route_policy_registry().assignment_sources(
        "meeting-intel-queue", SUMMARY
    )
    assert found == ("meeting-intel-queue@2", ("capability", "group", "global"))
    assert builtin_service_route_policy_registry().assignment_sources(
        "meeting-intel-queue", "ask.answer"
    ) is None
