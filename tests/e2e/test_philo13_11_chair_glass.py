"""PHILO-13-11 (C1, slice two) -- THE CHAIR AS WINDOWS, fenced AS RENDERED.

The owner ratified the canvas on 2026-10-02 ("Ratify, build it"; "Steel";
Capture "Yes" = a fourth Chair window on desktop, on demand from the Speak
AppIcon on the phone; story-11 §RATIFIED). The boards C1-4a, C1-4c, C1-4d
and C1-6a (assets/story-11-canvas/shots/) are rendered here by the product
itself: no canvas CSS, no seat, no shim. Through the real hub on an isolated
HOME at 1440x900 (mouse) and 393x852 (touch), seeded with the canvas week
(Avery, Sam, Jordan, Priya; meetings; decisions; a brief; the Team updates
folder destination).

The fences (each records its findings in ``chair-facts-<width>.json``):

  C1 four Chair windows (1440): Needs you, Brief, The week, Capture, each a
     DeskWindowFrame with its gadgets; the four tile without overlap; each
     body scrolls on its own; the Chair page does not scroll.
  C2 one blue window, and the screen title bar names it (slice one's F1);
     the screen title names each Chair window when it is in front (a press
     on each at 1440; each one shown at 393).
  C3 the lifecycle (R1): Close closes (PHILO-14 A1: the screen of objects
     stands where it was; no reopen Button); was: a compact reopen Button stands in the
     closed window's place; Window ▸ Chair checks the open ones; picking one
     reopens it in front; the reopen Button reopens too.
  C4 393 (R2): one Chair window at a time, Needs you first; >= 700 px of
     content; every target in the frame AND the Chair window body owns
     44 x 44; Speak opens Capture (Talk, Write a thought, Record meeting,
     Schedule); Go ▸ Chair has no Capture row.
  C5 every board: the frame fences of slice one (F2 ownership, F3 nothing
     clips in the frame, F5 frame text in place) and, inside the Chair
     windows: no clipped text, no strip that scrolls sideways, no two
     controls that overlap, every text >= 4.5:1 (3:1 large) on its ground.
  C6 the existing verbs keep their windows: Done, Name an owner and
     Connect calendar and Choose an engine in Needs you; Ack, Defer,
     Generate and the SEND well in Brief; Open in The week; no Run summary
     beside SUMMARY STORED.

Shots go to pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-build/
under HOLDSPEAK_EVIDENCE_WRITE=1 (``.tmp/evidence-shots/`` otherwise).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from .test_philo13_11_frame_glass import FRAME_JS
from tests._evidence import evidence_dir

# PHILO-14 A1: the Chair is the screen of objects; these specs read its windows (tests/conftest.py).
pytestmark = pytest.mark.chair_windows_open

pytest.importorskip("playwright.sync_api", reason="the Chair glass needs Playwright")

TOKEN = "philo13-11-chair"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-build")
SIZES = {1440: 900, 393: 852}
CHAIR = ["Needs you", "Brief", "The week", "Capture"]


def _seed(home: Path) -> None:
    """The canvas week (assets/story-11-canvas/harness/seed_db.py), minted by
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
        ("p-ledger", "Payments ledger cutover", "Move settlement to the new ledger by Nov 5."),
        ("p-obs", "Platform observability", "One tracing stack for all services."),
        ("p-hiring", "Staff hiring loop", "Two senior hires before Q1."),
    ]:
        db.projects.create_project(project_id=pid, name=name, description=desc, keywords=name.lower().split()[:3])
    prim = PrimitiveService(db)
    prim.create_decision(owner, decision_id="d-freeze", title="Freeze the old ledger on Nov 5", status="accepted",
                         decision_markdown="Freeze writes to the old ledger on Nov 5.")
    prim.create_decision(owner, decision_id="d-otel", title="Adopt OpenTelemetry for all services",
                         status="proposed", decision_markdown="Use the OTel SDK in every service.")
    prim.create_note(owner, note_id="n-1", title="Ledger cutover risks",
                     body_markdown="- reconciliation job slow\n- rollback plan owner: Jordan", tags=["week40"])
    for mid, title, hours_ago, pid, summary, topics, action, status in [
        ("m-standup", "Ledger cutover sync", 2, "p-ledger",
         "Dual-write is stable. The team agreed to freeze the old ledger on Nov 5. Jordan owns the rollback plan.",
         ["cutover", "rollback"], "Write the rollback runbook", "completed"),
        ("m-arch", "Architecture review: tracing", 26, "p-obs",
         "Reviewed the tracing options. OpenTelemetry chosen. Sam will pilot it in the billing service.",
         ["tracing", "otel"], "Pilot OTel in billing", "completed"),
        # a stored summary with the run switch OFF: SUMMARY STORED, never Run summary
        ("m-avery", "1:1 Avery", 50, None,
         "Avery wants to lead the ledger cutover. Promo packet due in two weeks.",
         ["career", "promo"], "Review Avery's promo packet", "disabled"),
    ]:
        start = (now - timedelta(hours=hours_ago)).replace(microsecond=0)
        db.meetings.save_meeting(MeetingState(
            id=mid, started_at=start, ended_at=start + timedelta(minutes=30), title=title,
            segments=[TranscriptSegment(text=summary.split(".")[0] + ".", speaker="Me", start_time=1.0, end_time=4.0),
                      TranscriptSegment(text="Agreed.", speaker="Avery", start_time=4.0, end_time=5.0)],
            intel=IntelSnapshot(timestamp=1.0, topics=topics, summary=summary, action_items=[{
                "id": f"{mid}-a1", "task": action, "owner": None, "due": None, "status": "pending",
                "review_state": "accepted", "source_timestamp": None, "created_at": start.isoformat()}]),
            intel_status=status))
        if pid:
            db.projects.associate_meeting_project(meeting_id=mid, project_id=pid, source="manual", confidence=1.0)
    store = production_people_store()
    store.initialize()
    people = PeopleService(store)
    for name, kind in [("Avery Chen", "direct_report"), ("Jordan Patel", "direct_report"),
                       ("Sam Rivera", "direct_report"), ("Priya Nair", "peer")]:
        rel = people.create_relationship(owner, {"display_name": name, "relationship_kind": kind,
                                                 "role_context": "Engineer", "cadence": "weekly"})
        if kind == "direct_report":
            req = people.create_request(owner, rel["id"], {"body": f"{name.split()[0]}: send the status by Thursday"})
            people.accept_request(owner, req["id"])
    MondayBriefService(db).generate(owner, now=now)
    (home / "Documents" / "HoldSpeak" / "Team updates").mkdir(parents=True, exist_ok=True)


