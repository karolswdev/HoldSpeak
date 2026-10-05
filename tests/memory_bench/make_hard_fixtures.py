"""Record the two fixtures of the hard relation questions.

* ``relation_hard_facts.json``: real-model ``memory.extract`` answers for the
  hard sources (``corpus.build_hard_corpus``).  The base corpus answers come
  from ``facts.json`` as recorded; only a prompt with no answer there goes to
  the endpoint, so this file holds the hard sources only.
* ``relation_hard_vectors.npz``: real-model vectors for every chunk text and
  question that ``vectors.npz`` does not hold.

Record again when a hard source, a hard question, the prompt or
``EXTRACTOR_VERSION`` changes:

    HOLDSPEAK_MEMORY_EMBED_MODEL=/path/to/nomic-embed-text-v1.5.Q8_0.gguf \\
        uv run python -m tests.memory_bench.make_hard_fixtures http://192.168.1.43:8080/v1 qwen3.8-27b
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np

from holdspeak.db import Database
from holdspeak.memory.embedder import (
    DOCUMENT_PREFIX, MEMORY_EMBED_DIM, cut_unit, query_text, text_key,
)
from holdspeak.memory.extract import EXTRACTOR_VERSION, extract_pending
from holdspeak.memory.retain import sweep

from . import bench
from .corpus import build_corpus, build_hard_corpus
from .engines import EndpointExtractor, FixtureExtractor, LlamaCppEmbedder, fixture_key


class _ReplayThenRecord:
    """The recorded base answer when there is one; else the endpoint."""

    boundary = "private_network"

    def __init__(self, base: FixtureExtractor, hard: dict[str, dict], live: EndpointExtractor) -> None:
        self.base = base
        self.hard = hard
        self.live = live
        self.model_id = live.model_id
        self.kept: dict[str, dict] = {}

    def extract(self, payload: dict) -> dict:
        key = fixture_key(payload)
        if key in self.base._answers:
            return self.base._answers[key]
        if key in self.hard:
            self.kept[key] = self.hard[key]
            return self.hard[key]
        return self.live.extract(payload)


def main(base_url: str, model: str) -> None:
    model_path = os.environ.get("HOLDSPEAK_MEMORY_EMBED_MODEL", "")
    db = Database(Path(tempfile.mkdtemp()) / "hard.db")
    build_corpus(db)
    build_hard_corpus(db)
    sweep(db)
    if model_path and Path(model_path).is_file():
        _record_vectors(db, model_path)
    else:
        # The vectors depend on the chunk texts only: a prompt change records
        # the facts again and keeps the vectors file as it is.
        print("HOLDSPEAK_MEMORY_EMBED_MODEL not set: vectors kept, facts recorded", file=sys.stderr)
    _record_facts(db, base_url, model)


def _record_vectors(db: Database, model_path: str) -> None:
    # Vectors: what the base fixture does not hold.
    with np.load(str(bench.FIXTURE), allow_pickle=False) as data:
        held = {str(key) for key in data["keys"]}
    with db._connection() as conn:
        chunk_texts = [str(row[0]) for row in conn.execute("SELECT text FROM memory_chunks ORDER BY id")]
    prefixed = [DOCUMENT_PREFIX + text for text in chunk_texts]
    prefixed += [query_text(question["q"]) for question in bench.load_hard_relation_questions()]
    prefixed = [text for text in dict.fromkeys(prefixed) if text_key(text) not in held]
    embedder = LlamaCppEmbedder(model_path, model_name="nomic-embed-text-v1.5.Q8_0")
    vectors = cut_unit(embedder.embed_full(prefixed), MEMORY_EMBED_DIM)
    np.savez_compressed(
        bench.HARD_VECTORS,
        model_id=np.array(embedder.model_id),
        keys=np.array([text_key(text) for text in prefixed]),
        vectors=vectors.astype(np.float32),
    )
    print(f"wrote {bench.HARD_VECTORS} ({len(prefixed)} vectors)", file=sys.stderr)


def _record_facts(db: Database, base_url: str, model: str) -> None:
    # Facts: the endpoint for the hard sources only.
    # A hard prompt already recorded keeps its answer; only a new or changed
    # prompt goes to the endpoint.
    live = EndpointExtractor(base_url, model)
    hard: dict[str, dict] = {}
    if bench.HARD_FACTS.is_file():
        recorded = json.loads(bench.HARD_FACTS.read_text())
        if recorded.get("model") == model and recorded.get("extractor_version") == EXTRACTOR_VERSION:
            hard = dict(recorded["answers"])
    engine = _ReplayThenRecord(FixtureExtractor(bench.FACTS), hard, live)
    stats = extract_pending(db, engine)
    bench.HARD_FACTS.write_text(json.dumps(
        {
            "model": model,
            "endpoint": base_url,
            "extractor_version": EXTRACTOR_VERSION,
            "answers": dict(sorted({**engine.kept, **live.answers}.items())),
        },
        indent=1, sort_keys=True, ensure_ascii=False,
    ) + "\n")
    print(
        f"{live.calls} endpoint calls, {len(engine.kept)} kept, {stats['sources']} sources, {stats['facts']} facts -> {bench.HARD_FACTS}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
