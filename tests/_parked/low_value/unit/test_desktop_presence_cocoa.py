# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_desktop_presence_cocoa.py to restore.

# ruff: noqa


# --- test_status_probe_reads_the_existing_connection_lamp: P1: asserts three substrings in a JS string constant
def test_status_probe_reads_the_existing_connection_lamp() -> None:
    assert "presence-activity" in PRESENCE_STATUS_PROBE_JS
    assert "data-on" in PRESENCE_STATUS_PROBE_JS
    assert "available" in PRESENCE_STATUS_PROBE_JS