# ── the Chair measures (run in the page) ────────────────────────────────

CHAIR_JS = r"""(width) => {
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
  const wins = [...document.querySelectorAll('.desk-window-shell.chair-window')].filter(visible);
  const chair = document.querySelector('.chair');
  const se = document.scrollingElement;
  const out = {width, windows: wins.map((w) => w.getAttribute('aria-label')),
    reopen: [...document.querySelectorAll('[data-testid^="chair-reopen-"] button')].filter(visible).map(label),
    page_scrolls: Boolean((chair && chair.scrollHeight > chair.clientHeight + 1) || (se && se.scrollHeight > se.clientHeight + 1)),
    bodies: {}, tiles_overlap: [], clipped: [], ellipsis: [], sideways: [], overlap: [], small_targets: [],
    low_contrast: [], small_text: []};
  for (const w of wins) { const b = w.querySelector('.chair-window-body'); if (!b) continue;
    const cs = getComputedStyle(b);
    out.bodies[w.getAttribute('aria-label')] = {overflowY: cs.overflowY, scrolls: b.scrollHeight > b.clientHeight + 1,
      h: Math.round(b.getBoundingClientRect().height)}; }
  // the four tile: no two Chair windows overlap (1440)
  if (width > 720) for (let i = 0; i < wins.length; i++) for (let j = i + 1; j < wins.length; j++) {
    const a = wins[i].getBoundingClientRect(), b = wins[j].getBoundingClientRect();
    const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left), oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (ox > 1 && oy > 1) out.tiles_overlap.push([wins[i].getAttribute('aria-label'), wins[j].getAttribute('aria-label')]);
  }
  for (const w of wins) {
    const body = w.querySelector('.chair-window-body'); if (!body) continue;
    const br = body.getBoundingClientRect();
    // nothing clips: a text box past its clipping ancestor (single-line ellipsis recorded)
    const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const el = n.parentElement; const text = n.textContent.trim();
      if (!text || !visible(el)) continue;
      const range = document.createRange(); range.selectNodeContents(n); const tr = range.getBoundingClientRect();
      if (tr.width < 1 || tr.height < 1) continue;
      for (let a = el; a && a !== body.parentElement; a = a.parentElement) {
        const cs = getComputedStyle(a);
        if (cs.overflowX === 'visible' && cs.overflowY === 'visible') continue;
        const ar = a.getBoundingClientRect();
        if (tr.left < ar.left - 1 || tr.right > ar.right + 1) {
          const hs = getComputedStyle(el);
          if (hs.textOverflow === 'ellipsis' && hs.whiteSpace === 'nowrap') out.ellipsis.push(text.slice(0, 40));
          else out.clipped.push({text: text.slice(0, 40), in: label(a)});
        }
        break;
      }
      // only what is on screen in its window is read for contrast and size
      if (tr.bottom < br.top || tr.top > br.bottom) continue;
      const cs = getComputedStyle(el); const size = parseFloat(cs.fontSize);
      if (size < 1) continue;
      if (size < 12 - 0.01) out.small_text.push({text: text.slice(0, 30), size});
      const fg = rgb(cs.color); if (!fg) continue;
      const ground = groundOf(el); const shown = fg.a < 1 ? blend(fg, ground) : fg;
      const r = ratio(shown, ground); const large = size >= 24 || (size >= 18.66 && Number(cs.fontWeight) >= 700);
      if (r < (large ? 3 : 4.5) - 0.01) out.low_contrast.push({text: text.slice(0, 30), ratio: Math.round(r * 100) / 100});
    }
    // nothing scrolls sideways inside a Chair window
    for (const e of [body, ...body.querySelectorAll('*')]) { if (!visible(e)) continue; const cs = getComputedStyle(e);
      if (['auto', 'scroll'].includes(cs.overflowX) && e.scrollWidth > e.clientWidth + 1) out.sideways.push(label(e)); }
    // no two visible controls of one window overlap (on screen in the body)
    const ctrls = [...body.querySelectorAll('button, a[href], input, select, textarea, [role=button]')].filter(visible)
      .map((c) => [c, c.getBoundingClientRect()]).filter(([, r]) => r.bottom > br.top && r.top < br.bottom);
    for (let i = 0; i < ctrls.length; i++) for (let j = i + 1; j < ctrls.length; j++) {
      const [ca, a] = ctrls[i], [cb, b] = ctrls[j];
      if (ca.contains(cb) || cb.contains(ca)) continue;
      const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left), oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (ox > 1 && oy > 1) out.overlap.push([label(ca), label(cb)]);
    }
    // 393: every target in the body owns 44 x 44 (on screen)
    if (width <= 720) for (const [c, r] of ctrls) {
      if (c.matches('input, textarea, select')) continue;
      if (r.width < 44 - 0.5 || r.height < 44 - 0.5) out.small_targets.push({control: label(c), w: Math.round(r.width), h: Math.round(r.height)});
    }
  }
  return out;
}"""


