"""PHILO-15 08 (B03) -- confirm an action item from a meeting in NO Project,
from its Needs row, AS RENDERED at 1440x900 and 393x852.

The meeting is an imported recording with a transcript and a finished
summary. Its summary carried decisions and action items; the REAL proposal
bridge (``ProposalBridgeService.bridge_meeting_artifacts``) turns the
summary's artifact into proposals. The meeting is in no Project.

  * The Needs row for the action says TO CONFIRM and carries Decline, Defer
    and Confirm as library Buttons with words (no glyph-only control).
  * The summary's own To review card of the same action is not a second row.
  * Confirm: the row leaves Needs; the proposal is confirmed; the summary's
    action row is accepted (one obligation, one row).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

# PHILO-14 A1: the Chair is the screen of objects; the Needs list is on it.
pytestmark = pytest.mark.chair_windows_open

pytest.importorskip("playwright.sync_api", reason="the confirm glass needs Playwright")

TOKEN = "philo15-08-confirm"
SHOTS = evidence_dir("docs/internal/philo/phase-15/08-shots")
SIZES = {1440: 900, 393: 852}
MEETING = "m-philo15-08"
ACTION = "Add the named failure fence before ship"
DECISION = "Use a recorded provider reply for isolated rig tests"


def _seed() -> dict[str, str]:
    """A finished summary of an unfiled meeting, bridged by the real bridge."""
    from holdspeak.db import get_database
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db = get_database()
    now = datetime.now()
    action_id = "action_philo15_08_priya"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, ended_at, title, duration_seconds, "
            " intel_status, intel_completed_at, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, 35.0, 'complete', ?, 'finalized', 'desktop')",
            (MEETING, (now - timedelta(minutes=20)).isoformat(),
             (now - timedelta(minutes=19)).isoformat(), "philo3_architect_meeting",
             (now - timedelta(minutes=18)).isoformat()),
        )
        for start, end, text in (
            (0.0, 26.0, "Decision three: use a recorded provider reply for isolated rig tests."),
            (26.0, 35.0, "Action: Priya Shah will add the named failure fence before ship."),
        ):
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
                "VALUES (?, ?, 'Speaker', ?, ?)",
                (MEETING, text, start, end),
            )
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, created_at) "
            "VALUES (?, ?, ?, 'Priya Shah', 'Friday', 'pending', 'pending', ?)",
            (action_id, MEETING, ACTION, now.isoformat()),
        )
        conn.execute(
            "INSERT INTO artifacts (id, meeting_id, origin, artifact_type, title, structured_json, "
            " confidence, status, plugin_id, plugin_version) "
            "VALUES (?, ?, 'meeting', 'summary_items', 'Decisions and action items', ?, 1.0, "
            " 'draft', 'meeting_summary', '1')",
            (f"summary-items-{MEETING}", MEETING, json.dumps({
                "decisions": [{"decision": DECISION, "rationale": None}],
                "action_items": [{"task": ACTION, "owner": "Priya Shah", "due": "Friday",
                                  "action_item_id": action_id}],
            })),
        )
        conn.commit()
    created = ProposalBridgeService(db).bridge_meeting_artifacts(MEETING)
    assert {p.kind for p in created} == {"decision", "action"}, created
    return {"action_item_id": action_id,
            "proposal_id": next(p.id for p in created if p.kind == "action")}


class TestConfirmFromAnUnfiledMeeting:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        self.ids = _seed()
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_confirm_an_action_item_from_its_needs_row(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        record: dict[str, Any] = {"width": width}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)

                row = page.locator("[data-testid='needs-row']", has_text=ACTION).first
                row.wait_for(timeout=20_000)
                row.scroll_into_view_if_needed()
                _settle(page)
                verbs = [" ".join(t.split()) for t in row.locator("[data-testid='needs-row-verb']").all_inner_texts()]
                record["verbs"] = verbs
                assert verbs == ["Decline", "Defer", "Confirm"], verbs
                assert "TO CONFIRM" in row.inner_text()
                # The summary's own To review card of this action is not a second row.
                same = page.locator("[data-testid='needs-row']", has_text=ACTION)
                assert same.count() == 1, same.all_inner_texts()
                page.screenshot(path=str(SHOTS / f"needs-row-{width}.png"))

                row.get_by_role("button", name=f"Confirm: {ACTION}").click()
                page.locator("[data-testid='needs-row']", has_text=ACTION).first.wait_for(
                    state="detached", timeout=20_000,
                )
                _settle(page)
                page.screenshot(path=str(SHOTS / f"needs-after-confirm-{width}.png"))

                wire = _api(page, "GET", f"/api/meetings/{MEETING}/follow-through-proposals", token=TOKEN)
                states = {p["id"]: p["state"] for p in wire["proposals"]}
                record["states"] = states
                assert states[self.ids["proposal_id"]] == "confirmed", states
                from holdspeak.db import get_database

                with get_database()._connection() as conn:
                    rows = conn.execute(
                        "SELECT id, review_state FROM action_items WHERE meeting_id=?", (MEETING,),
                    ).fetchall()
                record["action_rows"] = [dict(r) for r in rows]
                assert [(r["id"], r["review_state"]) for r in rows] == [
                    (self.ids["action_item_id"], "accepted"),
                ], record["action_rows"]
                record["page_errors"] = errors
                assert not errors, errors
            finally:
                (SHOTS / f"glass-{width}.json").write_text(json.dumps(record, indent=2, default=str))
                browser.close()
