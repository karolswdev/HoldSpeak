"""HS-103-04 — endpoint health: an honest circuit breaker, in isolation."""
from __future__ import annotations

from holdspeak.intel.endpoint_health import EndpointHealth


def _clock():
    """A controllable fake clock: call `.tick(seconds)` to advance it."""
    state = {"now": 0.0}

    def now() -> float:
        return state["now"]

    def tick(seconds: float) -> None:
        state["now"] += seconds

    now.tick = tick  # type: ignore[attr-defined]
    return now


def test_a_healthy_endpoint_stays_closed() -> None:
    health = EndpointHealth(failure_threshold=3, cooldown_seconds=10)
    for _ in range(10):
        ok, reason = health.check("ep1")
        assert ok and reason is None
        health.record_success("ep1", latency_ms=5.0)
    snap = health.snapshot()["ep1"]
    assert snap["circuit_open"] is False
    assert snap["consecutive_failures"] == 0
    assert snap["total_calls"] == 10


def test_n_consecutive_failures_opens_the_circuit() -> None:
    health = EndpointHealth(failure_threshold=3, cooldown_seconds=10)
    for _ in range(2):
        ok, _ = health.check("ep1")
        assert ok
        health.record_failure("ep1")
    # Two failures: not yet open.
    assert health.snapshot()["ep1"]["circuit_open"] is False
    ok, _ = health.check("ep1")
    assert ok
    health.record_failure("ep1")  # the third consecutive failure
    assert health.snapshot()["ep1"]["circuit_open"] is True


def test_circuit_open_calls_fail_fast_with_a_named_reason() -> None:
    health = EndpointHealth(failure_threshold=1, cooldown_seconds=30)
    health.record_failure("dead-endpoint")
    ok, reason = health.check("dead-endpoint")
    assert ok is False
    assert reason is not None
    assert "dead-endpoint" in reason
    assert "unreachable" in reason


def test_circuit_recovers_after_cooldown() -> None:
    clock = _clock()
    health = EndpointHealth(failure_threshold=1, cooldown_seconds=10, clock=clock)
    health.record_failure("ep1")
    ok, _ = health.check("ep1")
    assert ok is False
    clock.tick(11)
    ok, reason = health.check("ep1")
    assert ok is True and reason is None
    # A successful probe call clears the failure streak entirely.
    health.record_success("ep1")
    assert health.snapshot()["ep1"]["circuit_open"] is False
    assert health.snapshot()["ep1"]["consecutive_failures"] == 0


def test_a_success_resets_the_consecutive_failure_streak() -> None:
    health = EndpointHealth(failure_threshold=3, cooldown_seconds=10)
    health.record_failure("ep1")
    health.record_failure("ep1")
    health.record_success("ep1")
    health.record_failure("ep1")
    health.record_failure("ep1")
    # Two failures again (post-reset), still under threshold.
    assert health.snapshot()["ep1"]["circuit_open"] is False


def test_snapshot_is_empty_for_a_never_called_endpoint() -> None:
    health = EndpointHealth()
    assert health.snapshot() == {}
    ok, reason = health.check("never-seen")
    assert ok is True and reason is None


def test_endpoints_are_independent() -> None:
    health = EndpointHealth(failure_threshold=1, cooldown_seconds=10)
    health.record_failure("ep-a")
    ok_a, _ = health.check("ep-a")
    ok_b, _ = health.check("ep-b")
    assert ok_a is False
    assert ok_b is True
