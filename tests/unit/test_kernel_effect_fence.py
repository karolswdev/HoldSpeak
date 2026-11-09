"""The kernel's effect boundaries (HS-106-03, reduced 2026-11-09 by the fences diet).

Each test names a transport and the one module that may reach it. A second
caller is a new door around admission, and this file fails on it.

Parked in ``tests/_parked/fences/test_kernel_effect_fence.py``: the effect
census (a hand-kept entry per effect site), the broker line budgets and the
driver-conditional debt ratchet. Those were shape, not behaviour.
"""

from __future__ import annotations

import ast

from tests import _tree

_SKIP_DIRS = (
    ".mypy_cache",
    ".pytest_cache",
    "_parked",  # parked code is kept, never imported (never delete; park)
    "assets",
    "generated",
    "static",
    "vendor",
    "vendored",
)


def _sources() -> list[tuple[str, ast.Module, list[ast.AST]]]:
    out = []
    for path in _tree.python_files("holdspeak", exclude=_SKIP_DIRS):
        out.append((path.relative_to(_tree.ROOT).as_posix(), _tree.ast_of(path), _tree.walk(path)))
    return out


def _dotted_expr(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_expr(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return f"{_dotted_expr(node.func)}()"
    return ""


def test_lan_transports_are_only_referenced_by_the_scan_sender() -> None:
    """The LAN probe helpers have no caller outside the discovery module."""
    helpers = {"_execute_scan", "_probe_endpoint", "_lan_http_get"}
    referencing: set[str] = set()
    for relative, _tree_module, nodes in _sources():
        for node in nodes:
            if (
                (isinstance(node, ast.Name) and node.id in helpers)
                or (isinstance(node, ast.Attribute) and node.attr in helpers)
                or (isinstance(node, ast.ImportFrom) and any(a.name in helpers for a in node.names))
            ):
                referencing.add(relative)
    assert referencing == {"holdspeak/services/lan_engine_discovery.py"}


def test_terminal_transports_have_only_the_admitted_command_executor_as_caller() -> None:
    verbs = {"deliver", "deliver_keys", "resize_pane"}
    callers: set[str] = set()
    for relative, _module, nodes in _sources():
        module_aliases = {"coder_steering"}
        function_aliases: set[str] = set()
        for node in nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.endswith("coder_steering"):
                        module_aliases.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                if str(node.module or "").endswith("coder_steering"):
                    function_aliases |= {a.asname or a.name for a in node.names if a.name in verbs}
                module_aliases |= {a.asname or a.name for a in node.names if a.name == "coder_steering"}
        for node in nodes:
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id in function_aliases:
                callers.add(relative)
            elif isinstance(node.func, ast.Attribute) and node.func.attr in verbs:
                base = _dotted_expr(node.func.value)
                if base in module_aliases or base.endswith(".coder_steering"):
                    callers.add(relative)
    assert callers == {"holdspeak/delivery/commands.py"}


def test_delivery_command_adapters_cannot_bypass_process_admission() -> None:
    """Only the hub command service submits a native process input or resize."""
    private = {"_submit_native", "_submit_process_input", "_submit_process_resize"}
    callers = {
        relative
        for relative, _module, nodes in _sources()
        for node in nodes
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in private
    }
    assert callers == {"holdspeak/delivery/commands.py"}


def test_raw_desktop_module_is_reachable_only_from_warrant_server() -> None:
    importers = set()
    for path in _tree.python_files("holdspeak", exclude=_SKIP_DIRS):
        relative = path.relative_to(_tree.ROOT).as_posix()
        source = _tree.text_of(path)
        if "privileged_effects.desktop_driver" in source or (
            relative == "holdspeak/privileged_effects/desktop_executor.py"
            and "from .desktop_driver import" in source
        ):
            importers.add(relative)
    assert importers == {"holdspeak/privileged_effects/desktop_executor.py"}

    proxy = _tree.text_of("holdspeak/typer.py")
    for ambient_name in ("pyperclip", "pynput", "Controller", "osascript"):
        assert ambient_name not in proxy
