"""HS-131-16 — the mesh receiver proves authority locally.

The worker's physical model attempt used to be a side door: a hand-built envelope
with nonempty warrant-shaped strings was enough to construct an engine and call
`run_prompt`. Article XI.2 does not exempt it for crossing a process boundary, and
XI.3 does not let `payload["node"]` be a principal.

These are the focused, deterministic proofs for the two-proof protocol that
replaces it: the hub authenticates itself with a per-node Ed25519 signature the
node's own bearer token cannot forge, and the worker admits and receipts every
physical attempt through its OWN kernel before anything reaches a provider.
"""

from __future__ import annotations

import json
import time
from dataclasses import replace
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.delivery.node_credentials import MeshHubPin
from holdspeak.delivery.node_link import NodeTokenStore
from holdspeak.commands.mesh_serve import MeshServeWorker
from holdspeak.deployment_revisions import DeploymentRevision
from holdspeak.inference_targets import DeploymentIdentity
from holdspeak.kernel.mesh_local_authority import (
    derive_local_authority,
    reserve_local_execution,
)
from holdspeak.kernel.runtime import _configure
from holdspeak.mesh_authority import ed25519, verify_offer
from holdspeak.mesh_authority.offer import (
    canonical_offer_bytes,
    consume_verified_offer,
    payload_digest,
)
from holdspeak.mesh_authority.refusals import MeshAuthorityRefused
from holdspeak.mesh_authority.revision import derive_worker_execution_revision
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, ServiceError
from holdspeak.services.mesh_service import MeshService

PROMPT_SENTINEL = "SENTINEL-PROMPT-do-not-journal"
RESULT_SENTINEL = "SENTINEL-RESULT-do-not-journal"

#: The relay revision a hub freezes for a mesh destination: it names the REMOTE
#: work, so the worker derives its own executable revision from it.
RELAY_IDENTITY = DeploymentIdentity(
    destination_id="edge-profile",
    kind="mesh_node",
    engine="node_runtime",
    model="qwen3.5-4b",
    node="edge",
    boundary="private_mesh",
    model_path=None,
    endpoint="http://192.168.1.43:8080/v1",
    secret_slot="",
)


class _Store:
    """A hub kernel store whose warrant is live until the test says otherwise.

    The row it hands back carries ``operation_id``, ``name`` and ``version``
    because the real ``kernel_operations`` row does: repair R2.1 makes the hub
    read what the operation ACTUALLY is rather than writing the expected
    constant into an offer regardless of state.
    """

    def __init__(self, warrant: dict) -> None:
        self.warrant = warrant
        self.state = "claimed"
        self.revoked = False
        self.name = "inference.invoke"
        self.version = 1

    def valid_warrant(self, warrant):
        return warrant.get("signature") == self.warrant["signature"]

    def operation(self, operation_id):
        if operation_id != self.warrant["operation_id"]:
            return None
        return {
            "operation_id": operation_id,
            "name": self.name,
            "version": self.version,
            "warrant": self.warrant,
            "target_ref": self.warrant["target_binding"],
            "warrant_revoked": self.revoked,
            "state": self.state,
        }


class Rig:
    """One paired node, one hub queue, one worker kernel."""

    def __init__(self, tmp_path):
        self.relay_revision = DeploymentRevision.from_identity(RELAY_IDENTITY)
        self.execution_revision = derive_worker_execution_revision(self.relay_revision)
        self.hub_db = Database(tmp_path / "hub.db")
        self.worker_db = Database(tmp_path / "worker.db")
        self.worker_broker = _configure(self.worker_db)
        self.store = NodeTokenStore(tmp_path / "nodes.json")
        self.node_id, self.token, snapshot = self.store.pair("edge")
        # The EDGE snapshot, exactly as the middleware derives it from the
        # presented credential — it carries the token the report MAC uses.
        self.snapshot = self.store.identify(self.token)
        self.pin = MeshHubPin(
            node_name="edge",
            node_id=snapshot.node_id,
            generation=snapshot.generation,
            key_id=snapshot.key_id,
            offer_public_key=snapshot.offer_public_key,
        )
        self.warrant = {
            "operation_id": "op_hub_1",
            "target_binding": f"deployment-revision:{self.relay_revision.id}",
            "signature": "hub-warrant-signature",
            "execution_expires_at": 9_999_999_999,
        }
        self.kernel = SimpleNamespace(store=_Store(self.warrant))
        self.service = MeshService(
            self.hub_db, kernel=self.kernel, token_store=self.store
        )
        self.principal = Principal(PrincipalKind.NODE, self.node_id)
        self.now = 0.0
        #: Every request the worker's transport actually made.
        self.sent: list[tuple[str, dict]] = []

    # ── the hub side ─────────────────────────────────────────────────

    def enqueue(self, *, ordinal: int = 1, node_id=None, generation=None):
        envelope = {
            "deployment_revision": self.relay_revision.to_dict(),
            "warrant": self.warrant,
            "attempt_ordinal": ordinal,
        }
        return self.hub_db.mesh_relay.enqueue(
            node="edge",
            user_prompt=PROMPT_SENTINEL,
            envelope=envelope,
            destination_node_id=self.node_id if node_id is None else node_id,
            destination_generation=(
                self.snapshot.generation if generation is None else generation
            ),
            now=datetime.now(),
        )

    def claim(self, nonce: str = "nonce-1"):
        return self.service.claim_relay(
            self.principal, {"claim_nonce": nonce}, credential=self.snapshot
        )

    # ── the worker side ──────────────────────────────────────────────

    def monotonic(self) -> float:
        return self.now

    def verify(self, claimed, *, nonce="nonce-1", pin=None, started=0.0, expectation=None):
        return verify_offer(
            claimed["dispatch_offer"],
            pinned_key_id=(pin or self.pin).key_id,
            pinned_public_key=(pin or self.pin).public_key_bytes,
            node_name=(pin or self.pin).node_name,
            node_id=(pin or self.pin).node_id,
            credential_generation=(pin or self.pin).generation,
            claim_nonce=nonce,
            job=claimed["job"],
            authority_expectation=(
                claimed.get("authority_expectation") if expectation is None else expectation
            ),
            claim_started_monotonic=started,
            monotonic=self.now,
        )

    def worker(self, engine, **kw):
        return MeshServeWorker(
            hub_url="http://hub",
            pin=self.pin,
            token=self.token,
            database=self.worker_db,
            engine_factory=(lambda revision, **_kw: engine),
            http_post=kw.pop("http_post", self._post),
            sleep=lambda _s: None,
            monotonic=self.monotonic,
            **kw,
        )

    # ── what the worker has actually DONE ────────────────────────────

    def worker_state(self) -> dict:
        """Every trace a physical attempt would have left on this node.

        A refusal that claims to happen "before reservation, construction, or
        dispatch" has to be measurable, not asserted. These four counters are
        that measurement.
        """
        with self.worker_db._connection() as conn:
            counts = {
                table: conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
                for table in (
                    "mesh_worker_reservations",
                    "deployment_revisions",
                    "kernel_operations",
                    "kernel_receipts",
                )
            }
        return counts

    def resign(self, claimed, **fields):
        """Re-sign an offer body with the hub's REAL key after changing fields.

        This is the hostile case that a signature alone cannot answer: the bytes
        are authentic, so only a semantic comparison can refuse them.
        """
        body = dict(claimed["dispatch_offer"]["offer"])
        body.update(fields)
        signing = self.store.signing_snapshot("edge")
        return {
            "offer": body,
            "signature": ed25519.sign(
                bytes.fromhex(signing.offer_private_key), canonical_offer_bytes(body)
            ).hex(),
        }

    def _post(self, url, payload, *, token, timeout):
        """The transport, folded straight back onto the hub service."""
        self.sent.append((url, json.loads(json.dumps(payload))))
        if url.endswith("/api/mesh/relay/claim"):
            return self.service.claim_relay(
                self.principal, payload, credential=self.snapshot
            )
        job_id = url.rsplit("/", 2)[-2]
        if url.endswith("/complete"):
            return self.service.complete_relay(
                self.principal, job_id, payload, credential=self.snapshot
            )
        if url.endswith("/fail"):
            return self.service.fail_relay(
                self.principal, job_id, payload, credential=self.snapshot
            )
        raise AssertionError(url)


class Engine:
    """An injected fake provider. Counts every PHYSICAL call it receives."""

    active_provider = "fake"
    model = "qwen3.5-4b"

    def __init__(self, result=RESULT_SENTINEL, error=None, errors=None):
        self.result, self.error = result, error
        self.errors = list(errors or [])
        self.calls = 0
        self.prompts: list[str] = []

    def run_prompt(self, *, system_prompt="", user_prompt="", temperature=None, max_tokens=None):
        self.calls += 1
        self.prompts.append(user_prompt)
        if self.errors:
            raise self.errors.pop(0)
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def rig(tmp_path):
    reset_database()
    yield Rig(tmp_path)
    reset_database()


# ── 1. hub authenticity ──────────────────────────────────────────────


