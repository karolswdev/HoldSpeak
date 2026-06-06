"""HS-44-03: the history archive premium pass (behavior-preserving)."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _page() -> str:
    return (_REPO / "web" / "src" / "pages" / "history.astro").read_text()


def test_history_is_elevated_to_the_wizard_bar() -> None:
    """Ambient glow + an elevated rounded hero + a premium pill tab bar."""
    page = _page()
    # the same ambient accent glow as the dashboard, cockpit, and wizard.
    assert ".shell::before" in page
    assert "radial-gradient" in page
    # the hero + section read as raised, rounded, elevated surfaces.
    assert "var(--radius-lg)" in page
    assert "var(--elev-1)" in page
    # the tab row is a contained pill bar with a solid-accent active tab.
    assert "var(--radius-pill)" in page
    assert "backdrop-filter: blur" in page


def test_history_motion_is_reduced_motion_safe() -> None:
    page = _page()
    # cards lift on hover, guarded for reduced motion.
    assert "translateY(-2px)" in page
    assert "prefers-reduced-motion" in page


def test_history_preserves_behavior_hooks() -> None:
    """The Alpine DOM contract the factory + spoken-e2e depend on is intact."""
    page = _page()
    # the historyApp factory + its tab system.
    assert 'x-data="historyApp()"' in page
    for tab in ("meetings", "actions", "speakers", "projects", "intel"):
        assert f"setTab('{tab}')" in page
    # the card + artifact class names the JS and the spoken-e2e selectors read.
    for cls in ("meeting-card", "action-card", "speaker-card", "artifact-card",
                "risk-table", "incident-timeline", "status-pill"):
        assert cls in page
