"""HS-131-02: each provider dispatch is one admitted invocation child."""
from __future__ import annotations

import math
import threading
import time
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.deployment_revisions import capture_deployment_revision
from holdspeak.inference_targets import resolve_inference_target
from holdspeak.kernel.inference_runner import (
    ClosurePersistenceError, InferenceRunner, InvocationRequest, ProviderIndeterminate, SavedDefinition,
    ServiceContract,
)
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "owner")


class Adapter:
    def __init__(self, result="result", error=None):
        self.result, self.error, self.cancelled = result, error, False

    def dispatch(self, engine, payload, cancellation):
        if self.error:
            raise self.error
        return self.result

    def cancel(self):
        self.cancelled = True
        return "cancelled"


@pytest.fixture
def rig(tmp_path: Path):
    db = Database(tmp_path / "runner.db")
    db.profiles.upsert(
        profile_id="local", name="Local", kind="onDevice", model_file="/model.gguf",
    )
    revision = capture_deployment_revision(db, resolve_inference_target(db, "local"))
    return db, _configure(db), revision


def request(revision, *, origin=None, payload=None):
    payload = {"question": "private prompt"} if payload is None else payload
    return InvocationRequest(
        deployment_revision=revision.id,
        definition_origin=origin or ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=time.time() + 30, payload=payload,
    )


@pytest.mark.parametrize(
    ("error", "outcome"),
    [(None, "succeeded"), (KernelRefused("adapter_refused"), "refused"), (RuntimeError(), "failed"), (ProviderIndeterminate(), "indeterminate")],
)
def test_each_terminal_outcome_has_one_immutable_receipt(rig, error, outcome):
    db, broker, revision = rig
    runner = InferenceRunner(broker, db, engine_factory=lambda value: {"revision": value.id}, principal_provider=lambda: OWNER)
    result = runner.invoke(request(revision), Adapter(error=error))
    receipt = broker.store.receipt(result.operation_id)
    assert result.outcome == receipt["outcome"] == outcome
    assert broker.receipt(result.operation_id, outcome, result.result_ref, Principal(
        PrincipalKind.NODE, broker.store.operation(result.operation_id)["placement"].removeprefix("node:")
    )) == receipt



@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_service_contract_and_runner_refuse_nonfinite_payloads(rig, value):
    db, broker, revision = rig
    with pytest.raises(KernelRefused, match="inference_payload_not_canonicalizable"):
        ServiceContract.for_payload("ask", "v1", {"number": value})
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    with pytest.raises(KernelRefused, match="inference_payload_not_canonicalizable"):
        runner.invoke(InvocationRequest(
            deployment_revision=revision.id,
            definition_origin=ServiceContract("ask", "v1", ""),
            deadline_at=time.time() + 30, payload={"number": value},
        ), Adapter())


def test_hash_mismatch_and_stale_saved_revision_refuse_before_dispatch(rig):
    db, broker, revision = rig
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    with pytest.raises(KernelRefused, match="inference_payload_hash_mismatch"):
        runner.invoke(request(revision, origin=ServiceContract("ask", "v1", "sha256:" + "0" * 64)), Adapter())
    db.recipes.upsert(recipe_id="stale", name="Stale")
    with pytest.raises(KernelRefused, match="inference_saved_definition_revision_unknown"):
        runner.invoke(request(revision, origin=SavedDefinition("recipe:stale", "stale-revision")), Adapter())


def test_saved_and_service_origins_remain_distinct(rig):
    db, broker, revision = rig
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    saved_recipe = db.recipes.upsert(recipe_id="one", name="One")
    saved = runner.invoke(
        request(revision, origin=SavedDefinition("recipe:one", saved_recipe.last_modified)), Adapter()
    )
    service = runner.invoke(request(revision), Adapter())
    saved_op = broker.store.operation(saved.operation_id)
    service_op = broker.store.operation(service.operation_id)
    events = broker.events(0, {"operation_id": saved.operation_id}, OWNER)["events"]
    assert "recipe:one" in events[0]["refs"]
    assert saved_op["envelope_sha256"] != service_op["envelope_sha256"]


def test_fallback_is_two_invocations_not_one_logical_receipt(rig):
    db, broker, revision = rig
    parent = broker.submit({
        "request_schema": 1, "request_id": "fallback-parent", "idempotency_key": "fallback-parent",
        "operation": {"name": "inference.run", "version": 1}, "target": {},
        "arguments": {"invocation_id": "fallback-parent", "definition_ref": "recipe:one",
                      "definition_revision": "rev-1", "grounding_refs": [], "requested_target_id": "local",
                      "deadline_at": time.time() + 30, "input_snapshot": {}},
    }, OWNER)
    parent = broker.decide(parent["operation_id"], "approve", parent["revision"], OWNER)
    parent_operation = broker.store.operation(parent["operation_id"])
    broker.claim(Principal(PrincipalKind.NODE, parent_operation["placement"].removeprefix("node:")), "fallback-parent")
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    first = runner.invoke(InvocationRequest(**{**request(revision).__dict__, "parent_operation_id": parent_operation["operation_id"], "attempt_ordinal": 1}), Adapter(error=RuntimeError()))
    second = runner.invoke(InvocationRequest(**{**request(revision).__dict__, "parent_operation_id": parent_operation["operation_id"], "attempt_ordinal": 2}), Adapter())
    assert {first.outcome, second.outcome} == {"failed", "succeeded"}
    assert len({first.operation_id, second.operation_id}) == 2
    assert all(broker.store.operation(item.operation_id)["parent_operation_id"] == parent_operation["operation_id"] for item in (first, second))
    assert broker.store.receipt(first.operation_id) and broker.store.receipt(second.operation_id)


def test_remote_dispatch_keeps_a_linked_egress_effect(rig):
    db, broker, _ = rig
    db.profiles.upsert(
        profile_id="remote", name="Remote", kind="openAICompatible",
        base_url="https://example.test/v1", model="remote-model",
    )
    revision = capture_deployment_revision(db, resolve_inference_target(db, "remote"))

    class Remote(Adapter):
        egress_destination = "example.test"
        connector_id = "reference-provider"
        egress_data_classes = ("instruction",)

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    invocation = runner.invoke(request(revision), Remote())
    events = broker.events(0, {}, OWNER)["events"]
    egress_admission = next(event for event in events if "egress:example.test" in event["refs"])
    egress = broker.store.operation(egress_admission["operation_id"])
    assert invocation.outcome == "succeeded"
    assert egress["name"] == "external.egress"
    assert egress["parent_operation_id"] == invocation.operation_id
    assert broker.store.receipt(egress["operation_id"])["outcome"] == "succeeded"


def test_cancellation_reaches_adapter_and_blocks_late_publication(rig):
    db, broker, revision = rig
    started = threading.Event()
    release = threading.Event()
    published: list[str] = []

    class Slow(Adapter):
        def dispatch(self, engine, payload, cancellation):
            started.set()
            release.wait(2)
            return "late output"

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    result = []
    thread = threading.Thread(target=lambda: result.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "caller_cancel"}), Slow(), publish=lambda value: published.append(value) or "answer:late"
    )))
    thread.start()
    assert started.wait(2)
    assert runner.cancel("caller_cancel") == "cancelled"
    release.set()
    thread.join(2)
    assert result[0].outcome == "cancelled"
    assert published == []
    assert broker.store.receipt(result[0].operation_id)["outcome"] == "cancelled"
    assert broker.store.receipt(result[0].operation_id)["state"] == "cancelled"


