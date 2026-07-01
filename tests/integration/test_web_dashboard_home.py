"""HS-44-01: the dashboard idle "command center" home cards (behavior-preserving)."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def test_dashboard_has_idle_home_action_cards() -> None:
    page = (_REPO / "web" / "src" / "pages" / "live.astro").read_text()
    # the premium home-action cards, idle-only (don't steal the active meeting view).
    assert "home-actions" in page
    assert 'x-show="!meetingActive && !stopInProgress"' in page
    for href in ('href="/dictation"', 'href="/history"', 'href="/activity"', 'href="/settings"'):
        assert href in page
    # accent glow + reduced-motion respected.
    assert "radial-gradient" in page
    assert "prefers-reduced-motion" in page


def test_dashboard_idle_home_is_a_command_center() -> None:
    """HS-44-01 (deep): a warm idle headline + a recent-meetings glance."""
    page = (_REPO / "web" / "src" / "pages" / "live.astro").read_text()
    app = (_REPO / "web" / "src" / "scripts" / "dashboard-app.js").read_text()
    # an idle headline fills the hero's dead space.
    assert "hero-idle-h" in page and "Ready when you are" in page
    # a recent-meetings glance, idle-only, fed by /api/meetings.
    assert "home-recent" in page and "Recent meetings" in page
    assert "loadRecentMeetings" in app and "/api/meetings?limit=4" in app
    assert "recentMeetings" in app
