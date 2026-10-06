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
* ``local_wall().isoformat()`` (the compare-only clock written out);
* ``x.isoformat()`` where ``x`` is a naive wall time in the same function
  (from ``local_wall()``, ``parse_wall()``, ``.replace(tzinfo=None)``, a
  ``datetime(...)``/``datetime.combine(...)`` with no zone, or arithmetic on
  one of those): a naive clock serialised as a zoneless stamp.

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
    found.extend(_serialised_naive(tree, rel, classes))
    return list(dict.fromkeys(found))


#: Calls that give a NAIVE local wall time (compare-only values).
_NAIVE_CALLS = frozenset({"local_wall", "parse_wall", "naive_local"})


def _is_naive_source(node: ast.AST, naive: set[str], classes: set[str]) -> bool:
    """True when *node* evaluates to a naive datetime by its own shape."""
    if isinstance(node, ast.Name):
        return node.id in naive
    if isinstance(node, ast.BoolOp):  # ``now or local_wall()``
        return any(_is_naive_source(value, naive, classes) for value in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
        return _is_naive_source(node.left, naive, classes)
    if not isinstance(node, ast.Call):
        return False
    name = _dotted(node.func)
    keywords = {kw.arg for kw in node.keywords}
    if name.rsplit(".", 1)[-1] in _NAIVE_CALLS:
        return True
    if isinstance(node.func, ast.Attribute) and node.func.attr == "replace":
        if "tzinfo" in keywords:
            tz = next(kw.value for kw in node.keywords if kw.arg == "tzinfo")
            return isinstance(tz, ast.Constant) and tz.value is None
        return _is_naive_source(node.func.value, naive, classes)
    constructors = {f"{c}" for c in classes} | {f"{c}.combine" for c in classes} | {
        "datetime.datetime", "datetime.datetime.combine"}
    if name in constructors and "tzinfo" not in keywords:
        positional_tz = 8 if not name.endswith("combine") else 3
        return len(node.args) < positional_tz
    return False


def _serialised_naive(tree: ast.AST, rel: str, classes: set[str]) -> list[str]:
    """``x.isoformat()`` where ``x`` is a naive wall time in the same function:
    a naive clock written out as a zoneless stamp (Astra, #872)."""
    found: list[str] = []
    scopes = [tree] + [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    for scope in scopes:
        naive: set[str] = set()
        body = scope.body if hasattr(scope, "body") else []
        for node in _walk_in_order(body):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if _is_naive_source(node.value, naive, classes):
                            naive.add(target.id)
                        else:
                            naive.discard(target.id)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "isoformat"
                and _is_naive_source(node.func.value, naive, classes)
                and not (isinstance(node.func.value, ast.Call)
                         and _dotted(node.func.value.func) == "local_wall")
            ):
                found.append(f"{rel}:{node.lineno} a naive wall time serialised with isoformat()")
    return found


def _walk_in_order(body: list[ast.stmt]):
    """Nodes of *body* in source order, not entering nested functions."""
    stack = list(reversed(body))
    while stack:
        node = stack.pop()
        yield node
        children = [
            child for child in ast.iter_child_nodes(node)
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef))
        ]
        # An assignment's value is read before its target is bound.
        if isinstance(node, ast.Assign):
            children = [node.value] + [c for c in children if c is not node.value]
        stack.extend(reversed(children))


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
        "def h(now=None):\n"
        "    end = now or local_wall()\n"
        "    start = end - timedelta(days=1)\n"
        "    day = datetime.combine(end.date(), time_of_day)\n"
        "    gone = parse_wall(row).replace(hour=0)\n"
        "    a = start.isoformat()\n"
        "    b = day.isoformat()\n"
        "    return a, b, gone.isoformat()\n"
        "def k(stamp):\n"
        "    ok4 = utc_iso(local_wall())\n"
        "    ok5 = datetime.combine(d, t, tzinfo=timezone.utc).isoformat()\n"
        "    return ok4, ok5, aware(stamp).isoformat()\n"
    )
    sites = naive_sites(sample, "x.py")
    lines = sorted(int(site.split(":")[1].split()[0]) for site in sites)
    assert lines == [3, 4, 5, 6, 7, 8, 11, 20, 21, 22], sites


def test_allowlist_entries_carry_a_reason() -> None:
    for rel, reason in ALLOWLIST.items():
        assert (REPO / rel).exists(), rel
        assert reason.strip(), rel
