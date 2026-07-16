#!/usr/bin/env python3
"""Capture HS-93-02 Web evidence against the real production server.

Unlike the generic Vite layout-shot harness, this boots ``MeetingWebServer``
against an isolated database and config. Any failed API request or visible
request-error copy aborts the run, so disconnected frames cannot become roadmap
evidence.

The walk covers EVERY named workroom from a real Desk subject:

- Dictation — contextual entry from a Note pull-out ("Dictate about this"),
  plus the direct-URL fallback that fabricates no subject.
- Meeting archive/detail (History) — "Review meeting" from a Meeting object,
  detail opens, return lands on the same Desk subject.
- Workbench — "Edit Workflow" from a Workflow object, a real edit + save,
  return, re-enter: the draft identity is retained outside the URL.
- Runs-on editor (Profiles) — contextual entry, a stated recoverable failure
  (invalid save), a cancel, and a clean return with nothing stranded.
- Integration setup (Settings) — the original desktop/compact/direct walk.

    .venv/bin/python scripts/phase93_workroom_evidence.py [output-directory]
"""

from __future__ import annotations

import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from playwright.sync_api import Page, Response, sync_playwright  # noqa: E402

import holdspeak.config as config_module  # noqa: E402
from holdspeak.config import Config  # noqa: E402
from holdspeak.db import FIRST_DICTATION_SUCCESS, get_database, reset_database  # noqa: E402
from holdspeak.meeting_session import (  # noqa: E402
    IntelSnapshot,
    MeetingState,
    TranscriptSegment,
)
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402


DEFAULT_OUTPUT = (
    ROOT / "pm/roadmap/holdspeak/phase-93-effortless-holdspeak/evidence/hs-93-02"
)
VISIBLE_FAILURES = (
    "HoldSpeak could not complete that request",
    "HTTP 404",
)

NOTE_ID = "release"
NOTE_TITLE = "Release checklist"
MEETING_ID = "m1"
MEETING_TITLE = "Q3 kickoff"
WORKFLOW_ID = "wf_walk"
WORKFLOW_NAME = "Digest builder"
WORKBENCH_DRAFT_KEY = f"holdspeak.workroom.workbench.{WORKFLOW_ID}"
WORKBENCH_MATERIAL = "Walk material retained outside the URL."


def linear_graph(workflow_id: str, name: str) -> dict:
    """The exact linear wire ``buildLinearGraph`` emits for one Summarize."""
    return {
        "id": workflow_id,
        "name": name,
        "entry": "entry",
        "nodes": [
            {"id": "entry", "kind": {"entry": {}}},
            {"id": "source", "kind": {"source": {}}},
            {"id": "n1", "kind": {"summarize": {}}},
            {"id": "out", "kind": {"output": {}}},
        ],
        "exec_edges": [
            {"from": {"node": "entry", "name": "then"}, "to": "source"},
            {"from": {"node": "source", "name": "then"}, "to": "n1"},
            {"from": {"node": "n1", "name": "then"}, "to": "out"},
        ],
        "data_edges": [],
    }


def seed(database) -> None:
    database.notes.upsert(
        note_id=NOTE_ID,
        title=NOTE_TITLE,
        body_markdown="Ship after checks pass. Confirm the rollout owner.",
    )
    database.meetings.save_meeting(
        MeetingState(
            id=MEETING_ID,
            started_at=datetime(2026, 7, 10, 10, 0, 0),
            ended_at=datetime(2026, 7, 10, 10, 30, 0),
            title=MEETING_TITLE,
            segments=[
                TranscriptSegment(
                    text="The rollout gate is green after the checks.",
                    speaker="Karol",
                    start_time=0.0,
                    end_time=4.0,
                ),
                TranscriptSegment(
                    text="Then the release ships this week.",
                    speaker="Sam",
                    start_time=4.0,
                    end_time=8.0,
                ),
            ],
            intel=IntelSnapshot(
                timestamp=1.0,
                summary="Kickoff confirmed the rollout gate and the ship week.",
                action_items=[{"id": "ai1", "task": "Ship the release"}],
            ),
        )
    )
    database.workflows.upsert(
        workflow_id=WORKFLOW_ID,
        name=WORKFLOW_NAME,
        graph_json=linear_graph(WORKFLOW_ID, WORKFLOW_NAME),
    )
    database.profiles.upsert(
        profile_id="profile_lan",
        name="LAN box",
        kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1",
        model="Qwen3.5-9B-Q6_K",
    )
    database.milestones.mark(FIRST_DICTATION_SUCCESS)


