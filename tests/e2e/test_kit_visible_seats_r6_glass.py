"""The kit fits the visible seat, reading lines and the reading/list inset."""

from pathlib import Path
import json
import os
import uuid

import pytest
from .glass_infra import (
    _api,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
    choose_toolbar,
    press_verb,
)
from .test_settings_page_glass import TOKEN, _open_page

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".tmp/evidence-shots/kit14/r6"
TITLE = "Review the architecture migration and keep the current rollback plan, its decisions and the report for the steering group in view while the next delivery waits for its destination."
PERMISSION = (
    "Nothing was sent because access was refused; check permissions and try again."
)

VISIBLE = r"""el=>{let r=el.getBoundingClientRect(),top=r.top+el.clientTop,bottom=top+el.clientHeight;for(let p=el.parentElement;p;p=p.parentElement){if(['hidden','clip','auto','scroll'].includes(getComputedStyle(p).overflowY)){const b=p.getBoundingClientRect();top=Math.max(top,b.top+p.clientTop);bottom=Math.min(bottom,b.top+p.clientTop+p.clientHeight);}}const clip=getComputedStyle(el).clipPath.match(/inset\(([^)]+)\)/)?.[1].split(' ').map(parseFloat);top=Math.max(top,r.top+(clip?.[0]||0));bottom=Math.min(bottom,r.bottom-(clip?.[2]||0));return {top,bottom};}"""
WHOLE_ROWS = r"""el=>{const b=VISIBLE_BOUNDARY(el),rows=[...el.querySelectorAll('.object-list-row')].map(row=>({id:row.dataset.objectId,...row.getBoundingClientRect().toJSON()})),shown=rows.filter(r=>r.bottom>b.top+.5&&r.top<b.bottom-.5);return {bounds:b,well:el.getBoundingClientRect().toJSON(),shown,partial:shown.filter(r=>r.top<b.top-.5||r.bottom>b.bottom+.5)};}"""
WHOLE_LINES = r"""el=>{const b=VISIBLE_BOUNDARY(el),lines=[],walk=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);for(let n=walk.nextNode();n;n=walk.nextNode()){if(!n.textContent.trim())continue;const r=document.createRange();r.selectNodeContents(n);for(const box of r.getClientRects())if(box.bottom>b.top+.5&&box.top<b.bottom-.5)lines.push({text:n.textContent.slice(0,60),...box.toJSON()});}return {bounds:b,lines,partial:lines.filter(r=>r.top<b.top-.5||r.bottom>b.bottom+.5)};}"""
WHOLE_ROWS = WHOLE_ROWS.replace("VISIBLE_BOUNDARY", f"({VISIBLE})")
WHOLE_LINES = WHOLE_LINES.replace("VISIBLE_BOUNDARY", f"({VISIBLE})")


