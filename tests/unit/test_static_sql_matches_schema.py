"""Every static SQL statement in ``holdspeak/`` prepares against the real schema.

A statement that names a table or a column that does not exist fails only when
its code path runs. Two such statements shipped: a migrated Ask could not be
cancelled (``inference_operation_request_plans``), and a Room's overdue
commitments always counted 0 (``project_meetings``, hidden by a bare
``except``). This test prepares each statement with ``EXPLAIN`` against a
fresh database, so the fault shows at the file and line where it is written.

How a statement is read
-----------------------
The unit is the COMPLETE string expression, not a fragment. A constant, an
``a + b`` concatenation and an f-string are resolved together, with
module-level and class-level string constants substituted
(``_CURRENT_LINEAGE_CTE + "SELECT ... FROM current_jobs"`` is one statement).

Each statement gets exactly one verdict:

* PASSED: SQLite prepared it.
* OFFENDER: SQLite named a missing table or column. The test fails.
* UNCHECKED: the statement could not be completed statically (a runtime
  value inside it), or SQLite refused it for another reason. It is reported by
  ``file:line`` and counted. It is never counted as passed. The count has a
  ceiling, so new unchecked SQL is a decision and not an accident.

A constant that is only a part of other statements is judged through them.

Exclusions are per class or per function, never per file, each with a reason:
the statement targets a database that is not the hub's.
"""
from __future__ import annotations

import ast
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from holdspeak.db import Database

ROOT = Path(__file__).resolve().parents[2]
_STATEMENT = re.compile(r"\s*(SELECT|INSERT|UPDATE|DELETE|WITH)\s")
_NAMED = re.compile(r"(?<![:\w]):([A-Za-z_]\w*)")
_CONSTANT_NAME = re.compile(r"_*[A-Z][A-Z0-9_]*$")
_MISSING = re.compile(r"^no such (table|column)\b|\bhas no column named\b")

# (file, class or function) whose SQL targets ANOTHER database, with the reason.
_OTHER_DATABASE_SCOPES: dict[tuple[str, str], str] = {
    ("holdspeak/db/delivery_receipts.py", "NodeReceiptLedger"):
        "the node's own receipt ledger file (ledger_meta, command_receipts, target_sequences)",
    ("holdspeak/activity_history.py", "_read_safari_rows"): "Safari's History.db",
    ("holdspeak/activity_history.py", "_read_firefox_rows"): "Firefox's places.sqlite",
    ("holdspeak/people/store.py", "EncryptedPeopleStore"): "the encrypted People sidecar store",
    ("holdspeak/db/memory.py", "_public_match"):
        "an in-memory FTS5 table (:memory:) that runs the search's own matcher on redacted text",
    ("holdspeak/db/reconcile.py", "_rebuild_legacy_intel_queue_tables"):
        "reads the renamed tables of the older schema during the rebuild",
}

# Statements that cannot be completed statically today. New dynamic SQL makes
# this test fail with the list: make the statement static, or raise the ceiling
# on purpose.
_UNCHECKED_CEILING = 135  # measured 2026-10-04; +1 the time retriever (db/memory.py _time_rows: one read per kind spec, as recent() does)


@dataclass
class Sweep:
    passed: int = 0
    offenders: list[str] = field(default_factory=list)
    unchecked: list[str] = field(default_factory=list)


def _is_string_expr(node: ast.AST) -> bool:
    return (
        (isinstance(node, ast.Constant) and isinstance(node.value, str))
        or isinstance(node, ast.JoinedStr)
        or (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add))
    )


