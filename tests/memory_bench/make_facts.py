"""Record ``facts.json``: real-model ``memory.extract`` answers for the corpus.

Every chunk of every "yes" source is sent through the product's own prompt
(``holdspeak.memory.extract.build_payload``, by ``extract_pending``) to an
OpenAI-compatible endpoint, and each answer is stored under the hash of the
prompt.  ``FixtureExtractor`` replays them, so the FAST tests measure real
extraction with no model.  Record again when the prompt, the corpus or
``EXTRACTOR_VERSION`` changes:

    uv run python -m tests.memory_bench.make_facts http://192.168.1.43:8080/v1 qwen3.8-27b
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from holdspeak.db import Database
from holdspeak.memory.extract import EXTRACTOR_VERSION, extract_pending
from holdspeak.memory.retain import sweep

from .bench import HERE
from .corpus import build_corpus
from .engines import EndpointExtractor

FACTS = HERE / "facts.json"


def main(base_url: str, model: str) -> None:
    db = Database(Path(tempfile.mkdtemp()) / "facts.db")
    build_corpus(db)
    sweep(db)
    engine = EndpointExtractor(base_url, model)
    stats = extract_pending(db, engine)
    FACTS.write_text(json.dumps(
        {
            "model": model,
            "endpoint": base_url,
            "extractor_version": EXTRACTOR_VERSION,
            "answers": dict(sorted(engine.answers.items())),
        },
        indent=1, sort_keys=True, ensure_ascii=False,
    ) + "\n")
    print(f"{engine.calls} calls, {stats['sources']} sources, {stats['facts']} facts -> {FACTS}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
