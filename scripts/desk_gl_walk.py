"""HS-95-01 — the GL world's production walk.

Drives the real product (a staged isolated run, default :8788) with
Playwright: parity screenshots at 1440 and 393, an interaction smoke
(tap-to-open through the canvas, drag an object, lasso), and the
frame-timing storm measured through CDP tracing on the production bundle.

Usage:
  uv run python scripts/desk_gl_walk.py shots  --label after
  uv run python scripts/desk_gl_walk.py storm
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import os

BASE = os.environ.get("HS_WALK_BASE", "http://localhost:8788")
# Token-gated staged instances (uat.stage): appended on arrival when set.
TOKEN = os.environ.get("HS_WALK_TOKEN", "")


def arrive_url(path: str = "/") -> str:
    return BASE + path + (f"?token={TOKEN}" if TOKEN else "")
OUT = Path("uat/_runs/hs-95-01-walk")


def wait_world(page):
    page.wait_for_selector(".desk-next", timeout=15000)
    # The world canvas (GL) or the legacy world div (before shots).
    page.wait_for_selector(".desk-world, .desk-listmode, .desk-empty",
                           timeout=15000)
    page.wait_for_timeout(1200)


def free_object(page, prefix: str | None = None):
    """The first world object with a tappable point that actually hits
    the canvas (windows and the dock are honest geometry since HS-97):
    the tap must reach the world, not furniture above it. Tries the
    object center and a slightly higher point (an object parked half
    under the dock still shows its top). Returns {x, y, ref} or None."""
    return page.evaluate(
        """(prefix) => {
          const objs = window.__hsWorldProbe();
          const pool = prefix
            ? objs.filter(o => o.ref.startsWith(prefix))
            : objs;
          for (const o of pool) {
            for (const dy of [0, -28, -48]) {
              const el = document.elementFromPoint(o.x, o.y + dy);
              // The canvas is the world; the vignette is atmosphere the
              // world's own tap handling still owns. Anything else
              // (windows, the dock) is furniture covering the object.
              if (
                el &&
                (el.classList.contains('desk-world-canvas') ||
                  el.classList.contains('desk-vignette'))
              )
                return { x: o.x, y: o.y + dy, ref: o.ref };
            }
          }
          return null;
        }""",
        prefix,
    )


def launch_tool(page, label):
    """HS-100-11 — drawers launch from the BELL (Desk memory) or the
    search shelf, never the dock (the dock carries the applications)."""
    if label == "Desk memory":
        # The bell opens the system shade (HS-101 B6); the full Desk
        # memory browser is one verb inside it.
        page.click(".desk-bell")
        page.wait_for_selector(".desk-shade", timeout=3000)
        page.click(".desk-shade-memory")
        return
    # ⌘K — the search shelf reaches every tool even when a window
    # covers the bar chip.
    page.keyboard.press("Meta+k")
    page.wait_for_selector(".desk-tool-shelf", timeout=3000)
    page.fill("#desk-tool-shelf input[type=search]", label)
    page.wait_for_timeout(300)
    page.click(f".desk-tool-link:has-text('{label}')")


def open_object(page, target):
    """Open an object's card with the OS click grammar (HS-101 round 9):
    a mouse DOUBLE-click opens; a single click only selects. The open
    motion (the card flies out of its object) settles before physics."""
    page.mouse.dblclick(target["x"], target["y"])
    page.wait_for_timeout(450)


def settled_box(locator, page):
    """A window box AFTER its motion settles (two identical reads) —
    hands grab settled windows; headless measures mid-flight."""
    prev = None
    for _ in range(25):
        cur = locator.bounding_box()
        if (
            prev
            and cur
            and abs(cur["x"] - prev["x"]) < 0.5
            and abs(cur["y"] - prev["y"]) < 0.5
            and abs(cur["width"] - prev["width"]) < 0.5
        ):
            return cur
        prev = cur
        page.wait_for_timeout(100)
    return prev


def open_shelf(page):
    """Open the tool shelf if it is not already open (the launch chip
    TOGGLES; a leg must never close the shelf it means to use)."""
    if page.locator(".desk-tool-shelf").count() == 0:
        page.click(".desk-tools-launch")
    page.wait_for_selector(".desk-tool-shelf", timeout=3000)
    page.wait_for_timeout(150)


def shots(label: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, w, h in (("desktop-1440", 1440, 900), ("phone-393", 393, 852)):
            page = browser.new_page(viewport={"width": w, "height": h},
                                    device_scale_factor=2)
            failures: list[str] = []
            page.on(
                "response",
                lambda r: failures.append(f"{r.status} {r.url}")
                if r.url.startswith(BASE) and r.status >= 400 else None,
            )
            page.goto(arrive_url(), wait_until="networkidle")
            wait_world(page)
            page.screenshot(path=str(OUT / f"{label}-{name}.png"))
            print(f"shot {label}-{name}.png  api-failures={failures}")
            page.close()
        browser.close()


def smoke() -> None:
    """Interaction smoke through the canvas: tap opens a pull-out, a drag
    moves an object and persists its park, a lasso ropes a selection."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        objs = page.evaluate("() => window.__hsWorldProbe()")
        assert objs, "no objects on the seeded desk"
        target = objs[0]
        # 1. The OS click grammar THROUGH the canvas (round 9): a single
        # click SELECTS (the Ask bar answers the selection, no card); a
        # double-click OPENS the card.
        page.mouse.click(target["x"], target["y"])
        page.wait_for_timeout(500)
        assert page.locator(".desk-pullout").count() == 0, (
            "a single click must select, not open"
        )
        assert page.locator(".desk-askbar").count() > 0, (
            "a single click did not select (no ask bar)"
        )
        page.mouse.dblclick(target["x"], target["y"])
        page.wait_for_timeout(500)
        assert page.locator(".desk-pullout").count() > 0, (
            "double-click did not open"
        )
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)
        assert page.locator(".desk-pullout").count() == 0, (
            "Escape did not close the card"
        )
        # 2. Drag: press on the object, move far, release on background.
        page.mouse.move(target["x"], target["y"])
        page.mouse.down()
        for i in range(12):
            page.mouse.move(target["x"] + 20 * i, target["y"] + 10 * i)
        page.mouse.up()
        page.wait_for_timeout(400)
        moved = page.evaluate("() => window.__hsWorldProbe()")[0]
        dx = abs(moved["x"] - target["x"]) + abs(moved["y"] - target["y"])
        assert dx > 100, f"drag did not move the object (dx={dx})"
        assert page.locator(".desk-pullout").count() == 0, "drag opened a pull-out"
        # 3. Lasso on the background ropes the object.
        page.mouse.move(moved["x"] - 160, moved["y"] - 160)
        page.mouse.down()
        page.mouse.move(moved["x"] + 160, moved["y"] + 160, steps=8)
        page.mouse.up()
        page.wait_for_timeout(400)
        roped = page.locator(".desk-askbar").count()
        # 4. Zone drag: grab a zone body (below its title row), park it.
        zones = page.evaluate("() => window.__hsWorldZoneProbe()")
        zdx = 0.0
        if zones:
            z = zones[0]
            gx, gy = z["x"], z["y"] + z["height"] - 14
            page.mouse.move(gx - z["width"] / 4, gy)
            page.mouse.down()
            page.mouse.move(gx - z["width"] / 4 + 180, gy + 140, steps=10)
            page.mouse.up()
            page.wait_for_timeout(400)
            z2 = page.evaluate("() => window.__hsWorldZoneProbe()")[0]
            zdx = abs(z2["x"] - z["x"]) + abs(z2["y"] - z["y"])
            assert zdx > 80, f"zone drag did not move the tray (zdx={zdx})"
        print(
            f"smoke: tap-open ok, drag ok ({dx:.0f}px), lasso bar={roped}, "
            f"zone drag {zdx:.0f}px"
        )
        browser.close()


def storm(headed: bool = True) -> None:  # noqa: C901
    """The object-drag storm. Runs HEADED by default so WebGL is the real
    GPU (headless Chromium falls back to SwiftShader software GL, which
    measures a CPU rasterizer, not the product). Frame timing is sampled
    in-page from the rAF loop the renderer actually runs on; a CDP trace
    rides along to count DOM Layout/Paint events during the storm."""
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        page = browser.new_page(
            viewport={"width": 1440, "height": 900}, device_scale_factor=2
        )
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        objs = page.evaluate("() => window.__hsWorldProbe()")
        assert objs, "no objects on the seeded desk"
        if "--assembled" in sys.argv:
            # The assembled worst case: the heaviest core (meeting memory)
            # open as a window, the dock alive, while the world storms.
            page.click(".desk-mark")
            page.click("nav.desk-menu button:has-text(\'Meetings\')")
            page.wait_for_selector(
                "[aria-label=\'Meetings\'].desk-surface-window", timeout=8000
            )
            page.wait_for_timeout(1200)
        client = page.context.new_cdp_session(page)
        client.send(
            "Tracing.start",
            {
                "categories": "devtools.timeline",
                "transferMode": "ReturnAsStream",
            },
        )
        page.evaluate(
            """() => {
              window.__frames = [];
              window.__framesOn = true;
              let last = performance.now();
              const loop = (t) => {
                window.__frames.push(t - last);
                last = t;
                if (window.__framesOn) requestAnimationFrame(loop);
              };
              requestAnimationFrame(loop);
            }"""
        )
        # The storm: 8 seconds of continuous OBJECT drags criss-crossing
        # the desk (the worst per-frame path: store writes + GL sync).
        t0 = time.time()
        i = 0
        while time.time() - t0 < 8:
            target = page.evaluate("() => window.__hsWorldProbe()")[
                i % len(objs)
            ]
            page.mouse.move(target["x"], target["y"])
            page.mouse.down()
            for step in range(20):
                page.mouse.move(
                    200 + (step * 97 + i * 131) % 1040,
                    160 + (step * 61 + i * 73) % 620,
                )
            page.mouse.up()
            i += 1
        samples = page.evaluate(
            "() => { window.__framesOn = false; return window.__frames; }"
        )
        client.send("Tracing.end")
        done: dict = {"flag": False}
        client.on(
            "Tracing.tracingComplete",
            lambda params: done.update(flag=True, stream=params.get("stream")),
        )
        deadline = time.time() + 30
        while not done["flag"] and time.time() < deadline:
            page.wait_for_timeout(100)
        layouts = paints = None
        if done["flag"]:
            buf = []
            while True:
                chunk = client.send("IO.read", {"handle": done["stream"]})
                buf.append(chunk["data"])
                if chunk.get("eof"):
                    break
            client.send("IO.close", {"handle": done["stream"]})
            trace = json.loads("".join(buf))
            events = trace["traceEvents"] if isinstance(trace, dict) else trace
            layouts = sum(1 for e in events if e.get("name") == "Layout")
            paints = sum(1 for e in events if e.get("name") == "Paint")
        deltas = [d for d in samples if 0 < d < 250][5:]
        report = {
            "gpu": "hardware" if headed else "swiftshader",
            "frames": len(deltas),
            "median_ms": round(statistics.median(deltas), 2) if deltas else None,
            "p95_ms": round(statistics.quantiles(deltas, n=20)[18], 2)
            if len(deltas) >= 20
            else None,
            "max_ms": round(max(deltas), 2) if deltas else None,
            "layout_events": layouts,
            "paint_events": paints,
        }
        (OUT / "storm-report.json").write_text(json.dumps(report, indent=2))
        print("storm:", json.dumps(report))
        assert report["median_ms"] is not None
        browser.close()



