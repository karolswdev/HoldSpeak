"""Long real-produced roster and automation rows at both owner window sizes."""
from __future__ import annotations

import os
from pathlib import Path
import pytest
from . import open_rig
from .glass_infra import _api, _boot, _ensure_build, _settle, clear_hub_windows_http
from .test_people_os_grammar_glass import _open, TOKEN

LONG_NAME = "web/src/pages/cores/PeopleCore.tsx: keep the selected person's unsaved words and linked project in view when a late read finishes during the weekly architecture review with the platform team"
IDENTIFIER = "relationship_" + "platformarchitecturedecision" * 7

@pytest.mark.parametrize("width", [1440, 393])
def test_long_lists_keep_names_and_selection_in_their_wells(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect
    from holdspeak.db import get_database

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    shots=Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/lists14"
    shots.mkdir(parents=True, exist_ok=True)
    try:
        open_rig._seed(tmp_path / "home", base)
        original_people=len(open_rig._http(base,"GET","/api/people/relationships")["relationships"])
        people=[]
        for i in range(50):
            name = LONG_NAME if i == 0 else IDENTIFIER if i == 1 else f"Platform reviewer {i:02d} — {LONG_NAME}"
            people.append(open_rig._http(base, "POST", "/api/people/relationships", {"display_name":name,"relationship_kind":"peer"})["relationship"])
            get_database().workbenches.upsert(workbench_id=f"long-automation-{i}", name=name, instruction="Prepare the architecture review.")
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            clear_hub_windows_http(base,TOKEN)
            page=browser.new_page(viewport={"width":width,"height":900 if width==1440 else 852},reduced_motion="reduce")
            _open(page,base)
            phase=os.environ.get("LISTS14_PHASE","after")
            def shot(item, state):
                _settle(page)
                body=win.locator(".desk-surface-body")
                assert body.evaluate("el=>el.scrollWidth<=el.clientWidth+1 && el.scrollHeight<=el.clientHeight+1")
                assert win.locator('[data-object-id][aria-selected="true"]').count() <= 1
                for name in win.locator(".object-list-name").all():
                    assert name.inner_text().strip() != "…"
                page.screenshot(path=str(shots / f"{item}-{state}-{900 if width==1440 else 393}-{phase}.png"))
            win=page.locator("#surface-people")
            rows=win.get_by_test_id("people-roster").locator('[data-object-id]')
            expect(rows).to_have_count(original_people + len(people))
            shot("people-real-data","list")
            for i,state in [(0,"path-name"),(1,"identifier")]:
                row=win.locator(f'[data-object-id="{people[i]["id"]}"]')
                row.click()
                expect(row).to_have_attribute("aria-selected","true")
                expect(win.get_by_test_id("people-summary-name").locator("[title]")).to_have_attribute("title",people[i]["display_name"])
                shot("people-real-data",state)
            _api(page,"POST","/api/desk/windows/surface-people/close",{},token=TOKEN)
            page.get_by_role("button",name="Go",exact=True).first.click()
            page.locator("nav[aria-label='Go menu']").get_by_role("menuitem",name="Automations",exact=True).evaluate("el=>el.click()")
            win=page.locator("#surface-workbenches")
            expect(win.locator('[data-object-id]')).to_have_count(50)
            if width==1440:
                _api(page,"POST","/api/desk/windows/surface-workbenches/set_geometry",{"rect":{"x":"-1/2 + 100","y":"-1/2 + 80","w":"900px","h":"600px"}},token=TOKEN)
            shot("automations-real-data","list")
            for i,state in [(0,"path-name"),(1,"identifier")]:
                row=win.locator(f'[data-object-id="long-automation-{i}"]')
                row.click()
                expect(row).to_have_attribute("aria-selected","true")
                expect(win.get_by_test_id("automation-summary")).to_have_attribute("data-facts-name",people[i]["display_name"])
                shot("automations-real-data",state)
            browser.close()
    finally:
        server.stop()
