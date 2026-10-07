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
def test_the_concierge_anthropic_row_reads_not_supported_yet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    from .test_hs170_concierge_glass import _open_concierge, _window

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
                _open_concierge(page)
                page.get_by_test_id("concierge-root").wait_for(timeout=15_000)
                row = page.get_by_test_id("concierge-found-cloud:cloud-anthropic")
                row.wait_for(timeout=15_000)
                said = row.text_content() or ""
                assert "NOT SUPPORTED YET" in said and "READY" not in said, said
                assert page.get_by_test_id("concierge-check-cloud:cloud-anthropic").count() == 0
                row.scroll_into_view_if_needed()
                _settle(page)
                win = _window(page)
                (win if win.count() else page).screenshot(path=str(SHOTS / f"concierge-anthropic-{width}.png"))
                _assert_clean(page, errors)
                page.context.browser.close()
    finally:
        server.stop()
