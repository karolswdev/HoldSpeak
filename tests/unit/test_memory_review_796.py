"""Astra's review of PR #796: four findings, one fence each.

The router, the planner, the assignment service and the runner are real.
"""
from __future__ import annotations

import asyncio
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
from holdspeak.memory.engine import EmbeddingAdapter, MEMORY_EMBED_CAPABILITY
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.memory_service import MemoryService

from tests.memory_bench.corpus import build_corpus
from tests.unit.test_memory_engine import MODEL, FixtureModel
from tests.unit.test_phase143_inference_assignments import OWNER, _profile
from tests.unit.test_phase200_readiness import _assign


class SlowFixtureModel(FixtureModel):
    def __init__(self) -> None:
        super().__init__()
        self.delay = 0.0
        self.entered = threading.Event()

    def embed(self, texts, normalize=False, truncate=True):
        self.entered.set()
        if self.delay:
            time.sleep(self.delay)
        try:
            return super().embed(texts, normalize=normalize, truncate=truncate)
        except KeyError:
            self.batches.append(len(texts))
            return [[1.0] + [0.0] * 255 for _ in texts]  # a question outside the fixture


@pytest.fixture()
def desk(tmp_path: Path, monkeypatch):
    db = Database(tmp_path / "engine.db")
    refs = build_corpus(db)
    broker = _configure(db)
    model = SlowFixtureModel()
    monkeypatch.setattr(
        EmbeddingAdapter, "_local_model", staticmethod(lambda path: (model, threading.Lock()))
    )
    _profile(db, "embed-model", model=MODEL, claims=("embedding",))
    _assign(db, MEMORY_EMBED_CAPABILITY, ["embed-model"])
    return SimpleNamespace(db=db, refs=refs, broker=broker, model=model, tmp_path=tmp_path)


def _operations(db: Database) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT operation_id,name,principal_identity,parent_operation_id,state"
                " FROM kernel_operations ORDER BY created_at,rowid"
            )
        ]


# ── 1: search never blocks the hub's event loop and never hangs ───────────


def test_a_slow_engine_does_not_block_the_event_loop_or_the_search(desk, monkeypatch) -> None:
    import httpx

    import holdspeak.db as hsdb
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    memory_conductor.tick(desk.db, desk.broker)
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: desk.db)
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={"id": "m"})),
        host="127.0.0.1", auth_token="owner-secret",
    )
    desk.model.delay = 1.0  # the engine now takes one second for a question

    async def run() -> tuple[float, float, dict[str, Any]]:
        gaps: list[float] = []
        stop = asyncio.Event()

        async def heartbeat() -> None:
            last = time.perf_counter()
            while not stop.is_set():
                await asyncio.sleep(0.05)
                now = time.perf_counter()
                gaps.append(now - last)
                last = now

        beat = asyncio.create_task(heartbeat())
        await asyncio.sleep(0.1)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=server.app), base_url="http://hub",
            headers={"X-HoldSpeak-Token": "owner-secret"},
        ) as client:
            started = time.perf_counter()
            response = await client.get("/api/memory/search", params={"query": "offsite in Lisbon"})
            elapsed = time.perf_counter() - started
        stop.set()
        await beat
        assert response.status_code == 200, response.text
        return max(gaps), elapsed, response.json()

    worst_gap, elapsed, body = asyncio.run(run())
    assert worst_gap < 0.3, f"the event loop stalled for {worst_gap:.3f}s"
    assert elapsed < 0.9, f"the search waited {elapsed:.3f}s for the engine"
    # The answer for THIS query is the keyword answer, and it says why.
    assert body["hits"] and body["hits"][0]["source_ref"] == desk.refs["n-offsite"]
    assert "fusion" not in body["ranking"]
    assert body["ranking"]["engine"]["outcome"] == "timeout"
    # The slow call still finishes; the same question is then fused from the cache.
    for _ in range(60):
        again = desk.db.memory.search("offsite in Lisbon")
        if again.fusion is not None:
            break
        time.sleep(0.05)
    assert again.fusion is not None


# ── 2: background embedding never refuses a foreground local call ─────────


def _chat(desk, revision: str) -> Any:
    payload = {"system_prompt": "s", "user_prompt": "u"}
    request = InvocationRequest(
        deployment_revision=revision,
        definition_origin=ServiceContract.for_payload("ask.answer", "1", payload),
        deadline_at=time.time() + 30, payload=payload,
    )
    with _as_principal(OWNER):
        return desk.broker.inference_runner.invoke(request, CanonicalPromptAdapter(), publish=lambda value: "chat:1")


def test_a_local_chat_call_is_never_refused_by_a_background_embed_batch(desk) -> None:
    from holdspeak.services.project_update_service import _resolve_for_capability

    _profile(desk.db, "chat-model")
    _assign(desk.db, "ask.answer", ["chat-model"])
    chat_revision = _resolve_for_capability(desk.broker, "ask.answer")[0]
    chat_gate = threading.Event()
    chat_entered = threading.Event()

    class ChatEngine:
        active_provider = "fixture"
        active_model = "chat"

        def run_prompt(self, **_kwargs):
            chat_entered.set()
            chat_gate.wait(5)
            return "answer"

    def factory(revision, **_kwargs):
        if revision.id == chat_revision:
            return ChatEngine()
        return SimpleNamespace(provider="local", model_path="/private/embed-model.gguf")

    desk.broker.inference_runner._engine_factory = factory

    # A: the chat call starts WHILE an embed batch is inside the model.
    desk.model.delay = 0.6
    report: dict[str, Any] = {}
    worker = threading.Thread(target=lambda: report.update(memory_conductor.tick(desk.db, desk.broker)))
    worker.start()
    assert desk.model.entered.wait(5)
    chat_gate.set()
    outcome = _chat(desk, chat_revision)
    assert outcome.outcome == "succeeded", (outcome.outcome, outcome.error, outcome.runner_signal)
    desk.model.delay = 0.0
    worker.join(30)
    assert report["error"] == "" and report["embedded"] == desk.db.memory_index.stats()["chunks"] > 0

    # B: an embed call WHILE a local chat call is inside its model.
    chat_gate.clear()
    chat_entered.clear()
    result: list[Any] = []
    chatting = threading.Thread(target=lambda: result.append(_chat(desk, chat_revision)))
    chatting.start()
    assert chat_entered.wait(5)
    vector = desk.db.memory.embedder.embed_query("a question asked during the chat call")
    assert vector.shape == (256,)
    chat_gate.set()
    chatting.join(30)
    assert result[0].outcome == "succeeded"