class _Module:
    """One source file: its string constants and its complete string expressions."""

    def __init__(self, relative: str, source: str) -> None:
        self.relative = relative
        self.tree = ast.parse(source)
        self.constants: dict[str, str] = {}
        self.used_constants: set[str] = set()
        self.roots: list[tuple[ast.AST, str, str]] = []  # node, scope, assigned name
        for _ in range(3):  # a constant may be built from an earlier one
            self._collect_constants(self.tree)
        self._collect_roots(self.tree, scope="", parent_is_string=False, assigned="")

    def _collect_constants(self, tree: ast.AST) -> None:
        bodies = [tree.body] + [n.body for n in tree.body if isinstance(n, ast.ClassDef)]
        for body in bodies:
            for node in body:
                target = None
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target, value = node.targets[0], node.value
                elif isinstance(node, ast.AnnAssign) and node.value is not None:
                    target, value = node.target, node.value
                # Only NAMES_LIKE_THIS: a lower-case class attribute can be
                # shadowed by a local variable of the same name.
                if isinstance(target, ast.Name) and _CONSTANT_NAME.match(target.id) and _is_string_expr(value):
                    text = self.resolve(value, track=False)
                    if text is not None:
                        self.constants[target.id] = text

    def resolve(self, node: ast.AST, *, track: bool = True) -> str | None:
        """The complete text of a string expression, or None when a part is a runtime value."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name) and node.id in self.constants:
            if track:
                self.used_constants.add(node.id)
            return self.constants[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left, right = self.resolve(node.left, track=track), self.resolve(node.right, track=track)
            return None if left is None or right is None else left + right
        if isinstance(node, ast.JoinedStr):
            parts: list[str] = []
            for value in node.values:
                if isinstance(value, ast.FormattedValue):
                    if value.conversion != -1 or value.format_spec is not None:
                        return None
                    value = value.value
                text = self.resolve(value, track=track)
                if text is None:
                    return None
                parts.append(text)
            return "".join(parts)
        return None

    def static_parts(self, node: ast.AST) -> list[str]:
        """Every static piece of text inside a string expression."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return [node.value]
        if isinstance(node, ast.Name):
            return [self.constants[node.id]] if node.id in self.constants else []
        if isinstance(node, ast.BinOp):
            return self.static_parts(node.left) + self.static_parts(node.right)
        if isinstance(node, ast.JoinedStr):
            return [
                part for value in node.values
                for part in self.static_parts(value.value if isinstance(value, ast.FormattedValue) else value)
            ]
        return []

    def looks_like_sql(self, node: ast.AST) -> bool:
        return any(_STATEMENT.match(part) for part in self.static_parts(node))

    def _collect_roots(self, node: ast.AST, *, scope: str, parent_is_string: bool, assigned: str) -> None:
        if _is_string_expr(node) and not parent_is_string:
            self.roots.append((node, scope, assigned))
            return
        for child in ast.iter_child_nodes(node):
            child_scope = scope
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and not scope:
                child_scope = child.name  # the OUTERMOST class or function
            name = ""
            if isinstance(node, ast.Assign) and child is node.value and len(node.targets) == 1:
                target = node.targets[0]
                name = target.id if isinstance(target, ast.Name) else ""
            self._collect_roots(child, scope=child_scope, parent_is_string=False, assigned=name)


def _prepare(conn: sqlite3.Connection, sql: str) -> str:
    """'' when SQLite prepares ``sql``; otherwise SQLite's message."""
    names = set(_NAMED.findall(sql))
    attempts = ([{name: None for name in names}] if names and "?" not in sql else []) + [[None] * sql.count("?")]
    message = ""
    for parameters in attempts:
        try:
            conn.execute("EXPLAIN " + sql, parameters)
            return ""
        except sqlite3.Error as exc:
            message = str(exc)
            if _MISSING.search(message):
                return message
    return message or "did not prepare"


def sweep_source(conn: sqlite3.Connection, relative: str, source: str, into: Sweep) -> None:
    module = _Module(relative, source)
    verdicts = []
    for node, scope, assigned in module.roots:
        text = module.resolve(node)
        verdicts.append((node, scope, assigned, text))
    for node, scope, assigned, text in verdicts:
        where = f"{relative}:{node.lineno}"
        if (relative, scope) in _OTHER_DATABASE_SCOPES:
            continue
        if text is None:
            if module.looks_like_sql(node):
                into.unchecked.append(f"{where}: a runtime value is part of the statement")
            continue
        if not _STATEMENT.match(text):
            continue
        message = _prepare(conn, text.strip())
        if not message:
            into.passed += 1
        elif assigned and assigned in module.used_constants:
            continue  # a part of other statements: judged through them
        elif _MISSING.search(message):
            into.offenders.append(f"{where}: {message}")
        else:
            into.unchecked.append(f"{where}: {message}")


def sweep_package(conn: sqlite3.Connection) -> Sweep:
    result = Sweep()
    for path in sorted((ROOT / "holdspeak").rglob("*.py")):
        sweep_source(conn, path.relative_to(ROOT).as_posix(), path.read_text(encoding="utf-8"), result)
    return result


class _Fresh:
    """A fresh hub database, opened read-only for the sweep."""

    def __init__(self, tmp_path: Path) -> None:
        self._path = tmp_path / "schema.db"
        Database(self._path)

    def _connection(self):
        import contextlib

        conn = sqlite3.connect(f"file:{self._path}?mode=ro", uri=True)
        return contextlib.closing(conn)


def _fresh(tmp_path: Path) -> _Fresh:
    return _Fresh(tmp_path)


# ------------------------------------------------------------------ the sweep


def test_every_static_sql_statement_names_real_tables_and_columns(tmp_path: Path) -> None:
    with _fresh(tmp_path)._connection() as conn:
        result = sweep_package(conn)
    assert result.passed > 1000, "the extraction found too few statements to be the real sweep"
    assert not result.offenders, "SQL names a missing table or column:\n  " + "\n  ".join(result.offenders)


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