def test_a_node_token_holder_cannot_forge_a_hub_offer(rig) -> None:
    """The whole asymmetry, in one test.

    A node holds its bearer token and the hub's PUBLIC key. Neither lets it
    produce a signature the worker accepts, so a stolen node credential can
    impersonate that node but never mint hub dispatch authority for it.
    """
    rig.enqueue()
    claimed = rig.claim()
    body = dict(claimed["dispatch_offer"]["offer"])

    # Signing with the node's own bearer token material is not signing at all.
    impostor_private = (rig.token.encode() + b"\x00" * 32)[:32]
    forged = {
        "offer": body,
        "signature": ed25519.sign(impostor_private, canonical_offer_bytes(body)).hex(),
    }
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify({"job": claimed["job"], "dispatch_offer": forged})
    assert excinfo.value.reason == "mesh_offer_signature_invalid"

    # And the private half never left the hub: nothing the node can read carries it.
    assert rig.snapshot.offer_private_key == ""
    assert "offer_private_key" not in json.dumps(claimed)
    assert rig.token not in json.dumps(claimed)


def test_an_unpinned_key_id_never_reaches_signature_verification(rig) -> None:
    rig.enqueue()
    claimed = rig.claim()
    other = rig.store.pair("other-edge")[2]
    stranger = replace(rig.pin, key_id=other.key_id, offer_public_key=other.offer_public_key)
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify(claimed, pin=stranger)
    assert excinfo.value.reason == "mesh_offer_key_unpinned"


# ── 2. the offer matrix ──────────────────────────────────────────────


def test_a_missing_offer_is_not_work(rig) -> None:
    rig.enqueue()
    claimed = rig.claim()
    for absent in (None, {}, {"offer": None, "signature": ""}):
        with pytest.raises(MeshAuthorityRefused) as excinfo:
            rig.verify({"job": claimed["job"], "dispatch_offer": absent})
        assert excinfo.value.reason == "mesh_offer_missing"


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("claim_nonce", "someone-elses-nonce", "mesh_offer_signature_invalid"),
        ("node_id", "node_other", "mesh_offer_signature_invalid"),
        ("payload_sha256", "sha256:" + "0" * 64, "mesh_offer_signature_invalid"),
        ("execution_revision_id", "dep_other", "mesh_offer_signature_invalid"),
        ("first_ordinal", 9, "mesh_offer_signature_invalid"),
    ],
)
def test_tampering_with_any_signed_field_refuses(rig, field, value, reason) -> None:
    """Tamper is caught by the SIGNATURE, before any binding is even compared."""
    rig.enqueue()
    claimed = rig.claim()
    envelope = json.loads(json.dumps(claimed["dispatch_offer"]))
    envelope["offer"][field] = value
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify({"job": claimed["job"], "dispatch_offer": envelope})
    assert excinfo.value.reason == reason


def test_a_correctly_signed_offer_for_another_node_still_refuses(rig, tmp_path) -> None:
    """Authentic is not the same as MINE: the pin decides who the offer is for."""
    rig.enqueue()
    claimed = rig.claim()
    # Re-sign a body naming a different node with the SAME hub key.
    signing = rig.store.signing_snapshot("edge")
    body = dict(claimed["dispatch_offer"]["offer"])
    body["node_id"] = "node_somebody_else"
    envelope = {
        "offer": body,
        "signature": ed25519.sign(
            bytes.fromhex(signing.offer_private_key), canonical_offer_bytes(body)
        ).hex(),
    }
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify({"job": claimed["job"], "dispatch_offer": envelope})
    assert excinfo.value.reason == "mesh_offer_node_mismatch"


def test_a_stale_nonce_refuses_even_when_authentic(rig) -> None:
    rig.enqueue()
    claimed = rig.claim(nonce="poll-A")
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify(claimed, nonce="poll-B")
    assert excinfo.value.reason == "mesh_offer_nonce_mismatch"


def test_a_payload_swapped_after_signing_refuses(rig) -> None:
    """The prompt the worker would run must be the prompt the hub hashed."""
    rig.enqueue()
    claimed = rig.claim()
    swapped = dict(claimed["job"])
    swapped["user_prompt"] = "a different instruction entirely"
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify({"job": swapped, "dispatch_offer": claimed["dispatch_offer"]})
    assert excinfo.value.reason == "mesh_offer_payload_mismatch"


def test_freshness_is_monotonic_not_wall_clock(rig) -> None:
    rig.enqueue()
    claimed = rig.claim()
    rig.now = 5.0
    assert rig.verify(claimed, started=0.0) is not None  # inside the window
    rig.now = 10_000.0
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify(claimed, started=0.0)
    assert excinfo.value.reason == "mesh_offer_expired"


def test_an_offer_from_before_a_rotation_refuses(rig) -> None:
    """Sol Amendment 3: a generation only moves forward."""
    rig.enqueue()
    claimed = rig.claim()
    rig.store.rotate("edge")
    rotated = rig.store.pairing("edge")
    newer = replace(rig.pin, generation=rotated.generation)
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify(claimed, pin=newer)
    assert excinfo.value.reason == "mesh_offer_generation_mismatch"


def test_a_rotated_credential_cannot_inherit_queued_work(rig) -> None:
    """The queue binds identity AND generation, so old work does not transfer."""
    rig.enqueue()
    rig.store.rotate("edge")
    rotated = rig.store.pairing("edge")
    fresh = replace(rig.snapshot, generation=rotated.generation)
    claimed = rig.service.claim_relay(
        rig.principal, {"claim_nonce": "n"}, credential=fresh
    )
    assert claimed == {"job": None, "dispatch_offer": None}


def test_the_hub_signs_nothing_when_its_own_authority_is_not_live(rig) -> None:
    rig.enqueue()
    rig.kernel.store.revoked = True
    assert rig.claim() == {"job": None, "dispatch_offer": None}
    rig.kernel.store.revoked = False
    rig.kernel.store.state = "completed"
    assert rig.claim() == {"job": None, "dispatch_offer": None}


def test_an_envelope_without_a_context_ordinal_is_never_signed(rig) -> None:
    """The ordinal comes from the runner's dispatch context or not at all."""
    job = rig.hub_db.mesh_relay.enqueue(
        node="edge",
        user_prompt=PROMPT_SENTINEL,
        envelope={
            "deployment_revision": rig.relay_revision.to_dict(),
            "warrant": rig.warrant,
        },
        destination_node_id=rig.node_id,
        destination_generation=rig.snapshot.generation,
        now=datetime.now(),
    )
    assert job.id
    assert rig.claim() == {"job": None, "dispatch_offer": None}


# ── 3. exact, single-use authority ───────────────────────────────────


def test_a_verified_offer_is_exact_private_and_single_use(rig) -> None:
    rig.enqueue()
    offer = rig.verify(rig.claim())

    # A field-for-field copy is not the offer that was verified.
    with pytest.raises(MeshAuthorityRefused):
        consume_verified_offer(replace(offer))
    with pytest.raises(MeshAuthorityRefused):
        consume_verified_offer(SimpleNamespace(**offer.__dict__))

    reservation = reserve_local_execution(rig.worker_db, offer)
    derive_local_authority(offer, reservation)
    # Spent. The same pair cannot admit a second local execution.
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        derive_local_authority(offer, reservation)
    assert excinfo.value.reason == "mesh_offer_not_verified"


def test_replay_refuses_before_any_physical_work(rig) -> None:
    """The reservation is the election, and it happens before construction.

    The refusal is proved to be free of side effects: after it, the worker has
    persisted no execution revision and opened no kernel operation, so nothing
    was constructed and no provider was reached.
    """
    rig.enqueue()
    offer = rig.verify(rig.claim())
    assert reserve_local_execution(rig.worker_db, offer) is not None

    with pytest.raises(MeshAuthorityRefused) as excinfo:
        reserve_local_execution(rig.worker_db, offer)
    assert excinfo.value.reason == "mesh_offer_replayed"

    assert rig.worker_db.deployment_revisions.get(offer.execution_revision.id) is None
    with rig.worker_db._connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM kernel_operations").fetchone()
    assert count["c"] == 0


def test_the_derived_principal_is_narrow_and_offer_bound(rig) -> None:
    rig.enqueue()
    offer = rig.verify(rig.claim())
    authority = derive_local_authority(offer, reserve_local_execution(rig.worker_db, offer))
    assert authority.principal.kind is PrincipalKind.SERVICE
    # Exactly two operations: the physical attempt, and the signal that cancels
    # it. Nothing else — this principal cannot spawn, type, send, or approve.
    assert authority.principal.allowed_operations == frozenset(
        {("inference.invoke", 1), ("inference.cancel", 1)}
    )
    assert authority.principal.authority_basis == f"mesh-offer:{offer.offer_id}"
    # The worker module itself never writes a principal down.
    from pathlib import Path

    source = Path(__file__).resolve().parents[2] / "holdspeak/commands/mesh_serve.py"
    assert "Principal(" not in source.read_text(encoding="utf-8")


