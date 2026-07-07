"""HS-85-05 — the LIVE walk: The Mesh Edge, proven on the REAL hub.

No scratch DB, no faked engine: the hub already runs on 127.0.0.1:8765; a
REAL `holdspeak mesh serve` process becomes node `walk-edge`, carrying its
OWN config (an isolated HOME pointing straight at the .43 llama.cpp) — the
hub knows the profile; the NODE knows the provider. The phase's claim walked
end to end: the request moves, the model and the key don't.

Beats:
1. The worker starts; doctor's "Mesh edges" line shows the edge live.
2. The mesh profile is authored ONCE in the /profiles editor (the only
   place anything about the target is typed): kind Mesh node, node
   walk-edge.
3. An agent assigned to it answers in the browser — badge `⇄ mesh ·
   walk-edge` — and the worker's log proves the run executed in THAT
   process.
4. Meeting intel picked onto the profile (Settings → Runs on) and
   `intel --reroute` re-synthesizes artifacts THROUGH the edge.
5. Dictation picked onto the profile (Runtime → Runs on profile) and a
   dry-run rewrites through the same edge.
6. The worker is KILLED: the models door reads offline, and a forced run
   refuses fast (< 5s) naming the node. No hang.

Cleanup: assignments restored, the walk's recipe + profile deleted, the
worker's temp HOME removed.
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
NODE = "walk-edge"
PROFILE_NAME = "Walk Edge"
EDGE_URL = "http://192.168.1.43:8080/v1"
EDGE_MODEL = "Qwen3.5-9B-Q6_K"
OUT = Path("pm/roadmap/holdspeak/phase-85-the-mesh-edge/screenshots")
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


def start_worker(log_path: Path) -> subprocess.Popen:
    """The REAL edge: its own HOME, its own config → .43 directly."""
    home = Path(tempfile.mkdtemp(prefix="hs85-edge-home-"))
    cfg_dir = home / ".config/holdspeak"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(json.dumps({
        "meeting": {
            "intel_provider": "cloud",
            "intel_cloud_base_url": EDGE_URL,
            "intel_cloud_model": EDGE_MODEL,
        }
    }))
    env = dict(os.environ, HOME=str(home), HOLDSPEAK_HUB_TOKEN=TOKEN)
    logf = open(log_path, "w")
    # its own process GROUP: `uv run` wraps a child python, and killing only
    # the wrapper orphans a still-polling worker (the first run proved it).
    # -v: the worker's honest log lines otherwise go only to the temp HOME's
    # log file; verbose mirrors them to stderr, which THIS capture reads.
    return subprocess.Popen(
        ["uv", "run", "holdspeak", "-v", "mesh", "serve", "--hub", BASE, "--node", NODE],
        env=env, stdout=logf, stderr=subprocess.STDOUT,
        cwd=str(Path(__file__).resolve().parent.parent),
        start_new_session=True,
    )


def main():
    if not TOKEN:
        sys.exit("no web auth token found")
    before = api("GET", "/api/settings")
    prior_intel = before["meeting"].get("intel_profile_id")
    prior_dict = before["dictation"]["runtime"].get("profile_id")
    print(f"prior assignments: intel={prior_intel!r} dictation={prior_dict!r}")

    log_path = Path(tempfile.mkstemp(prefix="hs85-worker-", suffix=".log")[1])
    worker = start_worker(log_path)
    profile_id = None
    recipe = None
    walk_meeting = None
    try:
        # Beat 1 — the edge goes live (its polling is the heartbeat).
        deadline = time.time() + 30
        while time.time() < deadline:
            live = any(
                r.get("node") == NODE
                for r in api("GET", "/api/models")["models"]
                if r.get("node")
            )
            time.sleep(1)
            doc = subprocess.run(
                ["uv", "run", "holdspeak", "doctor"],
                capture_output=True, text=True, timeout=120,
                cwd=str(Path(__file__).resolve().parent.parent),
            )
            edge_line = next(
                (ln for ln in doc.stdout.splitlines() if "Mesh edges" in ln), ""
            )
            if f"{NODE}: live" in edge_line:
                break
        else:
            sys.exit("the worker never went live")
        print(f"beat 1: {edge_line.strip()!r}")

        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.set_viewport_size({"width": 1280, "height": 900})

            # Beat 2 — author THE profile in the editor (?token once; the
            # HS-83 wrapper carries it after — regression cover).
            pg.goto(f"{BASE}/profiles?token={TOKEN}", wait_until="networkidle")
            assert "token=" not in pg.url, "the token must scrub"
            pg.click(".pf-btn.primary")
            pg.fill("input[placeholder='OpenRouter · Claude Sonnet']", PROFILE_NAME)
            pg.click(".pf-segmented button:has-text('Mesh node')")
            pg.fill("input[placeholder='walk-edge']", NODE)
            pg.fill("input[placeholder='qwen3.5-4b']", f"{EDGE_MODEL}-via-edge")
            pg.click(".pf-drawer-foot button[type='submit']")
            pg.wait_for_selector(f".pf-name:has-text('{PROFILE_NAME}')", timeout=8_000)
            pg.wait_for_timeout(600)
            card = pg.locator(".pf-card", has=pg.locator(f".pf-name:has-text('{PROFILE_NAME}')"))
            state = card.locator("dd.pf-live, dd.pf-offline").first.inner_text()
            assert state.startswith("live ("), f"the card must read live, got {state!r}"
            pg.screenshot(path=str(OUT / "hs-85-05-walk-profile-live.png"))
            profile_id = next(
                p_["id"] for p_ in api("GET", "/api/profiles")["profiles"]
                if p_["name"] == PROFILE_NAME
            )
            print(f"beat 2: profile authored in the editor → {profile_id} ({state})")

            # Beat 3 — an agent on the edge answers; the worker's log proves it.
            recipe = api("POST", "/api/recipes", json={
                "id": "recipe_walk85", "name": "Walk85", "avatar": "🕸️",
                "role": "answers briefly", "system_prompt": "Answer in one short sentence.",
                "profile_id": profile_id,
            })["recipe"]
            pg.goto(f"{BASE}/", wait_until="networkidle")
            pg.wait_for_selector(".desk-obj", timeout=10_000)
            pg.add_style_tag(content=".desk-mc, .desk-mc-tab { display: none !important; }")
            pg.locator(".desk-rail-avatar[title='Walk85']").click()
            pg.wait_for_selector(".desk-chat", timeout=6_000)
            pg.fill(".desk-chat-composer input", "In one short sentence, what is a mesh?")
            pg.click(".desk-chat-composer .desk-chip:has-text('Send')")
            pg.wait_for_selector(".desk-chat-meta .egress-badge", timeout=180_000)
            badge = pg.inner_text(".desk-chat-meta .egress-badge")
            print(f"beat 3: agent badge = {badge!r}")
            assert "mesh" in badge and NODE in badge, "the badge must wear the mesh + node"
            worker_log = log_path.read_text()
            assert "COMPLETED on node walk-edge" in worker_log, \
                "the worker's log must prove the run executed there"
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / "hs-85-05-walk-agent-mesh-badge.png"))

            # Beat 4 — meeting intel picked onto the edge, artifacts through it.
            # A FRESH transcript each run: reroute dedup keys off the transcript
            # hash, so replaying the rig against a fixed meeting proves nothing
            # (the third run's find — every plugin came back "deduped").
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            txt = (
                f"Karol: The mesh edge walk of {stamp} needs a delivery readout.\n"
                "Karol: The relay queue ships this sprint and the worker polls "
                "every three seconds.\n"
                "Karol: The next milestone is the liveness door, owned by the "
                "hub team, due Friday.\n"
                "Karol: If the edge dies mid-run we refuse fast and name the "
                "node instead of hanging.\n"
            )
            imp = requests.post(
                f"{BASE}/api/meetings/import", headers=H, timeout=60,
                files={"file": ("walk85.txt", txt.encode(), "text/plain")},
                data={"title": f"Walk85 {stamp}"},
            )
            imp.raise_for_status()
            walk_meeting = imp.json()["meeting_id"]
            deadline = time.time() + 30
            while time.time() < deadline:
                detail = api("GET", f"/api/meetings/{walk_meeting}")
                if detail.get("intel_status") != "importing":
                    break
                time.sleep(0.5)
            pg.goto(f"{BASE}/settings", wait_until="networkidle")
            pg.click("text=Cloud & advanced")
            pg.wait_for_selector("#set-intel-profile", timeout=8_000)
            pg.select_option("#set-intel-profile", profile_id)
            pg.click("button:has-text('Save settings')")
            pg.wait_for_selector("text=Settings saved", timeout=8_000)
            completed_before = log_path.read_text().count("COMPLETED on node")
            out = subprocess.run(
                ["uv", "run", "holdspeak", "intel", "--reroute", walk_meeting,
                 "--profile", "delivery"],
                capture_output=True, text=True, timeout=600,
                cwd=str(Path(__file__).resolve().parent.parent),
            )
            assert out.returncode == 0, f"reroute failed: {out.stderr[-400:]}"
            payload = json.loads(out.stdout[out.stdout.index("{"):])
            assert payload.get("executed") is True and payload.get("artifacts_saved"), payload
            completed_after = log_path.read_text().count("COMPLETED on node")
            assert completed_after > completed_before, "the reroute must run through the edge"
            print(
                f"beat 4: reroute of fresh meeting {walk_meeting} executed THROUGH "
                f"the edge; artifacts_saved={payload['artifacts_saved']} (worker "
                f"completions {completed_before}→{completed_after})"
            )

            # Beat 5 — dictation picked onto the edge; a dry-run rewrites there.
            pg.goto(f"{BASE}/dictation", wait_until="networkidle")
            pg.click("#section-runtime")
            pg.wait_for_function(
                "document.querySelectorAll('#rt-profile option').length > 1", timeout=8_000
            )
            pg.select_option("#rt-profile", profile_id)
            pg.click("#rt-btn-save")
            pg.wait_for_selector("#rt-msg .ok-box", timeout=8_000)
            completed_before = log_path.read_text().count("COMPLETED on node")
            dry = api("POST", "/api/dictation/dry-run", json={
                "utterance": "please add a todo saying the mesh edge walk passed",
            })
            assert "error" not in dry, f"dry-run error: {dry}"
            completed_after = log_path.read_text().count("COMPLETED on node")
            assert completed_after > completed_before, "the dry-run must run through the edge"
            print(f"beat 5: dictation dry-run THROUGH the edge (completions "
                  f"{completed_before}→{completed_after}; keys {sorted(dry)[:6]})")

            # Beat 6 — kill the worker: offline honestly, refuse fast, by name.
            os.killpg(os.getpgid(worker.pid), signal.SIGINT)
            worker.wait(timeout=30)
            print("beat 6: worker stopped; waiting out the liveness window…")
            time.sleep(16)
            row = next(
                r for r in api("GET", "/api/models")["models"]
                if r.get("node") == NODE
            )
            assert row["live"] is False, "the models door must read offline"
            t0 = time.monotonic()
            r = requests.post(
                f"{BASE}/api/ask", headers=H, timeout=30,
                json={"prompt": "Go", "profile_id": profile_id},
            )
            elapsed = time.monotonic() - t0
            assert r.status_code == 400, f"expected 400, got {r.status_code}"
            assert NODE in r.json()["error"] and "offline" in r.json()["error"]
            assert elapsed < 5.0, f"the refusal took {elapsed:.1f}s — must be fast"
            print(
                f"beat 6: offline refusal in {elapsed:.2f}s → {r.json()['error']!r}"
            )
            pg.goto(f"{BASE}/", wait_until="networkidle")
            pg.wait_for_selector(".desk-rail-model.is-offline", timeout=10_000)
            pg.add_style_tag(content=".desk-mc, .desk-mc-tab { display: none !important; }")
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / "hs-85-05-walk-rail-offline.png"))
            b.close()

        print("HS-85-05 LIVE WALK: all six beats PROVEN — the request moved; "
              "the model and the key never did")
    finally:
        try:
            if worker.poll() is None:
                os.killpg(os.getpgid(worker.pid), signal.SIGKILL)
        except Exception:
            pass
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
        if walk_meeting:
            try:
                api("DELETE", f"/api/meetings/{walk_meeting}")
            except Exception:
                pass
        if profile_id:
            try:
                api("DELETE", f"/api/profiles/{profile_id}")
            except Exception:
                pass
        print(f"cleanup done; worker log kept at {log_path}")


if __name__ == "__main__":
    main()
