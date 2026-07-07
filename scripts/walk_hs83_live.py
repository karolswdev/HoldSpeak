"""HS-83-04 — the LIVE walk: Phase 83's three features against the REAL hub.

No scratch DB, no faked engine: this drives the hub already running on
127.0.0.1:8765 (its engine → the LAN llama.cpp), authenticates the browser the
way an owner does (?token=… once; the HS-83-04 layout wrapper carries it on
every request), and every answer below came out of the real model.

Beats:
1. The desk loads AUTHENTICATED (the token wrapper's own proof) and the rail
   lists the hub's real runnable models.
2. Ground this ask, control-vs-treatment, in the browser: the same codename
   question ungrounded (a guess) then grounded on the imported
   "envelope-proof" meeting (the real answer).
3. A persona conversation: a real recipe created for the walk, a grounded
   turn answered by the real model, thread persistence.
4. A model chat: one click on the hub's own model, a pinned turn.

Cleanup: the walk's note and recipe are deleted; the imported meeting
(a9e12058) predates the walk and stays.
"""
import os
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
TOKEN = os.environ.get("HS_WALK_TOKEN", "")
MEETING_ID = "a9e12058"   # envelope-proof (imported 2026-07-06; codename inside)
OUT = Path("pm/roadmap/holdspeak/phase-83-web-in-unison/screenshots")
OUT.mkdir(parents=True, exist_ok=True)
H = {"X-HoldSpeak-Token": TOKEN}
QUESTION = "What is the launch codename for the mesh milestone? Answer with just the codename."


def api(method, path, **kw):
    r = requests.request(method, BASE + path, headers=H, timeout=180, **kw)
    r.raise_for_status()
    return r.json() if r.text else {}


