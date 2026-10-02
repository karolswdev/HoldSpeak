"""PHILO-13-11 (C1) -- the Workbench frame, fenced AS RENDERED.

The owner ratified the canvas on 2026-10-02 ("Ratify, build it"; "Steel";
story-11 §RATIFIED). The canvas fences (assets/story-11-canvas/harness/
shoot.py) that apply to the FRAME are ported here onto the product itself:
no canvas CSS, no seat, no shim. Through the real hub on an isolated HOME at
1440x900 (mouse) and 393x852 (touch).

The fences (each records its findings in ``frame-facts-<width>.json``):

  F1 one blue front window: exactly one window title bar is blue, and the
     screen title bar names that window.
  F2 gadget ownership: close is the head's first control and iconify, zoom
     its last (1440); every frame control owns all nine of its probe points
     (``elementFromPoint``), unless a window in front covers the point.
  F3 nothing clips, nothing scrolls sideways in the frame: no text in the
     screen bar, a title bar or an open menu runs past its clipping box
     (single-line ellipsis is recorded, not failed), and no strip of choices
     scrolls sideways.
  F4 393: the front window's content is >= 700 px, and every frame target
     (screen bar, title bar, strip menu) owns at least 44 x 44.
  F5 frame text in place: every text on the screen bar, a title bar and an
     open menu is >= 12 px and reads >= 4.5:1 (>= 3:1 large) on the colour
     it actually sits on.

Seeded through the real producers on the rig's own database (the canvas seed,
``assets/story-11-canvas/harness/seed_db.py``, trimmed to what the frame
shows) before the page loads. Shots go to
pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-build/ under
HOLDSPEAK_EVIDENCE_WRITE=1 (``.tmp/evidence-shots/`` otherwise).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the frame glass needs Playwright")

TOKEN = "philo13-11-frame"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-build")
SIZES = {1440: 900, 393: 852}
ROOM = "Payments ledger cutover"


def _seed() -> None:
    """The canvas seed's projects, records, meetings and people, minted by
    the real producers into this rig's database (the singleton _boot reset)."""
    from holdspeak.db import get_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.people import production_people_store
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.monday_brief_service import MondayBriefService
    from holdspeak.services.people_service import PeopleService
    from holdspeak.services.primitive_service import PrimitiveService

    db = get_database()
    owner = Principal(PrincipalKind.OWNER, "karol")
    now = datetime.now()
    for pid, name, desc in [
        ("p-ledger", ROOM, "Move settlement to the new ledger by Nov 5."),
        ("p-obs", "Platform observability", "One tracing stack for all services."),
    ]:
        db.projects.create_project(project_id=pid, name=name, description=desc, keywords=name.lower().split()[:3])
    prim = PrimitiveService(db)
    prim.create_decision(owner, decision_id="d-otel", title="Adopt OpenTelemetry for all services",
                         status="proposed", decision_markdown="Use the OTel SDK in every service.")
    prim.create_note(owner, note_id="n-1", title="Ledger cutover risks",
                     body_markdown="- reconciliation job slow", tags=["week40"])
    for mid, title, hours_ago, pid, summary in [
        ("m-standup", "Ledger cutover sync", 2, "p-ledger", "Dual-write is stable. Freeze the old ledger on Nov 5."),
        ("m-arch", "Architecture review: tracing", 26, "p-obs", "OpenTelemetry chosen. Sam pilots it in billing."),
    ]:
        start = (now - timedelta(hours=hours_ago)).replace(microsecond=0)
        db.meetings.save_meeting(MeetingState(
            id=mid, started_at=start, ended_at=start + timedelta(minutes=30), title=title,
            segments=[TranscriptSegment(text=summary, speaker="Me", start_time=1.0, end_time=4.0)],
            intel=IntelSnapshot(timestamp=1.0, topics=["ledger"], summary=summary, action_items=[]),
            intel_status="completed"))
        db.projects.associate_meeting_project(meeting_id=mid, project_id=pid, source="manual", confidence=1.0)
    store = production_people_store()
    store.initialize()
    people = PeopleService(store)
    for name, kind in [("Avery Chen", "direct_report"), ("Jordan Patel", "direct_report"),
                       ("Sam Rivera", "direct_report"), ("Priya Nair", "peer")]:
        people.create_relationship(owner, {"display_name": name, "relationship_kind": kind,
                                           "role_context": "Engineer", "cadence": "weekly"})
    MondayBriefService(db).generate(owner, now=now)


# ── the measures (run in the page) ──────────────────────────────────────

