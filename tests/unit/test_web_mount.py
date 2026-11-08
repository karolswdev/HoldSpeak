"""The hub's router mounting lives in one runtime module (2026-11-08).

``holdspeak/runtime/web_mount.py`` mounts every router; ``web_server`` calls
it. Mount order matters where two routes overlap, so the assembled app is
checked for a route an earlier one shadows.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="the route list is read from the real app")

REPO = Path(__file__).parents[2]

_spec = importlib.util.spec_from_file_location(
    "gen_api_surface_for_mount", REPO / "scripts" / "gen_api_surface.py"
)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)  # type: ignore[union-attr]


def _route_list() -> list[list[str]]:
    rows: list[list[str]] = []
    for route in gen.build_reference_app().routes:
        kind = type(route).__name__
        if kind == "Mount":  # /_built exists only after a web build
            continue
        path = getattr(route, "path", "")
        if kind.endswith("WebSocketRoute"):
            rows.append(["WS", path])
            continue
        methods = sorted((getattr(route, "methods", set()) or set()) - {"HEAD"})
        rows.append([",".join(methods), path])
    return rows


def test_mount_routers_is_the_runtime_mount() -> None:
    from holdspeak.runtime.web_mount import mount_routers

    assert callable(mount_routers)


def test_web_mount_never_imports_web_server() -> None:
    names: set[str] = set()
    for source in (REPO / "holdspeak" / "runtime").glob("web_mount*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
            elif isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
    assert names, "no web_mount module found"
    assert not any(name.endswith("web_server") for name in names), names


def test_no_mounted_route_is_shadowed(monkeypatch) -> None:
    """Mount order matters only where two routes overlap: a route that an
    earlier route of the same method already matches never runs. Derived from
    the assembled app (the recorded list, tests/fixtures/hub_route_list.json,
    is parked: every park changed it, and it proved one refactor, #1900)."""
    monkeypatch.setenv("HOLDSPEAK_PHONE", "on")
    seen: list[tuple[set[str], object, str]] = []
    shadowed: list[str] = []
    for route in gen.build_reference_app().routes:
        kind = type(route).__name__
        if kind == "Mount":
            continue
        methods = {"WS"} if kind.endswith("WebSocketRoute") else set(getattr(route, "methods", set()) or set()) - {"HEAD"}
        path = getattr(route, "path", "")
        if "{" not in path:
            for earlier_methods, regex, earlier_path in seen:
                if methods & earlier_methods and regex.match(path):  # type: ignore[attr-defined]
                    shadowed.append(f"{sorted(methods & earlier_methods)} {path} (behind {earlier_path})")
                    break
        seen.append((methods, route.path_regex, path))  # type: ignore[attr-defined]
    assert len(seen) > 300, "the route walk went dark"
    assert not shadowed, "routes an earlier route shadows:\n  " + "\n  ".join(shadowed)
