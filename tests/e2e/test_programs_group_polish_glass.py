"""Long, path-first lists and the Programs reading seat use real wire shapes."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.tmp/evidence-shots/programs-group14'
TOKEN = 'programs-group-polish'
LONG_NAME = ('web/src/desk/programs/ProgramWindow.tsx: keep the selected step and its saved revision together '
             'while a newer answer arrives and the owner reads the next requirement before starting work')


@pytest.mark.parametrize('width', [1440, 393])
@pytest.mark.timeout(180)
def test_long_program_deck_and_project_columns(tmp_path, monkeypatch, width):
    from playwright.sync_api import sync_playwright, expect
    _ensure_build()
    OUT.mkdir(parents=True, exist_ok=True)
    tape = json.loads((ROOT / 'web/src/desk/programs/__fixtures__/program.live10.json').read_text())
    program = copy.deepcopy(tape['advanced'])
    program['steps'][1]['title'] = program['steps'][1]['brief'] = LONG_NAME
    program['steps'][2]['title'] = LONG_NAME.replace('ProgramWindow.tsx', 'ProgramSteps.tsx')
    listing = copy.deepcopy(tape['advanced_list'])
    template = next(row for row in listing['programs'] if row['id'] == program['id'])
    listing['programs'] = [{**template, 'id': program['id'] if i == 0 else f'long-{i}', 'title': LONG_NAME, 'place': f'/tmp/long-{i}'} for i in range(50)]
    wire = json.loads((ROOT / 'web/src/pages/cores/__tests__/fixtures/projects/recorded.json').read_text())
    projects = [{**wire['gets']['/api/projects']['projects'][1], 'id': f'long-project-{i}', 'name': LONG_NAME} for i in range(50)]
    room = wire['gets'][f"/api/projects/{wire['vendor']}/room"]
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    faults = []
    phase = os.environ.get('POLISH_PHASE', 'after')
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={'width': width, 'height': 900 if width == 1440 else 852}, reduced_motion='reduce')
            page.route('**/api/projects', lambda route: route.fulfill(json={'projects': projects}))
            page.route('**/api/projects/*/room', lambda route: route.fulfill(json=room))
            page.route('**/api/programs', lambda route: route.fulfill(json=listing))
            page.route(f"**/api/programs/{program['id']}", lambda route: route.fulfill(json=program))
            page.goto(f'{base}/?token={TOKEN}', wait_until='load')
            _api(page, 'PUT', '/api/setup/onboarding', {'disposition': 'completed'}, token=TOKEN)
            def open_window(app):
                clear_hub_windows_http(base, TOKEN)
                _api(page, 'POST', f'/api/desk/windows/surface-{app}/open', {}, token=TOKEN)
                if width == 1440:
                    _api(page, 'POST', f'/api/desk/windows/surface-{app}/set_geometry', {'rect': {'x': '-1/2 + 100', 'y': '-1/2 + 80', 'w': '900px', 'h': '600px'}}, token=TOKEN)
                page.reload(wait_until='load')
                _normal_chair(page)
                return page.locator(f'#surface-{app}')
            def shot(win, name):
                _settle(page)
                shot_width = 520 if name.startswith('projects-small') else 900 if width == 1440 else 393
                page.screenshot(path=str(OUT / f'{name}-{shot_width}-{phase}.png'))
                metrics = win.evaluate('''el => { const body=el.querySelector('.desk-surface-body');
                  return {body: [body.clientWidth,body.scrollWidth,body.clientHeight,body.scrollHeight],
                    heads:[...el.querySelectorAll('.surface-pane-inspector-head strong')].map(e=>({text:e.textContent,width:e.clientWidth,scroll:e.scrollWidth})),
                    wells:[...el.querySelectorAll('.surface-preference-well')].map(e=>({height:e.clientHeight,scroll:e.scrollHeight})),
                    columns:[...el.querySelectorAll('[role=columnheader]')].map(e=>e.textContent)}; }''')
                (OUT / f'{name}-{width}-{phase}.json').write_text(json.dumps(metrics, indent=2))
                if metrics['body'][1] > metrics['body'][0] + 1: faults.append((name, 'body overflow', metrics))
                if any(head['scroll'] > head['width'] + 1 for head in metrics['heads']): faults.append((name, 'heading overflow', metrics))
                return metrics
            win = open_window('projects')
            expect(win.get_by_test_id('projects-row')).to_have_count(50)
            facts = shot(win, 'projects-long-list')
            if 'Next' in facts['columns'] or 'Updated' in facts['columns'] or 'State' in facts['columns']:
                faults.append(('projects', 'columns with no values', facts))
            if win.get_by_role('region', name='Projects facts', exact=True).count(): faults.append(('projects', 'unselected inspector'))
            win.get_by_test_id('projects-row').first.click()
            shot(win, 'projects-long-selected')
            if width == 1440:
                _api(page, 'POST', '/api/desk/windows/surface-projects/set_geometry', {'rect': {'x': '-1/2 + 100', 'y': '-1/2 + 80', 'w': '520px', 'h': '360px'}}, token=TOKEN)
                shot(win, 'projects-small')
                _api(page, 'POST', '/api/desk/windows/surface-projects/close', {}, token=TOKEN)
                _api(page, 'POST', '/api/desk/windows/surface-projects/open', {}, token=TOKEN)
                _api(page, 'POST', '/api/desk/windows/surface-projects/set_geometry', {'rect': {'x': '-1/2 + 100', 'y': '-1/2 + 80', 'w': '520px', 'h': '360px'}}, token=TOKEN)
                page.reload(wait_until='load')
                _normal_chair(page)
                expect(win.get_by_test_id('projects-status')).to_contain_text('50 projects')
                shot(win, 'projects-small-overview')
            win.get_by_role('button', name='New project', exact=True).click()
            setup = page.locator('#surface-project-setup')
            expect(setup).to_be_visible()
            if width == 1440:
                _api(page, 'POST', '/api/desk/windows/surface-project-setup/set_geometry', {'rect': {'x': '-1/2 + 100', 'y': '-1/2 + 80', 'w': '900px', 'h': '600px'}}, token=TOKEN)
            shot(setup, 'projects-form')
            win = open_window('programs')
            expect(win.get_by_role('tab', name='Now', exact=True)).to_be_visible()
            facts = shot(win, 'programs-now')
            filename = win.locator('.surface-path-part').filter(has_text='ProgramSteps.tsx:')
            expect(filename).to_be_visible()
            assert filename.evaluate('''el=>{const range=document.createRange();range.selectNodeContents(el);const lines=[...range.getClientRects()];return lines.length===1 && lines[0].width<=el.getBoundingClientRect().width+1;}'''), 'Then must keep the filename on one line when it fits'
            assert any('web/src/' in head['text'] for head in facts['heads']), facts
            if width == 1440 and 'Program' not in facts['columns']: faults.append(('programs', 'missing column head'))
            # The complete sentence belongs to the heading; facts do not repeat its brief.
            repeats = win.locator('.surface-list-pane-preview').get_by_text(LONG_NAME, exact=True).count()
            if repeats > 1: faults.append(('programs', 'repeated step sentence', repeats))
            if not facts['wells']: faults.append(('programs', 'no scrollable reading well'))
            win.get_by_role('button', name='New program', exact=True).click()
            expect(win.get_by_role('region', name='New program', exact=True)).to_be_visible()
            shot(win, 'programs-form')
            win.get_by_role('button', name='Cancel', exact=True).click()
            page.unroute('**/api/programs')
            page.route('**/api/programs', lambda route: route.fulfill(json={**listing, 'programs': []}))
            page.reload(wait_until='load')
            _normal_chair(page)
            shot(win, 'programs-empty')
            expect(win.get_by_text('No programs yet', exact=True)).to_be_visible()
            shot(win, 'programs-empty')
            page.unroute('**/api/programs')
            page.route('**/api/programs', lambda route: route.fulfill(status=503, json={'detail': 'Programs not read'}))
            page.reload(wait_until='load')
            _normal_chair(page)
            expect(win.get_by_role('alert')).to_be_visible()
            shot(win, 'programs-failure')
            browser.close()
    finally:
        server.stop()
    assert not faults, faults


@pytest.mark.parametrize('width', [1440, 393])
@pytest.mark.timeout(180)
def test_collection_name_seats(tmp_path, monkeypatch, width):
    from playwright.sync_api import sync_playwright, expect
    _ensure_build()
    OUT.mkdir(parents=True, exist_ok=True)
    decisions = json.loads((ROOT / 'web/src/test/wire/decisions.honest-faces.wire.json').read_text())['wire']
    template = decisions['decisions'][0]
    decisions['decisions'] = [{**template, 'id': f'long-decision-{i}', 'record_id': None, 'text': LONG_NAME} for i in range(50)]
    decisions['page']['total'] = 50
    source = (ROOT / 'web/src/desk/recordings/__fixtures__/recordings.list.ts').read_text()
    recordings = json.loads(source[source.index('= {') + 2:].strip().removesuffix(';'))
    template = next(row for row in recordings['recordings'] if row['state'] == 'ready')
    recordings['recordings'] = [{**template, 'id': f'long-recording-{i}', 'title': LONG_NAME} for i in range(50)]
    program = json.loads((ROOT / 'web/src/desk/needs/__fixtures__/needs_you.rows.json').read_text())['program']['steps'][0]['gets']
    needs = copy.deepcopy(program['/api/desk/needs-you?fresh=1'])
    template = needs['items'][0]
    needs['items'] = [{**template, 'id': f"program:{template['program']['programId']}:long-step-{i}:merge", 'ref': f"program:{template['program']['programId']}:long-step-{i}:merge", 'program': {**template['program'], 'stepId': f'long-step-{i}'}, 'title': LONG_NAME} for i in range(50)]
    needs['members'] = [{'kind': 'attention', 'ref': row['ref']} for row in needs['items']]
    needs['count'] = 50
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={'width': width, 'height': 900 if width == 1440 else 852}, reduced_motion='reduce')
            for path, body in program.items():
                page.route(f'**{path}', lambda route, _request, body=body: route.fulfill(json=body))
            page.route('**/api/desk/needs-you*', lambda route: route.fulfill(json=needs))
            page.route('**/api/decisions/ledger?*', lambda route: route.fulfill(json=decisions))
            page.route('**/api/recordings', lambda route: route.fulfill(json=recordings))
            page.goto(f'{base}/?token={TOKEN}', wait_until='load')
            _api(page, 'PUT', '/api/setup/onboarding', {'disposition': 'completed'}, token=TOKEN)
            for app, count_id in [('decisions', 'decisions-row'), ('recordings', 'recordings-row'), ('needs', 'needs-row')]:
                clear_hub_windows_http(base, TOKEN)
                window_id = 'chair:needs' if app == 'needs' else f'surface-{app}'
                window_body = {'kind': 'chair', 'ref': 'needs'} if app == 'needs' else {}
                _api(page, 'POST', f'/api/desk/windows/{window_id}/open', window_body, token=TOKEN)
                if width == 1440:
                    _api(page, 'POST', f'/api/desk/windows/{window_id}/set_geometry', {'rect': {'x': '-1/2 + 100', 'y': '-1/2 + 80', 'w': '900px', 'h': '600px'}}, token=TOKEN)
                page.reload(wait_until='load')
                _normal_chair(page)
                win = page.locator(f'[id="{window_id}"]')
                expect(win.get_by_test_id(count_id)).to_have_count(50)
                for state in ['list', 'selected']:
                    if state == 'selected': win.get_by_test_id(count_id).first.click()
                    _settle(page)
                    page.screenshot(path=str(OUT / f'{app}-long-{state}-{900 if width == 1440 else 393}-after.png'))
                    seat = win.evaluate('''el=>({rect:el.getBoundingClientRect().toJSON(),scrolls:[...document.querySelectorAll('*')].filter(e=>e.scrollLeft && (e.contains(el) || el.contains(e))).map(e=>({tag:e.tagName,cls:e.className,left:e.scrollLeft,width:e.clientWidth,scroll:e.scrollWidth}))})''')
                    (OUT / f'{app}-{state}-{width}-seat.json').write_text(json.dumps(seat, indent=2))
                    if width == 393: assert seat['rect']['x'] >= -1 and seat['rect']['right'] <= width + 1 and not seat['scrolls'], seat
                    assert win.evaluate('''el=>{const body=el.querySelector('.desk-surface-body, .chair-window-body');return body.scrollWidth<=body.clientWidth+1 && body.scrollHeight<=body.clientHeight+1;}''')
                    assert win.locator('[data-object-id][aria-selected="true"]').count() == (1 if state == 'selected' else 0)
                    # A path-first name retains useful words and its full hover name.
                    names = win.locator('.object-list-selection-name [title]')
                    assert not names.evaluate_all("els => els.some(e=>e.textContent.trim()==='…')")
                    if app in ['decisions', 'recordings'] and state == 'list':
                        expect(win.get_by_role('region', name=f'{app.title()} facts', exact=True)).to_have_count(0)
                    if app == 'needs':
                        expect(win.get_by_test_id('arrival-display')).to_contain_text('50')
            browser.close()
    finally:
        server.stop()
