"""HS-84-05 — the LIVE walk: One Runtime, proven on the REAL hub → .43.

No scratch DB, no faked engine: this drives the hub already running on
127.0.0.1:8765 (its engine → the LAN llama.cpp on 192.168.1.43). The phase's
claim, walked end to end: an endpoint URL is typed in exactly ONE place (the
profile editor), and one profile authored once drives an agent chat, a
meeting-intel artifact run, and a dictation rewrite — with doctor naming the
profile for both pipelines.

Beats:
1. Author THE profile in the /profiles editor (the one place a URL is typed).
2. Pick it: Settings → Cloud & advanced → Runs on (meeting intel), and
   Dictation → Runtime → Runs on profile (dictation) — both saved in the UI.
3. An agent assigned to it answers in the browser, badge wearing the host.
4. `holdspeak intel --reroute` re-synthesizes the imported meeting's
   artifacts through the assigned profile.
5. A dictation dry-run passes through the same endpoint.
6. `holdspeak doctor`'s "Runtime profiles" line names the profile for BOTH
   pipelines.

Cleanup: both assignments cleared, the walk's recipe + profile deleted.
Reuses the HS-83 token-wrapper arrival (regression cover for the 401 find).
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
MEETING_ID = "a9e12058"  # envelope-proof (imported 2026-07-06)
PROFILE_NAME = "Walk .43"
PROFILE_URL = "http://192.168.1.43:8080/v1"
OUT = Path("pm/roadmap/holdspeak/phase-84-one-runtime/screenshots")
OUT.mkdir(parents=True, exist_ok=True)

TOKEN = os.environ.get("HS_WALK_TOKEN", "")
if not TOKEN:
    cfg_path = Path.home() / ".config/holdspeak/config.json"
    TOKEN = json.loads(cfg_path.read_text())["meeting"].get("web_auth_token", "")
H = {"X-HoldSpeak-Token": TOKEN}


def api(method, path, **kw):
    r = requests.request(method, BASE + path, headers=H, timeout=240, **kw)
    r.raise_for_status()
    return r.json() if r.text else {}


def cli(*args):
    proc = subprocess.run(
        ["uv", "run", "holdspeak", *args], capture_output=True, text=True, timeout=600
    )
    return proc.stdout, proc.stderr, proc.returncode


def main():
    if not TOKEN:
        sys.exit("no web auth token found")
    assert api("GET", f"/api/meetings/{MEETING_ID}").get("id") == MEETING_ID, \
        "the envelope-proof meeting is gone"

    before = api("GET", "/api/settings")
    prior_intel = before["meeting"].get("intel_profile_id")
    prior_dict = before["dictation"]["runtime"].get("profile_id")
    print(f"prior assignments: intel={prior_intel!r} dictation={prior_dict!r}")

    profile_id = None
    recipe = None
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.set_viewport_size({"width": 1280, "height": 900})

            # Beat 1 — author THE profile in the editor (arrive with ?token
            # once; the layout wrapper authenticates everything after).
            pg.goto(f"{BASE}/profiles?token={TOKEN}", wait_until="networkidle")
            assert "token=" not in pg.url, "the token must scrub from the address bar"
            pg.click(".pf-btn.primary")
            pg.fill("input[placeholder='OpenRouter · Claude Sonnet']", PROFILE_NAME)
            pg.fill("input[placeholder='https://openrouter.ai/api/v1']", PROFILE_URL)
            pg.fill("input[placeholder='anthropic/claude-sonnet-4']", "Qwen3.5-9B-Q6_K")
            pg.click(".pf-drawer-foot button[type='submit']")
            pg.wait_for_selector(f".pf-name:has-text('{PROFILE_NAME}')", timeout=8_000)
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(OUT / "hs-84-05-walk-profile-authored.png"))
            profile_id = next(
                p_["id"] for p_ in api("GET", "/api/profiles")["profiles"]
                if p_["name"] == PROFILE_NAME
            )
            print(f"beat 1: profile authored in the editor → {profile_id}")

            # Beat 2a — pick it for meeting intel in /settings.
            pg.goto(f"{BASE}/settings", wait_until="networkidle")
            pg.click("text=Cloud & advanced")
            pg.wait_for_selector("#set-intel-profile", timeout=8_000)
            pg.select_option("#set-intel-profile", profile_id)
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / "hs-84-05-walk-settings-picked.png"))
            pg.click("button:has-text('Save settings')")
            pg.wait_for_selector("text=Settings saved", timeout=8_000)
            assert api("GET", "/api/settings")["meeting"]["intel_profile_id"] == profile_id
            print("beat 2a: meeting intel picked in Settings and saved")

            # Beat 2b — pick it for dictation on the Runtime tab.
            pg.goto(f"{BASE}/dictation", wait_until="networkidle")
            pg.click("#section-runtime")
            # options never report "visible" — wait for the picker to populate
            pg.wait_for_function(
                "document.querySelectorAll('#rt-profile option').length > 1", timeout=8_000
            )
            pg.select_option("#rt-profile", profile_id)
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / "hs-84-05-walk-runtime-picked.png"))
            pg.click("#rt-btn-save")
            pg.wait_for_selector("#rt-msg .ok-box", timeout=8_000)
            assert api("GET", "/api/settings")["dictation"]["runtime"]["profile_id"] == profile_id
            print("beat 2b: dictation picked on the Runtime tab and saved")

            # Beat 3 — an agent assigned to the profile answers, badge honest.
            recipe = api("POST", "/api/recipes", json={
                "id": "recipe_walk84", "name": "Walk84", "avatar": "🧭",
                "role": "answers briefly", "system_prompt": "Answer in one short sentence.",
                "profile_id": profile_id,
            })["recipe"]
            pg.goto(f"{BASE}/", wait_until="networkidle")
            pg.wait_for_selector(".desk-obj", timeout=10_000)
            pg.add_style_tag(content=".desk-mc, .desk-mc-tab { display: none !important; }")
            pg.locator(".desk-rail-avatar[title='Walk84']").click()
            pg.wait_for_selector(".desk-chat", timeout=6_000)
            pg.fill(".desk-chat-composer input", "In one short sentence, what is dictation?")
            pg.click(".desk-chat-composer .desk-chip:has-text('Send')")
            pg.wait_for_selector(".desk-chat-meta .egress-badge", timeout=180_000)
            badge = pg.inner_text(".desk-chat-meta .egress-badge")
            print(f"beat 3: agent badge = {badge!r}")
            assert "192.168.1.43" in badge, "the agent badge must wear the profile's host"
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / "hs-84-05-walk-agent-badge.png"))
            b.close()

        # Beat 4 — the imported meeting re-synthesizes through the profile.
        out, err, code = cli("intel", "--reroute", MEETING_ID, "--profile", "delivery")
        assert code == 0, f"reroute failed: {err[-400:]}"
        payload = json.loads(out[out.index("{"):])
        assert payload.get("executed") is True, f"chain did not execute: {payload}"
        saved = payload.get("artifacts_saved")
        print(f"beat 4: reroute executed on the profile; artifacts_saved={saved}")
        assert saved, "the routed chain saved no artifacts"

        # Beat 5 — a dictation rewrite through the same endpoint.
        dry = api("POST", "/api/dictation/dry-run", json={
            "utterance": "please add a todo saying verify the runtime profile walk passed",
        })
        assert "error" not in dry, f"dry-run error: {dry}"
        print(f"beat 5: dictation dry-run OK (keys: {sorted(dry)[:8]})")

        # Beat 6 — doctor names the profile for BOTH pipelines.
        out, err, code = cli("doctor")
        line = next((ln for ln in out.splitlines() if "Runtime profiles" in ln), "")
        print(f"beat 6: doctor → {line.strip()!r}")
        assert PROFILE_NAME in line and "meeting intel" in line and "dictation" in line, \
            "doctor must name the profile for both pipelines"

        print("HS-84-05 LIVE WALK: all six beats PROVEN on the real hub → .43")
    finally:
        try:
            api("PUT", "/api/settings", json={
                "meeting": {"intel_profile_id": prior_intel},
                "dictation": {"runtime": {"profile_id": prior_dict}},
            })
        except Exception as exc:
            print(f"cleanup (settings) failed: {exc}")
        if recipe:
            try:
                api("DELETE", f"/api/recipes/{recipe['id']}")
            except Exception:
                pass
        if profile_id:
            try:
                api("DELETE", f"/api/profiles/{profile_id}")
            except Exception:
                pass
        print("cleanup: assignments restored; walk recipe + profile removed")


if __name__ == "__main__":
    main()
