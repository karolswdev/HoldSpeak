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

    def phone_laws(f: dict | None) -> None:
        if f is None or not phone:
            return
        px = frame_px(f)
        f["frame_px"] = px
        if px > FRAME_MAX:
            r.fails.append(f"{f['_key']}: the frame is {px} px (> {FRAME_MAX})")
        if (f.get("content_px") or 0) < CONTENT_MIN:
            r.fails.append(f"{f['_key']}: the front window's content is {f.get('content_px')} px (< {CONTENT_MIN})")

    def shoot(board_id: str, front: str | None, **kw):
        f = r.shoot(board_id, front, **kw)
        if f is not None:
            f["_key"] = f"{board_id}-{r.width}"
            phone_laws(f)
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
        shoot("C7-6-aftercare-opens-capture", "Capture",
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

    # ── C7-6 aftercare: an arriving card opens Capture; it never floats over work ──
    ev("() => import('/src/desk/chair/chairWindows.ts').then((m) => m.openChairWindow('chair:week'))")
    settle(1200)
    ev("() => import('/src/desk/intelligenceAttention.ts').then((m) => m.publishAftercare({ meeting_id: 'm-standup', title: 'Ledger cutover sync', open_total: 2, decided_total: 1 }))")
    settle(1800)
    shoot("C7-6-aftercare-opens-capture", "Capture",
          checks={"the card sits in the Capture window's slot": ev("() => !!document.querySelector(\"[id='chair:capture'] [data-aftercare-slot] .ambient-aftercare\")"),
                  "no fixed card over work": not ev("() => !!document.querySelector('.ambient-aftercare-fixed')")})
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


if __name__ == "__main__":
    sys.exit(board.main(SHOTS, "C7", "c7", boards))
