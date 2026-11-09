# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_intel_extract.py to restore.

# ruff: noqa


# --- TestExtractJsonNestedStructures: P3: the object goes straight through json.loads; these test Python's JSON parser (nesting, unicode, escapes)
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


# --- TestExtractJsonUnicode: P3: the object goes straight through json.loads; these test Python's JSON parser (nesting, unicode, escapes)
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


# --- TestExtractJsonEscapedQuotes: P3: the object goes straight through json.loads; these test Python's JSON parser (nesting, unicode, escapes)
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


# --- TestExtractJsonPlainObjects::test_valid_object_with_null_values: P3: tests what json.loads accepts or rejects, not the extractor's own recovery
# (was a method of class TestExtractJsonPlainObjects)
def test_valid_object_with_null_values(self):
    """JSON with null values is handled."""
    text = '{"owner": null, "due": null, "task": "Do something"}'
    result = _extract_json(text)
    assert result == {"owner": None, "due": None, "task": "Do something"}


# --- TestExtractJsonPlainObjects::test_valid_object_with_numbers: P3: tests what json.loads accepts or rejects, not the extractor's own recovery
# (was a method of class TestExtractJsonPlainObjects)
def test_valid_object_with_numbers(self):
    """JSON with numeric values is handled."""
    text = '{"count": 42, "ratio": 3.14, "negative": -10}'
    result = _extract_json(text)
    assert result == {"count": 42, "ratio": 3.14, "negative": -10}


# --- TestExtractJsonPlainObjects::test_valid_object_with_booleans: P3: tests what json.loads accepts or rejects, not the extractor's own recovery
# (was a method of class TestExtractJsonPlainObjects)
def test_valid_object_with_booleans(self):
    """JSON with boolean values is handled."""
    text = '{"active": true, "deleted": false}'
    result = _extract_json(text)
    assert result == {"active": True, "deleted": False}


# --- TestExtractJsonMalformed::test_trailing_comma: P3: tests what json.loads accepts or rejects, not the extractor's own recovery
# (was a method of class TestExtractJsonMalformed)
def test_trailing_comma(self):
    """JSON with trailing comma returns None (strict parsing)."""
    result = _extract_json('{"key": "value",}')
    assert result is None


# --- TestExtractJsonMalformed::test_single_quotes: P3: tests what json.loads accepts or rejects, not the extractor's own recovery
# (was a method of class TestExtractJsonMalformed)
def test_single_quotes(self):
    """JSON with single quotes returns None."""
    result = _extract_json("{'key': 'value'}")
    assert result is None


# --- TestExtractJsonMalformed::test_unquoted_keys: P3: tests what json.loads accepts or rejects, not the extractor's own recovery
# (was a method of class TestExtractJsonMalformed)
def test_unquoted_keys(self):
    """JSON with unquoted keys returns None."""
    result = _extract_json('{key: "value"}')
    assert result is None


# --- TestExtractJsonMalformed::test_invalid_value: P3: tests what json.loads accepts or rejects, not the extractor's own recovery
# (was a method of class TestExtractJsonMalformed)
def test_invalid_value(self):
    """JSON with invalid value returns None."""
    result = _extract_json('{"key": undefined}')
    assert result is None


# --- TestExtractJsonEdgeCases::test_empty_strings_in_values: P3: tests what json.loads accepts or rejects, not the extractor's own recovery
# (was a method of class TestExtractJsonEdgeCases)
def test_empty_strings_in_values(self):
    """JSON with empty string values is handled."""
    text = '{"name": "", "description": ""}'
    result = _extract_json(text)
    assert result == {"name": "", "description": ""}


# --- TestExtractJsonEdgeCases::test_empty_arrays_in_values: P3: tests what json.loads accepts or rejects, not the extractor's own recovery
# (was a method of class TestExtractJsonEdgeCases)
def test_empty_arrays_in_values(self):
    """JSON with empty array values is handled."""
    text = '{"topics": [], "action_items": []}'
    result = _extract_json(text)
    assert result == {"topics": [], "action_items": []}


# --- TestExtractJsonEdgeCases::test_very_long_string_value: P3: tests what json.loads accepts or rejects, not the extractor's own recovery
# (was a method of class TestExtractJsonEdgeCases)
def test_very_long_string_value(self):
    """JSON with very long string value is handled."""
    long_text = "A" * 10000
    text = f'{{"content": "{long_text}"}}'
    result = _extract_json(text)
    assert result is not None
    assert result["content"] == long_text


# --- TestExtractJsonEdgeCases::test_many_keys: P3: tests what json.loads accepts or rejects, not the extractor's own recovery
# (was a method of class TestExtractJsonEdgeCases)
def test_many_keys(self):
    """JSON with many keys is handled."""
    keys = {f"key{i}": i for i in range(100)}
    import json

    text = json.dumps(keys)
    result = _extract_json(text)
    assert result == keys
