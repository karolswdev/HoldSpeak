"""holdspeak/db/schema/ is one SCHEMA_SQL cut into domain modules.

The package joins its parts in execution order. These tests hold that join
honest: every part is whole statements, running the parts one by one builds
the same database as running SCHEMA_SQL, and the importers see one object.
The last test is the pure-move proof of the split (2026-11-08): SCHEMA_SQL is
byte for byte the text of the single schema.py at the split's base commit, and
a fresh database built from either has the same sqlite_master in the same
order. It skips when that commit is not in the clone, and after a later commit
edits the package (the proof is then history).
"""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest

import holdspeak.db as db_pkg
import holdspeak.db.core as db_core
import holdspeak.db.reconcile as db_reconcile
from holdspeak.db import schema

REPO = Path(__file__).resolve().parents[2]
SPLIT_BASE = "cbb0f06bb"  # origin/main when schema.py became a package


def _master(scripts: list[str]) -> list[tuple]:
    conn = sqlite3.connect(":memory:")
    try:
        for script in scripts:
            conn.executescript(script)
        return conn.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY rowid"
        ).fetchall()
    finally:
        conn.close()


def test_schema_sql_is_the_parts_in_order() -> None:
    assert schema.SCHEMA_SQL == "".join(part.SQL for part in schema.PARTS)
    names = [part.__name__.rsplit(".", 1)[1] for part in schema.PARTS]
    modules = sorted(p.stem for p in (REPO / "holdspeak/db/schema").glob("*.py") if p.stem != "__init__")
    assert sorted(names) == modules, "every schema module is one part, used once"


def test_importers_see_one_object() -> None:
    assert db_pkg.SCHEMA_SQL is schema.SCHEMA_SQL
    assert db_core.SCHEMA_SQL is schema.SCHEMA_SQL
    assert db_reconcile.SCHEMA_SQL is schema.SCHEMA_SQL
    assert db_pkg.SCHEMA_VERSION == db_core.SCHEMA_VERSION == schema.SCHEMA_VERSION


@pytest.mark.parametrize("part", schema.PARTS, ids=lambda p: p.__name__.rsplit(".", 1)[1])
def test_each_part_is_whole_statements(part) -> None:
    assert sqlite3.complete_statement(part.SQL), "a statement crosses a module boundary"


def test_parts_one_by_one_build_the_same_database() -> None:
    assert _master([part.SQL for part in schema.PARTS]) == _master([schema.SCHEMA_SQL])


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=False)


def test_split_is_a_pure_move() -> None:
    old = _git("show", f"{SPLIT_BASE}:holdspeak/db/schema.py")
    if old.returncode != 0:
        pytest.skip(f"split base {SPLIT_BASE} is not in this clone")
    edits = _git("rev-list", "--count", "HEAD", "--", "holdspeak/db/schema/")
    if edits.returncode != 0 or int(edits.stdout.strip() or 0) > 1:
        pytest.skip("a later commit edited the schema package; the proof stands at the split")
    namespace: dict = {}
    exec(compile(old.stdout, "schema.py@split-base", "exec"), namespace)
    assert schema.SCHEMA_SQL == namespace["SCHEMA_SQL"]
    assert schema.SCHEMA_VERSION == namespace["SCHEMA_VERSION"]
    assert _master([schema.SCHEMA_SQL]) == _master([namespace["SCHEMA_SQL"]])
