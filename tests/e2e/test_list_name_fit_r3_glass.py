"""Kit name seats: real columns, middle cuts and live font metrics."""
import json
import os
from pathlib import Path
import pytest
from . import open_rig
from .glass_infra import _api, _boot, _ensure_build, _settle
from .test_people_os_grammar_glass import TOKEN
from .test_lists_wave14_glass import IDENTIFIER
from .list_name_fit_rig import seed_names, scenes, open_window

# Canvas and geometry use the rendered cell and its actual computed font.
# No test substitutes a character width or a clientWidth value.
READ_NAME = """el=>{const style=getComputedStyle(el),canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');ctx.font=`${style.fontStyle} ${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;const gap=parseFloat(style.letterSpacing)||0,measure=text=>ctx.measureText(text).width+Math.max(0,text.length-1)*gap;const value=el.title.replace(/\\s+/g,' ').trim(),shown=el.textContent,parts=shown.split('…');const cell=el.closest('[data-col=name]'),row=el.closest('[data-object-id]'),a=cell.getBoundingClientRect(),b=row.getBoundingClientRect();return {value,shown,width:el.clientWidth,ink:measure(shown),spare:el.clientWidth-measure(shown),maxGlyph:Math.max(...[...value].map(measure)),middle:parts.length===2&&!!parts[0]&&!!parts[1]&&value.startsWith(parts[0])&&value.endsWith(parts[1]),full:shown===value,cell:a.toJSON(),row:b.toJSON(),font:style.font};}"""

@pytest.mark.parametrize('width',[1440,393])
@pytest.mark.timeout(300)
def test_list_name_seat(tmp_path,monkeypatch,width):
    from playwright.sync_api import sync_playwright, expect
    _ensure_build()
    server,base=_boot(tmp_path,monkeypatch,token=TOKEN)
    monkeypatch.setattr(open_rig,'TOKEN',TOKEN)
    phase=os.environ.get('LISTS_R3_PHASE','after')
    out=Path(__file__).resolve().parents[2]/'.tmp/evidence-shots/lists14/r3'
    out.mkdir(parents=True,exist_ok=True)
    failures=[]; measures={}
    def check(rule,ok,facts):
        if not ok: failures.append({'rule':rule,**facts})
    def fitted(title,rule,where):
        facts=title.evaluate(READ_NAME);measures[where]=facts
        check(rule,facts['ink']<=facts['width']+1 and (facts['full'] or facts['middle']) and (facts['full'] or facts['spare']<=facts['maxGlyph']+2),{'where':where,**facts})
        return facts
    try:
        people=seed_names(tmp_path,base,monkeypatch)
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            page=browser.new_page(viewport={'width':width,'height':900 if width==1440 else 852},reduced_motion='reduce')
            page.set_default_timeout(15000)
            page.goto(f'{base}/?token={TOKEN}',wait_until='load')
            for app,win,grid in scenes(page,base,width,people):
                # The long identifier is produced, not patched into a face.
                # Room and Needs you can read their names after the first row.
                page.wait_for_function("([selector,name])=>[...document.querySelectorAll(selector)].some(el=>el.title.includes(name))",arg=[f'[id="{win.get_attribute("id")}"] .object-list-selection-title',IDENTIFIER])
                title=grid.locator(f'.object-list-selection-title[title*="{IDENTIFIER}"]').first
                title.scroll_into_view_if_needed();_settle(page)
                # Read by full title: the rendered name may have a middle cut.
                title=grid.locator(f'.object-list-selection-title[title*="{IDENTIFIER}"]').first
                facts=fitted(title,2,f'{app}-identifier')
                if app=='people' and width==393:
                    row=title.locator('xpath=ancestor::*[@data-object-id][1]')
                    visible=row.locator('[role=gridcell]:visible').count()
                    check(3,visible==1 and facts['cell']['width']>=facts['row']['width']-2 and facts['spare']<=facts['maxGlyph']+2,{'where':'sole-column',**facts})
                page.screenshot(path=str(out/f'{app}-{900 if width==1440 else 393}-{phase}.png'))
            # A later FontFace registration must update a fixed-size name seat.
            probe_name='W'*96+'RevisionEnd'
            person=_api(page,'POST','/api/people/relationships',{'display_name':probe_name,'relationship_kind':'peer'},token=TOKEN)['relationship']
            win=open_window(page,base,'surface-people',width)
            row=win.locator(f'[data-object-id="{person["id"]}"]');row.click()
            title=row.locator('.object-list-selection-title')
            font_url=page.evaluate("()=>performance.getEntriesByType('resource').map(x=>x.name).find(x=>x.includes('inter-latin-600-normal')&&x.includes('.woff2'))")
            assert font_url,'The real Inter webfont was not loaded'
            style=page.add_style_tag(content='.object-list-selection-title { font-family: ListNameSwap, monospace !important; line-height: 20px !important; }')
            # Exercise a real window resize to measure the fallback face first.
            if width==1440:
                for size in (880,900):
                    _api(page,'POST','/api/desk/windows/surface-people/set_geometry',{'rect':{'x':'-1/2 + 100','y':'-1/2 + 80','w':f'{size}px','h':'600px'}},token=TOKEN);_settle(page)
            else:
                page.set_viewport_size({'width':width+24,'height':852});_settle(page)
                page.set_viewport_size({'width':width,'height':852});_settle(page)
            old=title.evaluate(READ_NAME)
            page.evaluate("""async url=>{const face=new FontFace('ListNameSwap',await (await fetch(url)).arrayBuffer(),{weight:'600'});document.fonts.add(face);await face.loaded;await document.fonts.ready;}""",font_url)
            _settle(page)
            now=title.evaluate(READ_NAME);measures['font-swap']={'before':old,'after':now}
            check(1,now['ink']<=now['width']+1 and (now['full'] or now['spare']<=now['maxGlyph']+2),{'where':'webfont-swap',**now})
            style.evaluate('el=>el.remove()')
            # An actual column-set change must use the newly available width.
            field=win.get_by_role('textbox',name='Find a person',exact=True)
            field.fill(IDENTIFIER);_settle(page)
            title=win.locator('.object-list-selection-title').first
            expect(title).to_have_attribute('title',IDENTIFIER)
            fitted(title,1,'column-set-change')
            # A font-family change with no window or row-size change also refits.
            font_style=page.add_style_tag(content='.object-list-selection-title {font-family: monospace !important;}')
            _settle(page);fitted(title,1,'font-family-change')
            font_style.evaluate('el=>el.remove()')
            browser.close()
    finally:
        (out.parent/f'r3-measures-{width}-{phase}.json').write_text(json.dumps({'measures':measures,'failures':failures},indent=2))
        server.stop()
    assert not failures,json.dumps(failures,indent=2)