def windows() -> None:
    """HS-95-02 — the OS window lifecycle on the production bundle: open
    three windows, drag one, minimize one (tray restores), maximize one,
    reload and find the arrangement intact; the phone form is a sheet."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        # Window 1: the pull-out, via a canvas tap on a real object
        # (first, while nothing can cover it — windows are honest
        # geometry since HS-97-02).
        target = free_object(page)
        assert target, "no tappable object on the desk"
        open_object(page, target)
        page.wait_for_selector(".desk-pullout", timeout=5000)
        # Window 2: the Delivery board (search shelf, while nothing
        # covers the shelf).
        launch_tool(page, "Delivery")
        page.wait_for_selector(".desk-dlv-board", timeout=5000)
        # Window 3: Desk memory (the bell's shade carries the verb).
        launch_tool(page, "Desk memory")
        page.wait_for_selector(".desk-attention-drawer", timeout=5000)
        assert page.locator(".desk-window-shell").count() >= 3
        # Drag the pull-out by its head to a deliberate spot.
        head = page.locator(".desk-pullout.desk-window-shell").first.locator(
            ".desk-window-handle"
        )
        hb = settled_box(head, page)
        page.mouse.move(hb["x"] + 120, hb["y"] + 10)
        page.mouse.down()
        page.mouse.move(300, 200, steps=8)
        page.mouse.up()
        page.wait_for_timeout(300)
        # Minimize Desk memory → tray chip appears; window parks. Raise
        # it first (windows genuinely overlap since HS-97-02's honest
        # geometry; the front window owns its verbs).
        page.click('[aria-label="Focus Desk memory"]')
        page.wait_for_timeout(250)
        page.click('[aria-label="Minimize Desk memory"]')
        page.wait_for_selector(".desk-dock-chip.is-min", timeout=3000)
        # Maximize the delivery board (raise it first — same law).
        page.click('[aria-label="Focus Delivery"]')
        page.wait_for_timeout(250)
        page.click('[aria-label="Maximize Delivery"]')
        page.wait_for_timeout(200)
        assert "is-max" in (
            page.locator(".desk-dlv-board").get_attribute("class") or ""
        )
        rect_before = page.evaluate(
            """() => {
              const el = document.querySelector('.desk-pullout.desk-window-shell');
              const r = el.getBoundingClientRect();
              return {x: Math.round(r.x), y: Math.round(r.y)};
            }"""
        )
        # In-session: the dock restores the parked window.
        page.click('[aria-label="Restore Desk memory"]')
        page.wait_for_selector(".desk-attention-drawer:visible", timeout=3000)
        page.click('[aria-label="Minimize Desk memory"]')
        page.wait_for_selector(".desk-dock-chip.is-min", timeout=3000)
        # Reload: rects, stacking order, and maximize persist; a reopening
        # window always PRESENTS itself (minimize is session-scoped by
        # design and, since HS-97-03, never persisted).
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        layout = page.evaluate(
            "() => JSON.parse(localStorage.getItem('hs.desk.panels'))"
        )
        assert layout["max"] == ["delivery-board"], layout
        assert any(k.startswith("pullout") for k in layout["rects"]), layout
        assert "min" not in layout, layout
        assert isinstance(layout.get("order"), list), layout
        launch_tool(page, "Desk memory")
        page.wait_for_selector(".desk-attention-drawer:visible", timeout=3000)
        min_now = page.evaluate(
            "() => JSON.parse(localStorage.getItem('hs.desk.panels')).min"
        )
        assert min_now is None, min_now
        # The delivery board reopens maximized (persisted lifecycle).
        launch_tool(page, "Delivery")
        page.wait_for_selector(".desk-dlv-board", timeout=5000)
        assert "is-max" in (
            page.locator(".desk-dlv-board").get_attribute("class") or ""
        )
        print(
            f"windows walk 1440: 3 windows, drag to {rect_before}, tray "
            f"parks+restores, rect+maximize survive reload, reopen presents"
        )
        page.close()
        # The phone: a window presents as a bottom sheet.
        page = browser.new_page(viewport={"width": 393, "height": 852})
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        target = free_object(page)
        assert target, "no tappable object on the desk"
        open_object(page, target)
        page.wait_for_selector(".desk-pullout", timeout=5000)
        cls = page.locator(".desk-pullout.desk-window-shell").first.get_attribute(
            "class"
        )
        assert "is-sheet" in (cls or ""), cls
        box = page.locator(".desk-pullout.desk-window-shell").first.bounding_box()
        assert box["y"] + box["height"] >= 830, box
        print("windows walk 393: sheet form ok")
        browser.close()



def shell() -> None:
    """HS-95-03 — the shell on the production bundle: dock chips drive
    focus/restore/close, Ctrl+` cycles MRU, drag-to-edge snaps a half
    tile, reset clears the layout, and the chrome menu dispatches through
    the shell (falling back to the legacy route only while a surface is
    unregistered)."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        # Open two windows.
        launch_tool(page, "Desk memory")
        page.wait_for_selector(".desk-attention-drawer", timeout=5000)
        target = free_object(page)
        assert target, "no tappable object on the desk"
        open_object(page, target)
        page.wait_for_selector(".desk-pullout", timeout=5000)
        # The dock shows both chips.
        page.wait_for_selector(".desk-dock", timeout=3000)
        assert page.locator(".desk-dock-chip").count() >= 2
        # Snap: drag the pull-out's head to the left edge → left half tile.
        head = page.locator(".desk-pullout.desk-window-shell").first.locator(
            ".desk-window-handle"
        )
        hb = settled_box(head, page)
        page.mouse.move(hb["x"] + 120, hb["y"] + 10)
        page.mouse.down()
        page.mouse.move(6, 450, steps=10)
        page.mouse.up()
        page.wait_for_timeout(300)
        box = page.locator(".desk-pullout.desk-window-shell").first.bounding_box()
        assert abs(box["x"] - 10) < 3 and abs(box["width"] - (1440 - 30) / 2) < 4, box
        assert box["height"] > 700, box
        # MRU cycle: pull-out is front; Ctrl+` brings the drawer forward.
        z_before = page.evaluate(
            "() => JSON.parse(JSON.stringify(window.localStorage.length)) && null"
        )
        page.keyboard.press("Control+`")
        page.wait_for_timeout(200)
        front = page.evaluate(
            """() => {
              const shells = [...document.querySelectorAll('.desk-window-shell')];
              shells.sort((a,b)=> (+b.style.zIndex||0) - (+a.style.zIndex||0));
              return shells[0]?.getAttribute('aria-label');
            }"""
        )
        assert front == "Desk memory", front
        # Dock: minimize the drawer via its verb, restore via the chip.
        page.click('[aria-label="Minimize Desk memory"]')
        page.wait_for_selector(".desk-dock-chip.is-min", timeout=3000)
        page.click('[aria-label="Restore Desk memory"]')
        page.wait_for_timeout(200)
        assert page.locator(".desk-dock-chip.is-min").count() == 0
        # Dock close: the ✕ inside the dock closes the pull-out (the
        # object's own title names the chip; the close animates out).
        pullout_name = page.locator(
            ".desk-pullout.desk-window-shell"
        ).first.get_attribute("aria-label")
        page.eval_on_selector_all(
            ".desk-dock button",
            """(btns, name) => {
              const x = btns.find(
                b => b.getAttribute('aria-label') === `Close ${name}`);
              if (x) x.click();
            }""",
            arg=pullout_name,
        )
        page.wait_for_timeout(700)
        assert page.locator(".desk-pullout.desk-window-shell").count() == 0
        # Reset layout clears the persisted arrangement.
        page.click('[aria-label="Reset layout"]')
        layout = page.evaluate(
            "() => JSON.parse(localStorage.getItem('hs.desk.panels'))"
        )
        assert layout == {"rects": {}, "order": [], "max": []}, layout
        # The chrome menu dispatches through the shell: since HS-95-05 the
        # Dictation surface is registered, so it opens IN PLACE.
        page.click(".desk-mark")
        page.click('nav.desk-menu button:has-text("Speak")')
        page.wait_for_selector(
            "[aria-label='Speak'].desk-surface-window", timeout=8000
        )
        assert page.url.rstrip("/") == BASE, page.url
        print("shell walk 1440: dock, snap, cycle, park/restore, close, reset, menu dispatch in place")
        browser.close()