FRAME_JS = r"""(width) => {
  const rgb = (s) => { const m = String(s).match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const blend = (top, under) => ({r: top.r * top.a + under.r * (1 - top.a), g: top.g * top.a + under.g * (1 - top.a),
    b: top.b * top.a + under.b * (1 - top.a), a: 1});
  const groundOf = (el) => { const chain = []; for (let e = el; e; e = e.parentElement) {
      const c = rgb(getComputedStyle(e).backgroundColor); if (c && c.a > 0) { chain.push(c); if (c.a >= 1) break; } }
    let g = {r: 0, g: 0, b: 0, a: 1}; for (let i = chain.length - 1; i >= 0; i--) g = blend(chain[i], g); return g; };
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && Number(cs.opacity) > 0.05; };
  const label = (e) => (e.getAttribute('aria-label') || e.textContent || e.className || '').trim().slice(0, 50);
  const shells = [...document.querySelectorAll('.desk-window-shell')].filter(visible);
  const heads = shells.map((s) => s.querySelector(':scope > .desk-pullout-head')).filter(Boolean);
  const menus = [...document.querySelectorAll('.desk-menu-list')].filter(visible);
  const bar = document.querySelector('.desk-menubar');
  const scopes = [bar, ...heads, ...menus].filter(Boolean);
  const out = {width, windows: shells.length, blue: [], front: [], screen: null,
    layout: [], ownership: [], clipped: [], ellipsis: [], sideways: [], content: null, small_targets: [],
    small_text: [], low_contrast: []};

  // F1 one blue front window; the screen bar names it
  const BLUE = {r: 102, g: 136, b: 187};
  for (const h of heads) { const c = rgb(getComputedStyle(h).backgroundColor);
    if (c && Math.abs(c.r - BLUE.r) < 3 && Math.abs(c.g - BLUE.g) < 3 && Math.abs(c.b - BLUE.b) < 3)
      out.blue.push(h.parentElement.getAttribute('aria-label')); }
  out.front = shells.filter((s) => s.classList.contains('is-front')).map((s) => s.getAttribute('aria-label'));
  const st = document.querySelector('[data-testid="desk-screen-title"]');
  out.screen = st ? st.textContent.trim() : null;

  // F2 the gadget layout and ownership by hit test
  for (const h of heads) {
    const btns = [...h.querySelectorAll('button')].filter(visible);
    const name = h.parentElement.getAttribute('aria-label');
    const first = btns[0], last = btns.slice(-2);
    if (!first || first.getAttribute('aria-label') !== `Close ${name}`) out.layout.push({name, first: first && label(first)});
    if (width > 720 && !(last.length === 2 && last[0].getAttribute('aria-label') === `Iconify ${name}`
        && last[1].getAttribute('aria-label') === `Zoom ${name}`)) out.layout.push({name, last: last.map(label)});
  }
  const controls = [...(bar ? bar.querySelectorAll('button') : []), ...heads.flatMap((h) => [...h.querySelectorAll('button')])].filter(visible);
  for (const c of controls) {
    const r = c.getBoundingClientRect(); let lost = 0;
    for (const fx of [0.15, 0.5, 0.85]) for (const fy of [0.15, 0.5, 0.85]) {
      const x = r.left + r.width * fx, y = r.top + r.height * fy;
      if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) continue;
      const hit = document.elementFromPoint(x, y);
      if (!hit) { lost++; continue; }
      if (hit.closest('button') === c) continue;
      const mine = c.closest('.desk-window-shell'), over = hit.closest('.desk-window-shell, .desk-menu-list');
      if (over && over !== mine) continue;  // a window or menu in front covers the point
      lost++;
    }
    if (lost) out.ownership.push({control: label(c), lost});
  }

  // F3 nothing clips, nothing scrolls sideways (the frame scopes + every strip of choices)
  for (const scope of scopes) {
    const walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      if (!n.textContent.trim() || !visible(n.parentElement)) continue;
      const range = document.createRange(); range.selectNodeContents(n); const tr = range.getBoundingClientRect();
      if (tr.width < 1 || tr.height < 1) continue;
      for (let a = n.parentElement; a && a !== document.body; a = a.parentElement) {
        const cs = getComputedStyle(a);
        if (cs.overflowX === 'visible' && cs.overflowY === 'visible') continue;
        const ar = a.getBoundingClientRect();
        if (tr.left < ar.left - 1 || tr.right > ar.right + 1) {
          const holder = n.parentElement; const hs = getComputedStyle(holder);
          if (hs.textOverflow === 'ellipsis' && hs.whiteSpace === 'nowrap') out.ellipsis.push(n.textContent.trim().slice(0, 40));
          else out.clipped.push({text: n.textContent.trim().slice(0, 40), in: label(a)});
        }
        break;
      }
    }
  }
  const strips = [...scopes.flatMap((s) => [s, ...s.querySelectorAll('*')]),
    ...document.querySelectorAll('.desk-wings, .surface-filter-tokens')];
  for (const e of strips) { if (!visible(e) || e.closest('.desk-dock')) continue; const cs = getComputedStyle(e);
    if (['auto', 'scroll'].includes(cs.overflowX) && e.scrollWidth > e.clientWidth + 1) out.sideways.push(label(e)); }

  // F4 393: the content and the targets
  if (width <= 720) {
    const front = shells.find((s) => s.classList.contains('is-front')) || shells[shells.length - 1];
    if (front) { const head = front.querySelector(':scope > .desk-pullout-head');
      const fr = front.getBoundingClientRect(); const hr = head.getBoundingClientRect();
      out.content = Math.round(fr.bottom - parseFloat(getComputedStyle(front).borderBottomWidth) - hr.bottom); }
    const targets = [...(bar ? bar.querySelectorAll('button') : []), ...heads.flatMap((h) => [...h.querySelectorAll('button')])].filter(visible);
    for (const t of targets) { const r = t.getBoundingClientRect();
      if (r.width < 44 - 0.5 || r.height < 44 - 0.5) out.small_targets.push({control: label(t), w: Math.round(r.width), h: Math.round(r.height)}); }
  }

  // F5 frame text in place: the 12 px floor and the contrast it reads at
  for (const scope of scopes) {
    const walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const el = n.parentElement; const text = n.textContent.trim();
      if (!text || !visible(el)) continue;
      const cs = getComputedStyle(el); const size = parseFloat(cs.fontSize);
      if (size < 1) continue;  // a word folded into an accessible name (font-size 0)
      if (size < 12 - 0.01) out.small_text.push({text: text.slice(0, 30), size});
      if (el.closest('.is-ghost')) continue;  // a ghosted row is the stipple's job (recorded by the canvas)
      const fg = rgb(cs.color); if (!fg) continue;
      const ground = groundOf(el); const shown = fg.a < 1 ? blend(fg, ground) : fg;
      const r = ratio(shown, ground); const large = size >= 24 || (size >= 18.66 && Number(cs.fontWeight) >= 700);
      if (r < (large ? 3 : 4.5) - 0.01) out.low_contrast.push({text: text.slice(0, 30), ratio: Math.round(r * 100) / 100});
    }
  }
  return out;
}"""


