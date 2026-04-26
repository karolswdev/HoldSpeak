"""Unit tests for the built-in `intent-router` stage (HS-1-06)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from holdspeak.plugins.dictation.blocks import (
    Block,
    InjectMode,
    InjectSpec,
    LoadedBlocks,
    MatchSpec,
)
from holdspeak.plugins.dictation.builtin.intent_router import IntentRouter
from holdspeak.plugins.dictation.contracts import (
    Transducer,
    Utterance,
)


def _utt(text: str = "Claude, build a function that...") -> Utterance:
    return Utterance(
        raw_text=text,
        audio_duration_s=1.0,
        transcribed_at=datetime(2026, 4, 25, tzinfo=timezone.utc),
    )


def _blocks(
    *,
    extras: dict[str, tuple[str, ...]] | None = None,
    second_block: bool = True,
) -> LoadedBlocks:
    blocks = [
        Block(
            id="ai_prompt_buildout",
            description="AI prompt buildout phase",
            match=MatchSpec(
                examples=("Claude, build a function that...",),
                negative_examples=("What time is it",),
                extras_schema=extras,
            ),
            inject=InjectSpec(mode=InjectMode.APPEND, template="{raw_text}"),
        )
    ]
    if second_block:
        blocks.append(
            Block(
                id="documentation_exercise",
                description="Documenting code or systems",
                match=MatchSpec(examples=("This module is responsible for...",)),
                inject=InjectSpec(mode=InjectMode.APPEND, template="{raw_text}"),
            )
        )
    return LoadedBlocks(
        version=1,
        blocks=tuple(blocks),
        default_match_confidence=0.6,
        source_path=None,
    )


class _FakeRuntime:
    backend = "fake"

    def __init__(self, *, returns: list[Any] | None = None) -> None:
        self._returns = list(returns or [])
        self.calls: list[dict[str, Any]] = []

    def load(self) -> None: ...

    def info(self) -> dict[str, Any]:
        return {"backend": self.backend}

    def classify(self, prompt: str, schema: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"prompt": prompt, "schema": schema, **kwargs})
        if not self._returns:
            raise AssertionError("FakeRuntime: no more queued returns")
        nxt = self._returns.pop(0)
        if isinstance(nxt, BaseException):
            raise nxt
        return nxt


def test_intent_router_conforms_to_transducer_protocol():
    rt = _FakeRuntime(returns=[{"matched": False, "block_id": None, "confidence": 0.0, "extras": {}}])
    router = IntentRouter(rt, _blocks())
    assert isinstance(router, Transducer)
    assert router.requires_llm is True


def test_happy_path_returns_intent_tag():
    rt = _FakeRuntime(
        returns=[
            {
                "matched": True,
                "block_id": "ai_prompt_buildout",
                "confidence": 0.87,
                "extras": {"stage": "buildout"},
            }
        ]
    )
    router = IntentRouter(rt, _blocks(extras={"stage": ("buildout",)}))
    result = router.run(_utt(), prior=[])

    assert result.stage_id == "intent-router"
    assert result.text == _utt().raw_text  # router does not transform text
    assert result.intent is not None
    assert result.intent.matched is True
    assert result.intent.block_id == "ai_prompt_buildout"
    assert result.intent.confidence == 0.87
    assert result.intent.extras == {"stage": "buildout"}
    assert result.warnings == []
    # DIR-F-005: scored against the full taxonomy union.
    assert result.metadata["taxonomy_size"] == 2


def test_no_match_response_is_normalized():
    rt = _FakeRuntime(
        returns=[
            {
                "matched": False,
                "block_id": None,
                "confidence": 0.42,  # ignored when matched=false
                "extras": {},
            }
        ]
    )
    router = IntentRouter(rt, _blocks())
    result = router.run(_utt(), prior=[])

    assert result.intent is not None
    assert result.intent.matched is False
    assert result.intent.block_id is None
    assert result.intent.confidence == 0.0


def test_unknown_block_id_triggers_retry_then_no_match(caplog):
    rt = _FakeRuntime(
        returns=[
            {"matched": True, "block_id": "not_a_real_block", "confidence": 0.9, "extras": {}},
            {"matched": True, "block_id": "still_bogus", "confidence": 0.8, "extras": {}},
        ]
    )
    router = IntentRouter(rt, _blocks())
    result = router.run(_utt(), prior=[])

    assert len(rt.calls) == 2
    assert result.intent is not None
    assert result.intent.matched is False
    assert result.intent.confidence == 0.0
    assert any("attempt 1 failed" in w for w in result.warnings)
    assert any("attempt 2 failed" in w for w in result.warnings)
    assert any("retries exhausted" in w for w in result.warnings)


def test_retry_recovers_on_second_attempt():
    rt = _FakeRuntime(
        returns=[
            RuntimeError("transient model error"),
            {
                "matched": True,
                "block_id": "ai_prompt_buildout",
                "confidence": 0.7,
                "extras": {},
            },
        ]
    )
    router = IntentRouter(rt, _blocks())
    result = router.run(_utt(), prior=[])

    assert result.intent is not None
    assert result.intent.matched is True
    assert result.intent.block_id == "ai_prompt_buildout"
    assert any("attempt 1 failed" in w for w in result.warnings)
    # No "retries exhausted" message — we recovered.
    assert not any("retries exhausted" in w for w in result.warnings)


def test_runtime_exceptions_never_propagate():
    rt = _FakeRuntime(
        returns=[RuntimeError("model dead"), RuntimeError("still dead")]
    )
    router = IntentRouter(rt, _blocks())
    result = router.run(_utt(), prior=[])

    # Stage's contract: never raise; always return a StageResult.
    assert result.intent is not None
    assert result.intent.matched is False


def test_invalid_confidence_triggers_retry():
    rt = _FakeRuntime(
        returns=[
            {"matched": True, "block_id": "ai_prompt_buildout", "confidence": 1.5, "extras": {}},
            {"matched": True, "block_id": "ai_prompt_buildout", "confidence": 0.5, "extras": {}},
        ]
    )
    router = IntentRouter(rt, _blocks())
    result = router.run(_utt(), prior=[])

    assert len(rt.calls) == 2
    assert result.intent is not None
    assert result.intent.confidence == 0.5


def test_non_dict_response_triggers_retry():
    rt = _FakeRuntime(returns=["just a string", "still a string"])
    router = IntentRouter(rt, _blocks())
    result = router.run(_utt(), prior=[])
    assert result.intent is not None
    assert result.intent.matched is False
    assert len(rt.calls) == 2


def test_empty_blockset_short_circuits_without_runtime_call():
    rt = _FakeRuntime(returns=[])  # no queued returns
    empty_blocks = LoadedBlocks(
        version=1,
        blocks=(),
        default_match_confidence=0.6,
        source_path=None,
    )
    router = IntentRouter(rt, empty_blocks)
    result = router.run(_utt(), prior=[])

    assert result.intent is not None
    assert result.intent.matched is False
    assert rt.calls == []
    assert result.metadata.get("reason") == "empty_blockset"


def test_prompt_includes_block_descriptions_and_examples():
    rt = _FakeRuntime(
        returns=[{"matched": False, "block_id": None, "confidence": 0.0, "extras": {}}]
    )
    router = IntentRouter(
        rt,
        _blocks(extras={"stage": ("buildout", "refinement")}),
    )
    router.run(_utt("hello"), prior=[])
    prompt = rt.calls[0]["prompt"]
    assert "ai_prompt_buildout" in prompt
    assert "documentation_exercise" in prompt
    assert "Claude, build a function" in prompt
    assert "What time is it" in prompt
    # Extras schema surfaced.
    assert "extras.stage" in prompt
    # Utterance present.
    assert "hello" in prompt


def test_custom_prompt_builder_is_used():
    rt = _FakeRuntime(
        returns=[{"matched": False, "block_id": None, "confidence": 0.0, "extras": {}}]
    )
    seen: dict[str, Any] = {}

    def builder(blocks: LoadedBlocks, utt: Utterance) -> str:
        seen["called"] = True
        return f"CUSTOM::{utt.raw_text}"

    router = IntentRouter(rt, _blocks(), prompt_builder=builder)
    router.run(_utt("ping"), prior=[])

    assert seen.get("called") is True
    assert rt.calls[0]["prompt"] == "CUSTOM::ping"
