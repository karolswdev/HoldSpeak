"""HS-150-07 — the orphan-component guard (orchestrator-authored).

The class this kills: BriefLane shipped in 135, was silently dropped
from the lane registry by 144's front-door rebuild, and sat green in
jsdom but unmounted for six phases; FollowThroughLane rotted the same
way. A surface component that no live code imports is a lie waiting
to be edited. Every non-test component under the chair's lanes and
the pullout views must be imported (ES `from ".../<Stem>"` form) by
at least one non-test source file.

Scope is deliberate: the two directories where the class has bitten.
Widening it is a ruling, not a refactor.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WEB_SRC = REPO / "web" / "src"

SURFACE_DIRS = (
    WEB_SRC / "desk" / "chair" / "lanes",
    WEB_SRC / "desk" / "pullouts" / "views",
)

# Barrel/registry files count as live importers only if they are
# themselves imported; both current barrels (lanes/index.ts) are, so a
# one-level check is honest today. If a barrel ever orphans, its OWN
# components stop being reachable and this guard must deepen.
_IGNORED_SUFFIXES = (".test.tsx", ".test.ts", ".d.ts")


def _candidates() -> list[Path]:
    found: list[Path] = []
    for directory in SURFACE_DIRS:
        for path in sorted(directory.glob("*.ts*")):
            if path.name.endswith(_IGNORED_SUFFIXES):
                continue
            if path.stem == "index":
                continue
            found.append(path)
    return found


def _source_files() -> list[Path]:
    return [
        path
        for path in WEB_SRC.rglob("*.ts*")
        if not path.name.endswith(_IGNORED_SUFFIXES)
    ]


def test_every_surface_component_is_imported_by_live_code() -> None:
    sources = _source_files()
    orphans: list[str] = []
    for component in _candidates():
        stem = component.stem
        pattern = re.compile(
            r"""from\s+["'][^"']*/""" + re.escape(stem) + r"""["']"""
        )
        imported = any(
            pattern.search(path.read_text(encoding="utf-8"))
            for path in sources
            if path != component
        )
        if not imported:
            orphans.append(str(component.relative_to(REPO)))
    assert not orphans, (
        "surface components imported by NOTHING (the orphaned-BriefLane "
        f"class): {orphans} — mount them, or retire them with grep proof"
    )


def test_the_guard_sees_the_surface_dirs() -> None:
    """The guard must never pass vacuously because a directory moved."""
    for directory in SURFACE_DIRS:
        assert directory.is_dir(), f"surface dir vanished: {directory}"
    assert _candidates(), "no surface components found — the scan is broken"
