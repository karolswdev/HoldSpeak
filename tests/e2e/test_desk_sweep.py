"""PHILO-17 test diet: ONE generic sweep over every desk application.

The compositor (Phase 16) put the desk's windows on the hub, so one rig can
open every application the same way an agent does and run the same fences on
each, in place of one "this face renders cleanly" file per phase.

* The applications come from the one manifest, ``web/src/desk/applications.ts``:
  collection runs that module itself in Node (``--experimental-strip-types``;
  its imports are types and lazy loaders, so nothing else loads). No Python
  copy of the list. Each application's scoped variants come from the same
  table (``subjectRef``, an alias ``scope``), and three seeded subjects add an
  object window each: a Project Room, a meeting window, a person window.
  Two poses that are not applications ride along: the Chair's Needs-you
  window (``chair:needs``, opened the same way) and the ⌘K palette open on a
  query that hits several sections (its own fence: rows inside the shelf, the
  selected row in view and at 4.5:1).
  A window the hub refuses (``window_not_on_hub``, desk_window_service.py)
  cannot open through the hub; it is listed in ``NOT_ON_HUB_APPS``.
* One hub per xdist worker (a module-scoped boot from ``glass_infra._boot``,
  every isolation switch it sets), seeded once with a realistic desk through
  the existing seed helpers: the canvas week with a 1:1 and a calendar
  (test_philo13_06_open_glass._seed), the Conductor flight
  (test_philo14_c4_conductor_glass._seed), a Project with items
  (test_hs158_room_glass) and watched sources (_hs173_seed.seed_health_room),
  a meeting whose summary failed (Needs you), and a saved destination.
* Each case clears the hub's windows, loads the desk, and opens ONE window
  with ``POST /api/desk/windows/{id}/open``. No menus.
* The fences, at 1440x900 and 393x852, on the window and on each of its wings
  (opened through the window's own wing control):
    drawn     the window opened on the hub is drawn and settles
    fit       the window is inside the viewport
    clean     no page error, no console error, no page-wide sideways scroll
    readable  no clipped or overlapping text (glass_infra on-glass reader)
    contrast  faint and ember text at 4.5:1 (the HS-202-05 rule, _MEASURE)
    floor     no readable text under 12 px (the PHILO-13-18 rule, _MEASURE)
    clipped   no text box whose scrollWidth exceeds its clientWidth without
              a scroller (a single-line ellipsis is lawful, UX-CANON A.6)
    overlap   no two interactive controls overlap (painted boxes)
    library   every verb is a library Button: no raw <button>
    material  the bevel grammar (test_philo14_b2_material_glass._assert_material)
    still     nothing interactive moves for 1.5 s after the window settles
    egress    every request goes to the hub's own origin (data:, blob: allowed)
  The bare desk (no window) is one more case, read over the whole screen.
* Every HTML route the hub serves (test_route_preflight.PAGE_ROUTES, fenced
  against the live app there) loads with no page error and no console error,
  read after its window settles and the same 1.5 s watch.
* Known reds on main are listed in ``KNOWN_REDS`` and marked
  ``xfail(strict=True, raises=KnownRed)``: a NEW red in the same case fails;
  a known red that heals fails too, so the list only shrinks. A red that
  shows on some runs only is listed with "MAYBE: " and gates neither way.

No fixed waits: condition waits only, except the 1.5 s no-move window.
"""
from __future__ import annotations

import functools
import json
import os
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="the desk sweep needs Playwright")

from holdspeak.services.desk_window_service import window_app  # noqa: E402
from holdspeak.services.errors import ValidationError  # noqa: E402

from ._hs173_seed import seed_health_room  # noqa: E402
from . import test_hs158_room_glass as hs158  # noqa: E402
from . import test_philo13_06_open_glass as open13  # noqa: E402
from .glass_infra import (  # noqa: E402
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _rendered_text_faults,
    clear_hub_windows_http,
)
from .test_hs202_05_first_use_type_floor import _FAINT_JS, _MEASURE, GATED_CONTRAST  # noqa: E402
from .test_philo14_b2_material_glass import _assert_material  # noqa: E402
from .test_philo14_c4_conductor_glass import _seed as _seed_agents  # noqa: E402
from .test_philo17_meeting_window_glass import _save_meeting  # noqa: E402
from .test_route_preflight import PAGE_ROUTES  # noqa: E402

pytestmark = [pytest.mark.e2e]

REPO = Path(__file__).resolve().parents[2]
TOKEN = "desk-sweep"
SIZES = {1440: 900, 393: 852}
T = 20_000
STILL_MS = 1500
TOLERANCE = 2
PALETTE_QUERY = "ledger"  # a Project, meetings, a decision, a note of the seed
MAYBE = "MAYBE: "


class KnownRed(AssertionError):
    """A red listed in KNOWN_REDS (the only failure the xfail accepts)."""


