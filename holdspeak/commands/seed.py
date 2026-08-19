"""`holdspeak seed` — apply the packaged furnished-desk seed.

Preservation-first by deterministic id: ordinary seeding creates only starter
objects that have never existed. Existing objects and tombstones are left
alone; destructive force-restoration lives behind Reset to seed in Settings.
"""

from __future__ import annotations


def run_seed_command(args) -> int:
    """Handle `holdspeak seed`. Returns a process exit code."""
    from ..db import get_database
    from ..db.seed import SeedError, apply_seed

    try:
        report = apply_seed(get_database())
    except SeedError as exc:
        print(f"Seed failed: {exc}")
        return 1

    print(f"Applied the packaged '{report.manifest}' seed:")
    print(f"  profiles seeded: {report.profiles_seeded}")
    for section, count in sorted(report.applied.items()):
        print(f"  {section}: {count}")
    for field, profile_id in sorted(report.profiles_adopted.items()):
        print(f"  adopted {field}: {profile_id}")
    print(f"  filed: {report.filed}")
    print("Re-running is safe: existing starter objects and deletions stay yours.")
    return 0
