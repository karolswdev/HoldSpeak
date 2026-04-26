"""Unit tests for the built-in `kb-enricher` stage (HS-1-06)."""

from __future__ import annotations

import inspect
from datetime import datetime, timezone

import pytest

from holdspeak.plugins.dictation.blocks import (
    Block,
    InjectMode,
    InjectSpec,
    LoadedBlocks,
    MatchSpec,
)
from holdspeak.plugins.dictation.builtin.kb_enricher import KbEnricher
from holdspeak.plugins.dictation.contracts import (
    IntentTag,
    StageResult,
    Transducer,
    Utterance,
)


def _utt(text: str = "hello world", project: dict | None = None) -> Utterance:
    return Utterance(
        raw_text=text,
        audio_duration_s=1.0,
        transcribed_at=datetime(2026, 4, 25, tzinfo=timezone.utc),
        project=project,
    )


def _make_blocks(
    *,
    template: str = "{raw_text}\n---\nproject: {project.name}",
    mode: InjectMode = InjectMode.APPEND,
    threshold: float | None = None,
    default_threshold: float = 0.6,
) -> LoadedBlocks:
    block = Block(
        id="ai_prompt_buildout",
        description="AI prompt buildout",
        match=MatchSpec(
            examples=("e",),
            extras_schema={"stage": ("buildout", "refinement")},
            threshold=threshold,
        ),
        inject=InjectSpec(mode=mode, template=template),
    )
    return LoadedBlocks(
        version=1,
        blocks=(block,),
        default_match_confidence=default_threshold,
        source_path=None,
    )


def _matched_tag(*, confidence: float = 0.9, extras: dict | None = None) -> IntentTag:
    return IntentTag(
        matched=True,
        block_id="ai_prompt_buildout",
        confidence=confidence,
        raw_label="ai_prompt_buildout",
        extras=extras or {},
    )


def _intent_result(tag: IntentTag, *, text: str = "hello world") -> StageResult:
    return StageResult(
        stage_id="intent-router",
        text=text,
        intent=tag,
        elapsed_ms=1.0,
    )


# ---------------------------------------------------------------------------
# Conformance + DIR-R-004
# ---------------------------------------------------------------------------


def test_kb_enricher_conforms_to_transducer_protocol():
    enricher = KbEnricher(_make_blocks())
    assert isinstance(enricher, Transducer)
    assert enricher.requires_llm is False


def test_kb_enricher_constructor_takes_no_runtime():
    """DIR-R-004: pure template substitution; no LLM injected."""
    sig = inspect.signature(KbEnricher.__init__)
    params = sig.parameters
    assert "runtime" not in params
    assert "llm" not in params


# ---------------------------------------------------------------------------
# Threshold gating (DIR-F-006)
# ---------------------------------------------------------------------------


def test_below_default_threshold_no_op():
    enricher = KbEnricher(_make_blocks(default_threshold=0.7))
    tag = _matched_tag(confidence=0.5)
    utt = _utt("hello world", project={"name": "holdspeak"})
    result = enricher.run(utt, prior=[_intent_result(tag, text=utt.raw_text)])

    assert result.text == "hello world"  # untouched
    assert result.metadata["reason"] == "below_threshold"
    assert result.metadata["threshold"] == 0.7


def test_per_block_threshold_overrides_default():
    enricher = KbEnricher(
        _make_blocks(default_threshold=0.4, threshold=0.95)
    )
    tag = _matched_tag(confidence=0.9)  # below per-block 0.95
    utt = _utt("hello world", project={"name": "holdspeak"})
    result = enricher.run(utt, prior=[_intent_result(tag, text=utt.raw_text)])

    assert result.metadata["reason"] == "below_threshold"
    assert result.metadata["threshold"] == 0.95


def test_at_or_above_threshold_applies_template():
    enricher = KbEnricher(_make_blocks(default_threshold=0.6))
    tag = _matched_tag(confidence=0.6)
    utt = _utt(project={"name": "holdspeak"})
    result = enricher.run(utt, prior=[_intent_result(tag)])

    assert "hello world" in result.text
    assert "project: holdspeak" in result.text


def test_no_intent_tag_no_op():
    enricher = KbEnricher(_make_blocks())
    utt = _utt(project={"name": "holdspeak"})
    result = enricher.run(utt, prior=[])

    assert result.text == "hello world"
    assert result.metadata["reason"] == "no_match"


def test_unmatched_intent_no_op():
    enricher = KbEnricher(_make_blocks())
    tag = IntentTag(
        matched=False,
        block_id=None,
        confidence=0.0,
        raw_label=None,
        extras={},
    )
    utt = _utt(project={"name": "holdspeak"})
    result = enricher.run(utt, prior=[_intent_result(tag)])

    assert result.text == "hello world"
    assert result.metadata["reason"] == "no_match"


