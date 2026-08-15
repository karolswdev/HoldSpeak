"""HS-85-03 — `holdspeak mesh serve`, the edge worker LOOP.

The protocol matrix (signatures, nonces, replay, cohorts, settlement) lives in
``test_mesh_receiver_authority.py``. This file is about the loop that carries it:
claim → verify → admit → report, plus backoff, stop, startup reconciliation, and
the CLI wiring.

HS-131-16 rewrote what each step DOES. The worker no longer builds an engine or
calls a provider: it proves the hub's Ed25519 offer, reserves it, and hands the
work to its own kernel. So the old envelope-shape tests are gone with the shape
they tested, and the loop-level guarantees are re-proved here against the
authenticated spine.
"""

from __future__ import annotations

import json

import pytest

from holdspeak.commands.mesh_serve import MeshServeRefused, MeshServeWorker
from holdspeak.db import reset_database

from .test_mesh_receiver_authority import (
    PROMPT_SENTINEL,
    RESULT_SENTINEL,
    Engine,
    Rig,
)


@pytest.fixture
def rig(tmp_path):
    reset_database()
    yield Rig(tmp_path)
    reset_database()


# ── the loop ─────────────────────────────────────────────────────────


def test_run_once_claims_verifies_admits_and_completes(rig) -> None:
    engine = Engine()
    job = rig.enqueue()
    assert rig.worker(engine).run_once() == 0

    assert engine.calls == 1
    assert engine.prompts == [PROMPT_SENTINEL]
    settled = rig.hub_db.mesh_relay.get(job.id)
    assert settled.status == "completed" and settled.result == RESULT_SENTINEL
    # The claim leg sent a fresh nonce and nothing else — no node name.
    claim_body = rig.sent[0][1]
    assert set(claim_body) == {"claim_nonce"} and claim_body["claim_nonce"]


def test_run_once_with_no_work_exits_clean(rig) -> None:
    engine = Engine()
    assert rig.worker(engine).run_once() == 0
    assert engine.calls == 0


def test_two_polls_send_two_different_nonces(rig) -> None:
    """Freshness is per-poll: an offer minted for an earlier poll cannot be replayed."""
    worker = rig.worker(Engine())
    worker.run_once()
    worker.run_once()
    nonces = [body["claim_nonce"] for url, body in rig.sent if url.endswith("/claim")]
    assert len(nonces) == 2 and nonces[0] != nonces[1]


def test_an_unverifiable_offer_is_not_work(rig) -> None:
    """A hub answer that does not verify never reaches the local kernel."""
    engine = Engine()
    rig.enqueue()

    def tampering_post(url, payload, *, token, timeout):
        answer = rig._post(url, payload, token=token, timeout=timeout)
        if url.endswith("/claim") and answer.get("dispatch_offer"):
            answer = json.loads(json.dumps(answer))
            answer["dispatch_offer"]["offer"]["first_ordinal"] = 99
        return answer

    worker = rig.worker(engine, http_post=tampering_post)
    assert worker.run_once() == 1
    assert engine.calls == 0
    with rig.worker_db._connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM kernel_operations").fetchone()
    assert count["c"] == 0


def test_engine_failure_reports_fail_without_provider_text(rig) -> None:
    engine = Engine(error=RuntimeError(f"endpoint said {PROMPT_SENTINEL}"))
    job = rig.enqueue()
    assert rig.worker(engine).run_once() == 1

    assert rig.hub_db.mesh_relay.get(job.id).status == "failed"
    reported = [body for url, body in rig.sent if url.endswith("/fail")]
    assert reported and reported[-1]["report"]["failure_class"] == "failed"
    assert PROMPT_SENTINEL not in json.dumps(reported[-1])


def test_unreachable_hub_backs_off_without_crashing() -> None:
    import urllib.error

    waits: list[float] = []

    def refuse(*_args, **_kwargs):
        raise urllib.error.URLError("connection refused")

    worker = MeshServeWorker(
        hub_url="http://nowhere",
        pin=None,
        token="t",
        http_post=refuse,
        sleep=waits.append,
    )
    assert worker.poll_step() is False
    assert worker.poll_step() is False
    assert waits == [1.0, 2.0]  # doubling backoff, no crash


def test_run_forever_stops_on_stop_and_does_work(rig) -> None:
    engine = Engine()
    rig.enqueue()
    worker = rig.worker(engine)
    original = worker.poll_step

    def once_then_stop() -> bool:
        did = original()
        worker._stop = True
        return did

    worker.poll_step = once_then_stop
    assert worker.run_forever() == 0
    assert engine.calls == 1


