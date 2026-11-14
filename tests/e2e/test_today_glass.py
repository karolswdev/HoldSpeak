"""Today at both sizes: shared list keys, View focus, fitting and after shots."""
from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from . import open_rig
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle

TOKEN = "today-wave13"
OUT = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/today14"
PHASE = os.environ.get("TODAY14_PHASE", "after")
ITEMS = {"day": "2-8", "meeting-selected": "1", "desk-pages": "3", "brief-send": "4", "week": "5", "prepared": "6", "empty-prepared": "6", "prepared-before-result": "6", "prepared-before-actions": "6", "activity-selected": "7", "brief-selected": "7", "dense-day": "real", "dense-selected": "real", "dense-week": "real", "dense-identifier": "real", "prepared-work": "clock"}
ROOT = Path(__file__).resolve().parents[2]
WID = "pullout:intelligence:desk"
pytestmark = [pytest.mark.e2e]


def _fit(win: Any, width: int) -> None:
    if width == 393 and win.locator(".object-list").is_visible():
        headings = win.locator(".object-list-th").evaluate_all("els => els.filter(e=>e.getClientRects().length && getComputedStyle(e).display!=='none').map(e=>e.textContent)")
        # A column that is empty in every row in view is not declared at
        # this width (#2319): State stands only when a row shows one.
        states = win.locator('.object-list-row [data-col="state"]').evaluate_all("els => els.filter(e=>e.getClientRects().length && e.textContent.trim()).length")
        assert headings == (["What", "State"] if states else ["What"]), headings
        for at in win.locator(".object-list-row [data-folded-col=when]").all():
            assert at.is_visible(), "At must move to the second line"
    for detail in win.locator(".object-list-detail").all():
        assert not re.search(r"\b(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\b", detail.inner_text()), detail.inner_text()
    bars = win.locator(".kit-statusbar")
    assert bars.count() == 1, "Every state has one strip"
    assert bars.first.is_visible(), "The strip stays visible in empty states"
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
    if width == 1440 and win.locator('.surface-list-pane[data-layout="deck"]').count():
        well = win.locator(".object-list").first.bounding_box()
        frame = win.bounding_box()
        assert well and frame and .64 <= well["width"]/frame["width"] <= .69, (well,frame)
        for title in win.locator(".object-list-selection-title").all():
            if title.inner_text() in ["Adopt OpenTelemetry for all services", "Ledger cutover sync", "Who owns read-only vs archive for the old ledger?", "Email Dana about the cutover window"]:
                assert title.evaluate("el => el.scrollWidth <= el.clientWidth"), title.inner_text()
    for at in win.locator('.object-list-cell[data-col="when"] .object-list-value').all():
        if at.is_visible():
            assert at.evaluate("el => el.scrollWidth <= el.clientWidth"), at.inner_text()
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
            # Optional immutable bundle replay for BEFORE captures. Hub data
            # still comes from this isolated rig's actual producers.
            if held_html := os.environ.get("TODAY14_BASELINE_HTML"):
                held = Path(held_html)
                page.route(re.compile(rf"^{re.escape(base)}/(?:\?token={TOKEN})?$"), lambda route: route.fulfill(path=held, content_type="text/html"))
                def held_asset(route: Any) -> None:
                    asset = held.parent / "assets" / route.request.url.rsplit("/", 1)[-1]
                    if asset.is_file():
                        route.fulfill(path=asset)
                    else:
                        route.continue_()
                page.route("**/_built/assets/*", held_asset)
            page.add_init_script("localStorage.setItem('hs:walk-voice','off')")
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            page.locator(".desk-dock-launch[aria-label^='Today']").first.click()
            win = page.locator(f'[id="{WID}"]')
            expect(win.get_by_test_id("today-body")).not_to_have_attribute("aria-busy","true",timeout=30_000)
            if width == 1440:
                # Today is the launcher pullout; size its mounted frame with
                # the same title/grip path as the frame and kit glass.
                box = win.bounding_box()
                title = win.locator(":scope > .desk-pullout-head .desk-pullout-title").bounding_box()
                assert box and title
                x, y = title["x"] + 10, title["y"] + title["height"] / 2
                page.mouse.move(x, y)
                page.mouse.down()
                page.mouse.move(x + 110 - box["x"], y + 100 - box["y"], steps=8)
                page.mouse.up()
                _settle(page)
                box = win.bounding_box()
                grip = win.locator(".desk-window-grip").bounding_box()
                assert box and grip
                x, y = grip["x"] + grip["width"] / 2, grip["y"] + grip["height"] / 2
                page.mouse.move(x, y)
                page.mouse.down()
                page.mouse.move(x + 900 - box["width"], y + 600 - box["height"], steps=8)
                page.mouse.up()
            page.wait_for_timeout(300)

            def shot(state: str) -> None:
                _settle(page)
                _fit(win, width)
                if width == 1440:
                    box = win.bounding_box()
                    assert box and abs(box["width"] - 900) < 1 and abs(box["height"] - 600) < 1, box
                if PHASE == "after" or state in ITEMS:
                    page.screenshot(path=str(OUT / f"{ITEMS.get(state, 'pane')}-{state}-{PHASE}-{900 if width == 1440 else 393}.png"))
                for title in win.locator(".surface-inspector-heading > strong:visible").all():
                    assert title.evaluate("el => el.scrollWidth <= el.clientWidth + 1"), title.inner_text()

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

            (ROOT / ".tmp/r3-today-seed-read.json").write_text(json.dumps(_api(page,"GET","/api/today",token=TOKEN),indent=2))
            assert not win.locator(".object-list-row").filter(has_text="1:1 commitment").count()
            waiting = win.get_by_role("rowgroup", name="Waits on you", exact=True)
            total = _api(page, "GET", "/api/today", token=TOKEN)["needs_you"]["count"]
            shown = waiting.locator(".object-list-row").count()
            remaining = total - shown
            assert remaining > 0
            expect(waiting.locator(".object-list-group-label")).to_have_text(f"Waits on you{total}")
            more = waiting.get_by_role("button", name=f"Open Needs you ({remaining} more)", exact=True)
            expect(more).to_be_visible()
            assert waiting.evaluate("el => el.lastElementChild.getAttribute('role') === 'toolbar'")
            shot("day")
            bounds = more.evaluate("""button => {
                const range = document.createRange(); range.selectNodeContents(button);
                const text = range.getBoundingClientRect(), plate = button.getBoundingClientRect();
                const well = button.closest('.object-list-rows').getBoundingClientRect();
                return {text: text.toJSON(), plate: plate.toJSON(), well: well.toJSON()};
            }""")
            for edge in ("left", "top"):
                assert bounds["text"][edge] >= max(bounds["plate"][edge], bounds["well"][edge]) - 1, bounds
            for edge in ("right", "bottom"):
                assert bounds["text"][edge] <= min(bounds["plate"][edge], bounds["well"][edge]) + 1, bounds
            if width == 393:
                assert bounds["plate"]["height"] >= 44, bounds
            more.click()
            needs = page.locator('[id="chair:needs"]')
            expect(needs).to_be_visible()
            needs.get_by_role("button", name=re.compile(r"^(Close Needs you|Back from Needs you)$")).click()
            expect(needs).not_to_be_visible()
            if width == 393:
                # A Chair app iconifies the previous phone window in its Dock.
                page.locator(".desk-dock-launch[aria-label^='Today']").first.click()
                expect(win).to_be_visible()
            meeting = win.locator('.object-list-row[data-kind="meeting"]').filter(has_text="1:1 Priya").first
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
            # A ready automation has no result yet: collection verbs stay live.
            before = tape["beforePrepared"]["gets"]["/api/today"]
            page.unroute("**/api/today")
            page.route("**/api/today", lambda route: route.fulfill(json=before))
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(win.get_by_test_id("today-body")).not_to_have_attribute("aria-busy","true",timeout=30_000)
            view("Prepared")
            shot("prepared-before-result")
            win.get_by_test_id("today-toolbar").get_by_role("button",name="Actions ▾",exact=True).click()
            expect(page.get_by_role("menu").get_by_role("menuitem",name="Prepare now",exact=True)).to_be_enabled()
            expect(page.get_by_role("menu").get_by_role("menuitem",name="Open the automation",exact=True)).to_be_enabled()
            shot("prepared-before-actions")
            page.keyboard.press("Escape")
            page.unroute("**/api/today")
            page.route("**/api/today",lambda route: route.fulfill(json=tape["gets"]["/api/today"]))
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(win.get_by_test_id("today-body")).not_to_have_attribute("aria-busy","true",timeout=30_000)
            view("Prepared")
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
            win.get_by_test_id("today-read-failed").get_by_role("button",name="Try again",exact=True).click()
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
            expect(win.get_by_test_id("today-inspector")).to_contain_text("Meeting 09-19 · 10:00")
            shot("desk-pages")
            # Real producers, owner-shaped volume: 50 path-led names, not
            # shortened display strings or a separate wire payload.
            from datetime import datetime, timedelta, timezone
            from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
            now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
            seed = open_rig._http(base, "GET", "/api/people/relationships")
            person = seed["relationships"][0]["id"]
            lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HoldSpeak//Today14//EN"]
            for i in range(50):
                name = (f"web/src/desk/pullouts/views/today/reconcile_owner_commitments_{i:02d}.tsx::KeepTheSelectedRevisionBoundToItsSource "
                        "keeps the saved answer when the next read completes and opens the same source")
                if i % 2:
                    name = (f"`holdspeak.services.reconcile_commitments_{i:02d}.KeepTheSelectedRevisionBoundToItsSourceWhenASecondReadCompletes"
                            "WithoutLosingTheSavedAnswerAndOpenTheOriginalSourceForTheOwner`")
                request = open_rig._http(base, "POST", f"/api/people/relationships/{person}/requests", {"body": name})["request"]
                open_rig._http(base, "POST", f"/api/people/requests/{request['id']}/accept", {})
                start = now + timedelta(minutes=i + 1)
                lines += ["BEGIN:VEVENT", f"UID:today14-{i}", f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",
                          f"DTEND:{(start + timedelta(minutes=30)).strftime('%Y%m%dT%H%M%SZ')}",
                          f"SUMMARY:{name}", "END:VEVENT"]
            lines += ["END:VCALENDAR", ""]
            ics = tmp_path / "home" / "today14.ics"
            ics.write_text("\r\n".join(lines), encoding="utf-8")
            open_rig._http(base, "PUT", "/api/settings", {"calendar": {"sources": [
                {"id": "today14", "label": "Work", "url": str(ics), "enabled": True}
            ]}})
            assert CalendarIngestConductor().refresh() is True
            page.unroute("**/api/today")
            _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
            dense = _api(page, "GET", "/api/today", token=TOKEN)
            assert len(dense["day"]["upcoming"]) >= 50
            assert dense["needs_you"]["count"] >= 50
            page.clock.set_fixed_time(now.isoformat())
            page.reload(wait_until="load")
            _normal_chair(page)
            expect(win.get_by_test_id("today-body")).not_to_have_attribute("aria-busy", "true", timeout=30_000)
            expect(win.locator('.object-list-row[data-kind="meeting"]')).to_have_count(len(dense["day"]["upcoming"]))
            shot("dense-day")
            win.locator(f'.object-list-row[data-object-id="event:{dense["day"]["upcoming"][0]["id"]}"]').click()
            expect(win.locator(".surface-inspector-name")).to_have_attribute("title", dense["day"]["upcoming"][0]["title"])
            shot("dense-selected")
            if width == 393:
                win.get_by_test_id("today-back").click()
            win.locator(f'.object-list-row[data-object-id="event:{dense["day"]["upcoming"][1]["id"]}"]').click()
            expect(win.locator(".surface-inspector-name")).to_have_attribute("title", dense["day"]["upcoming"][1]["title"])
            shot("dense-identifier")
            if width == 393:
                win.get_by_test_id("today-back").click()
            press("This week")
            shot("dense-week")
            browser.close()
    finally:
        server.stop()
