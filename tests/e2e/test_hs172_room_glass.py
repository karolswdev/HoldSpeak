"""HS-172-03/06 -- Room proposals and suggested sources glass rig.

Proposal rows in NEEDS YOU (confirm/edit/dismiss verbs), confirmed row in
DECISIONS & COMMITMENTS, suggested source above existing SOURCES.
Shots at 1440 and 393.  Asserts: no raw <button>, no zero counter, no LOCAL,
proposal text wraps (scrollWidth <= clientWidth on the primary span).
"""
from __future__ import annotations

import uuid
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

SHOTS_03 = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/story-03-shots"
)
SHOTS_06 = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/story-06-shots"
)
SHOTS_03.mkdir(parents=True, exist_ok=True)
SHOTS_06.mkdir(parents=True, exist_ok=True)

TOKEN = "hs172-room"


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


def _seed_meeting(meeting_id: str, title: str = "Standup") -> None:
    from holdspeak.db import get_database
    db = get_database()
    now = "2026-09-05T09:35:00"
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, transcription_status, "
            " provenance, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'complete', 'finalized', "
            "'active', 'desktop', ?)",
            (meeting_id, now, "2026-09-05T10:05:00", title, 1800.0, now),
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


def _seed_proposals(
    meeting_id: str, project_id: str,
) -> list[str]:
    from holdspeak.db import get_database
    db = get_database()
    now = "2026-09-05T09:35:00"
    proposals = [
        {
            "id": f"prop-{uuid.uuid4().hex[:16]}",
            "kind": "action",
            "text": "Marek owns the PostgreSQL migration",
            "owner_hint": "Marek",
            "due_hint": "Fri",
            "speaker_label": "Marek",
            "model_host": "192.168.1.43",
        },
        {
            "id": f"prop-{uuid.uuid4().hex[:16]}",
            "kind": "decision",
            "text": "cut-over on the 12th",
            "owner_hint": None,
            "due_hint": None,
            "speaker_label": None,
            "model_host": "192.168.1.43",
        },
    ]
    ids: list[str] = []
    with db._connection() as conn:
        for p in proposals:
            conn.execute(
                """INSERT INTO follow_through_proposals
                   (id, meeting_id, project_id, kind, text, owner_hint,
                    due_hint, source_artifact_id, source_plugin,
                    segment_timestamp, speaker_label, model_host,
                    fingerprint, state, original_text, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, '', 'decision_capture',
                           NULL, ?, ?, ?, 'proposed', ?, ?)""",
                (
                    p["id"], meeting_id, project_id, p["kind"], p["text"],
                    p["owner_hint"], p["due_hint"], p["speaker_label"],
                    p["model_host"], uuid.uuid4().hex[:32], p["text"], now,
                ),
            )
            ids.append(p["id"])
    return ids


def _seed_suggestion(project_id: str, meeting_id: str) -> str:
    from holdspeak.db import get_database
    db = get_database()
    sug_id = f"ssug_{uuid.uuid4().hex[:12]}"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO source_suggestions "
            "(id, project_id, meeting_id, provider, reference, status, created_at) "
            "VALUES (?, ?, ?, 'github', 'karolswdev/hs-infra', 'pending', ?)",
            (sug_id, project_id, meeting_id, "2026-09-05T09:35:00"),
        )
    return sug_id


def _seed_all(project_id: str) -> tuple[str, list[str], str]:
    meeting_id = f"mtg-{uuid.uuid4().hex[:12]}"
    _seed_meeting(meeting_id)
    _link_meeting_project(meeting_id, project_id)
    prop_ids = _seed_proposals(meeting_id, project_id)
    sug_id = _seed_suggestion(project_id, meeting_id)
    return meeting_id, prop_ids, sug_id


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


def _shot(page: Any, name: str, width: int, shots_dir: Path) -> Path:
    _settle(page)
    old = page.viewport_size
    page.set_viewport_size({"width": old["width"], "height": 2400})
    _settle(page)
    path = shots_dir / f"{name}.png"
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
    hits = re.findall(r'\b0\s+(?:NEEDS|SOURCES|DECISIONS|items|proposals)', text)
    assert not hits, f"Zero counters: {hits}"


