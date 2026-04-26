"""`llama-cpp-python` backend for the DIR-01 dictation router.

Spec: `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §7.1, §7.3.
Constrained decoding via GBNF (`grammar=` on `Llama.create_completion`).
The loader-failure handling pattern mirrors `holdspeak/intel.py`.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from holdspeak.logging_config import get_logger
from holdspeak.plugins.dictation.grammars import (
    StructuredOutputSchema,
    to_gbnf,
)
from holdspeak.plugins.dictation.runtime import RuntimeUnavailableError

log = get_logger("dictation.runtime.llama_cpp")


class LlamaCppRuntime:
    """`LLMRuntime` over `llama-cpp-python`."""

    backend = "llama_cpp"

    def __init__(
        self,
        *,
        model_path: str,
        n_ctx: int = 2048,
        n_threads: int | None = None,
        n_gpu_layers: int = -1,
        warm_on_start: bool = False,
        eviction_idle_seconds: int = 0,
        # Test seam: caller can pass an already-constructed Llama-like object.
        llama_factory: Any | None = None,
    ) -> None:
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.eviction_idle_seconds = eviction_idle_seconds
        self._llm: Any | None = None
        self._last_used: float = 0.0
        self._llama_factory = llama_factory
        self._gbnf_factory: Any | None = None

        if warm_on_start:
            self.load()

    def _resolve_factories(self) -> tuple[Any, Any]:
        """Return (llama_cls, llama_grammar_cls); resolved lazily."""
        if self._llama_factory is not None and self._gbnf_factory is not None:
            return self._llama_factory, self._gbnf_factory

        try:
            from llama_cpp import Llama, LlamaGrammar  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover — install-dependent
            raise RuntimeUnavailableError(
                "llama-cpp-python is not installed. "
                "Install with: uv pip install holdspeak[dictation-llama]"
            ) from exc

        llama_cls = self._llama_factory or Llama
        gbnf_cls = self._gbnf_factory or LlamaGrammar
        self._llama_factory = llama_cls
        self._gbnf_factory = gbnf_cls
        return llama_cls, gbnf_cls

    def load(self) -> None:
        if self._llm is not None:
            return
        llama_cls, _ = self._resolve_factories()
        path = Path(self.model_path).expanduser()
        if not path.exists():
            raise RuntimeUnavailableError(
                f"GGUF model not found: {path}. "
                "Download Qwen2.5-3B-Instruct-Q4_K_M.gguf into ~/Models/gguf/."
            )
        kwargs: dict[str, Any] = {
            "model_path": str(path),
            "n_ctx": self.n_ctx,
            "n_gpu_layers": self.n_gpu_layers,
        }
        if self.n_threads is not None:
            kwargs["n_threads"] = self.n_threads
        log.info("Loading dictation llama_cpp model: %s", path)
        try:
            self._llm = llama_cls(**kwargs)
        except Exception as exc:  # pragma: no cover — env-dependent
            log.error("Failed to load llama_cpp model: %s", exc, exc_info=True)
            raise RuntimeUnavailableError(
                f"Failed to load llama_cpp model {path}: {exc}"
            ) from exc

    def info(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "model": str(Path(self.model_path).expanduser()),
            "n_ctx": self.n_ctx,
            "n_threads": self.n_threads,
            "n_gpu_layers": self.n_gpu_layers,
            "loaded": self._llm is not None,
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
        assert self._llm is not None
        _, gbnf_cls = self._resolve_factories()

        gbnf_str = to_gbnf(schema)
        grammar = gbnf_cls.from_string(gbnf_str)

        self._maybe_evict()
        completion = self._llm.create_completion(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            grammar=grammar,
        )
        self._last_used = time.monotonic()

        text = _extract_completion_text(completion)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"llama_cpp produced non-JSON despite GBNF: {text!r}"
            ) from exc

    def _maybe_evict(self) -> None:
        if self.eviction_idle_seconds <= 0 or self._last_used == 0.0:
            return
        if time.monotonic() - self._last_used > self.eviction_idle_seconds:
            log.info("Evicting llama_cpp model after idle timeout")
            self._llm = None


def _extract_completion_text(completion: Any) -> str:
    """`Llama.create_completion` returns a dict-like; extract the text."""
    if isinstance(completion, dict):
        choices = completion.get("choices") or []
        if choices and isinstance(choices[0], dict):
            return str(choices[0].get("text", ""))
    return str(completion)
