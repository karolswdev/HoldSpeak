"""HS-85-01 — the mesh relay queue + the node wire.

Hub-local run rows (never a synced kind): enqueue → a node's worker claims →
complete/fail, with liveness born from the worker's own polling and deadlines
enforced lazily on read — a dead worker strands a run for at most its
deadline, never forever.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.services.mesh_service import MeshService
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

    class Store:
        def valid_warrant(self, warrant):
            return warrant.get("signature") == "signed"

        def operation(self, operation_id):
            return {
                "warrant": _relay_envelope()["warrant"],
                "target_ref": "deployment-revision:dep_wire",
                "warrant_revoked": False,
                "state": "claimed",
            }

    app = FastAPI()
    app.include_router(build_mesh_router(WebContext(
        get_state=lambda: {}, mesh_service=MeshService(db, kernel=SimpleNamespace(store=Store()))
    )))
    return TestClient(app)


def _relay_envelope() -> dict:
    binding = "deployment-revision:dep_wire"
    return {
        "deployment_revision": {"id": "dep_wire"},
        "warrant": {
            "operation_id": "op_wire", "target_binding": binding,
            "signature": "signed", "execution_expires_at": 9_999_999_999,
        },
    }


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


def test_liveness_is_bound_to_the_exact_credential_generation(db) -> None:
    """HS-131-16 (repair R8): a name is not an identity, and a poll is not
    evidence about a credential that did not make it.

    A worker still polling under generation 1 must never make generation 2 look
    live: work addressed to the new credential would be dispatched to a node that
    is not actually there under it. Liveness is keyed, stamped, and asked for by
    the exact `(node_id, credential_generation)` pair.
    """
    db.mesh_relay.touch_worker("edge-3", node_id="node_e3", generation=1, now=T0)

    assert db.mesh_relay.node_live("node_e3", 1, 15, now=T0 + timedelta(seconds=10))
    # The generation that never polled is not live on the strength of one that did.
    assert not db.mesh_relay.node_live("node_e3", 2, 15, now=T0 + timedelta(seconds=10))
    # Nor is another node with the same generation.
    assert not db.mesh_relay.node_live("node_other", 1, 15, now=T0 + timedelta(seconds=10))
    # Nor an unbound or absent identity.
    assert not db.mesh_relay.node_live("", 1, 15, now=T0)
    assert not db.mesh_relay.node_live("node_e3", 0, 15, now=T0)

    # The window is bounded on BOTH sides: too old is not live, and neither is a
    # stamp from the future — a backward clock cannot resurrect a silent node.
    assert not db.mesh_relay.node_live("node_e3", 1, 15, now=T0 + timedelta(seconds=20))
    assert not db.mesh_relay.node_live("node_e3", 1, 15, now=T0 - timedelta(seconds=1))
    assert db.mesh_relay.node_live("node_e3", 1, 15, now=T0)  # 0 <= age is live

    # After a rotation the worker polls under the NEW generation, and the old one
    # stops looking live immediately.
    db.mesh_relay.touch_worker("edge-3", node_id="node_e3", generation=2, now=T0)
    assert db.mesh_relay.node_live("node_e3", 2, 15, now=T0)
    assert not db.mesh_relay.node_live("node_e3", 1, 15, now=T0)


def test_an_authenticated_claim_stamps_the_identity_that_polled(db) -> None:
    """The production stamp comes from the authenticated claim, not a caller."""
    db.mesh_relay.claim_signed(
        node_name="edge-4", node_id="node_e4", generation=3,
        claim_nonce="n", authorize=lambda _job, _conn: None, now=T0,
    )
    assert db.mesh_relay.node_live("node_e4", 3, 15, now=T0)
    assert not db.mesh_relay.node_live("node_e4", 2, 15, now=T0)
    # An empty poll still counts as liveness, exactly as it always has.
    assert db.mesh_relay.worker_last_seen("edge-4") == T0


# ── the node wire (routes) ───────────────────────────────────────────────


def test_the_wire_refuses_every_principal_that_is_not_a_node(db, client) -> None:
    """HS-131-16: the relay legs are a NODE protocol, not an owner API.

    This used to be the open door — an unauthenticated POST naming a node in its
    own body claimed that node's work. Article XI.3 says the caller supplies
    neither its principal nor its authority, so the whole leg now refuses before
    any queue mutation, and `payload["node"]` is not a credential.
    """
    job = db.mesh_relay.enqueue(
        node="wire-node", user_prompt="over the wire", envelope=_relay_envelope(),
        now=datetime.now(),
    )

    claim = client.post("/api/mesh/relay/claim", json={"node": "wire-node"})
    assert claim.status_code == 403
    assert claim.json()["code"] == "mesh_node_authentication_required"

    for path, body in (
        (f"/api/mesh/relay/{job.id}/complete", {"result": "answered"}),
        (f"/api/mesh/relay/{job.id}/fail", {"error": "no model"}),
    ):
        resp = client.post(path, json=body)
        assert resp.status_code == 403
        assert resp.json()["code"] == "mesh_node_authentication_required"

    # Refused means REFUSED: the row is untouched and no liveness was stamped.
    assert db.mesh_relay.get(job.id).status == "queued"
    assert db.mesh_relay.worker_last_seen("wire-node") is None


def test_the_relay_edge_right_is_the_node_protocol_right() -> None:
    """The centralized route table, not the route body, is where this is decided."""
    from holdspeak.principals import PrincipalKind, Principal, PrincipalRight, required_right

    for path in (
        "/api/mesh/relay/claim",
        "/api/mesh/relay/relay_x/complete",
        "/api/mesh/relay/relay_x/fail",
    ):
        assert required_right("POST", path) is PrincipalRight.NODE_LINK
    # An owner has every right, so the right alone is not the whole gate — the
    # service's own `PrincipalKind.NODE` check is (proved in the authority suite).
    assert Principal(PrincipalKind.OWNER, "o").permits(PrincipalRight.NODE_LINK)
    assert not Principal(PrincipalKind.AGENT, "a").permits(PrincipalRight.NODE_LINK)


def test_an_unbound_row_cannot_be_claimed_by_the_authenticated_path(db) -> None:
    """A job enqueued without a stable destination binding is unclaimable.

    Enqueue binds `(node_id, credential_generation)`; the authenticated claim
    matches on both. A legacy or unpaired row therefore expires honestly at its
    deadline rather than dispatching to whoever asks for it.
    """
    db.mesh_relay.enqueue(node="wire-node", user_prompt="x", now=datetime.now())
    claimed = db.mesh_relay.claim_signed(
        node_name="wire-node", node_id="node_abc", generation=1,
        claim_nonce="n", authorize=lambda job, _conn: {"offer": {}, "signature": "s"},
    )
    assert claimed is None


def test_settlement_is_one_guarded_transactional_election(db) -> None:
    """HS-131-16 (repair R6): first settlement is ONE `BEGIN IMMEDIATE` election.

    The decision function runs inside the transaction and sees the stored relay
    proof; the terminal update is guarded on the exact claiming node and
    generation. Whatever commits first wins — everything after it finds nothing
    left to settle and cannot overwrite stored terminal proof.
    """
    job = db.mesh_relay.enqueue(
        node="wire-node", user_prompt="x", destination_node_id="node_a",
        destination_generation=2, now=datetime.now(),
    )
    signed = {"offer": {"offer_id": "offer_1"}, "signature": "sig"}
    claimed = db.mesh_relay.claim_signed(
        node_name="wire-node", node_id="node_a", generation=2,
        claim_nonce="nonce", authorize=lambda _job, _conn: signed,
    )
    assert claimed is not None and claimed[0].id == job.id
    proof = db.mesh_relay.proof(job.id)
    assert proof["claimed_by_node_id"] == "node_a" and proof["claimed_generation"] == 2
    assert proof["dispatch_offer"] == signed and proof["claim_nonce"] == "nonce"

    seen: list[dict] = []

    def settle(node_id: str, generation: int, status: str, **fields):
        def decide(inside, conn):
            # Repair R2.10: the callback decides on the transaction's OWN
            # connection, so every read it makes is the snapshot the guarded
            # update commits against.
            assert conn is not None
            seen.append(dict(inside or {}))
            return {"status": status, **fields}

        return db.mesh_relay.settle_first(
            job.id, node_id=node_id, generation=generation, decide=decide
        )

    # Another node, and the same node under a moved generation, both refuse.
    assert settle("node_b", 2, "completed", result="x") is False
    assert settle("node_a", 3, "completed", result="x") is False
    # The decision ran INSIDE the transaction, against the stored proof.
    assert seen[0]["claimed_by_node_id"] == "node_a"
    assert seen[0]["dispatch_offer"] == signed

    assert settle(
        "node_a", 2, "completed", result="answered",
        worker_terminal={"report_schema": 1},
    )
    assert db.mesh_relay.get(job.id).result == "answered"
    # A second settlement of a terminal job never mutates stored proof.
    assert settle("node_a", 2, "failed", error="late") is False
    assert db.mesh_relay.get(job.id).result == "answered"

    # A refusal raised inside the election leaves the row exactly as it was.
    def refuse(_inside, _conn):
        raise RuntimeError("no")

    with pytest.raises(RuntimeError):
        db.mesh_relay.settle_first(
            job.id, node_id="node_a", generation=2, decide=refuse
        )
    assert db.mesh_relay.get(job.id).result == "answered"


# ── never a synced kind ──────────────────────────────────────────────────


def test_relay_rows_never_ride_sync(db) -> None:
    from holdspeak.web.routes.sync import SYNC_KINDS, _MERGEABLE

    assert not any("relay" in k for k in SYNC_KINDS)
    assert not any("relay" in k for k in _MERGEABLE)
