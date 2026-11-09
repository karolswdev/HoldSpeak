# PARKED 2026-11-09 (fences diet, pipe/fences-diet): each test pins literal text in one named face file (LiveCore, AskPanel, history, DictationCore, three CSS files); a face rebuilt in the native language turned them red.
# Nothing replaces them: the left-rail ban and the aerogel tokens stay live in tests/unit/test_interior_canon_guard.py.
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
    assert source.count('className="conversation-composer desk-ask-composer"') == 1, (
        "HS-102-03 regression: AskPanel.tsx must compose its question "
        "as the shared conversation composer, not a stack of "
        "separate sections."
    )
    assert source.count("<PadGadget") == 1, "Ask has one library question pad"


def test_history_core_artifacts_wing_stays_parked() -> None:
    """Betterment capture C5 parked the Meetings Artifacts wing (HS-102-04's
    library composition lives on in ``history/_parked/ArtifactsLibrary.tsx``):
    a meeting's Results show under Outcomes ▸ Prepared. No live history file
    may bring the wing or its library dump back."""
    history_dir = WEB_SRC / "pages" / "cores" / "history"
    assert (history_dir / "_parked" / "ArtifactsLibrary.tsx").exists(), "parked, never deleted"
    live = "\n".join(file.read_text(encoding="utf-8") for file in sorted(history_dir.glob("*.tsx")))
    assert "<ArtifactsLibrary" not in live and 'from "./ArtifactsLibrary"' not in live, (
        "the Artifacts wing is parked (capture C5)")
    assert "PreparedResults" in live, "the meeting's Results are drawn under Outcomes ▸ Prepared"


def test_dictation_core_speech_settings_never_regresses() -> None:
    """HS-102-06 — the Speak gear face (Readiness/Knowledge/Runtime) is
    composed groups + EditInPlace + the shared RuntimeDestination, never
    the raw-wire dumps / Save-button forms / label-over-Select stack the
    owner's screenshots convicted ("an absolute joke — a cacophony of
    tiles, panes, forms, form groups").
    HS-117-08 decomposed the core into dictation/ sub-files; read the
    full tree."""
    core_file = WEB_SRC / "pages" / "cores" / "DictationCore.tsx"
    sub_dir = WEB_SRC / "pages" / "cores" / "dictation"
    parts = [core_file.read_text(encoding="utf-8")]
    if sub_dir.is_dir():
        for f in sorted(sub_dir.glob("*.tsx")):
            parts.append(f.read_text(encoding="utf-8"))
    source = "\n".join(parts)
    assert "Save knowledge" not in source and "Save instructions" not in source, (
        "HS-102-06 regression: Knowledge/Instructions must save on commit "
        "through EditInPlace, never an orange Save button."
    )
    # HS-112-01: the runtime destination is edited ONLY in the Prefs
    # models module — the Speak face states the fact and hands over,
    # never re-deriving a second endpoint editor.
    assert "SET IN ENGINES" in source, (  # Betterment E6 (was RUNS ON LIVES IN MODELS)
        "HS-112-01 regression: the Speak runtime face must hand over to "
        "the Prefs models module (the one dial), never embed or "
        "re-derive an endpoint editor."
    )
    assert "openai_compatible_base_url" not in source, (
        "HS-112-01 regression: no raw endpoint fields in the Speak face."
    )
    # HS-111-02: the gear door migrated from the macOS SurfaceGroup/
    # SurfaceToggle grammar to the HS-111-01 gadget sheet — the guard
    # follows the composition it protects.
    assert "GadgetGroup" in source and "CheckGadget" in source, (
        "HS-111-02 regression: Pipeline readiness must compose through "
        "GadgetGroup/GadgetRow/CheckGadget (the gadget sheet), not a "
        "bare SurfaceFacts key-value dump of the raw readiness wire."
    )


def test_fluidity_census() -> None:
    """HS-101 rule 5 (B2) — the desk is fluid: the named operating
    moments carry token-ridden, compositor-only motion, and reduced
    motion silences every one of them."""
    surface = (WEB_SRC / "desk" / "surface" / "surface.css").read_text(
        encoding="utf-8"
    )
    desk = (WEB_SRC / "desk" / "desk.css").read_text(encoding="utf-8")
    chrome = (WEB_SRC / "desk" / "components" / "window-chrome.css").read_text(
        encoding="utf-8"
    )
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
            chrome,
            "animation: desk-transient-in var(--duration-short) var(--ease-back)",
        ),
    }
    missing = [name for name, (text, needle) in moments.items() if needle not in text]
    assert not missing, f"fluid moments lost their motion: {missing}"
    for name, text in (("surface.css", surface), ("desk.css", desk)):
        assert "@media (prefers-reduced-motion: reduce)" in text, (
            f"{name} lost its reduced-motion silence"
        )
