"""HS-153-06 -- robust structured-output extraction for Qwen-style responses.

Models like Qwen3.6 on llama.cpp wrap JSON in think-blocks, markdown code
fences, or trailing prose.  The ``_extract_structured_json`` helper must
handle all of these and return the parsed dict.
"""
from __future__ import annotations

import pytest

from holdspeak.services.thread_practice import _extract_structured_json


class TestExtractStructuredJson:
    """Covers every Qwen3.6-observed wrapping variant."""

    def test_plain_json(self):
        raw = '{"violations": ["no source"], "warnings": []}'
        result = _extract_structured_json(raw)
        assert result == {"violations": ["no source"], "warnings": []}

    def test_fenced_json(self):
        raw = '```json\n{"violations": ["no source"], "warnings": []}\n```'
        result = _extract_structured_json(raw)
        assert result == {"violations": ["no source"], "warnings": []}

    def test_fenced_json_no_language_tag(self):
        raw = '```\n{"summary": "things happened"}\n```'
        result = _extract_structured_json(raw)
        assert result == {"summary": "things happened"}

    def test_think_block_then_json(self):
        raw = (
            "<think>\nLet me analyze the pending tool calls...\n"
            "The call lacks a source argument.\n</think>\n"
            '{"violations": ["no source named"], "warnings": []}'
        )
        result = _extract_structured_json(raw)
        assert result == {"violations": ["no source named"], "warnings": []}

    def test_think_block_then_fenced_json(self):
        raw = (
            "<think>Reasoning about the guardrail...</think>\n"
            "```json\n"
            '{"violations": ["egress risk"], "warnings": ["check boundary"]}\n'
            "```"
        )
        result = _extract_structured_json(raw)
        assert result == {
            "violations": ["egress risk"],
            "warnings": ["check boundary"],
        }

    def test_json_after_prose(self):
        raw = (
            "Based on my analysis, here is the result:\n"
            '{"violations": [], "warnings": ["possible risk"]}'
        )
        result = _extract_structured_json(raw)
        assert result == {"violations": [], "warnings": ["possible risk"]}

    def test_json_with_trailing_text(self):
        raw = (
            '{"summary": "Meeting discussed priorities."}\n\n'
            "I hope this summary is helpful!"
        )
        result = _extract_structured_json(raw)
        assert result == {"summary": "Meeting discussed priorities."}

    def test_empty_string(self):
        assert _extract_structured_json("") is None

    def test_no_json(self):
        assert _extract_structured_json("This is just plain text.") is None

    def test_nested_braces_in_json(self):
        raw = '{"violations": ["call {foo} has no source"], "warnings": []}'
        result = _extract_structured_json(raw)
        assert result == {
            "violations": ["call {foo} has no source"],
            "warnings": [],
        }

    def test_multiple_think_blocks(self):
        raw = (
            "<think>First thought</think>\n"
            "<think>Second thought</think>\n"
            '{"violations": ["found it"], "warnings": []}'
        )
        result = _extract_structured_json(raw)
        assert result == {"violations": ["found it"], "warnings": []}

    def test_array_not_accepted(self):
        """The helper returns only dict objects, not arrays."""
        raw = '["item1", "item2"]'
        assert _extract_structured_json(raw) is None
