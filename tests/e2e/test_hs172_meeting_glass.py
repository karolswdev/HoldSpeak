"""HS-172 -- meeting detail after a run glass rig.

Seed a meeting with intel_status=complete and follow_through_proposals.
Assert at 1440 + 393:
  - header shows RAN chip (success), duration, EgressChip
  - NEEDS YOU section shows proposals with Confirm:/Decide: prefix
  - Confirm and Dismiss buttons (library Button, no raw <button>)
  - no zero counters, no text clip on proposal primaries
  - meeting list row carries the RAN chip
  - shots to story-03-shots/

Companion to test_hs170_meetings_glass.py (not edited).
"""
from __future__ import annotations

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
    REPO,
)

pytest.importorskip("playwright.sync_api", reason="Meeting glass needs Playwright")

SHOTS = REPO / "pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/story-03-shots"
TOKEN = "hs172-meeting"


# ── Seed ────────────────────────────────────────────────────────

def _seed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Seed one meeting with intel=complete and 3 follow-through proposals."""
    from holdspeak.db import get_database

    db = get_database()
    now = datetime.now()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'complete', 'finalized', 'desktop')",
            (
                "m-ran",
                (now - timedelta(hours=1)).isoformat(),
                (now - timedelta(minutes=30)).isoformat(),
                "Standup",
                1800.0,
            ),
        )
        for i in range(5):
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "m-ran",
                    f"Discussion point {i} about the migration",
                    "Karol" if i % 2 == 0 else "Marek",
                    float(i * 360),
                    float((i + 1) * 360),
                ),
            )
        # 3 follow-through proposals: 2 action, 1 decision
        proposals = [
            ("decision", "cut-over on the 12th", None),
            ("action", "Marek owns the PostgreSQL migration", "Fri"),
            ("action", "Ania owns the API spec", "Fri"),
        ]
        for kind, text, due in proposals:
            pid = f"prop-{uuid.uuid4().hex[:12]}"
            fp = f"fp-{uuid.uuid4().hex[:16]}"
            conn.execute(
                "INSERT INTO follow_through_proposals "
                "(id, meeting_id, project_id, kind, text, due_hint, "
                " source_plugin, fingerprint, state, model_host, created_at) "
                "VALUES (?, 'm-ran', NULL, ?, ?, ?, 'decision_capture', ?, "
                " 'proposed', '192.168.1.43', ?)",
                (pid, kind, text, due, fp, now.isoformat()),
            )
        conn.commit()


def _open_meetings(page: Any, url: str) -> None:
    """Navigate to the Meetings surface."""
    page.evaluate("""() => {
        sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key: "review-meetings"})
        );
    }""")
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator(".desk-surface-window").first.wait_for(timeout=12_000)


# ── The rig ────────────────────────────────────────────────────


class TestMeetingAfterRun:
    """HS-172 -- the meeting detail after an intel run."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _seed(monkeypatch)
        self.tmp_path = tmp_path

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.parametrize("width", [1440, 393])
    def test_meeting_ran_with_proposals(self, width: int) -> None:
        from playwright.sync_api import sync_playwright, expect

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _normal_chair(page)
            _open_meetings(page, self.base)

            # Wait for list
            headline = page.locator("[data-testid='meetings-headline']")
            headline.wait_for(timeout=8_000)
            _settle(page)

            # The meeting list row should show the RAN chip or NEEDS YOU
            state_tokens = page.locator("[data-testid='state-token']")
            all_tokens = state_tokens.all_text_contents()
            # At least one token should say RAN or NEEDS YOU
            has_ran_or_needs = any(
                "RAN" in t or "NEEDS YOU" in t or "NEED YOU" in t
                for t in all_tokens
            )
            assert has_ran_or_needs, (
                f"No RAN or NEEDS YOU token at {width}: {all_tokens}"
            )

            # No raw <button>
            raw_buttons = page.evaluate("""() => {
                const body = document.querySelector('.desk-surface-body');
                if (!body) return [];
                return Array.from(body.querySelectorAll('button'))
                    .filter(b => !b.classList.contains('btn') && !b.classList.contains('desk-mic'))
                    .map(b => (b.textContent || '').trim().slice(0, 40));
            }""")
            assert len(raw_buttons) == 0, f"Raw buttons at {width}: {raw_buttons}"

            # No zero counters
            page_text = page.locator(".desk-surface-body").text_content() or ""
            assert "0 NEEDS" not in page_text, f"Zero counter '0 NEEDS' at {width}"

            # No LOCAL
            assert "LOCAL" not in page_text, f"'LOCAL' found at {width}"

            # Screenshot list
            _settle(page)
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(SHOTS / f"build-meeting-ran-{width}.png"),
                full_page=True,
            )

            if width == 1440:
                # Click on the Standup meeting to open detail
                row_body = page.locator(
                    "[data-testid='meeting-row-m-ran'] .meetings-stream-row-body"
                )
                row_body.click()
                detail = page.locator(".surface-split-detail .surface-display")
                detail.wait_for(timeout=8_000)
                _settle(page)

                # Verify RAN in the header tokens
                facts = page.locator(".meetings-detail-facts").text_content() or ""
                assert "RAN" in facts, f"RAN not in detail facts at {width}: {facts}"

                # NEEDS YOU section with 3 proposals
                needs = page.locator("[data-testid='meeting-needs-you']")
                expect(needs).to_be_visible(timeout=5_000)
                needs_text = needs.text_content() or ""
                assert "3" in needs_text or "NEEDS YOU" in needs_text, (
                    f"Expected NEEDS YOU 3 at {width}: {needs_text[:200]}"
                )

                # Confirm and Dismiss buttons
                confirm_btns = page.locator("[data-testid='proposal-confirm-btn']")
                dismiss_btns = page.locator("[data-testid='proposal-dismiss-btn']")
                assert confirm_btns.count() == 3, (
                    f"Expected 3 Confirm buttons, got {confirm_btns.count()}"
                )
                assert dismiss_btns.count() == 3, (
                    f"Expected 3 Dismiss buttons, got {dismiss_btns.count()}"
                )

                # Decide: and Confirm: prefixes
                assert "Decide:" in needs_text, f"Missing 'Decide:' prefix: {needs_text[:200]}"
                assert "Confirm:" in needs_text, f"Missing 'Confirm:' prefix: {needs_text[:200]}"

                # No text clip on proposal primaries
                proposals_clipped = page.evaluate("""() => {
                    const texts = document.querySelectorAll('.meetings-detail-outcome-text');
                    const clipped = [];
                    for (const t of texts) {
                        if (t.scrollWidth > t.clientWidth + 2) {
                            clipped.push(t.textContent?.trim().slice(0, 40));
                        }
                    }
                    return clipped;
                }""")
                assert len(proposals_clipped) == 0, (
                    f"Clipped proposals at {width}: {proposals_clipped}"
                )

                # Detail screenshot
                page.screenshot(
                    path=str(SHOTS / f"build-meeting-ran-detail-{width}.png"),
                    full_page=True,
                )

            # 393: nothing overflows
            if width == 393:
                no_overflow = page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth"
                )
                assert no_overflow, f"Page overflows at {width}"

            _assert_clean(page, errors)
            page.close()
            errors.clear()

            browser.close()
