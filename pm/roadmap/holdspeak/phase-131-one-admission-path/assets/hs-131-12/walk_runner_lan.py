"""HS-131-12 runner leg against the current admitted adapter boundary.

The historical HS-131-02 walk predates runner-issued DispatchContext enforcement.
This leg proves the final boundary instead: the runner claims the child, mints the
context, and only then constructs the engine from the frozen revision.
"""
from __future__ import annotations

import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

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
        profile_id="lan43",
        name="LAN .43",
        kind="openAICompatible",
        base_url=LAN_URL,
        model=LAN_MODEL,
        requires_key=False,
    )
    revision = capture_deployment_revision(db, resolve_inference_target(db, "lan43"))

    # The editable profile drifts after capture. A successful physical call can now
    # only have used the immutable revision because the live profile points nowhere.
    db.profiles.upsert(
        profile_id="lan43",
        name="LAN .43 (mutated)",
        kind="openAICompatible",
        base_url="http://127.0.0.1:9/v1",
        model="wrong-model",
        requires_key=False,
    )

    built: list[tuple[str, str, str]] = []

    def engine_factory(frozen, *, warrant=None, context=None):
        engine = build_intel_for_revision(
            frozen,
            warrant=warrant,
            context=context,
        )
        built.append(
            (
                frozen.id,
                str(getattr(engine, "cloud_base_url", "") or ""),
                str(getattr(engine, "cloud_model", "") or ""),
            )
        )
        return engine

    broker = _configure(db)
    owner = Principal(PrincipalKind.OWNER, "walk-owner")
    runner = InferenceRunner(
        broker,
        db,
        engine_factory=engine_factory,
        principal_provider=lambda: owner,
    )

    class Lan:
        egress_destination = "192.168.1.43"
        connector_id = "walk-lan-provider"
        egress_data_classes = ("instruction",)

        def dispatch(self, engine, _payload, _cancellation):
            return engine.run_prompt(user_prompt="", max_tokens=48)

        def cancel(self):
            return "cancelled"

    payload = {"probe": "revision"}
    request = InvocationRequest(
        deployment_revision=revision.id,
        definition_origin=ServiceContract.for_payload("walk", "v1", payload),
        deadline_at=time.time() + 120,
        payload=payload,
    )
    outcome = runner.invoke(request, Lan(), publish=lambda _text: "walk-result:revision")
    assert outcome.outcome == "succeeded", outcome
    assert built == [(revision.id, LAN_URL, LAN_MODEL)], built
    operation = broker.store.operation(outcome.operation_id)
    receipt = broker.store.receipt(outcome.operation_id)
    assert operation["state"] == "succeeded"
    assert operation["target_ref"] == f"deployment-revision:{revision.id}"
    assert receipt["outcome"] == "succeeded"
    events = broker.events(0, {}, owner)["events"]
    operations = [
        broker.store.operation(operation_id)
        for operation_id in {
            event["operation_id"]
            for event in events
            if event.get("operation_id")
        }
    ]
    egress_children = [
        child
        for child in operations
        if child
        and child["name"] == "external.egress"
        and child["parent_operation_id"] == outcome.operation_id
    ]
    assert len(egress_children) == 1
    egress_receipt = broker.store.receipt(egress_children[0]["operation_id"])
    assert egress_receipt["outcome"] == "succeeded"

    # The physical request may finish after cancellation, but the publication fence
    # must reject that late result and close the one invocation exactly once.
    started = threading.Event()

    class LanSlow(Lan):
        def dispatch(self, engine, _payload, _cancellation):
            started.set()
            return engine.run_prompt(user_prompt="", max_tokens=1024)

    published: list[str] = []
    slow_payload = {"probe": "cancellation"}
    slow = InvocationRequest(
        deployment_revision=revision.id,
        definition_origin=ServiceContract.for_payload("walk", "v1", slow_payload),
        deadline_at=time.time() + 300,
        payload=slow_payload,
        invocation_id="walk_cancel_leg",
    )
    results = []
    thread = threading.Thread(
        target=lambda: results.append(
            runner.invoke(
                slow,
                LanSlow(),
                publish=lambda _text: published.append("called") or "walk-result:late",
            )
        )
    )
    thread.start()
    assert started.wait(10), "dispatch never started"
    assert runner.cancel("walk_cancel_leg") == "cancelled"
    thread.join(120)
    assert not thread.is_alive(), "invoke did not return"
    assert results and results[0].outcome == "cancelled", results
    assert not published, "late model output must never publish"
    invocation_receipt = broker.store.receipt(results[0].operation_id)
    assert invocation_receipt["outcome"] == "cancelled"
    cancel_ops = [
        broker.store.operation(operation_id)
        for operation_id in {
            event["operation_id"]
            for event in broker.events(0, {}, owner)["events"]
            if event.get("operation_id")
        }
    ]
    cancel_ops = [
        child
        for child in cancel_ops
        if child
        and child["name"] == "inference.cancel"
        and child["parent_operation_id"] == results[0].operation_id
    ]
    assert len(cancel_ops) == 1
    assert cancel_ops[0]["state"] == "succeeded"

    print(
        "WALK OK: runner-issued context built the frozen revision; one physical "
        "attempt received one receipt and one egress child; cancellation fenced "
        "late publication."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(tempfile.mkdtemp(prefix="hs13112-runner-"))))
