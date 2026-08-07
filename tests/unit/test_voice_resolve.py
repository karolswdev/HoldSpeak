"""HS-118-05 — Voice resolver: prompt construction, retry chain,
parsing, validation, and resolution engine.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from holdspeak.voice_resolver import (
    MAX_REFS,
    MAX_TRANSCRIPT_CHARS,
    MAX_ZONES,
    ResolverResult,
    ZoneCatalogEntry,
    _extract_json_from_response,
    _validate_response,
    build_resolver_prompt,
    build_retry_prompt,
    format_zone_catalog,
    resolve_voice_references,
    truncate_transcript,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _zones(*pairs: tuple[str, str]) -> list[ZoneCatalogEntry]:
    return [ZoneCatalogEntry(id=zid, name=name, items=0) for zid, name in pairs]


def _mock_fn(responses: list[str]):
    """Build a run_prompt_fn that returns successive responses."""
    calls: list[dict[str, Any]] = []
    idx = [0]

    def fn(*, prompt: str, profile_id: str, max_tokens: int, timeout: float) -> str:
        calls.append({"prompt": prompt, "profile_id": profile_id, "max_tokens": max_tokens, "timeout": timeout})
        i = idx[0]
        idx[0] += 1
        if i >= len(responses):
            raise RuntimeError("No more mock responses")
        resp = responses[i]
        if isinstance(resp, Exception):
            raise resp
        return resp

    return fn, calls


def _mock_fn_raises(exc_type):
    """Build a run_prompt_fn that always raises."""
    def fn(*, prompt: str, profile_id: str, max_tokens: int, timeout: float) -> str:
        raise exc_type("simulated failure")
    return fn


# ── Prompt construction ─────────────────────────────────────────────────────

class TestResolverPrompt:
    def test_prompt_includes_zone_ids(self):
        zones = _zones(("dir_1", "Monday Standup"), ("dir_2", "Research Notes"))
        prompt = build_resolver_prompt(zones, "summarize the standup")
        assert "dir_1" in prompt
        assert "dir_2" in prompt
        assert "Monday Standup" in prompt

    def test_prompt_includes_transcript_as_json(self):
        zones = _zones(("dir_1", "Test"))
        prompt = build_resolver_prompt(zones, "check the test zone")
        # Transcript should be JSON-encoded in the prompt
        assert json.dumps("check the test zone") in prompt

    def test_retry_prompt_includes_previous_response(self):
        zones = _zones(("dir_1", "Test"))
        retry = build_retry_prompt(0, zones, "check test", "some garbage response")
        assert "some garbage response" in retry

    def test_retry_prompt_index_1(self):
        zones = _zones(("dir_1", "Test"))
        retry = build_retry_prompt(1, zones, "check test", "bad")
        assert "dir_1" in retry

    def test_retry_prompt_out_of_range_raises(self):
        with pytest.raises(ValueError):
            build_retry_prompt(99, [], "test", "bad")


# ── JSON extraction ─────────────────────────────────────────────────────────

class TestJsonExtraction:
    def test_plain_json(self):
        result = _extract_json_from_response('{"zone_ids": ["dir_1"]}')
        assert result == {"zone_ids": ["dir_1"]}

    def test_markdown_fenced_json(self):
        text = '```json\n{"zone_ids": ["dir_1"]}\n```'
        result = _extract_json_from_response(text)
        assert result == {"zone_ids": ["dir_1"]}

    def test_markdown_fenced_no_lang(self):
        text = '```\n{"zone_ids": ["dir_1"]}\n```'
        result = _extract_json_from_response(text)
        assert result == {"zone_ids": ["dir_1"]}

    def test_json_embedded_in_text(self):
        text = 'Here is the result: {"zone_ids": ["dir_1"]} as requested.'
        result = _extract_json_from_response(text)
        assert result == {"zone_ids": ["dir_1"]}

    def test_completely_invalid(self):
        assert _extract_json_from_response("not json at all") is None

    def test_empty_string(self):
        assert _extract_json_from_response("") is None


# ── Response validation ─────────────────────────────────────────────────────

class TestResponseValidation:
    def test_valid_ids_returned(self):
        parsed = {"zone_ids": ["dir_1", "dir_2"]}
        result = _validate_response(parsed, {"dir_1", "dir_2", "dir_3"})
        assert result == ["dir_1", "dir_2"]

    def test_unknown_ids_dropped(self):
        parsed = {"zone_ids": ["dir_1", "dir_unknown", "dir_2"]}
        result = _validate_response(parsed, {"dir_1", "dir_2"})
        assert result == ["dir_1", "dir_2"]

    def test_duplicates_removed(self):
        parsed = {"zone_ids": ["dir_1", "dir_1", "dir_2"]}
        result = _validate_response(parsed, {"dir_1", "dir_2"})
        assert result == ["dir_1", "dir_2"]

    def test_empty_zone_ids(self):
        parsed = {"zone_ids": []}
        result = _validate_response(parsed, {"dir_1"})
        assert result == []

    def test_non_list_zone_ids_rejected(self):
        parsed = {"zone_ids": "dir_1"}
        assert _validate_response(parsed, {"dir_1"}) is None

    def test_non_string_entries_rejected(self):
        parsed = {"zone_ids": [123, "dir_1"]}
        assert _validate_response(parsed, {"dir_1"}) is None

    def test_missing_zone_ids_key_rejected(self):
        parsed = {"zones": ["dir_1"]}
        assert _validate_response(parsed, {"dir_1"}) is None


# ── Transcript truncation ───────────────────────────────────────────────────

class TestTranscriptTruncation:
    def test_short_transcript_unchanged(self):
        assert truncate_transcript("hello") == "hello"

    def test_long_transcript_truncated(self):
        long_text = "word " * 1000  # well over 2048 chars
        result = truncate_transcript(long_text)
        assert len(result) <= MAX_TRANSCRIPT_CHARS

    def test_truncation_at_word_boundary(self):
        long_text = "a" * (MAX_TRANSCRIPT_CHARS - 5) + " " + "b" * 100
        result = truncate_transcript(long_text)
        assert len(result) <= MAX_TRANSCRIPT_CHARS
        # Should end at a word boundary (the space)
        assert not result.endswith("b")


# ── Zone catalog formatting ─────────────────────────────────────────────────

class TestFormatZoneCatalog:
    def test_formats_as_json(self):
        zones = _zones(("dir_1", "Test Zone"))
        catalog = format_zone_catalog(zones)
        parsed = json.loads(catalog)
        assert len(parsed) == 1
        assert parsed[0]["id"] == "dir_1"
        assert parsed[0]["name"] == "Test Zone"

    def test_truncates_to_max_zones(self):
        zones = [ZoneCatalogEntry(id=f"dir_{i}", name=f"Zone {i}") for i in range(300)]
        catalog = format_zone_catalog(zones)
        parsed = json.loads(catalog)
        assert len(parsed) == MAX_ZONES


# ── Resolution engine ───────────────────────────────────────────────────────

class TestResolveVoiceReferences:
    def test_valid_response_resolves(self):
        zones = _zones(("dir_1", "Monday Standup"), ("dir_2", "Research Notes"))
        fn, calls = _mock_fn(['{"zone_ids": ["dir_1", "dir_2"]}'])
        result = resolve_voice_references(
            zones=zones, transcript="summarize the standup and research",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.terminal_state == "success"
        assert len(result.refs) == 2
        assert result.refs[0].id == "dir_1"
        assert result.refs[0].name == "Monday Standup"
        assert result.refs[0].ref == "zone:dir_1"
        assert result.refs[1].id == "dir_2"
        assert result.attempts == 1

    def test_unknown_ids_dropped_silently(self):
        zones = _zones(("dir_1", "Test"))
        fn, _ = _mock_fn(['{"zone_ids": ["dir_1", "dir_unknown"]}'])
        result = resolve_voice_references(
            zones=zones, transcript="test",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.terminal_state == "success"
        assert len(result.refs) == 1
        assert result.refs[0].id == "dir_1"

    def test_empty_zone_ids_no_error(self):
        zones = _zones(("dir_1", "Test"))
        fn, _ = _mock_fn(['{"zone_ids": []}'])
        result = resolve_voice_references(
            zones=zones, transcript="what did I do today",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.terminal_state == "success"
        assert result.refs == []

    def test_malformed_json_retries(self):
        zones = _zones(("dir_1", "Test"))
        fn, calls = _mock_fn([
            "not json",
            '{"zone_ids": ["dir_1"]}',
        ])
        result = resolve_voice_references(
            zones=zones, transcript="test",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.terminal_state == "success"
        assert len(result.refs) == 1
        assert result.attempts == 2
        assert len(calls) == 2

    def test_all_attempts_malformed_gives_parse_failure(self):
        zones = _zones(("dir_1", "Test"))
        fn, calls = _mock_fn(["bad", "still bad", "nope"])
        result = resolve_voice_references(
            zones=zones, transcript="test",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.terminal_state == "parse_failure"
        assert result.attempts == 3
        assert result.refs == []

    def test_success_on_attempt_2(self):
        zones = _zones(("dir_1", "Test"), ("dir_2", "Other"))
        fn, _ = _mock_fn([
            "I think the answer is dir_1",  # malformed
            '{"zone_ids": ["dir_2"]}',       # valid
        ])
        result = resolve_voice_references(
            zones=zones, transcript="check other",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.terminal_state == "success"
        assert result.attempts == 2
        assert len(result.refs) == 1
        assert result.refs[0].id == "dir_2"

    def test_valid_shape_unknown_ids_no_retry(self):
        """Valid JSON shape but all IDs unknown: success with empty refs, no retry."""
        zones = _zones(("dir_1", "Test"))
        fn, calls = _mock_fn(['{"zone_ids": ["dir_unknown_1", "dir_unknown_2"]}'])
        result = resolve_voice_references(
            zones=zones, transcript="test",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.terminal_state == "success"
        assert result.refs == []
        assert result.attempts == 1
        assert len(calls) == 1  # no retry

    def test_empty_zone_catalog_skips_model(self):
        fn, calls = _mock_fn([])
        result = resolve_voice_references(
            zones=[], transcript="test",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.terminal_state == "success"
        assert result.refs == []
        assert len(calls) == 0

    def test_large_zone_catalog_truncated(self):
        zones = [ZoneCatalogEntry(id=f"dir_{i}", name=f"Zone {i}") for i in range(300)]
        fn, calls = _mock_fn(['{"zone_ids": ["dir_0"]}'])
        result = resolve_voice_references(
            zones=zones, transcript="check zone 0",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.terminal_state == "success"
        # Only first MAX_ZONES zones should be in the prompt
        prompt = calls[0]["prompt"]
        assert "dir_0" in prompt
        assert f"dir_{MAX_ZONES}" not in prompt

    def test_long_transcript_truncated(self):
        zones = _zones(("dir_1", "Test"))
        long_transcript = "word " * 1000
        fn, calls = _mock_fn(['{"zone_ids": []}'])
        resolve_voice_references(
            zones=zones, transcript=long_transcript,
            run_prompt_fn=fn, profile_id="prof-1",
        )
        # Prompt should contain the truncated transcript
        prompt = calls[0]["prompt"]
        assert len(prompt) < len(long_transcript) + 500

    def test_timeout_on_all_attempts(self):
        zones = _zones(("dir_1", "Test"))
        fn = _mock_fn_raises(TimeoutError)
        result = resolve_voice_references(
            zones=zones, transcript="test",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.terminal_state == "timeout"
        assert result.attempts == 3

    def test_error_on_all_attempts(self):
        zones = _zones(("dir_1", "Test"))
        fn = _mock_fn_raises(RuntimeError)
        result = resolve_voice_references(
            zones=zones, transcript="test",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.terminal_state == "error"
        assert result.attempts == 3

    def test_empty_transcript_skips_model(self):
        zones = _zones(("dir_1", "Test"))
        fn, calls = _mock_fn([])
        result = resolve_voice_references(
            zones=zones, transcript="   ",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.terminal_state == "success"
        assert result.refs == []
        assert len(calls) == 0

    def test_request_id_propagated(self):
        zones = _zones(("dir_1", "Test"))
        fn, _ = _mock_fn(['{"zone_ids": []}'])
        result = resolve_voice_references(
            zones=zones, transcript="test",
            run_prompt_fn=fn, profile_id="prof-1",
            request_id="custom-id-123",
        )
        assert result.request_id == "custom-id-123"

    def test_request_id_generated_when_empty(self):
        zones = _zones(("dir_1", "Test"))
        fn, _ = _mock_fn(['{"zone_ids": []}'])
        result = resolve_voice_references(
            zones=zones, transcript="test",
            run_prompt_fn=fn, profile_id="prof-1",
        )
        assert result.request_id.startswith("vr_")
