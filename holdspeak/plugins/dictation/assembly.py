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
    admission: Any = None,
    lexical: bool = False,
) -> BuildResult:
    """Resolve blocks + runtime, return a wired `DictationPipeline`.

    `runtime_factory` is a test seam — production callers leave it
    `None` and get the real `runtime.build_runtime` factory. When
    the factory raises `RuntimeUnavailableError` (or anything else),
    the pipeline still ships, but with `llm_enabled=False` so the
    `intent-router` stage is skipped per HS-1-03.

    HS-131-15: `admission` is what AUTHORIZES model-bearing construction, and it
    is also where the target comes from — see `_try_build_runtime`. `lexical=True`
    is the explicit "this configuration selects no provider-backed stage" path: it
    constructs nothing, mints no inference child, and cannot carry an admission.
    """
    blocks_path = global_blocks_path if global_blocks_path is not None else DEFAULT_GLOBAL_BLOCKS_PATH
    blocks = resolve_blocks(blocks_path, project_root)

    if lexical:
        if admission is not None:
            raise ValueError("a lexical pipeline may not carry a provider admission")
        # Invariant 4: intentionally lexical configuration never enters the
        # runtime factory at all, so there is no provider object to reach.
        runtime, runtime_status, runtime_detail = (
            None,
            "disabled",
            "no provider-backed dictation stage is configured",
        )
    else:
        runtime, runtime_status, runtime_detail = _try_build_runtime(
            cfg, runtime_factory, admission
        )
    llm_enabled = runtime is not None
    # HS-131-09: ONE seam admits every provider-reaching pipeline call. The
    # stages, the rewriter, and model-assisted target detection all hold this
    # wrapper, so none of them can reach a model outside the live session's
    # frozen plan — and none of them learns about the kernel.
    if runtime is not None and admission is not None:
        from ...speech_session.provider import admitted_runtime

        runtime = admitted_runtime(runtime, admission)

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
        # HS-176-02: the pipeline gets the SAME gated snapshot the intent-router
        # stage gets. It keeps the `text` subset for its own transcript seam
        # (ruling R1) and reads the routing subset back only to name the rule
        # the router nudged with. `None` when corrections are off, so a desk
        # with the feature disabled is byte-identical.
        corrections=intent_corrections,
    )
    return BuildResult(
        pipeline=pipeline,
        blocks=blocks,
        runtime_status=runtime_status,
        runtime_detail=runtime_detail,
        runtime=runtime,
    )


def _frozen_local_target(
    engine: str, model_path: str, capability: str
) -> tuple[str, str, str]:
    """Map ONE frozen on-device revision to ``(backend, mlx_model, llama_model)``.

    The frozen ENGINE decides which loader runs. The planner already answered that
    question when it froze the revision, so construction obeys the answer instead
    of re-deriving one — which is the whole point: which engine loads is a
    function of the frozen revision, not of a setting that can change under the
    run.

    Only a revision that named no concrete engine falls back to the artifact's
    shape: a ``this_device`` profile freezes the generic ``local`` and its
    ``model_file`` is a GGUF. Shape is NOT a safe general rule — real MLX model
    names carry dots, so ``Path("Qwen3.5-8B-MLX-4bit").suffix`` is
    ``".5-8B-MLX-4bit"`` and a suffix guess would refuse the default MLX artifact
    outright.

    An artifact that maps to nothing refuses BY NAME here, before any loader is
    constructed, rather than falling back to the ambient configured model (which
    is exactly the silent retarget this story exists to close).

    Constructs nothing itself: it only decides the arguments.
    """
    from ...speech_session.plan import REVISION_TARGET_UNBINDABLE, SpeechSessionRefused

    path = str(Path(model_path).expanduser())
    if engine == "mlx":
        return "mlx", path, ""
    if engine == "llama_cpp":
        return "llama_cpp", "", path
    artifact = Path(path)
    suffix = artifact.suffix.lower()
    if suffix == ".gguf":
        return "llama_cpp", "", path
    # Generic ``local`` profile revisions do not carry the dictation backend.
    # Their readiness contract DOES carry an existing concrete model_path: GGUF
    # is a file; MLX is a directory. Inspect that frozen artifact rather than its
    # suffix, because valid MLX directory names commonly contain dots.
    if artifact.is_dir() or not suffix:
        return "mlx", path, ""
    raise SpeechSessionRefused(
        REVISION_TARGET_UNBINDABLE,
        capability,
        detail=engine or suffix or "unknown_artifact",
    )


