"""The first-paint observer must reject a blank transition even after it heals."""
from __future__ import annotations

import pytest
from playwright.sync_api import sync_playwright

from scripts.graph_walk import arm_first_paint, snapshot, check_predicate


@pytest.fixture
def page():
    with sync_playwright() as play:
        browser = play.chromium.launch()
        page = browser.new_page(viewport={"width": 393, "height": 852})
        yield page
        browser.close()


@pytest.mark.parametrize("delay_ms,covered,expected", [(0, False, True), (200, False, False), (0, True, False)])
def test_first_read_paint_cannot_be_replaced_by_a_later_readable_frame(page, delay_ms, covered, expected):
    page.set_content('''<button id="done">Done</button><textarea class="editor"></textarea>
      <div id="cover" style="display:none;position:fixed;inset:0;background:white;z-index:5"></div>
      <script>document.querySelector('#done').onclick = () => {
        document.querySelector('.editor').remove();
        const body = document.createElement('section'); body.id = 'body';
        document.body.append(body);
        const fill = () => body.textContent = 'Keep the local ledger';
        if (DELAY) setTimeout(fill, DELAY); else fill();
        if (COVERED) document.querySelector('#cover').style.display = 'block';
      };</script>'''.replace('DELAY', str(delay_ms)).replace('COVERED', str(covered).lower()))
    predicate = {"kind": "readable_text", "value": "Keep the local ledger", "first_paint_after": ".editor"}
    case = {"expected": {"observe_at": "#body", "predicate": predicate}}
    arm_first_paint(page, case)
    assert page.evaluate('window.__graphFirstPaint.clickedAt') is None
    page.click('#done')
    page.wait_for_timeout(350)
    observed = snapshot(page, case)
    probe = observed['transition_probe']
    assert probe['armedAt'] <= probe['clickedAt']
    assert probe['frames']
    assert check_predicate(predicate, {}, observed)[0] is expected
    if delay_ms:
        assert not probe['firstReadFrame']['readable']
        assert probe['firstReadableFrame']['readable']
        assert observed['text'] == 'Keep the local ledger'


def test_a_later_blank_cannot_hide_behind_a_good_first_paint(page):
    page.set_content("""<button id="done">Done</button><textarea class="editor"></textarea>
      <script>document.querySelector('#done').onclick = () => {
        document.querySelector('.editor').remove();
        const body = document.createElement('section'); body.id = 'body';
        body.textContent = 'Keep the local ledger'; document.body.append(body);
        setTimeout(() => body.textContent = '', 100);
        setTimeout(() => body.textContent = 'Keep the local ledger', 250);
      };</script>""")
    predicate = {"kind": "readable_text", "value": "Keep the local ledger", "first_paint_after": ".editor"}
    case = {"expected": {"observe_at": "#body", "predicate": predicate}}
    arm_first_paint(page, case)
    page.click('#done')
    page.wait_for_timeout(400)
    observed = snapshot(page, case)
    assert observed['transition_probe']['firstReadFrame']['readable']
    assert observed['transition_probe']['firstUnreadableReadFrame']['text'] == ''
    assert observed['text'] == 'Keep the local ledger'
    assert not check_predicate(predicate, {}, observed)[0]
