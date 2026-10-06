"""The Conductor canvas: the F faces of docs/internal/CONDUCTOR.md, drawn on the REAL product.

A REAL hub (scripts/graph_walk.py serve) on an isolated HOME (tempfile.mkdtemp(prefix="kcanvas-",
dir="/tmp"), removed when the run ends), seeded through the product's producers (seed_db.py: the
Project, the action item, the decision, two hook-reported agent sessions) and routes
(rig.seed_hub); the PRODUCT app as on main, served by vite with the seats (seats.mjs) and the shim
(conductor.tsx, its stand-ins named in its header). Each width on its own hub and HOME.

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python docs/internal/conductor-canvas/harness/shoot.py
ONLY_WIDTH=393 / ONLY=K3 limit the run; STACK_STATE=<dev.py state> reuses a stack (iteration only;
a reused stack has no first run). Exit 2 on a failed fence.
"""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True   # no __pycache__ in the tree
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import board  # noqa: E402

RUNBOOK = "Write the rollback runbook"
ISSUE418 = "#418 Reconciliation job slow on month-end data"
ISSUE421 = "#421 Add the ledger freeze flag"
ROOM = "surface-project-memory"
NEEDS = "chair:needs-you"
SHEET = "agent-hand"

# The ChoiceCard species' radio is a visually hidden input; the whole card (its label) owns the tap.
# It is recorded under inherited_under_44 (a species fact), never counted as this canvas's target.
# This canvas's own targets: the 393 fence fails on these; any other small target is recorded as inherited.
OWN44 = r"""() => [...document.querySelectorAll(
  '[data-testid=firstrun-agents] button, [data-testid=k-launch-sheet] button, [data-testid=k-launch-sheet] input:not(.surface-choice-card-radio), .k-hand-footer button, '
  + '[data-testid=k-coder-row] button, [data-testid=k-hand-verb], [data-testid=k-flight], .k-tokens button, '
  + '[role=menu] [role^=menuitem], .desk-steer button, .desk-steer textarea')]
  .map((t) => (t.getAttribute('aria-label') || t.innerText || t.getAttribute('placeholder') || t.className || '').toString().trim().replace(/\s+/g, ' ').slice(0, 32))"""


def reset(r: board.Runner) -> None:
    r.ev("() => window.__k.reset()")
    r.close_all()


def first_run(r: board.Runner) -> None:
    """K1: the first-run face, before the first run is dismissed."""
    r.scope44 = OWN44
    card = "[data-testid=firstrun-agents]"
    r.page.locator(card).scroll_into_view_if_needed()
    r.settle(600)
    r.shoot_bare("K1a-agents-found", None, whole=[card + " [aria-label^='Install hooks']", card + " [data-agent=claude]", card + " [data-agent=tmux]"],
            checks={"two agent rows and a tmux row": r.ev(f"() => document.querySelectorAll('{card} [data-testid=k-agent-row]').length") == 3})
    r.tap(r.page.locator(card + " [aria-label^='Install hooks']"), 1600)
    r.page.locator(card).scroll_into_view_if_needed()
    r.shoot_bare("K1b-agents-done-receipt", None, whole=[card + " [data-testid=k-agents-receipt]"],
            checks={"the card folded to its receipt (no rows)": r.ev(f"() => !document.querySelector('{card} [data-testid=k-agent-row]')")})
    r.ev("() => window.__k.agents('missing')")
    r.settle(500)
    r.page.locator(card).scroll_into_view_if_needed()
    r.shoot_bare("K1c-agents-not-installed", None, whole=[card + " [aria-label^='Copy install: Claude']", card + " [data-testid=k-check-again]"])
    r.ev("() => window.__k.agents('found')")


