"""Make ``tests/memory_bench/vectors.npz``: real-model vectors for the fixed
benchmark corpus and its questions.

Run it when a corpus text, a question, the chunker or the model changes:

    HOLDSPEAK_MEMORY_EMBED_MODEL=/path/to/nomic-embed-text-v1.5.Q8_0.gguf \\
        uv run python scripts/memory_bench_vectors.py

The model file is ``nomic-embed-text-v1.5.Q8_0.gguf`` from
``nomic-ai/nomic-embed-text-v1.5-GGUF`` (146 MB).  The script builds the
corpus through the real producers in a throwaway database, runs the real
sweep, and embeds every chunk text and every question.  It also prints the
measures for the 256-value cut against the full 768 values.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from holdspeak.db import Database  # noqa: E402
from holdspeak.memory.embedder import (  # noqa: E402
    DOCUMENT_PREFIX, MEMORY_EMBED_DIM, cut_unit, model_id_for, query_text, text_key,
)
from holdspeak.memory.retain import embed_pending, sweep  # noqa: E402
from tests.memory_bench import bench  # noqa: E402
from tests.memory_bench.corpus import build_corpus  # noqa: E402
from tests.memory_bench.engines import LlamaCppEmbedder  # noqa: E402


class _FullSize:
    """The same model with no cut: the 768 measure."""

    def __init__(self, inner: LlamaCppEmbedder) -> None:
        self._inner = inner
        self.dim = 768
        self.model_id = model_id_for("nomic-embed-text-v1.5.Q8_0", 768)

    def embed_documents(self, texts):
        return cut_unit(self._inner.embed_full([DOCUMENT_PREFIX + t for t in texts]), 768)

    def embed_query(self, text):
        return cut_unit(self._inner.embed_full([query_text(text)]), 768)[0]


def main() -> int:
    model_path = os.environ.get("HOLDSPEAK_MEMORY_EMBED_MODEL", "")
    if not model_path or not Path(model_path).is_file():
        print("Set HOLDSPEAK_MEMORY_EMBED_MODEL to the GGUF file.", file=sys.stderr)
        return 2
    embedder = LlamaCppEmbedder(model_path, model_name="nomic-embed-text-v1.5.Q8_0")
    with tempfile.TemporaryDirectory() as scratch:
        db = Database(Path(scratch) / "bench.db")
        refs = build_corpus(db)
        sweep(db)
        with db._connection() as conn:
            chunk_texts = [str(row[0]) for row in conn.execute("SELECT text FROM memory_chunks ORDER BY id")]
        prefixed = [DOCUMENT_PREFIX + text for text in chunk_texts]
        prefixed += [query_text(question["q"]) for question in bench.load_questions()]
        prefixed = list(dict.fromkeys(prefixed))
        vectors = cut_unit(embedder.embed_full(prefixed), MEMORY_EMBED_DIM)
        np.savez_compressed(
            bench.FIXTURE,
            model_id=np.array(embedder.model_id),
            keys=np.array([text_key(text) for text in prefixed]),
            vectors=vectors.astype(np.float32),
        )
        print(f"wrote {bench.FIXTURE} ({len(prefixed)} vectors, {bench.FIXTURE.stat().st_size} bytes)")

        keyword = bench.run(db, refs)
        print(bench.table("keyword + relation (no engine)", keyword))
        embed_pending(db, embedder)
        db.memory.set_embedder(embedder)
        fused = bench.run(db, refs)
        print(bench.table("fused, 256 values", fused))
        full = _FullSize(embedder)
        embed_pending(db, full)
        db.memory.set_embedder(full)
        fused_full = bench.run(db, refs)
        print(bench.table("fused, 768 values", fused_full))
        bench.BASELINE.write_text(
            json.dumps(
                {
                    "note": "Written by scripts/memory_bench_vectors.py. 'keyword' is the search with no embedding engine (the baseline). The fused rows are the real model on the day the fixture was made.",
                    "model_id": embedder.model_id,
                    "keyword": keyword["groups"],
                    "fused_256": fused["groups"],
                    "fused_768": fused_full["groups"],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
