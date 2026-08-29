"""HS-148-03 — the truthful mock rig.

Boots the real hub with the production bundle and photographs the SAME
menus under each `data-menu-glyphs` state (none=A Purist / all=B
Tribute-Plus / launcher=C Hybrid) by setting the localStorage override
BEFORE app boot. Every exhibit shot is the real product rendering real
entries — no drawings. Orchestrator-run; shots land in
assets/story-03-exhibit/.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-148-menu-glyphs/assets/story-03-exhibit"
TOKEN = "hs148-exhibit"


def main() -> int:
    sys.path.insert(0, str(REPO))
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    SHOTS.mkdir(parents=True, exist_ok=True)
    home = Path(os.environ["HOME"])  # caller supplies the isolated HOME
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
    )
    url = server.start()
    failures: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            def open_desk(variant: str, width: int = 1440, height: int = 900):
                ctx = browser.new_context(viewport={"width": width, "height": height})
                page = ctx.new_page()
                page.emulate_media(reduced_motion="reduce")
                page.add_init_script(
                    f"window.localStorage.setItem('hs:menu-glyphs', '{variant}');"
                )
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                chair = page.locator(".chair")
                chair.wait_for()
                if chair.evaluate("el => el.classList.contains('chair-first-value')"):
                    page.get_by_role("button", name="Continue later", exact=True).click()
                page.locator(".chair:not(.chair-first-value)").wait_for()
                # The desk chrome exists once the Chair settles.
                page.locator(".desk-menubar, .desk-verbbar").first.wait_for(timeout=15000)
                return ctx, page

            def shoot_bar_menu(page, title: str, shot: str, checks: list[str]):
                page.get_by_role("button", name=title, exact=True).first.click()
                menu = page.locator('nav[role="menu"]').last
                menu.wait_for(timeout=15000)
                for text in checks:
                    if not menu.get_by_text(text, exact=False).first.is_visible():
                        failures.append(f"{shot}: missing {text!r}")
                page.screenshot(path=str(SHOTS / shot), full_page=True)
                page.keyboard.press("Escape")

            # The Go triptych — the same menu, three truths.
            for variant, shot in (("none", "go-A-purist-1440.png"),
                                  ("launcher", "go-C-hybrid-1440.png"),
                                  ("all", "go-B-tribute-plus-1440.png")):
                ctx, page = open_desk(variant)
                try:
                    shoot_bar_menu(page, "Go", shot, ["Speak", "Settings"])
                finally:
                    ctx.close()

            # The verb-panel comparison: Object under C (pure) vs B (glyphed).
            for variant, shot in (("launcher", "object-C-pure-1440.png"),
                                  ("all", "object-B-glyphed-1440.png")):
                ctx, page = open_desk(variant)
                try:
                    shoot_bar_menu(page, "Object", shot, ["Open", "Delete"])
                finally:
                    ctx.close()

            # The Desk menu under B shows kind glyphs; under C stays pure.
            for variant, shot in (("launcher", "desk-C-pure-1440.png"),
                                  ("all", "desk-B-kinds-1440.png")):
                ctx, page = open_desk(variant)
                try:
                    shoot_bar_menu(page, "Desk", shot, ["New Note", "Open People"])
                finally:
                    ctx.close()

            # The launcher submenu under C wears glyphs (floor right-click → Launch »).
            ctx, page = open_desk("launcher")
            try:
                page.get_by_role("button", name="Floor", exact=True).first.click()
                floor = page.locator("canvas, .world-stage, .desk-floor").first
                floor.wait_for(timeout=15000)
                floor.click(button="right", position={"x": 500, "y": 500})
                menu = page.locator('nav[role="menu"]').last
                menu.wait_for(timeout=15000)
                menu.get_by_text("Launch", exact=False).first.hover()
                page.wait_for_timeout(400)
                page.keyboard.press("ArrowRight") if False else None
                sub = page.locator('nav[role="menu"]').last
                page.screenshot(path=str(SHOTS / "launch-sub-C-1440.png"), full_page=True)
                page.keyboard.press("Escape")
            except Exception as error:  # noqa: BLE001 — the floor may be view-dependent; record honestly
                failures.append(f"launch-sub-C: {type(error).__name__}: {error}")
            finally:
                ctx.close()

            # 393 — the lone narrow menu under the shipped default.
            ctx, page = open_desk("launcher", width=393, height=852)
            try:
                shoot_bar_menu(page, "Go", "go-C-hybrid-393.png", ["Speak"])
            finally:
                ctx.close()

            browser.close()
    finally:
        server.stop()
        reset_database()
    for f in failures:
        print(f"FINDING {f}")
    print(f"shots={SHOTS}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
