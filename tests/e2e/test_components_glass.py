"""The Components app, AS RENDERED: what only a real browser proves of the species.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation. PHILO-14 B1 (the
object species on real glass, the Components window) is all of those: the
accessibility tree, arrow keys over the rendered columns, computed lamps and
44 px rows. Moved whole.

What jsdom cannot see, proved in Chromium on a real hub and the built
bundle: the gallery section "Object species (PHILO-14 B1)" in the
Components window (`/design/components`, `ObjectSpeciesGallery.tsx`).

WHAT THIS RIG PROVES, at 1440 and 393 (Astra's counsel on #932, r1):

  1. Non-pointer activation: `element.click()` on a DeskIcon and on an
     ObjectList row selects it (finding 1).
  2. The fold keeps the grid's semantics: in Chromium's ACCESSIBILITY TREE
     the ObjectList exposes the same columns in its headers and in every
     row, at both widths (finding 2).
  3. IconGrid navigation follows the RENDERED columns: Right lands on the
     icon to the right on the same line; Down lands on the icon straight
     below (finding 3).
  4. The all-running PRCard reads `CHECKS · 7 RUNNING` with no `0 OF`
     (finding 4).
  5. One object, one colour: the row lamp of the asking object and of the
     working object paints the same colour as its icon lamp (finding 5).
  6. Material: the SAYS quote has no rail (no border, no shadow) and the
     PRCard is flat (finding 6).
  7. At 393 every list row and every sort gadget is at least 44 px high.

WHAT IT DOES NOT PROVE: a screen reader's speech; a touch device; the
species inside the face lanes' own windows (A1/A2/A5/C2/C3 own that).
"""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the Components glass needs Playwright")

SHOTS = evidence_dir("p14-b1")
TOKEN = "components-glass"
GALLERY = "[data-testid=object-species-gallery]"


def _select_controls(page: Any) -> None:
    page.get_by_test_id("design-reference").wait_for()
    direct = page.get_by_role("button", name="Controls", exact=True)
    if direct.count():
        direct.click()
        return
    page.get_by_role("button", name=re.compile(r"^Patterns:")).click()
    page.locator("[role^='menuitem']").filter(has_text="Controls").first.click()


def _ax_columns(page: Any) -> dict[str, Any]:
    """Read the ObjectList's grid from Chromium's accessibility tree (CDP),
    not from the DOM: the exposed column headers, and per row the exposed
    cells (each cell named by the column it sits in, via data-col)."""
    cdp = page.context.new_cdp_session(page)
    tree = cdp.send("Accessibility.getFullAXTree")["nodes"]
    by_id = {n["nodeId"]: n for n in tree}

    def role(n: dict[str, Any]) -> str:
        return (n.get("role") or {}).get("value", "")

    def name(n: dict[str, Any]) -> str:
        return (n.get("name") or {}).get("value", "")

    grids = [n for n in tree if role(n) == "grid" and not n.get("ignored")]
    assert grids, "no grid in the accessibility tree"
    grid = grids[0]

    def walk(node: dict[str, Any]):
        for child_id in node.get("childIds", []):
            child = by_id.get(child_id)
            if not child:
                continue
            yield child
            yield from walk(child)

    headers = [name(n) for n in walk(grid) if role(n) == "columnheader" and not n.get("ignored")]
    rows = []
    for node in walk(grid):
        if role(node) != "row" or node.get("ignored"):
            continue
        cells = [c for c in walk(node) if role(c) == "gridcell" and not c.get("ignored")]
        if cells:
            rows.append(len(cells))
    cdp.detach()
    return {"headers": headers, "row_cells": rows}


_PROBE_JS = """() => {
  const g = document.querySelector('[data-testid=object-species-gallery]');
  const css = (el, p) => el ? getComputedStyle(el).getPropertyValue(p) : null;
  const dot = (el) => el && css(el.querySelector('.gadget-lamp-dot'), 'background-color');
  const askRow = g.querySelector('.object-list-row[data-object-id="claude:c1a0de00-runbook"] .gadget-lamp');
  const workRow = g.querySelector('.object-list-row[data-object-id="codex:c0dex000-recon"] .gadget-lamp');
  const askIcon = g.querySelector('.desk-icon-grid [data-object-id="claude:c1a0de00-runbook"] .desk-icon-lamp');
  const workIcon = g.querySelector('.desk-icon-grid [data-object-id="codex:c0dex000-recon"] .desk-icon-lamp');
  const quote = g.querySelector('.lane-rail-quote');
  const cards = [...g.querySelectorAll('.pr-card')];
  return {
    askRow: dot(askRow), askIcon: css(askIcon, 'background-color'),
    workRow: dot(workRow), workIcon: css(workIcon, 'background-color'),
    quoteBorder: css(quote, 'border-left-width'), quoteShadow: css(quote, 'box-shadow'),
    prShadow: cards.map((c) => css(c, 'box-shadow')),
    prText: cards.map((c) => c.innerText),
    rows: [...g.querySelectorAll('.object-list-row')].map((r) => r.getBoundingClientRect().height),
    sorts: [...g.querySelectorAll('.object-list-sort')].map((b) => b.getBoundingClientRect().height),
    marks: /\\[\\s?\\]|\\[x\\]/i.test(g.innerText),
  };
}"""


