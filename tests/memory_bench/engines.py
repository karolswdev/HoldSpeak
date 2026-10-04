"""The two engines the benchmark uses.

* ``LlamaCppEmbedder`` runs the real GGUF model in this process.  The fixture
  script and the nightly test use it.  It is test tooling: in the product the
  model runs behind the ``memory.embed`` capability.
* ``FixtureEmbedder`` reads real-model vectors from ``vectors.npz``, keyed by
  a hash of the prefixed text.  A text with no vector is an error.  The FAST
  tests use it, so they measure real meaning with no model.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Sequence

import numpy as np

from holdspeak.memory.embedder import (
    DOCUMENT_PREFIX, MEMORY_EMBED_DIM, cut_unit, model_id_for, query_text, text_key,
)


class MissingFixtureVector(KeyError):
    """A text has no vector in the fixture file."""


class LlamaCppEmbedder:
    """The GGUF model in this process, through ``llama-cpp-python``."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        dim: int = MEMORY_EMBED_DIM,
        model_name: str | None = None,
        n_ctx: int = 2048,
    ) -> None:
        self.model_path = Path(model_path)
        self.dim = int(dim)
        self.model_id = model_id_for(model_name or self.model_path.stem, self.dim)
        self._n_ctx = int(n_ctx)
        self._lock = threading.Lock()
        self._model = None

    def _load(self):
        if self._model is None:
            from llama_cpp import Llama  # optional extra; imported on first use

            self._model = Llama(
                model_path=str(self.model_path),
                embedding=True,
                n_ctx=self._n_ctx,
                n_batch=self._n_ctx,
                # An encoder model needs the whole input in one micro-batch.
                # With the default (512) llama.cpp ABORTS the process on a
                # batch of more than 512 tokens, so this is not optional.
                n_ubatch=self._n_ctx,
                verbose=False,
            )
        return self._model

    def _embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        with self._lock:
            model = self._load()
            raw = model.embed(list(texts), normalize=False, truncate=True)
        return cut_unit(np.asarray(raw, dtype=np.float32), self.dim)

    def embed_full(self, prefixed_texts: Sequence[str]) -> np.ndarray:
        """Full-size raw vectors (the fixture script and the 768 measure)."""
        with self._lock:
            model = self._load()
            raw = model.embed(list(prefixed_texts), normalize=False, truncate=True)
        return np.asarray(raw, dtype=np.float32)

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        return self._embed([DOCUMENT_PREFIX + str(text) for text in texts])

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([query_text(text)])[0]

    def close(self) -> None:
        with self._lock:
            model, self._model = self._model, None
        if model is not None:
            try:
                model.close()
            except Exception:  # pragma: no cover - best effort
                pass


class FixtureEmbedder:
    """Real-model vectors from a file, keyed by the hash of the prefixed text."""

    def __init__(self, path: str | Path) -> None:
        with np.load(str(path), allow_pickle=False) as data:
            self.model_id = str(data["model_id"])
            keys = [str(key) for key in data["keys"]]
            vectors = np.asarray(data["vectors"], dtype=np.float32)
        self.dim = int(vectors.shape[1])
        self._vectors = {key: vectors[index] for index, key in enumerate(keys)}
        self.calls = 0

    def _one(self, prefixed: str) -> np.ndarray:
        try:
            return self._vectors[text_key(prefixed)]
        except KeyError:
            raise MissingFixtureVector(prefixed[:120]) from None

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        self.calls += 1
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self._one(DOCUMENT_PREFIX + str(text)) for text in texts])

    def embed_query(self, text: str) -> np.ndarray:
        self.calls += 1
        return self._one(query_text(text))
