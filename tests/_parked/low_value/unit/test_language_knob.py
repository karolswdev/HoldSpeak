# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_language_knob.py to restore.

# ruff: noqa


# --- test_registry_is_whisper_sized: P1/P8: counts a constant table and scans a module's import lines
def test_registry_is_whisper_sized() -> None:
    assert len(WHISPER_LANGUAGES) >= 99
    assert all(code == code.lower() for code in WHISPER_LANGUAGES)


# --- test_registry_module_is_light: P1/P8: counts a constant table and scans a module's import lines
def test_registry_module_is_light() -> None:
    # The registry must be importable at config time: no transcription
    # backend, no numpy. Check real import statements, not docstring words.
    import holdspeak.languages as mod

    lines = [l.strip() for l in open(mod.__file__) if l.strip().startswith(("import ", "from "))]
    for line in lines:
        for heavy in ("mlx", "faster_whisper", "numpy", "torch"):
            assert heavy not in line, f"heavy import in languages.py: {line}"
