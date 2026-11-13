"""Shared fitting properties on seeded apps and recorded hub answers."""
from pathlib import Path
import json
import os
from urllib.parse import urlparse
import pytest
from .glass_infra import clear_hub_windows_http, _normal_chair, _settle
from .test_desk_sweep import TOKEN, _Case, _hub_open, _page, desk as sweep_desk, pw_browser

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.tmp/evidence-shots/kit14'


@pytest.fixture
def desk(tmp_path_factory, pw_browser):
    # Geometry cases own their seed. A later case must not reuse a launch
    # that an earlier question, producer or idle sweep changed.
    yield from sweep_desk.__wrapped__(tmp_path_factory, pw_browser)


def _before(page):
    snapshot = os.environ.get('KIT14_BASELINE_BUILD')
    if not snapshot:
        return
    build = Path(snapshot)
    def assets(route):
        path = urlparse(route.request.url).path
        relative = path.removeprefix('/_built/') if path.startswith('/_built/') else path.lstrip('/')
        if route.request.resource_type == 'document':
            route.fulfill(path=str(build / 'index.html'))
        elif path.startswith(('/_built/','/assets/')) and (build / relative).is_file():
            route.fulfill(path=str(build / relative))
        else:
            route.continue_()
    page.route('**/*', assets)


def _shot(page, item, state, width):
    _settle(page)
    OUT.mkdir(parents=True, exist_ok=True)
    phase = 'before' if os.environ.get('KIT14_BASELINE_BUILD') else 'after'
    page.screenshot(path=str(OUT / f'{item}-{state}-{width}-{phase}.png'))


def _press(page, win, label):
    button = win.get_by_role('button', name=label, exact=True)
    if button.count() and button.first.is_visible():
        button.first.click()
    else:
        win.get_by_role('button', name='Actions ▾', exact=True).click()
        page.get_by_role('menuitem', name=label, exact=True).click()