# ── the manifest, read from applications.ts itself ─────────────────────────

_MANIFEST_JS = """
import(process.argv[1]).then((m) => {
  process.stdout.write(JSON.stringify(m.DESK_APPLICATIONS.map((a) => ({
    action: a.action, windowId: a.windowId, label: a.label, href: a.href,
    subjectRef: a.subjectRef ?? null,
    scopes: (a.aliases ?? []).map((x) => x.scope).filter(Boolean),
  }))));
});
"""


@functools.cache
def _manifest() -> list[dict[str, Any]]:
    source = REPO / "web" / "src" / "desk" / "applications.ts"
    out = subprocess.run(
        ["node", "--experimental-strip-types", "--no-warnings", "-e", _MANIFEST_JS, source.as_uri()],
        capture_output=True, text=True, timeout=60,
    )
    assert out.returncode == 0, f"could not read {source} in Node: {out.stderr}"
    return json.loads(out.stdout)


def window_app_on_hub(wid: str) -> bool:
    try:
        window_app(wid)
    except ValidationError:
        return False
    return True


def _cases() -> tuple[list[tuple[str, str, str | None]], dict[str, str]]:
    """(case id, window id, scope) per hub window; and the refused ones."""
    cases: list[tuple[str, str, str | None]] = [("desk", "", None)]
    refused: dict[str, str] = {}
    seen: set[tuple[str, str | None]] = set()
    for app in _manifest():
        wid = app["windowId"]
        try:
            window_app(wid)
        except ValidationError as exc:
            refused[wid] = str(exc)
            continue
        for scope in [None, app["subjectRef"], *app["scopes"]]:
            if (wid, scope) in seen:
                continue
            seen.add((wid, scope))
            cases.append((wid if scope is None else f"{wid}@{scope}", wid, scope))
    # The seeded subjects: their ids are known after the seed ({...} below).
    cases += [
        ("room", "surface-project-memory", "project:{room}"),
        ("meeting", "pullout:meeting:{meeting}", None),
        ("person", "pullout:people:{person}", None),
        # Not applications, opened the same way: the Chair's Needs-you window
        # (its seed rows: accepted requests, a failed summary) ...
        ("needs", "chair:needs", None),
        # ... and the ⌘K palette, open on a query that hits several sections.
        ("palette", "desk-tool-shelf", PALETTE_QUERY),
    ]
    return cases, refused


CASES, NOT_ON_HUB_APPS = _cases()
# The window an application's address opens (the manifest's `href`), for the
# route test: a route waits for its window before it reads the errors.
ROUTE_WINDOWS = {a["href"]: a["windowId"] for a in _manifest() if a["href"] not in ("/", None)}

