"""Round-two properties of the shared title and instrument strip."""
from pathlib import Path
import pytest
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http

OUT = Path(__file__).resolve().parents[2] / '.tmp/evidence-shots/material12/r2'
TOKEN = 'material-r2'

@pytest.mark.parametrize('width', [1440, 393])
@pytest.mark.timeout(240)
def test_one_title_and_one_instrument_line(tmp_path, monkeypatch, width):
    from playwright.sync_api import sync_playwright, expect
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={'width':width, 'height':900 if width == 1440 else 852}, reduced_motion='reduce')
            page.goto(f'{base}/?token={TOKEN}', wait_until='load')
            _api(page, 'PUT', '/api/setup/onboarding', {'disposition':'completed'}, token=TOKEN)
            for app, seat in [('speak','surface-dictation'), ('live','surface-live'), ('ask','ask:desk'), ('today','intelligence:desk')]:
                clear_hub_windows_http(base, TOKEN)
                if app == 'ask':
                    page.keyboard.press('Control+i')
                elif app == 'today':
                    page.locator(".desk-dock-launch[aria-label^='Today']").first.click()
                else:
                    _api(page, 'POST', f'/api/desk/windows/{seat}/open', {}, token=TOKEN)
                if width == 1440 and app not in {'ask', 'today'}:
                    _api(page, 'POST', f'/api/desk/windows/{seat}/set_geometry', {'rect':{'x':'-1/2 + 110','y':'-1/2 + 100','w':'900px','h':'600px'}}, token=TOKEN)
                if app not in {'ask', 'today'}:
                    page.reload(wait_until='load')
                _normal_chair(page)
                win = page.locator('#ask') if app == 'ask' else page.locator('[id="pullout:intelligence:desk"]') if app == 'today' else page.locator(f'[id="{seat}"]')
                expect(win).to_be_visible()
                _settle(page)
                if width == 1440 and app in {'ask', 'today'}:
                    box = win.bounding_box()
                    grip = win.locator('.desk-window-grip').bounding_box()
                    assert box and grip
                    page.mouse.move(grip['x'] + grip['width']/2, grip['y'] + grip['height']/2)
                    page.mouse.down()
                    page.mouse.move(grip['x'] + grip['width']/2 + 900 - box['width'], grip['y'] + grip['height']/2 + 600 - box['height'], steps=8)
                    page.mouse.up()
                    _settle(page)
                    box = win.bounding_box()
                    assert abs(box['width'] - 900) < 2 and abs(box['height'] - 600) < 2, box
                expect(win.locator('.surface-mast-title')).to_have_count(1)
                expect(win.locator('.surface-mast-facts')).to_have_count(1)
                state_type = win.locator('.surface-mast-facts').evaluate("el => ({case:getComputedStyle(el).textTransform,tracking:parseFloat(getComputedStyle(el).letterSpacing)})")
                assert state_type['case'] == 'none' and state_type['tracking'] > 0, state_type
                expect(win.locator('.kit-statusbar')).to_have_count(1)
                expect(win.locator('.kit-statusbar-clock')).to_have_count(1)
                page.screenshot(path=str(OUT / f'1-{app}-rest-{900 if width == 1440 else 393}.png'))
            # Today now declares Refresh in its list verbs. Exercise the ink
            # strip verb through the same kit in the local busy specimen.
            page.goto(f'{base}/design/components?token={TOKEN}', wait_until='load')
            _normal_chair(page)
            page.get_by_role('navigation',name='Patterns').get_by_role('button',name='Conversation',exact=True).click()
            page.get_by_role('combobox',name='Example state').select_option('busy')
            strip = page.get_by_test_id('reference-conversation-status')
            verb = strip.get_by_role('button',name='Stop',exact=True)
            expect(verb).to_be_visible()
            verb.scroll_into_view_if_needed()
            facts = strip.evaluate('''el => {const r=el.getBoundingClientRect(), ctx=document.createElement('canvas').getContext('2d');ctx.fillStyle=getComputedStyle(el.querySelector('button'), getComputedStyle(el.querySelector('button'),'::before').content !== 'none' ? '::before' : null).backgroundColor;ctx.fillRect(0,0,1,1);return {plate:[...ctx.getImageData(0,0,1,1).data].slice(0,3),height:r.height,parts:[...el.querySelectorAll('button,time,.kit-statusbar-item')].filter(e=>e.getClientRects().length).map(e=>e.getBoundingClientRect().toJSON()),bg:getComputedStyle(el.querySelector('button')).backgroundColor}}''')
            assert facts['height'] <= max(p['height'] for p in facts['parts']) + 1, facts
            assert max(facts['plate']) < 100, facts
            assert max(p['y'] for p in facts['parts']) < min(p['bottom'] for p in facts['parts']), facts
            page.screenshot(path=str(OUT.parent / "r4" / f"ink-strip-{900 if width == 1440 else 393}.png"))
            verb.click()
            expect(verb).to_have_count(0)
            browser.close()
    finally:
        server.stop()
