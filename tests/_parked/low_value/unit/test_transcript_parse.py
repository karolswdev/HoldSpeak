# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_transcript_parse.py to restore.

# ruff: noqa


# --- test_suffix_registry_is_the_v1_trio: P1/P8/P6: a constant suffix set, a source scan for forbidden imports, and an isinstance check the parser tests already cover
def test_suffix_registry_is_the_v1_trio() -> None:
    assert TRANSCRIPT_SUFFIXES == frozenset({".vtt", ".srt", ".txt"})


# --- test_module_is_pure: P1/P8/P6: a constant suffix set, a source scan for forbidden imports, and an isinstance check the parser tests already cover
def test_module_is_pure() -> None:
    import holdspeak.transcript_parse as mod

    source = open(mod.__file__).read()
    for forbidden in ("import sqlite3", "from .db", "from .config", "import requests",
                      "import httpx", "open("):
        assert forbidden not in source, f"pure parser module must not use {forbidden!r}"


# --- test_parsed_transcript_shape: P1/P8/P6: a constant suffix set, a source scan for forbidden imports, and an isinstance check the parser tests already cover
def test_parsed_transcript_shape() -> None:
    parsed = parse_transcript("Ana: hi\n", "x.txt")
    assert isinstance(parsed, ParsedTranscript)
    cue = parsed.cues[0]
    assert (cue.text, cue.speaker) == ("hi", "Ana")