# ── known reds on main (filled from the first sweep; see the PR body) ─────
# (case id, width) -> {fence key: the defect}. A fence key is the fence name,
# or "<fence>@<wing>" for a wing. A defect that starts with "MAYBE: " shows on
# some runs only (it depends on timing or the clock): it is neither a new red
# when it shows nor a healed one when it does not.
KNOWN_REDS: dict[tuple[str, int], dict[str, str]] = {
    ("desk", 1440): {
        "overlap": "MAYBE: the People drawer icon and the Conductor drawer icon overlap by 5 px on the desk screen "
                   "(when the People caption `1:1 HH:MM` is wide enough)",
        "readable": "MAYBE: the People drawer icon overlaps the Conductor icon, and its count badge 1 overlaps its caption",
    },
    ("desk", 393): {
        "overlap": "the Dock's Delivery launcher and the More AppIcons control overlap (49x54 px)",
    },
    ("surface-places", 1440): {"overlap": "a Place card and its Favorite star are two controls drawn over each other (the star sits on the card Button)", "readable": "a Place card and its Favorite star are two controls drawn over each other (the star sits on the card Button)"},
    ("surface-places", 393): {"overlap": "a Place card and its Favorite star are two controls drawn over each other (the star sits on the card Button)", "readable": "a Place card and its Favorite star are two controls drawn over each other (the star sits on the card Button)"},
    ("surface-processes", 1440): {
        "clipped": "Processes: the target CHANNEL.SAVE_DESTINATION is 225 px in a 160 px cell, clipped",
        "readable": "Processes: CHANNEL.SAVE_DESTINATION runs over its neighbour Owner-session · Node:hub-project-writer",
    },
    ("surface-companion", 1440): {
        "library@Delivery": "Agents, Delivery wing: raw <button class=desk-list-open> rows (DeliveryListSection.tsx:54)",
        "still": "MAYBE: Agents: the Roster and How it connects sections move 44 px after the window settles (a late read)",
    },
    ("surface-companion", 393): {
        "library@Delivery": "Agents, Delivery wing: raw <button class=desk-list-open> rows (DeliveryListSection.tsx:54)",
    },
    ("surface-components", 1440): {
        "readable": "the Components catalog: receipt labels and topology node labels clip; at 393 the catalog body scrolls sideways", "readable@Record": "the Components catalog: receipt labels and topology node labels clip; at 393 the catalog body scrolls sideways",
        "contrast": "the Components catalog: the ember state-chip icons (* and ●) read 1:1 on their ground", "contrast@Record": "the Components catalog: the ember state-chip icons (* and ●) read 1:1 on their ground",
        "library": "the Components catalog: raw <button> demos (signal-btn Open popover, surface-topology-node This Mac / LAN Server / Cloud API)", "library@Record": "the Components catalog: raw <button> demos (signal-btn Open popover, surface-topology-node This Mac / LAN Server / Cloud API)",
    },
    ("surface-components", 393): {
        "readable": "the Components catalog: receipt labels and topology node labels clip; at 393 the catalog body scrolls sideways", "readable@Record": "the Components catalog: receipt labels and topology node labels clip; at 393 the catalog body scrolls sideways",
        "contrast": "the Components catalog: the ember state-chip icons (* and ●) read 1:1 on their ground", "contrast@Record": "the Components catalog: the ember state-chip icons (* and ●) read 1:1 on their ground",
        "library": "the Components catalog: raw <button> demos (signal-btn Open popover, surface-topology-node This Mac / LAN Server / Cloud API)", "library@Record": "the Components catalog: raw <button> demos (signal-btn Open popover, surface-topology-node This Mac / LAN Server / Cloud API)",
    },
    ("surface-concierge", 1440): {
        "still": "MAYBE: Runs on: the switchboard job rows (switchboard-job-*) move 84 px after the window settles",
    },
    ("meeting", 1440): {
        "still": "MAYBE: the meeting window: meeting-decide and the transcript speakers move 113 px after the window settles",
    },
    ("surface-concierge", 393): {
        "material": "Runs on at 393: the Dictation clean-up OFF Button has no bevel (box-shadow none)",
    },
    ("room", 1440): {
        "readable": "MAYBE: Room: risk rows (Settlement latency under load, RISK, LIKELIHOOD HIGH, DUE SEP 15) read as overlapping "
                    "the ask bar (Ask this project, Result, Choose); the reader does not read z-order, so this may be "
                    "rows scrolled under an opaque bar",
        "material@History": "Room, History wing: the GITHUB filter Button has no bevel (box-shadow none, not --bevel-raised)",
        "still": "MAYBE: Room: the footer receipt (room-footer-receipt) moves 51 px after the window settles",
        "overlap": "MAYBE: Room: the footer's Pause and Choose controls overlap (50x27 px) on some loads",
    },
    ("needs", 393): {
        "drawn": "a chair:needs window opened on the hub is not drawn at 393: the phone draws only the Chair window "
                 "its own cache names (chairWindows.ts `phone`); the hub adapter (hubWindows.ts adapterFor) clears "
                 "`closed` and leaves `phone` empty",
    },
    ("room", 393): {"material@History": "Room, History wing: the GITHUB filter Button has no bevel (box-shadow none, not --bevel-raised)"},
}


def _params() -> list[Any]:
    out = []
    for case in CASES:
        for width in SIZES:
            known = {k: v for k, v in KNOWN_REDS.get((case[0], width), {}).items() if not v.startswith(MAYBE)}
            marks = [pytest.mark.xfail(strict=True, raises=KnownRed,
                                       reason="; ".join(f"{k}: {v}" for k, v in sorted(known.items())))] \
                if known else []
            out.append(pytest.param(case, width, id=f"{case[0]}-{width}", marks=marks))
    return out


# ── the rig: one hub, one browser per module (per xdist worker) ───────────

@pytest.fixture(scope="module")
def pw_browser():
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    try:
        yield browser
    finally:
        browser.close()
        pw.stop()


@pytest.fixture(scope="module")
def desk(tmp_path_factory: pytest.TempPathFactory, pw_browser: Any) -> Any:
    _ensure_build()
    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.delivery.factory_launch as factory_launch
    from holdspeak.agent_context import event_log
    from holdspeak.db import get_database

    tmp = tmp_path_factory.mktemp("desk-sweep")
    with pytest.MonkeyPatch.context() as mp:
        state = tmp / "home" / ".holdspeak"
        state.mkdir(parents=True)
        # The C4 seed's agent state, inside this HOME (as the C4 rig does).
        mp.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
        mp.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
        mp.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
        # The reused seed helpers speak to the hub with their own module token.
        mp.setattr(open13, "TOKEN", TOKEN)
        mp.setattr(hs158, "TOKEN", TOKEN)
        server, base = _boot(tmp, mp, token=TOKEN)
        try:
            home = tmp / "home"
            week = open13._seed(home, base)  # canvas week, 1:1 Priya, calendar, brief
            _seed_agents(home)  # the Conductor flight
            _save_meeting("m-sweep-failed", "Vendor sync", 3, "error")  # a Needs-you member
            ctx = pw_browser.new_context()
            page = ctx.new_page()
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            room = hs158._seed_populated_project(page)
            seed_health_room(get_database(), project_id=room)
            folder = home / "Documents" / "HoldSpeak" / "Team updates"
            folder.mkdir(parents=True, exist_ok=True)
            _api(page, "POST", "/api/channels/destinations",
                 {"name": "Team updates", "channel": "file", "folder": str(folder)}, token=TOKEN)
            ctx.close()
            yield {"base": base, "room": room, "meeting": "m-standup", "person": week["priya"]}
        finally:
            server.stop()


