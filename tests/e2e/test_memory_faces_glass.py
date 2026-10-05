"""Memory on the Desk glass (canvas section 2, option B "Where the work lives",
ratified 2026-10-05), at 1440 and 393.

* **beliefs** -- Desk memory, query `cutover`: a CURRENT belief with its old
  text struck through under HISTORY, two DISPUTED beliefs (one ref reads
  `AGAINST · MTG ...`), a SUPERSEDED one with `SINCE`.
* **pages** -- the Atlas Room: STANDING PAGES under the head; one page
  STALE with its warn border and `STALE · 1 NEW SOURCE`.
* **desk** -- Intelligence -> BRIEF: the desk's standing pages.
* **person** -- withheld (no person scope exists): never drawn.

Every belief and page is produced inside the isolated HOME through the real
sweep, extract, consolidate and page paths with the slice 4 and slice 5
fixture engines.  Each board is scanned against UX-CANON A: every verb the
library Button, no counter of zero, no egress chip, no "Rewrite" verb.
Shots land in MEMORY_FACES_SHOTS (default: this session's scratchpad).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="memory faces glass needs Playwright")

SHOTS = Path(os.environ.get(
    "MEMORY_FACES_SHOTS",
    "/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/"
    "3ed420bf-5c67-4b0b-a6d6-c2c54896e5e9/scratchpad/memory-faces-shots",
))
SHOTS.mkdir(parents=True, exist_ok=True)
TOKEN = "memory-faces"
T = 15000


def _seed() -> None:
    """Beliefs and pages through the real paths, in the hub's own database."""
    from holdspeak.db import get_database
    from holdspeak.memory.pages import spec_for, write_page, write_pending
    from holdspeak.memory.retain import sweep
    from tests.unit.test_memory_slice4_observations import Rules, _filed_note, _learn, _meeting
    from tests.unit.test_memory_slice5_pages import Pages

    db = get_database()
    db.projects.create_project(project_id="atlas", name="Atlas cutover")
    _meeting(db, "m-0924", "Cutover date is 10-10. Cutover rollback owner is Marek.", day=24)
    _learn(db)
    _filed_note(db, "n-1001", "Cutover date is 10-17.", "atlas")
    _learn(db)  # supersedes the 10-10 belief
    _meeting(db, "m-0929", "Cutover rollback owner is Priya.", day=29)
    _learn(db, Rules("contradicts"))
    _filed_note(db, "n-desk-1", "Hiring loop reply is owed.", None)
    _filed_note(db, "n-desk-2", "Billing contract is waiting.", None)
    _learn(db)
    write_pending(db, Pages())
    # One new Atlas source after the pages were built: every Atlas page is
    # stale; three are written again, so ONE stays stale (the board).
    _filed_note(db, "n-1003", "Cutover freeze is 10-12.", "atlas")
    sweep(db)
    for slug in ("what-we-decided", "what-is-open", "risks-and-disputes"):
        write_page(db, Pages(), ("project", "atlas"), spec_for("project", slug))


_CANON_JS = """(sel) => {
  const roots = [...document.querySelectorAll(sel)];
  if (!roots.length) return { error: "no face " + sel };
  const q = (s) => roots.flatMap((r) => [...r.querySelectorAll(s)]);
  const LIBRARY = ["btn", "btn--chrome", "desk-mic", "surface-row-open"];
  const rawButtons = q("button")
    .filter((b) => !LIBRARY.some((c) => b.classList.contains(c)))
    .map((b) => (b.className || "") + "|" + (b.textContent || "").trim().slice(0, 30));
  const zeros = q(".surface-token, [data-chip], .surface-section-head h3")
    .map((n) => (n.textContent || "").trim())
    .filter((t) => /(^|\\s)0(\\s|$)/.test(t));
  const egress = q(".gadget-chip-egress").length;
  const rewrite = q("button").filter((b) => /rewrite/i.test(b.textContent || "")).length;
  return { rawButtons, zeros, egress, rewrite };
}"""


def _canon(page: Any, sel: str) -> None:
    scan = page.evaluate(_CANON_JS, sel)
    assert "error" not in scan, scan
    assert scan["rawButtons"] == [], f"raw <button> (A.1): {scan['rawButtons']}"
    assert scan["zeros"] == [], f"counter of zero (A.8): {scan['zeros']}"
    assert scan["egress"] == 0, "memory reads locally: no egress chip (A.9)"
    assert scan["rewrite"] == 0, "no on-demand rewrite exists: no Rewrite verb"


def _zoom(page: Any, window: Any, width: int) -> None:
    """At 1440 the face fills the work area (double-click the title bar):
    the board shows one window, not the Chair's stack behind it."""
    if width >= 1000:
        window.locator(".desk-window-title").first.dblclick()
        page.wait_for_timeout(600)


def _top(page: Any, window: Any, inner: str) -> None:
    window.locator(inner).first.evaluate("el => el.scrollIntoView({block: 'start'})")
    page.wait_for_timeout(200)


