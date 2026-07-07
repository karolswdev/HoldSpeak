"""HSM-25-03 — the LIVE walk: the phone serves the mesh, proven on the wire.

The REAL hub runs on 127.0.0.1:8765; the iPad SIMULATOR runs the real app
(built from source) with the consent toggle ON, serving as node `iPad` with
its OWN active profile pointing at the .43 llama.cpp — the hub knows only
the node name; the DEVICE knows the provider. A desk ask against a meshNode
profile executes on the device; killing the app reads offline everywhere
and refuses fast, by name.

Beats:
1. The app launches consented — the hub's models door shows node `iPad`
   live; the device Settings card reads "serving as iPad".
2. A meshNode profile naming `iPad` is authored hub-side; its /profiles
   card reads live.
3. An ask against that profile returns THROUGH the device: egress
   `{scope: mesh, host: iPad}`, real output.
4. The app is KILLED: the models door reads offline; a forced ask refuses
   fast (< 5s) naming the node; the /profiles card reads offline.
Cleanup: the hub profile deleted; the sim's consent flag reset.

Prereqs: the app installed on the booted simulator (scripts in evidence),
the hub live, the .43 endpoint up.
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
SIM = os.environ.get("HS_WALK_SIM", "8B48445F-0D62-4F63-BB24-1AB43BA15CAF")
BUNDLE = "dev.holdspeak.mobile"
NODE = "iPad"
EDGE_URL = "http://192.168.1.43:8080/v1"
EDGE_MODEL = "Qwen3.5-9B-Q6_K"
OUT = Path("pm/roadmap/holdspeak-mobile/phase-25-serve-the-mesh/screenshots")
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


def simctl(*args, **kw):
    return subprocess.run(["xcrun", "simctl", *args], capture_output=True,
                          text=True, timeout=120, **kw)


def seed_device():
    """Nothing persisted: the app seeds ITSELF from the walk env (the
    demo-env house pattern; `HS_WALK_SERVE_URL` in InferenceConfigStore.init
    adds an ephemeral endpoint profile as the active target + consent ON).
    Seeding the container plist from outside loses to cfprefsd — the first
    runs served with the migrated on-device profile while the plist on disk
    held the seed."""
    simctl("terminate", SIM, BUNDLE)


def launch_app():
    env = dict(os.environ,
               SIMCTL_CHILD_HS_CLASSIC_HOME="1",
               SIMCTL_CHILD_HS_DEMO_SETTINGS="1",
               SIMCTL_CHILD_HS_WALK_SERVE_URL=EDGE_URL,
               SIMCTL_CHILD_HS_WALK_SERVE_MODEL=EDGE_MODEL,
               SIMCTL_CHILD_HS_DESKTOP_HOST="127.0.0.1",
               SIMCTL_CHILD_HS_DESKTOP_PORT="8765",
               SIMCTL_CHILD_HS_DESKTOP_TOKEN=TOKEN,
               SIMCTL_CHILD_HS_DESKTOP_NAME="Karol's Mac")
    subprocess.run(["xcrun", "simctl", "launch", SIM, BUNDLE],
                   env=env, capture_output=True, text=True, timeout=60, check=True)


def node_row():
    return next((r for r in api("GET", "/api/models")["models"]
                 if r.get("node") == NODE), None)


def main():
    if not TOKEN:
        sys.exit("no web auth token found")
    profile_id = None
    try:
        # Beat 1 — the consented app serves; doctor's "Mesh edges" reads the
        # node live. (The models door only grows a row once a meshNode
        # PROFILE names the node — that is beat 2's assert.)
        seed_device()
        launch_app()
        deadline = time.time() + 45
        edge_line = ""
        while time.time() < deadline:
            doc = subprocess.run(
                ["uv", "run", "holdspeak", "doctor"],
                capture_output=True, text=True, timeout=120,
                cwd=str(Path(__file__).resolve().parent.parent),
            )
            edge_line = next(
                (ln for ln in doc.stdout.splitlines() if "Mesh edges" in ln), "")
            if f"{NODE}: live" in edge_line:
                break
            time.sleep(1)
        else:
            sys.exit(f"node {NODE} never went live on the hub")
        print(f"beat 1: {edge_line.strip()!r}")
        time.sleep(2)
        simctl("io", SIM, "screenshot",
               str((OUT / "hsm-25-03-walk-device-serving.png").resolve()))

        # Beat 2 — the meshNode profile naming the device, and its live card.
        profile_id = api("POST", "/api/profiles", json={
            "name": "Phone Edge", "kind": "meshNode", "node": NODE,
            "model": f"{EDGE_MODEL}-via-{NODE}",
        })["profile"]["id"]
        row = node_row()
        assert row is not None and row.get("live"), \
            f"the models door must now carry the live node row, got {row}"
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.set_viewport_size({"width": 1280, "height": 900})
            pg.goto(f"{BASE}/profiles?token={TOKEN}", wait_until="networkidle")
            card = pg.locator(".pf-card", has=pg.locator(".pf-name:has-text('Phone Edge')"))
            state = card.locator("dd.pf-live, dd.pf-offline").first.inner_text()
            assert state.startswith("live ("), f"the card must read live, got {state!r}"
            pg.screenshot(path=str(OUT / "hsm-25-03-walk-hub-card-live.png"))
            print(f"beat 2: profile {profile_id} card reads {state!r}")

            # Beat 3 — the ask executes ON the device (its provider, its .43).
            t0 = time.monotonic()
            ask = api("POST", "/api/ask", json={
                "prompt": "In one short sentence, what serves this answer?",
                "profile_id": profile_id,
            })
            took = time.monotonic() - t0
            egress = ask.get("egress") or {}
            assert egress.get("scope") == "mesh" and egress.get("host") == NODE, egress
            assert str(ask.get("output") or "").strip(), "the answer must be real"
            print(f"beat 3: ask THROUGH the device in {took:.1f}s — egress "
                  f"{egress}; output {ask['output'][:70]!r}")

            # Beat 4 — kill the app: offline honestly, refuse fast, by name.
            simctl("terminate", SIM, BUNDLE)
            print("beat 4: app killed; waiting out the liveness window…")
            time.sleep(16)
            row = node_row()
            assert row is not None and row.get("live") is False, row
            t0 = time.monotonic()
            r = requests.post(f"{BASE}/api/ask", headers=H, timeout=30,
                              json={"prompt": "Go", "profile_id": profile_id})
            elapsed = time.monotonic() - t0
            assert r.status_code == 400, f"expected 400, got {r.status_code}"
            assert NODE in r.json()["error"] and "offline" in r.json()["error"]
            assert elapsed < 5.0, f"refusal took {elapsed:.1f}s"
            print(f"beat 4: offline refusal in {elapsed:.2f}s → {r.json()['error']!r}")
            pg.reload(wait_until="networkidle")
            state = card.locator("dd.pf-live, dd.pf-offline").first.inner_text()
            assert state.startswith("offline ("), state
            pg.screenshot(path=str(OUT / "hsm-25-03-walk-hub-card-offline.png"))
            b.close()

        print("HSM-25-03 LIVE WALK: all four beats PROVEN — the phone served; "
              "the model and the key never moved")
    finally:
        if profile_id:
            try:
                api("DELETE", f"/api/profiles/{profile_id}")
            except Exception:
                pass
        simctl("terminate", SIM, BUNDLE)  # the env seed dies with the process
        print("cleanup done")


if __name__ == "__main__":
    main()
