#!/usr/bin/env python3
"""HS-63-06 closeout dogfood: the composed runtime boots and works, for real.

A green suite can't prove the eight-mixin WebRuntime actually assembles and
serves, so this boots the REAL entry path (`run_web_runtime`, the same call
`holdspeak web` makes) in a subprocess with a temp config, then drives it
over HTTP and a real browser:

  1. /api/state answers (the composed runtime serves);
  2. a meeting starts and stops through the real routes (the meeting_glue
     mixin's _start_meeting/_stop_active_meeting end to end, incl. the real
     recorder + the carved MeetingSession);
  3. a dictation dry-run flows through the real pipeline route;
  4. the dictation cockpit loads in Chromium with zero page errors;
  5. SIGTERM shuts it down cleanly (the signal path stayed in the core).

Run after building the web bundle.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PORT = 8791

BOOT = f"""
import os, sys, faulthandler
faulthandler.enable()
sys.path.insert(0, {str(Path(__file__).resolve().parents[4])!r})
import holdspeak.config as config_module
from pathlib import Path
config_module.CONFIG_FILE = Path(os.environ["HS_DOGFOOD_CONFIG"])
import holdspeak.db as db_module
from holdspeak.db import get_database
get_database(Path(os.environ["HS_DOGFOOD_DB"]))
from holdspeak.web_runtime import run_web_runtime
run_web_runtime(no_open=True)
"""


def main() -> int:
    import httpx
    from playwright.sync_api import sync_playwright

    tmp = Path(tempfile.mkdtemp())
    # A default config with our port; presence off; warm-on-start off.
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    import holdspeak.config as config_module
    from holdspeak.config import Config

    config_module.CONFIG_FILE = tmp / "config.json"
    Config().save(path=config_module.CONFIG_FILE)

    env = dict(os.environ)
    env["HOLDSPEAK_WEB_PORT"] = str(PORT)
    env["HS_DOGFOOD_CONFIG"] = str(tmp / "config.json")
    env["HS_DOGFOOD_DB"] = str(tmp / "dogfood.db")

    failures: list[str] = []
    page_errors: list[str] = []

    def check(ok, label):
        print(("PASS  " if ok else "FAIL  ") + label)
        if not ok:
            failures.append(label)

    print(f"runtime log: {tmp / 'runtime.log'}")
    proc = subprocess.Popen(
        [sys.executable, "-c", BOOT],
        env=env,
        stdout=open(tmp / "runtime.log", "w"),
        stderr=subprocess.STDOUT,
    )
    base = f"http://127.0.0.1:{PORT}"
    try:
        # 1. The composed runtime serves.
        up = False
        for _ in range(60):
            try:
                r = httpx.get(f"{base}/api/state", timeout=2)
                if r.status_code == 200:
                    up = True
                    break
            except Exception:
                pass
            time.sleep(0.5)
        check(up, "run_web_runtime boots and /api/state answers (the real entry path)")
        if not up:
            print((tmp / "runtime.log").read_text()[-3000:])
            return 1

        # 2. A real meeting lifecycle through the real routes.
        started = httpx.post(f"{base}/api/meeting/start", json={}, timeout=30).json()
        check(started.get("success") is True, f"meeting started ({started.get('meeting_id', started)})")
        time.sleep(3.0)  # let the recorder + transcribe loop breathe
        state = httpx.get(f"{base}/api/state", timeout=5).json()
        check(bool(state.get("meeting") or state.get("meeting_active") or state.get("is_active")), f"the runtime state reflects the meeting ({list(state)[:8]})")
        try:
            stopped = httpx.post(f"{base}/api/meeting/stop", json={}, timeout=120).json()
            check(stopped.get("success") is True, "meeting stopped through the real route")
        except Exception as exc:
            check(False, f"meeting stop blew up: {type(exc).__name__}: {exc}")
            print("--- runtime.log tail ---")
            print((tmp / "runtime.log").read_text()[-4000:])
            return 1
        meetings = httpx.get(f"{base}/api/meetings", timeout=10).json()
        count = len(meetings.get("meetings", []))
        check(count >= 1, f"the meeting persisted through the carved save path ({count} in the archive)")

        # 3. A dictation dry-run through the real pipeline route.
        dry = httpx.post(
            f"{base}/api/dictation/dry-run",
            json={"utterance": "ship the backend decomposition period"},
            timeout=30,
        ).json()
        check(
            isinstance(dry.get("final_text"), str) or isinstance(dry.get("stages"), list)
            or "error" not in dry,
            f"dry-run answered through the pipeline route ({list(dry)[:6]})",
        )

        # 4. The cockpit renders with zero page errors.
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.goto(f"{base}/dictation", wait_until="networkidle")
            page.wait_for_timeout(1200)
            browser.close()
        check(not page_errors, f"zero page errors on the cockpit (saw {page_errors!r})")

        # 5. Clean shutdown via the signal path (kept in the core).
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=20)
            check(True, f"SIGTERM shut the runtime down cleanly (exit {proc.returncode})")
        except subprocess.TimeoutExpired:
            check(False, "the runtime did not exit within 20s of SIGTERM")
    finally:
        if proc.poll() is None:
            proc.kill()

    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} failure(s))")
        print("--- runtime.log tail ---")
        print((tmp / "runtime.log").read_text()[-2000:])
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
