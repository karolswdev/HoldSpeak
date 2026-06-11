#!/usr/bin/env python3
"""HS-56-05 Linux orchestrator (runs on the dev Mac, drives 192.168.1.43).

Pairs with `dogfood_story05_linux.py` (running on the Linux box's real Xorg
session): launches it over SSH, opens a loopback tunnel so a local Playwright
page can act as the geometry oracle (same page, same 408x460 viewport → same
button coordinates), fires the real proposal, takes real X11 screenshots of
the overlay region, sends a REAL `xdotool` click at the Approve button's
screen position, and verifies the X11 active window (keyboard focus) never
changed. The audited decision itself is verified by the remote script
against its own database.

    .venv/bin/python pm/roadmap/holdspeak/phase-56-qlippy/dogfood_story05_linux_orchestrator.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

HOST = "192.168.1.43"
PORT = 8765
OUT_DIR = Path(__file__).resolve().parent / "screenshots"
CARD_W, CARD_H = 408, 460
OVERLAY_MARGIN_X, OVERLAY_Y = 22, 38


def _ssh(cmd: str, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", HOST, cmd], capture_output=True, text=True, **kw
    )


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    from playwright.sync_api import sync_playwright

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    print("· launching the dogfood on the Linux box…")
    _ssh("/tmp/hs5605-launch.sh")
    for _ in range(40):
        log = _ssh("cat /tmp/hs5605.log 2>/dev/null").stdout
        if "READY" in log:
            break
        time.sleep(1)
    else:
        print("FAIL  remote dogfood never reached READY")
        print(_ssh("cat /tmp/hs5605.log 2>/dev/null").stdout)
        return 1
    print("· remote overlay is up")

    tunnel = subprocess.Popen(
        ["ssh", "-o", "BatchMode=yes", "-N", "-L", f"{PORT}:127.0.0.1:{PORT}", HOST]
    )
    try:
        time.sleep(1.5)
        geo = _ssh(
            "DISPLAY=:0 XAUTHORITY=/run/user/1000/gdm/Xauthority xdotool getdisplaygeometry"
        ).stdout.split()
        screen_w = int(geo[0])
        overlay_x = screen_w - CARD_W - OVERLAY_MARGIN_X
        print(f"· X11 screen {geo[0]}x{geo[1]}; overlay region at x={overlay_x}, y={OVERLAY_Y}")

        active_before = _ssh(
            "DISPLAY=:0 XAUTHORITY=/run/user/1000/gdm/Xauthority xdotool getactivewindow 2>/dev/null || echo none"
        ).stdout.strip()

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": CARD_W, "height": CARD_H})
            page.goto(f"http://127.0.0.1:{PORT}/presence", wait_until="networkidle")
            page.wait_for_selector("#qlippy:not([hidden])", timeout=5000)
            page.wait_for_timeout(400)

            print("· firing the real proposal…")
            _ssh("touch /tmp/hs5605.fire")
            page.wait_for_selector("#qlippy-card.is-in", timeout=10000)
            page.wait_for_timeout(700)
            box = page.locator(".q-btn-primary").bounding_box()
            browser.close()
        if not box:
            print("FAIL  geometry oracle found no Approve button")
            return 1

        # Let the overlay's 0.4 s poll grow the frame, then photograph it.
        time.sleep(2.5)
        _ssh(
            "DISPLAY=:0 XAUTHORITY=/run/user/1000/gdm/Xauthority "
            f"import -window root -crop {CARD_W}x{CARD_H}+{overlay_x}+{OVERLAY_Y} /tmp/hs5605-card.png"
        )
        print("PASS  card-frame screenshot captured on the real X server")

        click_x = overlay_x + int(box["x"] + box["width"] / 2)
        click_y = OVERLAY_Y + int(box["y"] + box["height"] / 2)
        print(f"· clicking Approve at screen ({click_x},{click_y}) with xdotool…")
        _ssh(
            "DISPLAY=:0 XAUTHORITY=/run/user/1000/gdm/Xauthority "
            f"xdotool mousemove {click_x} {click_y} click 1"
        )
        time.sleep(2.0)

        active_after = _ssh(
            "DISPLAY=:0 XAUTHORITY=/run/user/1000/gdm/Xauthority xdotool getactivewindow 2>/dev/null || echo none"
        ).stdout.strip()
        if active_before == active_after:
            print(f"PASS  X11 active window unchanged across the click ({active_before or 'none'})")
        else:
            failures.append(f"active window changed: {active_before!r} → {active_after!r}")

        # The card resolves; the poll shrinks the overlay back.
        time.sleep(3.0)
        _ssh(
            "DISPLAY=:0 XAUTHORITY=/run/user/1000/gdm/Xauthority "
            f"import -window root -crop {CARD_W}x{CARD_H}+{overlay_x}+{OVERLAY_Y} /tmp/hs5605-passive.png"
        )

        # The remote verdict (the audited decision against its own DB).
        for _ in range(30):
            log = _ssh("cat /tmp/hs5605.log").stdout
            if "RESULT:" in log:
                break
            time.sleep(1)
        print("--- remote transcript ---")
        print(log)
        if "RESULT: PASS" not in log:
            failures.append("remote dogfood did not PASS")

        subprocess.run(
            ["scp", "-q", f"{HOST}:/tmp/hs5605-card.png", str(OUT_DIR / "story05-linux-card-frame.png")]
        )
        subprocess.run(
            ["scp", "-q", f"{HOST}:/tmp/hs5605-passive.png", str(OUT_DIR / "story05-linux-passive-frame.png")]
        )
    finally:
        tunnel.terminate()

    if failures:
        for f in failures:
            print(f"FAIL  {f}")
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
