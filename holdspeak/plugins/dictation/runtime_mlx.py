"""`mlx-lm` backend for the DIR-01 dictation router.

Spec: `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §7.1, §7.3.
Constrained decoding via an `outlines`-style logits processor over
`mlx-lm`. `outlines` is a localized dependency confined to this
module so the rest of the pipeline does not pay the import cost.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from holdspeak.logging_config import get_logger
from holdspeak.plugins.dictation.grammars import (
    StructuredOutputSchema,
    to_outlines_json,
)
from holdspeak.plugins.dictation.runtime import RuntimeUnavailableError

log = get_logger("dictation.runtime.mlx")


class MlxRuntime:
    """`LLMRuntime` over `mlx-lm` with `outlines`-style structured output."""

    backend = "mlx"

    def __init__(
        self,
        *,
        model: str = "~/Models/mlx/Qwen3-8B-MLX-4bit",
        warm_on_start: bool = False,
        eviction_idle_seconds: int = 0,
        # Test seams.
        load_fn: Any | None = None,
        generate_fn: Any | None = None,
        processor_factory: Any | None = None,
    ) -> None:
        self.model = model
        self.eviction_idle_seconds = eviction_idle_seconds
        self._loaded: tuple[Any, Any] | None = None  # (model, tokenizer)
        self._last_used: float = 0.0
        self._load_fn = load_fn
        self._generate_fn = generate_fn
        self._processor_factory = processor_factory

        if warm_on_start:
            self.load()

    def _resolve_mlx(self) -> tuple[Any, Any]:
        """Resolve `(load_fn, generate_fn)` from `mlx_lm` lazily."""
        if self._load_fn is not None and self._generate_fn is not None:
            return self._load_fn, self._generate_fn
        try:
            from mlx_lm import generate as mlx_generate, load as mlx_load  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover — install-dependent
            raise RuntimeUnavailableError(
                "mlx-lm is not installed. "
                "Install with: uv pip install holdspeak[dictation-mlx]"
            ) from exc
        self._load_fn = self._load_fn or mlx_load
        self._generate_fn = self._generate_fn or mlx_generate
        return self._load_fn, self._generate_fn

    def _resolve_processor_factory(self) -> Any:
        if self._processor_factory is not None:
            return self._processor_factory
        try:
            from outlines.processors import JSONLogitsProcessor  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover — install-dependent
            raise RuntimeUnavailableError(
                "outlines is not installed. "
                "Install with: uv pip install holdspeak[dictation-mlx]"
            ) from exc
        self._processor_factory = JSONLogitsProcessor
        return JSONLogitsProcessor

    def load(self) -> None:
        if self._loaded is not None:
            return
        load_fn, _ = self._resolve_mlx()
        path = Path(self.model).expanduser()
        # Allow HF repo IDs (no leading "/" or "~"). If it looks like a path,
        # require the directory to exist.
        if str(self.model).startswith(("/", "~", ".")) and not path.exists():
            raise RuntimeUnavailableError(
                f"MLX model snapshot not found: {path}. "
                "Download Qwen3-8B-MLX-4bit into ~/Models/mlx/."
            )
        log.info("Loading dictation mlx model: %s", self.model)
        try:
            model, tokenizer = load_fn(str(self.model))
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
        _, generate_fn = self._resolve_mlx()
        processor_cls = self._resolve_processor_factory()

        schema_json = to_outlines_json(schema)
        model, tokenizer = self._loaded
        processor = processor_cls(schema_json, tokenizer=tokenizer)

        self._maybe_evict()
        text = generate_fn(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            temp=temperature,
            logits_processors=[processor],
        )
        self._last_used = time.monotonic()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"mlx produced non-JSON despite logits processor: {text!r}"
            ) from exc

    def _maybe_evict(self) -> None:
        if self.eviction_idle_seconds <= 0 or self._last_used == 0.0:
            return
        if time.monotonic() - self._last_used > self.eviction_idle_seconds:
            log.info("Evicting mlx model after idle timeout")
            self._loaded = None
