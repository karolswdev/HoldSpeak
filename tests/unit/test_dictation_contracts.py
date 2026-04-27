"""Unit tests for DIR-01 dictation contracts (HS-1-02)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from holdspeak.plugins.dictation.contracts import (
    IntentTag,
    StageResult,
    Transducer,
    Utterance,
)


def test_utterance_construction_and_immutability():
    ts = datetime(2026, 4, 25, tzinfo=timezone.utc)
    utt = Utterance(
        raw_text="hello world",
        audio_duration_s=1.25,
        transcribed_at=ts,
        project={"name": "holdspeak"},
    )
    assert utt.raw_text == "hello world"
    assert utt.audio_duration_s == 1.25
    assert utt.transcribed_at == ts
    assert utt.project == {"name": "holdspeak"}
    assert utt.activity == {}

    with pytest.raises(FrozenInstanceError):
        utt.raw_text = "mutated"  # type: ignore[misc]


def test_intent_tag_defaults_and_immutability():
    tag = IntentTag(
        matched=True,
        block_id="ai_prompt_buildout",
        confidence=0.87,
        raw_label="ai_prompt_buildout",
    )
    assert tag.matched is True
    assert tag.block_id == "ai_prompt_buildout"
    assert tag.confidence == 0.87
    assert tag.extras == {}

    with pytest.raises(FrozenInstanceError):
        tag.confidence = 0.0  # type: ignore[misc]


def test_stage_result_defaults_and_immutability():
    res = StageResult(
        stage_id="intent-router",
        text="hello world",
        intent=None,
        elapsed_ms=42.0,
    )
    assert res.warnings == []
    assert res.metadata == {}
    assert res.intent is None

    with pytest.raises(FrozenInstanceError):
        res.text = "x"  # type: ignore[misc]


class _StubTransducer:
    id = "stub"
    version = "0.1.0"
    requires_llm = False

    def run(self, utt: Utterance, prior: list[StageResult]) -> StageResult:
        return StageResult(
            stage_id=self.id,
            text=utt.raw_text,
            intent=None,
            elapsed_ms=0.0,
        )


class _NotATransducer:
    id = "missing-run"
    version = "0.1.0"
    requires_llm = False


def test_transducer_protocol_conformance():
    stub = _StubTransducer()
    assert isinstance(stub, Transducer)

    bad = _NotATransducer()
    assert not isinstance(bad, Transducer)


def test_transducer_run_smoke():
    stub = _StubTransducer()
    utt = Utterance(
        raw_text="testing",
        audio_duration_s=0.5,
        transcribed_at=datetime(2026, 4, 25, tzinfo=timezone.utc),
    )
    res = stub.run(utt, prior=[])
    assert res.stage_id == "stub"
    assert res.text == "testing"
    assert res.intent is None
