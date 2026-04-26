"""Unit tests for the DIR-01 schema compiler (HS-1-04)."""

from __future__ import annotations

import json
import re

import pytest

from holdspeak.plugins.dictation.grammars import (
    BlockSet,
    BlockSpec,
    GrammarCompileError,
    StructuredOutputSchema,
    equivalent_value_sets,
    to_gbnf,
    to_outlines,
    to_outlines_json,
)


def _fixture_blockset() -> BlockSet:
    return BlockSet(
        blocks=(
            BlockSpec(
                id="ai_prompt_buildout",
                extras_schema={"stage": ("buildout", "refinement", "debugging")},
            ),
            BlockSpec(id="documentation_exercise"),
        ),
        default_match_confidence=0.6,
    )


def _fixture_schema() -> StructuredOutputSchema:
    return StructuredOutputSchema.from_block_set(_fixture_blockset())


def test_structured_output_schema_from_block_set_round_trip():
    schema = _fixture_schema()
    assert schema.block_ids == ("ai_prompt_buildout", "documentation_exercise")
    assert schema.extras_per_block["ai_prompt_buildout"]["stage"] == (
        "buildout",
        "refinement",
        "debugging",
    )
    assert schema.extras_per_block["documentation_exercise"] == {}


def test_block_set_rejects_empty():
    with pytest.raises(GrammarCompileError, match="at least one block"):
        StructuredOutputSchema.from_block_set(BlockSet(blocks=()))


def test_block_set_rejects_invalid_block_id():
    bs = BlockSet(blocks=(BlockSpec(id="Bad-Id"),))
    with pytest.raises(GrammarCompileError, match="block_id"):
        StructuredOutputSchema.from_block_set(bs)


def test_block_set_rejects_duplicate_block_ids():
    bs = BlockSet(
        blocks=(
            BlockSpec(id="dup"),
            BlockSpec(id="dup"),
        )
    )
    with pytest.raises(GrammarCompileError, match="duplicate"):
        StructuredOutputSchema.from_block_set(bs)


def test_block_set_rejects_empty_extras_enum():
    bs = BlockSet(blocks=(BlockSpec(id="b", extras_schema={"k": ()}),))
    with pytest.raises(GrammarCompileError, match="at least one value"):
        StructuredOutputSchema.from_block_set(bs)


def test_to_gbnf_contains_all_block_ids():
    schema = _fixture_schema()
    gbnf = to_gbnf(schema)
    # Block ids and JSON keys appear as escaped JSON-literal terminals
    # ("\"name\"") so the grammar emits real JSON.
    assert '\\"ai_prompt_buildout\\"' in gbnf
    assert '\\"documentation_exercise\\"' in gbnf
    for k in ("matched", "block_id", "confidence", "extras"):
        assert f'\\"{k}\\"' in gbnf


def test_to_gbnf_validates_with_llama_grammar_when_available():
    """If llama-cpp-python is installed, the GBNF must compile cleanly."""
    pytest.importorskip("llama_cpp")
    from llama_cpp import LlamaGrammar  # type: ignore[import-not-found]

    gbnf = to_gbnf(_fixture_schema())
    # Should not raise.
    LlamaGrammar.from_string(gbnf)


def test_to_outlines_emits_oneof_per_block():
    schema = _fixture_schema()
    artifact = to_outlines(schema)
    assert "oneOf" in artifact
    assert len(artifact["oneOf"]) == 2

    # block_id is constrained per branch via const.
    consts = sorted(b["properties"]["block_id"]["const"] for b in artifact["oneOf"])
    assert consts == ["ai_prompt_buildout", "documentation_exercise"]

    # Extras for ai_prompt_buildout.
    by_const = {b["properties"]["block_id"]["const"]: b for b in artifact["oneOf"]}
    extras = by_const["ai_prompt_buildout"]["properties"]["extras"]
    assert extras["properties"]["stage"]["enum"] == [
        "buildout",
        "refinement",
        "debugging",
    ]


def test_to_outlines_json_is_valid_json_and_round_trips():
    raw = to_outlines_json(_fixture_schema())
    assert json.loads(raw) == to_outlines(_fixture_schema())


def test_cross_backend_equivalence_value_sets_match():
    schema = _fixture_schema()
    expected = equivalent_value_sets(schema)

    gbnf = to_gbnf(schema)
    # Block ids appear as escaped JSON-string literals in the GBNF
    # (e.g. \"ai_prompt_buildout\"); strip the leading backslashes for the
    # equivalence check.
    found_ids_gbnf = set(re.findall(r'\\"([a-z][a-z0-9_]*)\\"', gbnf))
    for bid in expected["block_ids"]:
        assert bid in found_ids_gbnf

    artifact = to_outlines(schema)
    found_ids_outlines = {b["properties"]["block_id"]["const"] for b in artifact["oneOf"]}
    assert found_ids_outlines == set(expected["block_ids"])

    # Extras enum domains must be identical between the two emitters.
    by_const = {b["properties"]["block_id"]["const"]: b for b in artifact["oneOf"]}
    for bid, keys in expected["extras_per_block"].items():
        outlines_extras = by_const[bid]["properties"]["extras"]["properties"]
        for k, values in keys.items():
            assert tuple(outlines_extras[k]["enum"]) == values
            for v in values:
                assert f'\\"{v}\\"' in gbnf
