# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_phone_push.py to restore.

# ruff: noqa


# --- test_h2_is_installed_and_apns_says_ready: P3: checks the h2 package is installed
def test_h2_is_installed_and_apns_says_ready() -> None:
    assert http2_ready() is True
    assert ApnsPush(_key()).push_state() == PUSH_READY