class TestObjectSpeciesGlass:
    """replaces: tests/e2e/test_philo14_b1_object_species_glass.py::TestObjectSpeciesGlass::test_object_species (moved whole)."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        yield
        self.server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
    def test_object_species(self, width: int, height: int) -> None:
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            _normal_chair(page)
            page.goto(f"{self.base}/design/components?token={TOKEN}", wait_until="load")
            # The living reference opens on Forms; the retained object and
            # composer catalogue is the explicit Controls pattern.
            _select_controls(page)
            gallery = page.locator(GALLERY)
            try:
                gallery.wait_for(state="attached", timeout=20_000)
            except Exception:
                page.screenshot(path=str(SHOTS / f"glass-miss-{width}.png"))
                raise
            gallery.scroll_into_view_if_needed()
            _settle(page)

            # 1. non-pointer activation (element.click(): detail 0)
            icon = gallery.locator('.desk-icon-grid [data-object-id="n-1"]')
            assert icon.get_attribute("aria-pressed") == "false"
            icon.evaluate("el => el.click()")
            assert icon.get_attribute("aria-pressed") == "true", "element.click() did not select the icon"
            row = gallery.locator('.object-list-row[data-object-id="p-jordan"]')
            row.locator("button").evaluate("el => el.click()")
            assert row.get_attribute("aria-selected") == "true", "element.click() did not select the row"

            # 2. the a11y tree: headers == cells per row, at this width
            ax = _ax_columns(page)
            assert ax["headers"], ax
            assert len(ax["headers"]) == 4, ax
            assert ax["row_cells"] and all(n == len(ax["headers"]) for n in ax["row_cells"]), ax

            # 3. 2-D navigation by the rendered columns
            first = gallery.locator(".desk-icon-grid .desk-icon").first
            first.focus()
            boxes = gallery.locator(".desk-icon-grid .desk-icon").evaluate_all(
                "els => els.map(e => { const r = e.getBoundingClientRect(); return [r.left, r.top]; })"
            )
            # PHILO-14 A1 (#939): the Chair's screen of DeskIcons stands behind
            # the gallery; count the gallery's own icons only.
            focused = lambda: gallery.evaluate(  # noqa: E731
                "(g) => [...g.querySelectorAll('.desk-icon-grid .desk-icon')].indexOf(document.activeElement)"
            )
            page.keyboard.press("ArrowRight")
            assert focused() == 1
            assert abs(boxes[1][1] - boxes[0][1]) < 2 and boxes[1][0] > boxes[0][0]
            page.keyboard.press("ArrowDown")
            below = focused()
            assert boxes[below][1] > boxes[1][1] + 10, (below, boxes[below], boxes[1])
            assert abs(boxes[below][0] - boxes[1][0]) < 2, (below, boxes[below], boxes[1])

            facts = gallery.evaluate(_PROBE_JS.replace("() =>", "(_) =>"))
            # 4. all pending without a zero
            assert any("CHECKS · 7 RUNNING" in t for t in facts["prText"]), facts["prText"]
            assert not any(" 0 OF" in t or "0 FAILED" in t for t in facts["prText"]), facts["prText"]
            # 5. one object, one colour
            assert facts["askRow"] == facts["askIcon"], facts
            assert facts["workRow"] == facts["workIcon"], facts
            # 6. material
            assert facts["quoteBorder"] == "0px" and facts["quoteShadow"] == "none", facts
            assert all(s == "none" for s in facts["prShadow"]), facts
            assert not facts["marks"]
            # 7. 44 px at 393
            if width == 393:
                assert min(facts["rows"]) >= 44, facts["rows"]
                assert min(facts["sorts"]) >= 44, facts["sorts"]

            page.emulate_media(reduced_motion="reduce")
            _settle(page)
            # The window body scrolls: shoot the glass with the list in view
            # (an element shot of the whole gallery clips at the window).
            gallery.locator(".object-list").scroll_into_view_if_needed()
            _settle(page)
            page.screenshot(path=str(SHOTS / f"glass-list-{width}.png"))
            assert not errors, errors
            browser.close()


@pytest.mark.e2e
@pytest.mark.parametrize("width", [1440, 393])
def test_firefox_common_composer_specimen_owns_editor_material(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Actual gallery route, private Hub, local specimen; no PR send claim.

    Real Firefox proves the cascade and capture/action geometry under the
    retained PR host class. Draft/Preview are local gallery state only.
    """
    import json
    from playwright.sync_api import expect, sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = evidence_dir("conversation-components")
    try:
        with sync_playwright() as pw:
            browser = pw.firefox.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852},
                                    reduced_motion="reduce")
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            try:
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                _normal_chair(page)
                page.goto(f"{base}/design/components?token={TOKEN}", wait_until="load")
                _select_controls(page)
                specimen = page.get_by_test_id("reference-controls").locator("section.surface-section").filter(
                    has=page.get_by_role("textbox", name="Write a local preview"))
                editor = specimen.get_by_role("textbox", name="Write a local preview")
                editor.wait_for()
                editor.fill("Review the common editor material.\nKeep the next action in reach.")
                specimen.scroll_into_view_if_needed()
                _settle(page)
                facts = editor.evaluate("""el => {
                  const s=getComputedStyle(el), r=el.getBoundingClientRect();
                  return {font:s.fontFamily,size:parseFloat(s.fontSize),background:s.backgroundColor,
                    border:s.borderTopWidth,padding:s.padding,resize:s.resize,width:r.width};
                }""")
                assert facts["size"] >= 14 and "mono" not in facts["font"].lower(), facts
                assert facts["border"] == "0px", facts
                assert facts["background"] == "rgba(0, 0, 0, 0)", facts
                assert facts["resize"] == "vertical", facts
                assert specimen.locator("button.desk-mic").count() == 1
                controls = [specimen.locator("button.desk-mic"),
                            specimen.get_by_role("button", name="Preview", exact=True)]
                boxes = [control.bounding_box() for control in controls]
                assert abs(boxes[0]["y"] - boxes[1]["y"]) <= 1, boxes
                for control in controls:
                    expect(control).to_be_in_viewport(ratio=1)
                    assert control.evaluate("""el => {
                      const r=el.getBoundingClientRect();
                      return r.width>=44 && r.height>=44 && [.1,.5,.9].every(x=>[.1,.5,.9].every(y=>{
                        const hit=document.elementFromPoint(r.x+r.width*x,r.y+r.height*y);
                        return hit===el || el.contains(hit);
                      }));
                    }"""), "Common controls must own their complete hit area"
                assert specimen.evaluate("el=>el.scrollWidth<=el.clientWidth+1")
                page.screenshot(path=str(shots / f"composer-specimen-{width}.png"))
                (shots / f"composer-specimen-{width}.json").write_text(json.dumps(facts, indent=2))
                controls[1].click()
                expect(specimen).to_contain_text("Review the common editor material.")
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.parametrize("browser_name", ["chromium", "firefox"])
@pytest.mark.parametrize("width", [1440, 393])
def test_pressed_button_fill_survives_hover_and_keyboard_focus(
    browser_name: str, width: int,
) -> None:
    """Exercise the shared CSS state cascade in real engines, without a Hub.

    The fixture uses the library Button's class/ARIA contract. Browser hover
    and keyboard focus must retain the selected fill for primary and danger.
    """
    import re
    from playwright.sync_api import sync_playwright

    source = Path(__file__).resolve().parents[2] / "web" / "src" / "styles"
    css = (source / "tokens.css").read_text() + "\n" + re.sub(
        r'^@import[^\n]*\n', '', (source / "global.css").read_text(), flags=re.MULTILINE,
    )
    with sync_playwright() as pw:
        browser = getattr(pw, browser_name).launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": width, "height": 500}, reduced_motion="reduce")
            page.set_content(
                "<style>" + css + "</style><main style='padding:60px;display:grid;gap:20px'>"
                "<button id='primary' class='btn btn--primary' aria-pressed='true'>Selected primary</button>"
                "<button id='danger' class='btn btn--danger' aria-pressed='true'>Selected danger</button>"
                "<button id='next' class='btn'>Next control</button>"
                "</main>"
            )
            for variant, token in [("primary", "--accent-press"), ("danger", "--danger-fill")]:
                button = page.locator('#' + variant)
                expected = page.evaluate("""token => {
                  const probe=document.createElement('span');
                  probe.style.backgroundColor=`var(${token})`; document.body.appendChild(probe);
                  const value=getComputedStyle(probe).backgroundColor; probe.remove(); return value;
                }""", token)
                assert expected != "rgba(0, 0, 0, 0)", (variant, token)
                button.focus()
                page.keyboard.press("Tab")
                page.keyboard.press("Shift+Tab")
                assert button.evaluate("el=>el.matches(':focus-visible')"), variant
                assert button.evaluate("el=>getComputedStyle(el).backgroundColor") == expected
                button.hover()
                assert button.evaluate("el=>getComputedStyle(el).backgroundColor") == expected, variant
                assert button.evaluate("el=>getComputedStyle(el).outlineStyle") != "none", variant
                # The held and unheld hover states must remain distinct.
                button.evaluate("el=>el.setAttribute('aria-pressed','false')")
                assert button.evaluate("el=>getComputedStyle(el).backgroundColor") != expected, variant
                button.evaluate("el=>el.setAttribute('aria-pressed','true')")
                assert button.evaluate("el=>getComputedStyle(el).backgroundColor") == expected, variant
            shots = evidence_dir("modern-shell-pressed")
            page.screenshot(path=str(shots / f"{browser_name}-{width}.png"))
        finally:
            browser.close()