def test_pending_cancel_authenticates_before_registration(rig):
    db, broker, _ = rig
    runner = InferenceRunner(
        broker, db, engine_factory=lambda _: object(),
        principal_provider=lambda: (_ for _ in ()).throw(KernelRefused("principal_authentication_required")),
    )
    with pytest.raises(KernelRefused, match="principal_authentication_required"):
        runner.cancel("not_active_yet")
    assert runner._pending_cancellations == {}


def test_expired_deadline_refuses_before_provider_dispatch(rig):
    db, broker, revision = rig
    adapter = Adapter()
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    result = runner.invoke(InvocationRequest(
        **{**request(revision).__dict__, "deadline_at": time.time() - 1}
    ), adapter)
    assert result.outcome == "refused"
    assert adapter.cancelled is False


def test_deadline_cancels_a_blocked_dispatch_through_cancel_operation(rig):
    db, broker, revision = rig
    stopped = threading.Event()

    class Blocked(Adapter):
        def dispatch(self, engine, payload, cancellation):
            stopped.wait(2)
            return "late"

        def cancel(self):
            stopped.set()
            return "cancelled"

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    result = runner.invoke(InvocationRequest(
        **{**request(revision).__dict__, "invocation_id": "deadline_cancel", "deadline_at": time.time() + .1}
    ), Blocked())
    assert result.outcome == "cancelled"
    signals = [event for event in broker.events(0, {}, OWNER)["events"] if event["operation_id"] != result.operation_id]
    assert any(event["event_type"] == "operation.receipt" for event in signals)


def test_deadline_unknown_provider_closes_indeterminate_before_dispatch_returns(rig):
    db, broker, revision = rig
    entered = threading.Event()
    never = threading.Event()

    class Hung(Adapter):
        def dispatch(self, engine, payload, cancellation):
            entered.set()
            never.wait()
            return "unreachable"

        def cancel(self):
            return "unknown"

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    thread = threading.Thread(target=lambda: runner.invoke(InvocationRequest(
        **{**request(revision).__dict__, "invocation_id": "hung_deadline", "deadline_at": time.time() + .1}
    ), Hung()), daemon=True)
    thread.start()
    assert entered.wait(1)
    operation = broker.store.operation_for_native("hung_deadline")
    assert operation is not None
    receipt = None
    for _ in range(40):
        receipt = broker.store.receipt(operation["operation_id"])
        if receipt is not None:
            break
        time.sleep(.05)
    assert receipt is not None and receipt["outcome"] == "indeterminate"


def test_unknown_cancel_disposition_closes_indeterminate(rig):
    db, broker, revision = rig
    release = threading.Event()

    class Unknown(Adapter):
        def dispatch(self, engine, payload, cancellation):
            release.wait(2)
            return "late"

        def cancel(self):
            release.set()
            return "unknown"

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    results = []
    thread = threading.Thread(target=lambda: results.append(runner.invoke(InvocationRequest(
        **{**request(revision).__dict__, "invocation_id": "unknown_cancel"}
    ), Unknown())))
    thread.start()
    time.sleep(.05)
    assert runner.cancel("unknown_cancel") in {"pending", "unknown"}
    thread.join(2)
    assert results[0].outcome == "indeterminate"


def test_completed_cancel_disposition_allows_completed_result(rig):
    db, broker, revision = rig
    release = threading.Event()

    class Completed(Adapter):
        def dispatch(self, engine, payload, cancellation):
            release.wait(2)
            return "completed"

        def cancel(self):
            release.set()
            return "completed"

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    results = []
    thread = threading.Thread(target=lambda: results.append(runner.invoke(InvocationRequest(
        **{**request(revision).__dict__, "invocation_id": "completed_cancel"}
    ), Completed())))
    thread.start()
    time.sleep(.05)
    assert runner.cancel("completed_cancel") in {"pending", "completed"}
    thread.join(2)
    assert results[0].outcome == "succeeded"


def test_publish_errors_and_invalid_result_refs_close_failed(rig):
    db, broker, revision = rig
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    thrown = runner.invoke(request(revision), Adapter(), publish=lambda _: (_ for _ in ()).throw(RuntimeError("write failed")))
    invalid = runner.invoke(request(revision), Adapter(), publish=lambda _: "not a ref")
    assert thrown.outcome == invalid.outcome == "failed"
    assert broker.store.receipt(thrown.operation_id)["state"] == "failed"
    assert broker.store.receipt(invalid.operation_id)["state"] == "failed"


def test_claim_rechecks_revoked_parent_before_provider_dispatch(rig):
    db, broker, revision = rig
    # This direct operation is an outer run only; the runner's child must reject
    # after its parent loses liveness before the child claim.
    parent = broker.submit({
        "request_schema": 1, "request_id": "parent", "idempotency_key": "parent",
        "operation": {"name": "inference.run", "version": 1}, "target": {},
        "arguments": {"invocation_id": "parent", "definition_ref": "recipe:one",
                      "definition_revision": "rev-1", "grounding_refs": [],
                      "requested_target_id": "local", "deadline_at": time.time() + 30,
                      "input_snapshot": {}},
    }, OWNER)
    parent = broker.decide(parent["operation_id"], "approve", parent["revision"], OWNER)
    parent_op = broker.store.operation(parent["operation_id"])
    parent_node = Principal(PrincipalKind.NODE, parent_op["placement"].removeprefix("node:"))
    broker.claim(parent_node, "parent")
    broker.store.revoke_warrant(parent_op["operation_id"])
    adapter = Adapter()
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    result = runner.invoke(InvocationRequest(
        **{**request(revision).__dict__, "parent_operation_id": parent_op["operation_id"]}
    ), adapter)
    assert result.outcome == "refused"
    assert adapter.cancelled is False


def test_agent_child_derives_live_owner_parent_authority(rig):
    db, broker, revision = rig
    parent = broker.submit({
        "request_schema": 1, "request_id": "authority-parent", "idempotency_key": "authority-parent",
        "operation": {"name": "inference.run", "version": 1}, "target": {},
        "arguments": {"invocation_id": "authority-parent", "definition_ref": "recipe:one",
                      "definition_revision": "rev-1", "grounding_refs": [], "requested_target_id": "local",
                      "deadline_at": time.time() + 30, "input_snapshot": {},
                      "continuation_identities": ["agent:child"]},
    }, OWNER)
    parent = broker.decide(parent["operation_id"], "approve", parent["revision"], OWNER)
    parent_operation = broker.store.operation(parent["operation_id"])
    broker.claim(Principal(PrincipalKind.NODE, parent_operation["placement"].removeprefix("node:")), "authority-parent")
    agent = Principal(PrincipalKind.AGENT, "agent:child")
    class DelegatedRemote(Adapter):
        egress_destination = "example.test"
        egress_data_classes = ("instruction",)

    db.profiles.upsert(profile_id="delegated-remote", name="Remote", kind="openAICompatible", base_url="https://example.test/v1", model="remote")
    remote_revision = capture_deployment_revision(db, resolve_inference_target(db, "delegated-remote"))
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: agent)
    result = runner.invoke(InvocationRequest(**{
        **request(remote_revision).__dict__, "parent_operation_id": parent_operation["operation_id"]
    }), DelegatedRemote())
    assert result.outcome == "succeeded"
    assert broker.store.operation(result.operation_id)["principal_identity"] == "agent:child"