def _try_build_runtime(
    cfg: DictationConfig,
    runtime_factory: Callable[..., LLMRuntime] | None,
    admission: Any = None,
) -> tuple[Optional[LLMRuntime], RuntimeStatus, str]:
    """Construct the pipeline runtime AT the admitted frozen revision (HS-131-15).

    Sol Amendment 2 closed the hole this function used to open: it re-ran
    ``effective_dictation_llm`` — a fresh read of mutable config and profile
    state — *after* the session had already frozen a deployment revision, then
    relied on the dispatch seam to rebind whatever came out. That meant
    construction and WARM-ON-START (which really loads a model / opens a client)
    could land on a destination the receipt does not name, and a profile edit
    between admission and construction silently retargeted the run.

    So placement is read here from ONE place only: the revision the live
    admission already froze. Nothing in this function consults current settings
    for *where* to run.

    Refusals, all before any provider object exists:

    * no admission at all (and no explicit test seam) — model-bearing
      construction is not authorized (invariant 2);
    * an admitted capability whose frozen deployment object is missing;
    * a frozen engine with no constructible backend here.

    An admission that declares NO provider capability is the intentionally
    lexical case: it returns no runtime, so zero children are minted, and it is
    reported as ``disabled`` rather than as a runtime *limitation*.
    """
    from ...speech_session.plan import (
        PROVIDER_CAPABILITIES,
        REVISION_NOT_PLANNED,
        REVISION_TARGET_UNBINDABLE,
        SESSION_NOT_ADMITTED,
        SpeechSessionRefused,
    )

    factory = runtime_factory if runtime_factory is not None else build_runtime
    # An admitted synthetic-text entry never preloads outside a child. Concrete
    # runtimes implement ``warm_on_start`` in their constructors, before
    # ``admitted_runtime`` can wrap them; forcing it off means the first admitted
    # classify/rewrite child owns any physical load as part of that one attempt.
    warm_on_start = False if admission is not None else cfg.runtime.warm_on_start
    # DIR-R-003: cold-start hard-cap is `max_total_latency_ms × 5`.
    cold_start_cap_ms = cfg.pipeline.max_total_latency_ms * 5

    node = ""
    endpoint_model = ""
    endpoint_base_url: Optional[str] = None
    endpoint_api_key_env = ""
    endpoint_selected = False
    # The LOCAL artifacts. Under an admission these come from the FROZEN REVISION
    # and nothing else — they start blank so this function has no ambient
    # placement to fall back on. Only the explicit test seam (no admission) fills
    # them from configuration, below.
    local_backend = ""
    local_mlx_model = ""
    local_llama_model = ""

    if admission is not None:
        from ...speech_session.revision_target import (
            ENDPOINT_ENGINES,
            LOCAL_ENGINES,
            MESH_ENGINES,
        )

        capability = next(
            (name for name in PROVIDER_CAPABILITIES if admission.declares(name)), ""
        )
        if not capability:
            return None, "disabled", "no provider-backed dictation stage is admitted"
        deployment = getattr(admission, "deployment", None)
        revision = deployment(capability) if callable(deployment) else admission.plan.deployment(
            admission.revision(capability)
        )
        if revision is None:
            raise SpeechSessionRefused(REVISION_NOT_PLANNED, capability)
        engine = str(getattr(revision, "engine", "") or "")
        node = str(getattr(revision, "node", "") or "")
        if engine in MESH_ENGINES or node:
            endpoint_model = str(getattr(revision, "model", "") or "")
        elif engine in ENDPOINT_ENGINES:
            endpoint_selected = True
            endpoint_model = str(getattr(revision, "model", "") or "")
            endpoint_base_url = str(getattr(revision, "endpoint", "") or "") or None
            # Empty is authoritative: a keyless frozen revision must remain
            # keyless. Reconstructing a profile slot from ``destination_id`` here
            # would add credential authority the admitted revision did not grant.
            endpoint_api_key_env = str(getattr(revision, "secret_slot", "") or "")
        elif engine in LOCAL_ENGINES:
            # An on-device DESTINATION names the exact artifact whose readiness
            # admission checked (HS-130-03), so that artifact — and nothing the
            # configuration says now — is what loads and warms. EVERY local engine
            # binds this way: a revision that froze no artifact has not described
            # what a same-device child may load, so it refuses by name instead of
            # falling through to the ambient dictation paths.
            frozen_path = str(getattr(revision, "model_path", "") or "").strip()
            if not frozen_path:
                raise SpeechSessionRefused(
                    REVISION_TARGET_UNBINDABLE, capability, detail=engine or "local"
                )
            local_backend, local_mlx_model, local_llama_model = _frozen_local_target(
                engine, frozen_path, capability
            )
        else:
            raise SpeechSessionRefused(
                REVISION_TARGET_UNBINDABLE, capability, detail=engine
            )
    else:
        if runtime_factory is None:
            # Invariant 2: no live admission, no model-bearing runtime. Not a
            # "limitation" — a named refusal, so it can never be read as
            # `runtime_status="unavailable"` and quietly degraded to raw text.
            raise SpeechSessionRefused(SESSION_NOT_ADMITTED, "dictation-runtime")
        # The explicit test seam builds the caller's own object; it reaches no
        # provider, so the legacy placement read is harmless here — and this is
        # the ONLY branch that reads configuration for placement at all.
        from ...intel.providers import effective_dictation_llm

        local_backend = cfg.runtime.backend
        local_mlx_model = cfg.runtime.mlx_model
        local_llama_model = cfg.runtime.llama_cpp_model_path
        effective = effective_dictation_llm(cfg.runtime)
        if effective.reason:
            return None, "unavailable", effective.reason
        node = effective.node
        endpoint_model = effective.model
        endpoint_base_url = effective.base_url
        endpoint_api_key_env = effective.api_key_env
        endpoint_selected = bool(effective.profile_id)

    if node:
        # a meshNode revision: the LLM legs run on that node's provider via the
        # relay queue, wrapped in the same counting/cold-start delegate.
        try:
            from .runtime_counters import CountingRuntime
            from .runtime_mesh_relay import MeshRelayRuntime

            inner = MeshRelayRuntime(node=node, model_hint=endpoint_model)
            runtime = CountingRuntime(
                inner,
                warm_on_start=warm_on_start,
                cold_start_cap_ms=cold_start_cap_ms,
            )
        except Exception as exc:
            return None, "unavailable", f"{type(exc).__name__}: {exc}"
        return runtime, "loaded", f"backend=mesh_relay node={node}"
    backend = "openai_compatible" if endpoint_selected else local_backend
    try:
        runtime = factory(
            backend=backend,
            mlx_model=local_mlx_model,
            llama_cpp_model_path=local_llama_model,
            endpoint_model=endpoint_model,
            endpoint_base_url=endpoint_base_url,
            endpoint_api_key_env=endpoint_api_key_env,
            endpoint_timeout_seconds=cfg.runtime.openai_compatible_timeout_seconds,
            n_ctx=cfg.runtime.n_ctx,
            n_threads=cfg.runtime.n_threads,
            n_gpu_layers=cfg.runtime.n_gpu_layers,
            warm_on_start=warm_on_start,
            eviction_idle_seconds=cfg.runtime.eviction_idle_seconds,
            cold_start_cap_ms=cold_start_cap_ms,
        )
    except RuntimeUnavailableError as exc:
        return None, "unavailable", str(exc)
    except Exception as exc:
        return None, "unavailable", f"{type(exc).__name__}: {exc}"
    # The label names the backend THIS construction selected, not what the config
    # says now: `backend` is already the frozen revision's answer under admission.
    return runtime, "loaded", f"backend={getattr(runtime, 'backend', backend)}"
