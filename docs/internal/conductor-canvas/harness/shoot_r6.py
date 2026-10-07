"""Conductor R6: the session window's footer in Secure, Normal and YOLO, at rest and armed.

The F2 stack unchanged (shoot_built_f2.BuiltStack: a real hub on a scratch HOME, the F2 seed, a
`cat` pane per launch on a tmux server of its own). The fences are board.py's (C1's CONTRAST_ALL,
CLIP, OVERLAP, TARGETS44), scoped to the session controls at 393.

For each mode the hub's own control-mode route is set (`PUT /api/authority/control-mode`), the
session window opens from the Needs you row (Open), the footer is shot at rest, then the arm verb
is pressed (Secure, Normal: the ARM key; YOLO: the rename/kill arm verb) and the footer is shot
armed. Every request the press sends is recorded, so a before run and an after run show the same
arming call. The grant is disarmed and the window closed before the next mode.

Usage (from the worktree root):
  PHASE=before|after PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python docs/internal/conductor-canvas/harness/shoot_r6.py
Shots and facts go to .tmp/evidence-shots/conductor-r6/<PHASE>/. ONLY_WIDTH=393 limits the run.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shoot_built_f2 as f2  # noqa: E402  (patches rig.Stack to the F2 stack and the fake mic)
import board  # noqa: E402
import rig  # noqa: E402

B = board.B
REPO = HERE.parents[3]
PHASE = os.environ.get("PHASE", "after")
OUT = REPO / ".tmp/evidence-shots/conductor-r6" / PHASE
MODES = [("safe", "secure"), ("neutral", "normal"), ("yolo", "yolo")]

OWN44 = r"""() => [...document.querySelectorAll('[data-testid=session-controls] button')]
  .map((t) => (t.getAttribute('aria-label') || t.innerText || t.className || '').toString().trim().replace(/\s+/g, ' ').slice(0, 32))"""

# The footer's controls as a reader meets them: each verb, its element, its species, its box.
FOOTER = r"""() => { const c = document.querySelector('[data-testid=session-controls]'); if (!c) return null;
  return { text: c.innerText.replace(/\s+/g, ' ').trim(),
    verbs: [...c.querySelectorAll('button')].map((b) => { const r = b.getBoundingClientRect();
      return { label: b.innerText.replace(/\s+/g, ' ').trim(), aria: b.getAttribute('aria-label'), cls: b.className,
               library: b.classList.contains('btn') || b.classList.contains('btn--chrome') || b.classList.contains('gadget-transport-key'),
               w: Math.round(r.width), h: Math.round(r.height) }; }),
    tokens: [...c.querySelectorAll('.surface-token')].map((t) => t.innerText.trim()) }; }"""

ARM_VERB = "[data-testid=session-controls] button"


def arm_verb(r, mode: str):
    """The verb that arms rename and kill: YOLO's footer verb, else the ARM key."""
    page = r.page
    if mode == "yolo":
        return page.locator(ARM_VERB).filter(has_text=re.compile(r"\bArm\b")).first  # case-sensitive: never the ARM key
    return page.locator("[data-testid=session-controls] button:has-text('ARM')").first


def boards(r: board.Runner) -> None:
    ev, settle, page = r.ev, r.settle, r.page
    r.scope44 = OWN44
    r.shots = OUT
    st = f2.STACK[-1]
    calls: list[dict] = []
    page.on("request", lambda q: calls.append({"method": q.method, "url": q.url.split("?")[0].replace(st.url.split("/?")[0], ""),
                                               "body": q.post_data}) if q.method == "POST" and "/api/coders/" in q.url else None)
    inherit_clip = {"strips": ["terminal-well-screen"], "clipped": []}
    for wire, name in MODES:
        status, body = rig.hub_api(st.hub, "PUT", "/api/authority/control-mode", {"control_mode": wire})
        r.facts[f"_mode_{name}_{r.width}"] = {"status": status, "mode": (body or {}).get("control_mode") if isinstance(body, dict) else body}
        ev("() => import('/src/desk/chair/chairWindows.ts').then((m) => m.openChairWindow('chair:needs'))")
        settle(1500)
        r.tap(page.locator("[data-testid=arrival-coder-open]").first, 3500)
        controls = page.locator("[data-testid=session-controls]").first
        controls.wait_for(timeout=20_000)
        verb = arm_verb(r, wire)
        if verb.count():
            verb.scroll_into_view_if_needed()
        settle(800)
        r.shoot(f"R6-{name}-rest", None, inherit_clip=inherit_clip,
                checks={"the arm verb is on the footer": verb.count() == 1},
                extra={"footer": ev(FOOTER)})
        calls.clear()
        if verb.count():
            r.tap(verb, 2000)
        armed = ev("() => import('/src/desk/steering.ts').then((m) => m.useSteering.getState().armed)")
        factory = page.locator("[data-testid=session-controls] .desk-factory").first
        if factory.count():
            factory.scroll_into_view_if_needed()
        settle(600)
        r.shoot(f"R6-{name}-armed", None, inherit_clip=inherit_clip,
                checks={"the press armed the pane": armed is True},
                extra={"footer": ev(FOOTER), "arm_calls": list(calls)})
        ev("() => import('/src/desk/steering.ts').then((m) => m.useSteering.getState().disarm())")
        settle(800)
        ev("() => import('/src/desk/steering.ts').then((m) => m.useSteering.getState().closeSession())")
        settle(600)
        r.close_all()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    widths = [w for w in B.ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
    facts: dict = {}
    fails: list[str] = []
    for width, height in widths:
        rr = board.Runner(OUT, "K", width, height, "k", None)
        rr.first_run = None
        rr.run(boards)
        fails += rr.fails
        facts.update(rr.facts)
    facts["_fails"] = fails
    (OUT / "facts.json").write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    print("\nFAILS:" if fails else "\nALL FENCES HELD", *fails, sep="\n  ")
    return 2 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
