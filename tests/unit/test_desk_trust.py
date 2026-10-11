"""The Trust app (test diet, 2026-10-11): a cloud summary route, as the hub states it.

The real hub app (``MeetingWebServer``) over an isolated HOME, config and DB,
driven through ``TestClient``: the production Model Library defines a cloud
endpoint (its model discovery is the one stand-in, so nothing reaches
api.openai.com), the Concierge's summary selection assigns it, and the hub's
own reads (the meeting's planned route, ``/api/setup/status`` trust) name it.
The Trust window and the egress badge drawn from this answer are fenced in
``web/src/desk/__tests__/trust.app.test.tsx``.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

SUMMARY_HOST = "api.openai.com"


def _executions(db: Any) -> int:
    with db._connection() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM inference_route_executions").fetchone()[0])


def _library(db: Any, tmp_path: Path) -> Any:
    """The production ModelLibrary service over the hub's DB (the browser walk's seed)."""
    from holdspeak.config import Config
    from holdspeak.profile_key_store import ProfileKeyStore
    from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
    from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
    from holdspeak.services.model_library_service import ModelLibraryApplicationService
    from holdspeak.services.profile_key_service import ProfileKeyService

    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: tmp_path / "home")
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: tmp_path / "home")
    keys = ProfileKeyService(db, store=ProfileKeyStore(tmp_path / "summary-profile-keys.json"))
    return ModelLibraryApplicationService(
        db, setup_service=setup, acquisition_service=acquisition, profile_key_service=keys)


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import holdspeak.config as config_module
    from holdspeak.db import reset_database

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_a_selected_cloud_summary_route_is_named_in_trust(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """replaces: tests/e2e/test_hs201_summary_trust_glass.py::test_summary_cloud_route_is_visible_in_trust_glass (the hub half)"""
    discovery: list[str] = []
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models",
                        lambda base_url, **_k: discovery.append(base_url) or {"ok": True, "models": ["fixture-summary"]})
    monkeypatch.setattr("holdspeak.profile_key_store.resolve_profile_key", lambda *_a, **_k: None)

    from holdspeak.config import Config
    from holdspeak.meeting_session import MeetingState, TranscriptSegment
    from holdspeak.principals import Principal, PrincipalKind
    from tests.unit.test_model_library_providers import _draft

    db = hub.db
    cfg = Config.load()
    cfg.meeting.intel_enabled = False
    cfg.meeting.intelligence_auto = "off"
    cfg.meeting.allow_actuators = False
    cfg.save()
    meeting = MeetingState(
        id="hs201-summary-trust-fixture", title="Summary trust fixture",
        started_at=datetime.now() - timedelta(minutes=1), ended_at=datetime.now(),
        capture_status="finalized", transcription_status="final",
        segments=[TranscriptSegment("We agreed to send the budget report.", "Me", 0.0, 2.0)],
    )
    db.meetings.save_meeting(meeting)
    profile = _library(db, tmp_path).define_endpoint(
        Principal(PrincipalKind.OWNER, "desk-trust-owner"),
        _draft(request_id="desk-trust-provider", profile_id="desk-trust-cloud",
               provider_family="openai_compatible", label="Summary cloud fixture",
               model="fixture-summary", requires_key=False, endpoint="https://api.openai.com/v1"),
        None,
    )["provider"]
    assert discovery == ["https://api.openai.com/v1"]
    assert _executions(db) == 0

    selected = hub.client.post("/api/concierge/summary-selection", json={
        "commandId": "desk-trust-selection", "expectedAssignmentRevision": 0,
        "profileId": profile["profile_id"], "profileRevision": profile["profile_revision"],
    })
    assert selected.status_code == 200, selected.text
    assert selected.json()["status"] == "succeeded", selected.json()
    assert selected.json()["summaryAssignment"]["capabilityId"] == "meeting.deferred_analysis"

    detail = hub.client.get(f"/api/meetings/{meeting.id}")
    assert detail.status_code == 200, detail.text
    leg = detail.json()["planned_route"]["legs"][0]
    assert detail.json()["planned_route"]["status"] == "ready"
    assert (leg["host"], leg["boundary"]) == (SUMMARY_HOST, "cloud")
    assert (leg["profile_id"], leg["profile_revision"]) == (profile["profile_id"], profile["profile_revision"])

    status = hub.client.get("/api/setup/status")
    assert status.status_code == 200, status.text
    trust = status.json()["trust"]
    assert trust["actuators_enabled"] is False
    assert trust["transcript_egress"] in {"configured", "possible"}
    assert SUMMARY_HOST in trust["configured_endpoints"]
    cloud = next(row for row in trust["destinations"]
                 if row.get("enabled") and SUMMARY_HOST in str(row.get("destination", "")))
    assert cloud["id"] == "meeting_intel"
    assert cloud["boundary"] == "cloud"
    assert "summary" in cloud["operation"].lower()
    assert "explicit summary request" in cloud["background_ability"]

    with db._connection() as conn:
        live = conn.execute("SELECT COUNT(*) FROM inference_assignment_heads WHERE assignment_key=?",
                            ("capability:meeting.live_analysis",)).fetchone()[0]
    assert int(live) == 0
    # Naming the route ran nothing.
    assert _executions(db) == 0
