"""HS-201 follow-up: a selected cloud summary route is visible in Trust."""
from __future__ import annotations

import re
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
    REPO,
)


pytestmark = [pytest.mark.e2e, pytest.mark.requires_meeting]

TOKEN = "hs201-summary-trust-followup2"
SHOTS = REPO / "pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a-followup2"
SUMMARY_HOST = "api.openai.com"


def _execution_count(db: Any) -> int:
    with db._connection() as conn:
        return int(
            conn.execute("SELECT COUNT(*) FROM inference_route_executions").fetchone()[0]
        )


def _library_for_db(db: Any, tmp_path: Path) -> Any:
    """Compose the production ModelLibrary service over the hub's DB."""
    from holdspeak.config import Config
    from holdspeak.profile_key_store import ProfileKeyStore
    from holdspeak.services.inference_acquisition_service import (
        InferenceAcquisitionApplicationService,
    )
    from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
    from holdspeak.services.model_library_service import ModelLibraryApplicationService
    from holdspeak.services.profile_key_service import ProfileKeyService

    setup = InferenceSetupApplicationService(
        db,
        config_provider=Config,
        home_provider=lambda: tmp_path / "home",
    )
    acquisition = InferenceAcquisitionApplicationService(
        db,
        setup_service=setup,
        model_root=tmp_path / "custody",
        home_provider=lambda: tmp_path / "home",
    )
    keys = ProfileKeyService(
        db,
        store=ProfileKeyStore(tmp_path / "summary-profile-keys.json"),
    )
    return ModelLibraryApplicationService(
        db,
        setup_service=setup,
        acquisition_service=acquisition,
        profile_key_service=keys,
    )


def _assert_badge_names_host(page: Any, host: str) -> str:
    """Check badge data; the narrow badge clips text, so Trust proves visibility."""
    badge = page.locator(".egress-badge-button")
    badge.wait_for(state="visible", timeout=15_000)
    label = badge.get_attribute("aria-label") or ""
    assert host in label, f"global trust badge does not name {host}: {label!r}"
    badge_text = badge.inner_text()
    assert host.casefold() in badge_text.casefold(), (
        f"global trust badge text does not show {host}: {badge_text!r}"
    )
    box = badge.bounding_box()
    assert box is not None and box["x"] >= 0 and box["x"] + box["width"] <= page.viewport_size["width"]
    return label


