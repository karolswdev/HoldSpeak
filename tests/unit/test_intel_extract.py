"""Unit tests for intel._extract_json() function.

Tests JSON extraction from LLM responses that may contain:
- Plain JSON objects
- JSON wrapped in markdown code blocks
- JSON with surrounding text
- Malformed or invalid JSON
"""

from __future__ import annotations

import pytest

from holdspeak.intel import _extract_json


class TestExtractJsonPlainObjects:
    """Tests for plain JSON object extraction."""

    def test_valid_simple_object(self):
        """Valid simple JSON object is extracted correctly."""
        text = '{"key": "value"}'
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_valid_object_with_whitespace(self):
        """JSON with surrounding whitespace is handled."""
        text = '  \n  {"topics": ["one", "two"]}  \n  '
        result = _extract_json(text)
        assert result == {"topics": ["one", "two"]}

    def test_valid_complex_object(self):
        """Complex nested JSON object is extracted correctly."""
        text = """{
            "topics": ["Project planning", "Budget review"],
            "action_items": [
                {"task": "Review proposal", "owner": "Me", "due": "Friday"}
            ],
            "summary": "Meeting about Q1 planning"
        }"""
        result = _extract_json(text)
        assert result is not None
        assert result["topics"] == ["Project planning", "Budget review"]
        assert len(result["action_items"]) == 1
        assert result["action_items"][0]["task"] == "Review proposal"
        assert result["summary"] == "Meeting about Q1 planning"

class TestExtractJsonCodeBlocks:
    """Tests for JSON in markdown code blocks."""

    def test_json_code_block(self):
        """JSON in ```json ... ``` block is extracted."""
        text = '```json\n{"topics": ["Topic A"]}\n```'
        result = _extract_json(text)
        assert result == {"topics": ["Topic A"]}

    def test_json_code_block_no_language(self):
        """JSON in ``` ... ``` block without language tag is extracted."""
        text = '```\n{"summary": "Test summary"}\n```'
        result = _extract_json(text)
        assert result == {"summary": "Test summary"}

    def test_json_code_block_uppercase_language(self):
        """JSON in ```JSON ... ``` (uppercase) block is extracted."""
        text = '```JSON\n{"key": "value"}\n```'
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_json_code_block_with_extra_whitespace(self):
        """JSON code block with extra whitespace is handled."""
        text = '```json  \n  {"data": "test"}  \n  ```'
        result = _extract_json(text)
        assert result == {"data": "test"}

    def test_multiline_json_in_code_block(self):
        """Multiline JSON in code block is extracted."""
        text = """```json
{
    "topics": [
        "First topic",
        "Second topic"
    ],
    "summary": "A test"
}
```"""
        result = _extract_json(text)
        assert result is not None
        assert result["topics"] == ["First topic", "Second topic"]
        assert result["summary"] == "A test"


class TestExtractJsonSurroundingText:
    """Tests for JSON with surrounding text."""

    def test_json_with_leading_text(self):
        """JSON preceded by text is extracted."""
        text = 'Here is the analysis:\n{"result": "success"}'
        result = _extract_json(text)
        assert result == {"result": "success"}

    def test_json_with_trailing_text(self):
        """JSON followed by text is extracted."""
        text = '{"status": "complete"}\nThank you for the request.'
        result = _extract_json(text)
        assert result == {"status": "complete"}

    def test_json_with_surrounding_text(self):
        """JSON surrounded by text on both sides is extracted."""
        text = 'I analyzed the transcript:\n{"topics": ["Budget"]}\nHope this helps!'
        result = _extract_json(text)
        assert result == {"topics": ["Budget"]}

    def test_json_with_explanation(self):
        """JSON with LLM-style explanation is extracted."""
        text = """Based on the transcript, here's the meeting intelligence:

{"topics": ["Project kickoff", "Timeline"], "action_items": [], "summary": "Initial meeting"}

The above JSON contains the extracted information."""
        result = _extract_json(text)
        assert result is not None
        assert result["topics"] == ["Project kickoff", "Timeline"]
        assert result["action_items"] == []
        assert result["summary"] == "Initial meeting"


class TestExtractJsonEmptyAndMissing:
    """Tests for empty strings and missing JSON."""

    def test_empty_string_returns_none(self):
        """Empty string returns None."""
        result = _extract_json("")
        assert result is None

    def test_whitespace_only_returns_none(self):
        """Whitespace-only string returns None."""
        result = _extract_json("   \n\t  ")
        assert result is None

    def test_no_json_present_returns_none(self):
        """String with no JSON returns None."""
        result = _extract_json("This is just regular text without any JSON.")
        assert result is None

    def test_text_with_curly_braces_not_json(self):
        """Text with curly braces that isn't JSON returns None."""
        result = _extract_json("Hello {name}, welcome to {place}!")
        assert result is None

    def test_only_opening_brace(self):
        """String with only opening brace returns None."""
        result = _extract_json("{ incomplete")
        assert result is None

    def test_only_closing_brace(self):
        """String with only closing brace returns None."""
        result = _extract_json("incomplete }")
        assert result is None


class TestExtractJsonMalformed:
    """Tests for malformed JSON handling."""

    def test_missing_closing_brace(self):
        """JSON missing closing brace returns None."""
        result = _extract_json('{"key": "value"')
        assert result is None

    def test_missing_opening_brace(self):
        """JSON missing opening brace returns None."""
        result = _extract_json('"key": "value"}')
        assert result is None

    def test_truncated_json(self):
        """Truncated JSON returns None."""
        result = _extract_json('{"topics": ["one", "tw')
        assert result is None

    def test_array_not_object_returns_none(self):
        """JSON array (not object) returns None."""
        result = _extract_json('["item1", "item2", "item3"]')
        assert result is None

    def test_primitive_not_object_returns_none(self):
        """JSON primitive (not object) returns None."""
        result = _extract_json('"just a string"')
        assert result is None

    def test_number_not_object_returns_none(self):
        """JSON number (not object) returns None."""
        result = _extract_json("42")
        assert result is None


class TestExtractJsonEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_object(self):
        """Empty JSON object is extracted."""
        result = _extract_json("{}")
        assert result == {}

    def test_realistic_intel_response(self):
        """Realistic LLM intel response is extracted correctly."""
        text = """{
    "topics": [
        "Q1 budget review",
        "New hire onboarding",
        "Product roadmap updates"
    ],
    "action_items": [
        {
            "task": "Submit budget proposal",
            "owner": "Me",
            "due": "End of week"
        },
        {
            "task": "Schedule onboarding sessions",
            "owner": "Remote",
            "due": null
        },
        {
            "task": "Review competitor analysis",
            "owner": null,
            "due": "Next Monday"
        }
    ],
    "summary": "Team reviewed Q1 budget status, discussed onboarding process for new hires, and aligned on product roadmap priorities for the quarter."
}"""
        result = _extract_json(text)
        assert result is not None
        assert len(result["topics"]) == 3
        assert len(result["action_items"]) == 3
        assert result["action_items"][0]["owner"] == "Me"
        assert result["action_items"][1]["due"] is None
        assert "Q1 budget" in result["summary"]
