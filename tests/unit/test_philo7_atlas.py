"""PHILO-7-03: the atlas for the desk.

Three kinds of fence:

* the ``op_facts`` evaluator (``scripts/graph_walk.py``): a conjunction over
  actual operation reads, where missing, unread or refused evidence FAILS;
* the Phase 7 atlas file (``docs/internal/philo/graph/atlas-phase7.json``):
  every named pair is minted at 1440 and 393 with a headless ``.op``
  sibling, every admitted write the ``.op`` cases fire reads its kernel
  receipt back (refusal receipts included), and no face case claims one;
* the rig's carriage through the REAL hub (``MeetingWebServer`` over
  ``/api/mcp``): a case's arguments are sent as stated or the step is blocked
  by name, never collapsed into a different admitted write.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.runtime import composition
from scripts import graph_walk as gw

REPO = Path(__file__).resolve().parents[2]
ATLAS7 = REPO / "docs/internal/philo/graph/atlas-phase7.json"
STATUS = REPO / "pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/current-phase-status.md"
TOKEN = "philo7-03-rig"

#: The admission table (phase status, "The admission table"): the writes the
#: Phase 7 ``.op`` cases fire that are ADMITTED unconditionally.
ADMITTED = frozenset({
    "decision.create", "decision.update", "decision.supersede", "decision.delete",
    "zone.file", "zone.unfile", "kb.member.add", "kb.member.remove",
})
#: The note cases with a durable outcome (phase status, "Named atlas pairs").
NOTE_SIBLINGS = (
    "case.j1.first_words_keep_as_note.kept",
    "case.j11.write_a_thought.window_open",
    "case.j11.thought_keep.kept",
)


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


# ─────────────────────────────── the atlas file ──────────────────────────────

@pytest.fixture(scope="module")
def atlas7() -> dict:
    return json.loads(ATLAS7.read_text())


def _named_cases() -> list[str]:
    """The NEW browser cases the phase status names (section "Named atlas pairs")."""
    text = STATUS.read_text()
    section = text.split("## Named atlas pairs", 1)[1].split("\n## ", 1)[0]
    return re.findall(r"`(case\.p7\.[a-z0-9_.]+)`", section)


def _cases(atlas: dict) -> dict[str, dict]:
    return {case["id"]: case for case in atlas["cases"]}


def test_the_phase_status_names_nine_new_cases() -> None:
    assert len(_named_cases()) == 9, _named_cases()


def test_every_named_case_runs_at_both_widths_with_a_headless_sibling(atlas7) -> None:
    cases = _cases(atlas7)
    for case_id in _named_cases():
        assert case_id in cases, f"{case_id} is not minted"
        face = cases[case_id]
        assert sorted(face["viewports"]) == [393, 1440], case_id
        assert face["expected"]["predicate"]["kind"] == "readable_text", case_id
        sibling = cases.get(case_id + ".op")
        assert sibling is not None, f"{case_id} has no .op sibling"
        assert sibling["viewports"] == [], case_id
        assert not [step for step in sibling["setup"] + [sibling["trigger"]] if step["kind"] == "ui"], case_id


def test_the_durable_note_cases_have_op_siblings_and_the_boundary_case_is_excluded(atlas7) -> None:
    cases = _cases(atlas7)
    for case_id in NOTE_SIBLINGS:
        assert case_id + ".op" in cases, case_id
    excluded = {row["combination"] for row in atlas7["excluded"]}
    assert any("create_refused" in combination for combination in excluded)


def _op_steps(case: dict) -> list[dict]:
    return [step for step in case["setup"] + [case["trigger"]] if step["kind"] == "op"]


def _receipt_reads(case: dict) -> dict[str, str]:
    """{captured operation-id variable: 'observe' | 'read:<index>'} of each receipt read."""
    expected = case["expected"]
    found: dict[str, str] = {}
    observe = expected.get("observe_at")
    if isinstance(observe, dict) and observe.get("name") == "kernel.receipt.read":
        found[observe["args"]["operation_id"]] = "observe"
    op_reads = [read for read in expected.get("reads", []) if read.get("kind") == "op"]
    for index, read in enumerate(op_reads):
        if read.get("name") == "kernel.receipt.read":
            found[read["args"]["operation_id"]] = f"read:{index}"
    return found


def test_every_captured_admitted_write_reads_its_receipt_by_its_own_id(atlas7) -> None:
    """A captured operation id is proved only by a receipt READ whose
    operation_id fact names that same id -- never by the inline receipt."""
    problems = []
    for case in atlas7["cases"]:
        if case["viewports"]:
            continue
        reads = _receipt_reads(case)
        facts = case["expected"]["predicate"].get("facts", [])
        for step in _op_steps(case):
            if step["name"] not in ADMITTED or step.get("capture_path") != "operation_id":
                continue
            placeholder = "{%s}" % step["capture_as"]
            where = reads.get(placeholder)
            if where is None:
                problems.append(f"{case['id']}: {step['name']} {placeholder} has no receipt read")
                continue
            source, _, index = where.partition(":")
            matched = [fact for fact in facts
                       if fact.get("source") == source
                       and (not index or fact.get("index") == int(index))
                       and fact.get("path") == "objects.0.receipt.operation_id"
                       and fact.get("value") == placeholder]
            if not matched:
                problems.append(f"{case['id']}: the receipt read of {placeholder} is not asserted by id")
    assert not problems, problems


def test_every_admitted_write_the_cases_fire_has_its_receipt_read_somewhere(atlas7) -> None:
    fired = {step["name"] for case in atlas7["cases"] if not case["viewports"]
             for step in _op_steps(case) if step["name"] in ADMITTED}
    receipted = {step["name"] for case in atlas7["cases"] if not case["viewports"]
                 for step in _op_steps(case)
                 if step["name"] in ADMITTED and step.get("capture_path") == "operation_id"
                 and "{%s}" % step["capture_as"] in _receipt_reads(case)}
    assert fired <= receipted, sorted(fired - receipted)


def test_every_receipt_read_asserts_its_actor(atlas7) -> None:
    """Round two (Muad'Dib F3): the evidence says each receipt is checked for
    its actor. Every kernel receipt a case reads asserts actor_kind AND
    actor_identity (the owner), from that same read."""
    problems = []
    for case in atlas7["cases"]:
        if case["viewports"]:
            continue
        facts = case["expected"]["predicate"].get("facts", [])
        for placeholder, where in _receipt_reads(case).items():
            source, _, index = where.partition(":")
            paths = {fact.get("path"): fact.get("value") for fact in facts
                     if fact.get("source") == source and (not index or fact.get("index") == int(index))}
            if paths.get("objects.0.receipt.actor_kind") != "owner" \
                    or paths.get("objects.0.receipt.actor_identity") != "owner-session":
                problems.append(f"{case['id']}: the receipt read of {placeholder} does not assert its actor")
    assert not problems, problems


def test_the_supersede_receipt_names_the_successor_the_write_returned(atlas7) -> None:
    """Round two (Muad'Dib F3): the successor is captured from the supersede's
    own result and the READ receipt's result_ref must name it."""
    case = _cases(atlas7)["case.p7.decision_supersede.receipt.op"]
    assert {"as": "successor_id", "path": "id"} in case["trigger"].get("capture_more", [])
    facts = case["expected"]["predicate"]["facts"]
    assert {"source": "observe", "path": "objects.0.receipt.result_ref", "value": "decision:{successor_id}"} in facts


def test_refusal_receipts_are_read_for_each_admitted_family(atlas7) -> None:
    refused = {step["name"] for case in atlas7["cases"] if not case["viewports"]
               for step in [case["trigger"]]
               if step.get("capture_from") == "refusal" and "{%s}" % step["capture_as"] in _receipt_reads(case)}
    assert {"zone.file", "kb.member.add", "decision.update", "decision.delete"} <= refused, refused


def test_no_face_case_claims_a_receipt(atlas7) -> None:
    for case in atlas7["cases"]:
        if not case["viewports"]:
            continue
        text = json.dumps(case["expected"]["predicate"]) + json.dumps(case["expected"].get("reads", []))
        assert "receipt" not in text and "/api/kernel" not in text, case["id"]


def test_every_fact_names_a_source_a_test_and_a_read_in_range(atlas7) -> None:
    for case in atlas7["cases"]:
        predicate = case["expected"]["predicate"]
        if predicate["kind"] != "op_facts":
            continue
        op_reads = [read for read in case["expected"].get("reads", []) if read.get("kind") == "op"]
        assert predicate["facts"], case["id"]
        for fact in predicate["facts"]:
            assert fact["source"] in gw.OP_FACT_SOURCES, (case["id"], fact)
            assert any(test in fact for test in gw.OP_FACT_TESTS), (case["id"], fact)
            if fact["source"] == "read":
                assert 0 <= fact["index"] < len(op_reads), (case["id"], fact)


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


# ───────────────────── the equivalence run (round two, F2) ──────────────────

from scripts import philo7_pairs as pairs  # noqa: E402


def _delete_op_obs(*, listed: bool = False, receipt_op: str = "op_d", target: str = "decision:d1") -> dict:
    return {
        "variables": {"decision_id": "d1", "delete_op": "op_d"},
        "after": {
            "op": {"response": [{"id": "d1"}] if listed else [], "refusal": None},
            "op_reads": [
                {"response": None, "refusal": {"code": "not_found", "error": "Unknown decision: d1"}},
                {"response": {"objects": [{"receipt": {"operation_id": receipt_op, "target_ref": target}}]},
                 "refusal": None},
            ],
        },
    }


def test_the_delete_identity_is_a_real_check() -> None:
    """Muad'Dib F2a: the delete pair's identity leg returned True whatever it read."""
    assert pairs._delete_op(_delete_op_obs())[1] is True
    assert pairs._delete_op(_delete_op_obs(listed=True))[1] is False
    assert pairs._delete_op(_delete_op_obs(receipt_op="op_other"))[1] is False
    assert pairs._delete_op(_delete_op_obs(target="decision:someone-else"))[1] is False
    face = {"variables": {"decision_id": "d1"}, "after": {"api_reads": [
        {"path": "/api/decisions/d1", "status": 200, "payload": {"decision": {"id": "d1"}}},
        {"path": "/api/decisions", "status": 200, "payload": {"decisions": [{"id": "d1"}]}}]}}
    assert pairs._delete_face(face)[1] is False


def test_a_face_trigger_that_sends_nothing_is_not_a_refusal_check() -> None:
    """Muad'Dib F2b: no network response is 'not applicable', never 'not refused'."""
    assert pairs._face_trigger_response({"trigger_response_capture": {"chosen": None}}) is None
    chosen = {"method": "PUT", "path": "/x", "status": 200}
    assert pairs._face_trigger_response({"trigger_response_capture": {"chosen": chosen}}) == chosen
