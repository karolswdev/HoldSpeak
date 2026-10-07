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
        #: When set, an embed holds until the test opens the gate (R5: the
        #: slow engine is driven by the test, not by a wall-clock delay).
        self.gate: threading.Event | None = None

    def embed(self, texts, normalize=False, truncate=True):
        self.entered.set()
        if self.gate is not None:
            assert self.gate.wait(60), "the test never opened the engine gate"
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
    """The engine is held on a gate the test opens, so nothing here reads a
    wall clock (R5: the old 0.3 s loop-gap and 0.9 s search bounds tripped
    under FAST load).

    1. The search answers by keyword while the engine is STILL held: it did
       not wait for the engine (the 0.5 s budget ran out instead).
    2. With the budget raised far past the test, a held engine keeps one
       search in flight, and the event loop still runs other work: the test's
       own coroutine sees the engine entered while that search is pending.
    3. Once the engine answers, the same question is fused from the cache.
    """
    import httpx

    import holdspeak.db as hsdb
    import holdspeak.memory.engine as engine_module
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    memory_conductor.tick(desk.db, desk.broker)
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: desk.db)
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={"id": "m"})),
        host="127.0.0.1", auth_token="owner-secret",
    )

    def client() -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=server.app), base_url="http://hub",
            headers={"X-HoldSpeak-Token": "owner-secret"}, timeout=120,
        )

    async def until(flag: threading.Event) -> None:
        for _ in range(6000):  # bounded at 60 s; returns as soon as it is set
            if flag.is_set():
                return
            await asyncio.sleep(0.01)
        raise AssertionError("the engine was never entered")

    # 1: the search does not wait for a held engine.
    held = desk.model.gate = threading.Event()

    async def keyword_answer() -> tuple[dict[str, Any], bool]:
        async with client() as c:
            response = await c.get("/api/memory/search", params={"query": "offsite in Lisbon"})
        assert response.status_code == 200, response.text
        return response.json(), held.is_set()

    try:
        body, engine_released = asyncio.run(keyword_answer())
    finally:
        held.set()
    assert engine_released is False, "the search returned only after the engine answered"
    # The answer for THIS query is the keyword answer, and it says why.
    assert body["hits"] and body["hits"][0]["source_ref"] == desk.refs["n-offsite"]
    assert "fusion" not in body["ranking"]
    assert body["ranking"]["engine"]["outcome"] == "timeout"
    # 3: the held call finishes once released; the same question is fused.
    deadline = time.monotonic() + 30
    again = desk.db.memory.search("offsite in Lisbon")
    while again.fusion is None and time.monotonic() < deadline:
        time.sleep(0.05)
        again = desk.db.memory.search("offsite in Lisbon")
    assert again.fusion is not None

    # 2: a search in flight on a held engine leaves the event loop free.
    monkeypatch.setattr(engine_module, "QUERY_TIMEOUT_SECONDS", 120.0)
    desk.model.entered = threading.Event()
    gate = desk.model.gate = threading.Event()

    async def loop_stays_free() -> tuple[bool, int, dict[str, Any]]:
        async with client() as c:
            search = asyncio.create_task(
                c.get("/api/memory/search", params={"query": "a question for the loop probe"})
            )
            try:
                await until(desk.model.entered)  # this coroutine ran: the loop is free
                pending = not search.done()
            finally:
                gate.set()
            response = await search
        return pending, response.status_code, response.json()

    pending, status, probe = asyncio.run(loop_stays_free())
    assert pending, "the search finished before the held engine was released"
    assert status == 200, probe
    # The engine answered inside the search: the test's coroutine opened the
    # gate while the search waited. A blocked loop could not have, and the
    # search would have ended on its budget ("timeout").
    assert probe["ranking"]["engine"]["outcome"] in {"fused", "no_match"}, probe["ranking"]

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


def test_the_search_after_a_clear_makes_no_engine_call(desk, monkeypatch) -> None:
    # This test is about the clear, not the search budget (the slow-engine
    # test above owns that). Under FAST load a first-time question took more
    # than the 0.5 s budget, so the search ended "timeout" (R5); give it room.
    import holdspeak.memory.engine as engine_module

    monkeypatch.setattr(engine_module, "QUERY_TIMEOUT_SECONDS", 60.0)
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
