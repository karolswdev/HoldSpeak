# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_fault_plane.py to restore.

# ruff: noqa


# --- test_census_each_fault_point_locks_to_its_declared_site: P8: scans the tree's source text so each fault name appears in one module
def test_census_each_fault_point_locks_to_its_declared_site():
    """Every fault point is referenced by exactly its one declared module."""
    py_files = [
        p for p in (REPO_ROOT / "holdspeak").rglob("*.py")
        if p.relative_to(REPO_ROOT).as_posix() != "holdspeak/faults.py"
    ]
    contents = {p: p.read_text(encoding="utf-8") for p in py_files}
    import re

    for point, declared in FAULT_POINTS.items():
        # The injection call, not any string equal to the point's name: an
        # operation may share a name with a fault point (PHILO-17: the
        # `meeting.transcribe` operation is not the transcribe-loop fault).
        needle = (
            re.compile(r"faulted_plugin_keys") if point == PLUGIN_FAULT_PREFIX
            else re.compile(r'_fault_(?:trip|kill)\(\s*"' + re.escape(point) + '"')
        )
        hits = {
            p.relative_to(REPO_ROOT).as_posix()
            for p, text in contents.items()
            if needle.search(text)
        }
        assert hits == {declared}, (
            f"fault point {point!r} must inject only at {declared}, found {sorted(hits)}"
        )
    # And nothing outside the declared sites imports the plane's triggers.
    trigger_users = {
        p.relative_to(REPO_ROOT).as_posix()
        for p, text in contents.items()
        if "from .faults import" in text or "from ..faults import" in text
    }
    assert trigger_users == set(FAULT_POINTS.values())
