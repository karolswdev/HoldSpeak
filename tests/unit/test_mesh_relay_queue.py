"""HS-85-01 — the mesh relay queue + the node wire.

Hub-local run rows (never a synced kind): enqueue → a node's worker claims →
complete/fail, with liveness born from the worker's own polling and deadlines
enforced lazily on read — a dead worker strands a run for at most its
deadline, never forever.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes.mesh import build_mesh_router

T0 = datetime(2026, 7, 7, 12, 0, 0)


@pytest.fixture
def db(tmp_path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


@pytest.fixture
def client(db, monkeypatch) -> TestClient:
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    app.include_router(build_mesh_router(WebContext(get_state=lambda: {})))
    return TestClient(app)


# ── the repository lifecycle ─────────────────────────────────────────────


def test_enqueue_claim_complete_round_trips_verbatim(db) -> None:
    job = db.mesh_relay.enqueue(
        node="walk-edge",
        system_prompt="You are brief.",
        user_prompt="What is dictation?",
        temperature=0.2,
        max_tokens=64,
        model_hint="Qwen3.5-9B",
        now=T0,
    )
    claimed = db.mesh_relay.claim_next("walk-edge", now=T0 + timedelta(seconds=1))
    assert claimed is not None and claimed.id == job.id
    assert claimed.status == "running" and claimed.claimed_at is not None
    assert claimed.system_prompt == "You are brief."
    assert claimed.user_prompt == "What is dictation?"
    assert claimed.temperature == 0.2 and claimed.max_tokens == 64
    assert claimed.model_hint == "Qwen3.5-9B"

    assert db.mesh_relay.complete(job.id, result="Speaking words.", now=T0 + timedelta(seconds=2))
    done = db.mesh_relay.get(job.id, now=T0 + timedelta(seconds=3))
    assert done.status == "completed" and done.result == "Speaking words."


def test_claim_is_per_node(db) -> None:
    db.mesh_relay.enqueue(node="node-a", user_prompt="for a", now=T0)
    assert db.mesh_relay.claim_next("node-b", now=T0) is None
    claimed = db.mesh_relay.claim_next("node-a", now=T0)
    assert claimed is not None and claimed.user_prompt == "for a"


def test_claim_orders_oldest_first(db) -> None:
    first = db.mesh_relay.enqueue(node="n", user_prompt="one", now=T0)
    db.mesh_relay.enqueue(node="n", user_prompt="two", now=T0 + timedelta(seconds=1))
    assert db.mesh_relay.claim_next("n", now=T0 + timedelta(seconds=2)).id == first.id


def test_fail_carries_the_node_error_verbatim(db) -> None:
    job = db.mesh_relay.enqueue(node="n", user_prompt="x", now=T0)
    db.mesh_relay.claim_next("n", now=T0)
    assert db.mesh_relay.fail(job.id, error="llama exploded: OOM", now=T0 + timedelta(seconds=5))
    failed = db.mesh_relay.get(job.id, now=T0 + timedelta(seconds=6))
    assert failed.status == "failed" and failed.error == "llama exploded: OOM"


# ── deadlines: never a silent hang ───────────────────────────────────────


def test_unclaimed_job_fails_at_deadline_with_a_named_reason(db) -> None:
    job = db.mesh_relay.enqueue(node="ghost", user_prompt="x", deadline_seconds=30, now=T0)
    read = db.mesh_relay.get(job.id, now=T0 + timedelta(seconds=31))
    assert read.status == "failed"
    assert "node ghost never claimed the run" in read.error


def test_claimed_but_abandoned_job_fails_at_deadline(db) -> None:
    job = db.mesh_relay.enqueue(node="flaky", user_prompt="x", deadline_seconds=30, now=T0)
    db.mesh_relay.claim_next("flaky", now=T0 + timedelta(seconds=1))
    read = db.mesh_relay.get(job.id, now=T0 + timedelta(seconds=31))
    assert read.status == "failed"
    assert "claimed the run but never completed it" in read.error


def test_late_completion_is_refused(db) -> None:
    job = db.mesh_relay.enqueue(node="slow", user_prompt="x", deadline_seconds=30, now=T0)
    db.mesh_relay.claim_next("slow", now=T0 + timedelta(seconds=1))
    assert not db.mesh_relay.complete(job.id, result="too late", now=T0 + timedelta(seconds=40))
    assert db.mesh_relay.get(job.id, now=T0 + timedelta(seconds=41)).status == "failed"


# ── liveness: born from the worker's polling ─────────────────────────────


def test_claim_poll_stamps_liveness_and_ages_out(db) -> None:
    db.mesh_relay.claim_next("edge-1", now=T0)  # empty poll still stamps
    assert "edge-1" in db.mesh_relay.live_nodes(15, now=T0 + timedelta(seconds=10))
    assert "edge-1" not in db.mesh_relay.live_nodes(15, now=T0 + timedelta(seconds=20))


def test_worker_last_seen_reads_back(db) -> None:
    db.mesh_relay.touch_worker("edge-2", now=T0)
    assert db.mesh_relay.worker_last_seen("edge-2") == T0
    assert db.mesh_relay.worker_last_seen("never-seen") is None


# ── the node wire (routes) ───────────────────────────────────────────────


def test_wire_claim_complete_lifecycle(db, client) -> None:
    # the wire runs on the real clock — enqueue there too, or the deadline
    # (T0 + 120s) is already in the past and the claim honestly expires it
    job = db.mesh_relay.enqueue(node="wire-node", user_prompt="over the wire", now=datetime.now())

    resp = client.post("/api/mesh/relay/claim", json={"node": "wire-node"})
    assert resp.status_code == 200
    claimed = resp.json()["job"]
    assert claimed["id"] == job.id and claimed["user_prompt"] == "over the wire"

    resp = client.post(f"/api/mesh/relay/{job.id}/complete", json={"result": "answered"})
    assert resp.status_code == 200 and resp.json() == {"success": True}
    assert db.mesh_relay.get(job.id).result == "answered"

    # an empty poll returns null and still counts as liveness
    resp = client.post("/api/mesh/relay/claim", json={"node": "wire-node"})
    assert resp.status_code == 200 and resp.json()["job"] is None
    assert db.mesh_relay.worker_last_seen("wire-node") is not None


def test_wire_fail_and_validation(db, client) -> None:
    job = db.mesh_relay.enqueue(node="wire-node", user_prompt="x", now=datetime.now())
    client.post("/api/mesh/relay/claim", json={"node": "wire-node"})

    assert client.post("/api/mesh/relay/claim", json={}).status_code == 400
    assert client.post(f"/api/mesh/relay/{job.id}/complete", json={"result": ""}).status_code == 400
    assert client.post(f"/api/mesh/relay/{job.id}/fail", json={}).status_code == 400

    resp = client.post(f"/api/mesh/relay/{job.id}/fail", json={"error": "no model"})
    assert resp.status_code == 200
    # terminal jobs refuse further outcomes by name
    assert client.post(f"/api/mesh/relay/{job.id}/complete", json={"result": "late"}).status_code == 409
    assert client.post(f"/api/mesh/relay/{job.id}/fail", json={"error": "again"}).status_code == 409
    assert client.post("/api/mesh/relay/relay_unknown/fail", json={"error": "x"}).status_code == 409


# ── never a synced kind ──────────────────────────────────────────────────


def test_relay_rows_never_ride_sync(db) -> None:
    from holdspeak.web.routes.sync import SYNC_KINDS, _MERGEABLE

    assert not any("relay" in k for k in SYNC_KINDS)
    assert not any("relay" in k for k in _MERGEABLE)
