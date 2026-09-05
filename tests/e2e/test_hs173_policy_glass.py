"""HS-173-04 real-hub Steward policy glass: the sixth effect row.

Three legs:
  1. SIXTH ROW: the Reviewer nudge row unchecked by default, with
     EgressChip GITHUB.COM and PER-NUDGE APPROVAL token.
  2. CHECK + TEMPLATE: checking the row reveals the Nudge text
     StringGadget; Save round-trips the nudge_template.
  3. PHONE WIDTH: 393 stacking.

Shots to: assets/story-04-shots/
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _api, _normal_chair, _ensure_build

pytest.importorskip("playwright.sync_api", reason="Policy glass needs Playwright")

TOKEN = "hs173-policy-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-173-the-stewards-hand-and-voice/assets/story-04-shots"


# ── Boot / helpers ──────────────────────────────────────────────────


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)


def _open_project_room(page: Any, url: str, project_id: str) -> None:
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


def _create_project(page: Any) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": "Policy 173 Glass Project",
        "description": "Seeded for HS-173-04 policy glass.",
        "command_id": "hs173-policy-create-proj",
    }, token=TOKEN)
    return created["project"]["id"]


# ── Leg 1: SIXTH ROW unchecked + GITHUB.COM + PER-NUDGE APPROVAL ──


@pytest.mark.timeout(120)
def test_sixth_row_unchecked_with_badge_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _init_desk(page, url)

            project_id = _create_project(page)
            _open_project_room(page, url, project_id)

            # Enter steward posture
            page.click('[data-testid="steward-verb"]')
            page.wait_for_selector('[data-testid="steward-posture"]')

            # Enter policy
            page.click('[data-testid="steward-verb-policy"]')
            page.wait_for_selector('[data-testid="steward-policy"]')

            # The sixth kind label reads "Reviewer nudge"
            label = page.query_selector('[data-testid="steward-policy-kind-label-github_comment"]')
            assert label is not None, "github_comment label missing"
            assert label.text_content() == "Reviewer nudge"

            # EgressChip GITHUB.COM present
            effects = page.query_selector('[data-testid="steward-policy-effects"]')
            assert effects is not None
            egress_chips = effects.query_selector_all('.gadget-chip-egress')
            github_chip = None
            for chip in egress_chips:
                text = chip.text_content() or ""
                if "GITHUB.COM" in text:
                    github_chip = chip
                    break
            assert github_chip is not None, "GITHUB.COM EgressChip missing"

            # PER-NUDGE APPROVAL token present
            approval = page.query_selector('[data-testid="steward-policy-nudge-approval"]')
            assert approval is not None
            assert "PER-NUDGE APPROVAL" in (approval.text_content() or "")

            # The sixth checkbox is unchecked by default
            checkboxes = effects.query_selector_all('input[type="checkbox"]')
            assert len(checkboxes) >= 6, f"Expected 6 checkboxes, got {len(checkboxes)}"
            assert not checkboxes[5].is_checked(), "github_comment should be unchecked by default"

            # No nudge template row when unchecked
            template = page.query_selector('[data-testid="steward-policy-nudge-template"]')
            assert template is None, "Nudge template should be hidden when unchecked"

            page.screenshot(path=str(SHOTS / "build-steward-policy-1440.png"), full_page=True)
            browser.close()
    finally:
        server.stop()
        


# ── Leg 2: CHECK -> TEMPLATE APPEARS -> SAVE ROUND-TRIP ──────────────


@pytest.mark.timeout(120)
def test_check_reveals_template_and_save(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _init_desk(page, url)

            project_id = _create_project(page)
            _open_project_room(page, url, project_id)

            # Enter steward -> policy
            page.click('[data-testid="steward-verb"]')
            page.wait_for_selector('[data-testid="steward-posture"]')
            page.click('[data-testid="steward-verb-policy"]')
            page.wait_for_selector('[data-testid="steward-policy"]')

            # Check the github_comment checkbox (6th)
            effects = page.query_selector('[data-testid="steward-policy-effects"]')
            checkboxes = effects.query_selector_all('input[type="checkbox"]')
            checkboxes[5].click()

            # Template row now visible
            page.wait_for_selector('[data-testid="steward-policy-nudge-template"]')
            template_row = page.query_selector('[data-testid="steward-policy-nudge-template"]')
            assert template_row is not None

            # Save
            page.click('[data-testid="steward-verb-save-policy"]')
            page.wait_for_timeout(1000)

            # Back to list then re-enter policy to verify round-trip
            page.click('button:has-text("Back")')
            page.wait_for_selector('[data-testid="steward-posture"][data-phase="list"]')
            page.click('[data-testid="steward-verb-policy"]')
            page.wait_for_selector('[data-testid="steward-policy"]')

            # github_comment should be checked after save
            effects2 = page.query_selector('[data-testid="steward-policy-effects"]')
            checkboxes2 = effects2.query_selector_all('input[type="checkbox"]')
            assert checkboxes2[5].is_checked(), "github_comment should stay checked after save"

            # Template row visible after re-entry
            template2 = page.query_selector('[data-testid="steward-policy-nudge-template"]')
            assert template2 is not None, "Template row should be visible after round-trip"

            browser.close()
    finally:
        server.stop()
        


# ── Leg 3: PHONE WIDTH ─────────────────────────────────────────────


@pytest.mark.timeout(120)
def test_policy_stacking_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 393, "height": 852})
            _init_desk(page, url)

            project_id = _create_project(page)
            _open_project_room(page, url, project_id)

            page.click('[data-testid="steward-verb"]')
            page.wait_for_selector('[data-testid="steward-posture"]')
            page.click('[data-testid="steward-verb-policy"]')
            page.wait_for_selector('[data-testid="steward-policy"]')

            # The sixth row is present
            label = page.query_selector('[data-testid="steward-policy-kind-label-github_comment"]')
            assert label is not None
            assert label.text_content() == "Reviewer nudge"

            page.screenshot(path=str(SHOTS / "build-steward-policy-393.png"), full_page=True)
            browser.close()
    finally:
        server.stop()
        
