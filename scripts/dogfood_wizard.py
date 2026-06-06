#!/usr/bin/env python3
"""HS-43-06: dogfood the world-class first-run wizard.

Boots a fresh HoldSpeak server and drives the real wizard in a headless browser:

  1. a brand-new user hitting `/` is redirected to the `/welcome` wizard.
  2. the wizard walks Welcome → Permissions → Model → First dictation → Presence
     → You're set, one step at a time.
  3. selecting a model persists to config; flipping presence persists
     `config.presence.enabled` (no env var); a real dictation success (the
     runtime's `dictation_typed` broadcast) lights the "It worked" celebration.
  4. "Open HoldSpeak" lands on the dashboard.

    uv run python scripts/dogfood_wizard.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    import holdspeak.config as config_module

    cfg_path = Path(tempfile.mkdtemp()) / "config.json"
    config_module.CONFIG_FILE = cfg_path

    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    reset_database()
    get_database(Path(tempfile.mkdtemp()) / "wiz.db")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=lambda: {"runtime": {"last_transcription": "my first words in holdspeak"}},
        )
    )
    url = server.start()
    time.sleep(1.0)

    from playwright.sync_api import sync_playwright

    print("HoldSpeak wizard dogfood")
    print("=" * 24)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1380, "height": 880})

        # 1. fresh user on / -> the wizard
        page.goto(f"{url}/", wait_until="networkidle")
        time.sleep(0.8)
        print(f"1. fresh `/` -> {page.url.replace(url, '') or '/'}")
        assert page.url.endswith("/welcome"), "first-run did not open the wizard"

        page.wait_for_selector(".welcome-h", timeout=8000)
        page.click(".wz-btn.primary")  # -> permissions
        page.wait_for_selector(".perm-tiles", timeout=4000)
        time.sleep(0.4)
        print("2. permissions: system check shown")

        page.click(".wz-btn.primary")  # -> model
        page.wait_for_selector(".model-grid", timeout=4000)
        page.locator(".model-tile").nth(2).click()  # GGUF
        time.sleep(0.6)
        backend = json.loads(cfg_path.read_text()).get("dictation", {}).get("runtime", {}).get("backend")
        print(f"3. model: selected GGUF -> config backend = {backend!r}")

        page.click(".wz-btn.primary")  # -> dictation
        page.wait_for_selector(".dict-target", timeout=4000)
        server.broadcast("runtime_activity", {
            "state": "complete", "source": "dictation", "label": "Typed",
            "detail": "Dictated text was inserted.", "last_event": "dictation_typed", "last_error": "",
        })
        page.wait_for_selector(".dict-win", timeout=4000)
        time.sleep(0.4)
        print(f"4. first dictation: {page.locator('.dict-win-h').inner_text().strip()} "
              f"({page.locator('.dict-quote').inner_text().strip()!r})")

        page.click(".wz-btn.primary")  # -> presence
        page.wait_for_selector(".stp-presence .switch", timeout=4000)
        page.click(".stp-presence .switch")
        page.wait_for_selector(".switch.on", timeout=4000)
        time.sleep(0.5)
        presence = json.loads(cfg_path.read_text()).get("presence", {}).get("enabled")
        print(f"5. presence: toggled on -> config.presence.enabled = {presence} (no env var)")

        page.click(".wz-btn.primary")  # -> done
        page.wait_for_selector(".done-burst", timeout=4000)
        time.sleep(0.4)
        print("6. you're set: celebration shown")

        page.click(".wz-btn.primary")  # Open HoldSpeak -> /
        time.sleep(0.8)
        landed = page.url.rstrip("/").endswith(url.rstrip("/"))
        print(f"7. Open HoldSpeak -> {'dashboard' if landed else page.url}")
        browser.close()

    ok = backend == "llama_cpp" and presence is True and landed
    print()
    print(f"{'WIZARD DOGFOOD OK' if ok else 'WIZARD DOGFOOD FAILED'} — fresh clone → guided wizard → first dictation, zero file edits")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