def test_journal_has_no_prompt_output_or_audio_bodies(rig):
    db, broker, revision = rig
    prompt, output, audio = "PROMPT_BODY", "MODEL_OUTPUT", "AUDIO_FRAME"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    result = runner.invoke(request(revision, payload={"prompt": prompt, "audio_frame": audio}), Adapter(output))
    assert result.outcome == "succeeded"
    journal = str(broker.events(0, {}, OWNER))
    assert prompt not in journal and output not in journal and audio not in journal


def test_canceller_wins_before_publisher_transition(rig):
    db, broker, revision = rig
    dispatch_ready, release = threading.Event(), threading.Event()
    published, results = [], []

    class Choreographed(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatch_ready.set(); assert release.wait(2); return "late"

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    worker = threading.Thread(target=lambda: results.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "canceller_wins"}),
        Choreographed(), publish=lambda value: published.append(value) or "answer:late")))
    worker.start(); assert dispatch_ready.wait(2)
    assert runner.cancel("canceller_wins") == "cancelled"
    release.set(); worker.join(2)
    assert not worker.is_alive() and results[0].outcome == "cancelled" and published == []


def test_publisher_wins_before_cancel_request(rig):
    db, broker, revision = rig
    publishing, release, returned = threading.Event(), threading.Event(), []
    class Immediate(Adapter):
        pass
    def publish(value):
        publishing.set(); assert release.wait(2); return "answer:published"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    worker = threading.Thread(target=lambda: returned.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "publisher_wins"}), Immediate(), publish=publish)))
    worker.start(); assert publishing.wait(2)
    assert runner.cancel("publisher_wins") == "completed"
    release.set(); worker.join(2)
    assert not worker.is_alive() and returned[0].outcome == "succeeded"
    assert broker.store.receipt(returned[0].operation_id)["outcome"] == "succeeded"
    assert not any(broker.store.operation(event["operation_id"])["name"] == "inference.cancel" for event in broker.events(0, {}, OWNER)["events"])


def test_refused_cancellation_restores_running_and_publishes(rig):
    db, broker, revision = rig
    entered, release, results = threading.Event(), threading.Event(), []
    current = [OWNER]
    class Waiting(Adapter):
        def dispatch(self, engine, payload, cancellation):
            entered.set(); assert release.wait(2); return "normal"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: current[0])
    worker = threading.Thread(target=lambda: results.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "refused_cancel"}), Waiting())))
    worker.start(); assert entered.wait(2)
    current[0] = Principal(PrincipalKind.AGENT, "untrusted-canceller")
    assert runner.cancel("refused_cancel") == "refused"
    current[0] = OWNER; release.set(); worker.join(2)
    assert not worker.is_alive() and results[0].outcome == "succeeded"
    cancel_ops = [op for op in (broker.store.operation(event["operation_id"]) for event in broker.events(0, {}, OWNER)["events"]) if op["name"] == "inference.cancel"]
    assert cancel_ops and broker.store.receipt(cancel_ops[-1]["operation_id"])["state"] == "refused"


def test_pending_cancellation_uses_stored_authenticated_principal(rig):
    db, broker, revision = rig
    stored = Principal(PrincipalKind.OWNER, "stored-canceller")
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: stored)
    assert runner.cancel("pending_stored_principal") == "pending"
    runner._principal_provider = lambda: OWNER
    result = runner.invoke(InvocationRequest(**{**request(revision).__dict__, "invocation_id": "pending_stored_principal"}), Adapter())
    cancel_ops = [broker.store.operation(event["operation_id"]) for event in broker.events(0, {}, OWNER)["events"]]
    cancel = next(op for op in cancel_ops if op["name"] == "inference.cancel")
    assert result.outcome == "cancelled" and cancel["principal_identity"] == stored.identity


def test_terminal_receipts_gate_both_invoke_and_cancel_returns(rig):
    db, broker, revision = rig
    started, entered, release, finished = threading.Event(), threading.Event(), threading.Event(), []
    original_receipt = broker.receipt
    def gated_receipt(operation_id, outcome, result_ref, node):
        if outcome in {"cancelled", "succeeded"}:
            entered.set(); assert release.wait(2)
        return original_receipt(operation_id, outcome, result_ref, node)
    broker.receipt = gated_receipt
    class Waiting(Adapter):
        def dispatch(self, engine, payload, cancellation):
            started.set(); assert release.wait(2); return "late"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    invoke_thread = threading.Thread(target=lambda: finished.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "receipt_order"}), Waiting())))
    invoke_thread.start(); assert started.wait(2)
    cancel_thread = threading.Thread(target=lambda: runner.cancel("receipt_order"))
    cancel_thread.start(); assert entered.wait(2)
    assert invoke_thread.is_alive() and cancel_thread.is_alive()
    release.set(); cancel_thread.join(2); invoke_thread.join(2)
    assert not cancel_thread.is_alive() and not invoke_thread.is_alive() and finished[0].outcome == "cancelled"


def test_cancel_submit_failure_restores_running_and_notifies_waiters(rig):
    db, broker, revision = rig
    entered, release, results = threading.Event(), threading.Event(), []
    original_submit = broker.submit
    def submit(raw, principal):
        if raw["operation"]["name"] == "inference.cancel": raise RuntimeError("cancel admission unavailable")
        return original_submit(raw, principal)
    broker.submit = submit
    class Waiting(Adapter):
        def dispatch(self, engine, payload, cancellation):
            entered.set(); assert release.wait(2); return "normal"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    worker = threading.Thread(target=lambda: results.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "submit_raises"}), Waiting())))
    worker.start(); assert entered.wait(2)
    assert runner.cancel("submit_raises") == "refused"
    release.set(); worker.join(2)
    assert not worker.is_alive() and results[0].outcome == "succeeded"


def test_receipt_failure_after_acknowledgement_never_publishes_late_result(rig):
    db, broker, revision = rig
    entered, release, results, errors = threading.Event(), threading.Event(), [], []
    original_receipt = broker.receipt
    def failing_receipt(operation_id, outcome, result_ref, node):
        if outcome == "cancelled": raise RuntimeError("receipt disk failure")
        return original_receipt(operation_id, outcome, result_ref, node)
    broker.receipt = failing_receipt
    class Waiting(Adapter):
        def dispatch(self, engine, payload, cancellation):
            entered.set(); assert release.wait(2); return "late"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    def run():
        try: results.append(runner.invoke(InvocationRequest(**{**request(revision).__dict__, "invocation_id": "receipt_failure"}), Waiting(), publish=lambda _: (_ for _ in ()).throw(AssertionError("late result published"))))
        except ClosurePersistenceError as exc: errors.append(exc)
    worker = threading.Thread(target=run)
    worker.start(); assert entered.wait(2)
    with pytest.raises(ClosurePersistenceError): runner.cancel("receipt_failure")
    assert runner._active["receipt_failure"].state == "CLOSURE_FAILED"
    release.set(); worker.join(2)
    assert not worker.is_alive() and results == [] and len(errors) == 1


