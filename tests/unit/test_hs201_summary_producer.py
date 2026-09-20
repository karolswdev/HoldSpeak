"""HS-201-05 producer identity fences.

These tests keep the Concierge's detected profile reference tied to the
canonical Model Library producer.  A legacy endpoint row may still be shown,
but it does not carry an invented immutable revision into a summary gesture.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.concierge_service import apply, detect
from holdspeak.services.concierge_service import assign_summary
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.model_library_service import ModelLibraryApplicationService
from holdspeak.services.profile_service import ProfileService
from tests.unit.test_model_library_providers import OWNER, _draft, _library


def test_detect_carries_the_model_library_revision_from_the_producer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Connect and reconnect the same canonical profile, then detect it."""
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    library = _library(tmp_path, store_path=tmp_path / "profile-keys.json")
    assignments_before = library.assignment_heads(OWNER)
    first = library.define_endpoint(
        OWNER,
        _draft(
            request_id="producer-r1",
            profile_id="producer-main",
            provider_family="openai_compatible",
            requires_key=False,
        ),
        None,
    )
    second = library.define_endpoint(
        OWNER,
        {
            **_draft(
                request_id="producer-r2",
                profile_id="producer-main",
                provider_family="openai_compatible",
                label="Fixture v2",
                requires_key=False,
            ),
            "expected_profile_revision": 1,
        },
        None,
    )

    assert first["provider"]["profile_id"] == "producer-main"
    assert first["provider"]["profile_revision"] == 1
    assert second["provider"]["profile_id"] == "producer-main"
    assert second["provider"]["profile_revision"] == 2

    result = detect(db=library._db, home=tmp_path / "home")
    rows = [row for row in result["engines"] if row.get("profileId") == "producer-main"]
    assert len(rows) == 1
    assert rows[0]["profileId"] == second["provider"]["profile_id"]
    assert rows[0]["profileRevision"] == second["provider"]["profile_revision"]
    assert library.assignment_heads(OWNER) == assignments_before


def test_detect_does_not_invent_revision_for_a_legacy_endpoint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """A v1 endpoint has no immutable revision to pass to assignment CAS."""
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    db = Database(tmp_path / "legacy-endpoint.db")
    ProfileService(db).create_profile(
        Principal(PrincipalKind.OWNER, "legacy-producer-owner"),
        {
            "id": "legacy-endpoint",
            "name": "Legacy endpoint",
            "kind": "openAICompatible",
            "base_url": "http://127.0.0.1:9000/v1",
            "model": "fixture",
            "requires_key": False,
        },
    )

    result = detect(db=db, home=tmp_path / "home")
    row = next(row for row in result["engines"] if row.get("profileId") == "legacy-endpoint")
    assert row["profileId"] == "legacy-endpoint"
    assert "profileRevision" not in row


