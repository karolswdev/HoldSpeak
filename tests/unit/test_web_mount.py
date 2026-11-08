"""The hub's router mounting lives in one runtime module (2026-11-08).

``holdspeak/runtime/web_mount.py`` mounts every router; ``web_server`` calls
it. The move changes no route: the assembled app's routes, in mount order,
equal the list recorded from main before the move
(``tests/fixtures/hub_route_list.json``). Mount order matters for overlapping
paths, so the list is compared in order, not only as a set.
HOLDSPEAK_WIRE_WRITE=1 rewrites the fixture.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="the route list is read from the real app")

REPO = Path(__file__).parents[2]
FIXTURE = REPO / "tests" / "fixtures" / "hub_route_list.json"

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


def test_the_route_list_is_the_one_recorded_from_main(monkeypatch) -> None:
    monkeypatch.setenv("HOLDSPEAK_PHONE", "on")
    rows = _route_list()
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        FIXTURE.write_text("[\n" + ",\n".join(json.dumps(r) for r in rows) + "\n]\n")
    recorded = json.loads(FIXTURE.read_text())
    assert sorted(rows) == sorted(recorded), "a route was added or removed"
    assert rows == recorded, "the mount order changed"
