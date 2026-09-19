"""HS-201-01 — the desk names the one thing the meeting path needs.

Cold, isolated HOME. Nothing is seeded into the model library, so the
`capability:meeting.deferred_analysis` head does not exist and the
meeting-intel queue would refuse with `no_assignment`
(`holdspeak/services/inference_route_plan_service.py:399-403`) — the very
refusal the charter walk found in the hub log with nothing on the glass
(`audits/face-walk-opus.md` defect 1).

Tests:
  1. test_chair_names_the_blocker — the Chair draws ONE row with ONE
     library Button, the headline is not `Nothing needs you`, the Button
     opens Models, and after a REAL capability-scope assignment through
     `POST /api/inference/assignments/set` the row is gone. 1440 + 393.
  2. test_meetings_window_over_a_failed_row — the Meetings window never
     reads `Nothing needs you` above a FAILED meeting. 1440 + 393.
  3. test_chip_and_trust_agree — the chrome egress chip and the Trust
     window state the same thing on a virgin desk. 1440 + 393.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    REPO,
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="HS-201 glass needs Playwright")

SHOTS = REPO / "pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-01-shots"
TOKEN = "hs201-one-thing"
SUMMARY_CAPABILITY = "meeting.deferred_analysis"


def _quiet_concierge(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the Models window off the real hardware scan (speed, not truth)."""
    import holdspeak.services.concierge_service as cs

    detection = {
        "engines": [],
        "hardware": {"capability": {"apple_silicon": True, "system": "darwin",
                                    "architecture": "arm64", "ram_gb": 36}},
        "runtimes": [],
        "checkedAt": "2026-09-19T09:41:00Z",
    }
    monkeypatch.setattr(cs, "detect", lambda **_: detection)
    monkeypatch.setattr(cs, "propose", lambda **_: {"rows": [], "receipt": {"groups": 0, "engines": 0, "waiting": 0}})


def _assign_summary_engine() -> None:
    """Assign a real engine to the summary capability, the product's way.

    A real ModelProfileService profile, then the real
    InferenceAssignmentService at `capability:meeting.deferred_analysis`
    scope — the only scope the meeting queue's service route policy may
    read (`inference_service_route_policy.py:43`, `:93`).
    """
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

    db = get_database()
    owner = Principal(PrincipalKind.OWNER, "hs201-owner")
    # The summary capability declares structured output and its own result
    # schema (`holdspeak/inference_capabilities.py:1068`), so the profile
    # must claim both or the assignment is refused as incompatible.
    _profile(
        db,
        "hs201-summary-engine",
        claims=("language", "structured_output", _result_claim(SUMMARY_CAPABILITY)),
        modalities=("language", "text"),
    )
    InferenceAssignmentService(db).set_assignment(owner, {
        "command_id": "hs201-assign-summary",
        "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": SUMMARY_CAPABILITY},
        "entries": [{"profile_id": "hs201-summary-engine", "profile_revision": 1}],
    })


def _seed_failed_meeting() -> None:
    """One finalized meeting whose intelligence failed."""
    from holdspeak.db import get_database

    db = get_database()
    now = datetime.now()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'error', 'finalized', 'desktop')",
            (
                "m-failed",
                (now - timedelta(hours=2)).isoformat(),
                (now - timedelta(hours=1, minutes=30)).isoformat(),
                "Platform sync",
                1800.0,
            ),
        )
        conn.commit()