def test_run_forever_reconciles_abandoned_reservations(rig) -> None:
    """A reservation left by a previous life is INDETERMINATE, never rerun."""
    rig.worker_db.mesh_worker.reserve(
        hub_key_id="k", hub_operation_id="op_abandoned", first_ordinal=1
    )
    worker = rig.worker(Engine())
    worker._stop = True
    worker.run_forever()
    row = rig.worker_db.mesh_worker.get(
        hub_key_id="k", hub_operation_id="op_abandoned", first_ordinal=1
    )
    assert row["state"] == "indeterminate"


def test_a_second_live_worker_refuses_before_touching_reservations(rig) -> None:
    """HS-131-16 (repair R7): one live owner per worker database.

    Startup reconciliation rewrites every open reservation, so it may only run
    when nothing else is serving from this database — otherwise a second
    `mesh serve` would declare a RUNNING worker's in-flight attempt
    indeterminate. The lock is an OS lock: it is released by process exit of any
    kind, so the next owner reconciles honestly rather than finding a stale claim.
    """
    key = {"hub_key_id": "k", "hub_operation_id": "op_in_flight", "first_ordinal": 1}
    rig.worker_db.mesh_worker.reserve(**key)
    second = rig.worker(Engine())

    with rig.worker_db.mesh_worker.owner_lock():
        # A live owner holds the database. The second worker refuses, and the
        # first one's in-flight reservation is exactly as it was.
        assert second.run_forever() == 1
        assert rig.worker_db.mesh_worker.get(**key)["state"] == "reserved"

    # The owner exited. NOW its residue is reconciled — by the next owner, once.
    second._stop = True
    assert second.run_forever() == 0
    assert rig.worker_db.mesh_worker.get(**key)["state"] == "indeterminate"


def test_run_once_is_under_the_same_owner_lock(rig) -> None:
    """Repair R2.2: `--once` is a production serve mode, not a test seam.

    It reserves, executes, and settles against the same worker ledger
    `run_forever` does, so two ordinary CLI processes over one worker HOME must
    not be able to touch that ledger at the same time. Before this repair the
    lock covered only one of the two modes, and `holdspeak mesh serve --once`
    walked straight past a live owner into its reservations.
    """
    key = {"hub_key_id": "k", "hub_operation_id": "op_in_flight", "first_ordinal": 1}
    rig.worker_db.mesh_worker.reserve(**key)
    rig.enqueue()
    engine = Engine()
    second = rig.worker(engine)

    with rig.worker_db.mesh_worker.owner_lock():
        assert second.run_once() == 1
        # It refused BEFORE claiming: no poll, no reservation, no model.
        assert rig.sent == []
        assert engine.calls == 0
        assert rig.worker_db.mesh_worker.get(**key)["state"] == "reserved"
        with rig.worker_db._connection() as conn:
            assert conn.execute(
                "SELECT COUNT(*) AS c FROM mesh_worker_reservations"
            ).fetchone()["c"] == 1

    # Once the owner is gone, the same command works normally.
    assert second.run_once() == 0
    assert engine.calls == 1


def test_a_lost_reservation_on_the_refusal_path_also_halts(rig) -> None:
    """Repair R2.2: EVERY terminal path's CAS is checked, including refusal.

    The success path already halted on a failed compare-and-set. The local
    refusal path called the same CAS and threw its answer away, so a worker that
    had lost the ledger kept claiming work it could not account for — the exact
    condition ruling 8 exists to stop.
    """
    rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    worker = rig.worker(Engine())

    class _Refusing:
        """A runner whose local admission refuses by name."""

        def execute(self, authority, payload):
            from holdspeak.mesh_authority import MeshAuthorityRefused

            raise MeshAuthorityRefused("mesh_offer_expired")

        def stop(self, *_a):
            pass

    worker._local_runner = _Refusing()
    rig.worker_db.mesh_worker.settle = lambda **kw: False
    with pytest.raises(MeshServeRefused) as excinfo:
        worker.execute(claimed["job"], offer)
    assert excinfo.value.reason == "mesh_reservation_lost"
    assert worker._stop is True
    assert [url for url, _ in rig.sent if not url.endswith("/claim")] == []


