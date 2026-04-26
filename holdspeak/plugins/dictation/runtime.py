"""Pluggable LLM runtime for the DIR-01 dictation router (HS-1-04).

Spec: `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §7. Two concrete
backends share a single `LLMRuntime` Protocol; stage code MUST NOT
import either backend directly. Backend resolution is governed by
`dictation.runtime.backend: auto | mlx | llama_cpp` (default `auto`).

`auto` resolves to:
  - `mlx` on darwin/arm64 when `mlx_lm` is importable;
  - `llama_cpp` otherwise.

Explicit backend values never fall back: when the requested backend
is unavailable, `RuntimeUnavailableError` is raised with a remediation
hint; `holdspeak doctor` (HS-1-09) surfaces the reason.
"""

from __future__ import annotations

import importlib
import platform
from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from holdspeak.plugins.dictation.grammars import StructuredOutputSchema

VALID_BACKENDS = ("auto", "mlx", "llama_cpp")


class RuntimeUnavailableError(RuntimeError):
    """Raised when the requested backend cannot be loaded."""


@runtime_checkable
class LLMRuntime(Protocol):
    """The backend-agnostic surface every dictation runtime exposes."""

    backend: str

    def load(self) -> None: ...

    def info(self) -> dict[str, Any]: ...

    def classify(
        self,
        prompt: str,
        schema: StructuredOutputSchema,
        *,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> dict[str, Any]: ...


def _on_apple_silicon() -> bool:
    return platform.system() == "Darwin" and platform.machine() == "arm64"


def _module_importable(name: str) -> bool:
    try:
        importlib.import_module(name)
    except Exception:  # pragma: no cover — env-dependent
        return False
    return True


def resolve_backend(
    requested: str,
    *,
    on_arm64: Callable[[], bool] | None = None,
    mlx_importable: Callable[[], bool] | None = None,
    llama_cpp_importable: Callable[[], bool] | None = None,
) -> tuple[str, str]:
    """Resolve `auto | mlx | llama_cpp` → concrete backend + reason.

    Explicit backends never fall back: if requested is unavailable,
    `RuntimeUnavailableError` is raised.

    The seam args (`on_arm64`, `*_importable`) make resolution
    deterministically testable without touching the host environment.
    """
    if requested not in VALID_BACKENDS:
        raise RuntimeUnavailableError(
            f"Unknown runtime backend {requested!r}; expected one of {VALID_BACKENDS}."
        )

    arm64 = on_arm64 or _on_apple_silicon
    mlx_ok = mlx_importable or (lambda: _module_importable("mlx_lm"))
    llama_ok = llama_cpp_importable or (lambda: _module_importable("llama_cpp"))

    if requested == "mlx":
        if not arm64():
            raise RuntimeUnavailableError(
                "Backend 'mlx' requires darwin/arm64. "
                "Set dictation.runtime.backend='llama_cpp' or 'auto'."
            )
        if not mlx_ok():
            raise RuntimeUnavailableError(
                "Backend 'mlx' requires the 'mlx-lm' package. "
                "Install with: uv pip install holdspeak[dictation-mlx]"
            )
        return "mlx", "explicit"

    if requested == "llama_cpp":
        if not llama_ok():
            raise RuntimeUnavailableError(
                "Backend 'llama_cpp' requires the 'llama-cpp-python' package. "
                "Install with: uv pip install holdspeak[dictation-llama]"
            )
        return "llama_cpp", "explicit"

    # auto
    if arm64() and mlx_ok():
        return "mlx", "auto: darwin/arm64 with mlx_lm importable"
    if llama_ok():
        return "llama_cpp", "auto: fallback to llama_cpp"
    raise RuntimeUnavailableError(
        "No dictation runtime backend is available. Install either "
        "holdspeak[dictation-mlx] (darwin/arm64) or "
        "holdspeak[dictation-llama] (cross-platform)."
    )


def build_runtime(
    *,
    backend: str = "auto",
    mlx_model: str = "~/Models/mlx/Qwen3-8B-MLX-4bit",
    llama_cpp_model_path: str = "~/Models/gguf/Qwen2.5-3B-Instruct-Q4_K_M.gguf",
    n_ctx: int = 2048,
    n_threads: int | None = None,
    n_gpu_layers: int = -1,
    warm_on_start: bool = False,
    eviction_idle_seconds: int = 0,
    cold_start_cap_ms: int | None = None,
    # Test seams — production callers leave these defaulted.
    on_arm64: Callable[[], bool] | None = None,
    mlx_importable: Callable[[], bool] | None = None,
    llama_cpp_importable: Callable[[], bool] | None = None,
    factories: dict[str, Callable[..., LLMRuntime]] | None = None,
) -> LLMRuntime:
    """Resolve the backend and instantiate the corresponding runtime.

    The `factories` seam lets tests substitute backends without
    importing the heavy concrete modules. In production the default
    factories lazily import `runtime_mlx` / `runtime_llama_cpp`.
    """
    resolved, _ = resolve_backend(
        backend,
        on_arm64=on_arm64,
        mlx_importable=mlx_importable,
        llama_cpp_importable=llama_cpp_importable,
    )

    factories = factories if factories is not None else _default_factories()

    if resolved == "mlx":
        inner = factories["mlx"](
            model=mlx_model,
            warm_on_start=warm_on_start,
            eviction_idle_seconds=eviction_idle_seconds,
        )
    else:
        inner = factories["llama_cpp"](
            model_path=llama_cpp_model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            warm_on_start=warm_on_start,
            eviction_idle_seconds=eviction_idle_seconds,
        )

    # DIR-O-002 + DIR-R-003: wrap with counter-instrumenting +
    # cold-start-capping delegate.
    from holdspeak.plugins.dictation.runtime_counters import CountingRuntime
    return CountingRuntime(
        inner,
        warm_on_start=warm_on_start,
        cold_start_cap_ms=cold_start_cap_ms,
    )


def _default_factories() -> dict[str, Callable[..., LLMRuntime]]:
    def _mlx_factory(**kwargs: Any) -> LLMRuntime:
        from holdspeak.plugins.dictation.runtime_mlx import MlxRuntime

        return MlxRuntime(**kwargs)

    def _llama_factory(**kwargs: Any) -> LLMRuntime:
        from holdspeak.plugins.dictation.runtime_llama_cpp import LlamaCppRuntime

        return LlamaCppRuntime(**kwargs)

    return {"mlx": _mlx_factory, "llama_cpp": _llama_factory}
