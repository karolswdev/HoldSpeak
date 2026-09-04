"""HS-159-06 real-hub Interview glass.

The browser receives the production bundle and talks to a real
MeetingWebServer.  The interview setup flow -- answer two questions,
receive native suggestions seeded from real desk facts, select/test
one, reload to resume, finalize to an honest Project Room.

Seeding gaps (DB-layer only, no HTTP route exists):
  - Meetings: db.meetings.save_meeting(MeetingState) -- no POST /api/meetings
  - Decisions: direct INSERT INTO decisions -- no POST /api/decisions
  - Action items (Door): direct INSERT INTO action_items -- no POST /api/door
Each gap is noted for the next phase (the 158 precedent).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _api, _assert_clean, _normal_chair, _ensure_build

pytest.importorskip("playwright.sync_api", reason="Interview glass needs Playwright")

TOKEN = "hs159-interview-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-159-the-interview/assets/story-06-shots"

OUTCOME_TEXT = "Ship the Q4 Payments Platform on time with zero incidents"
SIGNALS_TEXT = "Missed sprint commitments, overdue action items, stale decisions"


# ── Boot / helpers ────────────────────────────────────────────────


def _init_desk(page: Any, url: str) -> None:
    """Navigate to the hub root, seed the desk, complete onboarding."""
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)


def _open_interview(page: Any, url: str) -> None:
    """Open the project-setup surface via the staged-surface-open mechanism.

    This is more deterministic than driving the desk.new-project verb
    through the menu -- it avoids multi-step menu navigation and directly
    stages the intent that SurfaceWindows consumes on mount.
    """
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["project-setup"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


# ── Seeding ───────────────────────────────────────────────────────


def _seed_desk_facts(tmp_path: Path) -> None:
    """Seed meetings, decisions, and overdue action items via the DB layer.

    All three are DB-layer gaps: no HTTP POST route exists for creating
    meetings, decisions, or raw action items.  Each gap is noted.
    """
    from holdspeak.db import get_database
    from holdspeak.meeting_session.models import MeetingState

    db = get_database()

    # 1. Meeting (DB gap: no POST /api/meetings)
    db.meetings.save_meeting(MeetingState(
        id="m-glass-001",
        started_at=datetime(2026, 8, 20, 10, 0),
        title="Sprint 7 Planning",
        capture_status="finalized",
    ))

    # 2. Decision with lifecycle 'accepted' (DB gap: no POST /api/decisions)
    now_iso = datetime.now().isoformat()
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decisions (
                   id, text, rationale, decided_at, date_basis,
                   source_timestamp, provenance_label,
                   source_artifact_id, source_meeting_id,
                   source_state, project_key, lifecycle,
                   superseded_by, created_at, updated_at, last_modified, deleted
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "dec-glass-001",
                "Adopt event sourcing for the payment ledger",
                "Reduces audit risk and enables real-time settlement views",
                "2026-08-15T14:30:00",
                "meeting_date",
                None,
                "reported",
                "artifact-glass-001",
                "m-glass-001",
                "linked",
                None,
                "accepted",
                None,
                now_iso, now_iso, now_iso, 0,
            ),
        )

    # 3. Overdue action item for Door (DB gap: no POST /api/door)
    past_due = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO action_items (
                   id, meeting_id, task, owner, due, status,
                   review_state, created_at, source_type, source_ref
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "ai-glass-001",
                "m-glass-001",
                "Update PCI compliance docs for new gateway",
                "karol",
                past_due,
                "pending",
                "accepted",
                now_iso,
                "meeting",
                "",
            ),
        )


# ── Tests ─────────────────────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_interview_walk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Full interview walk: questions -> suggestions -> select -> test
    -> RELOAD resume -> review -> finalize -> Room opens non-empty.
    Zero false historical events."""
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
            _seed_desk_facts(tmp_path)
            _open_interview(page, url)

            # ── Step 1: Answer outcome ──
            q_outcome = page.get_by_test_id("setup-question-outcome")
            q_outcome.wait_for(timeout=15000)
            textarea = q_outcome.locator("textarea")
            textarea.fill(OUTCOME_TEXT)
            textarea.press("Enter")

            # ── Step 2: Answer signals ──
            q_signals = page.get_by_test_id("setup-question-signals")
            q_signals.wait_for(timeout=15000)
            textarea2 = q_signals.locator("textarea")
            textarea2.fill(SIGNALS_TEXT)
            textarea2.press("Enter")

            # ── Step 3: Suggestions appear ──
            cards = page.get_by_test_id("setup-suggestion-cards")
            cards.wait_for(timeout=20000)

            # Assert at least 2 suggestion cards rendered
            card_elements = cards.locator('[role="option"]')
            card_elements.first.wait_for(timeout=10000)
            card_count = card_elements.count()
            assert card_count >= 2, f"Expected >=2 cards, got {card_count}"

            # Each card has a visible rationale
            for i in range(card_count):
                card = card_elements.nth(i)
                rationale = card.locator(".setup-card-rationale")
                assert rationale.is_visible(), f"Card {i} rationale not visible"

            # ── Face shot: question plane with collapsed answers ──
            if width == 1440:
                # Verify the collapsed answer rows are visible
                answer_outcome = page.get_by_test_id("setup-answer-outcome")
                answer_outcome.wait_for(timeout=5000)
                assert answer_outcome.is_visible()

                shot = SHOTS / "face-cards-1440.png"
                page.screenshot(path=str(shot), full_page=False)
                assert shot.exists() and shot.stat().st_size > 20_000

            if width == 393:
                shot = SHOTS / "face-cards-393.png"
                page.screenshot(path=str(shot), full_page=False)
                assert shot.exists() and shot.stat().st_size > 20_000

            # ── Step 4: Select the first card ──
            first_card = card_elements.first
            first_card.click()
            # Wait for selection to register (aria-selected=true)
            first_card_id_attr = first_card.get_attribute("data-testid")
            page.wait_for_function(
                """(testid) => {
                    const el = document.querySelector(`[data-testid="${testid}"]`);
                    return el && el.getAttribute('aria-selected') === 'true';
                }""",
                arg=first_card_id_attr,
                timeout=10000,
            )

            # ── Step 5: Test the selected card ──
            test_btn = first_card.locator(".setup-card-test-btn")
            test_btn.wait_for(timeout=5000)
            test_btn.click()

            # Wait for test result to appear inside the card
            # SuggestionCard renders .setup-card-test with data-test-state
            test_result = first_card.locator(".setup-card-test")
            test_result.wait_for(timeout=15000)
            assert test_result.is_visible()

            # Verify test result shows "Test passed" with match count
            result_text = test_result.inner_text()
            assert "Test passed" in result_text, f"Expected 'Test passed', got: {result_text}"
            assert "current match" in result_text, f"Expected match count, got: {result_text}"

            # ── Step 6: RELOAD the page ──
            # Store the session_id for resume verification
            session_id = page.evaluate(
                """() => sessionStorage.getItem('hs.project-setup.session-id')"""
            )
            assert session_id, "Session ID should be in sessionStorage before reload"

            page.reload(wait_until="load")
            _normal_chair(page)

            # The face must resume: re-open the interview surface
            _open_interview(page, url)

            # ── Step 7: Verify resume ──
            # After resume, the controller rehydrates at the proposals stage
            # because both answers were submitted and suggestions generated.
            # The collapsed answer rows should reappear.
            answer_outcome_resumed = page.get_by_test_id("setup-answer-outcome")
            answer_outcome_resumed.wait_for(timeout=15000)
            assert answer_outcome_resumed.is_visible()

            # Verify the outcome text was restored
            answer_text = answer_outcome_resumed.locator(".setup-answer-text")
            if answer_text.count() > 0:
                restored_outcome = answer_text.inner_text()
                assert OUTCOME_TEXT in restored_outcome or restored_outcome in OUTCOME_TEXT, (
                    f"Outcome not restored: {restored_outcome}"
                )

            # Verify signal answer was also restored
            answer_signals_resumed = page.get_by_test_id("setup-answer-signals")
            answer_signals_resumed.wait_for(timeout=10000)
            assert answer_signals_resumed.is_visible()

            # Verify suggestion cards are back
            cards_resumed = page.get_by_test_id("setup-suggestion-cards")
            cards_resumed.wait_for(timeout=15000)
            card_elements_resumed = cards_resumed.locator('[role="option"]')
            card_elements_resumed.first.wait_for(timeout=10000)
            assert card_elements_resumed.count() >= 2, "Cards should be restored after resume"

            # Verify the session ID survived
            session_id_after = page.evaluate(
                """() => sessionStorage.getItem('hs.project-setup.session-id')"""
            )
            assert session_id_after == session_id, (
                f"Session ID changed: {session_id} -> {session_id_after}"
            )

            # ── Step 8: Advance to review ──
            proceed_btn = page.get_by_test_id("setup-proceed-review")
            proceed_btn.wait_for(timeout=10000)
            proceed_btn.click()

            # Wait for the review screen
            review = page.get_by_test_id("setup-review")
            review.wait_for(timeout=10000)
            assert review.is_visible()

            # Verify review content
            review_outcome = page.get_by_test_id("review-outcome")
            review_outcome.wait_for(timeout=5000)
            assert review_outcome.is_visible()

            review_signals = page.get_by_test_id("review-signals")
            assert review_signals.is_visible()

            review_watches = page.get_by_test_id("review-watches")
            assert review_watches.is_visible()

            _assert_clean(page, errors)

            # ── Shot: activation review ──
            if width == 1440:
                shot_review = SHOTS / "walk-review-1440.png"
                page.screenshot(path=str(shot_review), full_page=False)
                assert shot_review.exists() and shot_review.stat().st_size > 20_000

            # ── Step 9: Finalize ──
            activate_btn = page.get_by_test_id("review-activate-btn")
            activate_btn.click()

            # Wait for the done state (the face transitions to "setup-done")
            done = page.get_by_test_id("setup-done")
            done.wait_for(timeout=20000)

            # Wait for the Project Room to open (the finalize handler
            # calls openSurface("open-project-memory", `project:{id}`))
            room_name = page.get_by_test_id("project-room-name")
            room_name.wait_for(timeout=20000)
            assert room_name.is_visible()

            # The Room should be NON-EMPTY: orientation band visible
            band = page.get_by_test_id("orientation-band")
            band.wait_for(timeout=10000)
            assert band.is_visible()

            _assert_clean(page, errors)

            # ── Shot: opened Room ──
            if width == 1440:
                shot_room = SHOTS / "walk-room-after-1440.png"
                page.screenshot(path=str(shot_room), full_page=False)
                assert shot_room.exists() and shot_room.stat().st_size > 20_000

            if width == 393:
                shot_393 = SHOTS / "walk-interview-393.png"
                page.screenshot(path=str(shot_393), full_page=False)
                assert shot_393.exists() and shot_393.stat().st_size > 20_000

            # ── Step 10: Zero false historical events ──
            # The ONLY service event should be project.created with source="setup".
            # No false watch-triggered events should exist.
            from holdspeak.db import get_database
            db = get_database()
            with db._connection() as conn:
                events = conn.execute(
                    "SELECT * FROM service_events ORDER BY created_at"
                ).fetchall()
            # Filter to project-related events
            project_events = [
                dict(e) for e in events
                if "project" in (e["event_type"] or "")
            ]
            # Exactly one project.created event, no false historical events
            assert len(project_events) == 1, (
                f"Expected 1 project event, got {len(project_events)}: "
                f"{[e['event_type'] for e in project_events]}"
            )
            assert project_events[0]["event_type"] == "project.created"

            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_interview_face_shots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Face shots at key stops for the orchestrator's beauty review.

    Shot: face-questions-1440 -- question plane with live brief and
    a collapsed answer visible.
    """
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
                viewport={"width": 1440, "height": 900},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            _seed_desk_facts(tmp_path)
            _open_interview(page, url)

            # Answer outcome first
            q_outcome = page.get_by_test_id("setup-question-outcome")
            q_outcome.wait_for(timeout=15000)
            textarea = q_outcome.locator("textarea")
            textarea.fill(OUTCOME_TEXT)
            textarea.press("Enter")

            # Now on signals step -- outcome is collapsed, signals question active
            q_signals = page.get_by_test_id("setup-question-signals")
            q_signals.wait_for(timeout=15000)

            # Verify the collapsed outcome answer is visible
            answer_outcome = page.get_by_test_id("setup-answer-outcome")
            answer_outcome.wait_for(timeout=5000)
            assert answer_outcome.is_visible()

            # Verify the brief panel is visible
            brief = page.get_by_test_id("setup-brief")
            brief.wait_for(timeout=5000)
            assert brief.is_visible()

            _assert_clean(page, errors)

            # Shot: question plane + live brief with a collapsed answer
            shot = SHOTS / "face-questions-1440.png"
            page.screenshot(path=str(shot), full_page=False)
            assert shot.exists() and shot.stat().st_size > 20_000

            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_blank_leg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Blank path: answer both questions -> finalize with nothing selected
    -> active Project, no Watch, honest empty Room (INT-002)."""
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
                viewport={"width": 1440, "height": 900},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            # No facts seeded -- blank path

            _open_interview(page, url)

            # Answer outcome
            q_outcome = page.get_by_test_id("setup-question-outcome")
            q_outcome.wait_for(timeout=15000)
            textarea = q_outcome.locator("textarea")
            textarea.fill("Explore a side project idea")
            textarea.press("Enter")

            # Answer signals
            q_signals = page.get_by_test_id("setup-question-signals")
            q_signals.wait_for(timeout=15000)
            textarea2 = q_signals.locator("textarea")
            textarea2.fill("Nothing specific yet")
            textarea2.press("Enter")

            # Wait for the proposals stage -- with no facts, blank path appears
            # Either suggestion-cards with zero cards, or the blank-path indicator
            blank_path = page.get_by_test_id("setup-blank-path")
            blank_btn = page.get_by_test_id("setup-proceed-blank")

            # Wait for either blank path or suggestion cards
            page.wait_for_function(
                """() => {
                    return document.querySelector('[data-testid="setup-blank-path"]') !== null
                        || document.querySelector('[data-testid="setup-proceed-blank"]') !== null
                        || document.querySelector('[data-testid="setup-suggestion-cards"]') !== null;
                }""",
                timeout=20000,
            )

            # Click "Create blank Project"
            blank_btn = page.get_by_test_id("setup-proceed-blank")
            blank_btn.wait_for(timeout=10000)
            blank_btn.click()

            # Wait for done
            done = page.get_by_test_id("setup-done")
            done.wait_for(timeout=20000)

            # The Room should open
            room_name = page.get_by_test_id("project-room-name")
            room_name.wait_for(timeout=20000)

            _assert_clean(page, errors)

            # Verify: no watches created
            from holdspeak.db import get_database
            db = get_database()
            with db._connection() as conn:
                watches = conn.execute(
                    "SELECT * FROM connector_watches"
                ).fetchall()
            assert len(watches) == 0, f"Expected 0 watches for blank path, got {len(watches)}"

            # Shot
            shot = SHOTS / "blank-room-1440.png"
            page.screenshot(path=str(shot), full_page=False)
            assert shot.exists() and shot.stat().st_size > 20_000

            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_abandon_leg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Abandon: start -> answer once -> cancel -> no Project exists."""
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": 1440, "height": 900},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            _open_interview(page, url)

            # Answer outcome only
            q_outcome = page.get_by_test_id("setup-question-outcome")
            q_outcome.wait_for(timeout=15000)
            textarea = q_outcome.locator("textarea")
            textarea.fill("This will be abandoned")
            textarea.press("Enter")

            # Wait for signals question to appear (proves stage advanced)
            q_signals = page.get_by_test_id("setup-question-signals")
            q_signals.wait_for(timeout=15000)

            # Click Cancel setup
            cancel_btn = page.locator(".setup-abandon-btn")
            cancel_btn.wait_for(timeout=5000)
            cancel_btn.click()

            # Wait for abandoned state
            abandoned = page.get_by_test_id("setup-abandoned")
            abandoned.wait_for(timeout=10000)
            assert abandoned.is_visible()

            # Verify: no project created
            from holdspeak.db import get_database
            db = get_database()
            with db._connection() as conn:
                projects = conn.execute(
                    "SELECT * FROM projects"
                ).fetchall()
            assert len(projects) == 0, f"Expected 0 projects after abandon, got {len(projects)}"

            _assert_clean(page, errors)

            browser.close()
    finally:
        server.stop()
        reset_database()
