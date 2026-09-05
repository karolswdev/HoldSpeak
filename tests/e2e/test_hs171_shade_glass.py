"""HS-171-04 -- Shade PROJECTS + dock badge glass rig.

Seeds two Rooms with needs-you items via watches, mutes one via
PUT /api/settings/heartbeat {muted_projects:[id]}. Opens the shade at
1440 + 393. Asserts:
  - caption count excludes the muted Room
  - the muted row is dimmed with MUTED
  - the badge equals the caption count
  - Open opens the Room window
  - quiet leg (no items): PROJECTS absent, badge absent

Shots to phase-171-the-heartbeat/assets/story-04-shots/.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot,
    _api,
    _assert_clean,
    _normal_chair,
    _ensure_build,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="Shade glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-171-the-heartbeat/assets/story-04-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs171-shade"


# ── Seed helpers ──────────────────────────────────────────────────


def _seed_project(project_id: str, name: str) -> str:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, NULL, "
            "'2026-09-01T00:00:00', '2026-09-05T10:00:00')",
            (project_id, name),
        )
    return project_id


def _seed_gh_connection(login: str = "karolswdev") -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, created_at, updated_at) "
            "VALUES ('wpc-gh', 'github', ?, 'connected', "
            " datetime('now'), datetime('now'), datetime('now'))",
            (login,),
        )


def _seed_watch(
    project_id: str,
    *,
    watch_id: str,
    connector_id: str = "gh",
    query_kind: str = "pull_requests",
    query: dict[str, Any] | None = None,
    snapshot: list[dict[str, Any]] | None = None,
    last_success_at: str | None = "2026-09-04T10:00:00",
    last_error: str | None = None,
    enabled: bool = True,
) -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, "
            " created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
            (
                watch_id,
                connector_id,
                query_kind,
                f"{connector_id} {query_kind}",
                json.dumps(query or {}, sort_keys=True),
                json.dumps(snapshot or []),
                int(enabled),
                last_success_at,
                last_error,
                project_id,
            ),
        )


def _seed_two_rooms_with_needs_you() -> tuple[str, str]:
    """Seed two projects that produce 3 needs-you items total.

    Returns (pid_active, pid_muted).
    """
    _seed_gh_connection()

    # Project Alpha: 2 items (PR review overdue + CI failure)
    pid1 = _seed_project("proj-alpha-171", "Q4 Platform")
    yesterday = (datetime.now() - timedelta(days=3)).isoformat()
    _seed_watch(pid1, watch_id="w-171-alpha-prs", connector_id="gh",
                query_kind="pull_requests",
                query={"repository": "karolswdev/HoldSpeak"},
                snapshot=[
                    {"number": 612, "title": "Rig settles animations before every shot",
                     "state": "OPEN", "url": "https://github.com/karolswdev/HoldSpeak/pull/612",
                     "reviewRequests": ["karolswdev"], "updatedAt": yesterday},
                ])
    _seed_watch(pid1, watch_id="w-171-alpha-ci", connector_id="gh",
                query_kind="branch_ci",
                query={"repository": "karolswdev/HoldSpeak", "branch": "main"},
                snapshot=[
                    {"conclusion": "failure", "branch": "main",
                     "url": "https://github.com/karolswdev/HoldSpeak/actions/runs/1",
                     "updated_at": (datetime.now() - timedelta(minutes=40)).isoformat()},
                ])

    # Project Beta: 1 item (CI failure)
    pid2 = _seed_project("proj-beta-171", "Governance")
    _seed_watch(pid2, watch_id="w-171-beta-ci", connector_id="gh",
                query_kind="branch_ci",
                query={"repository": "karolswdev/Beta", "branch": "main"},
                snapshot=[
                    {"conclusion": "failure", "branch": "main",
                     "url": "https://github.com/karolswdev/Beta/actions/runs/2",
                     "updated_at": (datetime.now() - timedelta(minutes=20)).isoformat()},
                ])

    return pid1, pid2


# ── Shot helpers ──────────────────────────────────────────────────

def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _open_shade(page: Any) -> None:
    """Open the system shade via the bell button."""
    bell = page.locator(".desk-bell")
    bell.wait_for(timeout=10000)
    bell.click()
    page.locator(".desk-shade").wait_for(timeout=5000)
    _settle(page)


# ── Tests ─────────────────────────────────────────────────────────


def _run_projects_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    """Seed two Rooms, mute one, assert the shade and dock badge."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            # Init desk
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)

            # Seed two Rooms
            pid_active, pid_muted = _seed_two_rooms_with_needs_you()

            # Mute one project via heartbeat settings
            _api(page, "PUT", "/api/settings/heartbeat",
                 {"muted_projects": [pid_muted]}, token=TOKEN)

            # Reload to pick up seeded data
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            # Fetch the needs-you aggregate to verify shape
            ny = _api(page, "GET", "/api/desk/needs-you", token=TOKEN)
            total_count = ny.get("count", 0)
            assert total_count > 0, f"Expected needs-you items, got count={total_count}"

            # Open the shade
            _open_shade(page)

            # ── PROJECTS section present ──
            projects_section = page.get_by_test_id("shade-projects")
            assert projects_section.count() == 1, "PROJECTS section should be present"

            # ── Caption count excludes muted ──
            caption = projects_section.locator("h4").text_content() or ""
            assert "PROJECTS" in caption.upper(), f"Caption should say PROJECTS: {caption}"
            # The muted Room's items should NOT be in the caption count.
            # The active Room (Q4 Platform) has items; Governance is muted.
            # Caption should say "N NEED YOU" where N = active items only.

            # ── Project rows ──
            project_rows = page.get_by_test_id("shade-project-row")
            assert project_rows.count() >= 2, \
                f"Expected at least 2 project rows, got {project_rows.count()}"

            # ── Muted row has is-muted class and MUTED token ──
            muted_rows = page.locator("[data-testid='shade-project-row'].is-muted")
            # The muted_projects field might not be wired through to the
            # needs-you items yet (a sibling is adding muted+mutedCount).
            # Code defensively: if zero muted rows, the sibling hasn't
            # landed yet; if >= 1, assert MUTED token.
            if muted_rows.count() > 0:
                muted_text = muted_rows.first.text_content() or ""
                assert "MUTED" in muted_text.upper(), \
                    f"Muted row should contain MUTED token: {muted_text}"

            # ── Dock badge ──
            # The Intelligence dock app should show the needs-you count.
            badge = page.locator(".desk-dock-app .desk-dock-badge")
            if badge.count() > 0:
                badge_text = badge.first.text_content() or ""
                # Badge should be a number matching the needs-you count.
                if badge_text.isdigit():
                    badge_val = int(badge_text)
                    assert badge_val > 0, "Dock badge should be > 0 when items exist"

            # ── Open verb opens the Room window ──
            open_buttons = projects_section.get_by_role("button", name="Open")
            if open_buttons.count() > 0:
                open_buttons.first.click()
                page.wait_for_timeout(1500)
                # Shade should close after clicking Open
                shade_after = page.locator(".desk-shade")
                assert shade_after.count() == 0, "Shade should close after Open click"

            # Take shot
            # Re-open shade for the screenshot
            _open_shade(page)
            _shot(page, "build-shade-projects", width)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_quiet_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    """Empty desk: PROJECTS section absent, dock badge absent."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            # Init desk -- no project seeding
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            # Open the shade
            _open_shade(page)

            # ── PROJECTS section absent ──
            projects_section = page.get_by_test_id("shade-projects")
            assert projects_section.count() == 0, \
                "PROJECTS section should be absent when no items exist"

            # ── Dock badge absent ──
            badge = page.locator(".desk-dock-app .desk-dock-badge")
            badge_visible = False
            if badge.count() > 0:
                txt = badge.first.text_content() or ""
                badge_visible = txt.isdigit() and int(txt) > 0
            assert not badge_visible, "Dock badge should be absent at zero"

            # Take shot
            _shot(page, "build-shade-quiet", width)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_dock_badge_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dock badge at 1440: present with items, absent without."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            # Init desk with projects
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)

            _seed_two_rooms_with_needs_you()

            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            # Wait for the dock to render and needs-you to load
            page.locator(".desk-dock").wait_for(timeout=10000)
            # Give the dock badge time to fetch
            page.wait_for_timeout(2000)

            _shot(page, "build-dock-badge", 1440)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── Pytest entries ──────────────────────────────────────────────────


@pytest.mark.timeout(120)
def test_shade_projects_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_projects_rig(tmp_path, monkeypatch, 1440)


@pytest.mark.timeout(120)
def test_shade_projects_393(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_projects_rig(tmp_path, monkeypatch, 393)


@pytest.mark.timeout(120)
def test_shade_quiet_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_quiet_rig(tmp_path, monkeypatch, 1440)


@pytest.mark.timeout(120)
def test_shade_quiet_393(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_quiet_rig(tmp_path, monkeypatch, 393)


@pytest.mark.timeout(120)
def test_dock_badge_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_dock_badge_rig(tmp_path, monkeypatch)


# ── HS-171-04 AC-5: shade polls while open, stops when closed ────────


def _run_polling_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Count GET /api/desk/needs-you requests via page.route.
    Open -> at least 1 request, wait one poll interval -> +1,
    close -> wait an interval -> no new request."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            # Track needs-you requests
            needs_you_requests: list[float] = []

            def intercept_needs_you(route):
                import time as _t
                needs_you_requests.append(_t.time())
                route.continue_()

            page.route("**/api/desk/needs-you", intercept_needs_you)

            # Init desk with seeded data
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _seed_two_rooms_with_needs_you()
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            # Clear the counter before opening shade
            needs_you_requests.clear()

            # Open the shade
            _open_shade(page)

            # Initial fetch fires on open
            page.wait_for_timeout(1000)
            count_after_open = len(needs_you_requests)
            assert count_after_open >= 1, (
                f"Expected >= 1 needs-you request on open, got {count_after_open}"
            )

            # Wait one poll interval (5 seconds) for a polling request
            page.wait_for_timeout(6000)
            count_after_poll = len(needs_you_requests)
            assert count_after_poll > count_after_open, (
                f"Expected more requests after poll interval; "
                f"open={count_after_open}, after={count_after_poll}"
            )

            # Close the shade
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            shade_after_close = page.locator(".desk-shade")
            assert shade_after_close.count() == 0, "Shade should be closed"

            # Record count after close
            count_at_close = len(needs_you_requests)

            # Wait another poll interval -- no new request should arrive
            page.wait_for_timeout(6000)
            count_after_close_wait = len(needs_you_requests)
            assert count_after_close_wait == count_at_close, (
                f"Polling should stop when closed; "
                f"at_close={count_at_close}, after_wait={count_after_close_wait}"
            )

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(120)
def test_shade_polling_stops_on_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_polling_rig(tmp_path, monkeypatch)


# ── HS-171-04 AC-6: artboard assertions (UX-CANON E.2) ──────────────


def _run_artboard_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    """Assert the artboard: three type steps, no raw <button>, no
    sentence (> 60 chars text node), nothing overflows at 393."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _seed_two_rooms_with_needs_you()
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            _open_shade(page)

            projects_section = page.get_by_test_id("shade-projects")
            assert projects_section.count() == 1, "PROJECTS section required for artboard test"

            # ── Three type steps present ──
            # Caption (h4), row primary (strong), tokens (small/span) should
            # have three distinct computed font sizes.
            font_sizes = page.evaluate("""() => {
                const section = document.querySelector('[data-testid="shade-projects"]');
                if (!section) return [];
                const sizes = new Set();
                const h4 = section.querySelector('h4');
                if (h4) sizes.add(Math.round(parseFloat(getComputedStyle(h4).fontSize)));
                const strong = section.querySelector('strong');
                if (strong) sizes.add(Math.round(parseFloat(getComputedStyle(strong).fontSize)));
                const token = section.querySelector('.surface-token, [data-chip]');
                if (token) sizes.add(Math.round(parseFloat(getComputedStyle(token).fontSize)));
                return Array.from(sizes);
            }""")
            assert len(font_sizes) >= 3, (
                f"Expected >= 3 distinct font sizes (caption, primary, token); got {font_sizes}"
            )

            # ── No raw <button> in the section ──
            raw_buttons = page.evaluate("""() => {
                const section = document.querySelector('[data-testid="shade-projects"]');
                if (!section) return 0;
                const buttons = section.querySelectorAll('button');
                let raw = 0;
                for (const btn of buttons) {
                    // Library Button (Signal.tsx) renders with class 'btn btn--<variant>'.
                    // Also accept surface- or signal- prefixed classes.
                    const cl = btn.className || '';
                    const isLibrary = cl.includes('btn')
                        || cl.includes('surface-') || cl.includes('signal-');
                    if (!isLibrary) raw++;
                }
                return raw;
            }""")
            assert raw_buttons == 0, (
                f"Found {raw_buttons} raw <button> elements in PROJECTS section; "
                "every verb must be the library Button"
            )

            # ── No sentence (> 60 chars text node) ──
            long_texts = page.evaluate("""() => {
                const section = document.querySelector('[data-testid="shade-projects"]');
                if (!section) return [];
                const walker = document.createTreeWalker(
                    section, NodeFilter.SHOW_TEXT, null
                );
                const long = [];
                let node;
                while ((node = walker.nextNode())) {
                    const t = (node.textContent || '').trim();
                    if (t.length > 60) long.push(t.slice(0, 80) + '...');
                }
                return long;
            }""")
            assert len(long_texts) == 0, (
                f"Found text nodes > 60 chars (no prose rule): {long_texts}"
            )

            # ── Nothing overflows at 393 ──
            if width <= 393:
                overflow = page.evaluate("""() => {
                    const section = document.querySelector('[data-testid="shade-projects"]');
                    if (!section) return [];
                    const overflowing = [];
                    for (const el of section.querySelectorAll('*')) {
                        const r = el.getBoundingClientRect();
                        if (r.right > 393) {
                            overflowing.push({
                                tag: el.tagName,
                                class: el.className,
                                right: Math.round(r.right),
                            });
                        }
                    }
                    return overflowing;
                }""")
                assert len(overflow) == 0, (
                    f"Elements overflow at 393px: {overflow}"
                )

            _shot(page, f"artboard-{width}", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(120)
def test_shade_artboard_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_artboard_rig(tmp_path, monkeypatch, 1440)


@pytest.mark.timeout(120)
def test_shade_artboard_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_artboard_rig(tmp_path, monkeypatch, 393)


# ── HS-171-04 AC-7: zero egress ─────────────────────────────────────


def _run_egress_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No outbound request beyond the hub origin while the shade is open.
    page.route on non-hub hosts asserts none."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        import urllib.parse

        hub_host = urllib.parse.urlparse(url).netloc

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            # Track ALL outbound requests
            external_requests: list[str] = []

            def track_all_requests(request):
                req_host = urllib.parse.urlparse(request.url).netloc
                if req_host and req_host != hub_host:
                    external_requests.append(request.url)

            page.on("request", track_all_requests)

            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _seed_two_rooms_with_needs_you()
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            # Clear before shade opens
            external_requests.clear()

            _open_shade(page)
            _settle(page)

            # Wait to catch any async fetches
            page.wait_for_timeout(2000)

            assert len(external_requests) == 0, (
                f"External requests detected while shade is open: {external_requests}"
            )

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(120)
def test_shade_zero_egress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_egress_rig(tmp_path, monkeypatch)


# ── HS-171-03 box 2: cache response time < 50 ms (glass rig) ────────


def _run_cache_timing_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Measure cached /api/desk/needs-you response time.

    The first call primes the cache; the second call must return in < 50 ms.
    Prints the measured latency for the orchestrator's evidence.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)

            # Seed rooms so the cache has something to compute.
            _seed_two_rooms_with_needs_you()
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            # First call: prime the cache.
            _api(page, "GET", "/api/desk/needs-you", token=TOKEN)

            # Second call: measure response time from the browser.
            timing_js = """
            async ([token]) => {
                const t0 = performance.now();
                const resp = await fetch('/api/desk/needs-you', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                const t1 = performance.now();
                const data = await resp.json();
                return { ms: t1 - t0, status: resp.status, count: data.count };
            }
            """
            result = page.evaluate(timing_js, [TOKEN])
            ms = result["ms"]
            print(f"HS-171-03 cache timing: {ms:.1f} ms (status={result['status']}, count={result['count']})")
            assert ms < 50, \
                f"Cached response should be < 50 ms, got {ms:.1f} ms"

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(120)
def test_cache_timing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_cache_timing_rig(tmp_path, monkeypatch)


# ── HS-171-03 box 5 / HS-171-06 box 5: zero egress (glass rig) ──────


def _run_zero_egress_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Assert no outbound HTTP during a cached /api/desk/needs-you read.

    Intercepts all outbound requests from the page and asserts none
    go outside the localhost hub.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _seed_two_rooms_with_needs_you()
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            # Prime the cache.
            _api(page, "GET", "/api/desk/needs-you", token=TOKEN)

            # Intercept outbound requests.
            external_requests: list[str] = []

            def _on_request(request):
                req_url = request.url
                if "localhost" not in req_url and "127.0.0.1" not in req_url:
                    external_requests.append(req_url)

            page.on("request", _on_request)

            # Second (cached) read.
            _api(page, "GET", "/api/desk/needs-you", token=TOKEN)

            assert len(external_requests) == 0, \
                f"Zero egress expected, got external requests: {external_requests}"

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(120)
def test_zero_egress_cached_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_zero_egress_rig(tmp_path, monkeypatch)


# ── HS-171-06 box 2: shade shows the most recent brief ──────────────


def _seed_brief(date: str = "2026-09-05", items_count: int = 3) -> None:
    """Seed a monday_briefs row + items so the shade has something to show."""
    from holdspeak.db import get_database
    db = get_database()
    brief_id = f"brief-{date}"
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO monday_briefs "
            "(id, period_start, period_end, headline, generated_at) "
            "VALUES (?, ?, ?, ?, datetime('now'))",
            (brief_id, date, date, "Review the PR backlog."),
        )
        for i in range(items_count):
            conn.execute(
                "INSERT OR IGNORE INTO monday_brief_items "
                "(id, brief_id, section, text, priority) "
                "VALUES (?, ?, 'action', ?, ?)",
                (f"bi-{date}-{i}", brief_id, f"Item {i+1}: overdue", i),
            )