def test_hung_adapter_cancel_closes_indeterminate_with_bounded_timeout(rig):
    db, broker, revision = rig
    entered, release, never, results = threading.Event(), threading.Event(), threading.Event(), []
    class HungCancel(Adapter):
        def dispatch(self, engine, payload, cancellation):
            entered.set(); assert release.wait(2); return "late"
        def cancel(self):
            never.wait(); return "cancelled"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER, cancel_timeout=.01)
    worker = threading.Thread(target=lambda: results.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "hung_cancel"}), HungCancel())))
    worker.start(); assert entered.wait(2)
    assert runner.cancel("hung_cancel") == "unknown"
    release.set(); worker.join(2)
    assert not worker.is_alive() and results[0].outcome == "indeterminate"


def test_only_elected_performer_returns_after_durable_cancellation(rig):
    db, broker, revision = rig
    dispatch_ready, release_dispatch = threading.Event(), threading.Event()
    public_entered, release_public = threading.Event(), threading.Event()
    cancel_entered, release_cancel = threading.Event(), threading.Event()
    invocation, public_result = [], []

    class Interleaved(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatch_ready.set(); assert release_dispatch.wait(2); return "late"
        def cancel(self):
            cancel_entered.set(); assert release_cancel.wait(2); return "cancelled"

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    original_perform = runner._perform_cancel
    def delayed_public_perform(iid, active, principal):
        if threading.current_thread().name == "public-canceller":
            public_entered.set(); assert release_public.wait(2)
        return original_perform(iid, active, principal)
    runner._perform_cancel = delayed_public_perform
    invoke_thread = threading.Thread(target=lambda: invocation.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "one_performer"}), Interleaved())))
    invoke_thread.start(); assert dispatch_ready.wait(2)
    public_thread = threading.Thread(target=lambda: public_result.append(runner.cancel("one_performer")), name="public-canceller")
    public_thread.start(); assert public_entered.wait(2)
    release_public.set(); assert cancel_entered.wait(2)
    release_dispatch.set()
    operation = broker.store.operation_for_native("one_performer")
    assert operation and broker.store.receipt(operation["operation_id"]) is None
    release_public.set()
    assert public_thread.is_alive() and broker.store.receipt(operation["operation_id"]) is None
    release_cancel.set(); public_thread.join(2); invoke_thread.join(2)
    assert not public_thread.is_alive() and not invoke_thread.is_alive()
    assert public_result == ["cancelled"]
    assert broker.store.receipt(operation["operation_id"])["outcome"] == "cancelled"


def test_dispatch_failure_racing_acknowledged_cancel_has_one_winner(rig):
    db, broker, revision = rig
    dispatch_ready, fail_dispatch = threading.Event(), threading.Event()
    cancellation_acknowledged = threading.Event()
    invoke_result, cancel_result = [], []
    class Race(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatch_ready.set(); assert fail_dispatch.wait(2); raise RuntimeError("provider failed")
        def cancel(self):
            cancellation_acknowledged.set(); return "cancelled"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    invoke_thread = threading.Thread(target=lambda: invoke_result.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "terminal_winner"}), Race())))
    invoke_thread.start(); assert dispatch_ready.wait(2)
    cancel_thread = threading.Thread(target=lambda: cancel_result.append(runner.cancel("terminal_winner")))
    cancel_thread.start(); assert cancellation_acknowledged.wait(2)
    active = runner._active["terminal_winner"]
    fail_dispatch.set()
    assert invoke_thread.is_alive()
    cancel_thread.join(2); invoke_thread.join(2)
    receipt = broker.store.receipt(invoke_result[0].operation_id)
    assert not cancel_thread.is_alive() and not invoke_thread.is_alive()
    assert invoke_result[0].outcome == receipt["outcome"] == "cancelled"
    assert cancel_result == ["cancelled"] and active.state == "CANCELLED"


def test_timeout_receipt_is_durable_before_waiting_canceller_observes_unknown(rig):
    db, broker, revision = rig
    dispatch_ready, release_dispatch, never = threading.Event(), threading.Event(), threading.Event()
    receipt_entered, release_receipt = threading.Event(), threading.Event()
    first, second, invocation = [], [], []
    original_receipt = broker.receipt
    def gated_receipt(operation_id, outcome, result_ref, node):
        if outcome == "indeterminate":
            receipt_entered.set(); assert release_receipt.wait(2)
        return original_receipt(operation_id, outcome, result_ref, node)
    broker.receipt = gated_receipt
    class Hung(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatch_ready.set(); assert release_dispatch.wait(2); return "late"
        def cancel(self):
            never.wait(); return "cancelled"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER, cancel_timeout=.01)
    invoke_thread = threading.Thread(target=lambda: invocation.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "timeout_durable"}), Hung())))
    invoke_thread.start(); assert dispatch_ready.wait(2)
    first_thread = threading.Thread(target=lambda: first.append(runner.cancel("timeout_durable")))
    first_thread.start(); assert receipt_entered.wait(2)
    operation = broker.store.operation_for_native("timeout_durable")
    second_thread = threading.Thread(target=lambda: second.append(runner.cancel("timeout_durable")))
    second_thread.start()
    assert second_thread.is_alive() and broker.store.receipt(operation["operation_id"]) is None
    release_receipt.set(); first_thread.join(2); second_thread.join(2)
    release_dispatch.set(); invoke_thread.join(2)
    assert first == second == ["unknown"]
    assert broker.store.receipt(operation["operation_id"])["outcome"] == "indeterminate"


def test_failure_receipt_is_durable_before_concurrent_cancel_observes_terminal(rig):
    db, broker, revision = rig
    receipt_entered, release_receipt = threading.Event(), threading.Event()
    invoke_result, cancel_result = [], []
    original_receipt = broker.receipt
    def gated_receipt(operation_id, outcome, result_ref, node):
        if outcome == "failed":
            receipt_entered.set(); assert release_receipt.wait(2)
        return original_receipt(operation_id, outcome, result_ref, node)
    broker.receipt = gated_receipt
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    invoke_thread = threading.Thread(target=lambda: invoke_result.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "failure_durable"}), Adapter(error=RuntimeError()))))
    invoke_thread.start(); assert receipt_entered.wait(2)
    operation = broker.store.operation_for_native("failure_durable")
    cancel_thread = threading.Thread(target=lambda: cancel_result.append(runner.cancel("failure_durable")))
    cancel_thread.start()
    assert cancel_thread.is_alive() and broker.store.receipt(operation["operation_id"]) is None
    release_receipt.set(); invoke_thread.join(2); cancel_thread.join(2)
    assert invoke_result[0].outcome == "failed" and cancel_result == ["failed"]
    assert broker.store.receipt(operation["operation_id"])["outcome"] == "failed"


def test_cancel_after_terminal_invocation_is_too_late_without_pending_marker(rig):
    db, broker, revision = rig
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    result = runner.invoke(InvocationRequest(**{**request(revision).__dict__, "invocation_id": "already_done"}), Adapter())
    assert result.outcome == "succeeded"
    assert runner.cancel("already_done") == "completed"
    assert runner._pending_cancellations == {}