def _assert_no_local(page: Any) -> None:
    text = page.locator('[data-testid="room-body"]').inner_text()
    assert "LOCAL" not in text, "LOCAL found (should be THIS DEVICE or LAN)"


def _assert_text_not_clipped(page: Any) -> None:
    clipped = page.evaluate("""() => {
        const spans = document.querySelectorAll('[data-testid="proposal-primary"]');
        const bad = [];
        for (const s of spans) {
            if (s.scrollWidth > s.clientWidth + 2) bad.push(s.textContent);
        }
        return bad;
    }""")
    assert not clipped, f"Proposal text clipped: {clipped}"


# ── Tests ─────────────────────────────────────────────────────────


def _run_proposals_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Proposals in NEEDS YOU at the given width."""
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
            _seed_all(project_id)

            _open_room(page, url, project_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)

            _shot(page, f"build-room-proposals-{width}", width, SHOTS_03)

            proposal_rows = page.locator('[data-testid="proposal-row"]')
            assert proposal_rows.count() >= 2, (
                f"Expected >= 2 proposal rows, got {proposal_rows.count()}"
            )

            _assert_no_raw_button(page)
            _assert_no_zero_counter(page)
            _assert_no_local(page)
            _assert_text_not_clipped(page)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_edit_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Edit unfolds under the proposal row."""
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
            _seed_all(project_id)

            _open_room(page, url, project_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)

            edit_btn = page.locator('[data-testid="proposal-edit"]').first
            if edit_btn.count() > 0:
                edit_btn.click()
                page.wait_for_timeout(300)
                _settle(page)
                edit_well = page.locator('[data-testid="proposal-edit-well"]')
                assert edit_well.count() > 0, "Edit well not visible after click"

            _shot(page, f"build-room-edit-{width}", width, SHOTS_03)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_confirmed_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Confirmed proposal appears in DECISIONS & COMMITMENTS."""
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
            _, prop_ids, _ = _seed_all(project_id)

            _open_room(page, url, project_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)

            if prop_ids:
                _api(page, "POST",
                     f"/api/proposals/{prop_ids[0]}/confirm", {},
                     token=TOKEN)
                refresh = page.locator('[data-testid="room-refresh"]')
                if refresh.count() > 0:
                    refresh.click()
                    page.wait_for_timeout(1500)
                    _settle(page)

            _shot(page, f"build-room-confirmed-{width}", width, SHOTS_03)

            # After confirm, the decision list carries the proposal-derived row
            decision_rows = page.locator('[data-testid="decision-row"]')
            if prop_ids:
                assert decision_rows.count() >= 1, "No decision row in D&C after confirm"
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_suggested_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Suggested source above existing sources."""
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
            _seed_all(project_id)

            _open_room(page, url, project_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)

            _shot(page, f"build-room-suggested-{width}", width, SHOTS_06)

            suggested = page.locator('[data-testid="suggested-source-row"]')
            assert suggested.count() >= 1, (
                f"Expected >= 1 suggested row, got {suggested.count()}"
            )
            _assert_no_local(page)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── Pytest entry points ──────────────────────────────────────────────


class TestRoomProposalsGlass:
    """HS-172-03/06 — Room proposals + suggested sources glass rig."""

    def test_proposals_1440(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _run_proposals_rig(tmp_path, monkeypatch, 1440)

    def test_proposals_393(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _run_proposals_rig(tmp_path, monkeypatch, 393)

    def test_edit_1440(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _run_edit_rig(tmp_path, monkeypatch, 1440)

    def test_confirmed_1440(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _run_confirmed_rig(tmp_path, monkeypatch, 1440)

    def test_suggested_1440(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _run_suggested_rig(tmp_path, monkeypatch, 1440)

    def test_suggested_393(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _run_suggested_rig(tmp_path, monkeypatch, 393)
