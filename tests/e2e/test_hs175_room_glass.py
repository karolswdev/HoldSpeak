"""HS-175-04 -- Room SOURCES meeting row glass rig.

Proves the meeting source row in SOURCES via a real meeting Watch
(created through ensure_meeting_watch): MTG emblem in the 52px lead
column, MEETINGS primary, N THIS WEEK and NEXT tokens, CHECKED/NEVER
StateChip, Pause verb, no EgressChip.
A Room with no linked meetings shows NO meeting row (A.8).
Seeds one GH Watch alongside so all three rows are shot together.
Shots at 1440 and 393.
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

pytest.importorskip("playwright.sync_api", reason="Room glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/assets/story-04-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs175-room"


# ── Seed helpers ─────────────────────────────────────────────────────


def _seed_project(name: str = "Ship the Q4 platform on schedule") -> str:
    from holdspeak.db import get_database
    db = get_database()
    project_id = f"proj-{uuid.uuid4().hex[:12]}"
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


def _seed_meeting(
    meeting_id: str,
    title: str = "Standup",
    started_at: str = "2026-09-05T09:35:00",
    intel_status: str = "complete",
) -> None:
    from holdspeak.db import get_database
    db = get_database()
    now = started_at
    ended_at_dt = datetime.fromisoformat(started_at) + timedelta(minutes=30)
    ended_at = ended_at_dt.isoformat()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, transcription_status, "
            " provenance, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'finalized', "
            "'active', 'desktop', ?)",
            (meeting_id, now, ended_at, title, 1800.0, intel_status, now),
        )


def _link_meeting_project(meeting_id: str, project_id: str) -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meeting_projects (meeting_id, project_id) "
            "VALUES (?, ?)",
            (meeting_id, project_id),
        )


def _seed_intel_attempt(
    meeting_id: str,
    outcome: str = "success",
    created_at: str = "2026-09-05T10:00:00",
) -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        conn.execute(
            "INSERT INTO intel_jobs "
            "(job_id, meeting_id, work_descriptor_sha256, transcript_hash, status) "
            "VALUES (?, ?, 'abc', 'def', 'completed')",
            (job_id, meeting_id),
        )
        conn.execute(
            "INSERT INTO intel_job_attempts "
            "(meeting_id, job_id, attempt, outcome, created_at) "
            "VALUES (?, ?, 1, ?, ?)",
            (meeting_id, job_id, outcome, created_at),
        )


def _seed_decision(meeting_id: str, text: str = "Refactor the API") -> str:
    from holdspeak.db import get_database
    db = get_database()
    rid = f"dr-{uuid.uuid4().hex[:8]}"
    sid = f"drs-{uuid.uuid4().hex[:8]}"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO decision_records "
            "(id, decision_text, source_type, source_id, created_at, updated_at) "
            "VALUES (?, ?, 'meeting', ?, datetime('now'), datetime('now'))",
            (rid, text, meeting_id),
        )
        conn.execute(
            "INSERT INTO decision_record_sources "
            "(id, record_id, source_type, source_ref, created_at) "
            "VALUES (?, ?, 'meeting', ?, datetime('now'))",
            (sid, rid, meeting_id),
        )
    return rid


def _seed_gh_watch(project_id: str) -> str:
    """Seed one GitHub Watch so GH + MTG rows appear together."""
    from holdspeak.db import get_database
    db = get_database()
    watch_id = f"w_gh_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now().isoformat(timespec="seconds")
    query = {"repository": "karolswdev/HoldSpeak"}
    with db._connection() as conn:
        db.automations.create_watch_in_transaction(
            conn,
            watch_id=watch_id,
            connector_id="gh",
            query_kind="pull_requests",
            name="GitHub PRs",
            query_json=json.dumps(query, sort_keys=True),
            enabled=True,
            schema_version="WatchSpec@1",
            project_id=project_id,
            intent="Track PRs",
            subject_kind="pull_requests",
            trigger_kind="poll",
            trigger_json="{}",
            mode="yolo",
            state="active",
            revision=1,
            baseline_state="",
            test_state="",
            created_at=now_iso,
            updated_at=now_iso,
        )
    return watch_id


def _ensure_meeting_watch(project_id: str) -> str | None:
    """Create the meeting Watch via the real seam."""
    from holdspeak.db import get_database
    from holdspeak.services.watch_service import ensure_meeting_watch
    db = get_database()
    result = ensure_meeting_watch(db, project_id)
    return result.get("id") if result else None


# ── Surface helpers ──────────────────────────────────────────────────


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)


def _open_room(page: Any, url: str, project_id: str) -> None:
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


def _window(page: Any) -> Any:
    return page.locator(".desk-surface-window").filter(
        has=page.locator('[data-testid="room-body"]')
    ).first


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    old = page.viewport_size
    page.set_viewport_size({"width": old["width"], "height": 2400})
    _settle(page)
    path = SHOTS / f"{name}.png"
    win = _window(page)
    if win.count() > 0:
        win.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    page.set_viewport_size(old)
    assert path.stat().st_size > 2_000, f"Shot {name} too small"
    return path


# ── Shared assertions ────────────────────────────────────────────────


def _assert_no_raw_button(page: Any) -> None:
    raw = page.evaluate("""() => {
        const body = document.querySelector('[data-testid="room-body"]');
        if (!body) return [];
        const btns = body.querySelectorAll('button');
        const raw = [];
        for (const b of btns) {
            if (b.classList.contains('btn') ||
                b.classList.contains('signal-button') ||
                b.classList.contains('surface-ledger-line') ||
                b.classList.contains('surface-edit-in-place') ||
                b.closest('.gadget-string') ||
                b.closest('.mic-button') ||
                b.classList.contains('desk-mic')) continue;
            raw.push(b.outerHTML.slice(0, 120));
        }
        return raw;
    }""")
    assert not raw, f"Raw <button>: {raw}"


def _assert_no_zero_counter(page: Any) -> None:
    import re
    text = page.locator('[data-testid="room-body"]').inner_text()
    hits = re.findall(r'\b0\s+(?:NEEDS|SOURCES|MEETINGS|DECISIONS|items)', text)
    assert not hits, f"Zero counters: {hits}"


def _assert_no_egress_on_meeting(page: Any) -> None:
    """No EgressChip on the meeting source row (local read, no egress)."""
    egress = page.evaluate("""() => {
        const row = document.querySelector('[data-testid="source-meeting-row"]');
        if (!row) return [];
        const chips = row.querySelectorAll('.surface-egress-chip, [data-scope]');
        return Array.from(chips).map(c => c.textContent.trim());
    }""")
    assert not egress, f"EgressChip on meeting row: {egress}"


# ── Seed combos ──────────────────────────────────────────────────────


def _seed_room_with_meetings(project_id: str) -> tuple[str, str]:
    """Seed two meetings linked to the project, one in the future.

    Creates the meeting Watch through the real seam (ensure_meeting_watch).
    Also seeds one GH Watch so all source rows appear together.

    Returns (past_meeting_id, future_meeting_id).
    """
    now = datetime.now()
    # Past meeting: yesterday
    past_dt = now - timedelta(days=1)
    past_iso = past_dt.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    past_mid = f"mtg-past-{uuid.uuid4().hex[:8]}"
    _seed_meeting(past_mid, title="Architecture Review", started_at=past_iso)
    _link_meeting_project(past_mid, project_id)
    _seed_intel_attempt(past_mid, created_at=past_iso)
    _seed_decision(past_mid, text="Refactor the API layer")

    # Future meeting: tomorrow
    future_dt = now + timedelta(days=1)
    future_iso = future_dt.replace(hour=14, minute=0, second=0, microsecond=0).isoformat()
    future_mid = f"mtg-future-{uuid.uuid4().hex[:8]}"
    _seed_meeting(future_mid, title="Sprint Planning", started_at=future_iso,
                  intel_status="disabled")
    _link_meeting_project(future_mid, project_id)

    # Create the meeting Watch via the real seam
    _ensure_meeting_watch(project_id)

    # Seed one GH Watch so GH + MTG rows appear together
    _seed_gh_watch(project_id)

    return past_mid, future_mid


# ── Test runners ─────────────────────────────────────────────────────


def _run_meeting_source_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Meeting source row present in SOURCES when meetings are linked."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        height = 900 if width >= 1440 else 852
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: errors.append(str(e)))

            _init_desk(page, url)
            project_id = _seed_project()
            _seed_room_with_meetings(project_id)

            _open_room(page, url, project_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)

            # Shoot the face
            shot_name = f"room-sources-meetings-{width}"
            _shot(page, shot_name, width)

            # Assert: meeting source row present
            mtg_row = page.locator('[data-testid="source-meeting-row"]')
            assert mtg_row.count() >= 1, (
                f"Expected meeting source row, got {mtg_row.count()}"
            )

            # Assert: MTG emblem in the lead slot
            lead_text = page.evaluate("""() => {
                const row = document.querySelector('[data-testid="source-meeting-row"]');
                if (!row) return '';
                const lead = row.querySelector('.surface-ledger-lead');
                return lead ? lead.textContent.trim() : '';
            }""")
            assert lead_text == "MTG", f"Expected MTG emblem, got {lead_text!r}"

            # Assert: MEETINGS primary
            scope = page.evaluate("""() => {
                const row = document.querySelector('[data-testid="source-meeting-row"]');
                if (!row) return '';
                const scope = row.querySelector('[data-testid="source-scope"]');
                return scope ? scope.textContent.trim() : '';
            }""")
            assert scope == "MEETINGS", f"Expected MEETINGS scope, got {scope!r}"

            # Assert: tokens present (at least THIS WEEK or NEXT)
            tokens = page.evaluate("""() => {
                const row = document.querySelector('[data-testid="source-meeting-row"]');
                if (!row) return [];
                const toks = row.querySelectorAll('[data-testid="source-meeting-token"]');
                return Array.from(toks).map(t => t.textContent.trim());
            }""")
            token_text = " ".join(tokens)
            assert "THIS WEEK" in token_text or "NEXT" in token_text, (
                f"Expected THIS WEEK or NEXT token, got: {tokens}"
            )

            # Assert: CHECKED/NEVER StateChip on line 2
            checked = page.locator('[data-testid="source-meeting-checked"]')
            assert checked.count() >= 1, "Expected CHECKED/NEVER chip"
            checked_text = checked.first.inner_text()
            assert "CHECKED" in checked_text or "NEVER" in checked_text, (
                f"Expected CHECKED or NEVER, got {checked_text!r}"
            )

            # Assert: Pause verb present (real Watch backing)
            pause_btn = page.locator('[data-testid="source-meeting-verb"]')
            assert pause_btn.count() >= 1, "Expected Pause verb on meeting row"
            pause_text = pause_btn.first.inner_text()
            assert pause_text in ("Pause", "Resume"), (
                f"Expected Pause or Resume, got {pause_text!r}"
            )

            # Assert: no EgressChip on the meeting row
            _assert_no_egress_on_meeting(page)

            # Assert: SOURCES count includes the meeting row (>= 2: GH + MTG)
            import re
            sources_label = page.evaluate("""() => {
                const sections = document.querySelectorAll(
                    '.surface-section-head, .surface-section-label'
                );
                for (const s of sections) {
                    const t = (s.textContent || '').trim();
                    if (t.startsWith('SOURCES')) return t;
                }
                return '';
            }""")
            assert "SOURCES" in sources_label, f"SOURCES section not found"
            m = re.search(r"SOURCES\s+(\d+)", sources_label)
            if m:
                count = int(m.group(1))
                assert count >= 2, f"SOURCES count {count} should include GH + MTG"

            _assert_no_raw_button(page)
            _assert_no_zero_counter(page)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_no_meetings_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Room with no linked meetings shows NO meeting row (A.8)."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            _init_desk(page, url)
            project_id = _seed_project("Empty Room")

            _open_room(page, url, project_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)

            # Assert: no meeting source row
            mtg_row = page.locator('[data-testid="source-meeting-row"]')
            assert mtg_row.count() == 0, (
                f"Expected no meeting source row, got {mtg_row.count()}"
            )

            # No zero counter
            _assert_no_zero_counter(page)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── Pytest entry points ──────────────────────────────────────────────


class TestRoomMeetingSourceGlass:
    """HS-175-04 -- Room SOURCES meeting row glass rig."""

    def test_meeting_source_1440(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _run_meeting_source_rig(tmp_path, monkeypatch, 1440)

    def test_meeting_source_393(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _run_meeting_source_rig(tmp_path, monkeypatch, 393)

    def test_no_meetings_no_row(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _run_no_meetings_rig(tmp_path, monkeypatch)
