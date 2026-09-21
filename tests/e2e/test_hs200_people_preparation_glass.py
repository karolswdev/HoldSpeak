"""HS-200-14 -- permitted People preparation, on glass (planned suite
``phase200_people_preparation``, the e2e half).

The Room's PEOPLE section against a REAL booted hub on an isolated HOME
with a REAL encrypted People store (the dev file keystore,
``HOLDSPEAK_PEOPLE_KEYSTORE_FILE``, keyed under the isolated HOME -- no
patch stands in for the resolver), at 1440 and 393:

  ready        -- two people share a first name; a confirmed commitment
                  names `Priya`: `OWNER · AMBIGUOUS · 2 MATCHES` + `Resolve`,
                  the caption `PEOPLE 1 OF 2`, `1 AMBIGUOUS` in the head line;
                  the linked person carries the commitment with its meeting
                  and segment and the PR fact with its Watch.
  resolve      -- `Resolve` unfolds the candidates UNDER the row (no modal);
                  one click links the alias through the ledger's own write;
                  the caption becomes `PEOPLE 2`.
  people-core  -- `People` opens PeopleCore scoped to this Project; closing
                  it puts focus back on the verb (return-to-task).
  locked       -- the key file turns unreadable: `PEOPLE 0 OF 2`, `LOCKED`,
                  `Unlock`; every owner row `OWNER · LOCKED`, no dead verb.
  not-set-up   -- no ledger at all: `NOT SET UP` + `Set up People`.

Commitments are made through the REAL confirm route on seeded proposals
(story 12's chain); Watch snapshots are the one thing no route can seed
and are written as rows the way `test_hs200_attention_glass.py` writes them.

Shots to phase-200-the-working-practice/assets/story-14-shots/ (only with
HOLDSPEAK_WRITE_SHOTS=1 -- the 388-PNG scar).
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="People preparation glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-14-shots"
)
WRITE_SHOTS = os.environ.get("HOLDSPEAK_WRITE_SHOTS") == "1"

TOKEN = "hs200-people"
OWNER_LOGIN = "karolswdev"

pytestmark = [pytest.mark.e2e]


# ── seeds ────────────────────────────────────────────────────────────


def _create_project(page: Any, name: str) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": name,
        "description": "Seeded for the HS-200-14 browser proof.",
        "command_id": f"hs200-14-{uuid.uuid4().hex[:8]}",
    }, token=TOKEN)
    return created["project"]["id"]


def _seed_gh_connection() -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, created_at, updated_at) "
            "VALUES ('wpc-gh', 'github', ?, 'connected', "
            " datetime('now'), datetime('now'), datetime('now'))",
            (OWNER_LOGIN,),
        )


def _seed_watch(project_id: str, *, watch_id: str, name: str, snapshot: list[dict[str, Any]], state: str = "active") -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, state, created_at, updated_at) "
            "VALUES (?, 'gh', 'pull_requests', ?, ?, ?, 1, datetime('now'), NULL, ?, ?, "
            " datetime('now'), datetime('now'))",
            (watch_id, name, json.dumps({"repository": name}, sort_keys=True),
             json.dumps(snapshot), project_id, state),
        )


def _seed_meeting_with_proposals(project_id: str, proposals: list[tuple[str, str]]) -> list[str]:
    """A finalized meeting linked to the Project and one PROPOSED action per
    (owner, text); returns the proposal ids for the real confirm route."""
    from holdspeak.db import get_database
    db = get_database()
    now = datetime.now()
    ids: list[str] = []
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, intel_status, capture_status, provenance) "
            "VALUES ('m-review', ?, ?, 'Architecture review', 1800.0, 'complete', 'finalized', 'desktop')",
            ((now - timedelta(hours=2)).isoformat(), (now - timedelta(hours=1, minutes=30)).isoformat()),
        )
        conn.execute(
            "INSERT OR IGNORE INTO meeting_projects (meeting_id, project_id, source, confidence) "
            "VALUES ('m-review', ?, 'manual', 1.0)",
            (project_id,),
        )
        for index, (owner, text) in enumerate(proposals):
            pid = f"prop-{uuid.uuid4().hex[:12]}"
            conn.execute(
                "INSERT INTO follow_through_proposals "
                "(id, meeting_id, project_id, kind, text, owner_hint, due_hint, source_plugin, "
                " fingerprint, state, model_host, created_at, segment_index, span_start, span_end) "
                "VALUES (?, 'm-review', ?, 'action', ?, ?, NULL, 'decision_capture', ?, 'proposed', "
                " '192.168.1.43', ?, ?, ?, ?)",
                (pid, project_id, text, owner, f"fp-{uuid.uuid4().hex[:12]}", now.isoformat(),
                 2 + index, 10.0 + index * 5, 14.0 + index * 5),
            )
            ids.append(pid)
    return ids


def _person(page: Any, name: str, *, aliases: tuple[str, ...] = (), project_id: str | None = None) -> str:
    created = _api(page, "POST", "/api/people/relationships", {"display_name": name}, token=TOKEN)
    rid = str(created["relationship"]["id"])
    for alias in aliases:
        _api(page, "POST", f"/api/people/relationships/{rid}/owner-aliases", {"alias": alias}, token=TOKEN)
    if project_id:
        _api(page, "POST", f"/api/people/relationships/{rid}/projects/{project_id}", {}, token=TOKEN)
    return rid


def _seed_ready_desk(page: Any) -> dict[str, str]:
    """His desk, with the ledger set up: Priya Sharma + Priya Nair (a shared
    first name), Marek Kubiak linked to the Project by `project_refs` and
    to his GitHub login by an owner alias; a review meeting whose two
    actions name `Priya` and `marek-k`; a PR waiting on `marek-k`."""
    _seed_gh_connection()
    project_id = _create_project(page, "Q4 platform")
    _api(page, "POST", "/api/people/setup", {}, token=TOKEN)
    sharma = _person(page, "Priya Sharma")
    nair = _person(page, "Priya Nair")
    marek = _person(page, "Marek Kubiak", aliases=("marek-k",), project_id=project_id)
    proposals = _seed_meeting_with_proposals(project_id, [
        ("Priya", "Confirm the freeze window"),
        ("marek-k", "Own the PostgreSQL migration"),
    ])
    for pid in proposals:
        confirmed = _api(page, "POST", f"/api/proposals/{pid}/confirm", {}, token=TOKEN)
        assert "error" not in confirmed, confirmed
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    _seed_watch(project_id, watch_id="w-prs", name="karolswdev/HoldSpeak", snapshot=[
        {"number": 612, "title": "Rig settles animations", "state": "OPEN",
         "reviewRequests": ["marek-k"], "updatedAt": yesterday},
        {"number": 613, "title": "Fix token alignment", "state": "OPEN",
         "reviewRequests": ["marek-k", OWNER_LOGIN], "updatedAt": yesterday},
    ])
    # A revoked source (counsel P2-v): paused, so its PR names Marek but
    # contributes no count -- the row must say `PAUSED · OMITTED`.
    _seed_watch(project_id, watch_id="w-paused", name="karolswdev/Paused", state="paused", snapshot=[
        {"number": 700, "title": "Old work", "state": "OPEN",
         "reviewRequests": ["marek-k"], "updatedAt": yesterday},
    ])
    return {"project_id": project_id, "sharma": sharma, "nair": nair, "marek": marek}


# ── glass helpers ────────────────────────────────────────────────────


def _arrive(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)


def _open_room(page: Any, project_id: str) -> None:
    page.evaluate(
        """([key, scope]) => {
          sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key, scope}));
        }""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.get_by_test_id("room-people-head-verb").wait_for(timeout=15000)
    _settle(page)


