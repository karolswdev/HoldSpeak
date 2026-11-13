"""Whole form rows, selected groups and fitted names on real-produced lists."""
from pathlib import Path
import os
import pytest
from . import open_rig
from .glass_infra import _api, _boot, _ensure_build, _settle, clear_hub_windows_http
from .test_people_os_grammar_glass import TOKEN, _open
from .test_lists_wave14_glass import LONG_NAME, IDENTIFIER


@pytest.mark.parametrize("width", [1440, 393])
def test_list_editors_and_long_names_fit_their_seats(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect
    from holdspeak.db import get_database
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setattr(open_rig, "TOKEN", TOKEN)
    phase=os.environ.get("LISTS_R2_PHASE","after")
    shots=Path(__file__).resolve().parents[2] / f".tmp/evidence-shots/lists14/{'r2' if phase=='after' else 'r2-before'}"
    shots.mkdir(parents=True,exist_ok=True)
    failures=[]
    def check(item, ok, detail):
        if not ok: failures.append(f"Item {item}: {detail}")
    try:
        seed=open_rig._seed(tmp_path / "home",base)
        people=[]
        for i in range(50):
            name=LONG_NAME if i==0 else IDENTIFIER if i==1 else f"Platform reviewer {i:02d} — {LONG_NAME}"
            people.append(open_rig._http(base,"POST","/api/people/relationships",{"display_name":name,"relationship_kind":"peer"})["relationship"])
            get_database().workbenches.upsert(workbench_id=f"long-automation-{i}",name=name,instruction="Prepare the architecture review.")
        for person in people[:2]:
            open_rig._http(base,"POST",f"/api/people/relationships/{person['id']}/one-on-ones",{})
        priya=seed["priya"]
        for text in ("Send the API migration estimate","Send the rollout dates"):
            open_rig._http(base,"POST",f"/api/people/relationships/{priya}/owed",{"body":text})
        for i in range(47):
            target_review=f"Review architecture change {i:02d}: {LONG_NAME}"
            request=open_rig._http(base,"POST",f"/api/people/relationships/{priya}/requests",{"body":target_review})["request"]
            open_rig._http(base,"POST",f"/api/people/requests/{request['id']}/accept",{})
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            clear_hub_windows_http(base,TOKEN)
            page=browser.new_page(viewport={"width":width,"height":900 if width==1440 else 852},reduced_motion="reduce")
            page.set_default_timeout(15000)
            _open(page,base)
            win=page.locator("#surface-people")
            def geometry(wid):
                if width==1440:
                    _api(page,"POST",f"/api/desk/windows/{wid}/set_geometry",{"rect":{"x":"-1/2 + 100","y":"-1/2 + 80","w":"900px","h":"600px"}},token=TOKEN)
                _settle(page)
            def shot(state):
                _settle(page)
                page.screenshot(path=str(shots/f"{state}-{900 if width==1440 else 393}.png"))
            def heading(name, item):
                head=win.locator('.surface-pane-inspector-head').first
                facts=win.locator('.surface-inspector-facts').first
                title=head.locator('strong').first
                result=title.evaluate("""el=>{const s=getComputedStyle(el),r=el.getBoundingClientRect();return {text:el.innerText,lines:r.height/parseFloat(s.lineHeight),fits:el.scrollWidth<=el.clientWidth+1};}""")
                check(item,result['fits'] and result['lines']<=2.1 and (result['text'].endswith('…') or ' '.join(result['text'].split())==name),result)
                full=facts.locator('.gadget-row').filter(has=page.get_by_text("Name",exact=True))
                check(3,full.count()==1 and name in full.inner_text() if full.count() else False,"Full Name fact missing")
            def verb(name):
                direct=win.get_by_role('button',name=name,exact=True)
                if direct.is_visible(): direct.click()
                else:
                    win.get_by_role('button',name='Actions ▾',exact=True).click()
                    page.get_by_role('menu').last.get_by_role('menuitem',name=name,exact=True).click()
            for i,state in ((0,"path"),(1,"identifier")):
                row=win.locator(f'[data-object-id="{people[i]["id"]}"]')
                row.click()
                win.get_by_test_id('people-summary-name').wait_for()
                well=win.get_by_role('grid',name='People',exact=True).locator('.object-list-rows')
                well.evaluate("(el,id)=>{const row=[...el.querySelectorAll('[data-object-id]')].find(row=>row.dataset.objectId===id);el.scrollTop+=row.getBoundingClientRect().top-el.getBoundingClientRect().top;}",people[i]["id"])
                _settle(page)
                if width==393:
                    check(5,win.get_by_role('columnheader',name='Open with them',exact=True).count()==0,"Empty Open with them column is declared")
                    name_box=win.locator('[data-object-id] [data-col="name"]').last.bounding_box()
                    check(5,bool(name_box and name_box['width']>=win.get_by_role('grid',name='People',exact=True).bounding_box()['width']-2),name_box)
                heading(people[i]['display_name'],2 if i else 3)
                shot(f"{2 if i else 3}-people-{state}")
                row.press('Enter')
                person_win=page.locator(f'[id="pullout:people:{people[i]["id"]}"]')
                person_win.get_by_test_id('person-window').wait_for()
                geometry(f"pullout:people:{people[i]['id']}")
                title=person_win.locator('.desk-window-title')
                shown=title.inner_text();full=title.get_attribute('title')
                check(7,title.evaluate('el=>el.scrollWidth<=el.clientWidth+1') and bool(shown.strip('…')) and (shown==full or shown.endswith('…')),(shown,full))
                chrome=person_win.evaluate("""win=>{const box=win.getBoundingClientRect(),back=win.querySelector('.desk-gadget-close').getBoundingClientRect();return {left:box.left,right:box.right,backLeft:back.left,backRight:back.right};}""")
                check(7,chrome['left']>=0 and chrome['right']<=width+1 and chrome['backLeft']>=chrome['left']-1 and chrome['backRight']<=chrome['right']+1,chrome)
                if state=='path' and shown!=full:
                    prefix=shown.removesuffix('…').rstrip()
                    check(7,full.startswith(prefix) and (prefix.endswith(('/', '.', '_', ':', '-')) or full[len(prefix):].startswith(' ')),(shown,full))
                figure=person_win.locator('.surface-mast-figures > div').first
                check(6,figure.is_visible() and figure.locator('dd').inner_text()=='1',"Saved 1:1 figure hidden")
                shot(f"6-7-person-title-{state}")
                _api(page,'POST',f"/api/desk/windows/pullout:people:{people[i]['id']}/close",{},token=TOKEN)
            row=win.locator(f'[data-object-id="{priya}"]');row.click();row.press('Enter')
            win=page.locator(f'[id="pullout:people:{priya}"]')
            win.get_by_test_id('people-composer').wait_for()
            geometry(f"pullout:people:{priya}")
            ledger=win.get_by_role('grid',name='Commitments',exact=True)
            selected=ledger.get_by_role('row',name=target_review,exact=False)
            selected.click();verb('Add…');_settle(page)
            bounds=selected.evaluate("""row=>{const well=row.closest('.object-list-rows'),group=row.closest('.object-list-group')?.querySelector('.object-list-group-label'),r=row.getBoundingClientRect(),w=well.getBoundingClientRect(),g=group?.getBoundingClientRect();return {selected:row.getAttribute('aria-selected'),row:r.toJSON(),well:w.toJSON(),group:g?.toJSON(),hit:document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest('[data-object-id]')===row};}""")
            r,w,g=bounds['row'],bounds['well'],bounds['group']
            check(4,bounds['selected']=='true' and bounds['hit'] and r['top']>=w['top']-1 and r['bottom']<=w['bottom']+1 and g and g['top']>=w['top']-1 and g['bottom']<=r['top']+1,bounds)
            shot('4-person-ledger-add')
            _api(page,'POST',f"/api/desk/windows/pullout:people:{priya}/close",{},token=TOKEN)
            _api(page,'POST','/api/desk/windows/surface-people/close',{},token=TOKEN)
            page.get_by_role('button',name='Go',exact=True).first.click()
            page.locator("nav[aria-label='Go menu']").get_by_role('menuitem',name='Automations',exact=True).evaluate('el=>el.click()')
            win=page.locator('#surface-workbenches');win.locator('[data-object-id]').first.wait_for();geometry('surface-workbenches')
            for i,state in ((0,'path'),(1,'identifier')):
                win.locator(f'[data-object-id="long-automation-{i}"]').click();_settle(page)
                heading(people[i]['display_name'],2 if i else 3)
                shot(f"{2 if i else 3}-automations-{state}")
            verb('Edit')
            form=win.get_by_test_id('automation-setup')
            form.get_by_role('combobox',name='Do kind').select_option('run_program')
            fields=form.locator(':scope > .surface-inspector-fields')
            for state,end in (('top',False),('bottom',True)):
                if end: fields.evaluate('el=>{el.scrollTop=el.scrollHeight}')
                _settle(page)
                clipped=fields.evaluate(r"""el=>{const box=el.getBoundingClientRect(),clip=getComputedStyle(el).clipPath,numbers=clip.startsWith('inset(')?clip.slice(6,-1).split(/\s+/).map(parseFloat):[],top=box.top+(numbers[0]||0),bottom=box.bottom-(numbers[2]||0);return [...el.querySelectorAll(':scope > .surface-inspector-rows > .gadget-row')].flatMap(row=>{const b=row.getBoundingClientRect();return b.bottom>top+1&&b.top<bottom-1&&(b.top<top-1||b.bottom>bottom+1)?[row.innerText]:[]});}""")
                check(1,not clipped,clipped)
                actions=form.locator(':scope > .surface-inspector-actions')
                check(1,actions.get_by_role('button',name='Save',exact=True).is_visible(),"Save out of view")
                shot(f"1-automation-program-{state}")
            browser.close()
    finally: server.stop()
    assert not failures, '\n'.join(failures)
