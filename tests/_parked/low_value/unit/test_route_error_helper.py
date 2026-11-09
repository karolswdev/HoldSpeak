# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_route_error_helper.py to restore.

# ruff: noqa


# --- test_error_500_logs_detail_and_exception: P4/P5: pins a log line and re-checks str(KeyError) on the same 500 body path
def test_error_500_logs_detail_and_exception(caplog) -> None:
    logger = logging.getLogger("test.error_500.log")
    with caplog.at_level(logging.ERROR, logger="test.error_500.log"):
        error_500(RuntimeError("nope"), logger, "Failed to run pipeline 42")
    # Reproduces the original `log.error(f"<detail>: {e}")` line exactly.
    assert "Failed to run pipeline 42: nope" in caplog.text


# --- test_error_500_stringifies_the_exception_in_the_body: P4/P5: pins a log line and re-checks str(KeyError) on the same 500 body path
def test_error_500_stringifies_the_exception_in_the_body() -> None:
    resp = error_500(KeyError("missing"), logging.getLogger("test.error_500.body"), "ctx")
    # str(KeyError("missing")) == "'missing'" — same as the old inline str(e).
    assert json.loads(resp.body) == {"error": "'missing'"}
