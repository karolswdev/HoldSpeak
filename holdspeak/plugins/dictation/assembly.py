"""Shared DIR-01 dictation pipeline assembly (HS-1-08).

Single source of truth for "build a `DictationPipeline` from
`Config.dictation`". Used by both the live controller path
(HS-1-07) and the `holdspeak dictation` CLI (HS-1-08); doctor
checks (HS-1-09) call into the same primitives.

When the runtime backend cannot be loaded (no extras installed,
model file missing, unknown backend), `build_pipeline` returns a
pipeline with `llm_enabled=False` so callers can still exercise
the non-LLM stages (DIR-F-011 — `intent-router` is skipped, not
errored). The `BuildResult.runtime_status` field tells the caller
what happened so it can report appropriately.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Optional

from holdspeak.config import DictationConfig
from holdspeak.plugins.dictation.blocks import LoadedBlocks, resolve_blocks
from holdspeak.plugins.dictation.builtin.intent_router import IntentRouter
from holdspeak.plugins.dictation.builtin.kb_enricher import KbEnricher
from holdspeak.plugins.dictation.pipeline import DictationPipeline, PipelineRun
from holdspeak.plugins.dictation.runtime import (
    LLMRuntime,
    RuntimeUnavailableError,
    build_runtime,
)

DEFAULT_GLOBAL_BLOCKS_PATH = Path.home() / ".config" / "holdspeak" / "blocks.yaml"

RuntimeStatus = Literal["loaded", "unavailable", "disabled"]


@dataclass(frozen=True)
class BuildResult:
    """Outcome of `build_pipeline`. Lets callers report what happened."""

    pipeline: DictationPipeline
    blocks: LoadedBlocks
    runtime_status: RuntimeStatus
    runtime_detail: str


def build_pipeline(
    cfg: DictationConfig,
    *,
    on_run: Callable[[PipelineRun], None] | None = None,
    project_root: Path | None = None,
    global_blocks_path: Path | None = None,
    runtime_factory: Callable[..., LLMRuntime] | None = None,
) -> BuildResult:
    """Resolve blocks + runtime, return a wired `DictationPipeline`.

    `runtime_factory` is a test/CLI seam — production callers leave
    it `None` and get the real `runtime.build_runtime` factory. When
    the factory raises `RuntimeUnavailableError` (or anything else),
    the pipeline still ships, but with `llm_enabled=False` so the
    `intent-router` stage is skipped per HS-1-03.
    """
    blocks_path = global_blocks_path if global_blocks_path is not None else DEFAULT_GLOBAL_BLOCKS_PATH
    blocks = resolve_blocks(blocks_path, project_root)

    runtime, runtime_status, runtime_detail = _try_build_runtime(cfg, runtime_factory)
    llm_enabled = runtime is not None

    stages: list[Any] = []
    if runtime is not None:
        stages.append(IntentRouter(runtime, blocks))
    stages.append(KbEnricher(blocks))

    pipeline = DictationPipeline(
        stages,
        enabled=True,
        llm_enabled=llm_enabled,
        on_run=on_run,
    )
    return BuildResult(
        pipeline=pipeline,
        blocks=blocks,
        runtime_status=runtime_status,
        runtime_detail=runtime_detail,
    )


def _try_build_runtime(
    cfg: DictationConfig,
    runtime_factory: Callable[..., LLMRuntime] | None,
) -> tuple[Optional[LLMRuntime], RuntimeStatus, str]:
    factory = runtime_factory if runtime_factory is not None else build_runtime
    # DIR-R-003: cold-start hard-cap is `max_total_latency_ms × 5`.
    cold_start_cap_ms = cfg.pipeline.max_total_latency_ms * 5
    try:
        runtime = factory(
            backend=cfg.runtime.backend,
            mlx_model=cfg.runtime.mlx_model,
            llama_cpp_model_path=cfg.runtime.llama_cpp_model_path,
            n_ctx=cfg.runtime.n_ctx,
            n_threads=cfg.runtime.n_threads,
            n_gpu_layers=cfg.runtime.n_gpu_layers,
            warm_on_start=cfg.runtime.warm_on_start,
            eviction_idle_seconds=cfg.runtime.eviction_idle_seconds,
            cold_start_cap_ms=cold_start_cap_ms,
        )
    except RuntimeUnavailableError as exc:
        return None, "unavailable", str(exc)
    except Exception as exc:
        return None, "unavailable", f"{type(exc).__name__}: {exc}"
    return runtime, "loaded", f"backend={getattr(runtime, 'backend', cfg.runtime.backend)}"
