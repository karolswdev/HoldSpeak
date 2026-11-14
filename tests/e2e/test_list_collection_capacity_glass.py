"""An unselected collection keeps main's complete list seat at both widths."""
import json
import os
import re
from pathlib import Path
import pytest
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http
from .test_programs_group_polish_glass import LONG_NAME
from .programs_group_rows_rig import row_faults
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.tmp/evidence-shots/programs-group14-r3'
TOKEN='collection-capacity'

@pytest.mark.parametrize('width',[1440,393])
@pytest.mark.timeout(240)
def test_unselected_collections_keep_the_whole_list(tmp_path,monkeypatch,width):
    from playwright.sync_api import sync_playwright, expect
    _ensure_build();OUT.mkdir(parents=True,exist_ok=True)
    phase=os.environ.get('POLISH_PHASE','after')
    projects=json.loads((ROOT/'web/src/pages/cores/__tests__/fixtures/projects/recorded.json').read_text())
    rows=[{**projects['gets']['/api/projects']['projects'][1],'id':f'long-project-{i}','name':LONG_NAME} for i in range(50)]
    room=projects['gets'][f"/api/projects/{projects['vendor']}/room"]
    decisions=json.loads((ROOT/'web/src/test/wire/decisions.honest-faces.wire.json').read_text())['wire']
    decisions['decisions']=[{**decisions['decisions'][0],'id':f'long-decision-{i}','record_id':None,'text':LONG_NAME} for i in range(50)]
    decisions['page']['total']=50
    source=(ROOT/'web/src/desk/recordings/__fixtures__/recordings.list.ts').read_text()
    recordings=json.loads(source[source.index('= {')+2:].strip().removesuffix(';'))
    template=next(row for row in recordings['recordings'] if row['state']=='ready')
    recordings['recordings']=[{**template,'id':f'long-recording-{i}','title':LONG_NAME} for i in range(50)]
    server,base=_boot(tmp_path,monkeypatch,token=TOKEN)
    faults=[];metrics={}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch();page=browser.new_page(viewport={'width':width,'height':900 if width==1440 else 852},reduced_motion='reduce')
            page.route('**/api/projects',lambda route:route.fulfill(json={'projects':rows}))
            page.route('**/api/projects/*/room',lambda route:route.fulfill(json=room))
            page.route('**/api/decisions/ledger?*',lambda route:route.fulfill(json=decisions))
            page.route('**/api/recordings',lambda route:route.fulfill(json=recordings))
            page.goto(f'{base}/?token={TOKEN}',wait_until='load')
            _api(page,'PUT','/api/setup/onboarding',{'disposition':'completed'},token=TOKEN)
            for app,query in [('projects','projects-row'),('decisions','decisions-row'),('recordings','recordings-row')]:
                clear_hub_windows_http(base,TOKEN)
                _api(page,'POST',f'/api/desk/windows/surface-{app}/open',{},token=TOKEN)
                if width==1440:_api(page,'POST',f'/api/desk/windows/surface-{app}/set_geometry',{'rect':{'x':'-1/2 + 100','y':'-1/2 + 80','w':'900px','h':'600px'}},token=TOKEN)
                page.reload(wait_until='load');_normal_chair(page);win=page.locator(f'#surface-{app}')
                expect(win.get_by_test_id(query)).to_have_count(50)
                for state in ['list','selected','selected-last']:
                    if state=='selected':win.get_by_test_id(query).first.click()
                    if state=='selected-last':win.get_by_test_id(query).last.click()
                    _settle(page);page.screenshot(path=str(OUT/f'{app}-{state}-{900 if width==1440 else 393}-{phase}.png'))
                    faults.extend(row_faults(win,(app,state),6 if width==1440 and state!='list' else 0))
                    if state=='list':
                        fit=win.evaluate('''el=>{const well=el.querySelector('.object-list-rows'),strip=el.querySelector('.kit-statusbar'),toolbar=el.querySelector('.object-list-toolbar');const rows=[...well.querySelectorAll('[data-object-id]')];const top=well.getBoundingClientRect().top,bottom=well.getBoundingClientRect().bottom;return {whole:rows.filter(r=>r.getBoundingClientRect().top>=top-1&&r.getBoundingClientRect().bottom<=bottom+1).length,capacity:Math.min(rows.length,Math.floor((strip.getBoundingClientRect().top-top)/rows[0].getBoundingClientRect().height)),wellBottom:bottom,statusTop:strip.getBoundingClientRect().top,toolbarHeight:toolbar.getBoundingClientRect().height,findY:el.querySelector('.object-list-find').getBoundingClientRect().top+el.querySelector('.object-list-find').getBoundingClientRect().height/2,verbsY:toolbar.querySelector('.object-list-toolbar-strip').getBoundingClientRect().top+toolbar.querySelector('.object-list-toolbar-strip').getBoundingClientRect().height/2,preview:!!el.querySelector('.surface-list-pane-preview')};}''')
                        metrics[app]=fit
                        if fit['whole']<fit['capacity'] or fit['preview']:faults.append((app,'unselected list lost rows',fit))
                        if width==393 and abs(fit['findY']-fit['verbsY'])>2:faults.append((app,'Find took a second row',fit))
                    if app=='projects' and state=='selected':
                        facts=win.locator('.surface-inspector-facts').inner_text()
                        for word in ['STATE','SOURCES','LAST UPDATE','OPEN ITEMS','NEXT MEETING']:
                            if word not in facts:faults.append(('project fact missing',word))
                    if state=='selected':
                        ink=win.evaluate('''el=>[...el.querySelectorAll('.object-list-selection-title[title],.surface-pane-inspector-head strong > [title]')].filter(node=>node.getBoundingClientRect().width).map(node=>{const range=document.createRange();range.selectNodeContents(node.firstChild);const b=node.getBoundingClientRect(),r=range.getBoundingClientRect();return {text:node.textContent,width:b.width,ink:r.width,whole:r.left>=b.left-1&&r.right<=b.right+1};})''')
                        metrics[app]['names']=ink
                        tracks=win.evaluate('''el=>[...el.querySelectorAll('.object-list-head [data-col]')].filter(h=>h.getBoundingClientRect().width).map(h=>{const key=h.dataset.col,row=el.querySelector('.object-list-row [data-col="'+key+'"]');return {key,head:h.getBoundingClientRect().toJSON(),cell:row?.getBoundingClientRect().toJSON()};})''')
                        metrics[app]['tracks']=tracks
                        if any(abs(track['head']['left']-track['cell']['left'])>1 or abs(track['head']['width']-track['cell']['width'])>1 for track in tracks):faults.append(('column heads and rows disagree',app,tracks))
                        if any(not name['whole'] for name in ink):faults.append(('name leaves its seat',app,ink))
                        head=win.locator('.surface-pane-inspector-head strong').first.inner_text()
                        if re.search(r'ProgramWindow\.\s*\n\s*tsx',head):faults.append(('extension on another line',head))
                    if app=='recordings' and state=='selected':
                        head=win.locator('.surface-pane-inspector-head strong').first
                        expect(head.locator('[title]')).to_have_attribute('title',LONG_NAME)
                if app=='projects' and width==1440:
                    _api(page,'POST','/api/desk/windows/surface-projects/set_geometry',{'rect':{'x':'-1/2 + 100','y':'-1/2 + 80','w':'520px','h':'360px'}},token=TOKEN)
                    _settle(page);page.screenshot(path=str(OUT/f'projects-selected-520-{phase}.png'))
                    faults.extend(row_faults(win,('projects','selected-520'),1))
                    gap=win.evaluate('''el=>{const grid=el.querySelector('.object-list'),well=grid.querySelector('.object-list-rows'),row=well.querySelector('.object-list-row');return {spare:grid.getBoundingClientRect().bottom-well.getBoundingClientRect().bottom,row:row.getBoundingClientRect().height,gridHeight:grid.clientHeight,wellHeight:well.clientHeight,wellTop:well.getBoundingClientRect().top,gridTop:grid.getBoundingClientRect().top,scroll:well.scrollTop,min:getComputedStyle(grid.parentElement).getPropertyValue('--surface-list-min'),children:[...grid.children].map(el=>({cls:el.className,height:el.getBoundingClientRect().height,margin:getComputedStyle(el).margin})),borders:getComputedStyle(well).borderWidth};}''')
                    metrics['small']=gap
                    if gap['spare']>=gap['row']-1:faults.append(('a whole row of list space was left blank',gap))
            browser.close()
    finally:server.stop()
    (ROOT/f'.tmp/programs-group14/r3/capacity-{width}-{phase}.json').write_text(json.dumps(metrics,indent=2))
    assert not faults,faults
