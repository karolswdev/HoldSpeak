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

BASE = "http://localhost:8788"
OUT = Path("uat/_runs/hs-95-01-walk")


def wait_world(page):
    page.wait_for_selector(".desk-next", timeout=15000)
    # The world canvas (GL) or the legacy world div (before shots).
    page.wait_for_selector(".desk-world, .desk-listmode, .desk-empty",
                           timeout=15000)
    page.wait_for_timeout(1200)


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
            page.goto(BASE + "/", wait_until="networkidle")
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
        page.goto(BASE + "/", wait_until="networkidle")
        wait_world(page)
        objs = page.evaluate("() => window.__hsWorldProbe()")
        assert objs, "no objects on the seeded desk"
        target = objs[0]
        # 1. Tap-to-open THROUGH the canvas at the rendered position.
        page.mouse.click(target["x"], target["y"])
        page.wait_for_timeout(500)
        assert page.locator(".desk-pullout").count() > 0, "tap did not open"
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
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


def storm(headed: bool = True) -> None:
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
        page.goto(BASE + "/", wait_until="networkidle")
        wait_world(page)
        objs = page.evaluate("() => window.__hsWorldProbe()")
        assert objs, "no objects on the seeded desk"
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
        page.goto(BASE + "/", wait_until="networkidle")
        wait_world(page)
        # Window 1: Desk memory (attention drawer).
        page.click(".desk-attention-launch")
        page.wait_for_selector(".desk-attention-drawer", timeout=5000)
        # Window 2: the Delivery board tab.
        page.click(".desk-dlv-tab")
        page.wait_for_selector(".desk-dlv-board", timeout=5000)
        # Window 3: the pull-out, via a canvas tap on a real object.
        target = page.evaluate("() => window.__hsWorldProbe()")[0]
        page.mouse.click(target["x"], target["y"])
        page.wait_for_selector(".desk-pullout", timeout=5000)
        assert page.locator(".desk-window-shell").count() >= 3
        # Drag the pull-out by its head to a deliberate spot.
        head = page.locator(".desk-pullout.desk-window-shell").first.locator(
            ".desk-window-handle"
        )
        hb = head.bounding_box()
        page.mouse.move(hb["x"] + 40, hb["y"] + 10)
        page.mouse.down()
        page.mouse.move(300, 200, steps=8)
        page.mouse.up()
        page.wait_for_timeout(300)
        # Minimize Desk memory → tray chip appears; window parks.
        page.click('[aria-label="Minimize Desk memory"]')
        page.wait_for_selector(".desk-dock-chip.is-min", timeout=3000)
        # Maximize the delivery board.
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
        # Reload: rects and maximize persist; a reopening window always
        # PRESENTS itself (minimize is session-scoped by design).
        page.reload(wait_until="networkidle")
        wait_world(page)
        layout = page.evaluate(
            "() => JSON.parse(localStorage.getItem('hs.desk.panels'))"
        )
        assert layout["max"] == ["delivery-board"], layout
        assert "pullout" in layout["rects"], layout
        page.click(".desk-attention-launch")
        page.wait_for_selector(".desk-attention-drawer:visible", timeout=3000)
        min_now = page.evaluate(
            "() => JSON.parse(localStorage.getItem('hs.desk.panels')).min"
        )
        assert min_now == [], min_now
        # The delivery board reopens maximized (persisted lifecycle).
        page.click(".desk-dlv-tab")
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
        page.goto(BASE + "/", wait_until="networkidle")
        wait_world(page)
        target = page.evaluate("() => window.__hsWorldProbe()")[0]
        page.mouse.click(target["x"], target["y"])
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
        page.goto(BASE + "/", wait_until="networkidle")
        wait_world(page)
        # Open two windows.
        page.click(".desk-attention-launch")
        page.wait_for_selector(".desk-attention-drawer", timeout=5000)
        target = page.evaluate("() => window.__hsWorldProbe()")[0]
        page.mouse.click(target["x"], target["y"])
        page.wait_for_selector(".desk-pullout", timeout=5000)
        # The dock shows both chips.
        page.wait_for_selector(".desk-dock", timeout=3000)
        assert page.locator(".desk-dock-chip").count() >= 2
        # Snap: drag the pull-out's head to the left edge → left half tile.
        head = page.locator(".desk-pullout.desk-window-shell").first.locator(
            ".desk-window-handle"
        )
        hb = head.bounding_box()
        page.mouse.move(hb["x"] + 40, hb["y"] + 10)
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
        # Dock close: the ✕ inside the dock closes the pull-out.
        page.eval_on_selector_all(
            ".desk-dock button",
            """(btns) => {
              const x = btns.find(b => b.getAttribute('aria-label') === 'Close Untitled meeting');
              if (x) x.click();
            }""",
        )
        page.wait_for_timeout(300)
        assert page.locator(".desk-pullout.desk-window-shell").count() == 0
        # Reset layout clears the persisted arrangement.
        page.click('[aria-label="Reset layout"]')
        layout = page.evaluate(
            "() => JSON.parse(localStorage.getItem('hs.desk.panels'))"
        )
        assert layout == {"rects": {}, "min": [], "max": []}, layout
        # The chrome menu dispatches through the shell; unregistered
        # surfaces fall back to the legacy route (retired in HS-95-08).
        page.click(".desk-mark")
        page.click('nav.desk-menu button:has-text("Dictation")')
        page.wait_for_url("**/dictation*", timeout=5000)
        print("shell walk 1440: dock, snap, cycle, park/restore, close, reset, menu dispatch")
        browser.close()




