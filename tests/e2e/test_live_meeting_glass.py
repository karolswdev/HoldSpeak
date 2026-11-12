"""Live meeting's shared transcript, inspector and stopped work at both sizes.

Only recorded hub replies reach the face. The rig keeps microphone and
recording probes off; no microphone or provider is used.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import pytest
from tests._evidence import evidence_dir
from .glass_infra import clear_hub_windows_http
from .test_desk_sweep import LIST_GRAMMAR_JS, TOKEN, T, _Case, _hub_open, _normal_chair, _page, desk, pw_browser

ROOT = Path(__file__).resolve().parents[2]
WIRES = ROOT / "web/src/test/wire"


def _wire(name: str) -> Any:
    return json.loads((WIRES / f"{name}.wire.json").read_text())["wire"]


def _press(page: Any, win: Any, name: str) -> None:
    verb = win.get_by_role("button", name=name, exact=True)
    if verb.count() and verb.first.is_visible():
        verb.first.click()
    else:
        win.get_by_role("button", name="Actions", exact=True).click()
        page.get_by_role("menuitem", name=name, exact=True).click()


@pytest.mark.parametrize("width", [900, 393])
@pytest.mark.timeout(240)
def test_live_transcript_and_inspectors(desk: dict[str, Any], pw_browser: Any, width: int) -> None:
    from playwright.sync_api import expect

    base = desk["base"]
    clear_hub_windows_http(base, TOKEN)
    _hub_open(base, "surface-live", None, window=width == 900)
    ctx, page, errors, requests = _page(pw_browser, width, base)
    out = evidence_dir("live13/r2")
    actions = _wire("live.actions")
    state = copy.deepcopy(actions["state"])
    ready: dict[str, Any] = {"meeting_active": False}
    current = {"state": ready, "mic": _wire("live.mic-check.hearing"), "fail": False, "stop": "saved"}
    # Replay the recorded read without unrelated rig runtime frames.
    page.route_web_socket("**/ws*", lambda socket: None)
    page.route("**/api/state", lambda route: route.fulfill(json=current["state"]))
    page.route("**/api/projects", lambda route: route.fulfill(json=actions["projects"]))
    page.route("**/api/projects/*/meetings/*", lambda route: route.fulfill(status=503, json={"detail": "Project link not saved"}) if current["fail"] else route.fulfill(json=actions["project_link"]))
    page.route("**/api/meeting/mic-check", lambda route: route.fulfill(json=current["mic"]))
    page.route("**/api/bookmark", lambda route: route.fulfill(status=503, json={"detail": "Moment not saved"}) if current["fail"] else route.fulfill(json=actions["bookmarks"]["The freeze date"]))
    page.route("**/api/meeting", lambda route: route.fulfill(status=503, json={"detail": "Details not saved"}) if current["fail"] else route.fulfill(json=actions["updates"]["Ledger review"]))
    # The stop receipt fields are the existing runtime Stop contract. Audio is
    # never started: this press only exercises the face's retained transcript.
    def stop(route: Any) -> None:
        if current["stop"] == "failed":
            route.fulfill(status=503, json={"detail": "Meeting did not stop"})
        elif current["stop"] == "saved":
            route.fulfill(json=actions["stop"])
        else:
            route.fulfill(json={"success": True, "status": "stopped", "meeting": {"id": state["id"], "capture_status": "recoverable" if current["stop"] == "recoverable" else "finalized"}, "save": {"database_saved": current["stop"] == "saved", "json_saved": True}, "save_error": "Database write failed" if current["stop"] == "recoverable" else ""})
    page.route("**/api/meeting/stop", stop)
    page.route("**/capture/recover", lambda route: route.fulfill(json={"recovered": True}))
    try:
        drawing = Path("/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/1feb1071-623f-4f4e-b10c-c152686a7e30/scratchpad/wave13/faces.html")
        if drawing.exists():
            canvas = ctx.new_page()
            canvas.goto(drawing.as_uri(), wait_until="load")
            canvas.locator("#live .v.stop").first.hover()
            canvas.close()
        page.goto(f"{base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        sweep = _Case(page, base, "surface-live", errors, requests)
        win = page.locator("#surface-live")

        def shot(name: str) -> None:
            sweep.settle()
            page.mouse.move(2, 2)
            assert not page.evaluate(LIST_GRAMMAR_JS, "#surface-live"), name
            stop_verb = win.get_by_role("button", name="Stop meeting", exact=True)
            if stop_verb.count():
                expect(stop_verb).to_be_visible()
                button, seat = stop_verb.bounding_box(), win.bounding_box()
                assert button and seat and button["y"] >= seat["y"] and button["y"] + button["height"] <= seat["y"] + seat["height"]
            if width == 393 and win.get_by_test_id("live-inspector-back").count():
                expect(win.get_by_role("button", name="Back", exact=True)).to_have_count(1)
                assert not win.locator(".surface-list-back").count()
            if win.get_by_role("tablist", name="Meeting work").count() and win.get_by_role("tablist", name="Meeting work").is_visible():
                expect(win.get_by_role("tab", name="Step 1: Recorded, Done", exact=True)).to_be_visible()
                if width == 393:
                    expect(win.locator(".surface-step-current-name")).to_be_visible()
            page.screenshot(path=str(out / f"{name}-{width}.png"))

        def reload() -> None:
            page.reload(wait_until="load")
            _normal_chair(page)
            sweep.settle()

        expect(win.get_by_role("textbox", name="Meeting name", exact=True)).to_be_visible(timeout=T)
        expect(win.get_by_role("combobox", name="Microphone", exact=True)).to_be_visible()
        assert win.locator(".live-ready-plate, .live-native-body, .live-mast").count() == 0
        assert "Your next meeting" not in win.inner_text()
        shot("ready")
        current["mic"] = _wire("live.mic-check.not-allowed")
        reload()
        expect(win.get_by_test_id("live-ready-mic-state")).to_have_text("Microphone not allowed")
        shot("microphone-refused")
        empty = copy.deepcopy(state)
        empty.update(segments=[], intel=None)
        current["state"] = empty
        reload()
        expect(win.get_by_test_id("live-transcript")).to_be_visible()
        expect(win.get_by_text("Listening for speech", exact=True)).to_have_count(1)
        assert not win.get_by_test_id("live-transcript").get_by_test_id("live-listening").count()
        shot("recording-empty")
        current["state"] = state
        reload()
        expect(win.get_by_test_id("live-transcript-line")).to_have_count(4)
        well = win.get_by_test_id("live-transcript")
        expect(well).to_have_attribute("data-feedback-redact", "true")
        expect(well.locator("li[data-mark]")).to_have_count(1)
        assert well.locator("li[data-mark]").evaluate("el => parseFloat(getComputedStyle(el).borderInlineStartWidth)") == 3
        assert well.evaluate("el => getComputedStyle(el).overflowY") == "auto"
        bounds = well.bounding_box()
        body = win.locator(".desk-surface-body").bounding_box()
        assert bounds and body and bounds["y"] + bounds["height"] <= body["y"] + body["height"] + 1
        expect(win.get_by_test_id("live-toolbar").get_by_role("combobox", name="Microphone", exact=True)).to_be_visible()
        assert not win.get_by_test_id("live-transcript").get_by_role("combobox").count()
        expect(win.locator('.surface-mast-figures > [data-tone="recording"]')).to_be_visible()
        shot("recording")
        toolbar = win.get_by_test_id("live-toolbar")
        assert toolbar.bounding_box()["height"] < 70, "Verbs fit one strip"
        expect(win.locator(".surface-mast-facts")).to_have_text("Recording")
        _press(page, win, "View: Caught so far")
        expect(win.get_by_test_id("live-caught")).to_be_visible()
        assert not win.get_by_role("button", name="Done", exact=True).count()
        expect(win.get_by_role("columnheader", name="At", exact=True)).to_be_visible()
        if width == 393:
            expect(win.get_by_role("button", name="Back", exact=True)).to_have_count(1)
            assert not win.locator(".surface-list-back").count()
            expect(win.get_by_role("button", name="Stop meeting", exact=True)).to_be_visible()
        recap = win.get_by_test_id("live-caught")
        list_box = recap.get_by_role("grid", name="Caught so far", exact=True).bounding_box()
        facts_box = recap.get_by_role("region", name="Meeting facts", exact=True).bounding_box()
        assert list_box and facts_box and 0 <= facts_box["y"] - list_box["y"] - list_box["height"] <= 20
        shot("caught")
        _press(page, win, "View: Transcript")
        expect(win.get_by_test_id("live-caught")).to_have_count(0)
        shot("inspector-closed")
        _press(page, win, "View: Caught so far")
        if width == 393:
            win.get_by_test_id("live-inspector-back").click()
        _press(page, win, "Name this moment")
        field = win.get_by_role("textbox", name="Name this moment", exact=True)
        field.fill("The freeze date")
        assert field.evaluate("el => el.scrollLeft") == 0
        shot("moment")
        current["fail"] = True
        win.get_by_role("button", name="Bookmark", exact=True).click()
        expect(field).to_have_value("The freeze date")
        expect(win.get_by_role("status").filter(has_text="Moment not saved")).to_be_visible()
        expect(win.locator(".surface-mast-facts")).to_have_text("Recording")
        shot("moment-failed")
        current["fail"] = False
        win.get_by_role("button", name="Bookmark", exact=True).click()
        expect(field).to_have_count(0)
        _press(page, win, "Edit details")
        title = win.get_by_role("textbox", name="Title", exact=True)
        title.fill("Ledger review")
        shot("details")
        for part in (win.get_by_test_id("live-details").locator(".gadget-row").first, win.get_by_role("button", name="Save", exact=True)):
            box = part.bounding_box()
            seat = win.bounding_box()
            assert box and seat and box["y"] >= seat["y"] and box["y"] + box["height"] <= seat["y"] + seat["height"]
        last = win.get_by_test_id("live-details").locator(".gadget-row").last.bounding_box()
        save = win.get_by_role("button", name="Save", exact=True).bounding_box()
        assert last and save and 0 <= save["y"] - last["y"] - last["height"] <= 20
        current["fail"] = True
        win.get_by_role("button", name="Save", exact=True).click()
        expect(title).to_have_value("Ledger review")
        expect(win.locator(".surface-mast-facts")).to_have_text("Recording")
        shot("details-failed")
        current["fail"] = False
        win.get_by_role("button", name="Save", exact=True).click()
        expect(title).to_have_count(0)
        if width == 393:
            win.get_by_test_id("live-inspector-back").click()
        _press(page, win, "Add to project")
        project_choice = win.get_by_role("combobox", name="Project", exact=True)
        project = next(row for row in actions["projects"]["projects"] if row["name"] == "Payments ledger cutover")
        expect(project_choice).to_have_value(project["id"])
        shot("project")
        current["fail"] = True
        win.get_by_role("button", name="Add", exact=True).click()
        expect(win.get_by_text("Project link not saved", exact=True)).to_be_visible()
        expect(project_choice).to_have_value(project["id"])
        shot("project-failed")
        current["fail"] = False
        win.get_by_role("button", name="Add", exact=True).click()
        expect(win.get_by_text(f"Added to {project['name']}", exact=True)).to_be_visible()
        expect(project_choice).to_have_count(0)
        shot("project-added")
        if width == 393:
            win.get_by_test_id("live-inspector-back").click()
        current["stop"] = "failed"
        _press(page, win, "Stop meeting")
        expect(win.get_by_role("button", name="Retry", exact=True)).to_be_visible()
        expect(win.locator(".surface-mast-facts")).to_have_text("Recording")
        shot("stop-failed")
        current["stop"] = "saved"
        win.get_by_role("button", name="Retry", exact=True).click()
        expect(win.get_by_role("tablist", name="Meeting work")).to_be_visible()
        expect(well.locator("li")).to_have_count(4)
        expect(win.get_by_role("button", name="Start meeting", exact=True)).to_be_enabled()
        shot("stopped")
        # Reopened stopped state comes from the same runtime producer shape;
        # intel status is a real enum, not a fabricated percentage.
        stopped = copy.deepcopy(actions["saved"])
        stopped.update(meeting_active=False, active=False, stopped=True, intel_status={"state": "running"})
        current["state"] = stopped
        reload()
        expect(win.locator('[data-testid="live-summary-engine"] .surface-meter')).to_be_visible()
        shot("summary-running")
        pane_width = win.get_by_test_id("live-room").bounding_box()["width"]
        win.get_by_role("tab", name=re.compile(r"^Step 3: Summary")).click()
        assert abs(win.get_by_test_id("live-room").bounding_box()["width"] - pane_width) <= 1
        expect(win.get_by_test_id("live-summary")).to_have_text("Summary running")
        shot("summary-pane")
        win.get_by_role("tab", name=re.compile(r"^Step 1: Recorded")).click()
        shot("recorded-pane")
        win.get_by_role("tab", name=re.compile(r"^Step 4: Proposals")).click()
        shot("proposals")
        if width == 393:
            win.get_by_test_id("live-inspector-back").click()
        win.get_by_role("tab", name=re.compile(r"^Step 2: Transcript")).click()
        page.emulate_media(reduced_motion="no-preference")
        shot("summary-motion")
        page.emulate_media(reduced_motion="reduce")
        _press(page, win, "View: Caught so far")
        shot("stopped-caught")
        current["state"] = state
        current["stop"] = "recoverable"
        reload()
        _press(page, win, "Stop meeting")
        expect(win.get_by_role("button", name="Retry recovery", exact=True)).to_be_visible()
        assert not win.get_by_role("button", name="Open meeting", exact=True).count()
        shot("stop-recoverable")
        win.get_by_role("button", name="Retry recovery", exact=True).click()
        expect(win.get_by_role("button", name="Open meeting", exact=True)).to_be_visible()
        shot("stop-recovered")
        current["state"] = stopped
        stopped["intel_status"] = {"state": "error", "detail": "Summary engine stopped"}
        reload()
        expect(win.get_by_text("Summary engine stopped", exact=True)).to_be_visible()
        expect(win.get_by_role("button", name="Try again", exact=True)).to_be_visible()
        expect(win.get_by_role("tab", name="Step 1: Recorded, Done", exact=True)).to_be_visible()
        shot("summary-failed")
        assert not [error for error in errors if error.startswith("pageerror:")], errors
    finally:
        ctx.close()
