"""PHILO-15 05 — three strong defaults on a real hub over an isolated HOME,
shot at 1440 and 393.

1. The lane's draft chip names the Default for AI work's model: Cadence
   drafts are OWNER work and inherit the default (no exact assignment).
2. The Brief generated itself: the cadence thread's Brief job (ON by default)
   ran at 06:00; the Brief window shows GENERATED <date> 06:00, and Generate
   stays for a re-run.
3. Anthropic reads NOT SUPPORTED YET: the Concierge's api.anthropic.com row
   (a real legacy profile through the real ``detect``) never reads READY.

Shots go to ``docs/internal/philo/phase-15/shots/05-strong-defaults/`` only
with HOLDSPEAK_EVIDENCE_WRITE=1, else to ``.tmp/evidence-shots/``.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="PHILO-15 glass needs Playwright")

SHOTS = evidence_dir("docs/internal/philo/phase-15/shots/05-strong-defaults")
TOKEN = "p14-c2-lane"  # the lane seed's credential minting reads this token
DEFAULT_PROFILE = "qwen3-8-27b"


def _assign_lan_default() -> str:
    """The state "Set up local AI" leaves: one LAN model as the GLOBAL default,
    nothing exact for Cadence drafts. Returns the model's label."""
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import _profile

    db = get_database()
    _profile(db, DEFAULT_PROFILE, model="qwen3.8-27b", boundary="private_network")
    InferenceAssignmentService(db).set_assignment(
        Principal(PrincipalKind.OWNER, "philo15-05-owner"),
        {
            "command_id": "philo15-05-default", "expected_revision": 0,
            "scope": {"kind": "global"},
            "entries": [{"profile_id": DEFAULT_PROFILE, "profile_revision": 1}],
        },
    )
    return DEFAULT_PROFILE.replace("-", " ").title()


def _page(pw: Any, url: str, width: int, errors: list[str]) -> Any:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852})
    page.emulate_media(reduced_motion="reduce")
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    # PHILO-16 (16b): one hub is one desk; this page starts on an empty desk.
    from .glass_infra import clear_hub_windows

    clear_hub_windows(page, TOKEN)
    page.reload(wait_until="load")
    _normal_chair(page)
    _settle(page)
    return page


@pytest.mark.e2e
@pytest.mark.timeout(240)
def test_the_lane_draft_chip_names_the_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.delivery.factory_launch as factory_launch
    import holdspeak.delivery.registry as delivery_registry
    from holdspeak.agent_context import event_log
    from holdspeak.services import agent_responder

    from .test_philo14_c2_lane_glass import _open_lane, _seed

    state = tmp_path / "home" / ".holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
    monkeypatch.setattr(delivery_registry, "DEFAULT_REGISTRY_PATH", state / "delivery_sources.json")
    monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
    monkeypatch.setattr(agent_responder, "DEFAULT_ANSWERS_PATH", state / "agent_answers.json")
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        _seed(tmp_path / "home")
        label = _assign_lan_default()
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            for width in (1440, 393):
                page = _page(pw, url, width, errors)
                roster = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
                [row] = [r for r in roster["task_overrides"] if r["id"] == agent_responder.CAPABILITY]
                assert row["has_override"] is False and row["effective"]["inherited_from"] == "global", row
                _open_lane(page)
                draft = page.locator("[data-testid='lane-ask'] .ask-well-draft")
                draft.wait_for(timeout=15_000)
                page.wait_for_function(
                    """(want) => (document.querySelector("[data-testid='lane-ask'] .ask-well-draft")?.textContent || "").includes(want)""",
                    arg=label.upper(), timeout=15_000,
                )
                text = draft.text_content() or ""
                assert "NOT SET" not in text, text
                draft.scroll_into_view_if_needed()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"lane-draft-chip-{width}.png"))
                _assert_clean(page, errors)
                page.context.browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.chair_windows_open
@pytest.mark.timeout(240)
def test_the_brief_generated_itself(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    from holdspeak.config import Config
    from holdspeak.runtime.cadence import CadenceMixin

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        # The cadence thread's tick, on the shipped defaults, at 06:00 today.
        class _Runtime(CadenceMixin):
            def __init__(self) -> None:
                self.config = Config()

        runtime = _Runtime()
        assert runtime._cadence_jobs_enabled() and not runtime._cadence_enabled()
        six = datetime.now().astimezone().replace(hour=6, minute=0, second=0, microsecond=0)
        with patch("holdspeak.runtime.cadence.local_now", return_value=six):
            runtime._cadence_tick_body()
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            for width in (1440, 393):
                page = _page(pw, url, width, errors)
                brief = _api(page, "GET", "/api/brief/latest", token=TOKEN)
                assert brief and brief.get("generated_at"), brief
                # Astra r1 P1: the scheduled Brief holds the work the owner's
                # Generate would (the fresh hub's engine blocker), never a
                # silent "No changes".
                waiting = [i["text"] for i in (brief.get("sections") or {}).get("waiting") or []]
                assert brief["headline"] != "No changes" and any(t.startswith("No engine") for t in waiting), brief
                assert not any(t.startswith("NOT READ") for t in waiting), waiting
                if width == 393:
                    page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')").click()
                date = page.locator("[data-testid='arrival-brief-date']").first
                date.wait_for(timeout=15_000)
                said = date.text_content() or ""
                assert "GENERATED" in said and "06:00" in said, said
                # Generate stays for a re-run.
                assert page.locator("[data-testid='arrival-brief-generate']").first.is_visible()
                date.scroll_into_view_if_needed()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"brief-generated-{width}.png"))
                _assert_clean(page, errors)
                page.context.browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.timeout(240)
