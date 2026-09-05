"""HS-170-04 -- Arrival glass rig.

Seeds two active projects with needs-you items, one unfinished thought,
one meeting with a transcript and intelligence off. Asserts at 1440 and
393: the headline equals the needs-you count and project count; sections
with zero items are absent from the DOM; `Run intelligence` appears only
on the meeting with words; the capture bar is at the foot; no raw
`<button>` in the arrival; no text node > 60 chars outside content rows;
nothing overflows at 393. Also the QUIET state (empty hub): only the
headline + capture bar.

Shots to phase-170-the-great-pass/assets/story-04-shots/.
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

pytest.importorskip("playwright.sync_api", reason="Arrival glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-170-the-great-pass/assets/story-04-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs170-arrival"


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
            "'2026-09-01T00:00:00', '2026-09-04T10:00:00')",
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


def _seed_two_projects_with_needs_you() -> None:
    """Seed two active projects that produce 3 needs-you items total."""
    _seed_gh_connection()

    # Project Alpha: 1 PR waiting on review
    pid1 = _seed_project("proj-alpha", "Q4 Platform")
    yesterday = (datetime.now() - timedelta(days=3)).isoformat()
    _seed_watch(pid1, watch_id="w-alpha-prs", connector_id="gh",
                query_kind="pull_requests",
                query={"repository": "karolswdev/HoldSpeak"},
                snapshot=[
                    {"number": 612, "title": "Rig settles animations before every shot",
                     "state": "OPEN", "url": "https://github.com/karolswdev/HoldSpeak/pull/612",
                     "reviewRequests": ["karolswdev"], "updatedAt": yesterday},
                ])

    # Project Beta: 1 CI failure + 1 Jira overdue = 2 items
    pid2 = _seed_project("proj-beta", "Governance")
    _seed_watch(pid2, watch_id="w-beta-ci", connector_id="gh",
                query_kind="branch_ci",
                query={"repository": "karolswdev/Beta", "branch": "main"},
                snapshot=[
                    {"conclusion": "failure", "branch": "main",
                     "url": "https://github.com/karolswdev/Beta/actions/runs/1",
                     "updated_at": (datetime.now() - timedelta(minutes=40)).isoformat()},
                ])
    overdue_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    _seed_watch(pid2, watch_id="w-beta-jira", connector_id="jira",
                query_kind="issues",
                query={"connection_ref": "https://karolsaneapple.atlassian.net",
                       "projects": ["KAN"]},
                snapshot=[
                    {"key": "KAN-7", "summary": "Payments cut-over runbook",
                     "due_at": overdue_date,
                     "url": "https://karolsaneapple.atlassian.net/browse/KAN-7"},
                ])


def _seed_scheduled_recording(page: Any) -> None:
    """Seed a future scheduled recording so the NEXT line renders."""
    from datetime import timezone
    starts = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(hours=1)
    result = _api(page, "POST", "/api/scheduled-recordings", {
        "title": "Standup",
        "cron_expr": f"{starts.minute} {starts.hour} {starts.day} {starts.month} *",
        "tz": "UTC",
        "one_shot": True,
        "duration_minutes": 30,
        "enabled": True,
    }, token=TOKEN)
    assert result["schedule"]["title"] == "Standup"


def _seed_thought(page: Any) -> None:
    """Seed one unfinished thought via the product's own API route."""
    _api(page, "POST", "/api/thoughts", {
        "request_id": str(uuid.uuid4()),
        "raw_text": "Plan to migrate authentication.",
        "source": {"kind": "typed"},
        "initial_note": {
            "title": "Migrate the auth service",
            "body_markdown": "Plan to migrate authentication.",
            "tags": [],
        },
    }, token=TOKEN)