def boards(r: board.Runner) -> None:
    ev, settle, page, phone = r.ev, r.settle, r.page, r.phone
    r.scope44 = OWN44

    # ── K2a the Object menu (the Floor list, the decision selected) ──
    ev("() => window.__cOpen.floorList()")
    settle(1500)
    ev("() => window.__cOpen.select('decision:d-freeze')")
    settle(600)
    if phone:
        r.tap(page.locator(".desk-verbbar [data-menu-id=go] button"), 700)
        r.open_sub("Object")   # main's grouped Go (C7): Go ▸ Object ▸
        row = page.locator("[role=menu] [role=menuitem]:has-text('Hand to agent')").first
        row.scroll_into_view_if_needed()
        settle(300)
    else:
        page.locator(".desk-verbbar [data-menu-id=object] button").first.click()
        settle(700)
    f = r.shoot_bare("K2a-object-menu", None)
    if f is not None and not any("Hand to agent" in x for m in f["menus"] for x in m["rows"]):
        r.fails.append(f"K2a-{r.width}: no Hand to agent row in the Object menu ({f['menus'][:1]})")
    r.escape()

    # ── K2b the object context menu (right button). At 393 main has no row long press: a press
    #    opens the object, so the phone's object menu is Go ▸ Object (K2a). Recorded, not drawn. ──
    if phone:
        r.facts[f"K2b-context-menu-{r.width}"] = {"not_drawn": "393: a row press opens the object; the object menu is Go > Object (K2a-393)"}
    else:
        name = page.locator(".desk-list-name-cell:has-text('Freeze the old ledger on Nov 5')").first
        name.scroll_into_view_if_needed()
        b = name.bounding_box()
        page.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, button="right")
        settle(600)
        f = r.shoot_bare("K2b-context-menu", None)
        if f is not None and not any("Hand to agent" in x for m in f["menus"] for x in m["rows"]):
            r.fails.append(f"K2b-{r.width}: no Hand to agent row in the context menu ({[m['label'] for m in f['menus']]})")
        r.escape()

    # ── K2c the ⌘K deck ──
    ev("() => window.__cOpen.palette('1')")
    settle(700)
    page.keyboard.type("hand", delay=40)
    settle(900)
    deck = r.ev("() => document.body.innerText")
    r.shoot_bare("K2c-command-deck", None, inherit=["Freeze the old ledger on Nov 5"], inherit_overlap=["39 ITEMS", "39 SHOWN"], checks={"the deck lists Hand to agent": "Hand to agent" in deck}, extra={"deck_has_verb": "Hand to agent" in deck})
    ev("() => window.__cOpen.palette('0')")
    settle(400)
    page.keyboard.press("Escape")
    ev("() => window.__cOpen.chair()")
    settle(1500)
    reset(r)

    # ── K2d the Door row verb (Needs you: the action item) ──
    show = page.locator("[data-testid=arrival-needs-you] button:has-text('Show all')").first
    if show.count():
        r.tap(show, 900)
    row = page.locator(f"[data-testid=arrival-needs-you-row]:has-text('{RUNBOOK}')").first
    row.scroll_into_view_if_needed()
    settle(500)
    r.shoot("K2d-door-row-verb", "Needs you", whole=[f"[aria-label='Hand to agent: {RUNBOOK}']"])

    # ── K3a the launch sheet (from the Door row) ──
    r.tap(row.locator("[data-testid=k-hand-verb]"), 1500)
    r.shoot("K3a-launch-sheet-claude", "Hand to agent", whole=["[data-testid=k-launch]", ".k-hand-footer .gadget-chip-egress", "[data-testid=k-control]"],
            checks={"the egress chip names the cloud agent's host": "API.ANTHROPIC.COM" in r.ev("() => document.querySelector('.k-hand-footer').innerText")})
    # ── K3c the Control-mode board (the owner question), unfolded under the chip ──
    r.tap(page.locator("[data-testid=k-control]"), 700)
    board_el = page.locator("[data-testid=k-control-board]")
    board_el.scroll_into_view_if_needed()
    settle(400)
    rows = r.ev("() => [...document.querySelectorAll('[data-testid=k-control-board] li.surface-ledger-row')].map((x) => x.innerText.replace(/\\s+/g, ' ').trim())")
    r.shoot("K3c-control-mode-mapping", "Hand to agent", whole=[] if phone else ["[data-testid=k-control-board]"],
            checks={"three modes, each with its four tokens": len(rows) == 3}, extra={"modes": rows})
    # Launch (stand-in S2: nothing spawns); the row now wears its flight chip.
    r.tap(page.locator("[data-testid=k-launch]"), 1200)
    launched = r.ev("() => window.__k.state().launches")
    if RUNBOOK not in launched:
        r.fails.append(f"K3-{r.width}: Launch did not record a launch ({launched})")
    reset(r)

    # ── K3b the launch sheet for an issue, Codex picked (from the Room row) ──
    ev("() => window.__cOpen.room('p-ledger')")
    settle(3500)
    ev(f"(w) => window.__cOpen.focus(w)", ROOM)
    settle(500)
    issue = page.locator(f"[id='{ROOM}'] [data-testid=needs-you-row]:has-text('#418')").first
    issue.scroll_into_view_if_needed()
    settle(400)
    r.shoot("K2e-room-row-verb", "Payments ledger cutover", whole=[f"[aria-label='Hand to agent: {ISSUE418}']"])
    r.tap(issue.locator("[data-testid=k-hand-verb]"), 1500)
    pick = page.locator("[data-testid=k-launch-sheet] label.surface-choice-card:has-text('Codex')").first
    r.tap(pick, 700)
    r.shoot("K3b-launch-sheet-codex", "Hand to agent", whole=["[data-testid=k-launch]", ".k-hand-footer .gadget-chip-egress"],
            checks={"the egress chip follows the pick": "API.OPENAI.COM" in r.ev("() => document.querySelector('.k-hand-footer').innerText")})
    r.tap(page.locator("[data-testid=k-launch]"), 1200)
    reset(r)

    # ── K4 in flight: the Claude session waits (seeded), Codex works (seeded), one PR is open ──
    ev(f"() => window.__k.set({RUNBOOK!r}, {{ agent: 'claude', state: 'waiting' }})")
    ev(f"() => window.__k.set({ISSUE418!r}, {{ agent: 'codex', state: 'working' }})")
    ev(f"() => window.__k.set({ISSUE421!r}, {{ agent: 'claude', state: 'pr_open', pr: 412 }})")
    ev("() => window.__cOpen.room('p-ledger')")
    settle(3500)
    ev(f"(w) => window.__cOpen.focus(w)", ROOM)
    settle(500)
    page.locator(f"[id='{ROOM}'] [data-testid=needs-you-row]").first.scroll_into_view_if_needed()
    settle(400)
    chips = r.ev(f"() => [...document.querySelectorAll(\"[id='{ROOM}'] [data-testid=k-flight]\")].map((c) => c.innerText.trim())")
    r.shoot("K4b-room-in-flight", "Payments ledger cutover",
            checks={"the Room shows WAITING, WORKING and PR #412 OPEN": all(any(w in c for c in chips) for w in ["WAITING", "WORKING", "PR #412 · OPEN"])},
            extra={"chips": chips})
    reset(r)
    show = page.locator("[data-testid=arrival-needs-you] button:has-text('Show all')").first
    if show.count():
        r.tap(show, 900)
    row = page.locator(f"[data-testid=arrival-needs-you-row]:has-text('{RUNBOOK}')").first
    row.scroll_into_view_if_needed()
    settle(500)
    r.shoot("K4a-door-row-in-flight", "Needs you", whole=["[data-testid=arrival-needs-you] [data-testid=k-flight]"])
    ev("() => window.__k.readCoders()")
    settle(1500)
    ev("() => import('/src/desk/chair/chairWindows.ts').then((m) => m.openChairWindow('chair:week'))")
    settle(1500)
    agents = page.locator("[data-testid=arrival-agents]").first
    agents.scroll_into_view_if_needed()
    settle(500)
    origin = r.ev("() => [...document.querySelectorAll('[data-testid=k-agent-origin]')].map((c) => c.innerText.trim())")
    r.shoot("K4c-agents-session-pin", "The week", whole=["[data-testid=arrival-agents] [data-testid=k-agent-origin]"],
            checks={"each session row names its item": len(origin) == 2}, extra={"origins": origin})

    # ── K5a the Needs you coder row ──
    ev("() => import('/src/desk/chair/chairWindows.ts').then((m) => m.openChairWindow('chair:needs'))")
    settle(1000)
    ev("() => window.__k.coderRow(true)")
    settle(2500)
    page.locator("[data-testid=k-coder-row]").first.scroll_into_view_if_needed()
    settle(500)
    head = r.ev("() => (document.querySelector('[data-testid=arrival-display]') || {}).innerText || ''")
    r.shoot("K5a-needs-you-coder-row", "Needs you",
            whole=["[data-testid=k-coder-question]", "[data-testid=k-speak-answer]", "[data-testid=k-coder-project]"],
            checks={"the head counts the coder row": head.startswith("13 ")}, extra={"headline": head})
    # Control: MAIN's session window for the same session (no answer well), measured, not shot.
    ev("() => import('/src/desk/shell.ts').then((m) => m.openCoderSession('claude:c1a0de00-runbook'))")
    settle(2500)
    main_clip = r.ev(board.B.CLIP)
    r.facts[f"_main_session_window_{r.width}"] = main_clip
    reset(r)
    ev("() => import('/src/desk/chair/chairWindows.ts').then((m) => m.openChairWindow('chair:needs'))")
    settle(800)
    page.locator("[data-testid=k-coder-row]").first.scroll_into_view_if_needed()
    settle(400)
    inherit_clip = {"strips": [x["cls"] for x in main_clip["strips"]], "clipped": [x["text"] for x in main_clip["clipped"]]}
    # ── K5b Speak answer: the session window, the steer composer already recording ──
    r.tap(page.locator("[data-testid=k-speak-answer]"), 2500)
    page.locator("[data-testid=k-answer-well]").first.scroll_into_view_if_needed()
    settle(500)
    listening = r.ev("() => !!document.querySelector('.desk-steer .desk-mic.is-listening')")
    r.shoot("K5b-speak-answer-recording", "claude", inherit_clip=inherit_clip, whole=[".desk-session-question", "[data-testid=k-answer-well] .desk-mic", "[data-testid=k-answer-well] .desk-steer-input"],
            checks={"the steer mic is listening": listening, "the session window is in front": r.ev("() => (document.querySelector('.desk-window-shell.is-front') || {}).id === 'session'")})
    # ── K5c Enter sends ──
    inp = page.locator("[data-testid=k-answer-well] .desk-steer-input").first
    inp.fill("Jordan owns the rollback. Avery reviews it.")
    inp.press("Enter")
    settle(1200)
    steered = r.ev("() => window.__k.state().steered")
    r.shoot("K5c-enter-sends", "claude", inherit_clip=inherit_clip, whole=["[data-testid=k-answer-well] .desk-steer-sent"],
            checks={"Enter sent the steer": bool(steered) and "Jordan owns" in str(steered.get("text", "") if isinstance(steered, dict) else steered),
                    "the composer is empty after the send": inp.input_value() == ""},
            extra={"steered": steered})
    reset(r)

    # ── K6 the merge: the commitment closes with the PR as evidence ──
    ev(f"() => window.__k.set({RUNBOOK!r}, {{ agent: 'claude', state: 'merged', pr: 413 }})")
    ev(f"() => window.__k.close({RUNBOOK!r}, 413)")
    ev("() => window.__cOpen.room('p-ledger')")
    settle(3500)
    ev(f"(w) => window.__cOpen.focus(w)", ROOM)
    settle(600)
    rows = r.ev(f"() => [...document.querySelectorAll(\"[id='{ROOM}'] [data-testid=needs-you-row]\")].map((c) => c.innerText.replace(/\\s+/g, ' ').trim())")
    r.shoot("K6-follow-through-receipt", "Payments ledger cutover", whole=["[data-testid=k-closed-receipt]"],
            checks={"the runbook left OPEN HERE": not any(RUNBOOK in x for x in rows)}, extra={"open_here": rows})
    reset(r)


if __name__ == "__main__":
    sys.exit(board.main(boards, first_run))