# ── 4. the frozen execution revision ─────────────────────────────────


def test_the_execution_revision_is_derived_not_configured(rig) -> None:
    derived = derive_worker_execution_revision(rig.relay_revision)
    assert (derived.kind, derived.engine, derived.boundary) == (
        "private_endpoint", "openai_compatible", "private_network"
    )
    assert derived.endpoint == RELAY_IDENTITY.endpoint
    assert derived.secret_slot == ""
    # Both nodes recompute the same content address, which is why it can be signed.
    assert derive_worker_execution_revision(rig.relay_revision).id == derived.id
    # A local artifact wins, and it never resolves back onto the mesh.
    local = DeploymentRevision.from_identity(
        replace(RELAY_IDENTITY, model_path="/models/q.gguf")
    )
    assert derive_worker_execution_revision(local).kind == "this_device"
    assert derive_worker_execution_revision(local).id != derived.id


def test_a_relay_revision_with_no_usable_target_refuses_by_name(rig) -> None:
    unusable = DeploymentRevision.from_identity(
        replace(RELAY_IDENTITY, endpoint="not a url", model_path=None)
    )
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        derive_worker_execution_revision(unusable)
    assert excinfo.value.reason == "mesh_execution_target_unusable"


# ── 5. local cardinality and receipts ────────────────────────────────


def test_one_offer_is_one_admitted_attempt_with_one_receipt(rig) -> None:
    engine = Engine()
    job = rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    worker = rig.worker(engine)

    assert worker.execute(claimed["job"], offer) is True
    assert engine.calls == 1

    report = rig.sent[-1][1]["report"]
    assert len(report["local_attempts"]) == 1
    attempt = report["local_attempts"][0]
    assert attempt["ordinal"] == 1 and attempt["outcome"] == "succeeded"

    receipt = rig.worker_broker.store.receipt(attempt["operation_id"])
    assert receipt["receipt_id"] == attempt["receipt_id"]
    assert receipt["outcome"] == "succeeded"
    operation = rig.worker_broker.store.operation(attempt["operation_id"])
    assert operation["target_ref"] == f"deployment-revision:{offer.execution_revision.id}"

    # The hub settled it, independently, from that report.
    settled = rig.hub_db.mesh_relay.get(job.id)
    assert settled.status == "completed" and settled.result == RESULT_SENTINEL


def test_a_typed_compatibility_signal_buys_exactly_one_more_attempt(rig) -> None:
    from holdspeak.kernel.provider_signals import ProviderCompatibilityRetry

    engine = Engine(errors=[ProviderCompatibilityRetry("max_completion_tokens")])
    rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    rig.worker(engine).execute(claimed["job"], offer)

    assert engine.calls == 2  # two PHYSICAL attempts, never a hidden retry
    report = rig.sent[-1][1]["report"]
    assert [a["ordinal"] for a in report["local_attempts"]] == [1, 2]
    assert [a["outcome"] for a in report["local_attempts"]] == ["failed", "succeeded"]
    # Two distinct operations, two distinct immutable receipts.
    ids = {a["operation_id"] for a in report["local_attempts"]}
    assert len(ids) == 2
    assert len({a["receipt_id"] for a in report["local_attempts"]}) == 2
    assert offer.max_attempts == 2


def test_a_third_attempt_has_no_authority(rig) -> None:
    """Two dialect signals is a genuine failure, not a third physical attempt."""
    from holdspeak.kernel.provider_signals import ProviderCompatibilityRetry

    engine = Engine(errors=[
        ProviderCompatibilityRetry("a"), ProviderCompatibilityRetry("b"),
    ])
    rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    rig.worker(engine).execute(claimed["job"], offer)
    assert engine.calls == 2
    report = rig.sent[-1][1]["report"]
    assert len(report["local_attempts"]) == 2
    assert report["terminal_outcome"] == "failed"


def test_a_provider_failure_is_receipted_and_reported_without_its_text(rig) -> None:
    engine = Engine(error=RuntimeError(f"boom {PROMPT_SENTINEL}"))
    job = rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    assert rig.worker(engine).execute(claimed["job"], offer) is False

    body = rig.sent[-1][1]
    assert rig.sent[-1][0].endswith("/fail")
    assert body["report"]["failure_class"] == "failed"
    assert PROMPT_SENTINEL not in json.dumps(body)
    assert rig.hub_db.mesh_relay.get(job.id).status == "failed"


# ── 6. cancellation ──────────────────────────────────────────────────


def test_stop_before_invoke_prevents_the_physical_attempt(rig) -> None:
    """The stop election and the active-id registration share one lock.

    Repair R2.3: stop also wins the terminal-publication election, so the
    cancelled local receipt is NOT permission to publish afterwards. The local
    truth is durable; nothing is sent.
    """
    engine = Engine()
    job = rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    worker = rig.worker(engine)
    worker._runner()  # materialize the local runner so stop can reach it
    worker.stop()

    assert worker.execute(claimed["job"], offer) is False
    assert engine.calls == 0
    # Nothing after the claim itself reached the wire.
    assert [url for url, _ in rig.sent if not url.endswith("/claim")] == []
    assert worker.publishing is False
    # The worker's own ledger still tells the truth about what happened.
    reservation = rig.worker_db.mesh_worker.get(
        hub_key_id=offer.key_id,
        hub_operation_id=offer.hub_operation_id,
        first_ordinal=offer.first_ordinal,
    )
    assert reservation["terminal_outcome"] == "cancelled"
    # And the hub's row is untouched by a report that was never sent.
    assert rig.hub_db.mesh_relay.get(job.id).status == "running"


# ── 7. independent hub settlement ────────────────────────────────────


def test_an_exact_duplicate_report_is_read_only(rig) -> None:
    engine = Engine()
    job = rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    rig.worker(engine).execute(claimed["job"], offer)

    url, body = rig.sent[-1]
    first = rig.hub_db.mesh_relay.proof(job.id)
    again = rig.service.complete_relay(
        rig.principal, job.id, body, credential=rig.snapshot
    )
    assert again["duplicate"] is True
    # Byte-identical retransmission changes nothing and reruns no model.
    assert rig.hub_db.mesh_relay.proof(job.id) == first
    assert engine.calls == 1


def test_a_conflicting_duplicate_cannot_mutate_terminal_proof(rig) -> None:
    engine = Engine()
    job = rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    rig.worker(engine).execute(claimed["job"], offer)
    before = rig.hub_db.mesh_relay.proof(job.id)

    _url, body = rig.sent[-1]
    conflicting = json.loads(json.dumps(body))
    conflicting["result"] = "a different answer"
    with pytest.raises(ConflictError) as excinfo:
        rig.service.complete_relay(
            rig.principal, job.id, conflicting, credential=rig.snapshot
        )
    # The report still MACs (only the separate result field moved), so the
    # refusal is the precise one: the digest the worker's receipts attest to is
    # not the digest of the answer now being offered.
    assert excinfo.value.code == "mesh_report_result_mismatch"
    assert rig.hub_db.mesh_relay.proof(job.id) == before


def test_a_modified_result_never_settles(rig) -> None:
    """A worker's answer must be the answer its own receipts attest to.

    The report is authentic and correctly MACed; only the separate product
    result moved. The hub recomputes the digest and refuses, because the result
    field is not what the local receipts described.
    """
    from holdspeak.mesh_authority import report_mac

    engine = Engine()
    job = rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    rig.worker(engine).execute(claimed["job"], offer)
    _url, body = rig.sent[-1]

    # A SECOND job, so this is a first settlement rather than a duplicate, and
    # a report re-bound to it and re-MACed — everything is consistent except
    # the answer being offered.
    fresh_job = rig.enqueue()
    rig.now = 1.0
    fresh_claim = rig.claim(nonce="n-fresh")
    assert fresh_claim["job"]["id"] == fresh_job.id
    fresh_offer = fresh_claim["dispatch_offer"]["offer"]

    report = json.loads(json.dumps(body["report"]))
    report["job_id"] = fresh_offer["job_id"]
    report["offer_id"] = fresh_offer["offer_id"]
    report["claim_nonce"] = fresh_offer["claim_nonce"]
    tampered = {
        "report": report,
        "mac": report_mac(report, rig.token),
        "result": "swapped answer",
    }
    with pytest.raises(ConflictError) as excinfo:
        rig.service.complete_relay(
            rig.principal, fresh_job.id, tampered, credential=rig.snapshot
        )
    assert excinfo.value.code == "mesh_report_result_mismatch"
    # Neither job's terminal proof moved.
    assert rig.hub_db.mesh_relay.get(job.id).result == RESULT_SENTINEL
    assert rig.hub_db.mesh_relay.get(fresh_job.id).result is None


