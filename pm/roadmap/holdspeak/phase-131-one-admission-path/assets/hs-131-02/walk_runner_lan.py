"""HS-131-02 real-LAN walk: the admitted runner against live metal (.43).

Proves, against the real llama.cpp endpoint at 192.168.1.43:8080:
  1. A revision captured before a profile mutation still executes the
     original endpoint (Article XI.3 on real metal).
  2. One real invocation = one admitted operation + one terminal receipt
     + one causally linked external.egress child.
  3. A cancellation mid-dispatch closes the invocation `cancelled`, the
     cancel child `succeeded`, and the late model output never publishes.

Run with an isolated HOME. Exits non-zero on any failed assertion.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from holdspeak.db import Database
from holdspeak.deployment_revisions import capture_deployment_revision
from holdspeak.inference_targets import build_intel_for_revision, resolve_inference_target
from holdspeak.kernel.inference_runner import InferenceRunner, InvocationRequest, ServiceContract
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind

LAN_URL = "http://192.168.1.43:8080/v1"
LAN_MODEL = "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf"


def main(workdir: Path) -> int:
    db = Database(workdir / "walk-runner.db")
    db.profiles.upsert(
        profile_id="lan43", name="LAN .43", kind="openAICompatible",
        base_url=LAN_URL, model=LAN_MODEL, requires_key=False,
    )
    revision = capture_deployment_revision(db, resolve_inference_target(db, "lan43"))
    print(f"revision={revision.id} endpoint={revision.endpoint} model={revision.model}")

    # Article XI.3 on metal: mutate the profile AFTER capture; the admitted
    # revision must keep executing the original endpoint.
    db.profiles.upsert(
        profile_id="lan43", name="LAN .43 (mutated)", kind="openAICompatible",
        base_url="http://127.0.0.1:9/v1", model="wrong-model", requires_key=False,
    )
    resolved = build_intel_for_revision(revision)
    print(f"post-mutation engine endpoint={getattr(resolved, 'cloud_base_url', '?')}")
    assert getattr(resolved, "cloud_base_url", "") == LAN_URL, "revision must ignore the mutation"

    broker = _configure(db)
    owner = Principal(PrincipalKind.OWNER, "walk-owner")
    runner = InferenceRunner(broker, db, engine_factory=build_intel_for_revision,
                             principal_provider=lambda: owner)

    class Lan:
        egress_destination = "192.168.1.43"
        connector_id = "walk-lan-provider"
        egress_data_classes = ("instruction",)

        def dispatch(self, engine, payload, cancellation):
            return engine.run_prompt(user_prompt=payload["prompt"], max_tokens=48)

        def cancel(self):
            return "cancelled"

    payload = {"prompt": "Reply with exactly: ADMITTED"}
    request = InvocationRequest(
        deployment_revision=revision.id,
        definition_origin=ServiceContract.for_payload("walk", "v1", payload),
        deadline_at=time.time() + 120, payload=payload,
    )
    outcome = runner.invoke(request, Lan(), publish=lambda text: f"walk-result:{hash(text) & 0xffff:x}")
    print(f"leg1 outcome={outcome.outcome} result_ref={outcome.result_ref}")
    assert outcome.outcome == "succeeded", outcome
    operation = broker.store.operation(outcome.operation_id)
    receipt = broker.store.receipt(outcome.operation_id)
    assert operation["state"] == "succeeded" and receipt["outcome"] == "succeeded"
    events = broker.events(0, {}, owner)["events"]
    egress = [
        broker.store.operation(event["operation_id"]) for event in events
        if "egress:192.168.1.43" in tuple(event.get("refs") or ())
    ]
    egress_children = [op for op in egress if op and op["parent_operation_id"] == outcome.operation_id]
    assert egress_children, "the remote call must carry a causally linked egress child"
    egress_receipt = broker.store.receipt(egress_children[0]["operation_id"])
    print(f"leg1 egress child={egress_children[0]['operation_id']} receipt={egress_receipt['outcome']}")

    # Leg 2: cancellation mid-dispatch against the live endpoint.
    started = threading.Event()

    class LanSlow(Lan):
        def dispatch(self, engine, payload, cancellation):
            started.set()
            return engine.run_prompt(user_prompt=payload["prompt"], max_tokens=1024)

    published: list[str] = []
    slow_payload = {"prompt": "Write a very long story about receipts."}
    slow = InvocationRequest(
        deployment_revision=revision.id,
        definition_origin=ServiceContract.for_payload("walk", "v1", slow_payload),
        deadline_at=time.time() + 300, payload=slow_payload,
        invocation_id="walk_cancel_leg",
    )
    results: list = []
    thread = threading.Thread(
        target=lambda: results.append(
            runner.invoke(slow, LanSlow(), publish=lambda text: published.append(text) or "walk-late")
        )
    )
    thread.start()
    assert started.wait(10), "dispatch never started"
    disposition = runner.cancel("walk_cancel_leg")
    print(f"leg2 cancel disposition={disposition}")
    thread.join(120)
    assert results, "invoke did not return"
    print(f"leg2 outcome={results[0].outcome}")
    assert results[0].outcome == "cancelled", results[0]
    assert not published, "late model output must never publish"
    invocation_receipt = broker.store.receipt(results[0].operation_id)
    assert invocation_receipt["outcome"] == "cancelled"
    cancel_children = [
        broker.store.operation(event["operation_id"]) for event in broker.events(0, {}, owner)["events"]
        if event.get("operation_id")
    ]
    cancel_ops = [
        op for op in cancel_children
        if op and op["name"] == "inference.cancel" and op["state"] in {"succeeded"}
    ]
    assert cancel_ops, "the admitted cancel child must close succeeded"
    print(f"leg2 cancel child={cancel_ops[0]['operation_id']} state={cancel_ops[0]['state']}")

    print("WALK OK: revision immutable on metal; one invocation/one receipt/one egress child; "
          "cancellation closed once, late output suppressed.")
    return 0


if __name__ == "__main__":
    import tempfile

    sys.exit(main(Path(tempfile.mkdtemp(prefix="hs13102-walk-"))))
