#!/usr/bin/env python3
"""Capture a screenshot of the Phase-40 Copilot Setup cockpit (HS-40-03/04).

Starts a real MeetingWebServer (serving the built bundle), drives the
`/dictation` runtime tab with Playwright, turns the depth knobs on so the rich
state is visible, and writes a PNG. Run after `cd web && npm run build`:

    .venv/bin/python scripts/screenshot_cockpit.py <out.png>
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


def main(out_path: str) -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import Database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    # Isolate config + DB so the shot is deterministic and touches no real state.
    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = Database(tmp / "cockpit.db")
    # Seed a couple of persisted corrections so the memory state is non-empty.
    db.dictation_corrections.record_correction(
        kind="intent", gist="fix the cli login flow", value="code_exercise"
    )
    db.dictation_corrections.record_correction(
        kind="target", gist="route the deploy notes to codex", value="codex_cli"
    )

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        ),
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 1600})
            page.goto(f"{url}/dictation", wait_until="networkidle")
            # Switch to the runtime cockpit tab.
            page.click('.scope-row button[data-section="runtime"]')
            page.wait_for_selector("#rt-rewrite-seg", state="visible")
            # loadRuntime() is async — wait for it to populate (the meta banner
            # fills in) before interacting, or renderRuntime resets our edits.
            page.wait_for_function(
                "document.getElementById('rt-meta-banner').textContent.includes('pipeline:')"
            )
            page.wait_for_timeout(200)
            # Show rich depth state: enable pipeline + rewrite stage, 3 passes,
            # corrections on, infer-target on (reveals the threshold).
            page.check("#rt-enabled")
            page.check("#rt-stage-rewriter")
            page.click('#rt-rewrite-seg .seg-btn[data-value="3"]')
            page.check("#rt-corrections-enabled")
            page.check("#rt-target-detect-llm-enabled")
            page.wait_for_selector("#rt-target-below-wrap", state="visible")
            page.wait_for_timeout(400)
            page.screenshot(path=out_path, full_page=True)
            browser.close()
    finally:
        server.stop()

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "cockpit.png"
    raise SystemExit(main(out))
