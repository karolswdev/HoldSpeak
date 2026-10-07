"""PHILO-15 01 — a Default for AI work clears "No engine for summaries".

"Set up local AI" assigns the LAN model as the GLOBAL default. The
meeting-intel queue reads that head (``meeting-intel-queue@2``), so a
summary would run. The roster states the queue's answer
(``task_overrides[].queue``); Needs you and the Brief read it and draw no
summaries row. 1440 + 393, on a real hub over an isolated HOME.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytestmark = pytest.mark.chair_windows_open

pytest.importorskip("playwright.sync_api", reason="PHILO-15 glass needs Playwright")

SHOTS = evidence_dir("docs/internal/philo/phase-15/shots/01-false-blocker")
TOKEN = "philo15-01"
SUMMARY = "meeting.deferred_analysis"
FALSE_ROW = "No engine for summaries"


def _assign_lan_default() -> None:
    """The state "Set up local AI" leaves: one LAN model as the global default."""
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

    db = get_database()
    _profile(
        db,
        "lan-qwen",
        claims=("language", "structured_output", _result_claim(SUMMARY)),
        modalities=("language", "text"),
        model="qwen3.8-27b",
        boundary="private_network",
    )
    InferenceAssignmentService(db).set_assignment(
        Principal(PrincipalKind.OWNER, "philo15-owner"),
        {
            "command_id": "philo15-01-default",
            "expected_revision": 0,
            "scope": {"kind": "global"},
            "entries": [{"profile_id": "lan-qwen", "profile_revision": 1}],
        },
    )


def _open_brief(page: Any, width: int) -> None:
    if width == 393:
        page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
        page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')").click()
    page.locator("[data-testid='arrival-brief-generate']").first.wait_for(timeout=15_000)


class TestDefaultClearsSummaries:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _assign_lan_default()
        yield
        self.server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_needs_you_and_brief_draw_no_false_row(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            _normal_chair(page)
            page.locator("[data-testid='arrival-display']").wait_for(timeout=15_000)
            _settle(page)

            # The roster states the queue's answer: a summary would run.
            roster = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            row = next(r for r in roster["task_overrides"] if r["id"] == SUMMARY)
            assert row["has_override"] is False, row
            assert row["queue"]["status"] == "assigned", row
            assert row["queue"]["inherited_from"] == "global", row

            # The hub's Needs you: no summaries blocker.
            needs = _api(page, "GET", "/api/desk/needs-you", token=TOKEN)
            assert "No engine for summaries" not in str(needs), needs

            # Needs you on the glass.
            page.wait_for_timeout(1_500)
            assert page.locator("[data-object-id='blocker:summary']").count() == 0
            assert page.locator("[data-object-id='blocker:engines']").count() == 0
            assert FALSE_ROW not in (page.locator("body").inner_text() or "")
            page.screenshot(path=str(SHOTS / f"needs-you-{width}.png"), full_page=False)

            # The Brief: generate it; the false row is not copied in.
            _open_brief(page, width)
            page.locator("[data-testid='arrival-brief-generate']").first.click()
            page.wait_for_function(
                """() => !!document.querySelector(
                  "[data-testid='arrival-brief-headline'], [data-testid='arrival-brief-row'], [data-testid='arrival-brief-handled']")""",
                timeout=20_000,
            )
            _settle(page)
            brief = _api(page, "GET", "/api/brief/latest", token=TOKEN)
            assert FALSE_ROW not in str(brief), brief
            assert FALSE_ROW not in (page.locator("body").inner_text() or "")
            page.screenshot(path=str(SHOTS / f"brief-{width}.png"), full_page=False)
            browser.close()
        assert not errors, errors
