# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_wake_word.py to restore.

# ruff: noqa


# --- test_module_imports_without_the_engine: P1/P8/P5: 'assert wake_word_available() in (True, False)', a source scan for an import line, and WakeWordConfig(**{}) which the defaults test already builds
def test_module_imports_without_the_engine():
    # This very file imported holdspeak.wake_word at the top with no
    # openwakeword requirement; the availability probe is bool either way.
    assert wake_word_available() in (True, False)


# --- test_lazy_imports_only: P1/P8/P5: 'assert wake_word_available() in (True, False)', a source scan for an import line, and WakeWordConfig(**{}) which the defaults test already builds
def test_lazy_imports_only():
    import holdspeak.wake_word as mod

    top_level = [
        l.strip()
        for l in open(mod.__file__)
        if l.startswith(("import ", "from "))
    ]
    for line in top_level:
        assert "openwakeword" not in line, f"engine import must be lazy: {line}"


# --- test_older_config_shape_coerces_forward: P1/P8/P5: 'assert wake_word_available() in (True, False)', a source scan for an import line, and WakeWordConfig(**{}) which the defaults test already builds
def test_older_config_shape_coerces_forward():
    # A config without the section loads with defaults (the _coerce path).
    assert WakeWordConfig(**{}).enabled is False
