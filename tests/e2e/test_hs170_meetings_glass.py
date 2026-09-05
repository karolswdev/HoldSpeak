"""HS-170-04 — meetings face glass rig.

Seed four meetings through the product's DB in the isolated hub:
  1. Census standup: OFF with a transcript — Run intelligence shown
  2. Design review: SAVED with 3 proposals (needs you)
  3. 1:1 Ania: SAVED, no outcomes
  4. Vendor call: OFF with NO transcript — Run intelligence NOT shown

Assert at 1440 + 393:
  - headline count equals OFF-with-words meetings (1)
  - Run intelligence present exactly on those rows, absent on no-transcript
  - clicking Run intelligence posts to the run route (monkeypatched)
  - the detail opens with one display; NEEDS YOU 3 with 3 verbs
  - NO TRANSCRIPT renders, 0 SEG never does
  - speaker tokens in transcript; no raw <button>
  - nothing overflows at 393
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
    REPO,
)

pytest.importorskip("playwright.sync_api", reason="Meetings glass needs Playwright")

SHOTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-170-the-great-pass/assets/story-04-shots"
)
SHOTS_DIR.mkdir(parents=True, exist_ok=True)

TOKEN = "hs170-meetings"


# ── Seed helpers ────────────────────────────────────────────────

def _seed_meetings() -> None:
    """Seed four meetings through the product's DB."""
    from holdspeak.db import get_database
    db = get_database()

    now = datetime.now()
    with db._connection() as conn:
        # 1. Census standup — OFF with transcript, speakers Karol/Ania
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'disabled', 'finalized', 'desktop')",
            ("m-off-words", (now - timedelta(hours=2)).isoformat(),
             (now - timedelta(hours=1, minutes=30)).isoformat(),
             "Census standup", 1800.0),
        )
        words_per_segment = 60
        num_segments = 20
        for i in range(num_segments):
            text = " ".join(f"word{j}" for j in range(words_per_segment))
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
                "VALUES (?, ?, ?, ?, ?)",
                ("m-off-words", text, "Karol" if i % 2 == 0 else "Ania",
                 float(i * 90), float((i + 1) * 90)),
            )

        # 2. Design review — SAVED with 3 proposals (needs-you)
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'complete', 'finalized', 'desktop')",
            ("m-saved-outcomes", (now - timedelta(days=2)).isoformat(),
             (now - timedelta(days=2) + timedelta(minutes=45)).isoformat(),
             "Design review", 2700.0),
        )
        for i in range(5):
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
                "VALUES (?, ?, ?, ?, ?)",
                ("m-saved-outcomes",
                 f"Discussion point {i} about the PostgreSQL migration",
                 "Karol" if i % 2 == 0 else "Ania",
                 float(i * 540), float((i + 1) * 540)),
            )
        # Seed 3 proposals with status='proposed' — these populate NEEDS YOU
        for title, action in [
            ("Decide: the PostgreSQL migration date", "decide"),
            ("Ania owes the API spec", "assign"),
            ("Follow up with vendor", "followup"),
        ]:
            pid = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO actuator_proposals "
                "(id, meeting_id, origin, window_id, plugin_id, plugin_version, "
                " idempotency_key, status, target, action, preview, "
                " payload_json, operation_json, policy_snapshot_json) "
                "VALUES (?, ?, 'meeting', ?, 'glass-test', '1.0', ?, "
                " 'proposed', 'slack', ?, ?, '{}', '{}', '{}')",
                (pid, "m-saved-outcomes", f"m-saved-outcomes:aftercare",
                 f"glass-{pid}", action, title),
            )

        # 3. 1:1 Ania — SAVED, no outcomes
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'complete', 'finalized', 'desktop')",
            ("m-saved-clean", (now - timedelta(days=7)).isoformat(),
             (now - timedelta(days=7) + timedelta(minutes=25)).isoformat(),
             "1:1 Ania", 1500.0),
        )
        for i in range(3):
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
                "VALUES (?, ?, ?, ?, ?)",
                ("m-saved-clean", f"Topic {i} about project status",
                 "Karol" if i % 2 == 0 else "Ania",
                 float(i * 500), float((i + 1) * 500)),
            )

        # 4. Vendor call — OFF, NO transcript
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'disabled', 'finalized', 'desktop')",
            ("m-no-transcript", (now - timedelta(days=9)).isoformat(),
             (now - timedelta(days=9) + timedelta(minutes=12)).isoformat(),
             "Vendor call", 720.0),
        )

        # 5. Dead recording — capture_status='recording' but session died
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'disabled', 'recording', 'desktop')",
            ("m-dead-rec", (now - timedelta(days=21)).isoformat(),
             None, "Standup gone wrong", 0.0),
        )

        # 6. Intelligence queued — capture finalized, intel queued
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'queued', 'finalized', 'desktop')",
            ("m-queued", (now - timedelta(days=1)).isoformat(),
             (now - timedelta(days=1) + timedelta(minutes=20)).isoformat(),
             "Already titled", 1200.0),
        )
        for i in range(2):
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
                "VALUES (?, ?, ?, ?, ?)",
                ("m-queued", f"Quick word {i}",
                 "Karol", float(i * 600), float((i + 1) * 600)),
            )

        conn.commit()