def test_a_report_whose_cohort_is_not_the_signed_budget_refuses(rig) -> None:
    from holdspeak.mesh_authority import report_mac

    engine = Engine()
    job = rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    rig.worker(engine).execute(claimed["job"], offer)
    _url, body = rig.sent[-1]

    # A third ordinal the hub never signed, correctly MACed by this very node.
    forged = json.loads(json.dumps(body["report"]))
    extra = json.loads(json.dumps(forged["local_attempts"][0]))
    extra["ordinal"] = 3
    forged["local_attempts"].append(extra)
    payload = {"report": forged, "mac": report_mac(forged, rig.token), "result": RESULT_SENTINEL}
    with pytest.raises(ConflictError) as excinfo:
        rig.service.complete_relay(rig.principal, job.id, payload, credential=rig.snapshot)
    assert excinfo.value.code == "mesh_report_cohort_mismatch"


# ── 8. the edge ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "principal",
    [
        Principal(PrincipalKind.OWNER, "owner-session"),
        Principal(PrincipalKind.AGENT, "agent-1"),
        Principal(PrincipalKind.NONE, "unauthenticated"),
    ],
)
def test_only_a_node_principal_reaches_the_relay_edge(rig, principal) -> None:
    rig.enqueue()
    with pytest.raises(ServiceError) as excinfo:
        rig.service.claim_relay(principal, {"claim_nonce": "n"}, credential=rig.snapshot)
    assert excinfo.value.code == "mesh_node_authentication_required"
    assert excinfo.value.context["status"] == 403


def test_a_payload_node_field_is_not_a_principal(rig) -> None:
    """The old side door, explicitly closed."""
    rig.enqueue()
    with pytest.raises(ServiceError):
        rig.service.claim_relay(
            Principal(PrincipalKind.NONE, "unauthenticated"),
            {"node": "edge", "claim_nonce": "n"},
            credential=None,
        )


def test_one_nodes_credential_cannot_speak_for_another(rig) -> None:
    other = rig.store.pair("other-edge")[2]
    rig.enqueue()
    with pytest.raises(ServiceError) as excinfo:
        rig.service.claim_relay(rig.principal, {"claim_nonce": "n"}, credential=other)
    assert excinfo.value.code == "mesh_node_identity_mismatch"


def test_the_browser_token_can_never_authenticate_as_a_node(rig) -> None:
    from holdspeak.delivery.node_link import NodeLinkError

    with pytest.raises(NodeLinkError) as excinfo:
        rig.store.authenticate("edge", "browser-owner-token", web_token="browser-owner-token")
    assert excinfo.value.reason == "node_token_required"


def test_rotation_and_revocation_are_visible_without_a_restart(rig, tmp_path) -> None:
    """A second handle on the same custody sees the first one's edits at once."""
    other_process = NodeTokenStore(tmp_path / "nodes.json")
    assert other_process.authenticate("edge", rig.token).node_id == rig.node_id
    rig.store.rotate("edge")
    from holdspeak.delivery.node_link import NodeLinkError

    with pytest.raises(NodeLinkError):
        other_process.authenticate("edge", rig.token)
    rig.store.revoke("edge")
    assert other_process.pairing("edge") is None


# ── 9. hygiene ───────────────────────────────────────────────────────


def test_no_content_or_credential_reaches_a_kernel_row_or_the_report(rig) -> None:
    engine = Engine()
    rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    rig.worker(engine).execute(claimed["job"], offer)

    sentinels = (PROMPT_SENTINEL, RESULT_SENTINEL, rig.token)
    signing = rig.store.signing_snapshot("edge").offer_private_key

    with rig.worker_db._connection() as conn:
        for table in ("kernel_operations", "kernel_journal", "kernel_receipts"):
            dump = json.dumps([dict(row) for row in conn.execute(f"SELECT * FROM {table}")])
            for sentinel in (*sentinels, signing):
                assert sentinel not in dump, f"{sentinel!r} reached {table}"

    report = json.dumps(rig.sent[-1][1]["report"])
    for sentinel in (PROMPT_SENTINEL, RESULT_SENTINEL, rig.token, signing):
        assert sentinel not in report

    # The signed offer is authority metadata only: it carries no prompt and no key.
    assert PROMPT_SENTINEL not in json.dumps(claimed["dispatch_offer"])
    assert signing not in json.dumps(claimed["dispatch_offer"])
    # The payload binding is a hash, not the payload.
    assert offer.payload_sha256 == payload_digest(
        {
            "system_prompt": claimed["job"]["system_prompt"],
            "user_prompt": PROMPT_SENTINEL,
            "temperature": None,
            "max_tokens": None,
        }
    )


# ── 10. the signature primitive itself (repair R12) ──────────────────


#: RFC 8032 §7.1, verbatim: secret key, public key, message, signature. If the
#: implementation ever stops agreeing with these it is not Ed25519 any more, and
#: every "the hub signed this" claim in the protocol above is worth nothing.
RFC_8032_VECTORS = [
    (
        "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
        "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
        "",
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555f"
        "b8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b",
    ),
    (
        "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
        "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
        "72",
        "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da08"
        "5ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00",
    ),
    (
        "c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
        "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025",
        "af82",
        "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac18"
        "ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a",
    ),
]


@pytest.mark.parametrize(("secret", "public", "message", "signature"), RFC_8032_VECTORS)
def test_the_signature_primitive_matches_rfc_8032(secret, public, message, signature) -> None:
    """Derivation, signing, and verification against the RFC's own vectors."""
    private_key = bytes.fromhex(secret)
    body = bytes.fromhex(message)
    assert ed25519.public_key(private_key).hex() == public
    assert ed25519.sign(private_key, body).hex() == signature
    assert ed25519.verify(bytes.fromhex(public), body, bytes.fromhex(signature))


def test_a_signature_that_is_not_this_one_is_always_false() -> None:
    """Every malformed or wrong input is a plain refusal, never an exception.

    A caller must never have to tell "not a signature" from "not THIS signature":
    both mean the same thing to the protocol, and a raised exception on a
    malformed input would be a second, weaker code path.
    """
    secret, public, message, signature = RFC_8032_VECTORS[2]
    key, body, sig = bytes.fromhex(public), bytes.fromhex(message), bytes.fromhex(signature)
    assert ed25519.verify(key, body, sig)

    # Tampered message, tampered signature, tampered key.
    assert not ed25519.verify(key, body + b"\x00", sig)
    assert not ed25519.verify(key, b"", sig)
    assert not ed25519.verify(key, body, bytes([sig[0] ^ 0x01]) + sig[1:])
    assert not ed25519.verify(bytes([key[0] ^ 0x01]) + key[1:], body, sig)

    # Malformed lengths.
    assert not ed25519.verify(key[:31], body, sig)
    assert not ed25519.verify(key + b"\x00", body, sig)
    assert not ed25519.verify(key, body, sig[:63])
    assert not ed25519.verify(key, body, sig + b"\x00")

    # A non-canonical point encoding (y >= p) never decompresses.
    assert not ed25519.verify(b"\xff" * 32, body, sig)
    # A non-canonical scalar (S >= L) is refused rather than reduced.
    order = 2**252 + 27742317777372353535851937790883648493
    assert not ed25519.verify(key, body, sig[:32] + order.to_bytes(32, "little"))
    assert not ed25519.verify(key, body, sig[:32] + b"\xff" * 32)

    # And a signature made by another key over the same message.
    other = bytes.fromhex(RFC_8032_VECTORS[1][0])
    assert not ed25519.verify(key, body, ed25519.sign(other, body))


# ── 11. the re-signed semantic matrix (repair R5) ────────────────────


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        # Authentic, and about the wrong KIND of act entirely.
        ("operation_kind", "inference.cancel@1", "mesh_offer_operation_mismatch"),
        ("operation_kind", "inference.invoke@2", "mesh_offer_operation_mismatch"),
        # Authentic, and about another node.
        ("node_id", "node_somebody_else", "mesh_offer_node_mismatch"),
        ("node_name", "attic-mac", "mesh_offer_node_mismatch"),
        # Authentic, and about another credential generation.
        ("credential_generation", 7, "mesh_offer_generation_mismatch"),
        # Authentic, and about another job.
        ("job_id", "relay_somewhere_else", "mesh_offer_node_mismatch"),
        # Authentic, and about another payload.
        ("payload_sha256", "sha256:" + "0" * 64, "mesh_offer_payload_mismatch"),
        # Authentic, and about another revision.
        ("relay_revision_id", "dep_not_this_one", "mesh_offer_revision_mismatch"),
        ("execution_revision_id", "dep_not_this_one", "mesh_offer_revision_mismatch"),
        # Authentic, and carrying no warrant binding at all.
        ("warrant_binding", "", "mesh_offer_malformed"),
        ("warrant_binding", "trust-me", "mesh_offer_malformed"),
        # Authentic, and naming an operation id that is not an identifier.
        ("hub_operation_id", "op 1; DROP", "mesh_offer_malformed"),
        # Authentic, and buying more physical attempts than the protocol allows.
        ("max_attempts", 3, "mesh_offer_ordinal_not_permitted"),
        ("first_ordinal", 0, "mesh_offer_malformed"),
    ],
)
def test_a_correctly_resigned_offer_with_a_wrong_semantic_field_refuses(
    rig, field, value, reason
) -> None:
    """The hostile case a signature cannot answer (repair R5).

    Every one of these is signed by the hub's REAL per-node key over its own
    canonical bytes, so signature verification passes. What refuses them is the
    semantic comparison against this worker's pin, this poll's nonce, and this
    job — and it refuses BEFORE a reservation, a revision, a runner, or a
    provider exists, which is measured rather than asserted.
    """
    rig.enqueue()
    claimed = rig.claim()
    before = rig.worker_state()

    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify({"job": claimed["job"], "dispatch_offer": rig.resign(claimed, **{field: value})})
    assert excinfo.value.reason == reason
    assert rig.worker_state() == before == {
        "mesh_worker_reservations": 0, "deployment_revisions": 0,
        "kernel_operations": 0, "kernel_receipts": 0,
    }


