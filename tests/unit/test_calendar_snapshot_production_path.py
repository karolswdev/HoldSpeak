"""Production-path proof for the Calendar Snapshot adapter (HS-146-07).

Template: test_one_path_spine.py:208-227 (the Ask driver's engine-factory
injection idiom). Fakes at the ENGINE-FACTORY level (NOT the route seam)
and proves a real dispatch travels admission -> runner -> vision adapter
-> extraction JSON -> parsed events.

Also proves the no-assignment case returns a named config refusal (not
an image-quality claim).
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import threading
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "test-owner")


def _configure(db: Any) -> Any:
    """Get a real broker from the kernel runtime, wired to the test database."""
    from holdspeak.kernel.runtime import _configure

    return _configure(db)


def _setup_profile(db: Database, profile_id: str = "prof_vision") -> str:
    """Create a profile for the direct-dispatch path.

    Template: test_one_path_spine.py:211-215 — the ask driver creates a profile
    and patches the engine factory. The direct dispatch path uses this profile
    through the broker's inference runner, exactly like the ask spine test.
    """
    db.profiles.upsert(
        profile_id=profile_id,
        name="Vision Test",
        kind="openAICompatible",
        base_url="http://192.168.1.50:8080",
        model="vision-model",
        requires_key=False,
        context_limit=16384,
    )
    return profile_id


DETERMINISTIC_EXTRACTION = json.dumps({
    "anchor_date": "2026-08-31",
    "anchor_confidence": "visible_header",
    "events": [
        {
            "title": "Morning Standup",
            "weekday": "monday",
            "start_time": "09:00",
            "end_time": "09:30",
            "location": "Room 1",
        },
        {
            "title": "Afternoon Review",
            "weekday": "friday",
            "start_time": "14:00",
            "end_time": "15:00",
            "location": None,
        },
    ],
})


class TestProductionPathDispatch:
    """Prove the production dispatch: admission -> runner -> vision adapter -> extraction."""

    def test_extract_via_router_dispatches_through_inference_machinery(
        self, tmp_path, monkeypatch,
    ):
        """Engine-factory-level fake: a real broker dispatch travels
        admission -> runner -> VisionPromptAdapter -> extraction JSON.
        """
        db = Database(tmp_path / "snapshot.db")
        profile_id = _setup_profile(db)
        broker = _configure(db)

        # Create a deployment revision so the runner can construct the engine.
        # This is what capture_deployment_revision does in the ask legacy path.
        from holdspeak.deployment_revisions import capture_deployment_revision
        from holdspeak.inference_targets import target_from_profile
        profile = db.profiles.get(profile_id)
        target = target_from_profile(profile, db)
        dep_rev = capture_deployment_revision(db, target)

        # Track what the vision adapter dispatched to the engine
        dispatched_payloads: list[dict[str, Any]] = []

        class FakeVisionEngine:
            active_provider = "openai_compatible"
            active_model = "vision-model"

            def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
                return DETERMINISTIC_EXTRACTION

            def run_prompt_messages(self, *, messages):
                dispatched_payloads.append({"messages": messages})
                # Verify multi-part content arrived
                user_msg = next(
                    (m for m in messages if m["role"] == "user"), None
                )
                assert user_msg is not None, "No user message in vision dispatch"
                content = user_msg["content"]
                assert isinstance(content, list), "User content should be multi-part array"
                has_text = any(
                    p.get("type") == "text" for p in content
                )
                has_image = any(
                    p.get("type") == "image_url" for p in content
                )
                assert has_text, "Multi-part content missing text part"
                assert has_image, "Multi-part content missing image part"
                return DETERMINISTIC_EXTRACTION

        monkeypatch.setattr(
            broker.inference_runner,
            "_engine_factory",
            lambda revision, **_: FakeVisionEngine(),
        )

        # Patch the module-level broker and database resolution
        monkeypatch.setattr(
            "holdspeak.services.calendar_snapshot_service._service",
            lambda: broker,
        )
        monkeypatch.setattr(
            "holdspeak.db.get_database",
            lambda: db,
        )

        from holdspeak.services.calendar_snapshot_service import (
            EXTRACTION_SYSTEM_PROMPT,
            EXTRACTION_USER_PROMPT,
            extract_via_router,
            parse_extraction_json,
        )

        payload = {
            "system_prompt": EXTRACTION_SYSTEM_PROMPT,
            "user_prompt": EXTRACTION_USER_PROMPT,
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
            "image_media_type": "image/png",
        }

        result = extract_via_router(OWNER, payload)

        # Verify the dispatch actually happened through the engine
        assert len(dispatched_payloads) > 0, (
            "VisionPromptAdapter never reached the engine — "
            "the dispatch did not travel the production path"
        )

        # Verify the output parses correctly
        assert "output" in result
        parsed = parse_extraction_json(result["output"])
        assert parsed.error is None, f"Extraction should succeed, got error: {parsed.error}"
        assert len(parsed.events) == 2
        assert parsed.events[0].title == "Morning Standup"
        assert parsed.anchor_date == "2026-08-31"

        # Verify egress truth was resolved from the assignment
        assert "egress" in result
        egress = result["egress"]
        assert egress is not None
        assert "scope" in egress

    def test_no_assignment_returns_named_config_refusal(
        self, tmp_path, monkeypatch,
    ):
        """No profile with vision claims -> named config refusal, NOT
        an image-quality claim like 'unreadable_screenshot'."""
        db = Database(tmp_path / "no-vision.db")
        # Create a profile WITHOUT vision claims
        db.profiles.upsert(
            profile_id="prof_text_only",
            name="Text Only",
            kind="openAICompatible",
            base_url="http://192.168.1.50:8080",
            model="text-model",
            requires_key=False,
        )
        broker = _configure(db)

        monkeypatch.setattr(
            "holdspeak.services.calendar_snapshot_service._service",
            lambda: broker,
        )

        from holdspeak.services.calendar_snapshot_service import (
            EXTRACTION_SYSTEM_PROMPT,
            EXTRACTION_USER_PROMPT,
            extract_via_router,
            parse_extraction_json,
        )

        payload = {
            "system_prompt": EXTRACTION_SYSTEM_PROMPT,
            "user_prompt": EXTRACTION_USER_PROMPT,
            "image_base64": "AAAA",
            "image_media_type": "image/png",
        }

        result = extract_via_router(OWNER, payload)

        # Should return a CONFIG refusal, never an image-quality claim
        parsed = parse_extraction_json(result["output"])
        assert parsed.error is not None, "Should have an error when no vision model assigned"
        assert parsed.error != "unreadable_screenshot", (
            "Config gap MUST NOT be laundered as an image-quality claim; "
            f"got {parsed.error!r}"
        )
        assert "no_vision_model" in parsed.error or "unavailable" in parsed.error or "no_route" in parsed.error or "failed" in parsed.error, (
            f"Expected a named config/assignment refusal, got {parsed.error!r}"
        )


class TestVisionPreFilter:
    """HS-147-05: pre-filter the direct-dispatch fallback to vision-capable
    profiles.  When none qualify the named refusal fires with ZERO dispatches."""

    def test_ondevice_only_profiles_refused_with_zero_dispatches(
        self, tmp_path, monkeypatch,
    ):
        """Only onDevice profiles exist and none have v2 vision claims.
        The refusal must fire before any inference dispatch."""
        db = Database(tmp_path / "no-vision-prefilter.db")
        # Create a local on-device profile (GGUF language model, no vision)
        db.profiles.upsert(
            profile_id="prof_local",
            name="Local Q6",
            kind="onDevice",
            model_file=str(tmp_path / "fake-model.gguf"),
            model="fake-q6",
            requires_key=False,
            context_limit=16384,
        )
        # Make the model file exist so the profile is "ready"
        (tmp_path / "fake-model.gguf").write_bytes(b"GGUF")

        broker = _configure(db)

        dispatch_count = 0
        original_invoke = broker.inference_runner.invoke

        def counting_invoke(*args, **kwargs):
            nonlocal dispatch_count
            dispatch_count += 1
            return original_invoke(*args, **kwargs)

        monkeypatch.setattr(broker.inference_runner, "invoke", counting_invoke)
        monkeypatch.setattr(
            "holdspeak.services.calendar_snapshot_service._service",
            lambda: broker,
        )
        monkeypatch.setattr("holdspeak.db.get_database", lambda: db)

        from holdspeak.services.calendar_snapshot_service import (
            EXTRACTION_SYSTEM_PROMPT,
            EXTRACTION_USER_PROMPT,
            extract_via_router,
            parse_extraction_json,
        )

        payload = {
            "system_prompt": EXTRACTION_SYSTEM_PROMPT,
            "user_prompt": EXTRACTION_USER_PROMPT,
            "image_base64": "AAAA",
            "image_media_type": "image/png",
        }

        result = extract_via_router(OWNER, payload)

        parsed = parse_extraction_json(result["output"])
        assert parsed.error == "no_vision_model_assigned", (
            f"Expected no_vision_model_assigned, got {parsed.error!r}"
        )
        assert dispatch_count == 0, (
            f"Pre-filter should prevent all dispatches; got {dispatch_count}"
        )

    def test_openai_compatible_profile_passes_prefilter(
        self, tmp_path, monkeypatch,
    ):
        """An openAICompatible profile (no v2 binding) passes the vision
        pre-filter — the dispatch reaches the engine."""
        db = Database(tmp_path / "vision-compat.db")
        profile_id = _setup_profile(db, profile_id="prof_cloud_vision")
        broker = _configure(db)

        from holdspeak.deployment_revisions import capture_deployment_revision
        from holdspeak.inference_targets import target_from_profile

        profile = db.profiles.get(profile_id)
        target = target_from_profile(profile, db)
        capture_deployment_revision(db, target)

        dispatch_count = 0

        class FakeVisionEngine:
            active_provider = "openai_compatible"
            active_model = "vision-model"

            def run_prompt_messages(self, *, messages, **_):
                return DETERMINISTIC_EXTRACTION

        monkeypatch.setattr(
            broker.inference_runner,
            "_engine_factory",
            lambda revision, **_: FakeVisionEngine(),
        )
        original_invoke = broker.inference_runner.invoke

        def counting_invoke(*args, **kwargs):
            nonlocal dispatch_count
            dispatch_count += 1
            return original_invoke(*args, **kwargs)

        monkeypatch.setattr(broker.inference_runner, "invoke", counting_invoke)
        monkeypatch.setattr(
            "holdspeak.services.calendar_snapshot_service._service",
            lambda: broker,
        )
        monkeypatch.setattr("holdspeak.db.get_database", lambda: db)

        from holdspeak.services.calendar_snapshot_service import (
            EXTRACTION_SYSTEM_PROMPT,
            EXTRACTION_USER_PROMPT,
            extract_via_router,
            parse_extraction_json,
        )

        payload = {
            "system_prompt": EXTRACTION_SYSTEM_PROMPT,
            "user_prompt": EXTRACTION_USER_PROMPT,
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
            "image_media_type": "image/png",
        }

        result = extract_via_router(OWNER, payload)

        assert dispatch_count > 0, (
            "openAICompatible profile should pass the vision pre-filter "
            "and dispatch at least once"
        )
        parsed = parse_extraction_json(result["output"])
        assert parsed.error is None, f"Happy path should succeed, got {parsed.error!r}"

    def test_vision_capable_helper_with_v2_claims(self, tmp_path):
        """A profile with a v2 model-profile revision claiming 'vision'
        passes _vision_capable regardless of legacy kind."""
        db = Database(tmp_path / "v2-vision.db")
        db.profiles.upsert(
            profile_id="prof_with_v2",
            name="V2 Vision",
            kind="onDevice",
            model_file=str(tmp_path / "model.gguf"),
            model="llava-v1.6",
            requires_key=False,
        )
        # Insert a v2 model profile revision WITH vision in claims
        import json as _json
        manifest = {"revision": "test-v2", "claims": ["vision", "language"]}
        manifest["sha256"] = "test-sha"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO model_profile_revisions
                   (profile_id, revision, sha256, label, provider_family,
                    runtime_family, model_or_artifact_identity,
                    supported_modalities_json, context_support,
                    tokenizer_template_requirements_json,
                    capability_manifest_json, safe_presentation_json,
                    created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("prof_with_v2", 1, "sha-test", "V2 Vision", "local",
                 "llama_cpp", "llava-v1.6",
                 _json.dumps(["language", "vision"]), "bounded",
                 _json.dumps({}), _json.dumps(manifest), _json.dumps({}),
                 "2026-08-28T00:00:00Z"),
            )

        from holdspeak.services.calendar_snapshot_service import _vision_capable

        profile = db.profiles.get("prof_with_v2")
        assert _vision_capable(profile, db) is True

    def test_vision_capable_helper_rejects_ondevice_without_claims(self, tmp_path):
        """An onDevice profile with no v2 binding is NOT vision-capable."""
        db = Database(tmp_path / "no-v2.db")
        db.profiles.upsert(
            profile_id="prof_local_only",
            name="Local Only",
            kind="onDevice",
            model_file=str(tmp_path / "model.gguf"),
            model="qwen3-q6",
            requires_key=False,
        )

        from holdspeak.services.calendar_snapshot_service import _vision_capable

        profile = db.profiles.get("prof_local_only")
        assert _vision_capable(profile, db) is False
