"""HS-69-12 — the Companion Agent Desk proof.

Seeds real agents and loads /companion (now the Agent Desk): the agent persona
cards + the live companion link. A Playwright route-mock injects an awaiting
coding session so the "Needs you" zone is also shown. Requires the built bundle.
"""
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

from playwright.sync_api import sync_playwright

from holdspeak.db import get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OUT = Path("pm/roadmap/holdspeak/phase-69-web-recrafted/screenshots")
OUT.mkdir(parents=True, exist_ok=True)

STATUS_MOCK = {
    "device_connected": True,
    "agent_sessions": [
        {"agent": "claude-on-ledgerline", "session_id": "s1", "awaiting_response": True,
         "summary": "Waiting on you: which migration strategy for the rate-limiter table?"},
        {"agent": "codex-on-questline", "session_id": "s2", "awaiting_response": False,
         "summary": "Running tests."},
    ],
}


def main():
    tmp = Path(tempfile.mkdtemp())
    reset_database()
    db = get_database(tmp / "holdspeak.db")
    db.agents.upsert(agent_id="a1", name="Summarizer", avatar="🧭",
                     role="Condenses long meetings into decisions + owners",
                     system_prompt="You summarize.", user_template="{input}", tools=["web"], kb_id="kb-platform")
    db.agents.upsert(agent_id="a2", name="Triage", avatar="🚦",
                     role="Routes action items to the right project and drafts issues",
                     system_prompt="You triage.", user_template="{input}", tools=["github"])
    db.agents.upsert(agent_id="a3", name="Reviewer", avatar="🔎",
                     role="Reviews a diff for correctness and reuse",
                     system_prompt="You review.", user_template="{input}", tools=[])

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        host="127.0.0.1")
    url = server.start()
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.set_viewport_size({"width": 1200, "height": 820})
            # inject a live companion link (awaiting session)
            pg.route("**/api/companion/status", lambda route: route.fulfill(
                status=200, content_type="application/json", body=json.dumps(STATUS_MOCK)))
            pg.goto(f"{url}/companion", wait_until="networkidle")
            pg.wait_for_selector(".ad-card", timeout=4000)
            pg.wait_for_timeout(600)
            agents = pg.eval_on_selector_all(".ad-card:not(.is-needs)", "e => e.length")
            needs = pg.eval_on_selector_all(".ad-card.is-needs", "e => e.length")
            link = pg.text_content(".ad-link")
            pg.screenshot(path=str(OUT / "companion-agent-desk.png"), full_page=True)
            b.close()
        print(f"agent cards: {agents} | needs-you cards: {needs} | link: {link!r}")
    finally:
        server.stop()
        reset_database()
    print("Saved companion screenshot to", OUT)


if __name__ == "__main__":
    main()
