"""HS-201 follow-up: trust reports the assigned summary route."""

from __future__ import annotations

from datetime import datetime

import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.services.meeting_route_projection import project_route
from holdspeak.setup_status import _trust_block
from tests.unit.test_hs201_route_contract import OWNER, assign_summary
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim


def _meeting_db(tmp_path) -> Database:
    db = Database(tmp_path / "summary-egress.db")
    db.meetings.save_meeting(
        MeetingState(
            id="summary-egress-meeting",
            title="Summary egress",
            started_at=datetime.now(),
            segments=[TranscriptSegment("Ship the report.", "Me", 0.0, 1.0)],
        )
    )
    return db


def _cloud_profile(db: Database, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use the production Model Library producer with a stubbed probe leaf."""
    from holdspeak.services.inference_acquisition_service import (
        InferenceAcquisitionApplicationService,
    )
    from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
    from holdspeak.services.model_library_service import ModelLibraryApplicationService

    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    monkeypatch.setattr(
        "holdspeak.profile_key_store.resolve_profile_key",
        lambda *_args, **_kwargs: None,
    )
    setup = InferenceSetupApplicationService(
        db, config_provider=Config, home_provider=lambda: tmp_path / "home"
    )
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: tmp_path / "home"
    )
    ModelLibraryApplicationService(
        db, setup_service=setup, acquisition_service=acquisition
    ).define_endpoint(
        OWNER,
        {
            "request_id": "summary-cloud-define",
            "profile_id": "summary-cloud",
            "expected_profile_revision": 0,
            "label": "Summary Cloud",
            "provider_family": "openai_compatible",
            "model": "uat-never-invoked",
            "endpoint": "https://api.openai.com/v1",
            "requires_key": False,
        },
        None,
    )


def test_summary_display_enriches_project_route_without_changing_public_route(tmp_path, monkeypatch) -> None:
    from holdspeak.services.meeting_route_projection import summary_route_display

    db = _meeting_db(tmp_path)
    _profile(
        db,
        "summary-local",
        claims=("language", "structured_output", _result_claim("meeting.deferred_analysis")),
        modalities=("language", "text"),
    )
    _cloud_profile(db, tmp_path, monkeypatch)
    assign_summary(db, ["summary-local", "summary-cloud"])

    public = project_route(db, invocation_id="summary-egress")
    display = summary_route_display(db)

    assert public["legs"][0].keys() == {
        "ordinal", "host", "boundary", "profile_id", "profile_revision", "deployment_revision_id"
    }
    assert public["legs"][1]["host"] == "api.openai.com"
    assert display["selection_hash"] == public["selection_hash"]
    assert display["legs"][0]["profile_label"] == "Summary Local"
    assert display["legs"][1]["profile_label"] == "Summary Cloud"
    assert display["legs"][1]["node"] == ""
    assert set(display["legs"][1]) == set(public["legs"][1]) | {"profile_label", "node"}
    assert set(public["legs"][1]) == {
        "ordinal", "host", "boundary", "profile_id", "profile_revision", "deployment_revision_id"
    }


def test_trust_reports_assigned_summary_route_even_when_legacy_intel_is_off(tmp_path, monkeypatch) -> None:
    db = _meeting_db(tmp_path)
    _profile(
        db,
        "summary-local",
        claims=("language", "structured_output", _result_claim("meeting.deferred_analysis")),
        modalities=("language", "text"),
    )
    _cloud_profile(db, tmp_path, monkeypatch)
    assign_summary(db, ["summary-local", "summary-cloud"])

    config = Config()
    config.meeting.intel_enabled = False
    trust = _trust_block(config, database=db)
    meeting = next(row for row in trust["destinations"] if row["id"] == "meeting_intel")

    assert "api.openai.com" in trust["configured_endpoints"]
    assert trust["transcript_egress"] == "configured"
    assert meeting["enabled"] is True
    assert meeting["name"] == "Meeting summary"
    assert meeting["destination"] == "This device -> api.openai.com"
    assert meeting["authority_basis"] == "Assigned summary route"


def test_legacy_cloud_fields_without_assignment_do_not_claim_summary(tmp_path) -> None:
    from holdspeak.services.meeting_route_projection import summary_route_display

    db = _meeting_db(tmp_path)
    config = Config()
    config.meeting.intel_enabled = True
    config.meeting.intel_provider = "cloud"
    config.meeting.intel_cloud_base_url = "https://api.openai.com/v1"

    trust = _trust_block(config, database=db)
    meeting = next(row for row in trust["destinations"] if row["id"] == "meeting_intel")

    assert trust["transcript_egress"] == "none"
    assert "api.openai.com" not in trust["configured_endpoints"]
    assert meeting["enabled"] is False
    assert meeting["destination"] == "Summary route unavailable"
    assert meeting["name"] == "Meeting summary"
    assert meeting["boundary"] == "unavailable"
    assert summary_route_display(db)["status"] == "unavailable"
