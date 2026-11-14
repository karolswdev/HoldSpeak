"""An unselected collection keeps main's complete list seat at both widths."""
import copy
import json
import mimetypes
import os
import re
from pathlib import Path
import pytest
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http
from .test_programs_group_polish_glass import LONG_NAME
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.tmp/evidence-shots/programs-group14-r2'
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
            if phase=='before':
                frozen=ROOT/'.tmp/programs-group14/r2/held-built'
                page.route('**/_built/**',lambda route:route.fulfill(path=str(frozen/route.request.url.split('/_built/',1)[1]),content_type=mimetypes.guess_type(route.request.url)[0] or 'application/octet-stream'))
                page.route(re.compile(r'^'+re.escape(base)+r'/(?:\?.*)?$'),lambda route:route.fulfill(path=str(frozen/'index.html'),content_type='text/html'))
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
                for state in ['list','selected']:
                    if state=='selected':win.get_by_test_id(query).first.click()
                    _settle(page);page.screenshot(path=str(OUT/f'{app}-{state}-{900 if width==1440 else 393}-{phase}.png'))
                    if state=='list':
                        fit=win.evaluate('''el=>{const well=el.querySelector('.object-list-rows'),strip=el.querySelector('.kit-statusbar'),toolbar=el.querySelector('.object-list-toolbar');const rows=[...well.querySelectorAll('[data-object-id]')];const top=well.getBoundingClientRect().top,bottom=well.getBoundingClientRect().bottom;return {whole:rows.filter(r=>r.getBoundingClientRect().top>=top-1&&r.getBoundingClientRect().bottom<=bottom+1).length,capacity:Math.min(rows.length,Math.floor((strip.getBoundingClientRect().top-top)/rows[0].getBoundingClientRect().height)),wellBottom:bottom,statusTop:strip.getBoundingClientRect().top,toolbarHeight:toolbar.getBoundingClientRect().height,findY:el.querySelector('.object-list-find').getBoundingClientRect().top+el.querySelector('.object-list-find').getBoundingClientRect().height/2,verbsY:toolbar.querySelector('.object-list-toolbar-strip').getBoundingClientRect().top+toolbar.querySelector('.object-list-toolbar-strip').getBoundingClientRect().height/2,preview:!!el.querySelector('.surface-list-pane-preview')};}''')
                        metrics[app]=fit
                        if fit['whole']<fit['capacity'] or fit['preview']:faults.append((app,'unselected list lost rows',fit))
                        if width==393 and abs(fit['findY']-fit['verbsY'])>2:faults.append((app,'Find took a second row',fit))
                    if app=='recordings' and state=='selected':
                        head=win.locator('.surface-pane-inspector-head strong').first
                        expect(head.locator('[title]')).to_have_attribute('title',LONG_NAME)
                if app=='projects' and width==1440:
                    _api(page,'POST','/api/desk/windows/surface-projects/set_geometry',{'rect':{'x':'-1/2 + 100','y':'-1/2 + 80','w':'520px','h':'360px'}},token=TOKEN)
                    _settle(page);page.screenshot(path=str(OUT/f'projects-selected-520-{phase}.png'))
            browser.close()
    finally:server.stop()
    (ROOT/f'.tmp/programs-group14/r2/capacity-{width}-{phase}.json').write_text(json.dumps(metrics,indent=2))
    assert not faults,faults
