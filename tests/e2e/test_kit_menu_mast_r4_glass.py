"""Mast navigation, menu placement and fact widths use real browser geometry."""

import json
import os
from pathlib import Path
import pytest
from . import open_rig, list_name_fit_rig
from .glass_infra import (
    _api,
    _boot,
    _ensure_build,
    _settle,
    _normal_chair,
    clear_hub_windows_http,
    choose_toolbar,
)
from .test_settings_page_glass import TOKEN, _open_page

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".tmp/evidence-shots/kit14/r4"


@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.timeout(300)
def test_shared_menu_mast_and_columns(tmp_path, monkeypatch, width):
    from playwright.sync_api import sync_playwright

    _ensure_build()
    OUT.mkdir(parents=True, exist_ok=True)
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    monkeypatch.setattr(list_name_fit_rig, "TOKEN", TOKEN)
    phase = os.environ.get("KIT_R4_PHASE", "after")
    failures = []
    facts = {}

    def check(item, ok, data):
        if not ok:
            failures.append({"item": item, **data})

    try:
        list_name_fit_rig.seed_names(tmp_path, base, monkeypatch)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
                reduced_motion="reduce",
            )
            page.set_default_timeout(15000)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")

            def shot(name):
                _settle(page)
                page.screenshot(
                    path=str(
                        OUT / f"{name}-{900 if width == 1440 else 393}-{phase}.png"
                    )
                )

            def back(win, name):
                if width != 393:
                    return
                value = win.locator(".desk-gadget-close").evaluate(
                    """el=>{const b=el.getBoundingClientRect(),walk=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let glyph=null;for(let n=walk.nextNode();n;n=walk.nextNode()){const at=n.textContent.indexOf('‹');if(at<0)continue;const r=document.createRange();r.setStart(n,at);r.setEnd(n,at+1);glyph=r.getBoundingClientRect().toJSON();}return {word:el.textContent,button:b.toJSON(),glyph};}"""
                )
                facts[name + "-back"] = value
                g, b = value["glyph"], value["button"]
                check(
                    1,
                    bool(
                        g
                        and g["width"] > 0
                        and g["left"] >= max(0, b["left"]) - 1
                        and g["right"] <= b["right"] + 1
                    ),
                    {"where": name, **value},
                )

            def menu_fit(win, menu, name):
                _settle(page)
                value = menu.evaluate(
                    """(menu,wid)=>{const win=document.getElementById(wid),box=win.getBoundingClientRect(),r=menu.getBoundingClientRect(),over=b=>Math.min(r.right,b.right)>Math.max(r.left,b.left)+1&&Math.min(r.bottom,b.bottom)>Math.max(r.top,b.top)+1;const protectedRows=[...win.querySelectorAll('.object-list-row[aria-selected=true],.object-list-head,.object-list-inner-toolbar,.desk-surface-foot')].filter(e=>{const b=e.getBoundingClientRect();return b.width>0&&b.height>0;});return {menu:r.toJSON(),window:box.toJSON(),over:protectedRows.filter(e=>over(e.getBoundingClientRect())).map(e=>({kind:e.className,text:e.textContent.slice(0,100),box:e.getBoundingClientRect().toJSON()})),clipped:[...menu.querySelectorAll(':scope > button .desk-menu-label')].filter(label=>{const range=document.createRange();range.selectNodeContents(label);const b=range.getBoundingClientRect();return b.bottom>r.top&&b.top<r.bottom&&(b.top<r.top-1||b.bottom>r.bottom+1);}).map(e=>e.textContent),scroll:menu.scrollHeight,client:menu.clientHeight};}""",
                    win.get_attribute("id"),
                )
                facts[name] = value
                r, b = value["menu"], value["window"]
                check(
                    2,
                    not value["over"]
                    and not value["clipped"]
                    and r["left"] >= b["left"] - 1
                    and r["right"] <= b["right"] + 1
                    and r["top"] >= b["top"] - 1
                    and r["bottom"] <= b["bottom"] + 1,
                    {"where": name, **value},
                )

            # Replay the recorded queued agent state; no agent or terminal runs.
            agent = json.loads(
                (
                    ROOT
                    / "web/src/desk/__tests__/fixtures/agents-ag8/coders-sessions.wire.json"
                ).read_text()
            )
            page.route(
                "**/api/coders/sessions**",
                lambda route: route.fulfill(json=agent["wire"]),
            )
            page.clock.set_fixed_time(agent["captured_at"])
            clear_hub_windows_http(base, TOKEN)
            page.goto(f"{base}/conductor?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            win = page.locator("#conductor")
            queued = win.locator(
                '[data-testid="agents-list"] [data-object-id^="queue:"]'
            ).first
            queued.wait_for()
            if width == 1440:
                _api(
                    page,
                    "POST",
                    "/api/desk/windows/conductor/set_geometry",
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
            queued.click(button="right")
            menu = page.get_by_role("menu", name="Agents actions", exact=True)
            menu.wait_for()
            menu_fit(win, menu, "agents-queued-menu")
            shot("agents-queued-menu")
            page.keyboard.press("Escape")
            queued.dblclick()
            _settle(page)
            back(win, "agents")
            shot("agents-mast")
            page.unroute("**/api/coders/sessions**")
            # Recorded real Program reads keep this a provider-free frame check.
            tape = json.loads(
                (
                    ROOT / "web/src/desk/programs/__fixtures__/program.live10.json"
                ).read_text()
            )
            program = tape["waiting"]
            pid = program["id"]
            page.route(
                "**/api/programs",
                lambda route: route.fulfill(json=tape["waiting_list"])
                if route.request.method == "GET"
                else route.continue_(),
            )
            page.route(
                f"**/api/programs/{pid}", lambda route: route.fulfill(json=program)
            )
            win = list_name_fit_rig.open_window(
                page, base, "surface-programs", width, object_ref=f"program:{pid}"
            )
            win.get_by_role("tab", name="Now", exact=True).wait_for()
            _settle(page)
            back(win, "programs")
            shot("programs-mast")
            # The produced assignment editor after removing Gemini leaves one add choice.
            chain = json.loads(
                (
                    ROOT
                    / "web/src/features/runson/__tests__/fixtures/settings-chain.recorded.json"
                ).read_text()
            )
            for endpoint, payload in chain["gets"].items():
                page.route(
                    f"**{endpoint}",
                    lambda route, _request, payload=payload: route.fulfill(
                        json=payload
                    ),
                )

            def editor(route):
                scope = route.request.post_data_json.get("scope", {})
                key = "default" if scope.get("kind") == "global" else "summaries"
                route.fulfill(json=chain["steps"][2]["editors"][key])

            page.route("**/api/inference/assignments/editor", editor)
            clear_hub_windows_http(base, TOKEN)
            _open_page(page, base, scope="engines")
            win = page.locator("#surface-settings")
            if width == 1440:
                _api(
                    page,
                    "POST",
                    "/api/desk/windows/surface-settings/set_geometry",
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
            section = win.locator("[data-settings-section=engines]")
            section.get_by_role("grid", name="Jobs", exact=True).wait_for()
            choose_toolbar(section, "Everything else engines", "order")
            order = section.get_by_role(
                "region", name="Everything else: engine order", exact=True
            )
            button = order.get_by_role("button", name="Add engine", exact=True)
            button.click()
            menu = page.get_by_role("menu", name="Engine order actions", exact=True)
            menu.wait_for()
            menu_fit(win, menu, "engines-add-menu")
            field = button.evaluate(
                "el=>el.closest('.gadget-row').getBoundingClientRect().toJSON()"
            )
            r = menu.bounding_box()
            check(
                2,
                r["y"] + r["height"] <= field["top"] + 1
                or r["y"] >= field["bottom"] - 1,
                {"where": "engines-order-row", "menu": r, "field": field},
            )
            shot("engines-add-menu")
            page.keyboard.press("Escape")
            page.unroute("**/api/inference/assignments/editor")
            for endpoint in chain["gets"]:
                page.unroute(f"**{endpoint}")
            win = list_name_fit_rig.open_window(page, base, "surface-meetings", width)
            win.get_by_test_id("meeting-row-name-fit-0").focus()
            page.keyboard.press("Enter")
            win.get_by_test_id("meeting-toolbar").get_by_role(
                "button", name="Actions ▾", exact=True
            ).click()
            menu = page.get_by_role("menu", name="Meeting actions", exact=True)
            menu.wait_for()
            menu_fit(win, menu, "meeting-actions")
            shot("meeting-actions")
            page.keyboard.press("Escape")
            win = list_name_fit_rig.open_window(
                page,
                base,
                "surface-project-memory",
                width,
                object_ref="project:name-fit-room",
            )
            win.get_by_test_id("room-body").wait_for()
            from .test_native_project_source_return_glass import _files

            files = _files(win)
            row = files.locator('[data-object-id="note:name-fit-0"]')
            row.wait_for()
            row.click()
            win.get_by_role("button", name="Project view", exact=True).click()
            menu = page.get_by_role("menu").last
            menu_fit(win, menu, "room-toolbar")
            shot("room-toolbar")
            page.keyboard.press("Escape")
            # A short real window forces a long menu to flip/scroll in its owner.
            if width == 1440:
                _api(
                    page,
                    "POST",
                    "/api/desk/windows/surface-project-memory/set_geometry",
                    {
                        "rect": {
                            "x": "-1/2 + 100",
                            "y": "-1/2 + 80",
                            "w": "900px",
                            "h": "360px",
                        }
                    },
                    token=TOKEN,
                )
                _settle(page)
                win.get_by_role("button", name="Project view", exact=True).click()
                menu = page.get_by_role("menu").last
                menu_fit(win, menu, "room-short-window")
                check(
                    2,
                    menu.evaluate("e=>e.scrollHeight>e.clientHeight"),
                    {"where": "short-menu-scrolls"},
                )
                menu.get_by_role("menuitem").last.focus()
                menu.press("End")
                _settle(page)
                last = menu.get_by_role("menuitem").last
                check(
                    2,
                    last.is_visible()
                    and last.evaluate(
                        "e=>{const b=e.getBoundingClientRect(),m=e.closest('[role=menu]').getBoundingClientRect();return b.top>=m.top-1&&b.bottom<=m.bottom+1;}"
                    ),
                    {"where": "last-menu-entry"},
                )
                page.keyboard.press("Escape")
            win = list_name_fit_rig.open_window(
                page,
                base,
                "chair%3Aneeds",
                width,
                payload={"kind": "chair", "ref": "needs"},
            )
            grid = win.get_by_role("grid", name="Needs you", exact=True)
            grid.locator("[data-object-id]").first.wait_for()
            _settle(page)
            # A fact column takes the width of its widest value in ANY row: a width
            # that follows the rows in view moves the column edges during a scroll.
            columns = grid.evaluate(
                """grid=>[...grid.querySelectorAll('.object-list-head [data-col]')].filter(e=>e.dataset.col!=='name'&&e.getBoundingClientRect().width>0).map(head=>{const key=head.dataset.col,cs=getComputedStyle(head),label=head.querySelector('span'),padding=(parseFloat(cs.paddingLeft)||0)+(parseFloat(cs.paddingRight)||0),content=Math.max(0,...[...grid.querySelectorAll('.object-list-row [data-col="'+key+'"]')].map(cell=>{const s=getComputedStyle(cell);return Math.max(0,...[...cell.children].map(e=>e.getBoundingClientRect().width))+(parseFloat(s.paddingLeft)||0)+(parseFloat(s.paddingRight)||0);}));return {key,width:head.getBoundingClientRect().width,needed:Math.max(content,(label?.getBoundingClientRect().width||0)+padding+4)};});"""
            )
            name_seat = grid.evaluate(
                """grid=>{const head=grid.querySelector('.object-list-head'),cells=[...head.querySelectorAll('[data-col]')].filter(e=>e.getBoundingClientRect().width>0),name=cells.find(e=>e.dataset.col==='name');return {name:name.getBoundingClientRect().width,remaining:head.getBoundingClientRect().width-cells.filter(e=>e!==name).reduce((sum,e)=>sum+e.getBoundingClientRect().width,0)};}"""
            )
            facts["needs-name-seat"] = name_seat
            check(
                3,
                abs(name_seat["name"] - name_seat["remaining"]) <= 2,
                {"where": "needs-name-seat", **name_seat},
            )
            facts["needs-columns"] = columns
            for col in columns:
                check(
                    3,
                    col["width"] <= col["needed"] + 2,
                    {"where": "needs-columns", **col},
                )
            shot("needs-columns")
            browser.close()
    finally:
        (OUT.parent / f"r4-measures-{width}-{phase}.json").write_text(
            json.dumps({"facts": facts, "failures": failures}, indent=2)
        )
        server.stop()
    assert not failures, json.dumps(failures, indent=2)
