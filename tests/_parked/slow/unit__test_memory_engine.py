"""Parked 2026-11-08 (the slow tier): the slow-marked cases of tests/unit/test_memory_engine.py, moved as text. Not collected."""


"""Memory slice 1, part 2: the ``memory.embed`` engine and the conductor.

The router, the route planner, the assignment service, the runner and the
embedding adapter are the real ones.  Only the physical leaf is replaced:
the model the adapter loads gives vectors from the benchmark fixture (real
``nomic-embed-text-v1.5`` vectors).  The slow test uses the real GGUF file.
"""
from __future__ import annotations

import asyncio
import os
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest

from holdspeak import memory_conductor
from holdspeak.db import Database
from holdspeak.kernel.inference_runner import InvocationRequest, ServiceContract
from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter
from holdspeak.kernel.runtime import _as_principal, _configure
from holdspeak.memory import engine as memory_engine
from holdspeak.memory.embedder import text_key
from holdspeak.memory.engine import (
    MEMORY_EMBED_CAPABILITY,
    EmbeddingAdapter,
    MemoryEngineError,
    resolve_embedder,
)
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.memory_service import MemoryService
from tests.memory_bench import bench
from tests.memory_bench.corpus import build_corpus
from tests.unit.test_phase143_inference_assignments import OWNER, _profile
from tests.unit.test_phase200_readiness import _assign

MODEL = "nomic-embed-text-v1.5.Q8_0"




@pytest.mark.slow
@pytest.mark.requires_llama_cpp
def test_the_real_model_through_the_real_router(tmp_path: Path) -> None:
    model_path = os.environ.get("HOLDSPEAK_MEMORY_EMBED_MODEL", "")
    if not model_path or not Path(model_path).is_file():
        pytest.skip("set HOLDSPEAK_MEMORY_EMBED_MODEL to nomic-embed-text-v1.5.Q8_0.gguf")
    pytest.importorskip("llama_cpp")
    db = Database(tmp_path / "real.db")
    refs = build_corpus(db)
    broker = _configure(db)
    _profile(db, "embed-model", model=MODEL, claims=("embedding",))
    with db._connection() as conn:
        conn.execute(
            "UPDATE inference_model_artifacts SET local_locator=? WHERE artifact_id='artifact-embed-model'",
            (model_path,),
        )
    _assign(db, MEMORY_EMBED_CAPABILITY, ["embed-model"])
    report = memory_conductor.tick(db, broker)
    assert report["error"] == "" and report["embedded"] == db.memory_index.stats()["chunks"]
    # A search waits half a second for its question, then answers by keyword.
    # On a loaded machine the first call can take longer, so each question is
    # embedded here with a long wait; the searches below read the cache.
    for question in bench.load_questions():
        db.memory.embedder.embed_query(question["q"], timeout=60)
    db.memory.embedder.embed_query("where is the company retreat", timeout=60)
    probe = db.memory.search("where is the company retreat")
    assert probe.engine == {"model_id": f"{MODEL}@256", "boundary": "local", "outcome": "fused"}, probe.engine
    measures = bench.run(db, refs)
    assert measures["groups"]["paraphrase"]["recall@5"] >= 0.7
    receipt = broker.store.receipt(db.memory.embedder.last_operation_id)
    assert receipt["outcome"] == "succeeded"