def _people_section(page: Any) -> Any:
    return page.locator("section.surface-section").filter(has=page.get_by_test_id("room-people-head-verb")).first


def _scroll_people_into_view(page: Any) -> None:
    """Put the section HEAD at the top of the body: the ask well is sticky
    at the foot at every width (Room condition 7), so a row merely
    "in view" can still sit underneath the composer (the 41 scar)."""
    _people_section(page).evaluate("el => el.scrollIntoView({block: 'start'})")
    _settle(page)


def _shot(page: Any, name: str, width: int) -> Path | None:
    """Take a shot with the pointer parked off every row (no hover state)."""
    if not WRITE_SHOTS:
        return None
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.mouse.move(2, 2)
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _room_window(page: Any) -> Any:
    return page.locator(".desk-surface-window").filter(has=page.get_by_test_id("room-people-head-verb")).first


def _primaries(page: Any) -> list[str]:
    """Every filled primary on the FACE (the Room window; the desk behind it
    is another face with its own one): at most one."""
    return _room_window(page).evaluate("""(win) => [...win.querySelectorAll('.btn--primary')]
        .filter(b => b.getBoundingClientRect().width > 0)
        .map(b => (b.className + ' :: ' + (b.textContent || '').trim()))""")


def _overflowing(page: Any, width: int) -> list[str]:
    """Every interactive element whose right edge passes the viewport."""
    return page.evaluate("""(width) => {
        const out = [];
        const chair = document.querySelector('.chair') || document;
        const sel = 'button, a, [role="button"], [role="group"], .surface-disclosure-trigger';
        for (const el of chair.querySelectorAll(sel)) {
            const r = el.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) continue;
            if (r.right > width + 0.5) out.push((el.className || el.tagName) + ' :: ' + (el.textContent || '').trim().slice(0, 40) + ' right=' + r.right.toFixed(1));
        }
        return out;
    }""", width)