# ── the page measures ──────────────────────────────────────────────────────

SETTLED_JS = r"""(id) => {
  const w = id ? document.getElementById(id) : document.querySelector('[data-testid=desk-screen]');
  if (!w) return false;
  const r = w.getBoundingClientRect();
  if (r.width < 1 || r.height < 1) return false;
  if (w.querySelector('[aria-busy="true"]:not(button)')) return false;
  if (/Loading…/.test(w.innerText || '')) return false;
  if ([...document.images].some((i) => i.getBoundingClientRect().width > 0 && !(i.complete && i.naturalWidth > 0))) return false;
  return !document.getAnimations().some((a) => a.playState === 'running'
    && (a.effect && a.effect.getTiming().iterations !== Infinity));
}"""

UNSETTLED_JS = r"""(id) => {
  const w = id ? document.getElementById(id) : document.querySelector('[data-testid=desk-screen]');
  if (!w) return {window: null, open: [...document.querySelectorAll('.desk-window-shell')].map((e) => e.id)};
  const r = w.getBoundingClientRect();
  return {box: [r.width, r.height].map(Math.round),
    busy: [...w.querySelectorAll('[aria-busy="true"]:not(button)')].map((e) => e.className).slice(0, 5),
    loading: /Loading…/.test(w.innerText || ''),
    images: [...document.images].filter((i) => i.getBoundingClientRect().width > 0 && !(i.complete && i.naturalWidth > 0)).map((i) => i.src).slice(0, 5),
    animations: document.getAnimations().filter((a) => a.playState === 'running' && a.effect && a.effect.getTiming().iterations !== Infinity)
      .map((a) => (a.animationName || a.transitionProperty || 'waapi') + ' on ' + String(a.effect.target && a.effect.target.className).slice(0, 40)).slice(0, 5)};
}"""

FIT_JS = r"""(id) => {
  const w = document.getElementById(id);
  if (!w) return 'no window';
  const r = w.getBoundingClientRect();
  if (r.width < 40 || r.height < 40) return `not drawn: ${Math.round(r.width)}x${Math.round(r.height)}`;
  if (r.left < -1 || r.top < -1 || r.right > innerWidth + 1 || r.bottom > innerHeight + 1)
    return `outside the viewport: ${[r.left, r.top, r.right, r.bottom].map(Math.round)} in ${innerWidth}x${innerHeight}`;
  return null;
}"""

# Shared by the three generic readers: the scope, visibility, a name.
_COMMON_JS = r"""
  const scope = sel ? document.querySelector(sel) : document.body;
  if (!scope) return ['no scope ' + sel];
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 1 && r.height > 1 && cs.visibility !== 'hidden' && cs.display !== 'none' && Number(cs.opacity) > 0.05
      && (!e.checkVisibility || e.checkVisibility({contentVisibilityAuto: true})); };
  const name = (e) => ((e.getAttribute('aria-label') || e.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40)
    || e.tagName.toLowerCase() + '.' + String(e.className).trim().split(/\s+/)[0]);
"""

# clipped: a text holder whose content is wider than its box, with no
# sideways scroller on it or above it, and no single-line ellipsis.
CLIPPED_JS = r"""(sel) => {""" + _COMMON_JS + r"""
  const out = [];
  for (const e of scope.querySelectorAll('*')) {
    if (!visible(e)) continue;
    if (![...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) continue;
    if (e.scrollWidth <= e.clientWidth + 1 || e.clientWidth === 0) continue;
    const cs = getComputedStyle(e);
    if (['auto', 'scroll'].includes(cs.overflowX)) continue;
    if (cs.textOverflow === 'ellipsis' && cs.whiteSpace === 'nowrap') continue;
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.tagName)) continue;
    let scrolled = false;
    for (let a = e.parentElement; a && a !== scope.parentElement; a = a.parentElement) {
      if (['auto', 'scroll'].includes(getComputedStyle(a).overflowX) && a.scrollWidth > a.clientWidth + 1) { scrolled = true; break; }
    }
    if (!scrolled) out.push(`${name(e)} (${e.scrollWidth} > ${e.clientWidth})`);
  }
  return out;
}"""

