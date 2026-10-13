"""The glass readers' own fences: each reader the desk sweep trusts must FAIL
on planted faults and pass the lawful cases. No hub: static fixtures in a real
Chromium (the readers measure layout, which jsdom cannot).

* The folded-word exception (PHILO-13-11 C1, Astra's counsel on #730): at 393
  the screen bar draws the mark, the egress chip and Search as pictures and
  folds their words into the control's name (design section 4). Both type-floor
  readers exempt such a word: the first-use floor (``type_floor_rig._MEASURE``,
  the sweep's ``floor`` fence) and the frame glass's F5
  (``test_philo13_11_frame_glass.FRAME_JS``). Each reader must REPORT a blank
  zero-size "Save" button, a zero-size "SEND FAILED" inside a picture control
  named "Open", and every word whose replacement is not PAINTED (a hidden or
  transparent picture, a picture that never loaded, a transparent or empty
  ::before glyph), and must still exempt the intended cases (a painted picture
  or ::before glyph, at 393 only).
* Scroll reach (PHILO-13-18 C8, Astra's counsel on #743): the on-glass reader
  (``glass_infra._rendered_text_faults``, the sweep's ``readable`` fence)
  exempts only REACHABLE scrolled text: a word shifted above a scroller's top
  is reported clipped; ordinary rows below the fold stay exempt.

Moved here whole from ``test_philo13_11_folded_word_reader.py`` and
``test_philo13_18_scroll_reach_reader.py`` (push 2 of the test diet,
2026-10-12; both parked in ``tests/e2e/_parked/``).
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="the reader fences need Playwright")

from .glass_infra import _rendered_text_faults  # noqa: E402
from .frame_rig import FRAME_JS  # noqa: E402
from .type_floor_rig import _MEASURE  # noqa: E402

PICTURE = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16'%3E"
    "%3Crect width='16' height='16' fill='%23000'/%3E%3C/svg%3E"
)

# Each control is a screen-bar control, so it is inside BOTH readers' scope.
FIXTURE = f"""<!doctype html><html><head><style>
  body {{ margin: 0; background: #eef0f3; color: #0b0c10; font: 13px sans-serif; }}
  .desk-menubar {{ display: flex; gap: 8px; height: 44px; align-items: center; }}
  button {{ height: 44px; min-width: 44px; background: #9ea4b0; color: #0b0c10; border: 1px solid #0b0c10; }}
  .folded {{ font-size: 0; }}
  .glyph::before {{ content: "⌂"; font: 700 16px monospace; color: #0b0c10; }}
  .glyph-clear::before {{ content: "⌂"; font: 700 16px monospace; color: transparent; }}
  .glyph-none::before {{ content: none; }}
</style></head><body><div class="desk-next" id="desk-next"><div class="desk-menubar">
  <button class="desk-mark folded" title="HoldSpeak" data-case="mark"><img src="{PICTURE}" width="16" height="16" alt="">HoldSpeak</button>
  <button class="desk-tools-launch folded" data-case="blank-save">Save</button>
  <button class="desk-tools-launch" aria-label="Open" data-case="send-failed-in-open"><img src="{PICTURE}" width="16" height="16" alt=""><span class="folded">SEND FAILED</span></button>
  <button class="egress-badge folded glyph" aria-label="Privacy and trust: Device" data-case="glyph">Device</button>
  <button class="desk-mark folded" title="Hidden" data-case="hidden-img"><img src="{PICTURE}" width="16" height="16" alt="" style="visibility: hidden">Hidden</button>
  <button class="desk-mark folded" title="Faded" data-case="transparent-img"><img src="{PICTURE}" width="16" height="16" alt="" style="opacity: 0">Faded</button>
  <button class="desk-mark folded" title="Wrapped" data-case="transparent-ancestor"><span style="opacity: 0"><img src="{PICTURE}" width="16" height="16" alt=""></span>Wrapped</button>
  <button class="desk-mark folded" title="Broken" data-case="broken-img"><img src="data:image/png;base64,AAAA" width="16" height="16" alt="">Broken</button>
  <button class="egress-badge folded glyph-clear" aria-label="Clear" data-case="glyph-transparent">Clear</button>
  <button class="egress-badge folded glyph-none" aria-label="Nothing" data-case="glyph-none">Nothing</button>
</div></div></body></html>"""


def _readers(width: int) -> dict[str, list[str]]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": width, "height": 852})
            page.set_content(FIXTURE)
            first_use = page.evaluate(_MEASURE, "#8b93a3")
            frame = page.evaluate(FRAME_JS, width)
        finally:
            browser.close()
    return {
        "first_use": sorted({s["text"] for s in first_use["small"]}),
        "frame": sorted({s["text"] for s in frame["small_text"]}),
    }


@pytest.mark.parametrize("reader", ["first_use", "frame"])
def test_the_negative_mutations_fail_the_reader(reader: str) -> None:
    seen = _readers(393)[reader]
    assert "Save" in seen, f"{reader}: a blank zero-size Save button passed the floor: {seen}"
    assert "SEND FAILED" in seen, f"{reader}: SEND FAILED hidden in a control named Open passed: {seen}"


# Astra counsel r2 on PR 730: the replacement must be PAINTED, not merely
# boxed. A hidden picture, a transparent picture (or one under a transparent
# ancestor), a picture that never loaded, a transparent ::before glyph and a
# ::before with no content each leave the word with nothing on the glass.
UNPAINTED = ["Hidden", "Faded", "Wrapped", "Broken", "Clear", "Nothing"]


@pytest.mark.parametrize("reader", ["first_use", "frame"])
def test_an_unpainted_replacement_fails_the_reader(reader: str) -> None:
    seen = _readers(393)[reader]
    missed = [word for word in UNPAINTED if word not in seen]
    assert not missed, f"{reader}: a word with no painted replacement passed the floor: {missed} (seen {seen})"


@pytest.mark.parametrize("reader", ["first_use", "frame"])
def test_the_intended_picture_control_is_exempt_only_at_393(reader: str) -> None:
    narrow, wide = _readers(393)[reader], _readers(1440)[reader]
    for word in ("HoldSpeak", "Device"):  # a painted picture; a painted ::before glyph
        assert word not in narrow, f"{reader}: the folded {word!r} was not exempt at 393"
        assert word in wide, f"{reader}: the fold exemption leaked to 1440 ({word!r})"


# ── scroll reach (PHILO-13-18 C8) ─────────────────────────────────────

SCROLL_FIXTURE = """<!doctype html><html><head><style>
  body { margin: 0; font: 13px sans-serif; }
  .box { width: 200px; height: 20px; overflow: auto; line-height: 20px; }
  .up { position: relative; top: -18px; display: block; }
</style></head><body>
  <div class="scope" id="unreachable"><div class="box"><span class="up">Unreachable</span></div></div>
  <div class="scope" id="scrolls"><div class="box"><div>Row one</div><div>Row two</div><div>Row three</div></div></div>
</body></html>"""


def _clipped(selector: str) -> list[str]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 393, "height": 852})
            page.set_content(SCROLL_FIXTURE)
            faults = _rendered_text_faults(page, selector, on_glass=True)
        finally:
            browser.close()
    return [c["text"] for c in faults["clipped"]]


def test_unreachable_text_in_a_scroller_is_reported() -> None:
    assert "Unreachable" in _clipped("#unreachable"), "a word above the scroll range passed the on-glass reader"


def test_text_below_the_fold_of_a_scroller_stays_exempt() -> None:
    assert _clipped("#scrolls") == [], "ordinary scrolled rows were reported clipped"
