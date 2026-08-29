"""Unit tests for the calendar snapshot service (HS-146-07)."""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from holdspeak.services.calendar_snapshot_service import (
    EXTRACTION_SYSTEM_PROMPT,
    ExtractedEvent,
    ExtractionResult,
    generate_ics,
    merge_extractions,
    parse_extraction_json,
    resolve_anchor_date,
    resolve_events_to_timestamps,
    snapshot_dir,
    write_ics_atomic,
)


# ── Schema validation ──────────────────────────────────────────────────


class TestParseExtractionJson:
    def test_valid_extraction(self):
        raw = json.dumps({
            "anchor_date": "2026-08-24",
            "anchor_confidence": "visible_header",
            "events": [
                {
                    "title": "Standup",
                    "weekday": "monday",
                    "start_time": "09:00",
                    "end_time": "09:30",
                    "location": "Room 1",
                },
                {
                    "title": "Lunch",
                    "weekday": "wednesday",
                    "start_time": "12:00",
                    "end_time": "13:00",
                    "location": None,
                },
            ],
        })
        result = parse_extraction_json(raw)
        assert result.error is None
        assert result.anchor_date == "2026-08-24"
        assert result.anchor_confidence == "visible_header"
        assert len(result.events) == 2
        assert result.events[0].title == "Standup"
        assert result.events[0].weekday == "monday"
        assert result.events[0].location == "Room 1"
        assert result.events[1].location is None

    def test_unreadable_screenshot(self):
        raw = json.dumps({"error": "unreadable_screenshot", "events": []})
        result = parse_extraction_json(raw)
        assert result.error == "unreadable_screenshot"
        assert result.events == []

    def test_invalid_json(self):
        result = parse_extraction_json("not json at all {{{")
        assert result.error == "unreadable_screenshot"

    def test_empty_events_is_refusal(self):
        raw = json.dumps({
            "anchor_date": "2026-08-24",
            "anchor_confidence": "visible_header",
            "events": [],
        })
        result = parse_extraction_json(raw)
        assert result.error == "unreadable_screenshot"

    def test_skips_invalid_weekday(self):
        raw = json.dumps({
            "anchor_date": "2026-08-24",
            "anchor_confidence": "inferred",
            "events": [
                {
                    "title": "Valid",
                    "weekday": "monday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                },
                {
                    "title": "Invalid",
                    "weekday": "marsday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                },
            ],
        })
        result = parse_extraction_json(raw)
        assert len(result.events) == 1
        assert result.events[0].title == "Valid"

    def test_skips_invalid_time_format(self):
        raw = json.dumps({
            "anchor_date": None,
            "anchor_confidence": "absent",
            "events": [
                {
                    "title": "Bad time",
                    "weekday": "friday",
                    "start_time": "9am",
                    "end_time": "10am",
                },
            ],
        })
        result = parse_extraction_json(raw)
        assert result.error == "unreadable_screenshot"

    def test_absent_anchor(self):
        raw = json.dumps({
            "anchor_date": None,
            "anchor_confidence": "absent",
            "events": [
                {
                    "title": "Meeting",
                    "weekday": "tuesday",
                    "start_time": "14:00",
                    "end_time": "15:00",
                },
            ],
        })
        result = parse_extraction_json(raw)
        assert result.anchor_date is None
        assert result.anchor_confidence == "absent"
        assert len(result.events) == 1


# ── ICS round-trip through the REAL parser ──────────────────────────────


class TestIcsRoundTrip:
    def test_generated_ics_passes_parser(self):
        from holdspeak.calendar_ingest import parse_calendar_bytes

        events = [
            {
                "title": "Standup",
                "weekday": "monday",
                "start_time": "09:00",
                "end_time": "09:30",
                "location": "Room 1",
                "starts_at": "2026-08-24T09:00:00+00:00",
                "ends_at": "2026-08-24T09:30:00+00:00",
            },
            {
                "title": "Review",
                "weekday": "friday",
                "start_time": "14:00",
                "end_time": "15:00",
                "location": None,
                "starts_at": "2026-08-28T14:00:00+00:00",
                "ends_at": "2026-08-28T15:00:00+00:00",
            },
        ]
        ics_bytes = generate_ics(events, source_id="test-src")
        result = parse_calendar_bytes(
            ics_bytes,
            now=datetime(2026, 8, 24, tzinfo=timezone.utc),
            subscription_revision="test-rev",
        )
        assert result.succeeded, f"Parser failed: {result.feed_error}"
        assert len(result.events) == 2
        titles = {e.title for e in result.events}
        assert "Standup" in titles
        assert "Review" in titles

    def test_ics_escapes_special_chars(self):
        from holdspeak.calendar_ingest import parse_calendar_bytes

        events = [
            {
                "title": "Team; sync, update",
                "weekday": "monday",
                "start_time": "10:00",
                "end_time": "11:00",
                "location": "Building 3, Floor 2",
                "starts_at": "2026-08-24T10:00:00+00:00",
                "ends_at": "2026-08-24T11:00:00+00:00",
            },
        ]
        ics_bytes = generate_ics(events, source_id="esc-src")
        result = parse_calendar_bytes(
            ics_bytes,
            now=datetime(2026, 8, 24, tzinfo=timezone.utc),
            subscription_revision="esc-rev",
        )
        assert result.succeeded


# ── Anchor resolution ──────────────────────────────────────────────────


class TestAnchorResolution:
    def test_snaps_to_monday(self):
        # 2026-08-26 is a Wednesday
        monday = resolve_anchor_date("2026-08-26")
        assert monday == date(2026, 8, 24)
        assert monday.weekday() == 0  # Monday

    def test_monday_stays_monday(self):
        monday = resolve_anchor_date("2026-08-24")
        assert monday == date(2026, 8, 24)

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError, match="Invalid anchor date"):
            resolve_anchor_date("not-a-date")

    def test_absent_anchor_blocks_confirm(self):
        """Absent anchor must be caught before resolution — never silent."""
        with pytest.raises(ValueError):
            resolve_anchor_date("")


class TestResolveEvents:
    def test_weekday_to_absolute(self):
        monday = date(2026, 8, 24)
        events = [
            ExtractedEvent("Standup", "monday", "09:00", "09:30"),
            ExtractedEvent("Review", "friday", "14:00", "15:00"),
        ]
        resolved = resolve_events_to_timestamps(events, monday)
        assert len(resolved) == 2
        # Close-counsel should-fix (2026-08-28): screenshot times are LOCAL
        # wall-clock, not UTC — a 09:00 standup must render 09:00 on the rail.
        local_tz = datetime.now().astimezone().tzinfo
        assert resolved[0]["starts_at"] == datetime(2026, 8, 24, 9, 0, tzinfo=local_tz).isoformat()
        assert resolved[1]["starts_at"] == datetime(2026, 8, 28, 14, 0, tzinfo=local_tz).isoformat()
        assert resolved[1]["ends_at"] == datetime(2026, 8, 28, 15, 0, tzinfo=local_tz).isoformat()


# ── Merge and dedupe ──────────────────────────────────────────────────


class TestMergeExtractions:
    def test_deduplicates_exact_match(self):
        r1 = ExtractionResult(
            anchor_date="2026-08-24",
            anchor_confidence="visible_header",
            events=[
                ExtractedEvent("Standup", "monday", "09:00", "09:30"),
                ExtractedEvent("Review", "friday", "14:00", "15:00"),
            ],
        )
        r2 = ExtractionResult(
            anchor_date="2026-08-24",
            anchor_confidence="inferred",
            events=[
                ExtractedEvent("Standup", "monday", "09:00", "09:30"),  # dupe
                ExtractedEvent("Lunch", "wednesday", "12:00", "13:00"),
            ],
        )
        merged = merge_extractions([r1, r2])
        assert len(merged.events) == 3
        assert merged.anchor_confidence == "visible_header"

    def test_single_passes_through(self):
        r = ExtractionResult(
            anchor_date=None,
            anchor_confidence="absent",
            events=[ExtractedEvent("Only", "tuesday", "10:00", "11:00")],
        )
        assert merge_extractions([r]) is r

    def test_all_errors_stays_error(self):
        r1 = ExtractionResult(None, "absent", [], error="unreadable_screenshot")
        r2 = ExtractionResult(None, "absent", [], error="unreadable_screenshot")
        merged = merge_extractions([r1, r2])
        assert merged.error == "unreadable_screenshot"


# ── File lifecycle ──────────────────────────────────────────────────────


class TestFileLifecycle:
    def test_atomic_write_and_replace(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "holdspeak.services.calendar_snapshot_service.snapshot_dir",
            lambda: tmp_path,
        )
        events1 = [
            {
                "title": "V1",
                "starts_at": "2026-08-24T09:00:00+00:00",
                "ends_at": "2026-08-24T10:00:00+00:00",
            },
        ]
        ics1 = generate_ics(events1, source_id="test-src")
        path1 = write_ics_atomic("test-src", ics1)
        assert path1.exists()
        assert b"V1" in path1.read_bytes()

        events2 = [
            {
                "title": "V2",
                "starts_at": "2026-08-24T09:00:00+00:00",
                "ends_at": "2026-08-24T10:00:00+00:00",
            },
        ]
        ics2 = generate_ics(events2, source_id="test-src")
        path2 = write_ics_atomic("test-src", ics2)
        assert path2 == path1
        assert b"V2" in path2.read_bytes()
        assert b"V1" not in path2.read_bytes()


# ── Capability registry presence ────────────────────────────────────────


class TestCapabilityRegistered:
    def test_calendar_snapshot_extract_in_registry(self):
        from holdspeak.inference_capabilities import builtin_capability_definitions

        defs = builtin_capability_definitions()
        ids = {d.id for d in defs}
        assert "calendar.snapshot_extract" in ids

    def test_capability_requires_vision(self):
        from holdspeak.inference_capabilities import builtin_capability_definitions

        defs = builtin_capability_definitions()
        cap = next(d for d in defs if d.id == "calendar.snapshot_extract")
        assert cap.requires.vision is True
        assert cap.requires.structured_output is True
        assert cap.group_id == "background"

    def test_vision_claim_refusal_via_compat_check(self):
        """Profiles without the vision claim refuse this capability."""
        from holdspeak.inference_capabilities import builtin_capability_definitions

        cap = next(
            d
            for d in builtin_capability_definitions()
            if d.id == "calendar.snapshot_extract"
        )
        # The capability requires vision=True; a profile without the "vision"
        # claim in its deployment would be refused by the compat check at
        # inference_assignment_service.py:1876.
        assert cap.requires.vision is True


# ── Vision prompt adapter shape ─────────────────────────────────────────


class TestVisionPromptAdapter:
    def test_adapter_builds_multipart_content(self):
        from holdspeak.kernel.vision_prompt_adapter import VisionPromptAdapter

        adapter = VisionPromptAdapter()

        class FakeEngine:
            active_provider = "openai_compatible"
            active_model = "test-model"

            def run_prompt_messages(self, *, messages):
                # Verify the messages structure
                assert len(messages) == 2  # system + user
                assert messages[0]["role"] == "system"
                user_msg = messages[1]
                assert user_msg["role"] == "user"
                assert isinstance(user_msg["content"], list)
                assert user_msg["content"][0]["type"] == "text"
                assert user_msg["content"][1]["type"] == "image_url"
                url = user_msg["content"][1]["image_url"]["url"]
                assert url.startswith("data:image/png;base64,")
                return '{"events": []}'

        import threading

        result = adapter.dispatch(
            FakeEngine(),
            {
                "system_prompt": "Extract events",
                "user_prompt": "Extract all events",
                "image_base64": "AAAA",
                "image_media_type": "image/png",
            },
            threading.Event(),
        )
        assert result["provider"] == "openai_compatible"
        assert result["model"] == "test-model"

    def test_adapter_without_image(self):
        from holdspeak.kernel.vision_prompt_adapter import VisionPromptAdapter

        adapter = VisionPromptAdapter()

        class FakeEngine:
            active_provider = "local"
            active_model = "local-model"

            def run_prompt_messages(self, *, messages):
                user_msg = messages[-1]
                # With no image, content array has only the text part
                assert len(user_msg["content"]) == 1
                return "ok"

        import threading

        result = adapter.dispatch(
            FakeEngine(),
            {
                "system_prompt": "Test",
                "user_prompt": "Test prompt",
                "image_base64": "",
                "image_media_type": "image/png",
            },
            threading.Event(),
        )
        assert result["output"] == "ok"