# overlap: two interactive controls whose painted boxes cross.
OVERLAP_JS = r"""(sel) => {""" + _COMMON_JS + r"""
  const CTL = 'button, [role=button], [role=tab], [role=menuitem], [role=menuitemcheckbox], [role=checkbox], '
    + '[role=switch], [role=option], input:not([type=hidden]), textarea, select, a[href]';
  const painted = (e) => { const r = e.getBoundingClientRect();
    let L = Math.max(r.left, 0), T = Math.max(r.top, 0), R = Math.min(r.right, innerWidth), B = Math.min(r.bottom, innerHeight);
    for (let a = e.parentElement; a && a !== document.documentElement; a = a.parentElement) {
      const cs = getComputedStyle(a); const ar = a.getBoundingClientRect();
      if (cs.overflowX !== 'visible') { L = Math.max(L, ar.left); R = Math.min(R, ar.right); }
      if (cs.overflowY !== 'visible') { T = Math.max(T, ar.top); B = Math.min(B, ar.bottom); }
    }
    return (R - L > 1 && B - T > 1) ? {L, T, R, B} : null; };
  const ctls = [...scope.querySelectorAll(CTL)].filter(visible)
    .filter((c) => !(c.parentElement && c.parentElement.closest(CTL)))
    .map((c) => ({c, p: painted(c)})).filter((x) => x.p);
  const out = [];
  for (let i = 0; i < ctls.length; i++) for (let j = i + 1; j < ctls.length; j++) {
    const a = ctls[i], b = ctls[j];
    if (a.c.contains(b.c) || b.c.contains(a.c)) continue;
    const w = Math.min(a.p.R, b.p.R) - Math.max(a.p.L, b.p.L), h = Math.min(a.p.B, b.p.B) - Math.max(a.p.T, b.p.T);
    if (!(w > 1 && h > 1)) continue;
    // an inset by design: a control drawn inside a text entry (the in-well mic)
    const inside = (x, y) => x.p.L >= y.p.L - 1 && x.p.R <= y.p.R + 1 && x.p.T >= y.p.T - 1 && x.p.B <= y.p.B + 1;
    if ((inside(a, b) && b.c.matches('textarea, input')) || (inside(b, a) && a.c.matches('textarea, input'))) continue;
    out.push(`${name(a.c)} x ${name(b.c)} (${Math.round(w)}x${Math.round(h)} px)`);
  }
  return out;
}"""

# library: a raw <button> is not the library Button (`btn`, `btn--chrome`)
# nor one of the library's own gadgets (the live171 walk's list) or the
# window frame's head.
LIBRARY_JS = r"""(sel) => {""" + _COMMON_JS + r"""
  // The library gadgets draw their own buttons (web/src/desk/surface/gadgets.tsx:
  // the stepper arrows, the table's add row, the transport key).
  const GADGETS = ['[role=tablist]', '.gadget-arrows', '.cycle-gadget', '.fold-gadget', '.check-gadget', '.stepper-gadget',
    '.scroll-hint', '.desk-traffic', '.desk-wings', '.surface-ledger-row', '.desk-pullout-head', '.desk-window-handle'];
  const CLASSES = ['btn', 'btn--chrome', 'desk-mic', 'surface-disclosure-trigger', 'gadget-transport-key', 'gadget-table-add',
    'surface-ledger-line'];
  return [...scope.querySelectorAll('button')].filter(visible)
    .filter((b) => !CLASSES.some((c) => b.classList.contains(c)))
    .filter((b) => !GADGETS.some((g) => b.closest(g)))
    .map((b) => `<button class="${String(b.className).slice(0, 60)}"> ${name(b)}`);
}"""

# still: every interactive element's box, each frame, keyed by element.
RECORD_JS = r"""([sel, ms]) => new Promise((resolve) => {
  const scope = sel ? document.querySelector(sel) : document.body;
  const CTL = 'button, [role=button], [role=tab], input, textarea, select, a[href], [data-testid]';
  const ids = new WeakMap(); let n = 0; const rows = {}; const t0 = performance.now();
  const tick = () => {
    for (const el of scope ? scope.querySelectorAll(CTL) : []) {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      let k = ids.get(el);
      if (k === undefined) {
        if (r.top >= innerHeight || r.bottom <= 0 || getComputedStyle(el).visibility !== 'visible') continue;
        ids.set(el, k = ++n);
        rows[k] = {name: (el.getAttribute('data-testid') || el.getAttribute('aria-label') || el.textContent || el.tagName)
          .trim().replace(/\s+/g, ' ').slice(0, 40), x: r.left, y: r.top, worst: 0};
      } else {
        const row = rows[k];
        row.worst = Math.max(row.worst, Math.abs(r.left - row.x), Math.abs(r.top - row.y));
      }
    }
    if (performance.now() - t0 < ms) requestAnimationFrame(tick); else resolve(Object.values(rows));
  };
  requestAnimationFrame(tick);
})"""

