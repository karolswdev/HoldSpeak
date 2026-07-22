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


def test_live_core_never_regresses_to_a_stat_strip() -> None:
    """HS-102-02 — the Live Meeting face is the working posture: one
    verb, one quiet facts line. `MetricStrip` was the literal four-cell
    connection/duration/segments/room grid the story convicted; it must
    never come back on this face."""
    source = (WEB_SRC / "pages" / "cores" / "LiveCore.tsx").read_text(
        encoding="utf-8"
    )
    assert "MetricStrip" not in source, (
        "HS-102-02 regression: LiveCore.tsx must not reintroduce "
        "MetricStrip — duration/segments/connection compose as ONE "
        "quiet SurfaceFacts line instead."
    )


def test_ask_panel_never_regresses_to_a_pre_box_or_section_stack() -> None:
    """HS-102-03 — the Ask AI composer is ONE well (mic + material +
    verb, grounding/rails/runs-on as captions in the well's foot) and
    the answer renders as `Material`, never `desk-pullout-md` raw
    markdown in a `<pre>`. Named by story so a future "quick fix"
    can't quietly bring either regression back."""
    source = (WEB_SRC / "desk" / "components" / "AskPanel.tsx").read_text(
        encoding="utf-8"
    )
    assert "desk-pullout-md" not in source, (
        "HS-102-03 regression: AskPanel.tsx must not render the answer "
        "as raw markdown in a <pre> — use Material instead."
    )
    assert "desk-chat-well" in source, (
        "HS-102-03 regression: AskPanel.tsx must compose its question "
        "as the one-well grammar (desk-chat-well), not a stack of "
        "separate sections."
    )


def test_history_core_artifacts_wing_is_the_library() -> None:
    """HS-102-04 — the Meetings Artifacts wing is the library
    composition (SurfaceLibrary/SurfaceLibraryTile, the artifact body
    as the tile face), never a Disclosure+SurfaceCode dump. `Disclosure`
    and `SurfaceCode` stay legal elsewhere in this file (the Outcomes
    routing receipt, round 6, out of scope) — this pins the POSITIVE
    shape rather than banning either import outright."""
    source = (WEB_SRC / "pages" / "cores" / "HistoryCore.tsx").read_text(
        encoding="utf-8"
    )
    assert "SurfaceLibrary" in source and "SurfaceLibraryTile" in source, (
        "HS-102-04 regression: the Artifacts wing must compose through "
        "SurfaceLibrary/SurfaceLibraryTile, matching the Blocks wing "
        "(DictationCore.tsx) — not a second library shape."
    )


def test_profiles_core_never_regresses_to_a_field_stack() -> None:
    """HS-102-01 — creating/editing a Runs on destination is choice
    bays + SurfaceGroup rows, never the old label-over-input `Field`/
    `Select` stack the story convicted. Named by story so the next
    "quick fix" can't quietly bring the old form back."""
    source = (WEB_SRC / "pages" / "cores" / "ProfilesCore.tsx").read_text(
        encoding="utf-8"
    )
    assert "<Field" not in source, (
        "HS-102-01 regression: ProfilesCore.tsx must not render a "
        "label-over-input <Field> stack in its create/edit path — use "
        "SurfaceGroup/SurfaceSettingRow choice bays instead."
    )
    assert "<Select" not in source, (
        "HS-102-01 regression: destination Kind is chosen by bay, "
        "never a bare <Select> the person has to simulate in their head."
    )


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
