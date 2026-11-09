# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_runtime_counters.py to restore.

# ruff: noqa


# --- test_initial_snapshot_is_all_zero: P1/P2: a fresh counter dict is zeros, and a wrapper hands back its stub's attribute
def test_initial_snapshot_is_all_zero() -> None:
    assert get_counters() == {
        "model_loads": 0,
        "classify_calls": 0,
        "classify_failures": 0,
        "constrained_retries": 0,
    }


# --- test_wrapper_delegates_backend_attribute: P1/P2: a fresh counter dict is zeros, and a wrapper hands back its stub's attribute
def test_wrapper_delegates_backend_attribute() -> None:
    inner = _StubRuntime()
    rt = CountingRuntime(inner)
    assert rt.backend == "stub"


# --- test_wrapper_delegates_info: P1/P2: a fresh counter dict is zeros, and a wrapper hands back its stub's attribute
def test_wrapper_delegates_info() -> None:
    inner = _StubRuntime()
    rt = CountingRuntime(inner)
    assert rt.info() == {"backend": "stub"}