def test_old_v1_manifest_stays_incompatible_while_producer_mints_v2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """The baseline v1 manifest cannot route; a real reconnect mints v2."""
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    library = _library(tmp_path / "reconnect", store_path=tmp_path / "reconnect-keys.json")
    # Baseline setup uses the producer's prior language-only profile body. It
    # stands in for a persisted v1 row; no profile qualification is performed.
    current_body = ModelLibraryApplicationService._profile_body

    def old_profile_body(draft: dict[str, object]) -> dict[str, object]:
        body = current_body(draft)
        evidence = {"revision": "model-library-provider-v1", "claims": ["language"]}
        return {
            **body,
            "supported_modalities": ["language"],
            "capability_manifest": {
                **evidence,
                "sha256": "sha256:" + hashlib.sha256(
                    json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            },
        }

    monkeypatch.setattr(ModelLibraryApplicationService, "_profile_body", staticmethod(old_profile_body))
    first = library.define_endpoint(
        OWNER,
        _draft(
            request_id="reconnect-v1",
            profile_id="reconnect-producer",
            provider_family="openai_compatible",
            requires_key=False,
        ),
        None,
    )
    with library._db._connection() as conn:
        old_row = dict(conn.execute(
            "SELECT revision,sha256,capability_manifest_json FROM model_profile_revisions WHERE profile_id=? AND revision=1",
            ("reconnect-producer",),
        ).fetchone())
    monkeypatch.setattr(ModelLibraryApplicationService, "_profile_body", staticmethod(current_body))
    old = assign_summary(
        assignment_service=InferenceAssignmentService(library._db),
        principal=OWNER,
        db=library._db,
        profile_id=first["provider"]["profile_id"],
        profile_revision=first["provider"]["profile_revision"],
        expected_assignment_revision=0,
        command_id="old-v1-summary",
    )
    assert old["status"] == "partial"
    assert old["result"]["code"] == "inference_assignment_incompatible"

    second = library.define_endpoint(
        OWNER,
        {
            **_draft(
                request_id="reconnect-v2",
                profile_id="reconnect-producer",
                provider_family="openai_compatible",
                requires_key=False,
            ),
            "expected_profile_revision": 1,
            "label": "Reconnected v2",
        },
        None,
    )
    assert second["provider"]["profile_revision"] == 2
    with library._db._connection() as conn:
        new_row = dict(conn.execute(
            "SELECT revision,sha256,capability_manifest_json FROM model_profile_revisions WHERE profile_id=? AND revision=1",
            ("reconnect-producer",),
        ).fetchone())
    assert new_row == old_row
    profile = library._profiles.get_profile(OWNER, second["provider"]["profile_id"])
    assert profile["capability_manifest"]["revision"] == "model-library-meeting-adapter-v2"
    assert any(
        claim.startswith("result_schema:")
        for claim in profile["capability_manifest"]["claims"]
    )
    fresh = assign_summary(
        assignment_service=InferenceAssignmentService(library._db),
        principal=OWNER,
        db=library._db,
        profile_id=second["provider"]["profile_id"],
        profile_revision=second["provider"]["profile_revision"],
        expected_assignment_revision=0,
        command_id="new-v2-summary",
    )
    assert fresh["status"] == "succeeded"


def test_manifest_result_schema_claim_excludes_unexecuted_provider_families(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Anthropic, paired, and future families retain language-only claims."""
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    # These families are deliberately checked at the producer mint seam only:
    # existing provider tests cover their readiness/binding refusals, while
    # this fence proves no unsupported family receives the Meeting claim.
    for family in ("anthropic", "future_backend", "paired_device"):
        body = ModelLibraryApplicationService._profile_body(
            {
                "profile_id": f"excluded-{family}",
                "expected_profile_revision": 0,
                "label": "Excluded family",
                "provider_family": family,
                "model": "fixture",
            }
        )
        assert body["supported_modalities"] == ["language"]
        manifest = body["capability_manifest"]
        assert not any(
            str(claim).startswith("result_schema:")
            for claim in manifest["claims"]
        )


def test_summary_apply_refuses_a_profile_without_an_immutable_revision(
    tmp_path: Path,
) -> None:
    """The Meetings gesture must not turn a v1 endpoint into ``@1``."""
    db = Database(tmp_path / "legacy-summary.db")
    db.profiles.upsert(
        profile_id="legacy-endpoint",
        name="Legacy endpoint",
        kind="openAICompatible",
        base_url="http://127.0.0.1:9000/v1",
        model="fixture",
        requires_key=False,
    )

    result = apply(
        rows=[{"group": "meetings", "engineId": "lan:legacy", "state": "READY"}],
        engines=[
            {
                "id": "lan:legacy",
                "kind": "lan",
                "profileId": "legacy-endpoint",
                "state": "READY",
            }
        ],
        assignment_service=InferenceAssignmentService(db),
        principal=OWNER,
        db=db,
    )

    assert result["results"] == [
        {
            "group": "meetings",
            "capabilityId": "meeting.deferred_analysis",
            "state": "FAILED",
            "code": "concierge_summary_profile_revision_missing",
            "plainReason": "This engine has no immutable model profile revision.",
        }
    ]
