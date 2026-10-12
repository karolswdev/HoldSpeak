"""The graph-walk rig (scripts/graph_walk.py): the op_facts evaluator and
the rig's carriage through the REAL hub (MeetingWebServer over /api/mcp).

Moved from tests/unit/test_philo7_atlas.py by the fast diet (2026-10-12); the
Phase 7 atlas-case pins and the Phase 7 equivalence-run tests are parked in
tests/_parked/unit/test_philo7_atlas.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.runtime import composition
from scripts import graph_walk as gw

REPO = Path(__file__).resolve().parents[2]
TOKEN = "philo7-03-rig"

#: The admission table (phase status, "The admission table"): the writes the
#: Phase 7 ``.op`` cases fire that are ADMITTED unconditionally.
#: The note cases with a durable outcome (phase status, "Named atlas pairs").


# ─────────────────────────── the op_facts evaluator ──────────────────────────

def _after(**parts: Any) -> dict[str, Any]:
    return {"headless": True, **parts}


def _ok(response: Any) -> dict[str, Any]:
    return {"name": "x", "response": response, "refusal": None}


def test_an_empty_fact_list_is_never_a_pass() -> None:
    ok, why = gw.check_predicate({"kind": "op_facts", "facts": []}, {}, _after(op=_ok({})))
    assert not ok and why.startswith("BLOCKED")


def test_a_fact_without_a_test_is_never_a_pass() -> None:
    ok, why = gw.check_predicate(
        {"kind": "op_facts", "facts": [{"source": "observe", "path": "id"}]}, {}, _after(op=_ok({"id": "a"})))
    assert not ok and why.startswith("BLOCKED")


def test_every_fact_must_hold() -> None:
    predicate = {"kind": "op_facts", "facts": [
        {"source": "observe", "path": "id", "value": "a"},
        {"source": "read", "index": 0, "path": "objects.0.receipt.operation_id", "value": "op_1"},
    ]}
    receipt = _ok({"objects": [{"receipt": {"operation_id": "op_1"}}]})
    assert gw.check_predicate(predicate, {}, _after(op=_ok({"id": "a"}), op_reads=[receipt]))[0]
    wrong = _ok({"objects": [{"receipt": {"operation_id": "op_2"}}]})
    ok, why = gw.check_predicate(predicate, {}, _after(op=_ok({"id": "a"}), op_reads=[wrong]))
    assert not ok and "op_2" in why


@pytest.mark.parametrize("reads", [[], [{"name": "kernel.receipt.read", "skipped": "unresolved placeholder; not sent"}]])
def test_a_missing_or_unsent_read_fails(reads) -> None:
    predicate = {"kind": "op_facts", "facts": [
        {"source": "read", "index": 0, "path": "objects.0.receipt.state", "value": "succeeded"}]}
    ok, _ = gw.check_predicate(predicate, {}, _after(op=_ok({}), op_reads=reads))
    assert not ok


def test_a_refused_read_never_satisfies_a_success_fact() -> None:
    predicate = {"kind": "op_facts", "facts": [{"source": "observe", "path": "id", "absent": True}]}
    refused = {"name": "x", "response": None, "refusal": {"code": "not_found", "error": "gone"}}
    ok, why = gw.check_predicate(predicate, {}, _after(op=refused))
    assert not ok and "refused" in why


def test_a_refusal_fact_needs_a_refusal_and_its_code() -> None:
    fact = {"source": "trigger", "refused": {"code": "not_found"}, "path": "error", "value": "Unknown directory: z"}
    predicate = {"kind": "op_facts", "facts": [fact]}
    refused = {"response": None, "refusal": {"code": "not_found", "error": "Unknown directory: z"}}
    assert gw.check_predicate(predicate, {}, _after(operation_trigger=refused))[0]
    other = {"response": None, "refusal": {"code": "mcp_refused", "error": "Unknown directory: z"}}
    assert not gw.check_predicate(predicate, {}, _after(operation_trigger=other))[0]
    succeeded = {"response": {"id": "z"}, "refusal": None}
    assert not gw.check_predicate(predicate, {}, _after(operation_trigger=succeeded))[0]


def test_contains_lacks_and_length_read_rows() -> None:
    rows = [{"primitive_id": "note:n", "directory_id": "z"}]
    facts = [
        {"source": "observe", "path": "", "contains": {"primitive_id": "note:n"}},
        {"source": "observe", "path": "", "lacks": {"primitive_id": "note:m"}},
        {"source": "observe", "path": "", "length": 1},
    ]
    assert gw.check_predicate({"kind": "op_facts", "facts": facts}, {}, _after(op=_ok(rows)))[0]
    for fact in ({"source": "observe", "path": "", "contains": {"primitive_id": "note:m"}},
                 {"source": "observe", "path": "", "lacks": {"primitive_id": "note:n"}},
                 {"source": "observe", "path": "", "length": 0}):
        assert not gw.check_predicate({"kind": "op_facts", "facts": [fact]}, {}, _after(op=_ok(rows)))[0], fact


# ───────────────────────── the rig's carriage, real hub ─────────────────────

class _RealHub:
    """The rig's ``hub.mcp``/``hub.api`` seams over the real hub app."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def mcp(self, request: dict[str, Any]) -> dict[str, Any]:
        return self.client.post("/api/mcp", json=request).json()

    def api(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        resp = self.client.request(method, path, json=body)
        return resp.status_code, resp.json()


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "rig.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=TOKEN,
    )
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    yield _RealHub(client)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _kb_with_note(hub: _RealHub) -> tuple[str, str]:
    kb = gw._op_call(hub, "kb.create", {"name": "Carriage"})["response"]["id"]
    note = gw._op_call(hub, "note.create", {"title": "Carried"})["response"]["id"]
    return kb, note


