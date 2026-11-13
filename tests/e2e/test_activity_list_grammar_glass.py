"""Activity over real isolated-hub records, with long names and explicit writes."""
import json
import mimetypes
import os
import re
from datetime import datetime, timezone
from pathlib import Path
import pytest
from .glass_infra import _api, _api_allow_error, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http
from .test_desk_sweep import _seed_finished_receipts
from .test_programs_group_polish_glass import LONG_NAME
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.tmp/evidence-shots/programs-group14-r2'
TOKEN='activity-list-grammar'

@pytest.mark.parametrize('width',[1440,393])
@pytest.mark.timeout(240)
def test_activity_records_and_verbs(tmp_path,monkeypatch,width):
    from playwright.sync_api import sync_playwright, expect
    _ensure_build();OUT.mkdir(parents=True,exist_ok=True)
    server,base=_boot(tmp_path,monkeypatch,token=TOKEN)
    from holdspeak.db import get_database
    db=get_database();phase=os.environ.get('POLISH_PHASE','after')
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch();page=browser.new_page(viewport={'width':width,'height':900 if width==1440 else 852},reduced_motion='reduce')
            if phase=='before':
                frozen=ROOT/'.tmp/programs-group14/r2/held-built'
                page.route('**/_built/**',lambda route:route.fulfill(path=str(frozen/route.request.url.split('/_built/',1)[1]),content_type=mimetypes.guess_type(route.request.url)[0] or 'application/octet-stream'))
                page.route(re.compile(r'^'+re.escape(base)+r'/(?:\?.*)?$'),lambda route:route.fulfill(path=str(frozen/'index.html'),content_type='text/html'))
            page.goto(f'{base}/?token={TOKEN}',wait_until='load')
            _api(page,'PUT','/api/setup/onboarding',{'disposition':'completed'},token=TOKEN)
            project=_api(page,'POST','/api/projects',{'name':'Architecture change'},token=TOKEN)['project']['id']
            for index in range(50):
                name=LONG_NAME.replace('ProgramWindow.tsx',f'ProgramStep{index}.tsx') if index%2==0 and index else LONG_NAME if index==0 else 'activity_saved_revision_'+('readwithoutspaces_'*9)+str(index)
                db.activity.upsert_activity_record(source_browser='chrome',url=f'https://example.test/architecture/{index}',title=name,project_id=project,last_seen_at=datetime.now(timezone.utc))
            rule=db.activity.create_activity_project_rule(project_id=project,name='Architecture pages',match_type='domain',pattern='example.test')
            candidate=db.activity.create_activity_meeting_candidate(source_connector_id='candidate_inference',title='Read the architecture change',meeting_url='https://example.test/meeting')
            _seed_finished_receipts()
            paths=['/api/activity/status','/api/activity/records?limit=100','/api/activity/project-rules','/api/activity/meeting-candidates','/api/activity/enrichment/connectors','/api/desk/projections?kind=receipt&attention_state=resolved&offset=0&limit=50']
            tape={'provenance':'real isolated hub; ActivityRecordsMixin and pipeline-event producers; no provider engine','gets':{path:_api(page,'GET',path,token=TOKEN) for path in paths}}
            writes=[]
            page.on('request',lambda request:writes.append(request.url) if request.method=='POST' and '/connections/' in request.url and '/recheck' in request.url else None)
            clear_hub_windows_http(base,TOKEN);_api(page,'POST','/api/desk/windows/surface-activity/open',{},token=TOKEN)
            if width==1440:_api(page,'POST','/api/desk/windows/surface-activity/set_geometry',{'rect':{'x':'-1/2 + 100','y':'-1/2 + 80','w':'900px','h':'600px'}},token=TOKEN)
            page.reload(wait_until='load');_normal_chair(page);win=page.locator('#surface-activity')
            def shot(state):
                _settle(page);page.screenshot(path=str(OUT/f'activity-{state}-{900 if width==1440 else 393}-{phase}.png'))
            def press(word):
                button=win.get_by_role('button',name=word,exact=True)
                if button.is_visible():button.click()
                else:
                    win.locator('[data-list-overflow]').first.click()
                    page.get_by_role('menuitem',name=re.compile('^'+re.escape(word)+'(?:$| )')).click()
            def view(word):
                target=win.get_by_role('tab',name=word,exact=True)
                if target.is_visible():target.click()
                else:
                    win.get_by_role('button',name='Activity views more',exact=True).click()
                    page.get_by_role('menuitem',name=word,exact=True).click()
            if phase=='before':
                expect(win.locator('[id^="activity-record-"]').first).to_be_attached();shot('records')
                win.locator('[id^="activity-record-"]').first.click();shot('selected')
                if win.get_by_role('tab',name='Rules',exact=True).is_visible():win.get_by_role('tab',name='Rules',exact=True).click()
                else:
                    win.locator('.desk-wings-menu').click();page.locator('[role^=menuitem]').filter(has_text=re.compile('^Rules$')).click()
                shot('rules')
                # The former gear combined candidates and connectors in its one face.
                gear=win.get_by_role('button',name='Candidates and connectors',exact=True)
                if gear.count():gear.click()
                else:
                    win.locator('.desk-wings-menu').click();page.locator('[role^=menuitem]').filter(has_text=re.compile('Candidates and connectors')).click()
                shot('connectors')
                assert not writes,writes
                assert not win.locator('.desk-pullout-head .desk-wings').count(), 'Activity tabs remain in the Mast'
                browser.close();return
            expect(win.get_by_role('grid',name='Activity',exact=True)).to_be_visible()
            expect(win.locator('[id="activity-record-1"]')).to_be_visible()
            assert win.get_by_test_id('activity-row').count() >= 50
            shot('records')
            assert not win.locator('.desk-pullout-head .desk-wings').count()
            assert not writes,writes
            win.locator('[id="activity-record-1"]').click();shot('selected')
            expect(win.get_by_role('region',name=LONG_NAME,exact=True)).to_be_visible()
            view('Rules');expect(win.get_by_test_id('activity-row')).to_have_count(1);shot('rules')
            win.get_by_test_id('activity-row').click();press('Delete');shot('delete-question')
            win.get_by_role('button',name='Cancel',exact=True).click()
            view('Candidates');expect(win.get_by_test_id('activity-row')).to_have_count(1);shot('candidates')
            win.get_by_test_id('activity-row').click();shot('candidate-selected')
            view('Connectors');expect(win.get_by_test_id('activity-row').first).to_be_visible();shot('connectors')
            win.get_by_test_id('activity-row').first.click();shot('connector-selected')
            # Record existing operation answers for the app press-through tests.
            connector=tape['gets']['/api/activity/enrichment/connectors']['connectors'][0]['id']
            tape['candidateStart']=_api_allow_error(page,'POST',f'/api/activity/meeting-candidates/{candidate.id}/start',{},token=TOKEN)
            tape['dryRun']=_api(page,'GET',f'/api/activity/enrichment/connectors/{connector}/dry-run?limit=25',token=TOKEN)
            tape['watched']=_api(page,'PUT','/api/activity/settings',{'enabled':True},token=TOKEN)
            tape['paused']=_api(page,'PUT','/api/activity/settings',{'enabled':False},token=TOKEN)
            tape['refreshed']=_api(page,'POST','/api/activity/refresh',{},token=TOKEN)
            tape['deletedRule']=_api(page,'DELETE',f'/api/activity/project-rules/{rule.id}',token=TOKEN)
            tape['recheckRefusal']=_api_allow_error(page,'POST','/api/connections/confluence/recheck',{},token=TOKEN)
            view('Records');press('Clear records');shot('clear-question')
            win.get_by_role('button',name='Cancel',exact=True).click()
            page.route('**/api/activity/records?*',lambda route:route.fulfill(status=503,json={'detail':'Activity not read'}))
            page.reload(wait_until='load');_normal_chair(page);expect(win.get_by_role('alert').first).to_be_visible();shot('failure')
            page.unroute('**/api/activity/records?*')
            tape['cleared']=_api(page,'DELETE','/api/activity/records',token=TOKEN)
            tape['emptyRecords']=_api(page,'GET','/api/activity/records?limit=100',token=TOKEN)
            page.route('**/api/desk/projections?*',lambda route:route.fulfill(json={'projections':[],'page':{'offset':0,'limit':50,'total':0,'has_more':False}}))
            page.reload(wait_until='load');_normal_chair(page);expect(win.get_by_text('No activity yet',exact=True)).to_be_visible();shot('empty')
            (ROOT/f'.tmp/programs-group14/r2/activity-producer-{width}.json').write_text(json.dumps(tape,indent=2)+'\n')
            if width==1440 and os.environ.get('HOLDSPEAK_RECORD_ACTIVITY')=='1':
                folder=ROOT/'web/src/pages/cores/__tests__/fixtures';folder.mkdir(exist_ok=True)
                (folder/'activity-grammar.json').write_text(json.dumps(tape,indent=2)+'\n')
            browser.close()
    finally:server.stop()