def cores() -> None:
    """HS-95-04 — one core, two hosts, on the production bundle: the tool
    shelf opens Activity and Commands as desk windows (no page chrome
    inside), while the flat routes still render the hero for deep links."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE + "/", wait_until="networkidle")
        wait_world(page)
        page.click(".desk-tools-launch")
        page.click(".desk-tool-link:has-text(\'Activity\')")
        page.wait_for_selector(".desk-surface-window", timeout=5000)
        assert page.locator(".desk-surface-window .page-hero").count() == 0
        assert page.locator(".desk-surface-window .page-wrap").count() == 0
        page.wait_for_selector(
            ".desk-surface-window:has-text(\'Activity intelligence\')",
            timeout=5000,
        )
        page.click(".desk-tools-launch")
        page.click(".desk-tool-link:has-text(\'Commands\')")
        page.wait_for_selector(
            ".desk-surface-window:has-text(\'Command board\')", timeout=5000
        )
        assert page.locator(".desk-surface-window").count() == 2
        page.screenshot(path=str(OUT / "cores-1440.png"))
        # The flat routes keep their chrome for deep links.
        page.goto(BASE + "/activity", wait_until="networkidle")
        page.wait_for_selector(".page-hero:has-text(\'Activity\')", timeout=5000)
        page.goto(BASE + "/commands", wait_until="networkidle")
        page.wait_for_selector(".page-hero:has-text(\'Commands\')", timeout=5000)
        print("cores walk: shelf opens both cores in-world (chrome-free); flat routes keep the hero")
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
        page.goto(BASE + "/", wait_until="networkidle")
        wait_world(page)
        # 1. The Dictate start chip opens the window IN PLACE.
        page.click(".desk-start-action:has-text(\'Dictate\')")
        page.wait_for_selector(".desk-surface-window", timeout=8000)
        assert page.url.rstrip("/") == BASE, page.url
        # 2. Speak into the utterance mic (hold-to-talk): the fake device
        # loops the wav; hold long enough to cover the phrase.
        page.click("text=Try it")
        mic = page.locator(".desk-surface-window .desk-mic-row .desk-mic")
        mic.wait_for(timeout=5000)
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
        page.click('[aria-label="Close Dictation"]')
        target = page.evaluate("() => window.__hsWorldProbe()")[0]
        page.mouse.click(target["x"], target["y"])
        page.wait_for_selector(".desk-pullout", timeout=5000)
        page.click(".desk-pullout button:has-text(\'Dictate about this\')")
        page.wait_for_selector(".desk-surface-window .desk-scope-chip",
                               timeout=8000)
        chip = page.locator(".desk-surface-window .desk-scope-chip").inner_text()
        assert page.url.rstrip("/") == BASE, page.url
        print(f"scoped in-world: {chip!r}")
        # 4. The flat route still answers for deep links.
        page.goto(BASE + "/dictation", wait_until="networkidle")
        page.wait_for_selector(".page-hero:has-text(\'Dictation\')", timeout=5000)
        print("dictation walk: chip + pullout open in-world; voice lands; flat route lives")
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
    else:
        raise SystemExit(f"unknown mode {mode}")