WINGS_JS = r"""(id) => {
  const w = document.getElementById(id);
  if (!w) return {kind: null, wings: []};
  const tabs = [...w.querySelectorAll('.desk-wings [role=tab]')].filter((t) => t.getBoundingClientRect().width > 0);
  if (tabs.length) return {kind: 'tabs', wings: tabs.map((t) => ({label: t.textContent.trim(),
    on: t.getAttribute('aria-selected') === 'true' || t.classList.contains('is-on')}))};
  const menu = w.querySelector('.desk-wings-menu');
  return {kind: menu && menu.getBoundingClientRect().width > 0 ? 'menu' : null, wings: []};
}"""


PALETTE_JS = r"""() => {
  const shelf = document.getElementById('desk-tool-shelf').getBoundingClientRect();
  const list = document.getElementById('desk-palette-listbox');
  const view = list.getBoundingClientRect();
  const rows = [...list.querySelectorAll('[id^=desk-palette-option-]')].filter((r) => r.getBoundingClientRect().height > 0);
  const outside = rows.map((r) => [r, r.getBoundingClientRect()])
    .filter(([, b]) => b.left < shelf.left - 1 || b.right > shelf.right + 1)
    .map(([r, b]) => `${r.id} ${Math.round(b.left)}..${Math.round(b.right)} outside ${Math.round(shelf.left)}..${Math.round(shelf.right)}`);
  const sections = [...new Set(rows.map((r) => r.id.replace('desk-palette-option-', '').split(':')[0]))];
  const sel = list.querySelector('.desk-deck-row.is-selected');
  const num = (c) => (c.match(/[\d.]+/g) || [0, 0, 0]).slice(0, 3).map(Number);
  let selected = null;
  if (sel) { const b = sel.getBoundingClientRect(); const cs = getComputedStyle(sel);
    selected = {text: sel.textContent.trim().slice(0, 40), bg: num(cs.backgroundColor), fg: num(cs.color),
      inView: b.top >= view.top - 1 && b.bottom <= view.bottom + 1 && b.bottom <= innerHeight + 1}; }
  return {outside, sections, selected};
}"""


def _contrast(a: list[float], b: list[float]) -> float:
    def lum(c: list[float]) -> float:
        ch = [v / 255 for v in c]
        ch = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in ch]
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]
    x, y = lum(a), lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


