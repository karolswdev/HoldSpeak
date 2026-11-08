"""No browser test hands an async check to ``page.wait_for_function``.

Playwright does not await an async check: it gets a Promise, takes it as
truthy and returns at once (a check of ``async () => false`` with a 2 s
timeout returned in 17 ms; #1942). Such a wait never waits. Poll the hub
from Python with ``tests/e2e/glass_infra.wait_for_hub`` instead.

Parked files (``tests/e2e/_parked/``) are not collected and are skipped.
"""

from __future__ import annotations

import ast
import re
import warnings
from pathlib import Path

E2E = Path(__file__).resolve().parents[1] / "e2e"
ASYNC_CHECK = re.compile(r"\basync\b\s*(\(|function\b|[A-Za-z_$][\w$]*\s*=>)")


def _literal_text(node: ast.AST) -> str:
    """The literal text of a str or f-string argument ('' for anything else)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(_literal_text(part) for part in node.values)
    return ""


def async_waits(source: str, name: str) -> list[str]:
    """Return ``name:line`` for each ``wait_for_function`` call with an async check."""
    found = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse(source, filename=name)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "wait_for_function"):
            continue
        args = list(node.args) + [kw.value for kw in node.keywords if kw.arg == "expression"]
        if any(ASYNC_CHECK.search(_literal_text(arg).lstrip()) for arg in args[:2]):
            found.append(f"{name}:{node.lineno}")
    return found


def test_the_guard_finds_the_shape() -> None:
    sample = (
        'page.wait_for_function("""async ([id]) => { return false; }""", arg=[1])\n'
        'page.wait_for_function("async token => token")\n'
        'page.wait_for_function(f"async () => {{ return {1}; }}")\n'
        'page.wait_for_function("() => window.ready === true")\n'
        'page.wait_for_function("() => document.fonts.status === \'loaded\'")\n'
    )
    assert async_waits(sample, "sample.py") == ["sample.py:1", "sample.py:2", "sample.py:3"]


def test_no_browser_test_waits_on_an_async_check() -> None:
    found = []
    for path in sorted(E2E.rglob("*.py")):
        if "_parked" in path.relative_to(E2E).parts:
            continue
        found += async_waits(path.read_text(encoding="utf-8"), str(path.relative_to(E2E.parents[1])))
    assert not found, (
        "page.wait_for_function does not await an async check, so these waits return at once; "
        "use glass_infra.wait_for_hub: " + ", ".join(found)
    )
