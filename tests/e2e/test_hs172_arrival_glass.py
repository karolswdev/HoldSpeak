"""HS-172 -- arrival face glass rig for proposal rows.

Seed a project with needs-you items including follow-through proposals,
meetings with intel_status=complete. Assert at 1440 + 393:
  - headline counts proposals in the total
  - MTG emblem on proposal rows
  - Decide:/Confirm: prefix (accent) + text + by Fri
  - Confirm (primary) + Open (ghost) verbs
  - MEETINGS section shows RAN chip
  - no raw <button>, no zero counter, no LOCAL, no text clip
  - shots to story-03-shots/

Companion to test_hs170_arrival_glass.py (not edited).

PHILO-14 A5: the Needs-you window body is the smart drawer. A proposal is
a `needs-row` (`data-object-id` `proposal:<id>`): its fact names the
meeting it came from, its lamp the act (`TO DECIDE` / `TO CONFIRM`), its
verb `Confirm` (`needs-row-verb`, `data-verb="confirm"`); the row body opens
it (`data-opens`). Testids: `needs-drawer`, `needs-list`, `needs-row`,
`needs-source-row`, `needs-row-verb`.
"""
from __future__ import annotations

import json
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
    REPO,
)
from tests._evidence import evidence_dir
from .chair_windows import open_chair_window

pytest.importorskip("playwright.sync_api", reason="Arrival glass needs Playwright")

SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/story-03-shots")
TOKEN = "hs172-arrival"


# ── Seed ────────────────────────────────────────────────────────


def _seed_project(conn: Any, project_id: str, name: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO projects "
        "(id, name, description, keywords_json, team_members_json, "
        "context_json, detection_threshold, is_archived, revision, "
        "target_at, created_at, updated_at) "
        "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, NULL, "
        "'2026-09-01T00:00:00', '2026-09-05T10:00:00')",
        (project_id, name),
    )


def _seed_gh_connection(conn: Any) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO watch_provider_connections "
        "(id, provider_id, external_connection_ref, state, "
        " last_connected_at, created_at, updated_at) "
        "VALUES ('wpc-gh', 'github', 'karolswdev', 'connected', "
        " datetime('now'), datetime('now'), datetime('now'))",
    )


def _seed_watch(conn: Any, project_id: str, watch_id: str,
                snapshot: list[dict[str, Any]]) -> None:
    conn.execute(
        "INSERT INTO connector_watches "
        "(id, connector_id, query_kind, name, query_json, snapshot_json, "
        " enabled, last_success_at, last_error, project_id, "
        " created_at, updated_at) "
        "VALUES (?, 'gh', 'pull_requests', 'gh prs', '{}', ?, 1, "
        " datetime('now'), NULL, ?, datetime('now'), datetime('now'))",
        (watch_id, json.dumps(snapshot), project_id),
    )


def _seed_all() -> None:
    from holdspeak.db import get_database
    db = get_database()
    now = datetime.now()

    with db._connection() as conn:
        # Project
        _seed_project(conn, "proj-a", "Q4 Platform")
        _seed_gh_connection(conn)

        # Watch with 1 PR waiting on review (a needs-you item)
        _seed_watch(conn, "proj-a", "w-prs", [
            {
                "title": "Rig settles animations before every shot",
                "number": 612,
                "state": "open",
                "url": "https://github.com/karolswdev/holdspeak/pull/612",
                "reviewRequests": ["karolswdev"],
                "created_at": (now - timedelta(days=3)).isoformat(),
                "updated_at": now.isoformat(),
            }
        ])

        # Meeting with intel=complete
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'complete', 'finalized', 'desktop')",
            (
                "m-standup",
                (now - timedelta(hours=1)).isoformat(),
                (now - timedelta(minutes=30)).isoformat(),
                "Standup",
                1800.0,
            ),
        )
        for i in range(3):
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
                "VALUES (?, ?, ?, ?, ?)",
                ("m-standup", f"Topic {i}", "Karol", float(i * 600), float((i + 1) * 600)),
            )

        # Link meeting to project
        conn.execute(
            "INSERT OR IGNORE INTO meeting_projects (meeting_id, project_id) "
            "VALUES ('m-standup', 'proj-a')",
        )

        # Follow-through proposals
        proposals = [
            ("action", "Marek owns the PostgreSQL migration", "Fri"),
            ("decision", "cut-over on the 12th", None),
        ]
        for kind, text, due in proposals:
            pid = f"prop-{uuid.uuid4().hex[:12]}"
            fp = f"fp-{uuid.uuid4().hex[:16]}"
            conn.execute(
                "INSERT INTO follow_through_proposals "
                "(id, meeting_id, project_id, kind, text, due_hint, "
                " source_plugin, fingerprint, state, model_host, created_at) "
                "VALUES (?, 'm-standup', 'proj-a', ?, ?, ?, 'decision_capture', ?, "
                " 'proposed', '192.168.1.43', ?)",
                (pid, kind, text, due, fp, now.isoformat()),
            )

        # Second meeting — OFF, for contrast
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'disabled', 'finalized', 'desktop')",
            (
                "m-oneone",
                (now + timedelta(hours=4)).isoformat(),
                None,
                "1:1 Ania",
                1800.0,
            ),
        )

        conn.commit()


