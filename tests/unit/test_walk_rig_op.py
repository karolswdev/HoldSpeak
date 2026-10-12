"""The walk rig's op step through a real hub process: Room operations, the steward and Send.

Grouped by service (the fast diet, 2026-10-12). Moved verbatim from:
- test_philo9_rig_op.py
- test_philo9_02_rig_op.py
- test_philo10_rig_op.py
"""
from __future__ import annotations

# ── moved from tests/unit/test_philo9_rig_op.py ──
# PHILO-9-01: the rig's ``op`` step drives the Room's operations through a REAL hub process.
#
# ``scripts/graph_walk.py`` boots ``holdspeak web`` on an isolated HOME
# (``gw.Hub``) and every step enters at ``POST /api/mcp``: the same operations
# an atlas case names. This fence runs the job's path -- make a project, add a
# milestone and a risk, list, file a decision, replay the filing, remove it, draft,
# publish, read the update back for delivery, what needs me -- and prints one
# observation line per step (``-s`` shows them; the evidence records them).
# Story 01 has no face criterion; this is the rig's op observation, not a glass case.

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import graph_walk as gw  # noqa: E402


@pytest.mark.timeout(240)
def test_the_rig_drives_the_room_job_through_a_real_hub(tmp_path: Path) -> None:
    hub = gw.Hub(tmp_path / "home", token="philo9-01-rig-op").start()
    variables: dict[str, Any] = {}
    provenance = {"fixture_hashes": {}, "restarts": [], "boundary_substitutions": [], "clock": {}}
    past = (date.today() - timedelta(days=3)).isoformat()
    observed: list[dict[str, Any]] = []

    def op(name: str, args: dict[str, Any], **capture: Any) -> dict[str, Any]:
        step = {"kind": "op", "name": name, "args": args, **capture}
        record = gw.run_step(step, page=None, hub=hub, provenance=provenance, variables=variables)
        observed.append({"op": name, "refusal": record["refusal"], "elapsed_s": round(record["elapsed_s"], 3),
                         "captured": record.get("captured")})
        assert record["refusal"] is None, (name, record["refusal"])
        return record["response"]

    try:
        op("project.create", {"name": "Payments ledger cutover"}, capture_as="project_id", capture_path="project.id")
        pid = variables["project_id"]
        op("project.item.create", {"project_id": pid, "item_type": "milestone", "title": "Cutover rehearsal",
                                   "due_at": past})
        op("project.item.create", {"project_id": pid, "item_type": "risk", "title": "Old ledger freeze slips",
                                   "details": {"likelihood": "medium", "impact": "high",
                                               "mitigation": "Freeze the schema by Friday"}})
        items = op("project.item.list", {"project_id": pid})
        assert sorted(i["title"] for i in items["items"]) == ["Cutover rehearsal", "Old ledger freeze slips"]
        room = op("project.get_room", {"project_id": pid})
        assert room["health"]["assessment"] == "at_risk"
        assert [r["title"] for r in room["needsYou"]["items"] if r.get("kind") == "milestone"] == ["Cutover rehearsal"]
        needs = op("desk.needs_you", {})
        assert any(i.get("title") == "Cutover rehearsal" for i in needs["items"])
        made = op("decision.create", {"title": "Freeze the schema"}, capture_as="decision_id")
        first = op("project.resource.add", {"project_id": pid, "resource_ref": f"decision:{made['id']}",
                                            "command_id": "pcmd_rig_file"})
        again = op("project.resource.add", {"project_id": pid, "resource_ref": f"decision:{made['id']}",
                                            "command_id": "pcmd_rig_file"})
        assert again == first
        assert op("project.resource.list", {"project_id": pid})["resources"][0]["resource_ref"] == f"desk_decision:{made['id']}"  # the one ref name (2026-10-03)
        assert op("project.resource.remove", {"project_id": pid, "resource_ref": f"decision:{made['id']}"})["removed"] is True
        op("project.draft_update", {"project_id": pid}, capture_as="update_id", capture_path="update.id")
        published = op("project.publish_update", {"update_id": variables["update_id"]})
        assert published["update"]["lifecycle"] == "published"
        updates = op("project.list_updates", {"project_id": pid, "lifecycle": "published"})
        assert updates["updates"][0]["body_md"] and updates["updates"][0]["deliveries"] == []
    finally:
        hub.stop()
    print("\nRIG OP OBSERVATIONS " + json.dumps(observed))
    assert len(observed) == 14


# ── moved from tests/unit/test_philo9_02_rig_op.py ──
# PHILO-9-02: the rig's ``op`` steps read the kernel receipt of each admitted write, through a REAL hub process.
#
# ``scripts/graph_walk.py`` boots ``holdspeak web`` on an isolated HOME and every
# step enters at ``POST /api/mcp`` (the test plan's rig line: "``op`` steps that
# read the kernel receipt for each admitted write"). The path is the steward's
# share of the owner's job: set the steward's policy, let it run and draft the
# update, read the run to its receipt, publish, mark it delivered, and read each
# admitted write's receipt back with ``kernel.receipt``. One observation line per
# step (``-s`` shows them; the evidence records them).

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


