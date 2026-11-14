"""Empty consumers of Ask's shared list-seat change, on a real isolated hub."""
from pathlib import Path
import os
import urllib.parse
import pytest
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows
from tests._evidence import evidence_dir

pytestmark = [pytest.mark.e2e]
TOKEN = "ask-empty-consumers"

@pytest.mark.parametrize("width", [1440, 393])
def test_empty_list_consumers_keep_their_working_seat(tmp_path: Path, monkeypatch, width):
    from playwright.sync_api import sync_playwright, expect
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = evidence_dir(os.environ.get("ASK_GLASS_SHOTS", "ask14r3"))
    stage = os.environ.get("ASK_GLASS_STAGE", "after")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page,"PUT","/api/setup/onboarding",{"disposition":"completed"},token=TOKEN)
            for name, wid, word in [("people","surface-people","People you meet appear here."),("projects","surface-projects","No projects yet"),("recordings","surface-recordings","No recordings yet"),("needs-you","chair:needs","Nothing needs you.")]:
                clear_hub_windows(page,TOKEN)
                payload={"geometry":{"x":"-1/2 + 24","y":"-1/2 + 24","w":900,"h":600}}
                _api(page,"POST",f"/api/desk/windows/{urllib.parse.quote(wid,safe='')}/open",payload,token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                win=page.locator(f'[id="{wid}"]')
                win.wait_for(timeout=20000)
                expect(win.get_by_text(word,exact=True)).to_be_visible(timeout=20000)
                _settle(page)
                assert win.locator('[role=row][data-object-id]').count()==0, name
                assert win.locator('.surface-mast-title').inner_text().strip(),name
                page.screenshot(path=str(shots/f"shared-{name}-empty-{stage}-{900 if width==1440 else 393}.png"))
                assert win.evaluate("el=>el.scrollWidth<=el.clientWidth+1"),name
            browser.close()
    finally:
        server.stop()
