"""Send's bounded form, owner press and in-window discard at both sizes.

The note, preview, prepared rows, refusals and receipts come from the isolated
hub. Only FileChannel.dispatch is held or failed; nothing leaves the rig.
"""
from __future__ import annotations

import os
import json
import threading
import uuid
from pathlib import Path
from typing import Any

import pytest

from .send_face_facts import send_face_facts
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, park_builtin_folder

TOKEN = "send-grammar"


@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.timeout(180)
def test_send_form_states(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect
    from holdspeak.services.channel_contract import FileChannel, Outcome

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    phase = os.environ.get("SEND_GRAMMAR_PHASE", "after")
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/os-grammar"
    shots.mkdir(parents=True, exist_ok=True)
    release = threading.Event()
    mode = "failed"
    real_dispatch = FileChannel.dispatch

    def dispatch(channel: Any, *args: Any, **kwargs: Any) -> Any:
        if mode == "held":
            assert release.wait(30)
        if mode == "failed":
            return Outcome("failed", "permission_denied")
        return real_dispatch(channel, *args, **kwargs)

    monkeypatch.setattr(FileChannel, "dispatch", dispatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.set_default_timeout(20000)
            page.goto(f"{base}/?token={TOKEN}")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            made = _api(page, "POST", "/api/thoughts", {
                "request_id": str(uuid.uuid4()), "raw_text": "The weekly report is ready.", "source": {"kind": "typed"},
                "initial_note": {"title": "Weekly report", "body_markdown": "# Weekly report\n\nThe weekly report is ready.\n" + "\nNext step: review the plan.\n" * 35, "tags": []},
            }, token=TOKEN)
            ref = f"note:{made['thought']['working_note']['id']}"
            page.goto(f"{base}/?open={ref}")
            _normal_chair(page)
            win = page.locator(".thought-workspace-window").first
            if width == 1440:
                _api(page, "POST", f"/api/desk/windows/pullout:{ref}/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)

            def open_send(wait_preview: bool = True) -> Any:
                win.locator(".thought-note-toolbar").get_by_role("button", name="Send…", exact=True).click()
                well = win.get_by_test_id("send-well")
                if wait_preview:
                    well.get_by_test_id("send-preview-body").first.wait_for()
                return well

            def shot(state: str) -> None:
                # Every state starts at its choices; only the payload itself
                # needs scrolling. Completion remains outside both wells.
                win.locator(".surface-inspector-fields").evaluate_all("els => els.forEach(el => el.scrollTop = 0)")
                _settle(page)
                if phase == "after":
                    facts = send_face_facts(win, six_lines=width == 1440 and state in {"ready", "prepared"})
                    (shots / f"send-{state}-{width}-facts.json").write_text(json.dumps(facts, indent=2))
                (shots / f"send-{state}-{width}-{phase}.json").write_text(json.dumps(win.evaluate("""el => [...el.querySelectorAll(".thought-send-scroll,.thought-send-well,[data-seat],.send-sheet,[data-testid=send-well],.surface-tab-panel,.surface-inspector-form,.surface-inspector-fields,.surface-inspector-actions")].map(e => ({cls:e.className,rect:e.getBoundingClientRect().toJSON(),display:getComputedStyle(e).display,flex:getComputedStyle(e).flex,overflow:getComputedStyle(e).overflow}))"""),indent=2))
                page.screenshot(path=str(shots / f"send-{state}-{'900x600' if width == 1440 else '393'}-{phase}.png"))

            if phase == "after":
                held_preview: list[Any] = []
                page.route("**/api/channels/preview", lambda route: held_preview.append((route, route.fetch())))
                well = open_send(False)
                expect(well.get_by_test_id("send-destination-word")).to_contain_text("HoldSpeak folder")
                expect(well.get_by_test_id("send-verb")).to_be_disabled()
                assert not _api(page, "GET", f"/api/channels/sends?document_ref={ref}", token=TOKEN)["sends"]
                shot("preparing")
                route, response = held_preview.pop()
                route.fulfill(response=response)
                page.unroute("**/api/channels/preview")
                well.get_by_test_id("send-preview-body").wait_for()
            else:
                well = open_send()
            shot("ready")
            if phase == "after":
                completion = well.locator(".surface-inspector-actions").first
                assert completion.get_by_role("button").all_text_contents() == ["Edit", "Cancel", "Send"]
                assert well.locator(".send-sheet-header").count() == 0
                box = completion.bounding_box()
                assert box and box["y"] + box["height"] <= page.viewport_size["height"]
                well.locator(".surface-inspector-fields").first.evaluate("el => el.scrollTop = el.scrollHeight")
                assert completion.bounding_box() == box
                assert well.locator("[data-feedback-redact=true]").count()
            well.get_by_test_id("send-verb").click()
            well.get_by_test_id("send-failed").wait_for()
            shot("failed")
            mode = "held"
            well.get_by_test_id("send-verb").click()
            well.get_by_test_id("send-running").wait_for()
            shot("sending")
            release.set()
            well.get_by_test_id("send-sent").wait_for()
            shot("sent")
            # A stale press crosses the real hub boundary and is refused;
            # the transport itself is never called for this request.
            def stale(route: Any) -> None:
                payload = route.request.post_data_json
                route.continue_(post_data=json.dumps({**payload, "preview_digest": "0" * 64}))
            page.route("**/api/channels/send", stale)
            well.get_by_test_id("send-verb").click()
            well.get_by_test_id("send-refused").wait_for()
            shot("refused")
            expect(well.get_by_test_id("send-preview-body")).to_contain_text("The weekly report is ready.")
            expect(well.get_by_test_id("send-verb")).to_be_enabled()
            page.unroute("**/api/channels/send", stale)
            well.get_by_test_id("send-back").click()
            dests = _api(page, "GET", "/api/channels/destinations", token=TOKEN)["destinations"]
            prepared = _api(page, "POST", "/api/channels/sends", {"document_ref": ref, "destination_id": dests[0]["id"]}, token=TOKEN)["send"]
            page.reload()
            _normal_chair(page)
            well = open_send()
            well.get_by_test_id("prepared-preview").wait_for()
            well.get_by_test_id("prepared-preview").scroll_into_view_if_needed()
            shot("prepared")
            if phase == "after":
                body_box = well.get_by_test_id("prepared-preview").get_by_test_id("send-preview-body").bounding_box()
                assert body_box and body_box["width"] >= well.bounding_box()["width"] * .8
            well.get_by_test_id("prepared-discard").click()
            shot("discard-question")
            question = well.locator("[data-question]")
            if phase == "after":
                expect(question).to_be_visible()
                expect(question.get_by_role("button", name="Cancel", exact=True)).to_be_focused()
            stored_prepared = next(s for s in _api(page, "GET", f"/api/channels/sends?document_ref={ref}", token=TOKEN)["sends"] if s["id"] == prepared["id"])
            assert stored_prepared["state"] == "prepared", "opening Discard must not write"
            question.get_by_role("button", name="Discard", exact=True).click()
            expect(well.get_by_test_id("prepared-result")).to_contain_text("Discarded")
            if phase == "before":
                well.get_by_test_id("prepared-result").scroll_into_view_if_needed()
            shot("discarded")
            park_builtin_folder()
            page.reload()
            _normal_chair(page)
            win.locator(".thought-note-toolbar").get_by_role("button", name="Send…", exact=True).click()
            well.get_by_test_id("send-none").wait_for()
            shot("no-destination")
            browser.close()
    finally:
        release.set()
        server.stop()