def _raw_buttons(page: Any) -> list[str]:
    """Every <button> in the PEOPLE section that is not the library Button,
    the mic, a ledger line, or a library Disclosure trigger."""
    return _people_section(page).evaluate("""(section) => {
        const raw = [];
        for (const btn of section.querySelectorAll('button')) {
            const cls = btn.className || '';
            if (!cls.includes('btn') && !cls.includes('desk-mic') &&
                !cls.includes('surface-ledger-line') &&
                !cls.includes('surface-disclosure-trigger')) raw.push(cls + ' :: ' + (btn.textContent || '').trim());
        }
        return raw;
    }""")


def _zero_counters(page: Any) -> list[str]:
    """Any `0 <NOUN>` or `0 OF` token on the section (A.8) -- except the
    typed partial `PEOPLE 0 OF N`, which is a coverage fraction, not a
    counter."""
    text = _people_section(page).inner_text()
    return [
        line.strip() for line in text.split("\n")
        if line.strip().startswith("0 ") and not line.strip().startswith("0 OF")
        or " 0 " in f" {line.strip()} " and "0 OF" not in line
    ]


def _people_body_check(page: Any, width: int) -> None:
    assert _raw_buttons(page) == [], "every verb is the library Button (A.1)"
    assert _zero_counters(page) == [], "no counters of zero (A.8)"
    assert len(_primaries(page)) <= 1, f"one filled primary per face: {_primaries(page)}"
    if width <= 480:
        assert page.evaluate("document.documentElement.scrollWidth") <= width
        over = _overflowing(page, width)
        assert over == [], f"elements past the viewport at {width}: {over}"


# ── legs ─────────────────────────────────────────────────────────────