def track_api_failures(page: Page) -> list[str]:
    failures: list[str] = []

    def observe(response: Response) -> None:
        if "/api/" in response.url and response.status >= 400:
            failures.append(f"{response.status} {response.url}")

    page.on("response", observe)
    return failures


def assert_clean(page: Page, api_failures: list[str], label: str) -> None:
    page.wait_for_timeout(700)
    body = page.locator("body").inner_text()
    visible = [text for text in VISIBLE_FAILURES if text in body]
    if api_failures or visible:
        detail = ", ".join([*api_failures, *visible])
        raise AssertionError(f"{label} is not clean: {detail}")


def workroom_bar(page: Page) -> str:
    page.wait_for_selector(".workroom-bar")
    return page.locator(".workroom-bar").inner_text()


def assert_bar(page: Page, label: str, *needles: str) -> None:
    # The bar renders the subject ref first and swaps in the resolved title
    # once items hydrate; wait boundedly for each needle instead of racing.
    deadline = time.monotonic() + 10.0
    missing = ""
    while time.monotonic() < deadline:
        text = workroom_bar(page)
        missing = next(
            (n for n in needles if n.upper() not in text.upper()), ""
        )
        if not missing:
            return
        page.wait_for_timeout(250)
    raise AssertionError(f"{label} bar is missing {missing!r}: {text!r}")


def open_desk_pullout(page: Page, url: str, title: str) -> None:
    """Land on the Desk and open the named object's pull-out."""
    page.goto(f"{url}/", wait_until="domcontentloaded")
    obj = page.locator(f'.desk-obj[aria-label^="{title}"]').first
    obj.wait_for()
    obj.click()
    page.locator(".desk-pullout", has_text=title).first.wait_for()


def return_to_subject(page: Page, label: str, subject_title: str) -> None:
    """Click the workroom return and prove it lands on the same Desk subject."""
    page.locator(".workroom-bar").get_by_role(
        "link", name="Back to subject on Desk"
    ).click()
    page.wait_for_url(re.compile(r"/\?open="))
    pullout = page.locator(".desk-pullout", has_text=subject_title).first
    pullout.wait_for()
    if not pullout.is_visible():
        raise AssertionError(f"{label}: return did not reopen {subject_title!r}")


def walk_dictation(page: Page, url: str, failures: list[str], output: Path) -> None:
    """Contextual entry from a Note subject, then the return home."""
    open_desk_pullout(page, url, NOTE_TITLE)
    page.get_by_role("link", name="Dictate about this").click()
    page.wait_for_url(re.compile(r"/dictation\?room="))
    assert_bar(
        page,
        "Dictation",
        "From Desk",
        f"Note · {NOTE_ID}",
        "Dictate about subject",
        "Back to subject on Desk",
    )
    assert_clean(page, failures, "contextual Dictation")
    page.screenshot(path=str(output / "after-web-room-dictation.png"))
    return_to_subject(page, "Dictation", NOTE_TITLE)
    assert_clean(page, failures, "Dictation return")


def walk_dictation_direct(
    page: Page, url: str, failures: list[str], output: Path
) -> None:
    """Direct URL: explicit Desk fallback, no fabricated subject."""
    page.goto(f"{url}/dictation", wait_until="domcontentloaded")
    assert_bar(page, "direct Dictation", "Opened directly", "Back to Desk")
    if page.locator(".workroom-bar strong").count() != 0:
        raise AssertionError("direct Dictation fabricated a subject")
    assert_clean(page, failures, "direct Dictation")
    page.screenshot(path=str(output / "after-web-room-dictation-direct.png"))
    page.locator(".workroom-bar").get_by_role("link", name="Back to Desk").click()
    page.wait_for_selector(".desk-next")


