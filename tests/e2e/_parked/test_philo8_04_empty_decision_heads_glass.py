"""PHILO-8-04 (a) -- the decision window shows no heading with nothing under it.

The owner opens a decision from the menubar Search. The read view shows the
"Decision context", "Decision" and "Consequences" headings only when the
field has text (UX-CANON: no empty labels). Edit still offers all three
fields, so he can fill an empty one. Read on the real page through the real
hub at 1440 and 393.

Red on main: ``web/src/desk/pullouts/DecisionPullout.tsx:113-115`` drew the
three headings unconditionally, so a title-only decision showed three
headings with nothing under them (BACKLOG "PHILO-7-04 follow-ups" row 1).
The third case is the Phase 7 story 04 shot case (context + decision, the
owner's words): both headings still show, "Consequences" does not.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the decision-heads glass needs Playwright")

TOKEN = "philo8-empty-heads"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-04-shots")

HEADS = ("Decision context", "Decision", "Consequences")

# (slug, title, fields, the headings the read view must show)
CASES: list[tuple[str, str, dict[str, str], tuple[str, ...]]] = [
    ("title-only", "Glass title only decision", {}, ()),
    (
        "context-only",
        "Glass context only decision",
        {"context_markdown": "Our own runners are full every night."},
        ("Decision context",),
    ),
    (
        "context-and-decision",
        "Move the nightly build to the shared runners",
        {
            "context_markdown": (
                "Our own runners are full every night. "
                "The shared runner pool has spare capacity after 8 PM."
            ),
            "decision_markdown": "Move the nightly build to the shared runners.",
        },
        ("Decision context", "Decision"),
    ),
]

_HEADS_JS = """(card) => Array.from(card.querySelectorAll('h3'))
  .filter((h) => h.offsetParent !== null)
  .map((h) => (h.textContent || '').trim())"""


def _open_decision(page: Any, title: str, decision_id: str) -> Any:
    page.locator("[aria-controls=desk-tool-shelf]").click()
    page.locator("[aria-controls=desk-palette-listbox]").fill(title)
    page.locator(f"[id='desk-palette-option-decision:{decision_id}']").click()
    region = page.locator(f"[role=region][aria-label='{title}']")
    region.locator(".desk-decision-card").wait_for(timeout=15_000)
    return region


class TestEmptyDecisionHeadsGlass:
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
    def test_a_heading_shows_only_with_text_under_it(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": width, "height": 900})
                errors: list[str] = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                ids = {}
                for slug, title, fields, _ in CASES:
                    created = _api(page, "POST", "/api/decisions",
                                   {"title": title, "status": "proposed", **fields}, token=TOKEN)
                    ids[slug] = created["decision"]["id"]

                for slug, title, _fields, want in CASES:
                    page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                    _normal_chair(page)
                    region = _open_decision(page, title, ids[slug])
                    card = region.locator(".desk-decision-card")
                    _settle(page)
                    heads = [h for h in card.evaluate(_HEADS_JS) if h in HEADS]
                    page.screenshot(path=str(SHOTS / f"{slug}-{width}.png"))
                    assert tuple(heads) == want, f"{slug} at {width}: headings {heads}, want {list(want)}"

                    if slug == "title-only":
                        # Edit still offers all three fields, so he can fill them.
                        region.get_by_role("button", name="Edit", exact=True).click()
                        editor = card.locator(".desk-decision-editor")
                        editor.wait_for(timeout=5_000)
                        for label in ("Context", "Decision", "Consequences"):
                            field = editor.get_by_label(label, exact=True)
                            assert field.count() == 1 and field.is_visible(), f"Edit: no {label} field at {width}"
                        _settle(page)
                        page.screenshot(path=str(SHOTS / f"{slug}-edit-{width}.png"))
                        region.get_by_role("button", name="Cancel", exact=True).click()
                    _assert_clean(page, errors)
                print(f"{width}: {ids}")
            finally:
                browser.close()
