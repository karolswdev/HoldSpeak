"""HS-44-02: the dictation cockpit premium pass (behavior-preserving)."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _page() -> str:
    return (_REPO / "web" / "src" / "pages" / "dictation.astro").read_text()


def test_dictation_has_cockpit_hero() -> None:
    """A wizard-bar hero (eyebrow + display title + lede) heads the surface."""
    page = _page()
    assert "cockpit-hero" in page
    assert "cockpit-eyebrow" in page
    assert "cockpit-h" in page
    assert "cockpit-lede" in page
    assert "Dictation cockpit" in page


def test_dictation_cockpit_is_elevated_to_the_wizard_bar() -> None:
    """Ambient glow + a premium contained nav + reduced-motion-safe motion."""
    page = _page()
    # the same ambient accent glow as the dashboard home + the wizard.
    assert ".dictation::before" in page
    assert "radial-gradient" in page
    # the section nav is a premium contained pill bar.
    assert "cockpit-tabs" in page
    # depth + motion that respects reduced-motion.
    assert "prefers-reduced-motion" in page


def test_dictation_cockpit_preserves_behavior_hooks() -> None:
    """The Alpine-free app's DOM contract is untouched — ids + section tabs."""
    page = _page()
    # the section tablist the JS binds via `[data-section]` is intact.
    assert 'role="tablist" aria-label="Dictation sections"' in page
    for section in ("readiness", "blocks", "kb", "hs", "hooks", "runtime", "memory", "dry-run"):
        assert f'data-section="{section}"' in page
    # the block-scope row + key control ids the JS reads by id.
    assert 'data-scope="global"' in page
    assert 'id="project-root-apply"' in page
    assert 'id="dry-btn-run"' in page
