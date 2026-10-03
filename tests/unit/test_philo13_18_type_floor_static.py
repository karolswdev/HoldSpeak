"""PHILO-13-18 (C8) -- the 12 px floor, fenced in the source.

UX-CANON "The 12 px floor" (type-scale ruling 2026-09-21): readable text is
12 px or more; only a nontext glyph goes below it, and only when a readable
word or an accessible control name says the same thing.

The type token carries the floor (`--font-size-xs`, 12 px, the smallest size
token), and no declaration under ``web/src`` sets a size under it: CSS
``font-size`` and ``font`` shorthand in px or rem, and inline ``fontSize`` in
TSX. Red on 5912fcb9: 283 declarations (157 of them 9-11 px under
``web/src/desk``, faces-surfaces.md F9).

GLYPHS is the whole exemption: each line is one nontext use (a picture, a
caret, an arrow, an image-only mic) whose meaning a word or an accessible name
carries. It is listed by file and selector, never by pattern; a new line here
needs a ruling.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "web" / "src"
FLOOR_PX = 12.0

# (file under web/src, selector the declaration sits in): nontext uses only.
GLYPHS = {
    ("desk/components/dock.css", ".desk-next .desk-dock-x"),  # the close picture (VerbGlyph svg); aria-label "Close <name>"
    ("desk/components/speak-to-fill.css", ".desk-next .desk-inline-editor-foot .desk-mic"),  # image-only mic; aria-label
    ("desk/pullouts/thread-pullout.css", ".thread-result-glyph"),  # ▣ beside the result title
    ("desk/pullouts/thread-pullout.css", ".thread-speaker-glyph"),  # ▶ / ■; aria-label "Speak message" / "Stop speaking"
    ("desk/surface/gadgets.css", ".gadget-cycle-glyph"),  # ↻ aria-hidden; the select's value is the word
    ("desk/surface/gadgets.css", ".gadget-string .desk-mic, .desk-next .gadget-string .desk-mic"),  # image-only mic
    ("desk/surface/gadgets.css", ".gadget-arrows button"),  # ▲ ▼; aria-label "Increase/Decrease <label>"
    ("desk/surface/gadgets.css", ".gadget-pad .desk-mic, .desk-next .gadget-pad .desk-mic"),  # image-only mic
    ("desk/surface/gadgets.css", ".gadget-fold > summary::before"),  # ▸ caret; the summary is the word
    ("desk/surface/patterns/disclosure.css", ".surface-disclosure-caret"),  # ▸ aria-hidden; the label is the word
    ("desk/surface/patterns/progress-plan.css", ".surface-plan-step-icon"),  # ○ ● ✓ ✗ aria-hidden; the step label
    ("desk/surface/patterns/state-chip.css", ".surface-state-chip-icon"),  # state icon aria-hidden; the chip label
    ("desk/surface/surface-footer.css", ".desk-next .ledger-filter-well .desk-mic"),  # image-only mic
    ("desk/surface/surface.css", ".surface-edit-mic .desk-mic, .desk-next .surface-edit-mic .desk-mic"),  # image-only mic
}

_SIZE = r"([0-9]*\.?[0-9]+)(px|rem)"
_FONT_SIZE = re.compile(r"font-size\s*:\s*" + _SIZE)
_FONT = re.compile(r"(?<![-\w])font\s*:\s*[^;{}]*?(?:^|\s)" + _SIZE + r"\s*(?:/|\s|;|$)")
_INLINE = re.compile(r"fontSize\s*:\s*['\"]?" + r"([0-9]*\.?[0-9]+)(px|rem)?\b")


def _px(value: str, unit: str | None) -> float:
    return float(value) * (16 if unit == "rem" else 1)


def _selector(lines: list[str], index: int) -> str:
    """The selector of the rule that holds line ``index`` (0-based)."""
    if "{" in lines[index]:
        return lines[index].split("{")[0].strip()
    j = index
    while j >= 0 and "{" not in lines[j]:
        j -= 1
    sel = lines[j].split("{")[0].strip()
    k = j
    while k > 0 and lines[k - 1].strip().endswith(","):
        k -= 1
        sel = lines[k].strip() + " " + sel
    return sel


def under_floor() -> list[tuple[str, int, float, str]]:
    found = []
    for path in sorted(SRC.rglob("*")):
        if path.suffix not in (".css", ".tsx", ".ts") or "__tests__" in path.parts or ".test." in path.name:
            continue
        rel = path.relative_to(SRC).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if path.suffix == ".css":
                code = re.sub(r"/\*.*?\*/", "", line)
                hits = [_px(v, u) for v, u in _FONT_SIZE.findall(code)] + [_px(v, u) for v, u in _FONT.findall(code)]
            else:
                hits = [_px(v, u or "px") for v, u in _INLINE.findall(line)]
            for px in hits:
                if 0 < px < FLOOR_PX:
                    sel = _selector(lines, i) if path.suffix == ".css" else ""
                    found.append((rel, i + 1, px, sel))
    return found


def test_the_type_token_carries_the_floor() -> None:
    tokens = json.loads((REPO / "web" / "design-tokens.json").read_text(encoding="utf-8"))
    sizes: dict[str, str] = {}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            name = node.get("name")
            if isinstance(name, str) and name.startswith("--font-size-"):
                sizes[name] = str(node.get("value"))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(tokens)
    assert sizes.get("--font-size-xs") == "0.75rem", sizes
    for name, value in sizes.items():
        m = re.fullmatch(_SIZE, value)
        assert m and _px(*m.groups()) >= FLOOR_PX, f"{name} = {value} sits under the 12 px floor"


def test_no_readable_size_under_12px_in_web_src() -> None:
    found = under_floor()
    readable = [f for f in found if (f[0], f[3]) not in GLYPHS]
    assert not readable, (
        f"{len(readable)} font sizes under 12 px under web/src (ride var(--font-size-xs)):\n  "
        + "\n  ".join(f"{p}:{n} {px:g}px {sel}" for p, n, px, sel in readable[:80])
    )


def test_every_glyph_exemption_is_still_a_live_declaration() -> None:
    """The list only shrinks: a healed glyph line leaves the list."""
    live = {(p, sel) for p, _n, _px, sel in under_floor()}
    stale = sorted(GLYPHS - live)
    assert not stale, f"glyph exemptions with no sub-12 declaration left (remove them): {stale}"