# ── The rig ────────────────────────────────────────────────────


class TestArrivalProposals:
    """HS-172 -- arrival face with proposal rows."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _seed_all()
        self.tmp_path = tmp_path

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.parametrize("width", [1440, 393])
    def test_arrival_proposals(self, width: int) -> None:
        from playwright.sync_api import sync_playwright, expect

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _normal_chair(page)

            # Wait for arrival
            headline = page.locator("[data-testid='arrival-display']")
            headline.wait_for(timeout=10_000)
            _settle(page)

            headline_text = headline.text_content() or ""
            # headline should show need count
            assert "need" in headline_text.lower(), (
                f"Headline at {width}: {headline_text}"
            )

            # A proposal row is its object: it names the meeting it came
            # from, the act it asks for, its verb, and its body opens it.
            proposal_rows = page.locator("[data-testid='needs-row'][data-object-id^='proposal:']")
            assert proposal_rows.count() >= 1, f"No proposal rows at {width}"
            facts = proposal_rows.locator(".needs-row-fact").all_text_contents()
            assert all(f.startswith("from ") for f in facts), f"proposal facts at {width}: {facts}"
            confirm_btns = proposal_rows.locator("[data-verb='confirm']")
            assert confirm_btns.count() == proposal_rows.count(), (
                f"Confirm on every proposal row at {width}, got {confirm_btns.count()}"
            )
            assert proposal_rows.first.get_attribute("data-opens") == "true", (
                f"the proposal row body opens it at {width}"
            )
            lamps = proposal_rows.locator(".needs-row-lamp").all_text_contents()
            assert any("TO DECIDE" in t for t in lamps), f"Missing TO DECIDE at {width}: {lamps}"
            assert any("TO CONFIRM" in t for t in lamps), f"Missing TO CONFIRM at {width}: {lamps}"

            # No raw <button> outside the surface kit
            raw_buttons = page.evaluate("""() => {
                const body = document.querySelector('.chair');
                if (!body) return [];
                // HS-200-15: the library Disclosure owns its own trigger
                // (the row's MORE control); it is a species, not a raw button.
                const allowed = ['btn', 'desk-mic', 'surface-ledger-line',
                    'gadget-cycle', 'gadget-stepper-btn', 'surface-disclosure-trigger'];
                // PHILO-13-11 (slice two): the Chair is windows; a title bar's
                // gadgets are the library chrome Button, fenced by
                // test_philo13_11_frame_glass.py F2. The body law is unchanged.
                return Array.from(body.querySelectorAll('button'))
                    .filter(b => !b.closest('.desk-pullout-head'))
                    .filter(b => !allowed.some(c => b.classList.contains(c)))
                    .map(b => (b.textContent || '').trim().slice(0, 40));
            }""")
            assert len(raw_buttons) == 0, f"Raw buttons at {width}: {raw_buttons}"

            # No zero counter
            body_text = page.locator(".chair").text_content() or ""
            assert "0 NEEDS" not in body_text, f"Zero counter at {width}"

            # No LOCAL
            assert "LOCAL" not in body_text, f"'LOCAL' at {width}"

            # MEETINGS section: RAN chip (renders as StateChip, not badge span)
            # PHILO-13-11 (slice two, R2): at 393 the meetings are in The week.
            if width <= 720:
                open_chair_window(page, "The week")
            meetings_section = page.locator("[data-testid='arrival-meeting-row']")
            meetings_text = ""
            for j in range(meetings_section.count()):
                meetings_text += meetings_section.nth(j).text_content() or ""
            assert "RAN" in meetings_text, (
                f"RAN label missing in meetings at {width}: {meetings_text[:200]}"
            )

            # No text clip on proposal primaries
            proposals_clipped = page.evaluate("""() => {
                const texts = document.querySelectorAll('[data-testid="needs-row"][data-object-id^="proposal:"] .needs-row-name');
                const clipped = [];
                for (const t of texts) {
                    if (t.scrollWidth > t.clientWidth + 2) {
                        clipped.push(t.textContent?.trim().slice(0, 40));
                    }
                }
                return clipped;
            }""")
            assert len(proposals_clipped) == 0, (
                f"Clipped proposals at {width}: {proposals_clipped}"
            )

            # Screenshot
            _settle(page)
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(SHOTS / f"build-arrival-confirm-{width}.png"),
                full_page=True,
            )

            # 393: nothing overflows
            if width == 393:
                no_overflow = page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth"
                )
                assert no_overflow, f"Arrival overflows at {width}"

            _assert_clean(page, errors)
            page.close()
            errors.clear()

            browser.close()

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    def test_arrival_confirm_fires(self) -> None:
        """Click Confirm on a proposal; assert the row leaves, headline drops, kernel fired."""
        from playwright.sync_api import sync_playwright

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _normal_chair(page)

            headline = page.locator("[data-testid='arrival-display']")
            headline.wait_for(timeout=10_000)
            _settle(page)

            confirm_btns = page.locator("[data-testid='needs-row'][data-object-id^='proposal:'] [data-verb='confirm']")
            assert confirm_btns.count() >= 2, "The seed gives an action and a decision proposal"

            # The proposal is chosen by its kind, never by its place in the
            # list (the ids are random, so the order is). Each kind results
            # in a different member of the hub's one rule (#788):
            #   action   -> a Room commitment that owns its action item; the
            #               commitment row is the member, no Door card.
            #   decision -> an action item with no owner; its Door card
            #               (UNASSIGNED) is the member.
            seeded = _api(page, "GET", "/api/projects/proj-a/proposals", token=TOKEN)["proposals"]
            by_kind = {p["kind"]: p for p in seeded if p["state"] == "proposed"}
            assert {"action", "decision"} <= set(by_kind), seeded

            def proposals(answer: dict) -> dict:
                return {row["id"]: row["title"] for row in answer["items"]
                        if row.get("source") == "proposal"}

            for kind in ("action", "decision"):
                proposal = by_kind[kind]
                title = proposal["text"]
                before = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
                count_before = confirm_btns.count()
                assert f"proposal:{proposal['id']}" in proposals(before), (kind, before["items"])

                page.get_by_role("button", name=f"Confirm: {title}", exact=True).click()
                page.wait_for_timeout(1500)
                _settle(page)

                assert confirm_btns.count() == count_before - 1, (
                    f"{kind}: Confirm count didn't drop: {count_before} -> {confirm_btns.count()}"
                )
                after = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
                # Exactly this proposal's row left.
                assert set(proposals(before)) - set(proposals(after)) == {f"proposal:{proposal['id']}"}, (
                    kind, proposals(before), proposals(after),
                )
                assert not set(proposals(after)) - set(proposals(before))
                members = {member["ref"] for member in after["members"]}
                same_title = [row for row in after["items"]
                              if row["title"] == title and row.get("source") != "proposal"]
                assert len(same_title) == 1, (kind, after["items"])
                row = same_title[0]
                if kind == "action":
                    assert row["source"] == "commitment" and row.get("actionItemId"), row
                    # The commitment owns its action item: no Door card for it.
                    assert not [r for r in after["items"]
                                if r.get("_isDoor") and r.get("ref") == row["actionItemId"]], after["items"]
                else:
                    assert row["source"] == "action_item" and row["why"] == "UNASSIGNED", row
                    assert row.get("_isDoor"), row
                assert (row.get("ref") if row.get("ref") is not None else row["id"]) in members, (row, members)
                # The headline is the hub's number.
                new_headline = (headline.text_content() or "").strip()
                assert new_headline.startswith(f"{after['count']} need"), (
                    f"{kind}: headline is not the hub's number {after['count']}: {new_headline}"
                )

            result = _api(page, "GET",
                "/api/projects/proj-a/proposals?state=confirmed",
                token=TOKEN)
            confirmed = result.get("proposals", [])
            assert {p["id"] for p in confirmed} >= {by_kind["action"]["id"], by_kind["decision"]["id"]}, (
                f"Both proposals must read confirmed: {result}"
            )

            _assert_clean(page, errors)
            page.close()
            browser.close()
