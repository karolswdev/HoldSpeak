#!/usr/bin/env python3
"""HS-47-06: capture the project-knowledge surfaces, reproducibly.

Boots one real `MeetingWebServer` over a temp DB (no mic, no LLM) and drives
`/dictation` with Playwright to capture the Phase-47 surfaces into
`docs/assets/screenshots/`:

    project-knowledge-facts.png    the Project Facts tab (explainer + empty state)
    project-knowledge-context.png  the Project Context tab (explainer + empty state)
    project-knowledge-setup.png    the guided "Set up project knowledge" panel
    project-knowledge-nudge.png    the ambient discovery nudge

The server is launched from the repo cwd, which has no `.holdspeak/project.yaml`
and no `.hs/`, so every empty state and the nudge render naturally. Run after
building the web bundle:

    (cd web && npm run build)
    .venv/bin/python scripts/screenshot_project_knowledge.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

OUT_DIR = Path(__file__).parent.parent / "docs" / "assets" / "screenshots"


def main() -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = get_database(tmp / "shot.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 1200})

            page.goto(f"{url}/dictation", wait_until="networkidle")
            page.wait_for_selector("#kn-nudge", state="visible", timeout=5000)
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT_DIR / "project-knowledge-nudge.png"))

            page.click('.scope-row button[data-section="kb"]')
            page.wait_for_selector("#kb-empty", state="visible", timeout=5000)
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT_DIR / "project-knowledge-facts.png"), full_page=True)

            page.click('.scope-row button[data-section="hs"]')
            page.wait_for_selector("#hs-empty", state="visible", timeout=5000)
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT_DIR / "project-knowledge-context.png"), full_page=True)

            page.click("#hs-empty-setup")
            page.wait_for_selector("#hs-setup", state="visible", timeout=5000)
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT_DIR / "project-knowledge-setup.png"), full_page=True)

            for name in ("nudge", "facts", "context", "setup"):
                print(f"Wrote {OUT_DIR / ('project-knowledge-' + name + '.png')}")
            browser.close()
    finally:
        server.stop()
        reset_database()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
