"""HS-56-02 — the Qlippy dock + card shell page locks.

The static skeleton (hidden until the double opt-in confirms), the
sprite-strip animation grammar, the motion spec with its reduced-motion
story, the FIFO/queue markers, and the never-acts gating in the driver.
"""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _page() -> str:
    return (_REPO / "web" / "src" / "pages" / "presence.astro").read_text()


def _qlippy_js() -> str:
    return (_REPO / "web" / "src" / "scripts" / "qlippy.js").read_text()


def _presence_js() -> str:
    return (_REPO / "web" / "src" / "scripts" / "presence-app.js").read_text()


def test_skeleton_is_static_and_hidden_by_default() -> None:
    page = _page()
    assert 'id="qlippy"' in page and 'class="q-wrap" hidden' in page
    for el in ("qlippy-card", "qlippy-dock-sprite", "qlippy-headline",
               "qlippy-detail", "qlippy-preview", "qlippy-privacy",
               "qlippy-actions", "qlippy-queue-hint", "qlippy-dismiss",
               "qlippy-announcer"):
        assert f'id="{el}"' in page
    # ARIA: the live-region announcer.
    assert 'aria-live="polite"' in page


def test_sprite_grammar_and_reduced_motion() -> None:
    page = _page()
    # 9-frame, 80x80 strips: 720px sheet, steps(9), pixelated.
    assert "background-size: 720px 80px" in page
    assert "steps(9)" in page
    assert "image-rendering: pixelated" in page
    # The dock scales by transform so the frame math stays exact.
    assert "transform: scale(0.7)" in page
    # Reduced motion: sprite loops pause, the slide becomes a fade.
    assert ".q-sprite { animation: none; }" in page


def test_motion_spec_markers() -> None:
    page = _page()
    # Signal settle: ~420 ms in / ~280 ms out on the emphasized curve,
    # the one-time settle bob + accent glow on alert.
    assert "cubic-bezier(0.16, 1, 0.3, 1)" in page
    assert "420ms" in page and "280ms" in page
    assert "q-settle" in page
    # JS-created action buttons styled globally (the Astro scoping rule).
    assert "is:global" in page and ".q-btn" in page


def test_driver_is_gated_twice_and_never_acts() -> None:
    js = _qlippy_js()
    # Double opt-in: presence.enabled AND presence.mascot.
    assert "presence.enabled || !presence.mascot" in js
    # The FIFO queue + hover-hold + the sleep threshold + the flourish.
    assert "queue" in js and "_updateQueueHint" in js
    assert "_hovered" in js
    assert "SLEEP_AFTER_MS = 5 * 60 * 1000" in js
    assert "FLOURISH_MS" in js
    # Qlippy never acts: the only thing that fires is a user's click on an
    # action button (no fetch/POST lives in the shell itself).
    assert "fetch(\"/api/settings\")" in js  # the one read: the gate
    assert js.count("fetch(") == 1


def test_presence_app_re_dispatches_broadcasts() -> None:
    js = _presence_js()
    assert "hs-activity" in js
    assert "hs-broadcast" in js
