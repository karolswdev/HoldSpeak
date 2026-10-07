"""PHILO-14 canvas: The Desk Is Objects. Three alternatives of the desk's shape (A Workbench,
B Bench, C Stage), five moments each, at 1440 and 393; and the CONTROL: the product as it is on
main, shot on the same seed.

Two legs, each width on its own hub and HOME (p14stack.P14Stack: rig.Stack + seed_f2.py + a tmux
server of its own + a fake `gh` on the hub's PATH; every scratch dir is removed at the end):
  - CONTROL (CANVAS_MODE=today): no seat, no shim. The Chair, the Floor, a Room, the Floor list,
    the Hand to agent sheet, the session window, the Needs you coder row.
  - PROPOSAL (CANVAS_MODE=proposal): one seat (seats.mjs) lets p14.tsx draw an alternative in the
    Chair's place; its stand-ins are named in p14.tsx's header (S1-S7).

The fences are board.py's (C1's JS_LIB, CONTRAST_ALL, CLIP, OVERLAP, TARGETS44 and C5's laws,
imported unchanged from the ratified story-11 and story-15 harnesses). A board whose face has no
window (a bare screen) is held to "no blue title bar" (shoot_bare), every other law the same.

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python docs/internal/philo/phase-14/canvas/harness/shoot.py
ONLY_WIDTH=393 / ONLY=B- / LEG=control|proposal limit the run. Exit 2 on a failed fence.
"""
from __future__ import annotations

import json
import os
import sys

sys.dont_write_bytecode = True   # no __pycache__ in the tree
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import board  # noqa: E402
import p14stack  # noqa: E402
import rig  # noqa: E402

B = board.B
SHOTS = HERE.parent / "shots"
MODE = {"m": "proposal"}
rig.Stack = lambda mode="proposal", shims="p": p14stack.P14Stack(MODE["m"], shims)   # board.Runner.run builds its stack here

DRAWER = "Payments ledger cutover"
INFO = "Info: Write the rollback runbook"
LANE = "Claude Code: rollback runbook"
NEEDS = "Needs you"
RUNBOOK = "Write the rollback runbook"

# This canvas's own targets at 393 (the fence fails on these; every other small target is main's
# and recorded as inherited): everything the proposal draws.
OWN44 = r"""() => [...document.querySelectorAll(
  '.p14-screen button, .p14-screen input, .p14-win .desk-pullout-body button, .p14-win .desk-pullout-body input, '
  + '.p14-win .surface-footer-layout button')]
  .map((t) => (t.getAttribute('aria-label') || t.innerText || t.getAttribute('placeholder') || t.className || '').toString().trim().replace(/\s+/g, ' ').slice(0, 32))"""


def board_for(r: board.Runner, name: str, front: str | None, bare: bool = False, **kw):
    if bare:
        return r.shoot_bare(name, None, **kw)
    return r.shoot(name, front, **kw)


# ── the proposal ─────────────────────────────────────────────────────────
FRONTS = {
    ("A", 1): None, ("A", 2): INFO, ("A", 3): DRAWER, ("A", 4): LANE, ("A", 5): NEEDS,
    ("B", 1): NEEDS, ("B", 2): DRAWER, ("B", 3): DRAWER, ("B", 4): LANE, ("B", 5): NEEDS,
    ("C", 1): None, ("C", 2): INFO, ("C", 3): None, ("C", 4): LANE, ("C", 5): NEEDS,
}
WIN_ID = {DRAWER: "p14:drawer", INFO: "p14:info", LANE: "p14:lane", NEEDS: "p14:needs"}
# The things each moment must show WHOLE on the glass.
WHOLE = {
    1: ["[data-testid=p14-icon-p-ledger], [data-testid=p14-shelf], [data-testid=p14-zone-p-ledger]"],
    2: ["[data-testid=p14-icon-m-standup-a1], [data-testid=p14-row-m-standup-a1]"],
    3: ["[data-testid=p14-confirm]", "[data-testid=p14-brief]", "[data-testid=p14-hand]"],
    4: ["[data-testid=p14-question]", "[data-testid=p14-answer]", "[data-testid=p14-ask] input"],
    5: ["[data-testid=p14-needs-head]"],
}


