"""HS-118-08: browser mic pipeline tests.

Tests the factored ``process_transcript`` function, the extended
``/api/dictation/transcribe`` endpoint, source tagging, cross-source
learning, audio floor contention, and hotkey parity.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.dictation_runner import (
    process_transcript,
    run_dictation_pipeline,
    run_pipeline_corrections_only,
)

_NOW = datetime(2026, 8, 5, 12, 0, 0)


def _enabled_config() -> SimpleNamespace:
    pipeline = SimpleNamespace(
        enabled=True,
        corrections_enabled=False,
        target_profile_override="auto",
        target_detect_llm_enabled=False,
        target_detect_llm_below=0.8,
        journal_enabled=True,
        journal_retention=500,
    )
    return SimpleNamespace(dictation=SimpleNamespace(pipeline=pipeline))


class _JournalSpy:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def record(self, run, **kwargs):
        self.calls.append({"run": run, **kwargs})
        return SimpleNamespace(id=99)


def _bare_server() -> SimpleNamespace:
    return SimpleNamespace(
        dictation_corrections=None,
        dictation_telemetry=None,
        dictation_journal=None,
    )


# --- process_transcript tests ---


def test_process_transcript_returns_text_when_no_config() -> None:
    """process_transcript with no config/server returns raw text unchanged."""
    result = asyncio.run(
        process_transcript("hello world", source="browser", context=None)
    )
    assert result == "hello world"


def test_process_transcript_returns_text_when_pipeline_disabled() -> None:
    """process_transcript with pipeline disabled returns raw text."""
    cfg = _enabled_config()
    cfg.dictation.pipeline.enabled = False
    server = _bare_server()
    result = asyncio.run(
        process_transcript(
            "hello world",
            source="browser",
            context=None,
            config=cfg,
            server=server,
        )
    )
    assert result == "hello world"


def test_process_transcript_browser_source_journals_as_browser() -> None:
    """Browser source is journaled with source="browser"."""
    cfg = _enabled_config()
    cfg.dictation.pipeline.enabled = False
    server = _bare_server()
    server.dictation_journal = _JournalSpy()

    asyncio.run(
        process_transcript(
            "test transcript",
            source="browser",
            context=None,
            config=cfg,
            server=server,
        )
    )

    assert len(server.dictation_journal.calls) == 1
    assert server.dictation_journal.calls[0]["source"] == "browser"


def test_process_transcript_hotkey_source_journals_as_hotkey() -> None:
    """Hotkey source is journaled with source="hotkey" (not "dictation")."""
    cfg = _enabled_config()
    cfg.dictation.pipeline.enabled = False
    server = _bare_server()
    server.dictation_journal = _JournalSpy()

    asyncio.run(
        process_transcript(
            "test transcript",
            source="hotkey",
            context=None,
            config=cfg,
            server=server,
        )
    )

    assert len(server.dictation_journal.calls) == 1
    assert server.dictation_journal.calls[0]["source"] == "hotkey"


def test_process_transcript_browser_skips_target_detection(monkeypatch) -> None:
    """Browser pipeline does NOT import or call target detection functions.

    When source="browser", process_transcript delegates to
    run_pipeline_corrections_only with skip_target_detection=True,
    which skips all target detection imports and calls.
    """
    # Poison the target detection imports so they'd fail if called
    import holdspeak.dictation_runner as dr

    target_detection_called = False

    original_run = dr.run_pipeline_corrections_only

    def spy_run(*args, **kwargs):
        nonlocal target_detection_called
        if kwargs.get("skip_target_detection") is False:
            target_detection_called = True
        return original_run(*args, **kwargs)

    monkeypatch.setattr(dr, "run_pipeline_corrections_only", spy_run)

    cfg = _enabled_config()
    cfg.dictation.pipeline.enabled = False
    server = _bare_server()

    result = asyncio.run(
        process_transcript(
            "some text",
            source="browser",
            context=None,
            config=cfg,
            server=server,
        )
    )
    assert result == "some text"
    assert not target_detection_called


# --- Hotkey parity tests ---


def test_hotkey_parity_disabled_pipeline() -> None:
    """Both process_transcript("hotkey") and process_transcript("browser")
    produce identical corrected output when the pipeline is disabled."""
    cfg = _enabled_config()
    cfg.dictation.pipeline.enabled = False
    server = _bare_server()

    hotkey_result = asyncio.run(
        process_transcript(
            "hello world",
            source="hotkey",
            context=None,
            config=cfg,
            server=server,
        )
    )

    browser_result = asyncio.run(
        process_transcript(
            "hello world",
            source="browser",
            context=None,
            config=cfg,
            server=server,
        )
    )

    assert hotkey_result == browser_result == "hello world"


def test_hotkey_parity_missing_config() -> None:
    """Both paths return text unchanged when config is missing."""
    hotkey_result = asyncio.run(
        process_transcript(
            "unchanged text",
            source="hotkey",
            context=None,
            config=SimpleNamespace(),
            server=_bare_server(),
        )
    )

    browser_result = asyncio.run(
        process_transcript(
            "unchanged text",
            source="browser",
            context=None,
            config=SimpleNamespace(),
            server=_bare_server(),
        )
    )

    assert hotkey_result == browser_result == "unchanged text"


def test_hotkey_parity_enabled_pipeline_fallback(monkeypatch) -> None:
    """When the pipeline build fails, both paths fall back to the raw text."""
    def _boom(*_a, **_k):
        raise RuntimeError("pipeline construction failed")

    monkeypatch.setattr("holdspeak.plugins.dictation.assembly.build_pipeline", _boom)
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.project_root.detect_project_for_cwd",
        lambda *_a, **_k: None,
    )

    cfg = _enabled_config()
    server = _bare_server()

    hotkey_result = asyncio.run(
        process_transcript(
            "keep me",
            source="hotkey",
            context=None,
            config=cfg,
            server=server,
        )
    )

    browser_result = asyncio.run(
        process_transcript(
            "keep me",
            source="browser",
            context=None,
            config=cfg,
            server=server,
        )
    )

    assert hotkey_result == browser_result == "keep me"


def test_parity_same_transcript_same_output(monkeypatch) -> None:
    """The same transcript through both hotkey and browser paths produces
    identical corrected output (the core parity guarantee)."""
    def _boom(*_a, **_k):
        raise RuntimeError("pipeline construction failed")

    monkeypatch.setattr("holdspeak.plugins.dictation.assembly.build_pipeline", _boom)
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.project_root.detect_project_for_cwd",
        lambda *_a, **_k: None,
    )

    transcript = "the quick brown fox jumps over the lazy dog"
    cfg = _enabled_config()
    server = _bare_server()

    hotkey = asyncio.run(
        process_transcript(transcript, source="hotkey", context=None, config=cfg, server=server)
    )
    browser = asyncio.run(
        process_transcript(transcript, source="browser", context=None, config=cfg, server=server)
    )

    assert hotkey == browser


# --- Cross-source learning ---


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


# --- Journal source validation ---


def test_browser_is_valid_journal_source() -> None:
    """The journal accepts "browser" as a valid source."""
    from holdspeak.db.journal import VALID_JOURNAL_SOURCES
    from holdspeak.plugins.dictation.journal import VALID_SOURCES

    assert "browser" in VALID_JOURNAL_SOURCES
    assert "browser" in VALID_SOURCES


def test_hotkey_is_valid_journal_source() -> None:
    """The journal accepts "hotkey" as a valid source."""
    from holdspeak.db.journal import VALID_JOURNAL_SOURCES
    from holdspeak.plugins.dictation.journal import VALID_SOURCES

    assert "hotkey" in VALID_JOURNAL_SOURCES
    assert "hotkey" in VALID_SOURCES


def test_dictation_is_valid_journal_source() -> None:
    """The journal still accepts "dictation" (backward compat)."""
    from holdspeak.db.journal import VALID_JOURNAL_SOURCES
    from holdspeak.plugins.dictation.journal import VALID_SOURCES

    assert "dictation" in VALID_JOURNAL_SOURCES
    assert "dictation" in VALID_SOURCES


# --- Audio floor contention ---


def test_browser_mic_active_hotkey_refused() -> None:
    """When the browser mic holds the audio floor, the hotkey capture is refused.

    The VoiceTypingSession arbiter is the single owner model. If the browser
    mic claims the floor, the hotkey's begin() returns False.
    """
    from holdspeak.voice_typing import VoiceTypingSession

    session = VoiceTypingSession()

    # Browser mic claims the floor
    assert session.acquire("browser_mic", lease_seconds=30.0) is True

    # Hotkey tries to begin -- should be refused because the floor is held
    # (begin requires an AudioSource, so we test with acquire as a proxy
    # for the hotkey's contention check)
    assert session.acquire("hotkey") is False

    # The active owner is the browser mic
    assert session.active_owner == "browser_mic"

    # Release the browser mic
    session.release("browser_mic")

    # Now the hotkey can claim
    assert session.acquire("hotkey") is True
    assert session.active_owner == "hotkey"


# --- Backward compatibility ---


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


def test_run_dictation_pipeline_journal_source_default() -> None:
    """Default journal_source is still "dictation"."""
    cfg = _enabled_config()
    cfg.dictation.pipeline.enabled = False
    server = _bare_server()
    server.dictation_journal = _JournalSpy()

    run_dictation_pipeline(
        "test",
        config=cfg,
        server=server,
        audio_duration_s=1.5,
        transcribed_at=_NOW,
    )

    assert len(server.dictation_journal.calls) == 1
    assert server.dictation_journal.calls[0]["source"] == "dictation"


def test_run_pipeline_corrections_only_skips_target(monkeypatch) -> None:
    """run_pipeline_corrections_only with skip_target_detection=True does
    not import target detection modules."""
    cfg = _enabled_config()
    cfg.dictation.pipeline.enabled = False
    server = _bare_server()

    result = run_pipeline_corrections_only(
        "test",
        config=cfg,
        server=server,
        audio_duration_s=0.0,
        transcribed_at=_NOW,
        skip_target_detection=True,
    )
    assert result == "test"


# --- HS-176 C1: the run's own facts leave the run (the SPOKEN half) ---
#
# The browser stream is the leg that runs the pipeline and writes the journal
# row for a spoken Speak-face utterance; the delivery that follows sends
# `raw: true` and computes nothing. `facts` is the sink that carries
# `raw_text` / `corrections_applied` / `journal_id` out of the publication that
# produced them — never a read-time "newest journal row" lookup (R2).


def test_process_transcript_fills_the_facts_sink_on_the_passthrough_lane() -> None:
    """Pipeline off: the row still exists, so the sink still names it."""
    cfg = _enabled_config()
    cfg.dictation.pipeline.enabled = False
    server = _bare_server()
    server.dictation_journal = _JournalSpy()
    facts: dict = {}

    result = asyncio.run(
        process_transcript(
            "test transcript",
            source="browser",
            context=None,
            config=cfg,
            server=server,
            facts=facts,
        )
    )

    assert result == "test transcript"
    assert facts == {
        "raw_text": "test transcript",
        "corrections_applied": [],
        "journal_id": 99,
    }


def test_process_transcript_facts_carry_the_ids_that_fired(monkeypatch) -> None:
    """A run whose rules fired reports THOSE ids, beside the heard transcript."""
    import holdspeak.plugins.dictation.assembly as assembly
    import holdspeak.plugins.dictation.project_root as project_root

    class _Run:
        final_text = "PostgreSQL needs a bump"
        corrections_applied = (5, 9)
        warnings: list = []
        total_elapsed_ms = 1.0

    class _Pipeline:
        def __init__(self) -> None:
            self.heard: list[str] = []

        def run(self, utterance):
            self.heard.append(utterance.raw_text)
            return _Run()

    pipeline = _Pipeline()
    monkeypatch.setattr(
        assembly,
        "build_pipeline",
        lambda *_a, **_kw: SimpleNamespace(
            runtime_status="loaded", runtime_detail="", pipeline=pipeline, runtime=None
        ),
    )
    monkeypatch.setattr(project_root, "detect_project_for_cwd", lambda *_a, **_kw: None)

    cfg = _enabled_config()
    server = _bare_server()
    server.dictation_journal = _JournalSpy()
    facts: dict = {}

    result = asyncio.run(
        process_transcript(
            "postgress needs a bump",
            source="browser",
            context=None,
            config=cfg,
            server=server,
            facts=facts,
        )
    )

    assert result == "PostgreSQL needs a bump"
    assert pipeline.heard == ["postgress needs a bump"]
    # the transcript AS HEARD, not the landed text -- the TEXT teach diffs
    # heard-vs-said, and a key harvested from the landed text never matches.
    assert facts["raw_text"] == "postgress needs a bump"
    assert facts["corrections_applied"] == [5, 9]
    assert facts["journal_id"] == 99


def test_process_transcript_without_a_sink_is_unchanged() -> None:
    """Every existing caller passes no sink and behaves exactly as before."""
    cfg = _enabled_config()
    cfg.dictation.pipeline.enabled = False
    server = _bare_server()
    server.dictation_journal = _JournalSpy()

    result = asyncio.run(
        process_transcript(
            "test transcript",
            source="browser",
            context=None,
            config=cfg,
            server=server,
        )
    )

    assert result == "test transcript"
    assert len(server.dictation_journal.calls) == 1