def test_failed_closure_retries_before_a_waiter_observes_durable_outcome(rig):
    db, broker, revision = rig
    third_attempt, release_receipt = threading.Event(), threading.Event()
    attempts, invoke_result, cancel_result = [], [], []
    original_receipt = broker.receipt
    def flaky_receipt(operation_id, outcome, result_ref, node):
        if outcome == "failed":
            attempts.append(outcome)
            if len(attempts) < 3: raise RuntimeError("transient receipt failure")
            third_attempt.set(); assert release_receipt.wait(2)
        return original_receipt(operation_id, outcome, result_ref, node)
    broker.receipt = flaky_receipt
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    invoke_thread = threading.Thread(target=lambda: invoke_result.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "retry_durable"}), Adapter(error=RuntimeError()))))
    invoke_thread.start(); assert third_attempt.wait(2)
    operation = broker.store.operation_for_native("retry_durable")
    cancel_thread = threading.Thread(target=lambda: cancel_result.append(runner.cancel("retry_durable")))
    cancel_thread.start()
    assert cancel_thread.is_alive() and broker.store.receipt(operation["operation_id"]) is None
    release_receipt.set(); invoke_thread.join(2); cancel_thread.join(2)
    assert attempts == ["failed", "failed", "failed"]
    assert invoke_result[0].outcome == "failed" and cancel_result == ["failed"]


def test_permanently_failed_closure_returns_same_error_to_waiter(rig):
    db, broker, revision = rig
    exhausted = threading.Event()
    attempts, invoke_errors = [], []
    original_receipt = broker.receipt
    def failing_receipt(operation_id, outcome, result_ref, node):
        if outcome == "failed":
            attempts.append(outcome)
            if len(attempts) == 3: exhausted.set()
            raise RuntimeError("persistent receipt failure")
        return original_receipt(operation_id, outcome, result_ref, node)
    broker.receipt = failing_receipt
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    def run():
        try: runner.invoke(InvocationRequest(**{**request(revision).__dict__, "invocation_id": "closure_error"}), Adapter(error=RuntimeError()))
        except ClosurePersistenceError as exc: invoke_errors.append(exc)
    invoke_thread = threading.Thread(target=run)
    invoke_thread.start(); assert exhausted.wait(2); invoke_thread.join(2)
    with pytest.raises(ClosurePersistenceError) as waiter_error: runner.cancel("closure_error")
    assert len(invoke_errors) == 1 and str(waiter_error.value) == str(invoke_errors[0])
    assert broker.store.receipt(broker.store.operation_for_native("closure_error")["operation_id"]) is None


def test_closure_failure_during_engine_build_never_dispatches_provider(rig):
    db, broker, revision = rig
    engine_started, release_engine = threading.Event(), threading.Event()
    dispatched, invoke_errors = [], []
    original_receipt = broker.receipt
    def failing_receipt(operation_id, outcome, result_ref, node):
        if outcome == "cancelled": raise RuntimeError("persistent cancellation receipt failure")
        return original_receipt(operation_id, outcome, result_ref, node)
    broker.receipt = failing_receipt
    def build_engine(value):
        engine_started.set(); assert release_engine.wait(2); return object()
    class NeverDispatch(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatched.append(True); return "impossible"
    runner = InferenceRunner(broker, db, engine_factory=build_engine, principal_provider=lambda: OWNER, receipt_attempts=1)
    def run():
        try: runner.invoke(InvocationRequest(**{**request(revision).__dict__, "invocation_id": "failed_during_engine"}), NeverDispatch())
        except ClosurePersistenceError as exc: invoke_errors.append(exc)
    invoke_thread = threading.Thread(target=run)
    invoke_thread.start(); assert engine_started.wait(2)
    with pytest.raises(ClosurePersistenceError) as cancel_error: runner.cancel("failed_during_engine")
    release_engine.set(); invoke_thread.join(2)
    assert dispatched == [] and len(invoke_errors) == 1
    assert str(invoke_errors[0]) == str(cancel_error.value)


def test_dispatch_admission_is_atomic_against_pre_dispatch_cancel(rig):
    db, broker, revision = rig
    engine_started, release_engine = threading.Event(), threading.Event()
    dispatched, cancel_calls, results = [], [], []
    def build_engine(value):
        engine_started.set(); assert release_engine.wait(2); return object()
    class Never(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatched.append(True); return "impossible"
        def cancel(self):
            cancel_calls.append(True); return "cancelled"
    runner = InferenceRunner(broker, db, engine_factory=build_engine, principal_provider=lambda: OWNER)
    worker = threading.Thread(target=lambda: results.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "atomic_pre_dispatch"}), Never())))
    worker.start(); assert engine_started.wait(2)
    assert runner.cancel("atomic_pre_dispatch") == "cancelled"
    release_engine.set(); worker.join(2)
    assert not worker.is_alive() and dispatched == [] and results[0].outcome == "cancelled" and cancel_calls == [True]
    children = [broker.store.operation(event["operation_id"]) for event in broker.events(0, {}, OWNER)["events"] if broker.store.operation(event["operation_id"])["name"] == "inference.cancel" and broker.store.operation(event["operation_id"])["parent_operation_id"] == results[0].operation_id]
    assert len({child["operation_id"] for child in children}) == 1 and children[0]["claimed_by"]
    assert broker.store.receipt(children[0]["operation_id"])["outcome"] == "succeeded"


def test_cancel_during_dispatch_is_cooperative_and_closes_after_return(rig):
    db, broker, revision = rig
    dispatch_started, release_dispatch, cancel_called = threading.Event(), threading.Event(), threading.Event()
    cancel_calls, invoke_result, cancel_result = [], [], []
    class Cooperative(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatch_started.set(); assert release_dispatch.wait(2); return "late"
        def cancel(self):
            cancel_calls.append(True); cancel_called.set(); return "cancelled"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    worker = threading.Thread(target=lambda: invoke_result.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "cooperative_dispatch"}), Cooperative())))
    worker.start(); assert dispatch_started.wait(2)
    canceller = threading.Thread(target=lambda: cancel_result.append(runner.cancel("cooperative_dispatch")))
    canceller.start(); assert cancel_called.wait(2)
    operation = broker.store.operation_for_native("cooperative_dispatch")
    assert canceller.is_alive() and broker.store.receipt(operation["operation_id"]) is None
    release_dispatch.set(); canceller.join(2); worker.join(2)
    assert cancel_result == ["cancelled"] and invoke_result[0].outcome == "cancelled"
    assert broker.store.receipt(operation["operation_id"])["outcome"] == "cancelled"
    children = [broker.store.operation(event["operation_id"]) for event in broker.events(0, {}, OWNER)["events"] if broker.store.operation(event["operation_id"])["name"] == "inference.cancel" and broker.store.operation(event["operation_id"])["parent_operation_id"] == operation["operation_id"]]
    assert len({child["operation_id"] for child in children}) == 1 and children[0]["claimed_by"]
    child_receipt = broker.store.receipt(children[0]["operation_id"])
    assert child_receipt["outcome"] == "succeeded" and child_receipt["result_ref"] == "invocation:cooperative_dispatch"
    assert cancel_calls == [True]


