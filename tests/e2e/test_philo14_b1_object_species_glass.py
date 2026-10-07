"""PHILO-14 B1 — the object species on real glass (the Components window).

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
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="PHILO-14 B1 glass needs Playwright")

SHOTS = evidence_dir("p14-b1")
TOKEN = "p14-b1-species"
GALLERY = "[data-testid=object-species-gallery]"


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
