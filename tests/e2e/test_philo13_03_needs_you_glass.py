"""PHILO-13-03 (A2-W) -- ONE meaning of "needs you", fenced AS RENDERED.

Through the real hub on an isolated HOME, at 1440x900 (mouse) and 393x852
(touch: every press a tap). The oracle week is minted through the real
producers (``scripts/philo13_needs_you_fixture.py`` ``seed_week``: meetings
through ``save_meeting``, the Room row through the proposal bridge, the mute
through heartbeat settings, no engine assigned); the hub then restarts on
that database, as the Dock atlas case does.

  * The Chair head, the bell and the Dock all show the same number: 6.
  * No visible "need(s) you" text on the glass carries another number.
  * Done on A1 (the Chair row's own Done) -> all three read 5 within 1 s,
    with no reload. The measured latency is written beside the shots.
  * The narrower counts name what they count: the Chair list ``ACTIONS``,
    Meetings never "needs you", the Room ``n open here`` / ``Clear here``.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

# PHILO-14 A1: the Chair is the screen of objects; these specs read its windows (tests/conftest.py).
pytestmark = pytest.mark.chair_windows_open

pytest.importorskip("playwright.sync_api", reason="the needs-you glass needs Playwright")

TOKEN = "philo13-03-needs-you"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-03-shots")
SIZES = {1440: 900, 393: 852}
A1_TASK = "A1 close the overdue release note"

# The three readers of the ONE number, and every "need(s) you" on the glass.
READERS = r"""() => {
  const num = (e) => { const m = ((e && e.innerText) || '').match(/\d+/); return m ? Number(m[0]) : null; };
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const said = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const t = n.textContent.replace(/\s+/g, ' ').trim();
    if (/needs? you/i.test(t) && vis(n.parentElement)) said.push(t);
  }
  for (const e of document.querySelectorAll('[aria-label]')) {
    const t = e.getAttribute('aria-label');
    if (/\d+\s+needs? you/i.test(t)) said.push('aria:' + t);
  }
  const head = document.querySelector('[data-testid=arrival-display]');
  const bell = document.querySelector('.desk-bell strong');
  const intel = document.querySelector('.desk-dock [aria-label^="Intelligence"] .desk-dock-badge');
  const memory = document.querySelector('.desk-dock [aria-label^="Desk memory"] .desk-dock-badge');
  return { said, head: head ? head.innerText : null, head_n: num(head), bell: num(bell),
           intel: num(intel), memory: memory ? num(memory) : null };
}"""

# Resolves with the milliseconds from the press until head, bell and Dock all
# read `target` (polled each animation frame; no reload in between).
AGREE = r"""(target) => new Promise((resolve) => {
  const t0 = window.__p13PressAt;
  const read = (sel) => { const e = document.querySelector(sel); const m = ((e && e.innerText) || '').match(/\d+/); return m ? Number(m[0]) : null; };
  const tick = () => {
    const head = read('[data-testid=arrival-display]');
    const bell = read('.desk-bell strong');
    const intel = read('.desk-dock [aria-label^="Intelligence"] .desk-dock-badge');
    if (head === target && bell === target && intel === target) {
      resolve({ ms: Math.round(performance.now() - t0), head, bell, intel });
      return;
    }
    if (performance.now() - t0 > 10000) { resolve({ ms: null, head, bell, intel }); return; }
    requestAnimationFrame(tick);
  };
  tick();
})"""


def _numbers_said(said: list[str]) -> list[int]:
    out: list[int] = []
    for text in said:
        for match in re.finditer(r"(\d+)\s+needs?\s+you", text, re.IGNORECASE):
            out.append(int(match.group(1)))
    return out


class TestOneNeedsYou:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        from scripts.philo13_needs_you_fixture import seed_week

        server, _ = _boot(tmp_path, monkeypatch, token=TOKEN)
        try:
            self.week = seed_week(tmp_path / "holdspeak.db", home=tmp_path)
        finally:
            server.stop()
        # The hub restarts on the seeded database (the Dock atlas case's
        # `seed_needs_you_week` restart): no cached projection survives.
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.evaluate("() => { window.__p13PressAt = performance.now(); }")
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            page.evaluate("() => { window.__p13PressAt = performance.now(); }")
            loc.click()

    @staticmethod
    def _shot(page: Any, name: str, width: int) -> None:
        _settle(page)
        page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))

    @staticmethod
    def _staged_open(page: Any, key: str, scope: str | None = None) -> None:
        page.evaluate(
            """([key, scope]) => sessionStorage.setItem(
                 "hs.desk.staged-surface-open", JSON.stringify(scope ? {key, scope} : {key}))""",
            [key, scope],
        )
        page.reload(wait_until="load")
        _normal_chair(page)

    def _agree_on(self, page: Any, n: int) -> dict[str, Any]:
        page.wait_for_function(
            """(n) => {
              const r = (s) => { const e = document.querySelector(s); const m = ((e && e.innerText) || '').match(/\\d+/); return m ? Number(m[0]) : null; };
              return r('[data-testid=arrival-display]') === n && r('.desk-bell strong') === n
                && r('.desk-dock [aria-label^="Intelligence"] .desk-dock-badge') === n;
            }""",
            arg=n, timeout=20_000,
        )
        return page.evaluate(READERS)

    @pytest.mark.parametrize("width", list(SIZES))
    def test_one_number_everywhere_and_done_moves_all_three(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        record: dict[str, Any] = {"width": width, "touch": width < 720,
                                  "oracle": {"expectedRefs": self.week["expectedRefs"],
                                             "expectedCount": self.week["expectedCount"]}}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # ── one number: 6 on the head, the bell and the Dock ──
                before = self._agree_on(page, 6)
                record["before"] = before
                assert before["head_n"] == before["bell"] == before["intel"] == 6, before
                if before["memory"] is not None:
                    assert before["memory"] == 6, before
                said = _numbers_said(before["said"])
                assert said and all(n == 6 for n in said), before["said"]

                # ── the narrower list names what it counts ──
                section = page.locator("[data-testid='arrival-needs-you']")
                caption = section.locator(".surface-caption, .surface-section-label, h2, h3").first.inner_text().strip()
                record["chair_caption"] = caption
                assert re.fullmatch(r"ACTIONS \d+( OF \d+)?", caption), caption
                assert not re.search(r"needs? you", section.inner_text(), re.IGNORECASE)
                self._shot(page, "a2w-chair-6", width)

                # ── Done on A1 -> all three read 5 within 1 s, no reload ──
                row = page.locator("[data-testid='arrival-needs-you-row']", has_text=A1_TASK).first
                done = row.get_by_role("button", name=re.compile(r"^Done: "))
                nav = []
                page.on("framenavigated", lambda frame: nav.append(frame.url))
                self._press(page, done, width)
                latency = page.evaluate(AGREE, 5)
                record["done_latency"] = latency
                assert latency["ms"] is not None, latency
                assert latency["ms"] <= 1000, latency
                assert not nav, f"the page navigated: {nav}"
                after = page.evaluate(READERS)
                record["after"] = after
                if after["memory"] is not None:
                    assert after["memory"] == 5, after
                said = _numbers_said(after["said"])
                assert said and all(n == 5 for n in said), after["said"]
                self._shot(page, "a2w-chair-done-5", width)

                # ── Meetings counts summaries, never "needs you" ──
                self._staged_open(page, "review-meetings")
                page.locator(".desk-surface-window").first.wait_for(timeout=15_000)
                page.locator(".meetings-headline, [data-testid='meetings-headline'], .surface-display").first.wait_for(timeout=15_000)
                _settle(page)
                meetings = page.evaluate(READERS)
                record["meetings"] = {"said": meetings["said"]}
                window_text = page.locator(".desk-surface-window").first.inner_text()
                record["meetings"]["headline"] = page.locator(".desk-surface-window .surface-display").first.inner_text()
                assert not re.search(r"needs? you", window_text, re.IGNORECASE), window_text[:400]
                assert all(n == 5 for n in _numbers_said(meetings["said"])), meetings["said"]
                self._shot(page, "a2w-meetings", width)

                # ── the Room counts its own open items ──
                self._staged_open(page, "open-project-memory", f"project:{self.week['ids']['project']}")
                head = page.locator("[data-testid='room-headline']")
                head.wait_for(timeout=15_000)
                _settle(page)
                room_head = head.inner_text().strip()
                record["room"] = {"headline": room_head}
                assert re.fullmatch(r"\d+ open here|Clear here", room_head), room_head
                room = page.evaluate(READERS)
                record["room"]["said"] = room["said"]
                assert all(n == 5 for n in _numbers_said(room["said"])), room["said"]
                room_window = page.locator("[data-testid='room-headline']").locator(
                    "xpath=ancestor::*[contains(@class,'desk-surface-window') or contains(@class,'desk-window-shell')][1]")
                if room_window.count():
                    text = room_window.first.inner_text()
                    record["room"]["open_here"] = bool(re.search(r"OPEN HERE", text))
                    assert not re.search(r"NEEDS YOU", text), text[:400]
                self._shot(page, "a2w-room", width)

                record["page_errors"] = errors
                assert not errors, errors
            finally:
                (SHOTS / f"a2w-glass-{width}.json").write_text(json.dumps(record, indent=2, default=str))
                browser.close()


# ── Astra's pass on #736: Meetings says `All summaries done` only when true ──

HEADLINE_CASES = {
    "stored": "All summaries done",
    "running": "1 summary running",
    "retrying": "1 summary queued",
}


def _mint_headline_case(tmp_path: Path, name: str) -> None:
    """One meeting through the stop-handoff producer and the REAL intel queue
    executor (``scripts/philo13_meetings_headline_fixture.py``), copied into
    the hub's database at the instant its list row was read (a held run is
    copied while the provider holds it)."""
    import sqlite3

    import scripts.philo13_meetings_headline_fixture as fixture

    rig = tmp_path / "rig"
    rig.mkdir()

    def copy(_db: Any) -> None:
        src = sqlite3.connect(rig / name / "queue.db")
        dst = sqlite3.connect(tmp_path / "holdspeak.db")  # _boot's DEFAULT_DB_PATH
        src.backup(dst)
        src.close()
        dst.close()

    fixture.ON_READ = copy
    try:
        rows = fixture._case(rig, name, fixture.CASES[name])
    finally:
        fixture.ON_READ = None
    assert [r["id"] for r in rows] == [fixture.MEETING_ID], rows


class TestMeetingsHeadlineTellsTheTruth:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
        _ensure_build()
        self.case = request.node.callspec.params["case"]
        _mint_headline_case(tmp_path, self.case)
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("case", list(HEADLINE_CASES))
    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_meetings_headline_names_the_live_fact(self, width: int, case: str) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = TestOneNeedsYou._page(self, pw, width)  # type: ignore[arg-type]
            try:
                wire = _api(page, "GET", "/api/meetings?limit=20", token=TOKEN)["meetings"]
                assert len(wire) == 1, wire
                page.wait_for_timeout(1000)
                _settle(page)
                TestOneNeedsYou._press(
                    page, page.locator(".desk-dock-launch[aria-label^='Meetings']"), width)
                window = page.locator(".desk-window[aria-label='Meetings']")
                head = window.locator(".surface-display").first
                head.wait_for(timeout=15_000)
                page.wait_for_function(
                    "(el) => el.innerText.trim().length > 0", arg=head.element_handle(), timeout=15_000)
                _settle(page)
                text = head.inner_text().strip()
                (SHOTS / f"a2w-meetings-headline-{case}-{width}.json").write_text(json.dumps({
                    "case": case, "width": width, "headline": text,
                    "wire": {k: wire[0].get(k) for k in ("id", "intel_status", "has_summary", "intel_job")},
                }, indent=2, default=str))
                TestOneNeedsYou._shot(page, f"a2w-meetings-headline-{case}", width)
                assert text == HEADLINE_CASES[case], (case, text, wire[0].get("intel_status"))
                assert not errors, errors
            finally:
                browser.close()
