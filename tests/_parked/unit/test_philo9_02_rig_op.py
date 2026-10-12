"""PHILO-9-02: the rig's ``op`` steps read the kernel receipt of each admitted write, through a REAL hub process.

``scripts/graph_walk.py`` boots ``holdspeak web`` on an isolated HOME and every
step enters at ``POST /api/mcp`` (the test plan's rig line: "``op`` steps that
read the kernel receipt for each admitted write"). The path is the steward's
share of the owner's job: set the steward's policy, let it run and draft the
update, read the run to its receipt, publish, mark it delivered, and read each
admitted write's receipt back with ``kernel.receipt``. One observation line per
step (``-s`` shows them; the evidence records them).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import graph_walk as gw  # noqa: E402


@pytest.mark.timeout(240)
def test_the_rig_reads_the_receipt_of_each_admitted_steward_write(tmp_path: Path) -> None:
    hub = gw.Hub(tmp_path / "home", token="philo9-02-rig-op").start()
    variables: dict[str, Any] = {}
    provenance = {"fixture_hashes": {}, "restarts": [], "boundary_substitutions": [], "clock": {}}
    observed: list[dict[str, Any]] = []

    def op(name: str, args: dict[str, Any], **capture: Any) -> dict[str, Any]:
        step = {"kind": "op", "name": name, "args": args, **capture}
        record = gw.run_step(step, page=None, hub=hub, provenance=provenance, variables=variables)
        observed.append({"op": name, "refusal": record["refusal"], "captured": record.get("captured"),
                         "operation_id": (record["response"] or {}).get("operation_id")
                         if isinstance(record["response"], dict) else None})
        assert record["refusal"] is None, (name, record["refusal"])
        return record["response"]

    def receipt(operation_id: str) -> dict[str, Any]:
        read = op("kernel.receipt.read", {"operation_id": operation_id})
        return read["objects"][0]["receipt"]

    try:
        op("project.create", {"name": "Payments ledger cutover"}, capture_as="project_id", capture_path="project.id")
        pid = variables["project_id"]
        policy = op("project.configure_steward", {"project_id": pid, "eligible_effect_kinds": ["draft_update"]})
        assert receipt(policy["operation_id"])["state"] == "succeeded"
        started = op("project.run_steward", {"project_id": pid})
        assert started["receipt"] is None and started["state"] == "claimed"
        deadline = time.monotonic() + 60
        while True:
            run = op("project.get_steward_run", {"run_id": started["run_id"]})
            if run["receipt"] is not None or time.monotonic() > deadline:
                break
            time.sleep(0.2)
        assert run["run"]["state"] == "completed" and run["receipt"]["outcome"] == "completed"
        assert receipt(started["operation_id"])["state"] == "succeeded"
        updates = op("project.list_updates", {"project_id": pid})
        drafted = updates["updates"][0]["id"]
        published = op("project.publish_update", {"update_id": drafted})
        assert receipt(published["operation_id"])["outcome"] == "succeeded"
        delivered = op("project.mark_update_delivered", {"update_id": drafted, "delivered_to": "Priya"})
        assert delivered["delivery"]["operation_id"] == delivered["operation_id"]
        assert receipt(delivered["operation_id"])["state"] == "succeeded"
        tools = op("connection.list", {})
        assert {t["provider_id"] for t in tools["tools"]} >= {"github", "jira", "confluence", "calendar", "models"}
    finally:
        hub.stop()
    print("\nRIG OP OBSERVATIONS " + json.dumps(observed))
