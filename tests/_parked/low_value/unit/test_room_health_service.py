# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_room_health_service.py to restore.

# ruff: noqa


# --- TestCreatedAtField::test_gh_watch_fields_includes_created_at: P1: a field name is in a constant string
# (was a method of class TestCreatedAtField)
def test_gh_watch_fields_includes_created_at(self) -> None:
    assert "createdAt" in GH_WATCH_FIELDS