def test_two_references_never_collapse_into_one_admitted_write(hub) -> None:
    """Astra's probe (red-kb-alias-probe.txt): resource_ref and ref both became
    ``ref`` and the later one was ADDED -- a write the case never stated."""
    kb, note = _kb_with_note(hub)
    args = {"kb_id": kb, "resource_ref": f"note:{note}", "ref": "note:other"}
    try:
        record = gw._op_call(hub, "kb.member.add", args)
    except gw.Blocked as exc:
        assert "'ref'" in str(exc), exc
    else:
        assert record["refusal"] is not None, f"the rig executed a collapsed write: {record['request']}"
    assert gw._op_call(hub, "kb.members", {"kb_id": kb})["response"] == []


def test_the_canonical_reference_is_carried(hub) -> None:
    kb, note = _kb_with_note(hub)
    record = gw._op_call(hub, "kb.member.add", {"kb_id": kb, "resource_ref": f"note:{note}"})
    assert record["request"]["params"]["arguments"] == {"kb_id": kb, "ref": f"note:{note}"}
    assert record["refusal"] is None and record["response"]["resource_ref"] == f"note:{note}"


def test_a_successor_id_is_never_answered_by_a_schema_refusal(hub) -> None:
    """decision.supersede takes successor_id; its MCP tool does not. The rig
    blocks the step by name instead of reporting a refusal the operation would
    never give (and the decision stays as it was)."""
    decision = gw._op_call(hub, "decision.create", {"title": "Keep", "status": "accepted"})["response"]["id"]
    try:
        record = gw._op_call(hub, "decision.supersede", {"decision_id": decision, "successor_id": "chosen"})
    except gw.Blocked as exc:
        assert "successor_id" in str(exc), exc
    else:
        pytest.fail(f"the rig sent a request the tool cannot carry: {record['request']} -> {record['refusal']}")
    assert gw._op_call(hub, "decision.read", {"decision_id": decision})["response"]["status"] == "accepted"


def test_a_refusal_receipt_is_captured_from_the_refusal_only_when_asked(hub) -> None:
    note = gw._op_call(hub, "note.create", {"title": "Loose"})["response"]["id"]
    step = {"kind": "op", "name": "zone.file", "capture_as": "refused_op", "capture_path": "operation_id",
            "args": {"directory_id": "absent-zone", "primitive_id": f"note:{note}"}}
    provenance: dict[str, Any] = {"fixture_hashes": {}}
    with pytest.raises(gw.Blocked):
        gw._op_step(step, hub, provenance, variables={})  # a refused write is not a success
    variables: dict[str, Any] = {}
    record = gw._op_step({**step, "capture_from": "refusal"}, hub, provenance, variables=variables)
    assert variables["refused_op"] == record["refusal"]["operation_id"]
    receipt = gw._op_call(hub, "kernel.receipt.read", {"operation_id": variables["refused_op"]})["response"]
    assert receipt["objects"][0]["receipt"]["state"] == "refused"


def test_an_api_capture_matches_by_value_never_by_position(hub) -> None:
    hub.api("POST", "/api/directories", {"name": "Seeded first"})
    hub.api("POST", "/api/directories", {"name": "Atlas zone"})
    variables: dict[str, Any] = {}
    step = {"kind": "api", "method": "GET", "path": "/api/directories", "body": None,
            "capture_as": "zone_id", "capture_path": "directories", "capture_match": {"name": "Atlas zone"}}
    record = gw.run_step(step, None, hub, {"fixture_hashes": {}}, variables=variables)
    zones = hub.api("GET", "/api/directories")[1]["directories"]
    assert variables["zone_id"] == next(z["id"] for z in zones if z["name"] == "Atlas zone")
    assert record["captured"]["match"] == {"name": "Atlas zone"}
    ambiguous = {**step, "capture_match": {"parent_id": None}}  # both rows are at the root
    with pytest.raises(gw.Blocked, match="matched 2 rows"):
        gw.run_step(ambiguous, None, hub, {"fixture_hashes": {}}, variables={})


def test_a_width_scoped_step_is_recorded_skipped_at_the_other_width() -> None:
    page = MagicMock()
    page.viewport_size = {"width": 1440}
    record = gw._ui_step(page, {"kind": "ui", "action": "click", "selector": "#x", "at_width": 393})
    assert record.get("skipped") and record.get("done") is False
    page.locator.assert_not_called()
    page.viewport_size = {"width": 393}
    record = gw._ui_step(page, {"kind": "ui", "action": "focus", "selector": "#x", "at_width": 393})
    assert record["done"] is True
    page.locator.assert_called_with("#x")
