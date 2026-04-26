"""Integration tests for HS-3-05: DIR-R-003 cold-start hard-cap.

Verifies the wrapper-level cap behaves correctly inside the full
DictationPipeline:

1. A cold-start cap breach disables the LLM stage for the session
   AND the pipeline keeps running (intent-router fall back to
   no-match, kb-enricher passes through).
2. The doctor counter check surfaces `llm_disabled_for_session=True`
   after a breach.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from holdspeak.config import Config
from holdspeak.plugins.dictation.contracts import Utterance


class _SlowStubRuntime:
    """LLMRuntime-shaped stub that sleeps inside classify to trip the cap."""

    backend = "stub"

    def __init__(self, sleep_s: float) -> None:
        self._sleep_s = sleep_s
        self.classify_calls = 0

    def load(self) -> None:
        pass

    def info(self) -> dict[str, Any]:
        return {"backend": self.backend, "loaded": True}

    def classify(self, prompt, schema, *, max_tokens=128, temperature=0.0):
        self.classify_calls += 1
        time.sleep(self._sleep_s)
        return {"block_id": None, "confidence": 0.0}


@pytest.fixture(autouse=True)
def _reset_counters() -> None:
    from holdspeak.plugins.dictation.runtime_counters import reset_counters
    reset_counters()
    yield
    reset_counters()


def test_pipeline_runs_after_cold_start_breach_without_raising(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """First utterance trips the cap → wrapper disabled. Second utterance
    falls through to no-match cleanly. Pipeline never raises."""
    from holdspeak.plugins.dictation.assembly import build_pipeline
    from holdspeak.plugins.dictation.runtime_counters import (
        CountingRuntime,
        get_session_status,
    )

    monkeypatch.setenv("HOME", str(tmp_path))

    cfg = Config()
    cfg.dictation.pipeline.enabled = True
    # Cap = max_total_latency_ms × 5 = 1 ms × 5 = 5 ms; stub sleeps 50 ms.
    cfg.dictation.pipeline.max_total_latency_ms = 1
    cfg.dictation.runtime.warm_on_start = False

    # IntentRouter only invokes classify when at least one block is
    # loaded. Seed a minimal one so the runtime actually runs.
    blocks_path = tmp_path / "blocks.yaml"
    blocks_path.write_text(
        "version: 1\n"
        "default_match_confidence: 0.5\n"
        "blocks:\n"
        "  - id: testing\n"
        "    description: test block\n"
        "    match:\n"
        "      examples:\n"
        "        - 'sample'\n"
        "    inject:\n"
        "      mode: replace\n"
        "      template: '{raw_text}'\n",
        encoding="utf-8",
    )

    slow_inner = _SlowStubRuntime(sleep_s=0.05)

    def _runtime_factory(**kwargs: Any) -> CountingRuntime:
        return CountingRuntime(
            slow_inner,
            warm_on_start=kwargs.get("warm_on_start", False),
            cold_start_cap_ms=kwargs.get("cold_start_cap_ms"),
        )

    result = build_pipeline(
        cfg.dictation,
        global_blocks_path=blocks_path,
        runtime_factory=_runtime_factory,
    )
    assert result.runtime_status == "loaded"

    utt1 = Utterance(
        raw_text="first utterance triggers cold-start",
        audio_duration_s=1.0,
        transcribed_at=datetime.now(),
    )
    run1 = result.pipeline.run(utt1)

    # Pipeline did not raise; intent-router warned about the failure
    # and fell through to a no-match.
    assert isinstance(run1.final_text, str)
    # Session is now disabled.
    assert get_session_status()["llm_disabled_for_session"] is True

    # Subsequent utterance: short-circuit, never invokes inner runtime
    # for the second time (the wrapper raises LLMRuntimeDisabledError
    # immediately; the IntentRouter's existing exception handler
    # treats it as a no-match warning).
    inner_calls_after_first = slow_inner.classify_calls
    utt2 = Utterance(
        raw_text="second utterance",
        audio_duration_s=1.0,
        transcribed_at=datetime.now(),
    )
    run2 = result.pipeline.run(utt2)

    assert isinstance(run2.final_text, str)
    # Inner runtime was not invoked again on utt2 (wrapper short-circuits).
    assert slow_inner.classify_calls == inner_calls_after_first


def test_doctor_counters_warn_after_cold_start_breach(monkeypatch) -> None:
    """`holdspeak doctor` reports WARN when the session is disabled."""
    from holdspeak.commands import doctor
    from holdspeak.plugins.dictation.runtime_counters import _set_session_disabled

    cfg = Config()
    cfg.dictation.pipeline.enabled = True

    _set_session_disabled("cold-start exceeded cap: 50ms > 5ms; LLM stage disabled")

    result = doctor._check_dictation_runtime_counters(cfg)
    assert result.status == "WARN"
    assert "llm_disabled_for_session=True" in result.detail
    assert "cold-start exceeded cap" in result.detail
    assert result.fix and "Restart" in result.fix
