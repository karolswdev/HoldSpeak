"""HS-69-02 broadening (Wave B) — seed + screenshot proof.

Boots the real MeetingWebServer against a seeded temp DB and captures the
surfaces that gained the `.signal-card` primitive this wave (/desk, /activity)
plus /history (the hs-materialize arrival), and PROBES computed styles so we
prove the global primitive actually paints on the JS/Alpine-injected DOM (a
class shipping in the bundle is not proof — the Astro-scoped-CSS-on-JS-DOM
gotcha). Requires the built bundle (cd web && npm run build) and Playwright.

Run: uv run python scripts/screenshot_phase69_substrate.py
"""
import json
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from playwright.sync_api import sync_playwright

from holdspeak.db import get_database, reset_database
from holdspeak.meeting_session import IntelSnapshot, MeetingState
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OUT = Path("pm/roadmap/holdspeak/phase-69-web-recrafted/screenshots")
OUT.mkdir(parents=True, exist_ok=True)


def _action(item_id, task, *, owner=None, status="pending", due=None):
    return {
        "id": item_id, "task": task, "owner": owner, "due": due,
        "status": status, "review_state": "pending", "source_timestamp": None,
        "created_at": datetime(2026, 6, 5, 10, 0, 0).isoformat(),
    }


def seed(db):
    # --- desk primitives -------------------------------------------------
    db.notes.upsert(note_id="n1", title="Rate-limiter spec",
                    body_markdown="# Rate limiter\nToken bucket, per-key.", tags=["infra", "draft"])
    db.notes.upsert(note_id="n2", title="Onboarding copy pass",
                    body_markdown="Trim the welcome wizard to three beats.", tags=["ux"])
    db.kbs.upsert(kb_id="kb1", name="Platform field notes", member_ids=["n1", "n2"])
    db.agents.upsert(agent_id="a1", name="Summarizer", avatar="🧭",
                     role="Condenses long meetings into decisions + owners",
                     system_prompt="You summarize.", user_template="Summarize: {input}",
                     tools=["web"], kb_id="kb1")
    db.agents.upsert(agent_id="a2", name="Triage", avatar="🚦",
                     role="Routes action items to the right project",
                     system_prompt="You triage.", user_template="Triage: {input}", tools=[])

    # --- meetings + artifacts (dashboard / history / desk) ---------------
    db.meetings.save_meeting(MeetingState(
        id="m-current", started_at=datetime(2026, 6, 5, 10, 0, 0),
        ended_at=datetime(2026, 6, 5, 10, 45, 0), title="API design follow-up",
        intel=IntelSnapshot(timestamp=0.0, action_items=[
            _action("c1", "Wire the rate limiter behind a flag", owner="Priya", due="Friday"),
            _action("c2", "Pick a service name"),
        ]),
    ))
    db.meetings.save_meeting(MeetingState(
        id="m-prior", started_at=datetime(2026, 6, 4, 14, 0, 0),
        ended_at=datetime(2026, 6, 4, 14, 30, 0), title="Weekly sync",
        intel=IntelSnapshot(timestamp=0.0, action_items=[
            _action("p1", "Draft the migration note", owner="Sam"),
        ]),
    ))
    db.plugins.record_artifact(
        artifact_id="art-decisions", meeting_id="m-current", artifact_type="decisions",
        title="Decisions", structured_json={"decisions": [{"decision": "Use Postgres for the primary store"}]},
        plugin_id="decision_capture")

    # --- activity: records -> nudges, + a project routing rule -----------
    db.activity.update_activity_privacy_settings(enabled=True)
    db.activity.upsert_activity_record(
        source_browser="safari", source_profile="default",
        url="https://github.com/karolswdev/HoldSpeak/issues/53",
        title="Activity Pre-Briefing", entity_type="github_issue",
        entity_id="karolswdev/HoldSpeak#53", visit_count=4,
        last_seen_at=datetime.now() - timedelta(minutes=18))
    db.activity.upsert_activity_record(
        source_browser="safari", source_profile="default",
        url="https://example.atlassian.net/browse/HS-204",
        title="HS-204 rate limiter", entity_type="jira_ticket",
        entity_id="HS-204", visit_count=2,
        last_seen_at=datetime.now() - timedelta(minutes=40))
    db.projects.create_project(project_id="holdspeak", name="HoldSpeak")
    db.activity.create_activity_project_rule(
        project_id="holdspeak", name="HoldSpeak Jira", match_type="entity_id_prefix",
        entity_type="jira_ticket", pattern="HS-", priority=200, enabled=True)


def probe(page, selector, props):
    """Return computed style props for the first matching element (or None)."""
    return page.evaluate(
        """([sel, props]) => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const cs = getComputedStyle(el);
            const out = {};
            for (const p of props) out[p] = cs.getPropertyValue(p);
            // also read the ::before (the gradient hairline) animation/bg presence
            const bef = getComputedStyle(el, '::before');
            out['__before_bg'] = bef.getPropertyValue('background-image').slice(0, 40);
            return out;
        }""",
        [selector, props],
    )


def main():
    tmp = Path(tempfile.mkdtemp())
    reset_database()
    db = get_database(tmp / "holdspeak.db")
    seed(db)

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        host="127.0.0.1")
    url = server.start()
    time.sleep(1.0)
    probes = {}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.set_viewport_size({"width": 1320, "height": 1400})

            # /desk
            pg.goto(f"{url}/desk", wait_until="networkidle")
            pg.wait_for_timeout(700)
            pg.screenshot(path=str(OUT / "desk.png"), full_page=True)
            probes["desk .card.signal-card"] = probe(
                pg, ".card.signal-card", ["box-shadow", "border-top-left-radius", "background-color"])

            # /activity
            pg.goto(f"{url}/activity", wait_until="networkidle")
            pg.wait_for_timeout(700)
            pg.screenshot(path=str(OUT / "activity.png"), full_page=True)
            probes["activity .rule-item.signal-card"] = probe(
                pg, ".rule-item.signal-card", ["box-shadow", "border-top-left-radius", "background-color"])
            probes["activity .nudge-card.signal-card"] = probe(
                pg, ".nudge-card.signal-card", ["box-shadow", "border-top-left-radius", "animation-name"])

            # /history (signal-card meeting cards + materialize)
            pg.goto(f"{url}/history", wait_until="networkidle")
            pg.wait_for_timeout(700)
            pg.screenshot(path=str(OUT / "history.png"), full_page=True)
            b.close()
    finally:
        server.stop()
        reset_database()

    (OUT / "probes.json").write_text(json.dumps(probes, indent=2))
    print(json.dumps(probes, indent=2))
    print("\nSaved screenshots to", OUT)


if __name__ == "__main__":
    main()
