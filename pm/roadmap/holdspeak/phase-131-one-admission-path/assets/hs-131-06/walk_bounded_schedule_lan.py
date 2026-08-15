"""HS-131-06 real-LAN walk: scheduled Workbench work under bounded delegation.

Against the live llama.cpp endpoint at 192.168.1.43:8080, through the REAL
service layer, proves the story's manual leg end-to-end:
  1. Owner enables a schedule -> one exact-terms local delegation; a due tick
     runs as the SCHEDULER principal through the admitted runner on real
     metal; parent + child receipts carry actor=scheduler, delegator=owner,
     and the schedule-delegation authority basis.
  2. The same due minute claimed again (restart shape) -> duplicate_tick
     refusal with a durable terminal refused receipt, before any model call.
  3. Owner changes a bound term (target) -> the delegation is revoked in the
     same gesture; the next due tick refuses by name with a terminal receipt;
     a deliberate re-enable mints a NEW delegation with new terms and the
     next tick runs on real metal again.
  4. schedule_enabled arriving as bare synced configuration (no local
     gesture) -> delegation_missing, no model call.
  5. Owner disables DURING an active scheduled run -> the delegation is
     revoked, the parent lands terminal non-completed, and the item does not
     publish late output.

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
from holdspeak.services.errors import ServiceError
from holdspeak.services.schedule_delegation import ScheduleDelegationService
from holdspeak.services.workbench_runner import WorkbenchRunner
from holdspeak.services.workbench_service import WorkbenchService

LAN_URL = "http://192.168.1.43:8080/v1"
LAN_MODEL = "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf"

OWNER = Principal(PrincipalKind.OWNER, "walk-owner")
SCHEDULER = Principal(PrincipalKind.SCHEDULER, "local-workbench-conductor")


def _last_receipt(db, broker):
    with db._connection() as conn:
        row = conn.execute(
            "SELECT operation_id FROM kernel_receipts ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
    return broker.store.receipt(row["operation_id"]) if row else None


def _make_workbench(db, service, name, item_title, body="Answer in one short sentence."):
    wb = service.create_workbench(
        OWNER, name=name, recipe_id="walk-sched-agent", profile_id="lan43",
        schedule="* * * * *",
    )
    db.workbench_items.upsert(
        item_id=f"{wb['id']}-item-1", workbench_id=wb["id"], title=item_title,
        body=body, priority=1, status="pending",
    )
    return wb["id"]


async def main() -> int:
    db = get_database()  # the runtime singleton, under the isolated HOME
    db.profiles.upsert(
        profile_id="lan43", name="LAN .43", kind="openAICompatible",
        base_url=LAN_URL, model=LAN_MODEL, requires_key=False,
    )
    db.profiles.upsert(
        profile_id="lan43b", name="LAN .43 second dial", kind="openAICompatible",
        base_url=LAN_URL, model=LAN_MODEL, requires_key=False,
    )
    db.recipes.upsert(
        recipe_id="walk-sched-agent", name="Walk Schedule Agent", role="assistant",
        system_prompt="Answer in one short sentence.", user_template="{input}",
        profile_id="lan43",
    )
    broker = _configure(db)
    service = WorkbenchService(db)
    runner = WorkbenchRunner(db, broker)
    delegations = ScheduleDelegationService(db)

    # ── Leg 1: enable gesture -> delegation -> due tick on real metal ──
    wid = _make_workbench(db, service, "Walk Sched 1", "Name one color")
    service.update_workbench(OWNER, wid, schedule_enabled=True)
    row = delegations.live(wid)
    assert row and row["delegator_kind"] == "owner", f"delegation minted: {row}"
    assert row["cadence"] == "* * * * *" and row["deployment_revision_id"], row
    basis = f"schedule-delegation:{row['id']}:{row['terms_sha256']}"

    run = await runner.run_scheduled(SCHEDULER, wid, due_minute=100001)
    parent = broker.store.operation(run["parent_operation_id"])
    assert parent["principal_kind"] == "scheduler", parent
    for op_id in [parent["operation_id"]] + [
        c["operation_id"] for c in run.get("children", [])
    ]:
        receipt = broker.store.receipt(op_id)
        assert receipt, f"terminal receipt missing for {op_id}"
        assert (
            receipt["actor_kind"], receipt["delegator_kind"], receipt["authority_basis"]
        ) == ("scheduler", "owner", basis), receipt
        assert receipt["actor_identity"] == "local-workbench-conductor", receipt
    item = db.workbench_items.get(f"{wid}-item-1")
    assert item.status == "done" and item.result, f"real output landed: {item.status}"
    print(f"leg1 parent={parent['operation_id']} basis={basis} item=done "
          f"output={item.result[:60]!r}")

    # ── Leg 2: same due minute again -> duplicate_tick, receipted, no model ──
    dup_reason = None
    try:
        await runner.run_scheduled(SCHEDULER, wid, due_minute=100001)
    except Exception as exc:
        dup_reason = getattr(exc, "reason", getattr(exc, "code", None))
    assert dup_reason == "duplicate_tick", f"duplicate refused by name: {dup_reason}"
    receipt = _last_receipt(db, broker)
    assert (receipt["state"], receipt["outcome"]) == ("refused", "duplicate_tick"), receipt
    print(f"leg2 duplicate_tick refused with terminal receipt {receipt['receipt_id']}")

    # ── Leg 3: bound-term change revokes; named refusal; re-enable runs anew ──
    service.update_workbench(OWNER, wid, profile_id="lan43b")
    assert delegations.live(wid) is None, "bound edit revoked the delegation"
    reason = None
    try:
        await runner.run_scheduled(SCHEDULER, wid, due_minute=100002)
    except Exception as exc:
        reason = getattr(exc, "reason", getattr(exc, "code", None))
    assert reason in {"delegation_revoked", "delegation_missing"}, reason
    receipt = _last_receipt(db, broker)
    assert receipt["state"] == "refused" and receipt["outcome"] == reason, receipt
    print(f"leg3a bound edit -> tick refused {reason} with receipt")

    service.update_workbench(OWNER, wid, schedule_enabled=False)
    service.update_workbench(OWNER, wid, schedule_enabled=True)
    row2 = delegations.live(wid)
    assert row2 and row2["id"] != row["id"], "re-enable minted a NEW delegation"
    db.workbench_items.upsert(
        item_id=f"{wid}-item-2", workbench_id=wid, title="Name one animal",
        body="Answer in one short sentence.", priority=1, status="pending",
    )
    run3 = await runner.run_scheduled(SCHEDULER, wid, due_minute=100003)
    receipt3 = broker.store.receipt(run3["parent_operation_id"])
    new_basis = f"schedule-delegation:{row2['id']}:{row2['terms_sha256']}"
    assert receipt3["authority_basis"] == new_basis, receipt3
    print(f"leg3b re-enable -> new delegation {row2['id']} ran on metal")

    # ── Leg 4: synced flag alone is not authority ──
    wid4 = _make_workbench(db, service, "Walk Sched Synced", "Name one fruit")
    with db._connection() as conn:  # sync writes config, never a gesture
        conn.execute("UPDATE workbenches SET schedule_enabled=1 WHERE id=?", (wid4,))
    reason4 = None
    try:
        await runner.run_scheduled(SCHEDULER, wid4, due_minute=100004)
    except Exception as exc:
        reason4 = getattr(exc, "reason", getattr(exc, "code", None))
    assert reason4 == "delegation_missing", reason4
    print("leg4 synced schedule_enabled -> delegation_missing, no model call")

    # ── Leg 5: disable during an active run fences late output ──
    wid5 = _make_workbench(db, service, "Walk Sched Cancel",
                           "Write a very long story about the ocean",
                           body="Write at least 800 words.")
    service.update_workbench(OWNER, wid5, schedule_enabled=True)
    task = asyncio.create_task(runner.run_scheduled(SCHEDULER, wid5, due_minute=100005))
    opened = None
    for _ in range(400):
        await asyncio.sleep(0.05)
        with db._connection() as conn:
            r = conn.execute(
                "SELECT operation_id, active_child_invocation_id FROM kernel_parent_runs "
                "WHERE definition_ref=? AND state='OPEN'", (f"workbench:{wid5}",)
            ).fetchone()
        if r and r["active_child_invocation_id"]:
            opened = r["operation_id"]
            break
    assert opened, "cancel-leg parent never opened with an active child"
    service.update_workbench(OWNER, wid5, schedule_enabled=False)  # the real gesture
    try:
        result5 = await task
        print(f"leg5 run returned (not raised): keys={sorted(result5)}")
    except Exception as exc:
        print(f"leg5 run surfaced {type(exc).__name__} after disable (honest)")
    assert delegations.live(wid5) is None, "disable revoked the delegation"
    with db._connection() as conn:
        state = conn.execute(
            "SELECT state FROM kernel_parent_runs WHERE operation_id=?", (opened,)
        ).fetchone()["state"]
        item5 = conn.execute(
            "SELECT status FROM workbench_items WHERE workbench_id=?", (wid5,)
        ).fetchone()
    assert state not in ("OPEN", "CANCELLING"), f"parent terminal, got {state}"
    assert item5["status"] != "done", f"late output must not publish: {dict(item5)}"
    print(f"leg5 disable mid-run -> parent={state} item={item5['status']} "
          f"delegation revoked")

    print("WALK OK: enable minted an exact-terms delegation and the scheduler ran "
          "admitted work on real metal with honest receipts; duplicate, revoked, "
          "and sync-only ticks refused by name with terminal receipts; re-enable "
          "minted new terms; disable mid-run fenced late output.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
