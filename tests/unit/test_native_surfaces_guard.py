"""HS-98-01 — the surface-idiom seam guard.

Window interiors are one visual product with the desk (Constitution,
Articles VII and VIII; DESIGN_SYSTEM.md "The surface idiom"). The
Signal PAGE grammar — viewport grids, nested Panel chrome, raw data
dumps, permanent button walls, modal confirms — is forbidden inside
`web/src/pages/cores/`. Cores compose the surface kit
(`web/src/desk/surface/`) instead.

The allowlist below is the Phase 98 conversion ledger, seeded at the
2026-07-18 truth. It only shrinks: a file leaves as its story converts
it, a stale entry (token no longer present) FAILS, and no file may be
added.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORES = REPO / "web" / "src" / "pages" / "cores"
SURFACE_CSS = REPO / "web" / "src" / "desk" / "surface"

# The page grammar, by name. Word-bounded so e.g. `Panel` never matches
# `SurfacePanelless` and `metric` never matches `surface-metrics`.
FORBIDDEN = (
    "page-grid",
    "span-4",
    "span-8",
    "span-12",
    "data-list",
    "data-row",
    "signal-eyebrow",
    "button-row",
    "code-block",
    "dialog-form",
    "Panel",
    "EmptyState",
    "Skeleton",
    "ResourceState",
    "ConfirmAction",
    "Dialog",
)

# file -> tokens that file is STILL allowed to carry (Phase 98 ledger;
# shrink-only — see the stale-entry test).
ALLOWED: dict[str, set[str]] = {
    "ActivityCore.tsx": {
        "data-list", "data-row", "button-row",
        "Panel", "ResourceState", "ConfirmAction",
    },
    "CommandsCore.tsx": {
        "data-list", "data-row", "button-row", "dialog-form",
        "Panel", "EmptyState", "ResourceState", "ConfirmAction", "Dialog",
    },
    "CompanionCore.tsx": {
        "data-list", "data-row", "Panel", "EmptyState", "ResourceState",
    },
    "ComponentsCore.tsx": {"page-grid", "Panel", "EmptyState", "Dialog"},
    "HistoryCore.tsx": {
        "data-list", "data-row", "button-row", "code-block", "dialog-form",
        "Panel", "EmptyState", "ResourceState", "ConfirmAction", "Dialog",
    },
    "LiveCore.tsx": {
        "page-grid", "span-4", "span-8", "span-12", "data-list", "data-row",
        "code-block", "dialog-form", "Panel", "EmptyState", "ResourceState",
        "Dialog",
    },
    "ProfilesCore.tsx": {
        "data-list", "data-row", "button-row", "dialog-form",
        "Panel", "EmptyState", "ResourceState", "ConfirmAction", "Dialog",
    },
    "RuntimeDocsCore.tsx": {"code-block", "Panel"},
    "SettingsCore.tsx": {"button-row", "Panel", "ResourceState"},
    "SetupCore.tsx": {
        "page-grid", "span-4", "span-8", "data-list", "data-row",
        "button-row", "Panel", "ResourceState",
    },
    "WorkbenchCore.tsx": {"button-row", "code-block", "Panel"},
}


def violations(text: str) -> set[str]:
    """The forbidden page-grammar tokens present in a core's source."""
    found = set()
    for token in FORBIDDEN:
        if re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", text):
            found.add(token)
    return found


def test_scanner_flags_a_plant() -> None:
    assert violations('<div className="page-grid">') == {"page-grid"}
    assert violations("import { Panel } from ") == {"Panel"}
    # Word bounds: kit names and unrelated words never match.
    assert violations("surface-metrics Panelless data-rows") == set()


def test_cores_speak_the_surface_idiom() -> None:
    assert CORES.is_dir()
    for path in sorted(CORES.glob("*.tsx")):
        found = violations(path.read_text(encoding="utf-8"))
        allowed = ALLOWED.get(path.name, set())
        fresh = found - allowed
        assert not fresh, (
            f"{path.name} speaks the page grammar: {sorted(fresh)} — "
            "compose web/src/desk/surface/ instead (DESIGN_SYSTEM.md, "
            "the surface idiom); the allowlist only shrinks"
        )


def test_allowlist_only_shrinks() -> None:
    """A converted file (or token) must LEAVE the ledger — stale rows
    would let the page grammar quietly return."""
    for name, tokens in ALLOWED.items():
        path = CORES / name
        assert path.exists(), f"allowlist names a dead file: {name}"
        found = violations(path.read_text(encoding="utf-8"))
        stale = tokens - found
        assert not stale, (
            f"{name}: allowlist rows {sorted(stale)} are stale — "
            "delete them (the ledger only shrinks)"
        )


def test_kit_css_answers_to_the_window() -> None:
    """The kit reflows by @container, never viewport width media."""
    for path in SURFACE_CSS.glob("*.css"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"@media[^{]*", text):
            assert not re.search(r"(min|max)-width", match.group(0)), (
                f"{path.name}: viewport width media query in the surface "
                "kit — use @container surface (DESIGN_SYSTEM.md rule 2)"
            )
