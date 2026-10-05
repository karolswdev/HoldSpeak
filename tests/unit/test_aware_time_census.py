"""The aware-time census: no stored stamp without a zone.

Every stamp HoldSpeak stores is an aware UTC instant written through
``holdspeak.timestamps`` (``utc_now`` / ``utc_now_iso`` / ``utc_iso``). A local
wall-clock read uses ``local_now()`` (aware) or, for a compare-only read against
naive local values, ``local_wall()``. This ``ast`` walk over ``holdspeak/**``
fails on every form that makes a naive local stamp:

* ``datetime.now()`` with no zone (unless it is ``datetime.now().astimezone()``,
  which is aware);
* ``datetime.utcnow()`` and ``datetime.today()``;
* ``datetime.now`` handed over as a callable (``default_factory=datetime.now``);
* ``time.strftime(fmt)`` with no time tuple (the local wall clock as text);
* ``local_wall().isoformat()`` (the compare-only clock written out).

The allowlist is empty. Add an entry only with a one-line reason.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PRODUCTION = REPO / "holdspeak"

# path relative to the repo -> reason. Empty by design.
ALLOWLIST: dict[str, str] = {}


def _dotted(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _aliases(tree: ast.AST) -> tuple[set[str], set[str]]:
    """Names bound to the ``datetime`` class and to the ``datetime`` module,
    at any scope (``from datetime import datetime as _dt`` included)."""
    classes, modules = {"datetime"}, {"datetime"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "datetime":
            for alias in node.names:
                if alias.name == "datetime":
                    classes.add(alias.asname or "datetime")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "datetime":
                    modules.add(alias.asname or "datetime")
    return classes, modules


def naive_sites(source: str, rel: str) -> list[str]:
    tree = ast.parse(source)
    classes, modules = _aliases(tree)
    nows = {f"{c}.now" for c in classes} | {f"{m}.datetime.now" for m in modules}
    stale = {f"{c}.{verb}" for c in classes for verb in ("utcnow", "today")} | {
        f"{m}.datetime.{verb}" for m in modules for verb in ("utcnow", "today")
    }

    def _is_datetime_now(node: ast.AST) -> bool:
        return _dotted(node) in nows

    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _dotted(node.func)
            if _is_datetime_now(node.func) and not node.args and not node.keywords:
                parent = parents.get(node)
                if isinstance(parent, ast.Attribute) and parent.attr == "astimezone":
                    continue  # datetime.now().astimezone() is aware local
                found.append(f"{rel}:{node.lineno} naive datetime.now()")
            elif name in stale:
                found.append(f"{rel}:{node.lineno} {name}()")
            elif name == "time.strftime" and len(node.args) == 1:
                found.append(f"{rel}:{node.lineno} time.strftime with no time tuple")
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "isoformat"
                and isinstance(node.func.value, ast.Call)
                and _dotted(node.func.value.func) == "local_wall"
            ):
                found.append(f"{rel}:{node.lineno} local_wall().isoformat() stored")
        elif isinstance(node, ast.Attribute) and _is_datetime_now(node):
            parent = parents.get(node)
            if isinstance(parent, ast.Call) and parent.func is node:
                continue  # a call, judged above
            found.append(f"{rel}:{node.lineno} datetime.now passed as a clock")
    return found


def test_no_naive_time_source_in_production() -> None:
    offenders: list[str] = []
    for path in sorted(PRODUCTION.rglob("*.py")):
        rel = str(path.relative_to(REPO))
        if rel in ALLOWLIST:
            continue
        offenders.extend(naive_sites(path.read_text(encoding="utf-8"), rel))
    assert not offenders, (
        "Naive (zoneless) time sources. Store aware UTC through "
        "holdspeak.timestamps (utc_now / utc_now_iso / utc_iso); read the wall "
        "clock with local_now() (or local_wall() for a compare-only read):\n  "
        + "\n  ".join(offenders)
    )


def test_census_sees_every_naive_form() -> None:
    sample = (
        "import time\n"
        "from datetime import datetime\n"
        "a = datetime.now().isoformat()\n"
        "b = datetime.utcnow()\n"
        "c = datetime.today()\n"
        "d = field(default_factory=datetime.now)\n"
        "e = time.strftime('%Y')\n"
        "f = local_wall().isoformat()\n"
        "def g():\n"
        "    from datetime import datetime as _dt\n"
        "    return _dt.now().isoformat()\n"
        "ok1 = datetime.now().astimezone()\n"
        "ok2 = datetime.now(timezone.utc)\n"
        "ok3 = time.strftime('%H', time.gmtime(0))\n"
    )
    lines = sorted(int(site.split(":")[1].split()[0]) for site in naive_sites(sample, "x.py"))
    assert lines == [3, 4, 5, 6, 7, 8, 11]


def test_allowlist_entries_carry_a_reason() -> None:
    for rel, reason in ALLOWLIST.items():
        assert (REPO / rel).exists(), rel
        assert reason.strip(), rel
