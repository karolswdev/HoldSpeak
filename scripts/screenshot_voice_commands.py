#!/usr/bin/env python3
"""HS-52-05: capture the Voice Commands board, reproducibly.

Boots one real ``MeetingWebServer`` over a temp config seeded with voice macros of
all four kinds (no mic, no LLM, no real command ever fired), opens ``/commands``, and
screenshots the populated board, the empty state, and the per-kind editor including
the shell danger treatment. Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python scripts/screenshot_voice_commands.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

OUT_DIR = (
    Path(__file__).parent.parent
    / "pm" / "roadmap" / "holdspeak" / "phase-52-voice-macros" / "screenshots"
)

POPULATED = [
    ("terminal", "launch_app", "Terminal"),
    ("docs", "open_url", "https://github.com/karolswdev/HoldSpeak"),
    ("ship it", "shell", "git push origin HEAD"),
    ("standup", "type_text", "## Standup\n- Yesterday:\n- Today:\n- Blockers:"),
]


def _capture(seed, suffix: str) -> None:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.config import Config, MacrosConfig, VoiceMacro, VoiceMacroAction
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    cfg = Config()
    if seed:
        cfg.dictation.macros = MacrosConfig(
            enabled=True,
            items=[VoiceMacro(k, VoiceMacroAction(kind, payload)) for (k, kind, payload) in seed],
        )
    cfg.save(path=config_module.CONFIG_FILE)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}))
    )
    url = server.start()
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1180, "height": 1000})
            page.goto(f"{url}/commands", wait_until="networkidle")
            page.wait_for_timeout(700)
            page.screenshot(path=str(OUT_DIR / f"board-{suffix}.png"))
            print(f"Wrote {OUT_DIR / ('board-' + suffix + '.png')}")

            if seed:
                # The add/edit editor, then the shell danger treatment within it.
                page.click(".vc-add-card")
                page.wait_for_selector("[data-vc-editor] .vc-editor", state="visible", timeout=5000)
                page.fill("[data-vc-keyword]", "open notes")
                page.click('[data-vc-kind="open_url"]')
                page.fill('[data-vc-payload-input="open_url"]', "https://example.com/notes")
                page.wait_for_timeout(300)
                page.screenshot(path=str(OUT_DIR / "editor-open-url.png"))
                print(f"Wrote {OUT_DIR / 'editor-open-url.png'}")

                page.click('[data-vc-kind="shell"]')
                page.fill('[data-vc-payload-input="shell"]', "git status")
                page.wait_for_timeout(300)
                page.screenshot(path=str(OUT_DIR / "editor-shell-danger.png"))
                print(f"Wrote {OUT_DIR / 'editor-shell-danger.png'}")
            browser.close()
    finally:
        server.stop()


def main() -> int:
    _capture(POPULATED, "populated")
    _capture(None, "empty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