def test_a_correctly_resigned_offer_for_another_destination_refuses(rig) -> None:
    """The relay revision names the destination, and it must be THIS node."""
    rig.enqueue()
    claimed = rig.claim()
    elsewhere = DeploymentRevision.from_identity(replace(RELAY_IDENTITY, node="attic-mac"))
    resigned = rig.resign(
        claimed,
        relay_revision={
            name: getattr(elsewhere, name)
            for name in (
                "destination_id", "kind", "engine", "model", "node",
                "boundary", "endpoint", "model_path", "secret_slot",
            )
        },
        relay_revision_id=elsewhere.id,
        execution_revision_id=derive_worker_execution_revision(elsewhere).id,
    )
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify({"job": claimed["job"], "dispatch_offer": resigned})
    assert excinfo.value.reason == "mesh_offer_destination_mismatch"
    assert rig.worker_state()["mesh_worker_reservations"] == 0


def test_the_worker_receives_a_job_projection_and_never_the_hub_warrant(rig) -> None:
    """Repair R3: the wire carries an id and the product payload, full stop.

    The claim answer used to be the whole relay row, hub kernel envelope and
    signed warrant included. A worker never needs the hub's authority to do its
    own work, and a node that holds one holds authority it was never issued.
    """
    rig.enqueue()
    claimed = rig.claim()

    assert set(claimed["job"]) == {
        "id", "system_prompt", "user_prompt", "temperature", "max_tokens"
    }
    wire = json.dumps(claimed)
    assert rig.warrant["signature"] not in wire
    assert "envelope" not in wire and "deployment_revision" not in claimed["job"]
    assert "status" not in claimed["job"] and "result" not in claimed["job"]

    # And a hub that DID send more than the projection is refused, not tolerated.
    smuggled = {**claimed["job"], "envelope": {"warrant": rig.warrant}}
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify({"job": smuggled, "dispatch_offer": claimed["dispatch_offer"]})
    assert excinfo.value.reason == "mesh_offer_malformed"


def test_the_signed_budget_is_the_smallest_remaining_authority(rig) -> None:
    """Repair R5: an offer cannot buy more time than its authority has left."""
    from holdspeak.services.mesh_relay_authority import COMPLETE_WITHIN_SECONDS

    # A row whose own deadline is 8 seconds away caps the budget at 8, not 120.
    rig.hub_db.mesh_relay.enqueue(
        node="edge", user_prompt=PROMPT_SENTINEL,
        envelope={
            "deployment_revision": rig.relay_revision.to_dict(),
            "warrant": rig.warrant, "attempt_ordinal": 1,
        },
        destination_node_id=rig.node_id,
        destination_generation=rig.snapshot.generation,
        deadline_seconds=8,
        now=datetime.now(),
    )
    offer = rig.claim()["dispatch_offer"]["offer"]
    assert 0 < offer["complete_within_seconds"] <= 8
    assert offer["dispatch_within_seconds"] <= offer["complete_within_seconds"]
    assert offer["complete_within_seconds"] < COMPLETE_WITHIN_SECONDS

    # And a warrant whose execution lifetime ends sooner caps it too.
    rig.warrant["execution_expires_at"] = time.time() + 3
    rig.hub_db.mesh_relay.enqueue(
        node="edge", user_prompt=PROMPT_SENTINEL,
        envelope={
            "deployment_revision": rig.relay_revision.to_dict(),
            "warrant": rig.warrant, "attempt_ordinal": 1,
        },
        destination_node_id=rig.node_id,
        destination_generation=rig.snapshot.generation,
        now=datetime.now(),
    )
    second = rig.claim(nonce="nonce-2")["dispatch_offer"]["offer"]
    assert 0 < second["complete_within_seconds"] <= 3


def test_an_authority_with_no_time_left_signs_nothing(rig) -> None:
    """Expired execution authority produces no offer at all, not a short one."""
    rig.enqueue()
    rig.warrant["execution_expires_at"] = time.time() - 1
    assert rig.claim() == {"job": None, "dispatch_offer": None}
    assert rig.hub_db.mesh_relay.proof(rig.enqueue().id)["status"] == "queued"


# ── 12. credential races (repair R4) ─────────────────────────────────


def test_a_rotation_that_wins_the_claim_refuses_by_name(rig) -> None:
    """One winner, and the loser is NAMED — not an untyped 500.

    The claim holds node custody from the signing-key read through its commit,
    so a rotate either lands entirely before it or waits. A request carrying the
    superseded snapshot is refused with the class a worker can act on.
    """
    job = rig.enqueue()
    rig.store.rotate("edge")
    with pytest.raises(ConflictError) as excinfo:
        rig.claim()
    assert excinfo.value.code == "mesh_credential_stale"
    assert excinfo.value.context.get("status") in (None, 409)
    # Refused means refused: the row is still queued and unclaimed.
    proof = rig.hub_db.mesh_relay.proof(job.id)
    assert proof["status"] == "queued" and not proof["claimed_by_node_id"]


def test_a_revocation_that_wins_the_claim_refuses_by_name(rig) -> None:
    job = rig.enqueue()
    rig.store.revoke("edge")
    with pytest.raises(ServiceError) as excinfo:
        rig.claim()
    assert excinfo.value.code == "mesh_credential_unavailable"
    assert rig.hub_db.mesh_relay.proof(job.id)["status"] == "queued"