def test_the_runs_on_anthropic_plate_reads_not_supported_yet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """PHILO-16 (C): ported from the Concierge row to the Runs on plate. A
    provider with no execution adapter reads NOT SUPPORTED YET, never READY,
    carries no verb, and a job refuses it."""
    _ensure_build()
    from .runs_on import open_runs_on, window

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from holdspeak.db import get_database

        db = get_database()
        db.profiles.upsert(
            profile_id="cloud-anthropic", name="Claude", kind="openAICompatible",
            base_url="https://api.anthropic.com/v1", model="claude-sonnet", requires_key=True,
        )
        db.profiles.upsert(
            profile_id="cloud-openrouter", name="OpenRouter Qwen", kind="openAICompatible",
            base_url="https://openrouter.ai/api/v1", model="qwen/qwen3", requires_key=True,
        )
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            for width in (1440, 393):
                page = _page(pw, url, width, errors)
                open_runs_on(page)
                row = page.get_by_test_id("switchboard-engine-cloud-anthropic")
                if width == 393:
                    # The phone list offers only what a job can take: the
                    # unsupported engine is no alternative anywhere.
                    assert page.get_by_test_id("switchboard-tap-cloud-anthropic").count() == 0
                else:
                    row.wait_for(timeout=15_000)
                    said = row.text_content() or ""
                    assert "NOT SUPPORTED YET" in said and "READY" not in said, said
                    assert row.locator("button").count() == 0, "an unsupported engine carries no verb"
                    assert page.get_by_test_id("switchboard-lamp-cloud-anthropic").get_attribute("data-lamp") == "broken"
                    page.get_by_test_id("switchboard-job-thoughts_notes").click()
                    row.focus()
                    page.keyboard.press("Enter")
                    page.wait_for_function(
                        "() => /REFUSED .* NOT SUPPORTED/.test(document.querySelector('[data-testid=runson-receipt]')?.textContent || '')"
                    )
                    row.scroll_into_view_if_needed()
                _settle(page)
                win = window(page)
                (win if win.count() else page).screenshot(path=str(SHOTS / f"runson-anthropic-{width}.png"))
                _assert_clean(page, errors)
                page.context.browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.chair_windows_open
@pytest.mark.timeout(240)
def test_a_brief_with_an_unread_source_says_partial(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Astra r1 P1: a source the producer could not read is a NOT READ row,
    and the receipt reads GENERATED · PARTIAL."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from holdspeak.db import get_database
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.monday_brief_service import MondayBriefService

        # A principal the needs-you rule cannot read for: the r1 defect's shape.
        MondayBriefService(get_database()).generate(Principal(PrincipalKind.SERVICE, "heartbeat"))
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            for width in (1440, 393):
                page = _page(pw, url, width, errors)
                if width == 393:
                    page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')").click()
                date = page.locator("[data-testid='arrival-brief-date']").first
                date.wait_for(timeout=15_000)
                said = date.text_content() or ""
                assert "GENERATED" in said and said.endswith("PARTIAL"), said
                body = page.locator("[data-testid='arrival-brief']").first.text_content() or ""
                assert "NOT READ · AI models" in body and "NOT READ · Decisions" in body, body
                date.scroll_into_view_if_needed()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"brief-partial-{width}.png"))
                _assert_clean(page, errors)
                page.context.browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.chair_windows_open
@pytest.mark.timeout(240)
@pytest.mark.xfail(
    reason="lane 09 (philo-15/09-morning-truth, B04): Generate returns today's stored "
    "Brief (monday_brief_service.py, the same-day return); lane 09 makes Generate regenerate.",
    strict=False,
)
def test_pressing_generate_regenerates_the_scheduled_brief(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Astra r1 MISSED: the 06:00 Brief must be refreshable. Pressing the
    Generate Button makes a new Brief (a new generated_at and a new receipt
    time on the face), not the stored 06:00 one. Un-xfail when lane 09 (#980)
    lands."""
    _ensure_build()
    from holdspeak.config import Config
    from holdspeak.runtime.cadence import CadenceMixin

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        class _Runtime(CadenceMixin):
            def __init__(self) -> None:
                self.config = Config()

        six = datetime.now().astimezone().replace(hour=6, minute=0, second=0, microsecond=0)
        with patch("holdspeak.runtime.cadence.local_now", return_value=six):
            _Runtime()._cadence_tick_body()
        from playwright.sync_api import sync_playwright

        errors: list[str] = []
        with sync_playwright() as pw:
            page = _page(pw, url, 1440, errors)
            before = _api(page, "GET", "/api/brief/latest", token=TOKEN)
            date = page.locator("[data-testid='arrival-brief-date']").first
            date.wait_for(timeout=15_000)
            shown_before = date.text_content() or ""
            assert "06:00" in shown_before, shown_before
            # The owner's press: the library Button in the Brief's head.
            with page.expect_response(lambda r: r.url.endswith("/api/brief/generate")) as answered:
                page.locator("[data-testid='arrival-brief-generate']").first.click()
            assert answered.value.status == 200, answered.value.text()
            after = _api(page, "GET", "/api/brief/latest", token=TOKEN)
            assert after["generated_at"] != before["generated_at"], (before["generated_at"], after["generated_at"])
            page.wait_for_function(
                "(old) => (document.querySelector(\"[data-testid='arrival-brief-date']\")?.textContent || '') !== old",
                arg=shown_before, timeout=15_000,
            )
            _assert_clean(page, errors)
            page.context.browser.close()
    finally:
        server.stop()

