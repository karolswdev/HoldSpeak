"""HS-83-01 — ground this ask on the web composer, proven live (Playwright,
real app, scratch DB).

Captures the picker (meeting expansion rows + the honest fetched-length gauge)
and the grounded printed card — and ASSERTS the treatment: the faked engine
captures the exact user_prompt, so the test proves the hub hydrated the
meeting's transcript and the toggled artifact from REFERENCES the composer
sent (ids only; the request body never carried the text).
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

ANSWER = "BLUE LANTERN — named in the kickoff transcript; the decisions artifact confirms it."


class _CapturingIntel:
    active_provider = "cloud"

    def __init__(self):
        self.user_prompt = ""

    def run_prompt(self, **kwargs):
        self.user_prompt = kwargs.get("user_prompt", "")
        return ANSWER


def seed(db) -> None:
    db.milestones.mark(FIRST_DICTATION_SUCCESS)
    db.notes.upsert(note_id="note_mesh", title="Mesh sync owner",
                    body_markdown="Karol owns the mesh sync review.")
    db.meetings.save_meeting(MeetingState(
        id="m83", started_at=datetime(2026, 7, 6, 10, 0, 0),
        ended_at=datetime(2026, 7, 6, 10, 30, 0), title="Q3 kickoff",
        segments=[
            TranscriptSegment(text="The launch codename for the mesh milestone is BLUE LANTERN.",
                              speaker="Karol", start_time=0.0, end_time=4.0),
            TranscriptSegment(text="Noted. BLUE LANTERN it is; the envelope ships this week.",
                              speaker="Sam", start_time=4.0, end_time=8.0),
        ],
        intel=IntelSnapshot(timestamp=1.0, summary="Kickoff set the codename and the ship week.",
                            action_items=[{"id": "ai83", "task": "Ship the envelope"}]),
    ))
    db.plugins.record_artifact(
        artifact_id="artifact_dec83", meeting_id="m83", artifact_type="decisions",
        title="Decisions", body_markdown="- The envelope ships this week.",
    )
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
            pg.add_init_script(
                'localStorage.setItem("hs.diorama.pos", JSON.stringify({'
                'note_mesh: {x: 0.3, y: 0.4},'
                '"m:m83": {x: 0.6, y: 0.4}}))'
            )
            pg.goto(f"{url}/", wait_until="networkidle")
            pg.wait_for_selector(".desk-obj", timeout=6000)
            pg.add_style_tag(content=".desk-mc, .desk-mc-tab { display: none !important; }")
            pg.wait_for_timeout(600)

            # Lasso the note → the bundle bar → the composer.
            pg.mouse.move(300, 260)
            pg.mouse.down()
            pg.mouse.move(480, 420, steps=10)
            pg.mouse.up()
            pg.wait_for_selector(".desk-askbar", timeout=4000)
            pg.click(".desk-askbar .desk-chip:has-text('Ask AI')")
            pg.wait_for_selector(".desk-ask", timeout=4000)

            # Ground this ask: pick the meeting; digest defaults on; toggle
            # the transcript and the bound Decisions artifact independently.
            pg.click(".desk-ground-head")
            pg.wait_for_selector(".desk-ground-row", timeout=4000)
            pg.click(".desk-ground-pick:has-text('Q3 kickoff')")
            pg.wait_for_selector(".desk-ground-expand", timeout=4000)
            pg.click(".desk-ground-expand .desk-chip:has-text('Transcript')")
            pg.click(".desk-ground-expand .desk-chip:has-text('Decisions')")
            pg.wait_for_timeout(400)
            tokens = pg.inner_text(".desk-ground-tokens")
            assert "tok" in tokens and not tokens.startswith("0 /"), f"gauge lies: {tokens!r}"
            head = pg.inner_text(".desk-ground-head")
            assert "1 meeting" in head and "1 artifact" in head, f"chip lies: {head!r}"
            pg.screenshot(path=str(OUT / "hs-83-01-picker.png"))

            # Run grounded. The composer ships REFS; the captured prompt must
            # contain hub-hydrated content the request never carried.
            pg.fill(".desk-ask-prompt textarea", "What is the launch codename?")
            pg.click(".desk-pullout-foot .desk-chip:has-text('Ask')")
            pg.wait_for_selector(".desk-ask-card", timeout=6000)
            up = fake.user_prompt
            assert "[MEETING: Q3 kickoff — 2026-07-06]" in up, f"no meeting block:\n{up}"
            assert "BLUE LANTERN" in up, "transcript did not hydrate"
            assert "[ARTIFACT: Decisions — Q3 kickoff]" in up, "artifact did not hydrate"
            assert "Mesh sync owner" in up, "the lasso'd card still rides as material"
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(OUT / "hs-83-01-grounded-print.png"))

            print("HS-83-01 rig: picker + gauge + hydrated grounding PROVEN")
            print(f"  captured prompt bytes: {len(up)}")
            b.close()
    finally:
        server.stop()
        reset_database()


if __name__ == "__main__":
    main()