def test_a_revocation_before_settlement_prevents_acceptance(rig) -> None:
    """A credential that dies mid-flight cannot settle — and does not rewrite
    the worker's truthful local receipt either."""
    engine = Engine()
    job = rig.enqueue()

    def revoking(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            rig.store.revoke("edge")
        return rig._post(url, payload, token=token, timeout=timeout)

    assert rig.worker(engine, http_post=revoking).run_once() == 1
    assert engine.calls == 1  # the physical attempt really happened

    proof = rig.hub_db.mesh_relay.proof(job.id)
    assert proof["status"] == "running" and proof["worker_terminal"] is None
    # The worker's own ledger is untouched by the hub's refusal: it succeeded
    # locally, and says so.
    with rig.worker_db._connection() as conn:
        outcomes = [
            row["outcome"] for row in conn.execute("SELECT outcome FROM kernel_receipts")
        ]
    assert outcomes == ["succeeded"]


def test_the_claim_and_the_settlement_both_hold_node_custody(rig) -> None:
    """The lock is not decoration: both decisions take it (repair R4)."""
    from contextlib import contextmanager

    original = rig.store.custody_lock
    held: list[str] = []

    @contextmanager
    def counting():
        with original():
            held.append("held")
            yield

    rig.store.custody_lock = counting
    engine = Engine()
    rig.enqueue()
    assert rig.worker(engine).run_once() == 0
    assert len(held) >= 2, "claim and settlement must each hold node custody"


def test_node_custody_serializes_a_rotation_against_a_held_decision(rig) -> None:
    """What holding that lock actually buys: a rotate WAITS for it."""
    import threading

    rotated = threading.Event()

    def rotate() -> None:
        rig.store.rotate("edge")
        rotated.set()

    thread = threading.Thread(target=rotate, daemon=True)
    with rig.store.custody_lock():
        thread.start()
        # The rotation is blocked on custody for as long as the decision holds it.
        assert not rotated.wait(0.5)
        assert rig.store.pairing("edge").generation == 1
    thread.join(timeout=30)
    assert rotated.is_set()
    assert rig.store.pairing("edge").generation == 2


def test_a_settlement_after_the_hub_deadline_refuses(rig) -> None:
    """The hub's own absolute deadline is enforced inside the transaction (R8)."""
    engine = Engine()
    job = rig.enqueue()

    def late(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            # The hub's wall clock has moved past the settlement deadline it
            # signed. The worker's work was honest; it is simply too late.
            rig.service._authority._clock = lambda: time.time() + 10_000
        return rig._post(url, payload, token=token, timeout=timeout)

    assert rig.worker(engine, http_post=late).run_once() == 1
    proof = rig.hub_db.mesh_relay.proof(job.id)
    assert proof["status"] == "running" and proof["worker_terminal"] is None


def test_a_revocation_during_the_work_prevents_acceptance(rig) -> None:
    """Repair R6: whatever commits first wins, and revocation can be first.

    The worker's attempt was admitted and receipted honestly. The hub's own
    authority died while it ran, so the settlement transaction finds no live
    warrant and refuses — without rewriting the worker's local receipt.
    """
    engine = Engine()
    job = rig.enqueue()

    def revoking(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            rig.kernel.store.revoked = True
        return rig._post(url, payload, token=token, timeout=timeout)

    assert rig.worker(engine, http_post=revoking).run_once() == 1
    assert engine.calls == 1
    proof = rig.hub_db.mesh_relay.proof(job.id)
    assert proof["status"] == "running" and proof["worker_terminal"] is None


def test_an_expiry_that_commits_first_wins_the_settlement(rig) -> None:
    """Repair R6: a deadline that passed while the worker worked is an outcome.

    The relay row's own deadline is enforced before the election opens, so the
    guarded terminal update finds nothing running to settle. The refusal is
    named; the terminal proof of the expired job is not rewritten by a report
    that arrived after it.
    """
    engine = Engine()
    job = rig.enqueue()

    def slow(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            # Time passed on the hub while this node was working.
            with rig.hub_db._connection() as conn:
                conn.execute(
                    "UPDATE mesh_relay_jobs SET deadline_at = ? WHERE id = ?",
                    ((datetime.now() - timedelta(seconds=5)).isoformat(), job.id),
                )
        return rig._post(url, payload, token=token, timeout=timeout)

    assert rig.worker(engine, http_post=slow).run_once() == 1
    settled = rig.hub_db.mesh_relay.get(job.id)
    assert settled.status == "failed" and settled.result is None
    assert rig.hub_db.mesh_relay.proof(job.id)["worker_terminal"] is None


def test_the_monotonic_deadline_is_recomputed_after_revision_persistence(rig) -> None:
    """Repair R8: persistence takes real time, and it cannot buy more.

    The budget used to be measured once, before the execution revision was
    written, and then handed to admission as if no time had passed. It is one
    monotonic INSTANT, not a duration that restarts: an offer whose window closed
    while the revision was being persisted refuses before the provider is reached.
    """
    from holdspeak.kernel.mesh_local_authority import (
        derive_local_authority,
        reserve_local_execution,
    )
    from holdspeak.kernel.mesh_local_runner import MeshLocalRunner
    from holdspeak.mesh_authority import canonical_job_payload

    engine = Engine()
    rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    authority = derive_local_authority(
        offer, reserve_local_execution(rig.worker_db, offer)
    )

    # Tick one: inside the window, on entry. Tick two: after the revision was
    # persisted, the signed window has closed.
    ticks = iter([0.0, 10_000.0])
    runner = MeshLocalRunner(
        rig.worker_db,
        engine_factory=lambda revision, **_kw: engine,
        monotonic=lambda: next(ticks),
    )
    with pytest.raises(MeshAuthorityRefused) as excinfo:
        runner.execute(authority, canonical_job_payload(claimed["job"]))
    assert excinfo.value.reason == "mesh_offer_expired"
    assert engine.calls == 0
    # The revision really was persisted first — this is the interval that used
    # to be invisible, not a refusal that happened earlier for another reason.
    assert rig.worker_db.deployment_revisions.get(offer.execution_revision.id) is not None
    with rig.worker_db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) AS c FROM kernel_operations"
        ).fetchone()["c"] == 0


# ── 13. empty output, and hostile reports (repairs R10, R11) ─────────


def test_an_empty_completion_is_an_honest_success(rig) -> None:
    """Repair R10: every string is a result, including the empty one.

    The worker receipted this attempt as succeeded and bound the digest of
    exactly this string. Refusing it only at the hub would leave a truthful
    local receipt facing a rejected settlement — the two nodes disagreeing about
    an attempt that plainly happened.
    """
    from holdspeak.mesh_authority import result_digest

    engine = Engine(result="")
    job = rig.enqueue()
    assert rig.worker(engine).run_once() == 0

    settled = rig.hub_db.mesh_relay.get(job.id)
    assert settled.status == "completed"
    assert settled.result == ""
    report = rig.sent[-1][1]["report"]
    assert report["terminal_outcome"] == "succeeded"
    assert report["result_sha256"] == result_digest("")
    # The hub accepted the digest it recomputed, so both nodes agree.
    assert rig.hub_db.mesh_relay.proof(job.id)["worker_terminal"] == report


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("failure_class", "provider said: " + PROMPT_SENTINEL),
        ("failure_class", "Traceback (most recent call last):\n  File ..."),
        ("node_name", PROMPT_SENTINEL + " " + RESULT_SENTINEL),
        ("hub_operation_id", "x" * 200),
        # Repair R2.7: SHORT, well-shaped, lowercase tokens that satisfy the old
        # `[a-z][a-z0-9_]{0,63}` grammar completely — and say something this
        # protocol never defined. A shape is not a vocabulary.
        ("failure_class", "credential"),
        ("failure_class", "prompt"),
        ("failure_class", "token"),
        ("failure_class", "api_key_rejected"),
    ],
)
def test_a_macd_report_carrying_content_refuses_without_persisting_it(
    rig, field, value
) -> None:
    """Repair R11: a node MAC is authentication, not sanitization.

    This report is authentic — MACed by the very node that claimed the job — and
    it still refuses, because the wire grammar is bounded opaque identifiers and
    a fixed failure vocabulary. Nothing it carries reaches stored proof.
    """
    from holdspeak.mesh_authority import report_mac

    job = rig.enqueue()
    claimed = rig.claim()
    offer = claimed["dispatch_offer"]["offer"]
    hostile = {
        "report_schema": 1,
        "offer_id": offer["offer_id"],
        "job_id": offer["job_id"],
        "hub_operation_id": offer["hub_operation_id"],
        "claim_nonce": offer["claim_nonce"],
        "node_name": offer["node_name"],
        "node_id": offer["node_id"],
        "credential_generation": offer["credential_generation"],
        "relay_revision_id": offer["relay_revision_id"],
        "execution_revision_id": offer["execution_revision_id"],
        "local_attempts": [{
            "ordinal": 1, "operation_id": "op_local_1", "receipt_id": "rcpt_1",
            "principal_identity": "mesh-receiver:op_hub_1",
            "claim_identity": "inference-abc", "outcome": "failed",
        }],
        "terminal_outcome": "failed",
        "result_sha256": "",
        "failure_class": "failed",
    }
    hostile[field] = value

    with pytest.raises(ConflictError) as excinfo:
        rig.service.fail_relay(
            rig.principal, job.id,
            {"report": hostile, "mac": report_mac(hostile, rig.token), "result": ""},
            credential=rig.snapshot,
        )
    assert excinfo.value.code == "mesh_report_malformed"
    proof = rig.hub_db.mesh_relay.proof(job.id)
    # Nothing of the report was written: no terminal proof, no error text, and
    # the row is exactly where the claim left it.
    assert proof["worker_terminal"] is None and proof["status"] == "running"
    assert not proof["error"] and not proof["result"]
    # The hostile value itself never became a stored field VALUE. (The offer the
    # hub signed legitimately contains the substring `credential_generation`, so
    # this compares values rather than sweeping the whole serialization.)
    stored = [str(v) for v in proof.values() if not isinstance(v, (dict, list))]
    assert value not in stored


def test_the_wire_grammar_admits_every_identifier_the_protocol_mints() -> None:
    """A fence that refuses honest traffic is a flake, not a fence.

    The claim nonce is `secrets.token_urlsafe`, which is base64url — so roughly
    one nonce in thirty legitimately begins with ``-`` or ``_``. The grammar has
    to admit exactly what this protocol produces while still refusing the things
    it exists to keep out: whitespace, newlines, quotes, and unbounded text.
    """
    import secrets
    import uuid

    from holdspeak.mesh_authority.offer import is_opaque_id, is_sha256
    from holdspeak.mesh_authority.report import result_digest

    for _ in range(200):
        assert is_opaque_id(secrets.token_urlsafe(18))
    for minted in (
        "-leading-hyphen", "_leading-underscore",
        "offer_" + uuid.uuid4().hex, "op_hub_1", "relay_abc123",
        "meshkey_" + uuid.uuid4().hex[:16], "mesh-receiver:op_hub_1",
        "inference-0123456789abcdef", "dep_" + "a" * 32,
    ):
        assert is_opaque_id(minted), minted

    for hostile in (
        "", " ", "x" * 129, "prompt with spaces", "line\nbreak",
        'quote"inside', "brace{}", "semi;colon", PROMPT_SENTINEL + " " + RESULT_SENTINEL,
    ):
        assert not is_opaque_id(hostile), hostile

    assert is_sha256(result_digest("anything"))
    assert is_sha256(result_digest(""))
    for wrong in ("sha256:" + "A" * 64, "sha256:" + "0" * 63, "0" * 64, "sha1:x"):
        assert not is_sha256(wrong), wrong


# ── 14. ordinary production observation (repair R1) ──────────────────