def test_every_exclusion_names_a_scope_that_holds_sql() -> None:
    """An exclusion is a class or a function with SQL in it, never a whole file."""
    for (relative, scope), reason in _OTHER_DATABASE_SCOPES.items():
        module = _Module(relative, (ROOT / relative).read_text(encoding="utf-8"))
        held = [n for n, s, _a in module.roots if s == scope and module.looks_like_sql(n)]
        assert scope and reason and held, f"{relative}::{scope} excludes no SQL statement"


# ------------------------------------------------- the detector, by mutation


def test_mutation_a_missing_table_and_a_missing_column_are_offenders(tmp_path: Path) -> None:
    """The two faults of the Ask cancel query."""
    with _fresh(tmp_path)._connection() as conn:
        assert _prepare(conn, "SELECT e.id FROM inference_route_executions e JOIN inference_operation_request_plans o ON o.id=e.operation_plan_id WHERE o.operation_id=?") == "no such table: inference_operation_request_plans"
        assert _prepare(conn, "SELECT e.id FROM inference_route_executions e ORDER BY e.created_at") == "no such column: e.created_at"
        assert _prepare(conn, "SELECT id FROM meetings WHERE id=?") == ""


def test_mutation_an_insert_into_a_missing_column_is_an_offender(tmp_path: Path) -> None:
    """SQLite words this one differently: "table X has no column named Y"."""
    source = 'def write(conn):\n    conn.execute("INSERT INTO meetings (id, astra_missing_column) VALUES (?, ?)", ("a", "b"))\n'
    result = Sweep()
    with _fresh(tmp_path)._connection() as conn:
        sweep_source(conn, "holdspeak/mutant.py", source, result)
    assert result.offenders == ["holdspeak/mutant.py:2: table meetings has no column named astra_missing_column"]
    assert result.passed == 0


def test_mutation_the_hub_delivery_repository_is_checked_and_the_node_ledger_is_not(tmp_path: Path) -> None:
    """The exclusion is the node ledger class, not the file that also holds the hub's repository."""
    relative = "holdspeak/db/delivery_receipts.py"
    source = (ROOT / relative).read_text(encoding="utf-8")
    start = source.index("class DeliveryCommandReceiptRepository")
    assert "command_id" in source[start:]
    mutant = source[:start] + source[start:].replace("command_id", "astra_missing_id")
    clean, mutated = Sweep(), Sweep()
    with _fresh(tmp_path)._connection() as conn:
        sweep_source(conn, relative, source, clean)
        sweep_source(conn, relative, mutant, mutated)
    assert clean.passed > 0 and not clean.offenders, clean
    assert mutated.offenders and all("astra_missing_id" in line for line in mutated.offenders), mutated


def test_mutation_a_bad_column_inside_a_cte_statement_is_an_offender(tmp_path: Path) -> None:
    """The complete WITH ... query is prepared: the CTE name hides nothing."""
    relative = "holdspeak/db/intel.py"
    source = (ROOT / relative).read_text(encoding="utf-8")
    marker = 'query = _CURRENT_LINEAGE_CTE + """\n                    SELECT j.*,m.title AS meeting_title'
    assert source.count(marker) == 1
    mutant = source.replace(marker, marker.replace("m.title", "m.astra_missing_title"))
    clean, mutated = Sweep(), Sweep()
    with _fresh(tmp_path)._connection() as conn:
        sweep_source(conn, relative, source, clean)
        sweep_source(conn, relative, mutant, mutated)
    assert not clean.offenders, clean.offenders
    assert len(mutated.offenders) == 1 and "no such column: m.astra_missing_title" in mutated.offenders[0], mutated.offenders
    assert mutated.passed == clean.passed - 1


def test_mutation_a_fragment_that_cannot_be_completed_is_unchecked_not_passed(tmp_path: Path) -> None:
    source = (
        "def read(conn, prefix):\n"
        '    return conn.execute(prefix() + "SELECT m.astra_missing FROM current_jobs j").fetchall()\n'
        "def named(conn, table):\n"
        '    return conn.execute(f"SELECT id FROM {table} WHERE id=?").fetchall()\n'
        "def tail(conn):\n"
        '    return conn.execute("SELECT * FROM current_jobs WHERE current_rank=1").fetchall()\n'
    )
    result = Sweep()
    with _fresh(tmp_path)._connection() as conn:
        sweep_source(conn, "holdspeak/mutant.py", source, result)
    assert result.passed == 0
    # A runtime value is part of the first two: UNCHECKED. The bare tail names a CTE
    # that nothing defines for it: an OFFENDER, not a pass.
    assert result.unchecked == [
        "holdspeak/mutant.py:2: a runtime value is part of the statement",
        "holdspeak/mutant.py:4: a runtime value is part of the statement",
    ]
    assert result.offenders == ["holdspeak/mutant.py:6: no such table: current_jobs"]
