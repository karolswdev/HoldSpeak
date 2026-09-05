"""HS-170-04 -- Speak face glass rig.

Artboard assertions on the settled face at 1440 and 393:
- idle (placeholder, ENGINE row shows a StateChip)
- typed utterance -> land (dry run) -> RESULT row with OK/Wrong
- Wrong unfolds the teach row (no dialog) -> Teach posts a correction
- Details folded by default
- Footer chip reads THIS DEVICE
- At 393 nothing overflows

Shots land in assets/story-04-shots/build-speak-*.png.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot,
    _api,
    _api_allow_error,
    _assert_clean,
    _normal_chair,
    _ensure_build,
    _settle,
    REPO,
)

pytest.importorskip("playwright.sync_api", reason="Speak glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-170-the-great-pass/assets/story-04-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs170-speak"

# Stubbed dry-run response — the isolated hub has no dictation engine,
# so we intercept the route and return a predetermined result.
DRY_RUN_RESULT = {
    "final_text": "Ship the Q4 platform on schedule with zero incidents",
    "text": "Ship the Q4 platform on schedule with zero incidents",
    "total_ms": 41,
    "target_profile": "Claude Code",
    "intent": "command",
    "journal_id": "glass-test-journal-1",
}


# ── Helpers ────────────────────────────────────────────────────────


def _stage_speak(page: Any) -> None:
    """Stage the dictation surface, reload, and cross the first sentence."""
    page.evaluate(
        """([key]) => {
          localStorage.removeItem("hs.desk.workspace.v1");
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["dictate"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = SHOTS / f"build-speak-{name}-{width}.png"
    target = page.locator(".desk-surface-window").first
    if target.count() > 0:
        target.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _init_desk(page: Any, url: str) -> None:
    """Navigate, seed, complete onboarding, cross the first sentence."""
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)


def _stub_dry_run(page: Any) -> None:
    """Intercept the dry-run route so the face lands without a real engine."""
    page.route("**/api/dictation/dry-run", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(DRY_RUN_RESULT),
    ))


def _type_and_land(page: Any) -> None:
    """Type an utterance, toggle DRY RUN on, and land via Ctrl+Enter."""
    well = page.locator(".speak-well textarea")
    well.click()
    well.fill("Ship the Q4 platform on schedule with zero incidents")

    # Toggle DRY RUN on (click the label wrapper, not the hidden input)
    dry_run = page.locator('.gadget-check-token').filter(has_text="DRY RUN")
    dry_run.click()

    # Ctrl+Enter triggers the dry-run submission
    well.press("Control+Enter")


