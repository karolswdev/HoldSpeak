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
from holdspeak.plugins.dictation.builtin.project_rewriter import ProjectRewriter
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
    # HS-39-03: the loaded runtime (or None) so callers can reuse it for
    # model-assisted target detection outside the pipeline.
    runtime: Optional[LLMRuntime] = None


def build_pipeline(
    cfg: DictationConfig,
    *,
    on_run: Callable[[PipelineRun], None] | None = None,
    project_root: Path | None = None,
    global_blocks_path: Path | None = None,
    runtime_factory: Callable[..., LLMRuntime] | None = None,
    corrections: list[Any] | None = None,
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

    # HS-39-02: corrections only influence routing when the feature is on AND
    # the store has entries; otherwise pass None so the router is byte-identical.
    intent_corrections = (
        corrections
        if corrections and getattr(cfg.pipeline, "corrections_enabled", False)
        else None
    )

    stages: list[Any] = []
    for stage_id in cfg.pipeline.stages:
        if stage_id == "intent-router":
            if runtime is not None:
                stages.append(IntentRouter(runtime, blocks, corrections=intent_corrections))
        elif stage_id == "project-rewriter":
            if runtime is not None:
                stages.append(
                    ProjectRewriter(
                        runtime,
                        rewrite_passes=cfg.pipeline.rewrite_passes,
                        latency_budget_ms=float(cfg.pipeline.max_total_latency_ms),
                    )
                )
        elif stage_id == "kb-enricher":
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
        runtime=runtime,
    )


def _try_build_runtime(
    cfg: DictationConfig,
    runtime_factory: Callable[..., LLMRuntime] | None,
) -> tuple[Optional[LLMRuntime], RuntimeStatus, str]:
    factory = runtime_factory if runtime_factory is not None else build_runtime
    # DIR-R-003: cold-start hard-cap is `max_total_latency_ms × 5`.
    cold_start_cap_ms = cfg.pipeline.max_total_latency_ms * 5

    # HS-84-02: the LLM leg runs where the assigned RuntimeProfile says. An
    # adopted profile also selects the openai_compatible backend (assignment is
    # the user's explicit "run it there"); dangling/none ⇒ the configured
    # backend + openai_compatible_* shape, byte-identical.
    from ...intel.providers import effective_dictation_llm

    effective = effective_dictation_llm(cfg.runtime)
    backend = "openai_compatible" if effective.profile_id else cfg.runtime.backend
    try:
        runtime = factory(
            backend=backend,
            mlx_model=cfg.runtime.mlx_model,
            llama_cpp_model_path=cfg.runtime.llama_cpp_model_path,
            openai_compatible_model=effective.model,
            openai_compatible_base_url=effective.base_url,
            openai_compatible_api_key_env=effective.api_key_env,
            openai_compatible_timeout_seconds=cfg.runtime.openai_compatible_timeout_seconds,
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