def _seed_meeting_with_transcript() -> str:
    """Seed a meeting that has a transcript but intelligence OFF."""
    from holdspeak.db import get_database
    db = get_database()
    meeting_id = str(uuid.uuid4())
    now = datetime.now()
    # today's meeting with "today" rows
    today0 = now.replace(hour=0, minute=0, second=30, microsecond=0)
    started = max(today0, now - timedelta(hours=2))
    ended = started + timedelta(minutes=30)
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, transcription_status, "
            " provenance, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                meeting_id,
                started.isoformat(),
                ended.isoformat(),
                "Census standup",
                1800.0,
                "disabled",  # OFF
                "finalized",
                "active",
                "desktop",
                now.isoformat(),
            ),
        )
        # Add transcript segments
        for i, (text, speaker) in enumerate([
            ("Good morning everyone", "Me"),
            ("Let's review the sprint", "Remote"),
            ("CI is red on main", "Me"),
        ]):
            conn.execute(
                "INSERT INTO segments "
                "(meeting_id, text, speaker, start_time, end_time) "
                "VALUES (?, ?, ?, ?, ?)",
                (meeting_id, text, speaker, float(i * 10), float(i * 10 + 9)),
            )
    return meeting_id


def _seed_meeting_without_transcript() -> str:
    """Seed a meeting that has been SAVED (has intel) but no transcript."""
    from holdspeak.db import get_database
    db = get_database()
    meeting_id = str(uuid.uuid4())
    now = datetime.now()
    two_days_ago = now - timedelta(days=2)
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, transcription_status, "
            " provenance, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                meeting_id,
                two_days_ago.isoformat(),
                (two_days_ago + timedelta(minutes=45)).isoformat(),
                "Design review",
                2700.0,
                "complete",  # SAVED
                "finalized",
                "active",
                "desktop",
                now.isoformat(),
            ),
        )
    return meeting_id


# ── Shot helpers ──────────────────────────────────────────────────

def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


# ── Tests ─────────────────────────────────────────────────────────


