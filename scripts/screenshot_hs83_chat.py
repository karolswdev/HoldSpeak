"""HS-83-02 — agent conversations on the web desk, proven live (Playwright,
real app, scratch DB).

Drives a REAL multi-turn conversation through `/api/recipes/{id}/chat`
(capturing engine — no model loads, the route runs for real): turn 1 plain,
then grounding attached mid-conversation, turn 2 asserted to carry the
hydrated meeting block AND the running conversation; the reply harvested to
the desk; the thread proven persistent across a reload.
"""
import tempfile
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

from playwright.sync_api import sync_playwright

from holdspeak.db import get_database, reset_database
from holdspeak.db.milestones import FIRST_DICTATION_SUCCESS
from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OUT = Path("pm/roadmap/holdspeak/phase-83-web-in-unison/screenshots")
OUT.mkdir(parents=True, exist_ok=True)


class _CapturingIntel:
    active_provider = "cloud"

    def __init__(self):
        self.prompts: list[str] = []

    def run_prompt(self, **kwargs):
        self.prompts.append(kwargs.get("user_prompt", ""))
        if len(self.prompts) == 1:
            return "Three things stood out from the kickoff; want the codename thread pulled?"
        return "BLUE LANTERN — it is named in the kickoff transcript you grounded me on."


def seed(db) -> None:
    db.milestones.mark(FIRST_DICTATION_SUCCESS)
    db.recipes.upsert(recipe_id="recipe_scout", name="Scout", avatar="🦊",
                      role="digs for the facts",
                      system_prompt="You are a sharp researcher.",
                      manual_context="The team is three engineers.")
    db.meetings.save_meeting(MeetingState(
        id="m83c", started_at=datetime(2026, 7, 6, 10, 0, 0), title="Q3 kickoff",
        segments=[TranscriptSegment(text="The launch codename is BLUE LANTERN.",
                                    speaker="Karol", start_time=0.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, summary="Kickoff set the codename.",
                            action_items=[{"id": "aic", "task": "Ship the envelope"}]),
    ))
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
             sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.set_viewport_size({"width": 1280, "height": 800})
            pg.goto(f"{url}/", wait_until="networkidle")
            pg.wait_for_selector(".desk-rail-avatar", timeout=6000)
            pg.add_style_tag(content=".desk-mc, .desk-mc-tab { display: none !important; }")

            # Open the persona's conversation from the rail.
            pg.click(".desk-rail-avatar")
            pg.wait_for_selector(".desk-chat", timeout=4000)

            # Turn 1 — plain. The reply bubble renders with the honest badge.
            pg.fill(".desk-chat-composer input", "What should I focus on after the kickoff?")
            pg.click(".desk-chat-composer .desk-chip:has-text('Send')")
            pg.wait_for_selector(".desk-chat-turn.is-agent .desk-chat-bubble", timeout=6000)
            up1 = fake.prompts[0]
            assert "[CONTEXT]" in up1 and "The team is three engineers." in up1
            assert "[CONVERSATION SO FAR]" not in up1, "turn 1 has no history"

            # Attach grounding mid-conversation (the selection persists per
            # conversation), then turn 2 must carry BOTH the hydrated meeting
            # and the running conversation.
            pg.click(".desk-ground-head")
            pg.wait_for_selector(".desk-ground-row", timeout=4000)
            pg.click(".desk-ground-pick:has-text('Q3 kickoff')")
            pg.wait_for_selector(".desk-ground-expand", timeout=4000)
            pg.click(".desk-ground-expand .desk-chip:has-text('Transcript')")
            pg.click(".desk-ground-head")  # collapse → the chip wears the label
            pg.wait_for_timeout(300)
            head = pg.inner_text(".desk-ground-head")
            assert "1 meeting" in head, f"grounding chip lies: {head!r}"
            pg.screenshot(path=str(OUT / "hs-83-02-thread-grounded-composer.png"))

            pg.fill(".desk-chat-composer input", "What is the launch codename?")
            pg.click(".desk-chat-composer .desk-chip:has-text('Send')")
            pg.wait_for_timeout(1500)
            assert len(fake.prompts) == 2, f"expected 2 turns, engine saw {len(fake.prompts)}"
            up2 = fake.prompts[1]
            assert "[MEETING: Q3 kickoff — 2026-07-06]" in up2 and "BLUE LANTERN" in up2
            assert "[CONVERSATION SO FAR]" in up2 and "Scout:" in up2
            assert up2.index("[GROUNDING]") < up2.index("[CONVERSATION SO FAR]")

            # Harvest the reply → a run-born artifact lands on the desk NEW.
            pg.locator(".desk-chat-turn.is-agent .desk-chip", has_text="Save to desk").last.click()
            pg.wait_for_selector(".desk-obj.is-new", timeout=6000)
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(OUT / "hs-83-02-thread-harvested.png"))

            # The thread survives a reload (device-local persistence).
            pg.reload(wait_until="networkidle")
            pg.wait_for_selector(".desk-rail-avatar", timeout=6000)
            pg.click(".desk-rail-avatar")
            pg.wait_for_selector(".desk-chat-turn.is-agent", timeout=4000)
            n = pg.eval_on_selector_all(".desk-chat-turn", "els => els.length")
            assert n >= 4, f"thread did not persist: {n} turns after reload"

            print("HS-83-02 rig: thread + grounding mid-conversation + harvest + persistence PROVEN")
            b.close()
    finally:
        server.stop()
        reset_database()


if __name__ == "__main__":
    main()