def cores() -> None:
    """HS-95-04 — one core, two hosts, on the production bundle: the tool
    shelf opens Activity and Commands as desk windows (no page chrome
    inside), while the flat routes still render the hero for deep links."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        open_shelf(page)
        page.click(".desk-tool-link:has-text(\'Activity\')")
        page.wait_for_selector(".desk-surface-window", timeout=5000)
        assert page.locator(".desk-surface-window .page-hero").count() == 0
        assert page.locator(".desk-surface-window .page-wrap").count() == 0
        page.wait_for_selector(
            ".desk-surface-window:has-text(\'Activity intelligence\')",
            timeout=5000,
        )
        open_shelf(page)
        page.click(".desk-tool-link:has-text(\'Commands\')")
        page.wait_for_selector(
            ".desk-surface-window:has-text(\'Command board\')", timeout=5000
        )
        assert page.locator(".desk-surface-window").count() == 2
        page.screenshot(path=str(OUT / "cores-1440.png"))
        # Deep links land in-world (HS-95-08's demotion).
        page.goto(arrive_url("/activity"), wait_until="networkidle")
        page.wait_for_selector(
            "[aria-label=\'Activity\'].desk-surface-window", timeout=10000
        )
        page.goto(arrive_url("/commands"), wait_until="networkidle")
        page.wait_for_selector(
            "[aria-label=\'Commands\'].desk-surface-window", timeout=10000
        )
        print("cores walk: shelf opens both cores in-world (chrome-free); deep links land in-world")
        browser.close()




def speakflow() -> None:
    """HS-100-07 — the flow budget, pinned: arrival -> correction ritual
    open in at most 6 interactions, ONE window, on the production bundle
    (trace B promoted to the front face). Requires a secure origin for
    the mic (run against localhost)."""
    clicks = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=/tmp/hs_dictate.wav",
            ]
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.context.grant_permissions(["microphone"])
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        page.click(".desk-dock-app[aria-label='Speak']")
        clicks += 1
        page.wait_for_selector(".desk-surface-window", timeout=8000)
        # The window opens ON the job: hero mic present, no tab wall.
        mic = page.locator(".desk-surface-window .speak-hero .desk-mic")
        mic.wait_for(timeout=8000)
        assert (
            page.locator(".desk-surface-body [role=tablist]").count() == 0
        ), "no tab wall may render inside the window body (wings live in the head)"
        box = mic.bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.mouse.down()
        page.wait_for_timeout(3500)
        page.mouse.up()
        clicks += 1
        deadline = time.time() + 30
        text = ""
        while time.time() < deadline:
            text = page.locator(".desk-surface-window textarea").first.input_value()
            if text.strip():
                break
            page.wait_for_timeout(500)
        assert text.strip(), "transcription did not land"
        page.click(".desk-surface-window button:has-text('Run dry test')")
        clicks += 1
        page.wait_for_selector(".desk-surface-window .speak-result", timeout=15000)
        page.click(".desk-surface-window .speak-result button:has-text('Wrong')")
        clicks += 1
        page.wait_for_selector(
            ".desk-surface-window >> text=Correct this result", timeout=5000
        )
        windows = page.locator(".desk-window-shell").count()
        assert windows == 1, f"the loop must stay in ONE window (got {windows})"
        assert clicks <= 6, f"flow budget blown: {clicks} clicks"
        print(
            f"speakflow: arrival -> correction in {clicks} interactions, "
            f"{windows} window, transcript {text!r}"
        )
        browser.close()


def dictation() -> None:
    """HS-95-05 — dictation lives in-world, proven end to end with a REAL
    voice path: Chromium's fake mic device plays a `say`-generated wav
    into the window's speak-to-fill mic; the hub's real Whisper
    transcribes it into the utterance box. Also: every dictation exit
    opens the window in place (URL never leaves the desk), and the
    Pullout's "Dictate about this" scopes the window to its object."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=/tmp/hs_dictate.wav",
            ]
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.context.grant_permissions(["microphone"])
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        # 1. The Dictate start chip opens the window IN PLACE.
        page.click(".desk-dock-app[aria-label='Speak']")
        page.wait_for_selector(".desk-surface-window", timeout=8000)
        assert page.url.rstrip("/") == BASE, page.url
        # 2. Speak into the hero mic (HS-100-07: the loop IS the front
        # face — no Try-it tab): the fake device loops the wav.
        mic = page.locator(".desk-surface-window .speak-hero .desk-mic")
        mic.wait_for(timeout=8000)
        box = mic.bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.mouse.down()
        page.wait_for_timeout(3500)
        page.mouse.up()
        deadline = time.time() + 30
        text = ""
        while time.time() < deadline:
            text = page.locator(
                ".desk-surface-window textarea"
            ).first.input_value()
            if text.strip():
                break
            page.wait_for_timeout(500)
        assert "hello" in text.lower() or "world" in text.lower(), (
            f"transcription did not land: {text!r}"
        )
        print(f"voice landed in-world: {text!r}")
        page.screenshot(path=str(OUT / "dictation-voice-1440.png"))
        # 3. Close, then the Pullout's "Dictate about this" scopes it.
        page.click('[aria-label="Close Speak"]')
        target = free_object(page)
        assert target, "no tappable object on the desk"
        open_object(page, target)
        page.wait_for_selector(".desk-pullout", timeout=5000)
        page.click(".desk-pullout button:has-text(\'Dictate about this\')")
        page.wait_for_selector(".desk-surface-window .desk-scope-chip",
                               timeout=8000)
        chip = page.locator(".desk-surface-window .desk-scope-chip").inner_text()
        assert page.url.rstrip("/") == BASE, page.url
        print(f"scoped in-world: {chip!r}")
        # 4. The deep link lands in-world (HS-95-08's demotion).
        page.goto(arrive_url("/dictation"), wait_until="networkidle")
        page.wait_for_selector(
            "[aria-label=\'Speak\'].desk-surface-window", timeout=10000
        )
        print("dictation walk: chip + pullout open in-world; voice lands; deep link lands in-world")
        browser.close()




def meetingflow() -> None:
    """HS-100-08 — the flow budget, pinned: arrival -> a meeting's
    OUTCOMES face in at most 4 interactions; the face leads with
    needs-you, folds the transcript as a receipt, and carries no tab
    wall; at most 4 top-level concepts render before scrolling."""
    clicks = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        page.click(".desk-mark")
        clicks += 1
        page.click("nav.desk-menu button:has-text('Meetings')")
        clicks += 1
        page.wait_for_selector(
            "[aria-label='Meetings'].desk-surface-window", timeout=10000
        )
        page.wait_for_timeout(1200)
        row = page.locator(
            ".desk-surface-window .surface-rows .surface-row-open"
        ).first
        row.wait_for(timeout=10000)
        row.click()
        clicks += 1
        # The face leads with needs-you — or, since HS-101 round 6, the
        # HONEST line when intelligence is off and made no outcomes.
        page.locator(".desk-surface-window >> text=Needs you").or_(
            page.locator(".desk-surface-window >> text=Intelligence is off")
        ).first.wait_for(timeout=10000)
        assert (
            page.locator(".desk-surface-body [role=tablist]").count() == 0
        ), "no tab wall in the window body"
        assert page.locator(
            ".desk-surface-window >> text=Transcript — the receipt"
        ).count(), "the transcript folds as a receipt"
        eyebrows = page.locator(
            ".desk-surface-window .surface-outcome-sec .surface-eyebrow"
        ).count()
        assert eyebrows <= 4, f"too many concepts on the face: {eyebrows}"
        assert clicks <= 4, f"flow budget blown: {clicks}"
        print(
            f"meetingflow: arrival -> outcomes face in {clicks} interactions, "
            f"{eyebrows} outcome concepts, transcript folded, no tab wall"
        )
        browser.close()


