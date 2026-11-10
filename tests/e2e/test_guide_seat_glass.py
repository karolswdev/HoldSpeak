"""The guide reserves one window seat on the seeded Desk, at both widths."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from .glass_infra import _api, _normal_chair

pytestmark = [pytest.mark.e2e]
T = 20_000

# Reuse the seeded Desk and its real app producers; guide geometry has no
# app-specific rig or second copy of the guide scripts.
from .test_desk_sweep import (  # noqa: E402, F401
    desk, pw_browser, _page, _hub_open, _start_app_walk, _guide_view,
    _GUIDE_SCRIPTS, _GUIDE_FENCES_JS, _GUIDE_VIEW_JS, SETTLED_JS, TOKEN as SWEEP_TOKEN,
)
from .glass_infra import clear_hub_windows_http  # noqa: E402

_SEAT_FACTS_JS = r"""wid => {
  const w = document.getElementById(wid), note = w.querySelector('[data-testid="guide-note"]');
  const N = note.getBoundingClientRect();
  const body = [...w.children].find(el => el.matches('.surface-host-body,.desk-pullout-body,.desk-surface-body,.chair-window-body'));
  const clip = el => {
    const r = el.getBoundingClientRect();
    let top = r.top, bottom = r.bottom;
    for (let p = el.parentElement; p && p !== w; p = p.parentElement) {
      if (/auto|scroll|hidden|clip/.test(getComputedStyle(p).overflowY)) {
        const b = p.getBoundingClientRect(); top = Math.max(top, b.top); bottom = Math.min(bottom, b.bottom);
      }
    }
    return {...r.toJSON(), top, bottom, height: Math.max(0,bottom-top)};
  };
  const rows = [...w.querySelectorAll('.object-list-row,.surface-rail-row,.needs-row,.gadget-row,.pg-tray,.pg-plate-head,.pg-turn-page')]
    .filter(el => !note.contains(el)).map(clip).filter(r => r.width && r.height > 1)
    .sort((a,b) => a.bottom-b.bottom);
  return {window:w.getBoundingClientRect().toJSON(), note:N.toJSON(),
    pane:body?.getBoundingClientRect().toJSON(), last_visible_row:rows.at(-1),
    ring:w.querySelector('[data-testid="guide-ring"]')?.getBoundingClientRect().toJSON()};
}"""


def _seat_shot(page: Any, wid: str, name: str) -> dict[str, Any]:
    import json
    # ResizeObserver has paid the latest note height back to the host.
    page.wait_for_function("""wid => {
      const w=document.getElementById(wid), n=w.querySelector('[data-testid="guide-note"]');
      return n && Math.abs(parseFloat(w.style.getPropertyValue('--guide-seat-height'))-n.offsetHeight)<2;
    }""", arg=wid, timeout=T)
    facts = page.evaluate(_SEAT_FACTS_JS, wid)
    assert facts['pane'] and facts['pane']['bottom'] <= facts['note']['top'] + 1, facts
    assert facts['last_visible_row'] and facts['last_visible_row']['bottom'] <= facts['note']['top'] + 1, facts
    assert not page.evaluate(_GUIDE_FENCES_JS, wid), page.evaluate(_GUIDE_FENCES_JS, wid)
    shots = evidence_dir('guide5')
    page.screenshot(path=str(shots / f'{name}.png'))
    (shots / f'{name}-facts.json').write_text(json.dumps(facts, indent=2))
    return facts


@pytest.mark.parametrize('name', ['programs', 'settings', 'needs'])
@pytest.mark.parametrize('width', [900, 393])
def test_the_guide_and_capture_reserve_a_seat_and_return_the_pane(desk: Any, pw_browser: Any, name: str, width: int) -> None:
    import json
    from playwright.sync_api import expect
    base = desk['base']
    wid = _GUIDE_SCRIPTS[name]['open']['app']
    clear_hub_windows_http(base, SWEEP_TOKEN)
    _hub_open(base, wid, None, window=width == 900)
    ctx, page, errors, _ = _page(pw_browser, width, base)
    page.add_init_script("localStorage.setItem('hs:walk-voice','off')")
    status = json.loads((Path(__file__).resolve().parents[2] / 'web/src/desk/feedback/fixtures/status-enabled.json').read_text())
    page.route('**/api/ui-feedback/status', lambda route: route.fulfill(json=status))
    try:
        page.goto(f'{base}/?token={SWEEP_TOKEN}', wait_until='load')
        _normal_chair(page)
        window = page.locator(f'[id="{wid}"]')
        page.wait_for_function(SETTLED_JS, arg=wid, timeout=T)
        before = _guide_view(page, wid)
        full_height = window.locator(':scope > .surface-host-body, :scope > .chair-window-body').bounding_box()
        _start_app_walk(page)
        for step in (1, 2):
            note = page.get_by_test_id('guide-note')
            expect(note.get_by_test_id('walk-count')).to_have_text(f"{step} of {len(_GUIDE_SCRIPTS[name]['steps'])}")
            expect(note.get_by_test_id('walk-next')).to_be_enabled()
            facts = _seat_shot(page, wid, f'{name}-step-{step}-{width}')
            assert facts['ring'] and facts['ring']['height'] > 0, facts
            if step == 1:
                note.get_by_role('button', name='Say what is off').click()
                note.get_by_role('textbox', name='Feedback words').wait_for(timeout=T)
                _seat_shot(page, wid, f'{name}-capture-{width}')
                note.get_by_role('button', name='Cancel', exact=True).click()
            if step == 1:
                note.get_by_test_id('walk-next').click()
        page.get_by_test_id('walk-stop').click()
        expect(page.get_by_test_id('guide-note')).to_have_count(0)
        assert window.get_attribute('data-guide-seat') is None
        page.wait_for_function('(args) => JSON.stringify(('+_GUIDE_VIEW_JS+')(document.getElementById(args.wid))) === JSON.stringify(args.before)', arg={'wid':wid,'before':before}, timeout=T)
        if full_height:
            after = window.locator(':scope > .surface-host-body, :scope > .chair-window-body').bounding_box()
            assert after and abs(after['height'] - full_height['height']) <= 1, (full_height, after)
        assert not any('pageerror:' in error for error in errors), errors
    finally:
        ctx.close()