class TestTheChairAsWindows:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.home = tmp_path / "home"
        _seed(self.home)
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
        _api(page, "POST", "/api/channels/destinations",
             {"name": "Team updates", "channel": "file",
              "folder": str(self.home / "Documents" / "HoldSpeak" / "Team updates")}, token=TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        try:
            page.locator(".desk-window-shell[aria-label='Needs you']").wait_for(timeout=10_000)
        except Exception:  # noqa: BLE001 -- the fences below name what is missing (red on bbf7e9a4)
            pass
        page.wait_for_timeout(1500)
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
    def _measure(page: Any, width: int, board: str, facts: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        page.wait_for_timeout(400)
        _settle(page)
        frame = page.evaluate(FRAME_JS, width)
        chair = page.evaluate(CHAIR_JS, width)
        facts[board] = {"frame": frame, "chair": chair}
        return frame, chair

    @staticmethod
    def _fails(frame: dict[str, Any], chair: dict[str, Any], width: int) -> dict[str, Any]:
        fails: dict[str, Any] = {}
        if len(frame["blue"]) != 1 or frame["front"] != frame["blue"] or frame["screen"] != frame["blue"][0]:
            fails["C2 one blue window, named by the screen bar"] = {
                "blue": frame["blue"], "front": frame["front"], "screen": frame["screen"]}
        if frame["ownership"]:
            fails["C5 frame ownership"] = frame["ownership"]
        if frame["clipped"] or frame["sideways"]:
            fails["C5 frame clips"] = {"clipped": frame["clipped"], "sideways": frame["sideways"]}
        if frame["small_text"] or frame["low_contrast"]:
            fails["C5 frame text in place"] = {"small": frame["small_text"], "low": frame["low_contrast"]}
        if chair["clipped"] or chair["sideways"] or chair["overlap"]:
            fails["C5 Chair windows: nothing clips, nothing scrolls sideways, nothing overlaps"] = {
                "clipped": chair["clipped"], "sideways": chair["sideways"], "overlap": chair["overlap"]}
        if chair["low_contrast"]:
            fails["C5 Chair windows: contrast in place"] = chair["low_contrast"]
        if chair["page_scrolls"]:
            fails["C1 the Chair page does not scroll"] = True
        for name, body in chair["bodies"].items():
            if body["overflowY"] not in ("auto", "scroll"):
                fails.setdefault("C1 each window scrolls on its own", []).append({name: body})
        if width > 720 and chair["tiles_overlap"]:
            fails["C1 the four tile"] = chair["tiles_overlap"]
        if width <= 720:
            if frame["content"] is None or frame["content"] < 700 or frame["small_targets"] or chair["small_targets"]:
                fails["C4 393 content and targets"] = {"content": frame["content"], "frame": frame["small_targets"],
                                                      "body": chair["small_targets"]}
        return fails

    @staticmethod
    def _verbs(page: Any) -> dict[str, Any]:
        """C6: the existing verbs, each in its window."""
        def inside(win: str, sel: str) -> int:
            return page.locator(f".desk-window-shell[aria-label='{win}'] {sel}").count()
        return {
            "needs.done": inside("Needs you", "[data-testid='arrival-commitment-verb'], [data-testid='arrival-door-verb']"),
            "needs.name_owner": inside("Needs you", "[data-testid='arrival-name-owner']"),
            "needs.connect_calendar": inside("Needs you", "[data-testid='arrival-connect-calendar']"),
            "needs.choose_engine": inside("Needs you", "[data-testid^='arrival-blocker-verb-']"),
            "brief.ack_defer": inside("Brief", "[data-testid='arrival-brief-row'] button"),
            "brief.generate": inside("Brief", "button:has-text('Generate')"),
            "brief.send_well": inside("Brief", ":text('Team updates')"),
            "week.open": inside("The week", "[data-testid='arrival-meeting-row'] button:has-text('Open')"),
            "week.stored": page.evaluate("""() => [...document.querySelectorAll(
                '.desk-window-shell[aria-label="The week"] [data-testid="arrival-meeting-row"]')]
                .filter((r) => (r.querySelector('[data-testid="arrival-meeting-badge"]') || {}).textContent === 'SUMMARY STORED')
                .map((r) => ({run: Boolean(r.querySelector('[data-testid="arrival-run-intel"]')),
                              open: Boolean(r.querySelector('[data-testid="arrival-meeting-open"]'))}))"""),
            "capture": inside("Capture", "[data-testid='arrival-develop-thought'], [data-testid='arrival-record-meeting'], [data-testid='arrival-schedule']"),
        }

    @staticmethod
    def _stop(facts: dict[str, Any], failures: dict[str, Any], tag: str) -> None:
        """No Chair windows to walk: record what the first board measured and fail."""
        failures = {k: v for k, v in failures.items() if v}
        facts["failures"] = failures
        (SHOTS / f"chair-facts-{tag}.json").write_text(json.dumps(facts, indent=2) + "\n")
        raise AssertionError(json.dumps(failures, indent=2))

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_chair_as_windows(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {}
        failures: dict[str, Any] = {}
        tag = f"{width}"
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                shell = lambda name: page.locator(f".desk-window-shell[aria-label='{name}']")  # noqa: E731
                if width > 720:
                    # C1-4a: the four windows
                    frame, chair = self._measure(page, width, "chair-windows", facts)
                    failures["chair-windows"] = self._fails(frame, chair, width)
                    if sorted(chair["windows"]) != sorted(CHAIR):
                        failures["chair-windows"]["C1 four Chair windows"] = chair["windows"]
                        self._stop(facts, failures, tag)
                    verbs = self._verbs(page)
                    facts["verbs"] = verbs
                    missing = [k for k, v in verbs.items() if k not in ("week.stored",) and not v]
                    stored = verbs["week.stored"]
                    if missing or not stored or any(r["run"] or not r["open"] for r in stored):
                        failures["chair-windows"]["C6 the verbs keep their windows"] = {"missing": missing, "stored": stored}
                    page.screenshot(path=str(SHOTS / f"build-C1-4a-chair-windows-{tag}.png"))

                    # C2b: the screen title names the front Chair window after a
                    # press on each one (Astra, #730: it read the Dock-only list).
                    named = {}
                    for name in CHAIR:
                        shell(name).locator(".desk-pullout-title").click()
                        page.wait_for_timeout(250)
                        named[name] = page.get_by_test_id("desk-screen-title").inner_text().strip()
                    facts["screen-title-after-press"] = named
                    if any(named[n] != n for n in CHAIR):
                        failures["chair-windows"]["C2 the screen title names each front Chair window"] = named
                    shell("Needs you").locator(".desk-pullout-title").click()

                    # C1-4c: Close closes. PHILO-14 A1 (board A-1): the Chair is
                    # the screen of objects, so no reopen Button stands in its place.
                    shell("Brief").get_by_role("button", name="Close Brief").click()
                    shell("Brief").wait_for(state="detached")
                    frame, chair = self._measure(page, width, "chair-window-closed", facts)
                    failures["chair-window-closed"] = self._fails(frame, chair, width)
                    if "Brief" in chair["windows"] or chair["reopen"]:
                        failures["chair-window-closed"]["C3 close closes; the screen stands"] = {
                            "windows": chair["windows"], "reopen": chair["reopen"]}
                    page.screenshot(path=str(SHOTS / f"build-C1-4c-chair-window-closed-{tag}.png"))

                    # C1-4d: Window ▸ Chair, a check on each open one
                    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
                    page.locator(".desk-verbbar-menu").wait_for()
                    page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Chair')").hover()
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Needs you')").wait_for()
                    rows = page.evaluate("""() => [...document.querySelectorAll('.desk-menu-list [role="menuitemcheckbox"]')]
                        .map((e) => [e.textContent.trim(), e.getAttribute('aria-checked')])""")
                    facts["window-menu-chair"] = rows
                    want = [["Needs you", "true"], ["Brief", "false"], ["The week", "true"], ["Capture", "true"]]
                    frame, chair = self._measure(page, width, "window-menu-chair", facts)
                    failures["window-menu-chair"] = self._fails(frame, chair, width)
                    if [[t.replace("✓", "").strip(), c] for t, c in rows] != want:
                        failures["window-menu-chair"]["C3 Window ▸ Chair checks the open ones"] = rows
                    page.screenshot(path=str(SHOTS / f"build-C1-4d-window-menu-chair-{tag}.png"))
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')").click()
                    shell("Brief").wait_for()
                    frame, chair = self._measure(page, width, "chair-window-reopened", facts)
                    failures["chair-window-reopened"] = self._fails(frame, chair, width)
                    if frame["screen"] != "Brief" or chair["reopen"]:
                        failures["chair-window-reopened"]["C3 reopened in front"] = {
                            "screen": frame["screen"], "reopen": chair["reopen"]}
                    # PHILO-14 A1: the screen's Needs you drawer reopens its window
                    shell("Needs you").get_by_role("button", name="Close Needs you").click()
                    shell("Needs you").wait_for(state="detached")
                    page.locator(".desk-screen [data-object-id='drawer:needs']").press("Enter")
                    shell("Needs you").wait_for()
                    # a press on a window brings it to the front (one blue)
                    shell("Needs you").locator(".desk-pullout-title").click()
                    frame, chair = self._measure(page, width, "needs-front", facts)
                    failures["needs-front"] = self._fails(frame, chair, width)
                    if frame["blue"] != ["Needs you"]:
                        failures["needs-front"]["C2 the pressed window is the blue one"] = frame["blue"]
                else:
                    # C1-6a: one window at a time, Needs you first
                    frame, chair = self._measure(page, width, "phone-desk", facts)
                    failures["phone-desk"] = self._fails(frame, chair, width)
                    if chair["windows"] != ["Needs you"]:
                        failures["phone-desk"]["C4 one window, Needs you first"] = chair["windows"]
                        self._stop(facts, failures, tag)
                    page.screenshot(path=str(SHOTS / f"build-C1-6a-phone-desk-{tag}.png"))

                    # C2b (393): the screen title names the one Chair window
                    named = {"Needs you": page.get_by_test_id("desk-screen-title").inner_text().strip()}

                    # C1-4a (393): Go ▸ Brief (PHILO-14 A1 #939: the Chair's
                    # windows are Go's first rows, two taps)
                    self._press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
                    page.locator(".desk-verbbar-menu").wait_for()
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Needs you')").wait_for()
                    rows = page.evaluate("""() => [...document.querySelectorAll('.desk-menu-list [role="menuitemcheckbox"]')]
                        .map((e) => [e.textContent.trim(), e.getAttribute('aria-checked')])""")
                    facts["go-chair"] = rows
                    if [t.replace("✓", "").strip() for t, _ in rows] != ["Needs you", "Brief", "The week"]:
                        failures["phone-desk"]["C4 Go has the Chair rows, no Capture row"] = rows
                    self._press(page, page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')"), width)
                    shell("Brief").wait_for()
                    frame, chair = self._measure(page, width, "chair-windows", facts)
                    failures["chair-windows"] = self._fails(frame, chair, width)
                    if chair["windows"] != ["Brief"]:
                        failures["chair-windows"]["C4 one window at a time"] = chair["windows"]
                    page.screenshot(path=str(SHOTS / f"build-C1-4a-chair-windows-{tag}.png"))
                    named["Brief"] = page.get_by_test_id("desk-screen-title").inner_text().strip()
                    self._press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
                    page.locator(".desk-verbbar-menu").wait_for()
                    self._press(page, page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('The week')"), width)
                    shell("The week").wait_for()
                    page.wait_for_timeout(250)
                    named["The week"] = page.get_by_test_id("desk-screen-title").inner_text().strip()
                    self._press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
                    page.locator(".desk-verbbar-menu").wait_for()
                    self._press(page, page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')"), width)
                    shell("Brief").wait_for()

                    # C1-4c (393): close gives the work area to the next Chair window
                    self._press(page, shell("Brief").get_by_role("button", name="Close Brief"), width)
                    shell("Brief").wait_for(state="detached")
                    frame, chair = self._measure(page, width, "chair-window-closed", facts)
                    failures["chair-window-closed"] = self._fails(frame, chair, width)
                    if len(chair["windows"]) != 1 or "Brief" in chair["windows"]:
                        failures["chair-window-closed"]["C4 the next Chair window takes the work area"] = chair["windows"]
                    page.screenshot(path=str(SHOTS / f"build-C1-4c-chair-window-closed-{tag}.png"))

                    # Capture on demand from the Speak AppIcon
                    self._press(page, page.locator(".desk-dock [aria-label^='Speak']").first, width)
                    shell("Capture").wait_for()
                    frame, chair = self._measure(page, width, "capture-from-speak", facts)
                    failures["capture-from-speak"] = self._fails(frame, chair, width)
                    verbs = self._verbs(page)
                    facts["capture-verbs"] = verbs["capture"]
                    page.wait_for_timeout(250)
                    named["Capture"] = page.get_by_test_id("desk-screen-title").inner_text().strip()
                    facts["screen-title-per-window"] = named
                    if any(named[n] != n for n in CHAIR):
                        failures["capture-from-speak"]["C2 the screen title names the shown Chair window"] = named
                    if chair["windows"] != ["Capture"] or verbs["capture"] != 3:
                        failures["capture-from-speak"]["C4 Speak opens Capture"] = {
                            "windows": chair["windows"], "capture": verbs["capture"]}

                    # C4b (Muad'Dib's ruling): ONLY the Dock's Speak AppIcon opens
                    # Capture; Go ▸ Speak (the verb, the menu, ⌘1) keeps opening the
                    # Speak (dictation) window, so it stays reachable from the Chair.
                    self._press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
                    page.locator(".desk-verbbar-menu").wait_for()
                    go_speak = page.locator(".desk-verbbar-menu").get_by_role("menuitem", name=re.compile(r"^Speak"))
                    go_speak.first.scroll_into_view_if_needed()
                    self._press(page, go_speak.first, width)
                    try:
                        page.locator(".desk-window-shell[aria-label='Speak']").wait_for(timeout=8_000)
                    except Exception:  # noqa: BLE001 -- the fence below names what opened instead
                        pass
                    page.wait_for_timeout(400)
                    go = {"speak_window": page.locator(".desk-window-shell[aria-label='Speak']").count(),
                          "screen": page.get_by_test_id("desk-screen-title").inner_text().strip()}
                    facts["go-speak"] = go
                    if go["speak_window"] != 1 or go["screen"] != "Speak":
                        failures["capture-from-speak"]["C4b Go ▸ Speak opens the Speak window"] = go
                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                failures = {k: v for k, v in failures.items() if v}
                facts["failures"] = failures
                (SHOTS / f"chair-facts-{tag}.json").write_text(json.dumps(facts, indent=2) + "\n")
                assert not facts["errors"], facts["errors"]
                assert not failures, json.dumps(failures, indent=2)
            finally:
                browser.close()