def test_unknown_block_id_no_op():
    enricher = KbEnricher(_make_blocks())
    tag = IntentTag(
        matched=True,
        block_id="not_loaded",
        confidence=0.9,
        raw_label="not_loaded",
        extras={},
    )
    utt = _utt(project={"name": "holdspeak"})
    result = enricher.run(utt, prior=[_intent_result(tag)])

    assert result.text == "hello world"
    assert result.metadata["reason"] == "unknown_block"
    assert any("not_loaded" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Inject modes
# ---------------------------------------------------------------------------


def test_append_mode_concatenates_after():
    enricher = KbEnricher(
        _make_blocks(template="[ctx]", mode=InjectMode.APPEND)
    )
    result = enricher.run(
        _utt("hi"),
        prior=[_intent_result(_matched_tag(), text="hi")],
    )
    assert result.text == "hi[ctx]"


def test_prepend_mode_concatenates_before():
    enricher = KbEnricher(
        _make_blocks(template="[ctx]", mode=InjectMode.PREPEND)
    )
    result = enricher.run(
        _utt("hi"),
        prior=[_intent_result(_matched_tag(), text="hi")],
    )
    assert result.text == "[ctx]hi"


def test_replace_mode_overwrites_text():
    enricher = KbEnricher(
        _make_blocks(template="[only]", mode=InjectMode.REPLACE)
    )
    result = enricher.run(
        _utt("hi"),
        prior=[_intent_result(_matched_tag())],
    )
    assert result.text == "[only]"


# ---------------------------------------------------------------------------
# Template variable resolution
# ---------------------------------------------------------------------------


def test_extras_placeholder_resolves():
    enricher = KbEnricher(
        _make_blocks(
            template="stage={intent.extras.stage}",
            mode=InjectMode.REPLACE,
        )
    )
    tag = _matched_tag(extras={"stage": "buildout"})
    result = enricher.run(
        _utt("ignored"),
        prior=[_intent_result(tag)],
    )
    assert result.text == "stage=buildout"


def test_nested_project_kb_placeholder_resolves():
    enricher = KbEnricher(
        _make_blocks(
            template="{project.kb.stack}",
            mode=InjectMode.REPLACE,
        )
    )
    utt = _utt(
        project={
            "name": "holdspeak",
            "kb": {"stack": "python+react"},
        }
    )
    result = enricher.run(utt, prior=[_intent_result(_matched_tag())])
    assert result.text == "python+react"


# ---------------------------------------------------------------------------
# DIR-F-007: unresolved placeholders never get typed
# ---------------------------------------------------------------------------


def test_unresolved_placeholder_skips_injection():
    enricher = KbEnricher(
        _make_blocks(
            template="{raw_text} :: {project.kb.missing_field}",
        )
    )
    utt = _utt(
        "hi",
        project={"name": "holdspeak", "kb": {"stack": "py"}},
    )
    result = enricher.run(
        utt, prior=[_intent_result(_matched_tag(), text="hi")]
    )

    assert result.text == "hi"  # injection skipped
    assert "{" not in result.text
    assert any(
        "unresolved placeholder" in w and "missing_field" in w
        for w in result.warnings
    )
    assert result.metadata["reason"] == "unresolved_placeholder"


def test_unresolved_when_project_is_none():
    enricher = KbEnricher(
        _make_blocks(template="{project.name} :: {raw_text}")
    )
    utt = _utt("hi", project=None)
    result = enricher.run(
        utt, prior=[_intent_result(_matched_tag(), text="hi")]
    )

    assert result.text == "hi"
    assert "{" not in result.text
    assert result.metadata["reason"] == "unresolved_placeholder"


def test_no_unresolved_braces_ever_typed_smoke():
    """Property-style: any rendered text must not contain '{...}'."""
    templates = [
        "{raw_text}",
        "{project.name} :: {raw_text}",
        "{intent.extras.stage} :: {raw_text}",
    ]
    for t in templates:
        enricher = KbEnricher(_make_blocks(template=t, mode=InjectMode.REPLACE))
        utt = _utt(project={"name": "holdspeak"})
        tag = _matched_tag(extras={"stage": "buildout"})
        result = enricher.run(utt, prior=[_intent_result(tag)])
        # Either it injected fully (no braces), or it skipped (text preserved
        # — in which case the original was also brace-free).
        assert "{" not in result.text


# ---------------------------------------------------------------------------
# Threading: kb-enricher acts on the latest stage's text
# ---------------------------------------------------------------------------


def test_acts_on_latest_text_not_raw_text():
    """If a prior stage transformed the text, kb-enricher operates on
    that transformed text (the pipeline contract)."""
    enricher = KbEnricher(
        _make_blocks(template=":suffix", mode=InjectMode.APPEND)
    )
    upstream = StageResult(
        stage_id="upper",
        text="HELLO",
        intent=_matched_tag(),
        elapsed_ms=0.0,
    )
    result = enricher.run(_utt("hello"), prior=[upstream])

    assert result.text == "HELLO:suffix"


def test_extras_dict_round_trip():
    """Sanity: the extras dict survives pickling-by-coercion."""
    extras = {"stage": "buildout", "depth": "shallow"}
    tag = _matched_tag(extras=extras)
    enricher = KbEnricher(
        _make_blocks(
            template="{intent.extras.stage}/{intent.extras.depth}",
            mode=InjectMode.REPLACE,
        )
    )
    result = enricher.run(_utt("ignored"), prior=[_intent_result(tag)])
    assert result.text == "buildout/shallow"