def walk_history(page: Page, url: str, failures: list[str], output: Path) -> None:
    """Review meeting from the Meeting object; detail opens; return home."""
    open_desk_pullout(page, url, MEETING_TITLE)
    page.get_by_role("link", name="Review meeting", exact=True).click()
    page.wait_for_url(re.compile(r"/history\?room="))
    assert_bar(
        page,
        "History",
        "From Desk",
        MEETING_TITLE,
        "Review meeting",
        "Back to subject on Desk",
    )
    detail = page.locator("dialog.signal-dialog[open]", has_text=MEETING_TITLE)
    detail.wait_for()
    assert_clean(page, failures, "Meeting detail")
    page.screenshot(path=str(output / "after-web-room-history.png"))
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    return_to_subject(page, "History", MEETING_TITLE)
    assert_clean(page, failures, "History return")


def walk_workbench(page: Page, url: str, failures: list[str], output: Path) -> None:
    """Edit Workflow from the Workflow object; edit, save, return, re-enter:
    the draft identity is retained outside the URL."""
    open_desk_pullout(page, url, WORKFLOW_NAME)
    page.get_by_role("link", name="Edit Workflow", exact=True).click()
    page.wait_for_url(re.compile(r"/workbench\?room="))
    assert_bar(
        page,
        "Workbench",
        "From Desk",
        WORKFLOW_NAME,
        "Edit workflow",
        "Back to subject on Desk",
    )
    page.wait_for_selector(".workbench-node")
    nodes_before = page.locator(".workbench-node").count()

    # A real edit: one added step and typed run material.
    page.get_by_role("group", name="Add a node").get_by_role(
        "button", name="Keep if"
    ).click()
    page.wait_for_timeout(150)
    nodes_after = page.locator(".workbench-node").count()
    if nodes_after != nodes_before + 1:
        raise AssertionError(
            f"adding a step did not add a node ({nodes_before} -> {nodes_after})"
        )
    page.get_by_label("Material").fill(WORKBENCH_MATERIAL)
    page.get_by_role("button", name="Save Workflow").click()
    page.get_by_text("Saved to this Workflow.").wait_for()
    assert_clean(page, failures, "Workbench edit + save")
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(150)
    page.screenshot(path=str(output / "after-web-room-workbench.png"))

    draft = page.evaluate(
        f"sessionStorage.getItem({WORKBENCH_DRAFT_KEY!r})"
    )
    if not draft or WORKBENCH_MATERIAL not in draft:
        raise AssertionError("the Workbench draft is not retained outside the URL")

    return_to_subject(page, "Workbench", WORKFLOW_NAME)

    # Re-enter the same workroom: the draft (material + added step) survives.
    page.get_by_role("link", name="Edit Workflow", exact=True).click()
    page.wait_for_url(re.compile(r"/workbench\?room="))
    page.wait_for_selector(".workbench-node")
    material = page.get_by_label("Material").input_value()
    if material != WORKBENCH_MATERIAL:
        raise AssertionError(
            f"re-entry lost the run material draft: {material!r}"
        )
    if page.locator(".workbench-node").count() != nodes_after:
        raise AssertionError("re-entry lost the added step")
    assert_bar(page, "Workbench re-entry", "From Desk", WORKFLOW_NAME)
    assert_clean(page, failures, "Workbench re-entry")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(150)
    page.screenshot(path=str(output / "after-web-room-workbench-retained.png"))
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(150)
    return_to_subject(page, "Workbench re-entry", WORKFLOW_NAME)