def test_dispatching_wedge_cannot_close_cancelled_before_provider_call(rig):
    db, broker, revision = rig
    at_boundary, release_boundary, adapter_called = threading.Event(), threading.Event(), []
    invoke_result, cancel_result = [], []
    class Provider(Adapter):
        def dispatch(self, engine, payload, cancellation):
            adapter_called.append(True); return "late"
        def cancel(self): return "cancelled"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    original_dispatch = runner._dispatch
    def gated_dispatch(*args):
        at_boundary.set(); assert release_boundary.wait(2); return original_dispatch(*args)
    runner._dispatch = gated_dispatch
    worker = threading.Thread(target=lambda: invoke_result.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "dispatch_wedge"}), Provider())))
    worker.start(); assert at_boundary.wait(2)
    operation = broker.store.operation_for_native("dispatch_wedge")
    canceller = threading.Thread(target=lambda: cancel_result.append(runner.cancel("dispatch_wedge")))
    canceller.start()
    assert canceller.is_alive() and adapter_called == [] and broker.store.receipt(operation["operation_id"]) is None
    release_boundary.set(); canceller.join(2); worker.join(2)
    assert cancel_result == ["cancelled"] and invoke_result[0].outcome == "cancelled"
    assert adapter_called == [True] and broker.store.receipt(operation["operation_id"])["outcome"] == "cancelled"


def test_dispatch_ack_receipt_retries_irreversibly_before_cancelled_closure(rig):
    db, broker, revision = rig
    dispatch_started, release_dispatch = threading.Event(), threading.Event()
    third_attempt = threading.Event()
    attempts, invoke_result, cancel_result, published = [], [], [], []
    original_receipt = broker.receipt
    outer = [""]
    def flaky_receipt(operation_id, outcome, result_ref, node):
        if operation_id != outer[0] and outcome == "succeeded":
            attempts.append(operation_id)
            if len(attempts) < 3: raise RuntimeError("transient cancel receipt failure")
            third_attempt.set()
        return original_receipt(operation_id, outcome, result_ref, node)
    broker.receipt = flaky_receipt
    class Provider(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatch_started.set(); assert release_dispatch.wait(2); return "late"
        def cancel(self): return "cancelled"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    worker = threading.Thread(target=lambda: invoke_result.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "dispatch_ack_retry"}), Provider(), publish=lambda value: published.append(value) or "answer:late")))
    worker.start(); assert dispatch_started.wait(2)
    outer[0] = broker.store.operation_for_native("dispatch_ack_retry")["operation_id"]
    canceller = threading.Thread(target=lambda: cancel_result.append(runner.cancel("dispatch_ack_retry")))
    canceller.start()
    assert third_attempt.wait(2)
    assert len(attempts) == 3 and runner._active["dispatch_ack_retry"].state == "DISPATCHING"
    release_dispatch.set(); canceller.join(2); worker.join(2)
    assert cancel_result == ["cancelled"] and invoke_result[0].outcome == "cancelled" and published == []


def test_dispatch_ack_persistent_receipt_failure_stays_irreversible(rig):
    db, broker, revision = rig
    dispatch_started, release_dispatch = threading.Event(), threading.Event()
    invoke_errors, published = [], []
    original_receipt = broker.receipt
    outer = [""]
    def failing_receipt(operation_id, outcome, result_ref, node):
        if operation_id != outer[0] and outcome == "succeeded": raise RuntimeError("persistent cancel receipt failure")
        return original_receipt(operation_id, outcome, result_ref, node)
    broker.receipt = failing_receipt
    class Provider(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatch_started.set(); assert release_dispatch.wait(2); return "late"
        def cancel(self): return "cancelled"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER, receipt_attempts=1)
    def run():
        try: runner.invoke(InvocationRequest(**{**request(revision).__dict__, "invocation_id": "dispatch_ack_failed"}), Provider(), publish=lambda value: published.append(value) or "answer:late")
        except ClosurePersistenceError as exc: invoke_errors.append(exc)
    worker = threading.Thread(target=run)
    worker.start(); assert dispatch_started.wait(2)
    outer[0] = broker.store.operation_for_native("dispatch_ack_failed")["operation_id"]
    with pytest.raises(ClosurePersistenceError): runner.cancel("dispatch_ack_failed")
    assert runner._active["dispatch_ack_failed"].state == "CLOSURE_FAILED"
    release_dispatch.set(); worker.join(2)
    assert len(invoke_errors) == 1 and published == []


def test_cancel_child_completed_is_refused_then_invocation_publishes(rig):
    db, broker, revision = rig
    engine_started, release_engine = threading.Event(), threading.Event()
    class Completed(Adapter):
        def cancel(self): return "completed"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: (engine_started.set(), release_engine.wait(2), object())[-1], principal_provider=lambda: OWNER)
    results = []
    worker = threading.Thread(target=lambda: results.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "completed_child"}), Completed())))
    worker.start(); assert engine_started.wait(2)
    assert runner.cancel("completed_child") == "completed"
    child = next(broker.store.operation(event["operation_id"]) for event in broker.events(0, {}, OWNER)["events"] if broker.store.operation(event["operation_id"])["name"] == "inference.cancel")
    receipt = broker.store.receipt(child["operation_id"])
    assert receipt["state"] == "refused" and receipt["result_ref"] == "cancel-disposition:completed"
    release_engine.set(); worker.join(2)
    assert results[0].outcome == "succeeded"


def test_cancel_child_adapter_error_is_failed_before_running_recovers(rig):
    db, broker, revision = rig
    entered, release, results = threading.Event(), threading.Event(), []
    class Broken(Adapter):
        def dispatch(self, engine, payload, cancellation):
            entered.set(); assert release.wait(2); return "normal"
        def cancel(self): raise RuntimeError("provider cancel failed")
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    worker = threading.Thread(target=lambda: results.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "failed_child"}), Broken())))
    worker.start(); assert entered.wait(2)
    assert runner.cancel("failed_child") == "refused"
    child = next(broker.store.operation(event["operation_id"]) for event in broker.events(0, {}, OWNER)["events"] if broker.store.operation(event["operation_id"])["name"] == "inference.cancel")
    assert broker.store.receipt(child["operation_id"])["outcome"] == "failed"
    release.set(); worker.join(2)
    assert results[0].outcome == "succeeded"


def test_base_exception_cancel_error_closes_child_then_reraises(rig):
    db, broker, revision = rig
    entered, release, results = threading.Event(), threading.Event(), []
    class AdapterAbort(BaseException): pass
    class Aborting(Adapter):
        def dispatch(self, engine, payload, cancellation):
            entered.set(); assert release.wait(2); return "normal"
        def cancel(self): raise AdapterAbort("abort")
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    worker = threading.Thread(target=lambda: results.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "base_exception_child"}), Aborting())))
    worker.start(); assert entered.wait(2)
    with pytest.raises(AdapterAbort): runner.cancel("base_exception_child")
    child = next(broker.store.operation(event["operation_id"]) for event in broker.events(0, {}, OWNER)["events"] if broker.store.operation(event["operation_id"])["name"] == "inference.cancel")
    assert broker.store.receipt(child["operation_id"])["outcome"] == "failed"
    assert runner._active["base_exception_child"].state == "RUNNING"
    release.set(); worker.join(2)
    assert results[0].outcome == "succeeded"


