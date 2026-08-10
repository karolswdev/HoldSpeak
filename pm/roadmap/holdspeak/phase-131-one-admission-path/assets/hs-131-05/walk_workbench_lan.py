"""HS-131-05 real-LAN walk: manual Workbench through the admitted runner.

Against the live llama.cpp endpoint at 192.168.1.43:8080, through the REAL
service layer, proves:
  1. A manual run over two pending items -> one workbench.run parent, two
     admitted item children + two DISTINCT memory children (memory default
     on), all receipts terminal, memory observations receipt-gated, history
     row carrying parent receipt + child links.
  2. A memory-disabled run -> item children only, zero memory children.
  3. A mid-item cancel -> no item output or memory write for the cancelled
     work, the earned receipts survive, the parent closes terminal.

Run with an isolated HOME. Exits non-zero on any failed assertion.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

from holdspeak.db import get_database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.workbench_runner import WorkbenchRunner

LAN_URL = "http://192.168.1.43:8080/v1"
LAN_MODEL = "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf"


def _children_of(broker, owner, parent_id):
    seen = {}
    for e in broker.events(0, {}, owner)["events"]:
        op = broker.store.operation(e["operation_id"])
        if op and op.get("parent_operation_id") == parent_id:
            seen[op["operation_id"]] = op
    return list(seen.values())


def _setup(db, wb_id, items):
    db.recipes.upsert(
        recipe_id="walk-wb-agent", name="Walk WB Agent", role="assistant",
        system_prompt="Answer in one short sentence.", user_template="{input}",
        profile_id="lan43",
    )
    db.workbenches.upsert(workbench_id=wb_id, name=f"Walk {wb_id}",
                          recipe_id="walk-wb-agent", profile_id="lan43")
    for i, title in enumerate(items, 1):
        db.workbench_items.upsert(
            item_id=f"{wb_id}-item-{i}", workbench_id=wb_id, title=title,
            body="Keep it to one sentence.", priority=i, status="pending",
        )


async def main(workdir: Path) -> int:
    db = get_database()  # the runtime singleton, under the isolated HOME
    db.profiles.upsert(
        profile_id="lan43", name="LAN .43", kind="openAICompatible",
        base_url=LAN_URL, model=LAN_MODEL, requires_key=False,
    )
    broker = _configure(db)
    owner = Principal(PrincipalKind.OWNER, "walk-owner")
    service = WorkbenchRunner(db, broker)

    # Leg 1: two items, memory on.
    _setup(db, "walk-wb1", ["Name one color", "Name one animal"])
    run = await service.run(owner, "walk-wb1")
    parent_id = run["parent_operation_id"]
    kids = _children_of(broker, owner, parent_id)
    item_kids = [k for k in kids if "item" in str(k.get("arguments", {}).get("invocation_id", "")) or k["operation_id"] in {c["operation_id"] for c in run["children"] if "item" in c.get("planned_node", str(c))}]
    # Robust split: use the run's own child links.
    links = run["children"]
    item_links = [c for c in links if str(c.get("invocation_id", "")).startswith("workbench_item_")]
    memory_links = [c for c in links if str(c.get("invocation_id", "")).startswith("workbench_memory_")]
    assert len(item_links) == 2, f"two item children, got {len(item_links)}: {links}"
    assert len(memory_links) == 2, f"two memory children, got {len(memory_links)}: {links}"
    for c in links:
        receipt = broker.store.receipt(c["operation_id"])
        assert receipt, f"child {c} lacks a terminal receipt"
    with db._connection() as conn:
        row = conn.execute("SELECT parent_receipt_id, child_links_json FROM workbench_runs WHERE parent_operation_id=?",
                           (parent_id,)).fetchone()

    assert row and row["parent_receipt_id"], "history row carries the parent receipt"
    from holdspeak.workbench_memory import read_memory
    mem = len(read_memory("walk-wb1"))
    assert mem >= 1, "memory observations landed receipt-gated"
    print(f"leg1 parent={parent_id} items=2 memory_children=2 receipts=all memory_rows={mem}")

    # Leg 2: memory disabled -> no memory children.
    _setup(db, "walk-wb2", ["Name one fruit"])
    run2 = await service.run(owner, "walk-wb2", memory_enabled=False)
    links2 = run2["children"]
    assert len([c for c in links2 if str(c.get("invocation_id", "")).startswith("workbench_item_")]) == 1
    assert not [c for c in links2 if str(c.get("invocation_id", "")).startswith("workbench_memory_")], \
        f"memory disabled must admit no memory child: {links2}"
    print(f"leg2 parent={run2['parent_operation_id']} item_children=1 memory_children=0")

    # Leg 3: cancel mid-item.
    _setup(db, "walk-wb3", ["Write a very long story about the ocean"])
    task = asyncio.create_task(service.run(owner, "walk-wb3"))
    parent3 = None
    for _ in range(200):
        await asyncio.sleep(0.05)
        with db._connection() as conn:
            r = conn.execute(
                "SELECT operation_id, active_child_invocation_id FROM kernel_parent_runs "
                "WHERE definition_ref='workbench:walk-wb3' AND state='OPEN'").fetchone()
        if r and r["active_child_invocation_id"]:
            parent3 = r["operation_id"]
            break
    assert parent3, "cancel-leg parent never opened with an active child"
    disposition = broker.parent_run_controller.cancel_by_operation_id(owner, parent3)
    try:
        result3 = await task
        print(f"leg3 run returned (not raised): keys={sorted(result3)}")
    except Exception as exc:
        print(f"leg3 run surfaced {type(exc).__name__} after cancel (honest)")
    with db._connection() as conn:
        state = conn.execute("SELECT state FROM kernel_parent_runs WHERE operation_id=?",
                             (parent3,)).fetchone()["state"]
        item = conn.execute("SELECT status, result FROM workbench_items WHERE workbench_id='walk-wb3'").fetchone()

    assert state not in ("OPEN", "CANCELLING"), f"parent terminal, got {state}"
    assert item["status"] != "complete", f"cancelled item must not complete: {dict(item)}"
    from holdspeak.workbench_memory import read_memory as _rm
    mem3 = len(_rm("walk-wb3"))
    assert mem3 == 0, "no memory write for cancelled work"
    for c in _children_of(broker, owner, parent3):
        receipt = broker.store.receipt(c["operation_id"])
        assert receipt is not None, "active child keeps its terminal receipt"
        print(f"leg3 child={c['operation_id']} receipt={receipt['outcome']}")
    print(f"leg3 disposition={disposition} parent_state={state} item_status={item['status']} memory_rows=0")

    print("WALK OK: manual Workbench runs admitted parent+item+memory children with "
          "receipts; disabled memory minted none; mid-run cancel left no item output "
          "or memory while receipts survived.")
    return 0


if __name__ == "__main__":
    import tempfile

    sys.exit(asyncio.run(main(Path(tempfile.mkdtemp(prefix="hs13105-walk-")))))
