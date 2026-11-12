"""Today at both sizes: shared list keys, View focus, fitting and after shots."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from . import open_rig
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle

TOKEN = "today-wave13"
OUT = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/today13"
ROOT = Path(__file__).resolve().parents[2]
WID = "pullout:intelligence:desk"
pytestmark = [pytest.mark.e2e]


def _fit(win: Any, width: int) -> None:
    bounds = win.evaluate("""win => {
      const w=win.getBoundingClientRect();
      const selectors=['.object-list-toolbar','.object-list-rows','.surface-pane-inspector-head','.surface-pane-actions','.kit-statusbar'];
      return [...win.querySelectorAll(selectors.join(','))].filter(el=>el.getClientRects().length).map(el=>{
        const r=el.getBoundingClientRect();return {part:el.className,x:r.left,y:r.top,right:r.right,bottom:r.bottom,w:r.width,h:r.height,seat:{x:w.left,y:w.top,right:w.right,bottom:w.bottom}};
      });
    }""")
    assert bounds
    for row in bounds:
        assert row["x"] >= row["seat"]["x"] - 1 and row["right"] <= row["seat"]["right"] + 1, row
        assert row["y"] >= row["seat"]["y"] - 1 and row["bottom"] <= row["seat"]["bottom"] + 1, row
    caption = win.get_by_role("button", name="Today view", exact=True)
    if caption.count() and caption.is_visible():
        text = caption.evaluate("""button => {
          const range=document.createRange();range.selectNodeContents(button);
          const text=range.getBoundingClientRect(), box=button.getBoundingClientRect();
          return {left:text.left,right:text.right,boxLeft:box.left,boxRight:box.right};
        }""")
        frame = win.bounding_box()
        assert frame
        assert text["left"] >= max(text["boxLeft"], frame["x"]) - 1, text
        assert text["right"] <= min(text["boxRight"], frame["x"] + frame["width"]) + 1, text
    for pill in win.locator(".object-list-dot-word > span:last-child").all():
        if pill.is_visible():
            assert pill.evaluate("el => el.scrollWidth <= el.clientWidth"), pill.inner_text()
    if width == 393 and win.locator('.surface-list-pane[data-layout="deck"]').count():
        pane = win.locator(".surface-list-pane").first
        details = pane.get_attribute("data-detail-open") is not None
        list_well = pane.locator(".object-list").first
        inspector = win.get_by_test_id("today-inspector")
        assert list_well.is_visible() != inspector.is_visible(), "A phone shows one well at a time"
        assert inspector.is_visible() == details
        visible = inspector if details else list_well
        rect, frame = visible.bounding_box(), win.bounding_box()
        assert rect and frame and rect["width"] >= frame["width"] - 4, (rect, frame)



@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.timeout(300)
def test_today_views_selection_keys_and_fit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        open_rig._seed(tmp_path / "home", base)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(viewport={"width": width,"height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page = context.new_page()
            page.add_init_script("localStorage.setItem('hs:walk-voice','off')")
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            page.locator(".desk-dock-launch[aria-label^='Today']").first.click()
            win = page.locator(f'[id="{WID}"]')
            expect(win.get_by_test_id("today-body")).not_to_have_attribute("aria-busy","true",timeout=30_000)
            if width == 1440:
                _api(page,"POST",f"/api/desk/windows/{WID}/set_geometry",{"rect":{"x":"-1/2 + 110","y":"-1/2 + 100","w":"900px","h":"600px"}},token=TOKEN)
            page.wait_for_timeout(300)

            def shot(state: str) -> None:
                _settle(page)
                _fit(win, width)
                page.screenshot(path=str(OUT / f"{state}-{900 if width == 1440 else 393}.png"))
                diagnostic = win.get_by_role("button", name="Today view", exact=True)
                if diagnostic.count() and diagnostic.is_visible():
                    (OUT / f"{state}-{width}-view.json").write_text(json.dumps(diagnostic.evaluate("""button => {
                      const range=document.createRange();range.selectNodeContents(button);
                      const chain=[]; for(let el=button;el;el=el.parentElement) {const r=el.getBoundingClientRect();const c=getComputedStyle(el);chain.push({name:el.className,left:r.left,right:r.right,scroll:el.scrollLeft,scrollWidth:el.scrollWidth,width:el.clientWidth,overflow:c.overflowX,visibility:c.visibility});}
                      return {text:range.getBoundingClientRect().toJSON(),chain};
                    }"""), indent=2))

            def view(name: str) -> None:
                win.get_by_role("button",name="Today view",exact=True).click()
                page.get_by_role("menu", name="Today view").get_by_text(name, exact=True).click()

            def press(label: str) -> None:
                toolbar = win.get_by_test_id("today-toolbar")
                control = toolbar.get_by_role("button",name=label,exact=True)
                if control.count() and control.is_visible():
                    control.click()
                else:
                    toolbar.get_by_role("button",name="Actions ▾",exact=True).click()
                    page.get_by_role("menu").get_by_text(label,exact=True).click()

            shot("day")
            meeting = win.locator(".object-list-row").filter(has_text="1:1 Priya").first
            meeting.click()
            shot("meeting-selected")
            if width == 393:
                win.get_by_test_id("today-back").click()
                expect(meeting).to_be_focused()
            press("This week")
            shot("week")
            press("Today only")
            assert win.locator(".today-plate,.surface-rail").count() == 0
            assert win.locator(".surface-mast").count() == 1
            rows = win.locator(".object-list-row")
            assert rows.count()
            assert rows.locator("button").count() == 0
            rows.first.click()
            expect(win.get_by_test_id("today-inspector")).to_be_visible()
            shot("day-selected")
            if width == 393:
                win.get_by_test_id("today-back").click()
            # Real keyboard selection uses the kit's one list authority.
            rows.first.focus()
            page.keyboard.press("ArrowDown")
            expect(rows.nth(1)).to_have_attribute("aria-selected","true")
            if width == 393 and win.get_by_test_id("today-back").is_visible():
                win.get_by_test_id("today-back").click()
            from .test_desk_sweep import _start_app_walk, _finish_app_walk
            _start_app_walk(page)
            expect(page.get_by_test_id("guide-note")).to_be_visible()
            _finish_app_walk(page)
            expect(rows.nth(1)).to_have_attribute("aria-selected", "true")
            shot("guide-restored")
            view("Brief")
            shot("brief")
            press("Send…")
            expect(win.get_by_test_id("send-well")).to_be_visible(timeout=30_000)
            expect(win.get_by_test_id("send-well")).not_to_have_attribute("aria-busy", "true", timeout=30_000)
            expect(win.get_by_test_id("send-back")).to_be_visible()
            shot("brief-send")
            win.get_by_test_id("send-back").click()
            if rows.count():
                rows.first.click()
                shot("brief-selected")
                if width == 393:
                    win.get_by_test_id("today-back").click()
            for name in ["Prepared","Activity"]:
                view(name)
                shot(name.lower())
                if rows.count():
                    rows.first.click()
                    shot(f"{name.lower()}-selected")
                    if width == 393:
                        win.get_by_test_id("today-back").click()
            # A producer-recorded Prepared answer exercises its suggested point.
            tape = json.loads((ROOT / "web/src/desk/__tests__/fixtures/daily-week/today-prepared.json").read_text())
            page.route("**/api/today",lambda route: route.fulfill(json=tape["gets"]["/api/today"]))
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(win.get_by_test_id("today-body")).not_to_have_attribute("aria-busy","true",timeout=30_000)
            view("Prepared")
            shot("prepared-work")
            rows.first.click()
            shot("prepared-work-selected")
            if width == 393:
                win.get_by_test_id("today-back").click()
            suggested = rows.filter(has_text="To add").first
            suggested.click()
            shot("prepared-suggestion")
            page.route("**/api/people/relationships/*",lambda route: route.abort("failed"))
            press("Add to the agenda")
            expect(win.get_by_test_id("today-action-failed")).to_be_visible()
            shot("agenda-failed")
            page.unroute("**/api/people/relationships/*")
            if width == 393:
                win.get_by_test_id("today-back").click()
            # Same request, new producer-recorded empty answer.
            empty = json.loads((ROOT / "web/src/desk/__tests__/fixtures/daily-week/today-empty.json").read_text())
            page.unroute("**/api/today")
            page.route("**/api/today",lambda route: route.fulfill(json=empty["gets"]["/api/today"]))
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(win.get_by_test_id("today-body")).not_to_have_attribute("aria-busy","true",timeout=30_000)
            shot("empty-day")
            view("Prepared")
            shot("empty-prepared")
            page.unroute("**/api/today")
            page.route("**/api/today",lambda route: route.abort("failed"))
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(win.get_by_test_id("today-read-failed")).to_be_visible(timeout=30_000)
            shot("read-failed")
            page.unroute("**/api/today")
            win.get_by_test_id("today-read-failed").get_by_role("button",name="Retry",exact=True).click()
            expect(win.get_by_test_id("today-read-failed")).to_have_count(0)
            shot("read-recovered")
            # A calendar arm and summary routes are stored production answers.
            daily = json.loads((ROOT / "web/src/desk/__tests__/fixtures/daily-week/today.json").read_text())
            page.clock.install(time=daily["recordedAt"])
            page.route("**/api/today", lambda route: route.fulfill(json=daily["afterArm"]["gets"]["/api/today"]))
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(win.get_by_test_id("today-body")).not_to_have_attribute("aria-busy", "true", timeout=30_000)
            rows.filter(has_text="1:1 with Mira").first.click()
            shot("recording-armed")
            summary = json.loads((ROOT / "web/src/desk/__tests__/fixtures/meetings-hub/hs170.json").read_text())
            finishing = deepcopy(daily["gets"]["/api/today"])
            finishing["day"]["meetings"] = summary["/api/meetings?limit=100"]["meetings"]
            page.clock.set_fixed_time(summary["_now"])
            page.unroute("**/api/today")
            page.route("**/api/today", lambda route: route.fulfill(json=finishing))
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(win.get_by_test_id("today-body")).not_to_have_attribute("aria-busy", "true", timeout=30_000)
            shot("to-finish")
            rows.filter(has_text="Census standup").first.click()
            shot("summary-selected")
            path = "**/api/meetings/m-off-words/intelligence/run"
            page.route(path, lambda route: route.abort("failed"))
            press("Make the summary")
            expect(win.get_by_test_id("today-summary-failed")).to_be_visible()
            shot("summary-failed")
            page.unroute(path)
            page.route(path, lambda route: route.fulfill(json=summary["POST /api/meetings/m-off-words/intelligence/run"]))
            press("Make the summary")
            expect(win.get_by_test_id("today-status")).to_contain_text("Queued at")
            shot("summary-queued")
            unavailable = json.loads((ROOT / "web/src/desk/__tests__/fixtures/meetings-hub/list-app.json").read_text())
            finishing["day"]["meetings"] = unavailable["/api/meetings?limit=100"]["meetings"]
            page.clock.set_fixed_time(finishing["day"]["meetings"][0]["started_at"])
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(win.get_by_test_id("today-body")).not_to_have_attribute("aria-busy", "true", timeout=30_000)
            rows.filter(has_text="Vendor call, Woodward").first.click()
            shot("summary-unavailable")
            pages = json.loads((ROOT / "web/src/test/wire/memory.desk-pages.wire.json").read_text())
            page.route("**/api/memory/pages?scope=desk", lambda route: route.fulfill(json=pages["pages"]))
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(win.get_by_test_id("today-body")).not_to_have_attribute("aria-busy", "true", timeout=30_000)
            view("Brief")
            rows.filter(has_text="What I owe").first.click()
            expect(win.get_by_role("button", name="Open the source: Meeting 09-19 · 10:00", exact=True)).to_be_visible()
            shot("desk-pages")
            browser.close()
    finally:
        server.stop()
