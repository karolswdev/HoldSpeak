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

from tests import _tree

ROOT = Path(__file__).resolve().parents[2]
WEB_SRC = ROOT / "web" / "src"

HARMLESS = re.compile(r"border-left\s*:\s*(0|none)\b")


def test_no_left_border_rails_in_web_css() -> None:
    offenders: list[str] = []
    for css in _tree.ts_files(WEB_SRC, suffixes=(".css",)):
        text = _tree.text_of(css)
        if "border-left" not in text:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
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


def test_a_transcript_mark_does_not_fake_a_left_rail_with_a_shadow() -> None:
    css = (WEB_SRC / "pages/cores/liveTranscript.css").read_text()
    marked = re.search(r"\.live-doc-line\[data-flagged\] \.live-doc-said\s*\{([^}]*)\}", css)
    assert marked, "the marked transcript rule must be present"
    assert not re.search(r"inset\s+(?!0(?:px)?\s)[\d.]+px\s+0\b", marked[1]), "a shadow is still a left rail"
    assert not re.search(r"border-(?:left|inline-start)\s*:\s*(?!0|none)", marked[1])