def test_ordinary_observation_journals_no_content_and_no_credential(rig) -> None:
    """The relay legs are observed, and what they write is content-free.

    Generic service observation serializes arguments and results. On this
    service those are a bearer credential, a prompt, a completion, a hub warrant,
    a signed offer, and a worker report — so the mesh legs journal an explicit
    projection instead: identifiers, generations, outcomes, and the fixed refusal
    class. This is the real production wiring: a `SQLiteObserver` over the hub
    database, exactly as the web runtime composes it.
    """
    from holdspeak.services.sqlite_observer import SQLiteObserver

    rig.service = MeshService(
        rig.hub_db, kernel=rig.kernel, token_store=rig.store,
        observer=SQLiteObserver(rig.hub_db._connection),
    )
    # claim → complete
    rig.enqueue()
    assert rig.worker(Engine()).run_once() == 0
    # claim → fail. A second physical attempt needs a second HUB OPERATION: the
    # worker's replay reservation is keyed to the first one, exactly as a product
    # retry requires fresh hub authority rather than a reused offer.
    rig.warrant["operation_id"] = "op_hub_2"
    rig.enqueue()
    assert rig.worker(Engine(error=RuntimeError(f"boom {RESULT_SENTINEL}"))).run_once() == 1
    # a refusal
    with pytest.raises(ServiceError):
        rig.service.claim_relay(
            Principal(PrincipalKind.OWNER, "owner-session"),
            {"claim_nonce": "n"}, credential=rig.snapshot,
        )

    with rig.hub_db._connection() as conn:
        rows = [dict(row) for row in conn.execute("SELECT * FROM pipeline_events")]
    methods = {row["method"] for row in rows}
    assert {"claim_relay", "complete_relay", "fail_relay"} <= methods, methods
    assert any(
        row["error_code"] == "mesh_node_authentication_required" for row in rows
    ), "a refused leg must still be journaled, by its named class"

    signing = rig.store.signing_snapshot("edge").offer_private_key
    signed_offer = rig.hub_db.mesh_relay.proof(
        rig.sent[-1][0].rsplit("/", 2)[-2]
    )["dispatch_offer"]["signature"]
    dump = json.dumps(rows)
    for sentinel in (
        PROMPT_SENTINEL, RESULT_SENTINEL, rig.token, signing,
        rig.warrant["signature"], signed_offer, "report", "warrant", "prompt",
    ):
        assert sentinel not in dump, f"{sentinel!r} reached pipeline_events"


# ── 15. the independent live-authority expectation (repair R2.1) ─────


def canonical_payload() -> dict:
    """The exact product payload the worker executes for the rig's job."""
    return {
        "system_prompt": "", "user_prompt": PROMPT_SENTINEL,
        "temperature": None, "max_tokens": None,
    }


def _expectation_alternates() -> dict[str, object]:
    """VALID alternate values for every semantic field of the expectation.

    None of these is malformed. Each is exactly the shape the protocol defines,
    correctly typed, and grammatically legal — a second authentic reading of the
    same wire. Only a SEMANTIC comparison can refuse them, which is the whole
    reason the expectation exists.
    """
    other_relay = DeploymentRevision.from_identity(
        replace(RELAY_IDENTITY, destination_id="other-edge-profile")
    )
    return {
        "job_id": "relay_0123456789ab",
        "hub_operation_id": "op_hub_9",
        "operation_kind": "inference.cancel@1",
        "warrant_binding": "sha256:" + "b" * 64,
        "relay_revision_id": other_relay.id,
        "execution_revision_id": derive_worker_execution_revision(other_relay).id,
        "destination_node_id": "node_00000000000000ff",
        "destination_generation": 2,
        "attempt_ordinal": 2,
        "dispatch_within_seconds": 29.0,
        "complete_within_seconds": 119.0,
        "hub_settlement_deadline": 1.0,
    }


@pytest.mark.parametrize("field", sorted(_expectation_alternates()))
def test_a_valid_alternate_expectation_field_refuses_before_any_work(rig, field) -> None:
    """Repair R2.1: the expectation is compared field by field, before work.

    The hub derives this projection INDEPENDENTLY — from its persisted queue row
    and its persisted kernel operation — and the signature covers its canonical
    hash. A crossed or stale construction, and a wire swap between two authentic
    offers, both land here: the offer says one thing, the hub's own live reading
    says another, and the worker refuses having reserved nothing, persisted no
    revision, built no runner, and reached no provider.
    """
    from holdspeak.mesh_authority.offer import expectation_digest

    rig.enqueue()
    claimed = rig.claim()
    before = rig.worker_state()

    crossed = dict(claimed["authority_expectation"])
    crossed[field] = _expectation_alternates()[field]
    # Re-hash and RE-SIGN the offer around it, so the only thing wrong is the
    # semantics: signature, key, nonce, node, payload, and freshness all verify.
    resigned = rig.resign(
        claimed, authority_expectation_sha256=expectation_digest(crossed)
    )

    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify(
            {"dispatch_offer": resigned, "job": claimed["job"]}, expectation=crossed
        )
    assert excinfo.value.reason == "mesh_offer_expectation_mismatch"
    assert rig.worker_state() == before


def test_an_expectation_that_is_not_hash_bound_refuses(rig) -> None:
    """A second authentic expectation cannot be swapped in beside this offer."""
    rig.enqueue()
    claimed = rig.claim()
    before = rig.worker_state()

    swapped = dict(claimed["authority_expectation"])
    swapped["hub_operation_id"] = "op_hub_9"  # authentic shape, other authority

    with pytest.raises(MeshAuthorityRefused) as excinfo:
        rig.verify(claimed, expectation=swapped)
    assert excinfo.value.reason == "mesh_offer_expectation_mismatch"
    assert rig.worker_state() == before


def test_the_expectation_carries_no_warrant_credential_or_content(rig) -> None:
    """Content-free by construction, and hash-bound — not a third factor."""
    from holdspeak.mesh_authority.offer import EXPECTATION_FIELDS, expectation_digest

    rig.enqueue()
    claimed = rig.claim()
    expectation = claimed["authority_expectation"]

    assert set(expectation) == set(EXPECTATION_FIELDS)
    signing = rig.store.signing_snapshot("edge")
    dump = json.dumps(expectation)
    for secret in (
        PROMPT_SENTINEL, RESULT_SENTINEL, rig.token,
        signing.offer_private_key, rig.warrant["signature"],
        claimed["dispatch_offer"]["signature"],
    ):
        assert secret not in dump, f"{secret!r} reached the authority expectation"
    for absent in ("warrant", "signature", "witness", "proof", "result", "error", "status"):
        assert absent not in expectation

    # The signature already covers it: the offer binds the canonical hash.
    assert claimed["dispatch_offer"]["offer"]["authority_expectation_sha256"] == (
        expectation_digest(expectation)
    )
    # And the verified offer is minted only when both agree.
    assert rig.verify(claimed).hub_operation_id == rig.warrant["operation_id"]


def test_the_hub_reads_the_operation_it_actually_stored(rig) -> None:
    """Repair R2.1: the operation kind is READ, never written in regardless.

    The relay leg only ever means `inference.invoke@1`, which is exactly why
    writing that constant into an offer would make the field a decoration. The
    hub reads the persisted kernel row: an operation that is something else signs
    nothing at all.
    """
    rig.enqueue()
    rig.kernel.store.name = "inference.cancel"
    assert rig.claim() == {"job": None, "dispatch_offer": None}

    rig.kernel.store.name = "inference.invoke"
    rig.kernel.store.version = 2
    assert rig.claim() == {"job": None, "dispatch_offer": None}

    # Restored, and the very same row now signs.
    rig.kernel.store.version = 1
    claimed = rig.claim()
    assert claimed["dispatch_offer"] is not None
    assert claimed["authority_expectation"]["operation_kind"] == "inference.invoke@1"


# ── 16. one monotonic instant, through physical dispatch (R2.4) ──────


def test_a_sub_50ms_remainder_is_used_exactly_as_it_is(rig) -> None:
    """Repair R2.4: the old 50 ms request floor bought unauthorized time."""
    rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    seen: list[float] = []

    def timing(url, payload, *, token, timeout):
        seen.append(timeout)
        return {"ack": True}

    worker = rig.worker(Engine(), http_post=timing)
    rig.now = offer.monotonic_deadline - 0.008
    remaining = offer.remaining_seconds(monotonic=rig.monotonic())

    assert worker._post("/complete", {}, timeout=remaining) == {"ack": True}
    assert seen == [pytest.approx(0.008)]


def test_an_exhausted_remainder_starts_no_request_at_all(rig) -> None:
    """No usable remainder means no request — not a floored one (repair R2.4)."""
    rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    posts: list[str] = []

    def counting(url, payload, *, token, timeout):
        posts.append(url)
        return rig._post(url, payload, token=token, timeout=timeout)

    worker = rig.worker(Engine(), http_post=counting)
    # The window closes exactly as the local receipt becomes durable.
    original = rig.worker_db.mesh_worker.settle

    def settle_then_expire(**kw):
        owned = original(**kw)
        rig.now = offer.monotonic_deadline
        return owned

    rig.worker_db.mesh_worker.settle = settle_then_expire
    try:
        assert worker.execute(claimed["job"], offer) is False
    finally:
        rig.worker_db.mesh_worker.settle = original
    assert posts == [], "an exhausted remainder must start no request"