def test_a_stop_during_the_claim_is_inherited_by_the_runner(rig) -> None:
    """Repair R7: a stop that wins BEFORE the runner exists is not lost.

    The runner is built lazily, on first execution. A stop that arrived while the
    claim was still in flight used to have nothing to cancel, and the runner born
    a moment later knew nothing about it — so the physical attempt happened
    anyway. Nothing here preconstructs the runner: this is the real ordering.
    """
    engine = Engine()
    rig.enqueue()
    holder: dict = {}

    def stopping(url, payload, *, token, timeout):
        answer = rig._post(url, payload, token=token, timeout=timeout)
        if url.endswith("/claim"):
            holder["worker"].stop()
        return answer

    worker = rig.worker(engine, http_post=stopping)
    holder["worker"] = worker
    assert worker._local_runner is None  # there is nothing to cancel yet

    assert worker.run_once() == 1
    assert engine.calls == 0, "a stop that won before dispatch must prevent it"
    # Repair R2.3: that same stop also won the terminal-publication election, so
    # the cancelled local receipt is not permission to publish. Only the claim
    # itself ever reached the wire.
    assert [url for url, _ in rig.sent if not url.endswith("/claim")] == []
    assert worker.publishing is False
    assert rig.worker_db.mesh_worker.get(
        hub_key_id=rig.pin.key_id,
        hub_operation_id=rig.warrant["operation_id"],
        first_ordinal=1,
    )["terminal_outcome"] == "cancelled"


# ── ledger ownership and transport ───────────────────────────────────


def test_losing_the_reservation_halts_serving(rig) -> None:
    """Sol ruling 8: a failed terminal CAS means this process lost the ledger."""
    engine = Engine()
    rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    worker = rig.worker(engine)

    original_settle = rig.worker_db.mesh_worker.settle
    rig.worker_db.mesh_worker.settle = lambda **kw: False
    try:
        with pytest.raises(MeshServeRefused) as excinfo:
            worker.execute(claimed["job"], offer)
    finally:
        rig.worker_db.mesh_worker.settle = original_settle
    assert excinfo.value.reason == "mesh_reservation_lost"
    assert worker._stop is True  # it stops claiming rather than guessing
    # Nothing was reported: the cohort it cannot account for is not asserted.
    posted = [url for url, _ in getattr(rig, "sent", []) if url.endswith(("/complete", "/fail"))]
    assert posted == []


