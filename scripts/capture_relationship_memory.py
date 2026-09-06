"""Capture assembled-hub evidence for relationship-aware memory."""
from __future__ import annotations

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

from playwright.sync_api import sync_playwright

from holdspeak.db import get_database, reset_database
from holdspeak.db.milestones import FIRST_DICTATION_SUCCESS
from holdspeak.web_auth import authenticated_browser_url
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


OUT = Path("docs/evidence/relationship-aware-memory").resolve()
NOW = "2026-09-01T14:00:00"


def seed(db) -> None:
    db.milestones.mark(FIRST_DICTATION_SUCCESS)
    db.projects.create_project(
        project_id="orion",
        name="Project Orion",
        description="Ship the private beta with a reversible deployment path.",
        keywords=["orion", "launch", "rollout"],
        context={
            "purpose": "Launch a dependable private beta.",
            "outcome": "A reversible rollout with explicit owners and evidence.",
        },
        updated_at=NOW,
    )
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings(id,started_at,title) VALUES('m-orion',?,'Orion launch review')",
            (NOW,),
        )
        conn.execute(
            """INSERT INTO meeting_projects(meeting_id,project_id,source,confidence)
               VALUES('m-orion','orion','manual',1)"""
        )
        conn.execute(
            """INSERT INTO segments(meeting_id,text,speaker,start_time,end_time)
               VALUES('m-orion',
                      'Zephyr launch readiness was approved after the rollback rehearsal.',
                      'Mina',0,7)"""
        )
        conn.execute(
            """INSERT INTO decisions
               (id,text,rationale,decided_at,date_basis,source_artifact_id,
                source_meeting_id,source_state,project_key,lifecycle,
                created_at,updated_at,last_modified,deleted)
               VALUES('d-rollout','Adopt blue-green rollout for the private beta',
                      'Rollback rehearsal completed successfully',?,'meeting_date',
                      'a-readiness','m-orion','linked',NULL,'accepted',?,?,?,0)""",
            (NOW, NOW, NOW, NOW),
        )
        conn.execute(
            """INSERT INTO decision_records
               (id,decision_text,rationale,owner,source_type,source_id,created_at,updated_at)
               VALUES('dr-rollout','Adopt blue-green rollout for the private beta',
                      'The reversible path limits launch risk','Mina','meeting','d-rollout',?,?)""",
            (NOW, NOW),
        )
        conn.execute(
            """INSERT INTO decision_record_sources
               (id,record_id,source_type,source_ref,created_at)
               VALUES('drs-rollout','dr-rollout','meeting','m-orion',?)""",
            (NOW,),
        )
        conn.execute(
            """INSERT INTO action_items(id,meeting_id,task,owner,status,created_at)
               VALUES('act-observe','m-orion','Publish launch observability dashboard',
                      'Ari','pending',?)""",
            (NOW,),
        )
    db.plugins.record_artifact(
        artifact_id="a-readiness",
        meeting_id="m-orion",
        artifact_type="memo",
        title="Launch readiness brief",
        body_markdown="Rollback gates, deployment owners, and the go/no-go checklist.",
        updated_at=NOW,
    )
    db.notes.upsert(
        note_id="n-orion",
        title="Zephyr operating notes",
        body_markdown="Zephyr monitoring thresholds and launch-day escalation owners.",
        created_at=NOW,
        last_modified=NOW,
    )
    db.project_relationships.upsert(
        project_id="orion", resource_ref="note:n-orion", last_modified=NOW
    )
    db.notes.upsert(
        note_id="n-personal",
        title="Zephyr research scratchpad",
        body_markdown="Unscoped Desk research about Zephyr capacity planning.",
        created_at=NOW,
        last_modified=NOW,
    )
    thread = db.threads.create_thread(title="Launch follow-through")
    message = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(
        message.id,
        kind="text",
        text="What did we decide about the Zephyr rollout?",
    )
    db.threads.freeze_refs(
        thread.id,
        message.id,
        [{"ref_kind": "note", "ref_id": "n-orion"}],
    )


def capture() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="holdspeak-memory-shot-"))
    reset_database()
    db = get_database(tmp / "shot.db")
    seed(db)
    OUT.mkdir(parents=True, exist_ok=True)
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        ),
        host="127.0.0.1",
    )
    url = server.start()
    time.sleep(1)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(
                authenticated_browser_url(f"{url}/", server.auth_token),
                wait_until="domcontentloaded",
            )
            page.wait_for_selector(".desk-bell", timeout=30_000)
            page.add_style_tag(
                content=".desk-mc,.desk-mc-tab{display:none!important}"
            )

            # Prove the owner-facing launcher: bell -> shade -> actual search window.
            page.click(".desk-bell")
            page.wait_for_selector(".desk-shade", state="visible")
            page.locator(".desk-shade").screenshot(
                path=str(OUT / "desk-memory-launcher.png")
            )
            page.click(".desk-shade-memory")
            page.wait_for_selector(".project-memory-core", state="visible")
            global_window = page.locator(".project-memory-core")
            global_search = page.get_by_role("searchbox", name="Search the Desk")
            global_search.fill("zephyr")
            page.locator(".project-memory-search").get_by_role(
                "button", name="Search", exact=True
            ).click()
            page.wait_for_selector(".project-memory-core .surface-row")
            page.wait_for_timeout(500)
            page.screenshot(path=str(OUT / "desk-memory-global.png"), full_page=True)
            global_window.screenshot(path=str(OUT / "desk-memory-results.png"))

            # Use the real tool shelf to reopen the same surface with Project scope.
            page.click(".desk-tools-launch")
            tool_search = page.get_by_role(
                "combobox", name="Search tools and Desk items"
            )
            tool_search.fill("Project Orion")
            page.get_by_role("option", name="Project Orion", exact=False).nth(1).click()
            page.wait_for_timeout(700)
            project_core = page.locator(".project-memory-core")
            project_window = project_core
            page.get_by_role("tab", name="Search", exact=True).click()
            project_search = page.get_by_role(
                "searchbox", name="Search this project"
            )
            project_search.fill("zephyr")
            project_core.locator(".project-memory-search").get_by_role(
                "button", name="Search", exact=True
            ).click()
            page.wait_for_selector(".project-memory-core .surface-row")
            page.wait_for_timeout(500)
            page.screenshot(path=str(OUT / "project-memory-scoped.png"), full_page=True)
            project_window.screenshot(path=str(OUT / "project-memory-results.png"))
            browser.close()
    finally:
        server.stop()
        reset_database()

    for name in (
        "desk-memory-launcher.png",
        "desk-memory-global.png",
        "desk-memory-results.png",
        "project-memory-scoped.png",
        "project-memory-results.png",
    ):
        print(OUT / name)


if __name__ == "__main__":
    capture()