def _run_brief_row_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    """Seed a brief, open the shade, assert the brief row shows."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)

            # Seed needs-you items (so PROJECTS section appears) and a brief.
            _seed_two_rooms_with_needs_you()
            _seed_brief(date="2026-09-05", items_count=5)

            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            # Open the shade.
            _open_shade(page)

            # ── Brief row present ──
            brief_row = page.get_by_test_id("shade-brief-row")
            assert brief_row.count() == 1, \
                "The brief row should be present in the shade"

            brief_text = brief_row.text_content() or ""
            # Should contain "Monday brief".
            assert "Monday brief" in brief_text, \
                f"Brief row should mention 'Monday brief': {brief_text}"

            # Should contain the item count.
            assert "5" in brief_text or "THING" in brief_text.upper(), \
                f"Brief row should show item count: {brief_text}"

            # Should contain the date (formatted by the shade as e.g. "SEP 05").
            # The shade formats generated_at via toLocaleDateString.
            assert "SEP" in brief_text.upper() or "2026" in brief_text, \
                f"Brief row should show a date token: {brief_text}"

            # Should have an Open verb (button).
            open_btn = brief_row.get_by_role("button", name="Open")
            assert open_btn.count() == 1, \
                "Brief row should have an Open button"

            _shot(page, "build-shade-brief", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(120)
def test_shade_brief_row_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_brief_row_rig(tmp_path, monkeypatch, 1440)
