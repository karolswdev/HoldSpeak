"""HS-172-05 -- People 1:1 Prep enrichment glass rig.

Seeds a People relationship with owner aliases, a Room with Watch
snapshots containing PRs and Jira issues matching the aliases.
Opens the Prep lens at 1440 + 393.  Asserts:
  - display step shows the person's name
  - summary rows present (PRS WAITING, ASSIGNMENTS OPEN)
  - no raw <button> in the card
  - no zero counter text
  - no her/him/she/he pronoun tokens
  - Open on a summary row switches to the Now wing

Shots to phase-172-the-loop-closes/assets/story-05-shots/.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot,
    _api,
    _assert_clean,
    _normal_chair,
    _ensure_build,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="People glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/story-05-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs172-people"


# ── Seed helpers ──────────────────────────────────────────────────


def _seed_project(project_id: str, name: str) -> str:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 1, NULL, "
            "'2026-09-01T00:00:00', '2026-09-05T10:00:00')",
            (project_id, name),
        )
    return project_id


def _seed_gh_connection(login: str = "karolswdev") -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, created_at, updated_at) "
            "VALUES ('wpc-gh', 'github', ?, 'connected', "
            " datetime('now'), datetime('now'), datetime('now'))",
            (login,),
        )


def _seed_watch(
    project_id: str,
    *,
    watch_id: str,
    connector_id: str = "gh",
    query_kind: str = "pull_requests",
    snapshot_entities: dict[str, Any] | list[Any] | None = None,
) -> None:
    from holdspeak.db import get_database
    db = get_database()
    snapshot_json = json.dumps({"entities": snapshot_entities or {}})
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, project_id, "
            " created_at, updated_at) "
            "VALUES (?, ?, ?, ?, '{}', ?, 1, datetime('now'), ?, "
            " datetime('now'), datetime('now'))",
            (
                watch_id,
                connector_id,
                query_kind,
                f"{connector_id} {query_kind}",
                snapshot_json,
                project_id,
            ),
        )


def _setup_people_and_relationship(page: Any) -> str:
    """Set up People store and create a relationship via the API.
    Returns the relationship id."""
    # Set up the People encrypted store.
    _api(page, "POST", "/api/people/setup", {}, token=TOKEN)

    # Create relationship "Ania".
    # _api returns {"status": ..., "payload": ...} where payload is the JSON body.
    result = _api(page, "POST", "/api/people/relationships", {
        "display_name": "Ania",
        "relationship_kind": "direct_report",
    }, token=TOKEN)
    payload = result.get("payload", result)
    rel_id = payload["relationship"]["id"]

    # Add owner alias "ania-k" (GitHub login).
    _api(page, "POST", f"/api/people/relationships/{rel_id}/owner-aliases", {
        "alias": "ania-k",
    }, token=TOKEN)

    return rel_id


def _link_project_to_relationship(page: Any, rel_id: str, project_id: str) -> None:
    """Link a project to a People relationship."""
    _api(page, "POST",
         f"/api/people/relationships/{rel_id}/projects/{project_id}",
         {}, token=TOKEN)


def _seed_watch_with_prs(project_id: str) -> None:
    """Seed a GitHub PR watch with two PRs waiting on ania-k."""
    five_days_ago = (datetime.now() - timedelta(days=5)).isoformat()
    two_days_ago = (datetime.now() - timedelta(days=2)).isoformat()
    _seed_watch(
        project_id,
        watch_id="w-gh-prs",
        connector_id="gh",
        query_kind="pull_requests",
        snapshot_entities={
            "pr-612": {
                "number": 612,
                "title": "Fix migration",
                "state": "open",
                "url": "https://github.com/karolswdev/holdspeak/pull/612",
                "review_requests": ["ania-k"],
                "updated_at": five_days_ago,
            },
            "pr-618": {
                "number": 618,
                "title": "Update types",
                "state": "open",
                "url": "https://github.com/karolswdev/holdspeak/pull/618",
                "review_requests": ["ania-k"],
                "updated_at": two_days_ago,
            },
        },
    )


def _seed_watch_with_issues(project_id: str) -> None:
    """Seed a Jira issue watch with one assignment for Ania."""
    _seed_watch(
        project_id,
        watch_id="w-jira-issues",
        connector_id="jira",
        query_kind="issues",
        snapshot_entities={
            "GOV-412": {
                "key": "GOV-412",
                "summary": "PostgreSQL migration",
                "assignee": "ania-k",
                "status": "In Progress",
                "status_category": "indeterminate",
                "url": "https://jira.example.com/browse/GOV-412",
            },
        },
    )


# ── Test ──────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def glass(tmp_path_factory: pytest.TempPathFactory, worker_id: str = "main"):
    """Boot the server, seed data, return (page, base_url, errors)."""
    from playwright.sync_api import sync_playwright

    tmp = tmp_path_factory.mktemp("hs172_people")
    mp = pytest.MonkeyPatch()

    # Use a file-based key store so macOS Keychain is not needed.
    keyfile = tmp / "people.key"
    keyfile.write_text("{}")
    keyfile.chmod(0o600)
    mp.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))

    _ensure_build()
    server, base = _boot(tmp, mp, token=TOKEN)

    project_id = _seed_project("proj-platform", "Platform")
    _seed_gh_connection()
    _seed_watch_with_prs(project_id)
    _seed_watch_with_issues(project_id)

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda err: errors.append(str(err)))

    page.goto(f"{base}/?token={TOKEN}")
    _normal_chair(page)

    # Set up People and relationship via the API.
    rel_id = _setup_people_and_relationship(page)
    _link_project_to_relationship(page, rel_id, project_id)

    yield page, base, errors, rel_id

    page.close()
    ctx.close()
    browser.close()
    pw.stop()
    server.stop()
    mp.undo()


def _open_people_prep(page: Any, base: str, rel_id: str) -> None:
    """Navigate to the People surface with the Prep lens for the given relationship."""
    page.evaluate(f"""() => {{
        sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({{key: "open-people", scope: "people:{rel_id}:prep"}})
        );
    }}""")
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    page.wait_for_timeout(800)
    _settle(page)


def test_prep_at_1440(glass: tuple) -> None:
    """Prep wing at 1440: display step, summary rows, no raw button, no zero counter."""
    page, base, errors, rel_id = glass

    page.set_viewport_size({"width": 1440, "height": 900})
    _open_people_prep(page, base, rel_id)

    # Wait for the prep lens to render.
    page.wait_for_selector("[data-testid='people-prep-lens']", timeout=5000)
    _settle(page)

    # Screenshot.
    page.screenshot(path=str(SHOTS / "build-people-prep-1440.png"), full_page=True)

    # Display step: the person's name.
    display = page.locator("[data-testid='prep-display-name']")
    assert display.text_content() == "Ania"

    # PRS WAITING summary row.
    prs_row = page.locator("[data-testid='prep-prs-row']")
    assert prs_row.count() > 0, "PRS WAITING row should be present"
    prs_label = page.locator("[data-testid='prep-prs-label']")
    label_text = prs_label.text_content() or ""
    assert "PRS WAITING" in label_text
    assert "ANIA" in label_text

    # ASSIGNMENTS row.
    assign_row = page.locator("[data-testid='prep-assignments-row']")
    assert assign_row.count() > 0, "ASSIGNMENTS row should be present"

    # Footer: THIS DEVICE + PREPARED.
    assert page.locator("text=THIS DEVICE").count() > 0
    receipt = page.locator("[data-testid='prep-receipt']")
    assert receipt.count() > 0
    receipt_text = receipt.text_content() or ""
    assert receipt_text.startswith("PREPARED ")

    # GUARD: no raw <button> in the card (UX-CANON A.1).
    # The library Button renders as <button class="btn ..."> or
    # <button class="signal-button ..."> or <button class="gadget-chip ...">
    card_html = page.locator("[data-testid='people-prep-lens']").inner_html()
    raw_buttons = re.findall(r'<button\b[^>]*>', card_html)
    for btn in raw_buttons:
        assert 'class=' in btn and ('btn ' in btn or 'btn"' in btn or 'signal-button' in btn or 'gadget-chip' in btn or 'surface-' in btn), (
            f"Raw <button> without library class: {btn[:100]}"
        )

    # GUARD: no zero counter text in the card.
    card_text = page.locator("[data-testid='prep-summary-rows']").text_content() or ""
    assert not re.search(r'\b0\s+(PRS?|ASSIGNMENTS?|COMMITMENTS?|ITEMS?)\b', card_text), (
        f"Zero counter found in card text: {card_text}"
    )

    # GUARD: no her/him/she/he pronoun tokens.
    assert not re.search(r'\b(her|him|she|he)\b', card_text, re.IGNORECASE), (
        f"Pronoun token found in card text: {card_text}"
    )

    _assert_clean(page, errors)


def test_prep_at_393(glass: tuple) -> None:
    """Prep wing at 393: stacked layout, Prep | Now wings only."""
    page, base, errors, rel_id = glass

    page.set_viewport_size({"width": 393, "height": 852})
    _open_people_prep(page, base, rel_id)

    page.wait_for_selector("[data-testid='people-prep-lens']", timeout=5000)
    _settle(page)

    # Screenshot.
    page.screenshot(path=str(SHOTS / "build-people-prep-393.png"), full_page=True)

    # Display step still present.
    display = page.locator("[data-testid='prep-display-name']")
    assert display.text_content() == "Ania"

    # Summary rows present.
    prs_row = page.locator("[data-testid='prep-prs-row']")
    assert prs_row.count() > 0

    # GUARD: no pronoun tokens at 393.
    card_text = page.locator("[data-testid='prep-summary-rows']").text_content() or ""
    assert not re.search(r'\b(her|him|she|he)\b', card_text, re.IGNORECASE)

    _assert_clean(page, errors)


def test_now_wing_from_prep(glass: tuple) -> None:
    """Open on a PRS summary row switches to the Now wing with per-entity rows."""
    page, base, errors, rel_id = glass

    page.set_viewport_size({"width": 1440, "height": 900})
    _open_people_prep(page, base, rel_id)

    page.wait_for_selector("[data-testid='people-prep-lens']", timeout=5000)
    _settle(page)

    # Click Open on the PRS WAITING row.
    page.locator("[data-testid='prep-prs-open']").click()
    page.wait_for_timeout(300)
    _settle(page)

    # The Now wing should show per-entity PR rows.
    now_concern = page.locator("[data-testid='people-now-concern']")
    assert now_concern.count() > 0, "Now concern view should appear"

    prs_detail = page.locator("[data-testid='now-prs-detail']")
    assert prs_detail.count() > 0, "PRS detail section should appear"

    # Screenshot.
    page.screenshot(path=str(SHOTS / "build-people-now-1440.png"), full_page=True)

    # Each PR should have its own Open verb.
    open_buttons = prs_detail.get_by_role("button", name="Open")
    assert open_buttons.count() >= 2, "Each PR row should have an Open verb"

    # Now tab should be selected.
    now_tab = page.get_by_role("tab", name="Now")
    assert now_tab.get_attribute("aria-selected") == "true"

    _assert_clean(page, errors)


def test_now_wing_at_393(glass: tuple) -> None:
    """Now wing at 393 after clicking Open on PRS summary."""
    page, base, errors, rel_id = glass

    page.set_viewport_size({"width": 393, "height": 852})
    _open_people_prep(page, base, rel_id)

    page.wait_for_selector("[data-testid='people-prep-lens']", timeout=5000)
    _settle(page)

    page.locator("[data-testid='prep-prs-open']").click()
    page.wait_for_timeout(300)
    _settle(page)

    page.screenshot(path=str(SHOTS / "build-people-now-393.png"), full_page=True)

    now_concern = page.locator("[data-testid='people-now-concern']")
    assert now_concern.count() > 0

    _assert_clean(page, errors)