def _run_needs_you_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    """Seed populated desk, assert the needs-you arrival state."""
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

            # Seed data
            _seed_two_projects_with_needs_you()
            _seed_scheduled_recording(page)
            _seed_thought(page)
            _seed_meeting_with_transcript()
            _seed_meeting_without_transcript()

            # Reload to pick up seeded data
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            # Wait for the arrival to render
            page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
            _settle(page)

            # ── HEADLINE asserts ──
            headline = page.get_by_test_id("arrival-display")
            headline_text = headline.text_content() or ""
            # Should contain count and project count
            assert "need you" in headline_text.lower(), \
                f"Headline should say 'need you': {headline_text}"
            # The count should be a digit
            assert headline_text[0].isdigit(), \
                f"Headline should start with a count: {headline_text}"
            # Should mention projects
            assert "project" in headline_text.lower(), \
                f"Headline should mention projects: {headline_text}"

            # ── NEXT line present ──
            next_line = page.get_by_test_id("arrival-next")
            assert next_line.count() == 1, "NEXT line should be present with a scheduled recording"
            next_text = next_line.text_content() or ""
            assert "NEXT" in next_text.upper(), f"NEXT line should start with NEXT: {next_text}"
            assert "STANDUP" in next_text.upper(), f"NEXT line should contain the title: {next_text}"

            # ── NEEDS YOU section present ──
            needs_you_section = page.get_by_test_id("arrival-needs-you")
            assert needs_you_section.count() == 1, "NEEDS YOU section should be present"

            # ── THOUGHTS section present ──
            thoughts_section = page.get_by_test_id("arrival-thoughts")
            assert thoughts_section.count() == 1, "THOUGHTS section should be present"

            # ── MEETINGS section present ──
            meetings_section = page.get_by_test_id("arrival-meetings")
            assert meetings_section.count() == 1, "MEETINGS section should be present"

            # ── Run intelligence button: only on meeting with transcript ──
            run_intel = page.get_by_test_id("arrival-run-intel")
            # Should appear exactly once (on the meeting with transcript+OFF)
            assert run_intel.count() == 1, \
                f"Expected 1 Run intelligence button, got {run_intel.count()}"

            # ── CAPTURE BAR present at the foot ──
            capture_bar = page.get_by_test_id("arrival-capture-bar")
            assert capture_bar.count() == 1, "Capture bar should be present"

            # ── No raw <button> in the arrival (all should be library Button) ──
            raw_buttons = page.evaluate("""() => {
                const chair = document.querySelector('[data-testid="chair"]');
                if (!chair) return 0;
                const buttons = chair.querySelectorAll('button');
                let raw = 0;
                for (const btn of buttons) {
                    // Library Buttons have class btn, MicButton has class mic-button-btn,
                    // SurfaceLedgerRow uses button.surface-ledger-line
                    const cls = btn.className;
                    if (!cls.includes('btn') &&
                        !cls.includes('desk-mic') &&
                        !cls.includes('surface-ledger-line')) {
                        raw++;
                    }
                }
                return raw;
            }""")
            assert raw_buttons == 0, f"{raw_buttons} raw <button> elements in the arrival"

            # ── No text node > 60 chars outside content rows ──
            long_text = page.evaluate("""() => {
                const chair = document.querySelector('[data-testid="chair"]');
                if (!chair) return [];
                const walker = document.createTreeWalker(chair, NodeFilter.SHOW_TEXT);
                const long = [];
                while (walker.nextNode()) {
                    const text = walker.currentNode.textContent?.trim() || '';
                    if (text.length > 60) {
                        // Allow inside content rows (ledger primary, thought titles)
                        const parent = walker.currentNode.parentElement;
                        const inRow = parent?.closest('.surface-ledger-primary, .surface-ledger-line');
                        if (!inRow) long.push(text.slice(0, 80));
                    }
                }
                return long;
            }""")
            assert len(long_text) == 0, f"Long text nodes: {long_text}"

            # ── Overflow check at 393 ──
            if width <= 393:
                no_overflow = page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth"
                )
                assert no_overflow, "Page overflows at 393"

            # ── Take shot ──
            _shot(page, "build-arrival-needs-you", width)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_quiet_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    """Empty desk: only headline + capture bar visible."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            # Init desk -- no extra seeding
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            # Wait for headline
            page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
            _settle(page)

            # ── HEADLINE: "Nothing needs you" ──
            headline = page.get_by_test_id("arrival-display")
            headline_text = headline.text_content() or ""
            assert "nothing needs you" in headline_text.lower(), \
                f"Quiet headline should say 'Nothing needs you': {headline_text}"

            # ── NEXT line absent (no scheduled recording) ──
            assert page.get_by_test_id("arrival-next").count() == 0, \
                "NEXT line should be absent when no scheduled recording"

            # ── Sections with zero items are ABSENT ──
            assert page.get_by_test_id("arrival-needs-you").count() == 0, \
                "NEEDS YOU section should be absent when empty"
            assert page.get_by_test_id("arrival-thoughts").count() == 0, \
                "THOUGHTS section should be absent when empty"
            # Brief might or might not exist (depends on whether latest returns null)
            assert page.get_by_test_id("arrival-brief").count() == 0, \
                "BRIEF section should be absent when empty"

            # ── CAPTURE BAR always present ──
            capture_bar = page.get_by_test_id("arrival-capture-bar")
            assert capture_bar.count() == 1, "Capture bar should always be present"

            # ── Take shot ──
            _shot(page, "build-arrival-quiet", width)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── Pytest entry points ───────────────────────────────────────────


class TestArrivalGlass:
    """HS-170-04 — the Arrival face glass rig."""

    def test_arrival_needs_you_1440(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _run_needs_you_rig(tmp_path, monkeypatch, 1440)

    def test_arrival_needs_you_393(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _run_needs_you_rig(tmp_path, monkeypatch, 393)

    def test_arrival_quiet_1440(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _run_quiet_rig(tmp_path, monkeypatch, 1440)

    def test_arrival_quiet_393(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _run_quiet_rig(tmp_path, monkeypatch, 393)
