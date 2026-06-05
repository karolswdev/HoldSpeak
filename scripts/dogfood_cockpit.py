#!/usr/bin/env python3
"""HS-40-06 dogfood: configure the copilot from the UI, correct, restart, persist.

Boots a server over a persistent config file + DB, configures the cockpit and
records a correction **entirely through the web UI** (no file editing), then
boots a *fresh* server over the same paths (a simulated restart) and confirms
the config + the correction survived. Writes a transcript + a post-restart
screenshot.

    .venv/bin/python scripts/dogfood_cockpit.py <out.png>
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


def _server(db_path: Path):
    from holdspeak.db import Database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    reset_database()
    db = Database(db_path)
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        ),
        dictation_corrections_repository=db.dictation_corrections,
    )
    return server, db


def _open_runtime(page, url):
    page.goto(f"{url}/dictation", wait_until="networkidle")
    page.click("#section-runtime")
    page.wait_for_selector("#rt-rewrite-seg", state="visible")
    page.wait_for_function(
        "document.getElementById('rt-meta-banner').textContent.includes('pipeline:')"
    )
    page.wait_for_timeout(150)


def main(out_path: str) -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    db_path = tmp / "holdspeak.db"
    log: list[str] = []

    # ── Session 1: configure + correct, entirely in the UI ──
    server, _db = _server(db_path)
    url = server.start()
    time.sleep(1.0)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1400})
        _open_runtime(page, url)
        # Configure the depth knobs via the cockpit.
        page.check("#rt-enabled")
        page.check("#rt-stage-rewriter")
        page.click('#rt-rewrite-seg .seg-btn[data-value="3"]')
        page.check("#rt-corrections-enabled")
        page.check("#rt-target-detect-llm-enabled")
        page.click("#rt-btn-save")
        page.wait_for_selector("#rt-msg .ok-box")
        log.append("session 1: configured via UI — pipeline on, 3 passes, corrections on, infer-target on")
        # Record a correction via the Memory tab add form.
        page.click("#section-memory")
        page.wait_for_function(
            "document.getElementById('mem-meta-banner').textContent.includes('remembered')"
        )
        page.fill("#mem-add-text", "ship the ledger reconciliation fix")
        page.fill("#mem-add-value", "agent_task_buildout")
        page.click("#mem-add-btn")
        page.wait_for_function("document.querySelectorAll('.mem-item').length >= 1")
        n1 = page.eval_on_selector_all(".mem-item", "els => els.length")
        log.append(f"session 1: recorded a correction in the Memory tab — {n1} card(s) shown")
        browser.close()
    server.stop()
    time.sleep(0.3)

    # ── Session 2: a fresh server over the SAME config + DB (restart) ──
    server2, db2 = _server(db_path)
    url2 = server2.start()
    time.sleep(1.0)
    persisted = db2.dictation_corrections.recent_corrections()
    log.append(f"session 2 (restart): durable store has {len(persisted)} correction(s): "
               + ", ".join(f"{r.kind}:{r.gist}→{r.value}" for r in persisted))
    from holdspeak.config import Config

    cfg = Config.load().dictation.pipeline
    log.append(
        "session 2 (restart): config persisted — "
        f"enabled={cfg.enabled} passes={cfg.rewrite_passes} "
        f"corrections={cfg.corrections_enabled} infer_target={cfg.target_detect_llm_enabled}"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1400})
        page.goto(f"{url2}/dictation", wait_until="networkidle")
        page.click("#section-memory")
        page.wait_for_function(
            "document.getElementById('mem-meta-banner').textContent.includes('remembered')"
        )
        page.wait_for_timeout(300)
        n2 = page.eval_on_selector_all(".mem-item", "els => els.length")
        log.append(f"session 2 (restart): Memory tab shows {n2} persisted correction card(s)")
        page.screenshot(path=out_path, full_page=True)
        browser.close()
    server2.stop()

    ok = len(persisted) >= 1 and cfg.enabled and cfg.rewrite_passes == 3
    print("\n".join(log))
    print(f"\nDOGFOOD {'PASSED' if ok else 'FAILED'} — correction + config survived the restart")
    print(f"Wrote {out_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "dogfood.png"
    raise SystemExit(main(out))
