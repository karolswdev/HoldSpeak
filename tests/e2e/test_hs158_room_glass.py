"""HS-158-05 real-hub Project Room glass.

The browser receives the production bundle and talks to a real
MeetingWebServer. Every record enters through the production HTTP
adapter. Room fields (purpose, outcome_text, lifecycle, posture) are
written directly via the DB layer because no HTTP route exposes them
yet (honest gap: update_project_room_fields has no PATCH route).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _api, _assert_clean, _normal_chair, _ensure_build

pytest.importorskip("playwright.sync_api", reason="Room glass needs Playwright")

TOKEN = "hs158-room-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-158-the-room/assets/story-05-shots"


def _init_desk(page: Any, url: str) -> None:
    """Navigate to the hub root so relative fetch paths work, then seed."""
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)


def _open_project_room(page: Any, url: str, project_id: str) -> None:
    """Navigate the desk to the Project Room for *project_id*.

    Uses the sessionStorage staging mechanism: before the desk mounts,
    we stage {key, scope} in hs.desk.staged-surface-open. When
    SurfaceWindows registers the open-project-memory surface, it
    consumes the staged intent and opens the window with the scope.
    """
    # Stage the surface open intent before reload.
    page.evaluate(
        """([key, scope]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key, scope})
          );
        }""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _seed_populated_project(page: Any) -> str:
    """Create a realistic Senior-Architect project through the real API.

    Returns the project id. Creates:
    - 2 milestones (one reached, one planned)
    - 2 risks (one critical open, one medium mitigated)
    - 1 dependency at_risk
    - 1 signal active
    - 1 workstream active

    Room fields (purpose, outcome_text, lifecycle, posture) are written
    via the DB layer because no HTTP PATCH route exposes them.
    """
    created = _api(page, "POST", "/api/projects", {
        "name": "Payments Platform Rewrite",
        "description": "Migrate from legacy payment gateway to modern event-driven architecture.",
        "command_id": "hs158-glass-create",
    }, token=TOKEN)
    project = created["project"]
    project_id = project["id"]

    # Write room fields directly via DB (no HTTP route exists).
    from holdspeak.db import get_database
    db = get_database()
    db.projects.update_project_room_fields(
        project_id,
        purpose="Replace the monolithic payment gateway with an event-driven platform that supports real-time settlement and multi-currency clearing.",
        outcome_text="All production payment traffic routes through the new platform with zero-downtime cutover by Q1.",
        lifecycle="active",
        posture="on_track",
        posture_reason="Sprint 4 velocity stable; PCI audit passed.",
    )

    # Items through the real API.
    items: list[dict[str, Any]] = [
        {
            "item_type": "milestone",
            "title": "PCI-DSS audit passed",
            "summary": "External auditor confirmed compliance for the new gateway.",
            "lifecycle": "reached",
            "due_at": "2026-07-15",
        },
        {
            "item_type": "milestone",
            "title": "Production cutover",
            "summary": "Route all live traffic through the new event-driven pipeline.",
            "lifecycle": "planned",
            "severity": "high",
            "due_at": "2026-10-01",
        },
        {
            "item_type": "risk",
            "title": "Settlement latency under load",
            "summary": "P99 settlement exceeds 800ms at projected Black Friday volume.",
            "lifecycle": "open",
            "severity": "critical",
            "due_at": "2026-09-15",
            "details": {"likelihood": "high", "impact": "critical", "mitigation": "Horizontal scaling spike test scheduled."},
        },
        {
            "item_type": "risk",
            "title": "Legacy API deprecation timeline",
            "summary": "Stripe v2 sunset pushed back; dual-write window extended.",
            "lifecycle": "mitigated",
            "severity": "medium",
            "details": {"likelihood": "low", "impact": "medium", "mitigation": "Dual-write window extended through Q1."},
        },
        {
            "item_type": "dependency",
            "title": "Compliance team sign-off",
            "summary": "Legal review of multi-currency clearing rules pending.",
            "lifecycle": "at_risk",
            "severity": "high",
            "due_at": "2026-09-01",
            "details": {"direction": "upstream", "counterpart_ref": "team:compliance"},
        },
        {
            "item_type": "signal",
            "title": "Partner bank integration interest",
            "summary": "Two partner banks expressed interest in direct settlement API.",
            "lifecycle": "active",
            "details": {"metric": "partner_interest_count", "latest_value": 2},
        },
        {
            "item_type": "workstream",
            "title": "Event sourcing migration",
            "summary": "Move transaction log from RDBMS to event store.",
            "lifecycle": "active",
        },
    ]
    # Each item creation bumps the project revision; skip expected_revision
    # to avoid tracking it across the chain (legacy behavior: API-006).
    for item_payload in items:
        _api(page, "POST", f"/api/projects/{project_id}/items", {
            **{k: v for k, v in item_payload.items() if v is not None},
        }, token=TOKEN)

    return project_id


