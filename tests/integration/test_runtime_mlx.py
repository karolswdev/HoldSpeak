"""Integration: end-to-end classify against a real Qwen3-8B-MLX-4bit.

Skipped cleanly when `mlx-lm` / `outlines` are not installed or the
snapshot is not present. Per spec §13 risk #7, models are downloaded
manually.
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


pytestmark = pytest.mark.requires_mlx


DEFAULT_MODEL = Path("~/Models/mlx/Qwen3-8B-MLX-4bit").expanduser()


def _have_stack() -> bool:
    try:
        import mlx_lm  # noqa: F401  type: ignore[import-not-found]
        from outlines.processors import JSONLogitsProcessor  # noqa: F401  type: ignore[import-not-found]
    except Exception:
        return False
    return DEFAULT_MODEL.exists()


@pytest.mark.skipif(
    not _have_stack(),
    reason=(
        "mlx-lm + outlines + "
        f"{DEFAULT_MODEL} are required for this integration test"
    ),
)
def test_mlx_runtime_classify_returns_valid_json():
    from holdspeak.plugins.dictation.runtime_mlx import MlxRuntime

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
    rt = MlxRuntime(model=str(DEFAULT_MODEL))
    result = rt.classify(
        "Classify this utterance: 'Claude, build me a function that...'",
        schema,
    )
    assert isinstance(result, dict)
    assert result["block_id"] in schema.block_ids
    json.dumps(result)
