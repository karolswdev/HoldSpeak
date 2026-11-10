"""Automations' selection, same-window setup, questions and bounded wells."""
from pathlib import Path
import re
import json
from typing import Any
import pytest
from tests._evidence import evidence_dir
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows
from .test_desk_sweep import AIR_WORDS_JS, LIST_GRAMMAR_JS, _seed_automation, _start_app_walk

pytestmark = [pytest.mark.e2e]
TOKEN = 'automations-grammar'

@pytest.mark.parametrize('width',[1440,393])
def test_automations_selection_and_setup_fit_one_window(tmp_path:Path,monkeypatch:pytest.MonkeyPatch,width:int):
    from playwright.sync_api import sync_playwright, expect
    _ensure_build()
    server,base = _boot(tmp_path,monkeypatch,token=TOKEN)
    from holdspeak.db import get_database
    db=get_database()
    wb=_seed_automation('grammar-note')
    db.workbenches.upsert(workbench_id='grammar-prep',name='Morning prep',instruction='Prepare my meetings.')
    db.workbenches.upsert(workbench_id='grammar-night',name='Nightly check',instruction='Check the changes.')
    shots=evidence_dir('os-grammar')
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            page=browser.new_page(viewport={'width':width,'height':900 if width==1440 else 852},reduced_motion='reduce',has_touch=width==393)
            page.set_default_timeout(15_000)
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(f'{base}/?token={TOKEN}')
            _api(page,'PUT','/api/setup/onboarding',{'disposition':'completed'},token=TOKEN)
            page.goto(f'{base}/?token={TOKEN}')
            _normal_chair(page)
            page.get_by_role('button',name='Go',exact=True).first.click()
            page.locator("nav[aria-label='Go menu']").get_by_role('menuitem',name='Automations',exact=True).evaluate('el => el.click()')
            win=page.locator('#surface-workbenches')
            win.get_by_role('grid',name='Automations',exact=True).wait_for()
            if width==1440:
                _api(page,'POST','/api/desk/windows/surface-workbenches/set_geometry',{'rect':{'x':'-1/2 + 100','y':'-1/2 + 80','w':'900px','h':'600px'}},token=TOKEN)
            def shot(state):
                _settle(page)
                if width == 1440:
                    box=win.bounding_box()
                    assert round(box["width"]) == 900 and round(box["height"]) == 600,box
                assert not page.evaluate(LIST_GRAMMAR_JS,'#surface-workbenches')
                assert win.evaluate("el => {const b=el.querySelector('.desk-surface-body');return b.scrollWidth<=b.clientWidth+1 && b.scrollHeight<=b.clientHeight+1}")
                air_words=page.evaluate(AIR_WORDS_JS,'#surface-workbenches')
                assert not air_words['air'],air_words['air']
                assert not air_words['whole'],air_words['whole']
                page.screenshot(path=str(shots/f'automations-{state}-{"900x600" if width==1440 else "393"}-after.png'))
            def selected_row(): return win.locator(f'[data-object-id="{wb}"]')
            def verb(name):
                direct=win.get_by_role('button',name=name,exact=True)
                if direct.is_visible(): direct.click()
                else:
                    win.get_by_role('button',name='Actions ▾',exact=True).click()
                    page.get_by_role('menu').last.get_by_role('menuitem',name=re.compile('^'+re.escape(name))).click()
            def setup_tab(label):
                tab=win.get_by_role('tab',name=label,exact=True)
                if tab.is_visible(): tab.click()
                else: win.get_by_role('combobox',name='Automation setup tab').select_option(value={'Do':'do','When':'when','About':'about','With':'with','Put it in':'put'}[label])
            shot('list')
            selected_row().click()
            expect(selected_row()).to_have_attribute('aria-selected','true')
            assert page.get_by_test_id('automation-window').count()==0
            shot('selected')
            selected_row().click(button='right')
            menu=page.get_by_role('menu',name='Automations actions',exact=True)
            expect(menu.get_by_role('menuitem',name=re.compile('^Run now'))).to_be_visible()
            shot('context-menu')
            page.keyboard.press('Escape')
            selected_row().press('ArrowDown')
            expect(win.locator('[aria-selected="true"][data-object-id]')).not_to_have_attribute('data-object-id',wb)
            selected_row().click()
            selected_row().press('Enter')
            obj=page.locator(f'[id="workbench:{wb}"]')
            obj.get_by_test_id('automation-sentence').wait_for()
            obj.locator('.desk-gadget-close').click()
            verb('Edit')
            win.get_by_test_id('automation-setup').wait_for()
            shot('edit-do')
            win.get_by_role('combobox',name='Do kind').select_option('run_program')
            shot('edit-program')
            win.get_by_role('button',name='Save',exact=True).scroll_into_view_if_needed()
            shot('edit-program-actions')
            win.get_by_role('combobox',name='Do kind').select_option('hand_to_agent')
            shot('edit-hand')
            win.get_by_role('combobox',name='Do kind').select_option('run')
            text=win.get_by_role('textbox',name='What it does')
            text.fill('Draft the update and name each owner.')
            page.route(f'**/api/workbenches/{wb}',lambda route:route.fulfill(status=503,json={'error':'Unavailable'}) if route.request.method=='PUT' else route.continue_())
            win.get_by_role('button',name='Save',exact=True).click()
            win.get_by_role('alert').wait_for()
            expect(text).to_have_value('Draft the update and name each owner.')
            shot('save-failed')
            page.unroute(f'**/api/workbenches/{wb}')
            win.get_by_role('button',name='Save',exact=True).click()
            win.get_by_test_id('automation-summary').wait_for()
            assert db.workbenches.get(wb).instruction=='Draft the update and name each owner.'
            verb('Edit')
            engine_recording=json.loads(Path('web/src/features/runson/__tests__/fixtures/engines.recorded.json').read_text())
            found=next(step for step in engine_recording['claude']['steps'] if step['name']=='found')['gets']['/api/concierge/detect']
            page.route('**/api/concierge/detect',lambda route:route.fulfill(json=found))
            for tab in ('When','About','With','Put it in'):
                setup_tab(tab)
                shot('edit-'+{'When':'when','About':'about','With':'with','Put it in':'put'}[tab])
                if tab == 'About' and width == 393:
                    assert win.get_by_role('tab',name='About',exact=True).is_visible()
                    assert win.get_by_role('combobox',name='Automation setup tab').count() == 0
                    source_list = win.get_by_role('grid',name='Sources to add',exact=True)
                    assert source_list.evaluate("el => {const row=el.closest('.gadget-row'),label=row.querySelector('.gadget-row-label');return el.getBoundingClientRect().top >= label.getBoundingClientRect().bottom && el.getBoundingClientRect().width >= row.clientWidth - 2}")
                if tab=='With':
                    win.get_by_role('combobox',name='With',exact=True).select_option(label='Add Claude Code')
                    expect(win.get_by_text('Anthropic',exact=True)).to_be_visible()
                    shot('engine-choice')
                if tab=='When':
                    win.get_by_role('combobox',name='When',exact=True).select_option('weekday')
                    shot('edit-schedule')
                    choices=win.get_by_role('combobox',name='When',exact=True).locator('option').evaluate_all("els => els.map(el=>el.value).filter(v=>v.startsWith('event:'))")
                    if choices:
                        win.get_by_role('combobox',name='When',exact=True).select_option(choices[0])
                        shot('edit-event')
            win.get_by_role('button',name='Cancel',exact=True).click()
            verb('Delete')
            question=win.get_by_role('region',name='Delete Friday team update?',exact=True)
            expect(question).to_be_visible()
            expect(question.get_by_role('button',name='Cancel',exact=True)).to_be_focused()
            expect(question.get_by_role('button',name='Delete',exact=True)).to_have_class(re.compile('btn--danger'))
            shot('delete')
            page.route(f'**/api/workbenches/{wb}',lambda route:route.fulfill(status=503,json={'error':'Unavailable'}) if route.request.method=='DELETE' else route.continue_())
            question.get_by_role('button',name='Delete',exact=True).click()
            question.get_by_role('alert').wait_for()
            shot('delete-failed')
            page.unroute(f'**/api/workbenches/{wb}')
            question.get_by_role('button',name='Cancel',exact=True).click()
            verb('New automation')
            shot('new')
            win.get_by_role('combobox',name='Automation starter').select_option('friday-team-update')
            shot('starter')
            page.route('**/api/workbench-templates/*/instantiate',lambda route:route.fulfill(status=503,json={'error':'Unavailable'}))
            win.get_by_role('button',name='Create',exact=True).click()
            win.get_by_role('alert').wait_for()
            shot('create-failed')
            expect(win.get_by_role('combobox',name='Automation starter')).to_have_value('friday-team-update')
            win.get_by_role('button',name='Cancel',exact=True).click()
            win.get_by_role('textbox',name='Find an automation').fill('no-such-automation')
            shot('no-match')
            win.get_by_role('textbox',name='Find an automation').fill('')
            selected_row().click()
            selected_row().dblclick()
            obj.get_by_test_id('automation-sentence').wait_for()
            obj.locator('.desk-gadget-close').click()
            page.evaluate("localStorage.setItem('hs:walk-voice','off')")
            _start_app_walk(page)
            script=json.loads(Path('web/src/desk/walks/automations.walk.json').read_text())
            for _ in range(len(script['steps'])+1):
                page.wait_for_function("() => ['walk-next','walk-choice-0','walk-end'].some(id => document.querySelector(`[data-testid=${id}]`)?.getClientRects().length)")
                if page.get_by_test_id('walk-end').is_visible(): break
                if page.get_by_test_id('walk-choice-0').is_visible():
                    with page.expect_response(lambda response:'/api/w/' in response.url and response.url.endswith('/answer')) as answered:
                        page.get_by_test_id('walk-choice-0').click()
                    assert answered.value.ok
                    page.get_by_test_id('walk-end').wait_for()
                    break
                else: page.get_by_test_id('walk-next').click()
            page.get_by_test_id('walk-back').click()
            shot('walk-done')
            selected_row().click()
            page.route(f'**/api/workbenches/{wb}/run',lambda route:route.fulfill(status=503,json={'error':'Unavailable'}))
            verb('Run now')
            win.get_by_role('alert').wait_for()
            shot('run-failed')
            page.unroute(f'**/api/workbenches/{wb}/run')
            recording=json.loads(Path('web/src/desk/__tests__/fixtures/automation-hub/program-still.json').read_text())
            detail=recording['gets'][f"/api/workbenches/{recording['workbench_id']}"]['workbench']
            page.route('**/api/workbenches',lambda route:route.fulfill(json={'workbenches':[detail]}))
            page.reload()
            _normal_chair(page)
            win.locator(f'[data-object-id="{detail["id"]}"]').click()
            shot('running')
            page.route('**/api/programs/*/park',lambda route:route.fulfill(status=503,json={'error':'Unavailable'}))
            verb('Cancel run')
            win.get_by_role('alert').wait_for()
            shot('cancel-failed')
            failed_recording=json.loads(Path('web/src/desk/__tests__/fixtures/automation-hub/failed.json').read_text())
            failed_detail=failed_recording['gets'][f"/api/workbenches/{failed_recording['workbench_id']}"]['workbench']
            page.route('**/api/workbenches',lambda route:route.fulfill(json={'workbenches':[failed_detail]}))
            page.reload()
            _normal_chair(page)
            failed_row=win.locator(f'[data-object-id="{failed_detail["id"]}"]')
            failed_row.click()
            if width == 1440: expect(failed_row).to_contain_text('Failed')
            shot('failed')
            page.route('**/api/workbenches',lambda route:route.fulfill(json={'workbenches':[]}))
            page.reload()
            _normal_chair(page)
            win.get_by_test_id('automation-home-empty').wait_for()
            shot('empty')
            page.route('**/api/workbenches',lambda route:route.fulfill(status=503,json={'error':'Unavailable'}))
            page.reload()
            _normal_chair(page)
            win.get_by_role('alert').wait_for()
            shot('read-failed')
            assert errors==[],errors
            browser.close()
    finally: server.stop()
