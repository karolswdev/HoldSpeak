"""Tests for shared dictation pipeline assembly."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from holdspeak.config import DictationConfig
from holdspeak.plugins.dictation.assembly import build_pipeline


class _Runtime:
    backend = "fake"

    def load(self) -> None:
        pass

    def info(self) -> dict[str, Any]:
        return {"backend": "fake"}

    def classify(self, prompt, schema, *, max_tokens=128, temperature=0.0):
        return {
            "matched": False,
            "block_id": schema.block_ids[0],
            "confidence": 0.0,
            "extras": {},
        }

    def rewrite(self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.15) -> str:
        return "rewritten"


def test_build_pipeline_respects_configured_stage_order(tmp_path: Path) -> None:
    cfg = DictationConfig()
    cfg.pipeline.stages = ["intent-router", "project-rewriter", "kb-enricher"]

    result = build_pipeline(
        cfg,
        project_root=tmp_path,
        global_blocks_path=tmp_path / "missing-blocks.yaml",
        runtime_factory=lambda **_kwargs: _Runtime(),
    )

    assert [stage.id for stage in result.pipeline._stages] == [  # type: ignore[attr-defined]
        "intent-router",
        "project-rewriter",
        "kb-enricher",
    ]


def test_build_pipeline_keeps_rewriter_opt_in_by_default(tmp_path: Path) -> None:
    cfg = DictationConfig()

    result = build_pipeline(
        cfg,
        project_root=tmp_path,
        global_blocks_path=tmp_path / "missing-blocks.yaml",
        runtime_factory=lambda **_kwargs: _Runtime(),
    )

    assert [stage.id for stage in result.pipeline._stages] == [  # type: ignore[attr-defined]
        "intent-router",
        "kb-enricher",
    ]
