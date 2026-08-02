"""`holdspeak seed` — apply the packaged architect's-desk seed (HS-112-03).

Idempotent by deterministic id: running it twice leaves one desk. It only
ever adds/updates the seed's own `hs-desk-*` objects; nothing else on the
desk is touched (reset lives in the app's Prefs, behind its own confirm).
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
    for section, count in sorted(report.applied.items()):
        print(f"  {section}: {count}")
    print(f"  filed: {report.filed}")
    print("Re-running is safe: the seed upserts by id, never duplicates.")
    return 0
