# PARKED 2026-11-09 (fences diet, pipe/fences-diet): a COUNT ceiling on UNCHECKED statements, raised by hand.
# Replaced by: nothing (a shape fence); test_every_static_sql_statement_names_real_tables_and_columns stays live.
"""Parked from tests/unit/test_static_sql_matches_schema.py."""
from pathlib import Path


def _fresh(tmp_path):  # the live helpers are in tests/unit/test_static_sql_matches_schema.py
    raise NotImplementedError


def sweep_package(conn):
    raise NotImplementedError


# Statements that cannot be completed statically today. New dynamic SQL makes
# this test fail with the list: make the statement static, or raise the ceiling
# on purpose.
_UNCHECKED_CEILING = 138  # measured 2026-10-04; +1 the time retriever (db/memory.py _time_rows: one read per kind spec, as recent() does); +3 the one-time zoneless-stamp repair (db/zoneless_stamps.py walks every time column by name, 2026-10-05)


def test_unchecked_statements_are_named_counted_and_do_not_grow(tmp_path: Path, capsys) -> None:
    """UNCHECKED is a verdict of its own: listed, counted, held under a ceiling."""
    with _fresh(tmp_path)._connection() as conn:
        result = sweep_package(conn)
    listing = "\n  ".join(result.unchecked)
    with capsys.disabled():
        print(f"\nstatic SQL sweep: {result.passed} passed, {len(result.unchecked)} UNCHECKED")
    assert len(result.unchecked) <= _UNCHECKED_CEILING, (
        f"{len(result.unchecked)} statements are UNCHECKED (ceiling {_UNCHECKED_CEILING}). "
        "Make the new statement static, or raise the ceiling on purpose:\n  " + listing
    )


