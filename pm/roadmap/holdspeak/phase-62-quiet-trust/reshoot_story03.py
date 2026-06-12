#!/usr/bin/env python3
"""HS-62-03: re-shoot every user-facing-doc screenshot that showed the old
privacy prose, from a live server, post-sweep.

Produces (straight into docs/assets/, reviewed before commit):
  - presence/qlippy-decision-card.png  (☁ github badge, 520x460)
  - presence/qlippy-learned-card.png   (⌂ Local badge, 520x460)
  - aftercare/followup-draft.png       (unconfigured: "Preview and copy only.")
  - aftercare/send-to-slack.png        (configured: buttons + the short note)
  - aftercare/file-as-issue.png        (the new proposal-note + guard copy)
  - screenshots/welcome.png            (rail foot "Local · 127.0.0.1")

Run after building the web bundle.
"""
from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

REPO = Path(__file__).resolve().parents[4]
ASSETS = REPO / "docs" / "assets"


def _seed(db):
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    started = datetime(2026, 6, 5, 10, 0, 0)
    prior = MeetingState(
        id="m-prior",
        started_at=datetime(2026, 6, 1, 10, 0, 0),
        ended_at=datetime(2026, 6, 1, 11, 0, 0),
        title="API design kickoff",
    )
    prior.intel = IntelSnapshot(
        timestamp=60.0,
        action_items=[{
            "id": "p1", "task": "Stand up the staging cluster", "owner": "Sam",
            "due": None, "status": "done", "review_state": "accepted",
            "source_timestamp": None, "created_at": prior.started_at.isoformat(),
        }],
    )
    db.meetings.save_meeting(prior)

    state = MeetingState(
        id="m-doc",
        started_at=started,
        ended_at=datetime(2026, 6, 5, 11, 0, 0),
        title="API design follow-up",
        segments=[
            TranscriptSegment(text="Let's open the design follow-up.", speaker="Me", start_time=0.0, end_time=8.0),
            TranscriptSegment(text="We're keeping Postgres as the primary store.", speaker="Sam", start_time=12.0, end_time=20.0),
            TranscriptSegment(text="Priya, can you own the rate limiter this week?", speaker="Me", start_time=40.0, end_time=48.0),
            TranscriptSegment(text="Yes — I'll wire it behind the feature flag.", speaker="Priya", start_time=70.0, end_time=78.0),
        ],
    )
    state.intel = IntelSnapshot(
        timestamp=120.0,
        action_items=[
            {"id": "a1", "task": "Wire the rate limiter behind a flag", "owner": "Priya",
             "due": "Friday", "status": "pending", "review_state": "accepted",
             "source_timestamp": 70.0, "created_at": started.isoformat()},
            {"id": "a2", "task": "Pick a service name", "owner": None,
             "due": None, "status": "pending", "review_state": "pending",
             "source_timestamp": None, "created_at": started.isoformat()},
        ],
    )
    db.meetings.save_meeting(state)
    db.plugins.record_artifact(
        artifact_id="art-doc-decisions",
        meeting_id="m-doc",
        plugin_id="decision_tracker",
        plugin_version="1.0.0",
        artifact_type="decisions",
        title="Decisions",
        structured_json={"decisions": [
            {"decision": "Use Postgres for the primary store",
             "rationale": "Transactions and team familiarity", "source_timestamp": 12.0},
        ]},
    )


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
    _seed(db)

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    failures: list[str] = []
    page_errors: list[str] = []

    def check(ok, label):
        print(("PASS  " if ok else "FAIL  ") + label)
        if not ok:
            failures.append(label)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()

            # ── the Qlippy cards (520x460, like the originals) ──────────
            page = browser.new_page(viewport={"width": 520, "height": 460})
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.goto(f"{url}/presence", wait_until="networkidle")
            page.wait_for_timeout(800)
            page.evaluate(
                """window.qlippyCard.present({
                    sprite: "alert", glyph: "bang",
                    headline: "A decision needs you",
                    detail: "github · create_issue",
                    preview: 'Open a GitHub issue in acme/widgets: “Follow up: Fix the flaky login test”',
                    egress: { scope: "cloud", label: "github" },
                    sticky: true,
                    actions: [{ label: "Approve", kind: "primary" },
                              { label: "Decline", kind: "danger" }],
                })"""
            )
            page.wait_for_selector("#qlippy-card.is-in", timeout=5000)
            page.wait_for_timeout(600)
            check((page.text_content("#qlippy-egress") or "") == "☁ github", "decision card badge")
            page.screenshot(path=str(ASSETS / "presence" / "qlippy-decision-card.png"))

            page.evaluate("window.qlippyCard.resolve()")
            page.wait_for_timeout(700)
            page.evaluate(
                """window.qlippyCard.present({
                    sprite: "learned", glyph: "lightbulb",
                    headline: "Learned from you",
                    detail: 'Applied "k8s" → kubernetes — matches 2 past dictations.',
                    egress: { scope: "local" },
                    actions: [{ label: "View digest", kind: "ghost" }],
                })"""
            )
            page.wait_for_timeout(700)
            check((page.text_content("#qlippy-egress") or "") == "⌂ Local", "learned card badge")
            page.screenshot(path=str(ASSETS / "presence" / "qlippy-learned-card.png"))
            page.close()

            # ── the aftercare shots (history detail) ────────────────────
            def open_detail(pg):
                pg.goto(f"{url}/history", wait_until="networkidle")
                pg.click("text=API design follow-up")
                pg.wait_for_selector(".aftercare-card", timeout=5000)
                pg.wait_for_timeout(500)


            def shoot_element(pg, selector, out_path):
                """Element screenshot clipped to CONTENT height (flex parents
                stretch the element box and leave dead space below)."""
                loc = pg.locator(selector)
                loc.scroll_into_view_if_needed()
                pg.wait_for_timeout(200)
                box = loc.bounding_box()
                content_h = loc.evaluate("el => el.scrollHeight")
                pg.screenshot(
                    path=str(out_path),
                    clip={"x": box["x"], "y": box["y"],
                          "width": box["width"], "height": min(box["height"], content_h)},
                )

            page = browser.new_page(viewport={"width": 1180, "height": 2600}, device_scale_factor=2)
            page.on("pageerror", lambda e: page_errors.append(str(e)))

            # followup-draft.png — unconfigured, draft open.
            open_detail(page)
            page.click("text=Draft follow-up")
            page.wait_for_selector(".followup-pre", timeout=5000)
            page.wait_for_timeout(400)
            note = page.text_content(".followup-draft .loop-note") or ""
            check(note.strip() == "Preview and copy only.", f"unconfigured note ({note.strip()!r})")
            shoot_element(page, ".aftercare-card", ASSETS / "aftercare" / "followup-draft.png")

            # file-as-issue.png — file the accepted item, shoot the proposals card.
            page.click("text=File as issue")
            page.fill(".loop-input", "acme/app")
            page.click("text=Create proposal")
            page.wait_for_selector(".proposal-card", timeout=5000)
            page.wait_for_timeout(500)
            guard = page.text_content(".proposal-guard") or ""
            check(
                guard == "Approving records the decision; execution is a separate step.",
                f"github guard copy ({guard!r})",
            )
            shoot_element(page, ".detail-card:has(.proposal-card)", ASSETS / "aftercare" / "file-as-issue.png")

            # send-to-slack.png — configured, draft open.
            config = Config.load()
            config.meeting.slack_webhook_url = "https://hooks.slack.com/services/T0/B0/doc"
            config.save(path=config_module.CONFIG_FILE)
            open_detail(page)
            page.click("text=Draft follow-up")
            page.wait_for_selector(".followup-pre", timeout=5000)
            page.wait_for_timeout(400)
            note = page.text_content(".followup-draft .loop-note") or ""
            check(
                note.strip() == "Send to Slack creates a proposal; approve it below.",
                f"configured note ({note.strip()!r})",
            )
            shoot_element(page, ".aftercare-card", ASSETS / "aftercare" / "send-to-slack.png")
            page.close()

            # ── welcome.png (1280x860, like the original) ───────────────
            page = browser.new_page(viewport={"width": 1280, "height": 860})
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.goto(f"{url}/welcome", wait_until="networkidle")
            page.wait_for_timeout(900)
            foot = page.text_content(".wz-rail-foot") or ""
            check(foot.strip() == "Local · 127.0.0.1", f"welcome rail foot ({foot.strip()!r})")
            page.screenshot(path=str(ASSETS / "screenshots" / "welcome.png"))
            page.close()

            browser.close()
    finally:
        server.stop()
        reset_database()

    check(not page_errors, f"zero uncaught page errors (saw {page_errors!r})")
    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} failure(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
