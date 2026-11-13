"""Wave 14 repairs on seeded apps; a small, named capture inventory."""
import json
import os
import re
from pathlib import Path
import pytest
from playwright.sync_api import expect
from .glass_infra import clear_hub_windows_http, _normal_chair, _settle
from .test_desk_sweep import TOKEN, _Case, _hub_open, _page, desk, pw_browser
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.tmp/evidence-shots/kit14/r2'
APPS={'agents':'conductor','people':'surface-people','meetings':'surface-meetings','projects':'surface-projects','decisions':'surface-decisions','recordings':'surface-recordings','programs':'surface-programs','needs':'chair:needs','automations':'surface-workbenches','today':'pullout:intelligence:desk','calls':'surface-calls','speak':'surface-dictation','room':'surface-project-memory'}
def shot(page,item,app,state,width):
 OUT.mkdir(parents=True,exist_ok=True);_settle(page)
 phase='before' if os.environ.get('KIT14_R2_BEFORE') else 'after'
 page.screenshot(path=str(OUT/f'{item}-{app}-{state}-{phase}-{width}.png'))
@pytest.mark.parametrize('width',[900,393])
@pytest.mark.parametrize('app',APPS)
def test_list_audit(desk,pw_browser,width,app):
 base=desk['base'];wid=APPS[app];clear_hub_windows_http(base,TOKEN)
 if app!='today':_hub_open(base,wid,f"project:{desk['room']}" if app=='room' else None,window=width==900)
 ctx,page,errors,requests=_page(pw_browser,width,base)
 from .test_kit_polish_wave14_glass import _before
 _before(page)
 if app=='recordings':
  from .test_recordings_os_grammar_glass import _recorded
  page.route(re.compile(r'/api/recordings(?:\?.*)?$'),lambda route:route.fulfill(json=_recorded('recordings.list')))
  page.route('**/api/recordings/*',lambda route:route.fulfill(json=_recorded('recording.ready')))
 if app=='calls':
  tape=json.loads((ROOT/'web/src/desk/calls/__fixtures__/calls.face.json').read_text())
  page.route(re.compile(r'/api/calls(?:\?.*)?$'),lambda route:route.fulfill(json=tape['recent']))
  page.route('**/api/calls/call-face',lambda route:route.fulfill(json=tape['detail']))
 if app=='speak':
  wire=json.loads((ROOT/'web/src/test/wire/dictation-journal.wire.json').read_text())['wire']
  page.route('**/api/dictation/journal?*',lambda route:route.fulfill(json=wire))
 try:
  page.goto(f'{base}/?token={TOKEN}',wait_until='load');_normal_chair(page)
  if app=='today':page.locator(".desk-dock-launch[aria-label^='Today']").first.click()
  case=_Case(page,base,wid,errors,requests);case.settle();win=page.locator(f'[id="{wid}"]');expect(win).to_be_visible()
  rows=win.locator('.object-list-row[data-object-id]:visible')
  if width==393 and not rows.count():
   back=win.get_by_role('button',name='Back',exact=True)
   if back.count() and back.is_visible():back.click();_settle(page)
  expect(rows.first).to_be_visible()
  if width==900:rows.first.click();_settle(page)
  shot(page,'A',app,'list',width)
  if not os.environ.get('KIT14_R2_BEFORE') and app=='speak' and width==393:
   setup=win.get_by_test_id('speak-setup-facts').bounding_box()
   live=win.get_by_test_id('speak-live').bounding_box()
   assert setup['width']>win.bounding_box()['width']*.8 and setup['y']>live['y']+live['height'],(setup,live)
  if not os.environ.get('KIT14_R2_BEFORE') and app in {'people','needs'}:
   shot(page,'5',app,'counted-rows',width)
   for well in win.locator('.object-list-rows:visible').all():
    box=well.bounding_box(); boxes=[row.bounding_box() for row in well.locator('.object-list-row').all()]
    visible=[row for row in boxes if row and row['y']<box['y']+box['height']-1 and row['y']+row['height']>box['y']]
    if boxes and boxes[-1]['y']+boxes[-1]['height']>box['y']+box['height']+1:
     assert visible and visible[-1]['y']+visible[-1]['height']>box['y']+box['height']+1,(app,box,visible)
  if not os.environ.get('KIT14_R2_BEFORE') and app=='needs':
   shot(page,'10',app,'verbs',width)
   for bar in win.locator('.kit-toolbar-verbs:visible,.surface-pane-actions:visible').all():
    buttons=bar.locator('button.btn:visible').all()
    centers=[b.bounding_box()['y']+b.bounding_box()['height']/2 for b in buttons]
    assert not centers or max(centers)-min(centers)<5,(app,width,centers)
  if not os.environ.get('KIT14_R2_BEFORE'):
   strip=win.locator('.desk-surface-foot > .kit-statusbar');expect(strip).to_be_visible()
   if app in {'meetings','today'}:shot(page,'12',app,'strip',width)
  # A declared state with words may never disappear from a visible row.
  for row in win.locator('.object-list-row[data-object-id]:visible').all():
   state=row.locator('[data-col="state"]')
   if state.count() and state.inner_text().strip():expect(state).to_be_visible()
  # Identity uses its available cell; short words do not shrink that seat.
  for name in win.locator('.object-list-selection-name:visible').all():
   assert name.evaluate("el=>el.closest('[data-col=name]').getBoundingClientRect().width-el.getBoundingClientRect().width<80")
 finally:ctx.close()