@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.parametrize("face", ["engines", "send", "ask"])
@pytest.mark.timeout(300)
def test_visible_seats_and_recovery(tmp_path, monkeypatch, width, face):
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    phase = os.environ.get("KIT_R6_PHASE", "after")
    OUT.mkdir(parents=True, exist_ok=True)
    faults = []
    facts = {}

    def check(item, condition, detail):
        if not condition:
            faults.append({"item": item, **detail})

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
                reduced_motion="reduce",
            )
            page.set_default_timeout(20000)
            if phase == "before":
                from .test_kit_polish_wave14_glass import _before

                monkeypatch.setenv(
                    "KIT14_BASELINE_BUILD",
                    os.environ.get(
                        "KIT_R6_BASELINE_BUILD", str(ROOT / ".tmp/kit-r6-before-build")
                    ),
                )
                _before(page)

            def shot(state):
                win.locator("img").evaluate_all(
                    "imgs=>Promise.all(imgs.filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height&&r.bottom>0&&r.top<innerHeight;}).map(e=>e.decode()))"
                )
                _settle(page)
                page.screenshot(
                    path=str(
                        OUT / f"{state}-{900 if width == 1440 else 393}-{phase}.png"
                    )
                )

            def size(win, wid):
                if width == 1440:
                    _api(
                        page,
                        "POST",
                        f"/api/desk/windows/{wid}/set_geometry",
                        {
                            "rect": {
                                "x": "-1/2 + 100",
                                "y": "-1/2 + 80",
                                "w": "900px",
                                "h": "600px",
                            }
                        },
                        token=TOKEN,
                    )
                _settle(page)

            if face == "engines":
                chain = json.loads(
                    (
                        ROOT
                        / "web/src/features/runson/__tests__/fixtures/settings-chain.recorded.json"
                    ).read_text()
                )
                for path, payload in chain["gets"].items():
                    page.route(
                        f"**{path}", lambda r, _request, p=payload: r.fulfill(json=p)
                    )
                settings = _open_page(page, base)
                settings.get_by_test_id("settings-index-engines").click()
                win = page.locator("#surface-settings")
                size(win, "surface-settings")
                jobs = settings.get_by_role("grid", name="Jobs", exact=True)
                jobs.locator(".object-list-row").first.wait_for()
                expect(win.get_by_test_id("settings-status")).to_contain_text("engines")
                page.evaluate("() => document.fonts.ready")
                _settle(page)
                shot("1-jobs-ready")
                for endpoint in chain["gets"]:
                    page.route(f"**{endpoint}", lambda r: r.abort("connectionfailed"))
                rail = win.get_by_role(
                    "navigation", name="Settings sections", exact=True
                )
                if not rail.is_visible():
                    win.get_by_role(
                        "button", name="Back from Engines", exact=True
                    ).click()
                win.get_by_test_id("settings-index-accounts").click()
                if not rail.is_visible():
                    win.get_by_role(
                        "button", name="Back from Accounts", exact=True
                    ).click()
                win.get_by_test_id("settings-index-engines").click()
                expect(
                    settings.get_by_text("Engines not read", exact=True)
                ).to_be_visible()
                _settle(page)
                page.wait_for_timeout(200)
                well = jobs.locator(".object-list-rows")
                for state in ["failed", "scrolled"]:
                    if state == "scrolled":
                        well.evaluate("e=>e.scrollTop=e.scrollHeight")
                        page.wait_for_timeout(200)
                    value = well.evaluate(WHOLE_ROWS)
                    facts[state] = value
                    check(
                        1,
                        bool(value["shown"]) and not value["partial"],
                        {"state": state, **value},
                    )
                    shot("1-jobs-" + state)
                for endpoint, payload in chain["gets"].items():
                    page.route(
                        f"**{endpoint}",
                        lambda r, _request, p=payload: r.fulfill(json=p),
                    )
                settings.get_by_test_id("settings-engines").get_by_role(
                    "button", name="Retry", exact=True
                ).click()
                expect(
                    settings.get_by_text("Engines not read", exact=True)
                ).to_be_hidden()
                _settle(page)
                value = well.evaluate(WHOLE_ROWS)
                facts["recovered"] = value
                check(
                    1,
                    bool(value["shown"]) and not value["partial"],
                    {"state": "recovered", **value},
                )
                shot("1-jobs-recovered")
            elif face == "send":
                from holdspeak.services import channel_email
                from holdspeak.services.channel_contract import FileChannel, Outcome

                monkeypatch.setattr(
                    channel_email,
                    "KEY_STORE",
                    lambda: channel_email.MemoryEmailKeyStore(),
                )
                monkeypatch.setattr(
                    FileChannel,
                    "dispatch",
                    lambda *_args, **_kwargs: Outcome("failed", "permission_denied"),
                )
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(
                    page,
                    "PUT",
                    "/api/setup/onboarding",
                    {"disposition": "completed"},
                    token=TOKEN,
                )
                _api(page, "GET", "/api/channels/destinations", token=TOKEN)
                email = _api(
                    page,
                    "POST",
                    "/api/channels/destinations",
                    {
                        "name": "Architecture review",
                        "channel": "email",
                        "provider": "resend",
                        "from_email": "owner@example.test",
                        "key_ref": "rig-email",
                        "to": ["review@example.test"],
                    },
                    token=TOKEN,
                )["destination"]
                made = _api(
                    page,
                    "POST",
                    "/api/thoughts",
                    {
                        "request_id": str(uuid.uuid4()),
                        "raw_text": "The architecture report is ready.",
                        "source": {"kind": "typed"},
                        "initial_note": {
                            "title": TITLE,
                            "body_markdown": f"# {TITLE}\n\n"
                            + (
                                "Keep the recovery point and the saved architecture review in view.\n\n"
                                * 50
                            ),
                            "tags": [],
                        },
                    },
                    token=TOKEN,
                )
                ref = "note:" + made["thought"]["working_note"]["id"]
                page.goto(f"{base}/?token={TOKEN}&open={ref}", wait_until="load")
                _normal_chair(page)
                win = page.locator(".thought-workspace-window").first
                win.get_by_test_id(
                    "thought-note-body"
                ).wait_for() if win.get_by_test_id(
                    "thought-note-body"
                ).count() else win.wait_for()
                page.wait_for_function(
                    "async ([id,token])=>{const r=await fetch('/api/desk/windows',{headers:{Authorization:'Bearer '+token}});return (await r.json()).windows?.some(w=>w.id===id)}",
                    arg=["pullout:" + ref, TOKEN],
                )
                size(win, "pullout:" + ref)
                press_verb(win.locator(".thought-note-toolbar"), "Send…")
                well = win.get_by_test_id("send-well")
                well.get_by_role("tab", name="Email", exact=True).click()
                choose_toolbar(well, "Destination", email["id"])
                preview = well.get_by_test_id("send-preview")
                preview.get_by_text("Subject", exact=True).wait_for()
                fields = preview.locator(".surface-inspector-fields").first
                for state in ["ready", "end"]:
                    if state == "end":
                        fields.evaluate("e=>e.scrollTop=e.scrollHeight")
                    _settle(page)
                    value = fields.evaluate(WHOLE_LINES)
                    payload = well.get_by_test_id("send-preview-body").evaluate(
                        "e=>{const w=e.closest('.surface-well-body');return {height:w.clientHeight,line:parseFloat(getComputedStyle(e).lineHeight)}}"
                    )
                    facts[state] = {"fields": value, "payload": payload}
                    check(
                        2,
                        bool(value["lines"])
                        and not value["partial"]
                        and payload["height"] >= payload["line"] * 4 - 1,
                        {"state": state, **facts[state]},
                    )
                    shot("2-email-" + state)
                well.get_by_role("tab", name="Folder", exact=True).click()
                choose_toolbar(well, "Destination", "holdspeak-folder")
                well.get_by_test_id("send-preview-body").wait_for()
                well.get_by_test_id("send-verb").click()
                receipt = well.get_by_test_id("send-failed")
                receipt.wait_for()
                facts["receipt"] = receipt.inner_text()
                check(
                    3,
                    receipt.inner_text() == PERMISSION,
                    {"text": receipt.inner_text()},
                )
                shot("3-send-failed")
            else:
                from holdspeak.db import get_database
                from holdspeak.services.primitive_service import PrimitiveService
                from holdspeak.principals import Principal, PrincipalKind

                notes = []
                service = PrimitiveService(get_database())
                owner = Principal(PrincipalKind.OWNER, "kit-r6")
                for i in range(50):
                    notes.append(
                        service.create_note(
                            owner,
                            note_id=f"r6-{i}",
                            title=(f"web/src/architecture/review_{i:02d}.tsx: " + TITLE)
                            if i % 2 == 0
                            else "saved_architecture_review_"
                            + "checkpoint_" * 18
                            + str(i),
                            body_markdown="Keep the saved source.",
                        )
                    )
                tools = json.loads(
                    (ROOT / "web/src/test/wire/ask.tools.wire.json").read_text()
                )
                answer = {
                    **tools["answer"],
                    "looked_at": [
                        {"ref": f"note:{n['id']}", "title": n["title"], "kind": "note"}
                        for n in notes
                    ],
                }
                page.route(
                    "**/api/ask/engine", lambda r: r.fulfill(json=tools["engine"])
                )
                page.route(
                    "**/api/inference/assignments",
                    lambda r: r.fulfill(json=tools["assignments"]),
                )
                page.route("**/api/ask", lambda r: r.fulfill(json=answer))
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(
                    page,
                    "PUT",
                    "/api/setup/onboarding",
                    {"disposition": "completed"},
                    token=TOKEN,
                )
                page.reload(wait_until="load")
                _normal_chair(page)
                page.keyboard.press("Control+KeyI")
                win = page.locator("[id=ask][data-layer=window]")
                editor = win.get_by_role(
                    "textbox", name="Ask about your work", exact=True
                )
                editor.wait_for()
                if width == 1440:
                    box = win.bounding_box()
                    grip = win.locator(".desk-window-grip").bounding_box()
                    x = grip["x"] + grip["width"] / 2
                    y = grip["y"] + grip["height"] / 2
                    page.mouse.move(x, y)
                    page.mouse.down()
                    page.mouse.move(
                        x + 900 - box["width"], y + 600 - box["height"], steps=8
                    )
                    page.mouse.up()
                editor.fill("Read the recovery points")
                editor.press("Enter")
                sources = win.get_by_test_id("ask-looked-at")
                sources.wait_for()
                if width == 393:
                    sources.get_by_role(
                        "button", name=f"Sources {len(notes)}", exact=True
                    ).click()
                sources.locator(".object-list-row").first.click()
                _settle(page)
                value = win.evaluate(
                    "e=>{const list=e.querySelector('[data-testid=ask-looked-at] .object-list-row'),bar=e.querySelector('[data-testid=ask-looked-at] .object-list-inner-toolbar'),reading=e.querySelector('[data-testid=ask-turn] .reading-document');return {row:list.getBoundingClientRect().left,bar:bar.getBoundingClientRect().left,text:reading.getBoundingClientRect().left}}"
                )
                facts["inset"] = value
                check(
                    4,
                    abs(value["row"] - value["text"]) < 1
                    and abs(value["bar"] - value["text"]) < 1,
                    value,
                )
                shot("4-ask-sources")
            browser.close()
    finally:
        (OUT.parent / f"r6-{face}-{width}-{phase}.json").write_text(
            json.dumps({"facts": facts, "failures": faults}, indent=2)
        )
        server.stop()
    assert not faults, json.dumps(faults, indent=2)
