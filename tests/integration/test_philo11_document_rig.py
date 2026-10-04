"""PHILO-11-01: each stored kind crosses the real rig op and hub boundary.

Sources are minted through the production services and repositories before
the subprocess hub starts. Every channel call below is graph_walk.run_step,
which reaches the real MCP endpoint. No channel response is injected.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import graph_walk as gw  # noqa: E402

KINDS = (
    "project_update", "monday_brief", "desk_decision", "meeting_decision",
    "decision_record", "meeting_summary", "meeting_digest", "meeting_followup",
)


@pytest.fixture(scope="module")
def document_hub(tmp_path_factory):
    from holdspeak.db.core import Database
    from tests.unit._philo11_documents import mint_documents

    home = tmp_path_factory.mktemp("philo11-rig")
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("HOME", str(home))
        patch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(home / "people.key"))
        path = home / ".local/share/holdspeak/holdspeak.db"
        db = Database(path)
        try:
            documents = mint_documents(db, people_keystore_path=home / "people.key")
        finally:
            db.close()
        hub = gw.Hub(home, token="philo11-document-rig").start()
        try:
            assert Path(hub.db_path).resolve() == path.resolve()
            yield hub, documents, home
        finally:
            hub.stop()


@pytest.mark.parametrize("kind", KINDS)
def test_each_document_previews_prepares_and_lists_through_the_real_rig(document_hub, kind: str) -> None:
    hub, documents, home = document_hub
    provenance = {"fixture_hashes": {}, "restarts": [], "boundary_substitutions": [], "clock": {}}
    variables: dict[str, Any] = {}
    observations: list[dict[str, Any]] = []

    def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
        record = gw.run_step(
            {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
        assert record["refusal"] is None, (name, record)
        result = record["response"]
        assert isinstance(result, dict), result
        observations.append({"name": name, "operation_id": result.get("operation_id"), "refusal": None})
        return result

    destination = op("channel.save_destination", {
        "channel": "file", "name": f"{kind} folder", "folder": str(home),
    })["destination"]["id"]
    ref = documents[kind]
    args = {"document_ref": ref, "destination_id": destination}
    preview = op("channel.preview", args)
    prepared = op("channel.prepare", args)
    row = prepared["send"]
    assert row["document_ref"] == ref
    assert row["payload_digest"] == preview["payload_digest"]
    assert row["state"] == "prepared"
    assert preview["preview"]["text"].strip()
    if kind == "monday_brief":
        # Inventory gap 5 (2026-10-03): the sent Brief carries no People data.
        assert "Avery" not in preview["preview"]["text"]
        assert "You owe" not in preview["preview"]["text"]
    if kind.startswith("meeting_") and kind != "meeting_decision":
        from tests.unit._philo11_documents import TRANSCRIPT_SENTINEL
        assert TRANSCRIPT_SENTINEL not in preview["preview"]["text"]
    sent = op("channel.send", {"send_id": row["id"], "command_id": f"rig-{kind}"})
    assert sent["outcome"] == "sent", sent
    proof = sent["send"]["proof"]
    assert Path(proof["path"]).parent == home.resolve()
    assert Path(proof["path"]).read_text() == preview["preview"]["text"]
    listed = op("channel.sends", {"document_ref": ref})["sends"]
    assert [(item["id"], item["state"]) for item in listed] == [(row["id"], "sent")]
    receipt = op("kernel.receipt.read", {"operation_id": sent["operation_id"]})["objects"][0]["receipt"]
    assert receipt["state"] == "succeeded"
    print("\nDOCUMENT RIG " + json.dumps({
        "kind": kind, "document_ref": ref, "db_under_home": True,
        "payload_digest": preview["payload_digest"], "steps": observations,
    }, sort_keys=True))
