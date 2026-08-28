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
