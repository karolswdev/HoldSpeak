"""HS-85-04 — mesh liveness on every surface (Playwright, real app, scratch DB).

The surfaces show LIVENESS, not existence: the /profiles card wears the mesh
state; the desk rail's models door dims an offline mesh model and names it in
the title; the settings picker labels the mesh option and the badge wears
`⇄ mesh · <node>`. Shot live AND offline, claims asserted.
"""
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from playwright.sync_api import sync_playwright

import holdspeak.config as config_mod
from holdspeak.config import Config
from holdspeak.db import get_database, reset_database
from holdspeak.db.milestones import FIRST_DICTATION_SUCCESS
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OUT = Path("pm/roadmap/holdspeak/phase-85-the-mesh-edge/screenshots")
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    config_mod.CONFIG_FILE = tmp / "config.json"
    Config().save(config_mod.CONFIG_FILE)

    reset_database()
    db = get_database(tmp / "holdspeak.db")
    db.milestones.mark(FIRST_DICTATION_SUCCESS)
    db.profiles.upsert(
        profile_id="p-phone", name="Pocket 4B", kind="meshNode",
        node="walk-edge", model="qwen3.5-4b",
    )

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        ),
        host="127.0.0.1",
    )
    url = server.start()
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.set_viewport_size({"width": 1280, "height": 900})

            # live: the worker polled 2s ago
            db.mesh_relay.touch_worker("walk-edge", now=datetime.now() - timedelta(seconds=2))
            pg.goto(f"{url}/profiles", wait_until="networkidle")
            pg.wait_for_selector(".pf-name:has-text('Pocket 4B')", timeout=8_000)
            state = pg.locator(".pf-meta .pf-live, .pf-meta .pf-offline").first.inner_text()
            assert state.startswith("live ("), f"expected live, got {state!r}"
            badge = pg.locator(".pf-card .egress-badge").first.inner_text()
            assert badge == "⇄ mesh · walk-edge", badge
            pg.screenshot(path=str(OUT / "hs-85-04-profiles-card-live.png"))
            print(f"  profiles card (live): state={state!r} badge={badge!r}")

            # offline: age the worker past the window
            db.mesh_relay.touch_worker("walk-edge", now=datetime.now() - timedelta(seconds=180))
            pg.goto(f"{url}/profiles", wait_until="networkidle")
            pg.wait_for_selector(".pf-name:has-text('Pocket 4B')", timeout=8_000)
            state = pg.locator(".pf-meta .pf-live, .pf-meta .pf-offline").first.inner_text()
            assert state.startswith("offline ("), f"expected offline, got {state!r}"
            pg.screenshot(path=str(OUT / "hs-85-04-profiles-card-offline.png"))
            print(f"  profiles card (offline): state={state!r}")

            # the rail's models door: offline mesh model dimmed + named
            pg.goto(f"{url}/", wait_until="networkidle")
            pg.wait_for_selector(".desk-rail-model", timeout=10_000)
            pg.add_style_tag(content=".desk-mc, .desk-mc-tab { display: none !important; }")
            title = pg.locator(".desk-rail-model.is-offline").first.get_attribute("title")
            assert title == "qwen3.5-4b — mesh · walk-edge (offline)", title
            pg.screenshot(path=str(OUT / "hs-85-04-rail-mesh-offline.png"))
            print(f"  rail models door: title={title!r}")

            # the settings picker: mesh label + badge
            pg.goto(f"{url}/settings", wait_until="networkidle")
            pg.click("text=Cloud & advanced")
            pg.wait_for_selector("#set-intel-profile", timeout=8_000)
            pg.select_option("#set-intel-profile", "p-phone")
            pg.wait_for_timeout(300)
            chip = pg.locator(".egress-chip").inner_text()
            assert chip == "⇄ mesh · walk-edge", chip
            label = pg.locator("#set-intel-profile option[value='p-phone']").inner_text()
            assert label == "Pocket 4B — mesh · walk-edge", label
            pg.screenshot(path=str(OUT / "hs-85-04-settings-mesh-picked.png"))
            print(f"  settings picker: label={label!r} chip={chip!r}")

            b.close()
    finally:
        server.stop()
        reset_database()
    print("HS-85-04 SCREENSHOTS OK —", OUT)


if __name__ == "__main__":
    main()
