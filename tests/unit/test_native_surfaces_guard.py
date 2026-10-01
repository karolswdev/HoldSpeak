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

# HS-98-07: the conversion ledger is CLOSED — every core speaks the
# surface idiom. This dict stays empty forever; the test below refuses
# any attempt to reopen it.
ALLOWED: dict[str, set[str]] = {}


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


def test_ledger_is_closed() -> None:
    """HS-98-07: the seam is retired. The ledger only ever shrank and
    is now empty — reopening it would let the page grammar return."""
    assert ALLOWED == {}, "the Phase 98 conversion ledger never reopens"


def viewport_queries(text: str) -> list[str]:
    """The viewport-width media queries in a stylesheet's source."""
    return [m.group(0) for m in re.finditer(r"@media[^{]*", text)
            if re.search(r"(min|max)-width", m.group(0))]


def kit_css_violations(root: Path) -> list[str]:
    """Every kit stylesheet, at ANY depth (PHILO-11-04, Astra r1 F5: the
    species under desk/surface/send/ and patterns/ are the kit too), that
    reads the viewport width."""
    return [f"{path.relative_to(root)}: {q.strip()}"
            for path in sorted(root.rglob("*.css"))
            for q in viewport_queries(path.read_text(encoding="utf-8"))]


def test_the_scan_reaches_nested_kit_css(tmp_path: Path) -> None:
    nested = tmp_path / "send" / "deep"
    nested.mkdir(parents=True)
    (tmp_path / "top.css").write_text("@container surface (max-width: 419px) { a { color: red; } }\n")
    (nested / "species.css").write_text("@media (max-width: 420px) { a { color: red; } }\n")
    assert kit_css_violations(tmp_path) == ["send/deep/species.css: @media (max-width: 420px)"]


def test_kit_css_answers_to_the_window() -> None:
    """The kit reflows by @container, never viewport width media."""
    assert any(p.parent != SURFACE_CSS for p in SURFACE_CSS.rglob("*.css")), "the scan must reach nested kit CSS"
    bad = kit_css_violations(SURFACE_CSS)
    assert not bad, (
        f"{bad}: viewport width media query in the surface "
        "kit — use @container surface (DESIGN_SYSTEM.md rule 2)"
    )
