"""Needs names, automation counts and dated update names use saved wire shapes."""
import copy,json,os
from pathlib import Path
import pytest
from .glass_infra import _api,_boot,_ensure_build,_normal_chair,_settle,clear_hub_windows_http
from .test_programs_group_polish_glass import LONG_NAME
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.tmp/evidence-shots/programs-group14-r3';TOKEN='group-detail-fit'

@pytest.mark.parametrize('width',[1440,393])
@pytest.mark.timeout(240)
def test_group_detail_fits(tmp_path,monkeypatch,width):
    from playwright.sync_api import sync_playwright,expect
    _ensure_build();OUT.mkdir(parents=True,exist_ok=True);phase=os.environ.get('POLISH_PHASE','after')
    home=json.loads((ROOT/'web/src/desk/__tests__/fixtures/automation-hub/home-rows.json').read_text())['gets']['/api/workbenches']
    source=home['workbenches'][0]
    rows=[{**copy.deepcopy(source),'id':f'long-auto-{i}','name':LONG_NAME if i==0 else f'Architecture check {i}','results':[{**source['results'][0],'new':True} for _ in range(5)] if i==0 else []} for i in range(3)]
    needs=json.loads((ROOT/'web/src/desk/needs/__fixtures__/needs_you.grammar.json').read_text())
    current=copy.deepcopy(needs['questions'])
    room=json.loads((ROOT/'web/src/features/project-room/__tests__/room-wires/grammar10.json').read_text())
    updates=copy.deepcopy(room['UPDATES_AFTER_SENDS'])
    roomId=room['BARE_ROOM']['project_id']
    server,base=_boot(tmp_path,monkeypatch,token=TOKEN);faults=[]
    from holdspeak.db import get_database
    get_database().projects.create_project(project_id=roomId,name='Architecture change')
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch();page=browser.new_page(viewport={'width':width,'height':900 if width==1440 else 852},reduced_motion='reduce')
            page.route('**/api/workbenches',lambda route:route.fulfill(json={**home,'workbenches':rows}))
            page.route('**/api/desk/needs-you*',lambda route:route.fulfill(json=current))
            page.route('**/api/coders/sessions?*',lambda route:route.fulfill(json=needs['questionSessions']))
            page.route('**/api/projects/*/room',lambda route:route.fulfill(json=room['BARE_ROOM']))
            page.route('**/api/projects/*/updates',lambda route:route.fulfill(json=updates))
            page.route('**/api/updates/*',lambda route:route.fulfill(json={'update':next(row for row in updates['updates'] if row['id']==route.request.url.rsplit('/',1)[-1])}))
            page.goto(f'{base}/?token={TOKEN}',wait_until='load');_api(page,'PUT','/api/setup/onboarding',{'disposition':'completed'},token=TOKEN)
            def open_window(app,body=None):
                clear_hub_windows_http(base,TOKEN);_api(page,'POST',f'/api/desk/windows/{app}/open',body or {},token=TOKEN)
                if width==1440:_api(page,'POST',f'/api/desk/windows/{app}/set_geometry',{'rect':{'x':'-1/2 + 100','y':'-1/2 + 80','w':'900px','h':'600px'}},token=TOKEN)
                page.reload(wait_until='load');_normal_chair(page);return page.locator(f'[id="{app}"]')
            def shot(item,state):
                _settle(page);page.screenshot(path=str(OUT/f'{item}-{state}-{900 if width==1440 else 393}-{phase}.png'))
            win=open_window('surface-workbenches');expect(win.locator('[data-object-id]')).to_have_count(3);shot('automations','list')
            expect(win.get_by_role('button',name='New automation',exact=True)).to_be_visible()
            win.locator('[data-object-id="long-auto-0"]').click();shot('automations','selected')
            if not win.get_by_test_id('automation-home-status').get_by_text('1 with new results',exact=True).count():faults.append('new count is not the number of visible automations')
            (OUT/f'automation-name-{width}-{phase}.json').write_text(json.dumps(win.evaluate('''el=>{const row=el.querySelector('[data-object-id]'),cell=row.querySelector('[data-col="name"]'),title=cell.querySelector('.object-list-selection-title');return {cell:cell.getBoundingClientRect().toJSON(),title:title.getBoundingClientRect().toJSON(),shown:title.textContent,full:title.title,tracks:getComputedStyle(row).gridTemplateColumns};}'''),indent=2))
            switches=win.get_by_role('checkbox',name='Automatic starts',exact=True)
            if not switches.count():faults.append('switch does not name what starts')
            else:
                control=switches.locator('..')
                if not control.locator('.surface-lamp').count():faults.append('switch has no state lamp')
                font=control.locator('.gadget-check-state-word').evaluate('el=>getComputedStyle(el).fontFamily')
                if 'mono' in font.lower():faults.append(('switch state uses mono',font))
            win=open_window('chair:needs',{'kind':'chair','ref':'needs'});expect(win.get_by_test_id('needs-row')).to_have_count(len(current['items']));shot('needs','mixed-list')
            if width==393:
                state=win.locator('.object-list-row [data-col="state"]').first
                if state.count():
                    fit=win.evaluate('''el=>{const cells=[...el.querySelectorAll('.object-list-row [data-col="state"]')];const pill=Math.max(...cells.map(c=>c.firstElementChild.getBoundingClientRect().width));return {cell:cells[0].getBoundingClientRect().width,pill};}''')
                    if fit['cell']>fit['pill']+24:faults.append(('state wider than its content',fit))
            win.get_by_test_id('needs-row').first.click();shot('needs','mixed-selected')
            win=open_window('surface-project-memory',{'object_ref':f'project:{roomId}'})
            shot('room','opening')
            expect(win.get_by_role('tablist',name='Project lists',exact=True)).to_be_visible()
            updatesTab=win.get_by_role('tab',name='Updates',exact=True)
            if updatesTab.is_visible():updatesTab.click()
            else:
                win.get_by_role('button',name='Project lists more',exact=True).click();page.get_by_role('menuitem',name='Updates',exact=True).click()
            grid=win.get_by_role('grid',name='Updates',exact=True);expect(grid.locator('[data-object-id]').first).to_be_visible();shot('room','updates')
            first=grid.locator('[data-object-id]').first
            if 'Team folder' not in first.locator('.object-list-selection-name').inner_text():faults.append('update name loses its saved audience')
            first.click();shot('room','update-selected')
            choosers=win.get_by_role('button',name='Project view',exact=True).count()+win.get_by_role('button',name='Update view',exact=True).count()+win.get_by_role('combobox',name='View',exact=True).count()
            if choosers!=1:faults.append(('one View chooser',choosers))
            browser.close()
    finally:server.stop()
    assert not faults,faults
