"""HS-96-03 — the design-system conformance locks.

The state contract lives in docs/internal/DESIGN_SYSTEM.md; these greps
keep its mechanical core true in the CSS: the global focus grammar, the
one pressed grammar, and the spec's coverage list. Raw values in the doc
are forbidden — every value is a token name.
"""

from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[2]
DOC = REPO / "docs" / "internal" / "DESIGN_SYSTEM.md"
GLOBAL = REPO / "web" / "src" / "styles" / "global.css"
DESK = REPO / "web" / "src" / "desk" / "desk.css"
WINDOW_CHROME = REPO / "web" / "src" / "desk" / "components" / "window-chrome.css"

COMPONENTS = (
    "Signal Button",
    "Desk chip",
    "Window verbs",
    "Dock",
    "The orb",
    "Window frame",
    "Inputs",
    # HS-111-08: the legacy dialect retired; the matrix pins the kit
    # species roster instead.
    "CheckGadget / CycleGadget / LampGadget / SurfaceState",
    "GL world states",
)

PRESSED_FAMILIES = (
    ".desk-chip",
    ".desk-window-verb",
    ".desk-dock-main",
    ".desk-dock-x",
    ".desk-dock-reset",
    ".desk-tool-link",
    ".desk-mark",
    ".studio-card",
    ".desk-dock-launch",
    ".desk-create-button",
    ".egress-badge-button",
)


def test_spec_doc_covers_every_component() -> None:
    text = DOC.read_text(encoding="utf-8")
    for name in COMPONENTS:
        assert name in text, f"DESIGN_SYSTEM.md lost the {name!r} matrix"


def test_spec_doc_speaks_only_tokens() -> None:
    text = DOC.read_text(encoding="utf-8")
    hexes = re.findall(r"#[0-9A-Fa-f]{3,8}\b", text)
    assert not hexes, f"raw values in the spec doc: {hexes}"


def test_global_focus_grammar_holds() -> None:
    css = GLOBAL.read_text(encoding="utf-8")
    assert ":focus-visible" in css
    assert "var(--focus-outline-width)" in css


def test_one_pressed_grammar_covers_the_chrome() -> None:
    """The chrome state contract moved with the window-chrome extraction."""
    chrome = WINDOW_CHROME.read_text(encoding="utf-8")
    block = chrome[chrome.index("HS-96-03") :]
    for family in PRESSED_FAMILIES:
        assert family in block, f"pressed grammar lost {family}"
    assert "translateY(1px)" in block
    glob_css = GLOBAL.read_text(encoding="utf-8")
    assert ":where(.btn):active:not(:disabled)" in glob_css
