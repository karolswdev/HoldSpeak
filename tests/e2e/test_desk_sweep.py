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
    drawn     the window opened on the hub settles and is visible: no
              display none, opacity 0 or visibility hidden on it or above
              it, and it is the thing at its own centre
    fit       the window is inside the viewport
    clean     no page error, no console error, no page-wide sideways scroll
    readable  no clipped or overlapping text (glass_infra on-glass reader);
              a scope it cannot read fails
    contrast  faint and ember text at 4.5:1 (the HS-202-05 rule, _MEASURE)
    floor     no readable text under 12 px (the PHILO-13-18 rule, _MEASURE)
    clipped   no text run cut by ANY ancestor with overflow hidden or clip
              (wholly cut text too), and no text box that spills its holder
              without a scroller (a single-line ellipsis is lawful, A.6)
    overlap   no two interactive controls overlap (painted boxes)
    library   every verb is a library Button: no raw <button>
    material  the bevel grammar (test_philo14_b2_material_glass._assert_material)
    still     nothing interactive moves for 1.5 s after the window settles
    egress    every request goes to the hub's own origin (data:, blob: allowed)
  The bare desk (no window) is one more case, read over the whole screen.
* Every HTML route the hub serves (tests/unit/test_route_preflight.PAGE_ROUTES, fenced
  against the live app there) draws what it is for: a standalone page its
  visible content, every other address the desk and the window it opens
  (shown, with text); and no page error or console error after the 1.5 s watch.
* Known reds on main are listed in ``KNOWN_REDS`` and marked
  ``xfail(strict=True, raises=KnownRed)``. Each entry excuses ONE defect: a
  fence key and a regex over one observation. Any other observation fails,
  in any fence; a strict entry nothing matches fails as healed. A red that
  shows on some runs only is ``maybe=True``: it excuses only its own matches.
* Collection fails when the manifest yields fewer than MANIFEST_FLOOR rows,
  or when the hub refuses a window for any reason but ``window_not_on_hub``.

