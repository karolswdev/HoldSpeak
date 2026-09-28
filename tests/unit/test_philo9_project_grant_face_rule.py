"""PHILO-9-07: the face's palette rule matches the palettes the hub resolves.

The ratified canvas settles it as a correctness rule: a grant's controls show
only where the credential's ISSUED palette holds the tools that grant covers.
The face declares the two palette lists (``web/src/pages/cores/SettingsCore.tsx``
``PROJECT_GRANT_PALETTES``, ``DESK_GRANT_PALETTES``); this fence derives them
from ``holdspeak.mcp.palettes.resolve_palette`` so a palette change cannot
leave a grant's verb on a credential that cannot use it, or hide it from one
that can.
"""
from __future__ import annotations

import re
from pathlib import Path

from holdspeak.kernel.desk import DESK_GRANT_OPERATIONS
from holdspeak.kernel.project import PROJECT_GRANT_OPERATIONS
from holdspeak.mcp.palettes import PALETTE_NAMES, resolve_palette

SOURCE = Path(__file__).resolve().parents[2] / "web" / "src" / "pages" / "cores" / "SettingsCore.tsx"


def _declared(name: str) -> list[str]:
    match = re.search(rf"export const {name} = \[([^\]]*)\] as const;", SOURCE.read_text(encoding="utf-8"))
    assert match, f"{name} is not declared by the face"
    return re.findall(r'"([A-Z]+)"', match.group(1))


#: The desk family the desk grant covers (the canvas: desk.*, zone.*, decision.*, note.*, kb.*).
DESK_FAMILY = ("desk.", "zone.", "decision.", "note.", "kb.")


def test_the_project_palettes_are_exactly_those_holding_the_bound() -> None:
    holding = [p for p in PALETTE_NAMES if set(PROJECT_GRANT_OPERATIONS) <= resolve_palette(p)]
    assert _declared("PROJECT_GRANT_PALETTES") == holding


def test_the_desk_palettes_are_exactly_those_holding_the_desk_writes() -> None:
    holding = [p for p in PALETTE_NAMES if any(t.startswith(DESK_FAMILY) for t in resolve_palette(p))]
    assert _declared("DESK_GRANT_PALETTES") == holding
    assert {name.split(".")[0] + "." for name in DESK_GRANT_OPERATIONS} <= set(DESK_FAMILY)
