"""HS-159-02: No-third-door fence for connector_watches writes.

This inventory test asserts that every runtime write path to
connector_watches flows through WatchService or the pinned
ReactionService methods.  No other module in holdspeak/ may INSERT,
UPDATE, or DELETE from connector_watches at runtime.

The sanctioned modules are:
1. holdspeak/db/automations.py -- the repository layer (persistence
   primitives only, never called from outside the two sanctioned
   services except for reads).
2. holdspeak/services/watch_service.py -- the universal facade.
3. holdspeak/services/reaction_service.py -- legacy compatibility path,
   pinned by the 31 legacy compat tests.

HOW A MODULE JOINS THIS LIST: add its repo-relative path to
SANCTIONED_WRITERS below and document the reason.  The fence then
protects the boundary by failing on any un-sanctioned write.

Design: grep-style source scan (same pattern as the REF-001 fence in
tests/unit/test_project_refs.py).  Scans every .py file under
holdspeak/ for SQL write operations on connector_watches, excluding
the sanctioned modules and non-runtime files (schema, reconcile,
migrations, tests).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


# Modules that are allowed to contain SQL writes to connector_watches.
# ReactionService is a sanctioned APPLICATION-LEVEL writer (it calls
# repo methods in automations.py) but does not contain raw SQL writes
# to the table, so it is not listed here.  The two-tier boundary:
#   SQL tier: automations.py + watch_service.py (listed below)
#   Service tier: WatchService + ReactionService (pinned by 31 tests)
SANCTIONED_WRITERS: list[str] = [
    "holdspeak/db/automations.py",       # Persistence primitives (the repo)
    "holdspeak/services/watch_service.py",   # Universal facade (HS-159-02)
]

# Non-runtime files excluded from scanning (schema definitions,
# reconcile logic, and test fixtures are not runtime write paths).
EXCLUDED_PATTERNS: list[str] = [
    "holdspeak/db/schema.py",
    "holdspeak/db/reconcile.py",
    "holdspeak/db/migrations/",
    "tests/",
]

# Patterns that indicate a runtime write to connector_watches.
# These catch INSERT, UPDATE, DELETE targeting the table.
_WRITE_PATTERNS: list[re.Pattern[str]] = [
    # INSERT INTO connector_watches
    re.compile(r'(?i)INSERT\s+(?:OR\s+\w+\s+)?INTO\s+connector_watches\b'),
    # UPDATE connector_watches
    re.compile(r'(?i)UPDATE\s+connector_watches\b'),
    # DELETE FROM connector_watches
    re.compile(r'(?i)DELETE\s+FROM\s+connector_watches\b'),
]


def test_no_third_door_connector_watches_writes() -> None:
    """Every runtime write to connector_watches flows through sanctioned modules.

    If this test fails, either:
    1. The new write belongs inside WatchService or ReactionService and
       should be moved there.
    2. The module has a legitimate reason to write to connector_watches
       and should be added to SANCTIONED_WRITERS with a documented reason.
    """
    repo_root = Path(__file__).resolve().parents[2]
    holdspeak_dir = repo_root / "holdspeak"
    violations: list[str] = []

    # Normalize sanctioned/excluded to repo-relative posix paths.
    sanctioned_set = {Path(p).as_posix() for p in SANCTIONED_WRITERS}
    excluded_prefixes = [Path(p).as_posix() for p in EXCLUDED_PATTERNS]

    for py_file in sorted(holdspeak_dir.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        rel = py_file.relative_to(repo_root).as_posix()

        # Skip sanctioned modules.
        if rel in sanctioned_set:
            continue

        # Skip non-runtime files.
        if any(rel.startswith(prefix) for prefix in excluded_prefixes):
            continue

        try:
            source = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for lineno, line in enumerate(source.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pattern in _WRITE_PATTERNS:
                if pattern.search(line):
                    violations.append(f"{rel}:{lineno}: {stripped}")

    assert not violations, (
        "Unsanctioned writes to connector_watches detected.  "
        "All runtime writes must flow through WatchService or "
        "ReactionService (sanctioned in SANCTIONED_WRITERS):\n"
        + "\n".join(f"  {v}" for v in violations)
    )


def test_sanctioned_modules_exist() -> None:
    """Every sanctioned module must exist in the repo."""
    repo_root = Path(__file__).resolve().parents[2]
    for module_path in SANCTIONED_WRITERS:
        full_path = repo_root / module_path
        assert full_path.exists(), (
            f"Sanctioned module {module_path} does not exist"
        )


def test_at_least_one_write_in_each_sanctioned_module() -> None:
    """Each sanctioned module actually writes to connector_watches.

    Prevents stale entries in SANCTIONED_WRITERS -- if a module no
    longer writes, it should be removed from the list.
    """
    repo_root = Path(__file__).resolve().parents[2]
    for module_path in SANCTIONED_WRITERS:
        full_path = repo_root / module_path
        source = full_path.read_text(encoding="utf-8")
        has_write = any(
            pattern.search(source)
            for pattern in _WRITE_PATTERNS
        )
        assert has_write, (
            f"Sanctioned module {module_path} has no writes to "
            f"connector_watches -- remove it from SANCTIONED_WRITERS"
        )
