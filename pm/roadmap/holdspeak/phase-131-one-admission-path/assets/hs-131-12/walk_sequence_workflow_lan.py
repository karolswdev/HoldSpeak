"""Run the shipped Sequence/Workflow walk with the production DB ownership model.

The HS-131-04 evidence leg constructed a standalone ``Database`` while current
runtime facades correctly resolve the process singleton. Mixing those ownership
models disposes the injected broker after the first child and invalidates only the
old harness context. This adapter keeps the original assertions unchanged while
using the same singleton database that the real hub uses.
"""
from __future__ import annotations

import asyncio
import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT))

from holdspeak.db import get_database


async def main(workdir: Path) -> int:
    source = (
        Path(__file__).resolve().parents[1]
        / "hs-131-04"
        / "walk_sequence_workflow_lan.py"
    )
    spec = importlib.util.spec_from_file_location("hs13104_walk", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("sequence/workflow walk asset is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.Database = get_database
    return int(await module.main(workdir))


if __name__ == "__main__":
    raise SystemExit(
        asyncio.run(main(Path(tempfile.mkdtemp(prefix="hs13112-sequence-workflow-"))))
    )