def _open_surface(page: Any, key: str) -> None:
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open", JSON.stringify({key})
          );
        }""",
        [key],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _arrive(page: Any, base: str) -> None:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)
    page.locator("[data-testid='arrival-display']").wait_for(timeout=10_000)
    _settle(page)


class TestOneThing:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        _quiet_concierge(monkeypatch)
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        yield
        self.server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_chair_names_the_blocker(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        suffix = str(width)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)

            # ── the product's own truth: no capability head ──
            roster = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            summary_row = next(
                row for row in roster["task_overrides"]
                if row["id"] == SUMMARY_CAPABILITY
            )
            assert summary_row["has_override"] is False, summary_row
            assert summary_row["effective"]["status"] == "no_assignment", summary_row

            # ── ONE row, ONE Button ──
            section = page.locator("[data-testid='arrival-blocker']")
            section.wait_for(timeout=10_000)
            rows = page.locator("[data-testid='arrival-blocker-row']")
            assert rows.count() == 1, f"{rows.count()} blocker rows at {width}"
            assert "No engine for summaries" in (rows.first.text_content() or "")
            verbs = section.locator("button")
            assert verbs.count() == 1, f"{verbs.count()} verbs at {width}"
            assert (verbs.first.text_content() or "").strip() == "Choose an engine"
            # UX-CANON A1: the library Button, never a raw element
            assert "btn" in (verbs.first.get_attribute("class") or "")

            # ── the headline does not lie over it ──
            headline = page.locator("[data-testid='arrival-display']").text_content() or ""
            assert headline.strip() != "Nothing needs you", headline

            page.screenshot(path=str(SHOTS / f"chair-blocker-{suffix}.png"), full_page=True)

            # ── the Button opens Models ──
            page.locator("[data-testid='arrival-blocker-verb']").click()
            page.locator("[data-testid='concierge-root']").wait_for(timeout=15_000)
            # Close it again so the "row is gone" shot is the Chair itself.
            page.locator("[data-testid='concierge-cancel']").click()
            _settle(page)

            # ── assign the engine the product's way; the row is gone ──
            _assign_summary_engine()
            roster = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            summary_row = next(
                row for row in roster["task_overrides"]
                if row["id"] == SUMMARY_CAPABILITY
            )
            assert summary_row["has_override"] is True, summary_row
            assert summary_row["effective"]["status"] == "assigned", summary_row

            _arrive(page, self.base)
            assert page.locator("[data-testid='arrival-blocker']").count() == 0, (
                f"blocker row survived the assignment at {width}"
            )
            headline = page.locator("[data-testid='arrival-display']").text_content() or ""
            assert headline.strip() == "Nothing needs you", headline

            page.screenshot(path=str(SHOTS / f"chair-assigned-{suffix}.png"), full_page=True)

            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_meetings_window_over_a_failed_row(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        _seed_failed_meeting()
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)
            _open_surface(page, "review-meetings")

            headline = page.locator("[data-testid='meetings-headline']")
            headline.wait_for(timeout=15_000)
            page.wait_for_function(
                """() => {
                  const el = document.querySelector("[data-testid='meetings-headline']");
                  return el && el.textContent && el.textContent.trim().length > 0;
                }""",
                timeout=15_000,
            )
            _settle(page)
            text = (headline.text_content() or "").strip()
            assert text != "Nothing needs you", text
            assert text == "1 meeting failed", text

            page.screenshot(
                path=str(SHOTS / f"meetings-failed-{width}.png"), full_page=True
            )
            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_chip_and_trust_agree(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)

            # The product's own trust block: zero destinations enabled.
            setup = _api(page, "GET", "/api/setup/status", token=TOKEN)
            destinations = setup["trust"]["destinations"]
            assert not [d for d in destinations if d["enabled"]], destinations
            # ...while the permission that used to drive the chip is ON.
            assert setup["trust"]["actuators_enabled"] is True, setup["trust"]

            chip = page.locator(".egress-badge").first
            chip.wait_for(timeout=10_000)
            chip_text = (chip.text_content() or "").strip()
            assert "EXTERNAL REACH" not in chip_text.upper(), chip_text
            assert "THIS DEVICE" in chip_text.upper(), chip_text

            chip.click()
            window = page.locator(".desk-trust-window")
            window.wait_for(timeout=10_000)
            _settle(page)
            trust_text = window.text_content() or ""
            assert "All data stays on this device" in trust_text, trust_text
            assert "None" in trust_text, trust_text

            page.screenshot(
                path=str(SHOTS / f"chip-and-trust-{width}.png"), full_page=True
            )
            _assert_clean(page, errors)
            page.close()
            browser.close()
