"""HS-101 B1 — the interior canon guard.

The owner's ban, verbatim (the HS-101-02 gate, 2026-07-19): "that
stupid ass accent on the left ... it's literally a ban. NO." No left
border rail may ship anywhere in the web surface — receipts float in
aerogel (DESIGN_SYSTEM.md, "The interior canon", rule 6). The guard
is strict: ANY non-zero `border-left` in web/src CSS fails, named by
file and line, so the rail can never come back under a different
color.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB_SRC = ROOT / "web" / "src"

HARMLESS = re.compile(r"border-left\s*:\s*(0|none)\b")


def test_no_left_border_rails_in_web_css() -> None:
    offenders: list[str] = []
    for css in sorted(WEB_SRC.rglob("*.css")):
        for lineno, line in enumerate(
            css.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if "border-left" not in line:
                continue
            if HARMLESS.search(line):
                continue
            rel = css.relative_to(ROOT)
            offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, (
        "the left rail is banned (HS-101 canon rule 6) — remove the "
        "border-left and use the aerogel inset (.surface-aerogel / "
        "--desk-aerogel-* tokens) instead:\n" + "\n".join(offenders)
    )


def test_aerogel_tokens_exist() -> None:
    """The replacement must exist before the ban bites: the aerogel
    family rides the token pipeline."""
    tokens = (ROOT / "web" / "src" / "styles" / "tokens.css").read_text(
        encoding="utf-8"
    )
    for name in (
        "--desk-aerogel-fill",
        "--desk-aerogel-edge",
        "--desk-aerogel-blur",
        "--desk-aerogel-shadow",
    ):
        assert name in tokens, f"{name} missing from generated tokens.css"


def test_fluidity_census() -> None:
    """HS-101 rule 5 (B2) — the desk is fluid: the named operating
    moments carry token-ridden, compositor-only motion, and reduced
    motion silences every one of them."""
    surface = (WEB_SRC / "desk" / "surface" / "surface.css").read_text(
        encoding="utf-8"
    )
    desk = (WEB_SRC / "desk" / "desk.css").read_text(encoding="utf-8")
    moments = {
        "aerogel receipts inflate": (
            surface,
            "animation: surface-aerogel-in var(--duration-short) var(--ease-back)",
        ),
        "sections (and wing faces) rise in": (
            surface,
            "animation: surface-rise-in var(--duration-medium) var(--ease-quart)",
        ),
        "row verbs ease to the pointer": (
            surface,
            "transform var(--duration-short) var(--ease-quart)",
        ),
        "transient menus spring": (
            desk,
            "animation: desk-transient-in var(--duration-short) var(--ease-back)",
        ),
    }
    missing = [name for name, (text, needle) in moments.items() if needle not in text]
    assert not missing, f"fluid moments lost their motion: {missing}"
    for name, text in (("surface.css", surface), ("desk.css", desk)):
        assert "@media (prefers-reduced-motion: reduce)" in text, (
            f"{name} lost its reduced-motion silence"
        )