def test_unknown_and_timeout_cancel_children_are_indeterminate(rig):
    db, broker, revision = rig
    entered, release, results = threading.Event(), threading.Event(), []
    class Unknown(Adapter):
        def dispatch(self, engine, payload, cancellation):
            entered.set(); assert release.wait(2); return "late"
        def cancel(self): return "unknown"
    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    worker = threading.Thread(target=lambda: results.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": "unknown_child"}), Unknown())))
    worker.start(); assert entered.wait(2)
    assert runner.cancel("unknown_child") == "unknown"
    child = next(broker.store.operation(event["operation_id"]) for event in broker.events(0, {}, OWNER)["events"] if broker.store.operation(event["operation_id"])["name"] == "inference.cancel")
    assert broker.store.receipt(child["operation_id"])["outcome"] == "indeterminate"
    release.set(); worker.join(2)
    assert results[0].outcome == "indeterminate"


def _cancel_children(broker, parent_operation_id):
    children = {}
    for event in broker.events(0, {}, OWNER)["events"]:
        operation = broker.store.operation(event["operation_id"])
        if operation["name"] == "inference.cancel" and operation["parent_operation_id"] == parent_operation_id:
            children[operation["operation_id"]] = operation
    return list(children.values())


@pytest.mark.parametrize(
    ("disposition", "child_outcome", "cancel_return"),
    [("completed", "refused", "completed"), ("failed", "failed", "refused"), ("unknown", "indeterminate", "unknown")],
)
def test_each_cancel_child_disposition_waits_for_its_own_durable_receipt(
    rig, disposition, child_outcome, cancel_return
):
    db, broker, revision = rig
    dispatch_started, release_dispatch = threading.Event(), threading.Event()
    child_receipt_entered, release_child_receipt = threading.Event(), threading.Event()
    cancel_calls, cancel_result, invocation = [], [], []
    original_receipt = broker.receipt

    def gated_receipt(operation_id, outcome, result_ref, node):
        operation = broker.store.operation(operation_id)
        if operation["name"] == "inference.cancel" and outcome == child_outcome:
            child_receipt_entered.set()
            assert release_child_receipt.wait(2)
        return original_receipt(operation_id, outcome, result_ref, node)

    broker.receipt = gated_receipt

    class Controlled(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatch_started.set()
            assert release_dispatch.wait(2)
            return "normal"

        def cancel(self):
            cancel_calls.append(True)
            if disposition == "failed":
                raise RuntimeError("cancel failed")
            return disposition

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    worker = threading.Thread(target=lambda: invocation.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": f"durable_child_{disposition}"}), Controlled()
    )))
    worker.start()
    assert dispatch_started.wait(2)
    canceller = threading.Thread(target=lambda: cancel_result.append(runner.cancel(f"durable_child_{disposition}")))
    canceller.start()
    assert child_receipt_entered.wait(2)
    operation = broker.store.operation_for_native(f"durable_child_{disposition}")
    children = _cancel_children(broker, operation["operation_id"])
    assert canceller.is_alive() and len(children) == 1 and children[0]["claimed_by"]
    assert broker.store.receipt(children[0]["operation_id"]) is None
    release_child_receipt.set()
    canceller.join(2)
    assert cancel_result == [cancel_return] and cancel_calls == [True]
    release_dispatch.set()
    worker.join(2)
    assert not worker.is_alive()
    assert broker.store.receipt(children[0]["operation_id"])["outcome"] == child_outcome


@pytest.mark.parametrize(
    ("disposition", "child_outcome", "public_result"),
    [("failed", "failed", "refused"), ("unknown", "indeterminate", "unknown")],
)
def test_cancel_child_receipt_transient_retries_once_adapter_call_and_shared_disposition(
    rig, disposition, child_outcome, public_result
):
    db, broker, revision = rig
    dispatch_started, release_dispatch = threading.Event(), threading.Event()
    third_attempt, release_third_attempt = threading.Event(), threading.Event()
    attempts, cancel_calls, first, second, invocation = [], [], [], [], []
    original_receipt = broker.receipt

    def flaky_receipt(operation_id, outcome, result_ref, node):
        operation = broker.store.operation(operation_id)
        if operation["name"] == "inference.cancel" and outcome == child_outcome:
            attempts.append(operation_id)
            if len(attempts) < 3:
                raise RuntimeError("transient child receipt failure")
            third_attempt.set()
            assert release_third_attempt.wait(2)
        return original_receipt(operation_id, outcome, result_ref, node)

    broker.receipt = flaky_receipt

    class Controlled(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatch_started.set()
            assert release_dispatch.wait(2)
            return "late"

        def cancel(self):
            cancel_calls.append(True)
            if disposition == "failed":
                raise RuntimeError("cancel failed")
            return disposition

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    invocation_id = f"transient_child_{disposition}"
    worker = threading.Thread(target=lambda: invocation.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": invocation_id}), Controlled()
    )))
    worker.start()
    assert dispatch_started.wait(2)
    first_thread = threading.Thread(target=lambda: first.append(runner.cancel(invocation_id)))
    first_thread.start()
    assert third_attempt.wait(2)
    second_thread = threading.Thread(target=lambda: second.append(runner.cancel(invocation_id)))
    second_thread.start()
    assert first_thread.is_alive() and second_thread.is_alive() and len(attempts) == 3
    release_third_attempt.set()
    first_thread.join(2)
    second_thread.join(2)
    assert attempts and len(set(attempts)) == 1 and len(attempts) == 3 and cancel_calls == [True]
    assert first == second == [public_result]
    release_dispatch.set()
    worker.join(2)
    assert not worker.is_alive()


