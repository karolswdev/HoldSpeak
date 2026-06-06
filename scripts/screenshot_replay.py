#!/usr/bin/env python3
"""Capture the Phase-45 replay before→after (HS-45-04).

Seeds a journal entry, records a target correction for its transcript, then in
the Journal tab clicks Replay and screenshots the before → after diff showing
the routing changed (the "it learned" payoff). No mic, no LLM endpoint. Run
after `cd web && npm run build`:

    .venv/bin/python scripts/screenshot_replay.py <out.png>
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
        description: a note block
        match: {examples: ["jot this down"]}
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

    Config.load = classmethod(  # type: ignore[assignment]
        lambda cls, *a, **k: Config(
            dictation=DictationConfig(
                pipeline=DictationPipelineConfig(
                    enabled=True, stages=["kb-enricher"], corrections_enabled=True
                ),
                runtime=LLMRuntimeConfig(),
            )
        )
    )
    reset_database()
    db = Database(tmp / "journal.db")
    entry = db.dictation_journal.record(
        source="dictation",
        transcript="send the weekly digest to the browser tab",
        final_text="send the weekly digest to the browser tab",
        block_id="quick_note",
        target_profile="terminal_shell",
        confidence=0.64,
        project_root=str(proj),
        stage_ms={"intent-router": 240.0, "kb-enricher": 2.0},
        total_ms=242.0,
    )
    # The user taught the copilot this should target the browser.
    db.dictation_corrections.record_correction(
        kind="target", gist="send the weekly digest to the browser tab", value="browser"
    )

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
            page = browser.new_page(viewport={"width": 1120, "height": 1000})
            page.goto(f"{url}/dictation", wait_until="networkidle")
            page.click('.scope-row button[data-section="journal"]')
            page.wait_for_selector(".journal-card", state="visible")
            page.click(f'button[data-journal-replay="{entry.id}"]')
            page.wait_for_selector(".replay-changed", state="visible")
            page.wait_for_timeout(400)
            page.screenshot(path=out_path, full_page=True)
            browser.close()
    finally:
        server.stop()

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "replay.png"
    raise SystemExit(main(out))
