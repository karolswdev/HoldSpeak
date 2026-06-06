#!/usr/bin/env python3
"""Capture the Phase-45 moment-of-truth (in-flow correct-and-teach) (HS-45-03).

Starts a real MeetingWebServer (durable journal + corrections repos) over a
seeded local project with the dictation pipeline enabled, runs an offline
dry-run on the Dry-run tab (journals a row → the in-moment fix affordance
appears), opens the fix form, teaches a correction, and screenshots the
"Taught ✓" state. No mic, no LLM endpoint. Run after `cd web && npm run build`:

    .venv/bin/python scripts/screenshot_moment_of_truth.py <out.png>
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

_BLOCKS = dedent(
    """
    version: 1
    default_match_confidence: 0.6
    blocks:
      - id: quick_note
        description: a quick note block
        match: {examples: ["jot this down", "note to self"]}
        inject: {mode: replace, template: "{raw_text}"}
    """
).strip()


def main(out_path: str) -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.config import (
        Config,
        DictationConfig,
        DictationPipelineConfig,
        LLMRuntimeConfig,
    )
    from holdspeak.db import Database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    proj = tmp / "ledgerline"
    (proj / ".holdspeak").mkdir(parents=True)
    (proj / ".holdspeak" / "blocks.yaml").write_text(_BLOCKS, encoding="utf-8")
    (proj / "pyproject.toml").write_text('[project]\nname="ledgerline"\n', encoding="utf-8")

    # Pipeline ON, kb-enricher (runs offline) so a dry-run journals a row.
    Config.load = classmethod(  # type: ignore[assignment]
        lambda cls, *a, **k: Config(
            dictation=DictationConfig(
                pipeline=DictationPipelineConfig(enabled=True, stages=["kb-enricher"]),
                runtime=LLMRuntimeConfig(),
            )
        )
    )
    reset_database()
    db = Database(tmp / "journal.db")

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        ),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1120, "height": 900})
            page.goto(f"{url}/dictation", wait_until="networkidle")
            # Point at the seeded project first (Apply resets the dry-run panel),
            # then type the utterance and run.
            page.fill("#project-root-override", str(proj))
            page.click("#project-root-apply")
            page.wait_for_timeout(300)
            page.click('.scope-row button[data-section="dry-run"]')
            page.wait_for_selector("#dry-utterance", state="visible")
            page.fill("#dry-utterance", "ship the new billing flow to the agent and write a test")
            page.click("#dry-btn-run")
            page.wait_for_selector("#moment-fix-open", state="visible")
            page.click("#moment-fix-open")
            page.wait_for_selector("#moment-form", state="visible")
            page.select_option("#moment-kind", "intent")
            page.fill("#moment-value", "agent_task_buildout")
            page.click("#moment-submit")
            page.wait_for_selector(".moment-done", state="visible")
            page.wait_for_timeout(400)
            page.screenshot(path=out_path, full_page=True)
            browser.close()
    finally:
        server.stop()

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "moment.png"
    raise SystemExit(main(out))
