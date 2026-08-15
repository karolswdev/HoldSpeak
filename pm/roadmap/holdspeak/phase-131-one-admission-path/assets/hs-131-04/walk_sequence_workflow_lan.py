"""HS-131-04 real-LAN walk: Sequence and Workflow through the admitted door.

Against the live llama.cpp endpoint at 192.168.1.43:8080, through the REAL
service layer (not the runner directly), proves:
  1. A two-step Sequence -> one sequence.run parent + exactly two admitted
     inference.invoke children with succeeded receipts, threaded output, and
     one receipt-gated finalized result.
  2. A synced-format Workflow graph (llm -> keep_if) -> one workflow.run
     parent + one child for the model node, none for the pure node.
  3. A mid-run parent cancellation -> no further children admitted, the
     already-earned child receipts survive, the parent closes cancelled.

Run with an isolated HOME. Exits non-zero on any failed assertion.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.sequence_workflow_service import SequenceWorkflowService

LAN_URL = "http://192.168.1.43:8080/v1"
LAN_MODEL = "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf"


def _ops(broker, owner):
    seen: dict[str, dict] = {}
    for e in broker.events(0, {}, owner)["events"]:
        op = broker.store.operation(e["operation_id"])
        if op:
            seen[op["operation_id"]] = op
    return list(seen.values())


def _named(ops, name):
    return [o for o in ops if o and o["name"] == name]


async def main(workdir: Path) -> int:
    db = Database(workdir / "walk-seq.db")
    db.profiles.upsert(
        profile_id="lan43", name="LAN .43", kind="openAICompatible",
        base_url=LAN_URL, model=LAN_MODEL, requires_key=False,
    )
    broker = _configure(db)
    owner = Principal(PrincipalKind.OWNER, "walk-owner")
    service = SequenceWorkflowService(db, broker=broker)

    # Leg 1: a two-step Sequence through the admitted door.
    db.recipes.upsert(
        recipe_id="walk-a1", name="Walk A1", role="assistant",
        system_prompt="Answer in five words or fewer.",
        user_template="Name one color in: {input}", profile_id="lan43",
    )
    db.recipes.upsert(
        recipe_id="walk-a2", name="Walk A2", role="assistant",
        system_prompt="Answer in five words or fewer.",
        user_template="Shout this in uppercase: {input}", profile_id="lan43",
    )
    db.chains.upsert(chain_id="walk-chain", name="Walk Chain",
                     steps=["walk-a1", "walk-a2"])
    run = await service.run_sequence(
        owner, "walk-chain", {"input": "a red apple", "inference_target_id": "lan43",
                              "max_tokens": 32},
    )
    ops = _ops(broker, owner)
    parents = _named(ops, "sequence.run")
    children = _named(ops, "inference.invoke")
    assert len(parents) == 1, f"one sequence.run parent, got {len(parents)}"
    assert len(children) == 2, f"two admitted children, got {len(children)}"
    linked = [c for c in children if c.get("parent_operation_id") == parents[0]["operation_id"]]
    assert len(linked) == 2, "both children cite the parent causation ID"
    for c in children:
        receipt = broker.store.receipt(c["operation_id"])
        assert receipt and receipt["outcome"] == "succeeded", receipt
    parent_receipt = broker.store.receipt(parents[0]["operation_id"])
    assert parent_receipt and parent_receipt["outcome"] == "succeeded", parent_receipt
    assert run["steps"][1]["output"], "threaded final output present"
    print(f"leg1 parent={parents[0]['operation_id']} children=2 receipts=succeeded "
          f"output={run['output']!r}")

    # Leg 2: a Workflow graph (llm -> keep_if) — child for the model node only.
    fixtures = Path(__file__).resolve().parents[6] / "pm" / "roadmap" / \
        "holdspeak-mobile" / "contracts" / "fixtures"
    import json as _json
    graph = _json.loads((fixtures / "blueprint-linear-sample.json").read_text("utf-8"))
    db.workflows.upsert(workflow_id="walk-wf", name="Walk WF",
                        prompt="fallback: {input}", graph_json=graph)
    before = len(_named(_ops(broker, owner), "inference.invoke"))
    wf = await service.run_workflow(
        owner, "walk-wf", {"input": "the standup notes", "inference_target_id": "lan43",
                           "max_tokens": 48},
    )
    ops2 = _ops(broker, owner)
    wf_parents = _named(ops2, "workflow.run")
    added = len(_named(ops2, "inference.invoke")) - before
    model_steps = [s for s in wf["steps"] if s.get("provider")]
    pure_steps = [s for s in wf["steps"] if not s.get("provider")]
    assert len(wf_parents) == 1, f"one workflow.run parent, got {len(wf_parents)}"
    assert added == len(model_steps), \
        f"children ({added}) must equal model dispatches ({len(model_steps)})"
    assert pure_steps, "the graph's pure node ran without minting a child"
    print(f"leg2 parent={wf_parents[0]['operation_id']} model_children={added} "
          f"pure_nodes={len(pure_steps)} kinds={[s['kind'] for s in wf['steps']]}")

    # Leg 3: cancel mid-run — start a fresh sequence, cancel the parent while
    # its first child is with the provider.
    db.chains.upsert(chain_id="walk-cancel", name="Walk Cancel",
                     steps=["walk-a1", "walk-a2"])
    task = asyncio.create_task(service.run_sequence(
        owner, "walk-cancel",
        {"input": "write a long story about mountains", "inference_target_id": "lan43",
         "max_tokens": 512},
    ))
    parent_row = None
    for _ in range(200):
        await asyncio.sleep(0.05)
        with db._connection() as conn:
            rows = conn.execute(
                "SELECT p.*, o.principal_kind, o.principal_identity "
                "FROM kernel_parent_runs p "
                "JOIN kernel_operations o ON o.operation_id = p.operation_id "
                "WHERE p.definition_ref = ? AND p.state = 'OPEN'",
                ("sequence:walk-cancel",),
            ).fetchall()
        if rows and rows[0]["active_child_invocation_id"]:
            parent_row = dict(rows[0])
            break
    assert parent_row is not None, "the cancel-leg parent never opened with an active child"
    disposition = broker.parent_run_controller.cancel_by_operation_id(
        owner, parent_row["operation_id"],
    )
    try:
        await task
        raise AssertionError("cancelled sequence must not return success")
    except AssertionError:
        raise
    except Exception as exc:
        print(f"leg3 run surfaced {type(exc).__name__} after cancel (honest)")
    ops3 = _ops(broker, owner)
    cancel_children = [
        o for o in _named(ops3, "inference.invoke")
        if o.get("parent_operation_id") == parent_row["operation_id"]
    ]
    assert len(cancel_children) <= 1, \
        f"no child admitted after parent cancel, got {len(cancel_children)}"
    for c in cancel_children:
        receipt = broker.store.receipt(c["operation_id"])
        assert receipt is not None, "the active child keeps its terminal receipt"
        print(f"leg3 child={c['operation_id']} receipt={receipt['outcome']}")
    with db._connection() as conn:
        state = conn.execute(
            "SELECT state FROM kernel_parent_runs WHERE operation_id = ?",
            (parent_row["operation_id"],),
        ).fetchone()["state"]
    assert state not in ("OPEN", "CANCELLING"), f"parent must be terminal, got {state}"
    print(f"leg3 disposition={disposition} parent_state={state}")

    print("WALK OK: Sequence and Workflow dispatch admitted parent+children with "
          "receipts; pure nodes mint no children; mid-run cancel fences admission "
          "while receipts survive.")
    return 0


if __name__ == "__main__":
    import tempfile

    sys.exit(asyncio.run(main(Path(tempfile.mkdtemp(prefix="hs13104-walk-")))))