class _Case:
    """One window on one page: the fences, their failures by fence key."""

    def __init__(self, page: Any, base: str, wid: str, errors: list[str], requests: list[str]) -> None:
        self.page, self.base, self.wid = page, base, wid
        self.errors, self.requests = errors, requests
        self.sel = f'[id="{wid}"]' if wid else None
        self.failures: dict[str, str] = {}
        self.baseline: tuple[set[str], set[str]] = (set(), set())

    def settle(self) -> None:
        try:
            self.page.wait_for_function(SETTLED_JS, arg=self.wid or None, timeout=T)
        except Exception as exc:  # noqa: BLE001 -- name what held it
            raise AssertionError(f"{self.wid or 'desk'} never settled: {self.page.evaluate(UNSETTLED_JS, self.wid or None)}") from exc

    def measure(self) -> tuple[set[str], set[str]]:
        m = self.page.evaluate(_MEASURE, self.page.evaluate(_FAINT_JS))
        small = {f"{s['text']!r} {s['px']}px ({s['path']})" for s in m["small"]}
        contrast = {f"{c['text']!r} {c['ratio']}:1 < {c['need']} ({c['kind']}, {c['path']})"
                    for c in m["contrast"] if c["kind"] in GATED_CONTRAST}
        return small, contrast

    def fences(self, wing: str = "") -> None:
        page, sel = self.page, self.sel
        at = f"@{wing}" if wing else ""

        def fail(fence: str, detail: Any) -> None:
            if detail:
                self.failures[fence + at] = str(detail)[:1500]

        if self.wid:
            fail("fit", page.evaluate(FIT_JS, self.wid))
        faults = _rendered_text_faults(page, sel or "[data-testid=desk-screen], .desk-menubar", on_glass=True)
        fail("readable", ([f"clipped {c}" for c in faults["clipped"]]
                          + [f"overlap {o[:2]}" for o in faults["overlaps"]]))
        small, contrast = self.measure()
        fail("floor", sorted(small - self.baseline[0]))
        fail("contrast", sorted(contrast - self.baseline[1]))
        fail("clipped", page.evaluate(CLIPPED_JS, sel))
        fail("overlap", page.evaluate(OVERLAP_JS, sel))
        fail("library", page.evaluate(LIBRARY_JS, sel))
        try:
            _assert_material(page, self.wid or "desk", sel)
        except AssertionError as exc:
            fail("material", exc)
        moved = [r for r in page.evaluate(RECORD_JS, [sel, STILL_MS]) if r["worst"] > TOLERANCE]
        fail("still", [f"{r['name']} moved {round(r['worst'])} px" for r in moved])
        # After the 1.5 s watch: an error a late read raises is counted too.
        try:
            _assert_clean(page, self.errors)
        except AssertionError as exc:
            fail("clean", exc or self.errors)
        origin = urllib.parse.urlsplit(self.base).netloc
        fail("egress", sorted({u for u in self.requests
                               if not u.startswith(("data:", "blob:")) and urllib.parse.urlsplit(u).netloc != origin}))

    def palette(self) -> None:
        """The palette's own fence: every row inside the shelf, the selected
        row in view, the selected row's plate at 4.5:1 (the rule of
        test_palette_two_line_glass)."""
        facts = self.page.evaluate(PALETTE_JS)
        problems = list(facts["outside"])
        if not facts["sections"] or len(facts["sections"]) < 2:
            problems.append(f"the query drew {facts['sections']} sections, not several")
        if not facts["selected"]:
            problems.append("no selected row")
        else:
            if not facts["selected"]["inView"]:
                problems.append(f"the selected row is out of view: {facts['selected']}")
            if _contrast(facts["selected"]["bg"], facts["selected"]["fg"]) < 4.5:
                problems.append(f"the selected row reads under 4.5:1: {facts['selected']}")
        if problems:
            self.failures["palette"] = str(problems)[:1500]

    def wings(self) -> None:
        """Each wing of the window, opened with the window's own wing control."""
        page, front = self.page, self.page.locator(self.sel)
        found = page.evaluate(WINGS_JS, self.wid)
        labels: list[str] = []
        if found["kind"] == "tabs":
            labels = [w["label"] for w in found["wings"] if not w["on"] and w["label"]]
        elif found["kind"] == "menu":
            front.locator(".desk-wings-menu").first.click()
            rows = page.locator(".desk-menu-list [role='menuitemcheckbox']")
            rows.first.wait_for(timeout=T)
            labels = [r.inner_text().strip() for r in rows.all()
                      if r.get_attribute("aria-checked") != "true" and r.inner_text().strip()]
            # The menu stays open: the first wing is picked from it as it is.
        for label in labels:
            try:
                if found["kind"] == "tabs":
                    front.locator(".desk-wings [role='tab']", has_text=label).first.click()
                else:
                    if not page.locator(".desk-menu-list [role='menuitemcheckbox']").count():
                        front.locator(".desk-wings-menu").first.click()
                    page.locator(".desk-menu-list [role='menuitemcheckbox']", has_text=label).first.click()
                self.settle()
            except Exception as exc:  # noqa: BLE001 -- a wing that cannot be opened is a red
                self.failures[f"wing@{label}"] = f"could not open: {str(exc)[:300]}"
                continue
            self.fences(label)


def _page(browser: Any, width: int, base: str) -> tuple[Any, Any, list[str], list[str]]:
    ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                              has_touch=width < 720, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(30_000)
    errors: list[str] = []
    requests: list[str] = []
    page.on("pageerror", lambda e: errors.append(f"pageerror: {str(e)[:300]}"))
    page.on("console", lambda m: errors.append(f"console: {m.text[:300]}") if m.type == "error" else None)
    page.on("request", lambda r: requests.append(r.url))
    return ctx, page, errors, requests

_BASELINES: dict[int, tuple[set[str], set[str]]] = {}


def _baseline(browser: Any, base: str, width: int) -> tuple[set[str], set[str]]:
    """The bare desk's floor and contrast reads at this width, once per
    worker: a window case reports only what the window adds (the desk's own
    are the `desk` case's)."""
    if width not in _BASELINES:
        clear_hub_windows_http(base, TOKEN)
        ctx, page, _, _ = _page(browser, width, base)
        try:
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            page.wait_for_function(SETTLED_JS, arg=None, timeout=T)
            _BASELINES[width] = _Case(page, base, "", [], []).measure()
        finally:
            ctx.close()
    return _BASELINES[width]


