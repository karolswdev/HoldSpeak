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

    def test_valid_object_with_null_values(self):
        """JSON with null values is handled."""
        text = '{"owner": null, "due": null, "task": "Do something"}'
        result = _extract_json(text)
        assert result == {"owner": None, "due": None, "task": "Do something"}

    def test_valid_object_with_numbers(self):
        """JSON with numeric values is handled."""
        text = '{"count": 42, "ratio": 3.14, "negative": -10}'
        result = _extract_json(text)
        assert result == {"count": 42, "ratio": 3.14, "negative": -10}

    def test_valid_object_with_booleans(self):
        """JSON with boolean values is handled."""
        text = '{"active": true, "deleted": false}'
        result = _extract_json(text)
        assert result == {"active": True, "deleted": False}


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


class TestExtractJsonNestedStructures:
    """Tests for nested objects and arrays."""

    def test_nested_objects(self):
        """Nested objects are handled correctly."""
        text = '{"outer": {"inner": {"deep": "value"}}}'
        result = _extract_json(text)
        assert result == {"outer": {"inner": {"deep": "value"}}}

    def test_array_of_objects(self):
        """Array of objects is handled correctly."""
        text = '{"items": [{"id": 1}, {"id": 2}, {"id": 3}]}'
        result = _extract_json(text)
        assert result == {"items": [{"id": 1}, {"id": 2}, {"id": 3}]}

    def test_mixed_nested_types(self):
        """Mixed nested arrays and objects are handled."""
        text = '{"data": {"list": [1, "two", null, {"nested": true}]}}'
        result = _extract_json(text)
        assert result == {"data": {"list": [1, "two", None, {"nested": True}]}}

    def test_deeply_nested_action_items(self):
        """Deeply nested action items structure is handled."""
        text = """{
            "topics": ["Sprint planning"],
            "action_items": [
                {
                    "task": "Create tickets",
                    "owner": "Me",
                    "due": "Monday",
                    "subtasks": [
                        {"name": "Backend"},
                        {"name": "Frontend"}
                    ]
                }
            ],
            "summary": "Planning session"
        }"""
        result = _extract_json(text)
        assert result is not None
        assert len(result["action_items"]) == 1
        assert result["action_items"][0]["subtasks"][0]["name"] == "Backend"


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

    def test_trailing_comma(self):
        """JSON with trailing comma returns None (strict parsing)."""
        result = _extract_json('{"key": "value",}')
        assert result is None

    def test_single_quotes(self):
        """JSON with single quotes returns None."""
        result = _extract_json("{'key': 'value'}")
        assert result is None

    def test_unquoted_keys(self):
        """JSON with unquoted keys returns None."""
        result = _extract_json('{key: "value"}')
        assert result is None

    def test_invalid_value(self):
        """JSON with invalid value returns None."""
        result = _extract_json('{"key": undefined}')
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


class TestExtractJsonUnicode:
    """Tests for Unicode content handling."""

    def test_unicode_values(self):
        """JSON with Unicode values is handled."""
        text = '{"greeting": "Hello, \u4e16\u754c!"}'
        result = _extract_json(text)
        assert result is not None
        assert result["greeting"] == "Hello, \u4e16\u754c!"

    def test_emoji_in_json(self):
        """JSON with emoji characters is handled."""
        text = '{"status": "Done!", "icon": "checkmark"}'
        result = _extract_json(text)
        assert result == {"status": "Done!", "icon": "checkmark"}

    def test_mixed_scripts(self):
        """JSON with mixed language scripts is handled."""
        text = '{"japanese": "\u3053\u3093\u306b\u3061\u306f", "arabic": "\u0645\u0631\u062d\u0628\u0627", "english": "Hello"}'
        result = _extract_json(text)
        assert result is not None
        assert result["japanese"] == "\u3053\u3093\u306b\u3061\u306f"
        assert result["arabic"] == "\u0645\u0631\u062d\u0628\u0627"
        assert result["english"] == "Hello"

    def test_unicode_escape_sequences(self):
        """JSON with Unicode escape sequences is handled."""
        text = '{"text": "Line1\\nLine2\\tTabbed"}'
        result = _extract_json(text)
        assert result is not None
        assert result["text"] == "Line1\nLine2\tTabbed"


class TestExtractJsonEscapedQuotes:
    """Tests for escaped quotes handling."""

    def test_escaped_double_quotes_in_value(self):
        """JSON with escaped double quotes in value is handled."""
        text = '{"quote": "He said \\"Hello\\""}'
        result = _extract_json(text)
        assert result is not None
        assert result["quote"] == 'He said "Hello"'

    def test_multiple_escaped_quotes(self):
        """JSON with multiple escaped quotes is handled."""
        text = '{"dialog": "\\"Hi\\" said Alice. \\"Hello\\" replied Bob."}'
        result = _extract_json(text)
        assert result is not None
        assert result["dialog"] == '"Hi" said Alice. "Hello" replied Bob.'

    def test_backslash_in_json(self):
        """JSON with backslashes is handled."""
        text = '{"path": "C:\\\\Users\\\\test"}'
        result = _extract_json(text)
        assert result is not None
        assert result["path"] == "C:\\Users\\test"

    def test_mixed_escapes(self):
        """JSON with mixed escape sequences is handled."""
        text = '{"text": "Tab:\\t Quote:\\" Newline:\\n"}'
        result = _extract_json(text)
        assert result is not None
        assert result["text"] == 'Tab:\t Quote:" Newline:\n'


class TestExtractJsonEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_object(self):
        """Empty JSON object is extracted."""
        result = _extract_json("{}")
        assert result == {}

    def test_empty_strings_in_values(self):
        """JSON with empty string values is handled."""
        text = '{"name": "", "description": ""}'
        result = _extract_json(text)
        assert result == {"name": "", "description": ""}

    def test_empty_arrays_in_values(self):
        """JSON with empty array values is handled."""
        text = '{"topics": [], "action_items": []}'
        result = _extract_json(text)
        assert result == {"topics": [], "action_items": []}

    def test_very_long_string_value(self):
        """JSON with very long string value is handled."""
        long_text = "A" * 10000
        text = f'{{"content": "{long_text}"}}'
        result = _extract_json(text)
        assert result is not None
        assert result["content"] == long_text

    def test_many_keys(self):
        """JSON with many keys is handled."""
        keys = {f"key{i}": i for i in range(100)}
        import json

        text = json.dumps(keys)
        result = _extract_json(text)
        assert result == keys

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
