"""Needs you selection grammar over recorded hub answers, on an isolated Desk."""
from __future__ import annotations
import json
import os
from pathlib import Path
import pytest
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http

TOKEN = 'needs-grammar'
ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / '.tmp/evidence-shots/os-grammar'

@pytest.mark.e2e
@pytest.mark.timeout(240)
def test_needs_states(tmp_path, monkeypatch):
    from playwright.sync_api import sync_playwright, expect
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    before = os.environ.get('NEEDS_GRAMMAR_BEFORE') == '1'
    fixture = ROOT / 'web/src/desk/needs/__fixtures__/needs_you.grammar.json'
    try:
        # Hook producer, isolated spool. No tmux keys or provider is used.
        import holdspeak.agent_context as context
        from holdspeak.agent_context import event_log, ingest_agent_hook_event
        spool = {'state_path': context.AGENT_CONTEXT_FILE, 'events_spool_dir': event_log.default_spool_dir()}
        for event, data in [('SessionStart', {'source': 'startup'}), ('UserPromptSubmit', {'prompt': 'Write the rollback runbook.'}),
                            ('Notification', {'notification_type': 'idle_prompt', 'message': 'Who owns the rollback runbook?'})]:
            ingest_agent_hook_event(agent='claude', payload={'session_id': 'needs-typed', 'cwd': str(tmp_path / 'home'),
                'hook_event_name': event, **data}, **spool)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            seed_page = browser.new_page()
            seed_page.goto(f'{base}/?token={TOKEN}', wait_until='load')
            typed = _api(seed_page, 'GET', '/api/desk/needs-you?fresh=1', token=TOKEN)
            sessions = _api(seed_page, 'GET', '/api/coders/sessions?include_ended=false', token=TOKEN)
            refused = seed_page.request.post(f'{base}/api/coders/claude%3Aneeds-typed/steer',
                headers={'Authorization': f'Bearer {TOKEN}'}, data={'text': 'Jordan', 'submit': True, 'kind': 'answer', 'wait_id': 'a-previous-wait'})
            assert refused.status == 409, refused.text()
            typed_refusal = {'status': refused.status, 'body': refused.json()}
            for sid, message, notification in [('needs-permission', 'Claude needs your permission to use Bash', 'permission_prompt'),
                                                ('needs-choice', 'Use the shared flag or an env var? Answer 1 for shared flag, 2 for env.', 'idle_prompt')]:
                for event, data in [('SessionStart', {'source': 'startup'}), ('UserPromptSubmit', {'prompt': 'Write the rollback runbook.'}),
                                    ('Notification', {'notification_type': notification, 'message': message})]:
                    ingest_agent_hook_event(agent='claude', payload={'session_id': sid, 'cwd': str(tmp_path / 'home'),
                        'hook_event_name': event, **data}, **spool)
            other_questions = _api(seed_page, 'GET', '/api/desk/needs-you?fresh=1', token=TOKEN)
            question_sessions = _api(seed_page, 'GET', '/api/coders/sessions?include_ended=false', token=TOKEN)
            folder = tmp_path / 'private-team-folder'
            folder.mkdir()
            note = _api(seed_page, 'POST', '/api/notes', {'title': 'Rollback runbook', 'body_markdown': 'Jordan owns the rollback runbook.', 'tags': []}, token=TOKEN)['note']
            dest = _api(seed_page, 'POST', '/api/channels/destinations', {'name': 'Private team folder', 'channel': 'file', 'folder': str(folder)}, token=TOKEN)['destination']
            prepared = _api(seed_page, 'POST', '/api/channels/sends', {'document_ref': f"note:{note['id']}", 'destination_id': dest['id']}, token=TOKEN)
            send_before = _api(seed_page, 'GET', '/api/desk/needs-you?fresh=1', token=TOKEN)
            sent = _api(seed_page, 'POST', '/api/channels/send', {'send_id': prepared['send']['id'], 'command_id': 'needs-grammar-send'}, token=TOKEN)
            send_after = _api(seed_page, 'GET', '/api/desk/needs-you?fresh=1', token=TOKEN)
            prepared_discard = _api(seed_page, 'POST', '/api/channels/sends', {'document_ref': f"note:{note['id']}", 'destination_id': dest['id']}, token=TOKEN)
            discard_before = _api(seed_page, 'GET', '/api/desk/needs-you?fresh=1', token=TOKEN)
            discarded = _api(seed_page, 'POST', f"/api/channels/sends/{prepared_discard['send']['id']}/discard", {}, token=TOKEN)
            discard_after = _api(seed_page, 'GET', '/api/desk/needs-you?fresh=1', token=TOKEN)
            _api(seed_page, 'POST', '/api/people/setup', {}, token=TOKEN)
            person = _api(seed_page, 'POST', '/api/people/relationships', {'display_name': 'Priya Raman'}, token=TOKEN)['relationship']
            request = _api(seed_page, 'POST', f"/api/people/relationships/{person['id']}/requests", {
                'body': 'Send Priya the rollout plan', 'visibility': 'shared_intent', 'source': {'kind': 'manual'}}, token=TOKEN)['request']
            _api(seed_page, 'POST', f"/api/people/requests/{request['id']}/accept", {}, token=TOKEN)
            promise_before = _api(seed_page, 'GET', '/api/desk/needs-you?fresh=1', token=TOKEN)
            promise = next(item for item in promise_before['items'] if item.get('source') == 'people_commitment')
            dismiss = next(verb for verb in promise['_doorCard']['lawful_verbs'] if verb['arguments'].get('verb') == 'dismiss')
            promise_path = f"/api/people/commitments/{dismiss['arguments']['commitment_id']}/transition"
            promise_answer = _api(seed_page, 'POST', promise_path, {'verb': 'dismiss'}, token=TOKEN)
            promise_after = _api(seed_page, 'GET', '/api/desk/needs-you?fresh=1', token=TOKEN)
            recorded = {'recordedBy': 'tests/e2e/test_needs_os_grammar_glass.py (hook ingest and file send, isolated hub)',
                    'typed': typed, 'sessions': sessions, 'typedRefusal': typed_refusal, 'questions': other_questions, 'questionSessions': question_sessions, 'send': {'before': send_before, 'answer': sent, 'after': send_after},
                    'discard': {'before': discard_before, 'answer': discarded, 'after': discard_after},
                    'promise': {'before': promise_before, 'path': promise_path, 'answer': promise_answer, 'after': promise_after}}
            recorded_text = json.dumps(json.loads(json.dumps(recorded).replace(str(tmp_path), '/tmp/needs-grammar')), indent=2) + '\n'
            (ROOT / '.tmp/needs-grammar-wire.json').write_text(recorded_text)
            if os.environ.get('HOLDSPEAK_WIRE_WRITE') == '1':
                fixture.write_text(recorded_text)
            seed_page.close()
            program = json.loads((ROOT / 'web/src/desk/needs/__fixtures__/needs_you.rows.json').read_text())['program']['steps'][0]['gets']['/api/desk/needs-you?fresh=1']
            send = json.loads((ROOT / 'web/src/desk/__tests__/fixtures/send-needs/needs-send.json').read_text())['needsYou']
            empty = json.loads((ROOT / 'web/src/desk/__tests__/fixtures/needsYou.recorded.json').read_text())['calendar']['quiet']['gets']['/api/desk/needs-you?fresh=1']
            for width in (1440, 393):
                for state, initial in [('empty', empty), ('fixed', program), ('typed', typed), ('send', discard_before)]:
                    clear_hub_windows_http(base, TOKEN)
                    page = browser.new_page(viewport={'width': width, 'height': 900 if width == 1440 else 852}, reduced_motion='reduce')
                    current = [initial]
                    presses = []
                    def needs_route(route):
                        if route.request.method == 'GET': route.fulfill(json=current[0])
                        else: route.fulfill(json={})
                    def discard_route(route):
                        presses.append(route.request.post_data_json)
                        current[0] = discard_after
                        route.fulfill(json=discarded)
                    page.route('**/api/desk/needs-you*', needs_route)
                    page.route('**/api/coders/sessions*', lambda route: route.fulfill(json=question_sessions))
                    page.route('**/api/channels/sends/*/discard', discard_route)
                    page.goto(f'{base}/?token={TOKEN}', wait_until='load')
                    _api(page, 'PUT', '/api/setup/onboarding', {'disposition': 'completed'}, token=TOKEN)
                    page.reload(wait_until='load'); _normal_chair(page)
                    _api(page, 'POST', '/api/desk/windows/chair%3Aneeds/open', {'kind': 'chair', 'ref': 'needs'}, token=TOKEN)
                    drawer = page.get_by_test_id('needs-drawer')
                    drawer.wait_for(timeout=15000)
                    if width == 1440:
                        _api(page, 'POST', '/api/desk/windows/chair%3Aneeds/set_geometry', {'rect': {'x': '-1/2 + 100', 'y': '-1/2 + 80', 'w': '900px', 'h': '600px'}}, token=TOKEN)
                    suffix = '900x600' if width == 1440 else '393'
                    def shot(name):
                        _settle(page)
                        SHOTS.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(SHOTS / f'needs-{name}-{suffix}-{"before" if before else "after"}.png'))
                        if not before:
                            assert drawer.evaluate("""el => {
                              const body = el.closest('.chair-window-body');
                              const pane = el.querySelector('.surface-list-pane');
                              return body.scrollHeight <= body.clientHeight+1 && body.scrollWidth <= body.clientWidth+1
                                && (!pane || pane.scrollHeight <= pane.clientHeight+1);
                            }"""), name
                            assert drawer.locator('[role=row] button').count() == 0
                    if not before and state != 'empty':
                        row = drawer.locator('[data-kind=send][data-testid=needs-row]') if state == 'send' else drawer.get_by_test_id('needs-row').first
                        row.click()
                        expect(row).to_have_attribute('aria-selected', 'true')
                        expect(drawer.get_by_test_id('needs-reader')).to_be_visible()
                        assert abs(row.bounding_box()['height'] - (26 if width == 1440 else 44)) < 1
                        assert drawer.locator('.object-list-rows').first.evaluate("""el => {
                          const row=el.querySelector('[data-object-id]');
                          return el.clientHeight >= row.getBoundingClientRect().height*3-1;
                        }""")
                    shot(state)
                    if not before and state == 'send':
                        row.press('ArrowUp')
                        expect(row).to_have_attribute('aria-selected', 'false')
                        drawer.locator('[data-testid=needs-row][aria-selected=true]').press('ArrowDown')
                        expect(row).to_have_attribute('aria-selected', 'true')
                        assert not presses
                        press_need_verb(page, 'Discard')
                        question = drawer.get_by_test_id('needs-question')
                        expect(question.get_by_role('button', name='Cancel', exact=True)).to_be_focused()
                        assert not presses
                        shot('armed')
                        question.get_by_role('button', name='Discard', exact=True).click()
                        expect(drawer.locator('[data-kind=send][data-testid=needs-row]')).to_have_count(0)
                        expect(drawer.get_by_test_id('needs-receipt')).to_contain_text('Discard')
                        assert len(presses) == 1
                        shot('after-answer')
                        drawer.get_by_role('tab', name='Answered', exact=True).click()
                        drawer.get_by_role('grid', name='Answered', exact=True).get_by_role('row').filter(has_text=note['title']).click()
                        shot('answered')
                    if not before and state == 'typed':
                        field = drawer.get_by_role('textbox', name='Answer', exact=True)
                        field.fill('Jordan')
                        shot('typed-draft')
                        page.route('**/api/coders/*/steer', lambda route: route.fulfill(status=typed_refusal['status'], json=typed_refusal['body']))
                        drawer.get_by_role('button', name='Send answer', exact=True).click()
                        expect(field).to_have_value('Jordan')
                        expect(drawer.get_by_test_id('needs-failure')).to_be_visible()
                        assert field.evaluate('''el => {
                          const well=el.closest('.surface-inspector-fields');
                          const input=el.getBoundingClientRect(), box=well.getBoundingClientRect();
                          return input.top >= box.top && input.bottom <= box.bottom;
                        }'''), 'the retained answer must stay whole above the completion row'
                        shot('typed-refused')
                        if width == 393:
                            page.get_by_test_id('needs-reader-back').click()
                            expect(drawer.get_by_test_id('needs-reader')).to_have_count(0)
                            shot('back')
                    page.close()
            browser.close()
    finally:
        server.stop()


def press_need_verb(page, label):
    drawer = page.get_by_test_id('needs-drawer')
    toolbar = drawer.get_by_role('toolbar', name='Needs you', exact=True)
    button = toolbar.get_by_role('button', name=label, exact=True)
    if button.is_visible(): button.click()
    else:
        toolbar.get_by_role('button', name='Actions ▾', exact=True).click()
        page.get_by_role('menu', name='Needs you actions', exact=True).get_by_role('menuitem', name=label, exact=True).click()
