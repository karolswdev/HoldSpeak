"""Opening a database builds no in-memory copy of the schema after the first time.

Each ``Database()`` used to build three full in-memory copies of SCHEMA_SQL to
read canonical table DDL (kernel_parent_runs, action_items,
thread_message_parts): about 40 ms each, on every one of the run's thousands of
new test databases and at every hub boot. They are cached per schema text now
(``holdspeak/db/reconcile.py`` ``_canonical_table``).
"""
from __future__ import annotations

import sqlite3

from holdspeak.db import reconcile
from holdspeak.db.core import Database


def test_a_second_database_builds_no_reference_schema(tmp_path, monkeypatch) -> None:
    Database(tmp_path / "first.db")
    Database(tmp_path / "first.db")  # a reopen reads canonical DDL: warms the caches
    built: list[str] = []
    real_connect = sqlite3.connect

    def counting_connect(target, *args, **kwargs):
        if str(target) == ":memory:":
            built.append(str(target))
        return real_connect(target, *args, **kwargs)

    monkeypatch.setattr(reconcile.sqlite3, "connect", counting_connect)
    Database(tmp_path / "second.db")
    Database(tmp_path / "second.db")  # a reopen too
    assert built == [], f"{len(built)} in-memory schema copies built"