# ── moved from tests/unit/test_philo10_rig_op.py ──
# PHILO-10-01: the rig's ``op`` steps reach the Send and read each admitted write's receipt, through a REAL hub process.
#
# ``scripts/graph_walk.py`` boots ``holdspeak web`` on an isolated HOME and every
# step enters at ``POST /api/mcp`` (the story's rig line: "``op`` steps that read
# the send's receipt and the record row"). The path is the owner's: save a
# folder destination, preview a published update, prepare, send, read what was
# sent, discard a second prepared send, remove the destination -- each admitted
# write's receipt read back with ``kernel.receipt.read``. One observation line
# per step (``-s`` shows them; the evidence records them).

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import graph_walk as gw  # noqa: E402


@pytest.mark.timeout(240)
def test_the_rig_reaches_the_send_and_reads_each_receipt(tmp_path: Path) -> None:
    hub = gw.Hub(tmp_path / "home", token="philo10-01-rig-op").start()
    variables: dict[str, Any] = {}
    provenance = {"fixture_hashes": {}, "restarts": [], "boundary_substitutions": [], "clock": {}}
    observed: list[dict[str, Any]] = []
    folder = tmp_path / "out"
    folder.mkdir()

    def op(name: str, args: dict[str, Any], **capture: Any) -> dict[str, Any]:
        step = {"kind": "op", "name": name, "args": args, **capture}
        record = gw.run_step(step, page=None, hub=hub, provenance=provenance, variables=variables)
        observed.append({"op": name, "refusal": record["refusal"],
                         "operation_id": (record["response"] or {}).get("operation_id")
                         if isinstance(record["response"], dict) else None})
        assert record["refusal"] is None, (name, record["refusal"])
        return record["response"]

    def receipt(operation_id: str) -> dict[str, Any]:
        return op("kernel.receipt.read", {"operation_id": operation_id})["objects"][0]["receipt"]

    try:
        op("project.create", {"name": "Payments ledger cutover"}, capture_as="project_id", capture_path="project.id")
        drafted = op("project.draft_update", {"project_id": variables["project_id"]})
        update = drafted["update"]["id"]
        # PHILO-15 B64: a fresh Project drafts an unreviewed NOTHING TO REPORT
        # (refused NOTHING VERIFIED); the owner's saved line is reviewed.
        op("project.update_draft", {"update_id": update,
                                    "body_md": "## Progress\n\nThe ledger cutover is on track.\n"})
        op("project.publish_update", {"update_id": update})
        saved = op("channel.save_destination", {"name": "Team folder", "channel": "file", "folder": str(folder)})
        assert receipt(saved["operation_id"])["state"] == "succeeded"
        dest = saved["destination"]["id"]
        assert [d["id"] for d in op("channel.destinations", {})["destinations"]] == ["holdspeak-folder", dest]
        document_ref = f"project_update:{update}"
        preview = op("channel.preview", {"document_ref": document_ref, "destination_id": dest})
        prepared = op("channel.prepare", {"document_ref": document_ref, "destination_id": dest})
        assert receipt(prepared["operation_id"])["state"] == "succeeded"
        assert prepared["send"]["payload_digest"] == preview["payload_digest"]
        sent = op("channel.send", {"send_id": prepared["send"]["id"], "command_id": "rig-press"})
        assert sent["outcome"] == "sent" and receipt(sent["operation_id"])["state"] == "succeeded"
        proof = sent["send"]["proof"]
        assert Path(proof["path"]).parent == folder.resolve() and proof["sha256"] == preview["payload_digest"]
        listed = op("channel.sends", {"document_ref": document_ref})["sends"]
        assert [(s["id"], s["state"]) for s in listed] == [(prepared["send"]["id"], "sent")]
        second = op("channel.prepare", {"document_ref": document_ref, "destination_id": dest})
        discarded = op("channel.discard", {"send_id": second["send"]["id"]})
        assert discarded["send"]["state"] == "discarded" and receipt(discarded["operation_id"])["state"] == "succeeded"
        assert op("channel.check_destination", {"destination_id": dest})["check"]["state"] == "ready"
        removed = op("channel.remove_destination", {"destination_id": dest})
        assert removed["destination"]["state"] == "parked" and receipt(removed["operation_id"])["state"] == "succeeded"
        history = op("project.list_updates", {"project_id": variables["project_id"]})["updates"]
        [row] = next(u for u in history if u["id"] == update)["deliveries"]
        assert (row["channel"], row["outcome"], row["operation_id"]) == ("file", "sent", sent["operation_id"])
    finally:
        hub.stop()
    print("\nRIG OP OBSERVATIONS " + json.dumps(observed))
