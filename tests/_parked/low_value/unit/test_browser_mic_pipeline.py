# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_browser_mic_pipeline.py to restore.

# ruff: noqa


# --- test_corrections_are_universal_across_sources: P1: asserts the config flag it set one line earlier and that a bare server has no store
def test_corrections_are_universal_across_sources() -> None:
    """Corrections are not siloed by source -- both browser and hotkey
    use the same correction store."""
    cfg = _enabled_config()
    cfg.dictation.pipeline.corrections_enabled = True
    server = _bare_server()

    # Both sources would access the same corrections_store on the server.
    # The correction store is source-agnostic: there is no source field
    # on corrections. This test verifies the config doesn't create silos.
    assert cfg.dictation.pipeline.corrections_enabled is True
    # The store is the same object -- no per-source branching exists.
    assert server.dictation_corrections is None  # bare server has no store


# --- test_browser_is_valid_journal_source: P1: asserts a string is in a constant set; the journal tests above write real rows with these sources
def test_browser_is_valid_journal_source() -> None:
    """The journal accepts "browser" as a valid source."""
    from holdspeak.db.journal import VALID_JOURNAL_SOURCES
    from holdspeak.plugins.dictation.journal import VALID_SOURCES

    assert "browser" in VALID_JOURNAL_SOURCES
    assert "browser" in VALID_SOURCES


# --- test_hotkey_is_valid_journal_source: P1: asserts a string is in a constant set; the journal tests above write real rows with these sources
def test_hotkey_is_valid_journal_source() -> None:
    """The journal accepts "hotkey" as a valid source."""
    from holdspeak.db.journal import VALID_JOURNAL_SOURCES
    from holdspeak.plugins.dictation.journal import VALID_SOURCES

    assert "hotkey" in VALID_JOURNAL_SOURCES
    assert "hotkey" in VALID_SOURCES


# --- test_dictation_is_valid_journal_source: P1: asserts a string is in a constant set; the journal tests above write real rows with these sources
def test_dictation_is_valid_journal_source() -> None:
    """The journal still accepts "dictation" (backward compat)."""
    from holdspeak.db.journal import VALID_JOURNAL_SOURCES
    from holdspeak.plugins.dictation.journal import VALID_SOURCES

    assert "dictation" in VALID_JOURNAL_SOURCES
    assert "dictation" in VALID_SOURCES


# --- test_run_dictation_pipeline_unchanged_api: P5/P8: a refactor-era signature pin; the disabled-pipeline tests already call it
def test_run_dictation_pipeline_unchanged_api() -> None:
    """run_dictation_pipeline signature is unchanged after factoring."""
    cfg = _enabled_config()
    cfg.dictation.pipeline.enabled = False
    server = _bare_server()

    # This must work without any new parameters
    result = run_dictation_pipeline(
        "test",
        config=cfg,
        server=server,
        audio_duration_s=1.5,
        transcribed_at=_NOW,
    )
    assert result == "test"
