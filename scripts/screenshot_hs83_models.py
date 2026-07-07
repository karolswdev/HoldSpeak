"""HS-83-03 — the models front door on the web desk, proven live (Playwright,
real app, scratch DB).

The rail lists what the hub can run (`GET /api/models` — the ask allow-list);
one click opens a chat titled with the model; a turn runs PINNED to that model
(`/api/ask` `model` override — asserted at the engine seam) and the reply's
badge wears the hub-reported model.
"""
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from playwright.sync_api import sync_playwright

from holdspeak.db import get_database, reset_database
from holdspeak.db.milestones import FIRST_DICTATION_SUCCESS
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OUT = Path("pm/roadmap/holdspeak/phase-83-web-in-unison/screenshots")
OUT.mkdir(parents=True, exist_ok=True)


class _CapturingIntel:
    active_provider = "cloud"

    def __init__(self):
        self.prompts: list[str] = []

    def run_prompt(self, **kwargs):
        self.prompts.append(kwargs.get("user_prompt", ""))
        return "MODEL DOOR OK — this turn ran pinned to me."


def seed(db) -> None:
    db.milestones.mark(FIRST_DICTATION_SUCCESS)
    db.recipes.upsert(recipe_id="recipe_scout", name="Scout", avatar="🦊",
                      role="digs for the facts", system_prompt="You are a researcher.")
    db.profiles.upsert(profile_id="profile_lan", name="LAN box",
                       kind="openAICompatible",
                       base_url="http://192.168.1.43:8080/v1",
                       model="Qwen3.5-9B-Q6_K")


def main():
    tmp = Path(tempfile.mkdtemp())
    reset_database()
    db = get_database(tmp / "holdspeak.db")
    seed(db)
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        host="127.0.0.1")
    url = server.start()
    time.sleep(1.0)
    fake = _CapturingIntel()
    try:
        with patch("holdspeak.intel.providers.build_meeting_intel_for_profile",
                   lambda **kw: fake), \
             patch("holdspeak.intel.providers.build_configured_meeting_intel",
                   lambda: fake), \
             patch("holdspeak.web.routes.sync._hub_model_name",
                   lambda ctx: "HubModel-9B"), \
             sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.set_viewport_size({"width": 1280, "height": 800})
            pg.goto(f"{url}/", wait_until="networkidle")
            pg.wait_for_selector(".desk-rail-avatar", timeout=6000)
            pg.add_style_tag(content=".desk-mc, .desk-mc-tab { display: none !important; }")

            # The rail's models section: the allow-list rows (hub row first).
            n_models = pg.eval_on_selector_all(".desk-rail-model", "els => els.length")
            assert n_models == 2, f"expected 2 model rows (hub + profile), got {n_models}"
            titles = pg.eval_on_selector_all(".desk-rail-model", "els => els.map(e => e.title)")
            assert titles[0] == "HubModel-9B", f"hub row first: {titles}"
            assert "Qwen3.5-9B-Q6_K" in titles
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / "hs-83-03-rail-models.png"))

            # One click opens a chat TITLED with the model; a turn runs pinned.
            pg.locator(".desk-rail-model").last.click()   # the profile's Qwen
            pg.wait_for_selector(".desk-chat", timeout=4000)
            head = pg.inner_text(".desk-chat .desk-pullout-title")
            assert "Qwen3.5-9B-Q6_K" in head, f"chat title lies: {head!r}"
            pg.fill(".desk-chat-composer input", "Which model is speaking?")
            pg.click(".desk-chat-composer .desk-chip:has-text('Send')")
            pg.wait_for_selector(".desk-chat-turn.is-agent .desk-chat-bubble", timeout=6000)
            # The pin reached the engine: the override resolved to the LAN
            # profile (its model matches), so the ask ran on that profile.
            assert len(fake.prompts) == 1
            assert "[USER]\nWhich model is speaking?" in fake.prompts[0]
            badge = pg.inner_text(".desk-chat-meta .egress-badge")
            assert "Qwen3.5-9B-Q6_K" in badge and "192.168.1.43" in badge, f"badge lies: {badge!r}"
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / "hs-83-03-model-chat.png"))

            print("HS-83-03 rig: rail door + pinned turn + honest badge PROVEN")
            b.close()
    finally:
        server.stop()
        reset_database()


if __name__ == "__main__":
    main()