# ── 3: an endpoint keeps the caller, the egress receipt and the boundary ──


def test_an_endpoint_search_keeps_caller_egress_and_boundary(desk, monkeypatch) -> None:
    from holdspeak.intel.engine import MeetingIntel

    import holdspeak.db as hsdb

    db = Database(desk.tmp_path / "endpoint.db")
    refs = build_corpus(db)
    # The engine's egress path asks the process for its broker, as the hub does.
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    broker = _configure(db)
    _profile(db, "lan-embed", model=MODEL, boundary="private_network", claims=("embedding",))
    _assign(db, MEMORY_EMBED_CAPABILITY, ["lan-embed"])
    fixture = FixtureModel()
    calls: list[int] = []

    class Embeddings:
        def create(self, *, model, input):
            calls.append(len(input))
            try:
                rows = fixture.embed(list(input))
            except KeyError:
                rows = [[1.0] + [0.0] * 255 for _ in input]
            return SimpleNamespace(data=[SimpleNamespace(index=i, embedding=row) for i, row in enumerate(rows)])

    def factory(revision, **_kwargs):
        engine = MeetingIntel(provider="cloud", cloud_model="nomic-embed-text-v1.5", cloud_base_url="http://embed.lan:8080/v1")
        engine._ensure_openai_client_loaded = lambda: setattr(engine, "_openai_client", SimpleNamespace(embeddings=Embeddings()))
        return engine

    broker.inference_runner._engine_factory = factory
    report = memory_conductor.tick(db, broker)
    assert report["error"] == "" and report["embedded"] > 0

    before = len(_operations(db))
    caller = Principal(PrincipalKind.OWNER, "local-mcp")
    answer = MemoryService(db).search(caller, "where is the company retreat")
    assert answer["hits"][0]["source_ref"] == refs["n-offsite"]
    new = _operations(db)[before:]

    # (a) the admitted call names the REAL caller.
    invoke = [op for op in new if op["name"] == "inference.invoke"]
    assert [op["principal_identity"] for op in invoke] == ["local-mcp"]
    # (b) the remote call wrote the external.egress operation and its receipt.
    egress = [op for op in new if op["name"] == "external.egress"]
    assert len(egress) == 1 and egress[0]["state"] in ("succeeded", "completed"), new
    assert broker.store.receipt(egress[0]["operation_id"])["outcome"] == "succeeded"
    # (c) the response carries the boundary, for the badge.
    assert answer["ranking"]["engine"]["boundary"] == "private_network"
    assert answer["ranking"]["engine"]["outcome"] == "fused"
    assert answer["ranking"]["fusion"]["boundary"] == "private_network"
    # The background batches wrote egress operations too, as the conductor.
    batch_egress = [op for op in _operations(db)[:before] if op["name"] == "external.egress"]
    assert len(batch_egress) == len(calls) - 1 > 0


# ── 4: a cleared assignment stops engine calls at once ────────────────────


def test_the_search_after_a_clear_makes_no_engine_call(desk) -> None:
    memory_conductor.tick(desk.db, desk.broker)
    assert desk.db.memory.search("where is the company retreat").fusion is not None
    calls = len(desk.model.batches)

    InferenceAssignmentService(desk.db).clear_assignment(
        OWNER,
        {
            "command_id": "clear-embed", "expected_revision": 1,
            "scope": {"kind": "capability", "capability_id": MEMORY_EMBED_CAPABILITY},
            "capability_id": MEMORY_EMBED_CAPABILITY,
        },
    )
    # No tick.  A question never asked before, and one that is in the cache.
    for question in ("who covers pager duty on Saturdays", "where is the company retreat"):
        answer = desk.db.memory.search(question)
        assert answer.fusion is None and answer.hits == []
        assert "engine" not in answer.to_dict()["ranking"]
    assert len(desk.model.batches) == calls
    # The background step stops too.
    desk.db.notes.upsert(note_id="late", title="Late", body_markdown="A note written after the clear.")
    from holdspeak.memory.retain import embed_pending, sweep

    sweep(desk.db)
    with pytest.raises(Exception):
        embed_pending(desk.db, desk.db.memory.embedder)
    assert len(desk.model.batches) == calls

    # A new assignment is used from the next tick on.
    _assign_again = InferenceAssignmentService(desk.db).set_assignment(
        OWNER,
        {
            "command_id": "assign-embed-again", "expected_revision": 2,
            "scope": {"kind": "capability", "capability_id": MEMORY_EMBED_CAPABILITY},
            "entries": [{"profile_id": "embed-model", "profile_revision": 1}],
        },
    )
    assert desk.db.memory.search("where is the company retreat").fusion is None  # not until a tick
    memory_conductor.tick(desk.db, desk.broker)
    assert desk.db.memory.search("where is the company retreat").fusion is not None
