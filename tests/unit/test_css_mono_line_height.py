"""Guard: a late mono webfont swap changes no size.

The mono face is a webfont (@fontsource JetBrains Mono, `font-display: swap`).
It can land after a window has drawn. Until then the stack falls back to a
local mono face with other vertical metrics (Menlo: a 14 px line at 12 px;
JetBrains Mono: 16 px). Every mono line with `line-height: normal` grew when
the webfont landed, and the Engines window's catalog moved 4 px after it
settled (ENGINES-STILL, 2026-10-28).

Two fences close the class:

1. The metric twin. `web/src/styles/global.css` declares "JetBrains Mono
   Fallback": local mono faces with JetBrains Mono's own ascent, descent and
   line gap. Every stack that names "JetBrains Mono" (CSS, TS, the token
   JSON) names the twin next, so the fallback line IS the webfont line. A
   mono family that names no JetBrains Mono must go through a mono token.
   This covers every rule, also a `font-family` rule that inherits its line.
2. The own line. A `font` shorthand that sets a mono family resets the line
   height to `normal`; it must name its line (`12px / 16px`), or a later
   `line-height` in the same rule must.

Each failure names file:line. No allow-list.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
WEB_SRC = WEB / "src"
TWIN = "JetBrains Mono Fallback"

_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_BLOCK = re.compile(r"([^{}]*)\{([^{}]*)\}")
_DEF = re.compile(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;{}]*)")
_DECL = re.compile(r"(?<![A-Za-z0-9_-])(font|font-family|line-height)\s*:\s*([^;{}]*)", re.I)
_MONO_WORDS = re.compile(r"jetbrains\s*mono|monospace", re.I)
_VAR = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)")
_JB = re.compile(r"""\\?["']JetBrains Mono\\?["']|JetBrains Mono(?=,)""")


def _css_files() -> list[Path]:
    return sorted(p for p in WEB_SRC.rglob("*.css") if "_parked" not in p.parts)


def _script_files() -> list[Path]:
    out = [p for ext in ("*.ts", "*.tsx") for p in WEB_SRC.rglob(ext)]
    return sorted(p for p in out if "_parked" not in p.parts and "__tests__" not in p.parts)


def _strip_comments(text: str) -> str:
    # Keep newlines so offsets still map to lines.
    return _COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def _line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _mono_tokens(files: list[Path]) -> set[str]:
    """Custom properties whose value names a mono family (chains resolved)."""
    defs: dict[str, set[str]] = {}
    for path in files:
        for m in _DEF.finditer(_strip_comments(path.read_text(encoding="utf-8"))):
            defs.setdefault(m.group(1), set()).add(m.group(2))
    mono = {n for n, vs in defs.items() if any(_MONO_WORDS.search(v) for v in vs)}
    changed = True
    while changed:
        changed = False
        for name, values in defs.items():
            if name not in mono and any(set(_VAR.findall(v)) & mono for v in values):
                mono.add(name)
                changed = True
    return mono


def _is_mono(value: str, tokens: set[str]) -> bool:
    return bool(_MONO_WORDS.search(value) or set(_VAR.findall(value)) & tokens)


def _shorthand_has_line(value: str) -> bool:
    """`12px / 16px`, `var(--x)/1.3`: a slash outside any var() fallback."""
    depth = 0
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "/" and depth == 0:
            return True
    return False


def shorthand_offenders() -> list[str]:
    """Fence 2: a mono `font` shorthand with no line after it in its rule."""
    files = _css_files()
    tokens = _mono_tokens(files)
    out: list[str] = []
    for path in files:
        text = _strip_comments(path.read_text(encoding="utf-8"))
        for block in _BLOCK.finditer(text):
            selector = " ".join(block.group(1).split())
            if selector.endswith("@font-face"):
                continue
            body, start = block.group(2), block.start(2)
            bare_at: int | None = None
            for d in _DECL.finditer(body):
                prop, value = d.group(1).lower(), d.group(2)
                if prop == "line-height":
                    bare_at = None
                elif prop == "font":
                    bare_at = d.start() if _is_mono(value, tokens) and not _shorthand_has_line(value) else None
            if bare_at is not None:
                out.append(f"{path.relative_to(ROOT)}:{_line(text, start + bare_at)} {selector[:80]}")
    return out


def stack_offenders() -> list[str]:
    """Fence 1: every JetBrains Mono stack names the twin next; every other
    mono family goes through a mono token."""
    files = _css_files()
    tokens = _mono_tokens(files)
    out: list[str] = []
    for path in [*files, *_script_files(), WEB / "design-tokens.json"]:
        raw = path.read_text(encoding="utf-8")
        text = _strip_comments(raw) if path.suffix == ".css" else raw
        for m in _JB.finditer(text):
            after = text[m.end():m.end() + 40]
            if not re.match(r"""\s*,\s*\\?["']JetBrains Mono Fallback\\?["']""", after):
                out.append(f"{path.relative_to(ROOT)}:{_line(text, m.start())} names JetBrains Mono without the twin next")
        if path.suffix != ".css":
            continue
        for d in _DECL.finditer(text):
            prop, value = d.group(1).lower(), d.group(2)
            if prop == "line-height" or not _MONO_WORDS.search(value):
                continue
            if "jetbrains" in value.lower() or set(_VAR.findall(value)) & tokens:
                continue
            out.append(f"{path.relative_to(ROOT)}:{_line(text, d.start())} a mono family outside the mono token")
    return out


def test_the_metric_twin_is_declared() -> None:
    text = _strip_comments((WEB_SRC / "styles" / "global.css").read_text(encoding="utf-8"))
    faces = [b.group(2) for b in _BLOCK.finditer(text)
             if b.group(1).strip().endswith("@font-face") and TWIN in b.group(2)]
    assert len(faces) >= 2, f"global.css declares no regular and bold {TWIN!r} @font-face"
    for face in faces:
        # JetBrains Mono: ascent 1020, descent 300, line gap 0 per 1000 units.
        for prop, want in (("ascent-override", "102%"), ("descent-override", "30%"), ("line-gap-override", "0%")):
            assert re.search(rf"{prop}\s*:\s*{re.escape(want)}", face), f"{TWIN} lacks {prop}: {want}"
        assert "local(" in face, f"{TWIN} must be a local face (no download)"


def test_every_mono_stack_names_the_twin() -> None:
    bad = stack_offenders()
    assert not bad, (f"a mono stack can fall back to a face with other metrics; name {TWIN!r} right after "
                     "\"JetBrains Mono\", or use var(--font-mono):\n" + "\n".join(bad))


def test_every_mono_shorthand_names_its_line() -> None:
    bad = shorthand_offenders()
    assert not bad, ("a mono `font` shorthand resets the line height to `normal`; name the line "
                     "(the 16 px line at 12 px, or the line its context uses):\n" + "\n".join(bad))


def test_the_guard_sees_a_bare_mono_rule() -> None:
    """The scan's own fence."""
    tokens = {"--font-mono"}
    assert _is_mono("500 12px var(--font-mono)", tokens)
    assert not _shorthand_has_line("500 12px var(--font-mono, a/b)")
    assert _shorthand_has_line("500 12px / 16px var(--font-mono)")
    assert not _is_mono("600 13px var(--font-sans)", tokens)
    assert _JB.search('font: 12px/1 "JetBrains Mono", monospace')
    assert _JB.search('"\\"JetBrains Mono\\", \\"SF Mono\\""')
