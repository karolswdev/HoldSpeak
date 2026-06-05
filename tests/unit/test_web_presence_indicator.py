from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_runtime_presence_card_is_accessible_and_reduced_motion_safe() -> None:
    page_source = (ROOT / "web/src/pages/index.astro").read_text()

    assert 'class="presence-card"' in page_source
    assert 'role="status"' in page_source
    assert 'aria-live="polite"' in page_source
    assert "@media (prefers-reduced-motion: reduce)" in page_source
    assert ".presence-ring.is-live { animation: none; }" in page_source


def test_dashboard_handles_runtime_activity_messages() -> None:
    script_source = (ROOT / "web/src/scripts/dashboard-app.js").read_text()

    assert "applyActivity(activity)" in script_source
    assert 'if (type === "runtime_activity")' in script_source
    assert "if (data && typeof data === \"object\") this.applyActivity(data)" in script_source
    assert "activityWindowLabel()" in script_source
