"""Phase 16 (the interior kit, §11 "Verb"; Astra r1 M6): the library Button
is ONE plate height, rendered.

A real hub on an isolated HOME. The Project's window (the Room window of the
canvas) holds verbs of every plated form the kit draws: ghost dense (Room,
History, Steward, Get Info), secondary dense (Open), the FilterBar tokens.
At 1440 each one's painted height is 28 px (the Steel plate, dense or not).
At 393 each one owns a 44 px target (its painted face, or the narrow-desk
halo). Shots to `.tmp/evidence-shots/p16-kit-verb/`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the kit Verb glass needs Playwright")

TOKEN = "p16-kit-verb"
SHOTS = evidence_dir("p16-kit-verb")

MEASURE = """(win) => [...win.querySelectorAll('.btn')]
  .filter((b) => b.offsetParent)
  .map((b) => {
    const r = b.getBoundingClientRect();
    const halo = getComputedStyle(b, '::after');
    return {
      word: b.textContent.trim().slice(0, 24),
      cls: b.className,
      h: Math.round(r.height * 10) / 10,
      halo: halo.content !== 'none' ? parseFloat(halo.height) || 0 : 0,
    };
  })"""


@pytest.mark.e2e
@pytest.mark.parametrize("width", [1440, 393])
def test_every_verb_is_one_plate_height(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            project = _api(page, "POST", "/api/projects", {
                "name": "Payments ledger cutover", "command_id": "p16-kit-verb",
            }, token=TOKEN)["project"]["id"]
            page.goto(f"{url}/?token={TOKEN}&open=project:{project}", wait_until="load")
            _normal_chair(page)
            window = page.locator(".drawer-window").last
            window.wait_for(timeout=20_000)
            window.get_by_role("button", name="History", exact=True).wait_for(timeout=20_000)
            _settle(page)
            verbs = window.evaluate(MEASURE)
            words = {v["word"] for v in verbs}
            assert {"Icons", "List", "Room", "History", "Steward", "Get Info", "Open"} <= words, verbs
            if width == 1440:
                heights = {v["h"] for v in verbs}
                assert heights == {28.0}, verbs
            else:
                small = [v for v in verbs if max(v["h"], v["halo"]) < 44]
                assert not small, small
                assert page.evaluate("document.scrollingElement.scrollWidth <= window.innerWidth")
            page.screenshot(path=str(SHOTS / f"kit-verb-{width}.png"))
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
