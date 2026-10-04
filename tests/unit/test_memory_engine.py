"""Memory slice 1, part 2: the ``memory.embed`` engine and the conductor.

The router, the route planner, the assignment service, the runner and the
embedding adapter are the real ones.  Only the physical leaf is replaced:
the model the adapter loads gives vectors from the benchmark fixture (real
``nomic-embed-text-v1.5`` vectors).  The slow test uses the real GGUF file.
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from holdspeak import memory_conductor
from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.memory import engine as memory_engine
from holdspeak.memory.engine import (
    EmbeddingAdapter, MEMORY_EMBED_CAPABILITY, MemoryEngineError, resolve_embedder,
)
from holdspeak.memory.embedder import text_key
from holdspeak.services.inference_assignment_service import InferenceAssignmentService

from tests.memory_bench import bench
from tests.memory_bench.corpus import build_corpus
from tests.unit.test_phase143_inference_assignments import OWNER, _profile
from tests.unit.test_phase200_readiness import _assign

MODEL = "nomic-embed-text-v1.5.Q8_0"


class FixtureModel:
    """Stands in for the loaded GGUF: real-model vectors, keyed by text."""

    def __init__(self) -> None:
        with np.load(str(bench.FIXTURE), allow_pickle=False) as data:
            self._vectors = dict(zip((str(k) for k in data["keys"]), np.asarray(data["vectors"])))
        self.batches: list[int] = []
        self.fail = False

    def embed(self, texts, normalize=False, truncate=True):
        if self.fail:
            raise RuntimeError("the model stopped")
        self.batches.append(len(texts))
        return [self._vectors[text_key(text)].tolist() for text in texts]


@pytest.fixture()
def desk(tmp_path: Path, monkeypatch):
    db = Database(tmp_path / "engine.db")
    refs = build_corpus(db)
    broker = _configure(db)
    model = FixtureModel()
    loaded: list[str] = []

    def fake_load(model_path: Path):
        loaded.append(str(model_path))
        return model, threading.Lock()

    monkeypatch.setattr(EmbeddingAdapter, "_local_model", staticmethod(fake_load))
    return SimpleNamespace(db=db, refs=refs, broker=broker, model=model, loaded=loaded)


def _assign_embed(db: Database) -> None:
    _profile(db, "embed-model", model=MODEL)
    _assign(db, MEMORY_EMBED_CAPABILITY, ["embed-model"])


def test_no_assignment_means_no_engine_and_todays_recall(desk) -> None:
    import json

    golden = json.loads(bench.GOLDEN.read_text())
    assert resolve_embedder(desk.broker, OWNER) is None
    report = memory_conductor.tick(desk.db, desk.broker)
    assert report["engine"] == "" and report["embedded"] == 0 and report["error"] == ""
    assert report["swept"]["written"] == len(desk.refs)  # chunks are built with no engine
    stats = desk.db.memory_index.stats()
    assert stats["chunks"] > 0 and stats["vectors"] == 0
    assert desk.db.memory.embedder is None
    assert desk.model.batches == []
    assert bench.keyword_snapshot(desk.db, desk.refs) == golden


def test_a_wider_assignment_is_never_used_for_embedding(desk) -> None:
    """The planner lets a capability inherit another assignment.  An embedding
    call must not reach a chat model that way."""
    _profile(desk.db, "chat-model")
    _assign(desk.db, "ask.answer", ["chat-model"])
    InferenceAssignmentService(desk.db).set_assignment(
        OWNER,
        {
            "command_id": "assign-global",
            "expected_revision": 0,
            "scope": {"kind": "global"},
            "entries": [{"profile_id": "chat-model", "profile_revision": 1}],
        },
    )
    assert resolve_embedder(desk.broker, OWNER) is None
    memory_conductor.tick(desk.db, desk.broker)
    assert desk.db.memory.embedder is None and desk.model.batches == []


def test_the_assigned_engine_embeds_through_the_runner_with_a_receipt(desk, capsys) -> None:
    _assign_embed(desk.db)
    before = bench.run(desk.db, desk.refs)

    report = memory_conductor.tick(desk.db, desk.broker)

    stats = desk.db.memory_index.stats()
    assert report["error"] == "" and report["engine"] == f"{MODEL}@256"
    assert report["embedded"] == stats["chunks"] == stats["vectors"] > 0
    # A local engine: small batches, so a live model call seldom meets a busy runtime.
    assert max(desk.model.batches) <= memory_conductor.LOCAL_BATCH
    # The adapter got the path of the assigned deployment's artifact.
    assert set(desk.loaded) == {"/private/embed-model.gguf"}

    embedder = desk.db.memory.embedder
    assert embedder is not None and embedder.boundary == "local"
    assert embedder.deployment_boundary == "same_device"
    # Each batch was one admitted inference.invoke child with a receipt that
    # names the deployment revision.
    receipt = desk.broker.store.receipt(embedder.last_operation_id)
    assert receipt["outcome"] == "succeeded"
    assert receipt["target_ref"] == f"deployment-revision:{embedder.revision_id}"
    assert receipt["actor_identity"] == "memory-conductor"
    with desk.db._connection() as conn:
        assert {row[0] for row in conn.execute("SELECT DISTINCT model_id FROM memory_embeddings")} == {f"{MODEL}@256"}

    # Recall is now fused, through the same callers, with the question
    # embedded by one more admitted child.
    after = bench.run(desk.db, desk.refs)
    with capsys.disabled():
        print()
        print(bench.table("before: no engine", before))
        print(bench.table("after: memory.embed through the router", after))
    assert after["groups"]["paraphrase"]["recall@5"] >= 0.7
    assert after["groups"]["same_word"]["recall@5"] >= before["groups"]["same_word"]["recall@5"]

    # A second tick does no engine work.
    calls = len(desk.model.batches)
    again = memory_conductor.tick(desk.db, desk.broker)
    assert again["embedded"] == 0 and again["swept"]["written"] == 0
    assert len(desk.model.batches) == calls


def test_an_engine_failure_ends_the_tick_and_recall_stays_whole(desk) -> None:
    import json

    golden = json.loads(bench.GOLDEN.read_text())
    _assign_embed(desk.db)
    desk.model.fail = True
    report = memory_conductor.tick(desk.db, desk.broker)
    assert report["error"] and report["embedded"] == 0
    assert desk.db.memory_index.stats()["vectors"] == 0
    # The engine is set and broken: every search still answers, keyword only.
    assert desk.db.memory.embedder is not None
    # No vector exists, so the engine is not called for a question at all.
    assert bench.keyword_snapshot(desk.db, desk.refs) == golden
    # The failed call has a receipt too; it is not a success.
    receipt = desk.broker.store.receipt(desk.db.memory.embedder.last_operation_id)
    assert receipt["outcome"] != "succeeded"

    desk.model.fail = False
    report = memory_conductor.tick(desk.db, desk.broker)  # the next tick completes
    assert report["error"] == "" and report["embedded"] == desk.db.memory_index.stats()["chunks"]


def test_the_embedding_slot_takes_no_chat_lease(desk) -> None:
    """A live local call holds the runtime lease.  The embed batches run all
    the same, and they leave that lease as it is (the concurrent proof is in
    test_memory_review_796.py)."""
    from holdspeak.kernel.local_runtime_lease import acquire_local_runtime_lease

    _assign_embed(desk.db)
    revision = resolve_embedder(desk.broker, OWNER).revision_id
    acquire_local_runtime_lease(desk.db, operation_id="op_live_chat", deployment_revision_id=revision)
    report = memory_conductor.tick(desk.db, desk.broker)
    assert report["error"] == "" and report["embedded"] == desk.db.memory_index.stats()["chunks"] > 0
    with desk.db._connection() as conn:
        leases = conn.execute(
            "SELECT operation_id FROM inference_runtime_leases WHERE state='active'"
        ).fetchall()
    assert [row[0] for row in leases] == ["op_live_chat"]


def test_clearing_the_assignment_turns_recall_back_to_keyword(desk) -> None:
    _assign_embed(desk.db)
    memory_conductor.tick(desk.db, desk.broker)
    assert desk.db.memory.embedder is not None
    assert desk.db.memory.search("where is the company retreat").fusion is not None
    InferenceAssignmentService(desk.db).clear_assignment(
        OWNER,
        {
            "command_id": "clear-embed",
            "expected_revision": 1,
            "scope": {"kind": "capability", "capability_id": MEMORY_EMBED_CAPABILITY},
            "capability_id": MEMORY_EMBED_CAPABILITY,
        },
    )
    memory_conductor.tick(desk.db, desk.broker)
    assert desk.db.memory.embedder is None
    result = desk.db.memory.search("where is the company retreat")
    assert result.fusion is None and result.hits == []


def test_every_caller_gets_fused_hits_with_no_change_at_the_call_site(desk, monkeypatch) -> None:
    """The route (palette, Room search box), the service (MCP memory.search,
    the chat tool) and project grounding (Ask) call what they called before."""
    from unittest.mock import MagicMock

    from fastapi.testclient import TestClient

    import holdspeak.db as hsdb
    from holdspeak.grounding import hydrate_refs_detailed
    from holdspeak.services.memory_service import MemoryService
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    _assign_embed(desk.db)
    memory_conductor.tick(desk.db, desk.broker)
    question = "where is the company retreat"  # no keyword hit: a paraphrase
    offsite = desk.refs["n-offsite"]

    calls_before = len(desk.model.batches)
    service = MemoryService(desk.db).search(OWNER, question)
    assert len(desk.model.batches) == calls_before + 1  # one admitted call for the question
    assert service["hits"][0]["source_ref"] == offsite
    assert service["ranking"]["fusion"]["retrievers"] == ["vector"]

    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: desk.db)
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={"id": "m"})),
        host="127.0.0.1",
        auth_token="owner-secret",
    )
    response = TestClient(server.app).get("/api/memory/search", params={"query": question})
    assert response.status_code == 200
    assert response.json()["hits"][0]["source_ref"] == offsite
    assert set(response.json()["hits"][0]) == set(service["hits"][0])
    # The same question again is not a second engine call.
    assert len(desk.model.batches) == calls_before + 1

    scoped = TestClient(server.app).get(
        "/api/memory/search", params={"query": "crews that cannot get online at the job site", "project_id": "harbor"}
    ).json()
    assert desk.refs["dd-offline"] in [hit["source_ref"] for hit in scoped["hits"][:5]]

    grounded = hydrate_refs_detailed(
        desk.db, [], [], "summary", qualified_refs=["project:harbor"],
        query="crews that cannot get online at the job site",
    )
    assert grounded.selection == "relevance"
    assert desk.refs["dd-offline"] in grounded.source_refs


def test_the_endpoint_leaf_calls_v1_embeddings_and_cuts_the_vectors() -> None:
    calls: list[dict[str, Any]] = []

    class Embeddings:
        def create(self, *, model, input):
            calls.append({"model": model, "input": input})
            rows = [
                SimpleNamespace(index=index, embedding=[float(index + 1)] * 768)
                for index in range(len(input))
            ]
            return SimpleNamespace(data=list(reversed(rows)))  # order is by index, not arrival

    class Engine:
        provider = "cloud"
        cloud_model = "nomic-embed-text-v1.5"
        loaded = 0
        warranted = 0

        def _ensure_openai_client_loaded(self):
            self.loaded += 1
            self._openai_client = SimpleNamespace(embeddings=Embeddings())

        def _remote_completion(self, sender, values):
            # The real engine wraps the send in `run_external_egress`
            # (the operation and receipt are asserted in test_memory_review_796.py).
            self.warranted += 1
            return sender(**values)

    engine = Engine()
    out = EmbeddingAdapter().dispatch(engine, {"texts": ["a", "b"], "dim": 256}, threading.Event())
    assert engine.loaded == 1 and calls == [{"model": "nomic-embed-text-v1.5", "input": ["a", "b"]}]
    assert engine.warranted == 1  # never the SDK client directly
    assert out["provider"] == "cloud" and out["model"] == "nomic-embed-text-v1.5" and out["dim"] == 256
    vectors = np.asarray(out["vectors"], dtype=np.float32)
    assert vectors.shape == (2, 256) and np.allclose(np.linalg.norm(vectors, axis=1), 1.0)


def test_the_adapter_refuses_vectors_it_cannot_use() -> None:
    class Short:
        provider = "cloud"
        cloud_model = "tiny"

        def _ensure_openai_client_loaded(self):
            self._openai_client = SimpleNamespace(
                embeddings=SimpleNamespace(
                    create=lambda **_: SimpleNamespace(data=[SimpleNamespace(index=0, embedding=[1.0] * 64)])
                )
            )

        def _remote_completion(self, sender, values):
            return sender(**values)

    with pytest.raises(ValueError):  # fewer values than the stored size
        EmbeddingAdapter().dispatch(Short(), {"texts": ["a"], "dim": 256}, threading.Event())


def test_the_local_load_sets_the_micro_batch_and_refuses_a_missing_file(tmp_path: Path, monkeypatch) -> None:
    from holdspeak import intel as intel_pkg

    seen: list[dict[str, Any]] = []

    def fake_llama(**kwargs):
        seen.append(kwargs)
        return SimpleNamespace(embed=lambda texts, **_: [[1.0] * 768 for _ in texts])

    monkeypatch.setattr(intel_pkg, "Llama", fake_llama)
    monkeypatch.setattr(memory_engine, "_MODELS", {})
    with pytest.raises(MemoryEngineError):
        EmbeddingAdapter._local_model(tmp_path / "absent.gguf")
    model_file = tmp_path / "embed.gguf"
    model_file.write_bytes(b"gguf")
    EmbeddingAdapter._local_model(model_file)
    EmbeddingAdapter._local_model(model_file)  # loaded once
    assert len(seen) == 1
    # llama.cpp aborts the process on a batch over n_ubatch for an encoder model.
    assert seen[0]["embedding"] is True
    assert seen[0]["n_ubatch"] == seen[0]["n_batch"] == seen[0]["n_ctx"] == 2048


def test_the_conductor_runs_only_in_the_database_owner(desk, monkeypatch) -> None:
    import holdspeak.db as hsdb
    from holdspeak import intel_queue_conductor
    from holdspeak.kernel import runtime as kernel_runtime

    monkeypatch.setattr(intel_queue_conductor, "owns_database", lambda: False)
    assert memory_conductor.start_memory_conductor() is None

    monkeypatch.setattr(intel_queue_conductor, "owns_database", lambda: True)
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: desk.db)
    monkeypatch.setattr(kernel_runtime, "_service", lambda: desk.broker)
    _assign_embed(desk.db)
    worker = memory_conductor.start_memory_conductor(poll_seconds=5)
    try:
        assert worker is not None and memory_conductor.start_memory_conductor() is worker
        for _ in range(200):
            if worker.last_report.get("embedded"):
                break
            threading.Event().wait(0.05)
        assert worker.last_report["embedded"] == desk.db.memory_index.stats()["chunks"] > 0
        desk.db.notes.upsert(note_id="late", title="Offsite", body_markdown="The team offsite is in Lisbon in March. Priya books the venue.")
        memory_conductor.wake()
        for _ in range(200):
            if "note:late" in desk.db.memory_index.ledger(["note"]):
                break
            threading.Event().wait(0.05)
        assert "note:late" in desk.db.memory_index.ledger(["note"])
    finally:
        memory_conductor.stop_memory_conductor(timeout=10)
    assert not worker.is_alive()


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
    _profile(db, "embed-model", model=MODEL)
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
