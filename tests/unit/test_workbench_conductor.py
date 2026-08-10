"""HS-131-06 durable scheduled-minute identity."""
from __future__ import annotations
import asyncio
import pytest
from holdspeak.db import Database
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.workbench_runner import WorkbenchRunner
from holdspeak.services.workbench_service import WorkbenchService

OWNER = Principal(PrincipalKind.OWNER, "conductor-owner")
SCHEDULER = Principal(PrincipalKind.SCHEDULER, "local-workbench-conductor")


def test_minute_dedupe_and_restart_with_live_delegation(tmp_path, monkeypatch):
    path=tmp_path / "restart.db"; db=Database(path)
    profile=db.profiles.upsert(profile_id="p",name="P",kind="openAICompatible",base_url="http://profile",model="model")
    recipe=db.recipes.upsert(recipe_id="r",name="R",system_prompt="S")
    service=WorkbenchService(db)
    wid=service.create_workbench(OWNER,name="W",recipe_id=recipe.id,profile_id=profile.id,schedule="* * * * *")["id"]
    service.update_workbench(OWNER,wid,schedule_enabled=True)
    class FakeIntel:
        def run_prompt(self, **_): return "unused"
    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: FakeIntel())
    broker=_configure(db)
    first=asyncio.run(WorkbenchRunner(db,broker).run_scheduled(SCHEDULER,wid,due_minute=999))
    assert first["receipt_id"]
    # Restart means a NEW Database object over the durable same file.
    restarted=Database(path); restarted_broker=_configure(restarted)
    with pytest.raises(KernelRefused) as duplicate:
        asyncio.run(WorkbenchRunner(restarted,restarted_broker).run_scheduled(SCHEDULER,wid,due_minute=999))
    assert duplicate.value.reason == "duplicate_tick"
    with restarted._connection() as conn:
        operation_id = conn.execute("SELECT operation_id FROM kernel_receipts ORDER BY created_at DESC LIMIT 1").fetchone()[0]
    receipt = restarted_broker.store.receipt(operation_id)
    assert (receipt["state"], receipt["outcome"]) == ("refused", "duplicate_tick")
    later=asyncio.run(WorkbenchRunner(restarted,restarted_broker).run_scheduled(SCHEDULER,wid,due_minute=1000))
    assert later["receipt_id"]
