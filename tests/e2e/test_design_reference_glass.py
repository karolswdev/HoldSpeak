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
    back = page.get_by_test_id("reference-back")
    if not direct.count() and back.count() and back.is_visible():
        # W2-BUILDER: at 393 an open group returns to the group rail first.
        back.click()
        direct = page.get_by_role("button", name=label, exact=True)
    if direct.count():
        direct.click()
        return
    page.get_by_role("button", name=re.compile(r"^Patterns:")).click()
    page.locator("[role^='menuitem']").filter(has_text=label).first.click()


@pytest.fixture
def desk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # The registry default is frozen at import time, before _boot sets HOME.
    import holdspeak.delivery.registry as registry_module

    monkeypatch.setattr(
        registry_module, "DEFAULT_REGISTRY_PATH",
        tmp_path / "home" / ".holdspeak" / "delivery_sources.json",
    )
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
        page.goto(f"{desk}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        _normal_chair(page)
        page.goto(f"{desk}/design/components?token={TOKEN}", wait_until="load")
        reference = page.get_by_test_id("design-reference")
        expect(reference).to_be_visible()
        expect(page.get_by_test_id("reference-status")).to_contain_text("Local specimen")
        expect(page.get_by_role("button", name="Give feedback on Components", exact=True)).to_be_visible()
        if width < 720:
            # W2-BUILDER: at 393 the group rail is the first view.
            _select_pattern(page, "Forms")

        writes: list[str] = []
        page.on("request", lambda request: writes.append(request.url)
                if request.method != "GET" and any(path in request.url for path in
                   ("/api/settings", "/api/notes", "/api/ask")) else None)

        # Forms is the actual Settings You field/controller with local IO.
        # Exercise a raw alias, held acknowledgement, refusal, retry and a
        # newer name draft without sending a production settings write.
        form = page.get_by_test_id("reference-owner-preferences")
        state = page.get_by_role("combobox", name="Example state")
        name = form.get_by_test_id("settings-owner-name").get_by_role("textbox")
        aliases = form.get_by_test_id("settings-owner-aliases").get_by_role("textbox")
        expect(state).to_have_value("saved")
        expect(name).to_have_value("Karol")
        expect(form.get_by_text("Carol", exact=True)).to_be_visible()
        # Window grammar 2026-10-24: the specimen is the Settings rail, pane
        # and status bar; each field keeps its save word as data.
        expect(form.get_by_test_id("settings-status")).to_contain_text("Local specimen")
        expect(form.get_by_test_id("reference-settings-index-you")).to_have_attribute("aria-current", "location")
        assert form.locator(".desk-mic").count() == 0
        page.screenshot(path=str(SHOTS / f"forms-{width}.png"), full_page=False)

        aliases.fill("Ari")
        alias_field = form.get_by_test_id("settings-owner-aliases")
        expect(alias_field).to_have_attribute("data-save-state", "Edited")
        expect(form.get_by_test_id("settings-status")).to_contain_text("Edited")
        aliases.press("Enter")
        expect(form.get_by_text("Ari", exact=True)).to_be_visible()
        expect(alias_field).to_have_attribute("data-save-state", "Saved")
        expect(form.get_by_test_id("settings-status")).to_contain_text("Saved just now")

        state.select_option("saving")
        form.get_by_role("button", name="Complete local write").wait_for()
        name = form.get_by_test_id("settings-owner-name").get_by_role("textbox")
        name_row = form.get_by_test_id("settings-owner-name")
        expect(name_row).to_have_attribute("data-save-state", "Saving")
        page.screenshot(path=str(SHOTS / f"forms-saving-{width}.png"), full_page=False)
        form.get_by_role("button", name="Complete local write").click()
        expect(name_row).to_have_attribute("data-save-state", "Saved")

        state.select_option("refused")
        form.get_by_role("button", name="Retry", exact=True).wait_for(timeout=10_000)
        name = form.get_by_test_id("settings-owner-name").get_by_role("textbox")
        name_row = form.get_by_test_id("settings-owner-name")
        expect(name).to_have_value("Karol A")
        expect(name_row).to_have_attribute("data-save-state", "Not saved")
        page.screenshot(path=str(SHOTS / f"forms-failed-{width}.png"), full_page=False)
        form.get_by_role("button", name="Retry").click()
        expect(name_row).to_have_attribute("data-save-state", "Saved")
        expect(name).to_have_value("Karol A")
        page.screenshot(path=str(SHOTS / f"forms-saved-{width}.png"), full_page=False)

        state.select_option("newer")
        form.get_by_role("button", name="Complete local write").wait_for()
        name = form.get_by_test_id("settings-owner-name").get_by_role("textbox")
        name_row = form.get_by_test_id("settings-owner-name")
        expect(name).to_have_value("Karol B")
        expect(name_row).to_have_attribute("data-save-state", "Edited")
        form.get_by_role("button", name="Complete local write").click()
        expect(name_row).to_have_attribute("data-save-state", "Saved")
        expect(name).to_have_value("Karol B")
        page.screenshot(path=str(SHOTS / f"forms-newer-{width}.png"), full_page=False)

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
        reset_form = page.get_by_test_id("reference-owner-preferences")
        expect(reset_form.get_by_test_id("settings-owner-name").get_by_role("textbox")).to_have_value("Karol")
        expect(reset_form.get_by_text("Carol", exact=True)).to_be_visible()
        expect(page.get_by_role("combobox", name="Example state")).to_have_value("saved")

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
        assert not writes, writes
        browser.close()
