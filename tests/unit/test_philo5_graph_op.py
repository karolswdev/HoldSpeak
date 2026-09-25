"""PHILO-5-03: operation steps use the owning hub's MCP transport."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts import graph_walk as gw


class _McpHub:
    url = "http://127.0.0.1:9999"

    def __init__(self, envelope):
        self.envelope = envelope
        self.requests = []

    def mcp(self, request):
        self.requests.append(request)
        return self.envelope


def _result(value, *, error: bool = False):
    return {"jsonrpc": "2.0", "id": 1,
            "result": {"content": [{"type": "text", "text": json.dumps(value)}],
                        "isError": error}}


def _resource_result(value):
    return {"jsonrpc": "2.0", "id": 1,
            "result": {"contents": [{"uri": "holdspeak://thoughts/t-1",
                                        "mimeType": "application/json",
                                        "text": json.dumps(value)}]}}


def test_the_canonical_map_has_all_seventeen_operations_and_no_local_service_target():
    # PHILO-5's seventeen, PHILO-7-01's fifteen desk-slice rows, then
    # PHILO-7-02's nine (decision.status is HTTP only: OP_HTTP_ONLY).
    assert len(gw.OP_MCP_PROJECTIONS) == 41
    assert set(gw.OP_MCP_PROJECTIONS) == {
        "decision.create", "decision.update", "decision.read", "decision.list",
        "meeting.list", "meeting.read", "meeting.import", "meeting.summary.run",
        "brief.generate", "brief.latest", "brief.shelf.write", "brief.shelf.read",
        "thought.create", "thought.save", "thought.read",
        "thought.workbench.read", "thought.list",
        "note.create", "note.read", "note.update", "note.delete", "note.list",
        "zone.create", "zone.read", "zone.update", "zone.delete", "zone.list",
        "kb.create", "kb.read", "kb.update", "kb.delete", "kb.list",
        "zone.file", "zone.unfile", "zone.members",
        "kb.member.add", "kb.member.remove", "kb.members",
        "decision.delete", "decision.supersede", "kernel.receipt.read",
    }
    assert gw.OP_HTTP_ONLY == {"decision.status"}
    assert all(value["kind"] in {"tool", "resource"}
               for value in gw.OP_MCP_PROJECTIONS.values())


def test_canonical_map_matches_live_operation_exposure_projection():
    # The adapter is allowed to be explicit, but it cannot drift from the
    # descriptor's live exposure. A descriptor rename therefore turns this
    # fence red instead of silently sending an old tool name.
    from holdspeak.operations import DESCRIPTORS

    descriptors = {descriptor.name: descriptor for descriptor in DESCRIPTORS}
    assert set(descriptors) == set(gw.OP_MCP_PROJECTIONS) | gw.OP_HTTP_ONLY
    for name in gw.OP_HTTP_ONLY:
        assert not [e for e in descriptors[name].exposure if e.startswith("mcp")], name
    for name, projection in gw.OP_MCP_PROJECTIONS.items():
        prefix = "mcp-resource:" if projection["kind"] == "resource" else "mcp:"
        exposed = [entry[len(prefix):] for entry in descriptors[name].exposure
                   if entry.startswith(prefix)]
        target = projection.get("uri") or projection.get("name")
        if projection["kind"] == "resource":
            target = target.replace("{thought_id}", "{thought_id}")
        assert any(entry == target or entry.startswith(target + "[")
                   for entry in exposed), (name, target, exposed)


def test_op_step_sends_a_tool_call_and_captures_the_decoded_domain_response():
    hub = _McpHub(_result({"id": "d-1", "title": "Decision"}))
    variables = {}
    record = gw.run_step(
        {"kind": "op", "name": "decision.create",
         "args": {"title": "Decision"}, "capture_as": "decision_id"},
        page=None, hub=hub, provenance={}, variables=variables,
    )
    assert variables == {"decision_id": "d-1"}
    assert record["name"] == "decision.create"
    assert record["response"] == {"id": "d-1", "title": "Decision"}
    assert record["domain_response"] == record["response"]
    assert record["refusal"] is None
    assert record["envelope"] == hub.envelope
    assert record["elapsed_s"] >= 0
    request = hub.requests[0]
    assert request["method"] == "tools/call"
    assert request["params"] == {
        "name": "desk.create",
        "arguments": {"kind": "decisions", "data": {"title": "Decision"}},
    }


@pytest.mark.timeout(180)
def test_real_hub_brief_capture_matches_the_decision_source_ref(tmp_path: Path):
    hub = gw.Hub(tmp_path / "home", token="philo5-capture-match-test").start()
    variables: dict[str, object] = {}
    provenance = {"fixture_hashes": {}, "restarts": [],
                  "boundary_substitutions": [], "clock": {}}
    try:
        made = gw.run_step(
            {"kind": "op", "name": "decision.create",
             "args": {"title": "Capture match decision", "status": "proposed"},
             "capture_as": "decision_id"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
        assert made["refusal"] is None, made
        decision_id = variables["decision_id"]

        generated = gw.run_step(
            {"kind": "op", "name": "brief.generate", "args": {}},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
        assert generated["refusal"] is None, generated

        latest = gw.run_step(
            {"kind": "op", "name": "brief.latest", "args": {},
             "capture_as": "item_id", "capture_path": "sections.decisions",
             "capture_match": {"source_ref": "decision:{decision_id}"},
             "capture_field": "id"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
        assert latest["refusal"] is None, latest
        rows = latest["response"]["sections"]["decisions"]
        matched = [row for row in rows
                   if row.get("source_ref") == f"decision:{decision_id}"]
        assert len(matched) == 1
        assert variables["item_id"] == matched[0]["id"]
        assert latest["captured"] == {
            "name": "item_id", "path": "sections.decisions",
            "match": {"source_ref": f"decision:{decision_id}"},
            "field": "id", "value": matched[0]["id"],
        }

        with pytest.raises(gw.Blocked, match="matched 0 rows; exactly one is required"):
            gw.run_step(
                {"kind": "op", "name": "brief.latest", "args": {},
                 "capture_as": "missing_item", "capture_path": "sections.decisions",
                 "capture_match": {"source_ref": "decision:missing"}},
                page=None, hub=hub, provenance=provenance, variables=variables,
            )
    finally:
        hub.stop()


def test_unresolved_op_args_block_before_dispatch():
    hub = _McpHub(_result({"id": "never"}))
    with pytest.raises(gw.Blocked, match="never_captured"):
        gw.run_step(
            {"kind": "op", "name": "decision.read",
             "args": {"decision_id": "{never_captured}"}},
            page=None, hub=hub, provenance={}, variables={},
        )
    assert hub.requests == []


def test_summary_run_requires_explicit_mcp_selection_hash_envelope():
    hub = _McpHub(_result({"job_id": "never"}))
    with pytest.raises(gw.Blocked, match="explicit expected_selection_hash"):
        gw.run_step(
            {"kind": "op", "name": "meeting.summary.run",
             "args": {"meeting_id": "m-1"}},
            page=None, hub=hub, provenance={}, variables={},
        )
    assert hub.requests == []


def test_op_refusal_is_named_and_can_match_exact_or_substring_error():
    hub = _McpHub(_result({"code": "owner_required",
                           "error": "meeting.import requires the owner"}, error=True))
    record = gw.run_step(
        {"kind": "op", "name": "meeting.import", "args": {"path": "/tmp/a.wav"}},
        page=None, hub=hub, provenance={}, variables={},
    )
    after = {"headless": True, "op": record}
    ok, why = gw.check_predicate(
        {"kind": "op_refusal", "code": "owner_required",
         "error_contains": "requires the owner"}, {}, after,
    )
    assert ok, why
    assert record["named_refusal"]["code"] == "owner_required"


def test_op_refusal_observes_the_trigger_record_without_refiring(tmp_path: Path):
    hub = _McpHub(_result({"code": "invalid_status", "error": "status is invalid"},
                           error=True))
    case = {
        "id": "cal-op-refusal",
        "trigger": {"kind": "op", "name": "decision.update",
                    "args": {"decision_id": "d-1", "status": "bogus"}},
        "expected": {
            "observe_at": {"kind": "op", "name": "decision.update",
                            "args": {"decision_id": "d-1", "status": "bogus"}},
            "predicate": {"kind": "op_refusal", "error_contains": "invalid"},
        },
        "completion_bound_s": 2,
        "late_grace_s": 0,
    }
    path = tmp_path / "observation.json"
    recorder = gw.Recorder(path, gw.observation_skeleton(
        case, brain="astra", viewport=1440, run_id="refusal",
        provenance={}, atlas="test"))
    record = gw.exercise(None, case, recorder=recorder, hub=hub,
                         provenance={"fixture_hashes": {}, "restarts": [],
                                     "boundary_substitutions": [], "clock": {}},
                         shots=tmp_path / "shots")
    assert record["verdict"] == "pass"
    assert len(hub.requests) == 1
    assert record["after"]["operation_trigger"]["refusal"]["code"] == "invalid_status"


def test_op_resource_projection_uses_resources_read_and_preserves_uri():
    hub = _McpHub(_resource_result({"thought": {"id": "t-1"}}))
    record = gw.run_step(
        {"kind": "op", "name": "thought.read", "args": {"thought_id": "t-1"}},
        page=None, hub=hub, provenance={}, variables={},
    )
    assert hub.requests[0]["method"] == "resources/read"
    assert hub.requests[0]["params"]["uri"] == "holdspeak://thoughts/t-1"
    assert record["response"] == {"thought": {"id": "t-1"}}


def test_headless_snapshot_reads_op_without_page_and_refuses_face_predicates():
    hub = _McpHub(_result({"id": "d-1", "title": "Decision"}))
    op_case = {"expected": {
        "observe_at": {"kind": "op", "name": "decision.read",
                        "args": {"decision_id": "d-1"}},
        "predicate": {"kind": "op_field", "path": "id", "value": "d-1"},
    }}
    observed = gw.snapshot(None, op_case, hub)
    assert observed["op"]["response"]["id"] == "d-1"
    assert gw.check_predicate(op_case["expected"]["predicate"], {}, observed)[0]

    face = gw.snapshot(None, {"expected": {
        "observe_at": "#face", "predicate": {"kind": "text_contains", "value": "x"},
    }}, hub)
    ok, why = gw.check_predicate(face["observe_at"] and {"kind": "text_contains", "value": "x"}, {}, face)
    assert not ok and why.startswith("BLOCKED:")


def test_supplementary_reads_refuse_mutating_operations_without_dispatch():
    hub = _McpHub(_result({"id": "never"}))
    with pytest.raises(gw.Blocked, match="mutating operations"):
        gw.snapshot(None, {"expected": {
            "observe_at": None,
            "reads": [{"kind": "op", "name": "decision.create", "args": {}}],
        }}, hub)
    assert hub.requests == []


@pytest.mark.timeout(180)
def test_real_hub_headless_protocol_snapshot_reads_the_producer(tmp_path: Path):
    hub = gw.Hub(tmp_path / "home", token="philo5-protocol-test").start()
    try:
        observed = gw.snapshot(None, {"expected": {
            "observe_at": "protocol: GET /api/decisions",
            "predicate": {"kind": "protocol_field", "path": "decisions",
                          "nonempty": False},
        }}, hub)
        assert observed["headless"] is True
        assert observed["protocol"]["status"] == 200
        assert "decisions" in observed["protocol"]["payload"]
    finally:
        hub.stop()


def test_restart_required_op_predicate_rejects_missing_retention_flags():
    after = {"op": {"name": "meeting.read", "response": {"summary": "s"}},
             "restart": {"summary_retained": True,
                         "receipt_retained": True,
                         "meeting_identity_retained": False}}
    ok, why = gw.check_predicate(
        {"kind": "op_field", "path": "summary", "value": "s",
         "restart_required": True}, {}, after)
    assert not ok
    assert "meeting_identity_retained" in why


@pytest.mark.timeout(180)
def test_real_hub_op_reaches_the_bound_registry(tmp_path: Path):
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.runtime import composition
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    # This is the same in-process REAL hub pattern used by PHILO-5-01. The
    # adapter below posts the graph-walk JSON-RPC to the actual app; a parent
    # process fake or a direct service import cannot satisfy the recording.
    db_path = tmp_path / "registry.db"
    old_default = db_core.DEFAULT_DB_PATH
    db_core.DEFAULT_DB_PATH = db_path
    reset_database()
    token = "philo5-op-test"
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=token,
    )
    root = composition.installed()
    assert root is not None and root.bare_root is False
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {token}"})

    class ClientHub:
        _mcp_request_id = 0
        url = "http://testserver"

        def mcp(self, request):
            response = client.post("/api/mcp", json=request)
            assert response.status_code == 200, response.text
            return response.json()

    hub_client = ClientHub()
    seen: list[str] = []
    real_invoke = root.operations.invoke

    def recording_invoke(principal, name, args=None, **kwargs):
        seen.append(name)
        return real_invoke(principal, name, args, **kwargs)

    root.operations.invoke = recording_invoke
    try:
        made = gw.run_step(
            {"kind": "op", "name": "decision.create",
             "args": {"title": "Registry reached"}},
            page=None, hub=hub_client, provenance={}, variables={},
        )
        assert made["refusal"] is None, made
        decision_id = made["response"]["id"]
        read = gw.run_step(
            {"kind": "op", "name": "decision.read",
             "args": {"decision_id": decision_id}},
            page=None, hub=hub_client, provenance={}, variables={},
        )
        assert read["refusal"] is None, read
        assert read["response"]["id"] == decision_id
        assert seen == ["decision.create", "decision.read"]
    finally:
        root.operations.invoke = real_invoke
        reset_database()
        composition.install(composition.bare(label="pytest"))
        db_core.DEFAULT_DB_PATH = old_default


@pytest.mark.timeout(180)
def test_real_hub_thought_resource_refusal_is_named(tmp_path: Path):
    hub = gw.Hub(tmp_path / "home", token="philo5-thought-test").start()
    try:
        record = gw.run_step(
            {"kind": "op", "name": "thought.read",
             "args": {"thought_id": "missing-thought"}},
            page=None, hub=hub, provenance={}, variables={},
        )
        assert record["response"] is None
        assert record["refusal"]["code"] == "not_found"
        assert "Unknown thought" in record["refusal"]["error"]
        assert record["envelope"]["error"]["data"]["code"] == "not_found"
    finally:
        hub.stop()


@pytest.mark.timeout(180)
def test_real_hub_thought_capture_preserves_revisions_and_workspace_cursor(tmp_path: Path):
    hub = gw.Hub(tmp_path / "home", token="philo5-thought-save-test").start()
    variables: dict[str, object] = {}
    provenance = {"fixture_hashes": {}, "restarts": [],
                  "boundary_substitutions": [], "clock": {}}
    try:
        status, directory = hub.api(
            "POST", "/api/directories", {"id": "hs-seed-inbox", "name": "Inbox"})
        assert status == 201, directory
        made = gw.run_step(
            {"kind": "op", "name": "thought.create",
             "args": {"request_id": "graph-walk-thought", "raw_text": "captured body"},
             "capture_as": "thought_id", "capture_path": "thought.id"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
        assert made["refusal"] is None, made

        read = gw.run_step(
            {"kind": "op", "name": "thought.read",
             "args": {"thought_id": "{thought_id}"},
             "capture_as": "aggregate_revision",
             "capture_path": "thought.aggregate_revision"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
        assert read["refusal"] is None, read
        gw.run_step(
            {"kind": "op", "name": "thought.read",
             "args": {"thought_id": "{thought_id}"},
             "capture_as": "working_revision",
             "capture_path": "thought.working_revision"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
        workbench = gw.run_step(
            {"kind": "op", "name": "thought.workbench.read",
             "args": {"thought_id": "{thought_id}"},
             "capture_as": "workspace_cursor",
             "capture_path": "workspace_cursor"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
        cursor = variables["workspace_cursor"]
        assert isinstance(cursor, dict), workbench

        saved = gw.run_step(
            {"kind": "op", "name": "thought.save",
             "args": {
                 "thought_id": "{thought_id}",
                 "expected_aggregate_revision": "{aggregate_revision}",
                 "expected_working_revision": "{working_revision}",
                 "body_markdown": "saved through graph walk",
                 "workspace_cursor": "{workspace_cursor}",
             }},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
        assert saved["refusal"] is None, saved
        assert saved["response"]["thought"]["working_note"]["body_markdown"] == \
            "saved through graph walk"

        final = gw.run_step(
            {"kind": "op", "name": "thought.read",
             "args": {"thought_id": "{thought_id}"}},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
        assert final["response"]["thought"]["working_note"]["body_markdown"] == \
            "saved through graph walk"
        assert variables["workspace_cursor"] == cursor
    finally:
        hub.stop()
