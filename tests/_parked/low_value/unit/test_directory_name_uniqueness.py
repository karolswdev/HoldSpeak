# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_directory_name_uniqueness.py to restore.

# ruff: noqa


# --- test_to_dict_includes_name_normalized: P6: to_dict has a key
def test_to_dict_includes_name_normalized(db: Database) -> None:
    d = db.directories.upsert(directory_id="d1", name="My Zone")
    assert d.to_dict()["name_normalized"] == "my zone"