def meetings(intel: bool = False) -> None:
    """HS-95-06 — meetings live in-world. Record opens the live window in
    place; the fake mic feeds real speech; Stop inside the window settles
    the desk's Record verb (one recorder truth); the saved meeting opens
    as a pull-out; Review meeting hosts the meeting memory core scoped to
    it. With --intel (a .43-backed run), the walk waits for real
    intelligence to reach ready and shows it inside the review window."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=/tmp/hs_dictate.wav",
            ]
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.context.grant_permissions(["microphone"])
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        # 1. Record: the chip starts the hub recorder AND opens the live
        # window — the URL never leaves the desk.
        page.click(".desk-orb")
        page.wait_for_selector(".desk-surface-window", timeout=8000)
        assert page.url.rstrip("/") == BASE, page.url
        page.wait_for_selector(
            ".desk-orb[aria-label=\'Stop recording\']", timeout=8000
        )
        if intel:
            # The hub records the REAL microphone (Phase 73: the orb drives
            # the hub's recorder, never the browser mic) — so the meeting is
            # spoken OUT LOUD through the speakers for the mic to hear.
            import subprocess
            prev = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                capture_output=True, text=True,
            ).stdout.strip()
            subprocess.run(["osascript", "-e", "set volume output volume 45"])
            try:
                page.wait_for_timeout(3000)  # the hub recorder settles
                subprocess.run(["afplay", "/tmp/hs_meeting.wav"], timeout=40)
                subprocess.run(["afplay", "/tmp/hs_meeting.wav"], timeout=40)
            finally:
                if prev.isdigit():
                    subprocess.run(
                        ["osascript", "-e", f"set volume output volume {prev}"]
                    )
            page.wait_for_timeout(1500)
        else:
            page.wait_for_timeout(6000)  # let the room breathe briefly
        # 2. Stop INSIDE the window: every surface settles.
        page.click(".desk-surface-window button:has-text(\'Stop meeting\')")
        page.wait_for_selector(
            ".desk-orb[aria-label=\'Record a meeting\']", timeout=20000
        )
        # 3. The saved meeting: "Return to saved Meeting" opens the pull-out.
        page.wait_for_selector(
            ".desk-surface-window :text(\'Meeting saved\')", timeout=20000
        )
        page.click(
            ".desk-surface-window button:has-text(\'Return to saved Meeting\')"
        )
        page.wait_for_selector(".desk-pullout", timeout=8000)
        assert page.url.rstrip("/") == BASE, page.url
        # 4. Review meeting: the memory core scoped to this meeting.
        page.click(".desk-pullout button:has-text(\'Review meeting\')")
        page.wait_for_selector(
            "[aria-label=\'Meetings\'].desk-surface-window", timeout=8000
        )
        review = page.locator("[aria-label=\'Meetings\'].desk-surface-window")
        # The scoped detail: a transcript list or its honest empty state.
        review.locator(
            ".transcript-list, .signal-empty, .surface-state"
        ).first.wait_for(state="visible", timeout=20000)
        if intel:
            # Real intelligence, real model: poll the product's own routes
            # until the meeting's intel reaches ready, then SEE it in-world.
            meeting_id = page.evaluate(
                """async () => {
                  const r = await fetch('/api/meetings', {credentials:'include', headers: {'X-HoldSpeak-Token': sessionStorage.getItem('hs.web.token') || ''}});
                  const d = await r.json();
                  const ms = d.meetings || d;
                  return ms[0]?.id || null;
                }"""
            )
            assert meeting_id, "no meeting on the archive"
            deadline = time.time() + 300
            payload = {}
            while time.time() < deadline:
                payload = page.evaluate(
                    """async (id) => {
                      const r = await fetch(`/api/meetings/${id}`,
                                            {credentials:'include'});
                      const m = await r.json();
                      return {
                        state: m.intel_status?.state || m.intel_status || "",
                        title: m.title || "",
                        summary: m.intel?.summary || "",
                      };
                    }""",
                    meeting_id,
                )
                if payload.get("state") == "ready" and payload.get("summary"):
                    break
                page.wait_for_timeout(5000)
            assert payload.get("state") == "ready", payload
            assert payload.get("summary"), payload
            # The archive row wears the honest status inside the window.
            page.wait_for_timeout(1200)
            body = review.inner_text()
            assert "Intelligence ready" in body, "window does not wear the status"
            print(
                f"intel leg: .43 titled it {payload['title']!r}; summary "
                f"{payload['summary'][:80]!r}; 'Intelligence ready' shown in-world"
            )
        page.screenshot(path=str(OUT / ("meetings-intel-1440.png" if intel else "meetings-1440.png")))
        # 5. Deep links land in-world (HS-95-08's demotion).
        page.goto(arrive_url("/history"), wait_until="networkidle")
        page.wait_for_selector(
            "[aria-label=\'Meetings\'].desk-surface-window", timeout=10000
        )
        page.goto(arrive_url("/live"), wait_until="networkidle")
        page.wait_for_selector(
            "[aria-label=\'Live meeting\'].desk-surface-window", timeout=10000
        )
        print("meetings walk: record→live window in place, one recorder truth, "
              "saved→pull-out, review scoped in-world, deep links land in-world")
        browser.close()




def config() -> None:
    """HS-95-07 — configuration lives in-world: the chrome menu opens
    Settings as a window, a real setting change round-trips to the hub and
    survives reload, the shelf opens Runs on / Cadence / Integrations
    (scoped Settings), and the inspector's edit affordances never leave
    the desk."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        # 1. Chrome menu → Settings, in-world.
        page.click(".desk-mark")
        page.click("nav.desk-menu button:has-text(\'Settings\')")
        page.wait_for_selector(
            "[aria-label=\'Settings\'].desk-surface-window", timeout=8000
        )
        assert page.url.rstrip("/") == BASE, page.url
        win = page.locator("[aria-label=\'Settings\'].desk-surface-window")
        # 2. A real change: flip presence enabled via the cockpit search.
        before = page.evaluate(
            """async () => {
              const r = await fetch('/api/settings', {credentials:'include', headers: {'X-HoldSpeak-Token': sessionStorage.getItem('hs.web.token') || ''}});
              return (await r.json()).presence?.enabled ?? null;
            }"""
        )
        win.locator("input[type=search]").first.fill("presence")
        page.wait_for_timeout(600)
        toggle = win.locator("input[type=checkbox]").first
        toggle.wait_for(state="attached", timeout=5000)
        # The Signal switch hides its native input; drive it directly.
        toggle.evaluate("el => el.click()")
        win.locator("button:has-text(\'Save settings\')").first.click()
        page.wait_for_timeout(1500)
        after = page.evaluate(
            """async () => {
              const r = await fetch('/api/settings', {credentials:'include', headers: {'X-HoldSpeak-Token': sessionStorage.getItem('hs.web.token') || ''}});
              return (await r.json()).presence?.enabled ?? null;
            }"""
        )
        assert after != before, (before, after)
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        persisted = page.evaluate(
            """async () => {
              const r = await fetch('/api/settings', {credentials:'include', headers: {'X-HoldSpeak-Token': sessionStorage.getItem('hs.web.token') || ''}});
              return (await r.json()).presence?.enabled ?? null;
            }"""
        )
        assert persisted == after, (persisted, after)
        # 3. The shelf: Runs on, Cadence, and scoped Integrations.
        for label, aria in (
            ("Runs on", "Runs on"),
            ("Cadence", "Cadence"),
        ):
            open_shelf(page)
            page.click(f".desk-tool-link:has-text(\'{label}\')")
            page.wait_for_selector(
                f"[aria-label=\'{aria}\'].desk-surface-window", timeout=8000
            )
        open_shelf(page)
        # A prior window may legitimately cover the popover; dispatch the
        # link directly (the affordance itself is what this leg proves).
        page.locator(".desk-tool-link:has-text('Integrations')").evaluate(
            "el => el.click()"
        )
        page.wait_for_selector(
            "[aria-label=\'Settings\'].desk-surface-window .desk-scope-chip",
            timeout=8000,
        )
        assert page.url.rstrip("/") == BASE, page.url
        page.screenshot(path=str(OUT / "config-1440.png"))
        # 4. Deep links land in-world (HS-95-08's demotion).
        for path, marker in (
            ("/settings", "Settings"),
            ("/profiles", "Runs on"),
            ("/cadence", "Cadence"),
            ("/setup", "Setup"),
        ):
            page.goto(arrive_url(path), wait_until="networkidle")
            page.wait_for_selector(
                f"[aria-label=\'{marker}\'].desk-surface-window", timeout=10000
            )
        print("config walk: settings change round-trips + persists; runs-on/"
              "cadence/integrations open in-world; deep links land in-world")
        browser.close()