@pytest.mark.parametrize(
    ("disposition", "child_outcome"), [("failed", "failed"), ("unknown", "indeterminate")],
)
def test_cancel_child_receipt_exhaustion_retains_one_error_for_all_cancellers(
    rig, disposition, child_outcome
):
    db, broker, revision = rig
    dispatch_started, release_dispatch = threading.Event(), threading.Event()
    exhausted = threading.Event()
    attempts, cancel_calls, errors, invocation_errors = [], [], [], []
    original_receipt = broker.receipt

    def failing_receipt(operation_id, outcome, result_ref, node):
        operation = broker.store.operation(operation_id)
        if operation["name"] == "inference.cancel" and outcome == child_outcome:
            attempts.append(operation_id)
            if len(attempts) == 3:
                exhausted.set()
            raise RuntimeError("persistent child receipt failure")
        return original_receipt(operation_id, outcome, result_ref, node)

    broker.receipt = failing_receipt

    class Controlled(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatch_started.set()
            assert release_dispatch.wait(2)
            return "late"

        def cancel(self):
            cancel_calls.append(True)
            if disposition == "failed":
                raise RuntimeError("cancel failed")
            return disposition

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    invocation_id = f"exhausted_child_{disposition}"
    def invoke():
        try:
            runner.invoke(InvocationRequest(**{**request(revision).__dict__, "invocation_id": invocation_id}), Controlled())
        except ClosurePersistenceError as exc:
            invocation_errors.append(exc)
    worker = threading.Thread(target=invoke)
    worker.start()
    assert dispatch_started.wait(2)
    def cancel():
        try:
            runner.cancel(invocation_id)
        except ClosurePersistenceError as exc:
            errors.append(exc)
    first = threading.Thread(target=cancel)
    second = threading.Thread(target=cancel)
    first.start()
    assert exhausted.wait(2)
    second.start()
    first.join(2)
    second.join(2)
    operation = broker.store.operation_for_native(invocation_id)
    children = _cancel_children(broker, operation["operation_id"])
    assert len(attempts) == 3 and len(set(attempts)) == 1 and cancel_calls == [True]
    assert len(errors) == 2 and str(errors[0]) == str(errors[1])
    assert len(children) == 1 and broker.store.receipt(children[0]["operation_id"]) is None
    release_dispatch.set()
    worker.join(2)
    assert len(invocation_errors) == 1 and str(invocation_errors[0]) == str(errors[0])


def test_completed_dispatch_cancel_has_refused_child_one_receipt_and_publication(rig):
    db, broker, revision = rig
    dispatch_started, release_dispatch = threading.Event(), threading.Event()
    published, cancel_calls, invocation, cancellation = [], [], [], []

    class Completed(Adapter):
        def dispatch(self, engine, payload, cancellation_event):
            dispatch_started.set()
            assert release_dispatch.wait(2)
            return "published result"

        def cancel(self):
            cancel_calls.append(True)
            return "completed"

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    invocation_id = "completed_dispatch_detail"
    worker = threading.Thread(target=lambda: invocation.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": invocation_id}),
        Completed(), publish=lambda value: published.append(value) or "answer:completed",
    )))
    worker.start()
    assert dispatch_started.wait(2)
    canceller = threading.Thread(target=lambda: cancellation.append(runner.cancel(invocation_id)))
    canceller.start()
    release_dispatch.set()
    canceller.join(2)
    worker.join(2)
    operation = broker.store.operation_for_native(invocation_id)
    children = _cancel_children(broker, operation["operation_id"])
    assert cancellation == ["completed"] and cancel_calls == [True] and published == ["published result"]
    assert invocation[0].outcome == "succeeded" and broker.store.receipt(operation["operation_id"])["outcome"] == "succeeded"
    assert len(children) == 1 and broker.store.receipt(children[0]["operation_id"])["outcome"] == "refused"
    assert broker.store.receipt(children[0]["operation_id"])["result_ref"] == "cancel-disposition:completed"


def test_unknown_child_is_terminal_before_late_dispatch_release_and_never_publishes(rig):
    db, broker, revision = rig
    dispatch_started, release_dispatch = threading.Event(), threading.Event()
    published, invocation = [], []

    class Unknown(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatch_started.set()
            assert release_dispatch.wait(2)
            return "late"

        def cancel(self):
            return "unknown"

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    invocation_id = "unknown_late_release"
    worker = threading.Thread(target=lambda: invocation.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": invocation_id}),
        Unknown(), publish=lambda value: published.append(value) or "answer:late",
    )))
    worker.start()
    assert dispatch_started.wait(2)
    assert runner.cancel(invocation_id) == "unknown"
    operation = broker.store.operation_for_native(invocation_id)
    children = _cancel_children(broker, operation["operation_id"])
    assert len(children) == 1 and children[0]["claimed_by"]
    assert broker.store.receipt(children[0]["operation_id"])["outcome"] == "indeterminate"
    release_dispatch.set()
    worker.join(2)
    assert invocation[0].outcome == "indeterminate" and published == []


def test_timeout_late_cancel_daemon_cannot_mutate_durable_closure_or_publish(rig):
    db, broker, revision = rig
    dispatch_started, release_dispatch, release_cancel = threading.Event(), threading.Event(), threading.Event()
    published, invocation = [], []

    class HungCancel(Adapter):
        def dispatch(self, engine, payload, cancellation):
            dispatch_started.set()
            assert release_dispatch.wait(2)
            return "late"

        def cancel(self):
            assert release_cancel.wait(2)
            return "cancelled"

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER, cancel_timeout=.01)
    invocation_id = "timeout_late_daemon"
    worker = threading.Thread(target=lambda: invocation.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": invocation_id}),
        HungCancel(), publish=lambda value: published.append(value) or "answer:late",
    )))
    worker.start()
    assert dispatch_started.wait(2)
    assert runner.cancel(invocation_id) == "unknown"
    operation = broker.store.operation_for_native(invocation_id)
    children = _cancel_children(broker, operation["operation_id"])
    child_receipt = broker.store.receipt(children[0]["operation_id"])
    invocation_receipt = broker.store.receipt(operation["operation_id"])
    assert child_receipt["outcome"] == invocation_receipt["outcome"] == "indeterminate"
    release_cancel.set()
    release_dispatch.set()
    worker.join(2)
    assert invocation[0].outcome == "indeterminate" and published == []
    assert broker.store.receipt(children[0]["operation_id"]) == child_receipt
    assert broker.store.receipt(operation["operation_id"]) == invocation_receipt


def test_dispatch_cancel_child_can_close_before_independently_gated_invocation_receipt(rig):
    db, broker, revision = rig
    dispatch_started, release_dispatch = threading.Event(), threading.Event()
    invocation_receipt_entered, release_invocation_receipt = threading.Event(), threading.Event()
    child_terminal, cancellation, invocation = threading.Event(), [], []
    original_receipt = broker.receipt

    def gated_receipt(operation_id, outcome, result_ref, node):
        operation = broker.store.operation(operation_id)
        if operation["name"] == "inference.invoke" and outcome == "cancelled":
            invocation_receipt_entered.set()
            assert release_invocation_receipt.wait(2)
        receipt = original_receipt(operation_id, outcome, result_ref, node)
        if operation["name"] == "inference.cancel" and outcome == "succeeded":
            child_terminal.set()
        return receipt

    broker.receipt = gated_receipt

    class Cooperative(Adapter):
        def dispatch(self, engine, payload, cancellation_event):
            dispatch_started.set()
            assert release_dispatch.wait(2)
            return "late"

        def cancel(self):
            return "cancelled"

    runner = InferenceRunner(broker, db, engine_factory=lambda _: object(), principal_provider=lambda: OWNER)
    invocation_id = "independent_receipt_gates"
    worker = threading.Thread(target=lambda: invocation.append(runner.invoke(
        InvocationRequest(**{**request(revision).__dict__, "invocation_id": invocation_id}), Cooperative()
    )))
    worker.start()
    assert dispatch_started.wait(2)
    canceller = threading.Thread(target=lambda: cancellation.append(runner.cancel(invocation_id)))
    canceller.start()
    operation = broker.store.operation_for_native(invocation_id)
    # The child gate is independent: it is terminal before dispatch releases.
    assert child_terminal.wait(2)
    child = _cancel_children(broker, operation["operation_id"])[0]
    assert broker.store.receipt(child["operation_id"])["outcome"] == "succeeded"
    assert broker.store.receipt(operation["operation_id"]) is None
    release_dispatch.set()
    assert invocation_receipt_entered.wait(2)
    assert canceller.is_alive() and broker.store.receipt(operation["operation_id"]) is None
    release_invocation_receipt.set()
    canceller.join(2)
    worker.join(2)
    assert cancellation == ["cancelled"] and invocation[0].outcome == "cancelled"
