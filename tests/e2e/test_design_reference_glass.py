"""The Components window's living pattern reference on real desk glass.

The examples are local specimens. This test proves the selector, the local
state changes and the narrow arrangement in Chromium at the two required
desk widths.
"""
from __future__ import annotations

from pathlib import Path
import re

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the design reference needs Playwright")

TOKEN = "design-reference-glass"
SHOTS = evidence_dir("design-reference")


def _select_pattern(page, label: str) -> None:
    direct = page.get_by_role("button", name=label, exact=True)
    if direct.count():
        direct.click()
        return
    page.get_by_role("button", name=re.compile(r"^Patterns:")).click()
    page.locator("[role^='menuitem']").filter(has_text=label).first.click()


@pytest.fixture
def desk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        yield base
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_patterns_are_real_local_compositions(desk: str, width: int, height: int) -> None:
    from playwright.sync_api import expect, sync_playwright

    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce")
        page.clock.install()
        page.goto(f"{desk}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        _normal_chair(page)
        page.goto(f"{desk}/design/components?token={TOKEN}", wait_until="load")
        reference = page.get_by_test_id("design-reference")
        expect(reference).to_be_visible()
        expect(page.locator('[aria-label="LOCAL SPECIMEN"]')).to_be_visible()
        expect(page.get_by_role("button", name="Give feedback on Components", exact=True)).to_be_visible()

        # Forms: the captured save completes while a newer edit remains in
        # the field, so the specimen demonstrates the real dirty boundary.
        form = page.get_by_test_id("reference-form")
        title = form.get_by_role("textbox", name="Project note title")
        page.screenshot(path=str(SHOTS / f"forms-{width}.png"), full_page=False)
        title.fill("Release note draft")
        page.clock.pause_at(page.evaluate("Date.now() / 1000") + 60)
        form.get_by_role("button", name="Save note").click()
        title.fill("Newer edit kept")
        scope = form.get_by_role("combobox", name="Project scope")
        scope.select_option("Team record")
        page.clock.run_for(120)
        expect(title).to_have_value("Newer edit kept")
        expect(scope).to_have_value("Team record")
        expect(form.get_by_text("Saved · newer edits remain.")).to_be_visible()
        page.clock.resume()
        page.get_by_role("combobox", name="Example state").select_option("failed")
        expect(form.get_by_text("Save failed.")).to_be_visible()
        page.screenshot(path=str(SHOTS / f"forms-failed-{width}.png"), full_page=False)
        form.get_by_role("button", name="Retry").click()
        expect(form.get_by_text("Saved.")).to_be_visible()
        expect(title).to_have_value("Newer edit kept")
        page.screenshot(path=str(SHOTS / f"forms-saved-{width}.png"), full_page=False)

        _select_pattern(page, "Reading")
        reading = page.get_by_test_id("reference-reading")
        state = page.get_by_role("combobox", name="Example state")
        state.select_option("empty")
        expect(reading.get_by_role("button", name="Keep excerpt")).to_have_count(0)
        expect(reading.get_by_role("button", name="Open source")).to_have_count(1)
        reading.get_by_role("button", name="Open source").last.click()
        expect(reading.get_by_test_id("reference-source-note")).to_be_visible()
        reading.get_by_role("button", name="Close source").click()
        expect(reading.get_by_test_id("reference-source-note")).to_have_count(0)

        state.select_option("long")
        expect(reading.get_by_test_id("reference-reading-document")).to_be_visible()
        document = reading.get_by_test_id("reference-reading-document")
        assert document.evaluate("el => getComputedStyle(el).overflowY") == "visible"
        host_body = page.locator(".desk-surface-body").first
        assert host_body.evaluate("el => el.scrollHeight > el.clientHeight")
        reading.get_by_role("button", name="Open source").click()
        expect(reading.get_by_test_id("reference-source-note")).to_be_visible()
        reading.get_by_role("button", name="Close source").click()
        expect(reading.get_by_test_id("reference-source-note")).to_have_count(0)
        keep = reading.get_by_role("button", name="Keep excerpt")
        keep.scroll_into_view_if_needed()
        expect(keep).to_be_in_viewport()
        keep.click()
        expect(reading.get_by_test_id("reference-kept-excerpt")).to_have_text("The team chose a local review pass for the next release.")
        page.screenshot(path=str(SHOTS / f"reading-{width}.png"), full_page=False)

        _select_pattern(page, "Lists")
        list_panel = page.get_by_test_id("reference-list")
        list_panel.get_by_role("textbox", name="Filter work items").fill("runtime")
        expect(list_panel.get_by_text("Runtime plan", exact=True)).to_be_visible()
        list_panel.get_by_role("button", name="Runtime plan").click()
        expect(list_panel.get_by_text("Selected: Runtime plan", exact=True)).to_be_visible()
        if width < 560:
            list_panel.get_by_role("button", name="Back to work items", exact=True).click()
        else:
            list_panel.get_by_role("button", name="Clear selection", exact=True).click()
        expect(list_panel.get_by_text("Selected: Runtime plan", exact=True)).to_have_count(0)
        list_panel.get_by_role("button", name="Runtime plan").click()
        expect(list_panel.get_by_text("Selected: Runtime plan", exact=True)).to_be_visible()
        page.screenshot(path=str(SHOTS / f"lists-{width}.png"), full_page=False)

        _select_pattern(page, "Conversation")
        conversation = page.get_by_test_id("reference-conversation")
        conversation_state = page.get_by_role("combobox", name="Example state")
        conversation_state.select_option("failed")
        failed_request = "Can we keep the release note local while we review it?"
        expect(conversation.get_by_text(failed_request, exact=True)).to_have_count(1)
        draft = conversation.get_by_role("textbox", name="Write a review note")
        draft.fill("Newer composer draft")
        conversation.get_by_role("button", name="Retry", exact=True).first.click()
        expect(conversation.get_by_role("button", name="Retry…", exact=True)).to_be_disabled()
        draft.fill("Newer composer draft while retrying")
        expect(conversation.get_by_text("The reply is available locally for the captured request.", exact=True)).to_be_visible()
        expect(draft).to_have_value("Newer composer draft while retrying")
        expect(conversation.get_by_text(failed_request, exact=True)).to_have_count(1)
        conversation_state.select_option("ordinary")
        conversation.get_by_role("textbox", name="Write a review note").fill("Keep the review local")
        conversation.get_by_role("button", name="Send locally").click()
        expect(conversation.get_by_text("Keep the review local", exact=True)).to_be_visible()
        page.screenshot(path=str(SHOTS / f"conversation-{width}.png"), full_page=False)

        _select_pattern(page, "Progress")
        progress = page.get_by_test_id("reference-progress")
        progress.get_by_role("button", name="Fail locally").click()
        expect(progress.get_by_text("Needs retry", exact=True)).to_be_visible()
        progress.get_by_role("button", name="Retry").click()
        expect(progress.get_by_role("progressbar", name="Check source progress")).to_have_attribute("aria-valuenow", "55")
        page.screenshot(path=str(SHOTS / f"progress-{width}.png"), full_page=False)

        page.get_by_role("button", name="Reset", exact=True).click()
        expect(page.get_by_test_id("reference-form").get_by_role("textbox", name="Project note title")).to_have_value("Sprint review notes")
        expect(page.get_by_role("combobox", name="Example state")).to_have_value("ordinary")

        # Controls remains a real selector destination for the existing
        # catalogue and its retained composer/object specimens.
        _select_pattern(page, "Controls")
        expect(page.get_by_test_id("object-species-gallery")).to_be_visible()
        expect(page.locator(".desk-pr-compose").first).to_be_visible()
        page.get_by_role("button", name="+ Add node", exact=True).click()
        node = page.get_by_role("button", name="Local node 1", exact=True)
        node.scroll_into_view_if_needed()
        expect(node).to_be_in_viewport()
        _settle(page)
        page.screenshot(path=str(SHOTS / f"patterns-{width}.png"), full_page=False)
        browser.close()