def _open_surface(page: Any, key: str) -> None:
    """Stage a surface key and reload."""
    page.evaluate(
        """([key]) => {
          localStorage.removeItem("hs.desk.workspace.v1");
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        [key],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _wait_for_surface_window(page: Any, timeout: int = 15000) -> bool:
    """Wait for a .desk-surface-window to appear."""
    try:
        page.locator(".desk-surface-window").first.wait_for(timeout=timeout)
        return True
    except Exception:
        return False


# ── The test ────────────────────────────────────────────────────

class TestMeetingsGlass:
    """HS-170-04 — the meetings face at 1440 + 393."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)

        # Monkeypatch the intel run route to return a fake job
        from holdspeak.services import meeting_intel_service as mis_mod
        def fake_run_intelligence(self_svc, principal, meeting_id):
            return {"jobId": "job-glass-123", "state": "queued", "host": "THIS DEVICE"}
        monkeypatch.setattr(mis_mod.MeetingIntelService, "run_intelligence", fake_run_intelligence)

        _seed_meetings()
        self.tmp_path = tmp_path

    def test_meetings_face(self) -> None:
        from playwright.sync_api import sync_playwright, expect

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch()

            for width in (1440, 393):
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.on("pageerror", lambda err: errors.append(str(err)))

                # Navigate with auth token
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "POST", "/api/desk/seed", token=TOKEN)
                _api(page, "PUT", "/api/setup/onboarding",
                     {"disposition": "completed"}, token=TOKEN)
                _normal_chair(page)

                # Open the meetings surface
                _open_surface(page, "review-meetings")
                found = _wait_for_surface_window(page, timeout=12000)
                assert found, f"Meetings surface window did not open at {width}"

                # Wait for data to render (headline is the signal)
                headline = page.locator("[data-testid='meetings-headline']")
                headline.wait_for(timeout=8_000)
                _settle(page)

                # ── Assert: headline ──
                headline_text = headline.text_content() or ""
                assert "1" in headline_text and "intelligence" in headline_text.lower(), (
                    f"Headline at {width}: expected '1 ... intelligence', got '{headline_text}'"
                )

                # ── Assert: Run intelligence on OFF-with-words row ──
                run_btns = page.locator("[data-testid='run-intelligence-btn']")
                expect(run_btns.first).to_be_visible(timeout=5_000)
                assert run_btns.count() == 1, (
                    f"Expected exactly 1 'Run intelligence' at {width}, got {run_btns.count()}"
                )

                # ── Assert: NO TRANSCRIPT renders ──
                no_transcript = page.locator("[data-testid='no-transcript-token']")
                expect(no_transcript.first).to_be_visible(timeout=3_000)

                # ── Assert: 0 SEG never appears ──
                win = page.locator(".desk-surface-window")
                page_text = win.text_content() or ""
                assert "0 SEG" not in page_text, (
                    f"'0 SEG' found in page at {width}"
                )

                # ── Assert: INTERRUPTED renders for dead capture, REC never does ──
                assert "INTERRUPTED" in page_text, (
                    f"'INTERRUPTED' not found at {width} for dead capture"
                )
                state_tokens_text = page.evaluate("""() => {
                    const body = document.querySelector('.desk-surface-body');
                    if (!body) return '';
                    const tokens = body.querySelectorAll('[data-testid="state-token"]');
                    return Array.from(tokens).map(t => t.textContent).join('|');
                }""")
                assert "REC" not in state_tokens_text.split("|"), (
                    f"'REC' state token found at {width}: {state_tokens_text}"
                )

                # ── Assert: no raw <button> in the face body ──
                raw_buttons = page.evaluate("""() => {
                    const body = document.querySelector('.desk-surface-body');
                    if (!body) return [];
                    const all = body.querySelectorAll('button');
                    const raw = [];
                    for (const b of all) {
                        if (!b.classList.contains('btn')) {
                            raw.push((b.textContent || '').trim().slice(0, 40));
                        }
                    }
                    return raw;
                }""")
                assert len(raw_buttons) == 0, (
                    f"Raw buttons at {width}: {raw_buttons}"
                )

                # ── Screenshot: list ──
                _settle(page)
                page.screenshot(
                    path=str(SHOTS_DIR / f"build-meetings-list-{width}.png"),
                    full_page=True,
                )

                if width == 1440:
                    # ── S-3: Click Run intelligence, assert host chip (Article III) ──
                    run_btns.first.click()
                    # The monkeypatch returns host="THIS DEVICE"; the
                    # EgressChip should appear on the row after the POST.
                    host_chip = page.locator(
                        "[data-testid='meeting-row-m-off-words'] .gadget-chip-egress"
                    )
                    expect(host_chip).to_be_visible(timeout=5_000)

                    # ── Click Design review to open detail ──
                    design_body = page.locator(
                        "[data-testid='meeting-row-m-saved-outcomes'] "
                        ".meetings-stream-row-body"
                    )
                    design_body.click()

                    # Wait for detail to render (the display title is the signal)
                    detail_display = page.locator(".surface-split-detail .surface-display")
                    detail_display.wait_for(timeout=8_000)
                    _settle(page)

                    detail_text = detail_display.text_content() or ""
                    assert "Design review" in detail_text, (
                        f"Detail display expected 'Design review', got '{detail_text}'"
                    )

                    # Assert: NEEDS YOU 3 with 3 outcome rows
                    needs_head = page.locator(".meetings-detail-needs-head .surface-caption")
                    expect(needs_head).to_be_visible(timeout=5_000)
                    needs_text = needs_head.text_content() or ""
                    assert "3" in needs_text, (
                        f"Expected 'NEEDS YOU 3', got '{needs_text}'"
                    )
                    outcome_rows = page.locator(".meetings-detail-outcome-row")
                    assert outcome_rows.count() == 3, (
                        f"Expected 3 outcome rows, got {outcome_rows.count()}"
                    )

                    # S-5: Each outcome row has Decide / Dismiss verbs
                    decide_btns = page.locator(".meetings-detail-outcome-verb .btn", has_text="Decide")
                    dismiss_btns = page.locator(".meetings-detail-outcome-verb .btn", has_text="Dismiss")
                    assert decide_btns.count() == 3, (
                        f"Expected 3 'Decide' buttons, got {decide_btns.count()}"
                    )
                    assert dismiss_btns.count() == 3, (
                        f"Expected 3 'Dismiss' buttons, got {dismiss_btns.count()}"
                    )

                    # Assert: proposal preview text renders
                    detail_text_full = page.locator(".surface-split-detail").text_content() or ""
                    assert "Decide: the PostgreSQL migration date" in detail_text_full, (
                        f"Expected proposal preview text in detail, got: {detail_text_full[:200]}"
                    )

                    # Assert: speaker tokens in transcript
                    speaker_tokens = page.locator("[data-testid='transcript-speaker']")
                    assert speaker_tokens.count() >= 2, (
                        f"Expected speaker tokens in transcript, got {speaker_tokens.count()}"
                    )

                    # Screenshot: detail
                    _settle(page)
                    page.screenshot(
                        path=str(SHOTS_DIR / f"build-meetings-detail-{width}.png"),
                        full_page=True,
                    )

                # ── 393: nothing overflows ──
                if width == 393:
                    no_overflow = page.evaluate(
                        "document.documentElement.scrollWidth <= window.innerWidth"
                    )
                    assert no_overflow, f"Page overflows at {width}"

                _assert_clean(page, errors)
                page.close()
                errors.clear()

            browser.close()
