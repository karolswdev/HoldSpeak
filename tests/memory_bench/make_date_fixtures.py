"""Record ``date_facts.json``: real-model ``memory.extract`` answers for the
date cases (``corpus.DATE_CASES``), each on its own desk.  Record again when
a case, the prompt or ``EXTRACTOR_VERSION`` changes:

    uv run python -m tests.memory_bench.make_date_fixtures http://192.168.1.43:8080/v1 qwen3.8-27b
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from holdspeak.db import Database
from holdspeak.memory.extract import EXTRACTOR_VERSION, extract_pending
from holdspeak.memory.retain import sweep

from . import bench
from .corpus import DATE_CASES, build_date_case
from .engines import EndpointExtractor


def main(base_url: str, model: str) -> None:
    live = EndpointExtractor(base_url, model)
    for case in DATE_CASES:
        db = Database(Path(tempfile.mkdtemp()) / "date.db")
        build_date_case(db, case)
        sweep(db)
        extract_pending(db, live)
    bench.DATE_FACTS.write_text(json.dumps(
        {
            "model": model,
            "endpoint": base_url,
            "extractor_version": EXTRACTOR_VERSION,
            "answers": dict(sorted(live.answers.items())),
        },
        indent=1, sort_keys=True, ensure_ascii=False,
    ) + "\n")
    print(f"{live.calls} calls -> {bench.DATE_FACTS}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
