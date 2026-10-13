"""PHILO-13-11 (C1) -- the folded-word exception, fenced on purpose-built glass.

At 393 the screen bar draws the mark, the egress chip and Search as pictures
and folds their words into the control's name (design §4). Both type-floor
readers exempt such a word: the first-use floor (`test_hs202_05_first_use_
type_floor._MEASURE`) and the frame glass's F5 (`test_philo13_11_frame_glass.
FRAME_JS`). Astra's counsel on #730 showed the first exception passed any
zero-size text under any named ancestor. These fixtures are her negative
mutations, kept as permanent fences: each reader must REPORT

  * a blank zero-size "Save" button (no picture, no explicit name), and
  * a zero-size "SEND FAILED" inside a picture control named "Open",

and every word whose replacement is not PAINTED (Astra r2: a hidden or
transparent picture, a picture that never loaded, a transparent or empty
::before glyph), and must still exempt the intended cases (a painted picture
or a painted ::before glyph, an explicit name holding the hidden word, at 393
only). No hub: the readers run
on static fixtures in a real Chromium.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="the reader fence needs Playwright")

from .test_hs202_05_first_use_type_floor import _MEASURE  # noqa: E402
from .test_philo13_11_frame_glass import FRAME_JS  # noqa: E402

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
