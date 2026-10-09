"""PHILO-15 lane 12 -- the UGLY bounces of rehearsal 1A, fenced AS RENDERED
through the real hub on an isolated HOME at 1440x900 and 393x852.

The bounces (docs/internal/philo/phase-15/rehearsal-1a/BOUNCES.md):

- B22: the meeting record uses the window's width; no empty column.
- B23: a folder in the SEND well reads by its name (HoldSpeak/Sent), never
  a raw path; a filename is never italics. (The well still opens itself
  when the built-in folder is the only destination: owner ruling 2026-10-05.)
- B27: the Concierge footer receipt never runs into Cancel.
- B28: The week's topic chips and Open fit the width at 393.

Each case measures bounding boxes: nothing past the window's right edge,
no receipt over a verb. The after-shots for B19 (Dock sprites), B24 (the
Intelligence window), B25 (an empty Project) and B30 (a desk label at 393)
are taken here too; their rules are fenced in vitest
(web/src/desk/__tests__/philo15Ugly.test.tsx, web/src/desk/systemSprites.test.ts).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .chair_windows import open_chair_window
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from .runs_on import patch, wait_board
from .test_hs201_one_thing_glass import _quiet_concierge
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the lane 12 glass needs Playwright")

TOKEN = "philo15-12-ugly"
SHOTS = evidence_dir("docs/internal/philo/phase-15/lane-12/shots")
SIZES = {1440: 900, 393: 852}
WIDTHS = list(SIZES)
T = 20_000
TITLE = "philo3_architect_meeting"
LONG_WORD = "Supercalifragilisticexpialidocious"
V2 = "Payments ledger cutover v2"
V3 = "Payments ledger cutover v3"
# A brief item row in Intelligence ▸ BRIEF (BriefView.tsx).
ITEM = "[data-testid=brief-sf-row], [data-testid=brief-tw-meetings], .intelligence-brief-rows li"
TOPICS = ["Local meeting ledger", "Summary retrieval after hub restart",
          "Recorded provider reply for isolated rig tests", "Named failure offense before ship"]
SUMMARY = ("Synthetic architect meeting covering three decisions: adopting SQLite for the local meeting "
           "ledger, keeping summary retrieval on the local desk after a hub restart, and using a recorded "
           "provider reply for isolated rig tests.")

# Every element inside `root` whose box ends past the root's right edge
# (1 px tolerance), and every element that ends past the viewport.
OVERFLOW_JS = """(root) => {
  const r = root.getBoundingClientRect();
  const vw = document.documentElement.clientWidth;
  const out = [];
  for (const e of root.querySelectorAll('*')) {
    const b = e.getBoundingClientRect();
    if (!b.width || !b.height) continue;
    const st = getComputedStyle(e);
    if (st.visibility === 'hidden' || st.display === 'none') continue;
    // The limit is the window's edge, or a nearer CLIPPING parent's edge
    // (overflow hidden/clip cuts the box: that is the bug, not an excuse).
    // A box inside a deliberate scroller (auto/scroll) is skipped.
    let limit = Math.min(r.right, vw), p = e.parentElement, scrolls = false;
    while (p && p !== root) {
      const ox = getComputedStyle(p).overflowX;
      if (/(auto|scroll)/.test(ox) && p.scrollWidth > p.clientWidth + 1) { scrolls = true; break; }
      if (/(hidden|clip)/.test(ox)) limit = Math.min(limit, p.getBoundingClientRect().right);
      p = p.parentElement;
    }
    if (scrolls) continue;
    if (b.right > limit + 1) {
      const chain = [];
      for (let a = e; a && a !== root.parentElement; a = a.parentElement) {
        const ab = a.getBoundingClientRect(), as = getComputedStyle(a);
        chain.push(`${a.tagName}.${String(a.className).split(' ').slice(0, 2).join('.')} w=${Math.round(ab.width)} r=${Math.round(ab.right)} sw=${a.scrollWidth} ox=${as.overflowX} disp=${as.display} gtc=${as.gridTemplateColumns.slice(0, 40)}`);
        if (chain.length > 12) break;
      }
      out.push({tag: e.tagName, cls: String(e.className).slice(0, 60), text: (e.textContent || '').trim().slice(0, 40),
                right: Math.round(b.right), limit: Math.round(limit), chain: out.length ? undefined : chain});
    }
  }
  return out;
}"""

# Every scroller in `root` (and root) that scrolls sideways: its content is
# wider than its box. (An ellipsis clips on purpose; a scroller should not.)
SIDEWAYS_JS = """(root) => [root, ...root.querySelectorAll('*')].filter((e) => {
  const ox = getComputedStyle(e).overflowX;
  return (ox === 'auto' || ox === 'scroll') && e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0
    && !['TEXTAREA', 'INPUT', 'SELECT'].includes(e.tagName);
}).map((e) => ({tag: e.tagName, cls: String(e.className).slice(0, 60), sw: e.scrollWidth, cw: e.clientWidth,
                text: (e.textContent || '').trim().slice(0, 40)}))"""

BOX_JS = "(e) => { const b = e.getBoundingClientRect(); return {x: b.left, y: b.top, w: b.width, h: b.height, r: b.right, btm: b.bottom}; }"


class TestPhilo15Lane12Ugly:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _quiet_concierge(monkeypatch)
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base, self.tmp = server, base, tmp_path
        SHOTS.mkdir(parents=True, exist_ok=True)
        self.facts: dict[str, Any] = {}
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _open(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        return browser, page, errors

    def _seed_meeting(self) -> None:
        from holdspeak.db import get_database
        from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment

        now = datetime.now().replace(microsecond=0)
        seg = [TranscriptSegment(text="Decision one. Use SQLite for the local meeting ledger.", speaker="Recording",
                                 start_time=0.0, end_time=6.0)]
        get_database().meetings.save_meeting(MeetingState(
            id="p15-12-m", started_at=now - timedelta(hours=1), ended_at=now - timedelta(minutes=59),
            title=TITLE, segments=seg, intel_status="completed",
            intel=IntelSnapshot(timestamp=0.0, summary=SUMMARY, topics=TOPICS)))

    def _stage(self, page: Any, key: str, scope: str | None = None) -> None:
        page.evaluate("([key, scope]) => sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify(scope ? {key, scope} : {key}))",
                      [key, scope])
        page.reload(wait_until="load")
        _normal_chair(page)

    def _shot(self, page: Any, name: str, width: int, target: Any = None) -> str:
        _settle(page)
        path = SHOTS / f"after-{name}-{width}.png"
        (target or page).screenshot(path=str(path))
        return str(path)

    def _write(self, name: str, width: int) -> None:
        (SHOTS / f"{name}-{width}.json").write_text(json.dumps(self.facts, indent=2, default=str))

    @staticmethod
    def _overflow(page: Any, root: Any) -> list[dict[str, Any]]:
        return root.evaluate(OVERFLOW_JS)

    # ── B23 + B28: The week and the Brief ────────────────────────────────

    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_week_fits_and_the_send_well_reads_names(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._seed_meeting()
                page.reload(wait_until="load")
                _normal_chair(page)
                week = open_chair_window(page, "The week")
                if width > 720:
                    page.get_by_role("button", name="Zoom The week").click()
                    page.wait_for_timeout(500)
                seat = week.locator("[data-seat=meeting]").first
                seat.locator("[data-testid=destination-row]").first.wait_for(timeout=T)
                page.wait_for_timeout(600)
                _settle(page)

                # B28: every topic chip and the Open verb sit inside the window.
                body = week.locator(".desk-surface-body, .desk-window-body").first
                root = body if body.count() else week
                over = self._overflow(page, root)
                topics = week.locator("[data-testid=meeting-summary-topics] .surface-token")
                assert topics.count() == len(TOPICS), topics.count()
                win_box = week.evaluate(BOX_JS)
                chip_boxes = [topics.nth(i).evaluate(BOX_JS) for i in range(topics.count())]
                open_btn = week.locator("[data-testid=arrival-meeting-open]")
                open_box = open_btn.first.evaluate(BOX_JS) if open_btn.count() else None
                self.facts["B28"] = {"window": win_box, "chips": chip_boxes, "open": open_box, "overflow": over}
                assert not over, over
                # Nothing in the window scrolls sideways (a box past its edge
                # hides inside a scroller otherwise).
                sideways = root.evaluate(SIDEWAYS_JS)
                self.facts["B28"]["sideways"] = sideways
                assert not sideways, sideways
                # Each chip's text stays inside its own box (it wraps).
                ink = topics.evaluate_all("(es) => es.map((e) => [e.scrollWidth, e.clientWidth])")
                self.facts["B28"]["chip_ink"] = ink
                assert all(sw <= cw + 1 for sw, cw in ink), ink
                for b in chip_boxes + ([open_box] if open_box else []):
                    assert b["r"] <= win_box["r"] + 1 and b["r"] <= width + 1, (b, win_box)
                self._shot(page, "B28-the-week", width, week)

                # B23: on a desk whose only destination is the built-in folder, the
                # well opens itself (owner ruling 2026-10-05, batteries included).
                # The folder reads by its name, never a raw path; the filename is
                # not italics.
                row = seat.locator("[data-testid=destination-row]").filter(has=page.locator("[data-destination='HoldSpeak folder']")).first
                line = " ".join(row.inner_text().split())
                self.facts["B23_week_row"] = line
                assert "HoldSpeak/Sent" in line and "/private" not in line and "/var/" not in line, line
                assert "~/" not in line, line
                preview = seat.locator("[data-testid=send-preview]").first
                preview.wait_for(timeout=T)
                fields = {f.locator("dt").inner_text().strip().upper(): f.locator("dd").inner_text().strip()
                          for f in preview.locator("[data-testid=send-preview-field]").all()}
                ems = preview.locator("[data-testid=send-preview-body] em").all_inner_texts()
                body_text = preview.locator("[data-testid=send-preview-body]").inner_text()
                self.facts["B23_week_preview"] = {"fields": fields, "em": ems, "body_head": body_text[:120]}
                assert fields.get("FOLDER") == "HoldSpeak/Sent", fields
                assert not ems, ems
                assert TITLE in body_text, body_text[:200]
                assert not self._overflow(page, preview), self._overflow(page, preview)
                preview.scroll_into_view_if_needed()
                self._shot(page, "B23-week-well", width, seat)

                # The Brief: the same well, the same name.
                _api(page, "POST", "/api/brief/generate", {}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                brief = open_chair_window(page, "Brief")
                bseat = brief.locator("[data-seat=brief]").first
                bseat.locator("[data-testid=destination-row]").first.wait_for(timeout=T)
                page.wait_for_timeout(600)
                bline = " ".join(bseat.locator("[data-testid=destination-row]").first.inner_text().split())
                self.facts["B23_brief_row"] = bline
                assert "HoldSpeak/Sent" in bline and "/private" not in bline and "/var/" not in bline, bline
                bprev = bseat.locator("[data-testid=send-preview]").first
                bprev.wait_for(timeout=T)
                bfields = {f.locator("dt").inner_text().strip().upper(): f.locator("dd").inner_text().strip()
                           for f in bprev.locator("[data-testid=send-preview-field]").all()}
                self.facts["B23_brief_preview"] = bfields
                assert bfields.get("FOLDER") == "HoldSpeak/Sent", bfields
                self._shot(page, "B23-brief-well", width, brief)
                self._write("week-and-brief", width)
                assert not errors, errors
            finally:
                browser.close()

    # ── B22: the meeting record ──────────────────────────────────────────

    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_record_uses_the_window_width(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._seed_meeting()
                self._stage(page, "review-meetings", "meeting:p15-12-m")
                detail = page.locator(".surface-split-detail").first
                detail.locator(".surface-display").first.wait_for(timeout=T)
                page.wait_for_timeout(800)
                _settle(page)

                def measure(tag: str) -> dict[str, Any]:
                    split = page.locator(".surface-split-railed .surface-split").first
                    s = split.evaluate(BOX_JS)
                    d = detail.evaluate(BOX_JS)
                    main = page.locator(".surface-split-railed .surface-split-main").first
                    m = main.evaluate("(e) => { const b = e.getBoundingClientRect(); const st = getComputedStyle(e);"
                                      " return {x: b.left, y: b.top, w: b.width, h: b.height, btm: b.bottom, display: st.display}; }")
                    facts = {"split": s, "detail": d, "rail": m}
                    self.facts[f"B22_{tag}"] = facts
                    # The record takes the split's whole width.
                    assert d["w"] >= s["w"] - 2, facts
                    # The rail is never a column beside it: hidden, or a strip above.
                    if m["display"] != "none" and m["h"] > 0:
                        assert m["btm"] <= d["y"] + 1, facts
                        assert m["w"] >= s["w"] - 2, facts
                    return facts

                measure("normal")
                win = page.locator(".desk-surface-window").filter(has=detail).first
                self._shot(page, "B22-record", width, win)
                if width > 720:
                    page.get_by_role("button", name="Zoom Meetings").click()
                    page.wait_for_timeout(700)
                    _settle(page)
                    page.mouse.wheel(0, 600)
                    page.wait_for_timeout(400)
                    measure("zoomed")
                    self._shot(page, "B22-record-zoomed", width)
                self._write("record", width)
                assert not errors, errors
            finally:
                browser.close()

    # ── B27: the Runs on footer (PHILO-16 C: the Concierge's, ported) ──

    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_runs_on_receipt_never_runs_into_undo(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from .glass_infra import engine_profile

        # One engine on the Default for AI work, the product's way; the
        # board then draws it and a patch writes the receipt beside Undo.
        engine_profile()
        from holdspeak.db import get_database
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        from tests.unit.test_phase143_inference_assignments import _profile

        # A second engine, so the patch is a change at both widths (the
        # phone list never offers the engine a job already runs on).
        _profile(get_database(), "lane12-second-engine")
        InferenceAssignmentService(get_database()).set_assignment(
            Principal(PrincipalKind.OWNER, "lane12-owner"),
            {"command_id": f"lane12-default-{width}", "expected_revision": 0, "scope": {"kind": "global"},
             "entries": [{"profile_id": "hs201-meeting-engine", "profile_revision": 1},
                         {"profile_id": "lane12-second-engine", "profile_revision": 1}]},
        )
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                _normal_chair(page)
                self._stage(page, "open-concierge")
                wait_board(page)
                patch(page, "default", "lane12-second-engine")
                receipt = page.get_by_test_id("runson-receipt")
                undo = page.get_by_test_id("runson-undo")
                undo.wait_for(timeout=T)
                page.wait_for_timeout(600)
                _settle(page)
                rb, cb = receipt.evaluate(BOX_JS), undo.evaluate(BOX_JS)
                text = receipt.inner_text()
                # The text's own box (the span may be wider than its glyphs when it wraps).
                ink = receipt.evaluate("(e) => { const r = document.createRange(); r.selectNodeContents(e);"
                                       " const rs = [...r.getClientRects()]; return rs.map((b) => ({x: b.left, r: b.right, y: b.top, btm: b.bottom})); }")
                self.facts["B27"] = {"receipt": rb, "undo": cb, "text": text, "ink": ink}
                same_row = lambda b: not (b["btm"] <= cb["y"] or b["y"] >= cb["btm"])  # noqa: E731
                assert rb["r"] <= cb["x"] + 0.5 or not same_row(rb), self.facts["B27"]
                for line in ink:
                    if same_row(line):
                        assert line["r"] <= cb["x"] + 0.5, self.facts["B27"]
                assert text.upper().startswith("PATCHED "), text
                footer = page.locator(".surface-footer-layout.runson-foot").first
                self._shot(page, "B27-runson-footer", width, footer)
                self._shot(page, "B27-runson", width)
                self._write("runson", width)
                assert not errors, errors
            finally:
                browser.close()

    # ── the after-shots for B19, B24, B25, B30 ───────────────────────────

    @pytest.mark.parametrize("width", WIDTHS)
    def test_after_shots_dock_intelligence_project_label(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._seed_meeting()
                for outcome in (LONG_WORD, V2, V3):
                    _api(page, "POST", "/api/projects/door", {"outcome": outcome}, token=TOKEN)
                _api(page, "POST", "/api/brief/generate", {}, token=TOKEN)   # Intelligence opens with items
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1200)
                _settle(page)
                # B19: every Dock item on the glass wears a sprite.
                dock = page.locator(".desk-dock").first
                launches = dock.locator(".desk-dock-launch")
                items = []
                for i in range(launches.count()):
                    item = launches.nth(i)
                    if not item.is_visible():
                        continue
                    items.append({"label": item.get_attribute("aria-label"),
                                  "sprite": item.locator("img.desk-dock-sprite").count()})
                self.facts["B19"] = items
                assert items and all(it["sprite"] == 1 for it in items), items
                self._shot(page, "B19-dock", width, dock)
                self._shot(page, "B19-B30-desk", width)

                # B30 (Astra r1): rendered labels on the desk. Each case is REQUIRED:
                # a missing label fails. Lines come from the label's own text.
                def label_lines(name: str) -> dict[str, Any]:
                    el = page.locator(f".desk-icon-name[title='{name}']").first
                    el.wait_for(timeout=T)
                    return el.evaluate("""(e) => ({text: e.innerText, lines: e.innerText.split('\\n'),
                        fitted: e.hasAttribute('data-fitted'), sh: e.scrollHeight, ch: e.clientHeight,
                        sw: e.scrollWidth, cw: e.clientWidth})""")

                b30: dict[str, Any] = {}
                for name in (TITLE, LONG_WORD, V2, V3):
                    got = label_lines(name)
                    b30[name] = got
                    assert got["fitted"], got
                    assert len(got["lines"]) <= 2, got            # the clamp hides nothing
                    assert got["sh"] <= got["ch"] + 1 and got["sw"] <= got["cw"] + 1, got
                # An underscore join is where it breaks (and the end stays).
                assert b30[TITLE]["lines"][0].endswith("_"), b30[TITLE]
                assert b30[TITLE]["lines"][-1].endswith("meeting"), b30[TITLE]
                # An unbroken overlong word: one line, cut with an ellipsis, never split.
                assert len(b30[LONG_WORD]["lines"]) == 1 and "…" in b30[LONG_WORD]["text"], b30[LONG_WORD]
                # Two names that differ only in their end: both ends visible.
                assert b30[V2]["text"].rstrip().endswith("v2"), b30[V2]
                assert b30[V3]["text"].rstrip().endswith("v3"), b30[V3]
                assert b30[V2]["text"] != b30[V3]["text"]
                self.facts["B30"] = b30
                self._shot(page, "B30-labels", width)

                # B24 (Astra r1): the Intelligence window opens AT its declared size
                # (rendered, not only the rect), with its first items in view;
                # a size he saved wins on the next open.
                if width > 720:
                    dock.locator("[data-app='intelligence:desk']").click()
                    win = page.locator(".desk-pullout:has(.intelligence-pullout)").first
                    win.wait_for(timeout=T)
                    first = win.locator(ITEM).first
                    first.wait_for(timeout=T)
                    page.wait_for_timeout(900)
                    _settle(page)
                    box = win.evaluate(BOX_JS)
                    item = first.evaluate(BOX_JS)
                    tops = win.locator(".intelligence-segment").evaluate_all(
                        "(es) => es.map((e) => Math.round(e.getBoundingClientRect().top))")
                    self.facts["B24"] = {"window": box, "first_item": item, "segment_tops": tops,
                                         "items": win.locator(ITEM).count()}
                    assert box["w"] >= 600, box
                    assert box["h"] >= 600, box                    # the declared 620, rendered
                    assert len(set(tops)) <= 1, tops
                    assert item["btm"] <= box["btm"] and item["y"] >= box["y"], (item, box)
                    self._shot(page, "B24-intelligence", width)
                    # He sizes it smaller; the saved size wins on the next open.
                    grip = win.locator(".desk-window-grip").first
                    g = grip.evaluate(BOX_JS)
                    page.mouse.move(g["x"] + g["w"] / 2, g["y"] + g["h"] / 2)
                    page.mouse.down()
                    page.mouse.move(g["x"] + g["w"] / 2 - 120, g["y"] + g["h"] / 2 - 160, steps=8)
                    page.mouse.up()
                    page.wait_for_timeout(500)
                    saved = win.evaluate(BOX_JS)
                    assert saved["w"] < box["w"] - 60 and saved["h"] < box["h"] - 60, (saved, box)
                    win.get_by_role("button", name=re.compile(r"^Close ")).first.click()
                    win.wait_for(state="detached", timeout=T)
                    page.reload(wait_until="load")
                    _normal_chair(page)
                    page.locator(".desk-dock [data-app='intelligence:desk']").click()
                    again = page.locator(".desk-pullout:has(.intelligence-pullout)").first
                    again.wait_for(timeout=T)
                    page.wait_for_timeout(900)
                    reopened = again.evaluate(BOX_JS)
                    self.facts["B24"]["saved"] = saved
                    self.facts["B24"]["reopened"] = reopened
                    assert abs(reopened["w"] - saved["w"]) <= 2 and abs(reopened["h"] - saved["h"]) <= 2, (reopened, saved)
                    self._shot(page, "B24-intelligence-saved-size", width)
                    again.get_by_role("button", name=re.compile(r"^Close ")).first.click()

                # B25: an empty Project from the Door reads NEW, its receipt CREATE.
                made = _api(page, "POST", "/api/projects/door", {"outcome": "Payments ledger cutover"}, token=TOKEN)
                pid = made.get("projectId")
                assert pid, made
                self._stage(page, "open-project-memory", f"project:{pid}")
                room = page.locator("[data-testid=room-head]").first
                room.wait_for(timeout=T)
                page.wait_for_timeout(1200)
                _settle(page)
                chip = page.locator("[data-testid=room-health-word]")
                self.facts["B25"] = {"head": room.inner_text(),
                                     "word": chip.first.inner_text() if chip.count() else None}
                assert chip.count() and "NEW" in chip.first.inner_text(), self.facts["B25"]
                assert "ON TRACK" not in room.inner_text(), self.facts["B25"]
                body_text = page.locator("#surface-project-memory").inner_text()
                assert "CREATE FROM SETUP" not in body_text, body_text[:400]
                self._shot(page, "B25-project", width)
                self._write("after", width)
                assert not errors, errors
            finally:
                browser.close()
