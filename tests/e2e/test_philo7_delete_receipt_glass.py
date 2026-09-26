"""PHILO-7-03 follow-up -- the Floor's decision-delete receipt, fenced AS RENDERED.

The owner selects a decision on the Floor (spatial view) and presses Delete.
The receipt must be readable in the viewport for the whole cycle: the pending
receipt ("Removed ...") and, after the undo window, "Removal committed". Each
phase is read on the real page through the real hub at 1440 and 393:
``readable_text`` (present, visible, inside the viewport) and 9 of 9
``elementFromPoint`` samples (a 3 x 3 grid, inset 2 px) land on the receipt,
and the receipt shares no pixel with the selection bar or the dock.
The hub side is read too: GET /api/decisions/{id} refuses after the commit.

Red on main: the wrapper carried the ``.desk-next`` root class, whose
``min-height: 100vh`` made the fixed box one viewport tall, so the receipt was
drawn at y = -12 (3 of 9 samples off-screen), and the committed phase cleared
after 1.2 s. Reproduced first by ``case.p7.decision_delete.gone``
(``docs/internal/philo/graph/atlas-phase7.json`` on the PHILO-7-03 branch).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _api_allow_error, _boot, _ensure_build, _normal_chair
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the delete-receipt glass needs Playwright")

TOKEN = "philo7-delete-receipt"
SHOTS = evidence_dir(".tmp/philo7-delete-receipt-shots")

_PROBE_JS = """(el) => {
  const r = el.getBoundingClientRect();
  const vw = window.innerWidth, vh = window.innerHeight;
  const style = getComputedStyle(el);
  const xs = [r.left + 2, r.left + r.width / 2, r.right - 2];
  const ys = [r.top + 2, r.top + r.height / 2, r.bottom - 2];
  const samples = [];
  for (const x of xs) for (const y of ys) {
    const hit = document.elementFromPoint(x, y);
    samples.push({x, y, owned: !!hit && (hit === el || el.contains(hit))});
  }
  return {
    text: el.innerText,
    rect: {x: r.left, y: r.top, w: r.width, h: r.height},
    visible: style.visibility !== 'hidden' && style.display !== 'none' && Number(style.opacity) > 0,
    inViewport: r.left >= 0 && r.top >= 0 && r.right <= vw && r.bottom <= vh && r.width > 0 && r.height > 0,
    samples,
  };
}"""


_OVERLAP_JS = """() => {
  const r = document.querySelector('.undo-receipt').getBoundingClientRect();
  const hits = [];
  for (const sel of ['.desk-askbar', '.desk-dock']) {
    for (const el of document.querySelectorAll(sel)) {
      const o = el.getBoundingClientRect();
      if (o.width && o.height && r.left < o.right && o.left < r.right && r.top < o.bottom && o.top < r.bottom)
        hits.push({sel, rect: {x: o.left, y: o.top, w: o.width, h: o.height}});
    }
  }
  return hits;
}"""


def _readable_receipt(page: Any, want: str, timeout_ms: int) -> dict[str, Any]:
    """Wait until the receipt reads ``want``; then it must be readable and uncovered."""
    page.wait_for_function(
        "(w) => (document.querySelector('.undo-receipt')?.innerText || '').includes(w)",
        arg=want,
        timeout=timeout_ms,
    )
    probe = page.locator(".undo-receipt").first.evaluate(_PROBE_JS)
    assert want in probe["text"], probe
    assert probe["visible"] and probe["inViewport"], f"{want!r}: not in the viewport: {probe['rect']}"
    owned = [s for s in probe["samples"] if s["owned"]]
    assert len(owned) == 9, f"{want!r}: {len(owned)}/9 samples on the receipt: {probe}"
    # Never covers: the receipt shares no pixel with the selection bar or the dock.
    overlaps = page.evaluate(_OVERLAP_JS)
    assert overlaps == [], f"{want!r}: the receipt overlaps {overlaps}"
    return probe


class TestDeleteReceiptGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_delete_receipt_is_readable_in_the_viewport(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": width, "height": 900})
                errors: list[str] = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                created = _api(page, "POST", "/api/decisions",
                               {"title": "Glass withdrawn decision", "status": "accepted"}, token=TOKEN)
                decision_id = created["decision"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)

                # To the Floor; at 393 the Floor opens as a list, so switch to the spatial view.
                page.locator("[data-testid=chair-floor-toggle]").click()
                if width <= 720:
                    page.locator("[aria-controls=desk-tool-shelf]").click()
                    page.locator("[aria-controls=desk-palette-listbox]").fill("Spatial view")
                    page.locator("[id='desk-palette-option-desk.toggle-view']").click()
                row = page.locator(f"[data-obj-id='decision:{decision_id}']")
                row.wait_for(state="attached", timeout=15_000)
                row.focus()
                page.keyboard.press("Shift+Enter")
                # An in-page clock: when 'Removal committed' first shows and when it goes.
                page.evaluate("""() => {
                  window.__committedFirst = null; window.__committedGone = null;
                  const iv = setInterval(() => {
                    const text = document.querySelector('.undo-receipt')?.innerText || '';
                    const now = performance.now();
                    if (text.includes('Removal committed') && window.__committedFirst === null) window.__committedFirst = now;
                    if (!text && window.__committedFirst !== null) { window.__committedGone = now; clearInterval(iv); }
                  }, 50);
                }""")
                page.keyboard.press("Delete")

                pending = _readable_receipt(page, "Removed", 5_000)
                page.screenshot(path=str(SHOTS / f"1-pending-{width}.png"))
                committed = _readable_receipt(page, "Removal committed", 15_000)
                page.screenshot(path=str(SHOTS / f"2-committed-{width}.png"))

                # The committed receipt stays long enough to read (the desk's outcome
                # linger, OUTCOME_LINGER_MS = 6000 in web/src/desk/linger.ts; main: 1.2 s).
                page.wait_for_function("() => window.__committedGone !== null", timeout=20_000)
                shown_ms = page.evaluate("() => window.__committedGone - window.__committedFirst")
                assert shown_ms >= 5_000, f"'Removal committed' shows for {shown_ms} ms only"

                status, payload = _api_allow_error(page, "GET", f"/api/decisions/{decision_id}", token=TOKEN)
                assert status == 404, payload
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
                print(f"{width}: pending {pending['rect']} committed {committed['rect']} shown {shown_ms:.0f} ms")
            finally:
                browser.close()
