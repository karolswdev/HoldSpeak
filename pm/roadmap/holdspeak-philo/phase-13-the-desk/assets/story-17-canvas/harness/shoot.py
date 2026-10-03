"""PHILO-13-17 (C7) canvas: the phone desk, drawn on the REAL product.

The rig, the seed, the vite config and the fences are story 15's
(../../story-15-canvas/harness/: rig.py, seed_db.py, vite.config.mjs, board.py; board.py
imports C1's ratified fence code). This folder holds C7's seats (seats-c7.mjs) and shim (c7.tsx).
393 is the story; 1440 is the control (C7 changes nothing there).

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-17-canvas/harness/shoot.py
Exit 2 on a failed fence.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "story-15-canvas/harness"))
import board  # noqa: E402

SHOTS = HERE.parent / "shots"
MEET = "pullout:meeting:m-standup"

# The phone fences (393): the frame at most 852/6 = 142 px; the front window's content >= 700 px;
# no chrome owns a content verb's hit point (C1's TARGETS44 over every target, all owned).
FRAME_MAX, CONTENT_MIN = 142, 700


def frame_px(f: dict) -> int:
    """The screen bar + the shelf. Capture is a window at 393 (C1), never a bar: when it is on the glass
    it is the front window's own content, measured by the content fence."""
    fr = f["frame"]
    return sum((fr[k] or {}).get("h", 0) for k in ("menubar", "dock"))


