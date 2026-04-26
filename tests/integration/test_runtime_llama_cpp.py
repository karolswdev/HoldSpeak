"""Integration: end-to-end classify against a real Qwen GGUF.

Skipped cleanly when `llama-cpp-python` is not installed or the
default model file is not present. Per spec §13 risk #7, models are
downloaded manually.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.plugins.dictation.grammars import (
    BlockSet,
    BlockSpec,
    StructuredOutputSchema,
)


pytestmark = pytest.mark.requires_llama_cpp


DEFAULT_MODEL = Path(
    "~/Models/gguf/Qwen2.5-3B-Instruct-Q4_K_M.gguf"
).expanduser()


def _have_model() -> bool:
    try:
        import llama_cpp  # noqa: F401  type: ignore[import-not-found]
    except Exception:
        return False
    return DEFAULT_MODEL.exists()


@pytest.mark.skipif(
    not _have_model(),
    reason=(
        "llama-cpp-python and "
        f"{DEFAULT_MODEL} are required for this integration test"
    ),
)
def test_llama_cpp_runtime_classify_returns_valid_json():
    from holdspeak.plugins.dictation.runtime_llama_cpp import LlamaCppRuntime

    schema = StructuredOutputSchema.from_block_set(
        BlockSet(
            blocks=(
                BlockSpec(
                    id="ai_prompt_buildout",
                    extras_schema={"stage": ("buildout", "refinement")},
                ),
                BlockSpec(id="documentation_exercise"),
            )
        )
    )
    rt = LlamaCppRuntime(
        model_path=str(DEFAULT_MODEL),
        n_ctx=2048,
    )
    result = rt.classify(
        "Classify this utterance: 'Claude, build me a function that...'",
        schema,
    )
    # GBNF guarantees structural validity.
    assert isinstance(result, dict)
    assert result["block_id"] in schema.block_ids
    json.dumps(result)  # idempotent serialization sanity check
