#!/usr/bin/env python3
"""HS-62-01 dogfood: the egress badge renders on live Qlippy cards.

A real server, the real /presence page with the mascot on, real cards
through the shell. Asserted: the cloud card shows "☁ slack" (the target
survives on the badge), the local card shows "⌂ Local", the badge is
actually styled (computed border-radius — the Astro scoped-CSS trap check),
and NO privacy paragraph exists anywhere in the card DOM.

Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-62-quiet-trust/dogfood_story01.py
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

OUT_DIR = Path(__file__).resolve().parent / "screenshots"


def main() -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.config import Config
    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    config = Config()
    config.presence.enabled = True
    config.presence.mascot = True
    config.save(path=config_module.CONFIG_FILE)
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        ),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    failures: list[str] = []
    page_errors: list[str] = []

    def check(ok: bool, label: str) -> None:
        print(("PASS  " if ok else "FAIL  ") + label)
        if not ok:
            failures.append(label)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 900, "height": 700})
            page.on("pageerror", lambda err: page_errors.append(str(err)))
            page.goto(f"{url}/presence", wait_until="networkidle")
            page.wait_for_timeout(800)

            # 1. A cloud-scoped decision card (the slack proposal shape).
            page.evaluate(
                """window.qlippyCard.present({
                    sprite: "alert", glyph: "bang",
                    headline: "A decision needs you",
                    detail: "slack · post_message",
                    preview: "*Weekly sync* (2026-06-12)\\n• Priya: wire the rate limiter",
                    egress: { scope: "cloud", label: "slack" },
                    sticky: true,
                    actions: [{ label: "Approve", kind: "primary" },
                              { label: "Decline", kind: "danger" }],
                })"""
            )
            page.wait_for_selector("#qlippy-card:not([hidden])", timeout=4000)
            page.wait_for_timeout(500)
            badge = page.text_content("#qlippy-egress") or ""
            check(badge == "☁ slack", f"cloud badge reads '☁ slack' (got {badge!r})")
            styled = page.evaluate(
                """(() => {
                    const el = document.getElementById("qlippy-egress");
                    const cs = getComputedStyle(el);
                    return { radius: cs.borderRadius, display: cs.display,
                             cls: el.className };
                })()"""
            )
            check(
                styled["display"] == "inline-flex" and styled["radius"] not in ("", "0px"),
                f"the badge is styled (computed {styled})",
            )
            check("is-cloud" in styled["cls"], "the cloud tone class applies")
            card_text = page.text_content("#qlippy-card") or ""
            for phrase in ("Data used", "nothing is sent", "stays on this machine",
                           "Your controls", "leaves your machine"):
                check(phrase not in card_text, f"no privacy prose on the card: {phrase!r}")
            page.screenshot(path=str(OUT_DIR / "story01-cloud-card.png"))

            # 2. A local-scoped card (the learned shape).
            page.evaluate("window.qlippyCard.resolve()")
            page.wait_for_timeout(600)
            page.evaluate(
                """window.qlippyCard.present({
                    sprite: "learned", glyph: "lightbulb",
                    headline: "Learned from you",
                    detail: 'Applied "k8s" → kubernetes — matches 3 past dictations.',
                    egress: { scope: "local" },
                })"""
            )
            page.wait_for_timeout(500)
            badge = page.text_content("#qlippy-egress") or ""
            check(badge == "⌂ Local", f"local badge reads '⌂ Local' (got {badge!r})")
            cls = page.get_attribute("#qlippy-egress", "class") or ""
            check("is-local" in cls, "the local tone class applies")
            page.screenshot(path=str(OUT_DIR / "story01-local-card.png"))

            browser.close()
    finally:
        server.stop()

    check(not page_errors, f"zero uncaught page errors (saw {page_errors!r})")
    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} failure(s))")
        return 1
    print("RESULT: PASS (all checks + zero page errors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