def boards(r: board.Runner) -> None:
    ev, settle, phone = r.ev, r.settle, r.phone
    r.strict_chrome = True   # condition 6: the menu bar and the Dock own no content hit point

    def phone_laws(f: dict | None) -> None:
        if f is None or not phone:
            return
        px = frame_px(f)
        f["frame_px"] = px
        if px > FRAME_MAX:
            r.fails.append(f"{f['_key']}: the frame is {px} px (> {FRAME_MAX})")
        if (f.get("content_px") or 0) < CONTENT_MIN:
            r.fails.append(f"{f['_key']}: the front window's content is {f.get('content_px')} px (< {CONTENT_MIN})")

    def chevron(f: dict) -> None:
        """Condition 3: the switcher's ▾ is PAINTED on the glass: whole, on top at its centre, and the
        pixels of its box change when it alone is hidden (two screenshots of that box)."""
        m = r.page.locator("[data-testid=c7-switcher-mark]")
        if not m.count():
            r.fails.append(f"{f['_key']}: no switcher chevron")
            return
        w = ev(board.WHOLE, "[data-testid=c7-switcher-mark]")
        b = m.first.bounding_box()
        clip = {"x": b["x"], "y": b["y"], "width": max(1, b["width"]), "height": max(1, b["height"])}
        shown = r.page.screenshot(clip=clip)
        ev("() => { document.querySelector('[data-testid=c7-switcher-mark]').style.visibility = 'hidden'; }")
        hidden = r.page.screenshot(clip=clip)
        ev("() => { document.querySelector('[data-testid=c7-switcher-mark]').style.visibility = ''; }")
        name_cut = ev("() => { const n = document.querySelector('.c7-switcher-name'); return n ? n.scrollWidth > n.clientWidth + 1 : null; }")
        f["chevron"] = {"whole": w.get("whole"), "painted": shown != hidden, "box": [round(b["x"]), round(b["y"]), round(b["width"]), round(b["height"])], "title_text_truncated": name_cut}
        if not (w.get("whole") and shown != hidden):
            r.fails.append(f"{f['_key']}: the switcher chevron is not painted whole ({f['chevron']})")

    def shoot(board_id: str, front: str | None, **kw):
        f = r.shoot(board_id, front, **kw)
        if f is not None:
            f["_key"] = f"{board_id}-{r.width}"
            phone_laws(f)
            if phone:
                chevron(f)
        return f

    def swipe(direction: int):
        """A touch swipe across the front window's body (CDP touch: start, 6 moves, end)."""
        y = 430
        x0, x1 = (340, 90) if direction > 0 else (150, 380)
        cdp = r.page.context.new_cdp_session(r.page)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y, "id": 1}]})
        for i in range(1, 7):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 + (x1 - x0) * i / 6, "y": y + i, "id": 1}]})
            r.page.wait_for_timeout(16)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        cdp.detach()
        settle(900)

    # ── C7-1 the frame: the Chair's Needs you, the frame and the content measured ──
    shoot("C7-1-the-frame", "Needs you")
    if not phone:
        # ── C7-1440 control: two windows, as C1 ratified (C7 changes nothing at 1440) ──
        ev("() => window.__cOpen.open('meeting:m-standup')")
        settle(2800)
        shoot("C7-9-control-two-windows", "Ledger cutover sync")
        ev("() => import('/src/desk/intelligenceAttention.ts').then((m) => m.publishAftercare({ meeting_id: 'm-standup', title: 'Ledger cutover sync', open_total: 2, decided_total: 1 }))")
        settle(1500)
        ev("(w) => window.__cOpen.focus(w)", "chair:capture")
        settle(800)
        shoot("C7-6a-aftercare-arrives", "Capture",
              checks={"the card sits in the Capture window's slot": ev("() => !!document.querySelector(\"[id='chair:capture'] [data-aftercare-slot] .ambient-aftercare\")")})
        return

    # ── C7-2 the swipe: Needs you -> Brief -> The week, and back ──
    swipe(+1)
    to1 = ev("() => window.__c7.current()")
    shoot("C7-2a-swipe-to-brief", "Brief", checks={"one swipe moves to the next window": to1 == "chair:brief"}, extra={"after_swipe": to1})
    swipe(+1)
    to2 = ev("() => window.__c7.current()")
    shoot("C7-2b-swipe-to-the-week", "The week", checks={"a second swipe moves to The week": to2 == "chair:week"}, extra={"after_swipe": to2})
    swipe(-1)
    back = ev("() => window.__c7.current()")
    print("swipe back", ev("() => window.__c7LastSwipe"), back, flush=True)
    if back != "chair:brief":
        r.fails.append(f"C7-2-{r.width}: a swipe back did not return to Brief ({back})")
    swipe(+1)

    # ── C7-3 two windows: a meeting window and Meetings, swiped between ──
    ev("() => window.__cOpen.surface('review-meetings')")
    settle(2800)
    ev("() => window.__cOpen.open('meeting:m-standup')")
    settle(2800)
    shoot("C7-3a-meeting-window", "Ledger cutover sync")
    swipe(-1)
    prev = ev("() => window.__c7.current()")
    shoot("C7-3b-swipe-to-meetings", "Meetings", checks={"a swipe back moves to Meetings": prev == "surface-meetings"}, extra={"after_swipe": prev})
    swipe(-1)
    prev2 = ev("() => window.__c7.current()")
    shoot("C7-3c-swipe-to-the-chair", "The week", checks={"past the first desk window the Chair's window returns": prev2 == "chair:week"}, extra={"after_swipe": prev2})

    # ── C7-4 the switcher: any open window in two taps ──
    r.tap(r.page.locator("[data-testid=c7-switcher]"), 700)
    f = shoot("C7-4a-switcher-open", None)
    if f is not None:
        rows = [x for m in f["menus"] for x in m["rows"]]
        for want in ("Needs you", "Brief", "The week", "Meetings", "Ledger cutover sync"):
            if not any(x.startswith(want) for x in rows):
                r.fails.append(f"C7-4a-{r.width}: the switcher does not list {want} ({rows})")
    r.pick_row("Needs you")
    taps_to = ev("() => window.__c7.current()")
    shoot("C7-4b-switcher-picked", "Needs you", checks={"two taps reach Needs you": taps_to == "chair:needs"}, extra={"taps": 2, "today_taps": "3 (Go > Chair > The week), the row at the end of a 48-row Go menu"})

    # ── C7-5 Go, grouped: Chair, Desk, Object, Window first ──
    r.tap(r.page.locator(".desk-verbbar [data-menu-id=go] button"), 700)
    f = shoot("C7-5a-go-grouped", None)
    if f is not None:
        rows = [x for m in f["menus"] for x in m["rows"]][:4]
        if [x.split(" ")[0] for x in rows] != ["Chair", "Desk", "Object", "Window"]:
            r.fails.append(f"C7-5a-{r.width}: Go does not lead with Chair, Desk, Object, Window ({rows})")
        f["go_rows"] = sum(len(m["rows"]) for m in f["menus"])
    r.open_sub("Object")
    shoot("C7-5b-go-object", None)
    r.escape()
    r.tap(r.page.locator(".desk-verbbar [data-menu-id=go] button"), 700)
    r.open_sub("Window")
    shoot("C7-5c-go-window", None)
    r.escape()

    # ── C7-6 aftercare (condition 1): arrival -> swipe away -> return; Capture stays in the ring; the card never floats ──
    r.close_all()
    ev("() => import('/src/desk/chair/chairWindows.ts').then((m) => m.openChairWindow('chair:week'))")
    settle(1200)
    ev("() => import('/src/desk/intelligenceAttention.ts').then((m) => m.publishAftercare({ meeting_id: 'm-standup', title: 'Ledger cutover sync', open_total: 2, decided_total: 1 }))")
    settle(1800)
    card_in_capture = "() => !!document.querySelector(\"[id='chair:capture'] [data-aftercare-slot] .ambient-aftercare\")"
    no_fixed = "() => !document.querySelector('.ambient-aftercare-fixed')"
    in_ring = "() => window.__c7.ring().some((w) => w.id === 'chair:capture')"
    shoot("C7-6a-aftercare-arrives", "Capture",
          checks={"the card sits in the Capture window's slot": ev(card_in_capture), "no fixed card over work": ev(no_fixed)})
    swipe(+1)
    away = ev("() => window.__c7.current()")
    shoot("C7-6b-aftercare-swipe-away", None,
          checks={"a swipe leaves Capture": away != "chair:capture", "no fixed card over work": ev(no_fixed),
                  "Capture stays in the ring": ev(in_ring)}, extra={"after_swipe": away})
    r.tap(r.page.locator("[data-testid=c7-switcher]"), 700)
    f = shoot("C7-6c-aftercare-switcher-lists-capture", None)
    if f is not None and not any(x.startswith("Capture") for m in f["menus"] for x in m["rows"]):
        r.fails.append(f"C7-6c-{r.width}: the switcher does not list Capture")
    r.escape()
    swipe(-1)
    back = ev("() => window.__c7.current()")
    shoot("C7-6d-aftercare-return", "Capture",
          checks={"a swipe back returns to Capture": back == "chair:capture", "the card is still in Capture's slot": ev(card_in_capture),
                  "no fixed card over work": ev(no_fixed)}, extra={"after_swipe": back})
    ev("() => import('/src/desk/intelligenceAttention.ts').then((m) => m.dismissAftercare())")
    settle(600)

    # ── C7-7 G5: the Meetings record footer at 393 (the egress chip on its own row) ──
    ev("() => window.__cOpen.surface('review-meetings')")
    settle(2500)
    r.tap(r.page.locator(".desk-window-shell[aria-label='Meetings'] :text('Vendor call')"), 1800)
    shoot("C7-7-g5-meetings-footer", "Meetings")
    # ── C7-8 a window's footer verbs own 44 px ──
    ev("() => window.__cOpen.open('meeting:m-standup')")
    settle(2500)
    shoot("C7-8-footer-verbs-44", "Ledger cutover sync")
    # Condition 6, the mutation proof on this real board: the Dock moved up 24 px over the footer verbs.
    ev("() => { const s = document.createElement('style'); s.id = 'c7-mutant'; s.textContent = '.desk-dock { transform: translateY(-24px) !important; }'; document.head.appendChild(s); }")
    settle(500)
    strict = ev(board.CHROME_OWNS)
    lenient = ev(board.TARGETS44)
    ev("() => document.getElementById('c7-mutant')?.remove()")
    settle(400)
    r.facts[f"_mutation_chrome_{r.width}"] = {"mutant": ".desk-dock translateY(-24px) over the meeting window's footer verbs (C7-8)",
                                              "c1_targets44": "CAUGHT" if lenient else "MISSED", "c1_caught": lenient[:4],
                                              "strict_chrome_fence": "CAUGHT" if strict else "MISSED", "strict_caught": strict[:4]}
    if not strict:
        r.fails.append(f"C7-8-{r.width}: the chrome fence MISSED the Dock over the footer verbs")
    print("mutation", r.facts[f"_mutation_chrome_{r.width}"], flush=True)

    # ── C7-10 the combined phone Send path (condition 2): Go ▸ Object ▸ Send to ▸ destination -> preview ──
    ev("(w) => window.__c5.docOf(w)", "pullout:meeting:m-standup")   # the window's read starts (as the menus do)
    settle(1200)
    r.tap(r.page.locator(".desk-verbbar [data-menu-id=go] button"), 700)
    r.open_sub("Object")
    f = shoot("C7-10a-go-object-send-to", None)
    if f is not None and not any(x.startswith("Send to") for m in f["menus"] for x in m["rows"]):
        r.fails.append(f"C7-10a-{r.width}: Go ▸ Object has no Send to")
    r.open_sub("Send to")
    f = shoot("C7-10b-go-object-send-to-rows", None)
    if f is not None and not any(x.startswith("Team updates") for m in f["menus"] for x in m["rows"]):
        r.fails.append(f"C7-10b-{r.width}: the nested Send to has no destination rows")
    r.pick_row("Slack #leads")
    settle(1800)
    W = "[id='pullout:meeting:m-standup']"
    shoot("C7-10c-go-send-to-preview", "Ledger cutover sync",
          whole=[f"{W} li.surface-ledger-row:has([data-testid=send-open]) .surface-primary", f"{W} [data-testid=send-open] [data-testid=send-preview-field] dd",
                 f"{W} [data-testid=send-open] [data-testid=send-verbs] .btn--primary"])


if __name__ == "__main__":
    sys.exit(board.main(SHOTS, "C7", "c5,c7", boards))
