"""PHILO-9-01: the rig's ``op`` step drives the Room's operations through a REAL hub process.

``scripts/graph_walk.py`` boots ``holdspeak web`` on an isolated HOME
(``gw.Hub``) and every step enters at ``POST /api/mcp``: the same operations
an atlas case names. This fence runs the job's path -- make a project, add a
milestone and a risk, list, file a decision, replay the filing, remove it, draft,
publish, read the update back for delivery, what needs me -- and prints one
observation line per step (``-s`` shows them; the evidence records them).
Story 01 has no face criterion; this is the rig's op observation, not a glass case.
"""
from __future__ import annotations

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
        assert op("project.resource.list", {"project_id": pid})["resources"][0]["resource_ref"] == f"decision:{made['id']}"
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