No fixed waits: condition waits only, except the 1.5 s no-move window.
"""
from __future__ import annotations

import functools
import json
import os
import re
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any, NamedTuple

import pytest

pytest.importorskip("playwright.sync_api", reason="the desk sweep needs Playwright")

from holdspeak.services.desk_window_service import window_app  # noqa: E402
from holdspeak.services.errors import ValidationError  # noqa: E402

from tests._evidence import evidence_dir  # noqa: E402

from ._hs173_seed import seed_health_room  # noqa: E402
from . import room_seed_rig as hs158  # noqa: E402
from . import open_rig as open13  # noqa: E402
from .glass_infra import (  # noqa: E402
    _api,
    _boot,
    _ensure_build,
    _normal_chair,
    _rendered_text_faults,
    clear_hub_windows_http,
)
from .test_hs202_05_first_use_type_floor import _FAINT_JS, _MEASURE, GATED_CONTRAST  # noqa: E402
from .test_philo14_b2_material_glass import LAMP_WORDS, MATERIAL_JS  # noqa: E402
from .conductor_rig import _seed as _seed_agents  # noqa: E402
from .test_philo17_meeting_window_glass import _save_meeting  # noqa: E402
from tests.unit.test_route_preflight import PAGE_ROUTES  # noqa: E402  (the e2e preflight is parked; the sweep fences every route)

pytestmark = [pytest.mark.e2e]

REPO = Path(__file__).resolve().parents[2]
MANIFEST_FLOOR = 22
TOKEN = "desk-sweep"
SIZES = {1440: 900, 393: 852}
T = 20_000
STILL_MS = 1500
TOLERANCE = 2
PALETTE_QUERY = "ledger"  # a Project, meetings, a decision, a note of the seed


class KnownRed(AssertionError):
    """A red listed in KNOWN_REDS (the only failure the xfail accepts)."""


# ── the manifest, read from applications.ts itself ─────────────────────────

_MANIFEST_JS = """
import(process.argv[1]).then((m) => {
  process.stdout.write(JSON.stringify(m.DESK_APPLICATIONS.map((a) => ({
    action: a.action, windowId: a.windowId, label: a.label, href: a.href,
    subjectRef: a.subjectRef ?? null,
    scopes: (a.aliases ?? []).map((x) => x.scope).filter(Boolean),
    aliases: (a.aliases ?? []).map((x) => ({key: x.key, scope: x.scope ?? null})),
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
    apps = json.loads(out.stdout)
    # No silent zero: a manifest that reads as empty (or loses most of its rows)
    # would make a sweep that sees nothing and passes.
    assert len(apps) >= MANIFEST_FLOOR, (
        f"{source} yielded {len(apps)} applications, under the floor of {MANIFEST_FLOOR} "
        f"(24 on 2026-10-11, less a margin of 2): the manifest read is broken, or rows were removed; "
        f"lower MANIFEST_FLOOR only for a deliberate removal")
    return apps


#: The one refusal the sweep expects: a window the hub will not hold.
NOT_ON_HUB_CODE = "window_not_on_hub"


def window_app_on_hub(wid: str) -> bool:
    """False only for the hub's deliberate refusal; any other refusal raises."""
    try:
        window_app(wid)
    except ValidationError as exc:
        if exc.code == NOT_ON_HUB_CODE:
            return False
        raise
    return True


def _cases() -> tuple[list[tuple[str, str, str | None]], dict[str, str]]:
    """(case id, window id, scope) per hub window; and the refused ones."""
    cases: list[tuple[str, str, str | None]] = [("desk", "", None)]
    refused: dict[str, str] = {}
    seen: set[tuple[str, str | None]] = set()
    for app in _manifest():
        wid = app["windowId"]
        if not window_app_on_hub(wid):  # any refusal but window_not_on_hub fails collection
            refused[wid] = NOT_ON_HUB_CODE
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


# ── the routes: what each served address must draw ───────────────────────
# The pages that draw no desk screen, and what each must show (routes.tsx
# PRODUCT_ROUTES: Presence draws its card; Welcome hands off to the Get ready
# cards, which stand in place of the desk screen):
STANDALONE_ROUTES = {"/presence": ".presence-card", "/welcome": ".firstrun-card-title"}
# Addresses that land on the bare desk (App.tsx: `/desk` and `*` go to `/`).
DESK_ROUTES = {"/": None, "/desk": None, "/workbench": None}


def _route_windows() -> dict[str, str]:
    """Each demoted address -> the window it opens: routes.tsx DEMOTED_ROUTES
    (path -> application key), the key through the manifest (an action, or an
    alias of one)."""
    source = (REPO / "web" / "src" / "routes.tsx").read_text(encoding="utf-8")
    block = source[source.index("export const DEMOTED_ROUTES"):]
    pairs = re.findall(r'path:\s*"([^"]+)",\s*surface:\s*"([^"]+)"', block)
    assert len(pairs) >= 15, f"routes.tsx DEMOTED_ROUTES read {len(pairs)} rows: the read is broken"
    by_key: dict[str, str] = {}
    for app in _manifest():
        by_key.setdefault(app["action"], app["windowId"])
        for alias in app["aliases"]:
            by_key.setdefault(alias["key"], app["windowId"])
    out = {}
    for path, key in pairs:
        assert key in by_key, f"routes.tsx sends {path} to {key!r}, which the manifest does not know"
        out[path] = by_key[key]
    return out


ROUTE_WINDOWS = _route_windows()

# ── known reds on main ─────────────────────────────────────────────────────
# (case id, width) -> the defects, ONE observation each: a fence key (the fence,
# or "<fence>@<wing>") and a regex that must match that one observation (an
# element, an element pair, a text). Only matching observations are excused;
# any other observation in the same fence fails. A strict defect that no
# observation matches fails as healed. A MAYBE defect (it shows on some runs
# only) excuses its own matches and is never "healed".


class Red(NamedTuple):
    key: str
    match: str
    why: str
    maybe: bool = False


# The library's topology map is a pan surface: 500 px of demo nodes in a 363 px
# view at 393. Its far nodes are reached by a drag; the reader reads them as cut.
# Fitting it on a phone is a design decision (zoom to fit, or a stacked phone
# layout), not a placement fix.
_TOPOLOGY_393 = [
    Red("readable", r"^clipped '.+' in surface-topology-map-area$",
        "Components at 393: the topology demo is wider than the phone; its far nodes pan into view"),
    Red("clipped", r"' cut by \.surface-topology-map-area \(x\)$",
        "Components at 393: the topology demo is wider than the phone; its far nodes pan into view"),
]

KNOWN_REDS: dict[tuple[str, int], list[Red]] = {
    ("surface-components", 393): _TOPOLOGY_393,
    ("desk", 1440): [
        Red("overlap", r"^People, DRAWER, 1:1 [\d:]+ x Conductor, DRAWER, ", "the People drawer icon overlaps the "
            "Conductor icon by 5 px when its `1:1 HH:MM` caption is wide (depends on the clock)", maybe=True),
        Red("readable", r"^overlap 'People, DRAWER, 1:1 [\d:]+' x 'Conductor, DRAWER, ",
            "the same People x Conductor icon overlap", maybe=True),
        Red("readable", r"^overlap '1' x 'People, DRAWER, 1:1 [\d:]+'$",
            "the People icon's count badge 1 overlaps its caption", maybe=True),
    ],
    ("surface-concierge", 1440): [
        # The ratified order: the jobs paint before the detection, the engines
        # fill in (useRunsOn.ts:222, fenced by runsOn.test.tsx "paints the
        # roster's jobs before the detection lands"). Holding them is a ruling.
        Red("still", r"^(switchboard-job-\w+|concierge-[\w-]+) moved \d+ px$",
            "Runs on: the switchboard job rows move 84 px after the window settles", maybe=True),
    ],
    ("room", 1440): [
        Red("readable", r"^overlap '(Settlement latency under load|Compliance team sign-off|RISK|LIKELIHOOD HIGH|"
            r"DUE SEP 15)' x '(Ask this project|Speak to ask this project|Result|Choose)'$",
            "Room: the risk rows read as overlapping the ask bar (the reader ignores z-order: the rows may be "
            "scrolled under an opaque bar); where they sit depends on the late read", maybe=True),
        # A late read (the sources row) lands after the window settles and moves the body
        # down (295 px seen); what overlaps the ask bar then depends on when it lands.
        # The footer receipt holds still now (it is said with the body it reads for).
        Red("still", r"^(room-add-source|steward-verb|source-scope|Pause|since-read-empty) "
            r"moved \d+ px$", "Room: a late read moves the body after the window settles (not reproduced "
            "on 2026-10-11 under held reads; kept until a run shows it)", maybe=True),
        Red("readable", r"^overlap '(GH|org/repo|\d+ OPEN PRS|·|CI GREEN|CI RED)' x 'Ask this project'$",
            "Room: the sources row reads as overlapping the ask bar after the late read lands", maybe=True),
        Red("overlap", r"^Pause x Choose ", "Room: the footer's Pause and Choose overlap on some loads", maybe=True),
        Red("readable", r"^overlap '(Pause|Choose)' x '(Pause|Choose)'$",
            "Room: the footer's Pause and Choose overlap on some loads", maybe=True),
    ],
}


def _params() -> list[Any]:
    out = []
    for case in CASES:
        for width in SIZES:
            known = [r for r in KNOWN_REDS.get((case[0], width), []) if not r.maybe]
            marks = [pytest.mark.xfail(strict=True, raises=KnownRed,
                                       reason="; ".join(f"{r.key}: {r.why}" for r in known))] if known else []
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

# drawn: the window is shown (no visibility:hidden, no opacity 0, no display
# none on itself or any ancestor) and is the thing at its own centre (unless
# a listed cover is there; none is listed today).
COVERS: tuple[str, ...] = ()
DRAWN_JS = r"""([sel, covers]) => {
  const w = sel ? document.querySelector(sel) : null;
  if (!w) return 'no element ' + sel;
  for (let a = w; a; a = a.parentElement) {
    const cs = getComputedStyle(a);
    if (cs.display === 'none') return `display none on ${a.id || a.className || a.tagName}`;
    if (Number(cs.opacity) <= 0.05) return `opacity ${cs.opacity} on ${a.id || a.className || a.tagName}`;
  }
  const cs = getComputedStyle(w);
  if (cs.visibility !== 'visible') return `visibility ${cs.visibility}`;
  const r = w.getBoundingClientRect();
  if (r.width < 40 || r.height < 40) return `not drawn: ${Math.round(r.width)}x${Math.round(r.height)}`;
  const x = Math.min(Math.max(r.left + r.width / 2, 0), innerWidth - 1);
  const y = Math.min(Math.max(r.top + r.height / 2, 0), innerHeight - 1);
  const hit = document.elementFromPoint(x, y);
  if (!hit) return 'nothing at its centre';
  if (w.contains(hit)) return null;
  if (covers.some((c) => hit.closest(c))) return null;
  return `covered at its centre by ${hit.id || hit.className || hit.tagName}`;
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

# clipped: every visible text run, walked through ALL its ancestors (not
# only the nearest clipping box): a box with overflow hidden or clip that cuts
# the run on an axis clips it, wholly or in part (wholly clipped text is
# reported, never dropped). A scroll container (auto, scroll) makes the run
# reachable on its axis: from there up, the scroller's box stands for the
# run on that axis. Lawful: a single-line ellipsis cut by its own box
# (UX-CANON A.6), and a visually-hidden (sr-only) run.
CLIPPED_JS = r"""(sel) => {
  const scopes = sel ? [...document.querySelectorAll(sel)] : [document.body];
  const out = [];
  const shown = (e) => { const cs = getComputedStyle(e);
    return cs.visibility !== 'hidden' && cs.display !== 'none'
      && (!e.checkVisibility || e.checkVisibility({contentVisibilityAuto: true, opacityProperty: true})); };
  const srOnly = (e) => { for (let a = e; a && a !== document.body; a = a.parentElement) {
      const r = a.getBoundingClientRect(), cs = getComputedStyle(a);
      if ((r.width <= 1 || r.height <= 1) && cs.overflow !== 'visible') return true;
      if (cs.clip === 'rect(0px, 0px, 0px, 0px)' || /inset\(50%|inset\(100%/.test(cs.clipPath)) return true; }
    return false; };
  const label = (a) => (a.id ? '#' + a.id : '') + (typeof a.className === 'string' && a.className.trim()
    ? '.' + a.className.trim().split(/\s+/)[0] : (a.id ? '' : a.tagName.toLowerCase()));
  for (const scope of scopes) {
    const walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const text = n.textContent.trim();
      const el = n.parentElement;
      if (!text || !el || !shown(el) || srOnly(el)) continue;
      const range = document.createRange(); range.selectNodeContents(n);
      const r = range.getBoundingClientRect();
      if (r.width < 1 && r.height < 1) continue;
      // A text box wider than its own holder with no scroller spills (it is
      // not whole in its box even where nothing cuts it).
      const hcs = getComputedStyle(el);
      if (el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0 && !['auto', 'scroll'].includes(hcs.overflowX)
          && !(hcs.textOverflow === 'ellipsis' && hcs.whiteSpace === 'nowrap')
          && !['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName)) {
        let scrolled = false;
        for (let a = el.parentElement; a; a = a.parentElement) {
          if (['auto', 'scroll'].includes(getComputedStyle(a).overflowX) && a.scrollWidth > a.clientWidth + 1) { scrolled = true; break; }
        }
        if (!scrolled) { out.push(`'${text.slice(0, 50)}' spills ${label(el)} (${el.scrollWidth} > ${el.clientWidth})`); continue; }
      }
      let L = r.left, R = r.right, T = r.top, B = r.bottom;
      // An absolutely positioned box escapes the overflow of every static
      // ancestor up to its containing block; a fixed one, up to a transform.
      let escape = null;
      for (let a = el; a && a !== document.documentElement; a = a.parentElement) {
        const cs = getComputedStyle(a); const ar = a.getBoundingClientRect();
        const contains = cs.transform !== 'none' || cs.filter !== 'none' || /paint|layout|strict|content/.test(cs.contain);
        if (escape === 'absolute' && a !== el && (cs.position !== 'static' || contains)) escape = null;
        if (escape === 'fixed' && a !== el && contains) escape = null;
        if (escape && a !== el) { if (cs.position === 'fixed') escape = 'fixed'; continue; }
        const ox = cs.overflowX, oy = cs.overflowY;
        const cutX = ['hidden', 'clip'].includes(ox) && (L < ar.left - 1 || R > ar.right + 1);
        const cutY = ['hidden', 'clip'].includes(oy) && (T < ar.top - 1 || B > ar.bottom + 1);
        const ellipsis = cutX && !cutY && cs.textOverflow === 'ellipsis' && cs.whiteSpace === 'nowrap'
          && (a === el || el.closest && a.contains(el));
        if ((cutX || cutY) && !ellipsis) {
          out.push(`'${text.slice(0, 50)}' cut by ${label(a)} (${cutX ? 'x' : ''}${cutY ? 'y' : ''})`);
          break;
        }
        if (ellipsis) break;
        if (['auto', 'scroll'].includes(ox)) { L = ar.left; R = ar.right; }
        if (['auto', 'scroll'].includes(oy)) { T = ar.top; B = ar.bottom; }
        if (cs.position === 'absolute') escape = 'absolute';
        else if (cs.position === 'fixed') escape = 'fixed';
      }
    }
  }
  return [...new Set(out)];
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
    // the one ratified waiver (test_philo13_13_dock_glass._read; the species
    // glass `pager`): at the phone width ONLY (the gadget is the phone's,
    // dock.css), the next page of the Dock's shelf (an AppIcon of the shelf
    // itself) scrolls under its sticky More AppIcons gadget, drawn over it on
    // purpose. At 1440, or against any other control, an overlap fails.
    const phone = matchMedia('(max-width: 720px)').matches;
    const pager = (x, y) => phone && x.c.matches('.desk-dock > .desk-dock-more')
      && y.c.matches('.desk-dock > .desk-dock-launch') && y.c.parentElement === x.c.parentElement;
    if (pager(a, b) || pager(b, a)) continue;
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
  // A specimen (the Components catalog's demo wings, data-specimen) is the
  // body's content, not the window's wing control.
  const tabs = [...w.querySelectorAll('.desk-wings [role=tab]')].filter((t) => t.getBoundingClientRect().width > 0)
    .filter((t) => !t.closest('[data-specimen]'));
  if (tabs.length) return {kind: 'tabs', wings: tabs.map((t) => ({label: t.textContent.trim(),
    on: t.getAttribute('aria-selected') === 'true' || t.classList.contains('is-on')}))};
  const menu = w.querySelector('.desk-wings-menu:not([data-specimen] *)');
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


def _material_faults(page: Any, face: str, root: str | None) -> list[str]:
    """test_philo14_b2_material_glass._assert_material, every observation
    (that helper stops at the first): the same reads, the same rules."""
    m = page.evaluate(MATERIAL_JS, root)
    if m is None:
        return [f"{face}: no scope {root}"]
    raised, sunken = m["raised"], m["sunken"]
    out: list[str] = []
    if "none" in (raised, sunken, m["soft"], m["softSunken"]):
        out.append("a bevel token resolves to none")
    for b in m["buttons"]:
        if not b["shadow"].startswith((raised, m["wbRaised"])):
            out.append(f"Button '{b['name']}' is not raised (box-shadow {b['shadow'][:40]})")
    for t in m["tokens"]:
        if not t["shadow"].startswith(m["softSunken"] if t["active"] else m["soft"]):
            out.append(f"token '{t['name']}' has the wrong soft bevel")
    for c in m["chips"]:
        ok = (c["border"] == "0px" and c["bg"] in ("rgba(0, 0, 0, 0)", "transparent") and c["lampW"] == "10px"
              and (c["lampShadow"] or "").startswith(raised) and (c["name"] or "").strip()
              and (not c["word"] or c["name"] == c["word"])
              and (c["word"] or c["state"] not in LAMP_WORDS or c["name"] == LAMP_WORDS[c["state"]]))
        if not ok:
            out.append(f"state chip '{c['name']}' breaks the lamp grammar")
    for f in m["facts"]:
        ok = (f["border"] == "rgba(0, 0, 0, 0)" and f["shadow"] == "none"
              and f["bg"] in ("rgba(0, 0, 0, 0)", "transparent")
              and (f["tone"] not in ("warn", "danger", "ok")
                   or (f["lampW"] == "10px" and (f["lampShadow"] or "").startswith(raised))))
        if not ok:
            out.append(f"fact '{f['text']}' is not flat")
    for shadow in m["bodies"]:
        if not shadow.startswith(sunken):
            out.append(f"a window body is not the well (box-shadow {shadow[:40]})")
    return out


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
        self.failures: dict[str, list[str]] = {}
        self.baseline: tuple[set[str], set[str]] = (set(), set())
        #: DESK_SWEEP_SHOTS=1: one shot per fence pass, named by this stem.
        self.shot = ""

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
        if self.shot and os.environ.get("DESK_SWEEP_SHOTS") == "1":
            name = re.sub(r"[^\w@.-]+", "_", f"{self.shot}{('-' + wing) if wing else ''}")
            page.screenshot(path=str(evidence_dir("desk-sweep") / f"{name}.png"))

        def fail(fence: str, observations: Any) -> None:
            if isinstance(observations, str):
                observations = [observations]
            observations = [str(o)[:400] for o in (observations or []) if o]
            if observations:
                self.failures.setdefault(fence + at, []).extend(observations)

        scope = sel or "[data-testid=desk-screen], .desk-menubar"
        fail("drawn", page.evaluate(DRAWN_JS, [sel or "[data-testid=desk-screen]", list(COVERS)]))
        if self.wid:
            fail("fit", page.evaluate(FIT_JS, self.wid))
        faults = _rendered_text_faults(page, scope, on_glass=True)
        if not faults["scopes"]:
            fail("readable", f"no visible {scope}: nothing was read")
        fail("readable", ([f"clipped '{c['text']}' in {c['in']}" for c in faults["clipped"]]
                          + [f"overlap '{o[0]}' x '{o[1]}'" for o in faults["overlaps"]]))
        small, contrast = self.measure()
        fail("floor", sorted(small - self.baseline[0]))
        fail("contrast", sorted(contrast - self.baseline[1]))
        fail("clipped", page.evaluate(CLIPPED_JS, scope))
        fail("overlap", page.evaluate(OVERLAP_JS, sel))
        fail("library", page.evaluate(LIBRARY_JS, sel))
        fail("material", _material_faults(page, self.wid or "desk", sel))
        moved = [r for r in page.evaluate(RECORD_JS, [sel, STILL_MS]) if r["worst"] > TOLERANCE]
        fail("still", [f"{r['name']} moved {round(r['worst'])} px" for r in moved])
        # After the 1.5 s watch: an error a late read raises is counted too.
        fail("clean", [e for e in self.errors if "ResizeObserver" not in e])
        if not page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"):
            fail("clean", "the page scrolls sideways")
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
            self.failures["palette"] = [str(p)[:400] for p in problems]

    def wings(self) -> None:
        """Each wing of the window, opened with the window's own wing control."""
        page, front = self.page, self.page.locator(self.sel)
        found = page.evaluate(WINGS_JS, self.wid)
        labels: list[str] = []
        if found["kind"] == "tabs":
            labels = [w["label"] for w in found["wings"] if not w["on"] and w["label"]]
        elif found["kind"] == "menu":
            front.locator(".desk-wings-menu:not([data-specimen] *)").first.click()
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
                        front.locator(".desk-wings-menu:not([data-specimen] *)").first.click()
                    page.locator(".desk-menu-list [role='menuitemcheckbox']", has_text=label).first.click()
                self.settle()
            except Exception as exc:  # noqa: BLE001 -- a wing that cannot be opened is a red
                self.failures.setdefault(f"wing@{label}", []).append(f"could not open: {str(exc)[:300]}")
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


def _verdict(case_id: str, width: int, failures: dict[str, list[str]]) -> None:
    dump = os.environ.get("DESK_SWEEP_DUMP")  # a directory: one JSON per case (to refresh KNOWN_REDS)
    if dump:
        Path(dump).mkdir(parents=True, exist_ok=True)
        (Path(dump) / f"{case_id.replace('/', '_')}-{width}.json").write_text(json.dumps(failures, indent=1))
    _judge(f"{case_id} at {width}", KNOWN_REDS.get((case_id, width), []), failures)


def _judge(where: str, listed: list[Red], failures: dict[str, list[str]]) -> None:
    """Each observation is excused only by a listed defect of its own fence
    key whose regex matches it; a strict defect nothing matches is healed."""
    new: list[str] = []
    matched: set[int] = set()
    for key, observations in sorted(failures.items()):
        for obs in observations:
            hits = [i for i, r in enumerate(listed) if r.key == key and re.search(r.match, obs)]
            if hits:
                matched.update(hits)
            else:
                new.append(f"  {key}: {obs}")
    healed = [f"  {r.key}: {r.why} (/{r.match}/)" for i, r in enumerate(listed) if not r.maybe and i not in matched]
    if new:
        raise AssertionError(f"{where}: new reds\n" + "\n".join(new))
    if healed:
        raise AssertionError(f"{where}: healed, remove from KNOWN_REDS\n" + "\n".join(healed))
    strict = [r for r in listed if not r.maybe]
    if strict:
        raise KnownRed(f"{where}: known reds\n" + "\n".join(f"  {r.key}: {r.why}" for r in strict))


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
        sweep.shot = f"{case_id}-{width}"
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
            sweep.failures["drawn"] = [str(exc)[:400]]
        else:
            sweep.fences()
            if palette:
                sweep.palette()
            elif wid:
                sweep.wings()
        _verdict(case_id, width, sweep.failures)
    finally:
        ctx.close()


# PHILO-17 sweepreds r2: the late-read faces hold still under a HELD read.
# Each case opens its window with one first read held 2.5 s in the page (the
# fetch waits; nothing else does), then watches every control for the hold
# plus 2 s after the window settles: nothing moves. Without the first-read
# gate each of these moved (Rhythm 18 px under load, the meeting 162 px, the
# Needs-you drawer 260 px, the Agents wings 44 px).
_HOLD_JS = """(([subs, ms]) => { const f = window.fetch.bind(window);
  window.fetch = (input, init) => { const u = typeof input === 'string' ? input : (input && input.url) || '';
    if (subs.some((s) => u.includes(s))) return new Promise((r) => setTimeout(r, ms)).then(() => f(input, init));
    return f(input, init); }; })(%s)"""
HELD = 2500


@pytest.mark.timeout(240)
@pytest.mark.parametrize(("case_id", "held"), [
    ("surface-cadence", ["/api/cadence/loops", "/api/settings/heartbeat"]),
    ("meeting", ["/api/decisions"]),
    ("needs", ["/api/desk/needs-you"]),
    ("surface-companion", ["/api/delivery/"]),
])
def test_a_held_first_read_moves_nothing(desk: dict[str, Any], pw_browser: Any, case_id: str, held: list[str]) -> None:
    [(_, wid, scope)] = [c for c in CASES if c[0] == case_id]
    wid, scope = wid.format(**desk), (scope.format(**desk) if scope else None)
    base = desk["base"]
    clear_hub_windows_http(base, TOKEN)
    _hub_open(base, wid, scope)
    ctx, page, _, _ = _page(pw_browser, 1440, base)
    try:
        page.add_init_script(_HOLD_JS % json.dumps([held, HELD]))
        page.goto(f"{base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        page.wait_for_function(SETTLED_JS, arg=wid, timeout=T)
        moved = [r for r in page.evaluate(RECORD_JS, [f'[id="{wid}"]', HELD + 2000]) if r["worst"] > TOLERANCE]
        assert not moved, f"{case_id} with {held} held {HELD} ms: {moved}"
    finally:
        ctx.close()


# The Dock waiver is the ratified geometry only (Astra r1 on #1108): a planted
# More overlap fails at 1440, and a planted overlap with a control that is not
# a shelf AppIcon fails at 393. The waived pair passes at 393 only.
_PLANTED_DOCK = """<style>body{margin:0} .desk-dock{position:fixed;left:0;right:0;bottom:0;height:56px;overflow:hidden}
.desk-dock > *{position:absolute;top:0;height:56px;width:85px;padding:0;border:0}</style>
<div class="desk-dock"><button class="desk-dock-launch" style="left:0">Meetings</button>
<button class="desk-dock-launch" style="left:340px">Delivery</button>
<span class="desk-dock-chip" style="left:%dpx"><button class="desk-dock-main">Notes</button></span>
<button class="desk-dock-more" aria-label="More AppIcons" style="left:344px;width:49px">▸</button></div>"""


@pytest.mark.parametrize(("width", "chip_left", "expect"), [
    (393, 0, []),  # the shelf's next page under More: waived
    (1440, 0, ["Delivery x More AppIcons"]),  # never at 1440
    (393, 344, ["Notes x More AppIcons"]),  # not a shelf AppIcon
])
def test_dock_pager_waiver_is_the_ratified_geometry(pw_browser: Any, width: int, chip_left: int,
                                                    expect: list[str]) -> None:
    ctx = pw_browser.new_context(viewport={"width": width, "height": SIZES[width]})
    try:
        page = ctx.new_page()
        page.set_content(_PLANTED_DOCK % (chip_left or 100))
        found = page.evaluate(OVERLAP_JS, None)
        overlaps = [o.split(" (")[0] for o in found if "More AppIcons" in o]
        assert overlaps == expect, found
    finally:
        ctx.close()


ROUTE_KNOWN_REDS: dict[str, str] = {}

VISIBLE_TEXT_JS = r"""(sel) => { const e = document.querySelector(sel); if (!e) return null;
  const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 ? (e.innerText || '').trim() : null; }"""


@pytest.mark.timeout(120)
@pytest.mark.parametrize("route", [
    pytest.param(r, marks=[pytest.mark.xfail(strict=True, reason=ROUTE_KNOWN_REDS[r])] if r in ROUTE_KNOWN_REDS else [])
    for r in PAGE_ROUTES])
def test_every_html_route_loads_clean(desk: dict[str, Any], pw_browser: Any, route: str) -> None:
    """Every HTML route the hub serves (test_route_preflight.PAGE_ROUTES,
    fenced there against the live app) draws what it is for, with no page or
    console error: the standalone page its own visible content; every other
    address the desk, and the window it opens, shown and not empty."""
    base = desk["base"]
    kinds = [k for k, table in (("standalone", STANDALONE_ROUTES), ("desk", DESK_ROUTES),
                                 ("window", ROUTE_WINDOWS)) if route in table]
    assert len(kinds) == 1, f"{route}: the sweep has {kinds or 'no'} expectation for it; add one"
    clear_hub_windows_http(base, TOKEN)
    ctx, page, errors, _ = _page(pw_browser, 1440, base)
    problems: list[str] = []
    try:
        page.goto(f"{base}{route}?token={TOKEN}", wait_until="load")
        if kinds == ["standalone"]:
            sel = STANDALONE_ROUTES[route]
            page.wait_for_function(f"() => ({VISIBLE_TEXT_JS})({sel!r})", timeout=T)
        else:
            page.locator("[data-testid=desk-screen]").wait_for(timeout=T)
            _normal_chair(page)
            wid = ROUTE_WINDOWS.get(route)
            if wid and window_app_on_hub(wid):
                sel = f'[id="{wid}"]'
                page.locator(sel).wait_for(timeout=T)
                page.wait_for_function(SETTLED_JS, arg=wid, timeout=T)
            else:
                sel = "[data-testid=desk-screen]"
                page.wait_for_function(SETTLED_JS, arg=None, timeout=T)
            drawn = page.evaluate(DRAWN_JS, [sel, list(COVERS)])
            if drawn:
                problems.append(f"{sel}: {drawn}")
        if not page.evaluate(VISIBLE_TEXT_JS, sel):
            problems.append(f"{sel}: no visible text")
        # The same 1.5 s watch the window cases keep: a late error is counted.
        page.evaluate(RECORD_JS, [None, STILL_MS])
        problems += [e for e in errors if "ResizeObserver" not in e]
        assert not problems, f"{route}: {problems}"
    finally:
        ctx.close()
