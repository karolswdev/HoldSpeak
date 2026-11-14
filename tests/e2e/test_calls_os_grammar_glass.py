"""Calls selection, questions and bounded panes at 900 × 600 and 393.

The frame is a real isolated hub. Call/phone reads replay the route tapes;
no phone, microphone, provider or destination is contacted.
"""
from __future__ import annotations

import json
import os
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
    declared = json.loads((ROOT / "tests/fixtures/calls.held.binding.json").read_text())["read"]
    settings = recorded("line.settings.json")
    status = recorded("line.calls.ready.json")
    phone = recorded("phone.settings.json")
    thread = recorded("phone.thread.json")
    phone_calls = recorded("phone.calls.json")
    phase = os.environ.get("CALLS_SHOT_PHASE", "after")
    shots = ROOT / ".tmp/evidence-shots/calls14/r2"
    shots.mkdir(parents=True, exist_ok=True)
    # The real call producer caps list names at 120 characters. Feed it
    # 180-character words, paths and unbroken identifiers, rather than
    # inventing a larger first_words value that the hub cannot return.
    from holdspeak.calls.runner import CallRecord, Line
    long_calls = []
    for index in range(50):
        words = (f"web/src/desk/calls/CallsWindow.tsx: review {index:02} " + "the saved architecture decision and report it to the team " * 4)[:180]
        if index % 2:
            words = (f"`CallTranscript{index:02}" + "SavedArchitectureDecision" * 8)[:179] + "`"
        record = CallRecord(phone_call_id=f"long-{index}", id=f"call-long-{index}", direction="in",
                            remote=tape["detail"]["remote"], state="ended", started_at=1794481200-index*300,
                            answered_at=1794481201-index*300, ended_at=1794481352-index*300, outcome="done")
        record.transcript = [Line("caller", words, record.started_at+5)]
        record.results = [{**tape["detail"]["results"][0], "label":words}]
        long_calls.append(record)
    scene = {"undeclared":False, "long":False, "declared":False, "voice":False, "live": False, "refusal": False, "empty": False, "off": False, "read_failed": False, "phone_failed": False, "telnyx": False, "nodes": "none"}
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
                    return route.fulfill(json={**(recorded("line.calls.starting.json") if scene["telnyx"] else status), "active": tape["undeclared"] if scene["undeclared"] else declared if scene["declared"] else voice if scene["voice"] else tape["held"] if scene["live"] else None})
                if path == "":
                    if scene["undeclared"]:
                        return route.fulfill(json={"calls":[tape["undeclared"]]})
                    if scene["read_failed"]:
                        return route.fulfill(status=503, json={"error": "The calls were not read"})
                    if scene["declared"]:
                        return route.fulfill(json={"calls":[declared]})
                    if scene["voice"]:
                        return route.fulfill(json={"calls":[voice]})
                    if scene["long"]:
                        return route.fulfill(json={"calls":[*tape["recent"]["calls"], *(call.summary() for call in long_calls)]})
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
                if path == f"/{declared['id']}":
                    return route.fulfill(json=declared)
                if path == "/call-voice-face":
                    return route.fulfill(json=voice)
                if path == "/call-face":
                    return route.fulfill(json=tape["undeclared"] if scene["undeclared"] else tape["held"] if scene["live"] else tape["detail"])
                for call in long_calls:
                    if path == f"/{call.id}":
                        return route.fulfill(json=call.full())
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
                expect(window.get_by_test_id("calls-status")).to_be_visible()
                picker = window.get_by_role("button", name="Call view", exact=True)
                if picker.count() and picker.is_visible():
                    picker.click()
                else:
                    window.get_by_role("button", name="Actions ▾", exact=True).first.click()
                    page.get_by_role("menuitem", name="View", exact=True).hover()
                page.get_by_role("menuitem", name=label, exact=True).click()
            def back():
                button = window.get_by_role("button", name="Back", exact=True)
                if width == 393 and button.count() and button.is_visible():
                    button.click()
            def shot(state):
                page.mouse.move(width-1, 0)
                _settle(page)
                if state in ("live", "held", "held-undeclared"):
                    metrics = window.get_by_role("log", name="Transcript").evaluate("""el=>[el,...el.querySelectorAll('li,p')].map(node=>({
                        tag:node.tagName,box:node.getBoundingClientRect().toJSON(),scroll:node.scrollTop,
                        visibility:getComputedStyle(node).visibility,color:getComputedStyle(node).color
                    }))""")
                    (ROOT / f".tmp/calls14-{state}-{width}-geometry.json").write_text(json.dumps(metrics, indent=2))
                if state in ("long-list", "long-results", "long-transcript"):
                    measurements = window.evaluate("""el => {
                        const box = node => node ? node.getBoundingClientRect().toJSON() : null;
                        const row = el.querySelector('[data-call="call-long-0"]');
                        const transcript = el.querySelector('[data-testid=calls-transcript]');
                        const number = [...el.querySelectorAll('[data-facts-name="Call facts"] .gadget-row')].find(row => row.textContent.includes('Number'));
                        return {
                            row: box(row), tracks: row ? getComputedStyle(row).gridTemplateColumns : null,
                            cells: row ? [...row.querySelectorAll('[data-col]')].filter(cell => getComputedStyle(cell).display !== 'none').map(cell => ({key: cell.dataset.col, box: box(cell), padding: getComputedStyle(cell).padding})) : [],
                            name: box(row?.querySelector('.object-list-selection-text')),
                            title: box(row?.querySelector('.object-list-selection-title')),
                            transcript: box(transcript), well: box(transcript?.querySelector('.surface-preference-well')),
                            lastWords: box(transcript?.querySelector('.transcript-list li:last-child p')),
                            number: box(number)
                        };
                    }""")
                    (ROOT / f".tmp/calls14r2-{state}-{width}-{phase}-measurements.json").write_text(json.dumps(measurements, indent=2))
                    visible = measurements["cells"]
                    assert abs(sum(cell["box"]["width"] for cell in visible) - measurements["row"]["width"]) <= 1, "The name track takes all width left by visible facts"
                    assert abs(measurements["title"]["width"] - measurements["name"]["width"]) <= 1, "The fitted name uses its whole text seat"
                    if state == "long-transcript":
                        line_height = window.get_by_test_id("calls-transcript").locator('.transcript-list li:last-child p').evaluate("el=>parseFloat(getComputedStyle(el).lineHeight)")
                        assert measurements["number"]["top"] - measurements["lastWords"]["bottom"] <= line_height, "Number follows the saved words without an empty reading band"
                page.screenshot(path=str(shots / f"audit-{state}-{'900' if width == 1440 else '393'}-{phase}.png"))
                assert window.locator('.cl-plate, .surface-rail, .desk-surface-body .surface-mast, [data-testid="line-egress"], [data-testid="phone-egress"]').count() == 0, state
                assert window.locator('[data-testid="calls-row"] button').count() == 0
                assert window.evaluate("""el => {
                  const body=el.querySelector('.desk-surface-body'),pane=el.querySelector('[data-testid="calls-window"]');
                  return body.scrollWidth<=body.clientWidth+1 && body.scrollHeight<=body.clientHeight+1 && pane.scrollWidth<=pane.clientWidth+1 && pane.scrollHeight<=pane.clientHeight+1;
                }"""), state
                if state in ("line-setup", "line-account", "phone-setup", "phone-alerts", "telnyx-setup", "telnyx-numbers", "telnyx-question", "telnyx-return", "line-add", "line-code", "line-account-telnyx"):
                    assert window.locator('.object-list-row[aria-selected="true"]').count() <= 1
                    for button in window.get_by_role("button").all():
                        if button.is_visible():
                            assert button.evaluate("""el=>{
                                const r=el.getBoundingClientRect(),w=el.closest('[data-layer=window]').getBoundingClientRect();
                                return r.left>=w.left && r.right<=w.right+1 && r.top>=w.top && r.bottom<=w.bottom;
                            }"""), f"{state}: {button.inner_text()}: {button.evaluate("el=>({box:el.getBoundingClientRect().toJSON(), parent:el.parentElement.className, html:el.outerHTML})")}"
                if width == 1440 and state in ("list", "results", "live", "held", "transcript"):
                    assert window.evaluate("""el=>{
                        const list=el.querySelector('[data-testid=calls-list] .object-list').getBoundingClientRect();
                        const pane=el.querySelector('[data-testid=calls-inspector]').getBoundingClientRect();
                        return list.width > pane.width && Math.abs(list.width/(list.width+pane.width)-2/3)<.02;
                    }"""), state
                if state in ("list", "results", "ended"):
                    expect(window.get_by_test_id("calls-list").get_by_role("columnheader", name="State", exact=True)).to_be_visible()
                    expect(window.get_by_test_id("calls-list").get_by_test_id("calls-outcome").first).to_be_visible()
                if state == "list":
                    unanswered = next(call for call in tape["recent"]["calls"] if call["outcome"] == "no_answer")
                    expect(window.locator(f'[data-call="{unanswered["id"]}"] [data-col="length"]')).to_have_text("")
                if width == 1440:
                    for column in ("Call", "At", "Length", "State"):
                        expect(window.get_by_test_id("calls-list").get_by_role("columnheader", name=column, exact=True)).to_be_visible()
                    if not scene["empty"] and not scene["read_failed"] and not scene["voice"] and not scene["declared"] and not scene["undeclared"]:
                        for key in ("when", "length"):
                            cell = window.locator(f'[data-call="call-face"] [data-col="{key}"]')
                            expect(cell).to_be_visible()
                            assert cell.evaluate("el=>el.scrollWidth<=el.clientWidth"), key
                        detail = window.locator('[data-call="call-face"] .object-list-detail')
                        expect(detail).to_have_text("Incoming call")
                if state in ("results", "live", "held", "held-undeclared"):
                    fact = window.get_by_test_id("calls-document").get_by_text("Number", exact=True).locator("..")
                    expect(fact).to_be_visible()
                    expect(fact).to_contain_text("+1 ··· 0142")
                    assert fact.evaluate("el=>Boolean(el.closest('[data-feedback-redact=true]'))")
                    expect(window.get_by_test_id("calls-document")).not_to_contain_text(tape["detail"]["remote"])
                if state in ("live", "held", "held-undeclared"):
                    words = window.get_by_role("log", name="Transcript").locator("li").last.locator("p")
                    expect(words).to_be_visible()
                    assert words.evaluate("el=>getComputedStyle(el).gridRowStart==='2'"), "Narrow transcript words use the whole next line"
                    assert window.get_by_role("log", name="Transcript").locator("li").last.evaluate("""el=>{
                        const line=el.getBoundingClientRect(),well=el.closest('[role=log]').getBoundingClientRect();
                        return line.top>=well.top-1 && line.bottom<=well.bottom+1;
                    }"""), f"{state}: newest words must stay whole"
                    if width == 1440:
                        expect(window.get_by_test_id("calls-results")).to_be_visible()
                        assert window.get_by_test_id("calls-result").first.evaluate("""el=>{
                            const row=el.getBoundingClientRect(),pane=el.closest('[data-testid=calls-inspector]').getBoundingClientRect();
                            return row.top>=pane.top && row.bottom<=pane.bottom;
                        }"""), f"{state}: a result stays whole below the live words"
                if state in ("line-account", "line-account-telnyx"):
                    limit = window.get_by_test_id("line-from-calls").locator(".gadget-row-gadget")
                    assert limit.evaluate("el=>el.scrollWidth<=el.clientWidth"), "Daily limit must fit its fact row"
                if state == "line-setup":
                    field = window.get_by_role("textbox", name="Line address", exact=True)
                    expect(field).to_have_value("SIP ···")
                    assert field.evaluate("el=>Boolean(el.closest('[data-feedback-redact=true]'))")
                    assert field.evaluate("el=>getComputedStyle(el).textTransform==='none' && el.scrollWidth<=el.clientWidth+1"), "Show the address from its start, in its own case"
                    expect(window.get_by_test_id("line-test")).not_to_contain_text(settings["allowed_numbers"][0])
                if state == "transcript":
                    assert window.get_by_test_id("calls-transcript").locator(".transcript-list li").first.evaluate("""el=>{
                        const row=el.getBoundingClientRect(),well=el.closest('.surface-preference-well').getBoundingClientRect();
                        return row.top>=well.top-1 && row.bottom<=well.bottom+1;
                    }"""), state
                if state == "phone-reply":
                    expect(window.get_by_test_id("phone-replying")).to_contain_text("Yes, retry it.")
                if state == "phone":
                    assert window.get_by_test_id("phone-wing").locator('.object-list-row [data-col]:not([data-col="name"])').count() == 0, "Message names use the free row width"
                    expect(window.get_by_test_id("phone-message").first.locator('.object-list-selection-title')).to_have_text(thread["messages"][0]["text"])
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
                if state == "call-failed":
                    expect(window.get_by_role("alert")).to_have_count(1)
                    expect(window.get_by_test_id("calls-refusal")).to_have_text("A call is on the line")
                    expect(window.get_by_test_id("calls-status")).to_contain_text("On the line")
                if state == "telnyx-setup" and width == 1440:
                    assert window.get_by_test_id("telnyx-balance").evaluate("""el=>{
                        const label=el.querySelector('.gadget-row-label').getBoundingClientRect();
                        const value=el.querySelector('.gadget-row-gadget').getBoundingClientRect();
                        return label.left<value.left && label.top<value.bottom && value.top<label.bottom;
                    }"""), "Balance is a fact row"
                page.screenshot(path=str(shots / f"audit-{state}-{'900' if width == 1440 else '393'}-{phase}.png"))
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
            for fact in tape["held"]["hold"]["facts"]:
                expect(window.get_by_test_id("calls-hold").get_by_text(fact["label"], exact=True).locator("..")).to_contain_text(fact["value"])
            shot("held")
            if width == 393:
                view("Results")
            else:
                picker = window.get_by_role("button", name="Call view", exact=True)
                picker.click()
                expect(page.get_by_role("menuitem", name="Results", exact=True)).to_have_count(0)
                page.keyboard.press("Escape")
                expect(picker).to_have_attribute("aria-expanded", "false")
            expect(window.get_by_test_id("calls-results")).to_contain_text("Platform plan")
            expect(window.get_by_test_id("calls-hold")).to_be_visible()
            shot("held-results")
            if width == 393:
                view("All calls")
            window.get_by_test_id("calls-yes").click()
            expect(window.get_by_test_id("calls-hold")).to_have_count(0)
            expect(window.get_by_test_id("calls-hangup")).to_be_visible()
            expect(window.locator(".surface-mast-figures [data-tone=stop]")).to_contain_text("1:12")
            shot("live")
            if width == 393:
                view("Results")
            expect(window.get_by_test_id("calls-results")).to_contain_text("Sent on your yes")
            shot("live-results")
            if width == 393:
                view("All calls")
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
            view("Line account")
            expect(window.get_by_test_id("line-user")).to_be_visible()
            shot("line-account-telnyx")
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
            scene.update(declared=True, voice=False)
            page.clock.set_fixed_time("2026-11-12T09:16:43-07:00")
            page.reload(wait_until="load")
            _normal_chair(page)
            question = window.get_by_test_id("calls-hold")
            expect(question).to_be_visible()
            for fact in declared["hold"]["facts"]:
                row = question.get_by_text(fact["label"], exact=True).locator("..")
                expect(row).to_contain_text(fact["value"])
            expect(question).not_to_contain_text("not described")
            expect(window.get_by_test_id("calls-no")).to_be_focused()
            shot("held-declared")
            scene.update(undeclared=True, declared=False)
            page.reload(wait_until="load")
            _normal_chair(page)
            question = window.get_by_test_id("calls-hold")
            expect(question.get_by_text("Write details", exact=True).locator("..")).to_contain_text("not described")
            shot("held-undeclared")
            scene.update(long=True, undeclared=False, live=False)
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(window.get_by_test_id("calls-row")).to_have_count(53)
            expect(window.locator('[data-testid="calls-row"] .object-list-selection-name > img')).to_have_count(0)
            expect(window.locator('[data-call="call-long-0"] .surface-lamp')).to_have_count(1)
            shot("long-list")
            window.locator('[data-call="call-long-0"]').click()
            expect(window.get_by_test_id("calls-document")).to_be_visible()
            expect(window.get_by_test_id("calls-document").locator('.surface-inspector-object img')).to_have_attribute("src", "/_built/desk/sprites/32/call.png")
            shot("long-results")
            verb("Open transcript")
            expect(window.get_by_test_id("calls-transcript")).to_contain_text(long_calls[0].transcript[0].text)
            shot("long-transcript")
            assert not errors, errors
            browser.close()
    finally:
        server.should_exit = True
