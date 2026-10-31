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
    material  the bevel grammar (material_rig._assert_material)
    still     nothing interactive moves for 1.5 s after the window settles;
              and with reduced motion (every case emulates it) nothing in the
              window runs a CSS animation, a CSS transition or a script
              animation (Element.animate) longer than the --duration-micro
              token, from page load on (MOTION_INIT_JS records each start)
    words     no "Conductor" or "coder" on any face; on the agent faces
              (Agents, the agent's window) none of the old machine words
              (Betterment AG1)
    target    at 393, every library Button and every pressable row (a menu
              row, an option, a tab, any other button or link that is not
              inline in prose) owns its 44 x 44 px area: the nine points of
              the area answer elementFromPoint with the control itself (the
              HS-202-05 hit reader, type_floor_rig.HIT_PROBE_JS)
    egress    every request goes to the hub's own origin (data:, blob: allowed)
    labels    on a WORKING window (WORKING_WINDOWS: Today, Needs you, the
              Room, Meetings, Ask, Speak, Agents, Activity, Automations) no
              list row, toolbar or status bar wears an egress chip, an IP
              address or a scope word (LAN, CLOUD, LOCAL, REMOTE, MIXED):
              the owner ruling of 2026-10-25 (UX-CANON A.9 amended). The
              address shows where the choice or the act is made (Settings,
              the Send preview, Setup, Processes); those windows are not
              fenced here.
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

from holdspeak.services.desk_window_service import RETIRED_APPS, RETIRED_WINDOWS, window_app  # noqa: E402
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
from .type_floor_rig import _FAINT_JS, _MEASURE, GATED_CONTRAST, HIT_PROBE_JS, OWNERSHIP_JS  # noqa: E402
from .material_rig import LAMP_WORDS, MATERIAL_JS, dot_fact_fault  # noqa: E402
from .conductor_rig import _seed as _seed_agents  # noqa: E402
from .meetings_rig import _save_meeting  # noqa: E402
from .door_rig import (  # noqa: E402
    _GH_AUTH_CONNECTED,
    _GH_PR_SNAPSHOT,
    _GH_REPO_LIST,
    _GH_RUN_LIST,
    _make_gh_runner,
    _make_jira_runner,
    _write_gh_fixture,
)
from tests.unit.test_route_preflight import PAGE_ROUTES  # noqa: E402  (the e2e preflight is parked; the sweep fences every route)

pytestmark = [pytest.mark.e2e]

REPO = Path(__file__).resolve().parents[2]
MANIFEST_FLOOR = 22
TOKEN = "desk-sweep"
SIZES = {1440: 900, 393: 852}
T = 20_000
STILL_MS = 1500

#: Betterment AG1 (DECISIONS #3): the words fence. No face says "Conductor"
#: or "coder" (the app is Agents, the session an agent). On the agent faces
#: (the Agents window ``conductor``, the agent's window ``lane``) the old
#: machine words are banned too (agents/DESIGN.md §4, "The words").
BANNED_WORDS = re.compile(r"\bConductor\b|\b[Cc]oders?\b|\bCODERS?\b")
AGENT_FACE_WORDS = re.compile(
    r"Re-brief|RE-BRIEF|Install hooks|ASKS YOU|WANTS APPROVAL|Wants approval|\brider\b|\bNODE\b"
    r"|\bTARGET\b|INCOMPATIBLE|stopped_by_owner|\bRaw\b"
)
AGENT_FACES = {"conductor", "lane"}
# The owner ruling of 2026-10-25 (UX-CANON A.9 amended): the working windows
# whose rows, toolbars and status bars carry no host, IP or scope word.
WORKING_WINDOWS = {
    "pullout:intelligence:desk", "chair:needs", "surface-project-memory", "surface-meetings",
    "ask", "surface-dictation", "conductor", "surface-activity", "surface-workbenches",
}
LABELS_JS = r"""(sel) => {
  const root = sel ? document.querySelector(sel) : null;
  if (!root) return [];
  const shown = (el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const zones = root.querySelectorAll('.object-list-row, .surface-ledger-row, .needs-row, [role=row], '
    + '[role=toolbar], .kit-toolbar, .kit-statusbar, .surface-footer');
  const ip = /\b(?:\d{1,3}\.){3}\d{1,3}\b/;
  const word = /\b(?:LAN|CLOUD|LOCAL|REMOTE|MIXED)\b/;
  const out = new Set();
  for (const zone of zones) {
    if (!shown(zone)) continue;
    const kind = zone.matches('[role=toolbar], .kit-toolbar') ? 'toolbar'
      : zone.matches('.kit-statusbar, .surface-footer') ? 'status bar' : 'row';
    for (const chip of zone.querySelectorAll('.gadget-chip-egress')) {
      if (shown(chip)) out.add(`egress chip '${chip.textContent.trim()}' on a ${kind}`);
    }
    const text = zone.innerText || '';
    const a = text.match(ip); if (a) out.add(`address '${a[0]}' on a ${kind}`);
    const w = text.match(word); if (w) out.add(`scope word '${w[0]}' on a ${kind}`);
  }
  return [...out];
}"""
WORDS_JS = "(sel) => { const el = sel ? document.querySelector(sel) : document.body; return el ? el.innerText : ''; }"
TOLERANCE = 2
PALETTE_QUERY = "ledger"  # a Project, meetings, a decision, a note of the seed


def _overlap(o: list[Any]) -> str:
    """One overlap observation: the two words, then WHERE each box is (the
    data-testids of its nearest marked ancestors), so a known red can name
    the element by its identity (PHILO-17, Astra r1 on #1111)."""
    where = o[3] if len(o) > 3 else ["", ""]
    text = f"overlap '{o[0]}' x '{o[1]}' @[{where[0]}] x [{where[1]}]"
    return text + (f" {o[2]}" if os.environ.get("SWEEP_DEBUG") else "")


class KnownRed(AssertionError):
    """A red listed in KNOWN_REDS (the only failure the xfail accepts)."""


# ── the manifest, read from applications.ts itself ─────────────────────────

_MANIFEST_JS = """
import(process.argv[1]).then((m) => {
  process.stdout.write(JSON.stringify(m.DESK_APPLICATIONS.map((a) => ({
    action: a.action, windowId: a.windowId, label: a.label, href: a.href,
    subjectRef: a.subjectRef ?? null, parked: a.parked ?? null,
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
    live_windows = {app["windowId"] for app in _manifest() if not app["parked"]}
    for app in _manifest():
        wid = app["windowId"]
        if not window_app_on_hub(wid):  # any refusal but window_not_on_hub fails collection
            refused[wid] = NOT_ON_HUB_CODE
            continue
        if app["parked"] and wid not in live_windows:
            known_app, _ = window_app(wid)
            assert known_app in RETIRED_APPS or wid in RETIRED_WINDOWS, (
                f"{wid} is parked in the manifest but the hub still opens its old host"
            )
            refused[wid] = "window_retired"
            continue
        for scope in [None, app["subjectRef"], *app["scopes"]]:
            if (wid, scope) in seen:
                continue
            seen.add((wid, scope))
            cases.append((wid if scope is None else f"{wid}@{scope}", wid, scope))
    # The seeded subjects: their ids are known after the seed ({...} below).
    cases += [
        ("room", "surface-project-memory", "project:{room}"),
        ("meeting", "surface-meetings", "meeting:{meeting}"),
        ("note", "pullout:note:{note}", None),
        ("person", "pullout:people:{person}", None),
        # Programs (2026-10-28): a Program's window (the board of direction
        # C), seeded through the real routes on a real git folder.
        ("program", "pullout:program:{program}", None),
        # PG-LANG LANG2: the same Program in its Text view, one line changed
        # and previewed: the change well with its diff row over the text.
        ("program-text", "pullout:program:{program}", None),
        # PG-LANG LANG4: the shaping bar under the toolbar, a sentence sent;
        # the rig hub has no planning engine, so the bar's refusal line with
        # Open Engines and Open text (a desk with an engine: the well).
        ("program-shape", "pullout:program:{program}", None),
        # PG-LANG LANG7: a Program in Drafting with its goal and no steps;
        # Plan it pressed. The rig hub has no planning engine, so the plan
        # line's refusal with Open Engines and Open text (a desk with an
        # engine: the draft's rows in the well, with their size lamps).
        ("program-plan", "pullout:program:{program_draft}", None),
        # Betterment A3: an automation's window (an object window, so a seeded
        # subject: the sentence, its newest result, an older failed one).
        ("automation", "workbench:{automation}", None),
        # Programs PG14: an automation that runs a Program (Do: Run a
        # program; its one result is the seeded Program, Running).
        ("automation-program", "workbench:{automation_program}", None),
        # Not applications, opened the same way: the Chair's Needs-you window
        # (its seed rows: accepted requests, a failed summary) ...
        ("needs", "chair:needs", None),
        # ... the Chair's other window (the 12 px floor walk of
        # PHILO-13-18 read them; tests/e2e/_parked/test_philo13_18_type_floor_glass.py) ...
        # Betterment D4: Today's Since-yesterday fold, unfolded (the Brief
        # wing it replaced is parked). Betterment D5: The week retired into
        # Today (its case is gone with it).
        ("brief", "pullout:intelligence:desk", None),
        ("capture", "chair:capture", None),
        # ... and the ⌘K palette, open on a query that hits several sections.
        ("palette", "desk-tool-shelf", PALETTE_QUERY),
        # PHILO-17 (concept C): the Today window, the day as a timeline. The
        # hub does not hold it (NOT_ON_HUB), so the dock opens it.
        ("today", "pullout:intelligence:desk", None),
        # Window grammar (2026-10-24): the Ask window (ask:desk). The hub
        # does not hold it (NOT_ON_HUB) and the Dock carries no Ask launcher,
        # so the desk's own shortcut opens it (Ctrl+I, as test_ask_glass).
        ("ask", "ask", None),
        # The parked Missed shade is replaced by Needs you above. The New
        # Project Door has BOTH sources picked (GitHub
        # karolswdev/HoldSpeak and Jira KAN, their counts in): the hub's gh
        # and acli are the door_rig fixture runners, signed in at the seed.
        ("door-picked", "surface-project-setup", None),
    ]
    return cases, refused


CASES, NOT_ON_HUB_APPS = _cases()


# ── the routes: what each served address must draw ───────────────────────
# The pages that draw no desk screen, and what each must show (routes.tsx
# PRODUCT_ROUTES: Presence draws its card; Welcome hands off to the Get ready
# cards, which stand in place of the desk screen):
STANDALONE_ROUTES = {"/presence": ".presence-card", "/welcome": ".setup-face h1"}
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


#: The Room's one ask-bar red: an item row's box (its where-path holds
#: `item-row`) under an ask-bar box (its where-path holds `room-ask`).
ROOM_ITEM_UNDER_ASK = (r"^overlap '[^']+' x '[^']+' @\[(?:[^\]<]*<)*item-row(?:<[^\]]*)?\]"
                       r" x \[(?:[^\]<]*<)*room-ask[\w-]*(?:<[^\]]*)?\](?: \[\[.*)?$")

KNOWN_REDS: dict[tuple[str, int], list[Red]] = {
    # 2026-10-16: the palette's named surface container healed its in-well
    # mic target at 393. That case now holds every target fence without an excuse.
    ("desk", 1440): [
        Red("overlap", r"^People, DRAWER, 1:1 [\d:]+ x Conductor, DRAWER, ", "the People drawer icon overlaps the "
            "Conductor icon by 5 px when its `1:1 HH:MM` caption is wide (depends on the clock)", maybe=True),
        Red("readable", r"^overlap 'People, DRAWER, 1:1 [\d:]+' x 'Conductor, DRAWER, ",
            "the same People x Conductor icon overlap", maybe=True),
        Red("readable", r"^overlap '1' x 'People, DRAWER, 1:1 [\d:]+'" r" @\[[^\]]*\] x \[[^\]]*\](?: \[\[.*)?$",
            "the People icon's count badge 1 overlaps its caption", maybe=True),
    ],
    # ENGINES-STILL (2026-10-28): the surface-engines "maybe" still red is
    # gone. Its real cause was the late mono webfont swap (the catalog moved
    # 4 px); the metric twin fixes it (tests/unit/test_css_mono_line_height.py).
    ("room", 1440): [
        # PHILO-17 (Astra r1 on #1111): an ITEM ROW (testid item-row) under
        # the ask bar (testid room-ask-*); which rows sit there depends on the
        # head's height. Named by identity: two ask-bar boxes, or any box that
        # is not an item row, never match (test_room_red_is_item_rows_only).
        Red("readable", ROOM_ITEM_UNDER_ASK,
            "Room: the risk rows read as overlapping the ask bar (the reader ignores z-order: the rows may be "
            "scrolled under an opaque bar); where they sit depends on the late read", maybe=True),
        # A late read (the sources row) lands after the window settles and moves the body
        # down (295 px seen); what overlaps the ask bar then depends on when it lands.
        # The footer receipt holds still now (it is said with the body it reads for).
        Red("still", r"^(room-add-source|steward-verb|source-scope|Pause|since-read-empty) "
            r"moved \d+ px$", "Room: a late read moves the body after the window settles (not reproduced "
            "on 2026-10-11 under held reads; kept until a run shows it)", maybe=True),
        Red("readable", r"^overlap '(GH|org/repo|\d+ OPEN PRS|·|CI GREEN|CI RED)' x 'Ask this project'" r" @\[[^\]]*\] x \[[^\]]*\](?: \[\[.*)?$",
            "Room: the sources row reads as overlapping the ask bar after the late read lands", maybe=True),
        Red("overlap", r"^Pause x Choose ", "Room: the footer's Pause and Choose overlap on some loads", maybe=True),
        Red("readable", r"^overlap '(Pause|Choose)' x '(Pause|Choose)'" r" @\[[^\]]*\] x \[[^\]]*\](?: \[\[.*)?$",
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
        # The Door's sources: gh and acli are fixture runners, signed in.
        gh_fixture = tmp / "gh_fixture.json"
        _write_gh_fixture(gh_fixture, auth=_GH_AUTH_CONNECTED,
                          repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
                          pr_list={"stdout": _GH_PR_SNAPSHOT, "returncode": 0},
                          run_list={"stdout": _GH_RUN_LIST, "returncode": 0})
        server, base = _boot(tmp, mp, token=TOKEN, gh_runner=_make_gh_runner(gh_fixture),
                             acli_runner=_make_jira_runner())
        try:
            home = tmp / "home"
            week = open13._seed(home, base)  # canvas week, 1:1 Priya, calendar, brief
            _seed_agents(home)  # the Conductor flight
            _save_meeting("m-sweep-failed", "Vendor sync", 3, "error")  # a Needs-you member
            # PHILO-17 (Today): a decision to make, so the To decide plate draws.
            get_database().proposals.create_proposal(
                meeting_id="m-sweep-failed", project_id=None, kind="decision",
                text="Freeze the ledger on Nov 12", source_plugin="summary")
            ctx = pw_browser.new_context()
            page = ctx.new_page()
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            room = hs158._seed_populated_project(page)
            seed_health_room(get_database(), project_id=room)
            folder = home / "Documents" / "HoldSpeak" / "Team updates"
            folder.mkdir(parents=True, exist_ok=True)
            _api(page, "POST", "/api/channels/destinations",
                 {"name": "Team updates", "channel": "file", "folder": str(folder)}, token=TOKEN)
            # The Door's two sources, signed in (the Connections list is a
            # cached read: a check stores the state).
            _api(page, "POST", "/api/connections/github/recheck", token=TOKEN)
            _api(page, "POST", "/api/providers/jira/connections",
                 {"site": "alpha.atlassian.net", "email": "user@example.com"}, token=TOKEN)
            jira_ref = urllib.parse.quote("alpha.atlassian.net|user@example.com", safe="")
            _api(page, "POST", f"/api/providers/jira/connections/{jira_ref}/recheck", token=TOKEN)
            thought = _api(page, "POST", "/api/thoughts", {
                "request_id": "desk-sweep-note",
                "raw_text": "Write the ledger rollback runbook before Friday.",
                "initial_note": {"title": "Ledger rollback", "body_markdown": "Write the ledger rollback runbook before Friday."},
            }, token=TOKEN)
            note_id = thought["thought"]["working_note"]["id"]
            program_id = _seed_program(page, tmp)
            program_draft = _seed_draft_program(page, tmp)
            briefing = _seed_briefing(page, tmp)
            ctx.close()
            _seed_finished_receipts()
            automation = _seed_automation(note_id)
            automation_program = _seed_program_automation(program_id)
            yield {"base": base, "room": room, "meeting": "m-standup", "person": week["priya"], "note": note_id,
                   "automation": automation, "program": program_id, "automation_program": automation_program,
                   "program_draft": program_draft, "briefing": briefing}
        finally:
            server.stop()


def _seed_draft_program(page: Any, tmp: Path) -> str:
    """PG-LANG LANG7: a Program in Drafting, its goal two paragraphs (journey
    J1), no steps yet (station 1, Dropped)."""
    repo = tmp / "program-draft-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Sweep", "-c", "user.email=sweep@example.com",
                    "commit", "-q", "--allow-empty", "-m", "start"], check=True)
    from tests.integration.program_plan_seed import J1_GOAL

    made = _api(page, "POST", "/api/programs", {
        "title": "Meeting recap in the Note", "goal": J1_GOAL, "repository": str(repo),
        "template": "build-and-review", "check_command": "true", "control": "normal",
    }, token=TOKEN)
    return str(made.get("id") or (made.get("program") or {}).get("id"))


def _seed_program(page: Any, tmp: Path) -> str:
    """Programs (2026-10-28): one Program on a real git folder, three steps
    (the third after the first two), three requirements (PG-REQ), started. The rig hub's runner is off
    (``HOLDSPEAK_PROGRAMS=off``), so the steps stay Ready and Planned and no
    agent is launched."""
    repo = tmp / "program-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Sweep", "-c", "user.email=sweep@example.com",
                    "commit", "-q", "--allow-empty", "-m", "start"], check=True)
    made = _api(page, "POST", "/api/programs", {
        "title": "The hub stops stalling", "goal": "The hub answers every read within a second.",
        "repository": str(repo), "template": "fast-cycle", "check_command": "true",
    }, token=TOKEN)
    program_id = str(made.get("id") or (made.get("program") or {}).get("id"))
    _api(page, "POST", f"/api/programs/{program_id}/plan", {"replace": True, "steps": [
        {"title": "Indexes", "brief": "Index the three pipeline_events scans.", "owns": ["holdspeak/db/schema.py"]},
        {"title": "Retention", "brief": "Prune read receipts after 14 days."},
        {"title": "The fan-out", "brief": "One read for the desk.", "after": [1, 2]},
    ]}, token=TOKEN)
    # PG-REQ: its requirements (the board of direction A, the Met column):
    # one on every step, his word on step 1, a check on the whole program.
    steps = _api(page, "GET", f"/api/programs/{program_id}", token=TOKEN)["steps"]
    for body in ({"text": "The change does only what its brief says", "each_step": True},
                 {"text": "I tried it on my desk", "kind": "word", "step_id": steps[0]["id"]},
                 {"text": "`true` is green on main", "kind": "check"}):
        _api(page, "POST", f"/api/programs/{program_id}/requirements", body, token=TOKEN)
    _api(page, "POST", f"/api/programs/{program_id}/start", {}, token=TOKEN)
    return program_id


def _seed_briefing(page: Any, tmp: Path) -> str:
    """PG-DIRECTION DIR2: a second Program whose step 1 waits on a core
    question (the runner is off, so the question is written on the step as
    the engine writes it), and its briefing page. Returns the page token."""
    from holdspeak.services.program_service import default_program_service

    repo = tmp / "briefing-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Sweep", "-c", "user.email=sweep@example.com",
                    "commit", "-q", "--allow-empty", "-m", "start"], check=True)
    made = _api(page, "POST", "/api/programs", {
        "title": "Overnight on the home box", "goal": "The hub stops stalling overnight.",
        "repository": str(repo), "template": "fast-cycle", "check_command": "true", "control": "yolo",
    }, token=TOKEN)
    program_id = str(made.get("id") or (made.get("program") or {}).get("id"))
    _api(page, "POST", f"/api/programs/{program_id}/plan", {"replace": True, "steps": [
        {"title": "Store the stall reason", "brief": "Store the stall reason in its own column.",
         "owns": ["holdspeak/services/stall.py"]},
    ]}, token=TOKEN)
    _api(page, "POST", f"/api/programs/{program_id}/start", {}, token=TOKEN)
    service = default_program_service()
    step = service.store.list_steps(program_id)[0]
    step.setdefault("facts", {})["core"] = {"kind": "outside_owned",
                                            "reason": "it touches files no step owns (holdspeak/db/schema.py)"}
    service.store.save_step(step)
    item = next(row for row in service.needs_you_items() if row["program_id"] == program_id and row["kind"] == "core")
    page_made = _api(page, "POST", "/api/reach/packages", {"refs": [f"program:{program_id}:{item['id']}"]}, token=TOKEN)
    return str(page_made["token"])


def _seed_automation(note_id: str) -> str:
    """Betterment A3: an automation with its sentence and two results, the
    rows a run writes (automation_runs / workbench_projection): the newest
    done (NEW, a run record naming its model), an older one failed with the
    engine's reason. No engine runs in the sweep."""
    import json as _json

    from holdspeak.db import get_database

    db = get_database()
    wb = db.workbenches.upsert(
        workbench_id="wb-sweep-friday", name="Friday team update",
        instruction="Draft my team update: what shipped, what slipped, and what I need from each person.",
        sources=[f"note:{note_id}"], output_target="inbox")
    answer = ("## Team update, week 42\n\n**Shipped:** the ledger rollback runbook (Mira).\n\n"
              "**Slipped:** the shard benchmark moves to Tuesday.\n\n"
              "- Mira: review the cutover plan by Thursday.\n- Theo: book the second hiring loop.")
    occurrence = {"occurrence": 1}
    db.workbench_items.upsert(
        item_id="wbocc_sweep_old", workbench_id=wb.id, title="Friday team update, Fri 9 Oct 2026",
        body=wb.instruction, status="failed", context=occurrence, grounding={"refs": [f"note:{note_id}"]},
        result="Error: the LAN engine did not answer in 60 s",
        claimed_at="2026-10-09T15:00:00+00:00", completed_at="2026-10-09T15:01:00+00:00")
    db.workbench_items.upsert(
        item_id="wbocc_sweep_new", workbench_id=wb.id, title="Friday team update, Fri 16 Oct 2026",
        body=wb.instruction, status="done", context=occurrence, grounding={"refs": [f"note:{note_id}"]},
        result=answer, result_egress={"boundary": "private_network", "model": "qwen3.8-27b"},
        result_artifact_id="artifact_sweep_friday",
        claimed_at="2026-10-16T15:00:00+00:00", completed_at="2026-10-16T15:00:41+00:00")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO workbench_runs (id, workbench_id, started_at, completed_at, items_attempted, "
            "items_completed, egress_boundary, model, status) VALUES (?,?,?,?,1,1,?,?,'completed')",
            ("wbrun_sweep_friday", wb.id, "2026-10-16T15:00:00+00:00", "2026-10-16T15:00:41+00:00",
             "private_network", "qwen3.8-27b"))
        conn.execute(
            "INSERT INTO artifacts (id, meeting_id, origin, artifact_type, title, body_markdown, structured_json, "
            "confidence, status, plugin_id, plugin_version, source_run_id, source_item_id) "
            "VALUES (?, NULL, 'run', 'workbench_output', ?, ?, ?, 0.0, 'new', 'workbench_run', '1', ?, ?)",
            ("artifact_sweep_friday", "Friday team update, Fri 16 Oct 2026", answer, _json.dumps({}),
             "wbrun_sweep_friday", "wbocc_sweep_new"))
        conn.commit()
    return wb.id


def _seed_program_automation(program_id: str) -> str:
    """Programs PG14: a run_program automation (Fast cycle, YOLO, Codex) and
    the one result its run writes: the seeded Program it started."""
    from holdspeak.db import get_database

    db = get_database()
    wb = db.workbenches.upsert(
        workbench_id="wb-sweep-nightly", name="Nightly fixes", instruction="Fix each bug with a test.",
        sources=[], output_target="today", do_kind="run_program", program_template="fast-cycle",
        program_control="yolo", program_runs_on=[{"profile": "codex-default", "engine": None}])
    db.workbench_items.upsert(
        item_id="wbprog_sweep_nightly", workbench_id=wb.id, title="The hub stops stalling",
        body=wb.instruction, status="done",
        context={"occurrence": 1, "run_id": "wbrun_sweep_nightly",
                 "program": {"program_id": program_id, "title": "The hub stops stalling", "steps": 3}},
        result="Started the program The hub stops stalling · 3 steps",
        claimed_at="2026-10-29T23:30:00+00:00", completed_at="2026-10-29T23:30:02+00:00")
    return wb.id


def _seed_finished_receipts() -> None:
    """The Missed shade's Finished rows: a sweep a LAN agent ran (origin
    remote: Activity says "Another device", no chip) and a local Steward run, seeded as
    tests/integration/test_face_wire_fences.py::test_shade_finished_remote_receipt
    seeds them."""
    import time
    import uuid

    from holdspeak.db import get_database

    with get_database()._connection() as conn:
        for n, (service, method, origin, caller, summary) in enumerate((
            ("HeartbeatService", "run_sweep", "remote", "studio.local", '{"watches":4,"rooms":2,"held":false}'),
            ("StewardService", "project_run_steward", "local", "", "{}"),
        )):
            conn.execute(
                """INSERT INTO pipeline_events
                   (event_id, timestamp, service, method,
                    principal_kind, principal_identity, args_summary,
                    result_summary, error, error_code, duration_ms,
                    correlation_id, is_async, origin, caller, caller_identity)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (f"ev-sweep-{n}", time.time() - n, service, method, "agent", "sweep-runner", "{}",
                 summary, None, None, 42.0, str(uuid.uuid4()), 0, origin, caller,
                 "sweep-runner" if origin == "remote" else ""),
            )
        conn.commit()


# ── the page measures ──────────────────────────────────────────────────────

SETTLED_JS = r"""(id) => {
  const w = id ? document.getElementById(id) : document.querySelector('[data-testid=desk-screen]');
  if (!w) return false;
  const r = w.getBoundingClientRect();
  if (r.width < 1 || r.height < 1) return false;
  if (w.querySelector('[aria-busy="true"]:not(button)')) return false;
  if (/Loading…/.test(w.innerText || '')) return false;
  // Long pages contain lazy pictures below their scroll port. Only pictures
  // on this window's glass must finish before its visible face is measured.
  if ([...w.querySelectorAll('img')].some((i) => {
    const b = i.getBoundingClientRect();
    const drawn = b.width > 0 && b.height > 0
      && b.right > Math.max(0, r.left) && b.left < Math.min(innerWidth, r.right)
      && b.bottom > Math.max(0, r.top) && b.top < Math.min(innerHeight, r.bottom);
    return drawn && !(i.complete && i.naturalWidth > 0);
  })) return false;
  // The floor/contrast fences read the persistent chrome too. Its phone
  // picture controls are not ready until their visible sprites have loaded.
  if ([...document.querySelectorAll('.desk-menubar img, .desk-dock img')].some((i) => {
    const b = i.getBoundingClientRect(), style = getComputedStyle(i);
    const drawn = style.display !== 'none' && style.visibility !== 'hidden'
      && b.width > 0 && b.height > 0 && b.right > 0 && b.left < innerWidth
      && b.bottom > 0 && b.top < innerHeight;
    return drawn && !(i.complete && i.naturalWidth > 0);
  })) return false;
  return !document.getAnimations().some((a) => a.playState === 'running'
    && (a.effect && a.effect.getTiming().iterations !== Infinity));
}"""

# The Brief has one face-local read after its first paint: a stale seeded
# brief makes itself again.  That generation keeps the body visible, so the
# generic settled predicate sees no busy marker while the rows are replaced.
# Wait for the actual completion state before taking the still measurement.
BRIEF_SETTLED_JS = r"""(id) => {
  const w = document.getElementById(id);
  if (!w) return false;
  // Betterment D4: the Since-yesterday fold is open and drawn.
  const toggle = w.querySelector('[data-testid=today-since-toggle]');
  return Boolean(toggle && toggle.getAttribute('aria-expanded') === 'true' && w.querySelector('[data-testid=today-since-rows]'));
}"""

UNSETTLED_JS = r"""(id) => {
  const w = id ? document.getElementById(id) : document.querySelector('[data-testid=desk-screen]');
  if (!w) return {window: null, open: [...document.querySelectorAll('.desk-window-shell')].map((e) => e.id)};
  const r = w.getBoundingClientRect();
  return {box: [r.width, r.height].map(Math.round),
    busy: [...w.querySelectorAll('[aria-busy="true"]:not(button)')].map((e) => e.className).slice(0, 5),
    loading: /Loading…/.test(w.innerText || ''),
    images: [...w.querySelectorAll('img')].filter((i) => {
      const b = i.getBoundingClientRect();
      return b.width > 0 && b.height > 0
        && b.right > Math.max(0, r.left) && b.left < Math.min(innerWidth, r.right)
        && b.bottom > Math.max(0, r.top) && b.top < Math.min(innerHeight, r.bottom)
        && !(i.complete && i.naturalWidth > 0);
    }).map((i) => i.src).slice(0, 5),
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
    // the one ratified waiver (tests/e2e/_parked/test_philo13_13_dock_glass.py _read; the species
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


# still, reduced motion: the longest motion lawful under reduced motion is the
# micro token (tokens.css `--duration-micro`, "immediate input feedback"),
# read from the token file so the fence never drifts from it.
_MICRO = re.search(r"--duration-micro:\s*(\d+)ms", (REPO / "web/src/styles/tokens.css").read_text(encoding="utf-8"))
assert _MICRO, "tokens.css has no --duration-micro in ms: the motion fence's threshold is lost"
MOTION_MAX_MS = int(_MICRO.group(1))

# Recorded from the first script on: every CSS animation and transition that
# starts, and every Element.animate call, longer than the threshold (or
# endless), with the element it ran on. The fence reads the ones in its scope.
MOTION_INIT_JS = r"""((thr) => {
  const runs = []; window.__hsMotion = runs;
  const ms = (v) => Math.max(0, ...String(v || '0s').split(',').map((x) => x.trim())
    .map((x) => x.endsWith('ms') ? parseFloat(x) : parseFloat(x) * 1000).filter((x) => !Number.isNaN(x)));
  const keep = (el, what, dur, endless) => { if (dur > thr || (endless && dur > 0)) runs.push({el, what, dur: Math.round(dur)}); };
  const orig = Element.prototype.animate;
  Element.prototype.animate = function (frames, options) {
    const a = orig.call(this, frames, options);
    try { const t = a.effect.getComputedTiming();
      keep(this, 'Element.animate', Number(t.duration) || 0, t.iterations === Infinity); } catch (e) { /* unreadable */ }
    return a;
  };
  document.addEventListener('animationstart', (e) => {
    const cs = getComputedStyle(e.target, e.pseudoElement || null);
    keep(e.target, 'animation ' + e.animationName + (e.pseudoElement || ''), ms(cs.animationDuration),
      cs.animationIterationCount === 'infinite');
  }, true);
  document.addEventListener('transitionrun', (e) => {
    const cs = getComputedStyle(e.target, e.pseudoElement || null);
    keep(e.target, 'transition ' + e.propertyName + (e.pseudoElement || ''), ms(cs.transitionDuration), false);
  }, true);
})(%d)"""

MOTION_JS = r"""(sel) => {
  const scope = sel ? document.querySelector(sel) : null;
  const name = (e) => (e.getAttribute && (e.getAttribute('data-testid') || e.id)) || (typeof e.className === 'string'
    && e.className.trim() ? '.' + e.className.trim().split(/\s+/)[0] : (e.tagName || '?').toLowerCase());
  return [...new Set((window.__hsMotion || []).filter((r) => !sel || (scope && scope.contains(r.el)))
    .map((r) => `${name(r.el)} runs ${r.what} ${r.dur} ms under reduced motion`))];
}"""

# target: the HS-202-05 hit reader (type_floor_rig.HIT_PROBE_JS) over every
# library Button and every pressable row in the scope, at the narrow desk
# only (the 44 px rule is `@media (max-width: 420px)`, global.css). A link
# inline in prose is not a target (WCAG 2.5.8, the inline exception). A
# control a layer in front covers at its centre is not reachable here and is
# not read (the probe's `occluded`).
TARGET_JS = r"""(sel) => {""" + OWNERSHIP_JS + HIT_PROBE_JS + r"""
  if (innerWidth > 420) return [];
  const scope = sel ? document.querySelector(sel) : document.body;
  if (!scope) return ['no scope ' + sel];
  const hit = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--desk-button-hit-size')) || 44;
  const PRESS = '.btn, button, [role=button], [role=menuitem], [role=menuitemcheckbox], [role=menuitemradio], '
    + '[role=option], [role=tab], [role=switch], [role=checkbox], a[href]';
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 1 && r.height > 1 && cs.visibility !== 'hidden' && cs.display !== 'none' && Number(cs.opacity) > 0.05
      && (!e.checkVisibility || e.checkVisibility({contentVisibilityAuto: true})); };
  const inline = (e) => e.matches('a[href]') && getComputedStyle(e).display === 'inline'
    && [...(e.parentElement ? e.parentElement.childNodes : [])].some((n) => n.nodeType === 3 && n.textContent.trim());
  const where = (e) => { const bits = [];
    for (let n = e; n && n !== document.body && bits.length < 3; n = n.parentElement) {
      const t = n.getAttribute('data-testid'); if (t) bits.push(t); }
    return bits.join('<'); };
  const out = [];
  for (const el of scope.querySelectorAll(PRESS)) {
    if (el.parentElement && el.parentElement.closest(PRESS)) continue;  // the outer control owns the press
    if (!visible(el) || inline(el) || el.disabled) continue;
    const r0 = el.getBoundingClientRect();
    if (r0.bottom <= 0 || r0.top >= innerHeight || r0.right <= 0 || r0.left >= innerWidth) continue;
    // The overlap fence's one ratified waiver: the Dock shelf's next page
    // scrolls under its sticky More AppIcons gadget at the phone width.
    if (el.matches('.desk-dock > .desk-dock-launch')) {
      const under = document.elementFromPoint(r0.left + r0.width / 2, r0.top + r0.height / 2);
      if (under && under.closest('.desk-dock > .desk-dock-more')) continue;
    }
    const p = hs202Probe(el, hit, where(el));
    if (p.occluded) continue;
    const label = ((el.getAttribute('aria-label') || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 30))
      || el.tagName.toLowerCase();
    if (p.bad.length) out.push(`'${label}' @[${p.path}] loses ${p.bad.length}/9 points of its ${hit} px area (${p.bad[0]})`);
  }
  return out;
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
    """material_rig._assert_material, every observation
    (that helper stops at the first): the same reads, the same rules."""
    m = page.evaluate(MATERIAL_JS, root)
    if m is None:
        return [f"{face}: no scope {root}"]
    raised, sunken = m["raised"], m["sunken"]
    out: list[str] = []
    if not m["tokenPresence"]:
        out.append("a shared material token is absent")
    for b in m["buttons"]:
        if b["shadow"] != "none" and not b["shadow"].startswith((raised, m["wbRaised"])):
            out.append(f"Button '{b['name']}' uses unregistered material (box-shadow {b['shadow'][:40]})")
    for t in m["tokens"]:
        if t["shadow"] != "none" and not t["shadow"].startswith(m["softSunken"] if t["active"] else m["soft"]):
            out.append(f"token '{t['name']}' uses unregistered selection material")
    for c in m["chips"]:
        # PHILO-17 ALIVE (owner 2026-10-11): a state is a soft tinted pill
        # with a round 8 px lamp dot.
        ok = (c["border"] == "0px" and c["lampW"] == "8px"
              and c.get("lampRadius") == "50%" and (c["name"] or "").strip()
              and (not c["word"] or c["name"] == c["word"])
              and (c["word"] or c["state"] not in LAMP_WORDS or c["name"] == LAMP_WORDS[c["state"]]))
        if not ok:
            out.append(f"state chip '{c['name']}' breaks the lamp grammar")
    for f in m["facts"]:
        ok = (f["border"] == "rgba(0, 0, 0, 0)" and f["shadow"] == "none"
              and (f["tone"] not in ("warn", "danger", "ok") or f["lampW"] == "8px"))
        if not ok:
            out.append(f"fact '{f['text']}' is not a pill")
    for f in m["dotFacts"]:
        fault = dot_fact_fault(f)
        if fault:
            out.append(f"state fact '{f['text']}' {fault}")
    for shadow in m["bodies"]:
        if shadow != "none" and not shadow.startswith(sunken):
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
            # A drawn frame is not enough: every visible head verb must
            # remain inside it, with its label intact (UX Canon A.6).
            fail("head", page.evaluate("""id => {
              const frame = document.getElementById(id);
              const head = frame?.querySelector('.desk-pullout-head');
              if (!frame || !head) return [];
              const f = frame.getBoundingClientRect();
              return [...head.querySelectorAll('button')].flatMap(button => {
                const r = button.getBoundingClientRect();
                if (!r.width || !r.height || getComputedStyle(button).visibility === 'hidden') return [];
                const name = button.getAttribute('aria-label') || button.textContent.trim();
                const out = r.left < f.left - 1 || r.right > f.right + 1 ||
                  r.top < f.top - 1 || r.bottom > f.bottom + 1;
                const clipped = button.scrollWidth > button.clientWidth + 1;
                return out || clipped ? [`${name}: ${out ? 'outside frame' : 'clipped label'}`] : [];
              });
            }""", self.wid))
        faults = _rendered_text_faults(page, scope, on_glass=True,
                                       horizontal_scroll=(".needs-chip-row",))
        if not faults["scopes"]:
            fail("readable", f"no visible {scope}: nothing was read")
        fail("readable", ([f"clipped '{c['text']}' in {c['in']}" for c in faults["clipped"]]
                          + [_overlap(o) for o in faults["overlaps"]]))
        small, contrast = self.measure()
        fail("floor", sorted(small - self.baseline[0]))
        fail("contrast", sorted(contrast - self.baseline[1]))
        fail("clipped", page.evaluate(CLIPPED_JS, scope))
        fail("overlap", page.evaluate(OVERLAP_JS, sel))
        fail("library", page.evaluate(LIBRARY_JS, sel))
        fail("material", _material_faults(page, self.wid or "desk", sel))
        moved = [r for r in page.evaluate(RECORD_JS, [sel, STILL_MS]) if r["worst"] > TOLERANCE]
        fail("still", [f"{r['name']} moved {round(r['worst'])} px" for r in moved])
        fail("still", page.evaluate(MOTION_JS, sel))
        fail("target", page.evaluate(TARGET_JS, sel))
        text = page.evaluate(WORDS_JS, sel)
        banned = AGENT_FACE_WORDS if self.wid in AGENT_FACES else None
        fail("words", sorted({m.group(0) for m in BANNED_WORDS.finditer(text)}
                             | ({m.group(0) for m in banned.finditer(text)} if banned else set())))
        # After the 1.5 s watch: an error a late read raises is counted too.
        fail("clean", [e for e in self.errors if "ResizeObserver" not in e])
        if not page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"):
            fail("clean", "the page scrolls sideways")
        if self.wid in WORKING_WINDOWS:
            fail("labels", page.evaluate(LABELS_JS, sel))
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
    page.add_init_script(MOTION_INIT_JS % MOTION_MAX_MS)
    page.set_default_timeout(30_000)
    errors: list[str] = []
    requests: list[str] = []
    page.on("pageerror", lambda e: errors.append(f"pageerror: {str(e)[:300]}"))
    def console_error(message: Any) -> None:
        if message.type != "error":
            return
        # Keep the old observation prefix for the exact known-red matching,
        # while retaining the failed resource URL for an actionable diagnosis.
        url = (message.location or {}).get("url", "")
        errors.append(f"console: {message.text[:300]}" + (f" [{url}]" if url else ""))

    page.on("console", console_error)
    page.on("request", lambda r: requests.append(r.url))
    return ctx, page, errors, requests

_BASELINES: dict[int, tuple[set[str], set[str]]] = {}


def _baseline(browser: Any, base: str, width: int) -> tuple[set[str], set[str]]:
    """The bare desk's floor and contrast reads at this width, once per
    worker: a window case reports only what the window adds (the desk's own
    are the `desk` case's)."""
    if width not in _BASELINES:
        clear_hub_windows_http(base, TOKEN)
        ctx, page, errors, _ = _page(browser, width, base)
        try:
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            try:
                page.wait_for_function(SETTLED_JS, arg=None, timeout=T)
            except Exception as exc:
                shot = evidence_dir("desk-sweep") / f"baseline-unsettled-{width}.png"
                page.screenshot(path=str(shot))
                raise AssertionError(
                    f"bare desk {width} did not settle: {page.evaluate(UNSETTLED_JS, None)}; "
                    f"errors={errors}; shot={shot}"
                ) from exc
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
    today = case_id in {"today", "brief"}
    ask = case_id == "ask"
    if wid and not palette and not today and not ask:
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
        if today:
            page.wait_for_function(SETTLED_JS, arg=None, timeout=T)
            launch = page.locator(".desk-dock-launch[aria-label^='Today']").first
            launch.click()
            page.locator(f'[id="{wid}"] [data-testid=today-day]').wait_for(timeout=T)
            if case_id == "brief":
                # Betterment D4: Today is one page; the brief is its Since
                # yesterday fold, made when Today opens. Unfold it.
                toggle = page.locator(f'[id="{wid}"] [data-testid=today-since-toggle]')
                toggle.wait_for(timeout=T)
                toggle.click()
                page.locator(f'[id="{wid}"] [data-testid=today-since-rows]').wait_for(timeout=T)
                page.wait_for_function(BRIEF_SETTLED_JS, arg=wid, timeout=T)
            page.mouse.move(2, 2)
        if ask:
            page.wait_for_function(SETTLED_JS, arg=None, timeout=T)
            page.keyboard.press("Control+KeyI")
            page.locator(f'[id="{wid}"] [data-testid=ask-body]').wait_for(timeout=T)
            page.mouse.move(2, 2)
        if case_id == "door-picked":
            page.wait_for_function(SETTLED_JS, arg=wid, timeout=T)
            for provider, pick in (("github", "karolswdev/HoldSpeak"), ("jira", "KAN")):
                page.get_by_test_id(f"door-trigger-{provider}").click()
                page.get_by_test_id(f"door-pick-{pick}").click()
                # Picked and checked: the row names the pick, and its check is done.
                page.wait_for_function("""([p, pick]) => { const r = document.querySelector(`[data-testid=door-row-${p}]`);
                  return r && r.textContent.includes(pick) && !/Checking/i.test(r.textContent); }""",
                                       arg=[provider, pick.split("/")[-1]], timeout=T)
            page.get_by_test_id("door-counts-github").wait_for(timeout=T)
            page.mouse.move(2, 2)
        if case_id == "program":
            # Programs (2026-10-28): the seeded Program's board, read.
            page.locator(f'[id="{wid}"] [data-testid=programs-board]').wait_for(timeout=T)
        if case_id == "program-text":
            # PG-LANG LANG2: Text (in More ▾ at the phone width), a planned
            # step's title changed, Preview: the well over the text.
            win = page.locator(f'[id="{wid}"]')
            win.locator("[data-testid=programs-board]").wait_for(timeout=T)
            if width < 720:
                win.get_by_test_id("program-more").click()
                page.get_by_role("menuitem", name="Text").click()
            else:
                win.get_by_role("group", name="View").get_by_role("button", name="Text").click()
            lines = win.locator("[data-testid=programs-text] textarea.kit-textpane-input")
            lines.first.wait_for(timeout=T)
            at = lines.evaluate_all("els => els.findIndex(e => e.value === 'step 3 The fan-out')")
            assert at >= 0, "the seeded Program's text has no step 3 line"
            lines.nth(at).fill("step 3 The fan-out, one read")
            win.get_by_test_id("program-text-preview").click()
            win.locator("[data-testid=programs-change-well] [data-testid=programs-diff-row]").first.wait_for(timeout=T)
            page.mouse.move(2, 2)
        if case_id == "program-shape":
            win = page.locator(f'[id="{wid}"]')
            win.locator("[data-testid=programs-board]").wait_for(timeout=T)
            bar = win.get_by_test_id("program-shape-bar")
            bar.get_by_role("textbox", name="Change the program").fill("put step 2 on Codex")
            bar.get_by_test_id("program-shape").click()
            win.locator("[data-testid=program-shape-refusal], [data-testid=programs-change-well]").first.wait_for(timeout=T)
            page.mouse.move(2, 2)
        if case_id == "program-plan":
            win = page.locator(f'[id="{wid}"]')
            # No steps yet: the board is an empty list; the goal and Plan it are the face.
            win.get_by_test_id("program-plan-it").wait_for(timeout=T)
            win.get_by_test_id("program-plan-it").click()
            win.locator("[data-testid=program-plan-refusal], [data-testid=programs-change-well]").first.wait_for(timeout=T)
            page.mouse.move(2, 2)
        if case_id == "person":
            # This pose is the seeded person's content, not the transient
            # readiness/detail gap or a frame whose lazy body has not loaded.
            page.locator(f'[id="{wid}"] [data-testid=people-detail-head]').wait_for(timeout=T)
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
            if case_id == "surface-activity":
                # Window grammar (2026-10-24): the remote sweep seed is a dense
                # list row (What · Who · When · Outcome). Its words and its
                # subject are whole, never squeezed into an ellipsis. Owner
                # ruling 2026-10-25: Who says "Another device" in plain words;
                # no REMOTE chip and no caller address on any row.
                receipt = page.locator('[id="activity-receipt-pipeline:ev-sweep-0"]')
                receipt.wait_for(timeout=T)
                name = receipt.locator("[data-testid^=activity-receipt-name-]")
                assert name.inner_text().replace("\n", " ").startswith("Checked 2 rooms")
                assert name.inner_text().replace("\n", " ").endswith("Heartbeat")
                extent = name.evaluate("""el => ({text: el.textContent,
                    width: el.clientWidth, content: el.scrollWidth})""")
                assert extent["width"] > 0 and extent["content"] <= extent["width"] + 1, (
                    f"Activity receipt text is truncated at {width}: {extent}")
                for badge in (receipt.get_by_text("Completed", exact=True),
                              receipt.get_by_text("Another device", exact=True)):
                    assert badge.is_visible(), f"Activity receipt badge missing at {width}"
                    box = badge.bounding_box()
                    assert box and box["x"] >= 0 and box["y"] >= 0 and (
                        box["x"] + box["width"] <= width
                        and box["y"] + box["height"] <= SIZES[width]), (
                        f"Activity receipt badge is off glass at {width}: {box}")
                chipped = page.locator('#surface-activity [id^="activity-receipt-"]:has(.gadget-chip-egress)')
                assert chipped.count() == 0, "an Activity row wears an egress chip (owner ruling 2026-10-25)"
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
    # Betterment setup ST1: the Rhythm window is parked; its home is
    # Settings ▸ Rhythm, whose quiet hours and Notify read the heartbeat.
    ("surface-settings@rhythm", ["/api/settings/heartbeat"]),
    ("meeting", ["/api/decisions"]),
    ("needs", ["/api/desk/needs-you"]),
    # Betterment AG1: surface-companion (the old Agents application) is
    # unmapped and its window retired; its held-read case left with it.
    # PHILO-17 flakes: the speech row (useSpeechSetup) drew late and moved
    # the Live deck 46 px; the destinations arrival scrolled the Settings
    # body 764 px; the People drawer's 1:1 caption moved the Conductor 24 px.
    ("surface-live", ["/api/setup/local-ai"]),
    ("surface-dictation", ["/api/setup/local-ai"]),
    ("surface-settings@integration:destinations", ["/api/channels/destinations"]),
    ("desk", ["/api/people/readiness"]),
    # The quick check's sweep (2026-10-12): a held desk read let Memory settle
    # before its open focus scrolled it 180 px; People drew its rows before
    # the Door read added the Next 1:1 plate above them (153 px).
    ("surface-project-memory", ["/api/kbs"]),
    ("surface-people", ["/api/door"]),
])
def test_a_held_first_read_moves_nothing(desk: dict[str, Any], pw_browser: Any, case_id: str, held: list[str]) -> None:
    [(_, wid, scope)] = [c for c in CASES if c[0] == case_id]
    wid, scope = wid.format(**desk), (scope.format(**desk) if scope else None)
    base = desk["base"]
    clear_hub_windows_http(base, TOKEN)
    if wid:
        _hub_open(base, wid, scope)
    ctx, page, _, _ = _page(pw_browser, 1440, base)
    try:
        page.add_init_script(_HOLD_JS % json.dumps([held, HELD]))
        page.goto(f"{base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        page.wait_for_function(SETTLED_JS, arg=wid or None, timeout=T)
        sel = f'[id="{wid}"]' if wid else "[data-testid=desk-screen]"
        moved = [r for r in page.evaluate(RECORD_JS, [sel, HELD + 2000]) if r["worst"] > TOLERANCE]
        assert not moved, f"{case_id} with {held} held {HELD} ms: {moved}"
    finally:
        ctx.close()


# PHILO-17 (Astra on #1113): the fitted topology map keeps its cards apart
# and its flow labels off the cards, at a 280 px phone, at 393 and at 1440,
# and a fitted map is whole in its box (every card inside the map area).
TOPOLOGY_JS = r"""() => {
  const t = document.querySelector('#surface-components [data-testid=topology-surface]');
  if (!t) return null;
  t.scrollIntoView({block: 'center'});
  const box = (e) => { const r = e.getBoundingClientRect(); return {L: r.left, T: r.top, R: r.right, B: r.bottom}; };
  const hit = (a, b) => Math.min(a.R, b.R) - Math.max(a.L, b.L) > 0.5 && Math.min(a.B, b.B) - Math.max(a.T, b.T) > 0.5;
  const cards = [...t.querySelectorAll('.surface-topology-node')].map((e) => ({name: e.getAttribute('aria-label'), ...box(e)}));
  const labels = [...t.querySelectorAll('.surface-topology-flow-label')].map((e) => ({name: e.textContent.trim(), ...box(e)}));
  const area = box(t.querySelector('.surface-topology-map-area'));
  const out = [];
  for (let i = 0; i < cards.length; i++) for (let j = i + 1; j < cards.length; j++)
    if (hit(cards[i], cards[j])) out.push(`card ${cards[i].name} x card ${cards[j].name}`);
  for (const l of labels) for (const c of cards) if (hit(l, c)) out.push(`label ${l.name} under card ${c.name}`);
  for (const c of [...cards, ...labels]) if (c.L < area.L - 0.5 || c.R > area.R + 0.5 || c.T < area.T - 0.5 || c.B > area.B + 0.5)
    out.push(`${c.name} outside the map ${JSON.stringify([c.L, c.R, c.T, c.B].map(Math.round))} in ${JSON.stringify([area.L, area.R, area.T, area.B].map(Math.round))}`);
  return {out, cards: cards.length, labels: labels.length};
}"""


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [280, 393, 1440])
def test_the_fitted_topology_keeps_cards_apart(desk: dict[str, Any], pw_browser: Any, width: int) -> None:
    base = desk["base"]
    clear_hub_windows_http(base, TOKEN)
    _hub_open(base, "surface-components", None)
    ctx = pw_browser.new_context(viewport={"width": width, "height": 852 if width < 720 else 900},
                                 device_scale_factor=1, has_touch=width < 720, reduced_motion="reduce")
    try:
        page = ctx.new_page()
        page.goto(f"{base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        page.wait_for_function(SETTLED_JS, arg="surface-components", timeout=T)
        controls = page.get_by_role("button", name="Controls", exact=True)
        if controls.count():
            controls.click()
        else:
            page.get_by_role("button", name=re.compile(r"^Patterns:")).click()
            page.locator("[role^='menuitem']").filter(has_text="Controls").first.click()
        page.locator("#surface-components [data-testid=topology-surface]").wait_for(timeout=T)
        seen = page.evaluate(TOPOLOGY_JS)
        assert seen and seen["cards"] == 3 and seen["labels"] == 2, seen
        assert not seen["out"], f"{width}: {seen['out']}"
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


# The target fence can fail (a planted page at 393, no hub): a 28 px row of
# buttons that share edges loses points, a 44 px button keeps all nine, a
# link inline in prose is not read, and at 1440 nothing is read.
_PLANTED_TARGETS = """<style>body{margin:0;padding:40px 16px;font:14px sans-serif}
.row{display:flex} .row button{height:28px;width:60px;margin:0;border:1px solid #000}
#big{height:48px;width:120px;margin-top:40px}</style>
<div class="row"><button>One</button><button>Two</button></div>
<button id="big">Big</button>
<p>Read <a href="#x">the guide</a> first.</p>"""


@pytest.mark.parametrize(("width", "expect"), [(393, ["One", "Two"]), (1440, [])])
def test_target_fence_sees_a_small_target(pw_browser: Any, width: int, expect: list[str]) -> None:
    ctx = pw_browser.new_context(viewport={"width": width, "height": SIZES[width]})
    try:
        page = ctx.new_page()
        page.set_content(_PLANTED_TARGETS)
        found = page.evaluate(TARGET_JS, None)
        assert sorted(re.match(r"^'([^']*)'", f).group(1) for f in found) == expect, found
    finally:
        ctx.close()


# The reduced-motion half of the still fence can fail: a planted transition
# and a script animation longer than the micro token are recorded, with the
# element they ran on; a shorter one is not; outside the scope is not read.
def test_still_fence_sees_motion_under_reduced_motion(pw_browser: Any) -> None:
    ctx = pw_browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    try:
        page = ctx.new_page()
        page.set_content("""<style>#slow{transition:opacity 400ms linear}</style>
<div id="win"><div id="slow" data-testid="slow-fade">a</div><div id="anim" data-testid="script-move">b</div>
<div id="quick" data-testid="quick-move">c</div></div><div id="out" data-testid="outside">d</div>""")
        page.evaluate(MOTION_INIT_JS % MOTION_MAX_MS)
        page.evaluate("""() => {
          document.getElementById('anim').animate([{opacity: 1}, {opacity: 0.5}], {duration: 300});
          document.getElementById('quick').animate([{opacity: 1}, {opacity: 0.5}], {duration: 10});
          document.getElementById('out').animate([{opacity: 1}, {opacity: 0.5}], {duration: 300});
          requestAnimationFrame(() => { document.getElementById('slow').style.opacity = '0.2'; });
        }""")
        page.wait_for_function("() => (window.__hsMotion || []).some((r) => r.what.startsWith('transition'))", timeout=T)
        found = sorted(page.evaluate(MOTION_JS, "#win"))
        assert found == ["script-move runs Element.animate 300 ms under reduced motion",
                         "slow-fade runs transition opacity 400 ms under reduced motion"], found
        assert any(f.startswith("outside ") for f in page.evaluate(MOTION_JS, None))
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
                try:
                    page.wait_for_function(SETTLED_JS, arg=wid, timeout=T)
                except Exception as exc:
                    raise AssertionError(f"{route} did not settle: {page.evaluate(UNSETTLED_JS, wid)}") from exc
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


@pytest.mark.timeout(120)
@pytest.mark.parametrize("width", [1440, 393])
def test_the_briefing_page_holds_the_fences(desk: dict[str, Any], pw_browser: Any, width: int) -> None:
    """PG-DIRECTION DIR2 (T3): the briefing page at /b/<token>, opened with no
    owner token, holds the window fences (readable, floor, contrast, clipped,
    overlap, library, still, target, clean, egress); its choices are 44 px
    library Buttons; a bad token draws the expired face with no data."""
    base = desk["base"]
    ctx, page, errors, requests = _page(pw_browser, width, base)
    try:
        page.goto(f"{base}/b/{desk['briefing']}", wait_until="load")
        try:
            page.locator("[data-testid=briefing-well]").wait_for(timeout=T)
        except Exception as exc:
            raise AssertionError(f"the page drew no well: {errors} {page.evaluate('document.body.innerText')[:300]!r}") from exc
        page.locator("[data-testid=briefing-choice-go_on]").wait_for(timeout=T)
        sweep = _Case(page, base, "", errors, requests)
        sweep.sel = "[data-testid=briefing-page]"
        sweep.shot = f"briefing-{width}"
        sweep.fences()
        heights = page.evaluate("""() => [...document.querySelectorAll('[data-testid=briefing-choices] button')]
          .map((b) => Math.round(b.getBoundingClientRect().height))""")
        if not heights or min(heights) < 44:
            sweep.failures.setdefault("target", []).append(f"the choices are {heights} px, not 44")
        stored = page.evaluate("() => [document.cookie, localStorage.length, sessionStorage.length]")
        if stored != ["", 0, 0]:
            sweep.failures.setdefault("clean", []).append(f"the page stored something: {stored}")
        _verdict("briefing", width, sweep.failures)
    finally:
        ctx.close()
    ctx, page, errors, _ = _page(pw_browser, width, base)
    try:
        page.goto(f"{base}/b/{'x' * 43}", wait_until="load")
        page.locator("[data-testid=briefing-expired]").wait_for(timeout=T)
        assert page.locator("[data-testid=briefing-well]").count() == 0
        # The one 404 is the honest answer (the shell, then the read); nothing else.
        assert all("404" in error for error in errors), errors
    finally:
        ctx.close()


def test_room_red_is_item_rows_only() -> None:
    """PHILO-17 (Astra r1 on #1111): the Room's ask-bar red excuses an item
    row under the ask bar, and nothing else: two ask-bar boxes, or a box that
    is not an item row, still fail."""
    red = re.compile(ROOM_ITEM_UNDER_ASK)
    assert red.search("overlap 'DUE SEP 1' x 'No engine for answers' @[item-row<items-section] x [room-ask-well]")
    assert red.search("overlap 'Settlement latency' x 'Ask this project' @[item-row] x [room-ask-input-well<room-ask-well]")
    # Two ask-bar boxes collide: never excused.
    assert not red.search("overlap 'No engine for answers' x 'Ask this project' @[room-ask-well] x [room-ask-input-well<room-ask-well]")
    # A box that is not an item row (a head chip, a source row): never excused.
    assert not red.search("overlap 'AT RISK' x 'Ask this project' @[room-head] x [room-ask-well]")
    assert not red.search("overlap 'x' x 'y' @[] x [room-ask-well]")
    # The item row under something that is not the ask bar: never excused.
    assert not red.search("overlap 'DUE SEP 1' x 'Pause' @[item-row] x [room-footer]")
    # An item row's own token (item-token<item-row) is an item row.
    assert red.search("overlap 'AT_RISK' x 'Choose' @[item-token<item-row<items-section] x [room-ask-input-well<room-ask-well]")
    # The ask bar's own word against the ask field: two ask-bar boxes.
    assert not red.search("overlap 'No engine for answers' x 'Ask this project' @[room-ask-no-engine<room-ask-input-well] x [room-ask-input-well<room-ask-well]")