def test_summary_cloud_route_is_visible_in_trust_glass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact deferred-summary assignment names its cloud route on both glasses."""
    _ensure_build()

    discovery_calls: list[str] = []

    def no_network_discovery(base_url: str, **_kwargs: Any) -> dict[str, Any]:
        discovery_calls.append(base_url)
        return {"ok": True, "models": ["fixture-summary"]}

    # ModelLibrary readiness uses the real producer API. Only its endpoint
    # discovery seam is replaced, so this test never contacts api.openai.com.
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        no_network_discovery,
    )

    from holdspeak.config import Config
    from holdspeak.db import get_database
    from holdspeak.meeting_session import MeetingState, TranscriptSegment
    monkeypatch.setattr("holdspeak.profile_key_store.resolve_profile_key", lambda *_args, **_kwargs: None)
    from holdspeak.principals import Principal, PrincipalKind
    from tests.unit.test_model_library_providers import _draft

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    db = get_database()
    cfg = Config.load()
    cfg.meeting.intel_enabled = False
    cfg.meeting.intelligence_auto = "off"
    cfg.meeting.allow_actuators = False
    cfg.save()

    meeting = MeetingState(
        id="hs201-summary-trust-fixture",
        title="Summary trust fixture",
        started_at=datetime.now() - timedelta(minutes=1),
        ended_at=datetime.now(),
        capture_status="finalized",
        transcription_status="final",
        segments=[TranscriptSegment("We agreed to send the budget report.", "Me", 0.0, 2.0)],
    )
    db.meetings.save_meeting(meeting)

    owner = Principal(PrincipalKind.OWNER, "hs201-summary-trust-owner")
    library = _library_for_db(db, tmp_path)
    provider = library.define_endpoint(
        owner,
        _draft(
            request_id="hs201-summary-trust-provider",
            profile_id="hs201-summary-cloud",
            provider_family="openai_compatible",
            label="Summary cloud fixture",
            model="fixture-summary",
            requires_key=False,
            endpoint="https://api.openai.com/v1",
        ),
        None,
    )
    profile = provider["provider"]
    assert profile["profile_revision"] == 1
    assert discovery_calls == ["https://api.openai.com/v1"]
    before_executions = _execution_count(db)
    assert before_executions == 0

    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(
                page,
                "PUT",
                "/api/setup/onboarding",
                {"disposition": "completed"},
                token=TOKEN,
            )

            selected = _api(
                page,
                "POST",
                "/api/concierge/summary-selection",
                {
                    "commandId": "hs201-summary-trust-selection",
                    "expectedAssignmentRevision": 0,
                    "profileId": profile["profile_id"],
                    "profileRevision": profile["profile_revision"],
                },
                token=TOKEN,
            )
            assert selected["status"] == "succeeded", selected
            assert selected["summaryAssignment"]["capabilityId"] == "meeting.deferred_analysis"

            detail = _api(page, "GET", f"/api/meetings/{meeting.id}", token=TOKEN)
            planned = detail["planned_route"]
            assert planned["status"] == "ready", planned
            assert planned["legs"]
            assert planned["legs"][0]["host"] == SUMMARY_HOST
            assert planned["legs"][0]["boundary"] == "cloud"
            assert planned["legs"][0]["profile_id"] == profile["profile_id"]
            assert planned["legs"][0]["profile_revision"] == profile["profile_revision"]

            status = _api(page, "GET", "/api/setup/status", token=TOKEN)
            trust = status["trust"]
            assert trust["actuators_enabled"] is False
            assert trust["transcript_egress"] in {"configured", "possible"}
            assert any(
                marker in trust["egress_detail"]
                for marker in ("Live analysis is off for Record", "assigned route")
            )
            destinations = trust["destinations"]
            cloud = next(
                (
                    row
                    for row in destinations
                    if row.get("enabled") and SUMMARY_HOST in str(row.get("destination", ""))
                ),
                None,
            )
            assert cloud is not None, destinations
            assert cloud["boundary"] == "cloud"
            assert "summary" in str(cloud["operation"]).lower()
            assert cloud["id"] == "meeting_intel"
            assert "explicit summary request" in cloud["background_ability"]

            with db._connection() as conn:
                live_rows = conn.execute(
                    "SELECT COUNT(*) FROM inference_assignment_heads "
                    "WHERE assignment_key=?",
                    ("capability:meeting.live_analysis",),
                ).fetchone()[0]
            assert int(live_rows) == 0
            assert _execution_count(db) == before_executions == 0

            for width in (1440, 393):
                page.set_viewport_size(
                    {"width": width, "height": 900 if width == 1440 else 852}
                )
                page.reload(wait_until="load")
                _normal_chair(page)
                _settle(page)
                _assert_badge_names_host(page, SUMMARY_HOST)
                page.get_by_role(
                    "button", name=re.compile(r"Privacy and trust", re.IGNORECASE)
                ).click()
                trust_window = page.locator(".desk-trust-window")
                trust_window.wait_for(state="visible", timeout=15_000)
                _settle(page)
                host_text = trust_window.get_by_text(
                    re.compile(r"api\.openai\.com", re.IGNORECASE)
                )
                host_text.wait_for(state="visible", timeout=15_000)
                assert host_text.is_visible()
                host_box = host_text.bounding_box()
                viewport = page.viewport_size
                assert host_box is not None
                assert host_box["x"] >= 0 and host_box["y"] >= 0
                assert host_box["x"] + host_box["width"] <= viewport["width"]
                assert host_box["y"] + host_box["height"] <= viewport["height"]
                assert trust_window.get_by_text(
                    re.compile(r"this device \+ external", re.IGNORECASE)
                ).is_visible()
                _assert_clean(page, errors)
                assert _execution_count(db) == before_executions == 0
                shot = SHOTS / f"summary-trust-{width}.png"
                SHOTS.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(shot), full_page=False)
                assert shot.stat().st_size > 2_000, shot
                print(f"SHOT {shot}")

            assert discovery_calls == ["https://api.openai.com/v1"]
            browser.close()
    finally:
        print(f"DISCOVERY_CALLS {discovery_calls!r}")
        print(f"ROUTE_EXECUTIONS {_execution_count(db)}")
        print(f"PAGE_ERRORS {errors!r}")
        server.stop()
