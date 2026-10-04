"""PHILO-8-03 (Codex Astra r1, r2) -- a late follow-up is BLOCKED, never a pass.

r1: an 8.5 s pause after the pending check of `case.p8.delete_then_leave.gone`
made the case PASS on the pre-fix product: the receipt already read "Removal
committed" before the face click, so the TIMER produced the DELETE and the 404
that the predicate credits to leaving the face.

r2: the guard was checked BEFORE Playwright's click, whose actionability wait
(up to 10 s) sat between the check and the event: with the click target
disabled for 8.5 s, the guard read "Undo 08s", the click landed after "Removal
committed", and the case PASSED again.

The rig now checks the guard AND delivers the event in ONE page task
(`scripts/graph_walk.py` `_guarded_delivery`). These fences run the REAL atlas
case through the REAL rig and a real hub, and delay the follow-up two ways:

* `before_guard` -- a pause before the step (r1);
* `click_wait`   -- the target disabled for 8.5 s from the moment the step
                    starts, so any waiting happens INSIDE the delivery (r2).

Expected: `blocked` at both widths, the guard named. Red: PHILO8_GUARD_RED=1
strips the guard (the round-one atlas shape) and both modes PASS; the r2 rig
(4905986f) passes `click_wait` with the guard kept (recorded under
docs/internal/philo/phase-8/atlas/reds/).

PHILO-13-01 (41229db26) made every refusal in a trigger's lifecycle a `fail`,
and this late, never-delivered follow-up read as a product failure. The rig
now raises `NotDelivered` for an expired guard and records it `blocked`
(`scripts/graph_walk.py` `exercise`); `fail` stays for observed product
failures (`tests/unit/test_philo13_graph_walk.py`).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts import graph_walk as gw

pytest.importorskip("playwright.sync_api", reason="the guard fence drives a real page")

REPO = Path(__file__).resolve().parents[2]
ATLAS8 = REPO / "docs/internal/philo/graph/atlas-phase8.json"
CASE = "case.p8.delete_then_leave.gone"
PAUSE_MS = 8_500
TOGGLE = "[data-testid=chair-floor-toggle]"

_DISABLE_JS = """([selector, ms]) => {
  const el = document.querySelector(selector);
  el.setAttribute('disabled', '');
  setTimeout(() => el.removeAttribute('disabled'), ms);
}"""


@pytest.mark.e2e
@pytest.mark.timeout(240)
@pytest.mark.parametrize("mode", ["before_guard", "click_wait"])
@pytest.mark.parametrize("width", [1440, 393])
def test_a_follow_up_after_the_window_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                  width: int, mode: str) -> None:
    atlas = json.loads(ATLAS8.read_text())
    case = next(c for c in atlas["cases"] if c["id"] == CASE)
    if os.environ.get("PHILO8_GUARD_RED"):
        for step in case["trigger"]["then"]:
            step.pop("requires", None)
    atlas["cases"] = [case]
    path = tmp_path / "atlas-one.json"
    path.write_text(json.dumps(atlas))

    real = gw._ui_step
    state = {"delayed": False, "still": False}

    def late(page, step, hub=None):
        if page is not None and not state["still"]:
            # A GPU-less runner (CI's macos-14 VM) draws the Floor's
            # every-frame atmosphere in SwiftShader; at 1440 x dpr 2 a frame
            # takes over a second and the 3 s wait for the pending receipt
            # ends first. The product's still mode (reduced motion,
            # gl/atmosphereRuntime.ts:71) stops that loop; the delete, the
            # window and the guard run the same code.
            state["still"] = True
            page.emulate_media(reduced_motion="reduce")
        if (step.get("selector") == TOGGLE and not state["delayed"]
                and page is not None and page.locator(".undo-receipt").count()):
            state["delayed"] = True
            if mode == "before_guard":
                page.wait_for_timeout(PAUSE_MS)
            else:  # the target is not actionable for 8.5 s: the wait is inside delivery
                page.evaluate(_DISABLE_JS, [TOGGLE, PAUSE_MS])
        return real(page, step, hub)

    monkeypatch.setattr(gw, "_ui_step", late)
    record = gw.run_case(path, CASE, brain="muaddib", viewport=width, out=tmp_path / "runs",
                         engine="none")
    notes = " | ".join(record.get("notes", []))
    print(f"{width} {mode}: verdict {record['verdict']}; delayed {state['delayed']}; {notes[:420]}")
    assert state["delayed"], "the delay was never injected (the receipt never showed)"
    assert record["verdict"] == "blocked", (record["verdict"], notes)
    assert record["trigger_error"]["lifecycle"] == "blocked", record["trigger_error"]
    assert "TRIGGER lifecycle failed" not in notes, notes
    assert "not delivered" in notes and "did not hold at delivery" in notes, notes


# ── the delivery script on a static page (no hub): it decides and sends in one task ──

_PAGE = """<!doctype html><html><body>
<span class="undo-receipt is-pending">Removed A <button>Undo</button><span class="undo-receipt-time">05s</span></span>
<button id="t" style="width:120px;height:40px" onclick="window.clicks=(window.clicks||0)+1">Go</button>
<div id="cover" style="display:none;position:fixed;inset:0;background:#000"></div>
<script>document.addEventListener('keydown', e => { if (e.key === 'Delete') window.keys=(window.keys||0)+1; });</script>
</body></html>"""
_GUARD = {"visible": ".undo-receipt.is-pending", "text": "Undo",
          "seconds_left": {"selector": ".undo-receipt-time", "min": 2}}


@pytest.fixture()
def static_page():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 800, "height": 600})
        page.set_content(_PAGE)
        yield page
        browser.close()


@pytest.mark.e2e
@pytest.mark.parametrize("setup, blocked_by", [
    ("", None),
    ("document.getElementById('t').disabled = true", "disabled"),
    ("document.getElementById('cover').style.display = 'block'", "covered"),
    ("document.querySelector('.undo-receipt').className = 'undo-receipt is-committed'", "not visible"),
    ("document.querySelector('.undo-receipt-time').textContent = '01s'", "wanted >= 2s"),
])
def test_the_delivery_checks_and_sends_in_one_task(static_page, setup: str, blocked_by: str | None) -> None:
    if setup:
        static_page.evaluate(f"() => {{ {setup}; }}")
    step = {"kind": "ui", "action": "click", "selector": "#t", "requires": _GUARD}
    if blocked_by is None:
        assert gw._ui_step(static_page, step)["done"]
        assert static_page.evaluate("() => window.clicks") == 1
    else:
        with pytest.raises(gw.Blocked, match=blocked_by):
            gw._ui_step(static_page, step)
        assert static_page.evaluate("() => window.clicks || 0") == 0


@pytest.mark.e2e
def test_a_guarded_press_reaches_the_document_keymap(static_page) -> None:
    gw._ui_step(static_page, {"kind": "ui", "action": "press", "key": "Delete", "requires": _GUARD})
    assert static_page.evaluate("() => window.keys") == 1
    static_page.evaluate("() => { document.querySelector('.undo-receipt-time').textContent = '00s'; }")
    with pytest.raises(gw.Blocked):
        gw._ui_step(static_page, {"kind": "ui", "action": "press", "key": "Delete", "requires": _GUARD})
    assert static_page.evaluate("() => window.keys") == 1
