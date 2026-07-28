"""HS-106-08: ``process.spawn`` adapts launch records without spine logic."""
from __future__ import annotations

from pathlib import Path

from holdspeak.db import Database
from holdspeak.kernel.broker import Broker
from holdspeak.kernel.journal import JournalStore
from holdspeak.kernel.model import OperationSpec
from holdspeak.kernel.process_spawn import ProcessSpawnCodec
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
NODE = Principal(PrincipalKind.NODE, "local")


class FakeLaunchService:
    def __init__(self) -> None:
        self.rows = {}

    def validate_request(self, request):
        if not request.get("source_id"):
            error = ValueError("source_unknown")
            error.reason = "source_unknown"
            raise error

    def record_admitted(self, launch_id, request, *, operation_id):
        self.rows[launch_id] = {
            "launch_id": launch_id,
            "state": "admitted",
            "request": dict(request),
            "operation_id": operation_id,
            "commands": {},
        }

    def record_decision(self, launch_id, decision, *, reason=""):
        self.rows[launch_id]["state"] = "approved" if decision == "approve" else "rejected"

    def launch_record(self, launch_id):
        return self.rows.get(launch_id)


class FakeCommands:
    def get(self, command_id):
        return None


def request(launch_id="launch_1234567890abcdef", *, source_id="src_1"):
    return {
        "request_schema": 1,
        "request_id": "request-spawn",
        "idempotency_key": f"process.spawn:{launch_id}",
        "operation": {"name": "process.spawn", "version": 1},
        "subject_refs": ["story:HS-106-08"],
        "target": {"ref": f"launch:{launch_id}"},
        "arguments": {
            "launch_id": launch_id,
            "agent_profile_id": "claude-default",
            "source_id": source_id,
            "worktree": {"mode": "existing", "worktree_id": "wt_1"},
            "story_ref": {"project": "holdspeak", "story_id": "HS-106-08"},
            "session_label": "hs-pr-393-proof",
        },
        "placement": "node:local",
    }


def rig(tmp_path: Path):
    db = Database(tmp_path / "spawn.db")
    service = FakeLaunchService()
    codec = ProcessSpawnCodec(service, FakeCommands())
    broker = Broker(
        JournalStore(db._connection),
        (OperationSpec(codec.name, codec.version, codec, "agent.submit", "propose"),),
        clock=lambda: 1000.0,
    )
    return broker, service


def test_process_spawn_admits_decides_claims_and_receipts(tmp_path: Path) -> None:
    broker, service = rig(tmp_path)
    handle = broker.submit(request(), OWNER)
    assert handle["state"] == "awaiting_decision"
    assert service.rows["launch_1234567890abcdef"]["state"] == "admitted"

    approved = broker.decide(handle["operation_id"], "approve", handle["revision"], OWNER)
    assert approved["state"] == "awaiting_execution"
    assert service.rows["launch_1234567890abcdef"]["state"] == "approved"

    claimed = broker.claim(NODE, "launch_1234567890abcdef")
    assert claimed["operations"][0]["operation_id"] == handle["operation_id"]
    receipt = broker.receipt(
        handle["operation_id"], "succeeded", "launch:launch_1234567890abcdef", NODE
    )
    assert receipt["outcome"] == "succeeded"


def test_process_spawn_refuses_hard_prerequisite_by_name(tmp_path: Path) -> None:
    broker, _ = rig(tmp_path)
    refused = broker.submit(request(source_id=""), OWNER)
    assert refused["state"] == "refused"
    assert refused["receipt"]["outcome"] == "source_unknown"


def test_process_spawn_rejects_client_execution_fields(tmp_path: Path) -> None:
    broker, _ = rig(tmp_path)
    raw = request()
    raw["arguments"]["command"] = "rm -rf /"
    refused = broker.submit(raw, OWNER)
    assert refused["receipt"]["outcome"] == "operation_field_not_allowed"
