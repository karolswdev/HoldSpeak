"""Retired schema has neither a live producer nor a live consumer."""
from __future__ import annotations

import re

from holdspeak.db.schema import RETIRED_TABLES
from tests._tree import ROOT, python_files, text_of


def _references(source: str, tables: frozenset[str]) -> set[str]:
    return set(re.findall(r"\b\w+\b", source.lower())) & tables


def _writers(source: str, tables: frozenset[str]) -> set[str]:
    return set(re.findall(
        r'\b(?:INSERT\s+(?:OR\s+\w+\s+)?INTO|REPLACE\s+INTO|UPDATE|DELETE\s+FROM)\s+["`\[]?(\w+)',
        source.lower(), re.IGNORECASE,
    )) & tables


def test_no_live_module_names_an_unwritten_retired_table() -> None:
    assert RETIRED_TABLES, "The schema must declare its retired history"
    sources = {
        str(path.relative_to(ROOT)): text_of(path)
        for path in python_files(exclude=("_parked",))
        if not path.is_relative_to(ROOT / "holdspeak/db/schema")
    }
    writers = set().union(*(_writers(source, RETIRED_TABLES) for source in sources.values()))
    assert not writers, f"Retired tables still have live writers: {sorted(writers)}"
    unwritten = RETIRED_TABLES - writers
    readers = {path: sorted(refs) for path, source in sources.items()
               if (refs := _references(source, unwritten))}
    assert not readers, f"Live modules still name unwritten tables: {readers}"


def test_census_finds_sql_writers_and_name_only_consumers() -> None:
    tables = frozenset({"history_rows"})
    for sql in ('INSERT INTO history_rows VALUES (?)',
                'INSERT OR IGNORE INTO "history_rows" VALUES (?)',
                'UPDATE HISTORY_ROWS SET value=?', 'DELETE FROM history_rows',
                'REPLACE INTO history_rows VALUES (?)'):
        assert _writers(sql, tables) == tables
    assert _references('forbidden = {"history_rows"}', tables) == tables
    assert not _references('history_rows_missing', tables)


def test_retired_history_is_not_imported_from_a_sync_peer(tmp_path) -> None:
    from holdspeak.db import Database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.sync_service import SyncService

    db = Database(tmp_path / "history.db")
    owner = Principal(PrincipalKind.OWNER, "sync-history-owner")
    sync = SyncService(db)
    payload = sync.pull(owner)
    for table in RETIRED_TABLES:
        payload[table] = [{"forged": True}]
    result = sync.push(owner, payload)
    assert result["success"]
    assert not RETIRED_TABLES.intersection(result["received"])
    with db._connection() as conn:
        for table in RETIRED_TABLES:
            assert not conn.execute(f'SELECT * FROM "{table}"').fetchall()