def _stage(page: Any, key: str, scope: str | None = None) -> None:
    page.evaluate(
        """([key, scope]) => sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key, scope}))""",
        [key, scope],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.wait_for_timeout(1500)
    _settle(page)


class TestTheFrame:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _seed()
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=2, has_touch=width < 720, is_mobile=False)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        page.evaluate(
            """async (token) => fetch('/api/setup/onboarding', {method: 'PUT',
                headers: {authorization: `Bearer ${token}`, 'content-type': 'application/json'},
                body: JSON.stringify({disposition: 'completed'})})""",
            TOKEN,
        )
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    @staticmethod
    def _measure(page: Any, width: int, board: str, facts: dict[str, Any]) -> dict[str, Any]:
        page.wait_for_timeout(400)
        _settle(page)
        m = page.evaluate(FRAME_JS, width)
        facts[board] = m
        return m

    @staticmethod
    def _fails(m: dict[str, Any], width: int, expect_window: bool) -> dict[str, Any]:
        fails: dict[str, Any] = {}
        if expect_window:
            if len(m["blue"]) != 1 or m["front"] != m["blue"] or m["screen"] != m["blue"][0]:
                fails["F1 one blue front window"] = {"blue": m["blue"], "front": m["front"], "screen": m["screen"]}
        if m["layout"] or m["ownership"]:
            fails["F2 gadget layout and ownership"] = {"layout": m["layout"], "ownership": m["ownership"]}
        if m["clipped"] or m["sideways"]:
            fails["F3 nothing clips, nothing scrolls sideways"] = {"clipped": m["clipped"], "sideways": m["sideways"]}
        if width <= 720:
            if (expect_window and (m["content"] is None or m["content"] < 700)) or m["small_targets"]:
                fails["F4 393 content and targets"] = {"content": m["content"], "small": m["small_targets"]}
        if m["small_text"] or m["low_contrast"]:
            fails["F5 frame text in place"] = {"small": m["small_text"], "low": m["low_contrast"]}
        return fails

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_frame(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {}
        failures: dict[str, Any] = {}
        tag = f"{width}"
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                if width > 720:
                    # The Desk with two windows (C1-1 / C1-2a): the Room, then Meetings.
                    _stage(page, "open-project-memory", "project:p-ledger")
                    self._press(page, page.locator(".desk-dock [aria-label^='Meetings']").first, width)
                    page.locator(".desk-window-shell[aria-label='Meetings']").wait_for()
                    m = self._measure(page, width, "two-windows-meetings-front", facts)
                    failures["two-windows-meetings-front"] = self._fails(m, width, True)
                    # the Room comes to the front by a press on its title bar
                    room = page.locator(f".desk-window-shell[aria-label='{ROOM}']")
                    room.locator(".desk-pullout-title").click()
                    m = self._measure(page, width, "two-windows-room-front", facts)
                    failures["two-windows-room-front"] = self._fails(m, width, True)
                    page.screenshot(path=str(SHOTS / f"build-C1-1-the-desk-{tag}.png"))
                    room.screenshot(path=str(SHOTS / f"build-C1-2a-window-gadgets-{tag}.png"))
                    # an open menu on the screen bar (paper, ink, the blue row)
                    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
                    page.locator(".desk-verbbar-menu").wait_for()
                    m = self._measure(page, width, "window-menu-open", facts)
                    failures["window-menu-open"] = self._fails(m, width, True)
                    page.screenshot(path=str(SHOTS / f"build-C1-2b-window-menu-{tag}.png"))
                    page.keyboard.press("Escape")
                else:
                    # The Chair at 393 (C1-1): the screen bar with no window.
                    m = self._measure(page, width, "chair", facts)
                    failures["chair"] = self._fails(m, width, False)
                    page.screenshot(path=str(SHOTS / f"build-C1-1-the-desk-{tag}.png"))
                    # A window with wings that do not fit: the strip menu (C1-2e).
                    _stage(page, "review-meetings")
                    page.locator(".desk-window-shell[aria-label='Meetings']").wait_for()
                    m = self._measure(page, width, "meetings", facts)
                    failures["meetings"] = self._fails(m, width, True)
                    page.screenshot(path=str(SHOTS / f"build-C1-2a-window-gadgets-{tag}.png"))
                    strip = page.locator(".desk-window-shell[aria-label='Meetings'] .surface-strip-menu")
                    if strip.count() != 1:
                        # §3a: four wings and a gear door do not fit one 393 row
                        failures["meetings"]["F3 the wings fold into the strip menu"] = {"strip_menus": strip.count()}
                    else:
                        self._press(page, strip, width)
                        page.locator(".desk-menu-list").first.wait_for()
                        m = self._measure(page, width, "strip-menu-open", facts)
                        failures["strip-menu-open"] = self._fails(m, width, True)
                        checked = page.locator(".desk-menu-list [aria-checked='true']").all_inner_texts()
                        facts["strip-menu-checked"] = checked
                        mark = page.evaluate("""() => { const g = document.querySelector(
                            '.desk-menu-list [aria-checked="true"] .desk-menu-glyph svg, .desk-menu-list [aria-checked="true"] .desk-menu-glyph');
                          if (!g) return 0; const r = g.getBoundingClientRect(); return r.width * r.height; }""")
                        facts["strip-menu-check-mark-area"] = mark
                        if len(checked) != 1 or not mark:
                            failures["strip-menu-open"]["F3 the current choice is checked, and the check shows"] = {
                                "checked": checked, "mark_area": mark}
                        page.screenshot(path=str(SHOTS / f"build-C1-2e-strip-menu-open-{tag}.png"))
                        page.keyboard.press("Escape")
                    # A window that fills the work area (C1-6b): People.
                    _stage(page, "open-people")
                    page.locator(".desk-window-shell[aria-label='People']").wait_for()
                    m = self._measure(page, width, "people", facts)
                    failures["people"] = self._fails(m, width, True)
                    page.screenshot(path=str(SHOTS / f"build-C1-6b-phone-window-{tag}.png"))
                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                failures = {k: v for k, v in failures.items() if v}
                facts["failures"] = failures
                (SHOTS / f"frame-facts-{tag}.json").write_text(json.dumps(facts, indent=2) + "\n")
                assert not facts["errors"], facts["errors"]
                assert not failures, json.dumps(failures, indent=2)
            finally:
                browser.close()