@pytest.mark.parametrize('width', [900, 393])
@pytest.mark.parametrize('item', ['1', '2', '4', '7', '8', '9', '13', '17', '21', '22', '24'])
def test_kit_geometry(desk, pw_browser, width, item):
    from playwright.sync_api import expect
    base = desk['base']
    if item in {'1','24'}:
        import holdspeak.agent_context as agent_context
        from tests.integration.test_desk_agents_wire import _ag0_seed
        _ag0_seed(Path(agent_context.AGENT_CONTEXT_FILE).parent.parent)
        if item == '24':
            from .agents_lane_rig import _http
            status, receipt = _http(base, 'POST', '/api/agent/launches/launch_ag0_done/done', TOKEN, {})
            assert status == 200, receipt
            desk['kit14_agent_checked'] = True
    app = 'surface-projects' if item == '2' else 'surface-workbenches' if item in {'8','9'} else 'surface-live' if item in {'17','21','22'} else 'conductor'
    clear_hub_windows_http(base, TOKEN)
    _hub_open(base, app, None, window=width == 900)
    ctx, page, errors, requests = _page(pw_browser, width, base)
    _before(page)
    if item == '24':
        # Exercise the named failure state with the hub's own missing-target
        # refusal. The retained launch still supplies the question and result.
        page.route('**/api/agent/launches/launch_ag0_done/seen', lambda route: route.continue_(url=f'{base}/api/agent/launches/kit14-missing/seen'))
    if item in {'17','21','22'}:
        wire = json.loads((ROOT / 'web/src/test/wire/live.actions.wire.json').read_text())['wire']
        page.route_web_socket('**/ws*', lambda socket: None)
        page.route('**/api/state', lambda route: route.fulfill(json=wire['state']))
    try:
        page.goto(f'{base}/?token={TOKEN}', wait_until='load')
        _normal_chair(page)
        case = _Case(page, base, app, errors, requests)
        case.settle()
        win = page.locator(f'[id="{app}"]')
        expect(win).to_be_visible()
        if item == '2':
            expect(win.locator('[data-object-id]').first).to_be_visible()
            _shot(page,item,'unselected',width)
            assert not win.get_by_text('Select a project', exact=True).count()
            assert not win.locator('.surface-list-pane-preview').count()
        elif item in {'8','9'}:
            row = win.locator('[data-object-id]').first
            row.click()
            _press(page,win,'Delete')
            question = win.locator('[data-question]')
            expect(question).to_be_visible()
            _shot(page,item,'delete-question',width)
            gap = question.evaluate('''el => {const parts=[...el.children].filter(e=>e.getClientRects().length), verbs=el.querySelector('.surface-inspector-actions'); const previous=parts[parts.indexOf(verbs)-1];return verbs.getBoundingClientRect().top-previous.getBoundingClientRect().bottom;}''')
            if item == '9':
                assert 0 <= gap <= 24, gap
            cancel = question.get_by_role('button',name='Cancel',exact=True)
            expect(cancel).to_be_focused()
            assert cancel.evaluate("el => parseFloat(getComputedStyle(el).outlineWidth)") >= 2
        elif item in {'4','7'}:
            rows = win.locator('[data-object-id]')
            expect(rows.nth(1)).to_be_visible()
            rows.first.click()
            if width == 393:
                win.get_by_role('button',name='Back',exact=True).click()
            rows.nth(1).hover()
            if item == '4':
                _shot(page,item,'selection-and-hover',width)
                assert win.locator('[data-object-id][aria-selected="true"]').count() == 1
                assert rows.first.evaluate('el=>getComputedStyle(el).backgroundColor') != rows.nth(1).evaluate('el=>getComputedStyle(el).backgroundColor')
            else:
                rows.nth(1).click(button='right')
                menu = page.get_by_role('menu').last
                expect(menu).to_be_visible()
                _shot(page,item,'row-menu',width)
                a,b = rows.nth(1).bounding_box(),menu.bounding_box()
                assert a and b
                assert b['y'] >= a['y']+a['height']-1 or b['y']+b['height'] <= a['y']+1, (a,b)
        elif item in {'1','24'}:
            row = win.get_by_role('row',name=__import__('re').compile('Draft test scaffolding for flags')).first
            row.click()
            if item == '24':
                expect(win.get_by_text('Could not mark it seen', exact=True)).to_be_visible()
                _press(page,win,'Remove')
                expect(win.locator('[data-question]')).to_be_visible()
                _shot(page,item,'remove-question',width)
                body = win.get_by_test_id('agents-mast').locator(':scope > .surface-inspector-body')
                assert body.evaluate("el=>el.scrollHeight<=el.clientHeight+1 || ['auto','scroll'].includes(getComputedStyle(el).overflowY)"), 'Overflowing reading needs a bounded scroll well'
                assert body.bounding_box()['y']+body.bounding_box()['height'] <= win.locator('.kit-statusbar').bounding_box()['y']+1
                return
            if width == 393:
                win.get_by_role('button',name='Back',exact=True).click()
            _shot(page,item,'list-name',width)
            if width == 900:
                expect(row.locator('[data-col="state"]')).to_be_visible()
                name=row.locator('.object-list-selection-name').get_attribute('title')
                shown=row.locator('.object-list-selection-title').inner_text()
                assert shown==name or shown=='…' or (shown.endswith('…') and name.startswith(shown[:-1]+' ')),(shown,name)
                assert row.locator('.object-list-selection-title').evaluate('el=>el.scrollWidth<=el.clientWidth+1')
        elif item == '13':
            line = win.locator('.surface-mast-facts')
            _shot(page,item,'mast',width)
            expect(win.locator('.surface-mast-title')).to_have_text('Agents')
            text = line.inner_text()
            full = line.get_attribute('aria-label')
            assert text == full or full.startswith(text+' · ') or not text
            assert line.evaluate('el=>el.scrollWidth <= el.clientWidth+1')
        elif item == '17':
            level = win.get_by_test_id('live-level')
            expect(level).to_be_visible()
            _shot(page,item,'recording-strip',width)
            assert level.bounding_box()['width'] >= 48
            bar = win.locator('.kit-statusbar')
            assert bar.evaluate('el=>el.scrollWidth<=el.clientWidth+1')
        elif item == '22':
            mark = win.locator('.transcript-list li[data-mark]')
            expect(mark).to_be_visible()
            _shot(page,item,'marked-transcript',width)
            assert mark.evaluate("el=>parseFloat(getComputedStyle(el).borderInlineStartWidth)") == 0
            assert mark.evaluate("el=>getComputedStyle(el).outlineStyle") == 'none'
            assert mark.locator('time').evaluate("el=>getComputedStyle(el).fontWeight") == '700'
        else:
            well = win.get_by_test_id('live-transcript')
            expect(well).to_be_visible()
            # Resize the shared well to the Calls inspector's narrow seat.
            # This changes only its containing width, never the transcript DOM.
            well.evaluate("el=>{el.style.width='270px';el.style.flex='none';el.style.height='300px';}")
            expect(well.locator('li').first).to_be_visible()
            _shot(page,item,'narrow-transcript',width)
            line = well.locator('li').first
            words = line.locator('p').bounding_box()
            time = line.locator('time').bounding_box()
            assert words and time and words['y'] >= time['y']+time['height']-1
            assert abs(words['x']-line.bounding_box()['x']-8) <= 2
    finally:
        ctx.close()
