"""Calls selection, questions and bounded panes at 900 × 600 and 393.

The frame is a real isolated hub. Call/phone reads replay the route tapes;
no phone, microphone, provider or destination is contacted.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "web/src/desk/calls/__fixtures__"
TOKEN = "calls-grammar"


def recorded(name):
    return json.loads((FIXTURES / name).read_text())


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_calls_selection_and_states(tmp_path, monkeypatch, width):
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    tape = recorded("calls.face.json")
    voice = recorded("calls.voice.face.json")["read"]
    settings = recorded("line.settings.json")
    status = recorded("line.calls.ready.json")
    phone = recorded("phone.settings.json")
    thread = recorded("phone.thread.json")
    phone_calls = recorded("phone.calls.json")
    shots = ROOT / ".tmp/evidence-shots/calls13/r2"
    shots.mkdir(parents=True, exist_ok=True)
    scene = {"voice":False, "live": False, "refusal": False, "empty": False, "off": False, "read_failed": False, "phone_failed": False, "telnyx": False, "nodes": "none"}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.clock.set_fixed_time("2026-11-12T04:01:13-07:00")
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            def calls_wire(route):
                path = route.request.url.split("/api/calls", 1)[1].split("?", 1)[0]
                if path == "/line/telnyx/status":
                    return route.fulfill(json=recorded("line.telnyx.status.connected.json"))
                if path == "/line/status":
                    return route.fulfill(json=recorded("line.status.telnyxStored.json" if scene["telnyx"] else "line.status.ready.json"))
                if path == "/line/nodes":
                    return route.fulfill(json=recorded("line.nodes.none.json" if scene["nodes"] == "none" else "line.nodes.ready.json"))
                if path == "/line/codes":
                    return route.fulfill(json=recorded("line.codes.karol.json"))
                if path == "/line/telnyx/numbers":
                    return route.fulfill(json=recorded("line.telnyx.numbers.212.json"))
                if path == "/status":
                    return route.fulfill(json={**(recorded("line.calls.starting.json") if scene["telnyx"] else status), "active": voice if scene["voice"] else tape["held"] if scene["live"] else None})
                if path == "":
                    if scene["read_failed"]:
                        return route.fulfill(status=503, json={"error": "The calls were not read"})
                    if scene["voice"]:
                        return route.fulfill(json={"calls":[voice]})
                    return route.fulfill(json={"calls": []} if scene["empty"] else tape["listed"] if scene["live"] else tape["recent"])
                if path.endswith("/decide"):
                    assert route.request.post_data_json["binding"] == tape["held"]["hold"]["binding"]
                    scene["live"] = True
                    return route.fulfill(json=tape["approved"] if route.request.post_data_json["decision"] == "approve" else tape["denied"])
                if path.endswith("/hangup"):
                    scene["live"] = False
                    return route.fulfill(json=tape["ended"])
                if path == "/place":
                    if scene["refusal"]:
                        return route.fulfill(status=409, json={"reason": "busy", "error": "A call is on the line"})
                    scene["live"] = True
                    return route.fulfill(json=tape["placed"])
                if path == "/call-voice-face":
                    return route.fulfill(json=voice)
                if path == "/call-face":
                    return route.fulfill(json=tape["held"] if scene["live"] else tape["detail"])
                return route.continue_()
            page.route("**/api/calls**", calls_wire)
            def settings_wire(route):
                if route.request.method == "GET":
                    preferences = recorded("line.telnyx.settings.connected.json") if scene["telnyx"] else settings
                    return route.fulfill(json={"calls": {**preferences, "phone_on": True, "enabled": not scene["off"]}})
                return route.continue_()
            page.route("**/api/settings", settings_wire)
            page.route("**/api/phone/status", lambda route: route.fulfill(json=phone))
            def phone_messages(route):
                if route.request.method == "POST" and route.request.url.endswith("/api/phone/messages") and scene["phone_failed"]:
                    return route.fulfill(status=503, json={"error": "Phone offline"})
                return route.fulfill(json=thread)
            page.route("**/api/phone/messages**", phone_messages)
            page.route("**/api/phone/push", lambda route: route.fulfill(json=recorded("phone.push.stored.json")))
            page.route("**/api/phone/calls", lambda route: route.fulfill(json=phone_calls))
            clear_hub_windows_http(base, TOKEN)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            page.evaluate("sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key:'open-calls'}))")
            page.reload(wait_until="load")
            _normal_chair(page)
            window = page.locator("#surface-calls")
            window.get_by_test_id("calls-window").wait_for()
            if width == 1440:
                _api(page, "POST", "/api/desk/windows/surface-calls/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
            def verb(label):
                button = window.get_by_role("button", name=label, exact=True)
                if button.count() and button.is_visible():
                    button.click()
                else:
                    window.get_by_role("button", name="Actions ▾", exact=True).first.click()
                    page.get_by_role("menuitem", name=label, exact=False).click()
            def view(label):
                window.get_by_role("button", name="Call view", exact=True).click()
                page.get_by_role("menuitem", name=label, exact=True).click()
            def back():
                button = window.get_by_role("button", name="Back", exact=True)
                if width == 393 and button.count() and button.is_visible():
                    button.click()
            def shot(state):
                page.mouse.move(width-1, 0)
                _settle(page)
                assert window.locator('.cl-plate, .surface-rail, .desk-surface-body .surface-mast, [data-testid="line-egress"], [data-testid="phone-egress"]').count() == 0, state
                assert window.locator('[data-testid="calls-row"] button').count() == 0
                assert window.evaluate("""el => {
                  const body=el.querySelector('.desk-surface-body'),pane=el.querySelector('[data-testid="calls-window"]');
                  return body.scrollWidth<=body.clientWidth+1 && body.scrollHeight<=body.clientHeight+1 && pane.scrollWidth<=pane.clientWidth+1 && pane.scrollHeight<=pane.clientHeight+1;
                }"""), state
                if state in ("line-setup", "line-account", "phone-setup", "phone-alerts"):
                    assert window.locator('.object-list-row[aria-selected="true"]').count() <= 1
                if state == "phone-reply":
                    expect(window.get_by_test_id("phone-replying")).to_contain_text("Yes, retry it.")
                if state == "phone":
                    assert window.locator('[data-testid="phone-message"]').first.evaluate("""el => {
                        const row=el.getBoundingClientRect(), well=el.closest('.object-list-rows').getBoundingClientRect();
                        return row.top>=well.top && row.bottom<=well.bottom+1;
                    }"""), state
                if state in ("phone-reply", "phone-send-failed", "phone-return"):
                    assert window.get_by_role("textbox", name="Message your phone", exact=True).evaluate("""el => {
                        const field=el.getBoundingClientRect(), well=el.closest('.surface-inspector-fields').getBoundingClientRect();
                        return field.top>=well.top && field.bottom<=well.bottom+1;
                    }"""), state
                assert window.locator(".surface-pane-inspector").evaluate_all("""nodes=>nodes.every(el=>{
                  const r=el.getBoundingClientRect(),w=el.closest('[data-layer=window]').getBoundingClientRect();
                  return !r.height || r.left>=w.left && r.right<=w.right+1 && r.bottom<=w.bottom+1;
                })"""), state
                page.screenshot(path=str(shots / f"{state}-{'900' if width == 1440 else '393'}.png"))
            shot("list")
            row = window.locator('[data-call="call-face"]')
            row.click()
            expect(window.get_by_test_id("calls-document")).to_be_visible()
            shot("results")
            verb("Open transcript")
            expect(window.get_by_test_id("calls-transcript")).to_contain_text("Review the platform plan.")
            shot("transcript")
            back()
            row.click(button="right")
            expect(page.get_by_role("menuitem", name="Open transcript", exact=False)).to_be_visible()
            shot("context-menu")
            page.keyboard.press("Escape")
            scene["refusal"] = True
            verb("Call me")
            expect(window.get_by_test_id("calls-refusal")).to_be_visible()
            expect(window.get_by_test_id("calls-status")).not_to_contain_text("Call failed")
            assert window.get_by_test_id("calls-document").locator(".surface-pane-inspector-head").evaluate("""el => {
                const r=el.getBoundingClientRect(), pane=el.closest('.surface-list-pane-preview').getBoundingClientRect();
                return r.top>=pane.top-1 && r.bottom<=pane.bottom+1;
            }""")
            shot("call-failed")
            scene["refusal"] = False
            window.get_by_role("button", name="Read again", exact=True).click()
            expect(window.get_by_test_id("calls-call-me")).to_be_enabled()
            verb("Call me")
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(window.get_by_test_id("calls-hold")).to_be_visible()
            expect(window.get_by_test_id("calls-no")).to_be_focused()
            for test_id in ("calls-yes", "calls-no"):
                assert window.get_by_test_id(test_id).evaluate("""el => {
                    const r=el.getBoundingClientRect(), w=el.closest('[data-layer=window]').getBoundingClientRect();
                    return r.top>=w.top && r.bottom<=w.bottom-24;
                }"""), test_id
            stop = window.get_by_test_id("calls-hangup")
            expect(stop).to_be_visible()
            expect(stop).to_have_class(__import__("re").compile("btn--danger"))
            expect(window.get_by_test_id("calls-toolbar").locator(".object-list-toolbar-strip > button").first).to_have_text("Hang up")
            expect(window.get_by_test_id("calls-yes-effect")).to_contain_text(tape["held"]["hold"]["words"])
            shot("held")
            window.get_by_test_id("calls-yes").click()
            expect(window.get_by_test_id("calls-hold")).to_have_count(0)
            expect(window.get_by_test_id("calls-hangup")).to_be_visible()
            expect(window.locator(".surface-mast-figures [data-tone=stop]")).to_contain_text("1:12")
            shot("live")
            verb("Hang up")
            shot("ended")
            back()
            window.get_by_test_id("calls-rail-phone").click()
            expect(window.get_by_test_id("phone-wing")).to_be_visible()
            shot("phone")
            verb("New message")
            expect(window.get_by_role("textbox", name="Message your phone", exact=True)).to_have_value("")
            expect(window.get_by_role("textbox", name="Message your phone", exact=True)).to_be_focused()
            shot("phone-new-message")
            window.get_by_role("button", name="Cancel", exact=True).click()
            incoming = next(message for message in thread["messages"] if message["direction"] == "from_phone")
            window.locator(f'[data-message="{incoming["id"]}"]').click()
            verb("Reply")
            window.get_by_role("textbox", name="Message your phone", exact=True).fill("Keep the staging window")
            shot("phone-reply")
            scene["phone_failed"] = True
            window.get_by_test_id("phone-send").click()
            expect(window.get_by_test_id("phone-refusal")).to_be_visible()
            expect(window.get_by_role("textbox", name="Message your phone", exact=True)).to_have_value("Keep the staging window")
            shot("phone-send-failed")
            view("Line setup")
            expect(window.get_by_test_id("line-settings")).to_be_visible()
            shot("line-setup")
            window.get_by_role("button", name="Add machine", exact=True).click()
            expect(window.get_by_test_id("line-add")).to_be_visible()
            shot("line-add")
            window.get_by_role("textbox", name="Add a machine", exact=True).fill("karol")
            window.get_by_role("button", name="Install the Line on karol", exact=True).click()
            expect(window.get_by_test_id("line-code-sheet")).to_be_visible()
            shot("line-code")
            window.get_by_test_id("line-code-cancel").click()
            view("Line account")
            expect(window.get_by_test_id("line-from-calls")).to_be_visible()
            shot("line-account")
            view("Phone setup")
            expect(window.get_by_test_id("phone-settings")).to_be_visible()
            shot("phone-setup")
            view("Phone alerts")
            expect(window.get_by_test_id("phone-push-key-id")).to_be_visible()
            assert window.get_by_role("textbox", name="App bundle ID", exact=True).evaluate("""el => {
                const r=el.getBoundingClientRect(), w=el.closest('[data-layer=window]').getBoundingClientRect();
                return r.left>=w.left && r.right<=w.right;
            }""")
            assert window.get_by_test_id("phone-push-host").evaluate("""el => {
                const r=el.querySelector('select,button').getBoundingClientRect(), row=el.closest('.gadget-row').getBoundingClientRect();
                return r.top>=row.top && r.bottom<=row.bottom+1;
            }""")
            shot("phone-alerts")
            view("All calls")
            expect(window.get_by_role("textbox", name="Message your phone", exact=True)).to_have_value("Keep the staging window")
            shot("phone-return")
            window.get_by_role("button", name="Cancel", exact=True).click()
            expect(window.get_by_test_id("phone-new-message")).to_be_visible()
            shot("phone-draft-kept")
            verb("New message")
            expect(window.get_by_role("textbox", name="Message your phone", exact=True)).to_have_value("Keep the staging window")
            scene["empty"] = True
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(window.get_by_test_id("calls-line-summary")).to_contain_text("No calls yet")
            shot("empty")
            scene["off"] = True
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(window.get_by_test_id("calls-status")).to_contain_text("Calls are off")
            shot("off")
            scene["read_failed"] = True
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(window.get_by_role("alert")).to_be_visible()
            expect(window.get_by_test_id("calls-status")).to_contain_text("Calls not read")
            shot("read-failed")
            scene.update(read_failed=False, off=False, empty=False, telnyx=True)
            page.reload(wait_until="load")
            _normal_chair(page)
            view("Telnyx setup")
            expect(window.get_by_test_id("telnyx-setup").get_by_label("Area code", exact=True)).to_be_visible()
            assert window.get_by_role("textbox", name="Area code", exact=True).evaluate("""el => {
                const r=el.getBoundingClientRect(), w=el.closest('[data-layer=window]').getBoundingClientRect();
                return r.left>=w.left && r.right<=w.right;
            }""")
            shot("telnyx-setup")
            window.get_by_role("textbox", name="Area code", exact=True).fill("212")
            window.get_by_test_id("telnyx-find").click()
            expect(window.get_by_test_id("telnyx-numbers")).to_be_visible()
            assert window.get_by_test_id("telnyx-number").first.evaluate("""el => {
                const r=el.getBoundingClientRect(), well=el.closest('.object-list-rows').getBoundingClientRect();
                return r.top>=well.top-1 && r.bottom<=well.bottom+1;
            }""")
            shot("telnyx-numbers")
            number = window.get_by_test_id("telnyx-number").first
            number.click()
            verb("Buy…")
            expect(window.get_by_test_id("telnyx-buy")).to_be_visible()
            expect(window.get_by_test_id("telnyx-buy-question").get_by_role("button", name="Cancel",exact=True)).to_be_focused()
            assert window.get_by_test_id("telnyx-buy").evaluate("""el=>{
                const r=el.getBoundingClientRect(),w=el.closest('[data-layer=window]').getBoundingClientRect();
                return r.top>=w.top && r.bottom<=w.bottom-24;
            }""")
            shot("telnyx-question")
            window.get_by_test_id("telnyx-buy-question").get_by_role("button", name="Cancel", exact=True).click()
            expect(window.get_by_test_id("telnyx-number").first).to_have_attribute("aria-selected", "true")
            shot("telnyx-return")
            scene.update(voice=True, live=False, telnyx=False)
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(window.get_by_test_id("calls-phone-answer")).to_contain_text("Waits for your voice")
            expect(window.get_by_test_id("calls-yes")).to_have_count(0)
            expect(window.get_by_test_id("calls-no")).to_have_count(0)
            expect(window.get_by_test_id("calls-hangup")).to_be_visible()
            shot("voice-question")
            assert not errors, errors
            browser.close()
    finally:
        server.should_exit = True
