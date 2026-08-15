"""HS-131-01 immutable deployment revision proof."""
from __future__ import annotations

from holdspeak.db import Database
from holdspeak.deployment_revisions import capture_deployment_revision, resolve_deployment_revision
from holdspeak.inference_targets import build_intel_for_revision, resolve_inference_target
from holdspeak.principals import UNAUTHENTICATED
from holdspeak.services.sync_service import SyncService


def _profile(db: Database) -> None:
    db.profiles.upsert(
        profile_id="lan", name="LAN", kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1", model="before", requires_key=True,
    )


def test_capture_survives_profile_mutation_and_deletion(tmp_path, monkeypatch) -> None:
    db = Database(tmp_path / "source.db")
    _profile(db)
    captured_target = resolve_inference_target(db, "lan")
    revision = capture_deployment_revision(db, captured_target)

    db.profiles.upsert(
        profile_id="lan", name="changed", kind="openAICompatible",
        base_url="https://changed.example/v1", model="after", requires_key=False,
    )
    db.profiles.delete("lan")

    resolved = resolve_deployment_revision(db, revision.id)
    assert resolved == revision
    assert resolved.endpoint == "http://192.168.1.43:8080/v1"
    assert resolved.model == "before"
    assert resolved.secret_slot.startswith("HOLDSPEAK_PROFILE_LAN_")

    class Engine:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", Engine)
    from tests.unit.admitted_context import admitted_context

    # HS-131-10: context-requiring factory. HS-131-13 deleted the legacy
    # `build_intel_for_target` companion assertion with the factory itself —
    # re-capturing the (now mutated, now deleted) target is the ONLY remaining way
    # to reach construction, and it still yields the frozen revision's endpoint.
    engine = build_intel_for_revision(
        resolved,
        context=admitted_context(revision=resolved),
    )
    assert engine.kwargs["cloud_base_url"] == revision.endpoint
    assert engine.kwargs["cloud_model"] == revision.model
    assert engine.kwargs["cloud_api_key_env"] == revision.secret_slot
    assert captured_target.deployment.endpoint == revision.endpoint


def test_deployment_revision_sync_round_trip_without_credential(tmp_path) -> None:
    source = Database(tmp_path / "source.db")
    destination = Database(tmp_path / "destination.db")
    _profile(source)
    revision = capture_deployment_revision(source, resolve_inference_target(source, "lan"))

    change_set = SyncService(source).pull(UNAUTHENTICATED)
    records = change_set["deployment_revisions"]
    assert records == [
        {"meta": {"id": revision.id, "kind": "deployment_revision", "last_modified": revision.id, "deleted": False}, "value": revision.to_dict()}
    ]
    assert "credential" not in str(records).lower()
    assert set(records[0]["value"]) == {
        "id", "destination_id", "kind", "engine", "model", "node", "boundary",
        "endpoint", "model_path", "secret_slot",
    }

    result = SyncService(destination).push(UNAUTHENTICATED, {"deployment_revisions": records})
    assert result["received"]["deployment_revisions"] == 1
    assert resolve_deployment_revision(destination, revision.id) == revision