@pytest.mark.parametrize('width',[900,393])
def test_live_seats(desk,pw_browser,width):
 base=desk['base'];clear_hub_windows_http(base,TOKEN);_hub_open(base,'surface-live',None,window=width==900)
 ctx,page,errors,requests=_page(pw_browser,width,base)
 wire=json.loads((ROOT/'web/src/test/wire/live.actions.wire.json').read_text())['wire']
 page.route_web_socket('**/ws*',lambda socket:None);page.route('**/api/state',lambda route:route.fulfill(json=wire['state']))
 try:
  page.goto(f'{base}/?token={TOKEN}',wait_until='load');_normal_chair(page);_Case(page,base,'surface-live',errors,requests).settle()
  win=page.locator('#surface-live');well=win.get_by_test_id('live-transcript');expect(well).to_be_visible()
  shot(page,'B','live','transcript',width)
  shot(page,'C','live','microphone',width)
  if width==900:
   line=well.locator('li').first;time=line.locator('time').bounding_box();words=line.locator('p').bounding_box()
   assert abs(words['y']-time['y'])<5,(time,words)
  if width==393:
   toolbar=win.get_by_test_id('live-toolbar');buttons=toolbar.locator(':scope > .kit-toolbar-verbs button:visible')
   ys=[round(b.bounding_box()['y']) for b in buttons.all()]
   assert len(set(ys))<=1,ys
   assert not toolbar.get_by_role('combobox',name='Microphone',exact=True).is_visible()
   toolbar.get_by_role('button',name='Actions ▾',exact=True).click()
   page.get_by_role('menuitem',name='Microphone',exact=True).hover()
   expect(page.get_by_role('menuitem',name='Settings…',exact=True)).to_be_visible()
   shot(page,'C','live','microphone',width)
   page.keyboard.press('Escape')
 finally:ctx.close()


def capture_state(page,win,app,state,width):
 mapping={
  ('people','brief-last'):['5'],
  ('agents','permission-held'):['23','19'],('agents','remove-question'):['23'],
  ('today','agenda-failed'):['19'],('today','prepared-suggestion'):['10'],('today','empty-day'):['12'],
  ('calls','call-failed'):['19'],('calls','live'):['B'],
  ('live','recording'):['16'],('live','caught'):['20'],('live','project-added'):['14'],('live','stopped'):['14'],
 }
 items=mapping.get((app,state),[])
 if not items:return
 _settle(page)
 if '19' in items:
  notice=win.locator('.surface-list-notice').first
  expect(notice).to_be_visible()
  toolbar=win.locator('.object-list-toolbar').first.bounding_box();box=notice.bounding_box()
  assert box['y']>=toolbar['y']+toolbar['height']-1,(toolbar,box)
 if '23' in items:
  safe=win.get_by_role('button',name='Deny' if state=='permission-held' else 'Cancel',exact=True)
  expect(safe).to_be_focused()
  assert safe.evaluate("el=>parseFloat(getComputedStyle(el).outlineWidth)>=2")
 if '16' in items:
  listening=win.get_by_test_id('live-listening');who=win.get_by_test_id('live-listening-who')
  if who.count():
   assert listening.evaluate("el=>el.closest('.kit-statusbar-item') !== document.querySelector('[data-testid=live-listening-who]').closest('.kit-statusbar-item')")
 if '20' in items and width>620:
  expect(win.get_by_test_id('live-transcript')).to_be_visible()
  expect(win.get_by_test_id('live-caught')).to_be_visible()
 for item in items:shot(page,item,app,state,900 if width>620 else 393)