def _run_ready_resolve_and_people(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _ensure_build()
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    key_file = home / "people-dev-key.json"
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(key_file))
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 1000})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            seeds = _seed_ready_desk(page)
            project_id = seeds["project_id"]

            # ── ready: the typed partial and the ambiguous owner ──
            _open_room(page, project_id)
            _scroll_people_into_view(page)
            section = _people_section(page)
            assert section.locator("h3").inner_text().strip() == "PEOPLE 1 OF 2"
            assert page.get_by_test_id("room-people-gaps").inner_text().strip() == "1 AMBIGUOUS"
            owner_tokens = [t.strip() for t in page.get_by_test_id("room-people-owner-token").all_inner_texts()]
            assert owner_tokens == ["OWNER · AMBIGUOUS · 2 MATCHES"], owner_tokens
            body = section.inner_text()
            assert "Priya Sharma" not in body and "Priya Nair" not in body, "an ambiguous owner was attributed"
            assert "marek-k" not in body, "a raw login crossed onto the face"
            assert "Marek Kubiak" in body
            marek_row = page.get_by_test_id("room-people-row").filter(has_text="Marek Kubiak").first
            marek_li = marek_row.locator("xpath=ancestor::li[1]")
            assert "1 OPEN COMMITMENT" in marek_li.inner_text()
            commitment = marek_li.get_by_test_id("room-people-commitment").first
            assert "Own the PostgreSQL migration" in commitment.inner_text()
            # Tokens are CSS-uppercased on the face; compare the rendered case.
            assert "MEETING · ARCHITECTURE REVIEW · SEGMENT 4" in commitment.inner_text().upper()
            assert commitment.get_by_test_id("room-people-open-source").count() == 1
            fact = marek_li.get_by_test_id("room-people-fact").first
            assert "karolswdev/HoldSpeak" in fact.inner_text() and "2 PRS WAITING" in fact.inner_text()
            assert marek_li.get_by_test_id("room-people-fact").count() == 1, "a paused Watch contributed a count"
            omitted = marek_li.get_by_test_id("room-people-omitted").first
            assert "karolswdev/Paused" in omitted.inner_text()
            assert omitted.get_by_test_id("room-people-omitted-token").inner_text().strip().upper() == "PAUSED · OMITTED"
            priya_li = page.get_by_test_id("room-people-unresolved-row").first.locator("xpath=ancestor::li[1]")
            assert "Confirm the freeze window" in priya_li.inner_text()
            assert page.get_by_test_id("room-people-head-verb").inner_text().strip() == "People"
            _people_body_check(page, width)
            _shot(page, "people-ready", width)

            # ── resolve: candidates under the row, no modal, the ledger's own write ──
            resolve = page.get_by_test_id("room-people-resolve-verb")
            assert resolve.get_attribute("aria-label") == "Resolve: Priya"
            resolve.click()
            page.get_by_test_id("room-people-resolve").wait_for(timeout=5000)
            _settle(page)
            assert page.locator("[role='dialog']").count() == 0, "no modals (A.4)"
            well = page.get_by_test_id("room-people-resolve")
            names = [t.strip() for t in well.get_by_test_id("room-people-candidate").all_inner_texts()]
            assert sorted(names) == ["Priya Nair", "Priya Sharma"], names
            _people_body_check(page, width)
            _shot(page, "people-resolve", width)
            well.get_by_test_id("room-people-candidate").filter(has_text="Priya Sharma").click()
            page.locator("section.surface-section h3", has_text="PEOPLE 2").first.wait_for(timeout=10000)
            _settle(page)
            assert page.get_by_test_id("room-people-gaps").count() == 0, "no gap tokens once complete"
            assert page.get_by_test_id("room-people-unresolved-row").count() == 0
            sharma_body = page.get_by_test_id("room-people-row").filter(has_text="Priya Sharma").first.locator("xpath=ancestor::li[1]").inner_text()
            assert "Confirm the freeze window" in sharma_body, "the commitment moved onto the resolved person"
            detail = _api(page, "GET", f"/api/people/relationships/{seeds['sharma']}", token=TOKEN)
            assert "Priya" in (detail["relationship"].get("owner_aliases") or []), "the alias landed in the ledger"
            _people_body_check(page, width)
            _shot(page, "people-resolved", width)

            # ── People: scoped to the Project, and the way back ──
            verb = page.get_by_test_id("room-people-head-verb")
            verb.focus()
            verb.click()
            page.get_by_test_id("people-roster-everyone").wait_for(timeout=15000)
            people_window = page.locator(".desk-surface-window").filter(
                has=page.get_by_test_id("people-roster-everyone"),
            ).first
            _settle(page)
            roster = people_window.inner_text()
            assert "1 ON THIS PROJECT" in roster and "Marek Kubiak" in roster
            assert "2 MORE · Everyone" in roster
            assert "Priya Nair" not in roster
            if width <= 480:
                over = _overflowing(page, width)
                assert over == [], f"elements past the viewport at {width}: {over}"
            _shot(page, "people-core-project", width)
            # The window's own traffic light (the dock carries a second `Close
            # People`; the window region is the one being closed).
            page.get_by_role("region", name="People").get_by_label("Close People").click()
            page.wait_for_function(
                "() => document.activeElement && document.activeElement.dataset.testid === 'room-people-head-verb'",
                timeout=5000,
            )
            _settle(page)

            # ── locked: the key file turns unreadable ──
            key_file.write_text("{not json", encoding="utf-8")
            readiness = _api(page, "GET", "/api/people/readiness", token=TOKEN)
            assert readiness["state"] == "locked", readiness
            _open_room(page, project_id)
            _scroll_people_into_view(page)
            section = _people_section(page)
            assert section.locator("h3").inner_text().strip() == "PEOPLE 0 OF 2"
            assert page.get_by_test_id("room-people-gaps").inner_text().strip() == "LOCKED"
            assert page.get_by_test_id("room-people-head-verb").inner_text().strip() == "Unlock"
            owner_tokens = sorted(t.strip() for t in page.get_by_test_id("room-people-owner-token").all_inner_texts())
            assert owner_tokens == ["OWNER · LOCKED", "OWNER · LOCKED"], owner_tokens
            assert page.get_by_test_id("room-people-resolve-verb").count() == 0, "no dead verb under a lock"
            body = section.inner_text()
            assert "Priya Sharma" not in body and "Marek Kubiak" not in body, "a locked store named nobody"
            assert "marek-k" in body or "Priya" in body
            _people_body_check(page, width)
            _shot(page, "people-locked", width)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_not_set_up(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _ensure_build()
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(home / "people-dev-key.json"))
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 1000})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            project_id = _create_project(page, "Q4 platform")
            proposals = _seed_meeting_with_proposals(project_id, [("Priya", "Confirm the freeze window")])
            for pid in proposals:
                _api(page, "POST", f"/api/proposals/{pid}/confirm", {}, token=TOKEN)
            assert _api(page, "GET", "/api/people/readiness", token=TOKEN)["state"] == "unconfigured"

            _open_room(page, project_id)
            _scroll_people_into_view(page)
            section = _people_section(page)
            assert section.locator("h3").inner_text().strip() == "PEOPLE 0 OF 1"
            assert page.get_by_test_id("room-people-gaps").inner_text().strip() == "NOT SET UP"
            assert page.get_by_test_id("room-people-head-verb").inner_text().strip() == "Set up People"
            owner_tokens = [t.strip().upper() for t in page.get_by_test_id("room-people-owner-token").all_inner_texts()]
            assert owner_tokens == ["OWNER · NOT SET UP"], owner_tokens
            assert page.get_by_test_id("room-people-resolve-verb").count() == 0
            _people_body_check(page, width)
            _shot(page, "people-not-set-up", width)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── entry points ─────────────────────────────────────────────────────


class TestPeoplePreparationGlass:
    @pytest.mark.timeout(240)
    def test_ready_resolve_people_locked_1440(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _run_ready_resolve_and_people(tmp_path, monkeypatch, 1440)

    @pytest.mark.timeout(240)
    def test_ready_resolve_people_locked_393(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _run_ready_resolve_and_people(tmp_path, monkeypatch, 393)

    @pytest.mark.timeout(180)
    def test_not_set_up_1440(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _run_not_set_up(tmp_path, monkeypatch, 1440)

    @pytest.mark.timeout(180)
    def test_not_set_up_393(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _run_not_set_up(tmp_path, monkeypatch, 393)