# ── Tests ──────────────────────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_speak_idle_1440(tmp_path, monkeypatch):
    """Idle at 1440: placeholder, ENGINE row, Details folded, THIS DEVICE footer."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)
            _stage_speak(page)

            page.locator(".speak-face").wait_for(timeout=10000)
            _settle(page)

            # The placeholder is present
            well = page.locator(".speak-well textarea")
            assert well.count() > 0
            placeholder = well.get_attribute("placeholder")
            assert placeholder == "Talk, or type here", f"Placeholder: {placeholder}"

            # ENGINE row exists with a StateChip
            engine = page.locator(".speak-engine")
            assert engine.count() > 0
            state_chip = engine.locator(".surface-state-chip")
            assert state_chip.count() > 0

            # Details fold is present and closed
            trigger = page.locator(".surface-disclosure-trigger")
            assert trigger.count() > 0
            assert trigger.get_attribute("aria-expanded") == "false"

            # Details body is NOT rendered when folded
            body = page.locator(".surface-disclosure-body")
            assert body.count() == 0, "Details should be folded by default"

            # Footer shows THIS DEVICE
            footer_text = page.locator(".surface-footer-layout").inner_text()
            assert "THIS DEVICE" in footer_text, f"Footer: {footer_text}"

            _shot(page, "idle", 1440)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_speak_idle_393(tmp_path, monkeypatch):
    """Idle at 393: nothing overflows horizontally."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 393, "height": 852})
            _init_desk(page, url)
            _stage_speak(page)

            page.locator(".speak-face").wait_for(timeout=10000)
            _settle(page)

            # Nothing overflows horizontally
            no_overflow = page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            )
            assert no_overflow, "Content overflows horizontally at 393px"

            _shot(page, "idle", 393)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_speak_landed_1440(tmp_path, monkeypatch):
    """Landed at 1440: typed utterance -> dry run -> RESULT row with OK/Wrong.

    Wrong unfolds the teach row (no dialog).
    Teach posts a correction via the API.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)
            _stub_dry_run(page)
            _stage_speak(page)

            page.locator(".speak-face").wait_for(timeout=10000)
            _settle(page)

            # Type and land
            _type_and_land(page)

            # Wait for the RESULT row to appear
            result = page.locator(".speak-result")
            result.wait_for(timeout=8000)
            _settle(page)

            # The result text is visible
            result_text = result.locator(".speak-result-text")
            assert result_text.count() > 0
            assert "Ship the Q4 platform" in result_text.inner_text()

            # OK and Wrong ghost buttons are present
            ok_btn = result.get_by_role("button", name="OK")
            assert ok_btn.count() > 0
            wrong_btn = result.get_by_role("button", name="Wrong")
            assert wrong_btn.count() > 0

            _shot(page, "landed", 1440)

            # ── Press Wrong: the teach row unfolds in place ──
            wrong_btn.click()
            teach_row = page.locator(".speak-teach")
            teach_row.wait_for(timeout=5000)
            _settle(page)

            # No dialog (the correction is in-world, never a modal)
            assert page.locator('[role="dialog"]').count() == 0

            # The teach row has: field picker, StringGadget, Teach button
            teach_btn = teach_row.get_by_role("button", name="Teach")
            assert teach_btn.count() > 0

            _shot(page, "teach", 1440)

            # ── Teach posts a correction via the API ──
            # Stub the correction routes
            page.route("**/api/dictation/journal/*/correct", lambda route: route.fulfill(
                status=200, content_type="application/json",
                body=json.dumps({"success": True}),
            ))
            page.route("**/api/dictation/corrections", lambda route: route.fulfill(
                status=200, content_type="application/json",
                body=json.dumps({"success": True}),
            ))

            # Type a correction value and click Teach; wait for the POST
            correction_input = teach_row.locator('input[type="text"]')
            if correction_input.count() > 0:
                correction_input.fill("Terminal")
                with page.expect_request(
                    lambda req: "correct" in req.url or "corrections" in req.url,
                    timeout=5000,
                ) as req_info:
                    teach_btn.click()
                assert req_info.value.method == "POST"

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_speak_landed_393(tmp_path, monkeypatch):
    """Landed at 393: the result row stacks; nothing overflows."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 393, "height": 852})
            _init_desk(page, url)
            _stub_dry_run(page)
            _stage_speak(page)

            page.locator(".speak-face").wait_for(timeout=10000)
            _settle(page)

            _type_and_land(page)

            result = page.locator(".speak-result")
            result.wait_for(timeout=8000)
            _settle(page)

            # Nothing overflows
            no_overflow = page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            )
            assert no_overflow, "Content overflows horizontally at 393px in landed state"

            _shot(page, "landed", 393)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_speak_unset_1440(tmp_path, monkeypatch):
    """Engine state: the StateChip on the ENGINE row shows a valid state."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)
            _stage_speak(page)

            page.locator(".speak-face").wait_for(timeout=10000)
            _settle(page)

            engine = page.locator(".speak-engine")
            assert engine.count() > 0
            chip = engine.locator(".surface-state-chip")
            assert chip.count() > 0
            chip_text = chip.inner_text()
            assert any(t in chip_text for t in ["NOT SET", "READY", "NOT READY"]), (
                f"StateChip text: {chip_text}"
            )

            _shot(page, "unset", 1440)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_speak_details_folded(tmp_path, monkeypatch):
    """Details Disclosure is folded by default."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)
            _stage_speak(page)

            page.locator(".speak-face").wait_for(timeout=10000)
            _settle(page)

            trigger = page.locator(".surface-disclosure-trigger")
            assert trigger.count() > 0
            assert trigger.get_attribute("aria-expanded") == "false"

            body = page.locator(".surface-disclosure-body")
            assert body.count() == 0

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_speak_footer_this_device(tmp_path, monkeypatch):
    """The footer EgressChip reads THIS DEVICE."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)
            _stage_speak(page)

            page.locator(".speak-face").wait_for(timeout=10000)
            _settle(page)

            footer = page.locator(".surface-footer-layout")
            assert footer.count() > 0
            text = footer.inner_text()
            assert "THIS DEVICE" in text, f"Footer: {text}"

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
