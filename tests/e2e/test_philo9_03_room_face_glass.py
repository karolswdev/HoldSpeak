"""PHILO-9-03 -- the Room's face tells the truth, fenced AS RENDERED through
the real hub on an isolated HOME at 1440x900 and 393x852.

The owner ratified both story 03 canvases "as drawn" on 2026-09-27
(pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/
story-03-items-canvas/ and story-03-delivery-canvas/): Q1 ITEMS after NEEDS
YOU, omitted when empty; Q2 the list chip `DELIVERED ×N` (PHILO-10-04 A2: now `DELIVERY ×N`, the same count); Q3 To + Mark
delivered above the body. Settled: missed ✗ (danger), dropped — (idle), a
failed items read is ITEMS UNAVAILABLE + Retry; a named refusal ✗ REFUSED +
its plain word; a lost answer ⚠ NO ANSWER · RESULT UNKNOWN with Retry bound to
its own update; Back in the editor's head verbs.

The charter's red-first matrix (current-phase-status.md, story 03 rows):
  F1 the Room from a meeting's project button   red at 1440 and 393
  F2 a past-due milestone shown, health turned  red at 1440 and 393
  Mark delivered                                new (readbacks at both widths)
  F3 steward counts equal the run               red at 1440 and 393
  F7 RECEIPTS are writes                        red at 1440 and 393
  F10 the Steward verb hit at its centre        red at 393; preservation green
                                                at 1440 (no verb under the well)
  F11 the update list words                     red at 1440 and 393
Each hub read the face is compared with is read in the same test. The fault
faces (a refusal, a lost answer) are injected at the browser's fetch; a lost
answer lets the request reach the hub (the row commits) and drops the reply.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, pick_wing
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the Room face glass needs Playwright")

TOKEN = "philo9-03-room-face"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-shots")
SIZES = {1440: 900, 393: 852}
WIDTHS = list(SIZES)
T = 20_000
NAME = "Payments ledger cutover"
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# Rendered facts of the Room window (the canvas harness's FACTS, shoot.py).
FACTS = r"""() => {
  const anchor = document.querySelector('[data-testid=room-body], [data-testid=update-posture], [data-testid=steward-posture]');
  const win = anchor ? anchor.closest('.desk-window') : null;
  if (!win) return {window: false};
  const GLYPH = /^[●○✓✗⚠—↻ℹ«»·▤›×\s>]+$/;
  const small = [];
  const walker = document.createTreeWalker(win, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const t = n.textContent.trim();
    if (!t || GLYPH.test(t)) continue;
    const el = n.parentElement;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (!r.width || !r.height || cs.visibility === 'hidden' || cs.display === 'none' || el.closest('.sr-only')) continue;
    const fs = parseFloat(cs.fontSize);
    if (fs < 12) small.push({text: t.slice(0, 40), fs, cls: String(el.className).slice(0, 60)});
  }
  const text = (sel) => [...win.querySelectorAll(sel)].filter((e) => e.getBoundingClientRect().height > 0)
    .map((e) => e.innerText.replace(/\s+/g, ' ').trim());
  const raw = [...win.querySelectorAll('button')].filter((b) => !String(b.className).includes('btn') && b.getBoundingClientRect().width);
  const head = (sel) => { const s = win.querySelector(sel + ' .surface-section-head, ' + sel + ' h3'); return s ? s.innerText.replace(/\s+/g, ' ').trim() : null; };
  return {
    window: true,
    title: (win.querySelector('.desk-window-title, [data-testid=window-title]')?.innerText || '').trim(),
    headline: text('[data-testid=room-headline]')[0] ?? null,
    head_chips: text('[data-testid=room-head-chips] .surface-state-chip, [data-testid=room-head-chips] .surface-token'),
    needs_you: text('[data-testid=needs-you-row]'),
    items_head: head('[data-section=items]'),
    items_section_present: !!win.querySelector('[data-section=items] .surface-section, [data-section=items] section'),
    item_rows: text('[data-testid=item-row]'),
    item_leads: [...win.querySelectorAll('[data-testid=item-row]')].map((r) => { const c = r.querySelector('.surface-state-chip'); return c ? {icon: c.innerText.trim(), state: c.getAttribute('data-state')} : null; }),
    item_danger_tokens: text('[data-testid=item-row] [data-tone=danger]'),
    controls_in_items: [...win.querySelectorAll('[data-testid=items-section] button, [data-testid=items-section] input')].length,
    update_list_head: text('.update-list .surface-ledger-count')[0] ?? null,
    update_rows: text('[data-testid=update-list-item]'),
    update_emblems: text('[data-testid=update-list-item] .update-lead-emblem'),
    delivered_chips: text('[data-testid=update-delivered-chip]'),
    deliver_verb: text('[data-testid=deliver-verb], [data-testid=deliver-retry]')[0] ?? null,
    deliver_to: (() => { const i = win.querySelector('[data-testid=deliver-to]'); return i ? {value: i.value, disabled: i.disabled} : null; })(),
    delivery_head: head('[data-section=delivery]'),
    delivery_rows: text('[data-testid=delivery-row]'),
    delivery_egress: win.querySelectorAll('[data-section=delivery] .gadget-chip-egress, [data-section=delivery] [data-testid*=egress]').length,
    receipts: text('[data-testid=receipt-row] .surface-primary'),
    plan: text('[data-testid=steward-run-plan] .surface-plan-step'),
    steward_outcome: text('[data-testid=steward-run-outcome]')[0] ?? null,
    words_send: /\bsend\b|\bsent\b/i.test(win.innerText),
    modal: !!document.querySelector('[role=dialog][aria-modal=true], .modal, dialog[open]'),
    small_text_count: small.length,
    small_text: small.slice(0, 12),
    raw_buttons: raw.map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 30)),
    h_overflow: document.documentElement.scrollWidth > window.innerWidth,
    ask_well_position: (() => { const c = win.querySelector('.room-ask-container'); return c ? getComputedStyle(c).position : null; })(),
    // F10: a visible verb or section head whose centre lies under the Ask well.
    under_ask_well: [...win.querySelectorAll('.btn, .surface-section-head, h3')].filter((e) => {
      if (e.closest('.room-ask-container')) return false;
      const r = e.getBoundingClientRect();
      if (!r.width || r.bottom < 0 || r.top > window.innerHeight) return false;
      const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      return !!hit && !!hit.closest('.room-ask-container');
    }).map((e) => e.innerText.replace(/\s+/g, ' ').trim().slice(0, 30)),
  };
}"""

# The nine-point pointer pass (the canvas harness's; story 04's glass): the
# centre, four edge midpoints and four corners, inset 1 px, of the painted face
# at 1440 and of the 44 x 44 target at 393. A point is owned when
# elementFromPoint AND the target of a real pointermove land inside the control.
POINTS = r"""([width, sels]) => {
  document.querySelectorAll('[data-probe]').forEach(e => e.removeAttribute('data-probe'));
  const els = sels.flatMap((s) => [...document.querySelectorAll(s)])
    .filter(b => { const r = b.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  return els.map((b, i) => {
    b.scrollIntoView({block: 'center'});
    b.dataset.probe = String(i);
    return {i, text: (b.innerText || b.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 30)};
  });
}"""
BOX = r"""([i, width]) => {
  const b = document.querySelector(`[data-probe="${i}"]`);
  b.scrollIntoView({block: 'center'});
  const r = b.getBoundingClientRect();
  const cy = r.top + r.height / 2, cx0 = r.left + r.width / 2;
  const narrow = width <= 420;
  const hw = narrow ? Math.max(22, r.width / 2) : r.width / 2, hh = narrow ? Math.max(22, r.height / 2) : r.height / 2;
  const l = cx0 - hw + 1, rr = cx0 + hw - 1, t = cy - hh + 1, bb = cy + hh - 1;
  return {face: [+r.width.toFixed(1), +r.height.toFixed(1)],
    points: [[cx0, cy, 'centre'], [cx0, t, 'top'], [rr, cy, 'right'], [cx0, bb, 'bottom'], [l, cy, 'left'],
             [l, t, 'top-left'], [rr, t, 'top-right'], [l, bb, 'bottom-left'], [rr, bb, 'bottom-right']]};
}"""
HIT = r"""([i, x, y]) => {
  const b = document.querySelector(`[data-probe="${i}"]`);
  const el = document.elementFromPoint(x, y);
  return {ok: !!el && !!b && b.contains(el), hit: el ? String(el.className || el.tagName).split(' ')[0] : null};
}"""
PM_ARM = r"""() => { window.__pm = null; if (!window.__pmArmed) { window.__pmArmed = true;
  document.addEventListener('pointermove', e => { window.__pm = e.target; }, true); } }"""
PM_READ = r"""([i]) => { const b = document.querySelector(`[data-probe="${i}"]`); const t = window.__pm;
  return {ok: !!t && !!b && b.contains(t), hit: t ? String(t.className || t.tagName).split(' ')[0] : null}; }"""

# The fault seam: the face's `/delivered` calls pass through this wrapper,
# which records every call and can HOLD one (the pending face), REFUSE one
# (a named hub code, nothing sent), or LOSE one (the request reaches the hub
# and commits; the reply is dropped as a network error).
FETCH_SEAM = r"""() => {
  if (window.__seam) return;
  window.__seam = true;
  window.__calls = [];
  window.__mode = null;
  const real = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const url = typeof input === 'string' ? input : input.url;
    if (!/\/api\/updates\/[^/]+\/delivered$/.test(url)) return real(input, init);
    const body = init && init.body ? JSON.parse(init.body) : {};
    window.__calls.push({url, update_id: decodeURIComponent(url.split('/')[3]), ...body});
    const mode = window.__mode; window.__mode = null;
    if (mode && mode.refuse) {
      return new Response(JSON.stringify({success: false, code: mode.refuse, error_code: mode.refuse}),
        {status: 409, headers: {'content-type': 'application/json'}});
    }
    if (mode && mode.hold) await new Promise((r) => { window.__release = r; });
    const res = await real(input, init);
    if (mode && mode.lose) { await res.text(); throw new TypeError('Failed to fetch'); }
    return res;
  };
}"""


def _record(name: str, width: int, data: Any) -> None:
    (SHOTS / f"{name}-{width}.json").write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def _shot(page: Any, name: str, width: int) -> None:
    page.mouse.move(1, 1)
    _settle(page)
    page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))


def _delivery_time(iso: str) -> str:
    d = datetime.fromisoformat(iso).astimezone()
    return f"{MONTHS[d.month - 1]} {d.day} {d.hour:02d}:{d.minute:02d}"




def _assert_room_named(page: Any, width: int, name: str) -> None:
    """The opened Room is named. PHILO-13-11 (C1): at 393 the head is one
    44 px row and the SCREEN title bar names the front window instead."""
    room = page.locator(".desk-window:has([data-testid=room-body])").first
    assert room.get_attribute("aria-label") == name, room.get_attribute("aria-label")
    if width < 720:
        screen = page.locator("[data-testid=desk-screen-title]").inner_text().strip()
        assert screen == name, f"the screen title bar names {screen!r}, not the Room {name!r}"
    else:
        assert name in room.inner_text()

class TestRoomFaceGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _open(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
        ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=self.base)
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        return browser, page, errors

    @staticmethod
    def _stage(page: Any, key: str, scope: str) -> None:
        page.evaluate("""([key, scope]) => sessionStorage.setItem('hs.desk.staged-surface-open',
            JSON.stringify({key, scope}))""", [key, scope])
        page.reload(wait_until="load")
        _normal_chair(page)

    def _room(self, page: Any, pid: str) -> None:
        self._stage(page, "open-project-memory", f"project:{pid}")
        page.locator("[data-testid=room-body]").wait_for(timeout=T)
        page.wait_for_timeout(900)
        _settle(page)

    @staticmethod
    def _project(page: Any, name: str = NAME) -> str:
        return _api(page, "POST", "/api/projects", {"name": name}, token=TOKEN)["project"]["id"]

    @staticmethod
    def _items(page: Any, pid: str) -> dict[str, str]:
        """The canvas's seed, through the real routes: a milestone 7 days late,
        an open high risk, a planned milestone, a missed and a dropped one."""
        today = date.today()
        ids: dict[str, str] = {}
        for body in (
            {"item_type": "milestone", "title": "Cutover rehearsal", "due_at": (today - timedelta(days=7)).isoformat()},
            {"item_type": "risk", "title": "Old ledger freeze slips", "severity": "high",
             "details": {"likelihood": "high", "impact": "high"}},
            {"item_type": "milestone", "title": "Ledger go-live", "due_at": (today + timedelta(days=14)).isoformat()},
            {"item_type": "milestone", "title": "Parallel run", "due_at": (today - timedelta(days=10)).isoformat()},
            {"item_type": "milestone", "title": "Vendor shadow run", "due_at": (today + timedelta(days=5)).isoformat()},
        ):
            ids[body["title"]] = _api(page, "POST", f"/api/projects/{pid}/items", body, token=TOKEN)["item"]["id"]
        for title, verb in (("Parallel run", "missed"), ("Vendor shadow run", "dropped")):
            _api(page, "POST", f"/api/projects/{pid}/items/{ids[title]}/transition", {"verb": verb}, token=TOKEN)
        return ids

    @staticmethod
    def _published(page: Any, pid: str) -> str:
        uid = _api(page, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"},
                   token=TOKEN)["update"]["id"]
        _api(page, "POST", f"/api/updates/{uid}/publish", {}, token=TOKEN)
        return uid

    @staticmethod
    def _deliveries(page: Any, pid: str, uid: str) -> list[dict[str, Any]]:
        ups = _api(page, "GET", f"/api/projects/{pid}/updates", token=TOKEN)["updates"]
        return next(u for u in ups if u["id"] == uid).get("deliveries", [])

    @staticmethod
    def _facts(page: Any) -> dict[str, Any]:
        return page.evaluate(FACTS)

    def _pointer(self, page: Any, width: int, sels: list[str]) -> list[dict[str, Any]]:
        page.evaluate(PM_ARM)
        out = []
        for probe in page.evaluate(POINTS, [width, sels]):
            box = page.evaluate(BOX, [probe["i"], width])
            bad = []
            for x, y, where in box["points"]:
                if not (0 <= x < width and 0 <= y < SIZES[width]):
                    bad.append((where, "off-screen"))
                    continue
                h = page.evaluate(HIT, [probe["i"], x, y])
                page.mouse.move(x, y)
                m = page.evaluate(PM_READ, [probe["i"]])
                if not (h["ok"] and m["ok"]):
                    bad.append((where, h["hit"], m["hit"]))
            out.append({"text": probe["text"], "face": box["face"], "points": len(box["points"]), "not_owned": bad})
        page.mouse.move(2, 60)
        return out

    @staticmethod
    def _updates(page: Any) -> None:
        page.locator("[data-testid=updates-verb]").click()
        page.locator("[data-testid=update-list]").wait_for(timeout=T)
        page.wait_for_timeout(400)

    @staticmethod
    def _open_update(page: Any, uid: str) -> None:
        page.locator(f"[data-testid=update-list-item]:has([data-update-id='{uid}'])").first.click()
        page.locator("[data-testid=update-editor]").wait_for(timeout=T)
        page.wait_for_timeout(400)

    @staticmethod
    def _back(page: Any) -> None:
        page.locator("[data-testid=update-verb-back]").click()
        page.locator("[data-testid=update-list]").wait_for(timeout=T)
        page.wait_for_timeout(300)

    # ── F1: every caller opens the Room ──────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_meetings_project_button_opens_the_room(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from holdspeak.db import get_database

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = self._project(page)
                now = datetime.now()
                with get_database()._connection() as conn:
                    conn.execute(
                        "INSERT INTO meetings (id, started_at, ended_at, title, duration_seconds, capture_status, provenance) "
                        "VALUES ('m-p903', ?, ?, 'Cutover sync', 1800.0, 'finalized', 'desktop')",
                        ((now - timedelta(hours=1)).isoformat(), (now - timedelta(minutes=30)).isoformat()))
                    conn.commit()
                _api(page, "POST", f"/api/projects/{pid}/meetings/m-p903", {}, token=TOKEN)
                self._stage(page, "review-meetings", "meeting:m-p903")
                page.locator(".surface-split-detail .surface-display").first.wait_for(timeout=T)
                pick_wing(page, "Review")
                page.locator("[data-testid='meeting-review']").wait_for(timeout=T)
                button = page.locator("[data-testid=review-project]").first
                button.wait_for(timeout=T)
                button.click()
                page.locator("[data-testid=room-body]").wait_for(timeout=10_000)
                page.wait_for_timeout(600)
                room = _api(page, "GET", f"/api/projects/{pid}/room", token=TOKEN)
                facts = self._facts(page)
                _record("f1-meeting-opens-room", width, {"hub_project": room["project"]["name"], **facts})
                _shot(page, "f1-meeting-opens-room", width)
                assert facts["window"], "the meeting's project button opened no Room"
                assert room["project"]["name"] == NAME
                _assert_room_named(page, width, NAME)
                assert "/projects" not in page.url
                assert not errors, errors
            finally:
                browser.close()

    def _two_late_rooms(self, page: Any) -> str:
        """Two Rooms, each with a milestone past its date, so each needs him
        (story 01's NEEDS YOU row) and the Chair names each row's project."""
        pid = self._project(page)
        other = self._project(page, "Vendor review")
        for project in (pid, other):
            _api(page, "POST", f"/api/projects/{project}/items",
                 {"item_type": "milestone", "title": "Cutover rehearsal",
                  "due_at": (date.today() - timedelta(days=7)).isoformat()}, token=TOKEN)
        return pid

    def _room_opened_for(self, page: Any, width: int, name: str, shot: str) -> dict[str, Any]:
        page.locator("[data-testid=room-body]").wait_for(timeout=10_000)
        page.wait_for_timeout(600)
        facts = self._facts(page)
        _record(shot, width, facts)
        _shot(page, shot, width)
        assert facts["window"], "no Room opened"
        _assert_room_named(page, width, name)
        return facts

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_chairs_project_button_opens_the_room(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._two_late_rooms(page)
                page.reload(wait_until="load")
                _normal_chair(page)
                button = page.get_by_role("button", name=f"Open the Project: {NAME}").first
                button.wait_for(state="attached", timeout=T)
                button.scroll_into_view_if_needed()
                button.click()
                self._room_opened_for(page, width, NAME, "f1-chair-opens-room")
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_shades_project_row_opens_the_room(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._two_late_rooms(page)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.locator(".desk-bell").click()
                page.locator(".desk-shade").wait_for(timeout=T)
                row = page.locator("[data-testid=shade-project-row]", has_text=NAME).first
                row.wait_for(timeout=T)
                row.get_by_role("button", name="Open").click()
                self._room_opened_for(page, width, NAME, "f1-shade-opens-room")
                assert not errors, errors
            finally:
                browser.close()

    # ── F2: the items section, as the ratified canvas draws it ───────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_late_milestone_and_a_risk_show_as_drawn(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = self._project(page)
                self._items(page, pid)
                empty = self._project(page, "Vendor review")
                self._room(page, pid)
                try:
                    page.locator("[data-testid=item-row]").first.wait_for(timeout=10_000)
                except Exception:
                    pass  # asserted below, as rendered
                room = _api(page, "GET", f"/api/projects/{pid}/room", token=TOKEN)
                first = self._facts(page)
                _shot(page, "items-late-first-view", width)
                assert first["item_rows"], "the Room shows no item: the late milestone is not on the face"
                page.locator("[data-section=items]").scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                facts = self._facts(page)
                pointer = self._pointer(page, width, ["[data-testid=steward-verb]", "[data-testid=room-refresh]"])
                _record("items-late", width, {"hub_health": room["health"]["assessment"], "hub_reason": room["health"].get("reason"),
                                              "hub_needs_you": [i["title"] for i in room["needsYou"]["items"]],
                                              "first_view": first, "section": facts, "pointer": pointer})
                _shot(page, "items-late-section", width)
                # The ratified order and words.
                rows = facts["item_rows"]
                assert facts["items_head"] == "ITEMS 5", facts["items_head"]
                assert [r.split(" ")[1] for r in rows] == ["Cutover", "Old", "Ledger", "Parallel", "Vendor"], rows
                assert "7 DAYS LATE" in rows[0] and "MILESTONE" in rows[0]
                assert "RISK" in rows[1] and "LIKELIHOOD HIGH" in rows[1] and "IMPACT HIGH" in rows[1]
                assert "MISSED" in rows[3] and "DROPPED" in rows[4]
                assert [lead["icon"] for lead in facts["item_leads"]] == ["●", "⚠", "○", "✗", "—"], facts["item_leads"]
                assert set(facts["item_danger_tokens"]) == {"7 DAYS LATE", "MISSED"}, facts["item_danger_tokens"]
                assert facts["controls_in_items"] == 0
                # Health and NEEDS YOU: the hub's, rendered (story 01's words).
                assert room["health"]["assessment"] == "at_risk"
                assert any("AT RISK" in c for c in first["head_chips"]), first["head_chips"]
                # Muad'Dib's ruling 3 (2026-09-28): the canvas words on the face,
                # the hub's words unchanged (test_the_late_words_are_the_canvas_words).
                assert "1 MILESTONE LATE" in first["head_chips"], first["head_chips"]
                assert first["headline"] == "1 needs you", first["headline"]
                assert any("Cutover rehearsal" in r for r in first["needs_you"]), first["needs_you"]
                assert facts["small_text_count"] == 0, facts["small_text"]
                assert facts["raw_buttons"] == [], facts["raw_buttons"]
                assert not facts["h_overflow"]
                # A project with no items: no section, no counter of zero.
                self._room(page, empty)
                none = self._facts(page)
                _shot(page, "items-empty-omitted", width)
                assert not none["items_section_present"] and none["item_rows"] == []
                # A failed items read is UNAVAILABLE + Retry, never empty.
                page.route("**/api/projects/*/items?*", lambda r: r.fulfill(status=503, body="{}"))
                self._room(page, pid)
                page.locator("[data-testid=items-unavailable]").wait_for(timeout=10_000)
                page.locator("[data-section=items]").scroll_into_view_if_needed()
                failed = self._facts(page)
                retry = self._pointer(page, width, ["[data-testid=items-retry]"])
                _record("items-unavailable", width, {**failed, "pointer": retry})
                _shot(page, "items-unavailable", width)
                assert failed["items_head"] and failed["items_head"].startswith("ITEMS"), failed["items_head"]
                assert all(not p["not_owned"] for p in retry), retry
                page.unroute("**/api/projects/*/items?*")
                page.locator("[data-testid=items-retry]").click()
                page.locator("[data-testid=item-row]").first.wait_for(timeout=10_000)
                assert len(self._facts(page)["item_rows"]) == 5
                assert all(not p["not_owned"] for p in pointer), pointer
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_late_words_are_the_canvas_words(self, width: int) -> None:
        """Muad'Dib's ruling 3 (2026-09-28), BUILD WHAT WAS RATIFIED: the face
        says `1 MILESTONE LATE` (health) and `MILESTONE · 7 DAYS LATE` (the
        NEEDS YOU why), mapped from the hub's fields; the hub keeps its own
        words (`1 OVERDUE`, `OVERDUE · 7 DAYS`) for MCP, read in the same test."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = self._project(page)
                _api(page, "POST", f"/api/projects/{pid}/items",
                     {"item_type": "milestone", "title": "Cutover rehearsal",
                      "due_at": (date.today() - timedelta(days=7)).isoformat()}, token=TOKEN)
                self._room(page, pid)
                room = _api(page, "GET", f"/api/projects/{pid}/room", token=TOKEN)
                page.locator("[data-testid=needs-you-why]").first.wait_for(timeout=T)
                # The head's tokens (the same locator on the base and the branch).
                reason = [t.strip() for t in page.locator("[data-testid=room-head-chips] .surface-token").all_inner_texts()]
                why = [w.strip() for w in page.locator("[data-testid=needs-you-why]").all_inner_texts()]
                _record("late-words", width, {"hub_reason": room["health"]["reason"],
                                              "hub_why": [i["why"] for i in room["needsYou"]["items"]],
                                              "face_reason": reason, "face_why": why})
                _shot(page, "late-words", width)
                assert room["health"]["reason"] == "1 OVERDUE"
                assert [i["why"] for i in room["needsYou"]["items"]] == ["OVERDUE · 7 DAYS"]
                assert "1 MILESTONE LATE" in reason and "1 OVERDUE" not in reason, reason
                assert why == ["MILESTONE · 7 DAYS LATE"], why
                assert not errors, errors
            finally:
                browser.close()

    # ── Mark delivered: copy and confirm (the Q0 ruling) ─────────────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_copy_then_mark_delivered_twice_reads_back_two_rows(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = self._project(page)
                uid = self._published(page, pid)
                self._room(page, pid)
                self._updates(page)
                self._open_update(page, uid)
                page.evaluate(FETCH_SEAM)
                page.locator("[data-testid=update-verb-copy]").click()
                page.wait_for_timeout(300)
                clip = page.evaluate("navigator.clipboard.readText().catch(e => 'ERR ' + e)")
                after_copy = self._facts(page)
                _shot(page, "deliver-1-after-copy", width)
                assert after_copy["deliver_verb"] == "Mark delivered", after_copy
                assert after_copy["delivery_head"] == "DELIVERY"
                # He leaves and returns (R4-3): Copy's 2 s feedback is gone and
                # no clipboard state is stored; Mark delivered is still offered.
                self._room(page, pid)
                self._updates(page)
                self._open_update(page, uid)
                page.evaluate(FETCH_SEAM)
                returned = self._facts(page)
                _shot(page, "deliver-2-returned", width)
                assert returned["deliver_verb"] == "Mark delivered", returned
                # To "Priya"; a DOUBLE-CLICK held at the hub: the pending face.
                page.locator("[data-testid=deliver-to]").fill("Priya")
                page.evaluate("window.__mode = {hold: true}")
                page.locator("[data-testid=deliver-verb]").dblclick()
                page.wait_for_timeout(300)
                pending = self._facts(page)
                busy = page.locator("[data-testid=deliver-verb]").evaluate(
                    "b => b.disabled || b.getAttribute('aria-busy') === 'true'")
                _shot(page, "deliver-3-pending", width)
                assert busy and pending["deliver_to"]["disabled"], pending["deliver_to"]
                assert pending["delivery_rows"] == []
                page.evaluate("window.__release()")
                page.locator("[data-testid=delivery-row]").first.wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                calls = page.evaluate("window.__calls")
                hub1 = self._deliveries(page, pid, uid)
                once = self._facts(page)
                _shot(page, "deliver-4-delivered-once", width)
                assert len(calls) == 1, calls  # one press, one call
                assert len(hub1) == 1 and hub1[0]["delivered_to"] == "Priya", hub1
                assert once["delivery_rows"] == [f"✓ Priya DELIVERED MANUAL {_delivery_time(hub1[0]['delivered_at'])}"], once["delivery_rows"]
                assert once["deliver_to"] == {"value": "", "disabled": False}
                # Priya was the wrong person: "Tomas" too. Both rows stay.
                page.locator("[data-testid=deliver-to]").fill("Tomas")
                page.locator("[data-testid=deliver-verb]").click()
                page.wait_for_function("document.querySelectorAll('[data-testid=delivery-row]').length >= 2", timeout=10_000)
                page.wait_for_timeout(300)
                calls = page.evaluate("window.__calls")
                hub2 = self._deliveries(page, pid, uid)
                both = self._facts(page)
                pointer = self._pointer(page, width, ["[data-testid=deliver-verb]", "[data-section=delivery] .desk-mic",
                                                      "[data-testid=update-verb-back]", "[data-testid=update-verb-copy]"])
                _record("deliver-two-rows", width, {"clipboard_head": str(clip)[:60], "calls": calls, "hub": hub2,
                                                    "after_copy": after_copy, "returned": returned, "pending": pending,
                                                    "once": once, "both": both, "pointer": pointer})
                _shot(page, "deliver-5-mistake-kept", width)
                assert calls[0]["command_id"] != calls[1]["command_id"], calls  # a new press, a new key
                assert [d["delivered_to"] for d in hub2] == ["Priya", "Tomas"], hub2
                assert both["delivery_rows"] == [f"✓ {d['delivered_to']} DELIVERED MANUAL {_delivery_time(d['delivered_at'])}" for d in hub2]
                # PHILO-10-04 (the owner's A2): DELIVERY N, the same count. The SEND
                # well now sits above (the ratified Send face); the manual history
                # itself still carries no egress badge.
                assert both["delivery_head"] == "DELIVERY 2", both["delivery_head"]
                assert both["delivery_egress"] == 0 and both["words_send"] and not both["modal"]
                assert both["small_text_count"] == 0, both["small_text"]
                assert both["raw_buttons"] == [], both["raw_buttons"]
                assert not both["h_overflow"]
                assert all(not p["not_owned"] for p in pointer), pointer
                # Back (the head verb) returns to the list; the ratified chip.
                self._back(page)
                listed = self._facts(page)
                _shot(page, "deliver-6-list-chip", width)
                assert listed["delivered_chips"] == ["✓ DELIVERY ×2"], listed["delivered_chips"]
                # A draft offers no Mark delivered.
                page.locator("[data-testid=update-verb-draft-deterministic]").click()
                page.locator("[data-testid=update-editor][data-lifecycle=draft]").wait_for(timeout=T)
                page.wait_for_timeout(500)
                draft = self._facts(page)
                _record("deliver-draft", width, draft)
                _shot(page, "deliver-7-draft-no-mark", width)
                assert draft["deliver_verb"] is None and draft["delivery_head"] is None
                assert not draft["h_overflow"], "the draft editor runs past the body"
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = self._project(page)
                a = self._published(page, pid)
                b = self._published(page, pid)
                self._room(page, pid)
                self._updates(page)
                page.evaluate(FETCH_SEAM)
                self._open_update(page, a)
                # A named refusal: the hub's code, its plain word; nothing kept.
                page.locator("[data-testid=deliver-to]").fill("Priya")
                page.evaluate("window.__mode = {refuse: 'update_not_published'}")
                page.locator("[data-testid=deliver-verb]").click()
                refused = page.locator("[data-testid=deliver-refused]")
                refused.wait_for(timeout=10_000)
                code = refused.get_attribute("data-code")
                word = refused.inner_text().replace("\n", " ")
                f_refused = self._facts(page)
                _shot(page, "deliver-8-refused", width)
                assert code == "update_not_published" and "REFUSED" in word and "NOT PUBLISHED" in word, word
                assert f_refused["deliver_to"] == {"value": "Priya", "disabled": False}
                page.evaluate("window.__mode = {refuse: 'idempotency_conflict'}")
                page.locator("[data-testid=deliver-verb]").click()
                page.wait_for_function("document.querySelector('[data-testid=deliver-refused]')?.dataset.code === 'idempotency_conflict'")
                assert "ALREADY USED" in page.locator("[data-testid=deliver-refused]").inner_text()
                assert self._deliveries(page, pid, a) == []
                # The answer is lost AFTER the row committed: result unknown.
                page.locator("[data-testid=deliver-to]").fill("Lena")
                page.evaluate("window.__mode = {lose: true}")
                page.locator("[data-testid=deliver-verb]").click()
                page.locator("[data-testid=deliver-uncertain]").wait_for(timeout=10_000)
                unknown = self._facts(page)
                _shot(page, "deliver-9-result-unknown", width)
                assert "NO ANSWER · RESULT UNKNOWN" in page.locator("[data-testid=deliver-uncertain]").inner_text()
                assert unknown["deliver_to"] == {"value": "Lena", "disabled": True}
                assert unknown["deliver_verb"] == "Retry"
                # Back -> B: clean. Back -> A: still unknown, Lena locked, Retry.
                self._back(page)
                self._open_update(page, b)
                f_b = self._facts(page)
                assert f_b["deliver_verb"] == "Mark delivered" and f_b["deliver_to"] == {"value": "", "disabled": False}
                assert not page.locator("[data-testid=deliver-uncertain]").count()
                self._back(page)
                self._open_update(page, a)
                f_a = self._facts(page)
                _shot(page, "deliver-10-back-on-a", width)
                assert f_a["deliver_verb"] == "Retry" and f_a["deliver_to"] == {"value": "Lena", "disabled": True}
                page.locator("[data-testid=deliver-retry]").click()
                page.locator("[data-testid=deliver-uncertain]").wait_for(state="detached", timeout=10_000)
                page.wait_for_timeout(300)
                calls = page.evaluate("window.__calls")
                lost, retry = calls[-2], calls[-1]
                hub_a, hub_b = self._deliveries(page, pid, a), self._deliveries(page, pid, b)
                retried = self._facts(page)
                pointer = self._pointer(page, width, ["[data-testid=deliver-verb]", "[data-testid=update-verb-back]"])
                _record("deliver-faults", width, {"calls": calls, "hub_a": hub_a, "hub_b": hub_b, "refused": f_refused,
                                                  "unknown": unknown, "b": f_b, "a": f_a, "retried": retried,
                                                  "pointer": pointer})
                _shot(page, "deliver-11-retried-one-row", width)
                assert retry["update_id"] == lost["update_id"] == a
                assert retry["command_id"] == lost["command_id"] and retry["delivered_to"] == lost["delivered_to"] == "Lena"
                assert [d["delivered_to"] for d in hub_a] == ["Lena"], hub_a
                assert hub_b == [] and not any(c["update_id"] == b for c in calls)
                assert retried["delivery_rows"] == [f"✓ Lena DELIVERED MANUAL {_delivery_time(hub_a[0]['delivered_at'])}"]
                assert all(not p["not_owned"] for p in pointer), pointer
                assert not errors, errors
            finally:
                browser.close()

    # ── F3: the steward's counts are the run's ───────────────────────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_steward_counts_equal_the_run(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = self._project(page)
                self._room(page, pid)
                page.locator("[data-testid=steward-verb]").click()
                page.locator("[data-testid=steward-verb-run]").click()
                page.wait_for_function(
                    "document.querySelector('[data-testid=steward-run-state]')?.innerText.toUpperCase().includes('COMPLETE')",
                    timeout=30_000)
                page.wait_for_timeout(800)
                runs = _api(page, "GET", f"/api/projects/{pid}/steward/runs", token=TOKEN)
                run = (runs.get("runs") or [runs])[0]
                steps = _api(page, "GET", f"/api/steward/runs/{run['id']}", token=TOKEN).get("steps", [])
                pr = run["summary"]["phase_results"]
                facts = self._facts(page)
                pointer = self._pointer(page, width, ["[data-testid=steward-open-review]"])
                _record("steward-counts", width, {"hub_run": run, "hub_steps": steps, **facts, "pointer": pointer})
                _shot(page, "steward-counts", width)
                plan = " | ".join(facts["plan"])
                sources = len(pr["observe"]["coverage"])
                effects = sum(1 for s in steps if not s["effect_kind"].startswith("phase:") and s["state"] == "completed")
                assert effects == pr["act"]["actions_taken"] == 0
                assert f"{sources} source" in plan, plan
                assert "1 effect" not in plan and "no effect allowed" in plan, plan
                assert "review opened" in plan and pr["compare"]["review_id"], plan
                assert "REVIEW OPENED" in facts["steward_outcome"] and "NO EFFECT ALLOWED" in facts["steward_outcome"]
                assert facts["raw_buttons"] == [], facts["raw_buttons"]
                assert facts["small_text_count"] == 0, facts["small_text"]
                assert all(not p["not_owned"] for p in pointer), pointer
                # The review the run opened is one press away.
                # The review the run opened is one press away: THAT review
                # (Codex Astra r1 finding 2), by its identity.
                page.locator("[data-testid=steward-open-review]").click()
                posture = page.locator("[data-testid=review-posture]").first
                posture.wait_for(timeout=T)
                assert posture.get_attribute("data-review-id") == pr["compare"]["review_id"]
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_review_on_a_completed_run_opens_that_review_even_after_acceptance(self, width: int) -> None:
        """Codex Astra r1 finding 2: complete a run, accept its review, reopen
        the run, press Review: the face shows the run's own (accepted) review
        and opens no new work -- the hub holds no new open review after."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = self._project(page)
                _api(page, "POST", f"/api/projects/{pid}/steward/runs", {}, token=TOKEN)
                page.wait_for_function(
                    f"""async () => {{ const r = await fetch('/api/projects/{pid}/steward/runs', {{headers: {{authorization: 'Bearer {TOKEN}'}}}});
                        const j = await r.json(); return (j.runs || [])[0]?.state === 'completed'; }}""", timeout=30_000)
                run = _api(page, "GET", f"/api/projects/{pid}/steward/runs", token=TOKEN)["runs"][0]
                rid = run["summary"]["phase_results"]["compare"]["review_id"]
                assert rid
                _api(page, "POST", f"/api/projects/{pid}/reviews/{rid}/accept", {}, token=TOKEN)
                before = _api(page, "GET", f"/api/projects/{pid}/delta", token=TOKEN)
                self._room(page, pid)
                page.locator("[data-testid=steward-verb]").click()
                page.locator("[data-testid=steward-list-item]").first.click()
                page.locator("[data-testid=steward-open-review]").wait_for(timeout=T)
                page.locator("[data-testid=steward-open-review]").click()
                posture = page.locator("[data-testid=review-posture]").first
                posture.wait_for(timeout=T)
                page.wait_for_timeout(600)
                after = _api(page, "GET", f"/api/projects/{pid}/delta", token=TOKEN)
                shown = {"id": posture.get_attribute("data-review-id"), "status": posture.get_attribute("data-review-status"),
                         "phase": posture.get_attribute("data-phase")}
                _record("steward-review-identity", width, {"run_review": rid, "shown": shown,
                                                            "delta_before": before, "delta_after": after})
                _shot(page, "steward-review-identity", width)
                # No new work: the hub holds no open review the press created.
                assert not (after.get("review_id") or (after.get("open_review") or {}).get("review_id")), after
                assert shown["id"] == rid and shown["status"] == "accepted", shown
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_refused_delivery_receipt_says_refused_and_why(self, width: int) -> None:
        """Codex Astra r1 finding 1: a mark refused by the hub (a draft:
        `update_not_published`, no row) is a RECEIPT that says ✗ REFUSED and
        NOT PUBLISHED, never a success chip or "MARKED DELIVERED"."""
        from playwright.sync_api import sync_playwright

        from .glass_infra import _api_allow_error

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = self._project(page)
                uid = _api(page, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"},
                           token=TOKEN)["update"]["id"]
                status, body = _api_allow_error(page, "POST", f"/api/updates/{uid}/delivered",
                                                {"delivered_to": "Priya", "command_id": "p903-refused"}, token=TOKEN)
                assert status == 400 and self._deliveries(page, pid, uid) == [], (status, body)
                hub = _api(page, "GET", f"/api/projects/{pid}/room", token=TOKEN)["receipts"]["items"]
                self._room(page, pid)
                row = page.locator("[data-testid=receipt-row]", has_text="DELIVERED").first
                row.wait_for(timeout=T)
                row.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                face = row.evaluate("""r => ({text: r.innerText.replace(/\s+/g, ' ').trim(),
                    lead: r.querySelector('.surface-state-chip')?.getAttribute('data-state'),
                    code: r.querySelector('[data-outcome]')?.dataset.code})""")
                _record("receipt-refused", width, {"hub": hub, "face": face})
                _shot(page, "receipt-refused", width)
                # The face first (as rendered), then the hub's record it draws.
                assert face["lead"] == "failure", face
                assert "MARKED DELIVERED" not in face["text"] and "MARK DELIVERED" in face["text"], face
                assert "REFUSED" in face["text"] and "NOT PUBLISHED" in face["text"], face
                assert face["code"] == "update_not_published", face
                mark = [i for i in hub if i["op"] == "mark_update_delivered"]
                assert mark and mark[0]["outcome"] == "refused" and mark[0].get("reason") == "update_not_published", hub
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_receipts_hold_only_this_rooms_work(self, width: int) -> None:
        """Codex Astra r1 finding 3 (inherited) and r2 finding 3: a project
        whose NAME contains this project's id, and an item in that other
        project whose TITLE equals this project's id, are not this Room's
        work: only the producer's project-identity field scopes a receipt."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = self._project(page)
                other = self._project(page, f"Mirror of {pid}")
                _api(page, "POST", f"/api/projects/{other}/items",
                     {"item_type": "risk", "title": pid, "details": {"likelihood": "high", "impact": "high"}},
                     token=TOKEN)
                hub = _api(page, "GET", f"/api/projects/{pid}/room", token=TOKEN)["receipts"]["items"]
                self._room(page, pid)
                rows = self._facts(page)["receipts"]
                _record("receipts-own-room", width, {"hub": hub, "face": rows})
                assert [i["op"] for i in hub].count("create_project") == 1, hub
                assert "create_item" not in [i["op"] for i in hub], hub
                assert rows.count("CREATE PROJECT") == 1 and "CREATE ITEM" not in rows, rows
                other_hub = _api(page, "GET", f"/api/projects/{other}/room", token=TOKEN)["receipts"]["items"]
                assert "create_item" in [i["op"] for i in other_hub], other_hub  # B's own work stays B's
                assert not errors, errors
            finally:
                browser.close()

    # ── F7: RECEIPTS are the Room's writes ───────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_receipts_list_the_writes_after_each_transition(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        def receipts(page: Any) -> list[str]:
            page.locator("[data-testid=receipt-row]").first.wait_for(timeout=10_000)
            return self._facts(page)["receipts"]

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = self._project(page)
                _api(page, "POST", f"/api/projects/{pid}/items", {"item_type": "risk", "title": "Freeze slips",
                     "details": {"likelihood": "high", "impact": "high"}}, token=TOKEN)
                self._room(page, pid)
                seen = {"created": receipts(page)}
                uid = self._published(page, pid)
                self._room(page, pid)
                seen["published"] = receipts(page)
                _api(page, "POST", f"/api/updates/{uid}/delivered", {"delivered_to": "Priya", "command_id": "p903-r"}, token=TOKEN)
                _api(page, "POST", f"/api/projects/{pid}/steward/runs", {}, token=TOKEN)
                page.wait_for_function(
                    f"""async () => {{ const r = await fetch('/api/projects/{pid}/steward/runs', {{headers: {{authorization: 'Bearer {TOKEN}'}}}});
                        const j = await r.json(); return (j.runs || [])[0]?.state === 'completed'; }}""", timeout=30_000)
                self._room(page, pid)
                seen["ran"] = receipts(page)
                page.locator("[data-testid=receipt-row]").first.scroll_into_view_if_needed()
                _record("receipts", width, seen)
                _shot(page, "receipts-writes", width)
                assert "CREATE PROJECT" in seen["created"] and "CREATE ITEM" in seen["created"], seen
                assert "PUBLISH UPDATE" in seen["published"], seen
                assert {"STEWARD RUN", "MARKED DELIVERED", "PUBLISH UPDATE"} <= set(seen["ran"]), seen
                assert not any(r.startswith("READ") for rows in seen.values() for r in rows), seen
                assert not errors, errors
            finally:
                browser.close()

    # ── F10: the Ask well covers no verb and no head ─────────────────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_ask_well_covers_no_verb_or_head(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = self._project(page)
                self._items(page, pid)
                self._room(page, pid)
                page.wait_for_timeout(800)  # the section reads settle (items, people)
                _settle(page)
                first = self._facts(page)
                verb = page.locator("[data-testid=steward-verb]")
                verb.evaluate("b => b.scrollIntoView({block: 'nearest'})")
                page.wait_for_timeout(300)
                hit = verb.evaluate("""b => { const r = b.getBoundingClientRect();
                    const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                    return {owned: !!el && b.contains(el), hit: el ? (el.closest('[data-testid]')?.dataset.testid || el.className) : null}; }""")
                pointer = self._pointer(page, width, ["[data-testid=steward-verb]"])
                _record("ask-well", width, {"first_view": first, "steward_hit": hit, "pointer": pointer})
                _shot(page, "ask-well-first-view", width)
                if width < 560:
                    assert first["under_ask_well"] == [], first["under_ask_well"]
                else:
                    # A wide window keeps Condition 7 (the well sticky at the
                    # foot, the ratified canvas as drawn): no VERB lies under it.
                    # A section head at the fold may (the RECEIPTS head; the
                    # story's evidence names it unpaid).
                    verbs = page.evaluate("""() => [...document.querySelectorAll('.desk-window .btn')].filter((e) => {
                        if (e.closest('.room-ask-container')) return false;
                        const r = e.getBoundingClientRect();
                        if (!r.width || r.bottom < 0 || r.top > innerHeight) return false;
                        const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                        return !!hit && !!hit.closest('.room-ask-container'); }).map((e) => e.innerText.trim())""")
                    assert verbs == [], verbs
                assert hit["owned"], hit
                assert all(not p["not_owned"] for p in pointer), pointer
                assert not errors, errors
            finally:
                browser.close()

    # ── F11: the update list's words ─────────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_update_list_words_fit_each_lifecycle(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = self._project(page)
                self._published(page, pid)
                _api(page, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"}, token=TOKEN)
                self._room(page, pid)
                self._updates(page)
                facts = self._facts(page)
                words = page.evaluate("""() => [...document.querySelectorAll('[data-testid=update-list-item] .update-list-row')]
                    .map(r => ({lifecycle: r.dataset.lifecycle, tokens: [...r.querySelectorAll('.surface-token')].map(t => t.innerText.trim())}))""")
                pointer = self._pointer(page, width, ["[data-testid=update-list-item] .surface-ledger-line, [data-testid=update-list-item] [role=button]"])
                _record("update-list", width, {**facts, "row_tokens": words, "pointer": pointer})
                _shot(page, "update-list-words", width)
                assert facts["update_list_head"] == "UPDATES 2", facts["update_list_head"]
                by = {w["lifecycle"]: w["tokens"] for w in words}
                assert by["published"][:2] == ["PUBLISHED", "REV 1"], by
                assert by["draft"][:1] == ["DRAFT"], by
                assert set(facts["update_emblems"]) == {"▤"}, facts["update_emblems"]
                assert facts["small_text_count"] == 0, facts["small_text"]
                assert not errors, errors
            finally:
                browser.close()
