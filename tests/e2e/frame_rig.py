"""The window-frame rig: the canvas seed (two projects, records, meetings,
people, a brief), the frame measures run in the page, and the staged open.

Was `ROOM`, `_seed`, `FRAME_JS` and `_stage` in
tests/e2e/test_philo13_11_frame_glass.py (moved here by the test diet,
push 2, 2026-10-12, so the files that share them import a rig, not a test
module).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .glass_infra import FOLDED_WORD_JS, _normal_chair, _settle

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

FRAME_JS = r"""(width) => {""" + FOLDED_WORD_JS + r"""
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
  const shells = [...document.querySelectorAll('.desk-window-shell:not([data-departing])')].filter(visible);
  const heads = shells.map((s) => s.querySelector(':scope > .desk-pullout-head')).filter(Boolean);
  const menus = [...document.querySelectorAll('.desk-menu-list')].filter(visible);
  const bar = document.querySelector('.desk-menubar');
  const scopes = [bar, ...heads, ...menus].filter(Boolean);
  const out = {width, windows: shells.length, blue: [], front: [], screen: null,
    layout: [], ownership: [], clipped: [], ellipsis: [], sideways: [], content: null, small_targets: [],
    small_text: [], low_contrast: []};

  // F1 one blue front window; the screen bar names it
  // The active-head token evolves with the owner's shared material.
  // Keep the one-front-window assertion; do not freeze the old Steel RGB.
  const paint = document.createElement('span');
  paint.style.backgroundColor = 'var(--wb-blue)'; document.body.appendChild(paint);
  const BLUE = rgb(getComputedStyle(paint).backgroundColor); paint.remove();
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
    // PHILO-13-12 (C2): depth is built, so the set ends iconify, zoom, depth
    // (1440) and Back ... depth (393).
    const first = btns[0], last = btns.slice(width > 720 ? -3 : -1);
    const exit = width > 720 ? `Close ${name}` : `Back from ${name}`;
    if (!first || first.getAttribute('aria-label') !== exit) out.layout.push({name, first: first && label(first)});
    const want = width > 720 ? [`Iconify ${name}`, `Zoom ${name}`, `To back ${name}`] : [`To back ${name}`];
    if (last.map((b) => b.getAttribute('aria-label')).join('|') !== want.join('|')) out.layout.push({name, last: last.map(label)});
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
    // every frame target: the screen bar, the title bars AND every choice of
    // an open menu (menuitem, menuitemcheckbox, menuitemradio)
    const targets = [...(bar ? bar.querySelectorAll('button') : []), ...heads.flatMap((h) => [...h.querySelectorAll('button')]),
      ...menus.flatMap((m) => [...m.querySelectorAll('[role^="menuitem"]')])].filter(visible);
    for (const t of targets) { const r = t.getBoundingClientRect();
      if (r.width < 44 - 0.5 || r.height < 44 - 0.5) out.small_targets.push({control: label(t), w: Math.round(r.width), h: Math.round(r.height)}); }
  }

  // F5 frame text in place: the 12 px floor and the contrast it reads at
  for (const scope of scopes) {
    const walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const el = n.parentElement; const text = n.textContent.trim();
      const cs = getComputedStyle(el); const size = parseFloat(cs.fontSize);
      // a zero-size word has no box: read it when its parent is visible
      const zero = size === 0 && cs.display !== 'none' && cs.visibility !== 'hidden'
        && el.parentElement && visible(el.parentElement);
      if (!text || !(visible(el) || zero)) continue;
      // the ONE exception: a word folded into a screen-bar picture control
      // (glass_infra.FOLDED_WORD_JS); any other size under 12 px fails
      if (foldedWord(el, text)) continue;
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
