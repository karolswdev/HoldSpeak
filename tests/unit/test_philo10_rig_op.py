"""PHILO-10-01: the rig's ``op`` steps reach the Send and read each admitted write's receipt, through a REAL hub process.

``scripts/graph_walk.py`` boots ``holdspeak web`` on an isolated HOME and every
step enters at ``POST /api/mcp`` (the story's rig line: "``op`` steps that read
the send's receipt and the record row"). The path is the owner's: save a
folder destination, preview a published update, prepare, send, read what was
sent, discard a second prepared send, remove the destination -- each admitted
write's receipt read back with ``kernel.receipt.read``. One observation line
per step (``-s`` shows them; the evidence records them).
"""
from __future__ import annotations

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