def _hub_open(base: str, wid: str, scope: str | None) -> None:
    import urllib.request

    request = urllib.request.Request(
        f"{base}/api/desk/windows/{urllib.parse.quote(wid, safe='')}/open",
        data=json.dumps({"object_ref": scope} if scope else {}).encode(), method="POST",
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as resp:
        assert resp.status < 300, resp.status


def _verdict(case_id: str, width: int, failures: dict[str, str]) -> None:
    dump = os.environ.get("DESK_SWEEP_DUMP")  # a directory: one JSON per case (to refresh KNOWN_REDS)
    if dump:
        Path(dump).mkdir(parents=True, exist_ok=True)
        (Path(dump) / f"{case_id.replace('/', '_')}-{width}.json").write_text(json.dumps(failures, indent=1))
    listed = KNOWN_REDS.get((case_id, width), {})
    maybe = {k for k, v in listed.items() if v.startswith(MAYBE)}
    known = {k: v for k, v in listed.items() if k not in maybe}
    failures = {k: v for k, v in failures.items() if k not in maybe}
    lines = lambda keys: "\n".join(f"  {k}: {failures.get(k, known.get(k))}" for k in sorted(keys))  # noqa: E731
    new = set(failures) - set(known)
    healed = set(known) - set(failures)
    if new:
        raise AssertionError(f"{case_id} at {width}: new reds\n{lines(new)}")
    if healed:
        raise AssertionError(f"{case_id} at {width}: healed, remove from KNOWN_REDS\n{lines(healed)}")
    if known:
        raise KnownRed(f"{case_id} at {width}: known reds\n{lines(known)}")


@pytest.mark.timeout(240)
@pytest.mark.parametrize(("case", "width"), _params())
def test_every_window_holds_the_fences(desk: dict[str, Any], pw_browser: Any,
                                       case: tuple[str, str, str | None], width: int) -> None:
    case_id, wid, scope = case
    wid, scope = wid.format(**desk), (scope.format(**desk) if scope else None)
    base = desk["base"]
    baseline = _baseline(pw_browser, base, width) if wid else (set(), set())
    clear_hub_windows_http(base, TOKEN)
    palette = case_id == "palette"
    if wid and not palette:
        # Opened on the hub before the page loads: the page seeds its windows
        # from the hub's rows (a view that is live follows the same rows by
        # its desk_changed frame; that follow is fenced in the PHILO-16 glass).
        _hub_open(base, wid, scope)
    ctx, page, errors, requests = _page(pw_browser, width, base)
    try:
        page.goto(f"{base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        page.locator("[data-testid=desk-screen]").wait_for(state="attached", timeout=T)
        sweep = _Case(page, base, wid, errors, requests)
        sweep.baseline = baseline
        if palette:
            page.wait_for_function(SETTLED_JS, arg=None, timeout=T)
            page.locator("[aria-controls=desk-tool-shelf]").first.click()
            page.locator("[aria-controls=desk-palette-listbox]").fill(scope)
            page.locator("#desk-palette-listbox .desk-deck-row.is-selected").wait_for(timeout=T)
            if width >= 720:
                page.mouse.move(2, 2)  # the selection is the top row, not a hover
        try:
            sweep.settle()
        except AssertionError as exc:  # not drawn: no other fence can read it
            sweep.failures["drawn"] = str(exc)[:1500]
        else:
            sweep.fences()
            if palette:
                sweep.palette()
            elif wid:
                sweep.wings()
        _verdict(case_id, width, sweep.failures)
    finally:
        ctx.close()


ROUTE_KNOWN_REDS: dict[str, str] = {}


@pytest.mark.timeout(120)
@pytest.mark.parametrize("route", [
    pytest.param(r, marks=[pytest.mark.xfail(strict=True, reason=ROUTE_KNOWN_REDS[r])] if r in ROUTE_KNOWN_REDS else [])
    for r in PAGE_ROUTES])
def test_every_html_route_loads_clean(desk: dict[str, Any], pw_browser: Any, route: str) -> None:
    """Every HTML route the hub serves loads with no page or console error
    (the list is test_route_preflight.PAGE_ROUTES, fenced there against the
    routes the live app serves)."""
    base = desk["base"]
    clear_hub_windows_http(base, TOKEN)
    ctx, page, errors, _ = _page(pw_browser, 1440, base)
    try:
        sep = "&" if "?" in route else "?"
        page.goto(f"{base}{route}{sep}token={TOKEN}", wait_until="load")
        wid = ROUTE_WINDOWS.get(route)
        desk_route = True
        try:  # Welcome and Presence draw no desk (web/src/routes.tsx PRODUCT_ROUTES)
            page.locator("[data-testid=desk-screen]").wait_for(state="attached", timeout=5_000)
        except Exception:  # noqa: BLE001
            desk_route = False
        if desk_route:
            # A desk route: past the Chair, then its window (or the bare desk) settled.
            _normal_chair(page)
            if wid and window_app_on_hub(wid):
                page.locator(f'[id="{wid}"]').wait_for(timeout=T)
            page.wait_for_function(SETTLED_JS, arg=wid if wid and window_app_on_hub(wid) else None, timeout=T)
        else:
            page.wait_for_function(
                "() => document.readyState === 'complete' && !document.getAnimations().some((a) => a.playState === 'running'"
                " && a.effect && a.effect.getTiming().iterations !== Infinity)", timeout=T)
        # The same 1.5 s watch the window cases keep: a late error is counted.
        page.evaluate(RECORD_JS, [None, STILL_MS])
        assert not [e for e in errors if "ResizeObserver" not in e], f"{route}: {errors}"
    finally:
        ctx.close()
