"""Guard: the desk has no second display face (owner, 2026-11-08).

Space Grotesk, Bricolage Grotesque, Archivo, Schibsted Grotesk and Fraunces
were each rejected live. Titles, masts and the wordmark are the text face,
Inter, by weight, size and tracking. This guard keeps the display token equal
to the body stack and keeps every rejected face out of the web sources.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WEB_SRC = REPO / "web" / "src"
TOKENS = WEB_SRC / "styles" / "tokens.css"
GLOBAL = WEB_SRC / "styles" / "global.css"
PACKAGE = REPO / "web" / "package.json"
REJECTED = ("Space Grotesk", "Bricolage Grotesque", "Archivo", "Schibsted Grotesk", "Fraunces")


def _token(name: str) -> str:
    match = re.search(rf"^\s*{re.escape(name)}:\s*([^;]+);", TOKENS.read_text(encoding="utf-8"), re.M)
    assert match, f"tokens.css: no {name}"
    return match.group(1).strip()


def test_the_display_token_is_the_text_face() -> None:
    display = _token("--font-display")
    assert display.startswith('"Inter"'), display
    assert "serif" in display and "sans-serif" in display, display


def test_only_the_text_face_and_the_mono_face_are_imported() -> None:
    imports = re.findall(r'@import\s+"@fontsource/([^/"]+)', GLOBAL.read_text(encoding="utf-8"))
    assert set(imports) <= {"inter", "jetbrains-mono"}, imports
    deps = PACKAGE.read_text(encoding="utf-8")
    hits = [face for face in ("fraunces", "space-grotesk", "bricolage", "archivo", "schibsted") if f"@fontsource/{face}" in deps]
    assert not hits, hits


def test_no_rejected_face_is_named_in_web_src() -> None:
    hits: list[str] = []
    for path in WEB_SRC.rglob("*"):
        if path.suffix not in {".css", ".ts", ".tsx", ".html"} or "_parked" in path.parts or "__tests__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for face in REJECTED:
            if face in text:
                hits.append(f"{path.relative_to(REPO)}: {face}")
    assert not hits, "\n".join(hits)
