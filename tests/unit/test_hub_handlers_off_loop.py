"""Keep route work off the hub event loop.

The owner: "I open a window and often need to wait 2-3 seconds. Even on local"
(2026-10-28).

The guard walks every Python route under ``holdspeak/web``. A synchronous
route runs in Starlette's threadpool. An async route must await something of
its own; one that does not would hold the loop. The allowlist is empty and
stays empty (checked below).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any

import anyio
import pytest

from holdspeak.runtime import composition

_REPO = Path(__file__).resolve().parents[2]
_WEB = _REPO / "holdspeak" / "web"
_ROUTE_DECORATORS = frozenset({
    "get", "post", "put", "patch", "delete", "head", "options",
    "api_route", "route", "websocket",
})

# The refactor program (2026-10-28) moved every on-the-loop route handler off
# the loop. The list stays EMPTY: a new handler that needs the loop awaits.
ALLOWLIST: dict[str, frozenset[str]] = {}


def _is_route_handler(node: ast.AST) -> bool:
    return (
        isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef))
        and any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr in _ROUTE_DECORATORS
            for decorator in node.decorator_list
        )
    )


def _runs_on_loop(node: ast.AsyncFunctionDef) -> bool:
    """Return whether the route's own body has no async operation.

    Nested definitions, lambdas, and class bodies belong to their own call
    sites. They must not make their enclosing route appear loop-bound.
    """
    class BodyVisitor(ast.NodeVisitor):
        has_async_operation = False

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            return

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            return

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            return

        def visit_Await(self, node: ast.Await) -> None:
            self.has_async_operation = True

        def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
            self.has_async_operation = True

        def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
            self.has_async_operation = True

    visitor = BodyVisitor()
    for statement in node.body:
        visitor.visit(statement)
    return not visitor.has_async_operation


def _route_handlers() -> list[tuple[str, int, str, bool, bool]]:
    handlers: list[tuple[str, int, str, bool, bool]] = []
    for path in sorted(_WEB.rglob("*.py")):
        relative = str(path.relative_to(_REPO / "holdspeak"))
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not _is_route_handler(node):
                continue
            is_async = isinstance(node, ast.AsyncFunctionDef)
            handlers.append((
                relative, node.lineno, node.name, is_async,
                is_async and _runs_on_loop(node),
            ))
    return handlers


def test_route_handlers_are_off_loop_or_allowlisted() -> None:
    offenders = [
        f"{path}:{line} {name}: make it `def`, or await its sync work "
        "through `run_in_threadpool`"
        for path, line, name, is_async, on_loop in _route_handlers()
        if is_async and on_loop and name not in ALLOWLIST.get(path, frozenset())
    ]
    assert not offenders, "route handlers still run on the event loop:\n" + "\n".join(offenders)


def test_allowlist_is_empty() -> None:
    assert ALLOWLIST == {}, "the allowlist is empty: make the handler `def` instead"


def test_route_handler_walk_is_non_vacuous() -> None:
    handlers = _route_handlers()
    assert len(handlers) > 400
    assert any(
        path == "web/routes/people.py"
        and name == "readiness"
        and not is_async
        for path, _line, name, is_async, _on_loop in handlers
    )


# The test boots the real MeetingWebServer so startup runs on its event loop.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_desk_needs_you import _boot  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_hub_raises_starlette_thread_limiter(hub: Any) -> None:
    with hub.client as client:
        tokens = client.portal.call(
            lambda: anyio.to_thread.current_default_thread_limiter().total_tokens
        )
    assert tokens == 64