def walk_profiles(page: Page, url: str, failures: list[str], output: Path) -> None:
    """Runs-on editor: contextual entry, a stated recoverable failure
    (invalid save, refused before any request), cancel, clean return."""
    open_desk_pullout(page, url, WORKFLOW_NAME)
    page.get_by_role("link", name="Configure Runs on", exact=True).click()
    page.wait_for_url(re.compile(r"/profiles\?room="))
    assert_bar(
        page,
        "Runs on",
        "From Desk",
        f"Workflow · {WORKFLOW_ID}",
        "Configure runs on",
        "Back to subject on Desk",
    )
    assert_clean(page, failures, "contextual Runs on")
    page.screenshot(path=str(output / "after-web-room-profiles.png"))

    # Recoverable failure: an invalid save is refused and stated in the room.
    page.get_by_role("button", name="New destination").click()
    dialog = page.locator("dialog.signal-dialog[open]")
    dialog.wait_for()
    dialog.get_by_role("button", name="Save destination").click()
    dialog.get_by_text("A Runs on destination needs a name.").wait_for()
    assert_clean(page, failures, "Runs on invalid save")
    page.screenshot(path=str(output / "after-web-room-failure.png"))

    # Cancel out; nothing stranded.
    dialog.get_by_role("button", name="Cancel").click()
    page.wait_for_timeout(200)
    if page.locator("dialog[open]").count() != 0:
        raise AssertionError("cancel left the Runs-on dialog stranded")

    return_to_subject(page, "Runs on", WORKFLOW_NAME)
    if page.locator("dialog[open]").count() != 0:
        raise AssertionError("the Runs-on return stranded a dialog")
    assert_clean(page, failures, "Runs on return")


def open_integration_workroom(page: Page, url: str) -> None:
    page.goto(f"{url}/", wait_until="domcontentloaded")
    page.locator(".desk-tools-launch").click()
    page.get_by_role("link", name=re.compile("Integrations")).click()
    page.wait_for_url(re.compile(r"/settings\?room="))
    page.wait_for_selector(".workroom-bar")
    context = page.locator(".workroom-bar").inner_text()
    assert "FROM DESK" in context.upper()
    assert "Integration destinations" in context
    assert "Back to subject on Desk" in context


def walk_settings(page: Page, url: str, failures: list[str], output: Path) -> None:
    open_integration_workroom(page, url)
    assert_clean(page, failures, "Integration Settings")
    page.screenshot(path=str(output / "after-web-room-settings.png"))
    return_to_subject_href = page.locator(".workroom-bar").get_by_role(
        "link", name="Back to subject on Desk"
    )
    return_to_subject_href.click()
    page.wait_for_url(re.compile(r"/\?open="))
    page.wait_for_selector(".desk-next")
    assert_clean(page, failures, "Integration Settings return")


def main(output_directory: str | None = None) -> int:
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="holdspeak-phase93-") as temp_dir:
        scratch = Path(temp_dir)
        config_module.CONFIG_FILE = scratch / "config.json"
        Config().save(config_module.CONFIG_FILE)
        reset_database()
        database = get_database(scratch / "holdspeak.db")
        seed(database)

        callbacks = WebRuntimeCallbacks(
            on_bookmark=MagicMock(
                return_value={"timestamp": 0.0, "label": "evidence"}
            ),
            on_stop=MagicMock(return_value={"status": "stopped"}),
            get_state=MagicMock(
                return_value={
                    "id": None,
                    "started_at": None,
                    "duration": 0,
                    "bookmarks": [],
                }
            ),
        )
        server = MeetingWebServer(callbacks, host="127.0.0.1")
        url = server.start()
        time.sleep(0.8)

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()

                # One desktop journey page: every room, entered from its Desk
                # subject, worked, and walked back home.
                desktop = browser.new_page(
                    viewport={"width": 1440, "height": 1000}
                )
                desktop_failures = track_api_failures(desktop)
                walk_dictation(desktop, url, desktop_failures, output)
                walk_dictation_direct(desktop, url, desktop_failures, output)
                walk_history(desktop, url, desktop_failures, output)
                walk_workbench(desktop, url, desktop_failures, output)
                walk_profiles(desktop, url, desktop_failures, output)
                walk_settings(desktop, url, desktop_failures, output)

                # The compact contextual Settings frame stays legible.
                compact = browser.new_page(
                    viewport={"width": 560, "height": 1000}
                )
                compact_failures = track_api_failures(compact)
                open_integration_workroom(compact, url)
                assert_clean(compact, compact_failures, "compact workroom")
                compact.screenshot(
                    path=str(output / "after-web-room-settings-compact.png"),
                    full_page=False,
                )

                browser.close()
        finally:
            server.stop()
            reset_database()

    print(f"HS-93-02 clean production Web evidence -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
