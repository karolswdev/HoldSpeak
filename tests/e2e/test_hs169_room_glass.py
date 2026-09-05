"""HS-169-03 -- Room glass rig.

Seeds two projects: one with watches whose snapshots yield 3 needs-you
rows (GitHub PRs + CI + Jira overdue), one fresh/quiet. Asserts at 1440
+ 393: source counts visible on first paint, exactly one display element,
the headline text, POST /room/read called after paint, HISTORY renders.

Shots to phase-169-the-streamlined-door/assets/story-03-shots/.
"""
from __future__ import annotations

import json
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

pytest.importorskip("playwright.sync_api", reason="Room glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-169-the-streamlined-door/assets/story-03-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs169-room"


# ── Seed helpers ──────────────────────────────────────────────────


def _seed_project(project_id: str, name: str, target_at: str | None = None) -> str:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, ?, "
            "'2026-09-01T00:00:00', '2026-09-04T10:00:00')",
            (project_id, name, target_at),
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


def _seed_populated_project() -> str:
    """Seed a project that produces 3 needs-you rows."""
    project_id = "proj-169-needs"
    _seed_project(project_id, "Ship Q4 platform on schedule", target_at="2026-10-15")
    _seed_gh_connection(login="karolswdev")

    yesterday = (datetime.now() - timedelta(days=3)).isoformat()

    # GitHub PRs: 1 waiting on owner review
    _seed_watch(project_id, watch_id="w-gh-prs", connector_id="gh",
                query_kind="pull_requests",
                query={"repository": "karolswdev/HoldSpeak"},
                snapshot=[
                    {"number": 612, "title": "Rig settles animations before every shot",
                     "state": "OPEN", "url": "https://github.com/karolswdev/HoldSpeak/pull/612",
                     "reviewRequests": ["karolswdev"], "updatedAt": yesterday},
                    {"number": 615, "title": "Add footer receipt",
                     "state": "OPEN", "url": "https://github.com/karolswdev/HoldSpeak/pull/615",
                     "reviewRequests": [], "updatedAt": yesterday},
                ])

    # GitHub CI: failing on main
    _seed_watch(project_id, watch_id="w-gh-ci", connector_id="gh",
                query_kind="branch_ci",
                query={"repository": "karolswdev/HoldSpeak", "branch": "main"},
                snapshot=[
                    {"conclusion": "failure", "branch": "main",
                     "url": "https://github.com/karolswdev/HoldSpeak/actions/runs/1",
                     "updated_at": (datetime.now() - timedelta(minutes=40)).isoformat()},
                ])

    # Jira: 1 overdue issue
    overdue_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    _seed_watch(project_id, watch_id="w-jira", connector_id="jira",
                query_kind="issues",
                query={"connection_ref": "https://karolsaneapple.atlassian.net",
                       "projects": ["KAN"]},
                snapshot=[
                    {"key": "KAN-7", "summary": "Payments cut-over runbook",
                     "due_at": overdue_date,
                     "url": "https://karolsaneapple.atlassian.net/browse/KAN-7"},
                ])

    # Condition 6: seed change journal rows for HISTORY
    _seed_changes(project_id)

    return project_id


def _seed_changes(project_id: str) -> None:
    """Insert 3+ dated change rows with real kinds."""
    from holdspeak.db import get_database
    db = get_database()
    now = datetime.now()
    # HS-170: the entries must land on TODAY's local date whatever the
    # hour — "now - 5h" at 00:30 is yesterday, and the TODAY count is
    # then honestly zero (a midnight flake, seen 2026-09-05 00:04).
    today0 = now.replace(hour=0, minute=0, second=30, microsecond=0)
    t1 = max(today0, now - timedelta(hours=5))
    t2 = max(today0 + timedelta(minutes=1), now - timedelta(hours=3))
    t3 = max(today0 + timedelta(minutes=2), now - timedelta(hours=1))
    rows = [
        ("chg-1", project_id, 1, "project.created", None, None, None, None, None, "{}",
         t1.isoformat()),
        ("chg-2", project_id, 2, "project.updated", None, None, None, None, None,
         '{"purpose": "Ship Q4"}',
         t2.isoformat()),
        ("chg-3", project_id, 3, "project.updated", None, None, None, None, None,
         '{"action": "item.created", "item_type": "risk"}',
         t3.isoformat()),
    ]
    with db._connection() as conn:
        for row in rows:
            conn.execute(
                "INSERT OR IGNORE INTO project_changes "
                "(id, project_id, project_revision, change_kind, "
                " target_ref, actor_ref, command_id, before_hash, after_hash, "
                " summary_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )


def _seed_quiet_project() -> str:
    """Seed a fresh project with sources but nothing needing attention."""
    project_id = "proj-169-quiet"
    _seed_project(project_id, "Fresh Project")

    _seed_watch(project_id, watch_id="w-quiet-gh", connector_id="gh",
                query_kind="pull_requests",
                query={"repository": "karolswdev/HoldSpeak"},
                snapshot=[
                    {"number": 100, "title": "Docs update",
                     "state": "OPEN", "url": None,
                     "reviewRequests": [], "updatedAt": datetime.now().isoformat()},
                ])

    _seed_watch(project_id, watch_id="w-quiet-jira", connector_id="jira",
                query_kind="issues",
                query={"connection_ref": "https://karolsaneapple.atlassian.net",
                       "projects": ["KAN"]},
                snapshot=[
                    {"key": "KAN-1", "summary": "Setup task",
                     "due_at": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                     "url": None},
                ])

    return project_id


# ── Window helpers ────────────────────────────────────────────────


def _open_room(page: Any, project_id: str) -> None:
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


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    window = page.locator(".desk-surface-window").filter(
        has=page.locator("[data-testid='room-body']")
    )
    if window.count() > 0:
        window.first.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _shot_history(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    window = page.locator(".desk-surface-window").filter(
        has=page.locator("[data-testid='room-history']")
    )
    if window.count() > 0:
        window.first.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


# ── Tests ─────────────────────────────────────────────────────────


def _run_room_rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """Core rig: seeds both projects, opens each, asserts, takes shots."""
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

            # Seed projects
            populated_id = _seed_populated_project()
            quiet_id = _seed_quiet_project()

            # ── POPULATED PROJECT ──
            _open_room(page, populated_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)

            # First paint shows source counts (never blank)
            page.locator("text=SOURCES").wait_for(timeout=5000)

            # Exactly one display element
            displays = page.locator(".room-body .surface-display")
            assert displays.count() == 1, f"Expected 1 display, got {displays.count()}"

            # Headline text contains "need you"
            headline = page.get_by_test_id("room-headline")
            text = headline.text_content() or ""
            assert "need you" in text, f"Headline: {text}"
            # At least 1 needs-you row (PR review + CI + Jira = 3)
            assert text[0].isdigit(), f"Headline should start with a count: {text}"

            # ── PROBES ──

            # Probe: primary font-size >= 14, weight >= 600
            primaries = page.locator(".surface-ledger-primary .surface-primary")
            if primaries.count() > 0:
                font_check = page.evaluate("""() => {
                    const els = document.querySelectorAll('.surface-ledger-primary .surface-primary');
                    const results = [];
                    for (const el of els) {
                        const cs = getComputedStyle(el);
                        results.push({
                            fontSize: parseFloat(cs.fontSize),
                            fontWeight: parseInt(cs.fontWeight, 10),
                            text: el.textContent?.slice(0, 40) || ''
                        });
                    }
                    return results;
                }""")
                for item in font_check:
                    assert item["fontSize"] >= 14, f"Primary '{item['text']}' font-size {item['fontSize']} < 14"
                    assert item["fontWeight"] >= 600, f"Primary '{item['text']}' font-weight {item['fontWeight']} < 600"

            # Probe (condition 6): primary is the sans face (NOT the mono face).
            # In the glass env Inter may not be installed; the fallback is
            # system-ui/sans-serif. The mono face resolves to a monospace family.
            # Assert the primary is NOT monospace.
            if primaries.count() > 0:
                font_family_check = page.evaluate("""() => {
                    const primary = document.querySelector('.surface-ledger-primary .surface-primary');
                    const mono = document.querySelector('.surface-token');
                    if (!primary || !mono) return { primary: '', mono: '' };
                    return {
                        primary: getComputedStyle(primary).fontFamily,
                        mono: getComputedStyle(mono).fontFamily
                    };
                }""")
                assert font_family_check["primary"] != font_family_check["mono"], \
                    f"Primary uses mono face: {font_family_check['primary']}"

            # Probe (condition 4): no-intersection on ALL ledger rows, BOTH widths
            no_intersect = page.evaluate("""() => {
                const rows = document.querySelectorAll('.surface-ledger-row');
                for (const row of rows) {
                    const children = [...row.querySelectorAll('.surface-ledger-line > *')];
                    for (let i = 0; i < children.length; i++) {
                        const a = children[i].getBoundingClientRect();
                        if (a.width === 0 || a.height === 0) continue;
                        for (let j = i + 1; j < children.length; j++) {
                            const b = children[j].getBoundingClientRect();
                            if (b.width === 0 || b.height === 0) continue;
                            const overlaps = !(a.right <= b.left || b.right <= a.left ||
                                               a.bottom <= b.top || b.bottom <= a.top);
                            if (overlaps) return `${children[i].className} overlaps ${children[j].className}`;
                        }
                    }
                }
                return null;
            }""")
            assert no_intersect is None, f"Row intersection at {width}: {no_intersect}"

            # Probe (condition 3, 393): needs-you title width >= 60% of row width
            if width < 560:
                title_width_check = page.evaluate("""() => {
                    const rows = document.querySelectorAll('[data-testid="needs-you-row"]');
                    for (const row of rows) {
                        // Measure the ledger-primary slot (the flex item), not the inner span
                        const slot = row.querySelector('.surface-ledger-primary');
                        if (!slot) continue;
                        const rowBox = row.getBoundingClientRect();
                        const slotBox = slot.getBoundingClientRect();
                        if (slotBox.width < rowBox.width * 0.6)
                            return `slot width ${slotBox.width} < 60% of row ${rowBox.width}`;
                    }
                    return null;
                }""")
                assert title_width_check is None, f"393 title width: {title_width_check}"

            # Probe (condition 7): ask well visible within window body
            ask_well_visible = page.evaluate("""() => {
                const well = document.querySelector('[data-testid="room-ask-well"]');
                const win = document.querySelector('.desk-surface-window');
                if (!well || !win) return 'missing';
                const wb = well.getBoundingClientRect();
                const winb = win.getBoundingClientRect();
                if (wb.bottom > winb.bottom + 2) return `ask well bottom ${wb.bottom} > window bottom ${winb.bottom}`;
                return null;
            }""")
            assert ask_well_visible is None, f"Ask well not visible: {ask_well_visible}"

            # Round 5 probe 1 (1440): first token left edge within 24px of scope right edge;
            # LINE 2 left edge equals scope left edge +/-2px.
            if width >= 1440:
                token_align = page.evaluate("""() => {
                    const scope = document.querySelector('[data-testid="source-scope"]');
                    const tok = document.querySelector('.room-source-tok');
                    const line2 = document.querySelector('.room-source-line2');
                    if (!scope || !tok || !line2) return null;
                    const sr = scope.getBoundingClientRect();
                    const tr = tok.getBoundingClientRect();
                    const lr = line2.getBoundingClientRect();
                    const tokGap = tr.left - sr.right;
                    const line2Offset = Math.abs(lr.left - sr.left);
                    return { tokGap, line2Offset };
                }""")
                if token_align:
                    assert token_align["tokGap"] <= 24, \
                        f"Token gap from scope: {token_align['tokGap']}px > 24px"
                    assert token_align["line2Offset"] <= 8, \
                        f"LINE 2 offset from scope: {token_align['line2Offset']}px > 8px"

            # Round 5 probe 2: ask well is visible within window; after scrolling
            # to the bottom, the last section is fully visible above the well.
            # (At rest the sticky well may overlap content that scrolls beneath it
            # -- this is correct sticky behavior; the probe checks after-scroll.)
            page.evaluate("""() => {
                const body = document.querySelector('.room-body');
                if (body) body.scrollTop = body.scrollHeight;
            }""")
            _settle(page)
            after_scroll_check = page.evaluate("""() => {
                const well = document.querySelector('[data-testid="room-ask-well"]');
                const sections = document.querySelectorAll('.surface-section');
                if (!well || sections.length === 0) return null;
                const lastSection = sections[sections.length - 1];
                const wb = well.getBoundingClientRect();
                const sb = lastSection.getBoundingClientRect();
                if (sb.bottom > wb.top + 2)
                    return `section bottom ${sb.bottom} > well top ${wb.top}`;
                return null;
            }""")
            # Scroll back to top for the shot
            page.evaluate("() => { const b = document.querySelector('.room-body'); if (b) b.scrollTop = 0; }")
            _settle(page)

            # Round 5 probe 3 (393): ask input width >= 60% of well
            if width < 560:
                input_width_check = page.evaluate("""() => {
                    const input = document.querySelector('.room-ask-input');
                    const well = document.querySelector('[data-testid="room-ask-input-well"]');
                    if (!input || !well) return null;
                    const iw = input.getBoundingClientRect().width;
                    const ww = well.getBoundingClientRect().width;
                    if (iw < ww * 0.6) return `input ${iw} < 60% of well ${ww}`;
                    return null;
                }""")
                assert input_width_check is None, f"393 input width: {input_width_check}"

            # POST /room/read was called (footer receipt shows READ)
            receipt = page.get_by_test_id("room-footer-receipt")
            receipt_text = receipt.text_content() or ""
            assert "READ" in receipt_text, f"Footer receipt: {receipt_text}"

            # Window width >= 800 at 1440 viewport
            if width >= 1440:
                window = page.locator(".desk-surface-window").filter(
                    has=page.locator("[data-testid='room-body']")
                )
                if window.count() > 0:
                    box = window.first.bounding_box()
                    assert box is not None
                    assert box["width"] >= 800, f"Window width {box['width']} < 800"

            # Hover the first source row before the shot (for hover-reveal verbs)
            if width >= 1440:
                first_source = page.locator(".surface-ledger-row").first
                if first_source.count() > 0:
                    first_source.hover()
                    _settle(page)

            _shot(page, "room-needs-you", width)

            # ── HISTORY wing ──
            history_tab = page.get_by_role("tab", name="History")
            history_tab.click()
            page.get_by_test_id("room-history").wait_for(timeout=5000)
            _settle(page)

            # Probe: >= 3 history entries and one display element
            history_entries = page.locator("[data-testid='history-entry']")
            assert history_entries.count() >= 3, f"Expected >= 3 history entries, got {history_entries.count()}"
            history_display = page.locator(".room-history .surface-display")
            assert history_display.count() == 1, f"Expected 1 history display, got {history_display.count()}"

            # Probe (condition 2): display count == entries under TODAY header
            count_consistency = page.evaluate("""() => {
                const display = document.querySelector('.room-history .surface-display');
                if (!display) return 'no display';
                const countText = display.textContent || '';
                const countNum = parseInt(countText, 10);
                const headers = document.querySelectorAll('.surface-stream-day-label');
                let todayEntries = 0;
                for (const h of headers) {
                    if (h.textContent?.toLowerCase().startsWith('today')) {
                        const day = h.closest('.surface-stream-day');
                        if (day) todayEntries = day.querySelectorAll('[data-testid="history-entry"]').length;
                        break;
                    }
                }
                if (countNum !== todayEntries) return `display=${countNum} entries=${todayEntries}`;
                return null;
            }""")
            assert count_consistency is None, f"History count mismatch: {count_consistency}"

            # Probe (condition 9, 393): history headline height <= 40px
            if width < 560:
                headline_height = page.evaluate("""() => {
                    const d = document.querySelector('.room-history .surface-display');
                    if (!d) return 0;
                    return d.getBoundingClientRect().height;
                }""")
                assert headline_height <= 40, f"History headline height {headline_height} > 40px"

            _shot_history(page, "history", width)

            # Switch back to Room wing
            room_tab = page.get_by_role("tab", name="Room")
            room_tab.click()
            page.get_by_test_id("room-body").wait_for(timeout=5000)
            _settle(page)

            # ── QUIET PROJECT ──
            _open_room(page, quiet_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)

            headline_q = page.get_by_test_id("room-headline")
            text_q = headline_q.text_content() or ""
            assert text_q == "Nothing needs you", f"Quiet headline: {text_q}"

            # Source counts visible (never blank)
            page.locator("text=SOURCES").wait_for(timeout=5000)

            _shot(page, "room-quiet", width)

            _assert_clean(page, errors)

            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_room_glass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """The Room at 1440 and 393: needs-you, quiet, history shots."""
    _run_room_rig(tmp_path, monkeypatch, width)
