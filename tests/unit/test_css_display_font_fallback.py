"""Guard: the display face (Fraunces, the language 2026-11-08) swaps in with no shift.

The display face is a webfont (@fontsource Fraunces, `font-display: swap`).
Until it lands the stack falls back to Georgia, whose vertical metrics differ.
`web/src/styles/global.css` declares "Fraunces Fallback": Georgia with the
Fraunces ascent, descent and line gap (the mono twin's pattern,
tests/unit/test_css_mono_line_height.py). Every stack that names "Fraunces"
names the twin next. The face the owner rejected (Space Grotesk) is gone from
the web source and the package manifest.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
TWIN = "Fraunces Fallback"
_FRAUNCES = re.compile(r"""["']Fraunces["']\s*,\s*["']([^"']+)["']""")


def _sources() -> list[Path]:
    out = [p for ext in ("*.css", "*.ts", "*.tsx") for p in (WEB / "src").rglob(ext)]
    return sorted(p for p in out if "_parked" not in p.parts and "__tests__" not in p.parts)


def test_global_css_declares_the_metric_twin() -> None:
    css = (WEB / "src" / "styles" / "global.css").read_text(encoding="utf-8")
    faces = re.findall(r"@font-face\s*\{([^}]*)\}", css)
    twins = [f for f in faces if TWIN in f]
    assert len(twins) == 2, "global.css: one twin for the regular weights, one for the bold"
    for face in twins:
        for prop in ("size-adjust", "ascent-override", "descent-override", "line-gap-override"):
            assert prop in face, f"global.css: the {TWIN} face sets no {prop}"


def test_every_fraunces_stack_names_the_twin_next() -> None:
    failures = []
    for path in _sources():
        text = path.read_text(encoding="utf-8")
        for m in _FRAUNCES.finditer(text):
            if m.group(1) != TWIN:
                line = text.count("\n", 0, m.start()) + 1
                failures.append(f"{path.relative_to(ROOT)}:{line}: Fraunces then {m.group(1)!r}")
    tokens = json.loads((WEB / "design-tokens.json").read_text(encoding="utf-8"))
    display = tokens["primitive"]["font"]["display"]["value"]
    if not display.startswith(f'"Fraunces", "{TWIN}"'):
        failures.append(f"web/design-tokens.json primitive.font.display: {display!r}")
    assert not failures, "\n".join(failures)


def test_the_rejected_face_is_gone() -> None:
    hits = [
        str(p.relative_to(ROOT))
        for p in [*_sources(), WEB / "package.json", WEB / "design-tokens.json"]
        if re.search(r"space[\s-]grotesk", p.read_text(encoding="utf-8"), re.I)
    ]
    assert not hits, hits