def test_a_transport_retry_repeats_the_bytes_and_never_the_model(rig) -> None:
    """Ruling 9: a lost acknowledgement re-sends the SAME report, not the run."""
    import urllib.error

    engine = Engine()
    job = rig.enqueue()
    attempts: list[dict] = []

    def flaky(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            attempts.append(json.loads(json.dumps(payload)))
            if len(attempts) == 1:
                raise urllib.error.URLError("the acknowledgement was lost")
        return rig._post(url, payload, token=token, timeout=timeout)

    assert rig.worker(engine, http_post=flaky).run_once() == 0
    assert engine.calls == 1  # the model ran ONCE
    assert len(attempts) == 2
    assert attempts[0] == attempts[1]  # byte-identical retransmission
    assert rig.hub_db.mesh_relay.get(job.id).result == RESULT_SENTINEL


def _bad_acks(rig) -> list:
    """Acknowledgements that are not this report's, in every shape (repair R9)."""
    return [
        {},
        {"success": True},
        {"success": True, "duplicate": False, "job_id": "relay_other",
         "offer_id": "offer_other", "report_digest": "sha256:" + "0" * 64},
        {"success": False, "duplicate": False, "job_id": "j",
         "offer_id": "o", "report_digest": "sha256:" + "0" * 64},
    ]


@pytest.mark.parametrize("index", range(4))
def test_an_answer_that_does_not_acknowledge_this_report_ends_delivery(rig, index) -> None:
    """A 2xx body is not an acknowledgement (repair R9).

    Retransmission stops only for a body with the exact expected field set that
    names THIS job, THIS offer, and the digest of the exact terminal bytes sent.
    Anything else refuses by name — it never counts as accepted, and it never
    spins the same report against a hub that is answering about something else.
    """
    engine = Engine()
    job = rig.enqueue()
    posts: list[str] = []

    def answering(url, payload, *, token, timeout):
        if url.endswith(("/complete", "/fail")):
            posts.append(url)
            return _bad_acks(rig)[index]
        return rig._post(url, payload, token=token, timeout=timeout)

    assert rig.worker(engine, http_post=answering).run_once() == 1
    assert engine.calls == 1
    assert len(posts) == 1, "an unacknowledged report is not retransmitted blindly"
    # The worker cannot prove settlement from an answer that is not about its
    # report, so it does not claim success — and the row stays unsettled.
    proof = rig.hub_db.mesh_relay.proof(job.id)
    assert proof["status"] == "running" and proof["worker_terminal"] is None


def test_the_real_acknowledgement_names_the_exact_report(rig) -> None:
    """And the acknowledgement the hub actually sends does satisfy that check."""
    from holdspeak.mesh_authority import report_digest

    engine = Engine()
    job = rig.enqueue()
    acks: list[dict] = []

    def watching(url, payload, *, token, timeout):
        answer = rig._post(url, payload, token=token, timeout=timeout)
        if url.endswith("/complete"):
            acks.append((payload["report"], answer))
        return answer

    assert rig.worker(engine, http_post=watching).run_once() == 0
    report, ack = acks[-1]
    assert set(ack) == {"success", "duplicate", "job_id", "offer_id", "report_digest"}
    assert ack["job_id"] == job.id and ack["duplicate"] is False
    assert ack["report_digest"] == report_digest(report)


def test_a_structured_4xx_is_a_decision_and_a_5xx_is_not_an_acknowledgement(rig) -> None:
    """The two things a failed POST can mean, told apart (repairs R9, R2.8).

    `HTTPError` is a `URLError` subclass, so a hub that answered 409 used to look
    exactly like a dropped packet and got the same report re-sent at it until the
    window closed. A structured 4xx is the hub's DECISION and is never retried. A
    5xx means the hub did NOT acknowledge, so the same immutable report may go
    out again inside the signed bounds — that is delivery, not a decision, and
    neither one ever reruns the model.
    """
    import urllib.error

    engine = Engine()
    job = rig.enqueue()
    posts: list[str] = []

    def refusing(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            posts.append(url)
            raise urllib.error.HTTPError(url, 409, "conflict", {}, None)
        return rig._post(url, payload, token=token, timeout=timeout)

    assert rig.worker(engine, http_post=refusing).run_once() == 1
    assert len(posts) == 1 and engine.calls == 1

    # A 5xx is a hub that fell over mid-answer: the SAME bytes go out again.
    engine_two = Engine()
    rig.warrant["operation_id"] = "op_hub_2"
    second = rig.enqueue()
    bodies: list[dict] = []

    def flaky(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            bodies.append(json.loads(json.dumps(payload)))
            if len(bodies) == 1:
                raise urllib.error.HTTPError(url, 503, "unavailable", {}, None)
        return rig._post(url, payload, token=token, timeout=timeout)

    assert rig.worker(engine_two, http_post=flaky).run_once() == 0
    assert engine_two.calls == 1 and len(bodies) == 2 and bodies[0] == bodies[1]
    assert rig.hub_db.mesh_relay.get(second.id).status == "completed"
    # The refused job never settled: its report never reached the hub at all.
    assert rig.hub_db.mesh_relay.proof(job.id)["worker_terminal"] is None


def test_the_report_request_timeout_is_capped_by_the_remaining_window(rig) -> None:
    """Repair R8: no request may be given more time than the offer has left."""
    from datetime import datetime

    engine = Engine()
    seen: list[tuple[str, float]] = []

    def timing(url, payload, *, token, timeout):
        seen.append((url, timeout))
        return rig._post(url, payload, token=token, timeout=timeout)

    rig.hub_db.mesh_relay.enqueue(
        node="edge", user_prompt=PROMPT_SENTINEL,
        envelope={
            "deployment_revision": rig.relay_revision.to_dict(),
            "warrant": rig.warrant, "attempt_ordinal": 1,
        },
        destination_node_id=rig.node_id,
        destination_generation=rig.snapshot.generation,
        deadline_seconds=5,
        now=datetime.now(),
    )
    assert rig.worker(engine, http_post=timing).run_once() == 0

    claim_timeout = [t for url, t in seen if url.endswith("/claim")][0]
    report_timeout = [t for url, t in seen if url.endswith("/complete")][0]
    assert claim_timeout == 30.0  # the default, before any offer exists
    assert 0 < report_timeout <= 5.0 < claim_timeout


def test_a_named_hub_refusal_is_an_answer_not_a_lost_packet(rig) -> None:
    """A refusal that will not change must not be re-sent until the window shuts."""
    from holdspeak.services.errors import ConflictError

    engine = Engine()
    rig.enqueue()
    posts: list[str] = []

    def refusing(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            posts.append(url)
            raise ConflictError("nope", code="mesh_report_conflict")
        return rig._post(url, payload, token=token, timeout=timeout)

    assert rig.worker(engine, http_post=refusing).run_once() == 1
    assert len(posts) == 1


# ── the terminal-publication election (repair R2.3) ──────────────────


def test_a_stop_after_the_first_send_cannot_unsend_the_report(rig) -> None:
    """Repair R2.3: publication that WON is not retracted by a later stop.

    Once the hub has been told, the truth is out; discarding the rest of a
    delivery would leave the two nodes disagreeing about work that physically
    happened. The bytes that keep going out are byte-identical, and the model
    never runs again.
    """
    import urllib.error

    engine = Engine()
    job = rig.enqueue()
    bodies: list[dict] = []
    holder: dict = {}

    def losing_then_stopping(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            bodies.append(json.loads(json.dumps(payload)))
            if len(bodies) == 1:
                # The first send BEGAN — publication has won the election — and
                # only then does a stop arrive.
                holder["worker"].stop()
                raise urllib.error.URLError("the acknowledgement was lost")
        return rig._post(url, payload, token=token, timeout=timeout)

    worker = rig.worker(engine, http_post=losing_then_stopping)
    holder["worker"] = worker
    assert worker.run_once() == 0

    assert worker._stop is True and worker.publishing is True
    assert engine.calls == 1, "a stop must not rerun the model"
    assert len(bodies) == 2 and bodies[0] == bodies[1]
    assert rig.hub_db.mesh_relay.get(job.id).status == "completed"


def test_a_stop_between_the_local_receipt_and_the_report_sends_nothing(rig) -> None:
    """The pre-send interval is covered too: stop there wins (repair R2.3)."""
    engine = Engine()
    job = rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    worker = rig.worker(engine)

    # The window between "every local receipt is durable" and "the first send
    # begins" is where a stop used to be lost entirely.
    original = rig.worker_db.mesh_worker.settle

    def settle_then_stop(**kw):
        owned = original(**kw)
        worker.stop()
        return owned

    rig.worker_db.mesh_worker.settle = settle_then_stop
    try:
        assert worker.execute(claimed["job"], offer) is False
    finally:
        rig.worker_db.mesh_worker.settle = original

    assert engine.calls == 1, "the physical attempt had already happened"
    assert worker.publishing is False
    assert [url for url, _ in rig.sent if not url.endswith("/claim")] == []
    # Local truth is durable; the hub simply never heard, and its own deadline
    # is what closes the job.
    assert rig.hub_db.mesh_relay.get(job.id).status == "running"
    with rig.worker_db._connection() as conn:
        assert [
            row["outcome"] for row in conn.execute("SELECT outcome FROM kernel_receipts")
        ] == ["succeeded"]


@pytest.mark.timeout(60)
def test_a_stop_during_local_execution_still_publishes_nothing(rig) -> None:
    """Stop while the provider is running: the cohort is never published.

    The stop arrives on ANOTHER thread, the way a signal handler or a second
    `Ctrl-C` reaches a worker that is already inside a model call. The physical
    attempt may finish — a provider that ignores cancellation is the design's
    recorded note — but the election has already been lost, so nothing is sent.
    """
    import threading
    import time as _time

    engine = Engine()
    rig.enqueue()
    claimed = rig.claim()
    offer = rig.verify(claimed)
    worker = rig.worker(engine)

    class _StoppingEngine(Engine):
        def run_prompt(self, **kw):
            # `stop` blocks until the dispatch it is cancelling settles, so it
            # cannot be called from this thread; a real stop never is.
            threading.Thread(target=worker.stop, daemon=True).start()
            deadline = _time.time() + 10
            while not worker._stop and _time.time() < deadline:
                _time.sleep(0.005)
            assert worker._stop, "the stop must land while the provider is running"
            return super().run_prompt(**kw)

    worker._engine_factory = lambda revision, **_kw: _StoppingEngine()
    assert worker.execute(claimed["job"], offer) is False
    assert worker.publishing is False
    assert [url for url, _ in rig.sent if not url.endswith("/claim")] == []


# ── HTTP response versus delivery loss (repair R2.8) ─────────────────


def test_a_structured_4xx_surfaces_its_fixed_code_once(rig, caplog) -> None:
    """Repair R2.8: the hub's own refusal CLASS is named, and named once.

    The edge answers a refusal with a strict ``{"error", "code"}`` body. Parsing
    exactly that shape is what turns "HTTP 409" back into the rule that refused;
    the raw body never travels further than the parse, so a hub that echoed
    content cannot leak it into a log line.
    """
    import io
    import logging
    import urllib.error

    engine = Engine()
    rig.enqueue()
    posts: list[str] = []
    body = json.dumps(
        {"error": f"nope {PROMPT_SENTINEL}", "code": "mesh_report_conflict"}
    ).encode()

    def refusing(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            posts.append(url)
            raise urllib.error.HTTPError(
                url, 409, "conflict", {}, io.BytesIO(body)
            )
        return rig._post(url, payload, token=token, timeout=timeout)

    with caplog.at_level(logging.WARNING, logger="holdspeak.mesh.serve"):
        assert rig.worker(engine, http_post=refusing).run_once() == 1
    assert len(posts) == 1, "a decision is never retried"
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert logged.count("mesh_report_conflict") == 1
    assert PROMPT_SENTINEL not in logged, "the raw body must not escape"


def test_a_malformed_4xx_body_is_still_terminal(rig) -> None:
    """No structured code is still a decision, not transport loss."""
    import io
    import urllib.error

    engine = Engine()
    rig.enqueue()
    posts: list[str] = []

    def refusing(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            posts.append(url)
            raise urllib.error.HTTPError(
                url, 400, "bad", {}, io.BytesIO(b"not json at all")
            )
        return rig._post(url, payload, token=token, timeout=timeout)

    assert rig.worker(engine, http_post=refusing).run_once() == 1
    assert len(posts) == 1


def test_a_5xx_that_never_clears_ends_as_the_fixed_unavailable_class(rig, caplog) -> None:
    """Repair R2.8: 5xx is NOT acknowledgement, and exhaustion has a name.

    A 5xx means the hub did not acknowledge, so the SAME immutable report may go
    out again inside the signed count and window. When that runs out the delivery
    ends as the fixed class `mesh_hub_unavailable` — never as a hub decision, and
    never by rerunning the model.
    """
    import logging
    import urllib.error

    engine = Engine()
    job = rig.enqueue()
    bodies: list[dict] = []

    def always_500(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            bodies.append(json.loads(json.dumps(payload)))
            raise urllib.error.HTTPError(url, 503, "unavailable", {}, None)
        return rig._post(url, payload, token=token, timeout=timeout)

    with caplog.at_level(logging.WARNING, logger="holdspeak.mesh.serve"):
        assert rig.worker(engine, http_post=always_500).run_once() == 1

    from holdspeak.commands.mesh_serve import REPORT_RETRY_LIMIT

    assert len(bodies) == REPORT_RETRY_LIMIT
    assert all(body == bodies[0] for body in bodies), "the report is immutable"
    assert engine.calls == 1, "delivery retry never repeats the model"
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert "mesh_hub_unavailable" in logged
    # The hub never accepted it, and says so.
    assert rig.hub_db.mesh_relay.proof(job.id)["worker_terminal"] is None


def test_an_unknown_local_reason_becomes_the_fixed_generic_class(rig) -> None:
    """Repair R2.7: the worker MAPS, and the hub only ever sees the set.

    A lowercase-token shape was never a vocabulary. An unrecognised kernel
    control class satisfies it completely while saying something both nodes never
    agreed to transport — so every unknown reason collapses to one fixed generic
    here, before the report is built.
    """
    from holdspeak.kernel.mesh_local_runner import MeshLocalRunner
    from holdspeak.mesh_authority.report import (
        GENERIC_FAILURE_CLASS,
        SAFE_FAILURE_CLASSES,
    )
    from types import SimpleNamespace

    for reason in (
        "adapter_context_required", "credential", "prompt", "token",
        "inference_deployment_revision_unknown", "api_key_rejected",
    ):
        outcome = SimpleNamespace(outcome="refused", error=reason)
        assert MeshLocalRunner._failure_class(outcome) == GENERIC_FAILURE_CLASS

    # A class the protocol DID define survives unchanged.
    known = SimpleNamespace(outcome="refused", error="mesh_execution_target_recursive")
    assert MeshLocalRunner._failure_class(known) == "mesh_execution_target_recursive"
    assert MeshLocalRunner._failure_class(
        SimpleNamespace(outcome="failed", error="")
    ) == "failed"
    assert GENERIC_FAILURE_CLASS in SAFE_FAILURE_CLASSES

    # And end to end: an ordinary provider explosion reports the generic class
    # rather than anything the exception said.
    rig.enqueue()
    engine = Engine(error=RuntimeError(f"boom {PROMPT_SENTINEL}"))
    assert rig.worker(engine).run_once() == 1
    report = rig.sent[-1][1]["report"]
    assert report["failure_class"] in SAFE_FAILURE_CLASSES
    assert PROMPT_SENTINEL not in json.dumps(report)


def test_a_socket_failure_is_bounded_by_the_same_count(rig) -> None:
    """Transport loss is retried, bounded, and ends with the same fixed class."""
    import socket

    engine = Engine()
    rig.enqueue()
    attempts: list[str] = []

    def unreachable(url, payload, *, token, timeout):
        if url.endswith("/complete"):
            attempts.append(url)
            raise socket.timeout("no route")
        return rig._post(url, payload, token=token, timeout=timeout)

    from holdspeak.commands.mesh_serve import REPORT_RETRY_LIMIT

    assert rig.worker(engine, http_post=unreachable).run_once() == 1
    assert len(attempts) == REPORT_RETRY_LIMIT
    assert engine.calls == 1


# ── construction guards ──────────────────────────────────────────────


def test_recursion_guard_refuses_a_mesh_engine(rig) -> None:
    """A serving node whose factory resolves back onto the mesh refuses by name."""
    from holdspeak.intel.mesh_relay import MeshRelayIntel

    job = rig.enqueue()
    worker = rig.worker(MeshRelayIntel(node="edge", relay=object()))
    assert worker.run_once() == 1

    reported = [body for url, body in rig.sent if url.endswith("/fail")]
    # The refusal is the EXACT structural one, not a generic failure: the guard
    # fires before adapter dispatch, so the node never relays the job onward.
    assert reported
    assert reported[-1]["report"]["failure_class"] == "mesh_execution_target_recursive"
    assert rig.hub_db.mesh_relay.get(job.id).status == "failed"


def test_the_worker_never_derives_its_own_target(rig) -> None:
    """Construction rides the SIGNED execution revision, not local configuration."""
    engine = Engine()
    claimed_revisions: list[str] = []
    rig.enqueue()

    def recording_factory(revision, **_kw):
        claimed_revisions.append(revision.id)
        return engine

    worker = rig.worker(engine)
    worker._engine_factory = recording_factory
    worker.run_once()
    assert claimed_revisions == [rig.execution_revision.id]
    persisted = rig.worker_db.deployment_revisions.get(rig.execution_revision.id)
    assert persisted is not None and persisted.endpoint == rig.execution_revision.endpoint


# ── the CLI ──────────────────────────────────────────────────────────


def test_cli_wiring_parses() -> None:
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "holdspeak.main", "mesh", "--help"],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0
    assert "serve" in proc.stdout


def test_the_real_parser_defaults_to_the_node_credential() -> None:
    """Repair R2: the SHIPPED parser, not a module constant, decides this.

    `mesh serve` used to default to `HOLDSPEAK_HUB_TOKEN` — the browser owner
    token. That posture is removed rather than demoted to a fallback, and the
    place it has to be removed is the argument surface an operator actually types.
    """
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "holdspeak.main", "mesh", "serve", "--help"],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0
    assert "HOLDSPEAK_NODE_TOKEN" in proc.stdout
    assert "HOLDSPEAK_HUB_TOKEN" not in proc.stdout


def test_serving_without_a_node_credential_refuses_by_name(monkeypatch, tmp_path) -> None:
    """The shared owner token posture is GONE, not a fallback."""
    from holdspeak.commands import mesh_serve
    from holdspeak.delivery import node_credentials
    from holdspeak.delivery.node_credentials import MeshHubPin, save_hub_pin

    monkeypatch.delenv("HOLDSPEAK_NODE_TOKEN", raising=False)
    monkeypatch.setenv("HOLDSPEAK_HUB_TOKEN", "an-owner-token")
    # A pin with no token in custody: the owner token in the environment is not
    # a credential this command will ever reach for.
    pin_path = tmp_path / "pin.json"
    save_hub_pin(
        MeshHubPin(
            node_name="edge", node_id="node_1", generation=1, key_id="meshkey_1",
            offer_public_key="ab" * 32,
        ),
        path=pin_path,
    )
    monkeypatch.setattr(node_credentials, "DEFAULT_HUB_PIN_PATH", pin_path)
    args = type("Args", (), {"hub": "http://hub", "once": True})()
    assert mesh_serve.run_mesh_serve_command(args) == 1
    assert mesh_serve.DEFAULT_TOKEN_ENV == "HOLDSPEAK_NODE_TOKEN"


def test_a_paired_node_without_a_pin_cannot_serve(monkeypatch, tmp_path) -> None:
    from holdspeak.commands import mesh_serve
    from holdspeak.delivery import node_credentials

    monkeypatch.setenv("HOLDSPEAK_NODE_TOKEN", "a-node-token")
    monkeypatch.setattr(
        node_credentials, "DEFAULT_HUB_PIN_PATH", tmp_path / "absent.json"
    )
    args = type("Args", (), {"hub": "http://hub", "once": True})()
    assert mesh_serve.run_mesh_serve_command(args) == 1


def test_the_product_pairing_path_carries_the_credential_to_the_worker(
    monkeypatch, tmp_path
) -> None:
    """Repair R2: export → import → serve, through the shipped commands.

    The hub exports one owner-only transfer document; this machine imports it
    with `holdspeak node pair`; `mesh serve` then loads BOTH halves of its
    credential out of local custody through the product loader. Nothing here
    hand-builds a pin, and the hub's offer private key never appears in any of it.
    """
    from holdspeak.commands import mesh_serve
    from holdspeak.commands.node_serve import main as node_main
    from holdspeak.delivery import node_credentials
    from holdspeak.delivery.node_link import NodeTokenStore

    # ── the hub machine ──
    hub_store = tmp_path / "hub" / "nodes.json"
    store = NodeTokenStore(hub_store)
    node_id, token = store.create("edge")
    transfer = tmp_path / "pairing.json"
    assert node_main([
        "token", "export", "--name", "edge",
        "--out", str(transfer), "--store-path", str(hub_store),
    ]) == 0

    exported = transfer.read_text()
    assert token in exported
    assert store.signing_snapshot("edge").offer_private_key not in exported
    assert transfer.stat().st_mode & 0o077 == 0  # owner-only, like every custody

    # ── the worker machine ──
    pin_path = tmp_path / "worker" / "pin.json"
    assert node_main(["pair", "--from", str(transfer), "--pin-path", str(pin_path)]) == 0
    monkeypatch.setattr(node_credentials, "DEFAULT_HUB_PIN_PATH", pin_path)
    monkeypatch.delenv("HOLDSPEAK_NODE_TOKEN", raising=False)

    captured: dict = {}

    class Recorder:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def run_once(self) -> int:
            return 0

    monkeypatch.setattr(mesh_serve, "MeshServeWorker", Recorder)
    args = type("Args", (), {"hub": "http://hub", "once": True})()
    assert mesh_serve.run_mesh_serve_command(args) == 0

    assert captured["token"] == token
    assert captured["pin"].node_id == node_id
    assert captured["pin"].node_name == "edge"
    assert captured["pin"].generation == 1
    assert captured["pin"].key_id == store.pairing("edge").key_id
    # And the environment still wins when an operator prefers it there.
    monkeypatch.setenv("HOLDSPEAK_NODE_TOKEN", "from-the-environment")
    assert mesh_serve.run_mesh_serve_command(args) == 0
    assert captured["token"] == "from-the-environment"


def test_a_pairing_transfer_never_carries_the_hub_private_key(tmp_path) -> None:
    """The one thing an export may not do, refused structurally."""
    from holdspeak.delivery.node_credentials import (
        NodeCustodyError,
        read_pairing_transfer,
        write_private_document,
    )
    from holdspeak.delivery.node_link import NodeTokenStore

    store = NodeTokenStore(tmp_path / "nodes.json")
    _node_id, token, snapshot = store.pair("edge")
    signing = store.signing_snapshot("edge")

    smuggled = tmp_path / "smuggled.json"
    write_private_document(smuggled, {
        "mesh_pairing_transfer_schema": 1,
        "node_name": snapshot.name,
        "node_id": snapshot.node_id,
        "generation": snapshot.generation,
        "key_id": snapshot.key_id,
        "offer_public_key": snapshot.offer_public_key,
        "node_token": token,
        "offer_private_key": signing.offer_private_key,
    })
    with pytest.raises(NodeCustodyError) as excinfo:
        read_pairing_transfer(smuggled)
    assert excinfo.value.reason == "node_custody_malformed"


def test_a_credential_snapshot_never_renders_its_secrets() -> None:
    """Repair R1: the redaction seam, at the type itself.

    A snapshot travels as an ordinary argument and lands in logs, tracebacks,
    and observer rows through `repr`. Its secrets are not renderable.
    """
    from holdspeak.delivery.node_credentials import NodeCredentialSnapshot

    snapshot = NodeCredentialSnapshot(
        name="edge", node_id="node_1", generation=2, key_id="meshkey_1",
        offer_public_key="ab" * 32, token="SECRET-TOKEN",
        offer_private_key="SECRET-PRIVATE-KEY",
    )
    rendered = f"{snapshot!r} {snapshot} {json.dumps(snapshot, default=str)}"
    assert "SECRET-TOKEN" not in rendered
    assert "SECRET-PRIVATE-KEY" not in rendered
    assert "node_1" in rendered and "<redacted>" in rendered