def main():
    if not TOKEN:
        sys.exit("set HS_WALK_TOKEN")
    assert api("GET", f"/api/meetings/{MEETING_ID}").get("id") == MEETING_ID, \
        "the envelope-proof meeting is gone — import a transcript first"

    note = api("POST", "/api/notes", json={
        "title": "Walk note", "body_markdown": "The web-in-unison walk grounds from here.",
    })["note"]
    recipe = api("POST", "/api/recipes", json={
        "id": "recipe_walk_scout", "name": "Walk Scout", "avatar": "🦊",
        "role": "digs for the facts", "system_prompt": "You are a sharp researcher. Be brief.",
    })["recipe"]

    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.set_viewport_size({"width": 1280, "height": 800})
            pg.add_init_script(
                'localStorage.setItem("hs.diorama.pos", JSON.stringify({'
                f'"note:{note["id"]}": {{x: 0.3, y: 0.42}}}}))'
            )

            # Beat 1 — arrive with ?token once; the wrapper authenticates the rest.
            pg.goto(f"{BASE}/?token={TOKEN}", wait_until="networkidle")
            pg.wait_for_selector(".desk-obj", timeout=10_000)
            # The mission-control conveyor reads THIS machine's real rails —
            # off-walk, and it must not intercept the lasso or leak local
            # project names into committed shots (the house rigs do the same).
            pg.add_style_tag(content=".desk-mc, .desk-mc-tab { display: none !important; }")
            assert "token=" not in pg.url, "the token must scrub from the address bar"
            pg.wait_for_selector(".desk-rail-model", timeout=10_000)
            models = pg.eval_on_selector_all(".desk-rail-model", "els => els.map(e => e.title)")
            print(f"rail models (real): {models}")
            assert any("Qwen" in m for m in models), "the hub's real model is missing from the rail"

            # Beat 2 — ground this ask, control vs treatment, in the browser.
            def run_ask(grounded: bool) -> str:
                pg.mouse.move(300, 260); pg.mouse.down()
                pg.mouse.move(480, 430, steps=10); pg.mouse.up()
                pg.wait_for_selector(".desk-askbar", timeout=6_000)
                pg.click(".desk-askbar .desk-chip:has-text('Ask AI')")
                pg.wait_for_selector(".desk-ask", timeout=6_000)
                if grounded:
                    pg.click(".desk-ground-head")
                    pg.wait_for_selector(".desk-ground-row", timeout=6_000)
                    pg.click(".desk-ground-pick:has-text('envelope-proof')")
                    pg.wait_for_selector(".desk-ground-expand", timeout=6_000)
                    pg.click(".desk-ground-expand .desk-chip:has-text('Transcript')")
                    pg.wait_for_timeout(300)
                pg.fill(".desk-ask-prompt textarea", QUESTION)
                if grounded:
                    pg.screenshot(path=str(OUT / "hs-83-04-walk-grounded-compose.png"))
                pg.click(".desk-pullout-foot .desk-chip:has-text('Ask')")
                pg.wait_for_selector(".desk-ask-card", timeout=120_000)
                text = pg.inner_text(".desk-ask-card")
                if grounded:
                    pg.screenshot(path=str(OUT / "hs-83-04-walk-grounded-answer.png"))
                pg.click(".desk-pullout-foot .desk-chip:has-text('Bin')")
                pg.wait_for_timeout(400)
                return text

            control = run_ask(grounded=False)
            treatment = run_ask(grounded=True)
            print(f"control (ungrounded): {control[:90]!r}")
            print(f"treatment (grounded): {treatment[:90]!r}")
            assert "BLUE LANTERN" not in control.upper(), "the control leaked the codename"
            assert "BLUE LANTERN" in treatment.upper(), "the grounded ask missed the codename"

            # Beat 3 — a persona conversation, grounded, answered by the real model.
            pg.locator(f".desk-rail-avatar[title='Walk Scout']").click()
            pg.wait_for_selector(".desk-chat", timeout=6_000)
            pg.click(".desk-ground-head")
            pg.wait_for_selector(".desk-ground-row", timeout=6_000)
            pg.click(".desk-ground-pick:has-text('envelope-proof')")
            pg.wait_for_selector(".desk-ground-expand", timeout=6_000)
            pg.click(".desk-ground-expand .desk-chip:has-text('Transcript')")
            pg.click(".desk-ground-head")
            pg.fill(".desk-chat-composer input", QUESTION)
            pg.click(".desk-chat-composer .desk-chip:has-text('Send')")
            pg.wait_for_selector(".desk-chat-turn.is-agent .desk-chat-bubble:not(.desk-chat-thinking)", timeout=120_000)
            reply = pg.inner_text(".desk-chat-turn.is-agent .desk-chat-bubble:not(.desk-chat-thinking)")
            print(f"persona reply: {reply[:90]!r}")
            assert "BLUE LANTERN" in reply.upper()
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / "hs-83-04-walk-persona-thread.png"))
            pg.click(".desk-pullout-close")

            # Beat 4 — the model door: the hub's own model, one pinned turn.
            pg.locator(".desk-rail-model").first.click()
            pg.wait_for_selector(".desk-chat", timeout=6_000)
            title = pg.inner_text(".desk-chat .desk-pullout-title")
            pg.fill(".desk-chat-composer input", "In one short sentence: which model family are you?")
            pg.click(".desk-chat-composer .desk-chip:has-text('Send')")
            pg.wait_for_selector(".desk-chat-meta .egress-badge", timeout=120_000)
            badge = pg.inner_text(".desk-chat-meta .egress-badge")
            print(f"model chat: title={title!r} badge={badge!r}")
            assert "Qwen" in title and "192.168.1.43" in badge
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / "hs-83-04-walk-model-chat.png"))

            print("HS-83-04 LIVE WALK: all four beats PROVEN on the real hub → .43")
            b.close()
    finally:
        try:
            api("DELETE", f"/api/notes/{note['id']}")
        except Exception:
            pass
        try:
            api("DELETE", f"/api/recipes/{recipe['id']}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