def proposal(r: board.Runner) -> None:
    ev, settle, phone = r.ev, r.settle, r.phone
    r.scope44 = OWN44
    for alt in "ABC":
        for m in range(1, 6):
            front = FRONTS[(alt, m)]
            # 393: moment 2 is the list (one window at a time; Info is the footer verb); C2 at 393
            # is the drawer window (the place opens as its list).
            if phone and m == 2:
                front = DRAWER
            if phone and alt == "B" and m == 1:
                front = None
            ev("() => window.__p.reset()")
            r.close_all()
            ev(f"() => window.__p.set({{alt: '{alt}', moment: {m}, view: 'icons'}})")
            settle(1400)
            if front:
                ev("(w) => window.__cOpen.focus(w)", WIN_ID[front])
                settle(500)
            if m == 2:
                row = r.page.locator("[data-testid=p14-row-m-standup-a1]").first
                if row.count():
                    row.scroll_into_view_if_needed()
                    settle(300)
            if phone and alt == "C" and m == 3:
                r.page.locator("[data-testid=p14-confirm]").first.scroll_into_view_if_needed()
                settle(400)
            whole = [w for w in WHOLE[m] if not (phone and m == 1)]
            if m == 2:
                whole = ["[data-testid=p14-row-m-standup-a1]"] if phone else ["[data-testid=p14-icon-m-standup-a1]", "[data-testid=p14-info], [data-testid=p14-tray-info]"]
            checks = {}
            if m == 4:
                checks["the lane shows the timeline, the PR and the files"] = ev(
                    "() => !!document.querySelector('[data-testid=p14-rail], [data-testid=p14-track]') && !!document.querySelector('[data-testid=p14-pr]') && !!document.querySelector('[data-testid=p14-files]')")
                checks["no terminal pane on the lane's face"] = ev("() => !document.querySelector('#p14\\\\:lane .xterm, #p14\\\\:lane .terminal-well-screen')")
            if m == 5:
                checks["six object rows, each with its sprite"] = ev("() => [...document.querySelectorAll('[data-testid=p14-need-row]')].filter((r) => r.querySelector('img')).length") == 6
            if m == 2:
                checks["no [ ] mark on the drawer"] = ev("() => !/\\[\\s?[x ]?\\s?\\]/.test((document.querySelector('#p14\\\\:drawer, [data-testid=p14-screen]') || document.body).innerText)")
            board_for(r, f"{alt}-{m}", front, bare=front is None and not (alt == "B" and m == 1 and not phone),
                      whole=whole, checks=checks)
            if alt == "A" and m == 2 and not phone:
                # A-2L: the same drawer in its list view (the list is one species in A, B and C).
                ev("() => window.__p.set({view: 'list'})")
                settle(900)
                ev("(w) => window.__cOpen.focus(w)", "p14:drawer")
                settle(400)
                r.page.locator("[data-testid=p14-row-m-standup-a1]").first.scroll_into_view_if_needed()
                settle(300)
                board_for(r, "A-2L", DRAWER, whole=["[data-testid=p14-row-m-standup-a1]"],
                          checks={"no [ ] mark on the drawer": ev("() => !/\\[\\s?[x ]?\\s?\\]/.test(document.getElementById('p14:drawer').innerText)")})
    ev("() => window.__p.reset()")


