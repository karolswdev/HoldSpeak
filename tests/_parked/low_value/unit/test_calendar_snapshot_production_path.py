# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_calendar_snapshot_production_path.py to restore.

# ruff: noqa


# --- TestSnapshotUIDDeterminism::test_uid_format_is_hex_at_snapshot_domain: P6: pins the uid's regex shape; same-content/different-content tests carry the dedupe
# (was a method of class TestSnapshotUIDDeterminism)
def test_uid_format_is_hex_at_snapshot_domain(self):
    import re
    from holdspeak.services.calendar_snapshot_service import _snapshot_uid

    event = {
        "title": "Test",
        "starts_at": "2026-08-31T09:00:00Z",
        "ends_at": "2026-08-31T10:00:00Z",
        "location": None,
    }
    uid = _snapshot_uid(event)
    # 16 hex chars + @holdspeak-snapshot
    assert re.match(r"^[0-9a-f]{16}@holdspeak-snapshot$", uid), \
        f"UID format wrong: {uid}"