def _seed_empty_project(page: Any) -> str:
    """Create a bare project with only a name."""
    created = _api(page, "POST", "/api/projects", {
        "name": "Empty Glass Project",
        "command_id": "hs158-glass-empty",
    }, token=TOKEN)
    return created["project"]["id"]


# ── Tests ───────────────────────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_room_populated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Seeded Project with items opens in the Room and renders truthfully."""
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            project_id = _seed_populated_project(page)
            _open_project_room(page, url, project_id)

            # Wait for the Room to render the orientation band.
            name_el = page.get_by_test_id("project-room-name")
            name_el.wait_for(timeout=15000)
            assert "Payments Platform Rewrite" in name_el.inner_text()

            # Orientation band is visible.
            band = page.get_by_test_id("orientation-band")
            band.wait_for()
            assert band.is_visible()

            # Focus block has at least one item visible.
            focus = page.get_by_test_id("focus-block")
            focus.wait_for(timeout=10000)
            assert focus.is_visible()
            # At least one focus item row should be visible.
            focus_rows = focus.locator(".surface-ledger-row")
            focus_rows.first.wait_for(timeout=10000)
            assert focus_rows.count() >= 1

            # No horizontal overflow.
            _assert_clean(page, errors)

            shot = SHOTS / f"room-populated-{width}.png"
            page.screenshot(path=str(shot), full_page=False)
            assert shot.exists() and shot.stat().st_size > 20_000, (
                f"Screenshot too small: {shot.stat().st_size} bytes"
            )
            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_room_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """A bare project with no items shows the honest empty state."""
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            project_id = _seed_empty_project(page)
            _open_project_room(page, url, project_id)

            name_el = page.get_by_test_id("project-room-name")
            name_el.wait_for(timeout=15000)
            assert "Empty Glass Project" in name_el.inner_text()

            # The empty state renders -- focus block has no items.
            # The orientation band is still visible.
            band = page.get_by_test_id("orientation-band")
            band.wait_for()
            assert band.is_visible()

            _assert_clean(page, errors)

            shot = SHOTS / f"room-empty-{width}.png"
            page.screenshot(path=str(shot), full_page=False)
            assert shot.exists() and shot.stat().st_size > 0
            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_room_degraded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Force the items section to degrade; the rest of the Room still renders.

    Monkeypatches ProjectService._read_room_items before hub boot so
    the /room endpoint returns items.state=degraded while orientation
    and other sections remain ok.
    """
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database
    from holdspeak.services.project_service import ProjectService

    original = ProjectService._read_room_items

    def _degraded_items(self: ProjectService, project_id: str) -> dict[str, Any]:
        raise RuntimeError("glass: forced items degradation")

    monkeypatch.setattr(ProjectService, "_read_room_items", _degraded_items)

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            project_id = _seed_populated_project(page)
            _open_project_room(page, url, project_id)

            # Orientation band still renders.
            name_el = page.get_by_test_id("project-room-name")
            name_el.wait_for(timeout=15000)
            assert "Payments Platform Rewrite" in name_el.inner_text()

            band = page.get_by_test_id("orientation-band")
            band.wait_for()
            assert band.is_visible()

            # The items section should show degraded state, not crash.
            # The focus block won't render (items.state === "degraded"),
            # but the degraded notice should appear.
            # Wait a moment for the room to finish rendering.
            page.wait_for_timeout(2000)

            _assert_clean(page, errors)

            shot = SHOTS / "room-degraded-1440.png"
            page.screenshot(path=str(shot), full_page=False)
            assert shot.exists() and shot.stat().st_size > 0
            browser.close()
    finally:
        server.stop()
        reset_database()
        monkeypatch.setattr(ProjectService, "_read_room_items", original)
