"""The embedding contract for memory (MEMORY-DESIGN.md §4).

The default model is ``nomic-embed-text-v1.5`` (GGUF ``Q8_0``): 768 values,
stored cut to 256 and made unit length.  A document gets the prefix
``search_document: `` and a question gets ``search_query: ``.

This module holds the contract only: the prefixes, the cut, the model id and
the ``MemoryEmbedder`` shape that the retain step and recall use.  It loads
no model.  The engine that runs the model is the ``memory.embed`` capability
(one admitted call per batch).
"""
from __future__ import annotations

import hashlib
from typing import Protocol, Sequence

import numpy as np

DOCUMENT_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "
MEMORY_EMBED_DIM = 256
DEFAULT_MODEL_NAME = "nomic-embed-text-v1.5.Q8_0"
#: A question can be a whole prompt.  Only its end is embedded.
QUERY_CHARS = 2000
EMBED_BATCH = 64


class MemoryEmbedder(Protocol):
    model_id: str
    dim: int

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray: ...

    def embed_query(self, text: str) -> np.ndarray: ...


def cut_unit(vectors: np.ndarray, dim: int = MEMORY_EMBED_DIM) -> np.ndarray:
    """Cut each vector to its first ``dim`` values and make it unit length."""
    matrix = np.asarray(vectors, dtype=np.float32)
    if matrix.ndim == 1:
        matrix = matrix.reshape(1, -1)
    if matrix.shape[1] < dim:
        raise ValueError("the model gives fewer values than the stored size")
    cut = matrix[:, :dim]
    norms = np.linalg.norm(cut, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (cut / norms).astype(np.float32)


def model_id_for(name: str, dim: int = MEMORY_EMBED_DIM) -> str:
    return f"{name}@{int(dim)}"


def text_key(prefixed_text: str) -> str:
    return hashlib.sha256(prefixed_text.encode("utf-8")).hexdigest()


def query_text(text: str) -> str:
    value = " ".join(str(text or "").split())
    return QUERY_PREFIX + value[-QUERY_CHARS:]


__all__ = [
    "DEFAULT_MODEL_NAME",
    "DOCUMENT_PREFIX",
    "EMBED_BATCH",
    "MEMORY_EMBED_DIM",
    "MemoryEmbedder",
    "QUERY_CHARS",
    "QUERY_PREFIX",
    "cut_unit",
    "model_id_for",
    "query_text",
    "text_key",
]
