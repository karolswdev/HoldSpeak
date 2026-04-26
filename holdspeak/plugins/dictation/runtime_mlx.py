"""`mlx-lm` backend for the DIR-01 dictation router.

Spec: `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §7.1, §7.3.
Constrained decoding via the `outlines` 1.x JSON-schema generator
over `mlx-lm` (`outlines.from_mlxlm` + `Generator(model,
output_type=JsonSchema(...))`). `outlines` is a localized
dependency confined to this module so the rest of the pipeline does
not pay the import cost.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from holdspeak.logging_config import get_logger
from holdspeak.plugins.dictation.grammars import (
    StructuredOutputSchema,
    to_outlines,
)
from holdspeak.plugins.dictation.runtime import RuntimeUnavailableError

log = get_logger("dictation.runtime.mlx")


class MlxRuntime:
    """`LLMRuntime` over `mlx-lm` with `outlines`-driven JSON-schema decoding."""

    backend = "mlx"

    def __init__(
        self,
        *,
        model: str = "~/Models/mlx/Qwen3-8B-MLX-4bit",
        warm_on_start: bool = False,
        eviction_idle_seconds: int = 0,
        # Test seams.
        load_fn: Any | None = None,
        generator_factory: Any | None = None,
    ) -> None:
        self.model = model
        self.eviction_idle_seconds = eviction_idle_seconds
        self._loaded: tuple[Any, Any] | None = None  # (model, tokenizer)
        self._last_used: float = 0.0
        self._load_fn = load_fn
        # `generator_factory(model, tokenizer, schema_dict) -> callable(prompt, max_tokens) -> str`.
        # Defaults to outlines.Generator(from_mlxlm(model, tokenizer), JsonSchema(schema)).
        self._generator_factory = generator_factory

        if warm_on_start:
            self.load()

    def _resolve_load_fn(self) -> Any:
        if self._load_fn is not None:
            return self._load_fn
        try:
            from mlx_lm import load as mlx_load  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover — install-dependent
            raise RuntimeUnavailableError(
                "mlx-lm is not installed. "
                "Install with: uv pip install holdspeak[dictation-mlx]"
            ) from exc
        self._load_fn = mlx_load
        return mlx_load

    def _resolve_generator_factory(self) -> Any:
        if self._generator_factory is not None:
            return self._generator_factory
        try:
            from outlines import Generator, from_mlxlm  # type: ignore[import-not-found]
            from outlines.types import JsonSchema  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover — install-dependent
            raise RuntimeUnavailableError(
                "outlines is not installed. "
                "Install with: uv pip install holdspeak[dictation-mlx]"
            ) from exc

        def _factory(mlx_model: Any, tokenizer: Any, schema_dict: dict[str, Any]) -> Any:
            omodel = from_mlxlm(mlx_model, tokenizer)
            return Generator(omodel, output_type=JsonSchema(schema_dict))

        self._generator_factory = _factory
        return _factory

    def load(self) -> None:
        if self._loaded is not None:
            return
        load_fn = self._resolve_load_fn()
        path = Path(self.model).expanduser()
        # Allow HF repo IDs (no leading "/" or "~"). If it looks like a path,
        # require the directory to exist.
        if str(self.model).startswith(("/", "~", ".")) and not path.exists():
            raise RuntimeUnavailableError(
                f"MLX model snapshot not found: {path}. "
                "Download Qwen3-8B-MLX-4bit into ~/Models/mlx/."
            )
        # mlx_lm.load accepts either a local snapshot dir or an HF repo
        # id. If the configured value looks like a filesystem path,
        # pass the expanded absolute path so `~` works; otherwise pass
        # the bare string (HF repo id).
        load_target = str(path) if str(self.model).startswith(("/", "~", ".")) else str(self.model)
        log.info("Loading dictation mlx model: %s", load_target)
        try:
            model, tokenizer = load_fn(load_target)
        except Exception as exc:  # pragma: no cover — env-dependent
            log.error("Failed to load mlx model: %s", exc, exc_info=True)
            raise RuntimeUnavailableError(
                f"Failed to load mlx model {self.model}: {exc}"
            ) from exc
        self._loaded = (model, tokenizer)

    def info(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "model": str(self.model),
            "device": "mlx",
            "loaded": self._loaded is not None,
        }

    def classify(
        self,
        prompt: str,
        schema: StructuredOutputSchema,
        *,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        self.load()
        assert self._loaded is not None
        generator_factory = self._resolve_generator_factory()

        schema_dict = to_outlines(schema)
        model, tokenizer = self._loaded
        generator = generator_factory(model, tokenizer, schema_dict)

        self._maybe_evict()
        text = generator(prompt, max_tokens=max_tokens)
        self._last_used = time.monotonic()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"mlx produced non-JSON despite outlines schema: {text!r}"
            ) from exc

    def _maybe_evict(self) -> None:
        if self.eviction_idle_seconds <= 0 or self._last_used == 0.0:
            return
        if time.monotonic() - self._last_used > self.eviction_idle_seconds:
            log.info("Evicting mlx model after idle timeout")
            self._loaded = None
