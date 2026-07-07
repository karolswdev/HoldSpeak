"""HS-84-03 — settings pick, not type (Playwright, real app, scratch DB).

Both endpoint sections author by PICKING a RuntimeProfile: the /settings
"Cloud & advanced" section and the /dictation Runtime tab each show the
"Runs on" picker + the pick's egress badge + the door to /profiles — and no
raw base-URL/model/key-env inputs. Shot in both states: empty (no profiles,
the picker offers only its default) and picked (a LAN profile assigned).
"""
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

from playwright.sync_api import sync_playwright

import holdspeak.config as config_mod
from holdspeak.config import Config
from holdspeak.db import get_database, reset_database
from holdspeak.db.milestones import FIRST_DICTATION_SUCCESS
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OUT = Path("pm/roadmap/holdspeak/phase-84-one-runtime/screenshots")
OUT.mkdir(parents=True, exist_ok=True)


def shot_settings_cloud(pg, url: str, name: str) -> None:
    pg.goto(f"{url}/settings", wait_until="networkidle")
    pg.click("text=Cloud & advanced")
    pg.wait_for_selector("text=Runs on", timeout=6000)
    time.sleep(0.4)
    pg.screenshot(path=str(OUT / name), full_page=False)
    print(f"  shot: {name}")


def shot_dictation_runtime(pg, url: str, name: str) -> None:
    pg.goto(f"{url}/dictation", wait_until="networkidle")
    pg.click("#section-runtime")
    pg.wait_for_selector("#rt-profile", state="visible", timeout=6000)
    # the section loads settings + readiness + profiles async; settle first
    time.sleep(1.2)
    pg.locator("#rt-profile").scroll_into_view_if_needed()
    pg.screenshot(path=str(OUT / name), full_page=False)
    print(f"  shot: {name}")


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    config_mod.CONFIG_FILE = tmp / "config.json"
    Config().save(config_mod.CONFIG_FILE)

    reset_database()
    db = get_database(tmp / "holdspeak.db")
    db.milestones.mark(FIRST_DICTATION_SUCCESS)

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
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

            print("state 1: no profiles, nothing assigned (the empty state)")
            shot_settings_cloud(pg, url, "hs-84-03-settings-cloud-empty.png")
            shot_dictation_runtime(pg, url, "hs-84-03-dictation-runtime-empty.png")

            print("state 2: a LAN profile exists and is assigned to both")
            db.profiles.upsert(
                profile_id="profile_lan",
                name="LAN box",
                kind="openAICompatible",
                base_url="http://192.168.1.43:8080/v1",
                model="Qwen3.5-9B-Q6_K",
            )
            db.profiles.upsert(
                profile_id="profile_phone",
                name="Pocket 4B",
                kind="onDevice",
                model_file="qwen3.5-4b.gguf",
            )
            cfg = Config.load(config_mod.CONFIG_FILE)
            cfg.meeting.intel_profile_id = "profile_lan"
            cfg.dictation.runtime.profile_id = "profile_lan"
            cfg.dictation.pipeline.enabled = True
            cfg.save(config_mod.CONFIG_FILE)

            shot_settings_cloud(pg, url, "hs-84-03-settings-cloud-picked.png")
            shot_dictation_runtime(pg, url, "hs-84-03-dictation-runtime-picked.png")

            # the load-bearing claims, asserted, not eyeballed
            pg.goto(f"{url}/settings", wait_until="networkidle")
            pg.click("text=Cloud & advanced")
            pg.wait_for_selector("text=Runs on", timeout=6000)
            assert pg.locator(".egress-chip").inner_text() == "☁ 192.168.1.43:8080", (
                "the settings badge must wear the picked profile's host"
            )
            assert pg.locator("#set-intel-profile").input_value() == "profile_lan", (
                "the picker must DISPLAY the assigned profile (Alpine x-for race)"
            )
            assert pg.locator("input[placeholder='https://api.openai.com/v1']").count() == 0, (
                "the raw base-URL input must be gone from /settings"
            )
            pg.goto(f"{url}/dictation", wait_until="networkidle")
            pg.click("#section-runtime")
            pg.wait_for_selector("#rt-profile-badge", state="visible", timeout=6000)
            assert pg.locator("#rt-profile-badge").inner_text() == "☁ 192.168.1.43:8080", (
                "the runtime badge must wear the picked profile's host"
            )
            assert pg.locator("#rt-openai-base-url").count() == 0, (
                "the raw base-URL input must be gone from the Runtime tab"
            )
            assert "runs on:" in pg.locator("#rt-meta-banner").inner_text(), (
                "the banner must name where the pipeline runs"
            )
            b.close()
    finally:
        server.stop()
        reset_database()
    print("HS-84-03 SCREENSHOTS OK —", OUT)


if __name__ == "__main__":
    main()
