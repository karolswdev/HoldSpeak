"""Every static SQL statement in ``holdspeak/`` prepares against the real schema.

A statement that names a table or a column that does not exist fails only when
its code path runs. Two such statements shipped: a migrated Ask could not be
cancelled (``inference_operation_request_plans``), and a Room's overdue
commitments always counted 0 (``project_meetings``, hidden by a bare
``except``). This test prepares each statement with ``EXPLAIN`` against a
fresh database, so the fault shows at the file and line where it is written.

Limits: only string constants that start with SELECT / INSERT / UPDATE /
DELETE are read. SQL built with f-strings or ``.format`` is not checked.
"""
from __future__ import annotations

import ast
import re
import sqlite3
from pathlib import Path

from holdspeak.db import Database

ROOT = Path(__file__).resolve().parents[2]
_STATEMENT = re.compile(r"(SELECT|INSERT|UPDATE|DELETE)\s")
_NAMED = re.compile(r"(?<!:):([A-Za-z_]\w*)")

# Files whose SQL targets a different database, with the reason.
_OTHER_DATABASES = {
    "holdspeak/activity_history.py": "the browsers' own history databases",
    "holdspeak/people/store.py": "the encrypted People sidecar store",
    "holdspeak/db/delivery_receipts.py": "the delivery receipt ledger file",
    "holdspeak/db/reconcile.py": "reads and rebuilds tables of older schemas",
    "holdspeak/db/schema.py": "the schema itself",
}
# Names that a statement defines for itself (a CTE the constant is a part of).
_STATEMENT_LOCAL = {"current_jobs"}


def _statements() -> list[tuple[str, int, str]]:
    found = []
    for path in sorted((ROOT / "holdspeak").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if relative in _OTHER_DATABASES:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                sql = node.value.strip()
                if _STATEMENT.match(sql) and "{" not in sql:
                    found.append((relative, node.lineno, sql))
    return found


def _missing(conn: sqlite3.Connection, sql: str) -> str:
    """The "no such table/column" message for ``sql``, or ''."""
    names = set(_NAMED.findall(sql))
    try:
        if names and "?" not in sql:
            conn.execute("EXPLAIN " + sql, {name: None for name in names})
        else:
            conn.execute("EXPLAIN " + sql, [None] * sql.count("?"))
    except sqlite3.Error as exc:
        message = str(exc)
        if message.startswith("no such") and message.rsplit(": ", 1)[-1] not in _STATEMENT_LOCAL:
            return message
    return ""


def test_every_static_sql_statement_names_real_tables_and_columns(tmp_path: Path) -> None:
    statements = _statements()
    assert len(statements) > 1000, "the extraction found too few statements to be the real sweep"
    db = Database(tmp_path / "schema.db")
    with db._connection() as conn:
        offenders = [
            f"{relative}:{line}: {message}"
            for relative, line, sql in statements
            if (message := _missing(conn, sql))
        ]
    assert not offenders, "SQL names a missing table or column:\n  " + "\n  ".join(offenders)


def test_the_sweep_catches_a_missing_table_and_a_missing_column(tmp_path: Path) -> None:
    """The detector itself: the two faults of the Ask cancel query are seen."""
    db = Database(tmp_path / "schema.db")
    with db._connection() as conn:
        assert _missing(conn, "SELECT e.id FROM inference_route_executions e JOIN inference_operation_request_plans o ON o.id=e.operation_plan_id WHERE o.operation_id=?") == "no such table: inference_operation_request_plans"
        assert _missing(conn, "SELECT e.id FROM inference_route_executions e ORDER BY e.created_at") == "no such column: e.created_at"
        assert _missing(conn, "SELECT id FROM meetings WHERE id=?") == ""