def _shots(page: Any, name: str, width: int, face: Any) -> None:
    _settle(page)
    page.screenshot(path=str(SHOTS / f"{name}-{width}.png"), full_page=False)
    if width >= 1000:
        face.screenshot(path=str(SHOTS / f"{name}-{width}-face.png"))
    print(f"[memory-faces] {SHOTS / name}-{width}")


def _stage(page: Any, key: str, scope: str | None = None) -> None:
    page.evaluate(
        """([key, scope]) => {
          localStorage.removeItem("hs.desk.workspace.v1");
          sessionStorage.setItem("hs.desk.staged-surface-open",
            JSON.stringify(scope ? {key, scope} : {key}));
        }""",
        [key, scope],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator(".desk-surface-window").first.wait_for(timeout=T)


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.timeout(600)
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_memory_on_the_desk(tmp_path, monkeypatch, width, height):
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        _seed()
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": width, "height": height})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            _normal_chair(page)
            # The Brief's own head (its real producer), so the desk board
            # shows the pages under a brief, as ratified.
            _api(page, "POST", "/api/brief/generate", None, token=TOKEN)

            # ── beliefs: Desk memory, `cutover` ──
            _stage(page, "open-project-memory")
            page.get_by_role("searchbox", name="Search the Desk").fill("cutover")
            page.locator(".desk-surface-window").get_by_role("button", name="Search desk memory", exact=True).click()
            page.get_by_test_id("recall-belief").first.wait_for(timeout=T)
            states = page.get_by_test_id("recall-belief").evaluate_all("els => els.map(e => e.dataset.state)")
            assert states == ["current", "disputed", "disputed", "superseded"], states
            heads = page.locator(".recall-results .surface-section-head h3").all_text_contents()
            assert heads[:3] == ["CURRENT 1", "DISPUTED 2", "SUPERSEDED 1"], heads
            current = page.get_by_test_id("recall-belief").first
            assert current.get_by_test_id("recall-belief-old").text_content() == "Cutover date is 10-10."
            assert page.get_by_role("button", name="Open the source: AGAINST · MTG 09-29 · 10:00").count() == 1
            assert page.get_by_test_id("recall-belief-since").count() == 1
            _canon(page, ".desk-surface-window")
            memory = page.locator(".desk-surface-window").first
            _zoom(page, memory, width)
            _top(page, memory, ".recall-head")
            _shots(page, "mem-B-beliefs", width, memory)
            # A ref opens a real Desk window: the meeting.
            page.get_by_role("button", name="Open the source: AGAINST · MTG 09-29 · 10:00").click()
            page.wait_for_timeout(1200)
            assert page.locator(".desk-window, .desk-surface-window").count() >= 2

            # ── pages: the Atlas Room ──
            _stage(page, "open-project-memory", "project:atlas")
            page.get_by_test_id("standing-pages").wait_for(timeout=T)
            titles = page.get_by_test_id("standing-page").evaluate_all("els => els.map(e => e.ariaLabel)")
            assert titles == ["What did we decide", "What is open and who owes it",
                              "Risks and disputes", "What changed this week"], titles
            stale = page.locator("[data-testid=standing-page][data-stale]")
            assert stale.count() == 1 and stale.get_attribute("aria-label") == "What changed this week"
            assert "STALE · 1 NEW SOURCE" in stale.get_by_test_id("standing-page-stale").text_content()
            assert "Harbor" not in page.get_by_test_id("standing-pages").text_content()
            _canon(page, ".desk-surface-window [data-testid=standing-pages]")
            room = page.locator(".desk-surface-window").first
            _zoom(page, room, width)
            _top(page, room, ".room-body")
            _shots(page, "mem-B-pages", width, room)

            # ── desk: the Brief (Intelligence -> BRIEF) ──
            page.evaluate("""() => { localStorage.removeItem("hs.desk.workspace.v1"); }""")
            page.reload(wait_until="load")
            _normal_chair(page)
            page.locator("button.desk-dock-app").first.click()
            page.locator(".desk-window .intelligence-pullout").first.wait_for(timeout=T)
            page.locator(".intelligence-segment", has_text="BRIEF").first.click()
            brief = page.locator(".desk-window:has(.intelligence-pullout)").first
            brief.get_by_test_id("standing-pages").wait_for(timeout=T)
            titles = brief.get_by_test_id("standing-page").evaluate_all("els => els.map(e => e.ariaLabel)")
            assert titles == ["What I owe", "What changed this week"] or titles == ["What changed this week"], titles
            text = brief.get_by_test_id("standing-pages").text_content()
            assert "Atlas" not in text and "Cutover" not in text
            _canon(page, ".desk-window:has(.intelligence-pullout) [data-testid=standing-pages]")
            _zoom(page, brief, width)
            _top(page, brief, ".intelligence-brief")
            _shots(page, "mem-B-desk", width, brief)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