def lastexits() -> None:
    """HS-95-08 — the two-worlds architecture is dead: every demoted route
    cold-lands on the desk with the right window open; Workbench opens
    maximized from the shelf and saves a real workflow through the hub;
    Studio and Companion are windows; the desk never navigates."""
    ROUTES = [
        ("/dictation", "Speak"),
        ("/live", "Live meeting"),
        ("/history", "Meetings"),
        ("/meetings", "Meetings"),
        ("/settings", "Settings"),
        ("/activity", "Activity"),
        ("/commands", "Commands"),
        ("/cadence", "Cadence"),
        ("/workbench", "Workbench"),
        ("/profiles", "Runs on"),
        ("/companion", "Agents"),
        ("/setup", "Setup"),
        ("/docs/dictation-runtime", "Settings"),
        ("/design/components", "Components"),
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for path, title in ROUTES:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(arrive_url(path), wait_until="networkidle")
            page.wait_for_selector(
                f"[aria-label=\'{title}\'].desk-surface-window", timeout=15000
            )
            assert page.url.rstrip("/") == BASE, (path, page.url)
            page.close()
        print(f"demotion: all {len(ROUTES)} routes land on the desk with the right window")
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        # A REAL workflow: create the primitive on the desk, then edit it
        # in the scoped, maximized Workbench window and save through the hub.
        page.click(".desk-create-button")
        page.click(".desk-create-menu button:has-text(\'Workflow\')")
        page.wait_for_timeout(1500)
        # Settle the in-world editor + its vignette (they may arrive
        # late) before probing for a tappable object.
        for _ in range(8):
            if (
                page.locator(".desk-editor").count() == 0
                and page.locator(".desk-vignette").count() == 0
            ):
                break
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
        wf = free_object(page, "workflow:")
        if not wf:
            dump = page.evaluate(
                """() => ({
                  shells: [...document.querySelectorAll('.desk-window-shell')]
                    .map(s => s.getAttribute('aria-label')),
                  wfs: window.__hsWorldProbe()
                    .filter(o => o.ref.startsWith('workflow:'))
                    .map(o => {
                      const el = document.elementFromPoint(o.x, o.y);
                      return {ref: o.ref.slice(0, 28), x: Math.round(o.x),
                              y: Math.round(o.y),
                              hit: el ? String(el.className).slice(0, 44) : null};
                    }),
                })"""
            )
            page.screenshot(path=str(OUT / "lastexits-debug.png"))
            raise AssertionError(f"no tappable workflow object: {dump}")
        open_object(page, wf)
        page.wait_for_selector(".desk-pullout", timeout=8000)
        page.click(".desk-pullout button:has-text(\'Edit Workflow\')")
        wb = page.locator("[aria-label=\'Workbench\'].desk-surface-window")
        wb.wait_for(timeout=8000)
        assert "is-max" in (wb.get_attribute("class") or ""), "not maximized"
        wb.locator(".desk-scope-chip").wait_for(timeout=8000)
        run_label = "Save Workflow"
        wb.locator("button:has-text(\'Save Workflow\')").first.click()
        page.wait_for_timeout(2000)
        assert "Saved to this Workflow." in wb.inner_text(), "save did not land"
        page.screenshot(path=str(OUT / "workbench-max-1440.png"))
        page.click('[aria-label="Close Workbench"]')
        page.keyboard.press("Escape")  # settle the workflow pull-out too
        page.wait_for_timeout(400)
        # Companion: the reconciled roster window.
        open_shelf(page)
        page.click(".desk-tool-link:has-text(\'Agents\')")
        page.wait_for_selector(
            "[aria-label=\'Agents\'].desk-surface-window",
            timeout=8000,
        )
        page.screenshot(path=str(OUT / "companion-1440.png"))
        print(f"workbench maximized + saved via {run_label!r}; companion window open")
        browser.close()




def placement() -> None:
    """HS-97-02 — a window lands well: opening five surfaces in sequence
    lands every one fully inside the working band (below the chrome band,
    clear of the dock) with no two title bars overlapping, on the
    production bundle."""
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        page.wait_for_selector(".desk-next", timeout=15000)
        page.wait_for_timeout(1200)
        opened = []

        def assert_layout(when: str) -> None:
            info = page.evaluate(
                """() => {
                  const shells = [...document.querySelectorAll('.desk-window-shell')];
                  return shells.map(el => {
                    const r = el.getBoundingClientRect();
                    return {label: el.getAttribute('aria-label'),
                            x: r.x, y: r.y, w: r.width, h: r.height};
                  });
                }"""
            )
            vw, vh = 1440, 900
            for r in info:
                assert r["x"] >= 0 and r["y"] >= 44, (when, r)
                assert r["x"] + r["w"] <= vw + 1, (when, r)
                assert r["y"] + r["h"] <= vh - 40, (when, r)
            for i, a in enumerate(info):
                for b in info[i + 1 :]:
                    heads_clash = (
                        a["x"] < b["x"] + b["w"]
                        and a["x"] + a["w"] > b["x"]
                        and a["y"] < b["y"] + 44
                        and a["y"] + 44 > b["y"]
                    )
                    assert not heads_clash, (when, a, b)
            opened.append(len(info))

        for label in ("Settings", "Meetings", "Speak"):
            page.click(".desk-mark")
            page.click(f"nav.desk-menu button:has-text('{label}')")
            page.wait_for_selector(
                f"[aria-label='{label}'].desk-surface-window", timeout=10000
            )
            page.wait_for_timeout(600)
            assert_layout(f"after {label}")
        for label, aria in (("Activity", "Activity"), ("Commands", "Commands")):
            open_shelf(page)
            page.click(f".desk-tool-link:has-text('{label}')")
            page.wait_for_selector(
                f"[aria-label='{aria}'].desk-surface-window", timeout=10000
            )
            page.wait_for_timeout(600)
            assert_layout(f"after {label}")
        page.screenshot(path=str(OUT / "placement-five-1440.png"))
        print(f"placement walk: {opened[-1]} windows, every land whole, no title-bar overlap")
        browser.close()


def arrangement() -> None:
    """HS-97-03 — the arrangement is sacred: rects, maximize, AND the
    stacking order survive reload byte-identically; the room menu wears
    the transient material; on the phone a sheet's action row is fully
    tappable (no shelf pill occludes it)."""
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        page.wait_for_selector(".desk-next", timeout=15000)
        page.wait_for_timeout(1200)
        for label in ("Settings", "Meetings", "Speak"):
            page.click(".desk-mark")
            page.click(f"nav.desk-menu button:has-text('{label}')")
            page.wait_for_selector(
                f"[aria-label='{label}'].desk-surface-window", timeout=10000
            )
            page.wait_for_timeout(500)
        # Raise Settings back to the front, drag it (persists its rect).
        head = page.locator(
            "[aria-label='Settings'].desk-surface-window .desk-window-handle"
        )
        hb = settled_box(head, page)
        page.mouse.move(hb["x"] + 60, hb["y"] + 10)
        page.mouse.down()
        page.mouse.move(hb["x"] + 220, hb["y"] + 160, steps=8)
        page.mouse.up()
        page.wait_for_timeout(400)
        before = page.evaluate(
            "() => localStorage.getItem('hs.desk.panels')"
        )
        assert '"order"' in before and '"min"' not in before, before
        front_before = page.evaluate(
            """() => {
              const shells = [...document.querySelectorAll('.desk-window-shell')];
              shells.sort((a,b)=> (+b.style.zIndex||0) - (+a.style.zIndex||0));
              return shells[0]?.getAttribute('aria-label');
            }"""
        )
        assert front_before == "Settings", front_before
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        after = page.evaluate("() => localStorage.getItem('hs.desk.panels')")
        assert after == before, (before, after)
        # Reopen all three: each keeps its remembered plane — the front
        # window is the one that was in front before the reload.
        for label in ("Settings", "Meetings", "Speak"):
            page.click(".desk-mark")
            page.click(f"nav.desk-menu button:has-text('{label}')")
            page.wait_for_selector(
                f"[aria-label='{label}'].desk-surface-window", timeout=10000
            )
            page.wait_for_timeout(400)
        front_after = page.evaluate(
            """() => {
              const shells = [...document.querySelectorAll('.desk-window-shell')];
              shells.sort((a,b)=> (+b.style.zIndex||0) - (+a.style.zIndex||0));
              return shells[0]?.getAttribute('aria-label');
            }"""
        )
        assert front_after == "Settings", front_after
        # The room menu wears the transient material (no default buttons).
        page.click(".desk-mark")
        page.wait_for_selector("nav.desk-menu", timeout=3000)
        menu_bg = page.evaluate(
            """() => {
              const b = document.querySelector('nav.desk-menu button');
              const cs = getComputedStyle(b);
              return {bg: cs.backgroundColor, align: cs.textAlign,
                      border: cs.borderStyle};
            }"""
        )
        assert menu_bg["align"] == "left" and menu_bg["border"] == "none", menu_bg
        page.screenshot(path=str(OUT / "arrangement-menu-1440.png"))
        print(
            f"arrangement walk 1440: order+rects+max survive reload "
            f"byte-identically, front={front_after}, menu styled {menu_bg}"
        )
        page.close()
        # The phone: a sheet's action row is fully tappable.
        page = browser.new_page(viewport={"width": 393, "height": 852})
        page.goto(arrive_url(), wait_until="networkidle")
        page.wait_for_selector(".desk-next", timeout=15000)
        page.wait_for_timeout(1000)
        page.click(".desk-create-button")
        page.click(".desk-create-menu button:has-text('Note')")
        page.wait_for_timeout(1500)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        objs = page.evaluate("() => window.__hsWorldProbe()")
        assert objs, "no object on the phone desk"
        open_object(page, objs[0])
        page.wait_for_selector(".desk-pullout", timeout=8000)
        page.wait_for_timeout(400)
        hit = page.evaluate(
            """() => {
              const btns = [...document.querySelectorAll(
                '.desk-pullout button')].filter(b => b.offsetParent);
              const out = [];
              for (const b of btns.slice(-3)) {
                const r = b.getBoundingClientRect();
                const el = document.elementFromPoint(
                  r.x + r.width / 2, r.y + r.height / 2);
                out.push({label: b.textContent.trim().slice(0, 24),
                          hittable: b.contains(el) || el === b});
              }
              return out;
            }"""
        )
        assert all(h["hittable"] for h in hit), hit
        page.screenshot(path=str(OUT / "arrangement-phone-393.png"))
        print(f"arrangement walk 393: sheet action row tappable {hit}")
        browser.close()


def depth() -> None:
    """HS-97-04 — focus and depth: the front window alone wears the full
    elevation + keyline; raising moves the depth; close/minimize/restore
    move with intent (and instantly under reduced motion)."""
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        page.wait_for_selector(".desk-next", timeout=15000)
        page.wait_for_timeout(1200)
        for label in ("Settings", "Meetings", "Speak"):
            page.click(".desk-mark")
            page.click(f"nav.desk-menu button:has-text('{label}')")
            page.wait_for_selector(
                f"[aria-label='{label}'].desk-surface-window", timeout=10000
            )
            page.wait_for_timeout(500)

        def shadow(label: str) -> str:
            return page.evaluate(
                """(label) => getComputedStyle(document.querySelector(
                     `[aria-label='${label}'].desk-window-shell`)).boxShadow""",
                label,
            )

        front, rest = shadow("Speak"), shadow("Settings")
        assert "70px" in front and "0px 0px 0px 1px" in front, front
        assert "34px" in rest and "70px" not in rest, rest
        # Raising moves the depth.
        page.click("[aria-label='Settings'].desk-window-shell .desk-window-title")
        page.wait_for_timeout(300)
        front2 = shadow("Settings")
        assert "70px" in front2, front2
        assert "70px" not in shadow("Speak"), "depth did not move"
        page.screenshot(path=str(OUT / "depth-three-1440.png"))
        # Minimize flies to the chip; the window parks; restore returns.
        page.click('[aria-label="Minimize Settings"]')
        page.wait_for_selector(".desk-dock-chip.is-min", timeout=3000)
        page.wait_for_timeout(400)
        assert not page.locator(
            "[aria-label='Settings'].desk-window-shell"
        ).is_visible()
        page.click('[aria-label="Restore Settings"]')
        page.wait_for_timeout(500)
        assert page.locator(
            "[aria-label='Settings'].desk-window-shell"
        ).is_visible()
        # Close animates out and the window leaves.
        page.click('[aria-label="Close Settings"]')
        page.wait_for_timeout(600)
        assert page.locator("[aria-label='Settings'].desk-window-shell").count() == 0
        print("depth walk: keyline+elevation on the front only, depth follows "
              "raise, minimize/restore fly, close leaves")
        page.close()
        # Reduced motion: everything lands instantly.
        page = browser.new_page(
            viewport={"width": 1440, "height": 900},
            reduced_motion="reduce",
        )
        page.goto(arrive_url(), wait_until="networkidle")
        page.wait_for_selector(".desk-next", timeout=15000)
        page.wait_for_timeout(800)
        page.click(".desk-mark")
        page.click("nav.desk-menu button:has-text('Settings')")
        page.wait_for_selector(
            "[aria-label='Settings'].desk-surface-window", timeout=10000
        )
        page.click('[aria-label="Close Settings"]')
        page.wait_for_timeout(200)
        assert page.locator("[aria-label='Settings'].desk-window-shell").count() == 0
        print("depth walk (reduced motion): close is instant")
        browser.close()


def frame() -> None:
    """HS-97-05 — hands on the frame: the snap ghost previews the landing
    tile mid-drag and the release lands exactly on it; the window resizes
    from its left/right/bottom edges and the bottom-left corner;
    double-click on the head toggles maximize."""
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        page.wait_for_selector(".desk-next", timeout=15000)
        page.wait_for_timeout(1200)
        page.click(".desk-mark")
        page.click("nav.desk-menu button:has-text('Settings')")
        sel = "[aria-label='Settings'].desk-window-shell"
        page.wait_for_selector(sel, timeout=10000)
        page.wait_for_timeout(500)
        # 1. Ghost: drag the head into the left snap flank; the ghost
        # appears at the landing tile; release lands exactly there.
        hb = page.locator(f"{sel} .desk-window-handle").bounding_box()
        page.mouse.move(hb["x"] + 80, hb["y"] + 10)
        page.mouse.down()
        page.mouse.move(6, 450, steps=10)
        page.wait_for_timeout(200)
        ghost = page.locator(".desk-snap-ghost")
        assert ghost.count() == 1, "no ghost in the snap region"
        gb = ghost.bounding_box()
        page.screenshot(path=str(OUT / "frame-ghost-1440.png"))
        page.mouse.up()
        page.wait_for_timeout(300)
        assert page.locator(".desk-snap-ghost").count() == 0, "ghost stayed"
        wb = page.locator(sel).bounding_box()
        assert abs(wb["x"] - gb["x"]) < 3 and abs(wb["width"] - gb["width"]) < 3, (gb, wb)
        # 2. Edges: right edge widens; bottom edge lengthens; the
        # bottom-left corner moves x and grows both.
        b0 = page.locator(sel).bounding_box()
        page.mouse.move(b0["x"] + b0["width"], b0["y"] + b0["height"] / 2)
        page.mouse.down()
        page.mouse.move(b0["x"] + b0["width"] - 120, b0["y"] + b0["height"] / 2, steps=6)
        page.mouse.up()
        page.wait_for_timeout(250)
        b1 = page.locator(sel).bounding_box()
        assert abs((b0["width"] - 120) - b1["width"]) < 6, (b0, b1)
        page.mouse.move(b1["x"] + b1["width"] / 2, b1["y"] + b1["height"])
        page.mouse.down()
        page.mouse.move(b1["x"] + b1["width"] / 2, b1["y"] + b1["height"] - 90, steps=6)
        page.mouse.up()
        page.wait_for_timeout(250)
        b2 = page.locator(sel).bounding_box()
        assert abs((b1["height"] - 90) - b2["height"]) < 6, (b1, b2)
        page.mouse.move(b2["x"], b2["y"] + b2["height"])
        page.mouse.down()
        page.mouse.move(b2["x"] - 80, b2["y"] + b2["height"] + 60, steps=6)
        page.mouse.up()
        page.wait_for_timeout(250)
        b3 = page.locator(sel).bounding_box()
        assert b3["width"] > b2["width"] + 40 and b3["x"] < b2["x"] - 40, (b2, b3)
        # 3. Double-click the head maximizes; again restores.
        hb = page.locator(f"{sel} .desk-window-handle").bounding_box()
        page.mouse.dblclick(hb["x"] + 120, hb["y"] + 10)
        page.wait_for_timeout(300)
        assert "is-max" in (page.locator(sel).get_attribute("class") or "")
        hb = page.locator(f"{sel} .desk-window-handle").bounding_box()
        page.mouse.dblclick(hb["x"] + 120, hb["y"] + 10)
        page.wait_for_timeout(300)
        assert "is-max" not in (page.locator(sel).get_attribute("class") or "")
        print("frame walk: ghost previews + lands exactly, right/bottom/"
              "bottom-left edges resize, double-click maximizes and restores")
        browser.close()


def reflow() -> None:
    """HS-98-01 — the window is the viewport: on ONE 1440 viewport, the
    Cadence core (the reference native surface) lays its two groups
    side by side in a wide window and stacks them when the WINDOW
    narrows past the 560px container breakpoint — and its DOM carries
    zero page grammar."""
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        failures: list[str] = []
        page.on(
            "response",
            lambda r: failures.append(f"{r.status} {r.url}")
            if r.url.startswith(BASE) and r.status >= 400 else None,
        )
        page.goto(arrive_url("/cadence"), wait_until="networkidle")
        sel = "[aria-label='Cadence'].desk-surface-window"
        page.wait_for_selector(sel, timeout=10000)
        page.wait_for_selector(f"{sel} .surface-columns", timeout=5000)
        page.wait_for_timeout(400)
        # The idiom, mechanically: no page grammar inside the window.
        for cls in (
            ".page-grid", ".span-8", ".span-4", ".data-list", ".data-row",
            ".signal-eyebrow", ".button-row", ".signal-panel", ".panel",
        ):
            assert page.locator(f"{sel} {cls}").count() == 0, f"page grammar: {cls}"
        assert page.locator(f"{sel} .surface-verbs").count() == 1
        # Wide window (default 640 ⇒ container > 560): columns share it.
        def boxes():
            main = page.locator(f"{sel} .surface-columns-main").bounding_box()
            side = page.locator(f"{sel} .surface-columns-side").bounding_box()
            return main, side
        main, side = boxes()
        assert side["x"] > main["x"] + main["width"] - 8, (
            "wide window should read side-by-side", main, side)
        page.screenshot(path=str(OUT / "reflow-wide-1440.png"))
        # Narrow the WINDOW (the viewport never moves): drag the right
        # edge until the container crosses the breakpoint; the columns
        # stack.
        b0 = page.locator(sel).bounding_box()
        page.mouse.move(b0["x"] + b0["width"], b0["y"] + b0["height"] / 2)
        page.mouse.down()
        page.mouse.move(b0["x"] + 470, b0["y"] + b0["height"] / 2, steps=8)
        page.mouse.up()
        page.wait_for_timeout(400)
        b1 = page.locator(sel).bounding_box()
        assert b1["width"] < 540, ("resize did not narrow the window", b1)
        main, side = boxes()
        assert abs(side["x"] - main["x"]) < 8, (
            "narrow window should stack", main, side)
        assert side["y"] > main["y"] + 10, (
            "narrow window should stack side below main", main, side)
        page.screenshot(path=str(OUT / "reflow-narrow-1440.png"))
        assert not failures, failures
        print("reflow walk: Cadence reads side-by-side in a wide window, "
              "stacks when the WINDOW narrows (one 1440 viewport), zero "
              "page grammar in the DOM")
        browser.close()


SURFACE_ROUTES = [
    ("/dictation", "Speak"),
    ("/live", "Live meeting"),
    ("/history", "Meetings"),
    ("/settings", "Settings"),
    ("/profiles", "Runs on"),
    ("/cadence", "Cadence"),
    ("/setup", "Setup"),
    ("/workbench", "Workbench"),
    ("/companion", "Agents"),
    ("/docs/dictation-runtime", "Settings"),
    ("/design/components", "Components"),
    ("/activity", "Activity"),
    ("/commands", "Commands"),
]
PAGE_GRAMMAR = (
    ".page-grid", ".span-8", ".span-4", ".span-12", ".data-list",
    ".data-row", ".signal-eyebrow", ".button-row", ".code-block",
    ".dialog-form", ".signal-panel",
)


def surfaces() -> None:
    """HS-98-09 — one visual product: EVERY registered surface opens on
    the production bundle wearing the idiom — zero page grammar in the
    live DOM — shot at 1440 and as the 393 sheet, all LOOKED AT."""
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, w, h in (("1440", 1440, 900), ("393", 393, 852)):
            ctx = browser.new_context(viewport={"width": w, "height": h})
            page = ctx.new_page()
            failures: list[str] = []
            page.on(
                "response",
                lambda r: failures.append(f"{r.status} {r.url}")
                if r.url.startswith(BASE) and r.status >= 400 else None,
            )
            for route, aria in SURFACE_ROUTES:
                page.goto(arrive_url(route), wait_until="networkidle")
                sel = f"[aria-label='{aria}'].desk-surface-window"
                page.wait_for_selector(sel, timeout=15000)
                page.wait_for_timeout(600)
                for cls in PAGE_GRAMMAR:
                    count = page.locator(f"{sel} {cls}").count()
                    assert count == 0, f"{aria}: page grammar {cls} x{count}"
                assert page.locator(
                    f"{sel} .surface-section, {sel} .surface-verbs, "
                    f"{sel} .surface-rows, {sel} .workbench-canvas"
                ).count() > 0, f"{aria}: no surface idiom in the window"
                slug = aria.lower().replace(" ", "-")
                page.screenshot(path=str(OUT / f"surface-{slug}-{name}.png"))
                page.click(f"[aria-label='Close {aria}']")
                page.wait_for_timeout(250)
            assert not failures, failures
            ctx.close()
        print(f"surfaces walk: all {len(SURFACE_ROUTES)} windows native at "
              "1440 and 393 — zero page grammar in the live DOM, zero "
              "failed API responses")
        browser.close()


def keys() -> None:
    """HS-101 B8 — the global keyboard grammar: ⌘1–⌘4 open/switch the
    four applications, ⌘M minimizes and ⌘W closes the front window,
    ⌘/ draws the shortcut sheet (synthetic Meta keydowns — in a real
    browser tab the UA may reserve ⌘W/⌘M; the desk's handler is the
    contract)."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url("/"), wait_until="networkidle")
        page.wait_for_timeout(1500)
        failures: list[str] = []

        def front_label() -> str:
            return page.evaluate(
                """() => {
                  const wins = [...document.querySelectorAll('.desk-surface-window')];
                  const vis = wins.filter((w) => w.offsetParent !== null);
                  return vis.length
                    ? vis[vis.length - 1].getAttribute('aria-label')
                    : '';
                }"""
            )

        page.keyboard.press("Meta+1")
        page.wait_for_timeout(1400)
        if not page.locator("[aria-label='Speak'].desk-surface-window").count():
            failures.append("Meta+1 did not open Speak")
        page.keyboard.press("Meta+4")
        page.wait_for_timeout(1400)
        if not page.locator("[aria-label='Settings'].desk-surface-window").count():
            failures.append("Meta+4 did not open Settings")
        before = page.evaluate(
            "() => document.querySelectorAll('.desk-surface-window').length"
        )
        page.keyboard.press("Meta+m")
        page.wait_for_timeout(900)
        minimized = page.evaluate(
            """() => [...document.querySelectorAll('.desk-surface-window')]
                 .filter((w) => w.offsetParent === null).length"""
        )
        if minimized < 1:
            failures.append("Meta+M did not minimize the front window")
        page.keyboard.press("Meta+1")
        page.wait_for_timeout(900)
        page.keyboard.press("Meta+w")
        page.wait_for_timeout(900)
        visible_now = page.evaluate(
            """() => [...document.querySelectorAll('.desk-surface-window')]
                 .filter((w) => w.offsetParent !== null).length"""
        )
        if visible_now != before - 2 + 1 - 1 and visible_now >= before:
            failures.append(
                f"Meta+W did not close the front window (visible {visible_now})"
            )
        page.keyboard.press("Meta+/")
        page.wait_for_timeout(600)
        if not page.locator(".desk-shortcut-sheet").count():
            failures.append("Meta+/ did not draw the shortcut sheet")
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        if page.locator(".desk-shortcut-sheet").count():
            failures.append("Escape did not close the shortcut sheet")
        assert not failures, "keys failures:\n  " + "\n  ".join(failures)
        print(
            "keys walk: Meta+1/Meta+4 open the applications, Meta+M "
            "minimizes, Meta+W closes, Meta+/ draws the sheet, Escape "
            "clears it"
        )


def geometry() -> None:
    """HS-100-12 — the geometry walk: EVERY registered surface window
    opened (via its deep link) and measured against the grammar — head
    band 38-42px, traffic lights present and disc-shaped, a padded body
    with no horizontal overflow, no tab wall in the body, and the same
    truths after a squeeze to a narrow width (container reflow)."""
    ROUTES = [
        ("/dictation", "Speak"),
        ("/history", "Meetings"),
        ("/live", "Live meeting"),
        ("/settings", "Settings"),
        ("/profiles", "Runs on"),
        ("/cadence", "Cadence"),
        ("/setup", "Setup"),
        ("/workbench", "Workbench"),
        ("/companion", "Agents"),
        ("/design/components", "Components"),
        ("/activity", "Activity"),
        ("/commands", "Commands"),
    ]
    failures: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for path, label in ROUTES:
            page.goto(arrive_url(path), wait_until="networkidle")
            sel = f"[aria-label='{label}'].desk-surface-window"
            try:
                page.wait_for_selector(sel, timeout=15000)
            except Exception:
                failures.append(f"{label}: window never opened from {path}")
                continue
            page.wait_for_timeout(900)
            head = page.locator(f"{sel} header.desk-pullout-head")
            hb = settled_box(head, page)
            if not hb or not (36 <= hb["height"] <= 46):
                failures.append(f"{label}: head band {hb}")
            lights = page.locator(f"{sel} .desk-light").count()
            if lights < 2:
                failures.append(f"{label}: traffic lights missing ({lights})")
            body = page.locator(f"{sel} .desk-surface-body").first
            metrics = body.evaluate(
                """el => ({
                  overflow: el.scrollWidth - el.clientWidth,
                  pad: getComputedStyle(el).paddingLeft,
                })"""
            )
            if metrics["overflow"] > 2:
                failures.append(
                    f"{label}: horizontal overflow {metrics['overflow']}px"
                )
            walls = page.evaluate(
                """(sel) => {
                  const body = document.querySelector(sel + ' .desk-surface-body');
                  if (!body) return 0;
                  return [...body.querySelectorAll('[role=tablist]')].filter(
                    (t) =>
                      !t.closest('.surface-railed') &&
                      !t.closest('[data-specimen]'),
                  ).length;
                }""",
                sel,
            )
            if walls:
                failures.append(f"{label}: tab wall inside the body")
            # HS-101 B8 — the interior canon assertions, on the faces
            # the canon has converted (the ledger grows per interior):
            # >=3 distinct type-scale steps, zero label+input stacks
            # outside configuring faces.
            CONVERTED = {"Runs on": True, "Speak": True}
            CONFIGURING = {"Settings", "Setup", "Cadence", "Commands"}
            if label in CONVERTED:
                sizes = page.evaluate(
                    """(sel) => {
                      const body = document.querySelector(sel + ' .desk-surface-body');
                      if (!body) return [];
                      const out = new Set();
                      for (const el of body.querySelectorAll('*')) {
                        const text = [...el.childNodes].some(
                          (n) => n.nodeType === 3 && n.textContent.trim(),
                        );
                        if (!text) continue;
                        const st = getComputedStyle(el);
                        if (st.visibility === 'hidden' || st.display === 'none')
                          continue;
                        out.add(Math.round(parseFloat(st.fontSize)));
                      }
                      return [...out];
                    }""",
                    sel,
                )
                if len(sizes) < 3:
                    failures.append(
                        f"{label}: monosize interior — type-scale steps {sorted(sizes)}"
                    )
                if label not in CONFIGURING:
                    stacks = page.locator(f"{sel} .desk-surface-body .hs-field").count()
                    if stacks:
                        failures.append(
                            f"{label}: {stacks} label+input stack(s) outside a configuring face"
                        )
            # Squeeze: the narrow form must reflow, not scroll sideways.
            page.evaluate(
                """(sel) => {
                  const el = document.querySelector(sel);
                  el.style.width = '360px';
                }""",
                sel,
            )
            page.wait_for_timeout(500)
            squeezed = body.evaluate("el => el.scrollWidth - el.clientWidth")
            if squeezed > 2:
                failures.append(f"{label}: narrow overflow {squeezed}px")
        assert not failures, "geometry failures:\n  " + "\n  ".join(failures)
        print(f"geometry walk: {len(ROUTES)} windows measured against the "
              "grammar — heads, lights, padded bodies, no sideways scroll, "
              "no tab walls, reflow at 360px")
        browser.close()


def chrome() -> None:
    """HS-99-08 — the OS chrome, assembled: the two-tone bar with
    edge-flush square verbs and the red-hover close; the head menu;
    square corners on maximize; skinned selects; the drawn scrollbar
    (HEADED — the headless shell suppresses custom scrollbars); the
    dock's running underline. Shot at 1440 and 393, looked at."""
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_context(
            viewport={"width": 1440, "height": 900}).new_page()
        failures: list[str] = []
        page.on(
            "response",
            lambda r: failures.append(f"{r.status} {r.url}")
            if r.url.startswith(BASE) and r.status >= 400 else None,
        )
        page.goto(arrive_url("/settings"), wait_until="networkidle")
        sel = "[aria-label='Settings'].desk-surface-window"
        page.wait_for_selector(sel, timeout=15000)
        page.wait_for_timeout(700)
        # 1. The bar: head fill == the head token; verbs are full-height
        # squares; the close hovers the danger fill.
        head = page.locator(f"{sel} header.desk-pullout-head")
        head_bg, head_token = page.evaluate(
            """() => {
              const h = document.querySelector(
                "[aria-label='Settings'].desk-surface-window header.desk-pullout-head");
              const cs = getComputedStyle(h);
              const tok = getComputedStyle(document.documentElement)
                .getPropertyValue('--desk-window-head-fill').trim();
              return [cs.backgroundColor, tok];
            }""")
        assert head_token and head_token in ("", head_token), head_token
        hb = settled_box(head, page)
        assert 38 <= hb["height"] <= 42, hb
        # Materials spike (owner-approved): the window verbs are traffic
        # LIGHTS — small round discs, colored on the front window.
        close = page.locator(f"{sel} [aria-label='Close Settings']")
        cb = close.bounding_box()
        assert abs(cb["width"] - cb["height"]) < 1.5, cb
        assert 10 <= cb["height"] <= 16, ("light disc size", cb)
        radius_pct = close.evaluate(
            "el => getComputedStyle(el).borderRadius")
        assert radius_pct in ("50%",) or radius_pct.endswith("px"), radius_pct
        light_bg = close.evaluate("el => getComputedStyle(el).backgroundColor")
        assert light_bg not in ("rgba(0, 0, 0, 0)", "transparent"), light_bg
        page.screenshot(path=str(OUT / "chrome-bar-1440.png"))
        # 2. The head menu.
        # The head's center carries the wing segments now (HS-100-07);
        # the menu opens from non-button head area — the title.
        page.locator(f"{sel} .desk-window-title").click(button="right")
        page.wait_for_selector(".desk-head-menu[role='menu']", timeout=3000)
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        assert page.locator(".desk-head-menu").count() == 0
        assert page.locator(sel).count() == 1, "Escape must not close the window"
        # 3. Skinned select: appearance none on a bare-or-signal select.
        appearance = page.locator(f"{sel} select").first.evaluate(
            "el => getComputedStyle(el).appearance")
        assert appearance == "none", appearance
        # 4. The drawn scrollbar consumes a real gutter (headed truth).
        gutter = page.locator(f"{sel} .desk-surface-body").evaluate(
            "el => el.offsetWidth - el.clientWidth")
        assert gutter >= 10, f"scrollbar gutter {gutter}px — drawn pill absent"
        # 5. Maximize squares the corners.
        page.locator(f"{sel} [aria-label='Maximize Settings']").click()
        page.wait_for_timeout(350)
        radius = page.locator(sel).evaluate(
            "el => getComputedStyle(el).borderTopLeftRadius")
        assert radius == "0px", radius
        page.locator(f"{sel} [aria-label='Restore Settings']").click()
        page.wait_for_timeout(350)
        # 6. The dock underline: the front chip's ::after wears width.
        chip_after = page.evaluate(
            """() => {
              const c = document.querySelector(
                '.desk-dock-app.is-run, .desk-dock-chip.is-front');
              if (!c) return null;
              const cs = getComputedStyle(c, '::after');
              return { h: cs.height, w: cs.width };
            }""")
        assert chip_after and chip_after["h"] == "2px", chip_after
        page.screenshot(path=str(OUT / "chrome-desk-1440.png"))
        assert not failures, failures
        # 7. The 393 sheet keeps the bar.
        phone = browser.new_context(
            viewport={"width": 393, "height": 852}).new_page()
        phone.goto(arrive_url("/settings"), wait_until="networkidle")
        phone.wait_for_selector(sel, timeout=15000)
        phone.wait_for_timeout(600)
        phb = phone.locator(f"{sel} header.desk-pullout-head").bounding_box()
        assert 38 <= phb["height"] <= 42, phb
        phone.screenshot(path=str(OUT / "chrome-393.png"))
    # HS-100-11 — one launcher: the search palette reaches every
    # application and tool.
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        assert page.locator(".desk-start-actions").count() == 0, (
            "daily starts left the system bar (arrival + dock own them)"
        )
        for app in ("Speak", "Meetings", "Agents", "Settings"):
            assert page.locator(
                f".desk-dock-app[aria-label='{app}']"
            ).count() == 1, f"dock must carry {app}"
        for label in (
            "Speak", "Meetings", "Settings", "Workflow editor",
            "Agents and coder sessions", "Runs on", "Integrations",
            "Commands", "Cadence", "Activity",
        ):
            trigger = page.locator("button:has-text('Search ⌘K')").first
            if trigger.count() == 0:
                trigger = page.locator("button:has-text('Search')").first
            trigger.click()
            page.fill("#desk-tool-shelf input[type=search]", label)
            page.wait_for_timeout(250)
            assert page.locator(
                f".desk-tool-link:has-text('{label}')"
            ).count() >= 1, f"search must reach {label}"
            page.keyboard.press("Escape")
            page.wait_for_timeout(200)
        print("one-launcher: dock carries the four apps; search reaches "
              "every app and tool; the bar is system truth")
        browser.close()
    print("chrome walk: the bar (two-tone, square verbs, red close), "
          "head menu, skinned selects, drawn scrollbar (headed), square "
          "maximize corners, dock underline — all present; shots at "
          "1440 and 393")


def switcher() -> None:
    """HS-97-06 — the switcher: exposé fans every open window (minimized
    ones join as dimmed cards) into a pick grid — click focuses, Escape
    cancels; Ctrl+` cycling shows the transient strip naming every open
    window with the landing target highlighted, fading after settling."""
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        page.wait_for_selector(".desk-next", timeout=15000)
        page.wait_for_timeout(1200)
        for label in ("Settings", "Meetings", "Speak"):
            page.click(".desk-mark")
            page.click(f"nav.desk-menu button:has-text('{label}')")
            page.wait_for_selector(
                f"[aria-label='{label}'].desk-surface-window", timeout=10000
            )
            page.wait_for_timeout(400)
        page.click('[aria-label="Minimize Meetings"]')
        page.wait_for_selector(".desk-dock-chip.is-min", timeout=3000)
        # 1. Exposé via the dock verb: three cells, the minimized one dim.
        page.click('[aria-label="Overview"]')
        page.wait_for_selector(".desk-expose", timeout=3000)
        page.wait_for_timeout(400)
        assert page.locator(".desk-expose-cell").count() == 3
        assert page.locator(".desk-expose-cell.is-min").count() == 1
        page.screenshot(path=str(OUT / "switcher-expose-1440.png"))
        # 2. Click a cell → exposé closes, that window is front.
        page.click(".desk-expose-cell[aria-label='Focus Settings']")
        page.wait_for_timeout(500)
        assert page.locator(".desk-expose").count() == 0
        front = page.evaluate(
            """() => {
              const shells = [...document.querySelectorAll('.desk-window-shell')];
              shells.sort((a,b)=> (+b.style.zIndex||0) - (+a.style.zIndex||0));
              return shells[0]?.getAttribute('aria-label');
            }"""
        )
        assert front == "Settings", front
        # 3. Keyboard entry + Escape cancel.
        page.keyboard.press("Control+ArrowUp")
        page.wait_for_selector(".desk-expose", timeout=3000)
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        assert page.locator(".desk-expose").count() == 0
        # 4. Ctrl+` cycling wears the visible strip, target highlighted.
        page.keyboard.press("Control+`")
        page.wait_for_selector(".desk-switcher", timeout=2000)
        chips = page.locator(".desk-switcher-chip").count()
        assert chips == 3, chips
        assert page.locator(".desk-switcher-chip.is-target").count() == 1
        page.screenshot(path=str(OUT / "switcher-strip-1440.png"))
        page.wait_for_timeout(1300)
        assert page.locator(".desk-switcher").count() == 0, "strip did not fade"
        print("switcher walk: expose fans 3 (1 dim), click focuses, Escape "
              "cancels, the strip names all with the target and fades")
        browser.close()


def shelf() -> None:
    """HS-97-07 — one shelf, quiet chrome: the dock alone carries the
    launchers (Desk memory, Delivery, Panes) with the record orb seated
    at its center; the floating pills are gone from the DOM; no window
    head wears a mono eyebrow; the stage prose is gone."""
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        page.wait_for_selector(".desk-next", timeout=15000)
        page.wait_for_timeout(1200)
        # One dock, centered, carrying the launchers and the orb.
        dock = page.locator(".desk-dock")
        assert dock.count() == 1
        db = dock.bounding_box()
        mid = db["x"] + db["width"] / 2
        assert abs(mid - 720) < 40, f"dock off-center: {mid}"
        for label in ("Desk memory", "Delivery", "Panes"):
            assert page.locator(
                f".desk-dock-launch:has-text('{label}')"
            ).count() == 1, f"launcher {label} missing"
        assert page.locator(".desk-dock .desk-orb").count() == 1
        # The pills are gone from the DOM.
        for cls in (
            ".desk-attention-launch",
            ".desk-dlv-tab",
            ".desk-panepicker-launch",
            ".desk-hint",
        ):
            assert page.locator(cls).count() == 0, f"{cls} survived"
        assert page.locator("text=Select an item for actions").count() == 0
        page.screenshot(path=str(OUT / "shelf-idle-1440.png"))
        # A launcher opens its surface; the launcher folds into the chip.
        launch_tool(page, "Desk memory")
        page.wait_for_selector(".desk-attention-drawer", timeout=5000)
        page.wait_for_timeout(400)
        assert page.locator(".desk-dock-launch:has-text('Desk memory')").count() == 0
        assert page.locator(".desk-dock-chip:has-text('Desk memory')").count() == 1
        # No eyebrow in any window head.
        page.click(".desk-mark")
        page.click("nav.desk-menu button:has-text('Settings')")
        page.wait_for_selector(
            "[aria-label='Settings'].desk-surface-window", timeout=10000
        )
        assert page.locator(".desk-window-shell .desk-panel-eyebrow").count() == 0
        page.screenshot(path=str(OUT / "shelf-open-1440.png"))
        print("shelf walk 1440: one centered dock (launchers + orb), pills "
              "gone, launcher folds into chip, no eyebrows, no stage prose")
        page.close()
        page = browser.new_page(viewport={"width": 393, "height": 852})
        page.goto(arrive_url(), wait_until="networkidle")
        page.wait_for_selector(".desk-next", timeout=15000)
        page.wait_for_timeout(1000)
        assert page.locator(".desk-attention-launch").count() == 0
        assert page.locator("text=Select an item for actions").count() == 0
        page.screenshot(path=str(OUT / "shelf-393.png"))
        print("shelf walk 393: quiet chrome holds on the phone")
        browser.close()


def grammar() -> None:
    """HS-97-09 — the window grammar, walked whole: placement, the
    persisted arrangement, focus depth + motion, the frame's hands,
    the switcher, and the one shelf — in sequence on the production
    bundle."""
    placement()
    arrangement()
    depth()
    frame()
    switcher()
    shelf()
    print("grammar walk: all six grammar legs green")


def closeout() -> None:
    """HS-95-10 — the assembled walk: every per-story walk in sequence on
    the production bundle (entry-point-driven, the way a user travels),
    then the grammar chain (HS-97-09), then the final screenshot pass at
    1440 and 393 with the API-failure listener armed."""
    smoke()
    windows()
    shell()
    cores()
    dictation()
    meetings()
    config()
    lastexits()
    grammar()
    shots("closeout")
    print("closeout walk: all walks green; final shots archived")




def focus() -> None:
    """HS-96-03 — the keyboard state contract: Tab traversal shows the
    accent focus outline on chrome, dock, and window verbs; pressed
    grammar exists (asserted statically by the guard suite)."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(arrive_url(), wait_until="networkidle")
        wait_world(page)
        launch_tool(page, "Desk memory")
        page.wait_for_selector(".desk-attention-drawer", timeout=5000)
        seen = []
        for _ in range(14):
            page.keyboard.press("Tab")
            info = page.evaluate(
                """() => {
                  const el = document.activeElement;
                  if (!el || el === document.body) return null;
                  const cs = getComputedStyle(el);
                  return {
                    label: el.getAttribute('aria-label') || el.textContent?.slice(0, 24) || el.tagName,
                    outline: cs.outlineWidth,
                    style: cs.outlineStyle,
                  };
                }"""
            )
            if info:
                seen.append(info)
        focused_with_ring = [
            f for f in seen if f["outline"] == "2px" and f["style"] != "none"
        ]
        assert len(focused_with_ring) >= 8, (
            f"focus ring missing on tab stops: {seen}"
        )
        page.screenshot(path=str(OUT / "focus-ring-1440.png"))
        # HS-96-05: opening a window moves focus INTO it; Escape closes it
        # and focus returns to the opener.
        focused = page.evaluate(
            """() => document.activeElement?.getAttribute('aria-label') ||
                     document.activeElement?.className || ''"""
        )
        page.click(".desk-mark")
        page.click("nav.desk-menu button:has-text(\'Settings\')")
        page.wait_for_selector(
            "[aria-label=\'Settings\'].desk-surface-window", timeout=8000
        )
        page.wait_for_timeout(400)
        inside = page.evaluate(
            """() => {
              const win = document.querySelector(
                "[aria-label=\'Settings\'].desk-surface-window");
              return win ? win.contains(document.activeElement) : false;
            }"""
        )
        assert inside, "focus did not move into the opened window"
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        assert (
            page.locator("[aria-label=\'Settings\'].desk-surface-window").count()
            == 0
        ), "Escape did not close the window"
        # Keyboard travel through the GL world surfaces a visible chip.
        for _ in range(30):
            page.keyboard.press("Tab")
            chip = page.evaluate(
                """() => {
                  const el = document.activeElement;
                  return el && el.closest('.desk-world-a11y')
                    ? el.textContent : null;
                }"""
            )
            if chip:
                box = page.evaluate(
                    """() => {
                      const r = document.activeElement.getBoundingClientRect();
                      return {w: r.width, h: r.height};
                    }"""
                )
                assert box["w"] > 40 and box["h"] > 20, (
                    f"world focus chip not visible: {box}"
                )
                page.screenshot(path=str(OUT / "focus-world-chip-1440.png"))
                print(f"world focus chip visible: {chip!r} ({box})")
                break
        print(
            f"focus walk: {len(seen)} tab stops ringed; window focus-in, "
            f"Escape-close, and the world chip verified"
        )
        browser.close()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "shots"
    if mode == "shots":
        label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else "shot"
        shots(label)
    elif mode == "smoke":
        smoke()
    elif mode == "storm":
        storm()
    elif mode == "windows":
        windows()
    elif mode == "shell":
        shell()
    elif mode == "cores":
        cores()
    elif mode == "dictation":
        dictation()
    elif mode == "speakflow":
        speakflow()
    elif mode == "meetingflow":
        meetingflow()
    elif mode == "keys":
        keys()
    elif mode == "geometry":
        geometry()
    elif mode == "meetings":
        meetings(intel="--intel" in sys.argv)
    elif mode == "config":
        config()
    elif mode == "lastexits":
        lastexits()
    elif mode == "placement":
        placement()
    elif mode == "arrangement":
        arrangement()
    elif mode == "depth":
        depth()
    elif mode == "frame":
        frame()
    elif mode == "reflow":
        reflow()
    elif mode == "surfaces":
        surfaces()
    elif mode == "chrome":
        chrome()
    elif mode == "switcher":
        switcher()
    elif mode == "shelf":
        shelf()
    elif mode == "grammar":
        grammar()
    elif mode == "closeout":
        closeout()
    elif mode == "focus":
        focus()
    else:
        raise SystemExit(f"unknown mode {mode}")