def test_persistence_consumes_the_same_monotonic_instant(rig) -> None:
    """The deadline is an INSTANT, not a duration that restarts on each read."""
    from holdspeak.kernel.mesh_local_runner import MeshLocalRunner

    rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    reservation = reserve_local_execution(rig.worker_db, offer)
    authority = derive_local_authority(offer, reservation)

    # Persisting the execution revision is what eats the budget here.
    original = rig.worker_db.deployment_revisions.upsert

    def slow_upsert(revision):
        rig.now = offer.monotonic_deadline  # the write took the whole window
        return original(revision)

    rig.worker_db.deployment_revisions.upsert = slow_upsert
    try:
        runner = MeshLocalRunner(
            rig.worker_db,
            engine_factory=lambda revision, **kw: Engine(),
            monotonic=rig.monotonic,
        )
        with pytest.raises(MeshAuthorityRefused) as excinfo:
            runner.execute(authority, canonical_payload())
    finally:
        rig.worker_db.deployment_revisions.upsert = original
    assert excinfo.value.reason == "mesh_offer_expired"
    # No kernel operation was ever admitted for it.
    with rig.worker_db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) AS c FROM kernel_operations"
        ).fetchone()["c"] == 0


# ── 17. one connection, one election, both winners (repair R2.10) ────


def _independent(rig) -> Database:
    """A SECOND, genuinely independent Database over the hub's own file.

    Not the same object with a different name: a separate connection cache, so
    its statements really are another SQLite connection racing the first. That
    is the only way an election proof means anything — a fake store mutated in
    sequence proves ordering, never contention.
    """
    return Database(rig.hub_db.db_path)


def test_the_claim_decides_on_its_own_connection(rig) -> None:
    """Repair R2.10: the callback reads on the transaction's connection.

    The authority read used to check a connection out of the shared factory,
    which on the claiming thread hands back a SECOND, short-lived connection —
    and therefore a second snapshot of exactly the operation, warrant, and
    revocation state the transaction is deciding against.
    """
    seen: list[object] = []
    original = rig.hub_db.mesh_relay.claim_signed

    def watching(*, authorize, **kw):
        def record(job, conn):
            seen.append(conn)
            # The transaction is OPEN on this connection, and it can read the
            # very row it is about to guard.
            assert conn.in_transaction
            row = conn.execute(
                "SELECT status FROM mesh_relay_jobs WHERE id = ?", (job.id,)
            ).fetchone()
            assert row["status"] == "queued"
            return authorize(job, conn)

        return original(authorize=record, **kw)

    rig.hub_db.mesh_relay.claim_signed = watching
    rig.enqueue()
    claimed = rig.claim()
    assert claimed["dispatch_offer"] is not None
    assert len(seen) == 1 and seen[0] is not None


def test_a_revocation_that_commits_first_wins_the_claim_on_real_connections(rig) -> None:
    """Both winner orders, with two REAL connections and a process barrier.

    Order A: the revocation commits before the claim transaction opens, so no
    offer is signed at all. Order B: the claim commits first, and the revocation
    that lands afterwards cannot unsign it — but it does stop the settlement.
    """
    import threading

    # ── order A: revocation first ────────────────────────────────────
    rig.enqueue()
    other = _independent(rig)
    barrier = threading.Barrier(2, timeout=30)

    def revoke_first() -> None:
        barrier.wait()
        rig.store.revoke("edge")

    thread = threading.Thread(target=revoke_first, daemon=True)
    thread.start()
    barrier.wait()
    thread.join(timeout=30)
    with pytest.raises(ConflictError) as excinfo:
        rig.claim()
    assert excinfo.value.code == "mesh_credential_unavailable"
    # Nothing moved on the OTHER connection either: the row is still queued.
    with other._connection() as conn:
        statuses = [
            row["status"] for row in conn.execute("SELECT status FROM mesh_relay_jobs")
        ]
    assert statuses == ["queued"]

    # ── order B: the claim commits first ─────────────────────────────
    # Re-pair: a NEW node id and generation 2, through the product verbs.
    rig.node_id, rig.token, snapshot = rig.store.pair("edge")
    rig.snapshot = rig.store.identify(rig.token)
    rig.principal = Principal(PrincipalKind.NODE, rig.snapshot.node_id)
    rig.pin = MeshHubPin(
        node_name="edge", node_id=snapshot.node_id, generation=snapshot.generation,
        key_id=snapshot.key_id, offer_public_key=snapshot.offer_public_key,
    )
    rig.warrant["operation_id"] = "op_hub_2"
    rig.enqueue()
    claimed = rig.claim()
    assert claimed["dispatch_offer"] is not None

    barrier = threading.Barrier(2, timeout=30)

    def revoke_after() -> None:
        barrier.wait()
        rig.store.revoke("edge")

    thread = threading.Thread(target=revoke_after, daemon=True)
    thread.start()
    barrier.wait()
    thread.join(timeout=30)

    # The signed offer is not unsigned by a revocation that lost the race — it is
    # already committed, on this connection and every other.
    with other._connection() as conn:
        row = conn.execute(
            "SELECT status, dispatch_offer_json FROM mesh_relay_jobs"
            " WHERE claimed_generation = ?", (rig.snapshot.generation,)
        ).fetchone()
    assert row["status"] == "running" and row["dispatch_offer_json"]
    # What the revocation DOES do is stop the settlement.
    with pytest.raises(ConflictError) as settling:
        rig.service.complete_relay(
            rig.principal, claimed["job"]["id"],
            {"report": {}, "mac": "", "result": ""}, credential=rig.snapshot,
        )
    assert settling.value.code in {"mesh_credential_stale", "mesh_report_malformed"}


def test_a_conflicting_report_that_commits_first_wins_the_settlement(rig) -> None:
    """Repair R2.10, settlement side: the loser settles nothing.

    Two real connections race the first settlement. Whichever commits first owns
    the terminal proof; the loser's guarded update matches no row, and the stored
    report and result are the winner's, unchanged.
    """
    import threading

    engine = Engine()
    job = rig.enqueue()
    assert rig.worker(engine).run_once() == 0
    winner = rig.hub_db.mesh_relay.proof(job.id)
    assert winner["status"] == "completed"

    # A second, independent connection now tries to settle the SAME job with a
    # conflicting terminal report. It arrives after the winner committed.
    other = _independent(rig)
    losers: list[object] = []

    def decide(proof, conn):
        losers.append(conn)
        assert conn.in_transaction
        # The loser can SEE the winner's committed proof on its own connection.
        assert proof["status"] == "completed"
        return {"status": "failed", "error": "late", "worker_terminal": {"x": 1}}

    settled = other.mesh_relay.settle_first(
        job.id,
        node_id=str(winner["claimed_by_node_id"]),
        generation=int(winner["claimed_generation"]),
        decide=decide,
    )
    assert settled is False, "the guarded update must match no row"
    assert losers and losers[0] is not None
    after = rig.hub_db.mesh_relay.proof(job.id)
    assert after["status"] == "completed"
    assert after["worker_terminal"] == winner["worker_terminal"]
    assert after["result"] == winner["result"]


def test_an_expiry_on_another_connection_wins_the_settlement(rig) -> None:
    """A deadline that lands first is an outcome, decided in the same election."""
    import threading
    from datetime import timedelta

    engine = Engine()
    job = rig.hub_db.mesh_relay.enqueue(
        node="edge",
        user_prompt=PROMPT_SENTINEL,
        envelope={
            "deployment_revision": rig.relay_revision.to_dict(),
            "warrant": rig.warrant, "attempt_ordinal": 1,
        },
        destination_node_id=rig.node_id,
        destination_generation=rig.snapshot.generation,
        deadline_seconds=1,
        now=datetime.now(),
    )
    claimed = rig.claim()
    offer = rig.verify(claimed)

    # Another real connection drives the row past its deadline, and a barrier
    # makes that land BEFORE the settlement transaction opens.
    other = _independent(rig)
    barrier = threading.Barrier(2, timeout=30)

    def expire() -> None:
        barrier.wait()
        other.mesh_relay.get(job.id, now=datetime.now() + timedelta(seconds=10))

    thread = threading.Thread(target=expire, daemon=True)
    thread.start()
    barrier.wait()
    thread.join(timeout=30)
    assert rig.hub_db.mesh_relay.proof(job.id)["status"] == "failed"

    worker = rig.worker(engine)
    assert worker.execute(claimed["job"], offer) is False
    # The expiry owns the row; the settlement found nothing left to settle.
    proof = rig.hub_db.mesh_relay.proof(job.id)
    assert proof["status"] == "failed" and proof["worker_terminal"] is None
    # And the worker's own receipt is untouched by the hub's refusal.
    with rig.worker_db._connection() as conn:
        assert [
            row["outcome"] for row in conn.execute("SELECT outcome FROM kernel_receipts")
        ] == ["succeeded"]