# ── the control: the product as it is on main ────────────────────────────
def control(r: board.Runner) -> None:
    ev, settle, page, phone = r.ev, r.settle, r.page, r.phone
    r.scope44 = "() => []"   # the control is main's face: every small target is recorded as inherited, never failed
    r.strict_chrome = False
    # 1 the Chair (home)
    ev("() => import('/src/desk/chair/chairWindows.ts').then((m) => m.openChairWindow('chair:needs'))")
    settle(1500)
    r.shoot("control-1", None)
    # 1b the Floor (the spatial desk), 2b the Floor list (the explorer with [ ])
    ev("() => window.__cOpen.floorList()")
    settle(800)
    ev("() => import('/src/desk/store.ts').then((m) => m.useDesk.getState().setViewMode('spatial'))")
    settle(4000)
    r.shoot_bare("control-1b", None)
    ev("() => window.__cOpen.floorList()")
    settle(2000)
    r.shoot_bare("control-2b", None, extra={"bracket_marks": ev("() => (document.body.innerText.match(/\\[ \\]/g) || []).length")})
    ev("() => window.__cOpen.chair()")
    settle(1500)
    r.close_all()
    # 2 a Room (the Project's face today)
    ev("() => window.__cOpen.room('p-ledger')")
    settle(3500)
    ev("(w) => window.__cOpen.focus(w)", "surface-project-memory")
    settle(600)
    r.shoot("control-2", DRAWER)
    r.close_all()
    # 5 the Needs you coder row
    ev("() => import('/src/desk/chair/chairWindows.ts').then((m) => m.openChairWindow('chair:needs'))")
    settle(1200)
    more = page.locator("[data-testid=arrival-needs-you] button:has-text('Show all')").first
    if more.count():
        r.tap(more, 900)
    coder = page.locator("[data-testid=arrival-coder-row]").first
    coder.scroll_into_view_if_needed()
    settle(500)
    r.shoot("control-5", "Needs you", extra={"coder_row": coder.inner_text() if coder.count() else None})
    # 3 Hand to agent: the launch sheet from a Door row (Launch is never pressed: no agent starts)
    verb = page.locator("[data-testid=hand-row-verb]").first
    if verb.count():
        verb.scroll_into_view_if_needed()
        settle(300)
        r.tap(verb, 2500)
        r.shoot("control-3", None)
        cancel = page.locator("[data-testid=hand-sheet] button:has-text('Cancel'), .desk-hand-footer button:has-text('Cancel')").first
        if cancel.count():
            r.tap(cancel, 800)
        r.close_all()
    else:
        r.fails.append(f"control-3-{r.width}: no Hand to agent verb on a Door row")
    # 4 the session window (Open on the coder row)
    ev("() => import('/src/desk/chair/chairWindows.ts').then((m) => m.openChairWindow('chair:needs'))")
    settle(1000)
    more = page.locator("[data-testid=arrival-needs-you] button:has-text('Show all')").first
    if more.count():
        r.tap(more, 900)
    opener = page.locator("[data-testid=arrival-coder-open]").first
    opener.scroll_into_view_if_needed()
    settle(300)
    r.tap(opener, 3000)
    # main's xterm well scrolls sideways inside itself (PaneWell; the Conductor F2 proof recorded the
    # same): recorded as inherited, as the control is main's face.
    r.shoot("control-4", None, inherit_clip={"strips": ["terminal-well-screen"], "clipped": []})


def main() -> int:
    widths = [w for w in B.ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
    legs = [x for x in ("control", "proposal") if os.environ.get("LEG", x) == x]
    facts_path = SHOTS / "facts.json"
    facts: dict = json.loads(facts_path.read_text()) if (os.environ.get("ONLY") or os.environ.get("ONLY_WIDTH") or os.environ.get("LEG")) and facts_path.exists() else {}
    fails: list[str] = []
    for leg in legs:
        MODE["m"] = "today" if leg == "control" else "proposal"
        for width, height in widths:
            r = board.Runner(SHOTS, "P", width, height, "p", None)
            r.first_run = None
            r.run(control if leg == "control" else proposal)
            fails += r.fails
            facts.update(r.facts)
    facts["_fails"] = fails
    SHOTS.mkdir(parents=True, exist_ok=True)
    facts_path.write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    print("\nFAILS:" if fails else "\nALL FENCES HELD", *fails, sep="\n  ")
    return 2 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
